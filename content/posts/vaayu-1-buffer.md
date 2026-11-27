---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2026-11-27T01:00:00+05:30
linktitle: "Vaayu part 1: text is a tree"
title: "Vaayu part 1: text is a tree"
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

_Part 1 of the [Vaayu series](/posts/2026/11/why-i-wrote-my-own-editor/). This one is about the data model every other feature hangs off: how the text is stored, how the rest of the editor finds out it changed, and how it gets back to disk without eating your file._

Every editor feature, from syntax highlighting to review comments, eventually asks one of three questions about the text:

1. what is on line N?
2. did anything change since I last looked?
3. where did my line go after that change?

So let's start with the struct that answers them.

## the buffer

Here's a trimmed `Buffer` from [`src/buffer.rs`](https://github.com/krshrimali/vaayu/blob/master/src/buffer.rs):

```rust
pub struct Buffer {
    pub id: u64,
    pub rope: Rope,
    pub path: Option<PathBuf>,
    pub cursor_line: usize,
    pub cursor_col: usize,
    /// Bumped on every content-changing operation, *including* undo/redo --
    /// this is a content revision, not just an "edited since load" flag, so
    /// syntax/git/LSP staleness checks (which key off it) see undo/redo too.
    pub edit_seq: u64,
    /// A snapshot of the rope as of the last load/save. `is_modified()`
    /// compares *content*, not a revision number, against this.
    saved_snapshot: Rope,
    undo_stack: Vec<UndoState>,
    redo_stack: Vec<UndoState>,
    pending_undo: Option<UndoState>,
    /// Line-count changes `(edit_line, delta)` since the editor last drained them.
    pending_line_shifts: Vec<(usize, i64)>,
    // ... encoding, BOM, line endings, folds, disk state
}
```

Four ideas are packed in here: a rope, a revision number, a line-shift log, and a saved snapshot. Let's take them one at a time.

## why a rope

The naive way to store a file is a `String`. Inserting a character in the middle of a 5 MB string means shifting everything after it. Do that on every keystroke and you'll feel it.

The other classic is a `Vec<String>`, one per line, which is roughly what Vim does with its memline (plus a swap file). Inserting a character only touches one line. But inserting a newline shifts every line after it, and "give me character 2,000,000" means walking lines.

A **rope** is a balanced tree whose leaves are small chunks of text. Each internal node remembers how many bytes, chars and line breaks are below it. So "which chunk holds character N?" and "where does line N start?" are both a walk down the tree, O(log n). Inserting means editing one leaf and fixing up the counts on the way back to the root.

{{< vaayu-svg "rope.svg" >}}

Vaayu uses [`ropey`](https://github.com/cessen/ropey). Here's what inserting a character actually does:

```rust
pub fn insert_char(&mut self, line: usize, col: usize, ch: char) {
    let idx = self.char_idx(line, col);
    let edit_line = (ch == '\n').then(|| self.rope.char_to_line(idx));
    self.rope.insert_char(idx, ch);
    self.edit_seq += 1;
    self.log_edit(idx, 0, 1);
    if let Some(l) = edit_line {
        self.record_line_shift(l, 1);
    }
}
```

The rope insert is one line. The other four lines are what make the rest of the editor work.

A rope is not magic, though. Anything that needs the whole document (saving, handing the text to a language server, a full re-parse) still visits every byte. It just stops _editing_ from being the expensive part.

> **A note on comparisons.** Helix also uses ropey. So when Vaayu inserts a character in 0.79 ms on a 50,000-line file and Helix takes 177 ms ([part 6](/posts/2026/11/vaayu-part-6-benchmarking-editors-honestly/)), the rope is _not_ the reason. Both editors have the same data structure. The difference is in what happens after the insert. I'll get to that in parts 3 and 5. VS Code uses a piece table, which is another good answer to the same problem.

## edit_seq: the cheapest cache key there is

Every content change bumps `edit_seq`. That includes undo and redo, and every keystroke in Insert mode. That matters more than it sounds, and I learned it the hard way on day one.

The first version only bumped `edit_seq` when you left Insert mode, and undo/redo didn't bump it at all. An audit found what that led to: type a multibyte character (say `é`) in the middle of Insert mode, and the syntax highlighter would pair the _new_ line text with the _old_ parse tree, slice a string in the middle of a UTF-8 character and abort the process. Undo had a quieter version of the same bug: the highlighter, git gutter and LSP all believed nothing had changed.

The fix was to make the rule boring: **every mutation bumps it**, regardless of how undo groups the edits.

Now every cache in the editor can be keyed by `(buffer.id, buffer.edit_seq)`. Semantic tokens, for example:

```rust
// Semantic tokens: request once per (buffer, edit_seq) when enabled.
let cur = (self.buf().id, self.buf().edit_seq);
```

If a background job comes back with results for revision 41 and the buffer is at 43, the results get thrown away. This "revision + discard stale" pattern is so central that [part 4](/posts/2026/11/vaayu-part-4-never-block-a-keystroke/) is about it.

## line shifts: where did my line go?

Lots of things point at line numbers that live outside the buffer: marks, the jumplist, other windows' cursors, review comments, tour highlights. When you insert a newline on line 10, everything pointing at line 11 or later is now off by one.

The buffer can't fix them itself, because it doesn't own them. So it writes them down instead:

```rust
/// Line-count changes `(edit_line, delta)` since the editor last drained
/// them, so the editor can shift marks, the jumplist, and other windows'
/// cached cursors that index this buffer by line.
pending_line_shifts: Vec<(usize, i64)>,
```

The editor drains that list after each command and shifts everything that points into the buffer. That's how a review comment stays on its line while you type above it, before you even save ([part 11](/posts/2026/11/vaayu-part-11-private-code-reviews-that-survive-edits/) is about what happens when it _can't_ follow).

## is it modified? compare content, not counters

Vaayu started with a `modified: bool`, like most editors. Undo back to exactly what's on disk, and it still said `[+]`. The same audit also found that `:q` only checked the _current_ buffer, so a modified buffer in the background was silently thrown away. Fun times.

Now Vaayu keeps a snapshot of the rope as of the last load or save and compares content:

```rust
/// compares *content*, not a revision number, against this -- Rope
/// clones are O(1) (structural sharing), so this costs nothing extra,
/// and it means undoing back to exactly the saved text is correctly
/// clean again, not just "fewer edits than before."
saved_snapshot: Rope,
```

This is a nice property of ropes that you get for free: cloning shares all the chunks, so holding the "saved" version costs almost nothing until you edit. And the comparison result is cached per `edit_seq`, so it doesn't re-compare on every frame.

## undo, and undo that survives a restart

Undo works on transactions, and here the rope pays off again. `begin_edit` doesn't record a list of operations; it just clones the rope (O(1), structural sharing) into `pending_undo`. Every primitive edit after that goes straight to the live rope. `commit_edit` pushes that snapshot onto the undo stack, unless the content didn't actually change:

```rust
pub fn commit_edit(&mut self) {
    if let Some(state) = self.pending_undo.take() {
        if state.rope == self.rope {
            return; // `i<Esc>` with nothing typed is not an undo step
        }
        self.undo_stack.push(state);
        self.redo_stack.clear();
        // ...
```

So undo is "swap in the old rope", not "replay the inverse of twenty edits". That's why `ciw` followed by typing a word is one undo step, not twenty, and why undo can't get an inverse operation wrong.

Undo history is also written to `.vaayu/undo/` when you save, so you can undo yesterday's change today. The file is guarded by a hash of the content it belongs to. If the file was changed by something else in the meantime (a `git checkout`, another editor), the saved history doesn't match and is ignored, instead of "undoing" into nonsense.

## text in memory, your format on disk

Inside the editor, text always uses `\n`. On disk, files are whatever they were: CRLF, a UTF-8 BOM, a different encoding. Vaayu remembers each of these on load and puts them back on save. A Windows file you open, edit one line of and save comes back as a one-line diff, not a 3,000-line one.

## saving without eating your file

The most important function in an editor is the one you never think about. Here's the core of Vaayu's atomic write, from [`src/files.rs`](https://github.com/krshrimali/vaayu/blob/master/src/files.rs):

```rust
let temp = parent.join(format!(
    ".vaayu-save-{}-{}",
    std::process::id(),
    NEXT.fetch_add(1, Ordering::Relaxed)
));
let result = (|| -> anyhow::Result<()> {
    let mut options = std::fs::OpenOptions::new();
    options.write(true).create_new(true);
    let mut f = options.open(&temp)?;
    if let Ok(meta) = std::fs::metadata(&path) {
        f.set_permissions(meta.permissions())?;
    }
    f.write_all(bytes)?;
    f.sync_all()?;
    std::fs::rename(&temp, &path)?;
    if let Ok(dir) = std::fs::File::open(parent) {
        let _ = dir.sync_all();
    }
    Ok(())
})();
if result.is_err() {
    let _ = std::fs::remove_file(&temp);
}
```

Step by step:

1. Write to a new temp file **next to** the real one (same directory, so same filesystem, so `rename` is atomic).
2. `create_new` refuses to reuse an existing file, so two saves can't collide.
3. Copy the original permissions, so saving doesn't turn your script non-executable.
4. `sync_all` so the bytes are actually on disk, not just in the page cache.
5. `rename` over the original. At every moment, the path holds either the complete old file or the complete new one. Never half of each.
6. Sync the directory, so the rename itself survives a power cut.

If the power goes out halfway through writing, you lose the edit, not the file. That trade is the whole point.

Before writing, Vaayu also checks whether the file changed on disk since it was loaded, and refuses to overwrite it silently. And the same function, with `private: true`, writes review notes and tasks with `0600` permissions and refuses to follow a symlink.

## crash recovery

The last safety net: when you stop typing, dirty buffers are snapshotted to `.vaayu/recovery/`. If Vaayu (or your laptop) dies, `:recover` brings them back. A recovered buffer comes back _unsaved_, so you look at it before it touches the real file, and it refuses to replace a buffer you've already started editing.

## what I'd do differently

- I'd define "revision" before writing a single cache. Treating `edit_seq` as "edited since Esc" instead of "the content changed" caused a crash and a data-loss bug before the editor was a day old.
- I'd make "modified" a comparison from the start. A flag is a second source of truth, and it will drift from the first one.



Next up, [part 2](/posts/2026/11/vaayu-part-2-teaching-rust-to-speak-vim/): turning keystrokes like `d2aw` into edits on this buffer.
