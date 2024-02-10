#!/bin/bash

folder_name=$(python3 misc/get_next_folder.py)
mkdir $folder_name
ssh andrew@andrew-CNC.local "rm -rf ~/motor_design/*"
rsync -az -e ssh $(dirname $0) andrew@andrew-CNC.local:~/motor_design --exclude='runs/*' --exclude='research/*'
ssh andrew@andrew-CNC.local "docker exec pyfemm $1"
rsync -az andrew@andrew-CNC.local:~/motor_design/runs/run_1/* $folder_name/
