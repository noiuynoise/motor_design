# pyFEMM docker container

This container runs pyFEMM in a container so you don't have to mess around with WINE to get everything running yourself.

Image is available here: https://hub.docker.com/repository/docker/noiuynoise/pyfemm/general

## Setup
To allow GUIs from docker containers to be shown during setup run the following command on the dev machine:
```
xhost +local:docker
```

## Building the container
Due to GUI elements, the container cannot be automatically built. To build the container, first build the base container:
```
docker build -t pyfemm_base .
```
Then run the container and install FEMM
```
docker run -it -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY --name pyfemm_install pyfemm_base wine /usr/share/femm_install.exe
```


Click 'install' on the wine mono installer, accept the terms for FEMM and install it to the default location. (uncheck the readme box) Once the installer has finished it will close out.

Then commit the container to a new image and delete the intermediate container:
```
docker commit pyfemm_install pyfemm
docker rm pyfemm_install
docker image rm pyfemm_base
```

To run FEMM run:
```
docker run -it --rm -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY pyfemm wine ~/.wine/drive_c/femm42/bin/femm.exe
```

To get a bash shell in the container run:
```
docker run -it --rm -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY pyfemm bash
```

It is probably possible to run the container headless after installing FEMM, but I haven't been able to get this working

To move the container to a new machine, use the following commands:
```
docker save -o pyfemm.tar pyfemm
scp pyfemm.tar andrew@andrew-cnc.local:~
rm pyfemm.tar
ssh andrew@andrew-cnc.local "docker load -i ~/pyfemm.tar && rm ~/pyfemm.tar"
```