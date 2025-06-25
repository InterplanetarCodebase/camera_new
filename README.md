# Camera Workspace for Jetson
This workspace contains necessary files to develop the object detection and video streaming functiinalities on the Jetson. README sections for each file is given below

## test_camera.py

This script streams raw video frames from a camera over a WebSocket connection for testing purposes.  
It does **not** perform any detection or annotation—just sends the camera feed as JPEG images.

### Usage

```sh
python test_camera.py <camera_index> <port>
```

- `<camera_index>`: Index of the camera to use (e.g., `0` for the default webcam).
- `<port>`: Port number to run the WebSocket server on.

**Example:**
```sh
python test_camera.py 0 8765
```

### Notes

- The server waits for at least one client to connect before it starts sending frames.
- This script is intended for **testing camera streaming and client connectivity**.
- No object detection or processing is performed—frames are sent as-is.
- Make sure `config.py` exists and contains the

## sticher.py

This script captures a series of images from a webcam, stitches them into a panorama, and optionally streams the final stitched image to a connected WebSocket client. It’s useful for generating panoramic views using multiple overlapping frames.

### Usage

```sh
python sticher.py <camera_index> <port>
```

- `<camera_index>`: Index of the camera to use (e.g., `0` for the default webcam).
- `<port>`: Port number to run the WebSocket server on.

**Example:**
```sh
python test_camera.py 0 8765
```

### Workflow

- Starts a WebSocket server on port 8765.
- Waits for a WebSocket client to connect.
- Captures 3 images from the webcam (5 seconds apart by default).
- Stitches the images together into a panorama.
- Crops and saves the result as stitched_image.jpg.
- Sends the image to the connected client in base64 format.


### Workflow

- The number of images and delay can be adjusted in the script via:
    NUM_IMAGES_TO_CAPTURE
    CAPTURE_DELAY
- Output is saved to:
    Folder: unstitched/ (raw images)
    File: stitched_image.jpg (final output)
- The script requires a display for image preview (cv2.imshow()).
- WebSocket clients must connect before the image capture begins.
- If stitching fails, the server will send a "STITCHING_FAILED" message.

### ⚠️ Caution

- The camera must remain steady during the entire capture process. Avoid shaking or repositioning it.
- Each captured image should have at least ~50% overlap with the previous one to ensure reliable stitching.
- Poor lighting, motion blur, or lack of shared features between frames can cause stitching to fail.

## client.py

`client.py` is a Python script for receiving and displaying a live video stream over a WebSocket connection. It connects to a video server, receives base64-encoded video frames, decodes them, and displays them in real time using OpenCV.

### Usage

```sh
python client.py <PORT>
```

- `<PORT>`: The port number where the WebSocket server is running.  
- The server IP address should be set in `config.IP`.

**Example:**
```sh
python client.py 8765
```

## config.py

The `config.py` file stores configuration settings for the video client and server scripts.

### Usage

This file should define the IP address of the server as a string variable named `IP`.  
Other scripts (such as `client.py`) will import this file to determine which server to connect to.

### Example

```python
IP = "localhost"
```

You can change `"localhost"` to any valid IP address or hostname where your WebSocket server is running, for example:

```python
IP = "192.168.1.100"
```

### Notes

- Make sure `config.py` is in the same directory as your client and server scripts.
- Only the `IP`

## stream.py

This script streams live video frames from a camera over a WebSocket connection.  
It is similar to `test_camera.py` but is intended for general-purpose video streaming (no detection or annotation).

### Usage

```sh
python stream.py <camera_index> <port>
```

- `<camera_index>`: Index of the camera to use (e.g., `0` for the default webcam).
- `<port>`: Port number to run the WebSocket server on.

**Example:**
```sh
python stream.py 0 8765
```

### Notes

- The server waits for at least one client to connect before it starts sending frames.
- Frames are sent as JPEG images, resized to 640x480.
- Make sure `config.py` exists and contains the `IP` variable.
- No object detection or processing is performed—frames are sent as-is.

## detect.py

`detect.py` runs a YOLO-based object detection server that streams annotated video frames over WebSocket. Model: Yolov5nu

### Usage

```sh
python detect.py <camera_index> <port>
```

- `<camera_index>`: Index of the camera to use (e.g., `0` for default webcam).
- `<port>`: Port number to run the WebSocket server on.

**Example:**
```sh
python detect.py 0 8765
```

### Notes

- The server waits for at least one client to connect before it starts sending video frames.
- Frames are annotated with YOLO detections and streamed to connected clients

 ## main.py

This script allows you to launch and manage multiple Python scripts as separate processes, each with its own arguments and a custom process name. It is useful for starting several components of a system (such as servers, clients, or workers) and managing their lifecycles together.

> **Note:**  
> The current implementation uses Unix-specific features (`os.setsid`, `exec -a`, and `bash`).  
> It will **not work on Windows** without modification.

### Usage

```sh
python main.py <script1.py> <arg1> ... <proc_name1> [<script2.py> <arg2> ... <proc_name2> ...]
```

- Each set consists of a script, its arguments, and a process name (used for identification).
- You can specify multiple sets in one command.

### Example

To run two scripts:
- `detect.py` with arguments `0 8765` as process name `detector`
- `client.py` with argument `8765` as process name `client`

```sh
python main.py detect.py 0 8765 detector stream.py 1 8766 streamer
```

This will:
- Start `detect.py 0 8765` as a process named `detector`
- Start `client.py 8765` as a process named `client`

### Features

- **Custom process names:** Makes it easier to identify processes in system tools.
- **Graceful shutdown:** Pressing `Ctrl+C` will send a signal to terminate all child processes.
- **Flexible argument grouping:** Each script and its arguments are grouped by the process name.

### Limitations

- **Unix/Linux only:** Uses `bash`, `exec -a`, and `os.setsid`.
- **Not compatible with Windows** as written.

### Example Process Layout

| Script      | Arguments | Process Name |
|-------------|-----------|--------------|
| detect.py   | 0 8765    | detector     |
| stream.py   | 1 8766    | streamer     |

You can extend this pattern to launch as many scripts as needed, each with its own arguments and process name.

## camera.sh

This script runs a Docker container with GPU and camera access, suitable for running video streaming or detection applications (such as those using Ultralytics/YOLO) on a Linux system with NVIDIA GPU support.

### Usage

```sh
sudo ./camera.sh
```

### What it does

- Sets up X11 display forwarding for GUI applications inside the container.
- Grants the container access to all GPUs (`--gpus all` and `--runtime=nvidia`).
- Runs the container in privileged mode with host networking.
- Mounts necessary device, configuration, and X11 files/directories for camera and display access.
- Starts a container named `camera` from the `ultralytics_image:latest` image.

### Requirements

- Docker with NVIDIA GPU support (`nvidia-docker2` or Docker 19.03+ with `--gpus` flag).
- X11 server running on the host (for GUI/video display).
- The `ultralytics_image:latest` Docker image built and available locally.
- Linux host with NVIDIA drivers and camera devices.

### Notes

- The script uses `xhost +local:root` to allow the container to access the X server.
- Mounting /tmp is necessary for GStreamer Pipeline.
- The container will have access to all host devices and modules for maximum compatibility with cameras and GPUs.
- You may need to adjust volume mounts or environment variables for your specific hardware or application.
- The image name `ultralytics_image:latest` is a placeholder—replace it with your actual image name if different.
