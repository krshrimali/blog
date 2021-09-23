---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2020-09-15
linktitle: "PyTorch C++ API, Docker Container with OpenCV"
title: "Releasing Docker Container and Binder for using Xeus-Cling, Libtorch and OpenCV in C++"
type:
- post
- posts
weight: 10
series:
- CPP
aliases:
- /blog/pytorch-cpp-opencv-docker/
---

Today, I am elated to share Docker image for `OpenCV`, `Libtorch` and `Xeus-Cling`. We'll discuss how to use the `dockerfile` and `binder`.

<img src="/assets/Cover-Docker-Binder.jpg"/>

Before I move on, the credits for creating and maintaining Docker image goes to <a href="https://github.com/vishwesh5">Vishwesh Ravi Shrimali</a>. He has been working on some cool stuff, please do get in touch with him if you're interested to know.

First question in your mind would be, **Why use Docker or Binder?** The answer to it lies in the frequency of queries on <a href="http://www.discuss.pytorch.org">the discussion forum of PyTorch</a> and Stackoverflow on **Installation of Libtorch with OpenCV in Windows/Linux/OSX**. I've had nightmares setting up the Windows system myself for `Libtorch` and nothing could be better than using `Docker`. Read on, to know why.

## Installing Docker on Mac OS

To install docker (community edition - CE) desktop in Mac OS system, simply navigate to the Stable Channel section <a href="https://docs.docker.com/v17.12/docker-for-mac/install/#download-docker-for-mac">here</a>. Once setup, you can use docker (command line and desktop). Once done, navigate to <a href="https://docs.docker.com/v17.12/docker-for-mac/install/#install-and-run-docker-for-mac">Install and run Docker for Mac</a> section and get used to the commands.

## Installing Docker on Ubuntu

Before moving on, please consider reading the <a href="https://docs.docker.com/v17.12/install/linux/docker-ce/ubuntu/">requirements to install Docker Community Edition</a>. For the steps to install `Docker CE`, refer <a href="https://docs.docker.com/v17.12/install/linux/docker-ce/ubuntu/#install-docker-ce-1">this</a>.

## Installing Docker on Windows

To install Docker on Windows, download docker (stable channel) from <a href="https://docs.docker.com/v17.12/docker-for-windows/install/#download-docker-for-windows">here</a>. The installation steps to install `Docker Desktop` on Windows can be found <a href="https://docs.docker.com/v17.12/docker-for-windows/install/#install-docker-for-windows-desktop-app">here</a>.

## Using Docker Image 

1. Fetch the docker image: `docker pull vishwesh5/libtorch-opencv:opencv-4-1-0`. This shall take a lot of time, so sit back and relax.
2. Run: `docker run -p 5000:5000 -p 8888:8888 -it vishwesh5/libtorch-opencv:opencv-4-1-0 /bin/bash`.

To know more about these commands, check out the references section.

Once done, you'll see your terminal showing another username: `jovyan`. You've entered the docker image, congratulations! No need to setup `OpenCV` or `Libtorch`. Vishwesh has done it for you!

Now since you have entered the docker container successfully, it should look something similar to this:

<img src="/assets/Docker-Image-1.png"/>

Time to test `Libtorch`. Let's go ahead and test a simple VGG-Net on MNIST dataset using Libtorch.

## Testing Docker Image

1. Clone the repository containing code for **Digit Classification using Libtorch on MNIST dataset**: `git clone https://github.com/krshrimali/Digit-Recognition-MNIST-SVHN-PyTorch-CPP.git`. Change directory to the cloned repository. 
2. Download the MNIST data from http://yann.lecun.com/exdb/mnist/. Download `train-images-idx3-ubyte.gz` and `train-labels-idx1-ubyte.gz` files for training the VGG-Net. You can skip downloading the test data for now. Use `gunzip <file_path>` to extract the training images and labels, and put them in the `data/` folder inside the clones repository.
3. Create a `build` folder: `mkdir build`
4. Run the CMake Configuration using: `cmake -DCMAKE_PREFIX_PATH=/opt/libtorch ..`. The result should be similar to something in the figure below.
5. Build the code using `make` command: `make`.
6. Execute the code, and that's it. Have fun learning.

<img src="/assets/Docker-Image-2.png"/>

## Testing Docker Image with Xeus-Cling

Let's test the Docker Image with Xeus-Cling.

1. Run `jupyter notebook` command in the console and copy the token from the url provided.
2. Open `http://localhost:8888` in your browser. Note that the port address (`8888`) comes from `-p 8888:8888` in the `docker run` command. You can change that if you want. Enter the token when asked.
3. Start a new notebook using `C++XX` kernel.
4. Include and load libraries in the first cell using: `#include "includeLibraries.h"`. This should do all the stuff for you.
5. Start doing experiments using Xeus-Cling now.

## Using Binder

And! What if you just want to try `Libtorch` or show it to the students? What if you are on a remote PC, and can't install Docker? Well, here is the `Binder`: https://mybinder.org/v2/gh/vishwesh5/torch-binder/master.

Go to the above link and a notebook shall open. 

Create a new notebook and start with: `#include "includeLibraries.h"` first and then start testing.

## Acknowledgements

Thanks to Vishwesh Ravi Shrimali, for creating the docker container and binder for this post.

## References

1. <a href="https://www.learnopencv.com/install-opencv-docker-image-ubuntu-macos-windows/">Install OpenCV Docker Image on Ubuntu, MacOS or Windows by Vishwesh Ravi Shrimali</a>.