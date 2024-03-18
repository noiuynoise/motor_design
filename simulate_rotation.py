import femm
import os
import json
from simulation import simulate_motor
from analysis import make_plots
import time
import argparse
import imageio
from motor_geometry.srm_design.srm_geometry import SrmGeometry
from typing import List, Dict

def GetMMFDict(run: int, steps: List[Dict[str, float]]) -> Dict[str, float]:
    if len(steps) == 0:
        return {}
    num_steps = steps[0]['steps']
    multiplier = run % num_steps
    mmf_dict = GetMMFDict(run // num_steps, steps[1:])
    for key in steps[0]['coils']:
        mmf_dict[key] = steps[0]['coils'][key] * multiplier
    return mmf_dict

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='motor tester')
    parser.add_argument('runner_number', type=int, help='runer number')
    args = parser.parse_args()
    run_stats = {}

    start = time.monotonic()

    config_file = 'run/simulation_config.json'
    config = None
    with open(config_file, 'r') as f:
        config = json.loads(f.read())
    if config is None:
        raise FileNotFoundError('no config file found')

    max_run = 1
    for driven_phase in config['driven_phases']:
        max_run *= driven_phase['steps']
    if args.runner_number >= max_run:
        raise ValueError('runner number exceeds maximum run number of: ' + str(max_run))


    mmf_dict = GetMMFDict(args.runner_number, config['driven_phases'])
    angle_step = config['angle_step']

    motor = SrmGeometry('run/geometry')
    start_time = time.monotonic()

    run_folder = f'run/run_{args.runner_number}'
    os.mkdir(run_folder)

    results = []
    femm.openfemm()
    for angle in range(0, int(motor.pole_pitch), angle_step):
        print(
            f'running angle {angle} at time {time.monotonic() - start_time}\n')
        image = run_folder + f'/image_{angle}.png'
        results.append(simulate_motor.simulate_motor(motor,
                                                     angle,
                                                     mmf_dict,
                                                     image_path=image,
                                                     temp_path=run_folder))
    femm.closefemm()
    images = []
    for i in range(0, len(results)):
        images.append(imageio.imread(run_folder + f'/image_{i * angle_step}.png'))
    imageio.mimsave(run_folder + '/rotation.gif', images, loop=0, duration=(2.0 / len(results)))
    with open(run_folder + '/results.json', 'w') as f:
        f.write(json.dumps(results, indent=4))

    end = time.monotonic()
    print(f'time elapsed: {end - start}\n')
    run_stats['time'] = end - start
    with open(run_folder + '/run.json', 'w') as f:
        f.write(json.dumps(run_stats, indent=4))
