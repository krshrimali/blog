---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2025-07-29
 linktitle: "Introducing Context Pilot: A Git History Assistant"
 title: "Introducing Context Pilot: A Git History Assistant"
 categories:
 - project
 tags:
 - blog
 - updates
 type:
 - post
 - posts
 weight: 10
 aliases:
 - /blog/announcing-context-pilot/
 toc: false
 comments: true
---

I know we all are developers and with increase in loss of attention now a days (at least I've this), let me quickly note some points down:

- As tempted I was, this blog was not written by any AI agent/model/autocomplete. Same as the project (except the README) - I intended to write this down myself.
- This project is emotionally very close to me, and I'll discuss the story towards the end. For those interested, I'd love if you all give it a read.
- This is only applicable to repositories with "git" as the version history.

----

## What is Context Pilot?

Briefly, this project help answers the questions for you:

1. Who touched this code in the last 2 releases (/N releases)?
2. Why was this changed in the last month? What's the reason?
3. Can you summarize changes to this file/selection over the last 3 months (/N months)?
4. Which files I should look at, if I'm changing the current function?
5. Based on the changes since this function was written, can you tell me how this function has evolved?
6. Do you know why and when this function was made async from sync?

## Demo

Before I even begin, I'll go ahead and share some demos for y'all, hope this excites you?

Here's a demo of "Can you summarize the changes done over last 1 year in a tabular format?" - please note that, this is a prompt on "a selection" and not the whole buffer.

<img src="https://raw.githubusercontent.com/krshrimali/blog/refs/heads/main/assets/blogs/chat-demo.png"/>

How about relevant commits? Here you go:

<img src="https://raw.githubusercontent.com/krshrimali/blog/refs/heads/main/assets/blogs/all-relevant-commits.png"/>

## But I use NeoVim:

I love my terminal, and I love neovim as well. I started with a plugin for neovim and later used ChatGPT(/other agents) to convert it to a VSCode extension. :) So I'll share some demos of neovim as well:

Here's a demo of relevant commits:

<img src="https://raw.githubusercontent.com/krshrimali/blog/refs/heads/main/assets/blogs/relevant-commits-neovim.png"/>

## But I use Emacs/Cursor/JetBrains IDEs!!

I understand, and I did attempt testing for emacs (tested briefly on doom emacs) here: https://github.com/krshrimali/context-pilot.el and for JetBrains IDEs: https://github.com/krshrimali/context-pilot-jetbrains. These both are WIP right now, and I'd probably ask Cursor agent to wrap these up. As long as people want it, I'll be happy to test them soon.

What about Cursor though? - Well Cursor's marketplace has been tricky for me. Users who would want to trust me on installing it via a .vsix file, I'll pubblish it on [context-pilot-vscode](https://github.com/krshrimali/context-pilot-vscode) repository soon. Or y'all can build yourselves as well :)

Please note that, the extensions used LLMs heavily as I don't know all languages. I give credits to the amazing work by Cursor team (specially the agents) for those.

----

## Details

When I started working in open source or any of my previous companies, I always had these questions and I would end up asking my teammates and/or looking at the git blame history. This wasn't quick, `git blame` on the UI is not the easiest of things to do. When you go back, you lose the track of your line number/function. So, I started thinking if I could somehow figure out the "evolution" of a file/selection and use it at my advantage.

That's how the motivation for context-pilot was born. Please note that, at that time (and even now) - I was using neovim as my main editor (and sometimes emacs), so I was not aware of many alternatives at that time. To be honest, I wasn't very keen on exploring existing alternatives in other editors as well, as I thought - it would be intersting to build. Looking back, I think I did the right thing but it's subjective.

Now of course, when you look at the answers, everyone thinks of LLMs. In 2023, agents were not the talk of the town and my brain was still active ( :wink: ). This project, does NOT use any LLM - but gives you the content you can pass to an LLM for getting those answers. The sole purpose of this project was to give you the "relevant commits" for each of your questions. Just pass to the LLM with the diffs (it generates it for you) and ask the right questions. It's easier for me to deliver it to mass without thinking of any privacy concerns anyone would have.

Some notes for those who want to get started:

1. The extension is available on VSCode Marketplace: https://marketplace.visualstudio.com/items?itemName=tgkrs.contextpilot.
2. The extension is available for neovim as well: https://github.com/krshrimali/context-pilot.nvim.
3. It's required for context-pilot to be installed, please see: https://github.com/krshrimali/context-pilot-rs for details.

I know the point 3 (requirement to install the binary separately) kinda sucks, but I'm working on seeing if I can ship it with the plugins. Community members have helped ship it to AUR: https://aur.archlinux.org/packages/contextpilot-git, and there's a homebrew tap as well: https://github.com/krshrimali/homebrew-context-pilot.

----

## Getting Started:

1. Start with installing the contextpilot binary and please make sure that it's in one of your "PATH" environments (example: `/usr/local/bin`, `/usr/bin/`, `~/.local/bin`).
2. Install your editor's extension ([neovim](https://github.com/krshrimali/context-pilot.nvim]), [vscode](https://marketplace.visualstudio.com/items?itemName=tgkrs.contextpilot)).
    - For NeoVim users, please make sure to call `:ContextPilotStartIndexing` to make your calls faster. For VSCode, it automatically does it for you.
3. Play around, if any issues - please log at: https://github.com/krshrimali/context-pilot-rs.

Thank you <3

-----

## Alternatives?

I understand that GitLens (VSCode extension) has the feature of line and file history, and so does JetBrains IDEs ("Local Git History") but given the option to pass things to LLM, I hope it turns out to be more useful than existing solutions.

-----

## Personal Story:

It's hard to stick to a project for more than 2 years, I had many life events during this time - and while everything was streamed on my YouTube channel (https://youtube.com/c/kushashwaraviShrimali) - it was still not easy to find the motivation in between. I do owe this project to my family and the audience of the channel for constantly supporting me with this. This has definitely taught me a lot, and it's still a work in progress.

Why am I writing a blog now when it's 'still not 100% complete/tested'? - Well, it will never be. I need people to use it and report issues. I'll be on the top of fixing most of those, but I need more support and I hope this blog does exactly that.

I've a small demo for you all here: https://www.youtube.com/watch?v=sETsJcaH6JA&t=186s if anyone is interested.

-----

## Technical Details?

I'll come up with another blog post for this. For now, I'd let users try it out and share some constructive feedback.

Thanks for reading!
Kush
