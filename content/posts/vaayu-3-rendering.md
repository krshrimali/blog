---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2026-12-15
linktitle: "Vaayu part 3: drawing a terminal frame in under a millisecond"
title: "Vaayu part 3: drawing a terminal frame in under a millisecond"
categories:
- project
tags:
- vaayu
- rust
- editor
- tui
- performance
type:
- post
- posts
weight: 10
series:
toc: true
comments: true
draft: true
---

_Part 3 of the [Vaayu series](/posts/2026/11/why-i-wrote-my-own-editor/). We have text ([part 1](/posts/2026/12/vaayu-part-1-text-is-a-tree/)) and a way to change it ([part 2](/posts/2026/12/vaayu-part-2-teaching-rust-to-speak-vim/)). Now it has to get onto the screen, roughly 60 times faster than you can blink._

This post starts with an embarrassing story, because it's the most useful thing I learned building Vaayu.

## the design doc said "damage tracking"

The very first design doc for Vaayu listed one key differentiator for speed: **damage-tracked rendering**. Only redraw what changed. Every serious terminal app does it.

On day one I wrote a latency benchmark (a PTY that sends keys and times the editor's output), ran it against bare Neovim, and Vaayu was slower. The first thing I found was embarrassing in a different way: that comparison used Vaayu's **debug** build, which is ~29× slower than release on the same cursor move (6.6 ms vs 0.23 ms). Always benchmark the release binary.

But even in release, there was real waste. I added opt-in per-frame stage timing (`VAAYU_PROFILE=path`) and looked at the raw bytes going to the terminal. On a plain `j`, Vaayu was clearing the screen and redrawing **every cell**. The damage tracking the design doc promised had never actually been built. `draw()` cleared and repainted the whole terminal on every keystroke.

Two lessons I keep coming back to:

1. A design doc is a wish, not a fact. Measure the thing you shipped.
2. Look at the bytes. A latency number tells you _that_ something is slow. The byte stream tells you _what_.

## the pipeline

Here's what happens between a keypress and the terminal today:

```text
 key ──► dispatch ──► editor state changes
                           │
                           ▼
              PaneDims: geometry for each pane
          (gutter, minimap, winbar, wrap width...)
                           │
                           ▼
         layout: which buffer lines are visible,
              and where each one wraps
                           │
                           ▼
       compose: each screen row into styled bytes
         (cached by what the row *is*, not where)
                           │
                           ▼
        diff: compare against what's on screen ──► write only the changed rows
```

Let's go through the interesting parts.

## FrameCache: remember what you wrote

The fix for the full repaint was a `FrameCache`. Each frame builds every row into a byte buffer, compares it with what was written to that row last frame, and only writes the rows that changed:

```rust
for (y, row) in frame.iter().enumerate() {
    if cache.rows.get(y) != Some(row) {
        queue!(
            out,
            MoveTo(0, y as u16),
            ResetColor,
            SetAttribute(Attribute::Reset)
        )?;
        out.write_all(row)?;
        // ...
    }
}
```

Building rows in memory is cheap. Talking to the terminal is not: every byte has to be written to the PTY, parsed by the emulator and painted. After this change, a `3j` on a 100×40 screen went from repainting all ~4,000 cells to touching **4 rows and 358 bytes**. I checked that by reading the raw output stream, not by trusting the timer.

## compose by identity, not by position

The row diff is about _output_. There's a second cache for _work_.

Building a row isn't free: syntax colours, selection, search matches, diagnostics, git signs, wide characters, tabs. When you scroll down by one line, 39 of the 40 rows show exactly the same content as before, just one row higher. Comparing by screen position, every row "changed".

So composed rows are also cached by **what they are**:

```rust
struct RowSignature {
    buffer: u64,
    /// Identity of the immutable glyph vector for this exact rendered line.
    content: u64,
    syntax: u64,
    line: usize,
    start: usize,      // which wrapped segment of the line
    width: usize,
    gutter: usize,
    current: bool,
    cursorline: bool,
    // ...
}
```

If a row's signature is in the cache, its styled bytes are reused, wherever it ends up on screen. A one-line edit only invalidates the row that changed, because the other lines keep their glyph vectors (and their `content` identity) even though the buffer's global revision moved.

## scrolling: let the terminal move the rows

Even with cached rows, a scroll still _writes_ every row, because each one moved. But terminals have known how to scroll a region for decades. So when the new viewport is the old one shifted up or down, Vaayu asks the terminal to do it:

```rust
fn emit_scroll<W: Write>(out: &mut W, body: usize, shift: isize) -> io::Result<()> {
    let amount = shift.unsigned_abs();
    write!(
        out,
        "\x1b[1;{}r\x1b[1;1H\x1b[{}{}\x1b[r",
        body,
        amount,
        if shift > 0 { 'M' } else { 'L' }
    )?;
    out.flush()
}
```

In English: set the scroll region to the editor body (`DECSTBM`, `ESC [ 1 ; N r`) so the status line doesn't move, delete or insert lines at the top, then reset the region. The terminal shifts pixels it already has. Then the normal row diff repaints only the newly exposed rows.

The hard part isn't the escape sequence. It's knowing when it's **safe**. The fast path is skipped whenever something on screen doesn't scroll with the text:

```rust
// trimmed: the real check has a few more conditions (winbar, split layout, ...)
let scroll_eligible = cache.dims == (cols, rows)
    && matches!(ed.mode, Mode::Normal)
    && ed.completion.is_none()
    && !ed.config.relativenumber
    && ed.windows.len() <= 1
    // The DECSTBM trick hardcodes row 1 as the first content row; a
    // tabline moves content down by one, so skip it with more than one tab.
    && ed.tabs.len() <= 1
    && !ed.config.sticky_scroll
    && !ed.config.minimap
    && ed.active_tour.is_none()
    && ed.float.is_none()
    && !ed.buf().folds.iter().any(|f| f.closed);
```

Each of those conditions is a bug I either hit or was afraid of: a sticky header that scrolled away with the text, relative line numbers that are all different after a scroll, a floating window that got dragged along. When any of them is on, Vaayu falls back to the plain row diff, which is always correct, just a little more output.

## finding a line's colours: O(n) → O(log n)

The second fix from that first profiling session. To colour a row, the renderer needs the syntax spans on that line. Spans were a sorted list, and the lookup scanned it **from the start, once per visible row, every frame**. On a big file, that's every span in the file × 40 rows × every frame.

Because spans are sorted by start, the fix is a binary search to the first span that could touch the line, bounded by the longest span in the file. A lookup is now O(log n + k), where k is the number of spans actually on the line.

It barely moved the numbers. The real cost was somewhere else, and finding it needed instrumentation _inside_ the row loop. That story (an 8 ms re-walk of the whole syntax tree on every keystroke) is in [part 5](/posts/2026/12/vaayu-part-5-incremental-tree-sitter-and-an-lsp-client-from-scratch/).

## one geometry, used twice

A sneaky source of bugs in TUIs: the code that decides _what's visible_ (scrolling the viewport so the cursor stays on screen) and the code that _paints_ compute the pane's size separately. Add a minimap or a winbar, forget one of them, and the cursor goes off the bottom of the pane.

In Vaayu both go through `PaneDims`, one struct that knows the gutter width, minimap, winbar, zen mode and global statusline. Viewport and paint read the same numbers, so they can't disagree.

## never trust a byte from a file

Also from the first-day audit: file contents containing a raw `ESC` (or any other control byte) were written straight to the terminal. Open a crafted file, and it could move the cursor or clear the screen. Now every control character is replaced one-for-one with a visible `�` at render time (one for one, so syntax spans computed on the original text still line up). An editor's output is a terminal program; anything in a file is untrusted input to it.

## how fast is it now?

On a 50,000-line file in a 100×40 PTY, median time from key to the editor's first output byte ([part 6](/posts/2027/01/vaayu-part-6-benchmarking-editors-honestly/) has the method and every caveat):

| Operation | Vaayu | Neovim (`-u NONE`) | Helix |
| --- | ---: | ---: | ---: |
| Cursor down | 1.00 ms | **0.50 ms** | 3.18 ms |
| Page scroll | 0.65 ms | **0.48 ms** | 3.17 ms |
| Insert a character | **0.79 ms** | 0.89 ms | 177 ms |

Notice that bare Neovim still wins on cursor movement. Its renderer is decades older than mine and very good: Neovim keeps a grid of cells and sends a diff over its UI protocol, so the terminal UI only ever writes what changed, at cell level. Helix uses a double-buffered cell grid and diffs cells too (the same idea as `ratatui`). Vaayu diffs **rows** and caches composition by identity, which writes a bit more on a one-cell change but makes the scroll and cache logic much simpler.

All three are well under a frame (16.7 ms at 60 Hz). Once you're there, the next limit is the terminal emulator, not the editor.

One honest caveat: these numbers measure when the first byte leaves the editor, not when your terminal finishes painting. A slow terminal emulator can add more than the editor does.

## what I'd do differently

- Write the benchmark before the renderer. If I'd measured on day one, the missing damage tracking would have been caught in an hour, not after a dozen features had been built on top.
- Treat every fast path as an optimization over a slow path that's always correct, and keep the list of "when not to take it" in one place. The scroll eligibility check is ugly, but it's ugly in one spot.

Here's what the terminal receives today, captured from the release binary in a PTY at 100×40 (escape sequences shown as text, long runs of padding trimmed). A `3j` from the top of `render.rs` rewrites three rows: the old cursor line, the new one, and the statusline. That's 541 bytes, a little more than the historical 358 because the statusline now carries more:

```text
\x1b[1;1H\x1b[K ... //! Cell-aware pane composition with cached terminal rows.
\x1b[4;1H\x1b[K ...     editor::Editor,
\x1b[39;1H\x1b[K ... NORMAL src/render.rs ... 4:1
\x1b[4;3H\x1b[2 q\x1b[?25h
```

And this is one line of scrolling (`Ctrl-E`), 190 bytes: set a scroll region, delete a line at the top so the terminal shifts the rest up itself, reset the region, then draw only the one new row at the bottom.

```text
\x1b[1;38r\x1b[1;1H\x1b[1M\x1b[r          <- the terminal moves 37 rows
\x1b[38;1H\x1b[K ...  1020         a == b <- Vaayu draws 1
```

Next, [part 4](/posts/2026/12/vaayu-part-4-never-block-a-keystroke/): what to do with work that can't fit in a frame.
