---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2024-02-26
 linktitle: "Building a ChatBot from your Documentation Website | DocsGPT"
 title: "Building a ChatBot from your Documentation Website | DocsGPT"
 categories:
 - projects
 - rust
 tags:
 - project
 - deep learning
 - LLM
 - rust
 type:
 - post
 - posts
 weight: 10
 aliases:
 - /blog/docs-gpt-part-1/
 toc: false
 comments: true
---

Hi everyone! Been a long time, thought I should talk about an ongoing project I'm working on.

## Introduction - What are we trying to do here?

Lemme start with some context and disclaimer first:

> This was a part of an interview process in one of the amazing startups, and I wanted to extend it to an end-to-end project (kinda out of scope from the requirement of that interview process). I won't be naming the startup here to help keep them anonymous and candid for their future candidates.

Alright, so here it begins. Imagine having a documentation website, and you would like to finetune a ChatBot Model to help answer your questions. That's it, that's the problem. Let's break it down on why this is an interesting problem to solve:

**For learning?**

1. It involves a lot of data preprocessing and cleaning. You'll also have to automate the data scraping and cleaning process.
    - It's probably safe to assume that generally all documentations are hosted somewhere on GitHub or any other platform, but to make it more complex - let's not use that assumption.
    - We'll have to scrape the data from the website, and clean it to make it ready for the model to consume.
    - Automating this process and by just using a single documentation link is a good challenge to solve.
    - A ChatBot Model takes an input of prompt and answer (kind of an _instruction dataset_ format) and we'll have to convert the documentation into this format. This is not as straight forward as it sounds, specially when you want to have minimal human intervention. More on this later.
2. Finetuning an LLM Model:
    - Always good to learn how to finetune an LLM model, because training it from scratch is never going to be _feasible_ for all of us (this includes the constraint on lack of resources, motivation and time, oh and also _need_).
    - The choice we make for which model to use is going to teach us a lot. Just in the exploring phase, we'll be going through multiple models that exist and will try setting up priorities on the "What works for us" question.

**For the product?**

Very honestly, I don't think there is a _huge_ product goal here. It's more of a learning project than a product project. But, if I were to think of a product goal, it would be to have a ChatBot Model that can answer questions from the documentation website. This can be used for customer support, or for internal documentation search, or for any other use case where you think a ChatBot can be helpful. In addition to this, I do think that this can be extended to something that is not just a documentation but a lot of text on websites.

**For fun?**

That's why I'm using Rust here. I know this question is going to come up quite a lot, so lemme answer this first.

**WHY RUST?**

- I honestly would love to see the performance of Rust in the data preprocessing and cleaning phase.
- It would be nice to see where does the data engineering ecosystem stand w.r.t Rust. We've all (probably?) used beautifulsoup in Python to scrap data from websites, and data cleaning/preprocessing libraries, but I'm excited to see where does Rust stand in this.
- I've been using Rust for some time now, and am pretty comfortable in _exploring_ the ecosystem with this project.
- Writing a ChatBot interface would be fun in Rust.
- Finetuning a model in Rust... hmm, I'm honestly not sure what's the state of [https://github.com/LaurentMazare/tch-rs](Rust bindings for PyTorch C++ API) - so it's something I'm very much looking forward to. I'm honestly nervous about this part, but let's see.
- Using a single language for the whole end to end flow would make it easier for me to automate everything including testing and workflows.

As always, I just want to point out that language you use isn't the topmost criteria of any project IMO. First should be, whether it got delivered to the users and if they are happy with it. So, yes, please feel free to port it to some other language of your choice and try out the ecosystem for yourself to learn and grow your confidence :)

## Plan

> I've been live streaming my work on this project on my YouTube channel here: https://youtube.com/c/kushashwaraviShrimali. Please feel free to check it out if you're interested.

1. Pick up a sample documentation website that we can use for this project. I'm picking up [PyTorch docs website](https://pytorch.org/docs/stable/index.html), it's well maintained, and the format is tricky enough to automate things for other websites in the future.
2. Input to this flow is going to be a simple documentation website link (of the index page).
    a. We'll have to fetch all the hyperlinks that are "internal" to the documentation website, and then fetch the content of those hyperlinks.
    b. We'll have to skip fetching content for "external" hyperlinks for now to avoid a lot of unrelated data (not really unrelated, but we can enable it easily if someone wants it).
    c. Output of this step should be: we have all the data in the text format from HTML webpages.
3. Convert this data into the format of ChatBot model.
4. Finetune the model by passing that data into a model of our choice.
5. Create a ChatBot interface to deploy the model (more like an API end-point for now).
6. Deploy the model to the ChatBot interface, or update the API end-point.

The very tricky part is, Step 3 here. Ideally, a ChatBot model takes input of the following format:

```
prompt: "What is the function of `torch.nn.functional.relu`?"
answer: "Applies the rectified linear unit function element-wise."
context: <optional>
... // other properties
```

The names (of the keys) can differ, but if you look at the format, it's more like an instruction dataset. We'll have to convert the documentation into this format.

**Question**: How would you convert a given "text" into the format above?

Let's just say, your task is to convert "this" blog that you're reading right now (thank you for being here btw ❤️) into a prompt-answer format (can leave `context` for now for simplicity).

I'm going to come back with another blog to discuss my solution, but for now, leaving this blog at this to let y'all ponder over this and come up with some interesting approaches.

## YouTube!

Sorry for the shameless plug here, I mean not really shameless since it's still my blog haha, but... I don't want to miss out on telling you that I've been live streaming my work on this project on my YouTube channel here: https://youtube.com/c/kushashwaraviShrimali. By the time I'm writing this, there have been 2 videos out:

- [Let's finetune a model for a ChatBot](https://www.youtube.com/watch?v=-3Cy-IxvvdA)
- [Fetching dataset for finetuning a model for a ChatBot](https://www.youtube.com/watch?v=Dm7Dz_-yZss)

There are more videos coming, and I hope that they help you out with honest development views. We all fail, none of this happens in 5 minutes, 10 minutes and so on. I wanted to be candid with whatever I develop, and I hope that if nothing - it at least helps y'all with some motivation to keep going on your projects.

I am grateful to you all for the love and support you've shown me, and I hope that I can give back to the community in some way or the other. I'm always open to feedback, and I hope that I can help you out with your projects in some way or the other. Feel free to reach out to me on [Twitter](https://twitter.com/kushashwa).

## Discord!

Yep, we also have an active discord channel, so please feel free to join and chat with all of us there. Link: https://discord.gg/nh2KuAX3V8.
