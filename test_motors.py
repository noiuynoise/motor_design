import femm
import os
import json
import motor_test.simulate_motor
import srm_design.generate_motor
import analysis.make_plots
from copy import copy
import time


if __name__ == "__main__":

    run_stats = {}

    start = time.monotonic()
    filepath = 'initial_config.json'
    if not os.path.isfile(filepath):
        raise ValueError('config not found')
    config_json = open(filepath, 'r')
    config = json.loads(config_json.read())

    # find which run folder to use
    folders = os.listdir('runs')
    last_run = 0
    for folder in folders:
        if folder[:4] == 'run_':
            last_run = max(last_run, int(folder[4:]))
    run_folder = f'runs/run_{last_run + 1}'
    os.mkdir(run_folder)
    os.system(f'cp {__file__} {run_folder}/run.py')
    os.system(f'cp initial_config.json {run_folder}/initial_config.json')

    # for now test tooth widths 2 - 4

    for i in range(6, 8):
        for j in [0]:
            femm.openfemm()
            width = i / 2
            test_folder = run_folder + f'/test_i_{width}_j_{j}'
            os.mkdir(test_folder)
            test_config = copy(config)
            config['stator']['tooth_tip_width'] = width
            config['stator']['tooth_root_width'] = width
            config['stator']['spine_width'] = width / 2 + j
            config['rotor']['pole_tip_width'] = width
            config['rotor']['pole_root_width'] = width
            config['rotor']['rib_width'] = width / 2 + j
            with open(test_folder + '/motor_params.json', 'w') as f:
                f.write(json.dumps(config, indent=4))
            motor_params = srm_design.generate_motor.generate_motor(config, test_folder + '/srm.FEM')
            results = []
            for angle in range(0, int(360 / config['rotor']['poles']), 1):
                image = None
                if angle % 10 == 0:
                    print(f'simulating parameter {width} at {angle} degrees')
                    image = test_folder + f'/image_{angle}.png'
                results.append(motor_test.simulate_motor.simulate_motor(test_folder + '/srm.FEM', motor_params['rotor_od'] / 2, angle, 10, 0, 0, image))
            femm.closefemm()
            with open(test_folder + '/results.json', 'w') as f:
                f.write(json.dumps(results, indent=4))
            analysis.make_plots.plot_flux_linkage(results, test_folder + '/flux.png')
            analysis.make_plots.plot_torque(results, test_folder + '/torque.png')
            analysis.make_plots.plot_max_torque(results, test_folder + '/max_torque.png')
    end = time.monotonic()
    print(f'time elapsed: {end - start}\n')
    run_stats['time'] = end - start
    with open(test_folder + '/run.json', 'w') as f:
        f.write(json.dumps(run_stats, indent=4))
