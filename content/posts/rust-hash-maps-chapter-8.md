---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2022-01-09
linktitle: Common Colleections (vector and strings) in Rust 
title: "Common Collections (Vector and Strings) in Rust [Notes]"
categories:
 - rust
tags:
 - development
 - coding
 - rust
 - notes
type:
- post
- posts
weight: 10
series:
- Rust
aliases:
- /blog/rust-common-collections-part-1/
toc: true
comments: true
---

## Chapter 8: Common Collections (Hash Maps)

In the [previous blog](https://krshrimali.github.io/posts/2022/01/common-collections-vector-and-strings-in-rust-notes/), I shared my notes on strings and vectors in Rust, and in this post we'll cover Hash Maps. I personally have found their use in competitive programming, a lot, but hopefully as we move on, we'll see lots of use-cases in real-life problems.

## Hash Maps

Hash Maps: `HashMap<K, V>`

- You can't access using indices, but through keys.
- Hash Maps store data on heap.
- Hash Maps are homogenous (all keys must have same type, and all values must have same type).
- Use `std::collections::HashMap` to bring `HashMap` to scope.

**Creating a New Hash Map**

First Way:

```rust
use std::collections::HashMap;

let mut scores = HashMap::new();
// Now insert key, val pair
scores.insert("Kush", 3);
scores.insert("Kushashwa", 10);
```

Second Way: In case you have keys and values stored in two different vectors, and want to generate a hashmap from them, use `collect()`.

```rust
use std::collections::HashMap;

let teams = vec![String::from("Blue"), String::from("Yellow")];
let initial_scores = vec![10, 50];

// Types will be infered by Rust from the data in the vectors
let mut scores: HashMap<_, _> = teams.into_iter().zip(initial_scores.into_iter()).collect();
```

Why `HashMap<_, _>`? `collect()` method can store values into different datastructures, and we need to specify the type of `scores`. For the types of keys and values, Rust can infer the types itself - hence we specify `_`.

I was curious what `into_iter()` does, and [here](https://stackoverflow.com/a/34745885) is a very interesting answer to `into_iter()` vs `iter()` on Stackoverflow. Someone mentioned [this blog post](https://hermanradtke.com/2015/06/22/effectively-using-iterators-in-rust.html/) in the comments, I've this as a TODO - but from the looks of it, it might be useful.

If you are curious what `teams.into_iter().zip(initial_scores.into_iter())` do? Great, check this:

```rust
fn main() {
    let teams = vec![String::from("Blue"), String::from("Yellow")];
    let initial_scores = vec![10, 50];

    let tuple_output = teams.into_iter().zip(initial_scores.into_iter());

    for item in tuple_output {
        println!("{}, {}" ,item.0, item.1);
    }
}
```

Outputs:

```rust
Blue, 10
Yellow, 50
```

So clearly, creating a vector of tuples (of a `String` and `Integer`). Maybe try passing a vector of different length to `.zip()` function? ;)

## Hash Maps and Ownership

Ownership is always the center of discussion when it comes to Rust. When you create a hashmap, and insert `String` objects, `i32` values, the ownership behaves differently:

1. For types that implement `Copy` trait, like `i32`, the values will be copied to the hashmap.
2. For `String` values (owned values), the values are moved into the hashmap and the hashmap will be the owner.

See the following example and corresponding error:

```rust
use std::collections::HashMap;

fn main() {
    let str1 = String::from("Kush");
    let str2 = String::from("Name");

    let mut map = HashMap::new();
    map.insert(str1, str2);

    println!("{}", str1);
}
```

```rust
   |
4  |     let str1 = String::from("Kush");
   |         ---- move occurs because `str1` has type `String`, which does not implement the `Copy` trait
...
8  |     map.insert(str1, str2);
   |                ---- value moved here
9  | 
10 |     println!("{}", str1);
   |                    ^^^^ value borrowed here after move
```

As you can see, value was moved when `map.insert(str1, str2)` was called. One important point, that I'll just take from the book:

> If we insert references to values into the hash map, the values won’t be moved into the hash map. The values that the references point to must be valid for at least as long as the hash map is valid.

(This is covered in detail in Chapter 10, so let's save it for later).

## Accessing Values in a Hash Map

Use `<HashMap>.get(<Key>)` function to get the value corresponding to the key. Please note that it returns `Option<&V>` where `V` is the type of the value.

```rust
use std::collections::HashMap;

fn main() {
    let str1 = String::from("Kush");
    let str2 = String::from("Name");

    let mut map = HashMap::new();
    map.insert(str1, str2);

    let val = map.get(&String::from("Kush"));
    println!("{}", val.unwrap());
}
```

Outputs: `Name`.

Since `map.get(&String::from("Kush"))` returns `Option<&String>` object, we need to `unwrap()` it in order to print it. Here is [an interesting post](https://www.ameyalokare.com/rust/2017/10/23/rust-options.html) on why using `unwrap()` is not the best idea, and what other options we have. I used `unwrap()` here, since I knew it is not `None`.

Iterating through a hash map is also easy in Rust:

```rust
// Use the same code as above
for (key, value) in &map {
    println!("{}: {}", key, value);
}
// Output:
// Kush: Name
```

## Updating a Hash Map

Note that you can only have one value corresponding to a key. Let's consider our options:

1. **Overwriting a value**: `insert()` twice, and the new value will replace the old value.
2. **Only insert if key has no value**:
    * Use `entry(<Key>)`, it returns an `Enum`: `Empty` (represents a value that might or might not exist).
    * Call `or_insert` on the enum, which inserts a value if key doesn't exist.
    * `or_insert` returns a mutable reference to the value present, or to the new value inserted.

    ```rust
    use std::collections::HashMap;

    fn main() {
        let mut scores = HashMap::new();
        scores.insert(String::from("Blue"), 10);

        scores.entry(String::from("Yellow")).or_insert(50);
        scores.entry(String::from("Blue")).or_insert(50);

        println!("{:?}", scores);
    }
    // Outputs
    // {"Blue": 10, "Yellow": 50}
    ```
3. **Updating a value based on the old value**: Comments in the code should help explain the example.

    ```rust
    use std::collections::HashMap;

    fn main() {
        let text = "hello world wonderful world";

        let mut map = HashMap::new();

        // "hello", "world", "wonderful", "world" - values of word
        for word in text.split_whitespace() {
            // if the map has an entry for word, return the count of it
            // else, insert 0 and increase the counter by 1
            // note that count is mutable reference
            // so it needs to be de-referenced (in order to use it)
            let count = map.entry(word).or_insert(0);
            *count += 1;
        }

        println!("{:?}", map); 
    }

    // Outputs:
    // {"world": 2, "wonderful": 1, "hello": 1}
    ```

## Hashing Functions

By default, Hash Maps in Rust use [`SipHash`](https://en.wikipedia.org/wiki/SipHash) hashing function, but you can use your own as well - it should implement `BuildHasher` trait. More on this is discussed in Chapter 10.

That's it for Chapter 8, thank you for reading. :)

## Note

---
**NOTE**

These are just my notes, or things I write down while/after reading the chapters/blogs or going through resources. I like sharing them, for everyone's and also my memory. At no point I say or mean that these should be preferred or read "over" the original resource mentioned. But as always, I'm open for feedback and/or suggestions, so feel free to comment here on the blog (just be nice, is all I ask for).

---
