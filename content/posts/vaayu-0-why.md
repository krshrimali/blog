---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2026-11-27
linktitle: "Why I wrote my own editor"
title: "Why I wrote my own editor"
categories:
- project
tags:
- vaayu
- rust
- editor
- tui
type:
- post
- posts
weight: 10
series:
toc: true
comments: true
---

_This is the first post in a series on **Vaayu**, a modal terminal editor I wrote in Rust. This one is the "why". The rest are the "how", and there are a lot of them. The full list is at the [end of this post](#the-series)._

I've used Neovim for years. My config grew the way everyone's does: a plugin for the file tree, one for fuzzy finding, one for git signs, one for the git UI, one for GitHub PRs, one for diagnostics in a list, one for terminals, one for the AI sidebar, one for code tours, one for... you get the idea. About forty of them, in the end.

None of these plugins are bad. Many are brilliant. But they don't know about each other. Trouble has a list, quickfix has a list, bqf makes quickfix look like a different list, the Snacks picker has its own list. Each has its own keys, its own idea of "preview" and its own way of being slow. And every time I updated one of them, I held my breath a little.

Then I tried Helix. It's fast, it ships with LSP and tree-sitter built in, and there's very little to configure. But it isn't Vim. Helix selects first and acts second (the Kakoune model), and years of `ci(` and `dap` in my fingers didn't want to relearn. It also doesn't have the things I spend half my day in: a git UI, a terminal, an AI agent beside the code, a way to leave myself review notes.

So I wanted the obvious thing:

> An editor that is feature complete with respect to my Neovim config (every third-party plugin, AI, GitHub support and more), and fast, like Helix.

That's Vaayu (वायु, "air"). You run it as `vaayu` or `vy`.

![Vaayu in a terminal: ,ff fuzzy-finds render.rs, ,kv opens a split, Ctrl-\ shows a floating shell running git log, and :tours starts a code tour](/assets/blogs/vaayu/overview.gif)

_Vaayu on its own source: fuzzy find, a split, the floating terminal, and a code tour._

## my config was the spec

The first decision turned out to matter the most: **I didn't design features, I copied my workflow.** My Neovim config became the requirements document. `plugins.lua`, `keymaps.lua`, the which-key file, the LSP setup: if it was active in my config, it went into a [parity plan](https://github.com/krshrimali/vaayu/blob/master/NEOVIM_PARITY_PLAN.md). If it only showed up in `lazy-lock.json` and nothing used it, it didn't count.

Parity here means something specific:

> The same editing task can be completed with equivalent navigation, feedback, safety, and keymap access. It does not require a Lua host, Neovim plugin API compatibility, identical floating-window geometry, or copying plugin implementation details.

That definition did a lot of work. It meant I didn't have to build Neovim. I had to build _my_ Neovim.

## why there is no plugin host

This is the decision people ask about first, so let me get it out of the way.

Vaayu has no Lua, no plugin API, nothing to install. Everything is in the binary. That sounds like a limitation (and it is one, I'll come back to that), but it's also the point. When there are no plugins, overlapping plugins can become **one feature**:

| In my Neovim config | In Vaayu |
| --- | --- |
| Trouble, quickfix, nvim-bqf, Snacks picker / fzf-lua results | one Results engine ([part 7](/posts/2026/11/vaayu-part-7-splits-floating-terminals-and-one-results-list/)) |
| gitsigns, Neogit, lazygit | git gutter, hunk actions, git workspace, lazygit in a float ([part 10](/posts/2026/11/vaayu-part-10-git-github-tests-and-tasks/)) |
| gh.nvim, Octo, Guh | one GitHub workspace on top of `gh` |
| review.nvim (commented out, but I wanted it) | private reviews that survive edits ([part 11](/posts/2026/11/vaayu-part-11-private-code-reviews-that-survive-edits/)) |
| codetours.nvim | code tours with visuals and AI authoring ([part 12](/posts/2026/11/vaayu-part-12-code-tours/)) |
| Sidekick, promptbank.nvim, Copilot | `:ai`, an agent CLI in a sidebar ([part 13](/posts/2026/11/vaayu-part-13-an-ai-agent-beside-the-code/)) |
| image.nvim | Markdown + Mermaid previews in the terminal ([part 8](/posts/2026/11/vaayu-part-8-pictures-in-a-terminal/)) |
| my own `terminal.lua` | split and floating terminals |
| grug-far | reviewed project-wide find and replace |
| nvim-treesitter, lspconfig, mason, blink.cmp, fidget | built in ([part 5](/posts/2026/11/vaayu-part-5-incremental-tree-sitter-and-an-lsp-client-from-scratch/)) |

A diagnostic, a grep match, a failing test, a review comment and a GitHub CI failure are all "a location with some text". In Vaayu they all go through the same list, with the same keys, the same preview, and the same `Ctrl-Q` to send them to quickfix. That's the thing a plugin ecosystem can't easily give you, because no plugin owns the whole picture.

The cost is real: you can't add your own feature without writing Rust and rebuilding. I'm fine with that for now, because the person I'm building for is me. But I'll be honest about it whenever I compare Vaayu to Neovim in this series.

## where it stands against Neovim and Helix

I'll go deep on benchmarks in [part 6](/posts/2026/11/vaayu-part-6-benchmarking-editors-honestly/), including where Vaayu loses. Here's the short version, from a 50,000-line Rust file in a 100×40 PTY, time to the editor's first output byte (median of three runs):

| | Vaayu | Neovim (`-u NONE`) | Helix |
| --- | ---: | ---: | ---: |
| Startup | 7.2 ms | 9.2 ms | 398 ms |
| Insert a character | 0.79 ms | 0.89 ms | 177 ms |
| Cursor down | 1.00 ms | **0.50 ms** | 3.18 ms |
| Idle memory | 63 MiB | **9.6 MiB** | 121 MiB |

Bare Neovim is still faster at moving the cursor and uses a fraction of the memory. But that's Neovim with no config at all, which nobody actually uses. My point isn't "Vaayu beats Neovim". It's that you can have _all of my plugins_ worth of features and still stay in the same latency class as bare Neovim.

## what's in it

Vaayu today, roughly 87,000 lines of Rust:

- Vim's grammar: operators, motions, text objects, registers, macros, dot-repeat, Visual block, Vim regex
- tree-sitter highlighting for 16 languages, an LSP client written from scratch, semantic tokens
- splits, tabs, sessions, a file tree, an outline, a minimap
- a fuzzy picker and live grep that never block a keystroke
- embedded terminals, a floating terminal, lazygit
- git and GitHub, a test runner, a personal task tracker
- private review comments, code tours, an AI agent sidebar
- Markdown previews with real images and Mermaid diagrams, inside the terminal
- the same editor in a browser tab with `vaayu --web`

## the series

The series is grouped in six parts. You can read the core (parts 1–5) as a small course on how editors work, or jump straight to the workflows (parts 11–13) if you care about working with AI agents.

**The core: text, keys, pixels, never blocking**

1. [Text is a tree: ropes, edit logs, and saving without losing data](/posts/2026/11/vaayu-part-1-text-is-a-tree/)
2. [Teaching Rust to speak Vim](/posts/2026/11/vaayu-part-2-teaching-rust-to-speak-vim/)
3. [Drawing a terminal frame in under a millisecond](/posts/2026/11/vaayu-part-3-drawing-a-terminal-frame-in-under-a-millisecond/)
4. [Never block a keystroke](/posts/2026/11/vaayu-part-4-never-block-a-keystroke/)

**Understanding code, and proving it's fast**

5. [Incremental tree-sitter and an LSP client from scratch](/posts/2026/11/vaayu-part-5-incremental-tree-sitter-and-an-lsp-client-from-scratch/)
6. [Benchmarking editors honestly](/posts/2026/11/vaayu-part-6-benchmarking-editors-honestly/)

**Beyond text: what used to be plugins**

7. [Splits, floating terminals and one Results list](/posts/2026/11/vaayu-part-7-splits-floating-terminals-and-one-results-list/)
8. [Pictures in a terminal](/posts/2026/11/vaayu-part-8-pictures-in-a-terminal/)
9. [The same editor in a browser tab](/posts/2026/11/vaayu-part-9-the-same-editor-in-a-browser-tab/)
10. [Git, GitHub, tests and tasks](/posts/2026/11/vaayu-part-10-git-github-tests-and-tasks/)

**The workflows I built it for**

11. [Private code reviews that survive edits](/posts/2026/11/vaayu-part-11-private-code-reviews-that-survive-edits/)
12. [Code tours](/posts/2026/11/vaayu-part-12-code-tours/)
13. [An AI agent beside the code](/posts/2026/11/vaayu-part-13-an-ai-agent-beside-the-code/)

**Building it**

14. [10 weeks, 87k lines, 292 commits](/posts/2026/11/vaayu-part-14-10-weeks-87k-lines-292-commits/)

If you want to try it:

```bash
git clone https://github.com/krshrimali/vaayu && cd vaayu
cargo install --path . --locked
vy src/main.rs
```

See you in part 1. Happy reading! :)
