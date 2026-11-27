---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2026-11-27
linktitle: "Vaayu part 14: 10 weeks, 87k lines, 292 commits"
title: "Vaayu part 14: 10 weeks, 87k lines, 292 commits"
categories:
- project
tags:
- vaayu
- rust
- editor
- ai
- retrospective
type:
- post
- posts
weight: 10
series:
toc: true
comments: true
---

_The last part of the [Vaayu series](/posts/2026/11/why-i-wrote-my-own-editor/). Thirteen posts on what Vaayu does and how. This one is about how it got built: the timeline, working with Claude as a pair programmer for most of it, how testing kept that honest, and what's still missing._

## the numbers

| | |
| --- | --- |
| First commit | 2026-09-15 |
| This post's snapshot | 2026-11-22 |
| Commits | 292 |
| Commits co-authored with Claude | 108 (93 with Sonnet 5, 14 with Opus 5.5 including one squash merge of 28 co-authored commits, 1 with an unversioned "Claude" trailer) |
| Lines of Rust | ~87,000 |
| Rust `#[test]`s | 1,012 |
| PTY-driven UI test scripts | ~230 Python files |
| Largest source file | `regression.rs`, 13,000 lines of regression tests |
| Largest feature file | `render.rs`, 6,100 lines |

{{< vaayu-svg "commits-per-week.svg" >}}

Most of the commits are from the first two weeks: 98 in the week of September 14 and 135 in the next one, including 103 in a single day (September 23). After that, the work changed shape: fewer, much larger commits, each one a whole feature with its own audit (the browser editor, the review rework, the tour UX pass).

## day one

The first commit was called **"Implement Anvil M0+M1: Vim-grammar modal editor core in Rust"**. (Anvil was the working name. It became Vaayu the same day.) It already had a rope buffer, a crossterm renderer, the operator + motion grammar, text objects, registers, macros, dot-repeat, `:s`, and my own Neovim leader bindings, including `jk` to escape with a real timeout.

It also said, honestly, what it didn't have:

> LSP, tree-sitter, fuzzy picker, git integration, and the SSH-latency prediction layer from the design doc are not implemented -- see README.md Status section.

By the end of that day, it had a fuzzy picker, tree-sitter for ten languages, completion, a git gutter, an LSP client and a Markdown preview. And then an audit found 45 real issues, including two crashes and a control-sequence injection, and the rest of the day went into fixing them ([part 1](/posts/2026/11/vaayu-part-1-text-is-a-tree/) and [part 3](/posts/2026/11/vaayu-part-3-drawing-a-terminal-frame-in-under-a-millisecond/) tell some of those stories).

That rhythm (build fast, then audit hard) is the real story of this project.

## working with Claude

I'll be direct about this, since the commit log is: 108 of Vaayu's 292 commits carry a Claude co-author trailer, and those include most of the big ones, starting with the very first. (One of them is the squash merge of the feature roadmap, which on its own folds in 28 co-authored commits, so by work done the share is higher than 108 / 292 suggests.)

The setup was simple: Claude Code in a terminal, with me steering. Claude wrote most of the code. I wrote the specs (the parity plan, the milestones, what "done" meant for each feature), decided what to build next, read the diffs, ran the editor, and sent things back when they were wrong. The commits without a trailer are the ones where the history doesn't record it, not a clean line between "mine" and "Claude's"; most of the work went through that same loop.

The job, it turned out, wasn't typing code. It was knowing exactly what I wanted, and being able to tell quickly whether I'd got it.

What worked, judging from the history:

- **A written spec.** My Neovim config, turned into the [parity plan](https://github.com/krshrimali/vaayu/blob/master/NEOVIM_PARITY_PLAN.md), gave every task a clear definition of done: the same task, the same keys, the same feedback. Vague asks produce vague code.
- **Milestones with names.** M0, M1, then numbered roadmap items (2.6, 2.7, 6.x...) that each commit refers to.
- **Every claim checked against something real.** A commit message that says "fixed" also says how it was verified: reproduced before, gone after, raw terminal output inspected.
- **Audits as a separate step.** Not "write code and tests together and call it done", but a separate pass whose only job is to find what's wrong, with evidence.

What went wrong, also from the history:

- **The design doc said "damage-tracked rendering", and it wasn't built.** The first renderer cleared and repainted the screen on every key. Nobody noticed until I measured ([part 3](/posts/2026/11/vaayu-part-3-drawing-a-terminal-frame-in-under-a-millisecond/)). A model will happily describe the architecture you asked for while building something simpler. So will a person, to be fair. Measure.
- **Confident numbers from the wrong build.** The first benchmark compared a debug build to Neovim and concluded Vaayu was several times slower ([part 6](/posts/2026/11/vaayu-part-6-benchmarking-editors-honestly/)).
- **Fixes that create bugs.** The span-rebuild throttle fixed typing latency and broke "colours catch up after you stop typing" ([part 5](/posts/2026/11/vaayu-part-5-incremental-tree-sitter-and-an-lsp-client-from-scratch/)). Another fix (bump `edit_seq` on every key) made an O(file) walk run on every keystroke.
- **Features that are fine alone and broken together.** The tour UX audit found ten problems that every individual test had missed ([part 12](/posts/2026/11/vaayu-part-12-code-tours/)).

None of these are AI-specific. They're what happens when a lot of code is written fast. What _is_ different is the speed: you hit all of them in days instead of months, so the safety nets have to be there from the start.

## the safety nets

### 1. tests in Vim notation

Unit tests feed keys the way you'd type them and check text and cursor ([part 2](/posts/2026/11/vaayu-part-2-teaching-rust-to-speak-vim/)). They're cheap enough that every bug fix gets one. `regression.rs` is 13,000 lines because every audit finding became a test.

### 2. reference data from real Vim

For the parts where "like Vim" is subtle (`%`, Visual block paste), behaviour was recorded from Vim itself and replayed against Vaayu. A model's (or my) memory of what Vim does is not a spec. Vim is.

### 3. the real binary, in a real PTY

About 230 Python scripts start the release binary in a pseudo-terminal, type at it, and read the screen back, at several terminal sizes. They're slow, and they catch what unit tests can't: focus bugs, layout at 40×12, a shell that never shows its prompt. CI runs the tour suites against both binary names (`vaayu` and `vy`).

### 4. audits with evidence

The repo has a whole shelf of them: `AUDIT.md`, `UI_AUDIT_2026-10-09.md` (1,000 recorded UI operations), a second round the same day, `2026-10-10`, `2026-10-11`, the tour UX plan. Each one records what was tested, the raw evidence (terminal captures, archives with SHA-256 hashes), what was found, and what was fixed. When a finding is a compatibility limit rather than a bug, it says so.

### 5. benchmarks you can rerun

Every number in this series is in [`BENCHMARKS.md`](https://github.com/krshrimali/vaayu/blob/master/BENCHMARKS.md) with its date, machine, binary hashes and raw samples, including the historical numbers that turned out to be measured wrong, marked as such.

## what's missing

First, the good news: Vaayu is my daily editor now. Neovim is retired.

It's only honest to list what Vaayu isn't:

- **No debugger.** DAP (the Debug Adapter Protocol) isn't implemented.
- **No plugin host.** You can't extend it without writing Rust. This was a deliberate choice ([part 0](/posts/2026/11/why-i-wrote-my-own-editor/)), and it's also the biggest reason it isn't for everyone.
- **Memory.** 63 MiB idle, vs bare Neovim's ~10 MiB.
- **Full Vim compatibility.** No Vimscript, so no `.vimrc`. Parity is measured against my workflow and recorded Vim behaviour, not all of Vim.
- **GitHub writes** beyond publishing a review. It's read-first on purpose, but merging a PR from the editor would be nice.
- **Remote editing** (`ssh://` open/save, remote grep) is on the roadmap, not in the editor.
- **Platforms.** I've run it on Linux, macOS and Windows, but CI only tests Linux (Ubuntu), so Linux is the only one with a safety net.
- **The comparison that matters most**: Vaayu vs Neovim _with my real config_. I haven't benchmarked that fairly yet.

## would I recommend writing your own editor?

Yes, if you want to understand editors. You'll learn more in a month of building one than in years of configuring one: ropes, terminal escape codes, LSP's UTF-16 columns, why Vim's `.` replays keys.

No, if what you want is a better editor for your team. Contribute to Neovim or Helix instead; they have decades of edge cases you'd be rediscovering.

And an AI pair makes the "yes" much cheaper than it used to be, but only if you build the safety nets first. Without the tests, the reference data, the PTY captures and the audits, I'd have had 87,000 lines of code that looked right.

## try it

```bash
git clone https://github.com/krshrimali/vaayu && cd vaayu
cargo install --path . --locked
vy src/main.rs        # in a terminal
vy --web src/main.rs  # in a browser tab
```

`:help` has every key. `:tour visuals` (after copying `examples/visuals.tour` into `.tours/`) walks through the code from part 1.

Thanks for reading all fourteen parts. If you made it this far, you deserve an editor that starts in 7 ms :)

<!-- Series index: link back to every part here before publishing, or point to /tags/vaayu/. -->
