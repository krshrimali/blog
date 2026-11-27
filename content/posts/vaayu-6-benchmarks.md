---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2026-11-27
linktitle: "Vaayu part 6: benchmarking editors honestly"
title: "Vaayu part 6: benchmarking editors honestly"
categories:
- project
tags:
- vaayu
- rust
- editor
- performance
- benchmarks
type:
- post
- posts
weight: 10
series:
toc: true
comments: true
---

_Part 6 of the [Vaayu series](/posts/2026/11/why-i-wrote-my-own-editor/). I've been quoting milliseconds for five posts. This one is about where they come from, every mistake I made getting them, and the full scorecard against Neovim and Helix, including where Vaayu loses._

Editor benchmarks on the internet are mostly vibes. "X feels snappier than Y." I wanted numbers, and the more I measured, the more I learned how easy it is to produce a number that's precise, repeatable, and wrong.

## what are we even measuring?

When you press `j`, a lot happens:

```text
 key pressed ─► terminal emulator ─► PTY ─► editor reads it ─► editor thinks
     ─► editor writes bytes ─► PTY ─► terminal parses ─► terminal paints ─► display scans out
```

You can only measure a slice of that. Vaayu's harness measures **from writing the key into the PTY to the first byte the editor writes back**. That's the editor's own reaction time. It deliberately excludes the terminal emulator and the display, which are the same for every editor you run in them.

Here's the core of it, from [`bench/editor_compare.py`](https://github.com/krshrimali/vaayu/blob/master/bench/editor_compare.py):

```python
def transact(fd, keys, quiet=0.012, timeout=3.0):
    drain(fd, 0.005)
    started = time.perf_counter()
    os.write(fd, keys)
    first = None
    total = 0
    last = started
    while time.perf_counter() - started < timeout:
        ready, _, _ = select.select([fd], [], [], quiet)
        now = time.perf_counter()
        if ready:
            part = os.read(fd, 65536)
            if first is None:
                first = now - started      # time to first output byte
            total += len(part)
            last = now
        elif first is not None and now - last >= quiet:
            return first, now - started, total   # + a "quiet" time
    return first, None, total
```

It records two things per key:

- **first output**: when the editor started answering.
- **quiet**: when the output stopped for 12 ms. A rough proxy for "done drawing", which includes the 12 ms wait itself.

And the bytes written, which turned out to be one of the most useful numbers of all ([part 3](/posts/2026/11/vaayu-part-3-drawing-a-terminal-frame-in-under-a-millisecond/)).

## the setup

The current run (2026-10-08):

- Intel Core i9-12900K, Linux 7.2.8 (CachyOS), Rust 1.99.0
- Vaayu 0.1.0 release build, Neovim 0.12.5 with `-u NONE`, Helix 25.07.1 with its runtime
- a 100×40 PTY, a generated 50,000-line Rust file for the large-buffer tests
- a 319-file project for the picker and grep tests
- fresh temporary XDG directories for every editor, no saved state, Rust LSP off
- nothing else running: no builds, no test suites
- 3 sequential runs; each table value is the **median of the three runs' medians**

Every raw sample, the exact command lines, and SHA-256 hashes of the binaries and the harness are committed next to the results. If you don't trust a number, you can rerun it.

## mistakes I made (so you don't have to)

### 1. benchmarking a debug build

The very first comparison used Vaayu's debug build. It "proved" Vaayu was several times slower than Neovim at everything. Release was ~29× faster on a plain cursor move (0.23 ms vs 6.6 ms). Always benchmark the release binary. Obvious in hindsight, easy to forget.

### 2. Esc isn't slow, it's waiting

Bare Neovim took **51 ms** to leave Insert mode, vs Vaayu's 0.8 ms. That looks like a 60× win. It isn't. In a terminal, `Esc` is also the first byte of every escape sequence (arrow keys, function keys...). When Neovim sees `Esc`, it waits `ttimeoutlen` (50 ms by default) to see whether more bytes follow. That's a setting, and it's a sensible one. Set it to 0 or 10 and the "difference" disappears. I report the number because it's what you get out of the box, but it says nothing about Neovim's code.

### 3. a picker that never closed

The picker benchmark sent `Esc` to close the picker and then opened live grep. But in Vaayu the picker's query box has its own Normal/Insert modes, like the rest of the editor. The first `Esc` only left Insert mode in the query. The picker was still open when the harness typed the grep command. So "close picker" and "open live grep" for Vaayu measured something other than what their labels said.

The fix: send two separately timed `Esc`s for Vaayu (leave the query, then close), and one for Helix. All historical numbers with the broken sequence are still in the repo, marked as such, and aren't used for any current claim.

### 4. first output is not "done"

Vaayu's live grep "opens" in about 1 ms. That's true, and it's also not what most people would assume it means. Grep runs in the background ([part 4](/posts/2026/11/vaayu-part-4-never-block-a-keystroke/)), so the editor _responds_ immediately and the results arrive later. The harness has separate "settle" windows to catch late output, and it reports them separately. "Responds in 1 ms" and "searches the project in 1 ms" are different claims. I only make the first one.

### 5. one machine, one day

The 2026-10-03 run and the 2026-09-16 run were on different machines (the later one in a cloud container), and Vaayu's startup went from 3.8 ms to 15–29 ms between them. Was the big feature roadmap I'd just merged to blame? I rebuilt the pre-roadmap version and ran it on the same container: the same 14–15 ms. So the roadmap didn't regress startup. Whether the rest of the gap was the container or older changes, that run simply can't tell, and I didn't pretend it could. Never compare numbers across machines, and when a number moves, rebuild the old version and check before you blame the new one.

## the scorecard

Time to first output, median of three run medians, in milliseconds. Lower is better. Bold marks the fastest.

| Process | Vaayu | Neovim bare | Helix |
| --- | ---: | ---: | ---: |
| Startup to first output | **7.19** | 9.19 | 397.96 |
| Idle memory (RSS, MiB) | 63.2 | **9.6** | 121.4 |

| Operation (50k-line file) | Vaayu | Neovim bare | Helix |
| --- | ---: | ---: | ---: |
| Cursor down | 1.001 | **0.504** | 3.178 |
| Page scroll | 0.654 | **0.484** | 3.165 |
| Enter Insert | 0.567 | **0.537** | 3.004 |
| Insert a character | **0.794** | 0.887 | 177.195 |
| Leave Insert | 0.811 | 50.805 ¹ | **0.754** |
| Submit a buffer search | **0.319** | 3.404 | 2.135 |
| Next search match | 2.501 | **0.507** | 4.404 |

| Project tools (319 files) | Vaayu | Helix |
| --- | ---: | ---: |
| Open file picker | **0.559** | 3.600 |
| Filter file picker | **0.901** | 3.851 |
| Close file picker | **0.707** | 2.945 |
| Open live grep | **1.083** | 3.637 |
| Filter live grep | **0.483** | 3.011 |

¹ `ttimeoutlen`, see above. Bare Neovim has no built-in picker or grep UI, so those rows compare Vaayu and Helix only.

{{< vaayu-svg "bench.svg" >}}

_The same numbers on one log scale. The spread inside each row matters more than any single dot: most of it is well under a millisecond, and the outliers are startup, Helix's large-file insert and Neovim's Esc timeout._

### where Vaayu loses

- **Memory.** 63 MiB vs bare Neovim's 9.6 MiB. Compiled-in grammars, caches of composed rows, the picker inventory, the image and diagram caches. Some of that is the price of the caching in parts 3 and 4. Some is just not having optimized for it yet.
- **Cursor down, page scroll, next match.** Bare Neovim is about twice as fast to first byte. Its renderer is excellent. Vaayu's row-based diff writes a bit more and does a bit more work per frame. Both are far below a frame (16.7 ms at 60 Hz), so I don't think anyone can feel it, but it's a loss and I'm reporting it.
- **Entering Insert** is a tie at this precision. I'm not calling 0.03 ms a win.

### where Vaayu wins, and what that means

- **Startup vs Helix (7 ms vs 398 ms).** Large and consistent across runs. I haven't profiled Helix's startup, so I won't guess why.
- **Typing on a big file vs Helix (0.8 ms vs 177 ms).** Also large and consistent, on this file, with this configuration. Helix and Vaayu use the same rope library ([part 1](/posts/2026/11/vaayu-part-1-text-is-a-tree/)), so it isn't the data structure. Vaayu's incremental highlight spans ([part 5](/posts/2026/11/vaayu-part-5-incremental-tree-sitter-and-an-lsp-client-from-scratch/)) are a plausible contributor. The benchmark doesn't isolate the cause, so that's all I can say.
- **Search submit vs both.** Vaayu answers first, but this is first output, not "found every match".
- **Picker and grep vs Helix.** A prewarmed inventory and background grep mean the first response doesn't wait. Helix's matcher (`nucleo`) is excellent; this is about architecture, not scoring speed.

### where it's a tie

- **Character insertion vs Neovim**: 0.79 vs 0.89 ms. 0.09 ms is not a meaningful difference.
- **LSP formatting with clangd**: 22.84 / 22.99 / 23.19 ms. Almost all of it is clangd.
- **The 12 ms "quiet" proxy**: in the current run it lands between about 12.6 and 16.6 ms for nearly every single-key operation in all three editors (Esc in bare Neovim and Helix's large-file insert aside). It includes the 12 ms wait itself, so at that resolution it barely separates them, which is itself a useful finding.

## what isn't measured

- **Neovim with my real config** (about forty plugins). This is the comparison that actually motivated Vaayu, and it isn't in the table, because a fair version is hard: plugin-heavy startup depends on lazy-loading choices, and I'd be benchmarking my config as much as Neovim. It's next on the list.
- **Physical painting.** Your terminal emulator adds its own time, and it varies more between terminals than these numbers vary between editors.
- **First run, cold caches, network filesystems**, and anything with the LSP doing real work.
- **Other machines.** Three runs on one machine is evidence for this workload, not a universal ranking.

## the browser editor

For completeness: when Vaayu runs in a browser tab ([part 9](/posts/2026/11/vaayu-part-9-the-same-editor-in-a-browser-tab/)), a keypress reaches the page's grid in ~2 ms and is painted in ~12 ms at the median in headless Chromium. The 12 ms is almost entirely waiting for the next animation frame, i.e. the display's refresh, not the editor.

## if you benchmark your own editor

1. Release builds only.
2. Measure in a PTY, at first byte, and record bytes written.
3. Fresh config and state directories, nothing else running.
4. Several runs; report medians **and** tails, and the sample counts.
5. Write down what a number does _not_ mean, next to the number.
6. When a number moves, rebuild the old version on the same machine before you believe it.
7. Publish the raw data and the harness.

And report your losses. A benchmark that only shows wins is an ad.

Next, [part 7](/posts/2026/11/vaayu-part-7-splits-floating-terminals-and-one-results-list/): the UI, from split windows to terminals inside the editor.
