---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2022-11-15
 linktitle: "Daily Update - 15th November 2022"
 title: "Daily Update: 15th November 2022 - Day 2"
 categories:
 - daily updates
 tags:
 - blog
 - updates
 type:
 - post
 - posts
 weight: 10
 series:
 - Weekly
 aliases:
 - /blog/daily-update-15-nov-2022/
 toc: false
 comments: true
---

Hi everyone, Day 2 of this series of daily updates. Started my day earlier than yesterday, at around 9 AM (work).

**Learning**:

* Watched this nice video from Jason on [The Right Way to Write C++ in 2022](https://www.youtube.com/watch?v=q7Gv4J3FyYE):
  * I like when he advocated on using different compilers, or at least verifying that it works for all (and if not, then you're aware).
  * Interest: take warnings seriously. Need to start doing it, I've been following this with Rust, but C++ never raised Rust-like "good enough" warnings. Might as well start doing it now.
  * Code coverage analysis: hmm, it used to stay at around 87 to 90% for the libraries I worked with. I agree, most of it should be tested, but as the library grows longer, you can't block PRs on coverage (specially by the community). But it's underrated, I've seen developers ignore it until they face the wrath of weird bugs. 100% testing coverage, will always be difficult, but if the goal is kept in that direction, it might reach to 95-100%.
  * Never heard of fuzz testing before...after reading about it, just another word of what we have done before. Never got a name to it though. ;)
  * Ship with Hardening Enabled: Again, no idea about this. I'll have to read about it. Marked as a TODO.
* Missed watching Edward's stream on TorchDynamo, I woke up late. :/ Going to re-watch the stream now. I'll share the notes in a separate blog once I'm done, I could only watch _some_ of it today.
* I've started learning Kernel Fusion, how does it work and why it can help (and when it can not). This is going to be a long road, hopefully I'll be able to share something concrete soon.

**Leetcode Problems**:

* [Longest substring without repeating characters](https://leetcode.com/problems/longest-substring-without-repeating-characters)
* [Clone graph](https://leetcode.com/problems/clone-graph)
  - Note: this was done in C++, Leetcode didn't have Rust added as the supported language for this.
* [Product of Array Except Self](https://leetcode.com/problems/product-of-array-except-self/)
I'm still learning Rust, so it takes some time for me to write the _best_ Rust versions of the codes above, but yeah - doing it the best way I can. I don't want to rush completing tens of problems in a day, to me - that doesn't make sense.

## Ending Words

Felt better as I am slowly collecting myself together. It's going to take some time though, but I aim to be consistent with the things I love doing.
