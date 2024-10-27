---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2024-10-27
 linktitle: "Staying Curious with Linked Lists"
 title: "Where are Linked Lists used?"
 categories:
 - cpp
 - data-structures
 tags:
 - blog
 type:
 - post
 - posts
 weight: 10
 series:
 - Staying Curious
 aliases:
 - /blog/staying-curious-linked-lists/
 toc: true
 comments: true
---

It's the Day-1 of _staying_ curious. I'll talk more about it towards the end, but first - let's get to the topic.

Starting from my college life, I've always been excited to know the "how", "why", "what", "where" questions of each data structure we would study. This series is not just about data structures though, anything that you can imagine with Computer Science - I hope to cover some of those in some more blog posts.

I want to cover Linked Lists today and some of its applications.

> **_NOTE_**: FYI, I did go through some other usages of LinkedLists before on my YouTube Channel: https://youtu.be/Czu5dHq86Tk?si=zng7vUrGNPQwC0hB - if any of you would like to check that out.

## Motivation

Linked Lists are probably only focused for interview preparations (at least from my experience with folks). But I want to show some more interesting things linked lists _already do_ in the world of computers. Let's start with a simple example of reversing a Linked List to serve a revision for most of you:

```cpp
#include <iostream>

struct LL {
    int data;
    LL* next;
};

LL* reverse(LL* head) {
    LL* prev = nullptr;
    LL* current = head;
    LL* next = nullptr;

    while (current != nullptr) {
        next = current->next;
        current->next = prev;
        prev = current;
        current = next;
    }

    head = prev;
    return head;
}

void printLL(LL* head) {
    while (head != nullptr) {
        std::cout << head->data << " ";
        head = head->next;
    }
    std::cout << std::endl;
}

int main() {
    LL* head = new LL();
    head->data = 1;
    head->next = new LL();
    head->next->data = 2;
    head->next->next = new LL();
    head->next->next->data = 3;
    head->next->next->next = nullptr;
    printLL(head);
    LL* reversedHead = reverse(head);
    printLL(reversedHead);
}
```

The output will be simple, we'll have `1 2 3` and `3 2 1` printed in two lines. This is a simple example of reversing a linked list.

But what if I tell you that Linked Lists are also used for garbage collection in programming languages. Yes, that's right! Linked Lists are used to keep track of memory that is not being used by the program and can be freed up. This is just one of the many applications of Linked Lists, and let's explore this further. Why not discuss Garbage Collection a bit?

## Garbage Collection

Note: While the definition might stay constant, but implementation details might vary from language to language.

Garbage Collection is a process of automatically finding and freeing up memory that is no longer being used by the program. This is done by the Garbage Collector, which is a part of the runtime environment of the programming language.

To make it simple, let's consider a simple example:

```cpp
int main() {
    int* ptr = new int(5);
    ptr = nullptr;
    return 0;
}
```

In the above code, we have allocated memory for an integer and then set the pointer to `nullptr`. This means that the memory allocated for the integer is no longer being used by the program. This is where the Garbage Collector comes into play. It will automatically find this memory and free it up so that it can be used by other parts of the program. This is a very simple example, but in real-world applications, memory management can get very complex.

Do note that C++ does not have a Garbage Collector (at least not with the standard library). There are however external libraries that can be used for garbage collection in C++. One of them is the [Boehm-Demers-Weiser Garbage Collector](https://github.com/ivmai/bdwgc).

Going a bit in detail, there are a few strategies that are opted, one of the less popular ones (w.r.t being implemented in languages) is "Free List".

## Free List

`FreeList` is essentially a data structure implemented using `LinkedList` that keeps track of the memory blocks that are not being used by the program. The next time when the program needs memory, it can check the `FreeList` to see if there are any memory blocks that can be reused.

Let's again understand this with an example:

```cpp
struct MemoryBlock {
    int data;
    MemoryBlock* next;
};

MemoryBlock* freeList = nullptr;

MemoryBlock* allocateMemoryBlock() {
    if (freeList == nullptr) {
        // Allocate a new memory block
        return new MemoryBlock();
    } else {
        MemoryBlock* block = freeList;
        freeList = freeList->next;
        return block;
    }
}
```

In the above code, we have a `MemoryBlock` structure that represents a memory block. We have a `freeList` that keeps track of the memory blocks that are not being used. The `allocateMemoryBlock` function checks if there are any memory blocks in the `freeList` that can be reused. If there are no memory blocks in the `freeList`, it allocates a new memory block. This won't work for most of the cases though, mostly because the requirement for the next memory block could be more then what we have in the `freeList`'s head pointer.

There are different variants of how `FreeList` can be implemented, but the basic idea remains the same - to keep track of memory blocks that are not being used by the program. I don't want to copy and paste the content from FreeList's Wikipedia page, but you can read more about it [here](https://en.wikipedia.org/wiki/Free_list). Coming from the same Wikipedia page, apparently - OCaml does use `FreeList` for satisfying its memory allocation requests (source: https://dev.realworldocaml.org/garbage-collector.html). I'll definitely suggest y'all to give it a read.

A very popular strategy is Mark-and-Sweep. I'll cover this in a separate blog post when we highlight Garbage Collection in detail. Please note that, this is simply a strategy and use of LinkedLists is independent of what strategies you use.

Given that y'all might have gain some context already, let's now understand why would we need Linked Lists for Garbage Collection.

## Why Linked Lists?

- Dynamic Size: Linked Lists can grow or shrink in size during the execution of the program. They are stored in the heap memory, which is dynamic in nature.
    - Many of you might be already aware - insertions and deletions are O(1) in Linked Lists.
    - This is because we can just change the pointers and the memory is already allocated.
- No Memory Wastage: Linked Lists do not waste memory. If we have a linked list of size 5, it will only take 5 memory blocks. This is not the case with arrays, where we have to allocate memory for the maximum size of the array.
- Flexible: You can store more complex data in a LinkedList (easily). Data could be of varied size as well.

Enough reasons for us to look at Linked Lists in a different light, right?

If you're curious on more implementation, I was looking at [this](https://github.com/ilies1511/mini_garbage_collector.git) repository, and it's a nicely written simple garbage collector in C. I'll definitely suggest y'all to give it a read.

Think of what you'll want your garbage collector to do post a `malloc` call? How would you want to manage the memory blocks? What if you have a `free` call? How would you want to manage the memory blocks then? Let's answer these questions before wrapping up.

If you remember, the `MemoryBlock` struct we defined earlier, we can use that to manage the memory blocks. We can have a `freeList` that keeps track of the memory blocks that are not being used. When we allocate a new memory block, we can check if there are any memory blocks in the `freeList` that can be reused. If there are no memory blocks in the `freeList`, we can allocate a new memory block. When we free a memory block, we can add it to the `freeList` so that it can be reused later.

```c
struct GarbageCollector {
    MemoryBlock* freeList;
} gc;

MemoryBlock* allocateMemoryBlock() {
    if (gc.freeList == nullptr) {
        // Allocate a new memory block
        return new MemoryBlock();
    } else {
        MemoryBlock* block = gc.freeList;
        gc.freeList = gc.freeList->next;
        return block;
    }
}
```

A good implementation would be to also consider coalescing the memory blocks. This means that if there are two adjacent memory blocks in the `freeList`, we can merge them into a single memory block. This can help in reducing fragmentation and improving memory utilization (specially for the cases when the required size is more than the individual blocks). Maybe something y'all can try implementing? 🚀

For this blog, I hope this would have given you more questions to ask and more things to explore. I'll be back with more such interesting topics in the next blog post. Stay tuned!

Thank you for reading! 🚀
