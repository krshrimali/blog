---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2026-11-27T02:00:00+05:30
linktitle: "Vaayu part 2: teaching Rust to speak Vim"
title: "Vaayu part 2: teaching Rust to speak Vim"
categories:
- project
tags:
- vaayu
- rust
- editor
- vim
type:
- post
- posts
weight: 10
series:
toc: true
comments: true
---

_Part 2 of the [Vaayu series](/posts/2026/11/why-i-wrote-my-own-editor/). [Part 1](/posts/2026/11/vaayu-part-1-text-is-a-tree/) was about storing text. This one is about the language you use to change it._

The best thing about Vim isn't the keys. It's that the keys form a **grammar**. Once you know `d` (delete) and `w` (word), you know `dw`. Once you also know `c` (change) and `i(` (inside parens), you get `ci(` without ever learning it. Learn N operators and M motions and you know N × M commands.

```text
   "a      3       d        2        aw
   ─┬─    ─┬─     ─┬─      ─┬─      ─┬─
 register count operator  count  text object / motion
```

So the job of Vaayu's Normal mode isn't to implement hundreds of commands. It's to implement a small parser, a few dozen motions and text objects, a dozen operators, and one function that combines them.

## the parser is a struct, not a state machine zoo

While you're typing a command, Vaayu keeps whatever it has seen so far in one place:

```rust
pub struct PendingState {
    pub count: Option<usize>,
    pub register: Option<char>,
    pub operator: Option<OperatorKind>,
    pub op_count: Option<usize>,
    pub awaiting: Option<Awaiting>,
}
```

Each key either fills in a field or completes the command. `"a` sets `register`. `3` sets `count`. `d` sets `operator`. Another `2` goes into `op_count`, because in Vim `3d2w` deletes six words, and Vaayu multiplies them the same way:

```rust
pub fn total_count(&self) -> usize {
    self.op_count
        .unwrap_or(1)
        .saturating_mul(self.count.unwrap_or(1))
        .min(MAX_COUNT)
}
```

That `saturating_mul` and `MAX_COUNT` (100,000) are there because an early audit found that a long enough count overflowed the arithmetic and could send a paste or macro loop spinning through an unbounded number of iterations. Every number a user can type is a number an attacker (or a cat on the keyboard) can type.

`awaiting` handles commands that need one more key: `f` needs a character, `"` needs a register name, `i` after an operator needs a text-object kind, `m` needs a mark name. It's an enum:

```rust
pub enum Awaiting {
    FindChar { forward: bool, before: bool },
    Replace,
    TextObject { inner: bool },
    RegisterName,
    MarkSet,
    MarkJump { exact: bool },
    MacroRegister,
    MacroReplay,
    GPrefix,
    ZPrefix,
    // ...
}
```

## motions are data

A motion is a value that says _where to go_, not code that moves the cursor:

```rust
pub enum Motion {
    Left, Right, Up, Down,
    LineStart, FirstNonBlank, LineEnd,
    WordFwd(bool),       // w / W
    WordEndFwd(bool),    // e / E
    WordBack(bool),      // b / B
    WordEndBack(bool),   // ge / gE
    FileStart, FileEnd,
    GotoLine(usize),
    MatchPair,           // %
    FindChar { ch: char, before: bool, forward: bool, repeat: bool },
    ParaFwd, ParaBack,
    // ... 33 variants in total
}
```

Each motion also has a **span kind**, and this is the part of Vim most people never think about:

```rust
pub enum Span {
    Empty,
    Inclusive,  // `e`: the character under the end is included
    Exclusive,  // `w`: it isn't
    Linewise,   // `j`, `}`: whole lines
}
```

`dw` and `de` both stop near the end of a word, but `dw` is exclusive and `de` is inclusive. `dj` deletes two whole lines, wherever your cursor is in them. Getting these right is 80% of "feels like Vim".

The `repeat` field in `FindChar` is a good example of how deep the rabbit hole goes. When you `;` after a `t` motion, the cursor is already parked right before the match. Search again from there and you'd find the same character and not move. So a repeated till skips the adjacent match. Vim does this. Nobody notices until it's missing.

## operators × motions = one function

Operators are a small enum too:

```rust
pub enum OperatorKind {
    Delete, Change, Yank,
    IndentRight, IndentLeft,
    ToggleCase, Lower, Upper, Rot13,
    Reindent, Format, Fold,
}
```

and there's one function that applies any operator to any span: `apply_operator_motion(ed, op, from, to, span)`. It turns the motion's result into a character range (respecting the span kind), and then does the operator's thing to that range. The case operators, for example, are four lines of real work:

```rust
ed.buf_mut().begin_edit();
let text = ed.buf_mut().delete_char_range(start, end);
ed.buf_mut().insert_str_at(start, &convert(&text));
ed.buf_mut().commit_edit();
```

`begin_edit`/`commit_edit` make it one undo step ([part 1](/posts/2026/11/vaayu-part-1-text-is-a-tree/)).

Vim also has special cases that you only learn from bug reports. Here's one that's in the code with a comment: a characterwise delete that covers _all_ the text of several lines (say `d}` from the start of a paragraph) is promoted to a linewise delete, so it takes the indentation and the trailing newline with it instead of leaving an empty line behind.

## text objects

Text objects (`iw`, `a(`, `i"`, `it`, `ip`, `as`, `ia` for an argument...) return a range instead of a position:

```rust
pub enum ObjectKind {
    Word(bool), Paren, Brace, Bracket, Angle,
    DoubleQuote, SingleQuote, Backtick,
    Argument, Paragraph, Sentence, Tag,
}
```

Because the operator function takes a range, `d`, `c`, `y`, `gU`, `>` and `=` work on every one of them for free. That's the N × M payoff.

## dot repeat: record keys, not intent

There are two ways to implement `.`:

1. remember _what_ happened ("deleted the word at 4:10"), or
2. remember the _keys_ that did it, and replay them.

Vaayu does the second. While a change is being typed, its keys are collected in `cmd_keys`. When the change completes, they become `last_change`:

```rust
pub fn finish_change_recording(&mut self) {
    if self.recording_change && !self.replaying {
        self.last_change = self.cmd_keys.clone();
    }
    self.recording_change = false;
}
```

Replaying keys is exactly right for things like `ciwfoo<Esc>`: on the next word, `.` changes _that_ word to `foo`, which is what you want. A "what happened" record would have to reinvent the whole grammar to get that right. (The `!self.replaying` check stops `.` from recording itself.)

Visual mode is the exception. `.` after a Visual change repeats it over a selection of the same _shape_, so that's stored separately.

Macros use the same machinery: `qa` records keys into a register, `@a` feeds them back through the same parser.

## Vim's regex is not your regex

Vim's default "magic" regex flips the usual rules: `(`, `)`, `{`, `+`, `?` and `|` are _literal_, and you escape them to make them special. `/\(foo\)\+` in Vim is `/(foo)+` everywhere else. Then there's `\<` and `\>` for word boundaries, `\v` to switch to "very magic", `\c` for case-insensitive, `\zs`...

I wanted my muscle memory to work in `/` and `:s`, so [`src/vimregex.rs`](https://github.com/krshrimali/vaayu/blob/master/src/vimregex.rs) translates Vim's dialect into one the [`fancy-regex`](https://github.com/fancy-regex/fancy-regex) crate understands (it adds backreferences and lookaround on top of the `regex` crate):

```rust
if !class && matches!(n, 'v' | 'V' | 'm' | 'M') {
    mode = n;      // \v, \V, \m, \M switch the escaping rules
    continue;
}
if !class && matches!(n, 'c' | 'C') {
    out.push_str(if n == 'c' { "(?i)" } else { "(?-i)" });
    continue;
}
if !class && n == '%' && chars.peek() == Some(&'(') {
    chars.next();
    out.push_str("(?:");   // \%( is a non-capturing group
    continue;
}
```

It's not the whole Vim dialect, and the module says so at the top. But it covers what I actually type.

## characters, graphemes and cells

A "column" in an editor is three different things:

- a **char** index (what the rope counts),
- a **grapheme**: what a person sees as one character (`é` written as `e` + a combining accent, or a flag emoji, which is two code points),
- a **cell**: how wide it is on screen (`界` takes two).

`l` moves by grapheme. The cursor is drawn by cell. The rope is indexed by char. And LSP speaks UTF-16 ([part 5](/posts/2026/11/vaayu-part-5-incremental-tree-sitter-and-an-lsp-client-from-scratch/)), just to make it interesting. Vaayu uses `unicode-segmentation` and `unicode-width` and converts at the edges. Visual block mode on lines with wide characters is where every mistake shows up, so there are tests for exactly that:

```rust
let mut e = editor("a界bc\n界abc\nxy\n");
keys(&mut e, "j$");
e.feed_key(Key::Ctrl('v'));
keys(&mut e, "jAQ\x1b");
assert_eq!(e.buf().rope.to_string(), "a界bc\n界abcQ\nxyQ\n");
```

## how do you know it's "like Vim"?

You test it against Vim. There are three layers:

1. **Unit tests in Vim notation.** [`src/vim_parity_tests.rs`](https://github.com/krshrimali/vaayu/blob/master/src/vim_parity_tests.rs) feeds keys like `2<CR>` or `<C-w>` and checks the cursor and text:

   ```rust
   let t = "  a\n  b\n    c\nabcdef\n";
   assert_eq!(at(t, 1, 0, "-").cursor(), (0, 2));
   assert_eq!(at(t, 0, 0, "2<CR>").cursor(), (2, 4));
   assert_eq!(at(t, 3, 0, "4|").cursor(), (3, 3));
   ```

2. **Reference data from a real Vim.** For the hairy parts (`%` matching, Visual block paste with every register type), a fixture file holds 214 cases recorded from Vim itself (120 Visual-block puts, 94 `%` motions): starting text, register contents and type, keys, and the expected text, cursor and registers afterwards. Vaayu replays every case and compares.

3. **The real binary in a PTY.** A Python harness starts `vaayu` in a pseudo-terminal at 40×12, 100×24 and 180×50, types the same commands, and reads the screen back with `pyte`.

The fixtures also found places where I _disagree_ with Vim on purpose. The Vim build used for reference replays only the deletion when you `.` after a Visual put. Vaayu replays the whole replacement, and the tests say so explicitly.

## vs Helix

Helix made a different, deliberate choice: **select first, then act**. `w` selects a word, `d` deletes the selection. You always see what you're about to change, which is genuinely nice, and multiple selections fall out of the model naturally.

The cost is that you can't reuse Vim muscle memory, and some things that are one command in Vim (`ci(` from anywhere inside the parens, `.` after a change) take more thought. Vaayu keeps the Vim grammar and adds multiple cursors on top of the same primitives, for when I want the Helix-style workflow.

## vs Neovim

Neovim is the reference. Where Vaayu differs, it's either a bug or listed in the [parity plan](https://github.com/krshrimali/vaayu/blob/master/NEOVIM_PARITY_PLAN.md). The big thing not there: Vimscript (and Lua). Your `.vimrc` doesn't load, and "like Vim" is measured against the commands I actually use and the reference data above, not against all of Vim.

## what I'd do differently

- I'd treat every count as hostile from the first commit. The overflow fix landed on day ten, after an audit found two reachable integer overflows. `saturating_mul` and a cap cost nothing to write up front.
- I'd record the Vim reference data before writing Visual block mode, not after. The grammar was there on day one; the 214 recorded cases came almost four weeks later, and they immediately turned up Unicode block edits and replacement pastes that my tests, written from memory, had gotten wrong.

Next, [part 3](/posts/2026/11/vaayu-part-3-drawing-a-terminal-frame-in-under-a-millisecond/): getting all this onto the screen, fast.
