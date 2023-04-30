---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2023-04-30
 linktitle: "Daily Update - 30th April 2023"
 title: "Daily Update: 30th April 2023"
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
 - /blog/daily-update-30-april-2023/
 toc: false
 comments: true
---

Lovely day, had my friend [imsrbh](https://github.com/imsrbh) come over and we were talking about the project I wanted to do. He had some ideas and of course some experience with Kafka, so he helped me setup Kafka and docker on my machine, and that's how it all started.

1. Setting up Kafka and Docker on my machine:
   - Refer to [this blog](https://medium.com/@fengliplatform/kafka-broker-setup-using-docker-image-33f7a8081a07#:~:text=1%20Setup%20Kafka%20cluster%20on%20Windows%20laptop%201,instance%20...%205%201.5%20Create%20Kafka%20topic%20) for Kafka setup.
   - We verified by running a sample producer-consumer app in Python and it worked.
2. [Starting to implement the core logic of getting key strokes in Rust](https://github.com/krshrimali/keystroke-store-rs)
   - I'm using `rdev` library for this, it was decent.
   - Was wondering how I can convert the keystrokes to strings, apparently it was a Rust Enum.
   - Fortunately, they had a feature `serialize` which would help me do just that. Now it's quite smooth.
3. Implementing Kafka Producer-Consumer in Rust
   - Kafka has a client in Rust, `cargo add kafka` will help.
   - Wrote Kafka Producer and Consumer referring to their official documentation.
   - It works flawlessly.
   - We were sending the keys as `&[u8]` and had to convert these to strings back at consumer (need to proper error checking there)
   - Producer repo: https://github.com/krshrimali/keystroke-store-rs
   - Consumer repo: https://github.com/krshrimali/keystroke-consumer-rs

A lot of TODOs from yesterday are left, I'll move them to tomorrow, yay! Procrastination, let's go 😆🎉

TODOs:

1. Explore HVM: https://github.com/HigherOrderCO/HVM, looks interesting at least.
2. Read through: [Specifying and Verifying Higher-order Rust Iterators](https://hal.science/hal-03827702v2/document).
3. Read through: [How does async rust work](https://bertptrs.nl/2023/04/27/how-does-async-rust-work.html)
4. Record a video for YouTube!

Alright, thank you all for reading. :) See y'all tomorrow!
