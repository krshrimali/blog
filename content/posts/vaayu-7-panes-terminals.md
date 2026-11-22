---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2027-01-12
linktitle: "Vaayu part 7: splits, floating terminals and one results list"
title: "Vaayu part 7: splits, floating terminals and one results list"
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
draft: true
---

_Part 7 of the [Vaayu series](/posts/2026/11/why-i-wrote-my-own-editor/). The core is done: text, keys, frames, background work, code. From here on the series is about everything around the text, starting with how the screen is divided up._

In my Neovim config, the "screen" was a negotiation between plugins: nvim-tree on the left, outline.nvim on the right, Trouble at the bottom, a floating terminal from my own `terminal.lua` on top, the Snacks picker floating on top of _that_. Each one had its own idea of what a window is.

Vaayu has three building blocks instead:

1. a **split tree** for panes,
2. a **float compositor** for things on top,
3. one **Results** list for anything that's "a list of places".

And one thing that lives inside panes: a real terminal.

## the split tree

Windows are a binary tree. A leaf is a pane; a node splits its space between two children:

```rust
pub enum Layout {
    Leaf(usize),
    Split {
        vertical: bool,
        first: Box<Layout>,
        second: Box<Layout>,
        /// Fraction of the split's space given to `first` (0..1).
        ratio: f32,
        /// A pinned side with a fixed size (for sidebars).
        // ...
    },
}
```

`:vsplit` turns a leaf into a vertical `Split` with the old pane as `first` and the new one as `second`. Splitting inside a split gives you the mixed layouts you'd expect (a vertical split whose right side is split horizontally). Closing a pane replaces its parent node with the sibling. Resizing is changing a `ratio`, which is also what dragging a divider with the mouse does.

Each pane has its own cursor, viewport, preview position and zoom, so the same buffer can be open in two panes at different places. The cap is 32 panes, which is more than any terminal can usefully show.

The file tree and the outline are pinned sidebars: a split with a fixed-size side, so resizing the window doesn't squash them. Tabs each keep their own tree. `:mksession` saves the layout (file names, positions, folds), not unsaved text or running processes.

All of the geometry goes through the same `PaneDims` that the renderer uses ([part 3](/posts/2026/12/vaayu-part-3-drawing-a-terminal-frame-in-under-a-millisecond/)), so what's visible and what's painted can't disagree.

## one Results list

Here's the thing my plugin setup could never do. Think about what these have in common:

- LSP diagnostics
- grep matches
- references to a symbol
- failing tests
- git status, a PR's changed files, a CI run's failures
- review comments
- personal tasks

They're all **a list of locations with some text**. So in Vaayu they're all the same type:

```rust
pub struct Entry {
    pub path: Option<PathBuf>,
    pub buffer_id: Option<u64>,
    pub line: usize,
    pub col: usize,
    pub text: String,
    pub detail: String,
    pub note_id: Option<u64>,
    pub action: Option<serde_json::Value>,
    // ...
}
```

and they all open in the same Results view: same keys to move and filter, same preview pane, same `?` for help, `/` to search, `Ctrl-Q` to send to quickfix, `Ctrl-V`/`Ctrl-X` to open in a split.

The `action` field is how a list stays useful after it's exported. A task row in quickfix still knows it's a task, so you can mark it done from there. A review comment still knows which comment it is.

In Neovim this was Trouble + quickfix + nvim-bqf + the picker's own results, four lists with four sets of keys. The individual plugins are each better at their one job than Vaayu's list is at that job. But having _one_ list is worth more to me than having the best of four.

## a real terminal in a pane

`:terminal` opens your shell in a split. Under the hood ([`src/pty.rs`](https://github.com/krshrimali/vaayu/blob/master/src/pty.rs)):

- [`portable-pty`](https://crates.io/crates/portable-pty) creates a pseudo-terminal and starts the shell in it,
- a **reader thread** reads its output and feeds it to a [`vt100`](https://crates.io/crates/vt100) parser, which keeps a virtual screen of cells,
- the renderer draws that screen into the pane like any other content.

The editor is now a terminal emulator inside a terminal emulator. Which brings us to my favourite bug.

### the shell that never showed a prompt

My shell is fish. In the first version, opening `:terminal` showed... nothing. A blank pane, forever.

Interactive shells (fish especially) **ask the terminal questions** when they start: "what kind of terminal are you?" (`ESC [ c`), "where is the cursor?" (`ESC [ 6 n`), "what's your background colour?" (`ESC ] 11 ; ?`), "do you support the kitty keyboard protocol?" (`ESC [ ? u`). A real terminal answers. `vt100` is a parser, not a terminal; it doesn't answer anything. So fish sat there waiting for a reply that would never come.

The fix is to answer the questions the embedded terminal is asked:

```rust
/// Answers the terminal capability probes emitted by interactive shells such
/// as fish. The embedded VT screen parses terminal output but is not an outer
/// terminal, so without these replies shells can wait for a response that
/// never arrives before showing their first prompt.
fn terminal_query_replies(pending: &mut Vec<u8>) -> Vec<Vec<u8>> {
    // ...
    if rest.starts_with(b"\x1b[0c") || rest.starts_with(b"\x1b[c") {
        replies.push(b"\x1b[?1;2c".to_vec());        // "I'm a VT100 with AVO"
    } else if rest.starts_with(b"\x1b[6n") {
        replies.push(b"\x1b[1;1R".to_vec());         // cursor position
    } else if rest.starts_with(b"\x1b[?u") {
        replies.push(b"\x1b[?0u".to_vec());          // no kitty keyboard flags
    } else if rest.starts_with(b"\x1b[>0q") {
        replies.push(b"\x1bP>|vaayu 0.1.0\x1b\\".to_vec()); // terminal name/version
    } else if rest.starts_with(b"\x1b]11;?") {
        replies.push(b"\x1b]11;rgb:2020/2020/2020\x1b\\".to_vec()); // background
    }
    // ...
}
```

One subtle part: a probe can arrive split across two reads (`ESC [` in one chunk, `6n` in the next). So partial probes stay in `pending` until they're complete, and there's a test for exactly that.

### scrolling, copying, and getting keys through

A terminal pane has Normal mode like any other pane. `Esc` leaves Terminal input mode, and then `j`/`k`, `Ctrl-U`/`Ctrl-D`, `gg`/`G` and the mouse wheel scroll its history (5,000 lines, capped so a runaway `yes` can't eat your memory). `/`, `v` or `y` open the whole output in a buffer, so you can search and yank it with the usual keys. Programs that ask for mouse reports get the mouse; full-screen programs get arrow keys.

And since `Esc` and `Ctrl-W` mean something to the editor, `Ctrl-\` sends the next key to the program literally.

## the floating terminal

`Ctrl-\` in Normal mode opens a floating shell on top of everything. Press it again and it hides, but the **process keeps running**. Press it again and you're back where you were, with your half-typed command still there. `Esc` or `Ctrl-Q` actually closes it and stops the shell.

That "hide but keep alive" is the whole feature, and it's why I had a custom `terminal.lua` in my Neovim config. lazygit uses the same float. So do tool installers. The float compositor draws on top of the pane rows, and because everything goes through the same row diff, closing a float repaints exactly the rows it covered.

AI agents ([part 13](/posts/2027/02/vaayu-part-13-an-ai-agent-beside-the-code/)) use the same PTY machinery in a right-hand sidebar, with their own detach/reattach behaviour.

## vs Neovim and Helix

- **Neovim** has excellent built-in terminals (`:terminal`, using libvterm, which _does_ answer probes) and window management. What it doesn't have is a single list or a single float model. Those come from plugins, and plugins don't coordinate.
- **Helix** has splits, but no embedded terminal at all, by design. You use your terminal multiplexer.

Which raises the fair question: why not just use tmux? I do use tmux. But a terminal _inside_ the editor can share things a separate pane can't: the editor can send a selection to it, capture its output into a buffer, and (for agents) paste structured context into it.

## what I'd do differently

- Results was shared from the first day, and that paid off everywhere. But the fuzzy picker is still a separate list type, and it shows: when I made list navigation behave like Vim, the same fix had to be written twice, 90 lines in `picker.rs` and 20 in `results.rs`. I'd make the picker a Results list with a query bar on top.

Next, [part 8](/posts/2027/01/vaayu-part-8-pictures-in-a-terminal/): putting real images in a terminal without breaking any of the above.
