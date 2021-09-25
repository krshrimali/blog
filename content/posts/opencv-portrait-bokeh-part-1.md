---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2020-12-07
 linktitle: OpenCV, Portrait Bokeh Part-1
 title: "Implementing Portrait Bokeh in OpenCV using Face Detection (Part-1)"
 categories:
 - opencv
 tags:
 - computer vision
 - python
 - portrait bokeh
 - image processing
 type:
 - post
 - posts
 weight: 10
 series:
 - CPP
 aliases:
 - /blog/opencv-portrait-bokeh-part-1/
---

![](https://raw.githubusercontent.com/krshrimali/blog/main/assets/cover-images/Dec_7_2020.jpg)

# OpenCV: Using face detection for Portrait Bokeh (Background Blur) (Part - 1)

This blog discusses using Face Detection in OpenCV for Portrait Bokeh. We'll be implementing Portrait Bokeh (blurring everything but faces) using 3 different methods in this series:

1. Using Face Detection (cropping a rectangle)
2. Using Face Detection (cropping a circle)
3. Using Facial Landmark Detection and Convex Hull

Don't lose hopes if you are confused. We will be going through each method one by one, and hopefully the road will be crearer from here.

## Portrait Bokeh: Discussing Problem Statement

Before moving ahead, let's talk about "What is Portrait Bokeh?". It's important to talk about the problem before discussing solutions. Take a quick look at the two images below:

<img src="/assets/opencv/input_method1.jpeg" /> <img src="/assets/opencv/output_final.jpg" />

As you might have spotted the difference already, the image on the left is our input (/original) image while the image on the right is our output image. If you haven't spotted the difference, everything except the face in the image on the right is blurred! This feature now comes in almost all smart phones, and is also termed as just Portrait mode. Whenever you want to highlight the people near to the camera (mostly you, your friends or anyone) and blur the background, this is the mode you will usually choose. While some blur everything except faces, others might choose to keep the body instead of just faces. Our problem statement will be limited to faces here.

## Methodology opted

Let's discuss on how we can go ahead to solve this problem. We surely need to know where the face is to avoid blurring it, so the first step has to be of face detection. And since we need to blur the background, so at some stage, we need to do blurring as well. Since this part is about the simplest step, we can just combine them and say:

1. Detect face(s) from the given input image.
2. Crop the faces and store them as separate objects.
3. Blur the whole image.
4. Overlay the cropped faces from step-2 on the output from step-3.

## Video Tutorial

I started a YouTube channel where I go live on the weekends, and upload videos on the week days (not so regularly) about Computer Vision, deploying models into production and more. If you haven't seen it before, please check it out [here](https://youtube.com/c/kushashwaraviShrimali). For this blog, I have already uploaded a detailed tutorial. Check it out [here](https://www.youtube.com/watch?v=Nd3wFiSH-gw).

## Step 1: Detecting Faces using Haarcascade

We'll be using haarcascade model files to detect face in the image. To ease the computation and satisfy the input to the model, we need to first convert the image to GrayScale (if it's not already) - that is the image will now have only one channel instead of 3 (Blue, Green, Red). Download the model file to your directory from [here](https://github.com/opencv/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml). Let's go ahead and initialize our Face Detector.

```python
model_path = "haarcascade_frontalface_default.xml" # Assuming this is in our current directory
face_detector = cv2.CascadeClassifier(model_path)
```

Once we have the model loaded, let's go ahead and detect faces from the given image. Remember, that we will also convert the image to grayscale.

```python
# Read input image (get image path first from command line, else take sample.png - default)
img_path = self.argv[1] if len(sys.argv) > 1 else "sample.png"
img = cv2.imread(img_path, 1)

# Convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Get faces
# Use default arguments, scaleFactor can be tweaked depending on the image
# The output will be in format: [ [<top left x coord>, <top left y>, <width>, <height> : for face 1], [ ... : for face 2], ... ]
faces = face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
```

Once we have the faces, we can crop them and use in the Step-4 again. The output from face detection should look like this:

<img src="/assets/opencv/rect_sample_method1.jpeg" />

## Step 2: Crop faces

To crop them and store in another object:

```python
cropped_faces = []
for face in faces:
    # Get points: tlx (top left x), tly (top left y), w (width), h (height)
    tlx, tly, w, h = face[0], face[1], face[2], face[3]
    cropped_faces.append(
        face[tly:tly+h, tlx:tlx+w]
    )
```

The list `cropped_faces` will now contain only faces. We can use this list again in Step-4!

## Step 3 and Step 4: Blur the image and overlay faces

Let's blur the whole image, and then overlay the images on the top of it. To blur, we will be using Gaussian Blur which works just fine.

```python
blur = cv2.GaussianBlur(img, (11, 11)) # Here, (11, 11) is the kernel size
```

Once the whole image has been blurred, let's overlay the cropped faces from `Step 2`.

```python
for face_index, cropped_face in enumerate(cropped_faces):
    # Get face coordinates, to get ROI
    face_coords = faces[face_index]
    tlx, tly, w, h = face_coords[0], face_coords[1], face_coords[2], face_coords[3]

    # Overlay the ROI of face to the cropped face
    blur[tly:tly+h, tlx:tlx+w] = cropped_face
```

Following image explains the procedure in details with visualization.

<img src="/assets/opencv/procedure_method1.jpg" />

And this is how the output (on the right) will look like (see below).

<img src="/assets/opencv/output_method1.jpg" />

While I know many of you will be thinking that it's not accurate at all (since we can see the rectangle there), and that will be a topic for the next blog where we will attempt to crop a circle. Make sure to leave a comment if you have any suggestions, feedback or if this blog helped you in any way - I would love to hear that!
