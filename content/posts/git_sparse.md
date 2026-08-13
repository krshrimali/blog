---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2026-08-13
linktitle: "Digging into git sparse-checkout"
title: "What Actually Happens with git clone --sparse?"
categories:
 - git
tags:
 - git
 - development
 - coding
type:
- post
- posts
weight: 10
---

For huge repositories, we all have done `git clone --sparse` once. And it's an interesting case study.

This came into my attention, thanks to nerd-fonts repository where one of the suggestions to _only clone a particular sub-directory_ was to:

```bash
# We'll come to --filter=blob:none in some other repository
git clone --filter=blob:none --sparse git@github.com:ryanoasis/nerd-fonts.git
cd nerd-fonts
git sparse-checkout add patched-fonts/JetBrainsMono
```

`patched-fonts/JetBrainsMono` is the path of the subdir we wanted to explicitly clone, and skip all others.

I was really curious about how it works, so I dug deeper. Hopefully this blog gives you an idea of how this works from a user command to the main logic of this command.

To begin with, it's important for us to distinguish b/w checkout and clone.

In clone, you've two steps:

1. Fetch (fetch objects from network)
2. Checkout (write files into the working directory)

`--sparse` only affects the checkout phase.

See as an example here:

```c
// builtin/clone.c:1626
if (option_sparse_checkout && git_sparse_checkout_init(dir))
    return 1;

junk_mode = JUNK_LEAVE_REPO;
err = checkout(submodule_progress, &filter_options, ...); // <--- checkout happens here, which is skipped when sparse
```

It's actually quite interesting to see `git_sparse_checkout_init` function:

```c
static int git_sparse_checkout_init(const char *repo)
{
    struct child_process cmd = CHILD_PROCESS_INIT;
    // Note the command construction here...
    strvec_pushl(&cmd.args, "-C", repo, "sparse-checkout", "set", NULL);
    cfg->apply_sparse_checkout = 1;
    cmd.git_cmd = 1;
    run_command(&cmd);  // literally spawns: git -C <repo> sparse-checkout set
}
```

So, essentially, job of `--sparse` is:

1. First clone fully (fetch happens exactly as what happens without `--sparse`).
2. Just before checkout, perform `git sparse-checkout set`.
    - This only writes a "root-level files" pattern.
3. Post this, the checkout only writes the patterns.

The biggest gotcha here is: `--sparse` doesn't really reduce network transfer. All the history, all the blobs --- are all downloaded nonetheless. The only difference is, working directory only sees *root files*.

To save bandwidth, there's another option: partial clone `--filter=blob:none` which is a separate flag --- maybe we'll discuss this one day? :)

---

What happens when you run `git sparse-checkout set dirName1 dirName2`? `git` doesn't store these directory names, but instead stores in a format of gitignore like patterns. This is called 'cone mode', and happens through two hashmaps (recursive and parent). We'll be discussing this in the upcoming blog, but at first - I hope this short blog got you excited about what happens with `--filter=blob:none` as well? :)
