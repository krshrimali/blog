---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2027-02-02
linktitle: "Vaayu part 10: git, GitHub, tests and tasks"
title: "Vaayu part 10: git, GitHub, tests and tasks"
categories:
- project
tags:
- vaayu
- rust
- editor
- git
type:
- post
- posts
weight: 10
series:
toc: true
comments: true
draft: true
---

_Part 10 of the [Vaayu series](/posts/2026/11/why-i-wrote-my-own-editor/). This post is a tour of the everyday tools that used to be separate plugins in my Neovim config: git signs and hunks, GitHub PRs and CI, a test runner, project-wide replace, and a personal task tracker. They have one thing in common: they all write to the same Results list from [part 7](/posts/2027/01/vaayu-part-7-splits-floating-terminals-and-one-results-list/)._

None of these is the most exciting thing in Vaayu. But they're what I use every hour, and they show the payoff of "no plugins, one surface" better than any single feature.

## the git gutter

The `+`/`~`/`-` signs next to changed lines. In Neovim, that's gitsigns.nvim.

[`src/gitdiff.rs`](https://github.com/krshrimali/vaayu/blob/master/src/gitdiff.rs) fetches the file's content at `HEAD` once (in the background, via `git show`), then diffs it against the buffer's **current text in memory** with the [`similar`](https://crates.io/crates/similar) crate:

```rust
let diff = similar::TextDiff::from_lines(head, current);
for op in diff.ops() {
    match op {
        similar::DiffOp::Insert { .. }  => /* Sign::Added on the new lines */,
        similar::DiffOp::Replace { .. } => /* Sign::Modified */,
        similar::DiffOp::Delete { .. }  => /* Sign::Removed marker */,
        _ => {}
    }
}
```

Because it diffs in memory, the gutter updates as you type, not on save. The `HEAD` content is cached, and the diff is keyed on the buffer's `edit_seq` ([part 1](/posts/2026/12/vaayu-part-1-text-is-a-tree/)), so it only reruns when the text changed. A new file with no `HEAD` blob is diffed against an empty string, so the whole thing shows as added.

`]c`/`[c` jump between hunks. Staging works on **saved** files: `:gitstage` lists the hunks, and Enter applies one, after checking it still applies to what's on disk. Partial staging against unsaved text is a great way to commit something that never existed, so Vaayu doesn't do it.

There's also `:gitblame`, `:gitdiff`, a git status list, conflict marker navigation and resolution, and `,gp` to copy a GitHub permalink to the current line. And when I want the full power of git, lazygit runs in the floating terminal.

## GitHub, read-first

This replaced gh.nvim, Octo and Guh for me. It's built on the `gh` CLI, and the module's doc comment is the design:

```rust
//! GitHub workspace (read-first), built on the `gh` CLI: PR list, a PR's
//! overview / checkout / diff / review threads, CI checks and their logs,
//! and the issue list. Every view is an ordinary `Results` list (the same
//! choice `:gitstatus` made), each `gh` call runs on a background thread
//! (they all hit the network), and a missing `gh`, a logged-out `gh`, or a
//! project without a GitHub remote each degrade to one clear message
//! rather than a raw stderr dump. Nothing here writes to GitHub; the one
//! local side effect is `gh pr checkout`.
```

Three decisions in there:

1. **`gh`, not the GitHub API directly.** `gh` already handles login, tokens, enterprise hosts and SSO. Vaayu stores no credentials and asks for none.
2. **Read-first.** Browsing PRs, reading review threads, opening a failed CI job's log at the failing line: all read-only. The only write is `:reviewpublish`, which is explicit, previewed, and covered in [part 11](/posts/2027/02/vaayu-part-11-private-code-reviews-that-survive-edits/).
3. **Everything is a Results list.** A PR's changed files, its review threads and its failing checks all use the same keys and the same preview as grep results. A CI failure that mentions `src/foo.rs:42` is a jumpable location.

`,Gp` lists PRs, `,Gv` shows the current branch's PR, `,Gd` its diff, `,Gr` its review threads, `,Gc` its CI checks, `,Gi` issues.

## tests: run, stream, jump

[`src/testrun.rs`](https://github.com/krshrimali/vaayu/blob/master/src/testrun.rs) detects the project's runner (cargo, pytest, `go test`, jest / vitest / `npm test`) and runs the nearest test, the file, the suite, or the last run again (`,Tn` / `,Tf` / `,Ts` / `,Tl`).

- Output streams live into a Results pane while it runs.
- When it finishes, the output is parsed (per runner, with colours turned off and stray ANSI stripped) into a quickfix list of failures, and `✓`/`✗` marks on the test declarations in the gutter.
- The runner gets its own **process group**, so `:teststop` stops it and everything it spawned. Killing only the parent of a `cargo test` would leave the test binaries running.

In my Neovim config this was a small `:test` command in my own utils module. The popular plugin, neotest, is far more capable (it understands test trees, runs in parallel, has a summary window), but I mostly needed "run the thing under my cursor and show me what broke".

## project-wide find and replace

`,sr` (or `:far`) is a reviewed search-and-replace across the project: type the pattern and the replacement, watch a live preview of every affected line, toggle individual matches or whole files off, then press `R` to apply.

Two details that make it safe:

- Before applying, each line is re-checked. If the file changed since the match was found, that match is skipped, not applied to the wrong text.
- Each affected buffer gets **one undo step**. `U` undoes the whole replace. And the edits land in buffers, unsaved, so you can look before writing.


## a personal task tracker

This one isn't a Neovim plugin I had. It's a habit I wanted the editor to support.

`:today` opens today's task list as an editable document. `:ystd`, `:week` and `:on 2026-11-22` go to other days. `,tl` opens a small draft (Priority, Task, Notes) and `:wq` saves it. `:tasklist` browses every entry, highest priority first.

Each day is a TOML file in the user data directory (not in a project, so it follows you across projects):

```toml
version = 1
date = "2026-11-22"

[[entries]]
id = 3
created_at = "2026-11-22T09:14:03+05:30"
kind = "task"
status = "open"
priority = 2
time = "15:00"
text = "Publish part 10"
notes = "Check the CI permalink example"
```

_(An illustrative entry, with the real fields.)_

The interesting engineering is in making a plain text file safe to edit from two places (the day document and the list view) at once:

- **Validation on every write**: the date has to match the file name, IDs must be unique, timestamps and statuses must parse. A bad save is refused, with the reason, instead of writing a file the next load can't read.
- **A file lock and an expected snapshot**: a write takes `tasks.lock`, re-reads the file, and refuses if it changed since you loaded it. Then it writes atomically ([part 1](/posts/2026/12/vaayu-part-1-text-is-a-tree/)). No symlinks, `0600` permissions.
- **Rollover without duplicates**: at startup, open tasks from earlier days move to today. That's two writes to two files, which can't be atomic together. So each moved task carries a `rollover_id`. If the editor dies between the writes, the next rollover sees the ID and finishes the move instead of copying the task twice.

## why one list matters

Here's the thing I didn't appreciate until it was built. A failing test, a CI failure, a grep match, a diagnostic, a review comment and an overdue task are all rows in the same kind of list. I can send any of them to quickfix and walk through them with `]q`. I can filter them the same way. And the AI sidebar ([part 13](/posts/2027/02/vaayu-part-13-an-ai-agent-beside-the-code/)) can be handed any of them as context.

In Neovim, each of these lived in a different plugin's UI, with different keys, and the only thing they shared was quickfix, if the plugin bothered to support it.

## vs Neovim and Helix

- **Neovim**: gitsigns + Neogit + gh.nvim/Octo + grug-far + todo-comments, plus my own test utils. Each one is excellent, and more powerful than Vaayu's version in its own lane. Together they're six UIs.
- **Helix**: a git gutter. Everything else is your terminal.

## what I'd do differently

- I'd have lived with the task tracker as a plain TOML file for a week before building commands around it. It landed on October 5, and the next five commits to it, all within four days, changed how it works: shortcuts, drafts, priorities and notes, rollover, flexible labels. A week of using a plain file would have told me most of that before any of it was code.

Next, the three posts this editor was really built for. Starting with [part 11](/posts/2027/02/vaayu-part-11-private-code-reviews-that-survive-edits/): code reviews.
