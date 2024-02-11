#!/bin/bash

folder_name=$(python3 utils/get_next_folder.py)
mkdir $folder_name
ssh andrew@andrew-CNC.local "rm -rf ~/motor_design/*"
rsync -az -e ssh $(dirname $0) andrew@andrew-CNC.local:~/motor_design --exclude='runs/*' --exclude='research/*'
ssh andrew@andrew-CNC.local "python3 ~/motor_design/test_manager.py \"$1\" $2 $3 $4"
rsync -az andrew@andrew-CNC.local:~/motor_design/runs/* $folder_name/
