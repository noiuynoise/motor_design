import os
import argparse
import json
import subprocess
import time
import string
import random



def get_containers():
    containers_proc = subprocess.Popen(['docker', 'ps', '-a', '--format', '{{json .}}'], stdout=subprocess.PIPE)
    jq_proc = subprocess.Popen(['jq', '--tab', '-s', '.'], stdin=containers_proc.stdout, stdout=subprocess.PIPE)
    jq_proc.wait()
    return json.loads(jq_proc.communicate()[0].decode('utf-8'))

def get_running_containers(id = None):
    containers = get_containers()
    num_running = 0
    for container in containers:
        if container['State'] == 'running': 
            if id is None or container['Names'][:len(id)] == id:
                num_running += 1
    return num_running
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='run manager')
    parser.add_argument('command', type=str, help='command to run in container (with number argument appended)')
    parser.add_argument('num_runners', type=int, help='number of runners to start')
    parser.add_argument('run_start', type=int, help='start index for runners')
    parser.add_argument('run_end', type=int, help='end index for runners')
    args = parser.parse_args()

    id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    os.system(f'cp {__file__} {os.path.dirname(os.path.realpath(__file__))}/runs/manager.py')

    for i in range(args.run_start, args.run_end + 1, 1):
        while (get_running_containers(id) >= args.num_runners):
            # print(f'waiting for runners to complete\n')
            time.sleep(5)
        print(f'starting runner {i}\n')
        command = ['docker', 'run', '-d', '--rm', '--name', f'{id}_{i}',
                          '-v', '/tmp/.X11-unix:/tmp/.X11-unix',
                          '-e', 'DISPLAY=:0', '-v', f'{os.path.dirname(os.path.realpath(__file__))}:/code',
                          'pyfemm'] + args.command.split(" ") + [str(i)]
        subprocess.Popen(command, stdout=subprocess.PIPE)
        time.sleep(10)
    
    # wait for all containers to stop
    while (get_running_containers(id) > 0):
        time.sleep(5)
    print('all runners complete\n')

    # containers_proc = subprocess.Popen(['docker', 'ps', '-a', '--format', '{{json .}}'], stdout=subprocess.PIPE)
    # jq_proc = subprocess.Popen(['jq', '--tab', '-s', '.'], stdin=containers_proc.stdout, stdout=subprocess.PIPE)
    # jq_proc.wait()
    # containers = json.loads(jq_proc.communicate()[0].decode('utf-8'))

    # available_container_numbers = []
    # last_container_number = -1
    # prefix = 'pyfemm_runner_'
    # for container in containers:
    #     if container['Names'][:len(prefix)] == prefix:
    #         last_container_number = max(last_container_number, int(container['Names'][len(prefix):]))
    #         if container['State'] != 'running':
    #             available_container_numbers.append(int(container['Names'][len(prefix):]))

    # # if len(available_container_numbers) < args.num_runners:
    # #     if last_container_number is None:
    
    # print(available_container_numbers)