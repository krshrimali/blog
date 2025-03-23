---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2025-03-23
linktitle: "Revamping my Rust Project"
title: "Progress Update: Context Pilot (Revamping)"
categories:
 - project
tags:
 - development
 - coding
 - rust
type:
- post
- posts
weight: 10
series:
- CPP
aliases:
- /blog/progress-context-pilot-mar-2025/
toc: true
comments: true
---

I've had many iterations on this project that I'm going to talk about today, over the last 1.5-2 years. There are good and bad things about it. Good is that I'm persisting with completing it one day, bad is that I've not done it yet.

In this blog, I'll quickly touch upon why it has taken so much time and what's happening behind the scenes.

## About the project:

For a piece of code, this project is going to help you with questions like:

"Where is this logic tested?"
"Which other features does this logic mostly pair with?"
"What other things are dependent on this logic?"
"Who is the right person to reach out to, for any queries?"

I hope these points are enough motivation for someone to understand the importance of this project.

## Progress:

I've had a [working model](https://github.com/krshrimali/context-pilot-rs) in 2023 when I started, and plugins ready for [neovim](https://github.com/krshrimali/context-pilot.nvim) and [vscode](https://github.com/krshrimali/context-pilot-vscode) but I realized this project - for a better direction - needs to act like an LSP. Do a lot of async work, like indexing, and make sure results are quicker and reliable.

Now, converting the initial binary code into server, wasn't easy at all, for several reasons:

1. I started with a simple JSON as the DB, for initial PoC. JSON is not scalable, but that wasn't the bottleneck back then. Bottelneck was reading a huge JSON file - so the immediate solution was to use DB Sharding concept - divide your huge file into chunks, and know which one to read when a user queries.
2. Making this a proper async server hasn't been easy. Rust (or for that matter, any language) async programming comes with its own debugging issues, and complex code. I've had to rewrite the codebase several times to make it work.

And of course, apart from the technical excuses, there has been life:

1. Work has kept me very busy, for good. Of course, no excuses but that's what pays me and I like being religious towards it - so yep, I enjoy spending most of my time there.
2. Saturation - Of course, working on a single thing for 2 years can get tiring. I've had some other projects picked up, and targeting physical fitness as well, so yes - I've not really spent 2 years on this project only :D obviously!

Anyways, there is some motivation again to help finish this. Mostly for the reasons that I want to use it personally, and I think it is going to be of huge help to me at work and personally as well.

## What's next?

I'm going to revamp this whole project. The way it was designed before, doesn't seem right to me anymore. I think I had too many API details exposed on the Database level for the sake of making it work:
```rust
#[derive(Default, Clone)]
pub struct DB {
    pub index: u32,          // The line of code that you are at, right now? TODO:
    pub folder_path: String, // Current folder path that this DB is processing, or the binary is running
    pub curr_items: u32,     // TODO:
    pub mapping_file_name: String, // This is for storing which file is in which folder/file? <-- TODO:
    pub current_data: DBType, // The data that we have from the loaded DB into our inhouse member
    pub db_file_path: String,
    pub mapping_file_path: String,
    pub mapping_data: MappingDBType,
    pub curr_file_path: String,
    pub workspace_path: String,
}
```

As you can already see, this is just too much detail for - even me to understand after some time. I know, at some point of time, even if this works, I'm going to face the issue of "Wait, what does this mean? Why did I write it?". So, better fix it now. It's also a code quality thing I've in mind that I hate debugging things further. I've had some luck while fixing [here](https://github.com/krshrimali/context-pilot-rs/commit/d0aa6bea5c0ed0101c2b37c3ac30b6f959ba8aa7) where I was at least able to find the bug, but then fixing it would just need me to fix the DB asynchronous writing and reading.

It's not ergonomic for me and the readers as well to look at the piece of code in the current state and understand what caused what :)

I'll share more technical details in the next blog, but for now, this would be it.
