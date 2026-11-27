---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2026-11-27T11:00:00+05:30
linktitle: "Vaayu part 11: private code reviews that survive edits"
title: "Vaayu part 11: private code reviews that survive edits"
categories:
- project
tags:
- vaayu
- rust
- editor
- code-review
- ai
type:
- post
- posts
weight: 10
series:
toc: true
comments: true
---

_Part 11 of the [Vaayu series](/posts/2026/11/why-i-wrote-my-own-editor/), and the first of three posts about the workflows I actually built Vaayu for. This one is about reviewing code: why it needed to move into the editor, and how a comment stays attached to the right code while that code keeps changing under it._

## why this matters

I've [written before](/posts/2026/09/reviews-deserve-better-tooling/) that reviews have become the bottleneck. A growing share of the code I read wasn't typed by a person. An agent wrote it, in a few minutes, and now I have to understand it, question it, and decide whether it's right.

GitHub reviews are built for a different moment: the code is finished, pushed, and someone else reads it. But my most important review happens earlier, while the code is still changing, often in a loop with an agent:

1. the agent writes something,
2. I read it and leave comments on specific lines,
3. the agent (or I) fixes them,
4. I check the fixes and resolve or reply,
5. repeat until it's good enough to push.

For that loop, I need comments that are:

- **private**: not on GitHub, not in the code, not in a commit,
- **attached to code that's still being edited**, possibly by several things at once,
- **readable by an agent**, with a way for it to reply,
- and, when I'm done, **publishable** to the PR if I want.

Nothing in my Neovim setup did all of that. `octo.nvim` comments on a PR that already exists on GitHub. `review.nvim` was close, and I'd commented it out of my config. So reviews became a first-class Vaayu feature.

## what it looks like

`,rc` on a line or a Visual selection opens a comment right below the code, tinted so you can see what it's about. Type, `Esc`, `:w`. That's a comment.

![Selecting three lines with V, ,rc opens a comment window, the comment is typed and saved with :w, and after :q the gutter shows ● and the comment text appears after the line; ,rl then lists it](/assets/blogs/vaayu/review.gif)

Saved comments show in the gutter:

| Mark | Meaning |
| --- | --- |
| `●` | an open comment starts here |
| `│` | the rest of its range |
| `◌` | the code it was about has changed: check it |
| `○` | resolved |

and as text after the line (`:set reviewtext=all|cursor|off`). `]r`/`[r` jump between open comments **across files**. `,rv` shows the thread, `,rr` replies, `,rx` resolves. `,rl` lists the whole review in a Results list ([part 7](/posts/2026/11/vaayu-part-7-splits-floating-terminals-and-one-results-list/)), and the detail pane shows the thread, the code as it was when you commented, and the code there now, if it's different.

A folder can hold any number of named reviews (`:reviews`), each with an optional base revision, so `:reviewfiles` can list the files changed since `main` with a comment count next to each.

## the hard part: where did my line go?

A comment says "line 42 of `src/render.rs`". Then:

- you insert ten lines above it,
- you save, and `rustfmt` reflows the file,
- the agent moves the function to another place in the file,
- you `git pull` and someone else changed it.

Line numbers break on the very first edit. So a comment stores more than a line number:

```rust
pub struct Comment {
    pub id: u64,
    /// The `#N` people see; unique within a review and never reused.
    pub seq: u64,
    pub file: PathBuf,
    /// 0-based, inclusive.
    pub start: usize,
    pub end: usize,
    /// The commented lines as they were when the comment was placed.
    pub anchor: String,
    pub before: Vec<String>,   // 2 lines of context above
    pub after: Vec<String>,    // 2 lines of context below
    pub text: String,
    pub status: Status,
    pub state: AnchorState,
    // author, timestamps, replies...
}
```

The **anchor** is the commented code itself, plus two lines of **context** on each side. Following the code happens in two layers.

### layer 1: live edits

While a file is open, comments follow edits as you type, using the line-shift log from [part 1](/posts/2026/11/vaayu-part-1-text-is-a-tree/). Insert ten lines above, and the comment moves down ten lines immediately, before you save. Undo moves it back.

### layer 2: re-finding after the file changes

When a file changes on disk (you saved and a formatter ran, the agent edited it, you pulled), the shift log doesn't know what happened. So the comment has to be **found again**. That's [`locate`](https://github.com/krshrimali/vaayu/blob/master/src/review_store.rs):

```rust
/// Finds where `c`'s anchor is now: `(start, end, state)`.
///
/// The fast path keeps the comment where it is when the anchor and its
/// context still match there (live edits already shifted it). Otherwise
/// every occurrence is scored by how much surrounding context still
/// matches; a unique best match moves the comment, an unresolvable tie or a
/// whitespace-only match without context keeps the nearest candidate but
/// marks it stale for a person to check.
pub fn locate(c: &Comment, idx: &LineIndex) -> (usize, usize, AnchorState)
```

In steps:

1. **Fast path.** If the anchor is still exactly where the comment thinks it is, with all of its context, done.
2. **Find candidates.** Every place in the file where the anchor's lines appear. First exactly, then again ignoring whitespace (so a reindent doesn't lose the comment).
3. **Score them by context.** Count how many of the surrounding lines still match, walking outward until one doesn't:

   ```rust
   fn context_score(lines: &[String], start: usize, n: usize, c: &Comment) -> usize {
       let mut score = 0;
       for (k, b) in c.before.iter().rev().enumerate() {
           if start > k && norm(&lines[start - 1 - k]) == norm(b) {
               score += 1;
           } else {
               break;
           }
       }
       for (k, a) in c.after.iter().enumerate() {
           if lines.get(start + n + k).is_some_and(|l| norm(l) == norm(a)) {
               score += 1;
           } else {
               break;
           }
       }
       score
   }
   ```

4. **Only move when certain.** A single best candidate whose surroundings agree moves the comment. Anything else (a tie between two identical blocks, a match whose context is completely different, no match at all) leaves the comment near where it was and marks it **needs attention** (`◌`).

That last rule is the most important design decision in the feature. There's a comment in the code about it:

```rust
// Certain: one best candidate whose surroundings agree (or there
// is no context to compare). A unique match whose context all
// differs is more likely an unrelated identical line, so the
// comment stays put and is flagged instead of jumping there.
```

Think about `}` or `return Ok(());`, lines that appear dozens of times in a file. A tool that confidently moves your comment to the wrong `return Ok(());` is worse than one that says "I'm not sure where this went, please look". **A review tool should never guess silently.** The list's detail pane shows the original code next to what's there now, so checking takes a second, and `,rm` re-anchors the comment to wherever you point.

{{< vaayu-svg "anchor-scoring.svg" >}}

## many editors, one review

It's easy to end up with two Vaayu sessions open on the same repo (say, one in the terminal and one in a browser tab), while an agent run is replying to comments at the same time. Each one writes to the same review file. The naive approach (read, change, write) loses whatever the other one wrote in between.

So nothing writes the file directly. Every change is recorded as an **operation** that names exactly the fields it changes:

```rust
pub enum Op {
    Create(Box<Comment>),
    Text { id: u64, text: String, at: String },
    Status { id: u64, status: Status, at: String },
    Anchor { id: u64, file: PathBuf, start: usize, end: usize, /* ... */ },
    Position { id: u64, start: usize, end: usize, state: AnchorState },
    Rename { from: PathBuf, to: PathBuf },
    Delete { id: u64 },
    Reply { id: u64, reply: Reply },
    // title, review status, base...
}
```

and every write does this, from the module's own description:

> A write takes the review's OS lock, re-reads the file, replays this session's pending operations onto whatever is there now, and replaces it atomically -- so two editors (or an editor and an agent run) adding, editing and resolving comments in the same review merge instead of refusing or overwriting each other.

In code, the heart of `flush`:

```rust
let _lock = crate::files::private_lock(&dir, &format!("{}.lock", self.view.id))?;
let mut base = read_review(&self.path)?;          // whatever is on disk *now*
for op in &self.pending {
    if let Err(w) = op.apply(&mut base) {          // e.g. "comment was deleted
        warnings.push(w);                          //  in another session"
    }
}
crate::files::atomic_write(&self.path, serde_json::to_string_pretty(&base)?.as_bytes(), true)?;
```

It's a tiny version of how collaborative editors and databases merge: don't ship states, ship intentions, and replay them onto the latest state under a lock.

A few details fall out of this:

- **`#N` is assigned under the lock.** Two sessions creating a comment at the same moment get `#7` and `#8`, never two `#7`s. Numbers are never reused, so "fix #12" means the same thing forever.
- **Identity is a random 64-bit id**, separate from `#N`, so merging never depends on display numbers.
- **Other sessions' changes show up within about a second**: each session checks the file's metadata every 500 ms and reloads when it changed.
- **Deleted elsewhere** is handled: an edit to a comment someone else deleted is dropped with a warning instead of resurrecting it.

## privacy

Reviews live in `.vaayu/reviews/<id>.json` at the root of the git work tree, with `0700` directories and `0600` files, a local git ignore rule, and a refusal to follow symlinks. Source files are never modified. Unsaved comment drafts are covered by `:recover`.

To be clear about the limits: this is "only your OS account can read it" privacy, not encryption.

## handing comments to an agent

This is where the loop closes. `,ra` (or `A` in the list) sends the selected comments, or all open ones, to an agent command you configure:

```toml
review_command = ["claude", "-p", "--output-format", "text"]
```


The agent gets a versioned JSON packet on stdin: each comment with its thread, the code when it was commented, **the code there now**, and instructions. It answers on stdout with JSON Lines:

```json
{"comment": 3, "reply": "Renamed it to `row_signature`", "resolve": true}
{"file": "src/render.rs", "line": 120, "message": "This branch can't be reached when tabs > 1"}
```

- A `comment` line becomes a **reply** on that comment, marked as from the agent.
- `"resolve": true` doesn't resolve anything. It shows as `✓?`: the agent _proposes_ that it's done, and **a person decides**. That's on purpose.
- A `file`/`line` line (or plain `path:line: message` output) becomes a jumpable **finding**. `c` on a finding turns it into a real comment.
- Anything else is kept as raw output, so nothing the agent says is lost.

Every run's request, stdout, stderr and outcome are kept under `.vaayu/reviews/runs/` (`:reviewruns` to browse them). Runs can be cancelled and have a timeout that stops everything they started. `:reviewexport` writes the packet without running anything, if you'd rather paste it somewhere yourself.

This is the same philosophy as [prtui](/posts/2026/09/reviews-deserve-better-tooling/): an agent's work should be reviewed like a PR, line by line, with a paper trail. prtui does it after the fact; Vaayu does it while the code is still being written.

## to and from GitHub

When the code is pushed and has a PR:

- **`:reviewpublish`** prepares your open comments as a GitHub review. Comments on lines that are part of the PR's diff become inline comments; the rest go into the review's summary, so nothing is silently dropped (GitHub rejects inline comments outside the diff). You see the plan before anything is posted.
- **`:reviewimport`** goes the other way: a PR's review threads become a new local review, anchored in your working copy, so you can work through a colleague's comments with `]r` and track them privately.

## vs everything else

| | Private | Before pushing | Follows edits | Agent loop | GitHub |
| --- | :---: | :---: | :---: | :---: | :---: |
| GitHub / GitLab reviews | | | ~ | | ✓ |
| octo.nvim | | | ~ | | ✓ |
| TODO comments in code | | ✓ | ✓ | | |
| Vaayu reviews | ✓ | ✓ | ✓ | ✓ | ✓ |

_(~: GitHub marks comments "outdated" when the code changes, rather than following it.)_

Helix and Zed have nothing comparable. VS Code has comment APIs that extensions use, mostly for PR review.

## what I'd do differently

- I started with one global `comments.json` per project. Moving to one file per named review, with an operation log, was a full rewrite. (Old comments are imported once into a review called "Imported comments".) If I'd thought about two sessions writing at once from the start, I'd have begun with operations.


Next, [part 12](/posts/2026/11/vaayu-part-12-code-tours/): the other direction. Instead of me explaining what's wrong with code, code explaining itself to me.
