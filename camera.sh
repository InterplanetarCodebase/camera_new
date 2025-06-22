#!/bin/bash
export DISPLAY=${DISPLAY:-:0}
xhost +local:root
docker run -it \
    --gpus all \
    --runtime=nvidia \
    --privileged \
    --net=host \
    --name=camera \
    -e DISPLAY=$DISPLAY \
    -e QT_X11_NO_MITSHM=1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v /dev:/dev \
    -v /tmp:/tmp \ # important if using GStreamer Pi camera \
    -v /etc/enctune.conf:/etc/enctune.conf \
    -v /etc/nv_tegra_release:/etc/nv_tegra_release \
    -v /usr/lib/aarch64-linux-gnu/tegra:/usr/lib/aarch64-linux-gnu/tegra \
    -v /usr/lib/aarch64-linux-gnu/v4l2-utils:/usr/lib/aarch64-linux-gnu/v4l2-utils \
    -v /lib/modules:/lib/modules \
    ultralytics_image:latest # Apatoto ekta nam
