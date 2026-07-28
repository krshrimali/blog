---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2026-07-28
 linktitle: OpenCV, C++ to Python Bindings
 title: "How OpenCV Exposes 4,000+ C++ Functions to Python (Without Writing a Line of Python)"
 categories:
 - opencv
 tags:
 - opencv
 - c++
 - python
 - bindings
 - computer vision
 type:
 - post
 - posts
 weight: 10
 series:
 - CPP
 aliases:
 - /blog/opencv-cpp-python-bindings/
 toc: true
 comments: true
---

OpenCV is possibly one of the most interesting code-bases I've read through, for many technical reasons. One of the reason is what I'm going to cover today.

There are >4k python functions exposed in OpenCV, and no - they are not written in Python. They are all generated from C++ code. How does OpenCV do that? We'll touch upon it today.

> **Note:** I love OpenCV --- it's the best image processing and computer vision library that has stayed true to Open Source and delivered on its promises. It is also the library that I first touched upon (along with NumPy and Matplotlib) when I was 19 --- I was playfully creating animations by blurring an image from the original image every frame (with an increase in the kernel sizes), and then understanding what happens behind the scenes. From blurring to canny edge detection to contour detection to convex hull, I was [hooked](https://github.com/krshrimali/OpenCV_Work). I still am. We'll talk more about all this one day, but for now, let's go ahead and touch upon it.

All of understand blurring, right? If not, a simple example below will help you understand it better. The code below blurs an image using a Gaussian kernel of size 5x5.

```python
import cv2
import numpy as np

img = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
blurred_img = cv2.GaussianBlur(img, (5, 5), 0)
cv2.imwrite('blurred_image.jpg', blurred_img)
cv2.imwrite('original_image.jpg', img)
```

See a comparison of original image and blurred image. For starters, I've created a sample image above, totally random - just pure numbers b/w (0, 255) in RGB format. The original image is on the left, and the blurred image is on the right.

<img src="/assets/blogs/opencv-python-bindings-original.jpg" width="45%" /> <img src="/assets/blogs/opencv-python-bindings-gaussianblur.jpg" width="45%" />

```cpp
# Ref: https://github.com/opencv/opencv/blob/d7e6e58652db60ee57b807086c3bfef0c5d836e6/modules/imgproc/include/opencv2/imgproc.hpp#L1575-L1578
CV_EXPORTS_W void GaussianBlur( InputArray src, OutputArray dst,
                     Size ksize, double sigmaX,
                     double sigmaY = 0,
                     int borderType = BORDER_DEFAULT,
                     AlgorithmHint hint = cv::ALGO_HINT_DEFAULT );
```

The above declaration of the function `GaussianBlur` is in C++, and let's see how it is exposed to Python.

When you run CMake to build OpenCV, here's what OpenCV does behind the scenes:

1. A python file [`gen2.py`](https://github.com/opencv/opencv/blob/ba19416730eb9ec8a6b57ce8621c194ecdaed957/modules/python/src2/gen2.py) is tasked to generate C++ wrappers equivalent to the function above, which will be compiled into a shared library.
  - `gen2.py` is a script, that contains a parser file [`hdr_parser.py`](https://github.com/opencv/opencv/blob/288471f559ff4ef28e270ccd1351e0e0cbc9d85b/modules/python/src2/hdr_parser.py) --- that looks at the defined header files in OpenCV, and recognizes which functions are to be exposed in Python. How does it do that? `CV_EXPORTS_W` --- we'll talk about it in a bit. Hold on! ;)
  - The final generated code looks like this (I generated this by actually running `gen2.py`/`hdr_parser.py` from a real OpenCV checkout against `core.hpp` and `imgproc.hpp`, rather than typing it from memory --- so this is the real output, not a paraphrase):

```cpp
static PyObject* pyopencv_cv_GaussianBlur(PyObject* , PyObject* py_args, PyObject* kw)
{
    using namespace cv;

    pyPrepareArgumentConversionErrorsStorage(2);

    {
    PyObject* pyobj_src = NULL;
    Mat src;
    PyObject* pyobj_dst = NULL;
    Mat dst;
    PyObject* pyobj_ksize = NULL;
    Size ksize;
    PyObject* pyobj_sigmaX = NULL;
    double sigmaX=0;
    PyObject* pyobj_sigmaY = NULL;
    double sigmaY=0;
    PyObject* pyobj_borderType = NULL;
    int borderType=BORDER_DEFAULT;
    PyObject* pyobj_hint = NULL;
    AlgorithmHint hint=cv::ALGO_HINT_DEFAULT;

    const char* keywords[] = { "src", "ksize", "sigmaX", "dst", "sigmaY", "borderType", "hint", NULL };
    if( PyArg_ParseTupleAndKeywords(py_args, kw, "OOO|OOOO:GaussianBlur", (char**)keywords, &pyobj_src, &pyobj_ksize, &pyobj_sigmaX, &pyobj_dst, &pyobj_sigmaY, &pyobj_borderType, &pyobj_hint) &&
        pyopencv_to_safe(pyobj_src, src, ArgInfo("src", 0)) &&
        pyopencv_to_safe(pyobj_dst, dst, ArgInfo("dst", 1)) &&
        pyopencv_to_safe(pyobj_ksize, ksize, ArgInfo("ksize", 0)) &&
        pyopencv_to_safe(pyobj_sigmaX, sigmaX, ArgInfo("sigmaX", 0)) &&
        pyopencv_to_safe(pyobj_sigmaY, sigmaY, ArgInfo("sigmaY", 0)) &&
        pyopencv_to_safe(pyobj_borderType, borderType, ArgInfo("borderType", 0)) &&
        pyopencv_to_safe(pyobj_hint, hint, ArgInfo("hint", 0)) )
    {
        ERRWRAP2(cv::GaussianBlur(src, dst, ksize, sigmaX, sigmaY, borderType, hint));
        return pyopencv_from(dst);
    }

        pyPopulateArgumentConversionErrors();
    }

    { // second overload: identical logic, but Mat -> UMat, for the Transparent API (T-API/OpenCL) path
    ...
    }
    pyRaiseCVOverloadException("GaussianBlur");

    return NULL;
}
```

A couple of things jump out the moment you look at this:

- **There are two overloads, generated automatically.** `GaussianBlur` takes `InputArray`/`OutputArray` in C++, which is really a type-erased wrapper that can bind to `Mat`, `UMat`, `std::vector<>`, etc. Since Python needs a concrete type to convert against, `gen2.py` expands this into one overload per concrete backing type it knows how to bridge --- here, `Mat` (plain CPU array) and `UMat` (OpenCL-backed array, used for the Transparent API). Both bodies are byte-for-byte identical except for the type substitution.
- **`dst` is both an input and an output argument.** Notice `ArgInfo("dst", 1)` --- the `1` is an output-arg flag. That's why you can call `cv2.GaussianBlur(img, (5, 5), 0)` in Python without ever allocating an output buffer: the wrapper allocates `dst` internally and returns it via `pyopencv_from(dst)`.
- **Failure has a real fallback path.** If parsing/conversion fails for every overload, control falls through to `pyRaiseCVOverloadException("GaussianBlur")` --- this is exactly the `error: (-5:Bad argument) ... overload resolution failed` message you've probably seen if you've ever passed the wrong type into an OpenCV Python call.

2. The generated C++ code is compiled into a shared library, which is then linked with the Python interpreter. This allows Python to call the C++ functions directly.
  - `cv2.cpp` file is an interesting file that contains the glue code to connect the generated C++ functions with Python. It uses the Python C API to create Python objects and call the C++ functions. It essentially imports the headers in the required header, for the .so file alongwith other features. I only mentioned the relevant part here :)

A very interesting thing about OpenCV's code-base is that they convert all the types like `std::vector<std::string>` to `vector_string`, see an exhaustive list here: https://github.com/opencv/opencv/blob/91c78f50647c0f342ac72bed3d5c8952fa9523ae/modules/python/src2/cv2.cpp#L22-L47:

```cpp
typedef std::vector<uchar> vector_uchar;
typedef std::vector<char> vector_char;
typedef std::vector<int> vector_int;
typedef std::vector<float> vector_float;
typedef std::vector<double> vector_double;
typedef std::vector<size_t> vector_size_t;
typedef std::vector<Point> vector_Point;
typedef std::vector<Point2f> vector_Point2f;
typedef std::vector<Point3f> vector_Point3f;
typedef std::vector<Size> vector_Size;
typedef std::vector<Vec2f> vector_Vec2f;
typedef std::vector<Vec3f> vector_Vec3f;
typedef std::vector<Vec4f> vector_Vec4f;
typedef std::vector<Vec6f> vector_Vec6f;
typedef std::vector<Vec4i> vector_Vec4i;
typedef std::vector<Rect> vector_Rect;
typedef std::vector<Rect2d> vector_Rect2d;
typedef std::vector<RotatedRect> vector_RotatedRect;
typedef std::vector<KeyPoint> vector_KeyPoint;
typedef std::vector<Mat> vector_Mat;
typedef std::vector<std::vector<Mat> > vector_vector_Mat;
typedef std::vector<UMat> vector_UMat;
typedef std::vector<DMatch> vector_DMatch;
typedef std::vector<String> vector_String;
typedef std::vector<std::string> vector_string;
typedef std::vector<Scalar> vector_Scalar;
```

I was particularly interested in the above typedefs, so I went and checked exactly how they're used, instead of guessing.

The headers themselves use completely ordinary C++ template syntax --- no header ever writes `vector_string` as an argument type. For example:

```cpp
CV_EXPORTS_W void calcBackProject( InputArrayOfArrays images, const std::vector<int>& channels, ... );
CV_EXPORTS_W void transposeND(InputArray src, const std::vector<int>& order, OutputArray dst);
```

So `hdr_parser.py` does see the real `std::vector<int>` / `std::vector<std::string>` syntax, and it **derives** the flattened name itself. I confirmed this by calling its `parse_arg` function directly:

```
>>> parse_arg('const std::vector<int>& channels', 0)
('vector_int', 'channels', ['/C', '/Ref'], ...)

>>> parse_arg('const std::vector<std::string>& names', 0)
('vector_string', 'names', ['/C', '/Ref'], ...)
```

The mechanism is simple bracket-matching, not real template parsing (`hdr_parser.py:292-353`): it tokenizes the type string on `<`, `>`, `,`, `&`, `*`, and space, then walks the tokens --- every `<` appends `_` to a running `arg_type` string, every inner identifier gets appended as-is, every `,` inside a template becomes `_and_`, every closing `>` pops a stack it uses to track nesting. So `vector<int>` becomes `vector_int`, and (hypothetically) `map<int, string>` would become `map_int_and_string`. A final cleanup pass then strips namespace qualifiers: `arg_type = self.batch_replace(arg_type, [("std::", ""), ("cv::", ""), ("::", "_")])` (`hdr_parser.py:385`) --- that's what turns the intermediate `vector_std::string` into `vector_string`.

This is purely syntactic flattening. The parser has no idea what `std::vector` *means*; it just knows that whatever sits between `<` and `>` needs to become part of an underscore-joined identifier.

So what are the typedefs in `cv2.cpp` actually for, if the parser doesn't need them to read the header? They're for the *other end* of the pipeline. `gen2.py` takes the derived name (`vector_string`) and uses it as a literal C++ type when it emits the wrapper --- you'll find locals like `vector_string names;` declared inside the generated `pyopencv_cv_someFunc` bodies. That only compiles because `cv2.cpp` has `typedef std::vector<std::string> vector_string;` sitting in scope. The typedefs exist so the *generated* code is valid C++, not so the header is easier to parse.

Alright, now let's talk about macros like `CV_EXPORTS_W` properly, since it's the tag that decides whether a function is in that 4,000+ list at all.

Here's the part that surprised me most: `CV_EXPORTS_W` does almost nothing at compile time. Its definition, in [`modules/core/include/opencv2/core/cvdef.h`](https://github.com/opencv/opencv/blob/4.x/modules/core/include/opencv2/core/cvdef.h), is just:

```cpp
/* special informative macros for wrapper generators */
#define CV_EXPORTS_W CV_EXPORTS
#define CV_EXPORTS_W_SIMPLE CV_EXPORTS
#define CV_EXPORTS_AS(synonym) CV_EXPORTS
#define CV_EXPORTS_W_MAP CV_EXPORTS
#define CV_EXPORTS_W_PARAMS CV_EXPORTS
```

To the actual C++ compiler, `CV_EXPORTS_W` collapses down to plain `CV_EXPORTS` --- the ordinary dllexport/visibility macro every exported symbol in OpenCV already carries. As far as GCC/Clang/MSVC are concerned, `CV_EXPORTS_W` is not special at all. It exists purely as a marker for a *different* reader: `hdr_parser.py`.

And that reader doesn't do anything clever with it either. Inside `parse_func_decl`, the very first check is a plain substring search:

```python
if self.wrap_mode:
    if not (("CV_EXPORTS_AS" in decl_str) or ("CV_EXPORTS_W" in decl_str) or ("CV_WRAP" in decl_str)):
        return []
```

That's it. If none of `CV_EXPORTS_AS`, `CV_EXPORTS_W`, or `CV_WRAP` literally appear as text in the declaration string, the parser bails out with an empty result, and the function is invisible to Python --- no AST, no symbol table lookup, just `in`. Every plain (non-`CV_EXPORTS_W`) function in OpenCV's C++ headers is skipped this same way, which is exactly why the API surface exposed to Python is a curated subset of the full C++ API rather than all of it.

A few siblings of `CV_EXPORTS_W` round out the picture, since they answer the "what about methods and properties?" question:
- `CV_WRAP` --- same idea as `CV_EXPORTS_W`, but for class *methods* rather than free functions.
- `CV_EXPORTS_AS(pythonName)` --- exports the function under a different name in Python than its C++ name (you'll see this on overloaded C++ functions that Python can't disambiguate the same way, so they get distinct names).
- `CV_PROP` / `CV_PROP_RW` --- marks a class member as a read-only / read-write Python property, so `cv2.KeyPoint().pt` works even though `pt` is just a public C++ field.

So the whole "which 4,000+ functions get exposed" question comes down to: a text tag on a declaration, a substring check in a script that isn't even parsing real C++ grammar, and a template engine (`gen2.py`) that stamps out the Python C-API glue from what survives that filter. It's not glamorous, but it's the kind of pragmatic, low-magic engineering that lets a codebase this large stay maintainable --- and it's part of why I keep coming back to read this source, all these years after the 19-year-old me first typed `cv2.GaussianBlur` without any idea what was happening underneath.

Next time, we'll dig into `cv2.cpp` itself --- the actual glue file, module init, and how `pyopencv_to`/`pyopencv_from` do the type conversion dance for something like a `Mat` <-> NumPy array.
