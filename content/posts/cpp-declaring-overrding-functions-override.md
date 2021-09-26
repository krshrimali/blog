---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2021-09-25
 linktitle: Declaring Overriding functions override 
 title: "Declaring Overriding Functions override (Notes)"
 categories:
 - cpp
 - book reading
 tags:
 - development
 - coding
 - cpp
 - notes
 - override
 type:
 - post
 - posts
 weight: 10
 series:
 - CPP
 aliases:
 - /blog/notes-declaring-overriding-functions-override/
 toc: false
 comments: true
---

---
**NOTE**

My notes on Chapter 3, Item 12 of Effective Modern C++ written by Scott Meyers.

Some (or even all) of the text can be similar to what you see in the book, as these are notes: I've tried not to be unnecessarily creative with my words. :)

---

![](https://raw.githubusercontent.com/krshrimali/blog/main/assets/cover-images/declaring-overriding-functions-override.png)

Overriding != Overloading

_Example_ of virtual function overriding:

```cpp
// Base class
class Base {
public:
    virtual void doWork();
    // ...
};

// Derived class from Base
class Derived: public Base {
public:
    // virtual is optional
    // this will "override" Base::doWork
    virtual void doWork();
    // ...
};


// This creates a "Base" class pointer to "Derived" class object
std::unique_ptr<Base> upb = std::make_unique<Derived>();

// Derived doWork() function is invoked
upb->doWork();
```

This is how virtual function overriding allows to invoke a "derived class function" from a base class interface.

**Requirements for overriding**:

1. Base class function must be virtual.
2. Base and derived function names must be identical (except for destructors).
3. Parameter types of base and derived functions must be identical.
4. Constness of both base and derived functions must be identical.
5. The return types and exception specifications of the base and derived functions must be compatible.
6. [from C++11] Both functions should have identical reference qualifiers (see below)

Reference qualifiers were new to me, but the book gives a really good example:

```cpp
// Useful when you want to limit the calls to lvalues or rvalues only

class Widget {
public:
    // ...
    void doWork() &; // Only when *this is an lvalue
    void doWork() &&; // Only when *this is an rvalue
    // ...
};

// Suppose there is a makeWidget() function that returns an instance of Widget class, this will be an rvalue here
Widget makeWidget();

// lvalue
Widget w;

// this will call void doWork() &;
w.doWork();

// this will call void doWork() &&;
makeWidget().doWork();
```

In case the functions don't have identical reference qualifiers, the derived class will _still have_ the function, but it won't override the base class function.

Because of a lot of conditions (see 6 _requirements_ above), it's easy to make mistakes or forget a few things while overriding a function. And the book states that it's not worth expecting from compiler to report an error, because the code can still be valid - it's just you expected it to override, but it didn't.

See an example below:

```cpp
class Base {
public:
    virtual void mf1() const;
    virtual void mf2(int x);
    virtual void mf3() &;
    void mf4() const;
};

class Derived: public Base {
public:
    virtual void mf1();
    virtual void mf2(unsigned int x);
    virtual void mf3() &&;
    void mf4() const;
};
```

None of the functions in `Derived` class will override functions in the `Base` class. Why?

1. `mf1()`: declared `const` in `Base` but not in `Derived`.
2. `mf2()`: arg `int` in `Base` but `unsigned int` in `Derived`.
3. `mf3()`: lvalue-qualified in `Base` but rvalue-qualified in `Derived`.
4. `mf4()`: isn't declared `virtual` in `Base`.

To avoid worrying about human mistakes, it's better to let the compiler know explicitly that these functions are expected to override. For that, declare the functions in `Derived` class `override`.

```cpp
class Derived: public Base {
public:
    virtual void mf1() override;
    virtual void mf2(unsigned int x) override;
    virtual void mf3() && override;
    virtual void mf4() const override;
};
```

Now, this won't compile for sure no matter what compiler you are using.

C++-11 introduced  2 contextual keywords: `final` (see note below), `override`. These keywords are reserved, but only in certain contexts.

**Note:** In case you want to prevent a function in a base class to be overridden in derived classes, you can declare them `final`. `final` can also be declared for a class, in which case it won't be allowed to be used a base class.

For `override`: In case your old (legacy) code uses `override` somewhere else, it's fine - keep it! Only when it's used at the end of a member function declaration, then it's reserved.

```cpp
class Sample {
public:
    // legal
    void override();
}
```

The chapter (item) ends with a brief about lvalue and rvalue reference member functions, which I would like to cover in another blog. For this blog, I think this should be good! :)

Thank you for reading.
