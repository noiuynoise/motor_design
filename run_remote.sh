#!/bin/bash

folder_name=$(python3 utils/get_next_folder.py)
mkdir $folder_name
ssh andrew@andrew-CNC.local "rm -rf ~/motor_design/*"
rsync -az -e ssh $(dirname $0) andrew@andrew-CNC.local:~/motor_design --exclude='runs/*' --exclude='run/*' --exclude='complete_runs/*' --exclude='research/*'
echo "starting test_manager.py"
ssh andrew@andrew-CNC.local "nohup python3 -u ~/motor_design/test_manager.py $1 $2 $3"
rsync -az andrew@andrew-CNC.local:~/motor_design/run/* $folder_name/
