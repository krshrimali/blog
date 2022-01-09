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

## Chapter 8: Common Collections

These are my notes from the [chapter-8](https://doc.rust-lang.org/book/ch08-00-common-collections.html) of [rust book](https://doc.rust-lang.org/book). Please scroll down to the bottom (`Note`) section if you are curious about what this is.

### 8.1: Storing Lists of Values with Vectors

`Vec<T>` collection type discussed, aka vector:
    * By default contiguous.
    * All values should be of same type.

```rust
// Creation
let v: Vec<i32> = Vec::new();

// vec! macro for convenience
// default integer type is i32
let v = vec![1, 2, 3];

// Modifying
let mut v = Vec::new();
// Rust infers the type from the elements pushed here
v.push(5);
v.push(6);
// ...

// Dropping
// a vector is freed, when it goes out of scope
{
    let v = vec![1, 2, 3, 4];
    // ...
} // <-- v goes out of scope here, and hence memory is freed as well

// Reading Elements of Vectors
let v = vec![1, 2, 3, 4, 5];
// First way:
let third: &i32 = &v[2];
println!("The third element is: {}", third);

// Second way:
match v.get(2) {
    Some(num) => println!("The third element is: {}", num),
    None => println!("There is no third element."),
}
```

`.get(&index)` method allows you to handle out of range errors.

> When a program has a valid reference, the borrow checker enforces the ownership and borrowing rules to ensure this reference and any other references to the contents of the vector remain valid.

Following example will fail:

```rust
let mut v = vec![1, 2, 3, 4, 5];
let first = &v[0];
v.push(6);
println!("The first element is: {}", first);
```

- Adding an element to a vector may require the old memory chunk to be transferred to a new space, causing old memory disallocation for the object `v`.
- Accessing `&v[0]` can thus be dangerous, and hence the borrowing rules prevent programs from ending up in that situation.

```rust
// Iterating over the values in a vector
let v = vec![100, 32, 57];
// get immutable references to each element in a vector v
for i in &v {
    println!("{}", i);
}

// get mutable references to each element in a mutable veector v
let mut v = vec![100, 32, 57];
for i in &mut v {
    *i += 50;
}
```

You can use an `enum` to store multiple type values in a vector, but indirectly, this is how:

```rust
enum SpreadsheetCell {
    Int(i32),
    Float(f64),
    Text(String),
}

let row = vec![
    SpreadsheetCell::Int(3),
    SpreadsheetCell::Text(String::from("blue")),
    SpreadsheetCell::Float(10.12),
];
```

Note how `row` vector still has same types (of `enum SpreadsheetCell`) but can hold values of multiple types through enums.

### 8.2: Storing UTF-8 Encoded Text with Strings

In Rust, strings are implemented as a collection of bytes + some methods to provide useful functionality when those bytes are interpreted as text.

(both types listed below are UTF-8 encoded)

- Rust has only one string type in the **core language**: string slice `str` (usually seen in borrowed form: `&str`).
- Rust's standard library provides `String` type: (not coded into the core language):
    - It's _growbable, mutable, and owned_ UTF-8 encoded string type.

There are other string types included in Rust's standard library: `OsString, OsStr, CString, CStr". Types ending with `String` refer to owned variants, while types ending with `Str` refer to borrowed variants. (not discussed in the book/chapter)

```rust
// Creating a new string
let mut s = String::new();

// If you have some initial data, use to_string method
// this is available on any type that implements the Display trait

// Following three methods are valid
// First
let data = "initial contents"; // a string literal
let s = data.to_string();
// Second
let s = "initial conents".to_string();
// Third
let s = String::from("initial contents");

// Updating a string
let mut s = String::from("foo");
s.push_str("bar"); // s is now "foobar"

// Appending to a string
// using push_str and push
let mut s = String::from("foo");
s.push_str("bar");

let mut s1 = String::from("foo");
let s2 = "bar";
// We don't take ownership of s2 here
// To ensure that we can still use s2 even after appending contents to s1
s1.push_str(s2);
println!("s2 is {}", s2);
println!("s1 is {}", s1);

// Use push to append single character to the String
let mut s = String::from("lo");
s.push('l'); // now "lol"

// Concatenation with + operator or the format! macro
let s1 = String::from("Hello, ");
let s2 = String::from("world!");
let s3 = s1 + &s2;
```

Consider the following script:

```rust
let s1 = String::from("foo");
let s2 = String::from(" bar");
// The operation takes ownership of s1 here
let s3 = s1 + &s2;
// You can not use s1 after the operation above
println!("s3 is: {}", s3);
```

Following is the error you'll get:

```rust
error[E0382]: borrow of moved value: `s1`
 --> src/main.rs:5:27
  |
2 |     let s1 = String::from("foo");
  |         -- move occurs because `s1` has type `String`, which does not implement the `Copy` trait
3 |     let s2 = String::from(" bar");
4 |     let s3 = s1 + &s2;
  |              -- value moved here
5 |     println!("s1 is: {}", s1);
  |                           ^^ value borrowed here after move

For more information about this error, try `rustc --explain E0382`
```

So what's happening? The `+` operator uses an `add` method whose signature looks like this for our inputs:

```rust
fn add(self, s: &str) -> String {
    // ...
}
```

A few notes about `s` parameter:

1. It's taken by reference. Means you add reference of the second string to the firstt string.
2. You can not add 2 `String` values together, only `&str` to a `String`. (Rust compiler, in our case, coerces the `&String` argument into a `&str`, more on deref coercion later).

Note about `self` parameter:

1. `add` method takes ownership of `self` (it doesn't have an `&`).
2. The point above implies, `s1` will be moved to the `add` call and no longer be valid after that.

```rust
let s3 = s1 + &s2;
```

The above statement actually:

1. Moves `s1` into the `add` call / takes ownership of `s1` (making it invalid after that)
2. Appends a _copy_ of the contents of `s2`.
3. Returns ownership of the result.

(this process is more efficient than copying).

```rust
// Concatenating multiple strings
let s1 = String::from("tic");
let s2 = String::from("tac");
let s2 = String::from("toe");

let s = s1 + "-" + &s2 + "-" + &s3;

// You can also do:
// Uses reference for all parameters, so no ownership of any here...
let s = format!("{}-{}-{}", s1, s2, s3);
```

Talking about Indexing into Strings:

The following will give an error.

```rust
// Indexing into Strings
// Not like other languages (C++/Python):
let s1 = String::from("hello");
let h = s1[0];
```

Error:

```rust
error[E0277]: the type `String` cannot be indexed by `{integer}`
 --> src/main.rs:3:13
  |
3 |     let h = s1[0];
  |             ^^^^^ `String` cannot be indexed by `{integer}`
  |
  = help: the trait `Index<{integer}>` is not implemented for `String`
```

_Rust strings don't support indexing_. To understand, let's understand how memory storage works for strings in Rust.

A `String` is a wrapper over a `Vec<u8>`. Consider:

```rust
// Hola is 4 bytes long (each of the chars take 1 byte when encoded in UTF-8) and len will be 4
let hello = String::from("Hola");

// Now consider:
let hello = String::from("Здравствуйте");
// Number of bytes stored for hello: 24
// Each unicode scalar value in the string above takes 2 bytes of storage.
```

Hence, indexing into string's bytes will not always correlate to a valid Unicode scalar value. Hence, no indexing support for strings in Rust.

> A final reason Rust doesn’t allow us to index into a String to get a character is that indexing operations are expected to always take constant time (O(1)). But it isn’t possible to guarantee that performance with a String, because Rust would have to walk through the contents from the beginning to the index to determine how many valid characters there were.

Slicing strings:

```rust
let hello = "Здравствуйте";
// This will give you first 4 bytes of hello string
let s = &hello[0..4];
// In hello, every character is of 2 bytes, so s will have Зд
```

With the same `hello` string, what will be the output if we used `let s = &hello[0..1];`? Following error will be raised:

```rust
thread 'main' panicked at 'byte index 1 is not a char boundary; it is inside 'З' (bytes 0..2) of `Здравствуйте`', src/main.rs:3:13
```

Iterating over strings: use the `chars` method.

```rust
for c in "नमस्ते".chars() {
    println!("{}", c);
}

// Output:
//  न
//  म
//  स
//   ्
//  त
//   े

// bytes method will return each raw byte
for b in "नमस्ते".bytes() {
    println!("{}", b);
}

// Output:
// All 18 bytes that made up this string
// 224
// 164
// 168
// 224
// 164
// 174
// 224
// 164
// 184
// 224
// 165
// 141
// 224
// 164
// 164
// 224
// 165
// 135
```

Note: valid unicode scalar values maybe made up of more than 1 byte, like above.

## Note

---
**NOTE**

These are just my notes, or things I write down while/after reading the chapters/blogs or going through resources. I like sharing them, for everyone's and also my memory. At no point I say or mean that these should be preferred or read "over" the original resource mentioned. But as always, I'm open for feedback and/or suggestions, so feel free to comment here on the blog (just be nice, is all I ask for).

---