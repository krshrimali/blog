---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2026-11-27T05:00:00+05:30
linktitle: "Vaayu part 5: incremental tree-sitter and an LSP client from scratch"
title: "Vaayu part 5: incremental tree-sitter and an LSP client from scratch"
categories:
- project
tags:
- vaayu
- rust
- editor
- tree-sitter
- lsp
type:
- post
- posts
weight: 10
series:
toc: true
comments: true
---

_Part 5 of the [Vaayu series](/posts/2026/11/why-i-wrote-my-own-editor/). So far the editor knows text. This post is about how it knows **code**: syntax highlighting with tree-sitter, and talking to language servers. It's also where the biggest performance bug in Vaayu was hiding._

There are two kinds of "understanding" in a modern editor, and they're good at different things:

- **tree-sitter** parses one file, fast, on every keystroke. It knows that `fn` is a keyword and `"x"` is a string. It doesn't know what `foo()` refers to.
- a **language server** (rust-analyzer, clangd, pyright...) understands the whole project. It knows where `foo` is defined, what type it returns, and that you misspelled it. It's slower, and it runs in another process.

Vaayu has both built in. Let's start with the one that bit me.

## incremental parsing is not incremental highlighting

tree-sitter's headline feature is incremental parsing. You tell it what changed, give it the old tree, and it reuses everything it can:

```rust
if let Some(tree) = &mut self.tree {
    tree.edit(&edit);   // "bytes 120..120 became 120..121"
}
let new_tree = self.parser.parse(new_text.as_bytes(), self.tree.as_ref());
```

On a typical edit this takes microseconds. So I assumed highlighting was cheap.

After the rendering fixes in [part 3](/posts/2026/11/vaayu-part-3-drawing-a-terminal-frame-in-under-a-millisecond/), Vaayu matched bare Neovim on cursor motion, but **typing in Insert mode was still about 8× slower** (2.5 ms vs 0.3 ms per character). The binary search for spans hadn't helped. So I added timers inside the row loop and inside the syntax update, and the answer was obvious once I could see it:

The parse was incremental. **Rebuilding the highlight spans was not.** After every parse, the code walked the entire tree from the root to produce a fresh list of `(start, end, class)` spans. About 8 ms per keystroke on a modest file.

Worse, a correctness fix from the same day (every keystroke bumps `edit_seq`, see [part 1](/posts/2026/11/vaayu-part-1-text-is-a-tree/)) meant that every keystroke now triggered that full re-walk. One fix made the other bug much more visible.

### fix 1: throttle (and the bug the throttle caused)

The quick fix was to throttle the full rebuild, so a typing burst pays for it once instead of on every key. Rendering against slightly stale spans for a few tens of milliseconds is safe, because the renderer clamps every span to valid UTF-8 boundaries anyway.

That introduced its own bug: if you stopped typing _inside_ the throttle window, nothing woke the editor up to finish the deferred rebuild. The main loop only redraws on a key or an LSP message, so colours could stay stale until you pressed something. The fix was a third wake-up condition in the idle loop: "is a syntax rebuild due?".

(Fun detail: my first check of that fix said "colours never appear". It was wrong. I was looking at a partial delta of the terminal output instead of a full capture. Look at the bytes, but look at all of them.)

### fix 2: actually incremental spans

The throttle only limits _how often_ you pay. The real fix is to not pay. tree-sitter can tell you which byte ranges differ between the old tree and the new one, and that's all you need:

```rust
fn compute_incremental_spans(
    old_spans: &[(usize, usize, HlClass)],
    lang: Lang,
    old_tree: &Tree,
    new_tree: &Tree,
    edit: InputEdit,
    new_text: &str,
) -> Option<Vec<(usize, usize, HlClass)>> {
    let mut lo = edit.start_byte;
    let mut hi = edit.new_end_byte.min(new_text.len());
    for r in old_tree.changed_ranges(new_tree) {
        lo = lo.min(r.start_byte);
        hi = hi.max(r.end_byte.min(new_text.len()));
    }
    let root = new_tree.root_node();
    let mut enclosing = root.descendant_for_byte_range(lo, hi).unwrap_or(root);
    // A string leaf can be contained in a classified string node. Rebuild
    // the same atomic highlight unit used by the full traversal.
    let mut ancestor = enclosing.parent();
    while let Some(node) = ancestor {
        if classify(&node, new_text.as_bytes(), keywords(lang)).is_some() {
            enclosing = node;
        }
        ancestor = node.parent();
    }
    // ... re-walk `enclosing`, shift every old span after the edit by the
    // byte delta, and splice the three pieces together
}
```

1. Union the edit range with tree-sitter's changed ranges.
2. Find the smallest node that covers it, and climb up while an ancestor is itself a highlight unit (so typing inside a string re-classifies the whole string, not half of it).
3. Re-walk only that node. Keep old spans before it. Shift old spans after it by the size of the edit.

If anything looks off (no old tree, a pending full rebuild), it returns `None` and the full rebuild runs, throttled to at most once every 50 ms. The fast path is an optimization over a slow path that's always correct, same as the scroll trick in part 3.

After this, inserting a character on a 50,000-line Rust file takes **0.79 ms** to first output. Bare Neovim takes 0.89 ms.

### large files

Above 5 MB (`large_file_kb = 5120`), Vaayu skips tree-sitter, spell checking, TODO scanning and rainbow brackets entirely. You get a fast plain-text editor instead of a slow smart one. Neovim users will know this as the `bigfile.nvim` plugin; here it's a config value.

### grammars are compiled in

Vaayu links its grammars into the binary as Rust crates: Rust, Python, JavaScript/JSX, TypeScript/TSX, Go, C, Bash, JSON, TOML, YAML, Lua, Vim, CSS, HTML and Solidity. (Markdown previews use `pulldown-cmark` instead, see [part 8](/posts/2026/11/vaayu-part-8-pictures-in-a-terminal/).) Nothing to download, nothing to `:TSInstall`. The cost is a bigger binary and no way to add a language without rebuilding.

## an LSP client from scratch

The Language Server Protocol is JSON-RPC over stdin/stdout, with HTTP-style headers. The whole framing layer fits on a screen:

```rust
pub fn read_message<R: BufRead>(r: &mut R) -> io::Result<Option<Value>> {
    let mut content_length: Option<usize> = None;
    loop {
        let mut line = String::new();
        if r.read_line(&mut line)? == 0 {
            return Ok(None);
        }
        let line = line.trim_end();
        if line.is_empty() {
            break;
        }
        if let Some(v) = line.strip_prefix("Content-Length:") {
            content_length = v.trim().parse().ok();
        }
    }
    let len = content_length.ok_or_else(|| /* missing Content-Length */)?;
    if len > 32 * 1024 * 1024 {
        return Err(/* "LSP message exceeds 32 MiB" */);
    }
    let mut buf = vec![0u8; len];
    r.read_exact(&mut buf)?;
    Ok(Some(serde_json::from_slice(&buf)?))
}
```

Note the 32 MiB cap. A buggy server that sends a garbage length shouldn't be able to make the editor allocate gigabytes.

Each server runs as a child process with a reader thread that turns messages into events for the main loop ([part 4](/posts/2026/11/vaayu-part-4-never-block-a-keystroke/)'s pattern again). The interesting parts are everything around the framing.

### UTF-16, the tax everyone pays

LSP positions are `{line, character}`, and `character` counts **UTF-16 code units**, because that's what JavaScript strings use. The rope counts Unicode chars. They agree for ASCII and disagree for emoji, many CJK characters and anything outside the Basic Multilingual Plane:

```rust
pub fn utf16_col(s: &str, col: usize) -> usize {
    s.chars().take(col).map(char::len_utf16).sum()
}
pub fn utf16_to_col(s: &str, units: usize) -> usize {
    let mut n = 0;
    for (i, c) in s.chars().enumerate() {
        if n + c.len_utf16() > units {
            return i;
        }
        n += c.len_utf16();
    }
    s.chars().count()
}
```

Every position going to a server goes through `utf16_col`, and every position coming back goes through `utf16_to_col`. Forget it once, and "go to definition" lands one column off on any line with an emoji in a comment.

### stale answers

A hover or completion reply can arrive after you've typed three more characters. So every request remembers the buffer and `edit_seq` it was made for, and replies that no longer match are dropped. When a request is no longer wanted (you moved on, or pressed Esc), Vaayu sends `$/cancelRequest` so the server can stop working on it too.

Requests have deadlines. `initialize` gets a more generous one, because rust-analyzer on a big workspace can take a long time to start, and killing it after the normal request timeout would just restart it forever. But even that is bounded, so a truly hung server gets reaped.

### one root, many servers

Clients are per project root, and a buffer can have more than one server (say, `pyright` for types and `ruff` for linting). Diagnostics from all of them merge into one list, which feeds the gutter, the Results list ([part 7](/posts/2026/11/vaayu-part-7-splits-floating-terminals-and-one-results-list/)), and the context sent to the AI sidebar ([part 13](/posts/2026/11/vaayu-part-13-an-ai-agent-beside-the-code/)).

Semantic tokens (the server's own colouring, e.g. "this identifier is a mutable variable") are an optional overlay on top of tree-sitter, requested once per `(buffer, edit_seq)`.

### testing against a fake server

You can't test an LSP client against rust-analyzer in CI and expect it to be fast or deterministic. So there's a [`tests/mock_lsp.py`](https://github.com/krshrimali/vaayu/blob/master/tests/mock_lsp.py) that speaks just enough LSP to answer with known diagnostics, hovers and edits, with no network and no real workspace writes. There's also a real-clangd test, run separately, for the end-to-end path.

## vs Neovim and Helix

In my Neovim config this was `nvim-treesitter` + `nvim-lspconfig` + `mason.nvim` + `blink.cmp` + `fidget.nvim` for progress. Five plugins, each with its own update cycle, wired together in Lua. It works great, once it works.

**Helix** is the closest rival here: tree-sitter and LSP are built in, with no setup. It loads grammars as shared libraries from its runtime directory, which keeps the binary small and makes adding a language easy. Vaayu compiles them in.

Measured on warm formatting with clangd (five fresh runs each), all three editors are a tie: Vaayu 22.84 ms, Neovim 22.99 ms, Helix 23.19 ms. That makes sense: almost all of it is clangd doing the work. The editor's LSP client is rarely the bottleneck. The editor's _highlighting_, as I found out, can be.

## what I'd do differently

- I'd have profiled typing, not just moving, from the start. Cursor movement was fine; it was the edit path that hid an O(file) walk.


Next, [part 6](/posts/2026/11/vaayu-part-6-benchmarking-editors-honestly/): how all these numbers were measured, and how easy it is to measure them wrong.
