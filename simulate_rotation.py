import femm
import os
import json
from simulation import simulate_motor
from analysis import make_plots
from copy import copy
import time
import argparse
from utils.motor_config_helper import MotorConfig


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='motor tester')
    parser.add_argument('runner_number', type=int, help='runer number')
    args = parser.parse_args()
    run_stats = {}

    start = time.monotonic()

    run_folder = f'runs/run_{args.runner_number}'
    os.mkdir(run_folder)

    sim_info = None
    with open('run/geometry/sim_info.json', 'r') as f:
        sim_info = json.loads(f.read())
    femm.openfemm()
    results = []
    # this is in AMP TURNS. Make sure to account for number of turns for sim maximum / step
    a_current = int(args.runner_number)
    b_current = 0
    start_time = time.monotonic()
    for angle in range(0, int(sim_info["pole_pitch"]), 1):
        print(
            f'running angle {angle} at time {time.monotonic() - start_time}\n')
        image = None
        if angle % 10 == 0:
            image = run_folder + f'/image_{angle}.png'
        results.append(simulate_motor.simulate_motor('run/geometry/motor.FEM',
                                                     sim_info["rotate_diameter"] / 2,
                                                     angle,
                                                     a_current, b_current, 0,
                                                     image_path=image,
                                                     temp_path=run_folder))
    femm.closefemm()
    with open(run_folder + '/results.json', 'w') as f:
        f.write(json.dumps(results, indent=4))
    make_plots.plot_flux_linkage(results, run_folder + '/flux.png')
    make_plots.plot_torque(results, run_folder + '/torque.png')

    end = time.monotonic()
    print(f'time elapsed: {end - start}\n')
    run_stats['time'] = end - start
    with open(run_folder + '/run.json', 'w') as f:
        f.write(json.dumps(run_stats, indent=4))
