#!/bin/bash

folder_name=$(python3 utils/get_next_folder.py)
host_name="andrew@andrew-sim"
mkdir $folder_name
# if arg 2 is 0 then we are running a new test, so we need to clear the remote directory
if [ "$2" == "0" ]; then
  ssh $host_name "rm -rf ~/motor_design/*"
  rsync -az -e ssh $(dirname $0) $host_name:~/motor_design --exclude='runs/*' --exclude='run/*' --exclude='complete_runs/*' --exclude='research/*'
fi
echo "starting test_manager.py"
ssh $host_name "nohup python3 -u ~/motor_design/test_manager.py $1 $2 $3"
rsync -az $host_name:~/motor_design/run/* $folder_name/
