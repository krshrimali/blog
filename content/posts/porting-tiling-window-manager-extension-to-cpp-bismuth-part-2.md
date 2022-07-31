---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2022-07-31
 linktitle: Porting a Tiling WM to C++ (Part-2)
 title: "Porting a Tiling Window Manager Extenstion to C++ (Bismuth): Part-2 (getting closest relative window)"
 categories:
 - cpp
 - projects
 - open-source
 - kde
 tags:
 - development
 - coding
 - cpp
 - contributions
 - open source 
 - KDE
 - Bismuth
 type:
 - post
 - posts
 weight: 10
 series:
 - Projects
 aliases:
 - /blog/porting-tiling-wm-to-cpp-part-2/
 toc: true
 comments: true
---

Hi everyone! In this blog, I will be discussing the algorithm used in Bismuth to find the closest relative window to be focused for `focusWindowByDirection` event. If you haven't read the previous blog, make sure to give it a read [here](https://krshrimali.github.io/posts/2022/07/porting-a-tiling-window-manager-extenstion-to-c-bismuth-part-1/).

## Recap from the previous blog

Let's start with a quick recap though, in the previous blog, we discussed:

`focusWindowByDirection` requires the following information:

  * `direction` (from the user) - can be one of: `right, left, top/up, bottom/down`.
  * `activeWindow` (from the current session) - this is needed since `focusWindowByDirection` event is a _relative_ event to your current focused window.
  * Neighbor window candidates (`neighborCandidates`) to your current window (`activeWindow`) and the given direction (`direction`).

  ```cpp
  // declaration
  std::vector<Window> Engine::getNeighborCandidates(const FocusDirection &direction, const Window &basisWindow);

  // use
  std::vector<Window> neighborCandidates = getNeighborCandidates(direction, basisWindow);
  ```

  * From these neighbor candidates (`neighborCandidates`), we will now find the closest relative window corner. To me, it was tricky to understand at first, so we'll be discussing this in detail over in the later sections.
  * Once we know the closest relative window corner, we'll try to find the window which satisfies the corner condition.
  * If there were multiple found, we'll return the first one based on the time-stamp (last used)

## Understanding the scenario

I want to start off with a visual, took me some time to draw it, but in case it doesn't look good, I'm sorry! My drawing teacher in the high school tried his best, but... 

![]("https://raw.githubusercontent.com/krshrimali/blog/main/assets/blogs/bismuth-part-2-window-alignment.png")

Above image is visual of a tiling window layout where there are in total 5 windows opened (just for imagination, no sane person would open these many windows on a 24 inch monitor... xD): `A, B, C, D, E`, where as mentioned in the figure above, `E` is the active window and we are trying to focus `UP`. A few notes to take from the figure:

1. `A, B, C, D` windows are of same height and width `w` and `h`. We'll use this information later.
2. `E` window is the active window with width: `2 * w` and height: `h`.
3. We are trying to focus `UP`.

## Getting Closest Relative Window Corner

In the [previous blog](https://krshrimali.github.io/posts/2022/07/porting-a-tiling-window-manager-extenstion-to-c-bismuth-part-1/), we had covered `getNeighborCandidates`, the output here would be windows: `A, B, C, D`. The order will not matter here for understanding, so don't worry about that.

The next steps in the code include:

```cpp
int closestRelativeWindowCorner = getClosestRelativeWindowCorner(direction, neighborCandidates);

auto closestWindows = getClosestRelativeWindow(direction, neighborCandidates, getClosestRelativeWindow);

return most_recently_used(closestWindows);
```

I didn't add comments here, because we'll be going through these 2 magic functions below. Let's start with `getClosestRelativeWindowCorner`. The source code for the definition of this function is:

```cpp
int Engine::getClosestRelativeWindowCorner(const Engine::FocusDirection &direction, const std::vector<Window> &neighbors)
{
    return std::reduce(neighbors.cbegin(),
                       neighbors.cend(),
                       /* initial value */ direction == Engine::FocusDirection::Up || direction == Engine::FocusDirection::Left ? 0 : INT_MAX,
                       [&](int prevValue, const Window &window) {
                           switch (direction) {
                           case Engine::FocusDirection::Up:
                               return std::max(window.geometry().bottom(), prevValue);
                           case Engine::FocusDirection::Down:
                               return std::min(window.geometry().y(), prevValue);
                           case Engine::FocusDirection::Left:
                               return std::max(window.geometry().right(), prevValue);
                           case Engine::FocusDirection::Right:
                               return std::min(window.geometry().x(), prevValue);
                           }
                       });
}
```

Don't worry about the code if it confuses you, keep in mind that we have the direction as `Engine::FocusDirection::Up`, and `neighbors` as `{A, B, C, D}`. This function gets you the closest window corner relative to the active window or the basis window. How would you do that? Well, it will depend on the direction.

If the direction is `Up` or `Down` --> you should compare the `y` coordinate.
If the direction is `Left` or `Right` --> you should compare the `x` coordinate.

Now remember the mathematics lectures you had way back in the high school, if you wanna focus up, which vertex do you really care about? Keep your focus on the window C and E for once, the comparison should definitely be with the bottom right's y coordinate, right? That's what we do here:

```cpp
case Engine::FocusDirection::Up: 
  return std::max(window.geometry().bottom(), prevValue);
```

A quick look at `bottom()` source code in `qrect.h` file:

```cpp
Q_DECL_CONSTEXPR inline QRect::bottom() const noexcept { return y2; }
```

Where `y2` is the bottom right's y coordinate. Since we are going up, and anything above the basis window should have `y` value < basis window's `y` value. (The top left of any screen is considered to be `(0, 0)` in this blog). Hence we set the initial value as `0`. If we had to go down, we'll set it to `INT_MAX` as for anything below the basis window, we'll use `std::min` and hence `INT_MAX` will fade away with each neighbor window.

Anyways, enough of theory, so what will be the output of this function for our scenario? Well, this function will give us `y_C + h` (which is equal to `y_D + h`, so any of them is fine). Now, we'll go ahead to the next function.

## Getting Closest Relative Window

```cpp
std::vector<Window> getClosestRelativeWindow(const Engine::FocusDirection &direction, const std::vector<Window> &windowArray, const int &closestPoint)
{
    std::vector<Window> result;
    std::copy_if(windowArray.cbegin(), windowArray.cend(), result.begin(), [&](const Window &window) {
        switch (direction) {
        case Engine::FocusDirection::Up:
            return window.geometry().bottom() > closestPoint - 5;
        case Engine::FocusDirection::Down:
            return window.geometry().y() < closestPoint + 5;
        case Engine::FocusDirection::Left:
            return window.geometry().right() > closestPoint - 5;
        case Engine::FocusDirection::Right:
            return window.geometry().x() < closestPoint + 5;
        }
    });
    return result;
}
```

Again, remember, we have `direction` as `Engine::FocusDirection::Up`, `windowArray` as `{A, B, C, D}`, and `closestPoint` as `y_C + h` value.

This function only exists to give you _all the windows_ which are _close enough_ to the `closestPoint`. The output out of this function will be windows `C, D` (reminder: `E` is the basis or active window).

Some will wonder why do we have two functions: `getClosestRelativeWindowCorner`, and `getClosestRelativeWindow`? And why this `-5, +5`? Unfortunately, it's possible that some windows aren't tiled properly, see [this](https://github.com/Bismuth-Forge/bismuth/issues/102) issue. I've attached the screenshot: (credits to the author)

![]("https://raw.githubusercontent.com/krshrimali/blog/main/assets/blogs/bismuth-part-2-not-sized-properly.png")

Hence we can't be too strict here. I personally believe this number `+/- 5` should be tinkered better and not hard-coded, but that's for later.

So from `A, B, C, D` being the _neighbor candidates_, we have `C, D` as the final _closest windows_ to the basis window (`E`). Now which one to choose? That's where we'll have to store the timestamps for each window. And this timestamp should record the last time it was used or accessed. We just get the most recently used out of these windows, and I'll be discussing in the future blogs. I think we discussed a lot today. So that should be it...

## Acknowledgement

I don't want to shy away from thanking the main maintainer of Bismuth, [gikari](https://github.com/gikari) who has worked pro-actively on Bismuth. Of course, the credits should also go to [krohnkite](https://github.com/esjeon/krohnkite) for the hard work they put in.

In case anyone has a feedback or suggestion, please leave a comment on this blog. I wish everyone good health and success. Thanks for reading <3
