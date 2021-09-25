---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2020-04-26
linktitle: Vectors in C++ Part 2 
title: "Understanding how Vectors work in C++ (Part-2): What happens when you initialize a vector?"
categories:
 - cpp
tags:
 - development
 - coding
 - cpp
 - notes
 - vectors
type:
- post
- posts
weight: 10
series:
- CPP
aliases:
- /blog/vectors-cpp-part-2/
---

In the last blog post, I realized there were a lot of methods inherited from the base struct `_Vector_base_` and `_Vector_impl_data`. Instead of directly going to the source code of these structs, I'll go through their methods and objects by explaining what happens when we initialize a vector.

![](https://raw.githubusercontent.com/krshrimali/blog/main/assets/cover-images/Vector-Part-2.png)

That is, we will start from calling a vector constructor and then see how memory is allocated. If you haven't looked at the previous blog post, please take a look <a href="https://krshrimali.github.io/How-Vectors-Work-in-C++-Part-1">here</a>. I want to be thorough with the blog post, so I'll divide this into multiple posts. By the end of this post, you'll go through the following structs:

1. `_Vector_impl_data` struct which contains pointers to memory locations (start, finish and end of storage).
2. `_Vector_impl` struct (inherits `_Vector_impl_data` as well)).

I usually opt for the bottom-up approach. Vectors can be initialized in many ways, three of them will be discussed in today's blog. We'll start from the very basic constructor of a vector using an initializer list and slowly reach to memory allocation and how the above 2 structs are used. Let's start!

## Using Initializer Lists

So what happens when we initialize a vector with an initializer list?

```cpp
std::vector<int> vec {1, 2, 3};
```

The vector class has many constructors in GCC depending on the type of inputs you give. Let's take a look at the constructor when the input is an initializer list:

```cpp
vector(initializer_list<value_type> __l, const allocator_type& __a = allocator_type()) : _Base(__a) {
    _M_range_initialize(__l.begin(), __l.end(), random_access_iterator_tag());
}
```

If you are curious what `_Base` is, `_Base` is declared as: `typedef _Vector_base<_Tp, _Alloc> _Base;`. Just so you know, where and how is `_Vector_base` used. When the constructor is called, it calls the constructor of `_Vector_base` with `__a` (allocator type). As you might have noticed, we are calling `_M_range_initialize` and passing 2 iterators (`__l.begin(), __l.end()`) and 1 forward iterator tag.

Note that the iterators are Forward Iterators, that is: we can use these iterators to access elements from begin (accessed using `.begin()`) till the end (accessed using `.end()`).

We are using `random_access_iterator_tag` as `forward_iterator_tag`. This tag helps us to categorize the iterator as random-access iterator. Random-access iterators allow accessing elements by passing arbitrary offset position (see: <a href="documentation">http://www.cplusplus.com/reference/iterator/RandomAccessIterator/</a> for more details).

Let's go ahead and see what `_M_range_initialize` does.

```cpp
template <typename _ForwardIterator>
void _M_range_initialize(_ForwardIterator __first, _ForwardIterator __last, std::forward_iterator_tag) {
    const size_type __n = std::distance(__first, __last);
    this->_M_impl._M_start = this->_M_allocate(_S_check_init_len(__n, _M_get_Tp_allocator()));
    this->_M_impl._M_end_of_storage = this->_M_impl._M_start + __n;
    this->_M_impl._M_finish = std::__uninitialized_copy_a(__first, __last, this->_M_impl._M_start, _M_get_Tp_allocator());
}
```

Let's go line by line.

* First we find the distance using `std::distance` which takes first and last iterators, and returns size such as: `__last = __first + size`.
* Next, we allocate memory for `__n` objects. The function `this->_M_allocate` returns pointer to the starting location of the memory allocated.
    ```cpp
    static size_type _S_check_init_len(size_type __n, const allocator_type& __a)
    {
        if (__n > _S_max_size(_Tp_alloc_type(__a)))
        __throw_length_error(
            __N("cannot create std::vector larger than max_size()"));
        return __n;
    }
    ```
    * The function `_S_check_init_len` is called by constructors to check size. If the requested size is greater than the maximum size for the allocator type, it throws length error (`"cannot create std::vector larger than max_size()"`). Else, it returns `__n`.
    * Once we have validated the size, `this->_M_allocate` call allocates the memory. Note that, `_M_allocate` is a part of `_Vector_base` struct. `_M_allocate` allocates memory for `__n` number of objects. This returns a pointer to the memory location (starting), to `_M_start`.
    * The end of storage pointer stores the end of memory location for the memory allocated for `__n` objects.
    * The function `std::__uninitialized_copy_a` copies the range `[__first, __last)` into the `this->_M_impl._M_start`. This returns a pointer to memory location starting at `this->_M_impl._M_start` with length of `__first - __last`.

To summarize, when we initialized vector with initializer list:

1. It first calculates the number of objects to allocate memory for. This is assigned to `__n`.
2. Then, memory is allocated for `__n` objects (including a check if this much memory can be allocated based on the allocator type, if not then it returns a length error). The pointer `_M_start` points to the starting memory location.
3. The end of storage is the end location of the storage. Since we have passed the initializer list, so it knows the end of storage is starting location + len(initializer_list).
4. The elements are then copied the range `[__first, __last)` into the memory allocated.

Depending on how you initialize your vectors, the process may change but overall, the intention is the same: to allocate memory (if valid) and set pointers (start, end of storage and finish).

## Using similar value and specified number of elements (fill)

Let's take a look at an example of using

```cpp
std::vector<int> vec(10, 0);
```

The above constructor call will give you a vector of 10 elements with all zeros. You can print the elements using:

```cpp
// Instead of using auto, we can use
// for (std::vector<int>::iterator it = vec.begin(); it != vec.end(); it++) {
//     std::cout << *it << " ";
// }
for (auto it = vec.begin(); it != vec.end(); it++) {
    std::cout << *it << " ";
}
std::cout << std::endl;
```

Let's see what changes when the vector is constructed in the above mentioned way. Let's take a look at the constructor which is called:

```cpp
vector(size_type __n, const value_type& __value, const allocator_type& __a = allocator_type()) : _Base(_S_check_init_len(__n, __a), __a {
    _M_fill_initialize(__n, __value);
}
```

As the documentation of the above constructor explains, this constructor fills the vector with `__n` copies of `__a` value. Note the use of `_S_check_init_len` here (we discussed this before). Instead of calling `_M_range_initialize`, `_M_fill_initialize` is called here. For our example, this function is passed with values: 10 (`__n`) and 0 (`__value`). Let's take a look at the definition of `_M_fill_initialize`:

```cpp
void _M_fill_initialize(size_type __n, const value_type& __value) {
    this->_M_impl._M_finish = std::__uninitialized_fill_n_a(this->_M_impl._M_start, __n, __value, _M_get_Tp_allocator());
}
```

The call `__uninitialized_fill_n` copies the value (`__value`, here 0) into the range `[this->_M_impl._M_start, this->_M_impl._M_start + __n)` and returns the end of it's range. As per the documentation, it is similar to `fill_n()` but does not require an initialized output range. Wait, you might be wondering, we didn't initialize `this->_M_impl._M_start`! We did! Note that we called `_Base(_S_check_init_len(__n, __a)` when the constructor is called. `_Base` is nothing but a typedef of `_Vector_base`. Let's take a look at this call:

```cpp
_Vector_base(size_t __n) : _M_impl() {
    _M_create_storage(__n);
}
```

* `_M_impl` is an object of type `_Vector_impl` declared in `_Vector_base` struct.
* `_M_create_storage(__n)` is defined as:
    ```cpp
    void _M_create_storage(size_t __n) {
        this->_M_impl._M_start = this->_M_allocate(__n);
        this->_M_impl._M_finish = this->_M_impl._M_start;
        this->_M_impl._M_end_of_storage = this->_M_impl._M_start + __n;
    }
    ```
    This will answer most of your queries. Let's start line by line.
    * `this->_M_allocate(__n)` was discussed before, which allocates memory for `__n` objects. Please note that the constructor call `_M_impl()` had initialized these pointers for us. Here, the pointer is set to the starting memory location.
    * Since the function `_M_create_storage` creates storage, and doesn't copy elements to the memory location. So `this->_M_impl._M_finish` is set to `this->_M_impl._M_start`.
    * The end of storage is, as before, set to `this->_M_impl._M_start + __n`.

So, eventually, it's quite similar to what we saw when we initialized our vector with initializer list.

## Using another vector (copy)

Let's take a look at another way to another initalize a vector:

```cpp
std::vector<int> vec_copy {1, 2, 3};
std::vector<int> vec(vec_copy);

// Try printing the elements of vec
for (auto it = vec.begin(); it != vec.end(); it++) {
    std::cout << *it << std::endl;
}
```

When you call `vec(vec_copy)`, the copy constructor is called. Let's take a look at it's definition:

```cpp
vector(const vector& __x) : _Base(__x.size(), _Alloc_traits::_S_select_on_copy(__x._M_get_Tp_allocator()) {
    this->_M_impl._M_finish = std::__uninitialized_copy_a(__x.begin(), __x.end(), this->_M_impl._M_start, _M_get_Tp_allocator());
}
```

The function body is similar to what we saw in the constructor definition when we initialized vector using `size_type __n, value_type value`. Notice how we initialize the base struct here. Let's take a look at `_S_select_on_copy(__x._M_get_Tp_allocator())` first. `_M_get_Tp_allocator()` returns `_M_impl` object.

```cpp
const _Tp_alloc_type& _M_get_Tp_allocator() {
    return this->_M_impl;
}
```

Note that, here, `this->_M_impl` will already have the pointers set to the memory locations for start, finish and end of storage (as we use the allocator of `__x`). The objective is to use the copy of allocator object used by `__x`. Let's take a look at the constructor of Base struct:

```cpp
_Vector_base(size_t __n, const allocator_type& __a) : _M_impl(__a) {
    _M_create_storage(__n);
}
```

Overall, it's the same to what we saw before except that we use the copy of the alloactor of vector `__x`. The call `_M_create_storage(__n)` does the same task of setting pointers `_M_start, M_end_of_storage, _M_finish` as we observed before.

For today's blog, we discussed 3 popular ways to initialize a vector in C++ and went through how memory is allocated when the constructors are called. As we move forward, we will slowly get familiar with the design patterns and methods used in GCC.

As always, I would love to hear your feedback on my blogs. Correct me if I was wrong anywhere, no one is perfect afterall. If this helped you, please let me know - it keeps me going! See you all in the next blog!
