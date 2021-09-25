---
author:
  name: "Kushashwa Ravi Shrimali"
date: 2019-07-23
linktitle: "PyTorch C++ API, Dogs vs Cats"
title: "Classifying Dogs vs Cats using PyTorch C++ API: Part-1"
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
- /blog/pytorch-cpp-dogs-vs-cats/
toc: true
comments: true
---

Hi Everyone! So excited to be back with another blog in the series of PyTorch C++ Blogs. 

Today, we are going to see a practical example of applying a CNN to a Custom Dataset - Dogs vs Cats. This is going to be a short post of showing results and discussion about hyperparameters and loss functions for the task, as code snippets and explanation has been provided [here](https://krshrimali.github.io/Training-Network-Using-Custom-Dataset-PyTorch-CPP/), [here](https://krshrimali.github.io/Custom-Data-Loading-Using-PyTorch-CPP-API/) and [here](https://krshrimali.github.io/PyTorch-C++-API/).

![](https://raw.githubusercontent.com/krshrimali/blog/main/assets/cover-images/Cover-Dogs-Cats.jpg)

<!--more-->

**Note**: This is Part-1 of the blog on Dogs vs Cats Classification using PyTorch C++ API.

## Dataset Overview

Let's have a look at the dataset and it's statistics. **Dogs vs Cats** dataset has been taken from the famous [Kaggle Competition](https://www.kaggle.com/c/dogs-vs-cats). 

The training set contains 25k images combined of dogs and cats. The data can be downloaded from [this](https://www.kaggle.com/c/dogs-vs-cats/data) link. 

Let's have a look at sample of the data:

![Figure 1: Sample of Dog Images in the Dataset](https://raw.githubusercontent.com/krshrimali/krshrimali.github.io/master/assets/dogs-dataset.jpg)

![Figure 2: Sample of Cat Images in the Dataset](https://raw.githubusercontent.com/krshrimali/krshrimali.github.io/master/assets/cats-dataset.jpg)

As we can see, the dataset contains images of cats and dogs with multiple instances in the same sample as well.

## Loading Data

Although we have discussed this before ([here](https://krshrimali.github.io/Custom-Data-Loading-Using-PyTorch-CPP-API/)), but let's just see how we load the data. Since this is a binary classification problem (2 classes: Dog and Cat), we will have labels as 0 (for a Cat) and 1 (for a Dog). The data comes in two zip files:

1. `train.zip`: Data to be used for training
2. `test.zip`: Data to be used for testing

The `train.zip` file contains files with filenames like `<class>.<number>.jpg` where:

* `class` can be either cat or dog.
* `number` represents the count of the sample.

For example: `cat.100.jpg` and `dog.1.jpg`. In order to load the data, we will move the cat images to `train/cat` folder and dog images to `train/dog` folder. You can accomplish this using `shutil` module:

```python
# This code moves cat and dog images to train/cat and train/dog folders respectively
import shutil, os

files = os.listdir('train/')

count_cat = 0 # Number representing count of the cat image
count_dog = 0 # Number representing count of the dog image

for file in files:
	if(file.startswith('cat') and file.endswith('jpg')):
		count_cat += 1
		shutil.copy('train/' + file, 'train/cat/' + str(count_cat) + ".jpg")
	elif(file.startswith('dog') and file.endswith('jpg')):
		count_dog += 1
		shutil.copy('test/' + file, 'train/dog/' + str(count_dog) + '.jpg')
```

Once done, let's go ahead and load this data. Since we have discussed this [before](https://krshrimali.github.io/posts/2019/07/custom-data-loading-using-pytorch-c-api/), I'll just paste the snippet here.

```cpp
torch::Tensor read_data(std::string loc) {
	// Read Image from the location of image
	cv::Mat img = cv::imread(loc, 0);
	cv::resize(img, img, cv::Size(200, 200), cv::INTER_CUBIC);
	std::cout << "Sizes: " << img.size() << std::endl;
	torch::Tensor img_tensor = torch::from_blob(img.data, {img.rows, img.cols, 1}, torch::kByte);
	img_tensor = img_tensor.permute({2, 0, 1}); // Channels x Height x Width

	return img_tensor.clone();
};

torch::Tensor read_label(int label) {
	torch::Tensor label_tensor = torch::full({1}, label);
	return label_tensor.clone();
}

vector<torch::Tensor> process_images(vector<string> list_images) {
	cout << "Reading images..." << endl;
	vector<torch::Tensor> states;
	for (std::vector<string>::iterator it = list_images.begin(); it != list_images.end(); ++it) {
        cout << "Location being read: " << *it << endl;
		torch::Tensor img = read_data(*it);
		states.push_back(img);
	}
	cout << "Reading and Processing images done!" << endl;
	return states;
}

vector<torch::Tensor> process_labels(vector<int> list_labels) {
	cout << "Reading labels..." << endl;
	vector<torch::Tensor> labels;
	for (std::vector<int>::iterator it = list_labels.begin(); it != list_labels.end(); ++it) {
		torch::Tensor label = read_label(*it);
		labels.push_back(label);
	}
	cout << "Labels reading done!" << endl;
	return labels;
}

/* This function returns a pair of vector of images paths (strings) and labels (integers) */
std::pair<vector<string>,vector<int>> load_data_from_folder(vector<string> folders_name) {
	vector<string> list_images;
	vector<int> list_labels;
	int label = 0;
	for(auto const& value: folders_name) {
		string base_name = value + "/";
		cout << "Reading from: " << base_name << endl;
		DIR* dir;
		struct dirent *ent;
		if((dir = opendir(base_name.c_str())) != NULL) {
			while((ent = readdir(dir)) != NULL) {
				string filename = ent->d_name;
				if(filename.length() > 4 && filename.substr(filename.length() - 3) == "jpg") {
					cout << base_name + ent->d_name << endl;
					// cv::Mat temp = cv::imread(base_name + "/" + ent->d_name, 1);
					list_images.push_back(base_name + ent->d_name);
					list_labels.push_back(label);
				}

			}
			closedir(dir);
		} else {
			cout << "Could not open directory" << endl;
			// return EXIT_FAILURE;
		}
		label += 1;
	}
	return std::make_pair(list_images, list_labels);
}
```

The above snippet has the utility functions we need. Here is a quick summary of what they do:

1. **load_data_from_folder**: This function returns a tuple of list of image paths (string) and list of labels (int). It takes a vector of folders names (string type) as parameter. 

2. **process_images**: This function returns a vector of Tensors (images). This function calls `read_data` function which reads, resizes and converts an image to a Torch Tensor. It takes a vector of image paths (string) as parameter.

3. **process_labels**: Similar to `process_images` function, this function returns a vector of Tensors (labels). This function calls `read_label` function which takes an `int` as a parameter (label: 0 or 1) and returns a Tensor.


Let's now go ahead and see how we load the data. For this, we first need to define the `Dataset` class. This class should initialize two variables: one for images and one for labels. As discussed [here](https://krshrimali.github.io/posts/2019/07/custom-data-loading-using-pytorch-c-api/), we'll also define `get()` and `size()` functions.


```cpp
class CustomDataset : public torch::data::Dataset<CustomDataset> {
private:
	/* data */
	// Should be 2 tensors
	vector<torch::Tensor> states, labels;
public:
	CustomDataset(vector<string> list_images, vector<int> list_labels) {
		states = process_images(list_images);
		labels = process_labels(list_labels);
	};

	torch::data::Example<> get(size_t index) override {
		/* This should return {torch::Tensor, torch::Tensor} */
		torch::Tensor sample_img = states.at(index);
		torch::Tensor sample_label = labels.at(index);
		return {sample_img.clone(), sample_label.clone()};
	};

  torch::optional<size_t> size() const override {
		return states.size();
  };
};
```

Once done, we can go ahead and initialize the Dataset in our `main()` function.

```cpp
int main(int argc, char const *argv[]) {
  // Load the model.
  // Read Data
  vector<string> folders_name;
  folders_name.push_back("/home/krshrimali/Documents/data-dogs-cats/train/cat");
  folders_name.push_back("/home/krshrimali/Documents/data-dogs-cats/train/dog");

  std::pair<vector<string>, vector<int>> pair_images_labels = load_data_from_folder(folders_name);

  vector<string> list_images = pair_images_labels.first;
  vector<int> list_labels = pair_images_labels.second;

  auto custom_dataset = CustomDataset(list_images, list_labels).map(torch::data::transforms::Stack<>());
}
```

## Network Overview

To make things easy to read (a programmer's mantra), we define our network in a header file. We will use a CNN network initially for this binary classification task. Since I'm not using a GPU, the training is slow and that's why I experimented it only for 10 epochs. The whole objective is to discuss and show how to use PyTorch C++ API for this. You can always run it for more epochs or change the network parameters. 

```cpp
struct NetImpl: public torch::nn::Module {
    NetImpl() {
        // Initialize the network
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
        fc1 = register_module("fc1", torch::nn::Linear(130*6*6, 2000));
        fc2 = register_module("fc2", torch::nn::Linear(2000, 1000));
        fc3 = register_module("fc3", torch::nn::Linear(1000, 100));
        fc4 = register_module("fc4", torch::nn::Linear(100, 2));
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
        x = torch::max_pool2d(x, 2);


        x = x.view({-1, 130*6*6});

        x = torch::relu(fc1->forward(x));
        x = torch::relu(fc2->forward(x));
        x = torch::relu(fc3->forward(x));
        x = fc4->forward(x);
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

    torch::nn::Linear fc1{nullptr}, fc2{nullptr}, fc3{nullptr}, fc4{nullptr};
};
```

We will initialize this network and pass each batch of our data once in an epoch.

```cpp
// Initialize the Network
auto net = std::make_shared<NetImpl>();
```

## Training the Network on Dogs vs Cats Dataset

We had before discussed code for training [here](https://krshrimali.github.io/posts/2019/07/training-a-network-on-custom-dataset-using-pytorch-c-api/). I suggest the reader to go through that blog in order to train the dataset. I'll give more insights on training in the next blog!

That's it for today. I'll be back with Part-2 of this "Dogs vs Cats Classification" with training, experimentation and results. We'll also discuss on using different networks, and in the Part-3, we'll discuss using **Transfer Learning** for this classification task.
