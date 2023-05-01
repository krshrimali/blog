---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2023-05-01
 linktitle: "Daily Update - 1st May 2023"
 title: "Daily Update: 1st May 2023"
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
 - /blog/daily-update-01-may-2023/
 toc: false
 comments: true
---

Interesting day, lots of design stuff for the [project we've been working on](https://github.com/krshrimali/keystroke-store-rs).

1. Designing flow for the word combinator service
    - This is actually tricky, as we are figuring out how we'll figure out the keystrokes into words/phrases (I'd like to call them _entities_ at one point of time).
    - The algorithm is close, and I'm particularly hopeful about it:
        - It considers some edge cases of mouse events, sitting idle, and gives user the control what they would like to choose.
        - More on this very soon!
2. Boring nerdy stuff: Exploring fzf
    - I wanted to have fzf previews height changed to 100%, finally changed my zsh config for that. It looks much better now.
    - Then figured out that I'm using outdated formula for fzf, and I'll end up going through fzf release notes to see what has changed over the last few releases.
        - It's usually a good practice I believe to go through the release notes, and be aware of the tools you use.
3. Work day tomorrow, so doing some early readings.
    - Of course can't share details, but yep, going to be more occupied now.

A lot of TODOs from ~yesterday~ day before yesterday are left 🥺, I'll move them to tomorrow, yay! Procrastination, let's go 😆🎉

TODOs:

1. Explore HVM: https://github.com/HigherOrderCO/HVM, looks interesting at least.
2. Read through: [Specifying and Verifying Higher-order Rust Iterators](https://hal.science/hal-03827702v2/document).
3. Read through: [How does async rust work](https://bertptrs.nl/2023/04/27/how-does-async-rust-work.html)
4. Record a video for YouTube!

Alright, thank you all for reading. :) See y'all tomorrow!
