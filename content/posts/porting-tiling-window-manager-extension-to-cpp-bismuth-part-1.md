---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2022-07-23
 linktitle: Porting a Tiling Window Manager Extenstion to C++
 title: "Porting a Tiling Window Manager Extenstion to C++ (Bismuth): Part-1"
 categories:
 - cpp
 - projects
 - open-source
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
 - /blog/porting-tiling-wm-to-cpp/
 toc: true
 comments: true
---

# Porting a KDE Tiling Window Manager Extension from TypeScript to C++ [Bismuth]: Part-1 (Introduction)

Hi everyone! I understand it's been a long time, and I'm so excited to be writing this blog today. In today's blog, I wanted to talk about my journey (so far) on contributing to [Bismuth (a KDE's Tiling Window Manager Extension)](https://github.com/Bismuth-Forge/bismuth/), mainly how and why I started, and where I am right now.

## The Story: Why KDE Plasma and Why Bismuth?

For the last few months (close to a year), I've been using Pop OS (a linux distribution by System 76) which had this amazing automatic tiling window extension called [`pop-shell`](https://github.com/pop-os/shell), and it was close to what I always needed:

1. Tiling.
2. A desktop environment.
3. Ability to configure keyboard shortcuts.
4. Ability to turn-off tiling to floating.
5. An option to launch specific windows as floating windows. (example: Steam)
6. An active community to seek help or suggestions from.
7. Open-Sourced!

Now some would say that there is a possibility to install tiling window managers on desktop environments (I'm aware [i3 on KDE Plasma](https://github.com/heckelson/i3-and-kde-plasma)), but that just felt... _odd_ for some reason. So I stuck with Pop OS, until [this happened](https://github.com/pop-os/shell/issues/1470), oh and also [this](https://github.com/pop-os/pop/issues/2444). The second issue where there was a lag while dragging windows, was unfortunately not a Pop OS bug but was mostly related to upstream (mutter if I'm not wrong). And when they say that it only happened with NVIDIA drivers, I knew that it's something that will probably take some time to resolve (I would rather prefer not to get into the details here).

That's when I decided to explore KDE Plasma. KDE Plasma 5.25 was just announced, and oh man - it seemed to have impressed a lot of people out there. However, what impressed me the most was that it had no such issues with NVIDIA drivers, at least no lag while dragging windows. I also liked their zoom accessibility feature, much much much better than what GNOME had. Needless to say, that I had decided to stick to KDE Plasma after that.

Just to give some context, I use multiple monitors and while people happily survive without a tiling window manager, I was the opposite - I felt the need of tiling, specially when I started streaming or sharing my work with others. And then I saw [this video: "TILING comes to KDE Kwin? ;)"](https://www.youtube.com/watch?v=TQzaDrmsE9A)! I was wow-ed (is that a word BTW?). Though the video's title was click-baity, but it served the purpose. I was introduced to this amazing KDE Tiling Window Manager Extension named **Bismuth** (https://github.com/Bismuth-Forge/bismuth/). I didn't waste any time in installing and setting up the extension on my machine...

## The Motivation: Why contribute?

Of course, with great power comes great responsibility, and in the Linux ecosystem, _with more users, comes more bugs_. The same happened with Bismuth, lots of users started trying it, and it had good amount of issues, interestingly, less were bugs and more were about features. However, I got stuck with one of the most important feature I needed, and it was "Move window to the next/previous screen/monitor" with a keyboard-shortcut. Now, do note that Bismuth did promise that it comes with the feature, so it was a bug. And as any other user would do, I thought of raising an issue but there was one already: [here](https://github.com/Bismuth-Forge/bismuth/issues/370). I regularly move my windows from one screen to another with keyboard shortcuts, and with this bug, I started facing issues. But as they say, in open-source, the community is everything. A guy with username: [benemorius](https://github.com/benemorius) came up with a solution, and even though it took me some time to get it working, but it was eventually fixed. I started realizing how much I love this process, but more than that - I wanted to dive into the source code, and understand how it works. That was the time I realized I will look at the issues, found many opened, but since the maintainer of the library had a goal of porting it from typescript to C++, which meant that new features were essentially blocked till then (unless and until they are small with respect to the number of lines of code).

That was the time I realized that I should stop complaining, and instead start helping. I found an opened issue [here](https://github.com/Bismuth-Forge/bismuth/issues/335#issuecomment-1159362257) and left a comment. The maintainer was very kind to respond, and guide through the process. And that's where I started contributing to Bismuth.

To a lot of people, and even to me, porting looks like an onboarding task, you have got things baked in for yourself, all you have to do is port it to another language. This was different though, I realized that I might have to write my own code at some places (https://github.com/Bismuth-Forge/bismuth/issues/335#issuecomment-1159993392), it was a re-write from ground up.

One thing I missed writing so far, was how much I loved developing tools and libraries. It's something that comes naturally to me, and Bismuth seemed to be an amazing place to continue my passion.

## Contributions

For those who might be unaware, I did all my contributions (so far) live on my Twitch channel: [buffetcodes](https://twitch.tv/buffetcodes), and have uploaded all the recordings on my [YouTube channel](https://youtube.com/c/kushashwaraviShrimali). There is a [playlist if you are interested](https://www.youtube.com/playlist?list=PLfjzHJeA53gTMjuPI1YaQ9jjZx_E8mqJZ).

Honestly speaking, I had no clue when I started that how the journey will be, how easy/difficult it will be! To me, it was just fun. I don't know if it was easy, or if it was difficult, it was just something very fun to do! Plus, came with a lot of learning. So far, when I'm writing this blog, I've 2 opened PRs:

1. [C++ Port: `focusWindowByDirection`](https://github.com/Bismuth-Forge/bismuth/pull/387)
2. [C++ Port: `ThreeColumn` layout](https://github.com/Bismuth-Forge/bismuth/pull/393)

To give you a glimpse, here is how the code looks when you do press a keyboard shortcut to focus window to your left/right/up/down:

```cpp
void Engine::focusWindowByDirection(FocusDirection direction)
{
    auto windowsToChoseFrom = m_windows.visibleWindowsOn(activeSurface());

    if (windowsToChoseFrom.empty()) {
        return;
    }

    // If there is no current window, select the first one.
    auto activeWindow = m_windows.activeWindow();
    if (!activeWindow.has_value()) {
        activeWindow = windowsToChoseFrom.front();
    }

    auto window = windowNeighbor(direction, activeWindow.value());

    if (window.has_value()) {
        window->activate();
    }
}
```

Let's consider that you are trying to focus right from your current window, so the parameter `direction` will have a value of `FocusDirection::Right` (it's an `enum`). The current state of Bismuth only allowed you to move right/left/top/bottom on the current screen, that means if you want to move to the next monitor - you can't use the same keyboard shortcuts. Hence the first line in the body of the function:

```cpp
// This gets all the visible windows (not hidden) on the active screen/montior/surface
auto windowsToChoseFrom = m_windows.visible(activeSurface());
```

Now of-course there is a possibility that you have no windows visible on the surface, in that case it will just return (which is what the next 3 lines do):

```cpp
// Early return if no window is visible on the current surface
if (windowsToChoseFrom.empty()) {
  return;
}
```

Okay, now comes the serious part. Whenever you think of `focusWindowByDirection`, there are 2 possibilities (apart from those listed above):

1. You have an active window, that means your mouse is already focused on a window on the current screen.
2. You don't have an active window, that means your focus can be on the panel, or maybe on an icon or wherever except a window on the current surface.

These two cases need to be handled, and that's what the next few lines do:

```cpp
// If there is no current window, select the first one.
auto activeWindow = m_windows.activeWindow();
if (!activeWindow.has_value()) {
    activeWindow = windowsToChoseFrom.front();
}
```

Once the extension knows what `activeWindow` is, it's comparatively easier to figure out which window to focus on (only if it's possible). Time to talk about the function that does the magic.

```cpp
/* This function returns the closest window (if any) from the current window for the given direction */
std::optional<Window> Engine::windowNeighbor(Engine::FocusDirection direction, const Window &basisWindow);
```

Above is the declaration of the function, and hopefully the comment describes it well. You will definitely need to know the window relative to which you'll return the output window, and the direction is a must. Note the return type, `std::optional<Window>`. As I said, it is possible that there is a window to the right, it's also possible that there are no more windows to the right direction. Hence [`std::optional`](https://en.cppreference.com/w/cpp/utility/optional) there.

Let me quickly talk about the algorithm that Bismuth follows for this feature:

1. Get all possible candidates in the neighborhood of the active window _for the given direction_:
  * If the direction is right, you need to know how many _tiled_ windows are on the right to the active window.
  * These neighbor candidates can also be on the top-right if the given direction is right.
2. Get the _closest_ relative window from the candidates selected in the step-1.
3. If there are multiple windows from step-2, return the window which was used recently (this means that we need each window to have "the time it was last used" as a meta-data).

I'll be diving deep into the code for each of these steps in my next blog.

Do note that I'm not doing this full-time, so this will obviously look slow to a lot of people, but I see a motivation behind doing this. I also believe that it is worth to mention [benemorius's work](https://github.com/benemorius/bismuth/) on Bismuth, where has fixed a lot of the issues + added new features to Bismuth, and that is amazing! Shoutout to him on what he has been doing for the community.

Thank you for reading this blog, and if you are interested, feel free to check out [Bismuth](https://github.com/Bismuth-Forge/bismuth/). 😄❤️
