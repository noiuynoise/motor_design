import os
import argparse
import json
import subprocess
import time
import string
import random


def get_containers():
    containers_proc = subprocess.Popen(
        ['docker', 'ps', '-a', '--format', '{{json .}}'], stdout=subprocess.PIPE)
    jq_proc = subprocess.Popen(
        ['jq', '--tab', '-s', '.'], stdin=containers_proc.stdout, stdout=subprocess.PIPE)
    jq_proc.wait()
    return json.loads(jq_proc.communicate()[0].decode('utf-8'))


def get_running_containers(id=None):
    containers = get_containers()
    num_running = 0
    for container in containers:
        if container['State'] == 'running':
            if id is None or container['Names'][:len(id)] == id:
                num_running += 1
    return num_running


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='run manager')
    parser.add_argument('num_runners', type=int,
                        help='number of runners to start')
    parser.add_argument('run_start', type=int, help='start index for runners')
    parser.add_argument('run_end', type=int, help='end index for runners')
    args = parser.parse_args()
    id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    start_time = time.monotonic()

    repo_path = os.path.dirname(os.path.realpath(__file__))
    code_path = f'{repo_path}/run/code'

    if args.run_start == 0:
        os.mkdir(f'{repo_path}/run/code')
        os.system(
            f'cp {__file__} {code_path}/manager.py')
        os.system(
            f'cp {repo_path}/simulate_rotation.py {code_path}/simulate_rotation.py')
        os.system(
            f'cp {repo_path}/generate_motor.py {code_path}/generate_motor.py')
        os.system(
            f'cp {repo_path}/simulation_config.json {repo_path}/run/simulation_config.json')

        print(f'generating motor geometry')
        command = ['docker', 'run', '--rm', '--init', '--name', f'{id}_geometry',
                   '-v', f'{repo_path}:/code', '--env', 'SIM_RUNNER=1',
                   'pyfemm', 'xvfb-run', 'python3', '/code/generate_motor.py']
        subprocess.Popen(command).wait()

    print(
        f'starting {args.num_runners} runners. Start: {args.run_start} End: {args.run_end}')
    for i in range(args.run_start, args.run_end + 1, 1).reverse():
        while (get_running_containers(id) >= args.num_runners):
            runs_complete = max(
                0, i - get_running_containers(id) - args.run_start)
            time_elapsed = time.monotonic() - start_time
            time_remaining = "unknown"
            if runs_complete > 0:
                time_remaining = time_elapsed / runs_complete * \
                    (args.run_end - i + args.num_runners)
                time_remaining = f'{int(time_remaining / 3600)}h {int(time_remaining / 60) % 60}m {int(time_remaining) % 60}s'
            print(f'{runs_complete} runs complete out of {args.run_end - args.run_start}. {int(time_elapsed)}s elapsed. Estimated completion in: {time_remaining}                     ', end='\r')
            time.sleep(5)
        command = ['docker', 'run', '-d', '--rm', '--init', '--name', f'{id}_{i}',
                   '-v', f'{os.path.dirname(os.path.realpath(__file__))}:/code', '--env', 'SIM_RUNNER=1',
                   'pyfemm', 'xvfb-run', 'python3', '-u', 'simulate_rotation.py'] + [str(i)] # + ['>', f'run/run_{str(i)}.log']
        try:
            subprocess.Popen(command, stdout=subprocess.PIPE).wait(timeout=10)
        except subprocess.TimeoutExpired:
            print(f'runner {i} failed to start')
        time.sleep(1)
    print('\nwaiting for runners to complete')

    # wait for all containers to stop
    while (get_running_containers(id) > 0):
        time.sleep(5)
    print(f'all runners complete in {time.monotonic() - start_time}s')
