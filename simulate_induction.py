import femm
import os
import json
from simulation import simulate_induction_motor
import time
import argparse
import imageio
from motor_geometry.interface.motor_geometry_factory import MakeGeometry
from typing import List, Dict

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


    mmf_dict = {}
    for key, value in config['currents'].items():
        mmf_dict[key] = value['re'] + 1j * value['im']
    femm.openfemm()

    motor = MakeGeometry('run/geometry')
    motor.GenerateGeometry()
    start_time = time.monotonic()

    mmf_dict = motor.GetCurrentForDissipation(config['power_dissipation'])

    run_folder = f'run/run_{args.runner_number}'
    os.mkdir(run_folder)
    os.system(f'cp {config_file} {run_folder}/simulation_config.json')
    os.system(f'cp run/geometry/motor_config.json {run_folder}/motor_config.json')
    out = {}
    out['rotor_weight'] = motor.GetRotorWeight()
    out['stator_length'] = motor.config['pcb']['trace_pitch'] * motor.config['pcb']['num_traces']
    results = []
    last_time = start_time
    num_steps = int((config['end_frequency_exp'] - config['start_frequency_exp']) * config['runs_per_decade'])
    for idx in range(0, num_steps, 1):
        frequency = 10 ** (config['start_frequency_exp'] + idx / config['runs_per_decade'])
        image = run_folder + f'/image_{idx}.png'
        results.append(simulate_induction_motor.simulate_induction_motor(motor,
                                                     frequency,
                                                     mmf_dict,
                                                     image_path=image,
                                                     temp_path=run_folder))
        print(
            f'ran frequency {frequency:.2f} in  {time.monotonic() - last_time:.2f}s\n')
        last_time = time.monotonic()
    femm.closefemm()
    images = []
    for i in range(0, len(results)):
        images.append(imageio.imread(run_folder + f'/image_{i}.png'))
    imageio.mimsave(run_folder + '/rotation.gif', images, loop=0, duration=(2.0 / len(results)))
    out['data'] = results
    with open(run_folder + '/results.json', 'w') as f:
        f.write(json.dumps(out, indent=1))

    end = time.monotonic()
    print(f'time elapsed: {end - start}\n')
    run_stats['time'] = end - start
    with open(run_folder + '/run.json', 'w') as f:
        f.write(json.dumps(run_stats, indent=1))
