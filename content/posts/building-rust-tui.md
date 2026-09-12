---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2026-09-12
 linktitle: "building a TUI in Rust"
 title: "Building a TUI for reviewing claude sessions and github PRs, in Rust"
 categories:
 - project
 tags:
 - blog
 - updates
 - rust
 - tui
 type:
 - post
 - posts
 weight: 10
 series:
 toc: true
 comments: true
---

# How prtui makes a PR, a branch, and a Claude Code session the same review

This is the technical follow-up to [the philosophy post](/posts/2026/09/prtui/). Which I thought I owe it all of you.

Repository for reference: [github.com/krshrimali/research-reviews/tree/main/rtui](https://github.com/krshrimali/research-reviews/tree/main/rtui)

Let's start with the our core `struct`:

## one struct is the main core

```rust
pub struct Source {
    pub kind: &'static str,                                 // "branch" | "pr" | "claude"
    pub repo_root: STring,
    pub base_sha: String,
    pub head_sha: String,
    pub commits: Vec<Commit>,
    pub files: Vec<ChangedFile>,
    pub caps: Caps,                                         // what this kind of source can actually do? [capabilities]
    pub synthetic_diff: HashMap<String, String>             // non-git sources only...
    // ...
}
```

- Everything in our "PRTUI" (files, commits, diff tab, comment anchoring, publish flow) -> operates on a single `Source`.
- A GitHub PR and a local branch both fill this in by shelling out to `git`/`gh` and letting `base_sha..head_sha` do the work.
- Commits come from `git log`.
- `files` come from `git diff --name-status`, and any given file's diff would be fetched from git on demand.

But, what about claude session's diff?

- The diff of a claude session comes from a transcript, with `synthetic_diffs` being the holding source for every diff.
    - Why not use git? Well, you don't always start claude from `git`, and then not everything is committed and pushed ofc.

```rust
impl Source {
    pub fn commit_diff(&self, sha: &str) -> String {
        if self.caps.is_claude_session {
            self.synthetic_diffs.get(sha).cloned().unwrap_or_default()
        } else {
            git::commit_diff(sha, Some(self.repo_root));
        }
    }
}
```

Everything above this layer, like ratatui rendering, the comment store, the outdated thread detection, the split-diff view - has no idea whether they are looking at a GitHub API or a JSONL file on the disk.

Coding style note: The `Caps` struct (`can_submit`, `has_threads`, `is_claude_session`, ...) is what a session opts out of - there's no PR to publish to, so `caps.can_submit` is `false` and the publish key just says so instead of guessing from `kind == 'claude'` string matching style.

## how are claude sessions handled?

A claude code session is a `.jsonl` file under `~/.claude/projects/<repo-id/name>`, one event per line: user messages, assistant messages (text + tool calls), and tool results.
    - Turning this into "commits" means deciding where one turn ends and the next begins, which is just:

> a new turn starts at every real user message, and everything the assistant does in response belongs to that same turn, until the next real prompt.

I know, "Real" sounds fishy, right? Because, there can be messages which look like user messages but aren't, slash-command invocations, system reminder injections, hook notifications etc. Getting the turn boundary right means filtering those out (`is_synthetic_wrapper`) while still unwrapping the ones that "are" real - a `/goal` invocations' `<command-args>` content is the actual prompt, just fenced.

What does this cost us though? The payoff for getting the boundary right is that the diff part is almost free! Every `Edit, Write, MultiEdit` tool calls' result carries a `structuredPatch` -> claude code's own pre-computed hunk array, `oldStart/oldLines/newStart,newLines/lines` the exact shape a unified diff hunk already has:

```json
"structuredPatch": [{
    "oldStart": 48, "oldLines": 11, "newStart": 48, "newLines": 11,
    "lines": [" })", " ", "-monitor=...", "--somemorecode", " })"]
}]
```

That's a `diff --git` block away from being a real patch :) No diffing algorithm would be needed here (!!)!

```rust
fn build_file_change(repo_root: &str, raw_path: &str, tur: &Value) -> Option<FileChange> {
    let patch = tur.get("structuredPatch")?.as_array()?;
    // ... format each hunk's "@@ -oldStart,oldLines +newStart,newLines @@" + lines
}
```

Each turn's response text gets folded in as `# ` - prefixed comment lines above its diff (rendered through the same lightweight inline-markdown parser used for PR/comment bodies - bold, code spans, headings), so opening a turn shows the prompt, the reply and the patch it produced, all in one screen that's structurally identical to a commit view.

## so that's it?

Nope! There's diff that claude code doesn't give us. The per-turn hunks are great until a file gets touched twice:

Concatenate turn 1's hunk and turn 3's hunk for the same file and you get two `@@` blocks that can both claim to be line "line 12" - because each `structuredPatch` is relative to that edit's own before/after state, not to the file's state at the start of the session. Render that as one file's diff and a comment on "line 12" is ambiguous - which edit is line 12??

What you actually want for "browse this file's history" is a 2-point diff:

*. Content at session start vs content now.
    - The file's current content on disk is almost always right - the session lives inside your real checkout, nothing needs to reconstruct that part. So walk backward instead: take the current content, and for every edit this session made to this file, undo it - in reverse chronological order - using nothing but `structuredPatch` which every edit always carries. I'll leave the code logic away from this blog as it's less interesting to read but more interesting to think :)

That still leaves an actual diffing problem: two full file contents, no hunks connecting them. Claude Code can't help here - this pairing never happened as one of its edits - so this is the one spot in prtui with a real diff algo. It's the textbook LCS edit-script, walked forward through a DP table computed backward:

```rust
enum LineOp { Eq(usize, usize), Del(usize), Ins(usize) }

fn line_ops(a: &[&str], b: &[&str]) -> Vec<LineOp> {
    let (n, m) = (a.len(), b.len());
    let mut dp = vec![vec![0u32; m + 1]; n + 1];
    for i in (0..n).rev() {
        for j in (0..m).rev() {
            dp[i][j] = if a[i] == b[j] { dp[i+1][j+1] + 1 } else { dp[i+1][j].max(dp[i][j+1]) };
        }
    }
    let (mut i, mut j, mut ops) = (0, 0, Vec::new());
    while i < n && j < m {
        if a[i] == b[j] { ops.push(LineOp::Eq(i, j)); i += 1; j += 1; }
        else if dp[i+1][j] >= dp[i][j+1] { ops.push(LineOp::Del(i)); i += 1; }
        else { ops.push(LineOp::Ins(j)); j += 1; }
    }
    // trailing tail: whichever side has leftovers
    ops
}
```

Maybe in one of our blogs, we'll cover this in detail..., but for now, onto the next challenge.

## comments that survive the code moving

All the work would go into a bin, if a common silently detaches from the line it was about. `prtui` reuses the same reconcilation for every source kind:

Each comment snapshots the trimmed code of the line it was anchored to, and on every reload, `locate_anchor` checks what happened to that snapshot.

```rust
pub fn locate_anchor(line_start: u32, anchor: &str, code_at: &HashMap<u32, String>) -> Anchor {
    if code_at.get(&line_start) == Some(&anchor.to_string()) { return Anchor::InPlace; }
    let matches: Vec<u32> = code_at.iter()
        .filter(|(_, v)| v.as_str() == anchor).map(|(k, _)| *k).collect();
    match matches.len() {
        0 => Anchor::Outdated,
        1 => Anchor::MoveTo(matches[0]),
        _ => {
            let nearest = *matches.iter().min_by_key(|k| (**k as i64 - line_start as i64).abs()).unwrap();
            if (nearest as i64 - line_start as i64).abs() <= REPOSITION_WINDOW {
                Anchor::MoveTo(nearest)
            } else {
                Anchor::Outdated  // too ambiguous to trust a duplicate-line match this far away
            }
        }
    }
}
```

Unchanged code that just moved (a function got reordered, a line shifted after an insert above it) follows the comment with it. Code that's actually gone gets marked as Outdated - pulled off the live diff, kept in a dedicated Comments-view section with the original snapshot for context, exactly like GitHub does it.

This runs identically whether the "diff" underneath is `git diff` output or a synthetic session diff, because by the time this code runs, it's just lines and line numbers — the `Source` abstraction has already erased where they came from.

## nothing blocks on network or disk

Our picker, which shows you all the sources as options:

1. Local branches (instant, `git for-each-ref`)
    - These run synchronously.
2. PRs need a network round-trip through `gh`
    - Runs on its own background thread with an `mpsc::Receiver` (the picker polls every frame)
3. Claude session discovery means reading and JSON-parsing every `.jsonl` file in `~/.claude/projects/<slug>`
    - Runs on its own background thread with an `mpsc::Receiver` (the picker polls every frame)

```rust
let (claude_tx, claude_rx) = channel();
std::thread::spawn(move || {
    let sessions = claude_sessions::discover(&claude_root) // this reads and parses every .jsonl file
        .into_iter().map(item_from_session).collect();
    let _ = claude_tx.send(sessions);
});
```

A large session history or a slow `gh pr list` would show up as a spinner, so that the terminal doesn't look frozen :) The same pattern runs the actual claude review process (`claude -p --output-format stream-json`), streaming progress into the status bar while stdout is read on one thread and stdin is written on another, so a large prompt piped in can't deadlock against a large response streaming out.

## a prompt you can paste anywhere

While I did integrate claude reviews into my tool, but giving users the final prompt to modify/use it at their convenience was my goal as well.

The prompt builder (keymap: 'Y') exists exactly for this. You would be able to pick comment which matters for your review, edit the assembled text by hand, and paste the result into any CLI.

```rust
user.push_str("Inspect the current checkout directly. Run:\n\n```sh\n");
user.push_str(&format!("git diff --no-ext-diff --unified=3 {}...HEAD", source.base_sha));
```

That trick quietly breaks for a Claude session, though - `base_sha` and `head_sha` are both just "the repo's current HEAD" there (there's no comparison range, only a transcript), so the generated command is `git diff HEAD...HEAD`: always empty. The fix is the obvious one once you notice it: check `caps.is_claude_session` and paste the diff directly instead of the command, since a session's diff already lives in memory and isn't the multi-thousand-line patch this trick exists to avoid pasting.

## how it's tested

This is where it helped me a lot, thanks to ratatui's `TestBackend` - a terminal buffer with no terminal attached, so the whole test suite runs headless:

- real key events through: `App::on_key`
- assertions on the resulting buffer's text and styles
- uses a small binary that walks every screen of a synthetic fixture repo (and a real cc session transcript) and exports each one as an SVG via `buffer_to_svg` via RataTui's `shot`.
    - btw, this is how the screenshots were taken and put into README, everything automated :) -> none of them are mockups.

This is also how I enabled my agentic calls to find bugs, asking it to use those screenshots and find real UI/UX bugs + trying out all valid operations via the UI.

And yep! I can't miss adding that none of these are large ideas on their own:

- Reusing a struct
- Undoing a patch instead of replaying it
- Shelling out to `date`
- Asserting instead of assuming

Whta they all add up to is a tool where reviewing a CC session costs "nothing extra" over reviewing a PR.

**Code:** [github.com/krshrimali/research-reviews/tree/main/rtui](https://github.com/krshrimali/research-reviews/tree/main/rtui)

## how to install?

It's pretty simple, instructions below:

```bash
git clone https://github.com/krshrimali/research-reviews.git
cd research-reviews/rtui
cargo build --release
./target/release/prtui            # opens the picker: PRs, branches, Claude sessions
```

Hope y'all liked this blog! :)

Thanks for reading!
