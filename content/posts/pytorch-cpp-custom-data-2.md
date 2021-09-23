---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2019-07-02
linktitle: "PyTorch C++ API, Custom Data Loading"
title: "Custom Data Loading using PyTorch C++ API"
type:
- post
- posts
weight: 10
series:
- CPP
aliases:
- /blog/pytorch-cpp-data-loading
---

## Overview: How C++ API loads data?

In the last blog, we discussed application of a VGG-16 Network on MNIST Data. For those, who are reading this blog for the first time, here is how we had loaded MNIST data:

```cpp
auto data_loader = torch::data::make_data_loader<torch::data::samplers::SequentialSampler>(
			std::move(torch::data::datasets::MNIST("../../data").map(torch::data::transforms::Normalize<>(0.13707, 0.3081))).map(
				torch::data::transforms::Stack<>()), 64);
```

Let's break this piece by piece, as for beginners, this may be unclear. First, we ask the C++ API to load data (images and labels) into tensors.

```cpp
// Your data should be at: ../data position
auto data_set = torch::data::datasets::MNIST("../data");
```

If you have this question on how the API loads the images and labels to tensors - we'll get to that. For now, just take it as a black box, which loads the data. Next, we apply transforms (like normalizing to ImageNet standards):

```cpp
auto data_set = data_set.map(torch::data::transforms::Normalize<>(0.13707, 0.3081)).map(torch::data::transforms::Stack<>())
```

For the sake of batch size, let's divide the data for batch size as 64.

```cpp
std::move(data_set, 64);
```

Once this all is done, we can iterate through the data loader and pass each batch to the network. It's time to understand how this all works, let's go ahead and look at the source code of `torch::data::datasets::MNIST` class.

```cpp
namespace torch {
namespace data {
namespace datasets {
/// The MNIST dataset.
class TORCH_API MNIST : public Dataset<MNIST> {
 public:
  /// The mode in which the dataset is loaded.
  enum class Mode { kTrain, kTest };

  /// Loads the MNIST dataset from the root path.
  ///
  /// The supplied root path should contain the content of the unzipped
  /// MNIST dataset, available from http://yann.lecun.com/exdb/mnist.
  explicit MNIST(const std::string& root, Mode mode = Mode::kTrain);

  /// Returns the Example at the given index.
  Example<> get(size_t index) override;

  /// Returns the size of the dataset.
  optional<size_t> size() const override;

  /// Returns true if this is the training subset of MNIST.
  bool is_train() const noexcept;

  /// Returns all images stacked into a single tensor.
  const Tensor& images() const;

  /// Returns all targets stacked into a single tensor.
  const Tensor& targets() const;

 private:
  Tensor images_, targets_;
};
} // namespace datasets
} // namespace data
} // namespace torch
```

Reference: https://github.com/pytorch/pytorch/blob/master/torch/csrc/api/include/torch/data/datasets/mnist.h

Assuming the reader has done some basic C++ before reading this, they will be very well aware of how to initialize a C++ Class. Let's go step by step. What happens when we initialize the class? Let's look at the definition of constructor of the class MNIST at `mnist.cpp`:

```cpp
MNIST::MNIST(const std::string& root, Mode mode)
    : images_(read_images(root, mode == Mode::kTrain)),
      targets_(read_targets(root, mode == Mode::kTrain)) {}
```

Observing the above snippet, it's clear that the constructor calls `read_images(root, mode)` and `read_targets` for loading images and labels into tensors. Let's go to the source code of `read_images()` and `read_targets()`.

1. **read_images()**:

```cpp
Tensor read_images(const std::string& root, bool train) {
  // kTrainImagesFilename and kTestImagesFilename are specific to MNIST dataset here
  // No need for using join_paths here
  const auto path =
      join_paths(root, train ? kTrainImagesFilename : kTestImagesFilename);

  // Load images
  std::ifstream images(path, std::ios::binary);
  TORCH_CHECK(images, "Error opening images file at ", path);
  // kTrainSize = len(training data)
  // kTestSize = len(testing_data)
  const auto count = train ? kTrainSize : kTestSize;

  // Specific to MNIST data
  // From http://yann.lecun.com/exdb/mnist/
  expect_int32(images, kImageMagicNumber);
  expect_int32(images, count);
  expect_int32(images, kImageRows);
  expect_int32(images, kImageColumns);

  // This converts images to tensors
  // Allocate an empty tensor of size of image (count, channels, height, width)
  auto tensor =
      torch::empty({count, 1, kImageRows, kImageColumns}, torch::kByte);
  // Read image and convert to tensor
  images.read(reinterpret_cast<char*>(tensor.data_ptr()), tensor.numel());
  // Normalize the image from 0 to 255 to 0 to 1
  return tensor.to(torch::kFloat32).div_(255);
}
```

2. **read_targets()**:

```cpp
Tensor read_targets(const std::string& root, bool train) {
  // Specific to MNIST dataset (kTrainImagesFilename and kTestTargetsFilename)
  const auto path =
      join_paths(root, train ? kTrainTargetsFilename : kTestTargetsFilename);
  // Read the labels
  std::ifstream targets(path, std::ios::binary);
  TORCH_CHECK(targets, "Error opening targets file at ", path);

  // kTrainSize = len(training_labels)
  // kTestSize = len(testing_labels)
  const auto count = train ? kTrainSize : kTestSize;

  expect_int32(targets, kTargetMagicNumber);
  expect_int32(targets, count);

  // Allocate an empty tensor of size of number of labels
  auto tensor = torch::empty(count, torch::kByte);
  // Convert to tensor
  targets.read(reinterpret_cast<char*>(tensor.data_ptr()), count);
  return tensor.to(torch::kInt64);
}
```

Since we are now done with how the constructor works, let's go ahead and see what other functions does the class inherit.

```cpp
Example<> MNIST::get(size_t index) {
  return {images_[index], targets_[index]};
}

optional<size_t> MNIST::size() const {
  return images_.size(0);
}
```

The above two functions: `get(size_t)` and `size()` are used to get a sample image and label and length of the data respectively.

## The Pipeline

Since we are now clear with the possible pipeline of loading custom data:

1. Read Images and Labels
2. Convert to Tensors
3. Write `get()` and `size()` functions
4. Initialize the class with paths of images and labels
5. Pass it to the data loader

## Coding your own Custom Data Loader

Let's first write the template of our custom data loader:

```cpp
// Include libraries
#include <ATen/ATen.h>
#include <torch/torch.h>
#include <iostream>
#include <vector>
#include <tuple>
#include <opencv2/opencv.hpp>
#include <string>

/* Convert and Load image to tensor from location argument */
torch::Tensor read_data(std::string location) {
  // Read Data here
  // Return tensor form of the image
  return torch::Tensor;
}

/* Converts label to tensor type in the integer argument */
torch::Tensor read_label(int label) {
  // Read label here
  // Convert to tensor and return
  return torch::Tensor;
}

/* Loads images to tensor type in the string argument */
vector<torch::Tensor> process_images(vector<string> list_images) {
  cout << "Reading Images..." << endl;
  // Return vector of Tensor form of all the images
  return vector<torch::Tensor>;
}

/* Loads labels to tensor type in the string argument */
vector<torch::Tensor> process_labels(vector<string> list_labels) {
  cout << "Reading Labels..." << endl;
  // Return vector of Tensor form of all the labels
  return vector<torch::Tensor>;
}

class CustomDataset : public torch::data::dataset<CustomDataset> {
private:
  // Declare 2 vectors of tensors for images and labels
  vector<torch::Tensor> images, labels;
public:
  // Constructor
  CustomDataset(vector<string> list_images, vector<string> list_labels) {
    images = process_images(list_images);
    labels = process_labels(list_labels);
  };

  // Override get() function to return tensor at location index
  torch::data::Example<> get(size_t index) override {
    torch::Tensor sample_img = images.at(index);
    torch::Tensor sample_label = labels.at(index);
    return {sample_img.clone(), sample_label.clone()};
  };

  // Return the length of data
  torch::optional<size_t> size() const override {
    return labels.size();
  };
};
```

We are almost there, all we need to do is - Read Images and Labels to `torch::Tensor` type. I'll be using OpenCV to read images, as it also helps later on to visualize results.

**Reading Images**:

The process to read an image in OpenCV is trivial: `cv::imread(std::string location, int)`. We then convert it to a tensor. Note that a tensor is of form (batch size, channels, height, width), so we also permute the tensor to that form.

```cpp
torch::Tensor read_data(std::string loc) {
	// Read Image from the location of image
	cv::Mat img = cv::imread(loc, 1);

  // Convert image to tensor
	torch::Tensor img_tensor = torch::from_blob(img.data, {img.rows, img.cols, 3}, torch::kByte);
	img_tensor = img_tensor.permute({2, 0, 1}); // Channels x Height x Width

	return img_tensor.clone();
};
```

**Reading Labels**:

```cpp
// Read Label (int) and convert to torch::Tensor type
torch::Tensor read_label(int label) {
	torch::Tensor label_tensor = torch::full({1}, label);
	return label_tensor.clone();
}
```

## Final Code

Let's wrap up the code!

```cpp
// Include libraries
#include <ATen/ATen.h>
#include <torch/torch.h>
#include <iostream>
#include <vector>
#include <tuple>
#include <opencv2/opencv.hpp>
#include <string>

/* Convert and Load image to tensor from location argument */
torch::Tensor read_data(std::string loc) {
  // Read Data here
  // Return tensor form of the image
  cv::Mat img = cv::imread(loc, 1);
	cv::resize(img, img, cv::Size(1920, 1080), cv::INTER_CUBIC);
	std::cout << "Sizes: " << img.size() << std::endl;
	torch::Tensor img_tensor = torch::from_blob(img.data, {img.rows, img.cols, 3}, torch::kByte);
	img_tensor = img_tensor.permute({2, 0, 1}); // Channels x Height x Width

	return img_tensor.clone();
}

/* Converts label to tensor type in the integer argument */
torch::Tensor read_label(int label) {
  // Read label here
  // Convert to tensor and return
  torch::Tensor label_tensor = torch::full({1}, label);
	return label_tensor.clone();
}

/* Loads images to tensor type in the string argument */
vector<torch::Tensor> process_images(vector<string> list_images) {
  cout << "Reading Images..." << endl;
  // Return vector of Tensor form of all the images
  vector<torch::Tensor> states;
	for (std::vector<string>::iterator it = list_images.begin(); it != list_images.end(); ++it) {
		torch::Tensor img = read_data(*it);
		states.push_back(img);
	}
	return states;
}

/* Loads labels to tensor type in the string argument */
vector<torch::Tensor> process_labels(vector<string> list_labels) {
  cout << "Reading Labels..." << endl;
  // Return vector of Tensor form of all the labels
  vector<torch::Tensor> labels;
	for (std::vector<int>::iterator it = list_labels.begin(); it != list_labels.end(); ++it) {
		torch::Tensor label = read_label(*it);
		labels.push_back(label);
	}
	return labels;
}

class CustomDataset : public torch::data::dataset<CustomDataset> {
private:
  // Declare 2 vectors of tensors for images and labels
  vector<torch::Tensor> images, labels;
public:
  // Constructor
  CustomDataset(vector<string> list_images, vector<string> list_labels) {
    images = process_images(list_images);
    labels = process_labels(list_labels);
  };

  // Override get() function to return tensor at location index
  torch::data::Example<> get(size_t index) override {
    torch::Tensor sample_img = images.at(index);
    torch::Tensor sample_label = labels.at(index);
    return {sample_img.clone(), sample_label.clone()};
  };

  // Return the length of data
  torch::optional<size_t> size() const override {
    return labels.size();
  };
};

int main(int argc, char** argv) {
  vector<string> list_images; // list of path of images
  vector<int> list_labels; // list of integer labels

  // Dataset init and apply transforms - None!
  auto custom_dataset = CustomDataset(list_images, list_labels).map(torch::data::transforms::Stack<>());
}
```

That's it for today! In the next blog, we'll use this custom data loader and implement a CNN on our data. By then, happy learning. Hope you liked this blog. :)