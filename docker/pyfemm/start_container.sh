#!/bin/bash

docker run -it --name pyfemm -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY -v $(dirname "$0")/../..:/code pyfemm sleep infinity
