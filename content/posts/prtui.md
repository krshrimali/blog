---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2026-09-08
 linktitle: "prtui: Reviews Deserve Better Tooling"
 title: "Reviews Deserve Better Tooling"
 categories:
 - project
 tags:
 - blog
 - updates
 - rust
 - tui
 type:
 - post
 - posts
 weight: 10
 series:
 toc: false
 comments: true
---

# Reviews deserve better tooling

_Minor note before you start: I also wrote a technical blog post if it interests you: https://krshrimali.github.io/posts/2026/09/building-a-tui-for-reviewing-claude-sessions-and-github-prs-in-rust/. Happy reading! :)_

I don't think I need to emphasize much on how reviews have become a major bottleneck. But let's not forget how important they are as well.

I don't mean to talk much on what would happen 5 years down the line, because honestly - I don't know. Personally, I just know that it's worth spending time building tools that lead us to a direction where it becomes easier.

My philosophy as of "now" (until Anthropic/OpenAI announces something that changes my mind):

1. Reviews were, have been, and "are" highly important. Whether it's a human's code or a code written by an agent, a review is important in every part of your life (not just code :)).
2. Imagining an agent's response as a "commit" and the final response as a PR with files changed as diff, is how I view the current state.
3. We deserve better tooling.

In the direction of the same, I built **prtui** — a terminal UI that treats reviewing a GitHub PR, a local branch, and a Claude Code session as the exact same motion.

![The picker: pick a PR, a branch, or a Claude Code session from one fuzzy list](https://raw.githubusercontent.com/krshrimali/research-reviews/0b22207a9a0e9eb2ff21c3ccb1bbaeb3ff7e5226/rtui/docs/screenshots/picker.svg)

That third one is the part I actually want to talk about, because it's where philosophy #2 stopped being an opinion and turned into code.

## a session is a PR, if you look at it right

Here's the thing about working with an agent that nobody quite talks about: the moment it finishes, the conversation is over, but the changes are still sitting there. You scroll back up through a wall of text to figure out *which* response touched *which* file, and *why*. It's not that different from squinting at a PR with no diff view - all the information is technically there, just not shaped like something you can review.

So prtui just... shapes it that way. Point it at a local Claude Code session and it opens exactly like a PR would: every prompt-and-response exchange becomes a commit, the response text sits where a commit message would, and any file edits render as an actual diff underneath - not reconstructed after the fact, but pulled straight from the structured patches Claude Code already recorded.

![A Claude Code session's turns, shown as commits](https://raw.githubusercontent.com/krshrimali/research-reviews/0b22207a9a0e9eb2ff21c3ccb1bbaeb3ff7e5226/rtui/docs/screenshots/claude_session_commits.svg)

You get a Files panel, a Commits panel, a Diff view. Select a turn and you see its response sitting right next to the diff it produced - the actual prompt, the actual reply, the actual patch, in one place:

![One turn's response and diff, side by side](https://raw.githubusercontent.com/krshrimali/research-reviews/0b22207a9a0e9eb2ff21c3ccb1bbaeb3ff7e5226/rtui/docs/screenshots/claude_session_diff.svg)

You comment on a line the same way you'd comment on a line in a real PR:

![Composing a suggested-change comment](https://raw.githubusercontent.com/krshrimali/research-reviews/0b22207a9a0e9eb2ff21c3ccb1bbaeb3ff7e5226/rtui/docs/screenshots/compose.svg)

You get a net "since this session started" view when you want the whole arc instead of the blow-by-blow. `w` toggles between the two.

Nothing about that required a new mental model. It required believing the old one already fits, and building the thing that makes it visible.

## the boring parts still matter more than they get credit for

None of this works if the underlying review experience isn't actually good, so most of what's in prtui is just... a review tool, doing review-tool things. GitHub-accurate colors. Neovim keys. Inline threads that survive a rebase and get marked outdated instead of silently vanishing.

![Reviewing a diff, with an inline thread and syntax highlighting](https://raw.githubusercontent.com/krshrimali/research-reviews/0b22207a9a0e9eb2ff21c3ccb1bbaeb3ff7e5226/rtui/docs/screenshots/diff.svg)

Split diffs when unified doesn't read well:

![Side-by-side split diff](https://raw.githubusercontent.com/krshrimali/research-reviews/0b22207a9a0e9eb2ff21c3ccb1bbaeb3ff7e5226/rtui/docs/screenshots/split_diff.svg)

A picker that mixes PRs, branches, and sessions into one fuzzy-searchable list, because "what am I supposed to be looking at today" is its own kind of overhead. Timestamps in your own timezone, because "3 hours ago" shouldn't require doing math:

![Timeline of commits and reviews, in local time](https://raw.githubusercontent.com/krshrimali/research-reviews/0b22207a9a0e9eb2ff21c3ccb1bbaeb3ff7e5226/rtui/docs/screenshots/timeline.svg)

An async review runs in the background while you keep reading, and a follow-up reply gets a follow-up response instead of starting the conversation over:

![A completed Claude review, followed by a threaded follow-up](https://raw.githubusercontent.com/krshrimali/research-reviews/0b22207a9a0e9eb2ff21c3ccb1bbaeb3ff7e5226/rtui/docs/screenshots/claude_review.svg)

And because I don't think review should be locked to whichever agent happens to be running inside the tool: there's a prompt builder that lets you pick exactly which comments matter, edit the text by hand, and copy the whole thing out to paste into any CLI you want. The tool doesn't need to own the conversation to be useful in it.

None of this is a rewrite of how review works. It's closer to: if a response is a commit and a session is a PR, then everything we already built for reviewing PRs just... applies. That's the whole idea. It's a small claim, and I'd rather make a small claim well than a big one loosely.

## on the name

I'm calling it **prtui** for now, mostly because that's what it's been since the first Neovim-plugin iteration and renaming things has a cost. But "PR" undersells it a bit once a Claude session is a first-class citizen next to a PR, so I'm not fully attached. A few other directions, if you have an opinion:

- **rtui** - just "review tui," drops the GitHub-specific framing. (Also already the name of the project folder, so there's a case for just formalizing it.)
- **anyreview** / **revuni** - leans into "review anything the same way," which is closer to the actual pitch than "PR" is.
- **lazyreview** - it's very explicitly lazygit-shaped, so this one's honest at least.

No strong conviction here. Open to better ones.

---

It's a single static binary, builds offline, no runtime dependencies.

**Code:** [github.com/krshrimali/research-reviews/tree/main/rtui](https://github.com/krshrimali/research-reviews/tree/main/rtui)

**Install:**

```bash
git clone https://github.com/krshrimali/research-reviews.git
cd research-reviews/rtui
cargo build --release
./target/release/prtui            # opens the picker: PRs, branches, Claude sessions
./target/release/prtui .          # jump straight into the current branch
./target/release/prtui 482        # jump straight into PR #482 (needs gh)
```

Needs `git`; `gh` for PR mode; `claude` if you want it to run reviews for you. Comments, sessions, and everything else are yours - stored locally, nothing leaves your machine unless you tell it to.

If "review as a first-class thing, regardless of who wrote the code" sounds like your problem too, I'd like to hear about it.
