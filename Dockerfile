FROM ultralytics/ultralytics:latest-jetson-jetpack4

RUN apt-get update && \
    apt-get install -y nano git && \
    pip3 install --no-cache-dir websockets imutils

RUN git clone https://github.com/InterplanetarCodebase/camera_new /workspace/repository

WORKDIR /workspace/repository

CMD ["/bin/bash"]
