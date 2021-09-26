---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2021-09-26
 linktitle: Prefer const_iterators to iterators
 title: "Prefer const_iterators to iterators (Notes)"
 categories:
 - cpp
 - book reading
 tags:
 - development
 - coding
 - cpp
 - notes
 - iterators
 type:
 - post
 - posts
 weight: 10
 series:
 - CPP
 aliases:
 - /blog/notes-prefer-const-iterators-to-iterators/
 toc: false
 comments: true
---

---
**NOTE**

My notes on Chapter 3, Item 13 of Effective Modern C++ written by Scott Meyers.

Some (or even all) of the text can be similar to what you see in the book, as these are notes: I've tried not to be unnecessarily creative with my words. :)

---

![](https://raw.githubusercontent.com/krshrimali/blog/main/assets/cover-images/prefer-const-iterators-to-iteratorspng)

In C++, iterators come handy to point at memory addresses of STL containers. For example,

```cpp
// C++11

std::vector<int> x {11, 9, 23, 6};

// begin() member function returns an iterator, which points to the first
// memory address of the container x
std::vector<int>::iterator it = x.begin();
```

While the general practice is to use `const` whenever possible, but programmers tend to use whenever it's _practical_. `const_iterators` is particularly suggested when you want to use iterators, but you don't need to modify what it points to.

Take an example of the code snippet above, you have the iterator `it` pointing to the beginning position of the container, and if you want to insert a value before this, you just need to pass this iterator to `x.insert()` along with the value, right? You don't need to modify the iterator. In such cases, `const_iterator` will be a better choice.

But, this is all for C++-11 and above. In C++-98, `const_iterator` wasn't just ready:

```cpp
// C++-98
// Without using const_iterator

// C++-98, initializing a vector wasn't that trivial as it is now
const int values[] = {11, 23, 6};
std::vector<int> x (values, values+3);

// Want to insert 9 before 23 here
std::vector<int>::iterator it = std::find(x.begin(), x.end(), 23);
x.insert(it, 9);
```

While this will work in C++-98, but since we don't modify the iterator `it`, using `const_iterators` is a better choice:

```cpp
// C++-98: this won't compile

// Not using aliases here, C++-98 didn't have the support for aliases
// (was introduced in C++-11)
// Using these typedefs makes it easier to reuse them
typedef std::vector<int>::iterator it;
typedef std::vector<int>::const_iterator c_it;

// C++-98, initializing a vector wasn't that trivial as it is now
const int values[] = {11, 23, 6};
std::vector<int> x (values, values+3);

c_it ci = std::find(static_cast<c_it>(x.begin()), static_cast<c_it>(x.end()), 23);
x.insert(static_cast<it>(ci), 9);
```

If you compile the code snippet above using C++-98 (if you are using `g++`, use: `g++ <filename>.cpp -std=c++-98`), you will hopefully get an error similar to:

```cpp
main.cpp:10:14: error: no matching conversion for static_cast from 'c_it' (aka '__wrap_iter<const int *>') to 'it' (aka '__wrap_iter<int *>')
    x.insert(static_cast<it>(ci), 9);
             ^~~~~~~~~~~~~~~~~~~
```

As you can probably notice, it says "no matching coversion for `static_cast` from `c_it` to `it`", that means in C++-98 there was no straight forward way to cast `const_iterator` to `iterator`. The author does point that there are some reall non-trivial ways to get around, but those are out of the scope of this blog and the book as well.

A few observations in the snippet above:

1. In `std::find` we cast `x.begin()` iterators to `const_iterator` (`c_it`) because in C++-98, there was no simple way to get a `const_iterator` from a non-const container.
2. The reason we cast our `const_iterator` (`ci`) back to `iterator` in the call `x.insert()` is: in C++-98, locations for insertions (and erasures) could only be specified by iterators, not const iterators.

In fact, in C++-11, there is no simple way to convert `const_iterator` to `iterator`.

Here comes C++-11 now, they introduced `cbegin()` which returns a `const_iterator` instead, similarly `cend()` member function exists.

```cpp
// In C++-11, initializing of a vector got easier
std::vector<int> x {11, 23, 6};

// could have used auto here, but just typing the type for understanding 
// Notice the use of cbegin(), cend() instead of static_cast<c_it>(x.begin()), ...
std::vector<int>::const_iterator ci = std::find(x.cbegin(), x.cend(), 23);

x.insert(ci, 11);
```

This will compile successfully, make sure to pass `-std=c++11` flag while compiling if you are using `g++` to make sure you are using C++-11.

It's near this time, isn't it?

Only place where C++-11 comes up a bit short is, when you want to use non-member functions (in case you are writing a generic code for your library, see example below):

```cpp
// This is a generic function which will find targetVal in a container
// Use of decltype discussed before
template<typename C, typename V>
auto find_value(C& container, const V& targetVal) -> decltype(std::begin(container)) {
    // Notice the use of non-member cbegin and cend functions here
    // Note: member functions would have looked like: container.cbegin(), container.cend()
    auto it = std::find(std::cbegin(container), std::cend(container), targetVal);
    return it;
}
```

If you try to compile this using C++-11 `-std=c++11` flag, this will fail with an error like:

```cpp
main.cpp:6:25: error: no matching function for call to 'begin'
    auto it = std::find(std::cbegin(container), std::cend(container), targetVal);

main.cpp:6:49: error: no matching function for call to 'end'
    auto it = std::find(std::cbegin(container), std::cend(container), targetVal);
```

In C++-11, they failed to add `cbegin, cend, rbegin, rend, crbegin, crend` as member functions (but `begin, end` were added). This was later rectified in C++-14, so if you compile the code above using `-std=c++14`, this won't fail anymore.

If you are using C++-11, you can get around by defining a `cbegin()` function:

```cpp
template<class C>
auto cbegin(const C& container) -> decltype(std::begin(container)) {
    return std::begin(container);
}
```

The reason using `std::begin` works here, because in C++-11, if you pass a reference to `const` version of the container to `std::begin`, it will return a `const_iterator` (notice that we pass `const C& container` in the arguments).

The whole gist is to use `const_iterator` whenever possible. C++-14 tidied up the usage, however C++-11 added required support and features.

Thank you for reading!
