---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2021-08-14
 linktitle: Scoped Enums over Unscoped Enums
 title: "Prefer Scoped Enums over Unscoped Enums (Notes)"
 categories:
 - cpp
 - book reading
 tags:
 - development
 - coding
 - cpp
 - notes
 - scoped enums
 - unscoped enums
 type:
 - post
 - posts
 weight: 10
 series:
 - CPP
 aliases:
 - /blog/notes-scoped-enums-over-unscoped-enums/
---

## Scoped vs Unscoped Enums 

* **General rule:** declaring a name inside curly braces is limited to that scope.
* **Exception:** C++-98 style Enums

![](https://raw.githubusercontent.com/krshrimali/blog/main/assets/cover-images/Unscoped-Scoped-Enums.png)

---
**NOTE**

My notes on Chapter 3, Item 10 of Effective Modern C++ written by Scott Meyers.

Some (or even all) of the text can be similar to what you see in the book, as these are notes: I've tried not to be unnecessarily creative with my words. :)

---

```cpp
// You can't declare black, white, red in the scope containing the enum Color
enum Color {
    black, white, red;
};

auto white = false; // error: white already declared in this scope
```

* Unscoped Enums have implicit type conversions for their enumerators.
* Enumerators can implicitly convert to integral types, and then to floating-point types.

```cpp
// Assume Color is declared like above
Color c = red; // valid since Enumerator white is leaked to the scope Color is in
if (c < 10) {  // valid, implicit conversion
    // ... do something
}
else if (c < 10.5) {  // also valid, implicit conversion
    // ... do something
}
```

The C++-98 Style Enums are termed as Unscoped Enums (because of leaking names).

**C++-11 Scoped Enums**:

```cpp
// black, white, red are now scoped to Color Enum
enum class Color {
    black, white, red;
};

// This is now valid
auto white = false;
```

Separately, if you do: (consider `Color` Enum has already been declared)

```cpp
Color c = white; // error: no enumerator named "white" is in this scope
Color c = Color::white; // valid
auto c = Color::white; // valid
```

* Also referred as enum classes (because declared using `enum class`).
* Enumerators in scoped Enums are strongly typed (no implicit type conversion)

```cpp
// Assume Color is declared as above using enum class
Color c = Color::red;

if (c < 10.5) {  // Error! can't compare Color and double
    // do something...
}
```

**Note:** you can do explicit casting using `cast`.
**Note about enums in C++:**
    * Every enum in C++ has an integral underlying type that is determined by compilers.
    * Compilers need to know the size of enum before using it.

## C++98 vs C++11 on Enums

**C++98:**

* Unscoped enums can not be forward-declared.
    * Hence only enums with definitions are supported.
    * Allows compilers to choose underlying type for each enum prior to the enum being used.
* Drawbacks?
    * Increase in compilation dependencies: wherever the enum is used, even if not affected by any addition in the enum, it will be recompiled (generally speaking, that is without any tweaks/optimizations).

**C++11:**

* Both unscoped and scoped enums can be forward-declared. Unscoped enums will need a few efforts though:

```cpp
/* For Scoped Enums */

// Default underlying type is int
enum class Status; 
// Override it
enum class Status: std::uint32_t;

/* For Unscoped Enums */

// There is no underlying type for unscoped enum
// You can manually specify though
enum Status: sd::uint32_t;
```

_These specifications for underlying types can also go on enum's definitions._

## Unscoped Enums over Scoped Enums?

Imagine when you have a code like this:

```cpp
// Ordered as: name, email, reputation
using UserInfo = std::tuple<std::string, std::string, std::size_t>;

UserInfo uInfo;

// This is not clear to the reader, you can't always remember what 1st indexed field in UserInfo is
auto val = std::get<1>(uInfo);
```

Using the property of intrinsic conversion in unscoped enums, you can solve this:

```cpp
enum InfoFields { uName, uEmail, uReputation };

// UserInfo defined as above
UserInfo uInfo;

// Implicit conversion of int (default underlying type of enums) to std::size_t (that's what std::get takes)
auto val = std::get<uEmail>(uInfo);
```

For scoped enums though, you'll have to use `static_cast<std::size_t>(InfoFields::uEmail)` instead of just `uEmail` (for unscoped enums) passed to `std::get`, which is less readable. But...

This can be redued by using a custom function which:
    * takes: enum
    * returns: corresponding `std::size_t` value

`std::get` is a template, and the value needs to be understood during compilation only, so the function should be a `constexpr` (more on this later in the series).

To generalize, let's keep the enum's underlying type (`std::underlying_type` type trait)

```cpp
// Using noexcept because we know there'll be no exceptions raised
template <typename E>
constexpr typename std::underlying_type<E>::type toUType(E enumerator) noexcept {
    return static_cast<typename std::underlying_type<E>::type>(enumerator);
}
```

From the [previous blog](https://krshrimali.github.io/Alias-Declarations-over-Typedefs-CPP/), we know that in C++14, we could have simplified by writing:

```cpp
// Using noexcept because we know there'll be no exceptions raised
template <typename E>
constexpr std::underlying_type_t<E> toUType(E enumerator) noexcept {
    return static_cast<std::underlying_type_t<E>>(enumerator);
}
```

Could have used `auto` for return type in C++14:


```cpp
// Using noexcept because we know there'll be no exceptions raised
template <typename E>
constexpr auto toUType(E enumerator) noexcept {
    return static_cast<std::underlying_type_t<E>>(enumerator);
}
```

Now this can be used as:

```cpp
// Reminder, InfoFields was defined as:
enum InfoFields { uName, uEmail, uReputation };

// toUType is defined above
auto val = std::get<toUType(InfoFields::uEmail)>(uInfo);
```

## Good Reads

1. Forward Declaration:
    * Stackoverflow: https://stackoverflow.com/questions/4757565/what-are-forward-declarations-in-c
2. Are Unscoped Enums still helpful?
    * Stackoverflow: https://stackoverflow.com/questions/27320603/are-unscoped-enumerations-still-useful
3. Proposal for forward declaration to enums (accepted), dated 2008: http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2008/n2764.pdf
4. Forward Declaring an Enum in C++? 
    * Stackoverflow: https://stackoverflow.com/questions/71416/forward-declaring-an-enum-in-c

## Acknowledgement (Reviews)

Thanks to [Kshitij Kalambarkar](https://kshitij12345.github.io/) for helping in reviewing the blog. It's always helpful to get another set of eyes to what you write. :)

That's it for this blog, thank you for reading everyone!
