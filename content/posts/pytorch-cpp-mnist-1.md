---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2019-06-07
linktitle: "PyTorch C++ API, MNIST"
title: "Introduction to PyTorch C++ API: MNIST Digit Recognition using VGG-16 Network"
categories:
 - pytorch
 - deep learning
tags:
 - development
 - coding
 - cpp
 - notes
 - pytorch-cpp
 - libtorch
type:
- post
- posts
weight: 10
series:
- CPP
aliases:
- /blog/pytorch-cpp-mnist-vgg-16/
---

# Environment Setup [Ubuntu 16.04, 18.04]
<!--more-->
*Note: If you have already finished installing PyTorch C++ API, please skip this section.*

1. Download `libtorch`:
    - CPU Version: `wget https://download.pytorch.org/libtorch/cpu/libtorch-shared-with-deps-latest.zip -O libtorch.zip`
    - GPU Version (CUDA 9.0): `wget https://download.pytorch.org/libtorch/cu90/libtorch-shared-with-deps-latest.zip -O libtorch.zip`
    - GPU Version (CUDA 10.0): `wget https://download.pytorch.org/libtorch/cu100/libtorch-shared-with-deps-latest.zip`

2. Unzip `libtorch.zip`:
    - `unzip libtorch.zip`

We'll use the `absolute` path of extracted directory (`libtorch`) later on.

# Implementation

The VGG-16 Network is shown in the Figure below.

![](https://raw.githubusercontent.com/krshrimali/blog/main/assets/blogs/VGG-16-Architecture-resized.png)

We'll start of by first including `libtorch` header file.

`#include <torch/torch.h>`

We'll then go ahead and define the network. We'll inherit layers from `torch::nn::Module`.


```cpp
/* Sample code for training a FCN on MNIST dataset using PyTorch C++ API */
/* This code uses VGG-16 Layer Network */

struct Net: torch::nn::Module {
    // VGG-16 Layer
    // conv1_1 - conv1_2 - pool 1 - conv2_1 - conv2_2 - pool 2 - conv3_1 - conv3_2 - conv3_3 - pool 3 -
    // conv4_1 - conv4_2 - conv4_3 - pool 4 - conv5_1 - conv5_2 - conv5_3 - pool 5 - fc6 - fc7 - fc8
    
    // Note: pool 5 not implemented as no need for MNIST dataset
    Net() {
        // Initialize VGG-16
        // On how to pass strides and padding: https://github.com/pytorch/pytorch/issues/12649#issuecomment-430156160
        conv1_1 = register_module("conv1_1", torch::nn::Conv2d(torch::nn::Conv2dOptions(1, 10, 3).padding(1)));
        conv1_2 = register_module("conv1_2", torch::nn::Conv2d(torch::nn::Conv2dOptions(10, 20, 3).padding(1)));
        // Insert pool layer
        conv2_1 = register_module("conv2_1", torch::nn::Conv2d(torch::nn::Conv2dOptions(20, 30, 3).padding(1)));
        conv2_2 = register_module("conv2_2", torch::nn::Conv2d(torch::nn::Conv2dOptions(30, 40, 3).padding(1)));
        // Insert pool layer
        conv3_1 = register_module("conv3_1", torch::nn::Conv2d(torch::nn::Conv2dOptions(40, 50, 3).padding(1)));
        conv3_2 = register_module("conv3_2", torch::nn::Conv2d(torch::nn::Conv2dOptions(50, 60, 3).padding(1)));
        conv3_3 = register_module("conv3_3", torch::nn::Conv2d(torch::nn::Conv2dOptions(60, 70, 3).padding(1)));
        // Insert pool layer
        conv4_1 = register_module("conv4_1", torch::nn::Conv2d(torch::nn::Conv2dOptions(70, 80, 3).padding(1)));
        conv4_2 = register_module("conv4_2", torch::nn::Conv2d(torch::nn::Conv2dOptions(80, 90, 3).padding(1)));
        conv4_3 = register_module("conv4_3", torch::nn::Conv2d(torch::nn::Conv2dOptions(90, 100, 3).padding(1)));
        // Insert pool layer
        conv5_1 = register_module("conv5_1", torch::nn::Conv2d(torch::nn::Conv2dOptions(100, 110, 3).padding(1)));
        conv5_2 = register_module("conv5_2", torch::nn::Conv2d(torch::nn::Conv2dOptions(110, 120, 3).padding(1)));
        conv5_3 = register_module("conv5_3", torch::nn::Conv2d(torch::nn::Conv2dOptions(120, 130, 3).padding(1)));
        // Insert pool layer
        fc1 = register_module("fc1", torch::nn::Linear(130, 50));
        fc2 = register_module("fc2", torch::nn::Linear(50, 20));
        fc3 = register_module("fc3", torch::nn::Linear(20, 10));
    }

    // Implement Algorithm
    torch::Tensor forward(torch::Tensor x) {
        x = torch::relu(conv1_1->forward(x));
        x = torch::relu(conv1_2->forward(x));
        x = torch::max_pool2d(x, 2);

        x = torch::relu(conv2_1->forward(x));
        x = torch::relu(conv2_2->forward(x));
        x = torch::max_pool2d(x, 2);

        x = torch::relu(conv3_1->forward(x));
        x = torch::relu(conv3_2->forward(x));
        x = torch::relu(conv3_3->forward(x));
        x = torch::max_pool2d(x, 2);

        x = torch::relu(conv4_1->forward(x));
        x = torch::relu(conv4_2->forward(x));
        x = torch::relu(conv4_3->forward(x));
        x = torch::max_pool2d(x, 2);

        x = torch::relu(conv5_1->forward(x));
        x = torch::relu(conv5_2->forward(x));
        x = torch::relu(conv5_3->forward(x));

        x = x.view({-1, 130});

        x = torch::relu(fc1->forward(x));
        x = torch::relu(fc2->forward(x));
        x = fc3->forward(x);

        return torch::log_softmax(x, 1);
    }

    // Declare layers
    torch::nn::Conv2d conv1_1{nullptr};
    torch::nn::Conv2d conv1_2{nullptr};
    torch::nn::Conv2d conv2_1{nullptr};
    torch::nn::Conv2d conv2_2{nullptr};
    torch::nn::Conv2d conv3_1{nullptr};
    torch::nn::Conv2d conv3_2{nullptr};
    torch::nn::Conv2d conv3_3{nullptr};
    torch::nn::Conv2d conv4_1{nullptr};
    torch::nn::Conv2d conv4_2{nullptr};
    torch::nn::Conv2d conv4_3{nullptr};
    torch::nn::Conv2d conv5_1{nullptr};
    torch::nn::Conv2d conv5_2{nullptr};
    torch::nn::Conv2d conv5_3{nullptr};

    torch::nn::Linear fc1{nullptr}, fc2{nullptr}, fc3{nullptr};
};
```

Once done, we can go ahead and test the network on our sample dataset. Let's go ahead and load data first. We'll be using 10 epochs, learning rate (0.01), and `nll_loss` as loss functio. 

```cpp
int main() {
	// Create multi-threaded data loader for MNIST data
	auto data_loader = torch::data::make_data_loader<torch::data::samplers::SequentialSampler>(
			std::move(torch::data::datasets::MNIST("/absolute/path/to/data").map(torch::data::transforms::Normalize<>(0.13707, 0.3081)).map(
				torch::data::transforms::Stack<>())), 64);
	
    // Build VGG-16 Network
    auto net = std::make_shared<Net>();

    torch::optim::SGD optimizer(net->parameters(), 0.01); // Learning Rate 0.01

	// net.train();

	for(size_t epoch=1; epoch<=10; ++epoch) {
		size_t batch_index = 0;
		// Iterate data loader to yield batches from the dataset
		for (auto& batch: *data_loader) {
			// Reset gradients
			optimizer.zero_grad();
			// Execute the model
			torch::Tensor prediction = net->forward(batch.data);
			// Compute loss value
			torch::Tensor loss = torch::nll_loss(prediction, batch.target);
			// Compute gradients
			loss.backward();
			// Update the parameters
			optimizer.step();

			// Output the loss and checkpoint every 100 batches
			if (++batch_index % 2 == 0) {
				std::cout << "Epoch: " << epoch << " | Batch: " << batch_index 
					<< " | Loss: " << loss.item<float>() << std::endl;
				torch::save(net, "net.pt");
			}
		}
	}
}
```

For code, check out my repo here: https://github.com/krshrimali/Digit-Recognition-MNIST-SVHN-PyTorch-CPP

In the next blog, we will discuss about another network on MNIST and SVHN Dataset. 

# References

1. https://pytorch.org/cppdocs/
2. http://yann.lecun.com/exdb/mnist/