---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2021-08-12
 linktitle: Alias Declarations vs Typedefs
 title: "Prefer Alias Declarations to Typedefs (Notes)"
 categories:
 - cpp
 - book reading
 tags:
 - development
 - coding
 - cpp
 - notes
 - aliases
 - typedefs
 type:
 - post
 - posts
 weight: 10
 series:
 - CPP
 aliases:
 - /blog/notes-alias-vs-typedefs/
 toc: true
 comments: true
---

One solution to avoiding using long type names:

```cpp
// So C++98 like
typedef std::unique_ptr<std::unordered_map<std::string, std::string>> UPtrMapSS;
```
<!--more-->

![](https://raw.githubusercontent.com/krshrimali/blog/main/assets/cover-images/alias-declarations-typedefs.png)

---
**NOTE**

My notes on Chapter 3, Item 9 of Effective Modern C++ written by Scott Meyers.

Some (or even all) of the text can be similar to what you see in the book, as these are notes: I've tried not to be unnecessarily creative with my words. :)

---

C++11 also offers alias declarations:

```cpp
using UPtrMapSS = typedef std::unique_ptr<std::unordered_map<std::string, std::string>>;
```

Advantages of alias declarations over typedefs:

1. For types involving function pointers, aliases are easier to read (for some people):
    ```cpp
    // typedef
    typedef void (*FP)(int, const std::string&);

    // alias declaration
    using FP = void (*)(int, const std::string&);
    ```
2. Alias declarations can be templatized, but typedefs can not.
    ```cpp
    // MyAlloc is a custom allocator
    template <typename T>
    using MyAllocList = std::list<T, MyAlloc<T>>;

    MyAllocList<Widget> lw; // will create std::list<Widget, MyAlloc<Widget>>
    ```

    vs: typedef, a hack way:

    ```cpp
    // templatized struct here
    template <typename T>
    struct MyAllocList {
        typedef std::list<T, MyAlloc<T>> type;
    };

    MyAllocList<Widget>::type lw;
    ```
3. In case you want to use a type specified by template parameter, with typedefs it gets complex:
    ```cpp
    // MyAllocList is defined as mentioned in 2nd point
    template <typename T>
    class Widget {
    private:
        typename MyAllocList<T>::type list;
        // ...
    };
    ```
    * Here `MyAllocList<T>::type` is now a dependent type (dependent on type `T` from template paramater).
    * C++ Rule: need to use `typename` before name of a dependent type.

    With alias declaration of `MyAllocList`, no need to use `typename` and `::type`:
    ```cpp
    template <typename T>
    class Widget {
    private:
        // no typename and ::type
        MyAllocList<T> list;
        // ...
    }
    ```

Explanation on the 3rd point:

1. Compiler understands the alias declared `MyAllocList` when used inside a template class `Widget` as `MyAllocList<T>` is not a dependent type.
2. A user can have `type` as a data member, and thus it's important to mention `typename` when using `MyAllocList<T>::type` (as a type), so that compiler knows it's a type.

Creating revised types from template type paramaeters is a common practice in Template Meta Programming (TMP). A few important points to note:

In C++11 (in header: `<type_traits>`):

```cpp
std::remove_const<T>::type // yields T from const T
std::remove_reference<T>::type // yields T from T& and T&&
std::add_lvalue_reference<T>::type // yields T& from T
```

In case you are applying the above transformations inside a template to a type parameter, you'll have to use `typename`. This is because they have been implemented as typedefs inside templatized structs. 

In C++14, their alias equivalent were added which do not require you to prefix `typename`:

```cpp
// equivalents to the above 3 transformations 
std::remove_const_t<T>
std::remove_reference_t<T>
std::add_lvalue_reference<T>
```

**Acknowledgement**

* Thanks to [Kshitij Kalambarkar](https://kshitij12345.github.io/) for reviewing this blog.

Thanks for reading!

{{ template "_internal/disqus.html" . }}
