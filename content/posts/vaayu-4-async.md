---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2026-11-27T04:00:00+05:30
linktitle: "Vaayu part 4: never block a keystroke"
title: "Vaayu part 4: never block a keystroke"
categories:
- project
tags:
- vaayu
- rust
- editor
- concurrency
type:
- post
- posts
weight: 10
series:
toc: true
comments: true
---

_Part 4 of the [Vaayu series](/posts/2026/11/why-i-wrote-my-own-editor/). [Part 3](/posts/2026/11/vaayu-part-3-drawing-a-terminal-frame-in-under-a-millisecond/) got a frame out in under a millisecond. But some work just doesn't fit in a millisecond: searching a project, scanning a few hundred thousand files, asking git or a language server. This post is about where that work goes._

There's one rule in Vaayu that everything else follows:

> **The thread that reads your keys never waits for anything slow.**

Not for the disk, not for `ripgrep`, not for git, not for a language server. If something might take longer than a frame, it runs somewhere else, and its answer is allowed to arrive late, or never.

That rule needs exactly one pattern to work. Once you see it, you'll see it everywhere in the codebase.

## the pattern: generations

Here's live grep, from [`src/jobs.rs`](https://github.com/krshrimali/vaayu/blob/master/src/jobs.rs). When you type in the query box, the editor doesn't start a search. It bumps a counter and writes down what it wants:

```rust
pub fn schedule_grep(&mut self) {
    self.search_job.generation.fetch_add(1, Ordering::Relaxed);
    let (query, fixed, paths) = /* the current query */;
    self.search_job.pending = Some((Instant::now(), query, fixed, paths));
}
```

On each pass through the main loop, if a request has been pending for 60 ms with no newer keystroke, it starts a worker thread and gives it the **generation number it was started under**:

```rust
if self.search_job.pending
    .as_ref()
    .is_some_and(|(t, ..)| t.elapsed() >= Duration::from_millis(60))
{
    let (_, query, fixed, paths) = self.search_job.pending.take().unwrap();
    let generation = self.search_job.generation.clone();
    let id = generation.load(Ordering::Relaxed);
    let (tx, rx) = mpsc::channel();
    self.search_job.rx = Some(rx);
    std::thread::spawn(move || {
        let mut command = Command::new("rg");
        // ... --json --line-number ...
    });
}
```

While `rg` streams results, the worker keeps checking whether it still matters, and kills `ripgrep` the moment it doesn't:

```rust
if generation.load(Ordering::Relaxed) != id || entries.len() >= 5000 {
    let _ = child.kill();
    break;
}
```

And when results arrive back on the main thread, they're only used if they're still current:

```rust
if let Ok((id, entries, error)) = rx.try_recv() {
    if id == self.search_job.generation.load(Ordering::Relaxed) {
        // show them
    }
}
```

That's it. Three ideas:

1. **Debounce**: wait 60 ms of quiet before starting, so typing `render` starts one search, not six.
2. **Generation**: every request carries the counter value it started with. If the counter moved, the request is stale.
3. **Cancel and discard**: stale workers kill their child process, and stale results are dropped on arrival. The newest request always wins, no matter which finishes first.

{{< vaayu-svg "generations.svg" >}}

_Typing `rend` slowly enough that each key outlives the 60 ms debounce. Typed fast, only one search would start at all._

The `try_recv` matters as much as the generation. The main loop _polls_ for results; it never blocks waiting for them. If grep is slow, your cursor still moves.

## the same pattern, everywhere

Once I had it, it showed up in every subsystem:

| Work | Where it runs | What "stale" means |
| --- | --- | --- |
| Live grep | a worker thread + `rg` | the query changed (generation) |
| File picker inventory | a background scan after the first frame | the project changed (watcher) |
| Syntax re-highlight | deferred while you type | `edit_seq` moved |
| LSP responses | a reader thread per server | the buffer's `edit_seq` moved, or a newer request was sent |
| Git gutter / blame | background `git` | the file's revision moved |
| Mermaid diagrams | one lazy worker with a 3 s deadline | the source or the theme changed |
| Project find & replace | debounced per-line search | the line changed since it was found |

The revision from [part 1](/posts/2026/11/vaayu-part-1-text-is-a-tree/) (`edit_seq`) is just a generation number that the buffer bumps for you.

## no async runtime

A question I get: why threads and channels, and not `tokio`?

Mostly because the work isn't the kind async is good at. Async shines when you have thousands of things waiting on I/O at once. An editor has a handful of background jobs at a time, and most of them are a child process (`rg`, `git`, a language server) or CPU work (fuzzy scoring, layout, diagram rendering). A thread per job is simple, the code reads top to bottom, and there's no runtime to start, which helps the 7 ms startup. Even the web server in [part 9](/posts/2026/11/vaayu-part-9-the-same-editor-in-a-browser-tab/) is plain threads.

## the file picker: don't sort what you won't show

The picker has the same shape plus one algorithmic trick.

First, the **inventory** (every file in the project) is scanned in the background right after the first frame is drawn, and refreshed when the file watcher sees files appear or disappear. So when you press `,ff`, there's nothing to wait for. The picker opens in about half a millisecond.

Then, on each keystroke, every path gets a fuzzy score. A project can have hundreds of thousands of paths, and the screen shows maybe 30 of them. The obvious code sorts every match and takes the top. Vaayu keeps a **bounded min-heap** of the best 500 instead:

```rust
let mut heap: BinaryHeap<Reverse<Scored>> = BinaryHeap::with_capacity(k + 1);
for (idx, f) in candidates.iter().enumerate() {
    let Some(base_score) = fuzzy_score(f, query) else { continue };
    let score = base_score + boost.get(f.as_str()).copied().unwrap_or(0);
    let candidate = Scored { score, path: f, idx };
    if heap.len() < k {
        heap.push(Reverse(candidate));
    } else if let Some(Reverse(worst)) = heap.peek() {
        if candidate > *worst {
            heap.pop();
            heap.push(Reverse(candidate));
        }
    }
}
let mut top: Vec<Scored> = heap.into_iter().map(|Reverse(s)| s).collect();
```

The heap's top is the _worst_ of the current best 500. A new path only gets in if it beats that one. Sorting everything costs about n log n. This costs n log k plus a final k log k sort of the survivors, with k = 500. You still have to score every path, so the n doesn't go away, but the sort and the memory shrink a lot. When I added it, I kept the old full sort around in a test and checked that both give identical results.

The scorer has a fast path for ASCII (most paths), and a careful Unicode path with a comment worth quoting:

```rust
// Per-char case folding (not `candidate.to_lowercase()` as a whole),
// deliberately: some characters lowercase to more than one char (Turkish
// 'İ' -> "i̇", for example), which would make `cand_lower` longer than
// `cand` and desync the index used below to look back into `cand` --
// real crash, reproduced by searching a filename containing 'İ'.
```

## the file watcher

Vaayu uses the [`notify`](https://github.com/notify-rs/notify) crate to hear about changes on disk. Events are batched (75 ms debounce, at most 500 ms of latency) and then:

- a **clean** buffer whose file changed is reloaded,
- a **dirty** buffer is flagged `[changed on disk]` instead, never silently replaced,
- the file tree invalidates the directories that changed,
- files appearing or disappearing trigger a rate-limited inventory refresh for the picker.

Watchers aren't perfectly reliable everywhere (network filesystems, editors that save by renaming), so polling on focus is still there as a fallback.

## progress you don't notice

Background work needs feedback, but not too much. A spinner that flashes for 40 ms is worse than no spinner. So [`progress.rs`](https://github.com/krshrimali/vaayu/blob/master/src/progress.rs) has three numbers:

```rust
pub const SHOW_AFTER: Duration = Duration::from_millis(250);
pub const LINGER: Duration = Duration::from_millis(2000);
pub const MAX_ROWS: usize = 5;
```

A job only shows up if it's still running after 250 ms. A finished job stays for 2 seconds so you can see it completed. At most five rows stack up. Most work finishes before you ever see it, which is the point.

## vs Neovim and Helix

**Telescope** (the most popular Neovim picker) is lovely, but its sorter runs in Lua on Neovim's main loop. On a big repo you can feel typing in the prompt lag, which is why so many people install the native fzf sorter or switch to fzf-lua (which hands the work to an external `fzf` process). My own config used the Snacks picker and fzf-lua for the same reason. It's the same lesson: get the work off the thread that handles keys.

**Helix**'s picker uses [`nucleo`](https://github.com/helix-editor/nucleo), which is an excellent, parallel fuzzy matcher. Faster than my scorer, honestly. Where Vaayu differs is architecture: a prewarmed inventory and first output that doesn't wait for the matcher. In the benchmark, Vaayu's picker opens in 0.56 ms vs Helix's 3.60 ms, and live grep opens in 1.08 ms vs 3.64 ms.

Be careful with those numbers, though. They measure the time to the editor's _first response_ to your key, not the time to finish searching the project. Because grep runs in the background, Vaayu can respond before the results are in. That's the whole design, but it's a different thing from "searches faster". [Part 6](/posts/2026/11/vaayu-part-6-benchmarking-editors-honestly/) goes into exactly this.

## what I'd do differently

- I'd build the generation pattern as a small reusable type from the start. Each subsystem grew its own copy (an `AtomicU64` here, an `edit_seq` check there) and they all work, but a shared `Job<T>` would have made them easier to audit.


Next, [part 5](/posts/2026/11/vaayu-part-5-incremental-tree-sitter-and-an-lsp-client-from-scratch/): how Vaayu understands the code it's showing, and the 8 ms bug that was hiding in it.
