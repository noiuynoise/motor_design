#!/bin/python3
import matplotlib.pyplot as plt
import json
from argparse import ArgumentParser
from copy import deepcopy
from . import motor_specs

def plot_flux_linkage(results_dict, output_file, title = None):
    results = deepcopy(results_dict)
    plt.figure()
    x_axis = None
    if 'angle' in results[0]:
        plt.xlabel('Angle (degrees)')
        x_axis = [res['angle'] for res in results]
        x_axis += [res['angle'] + results[-1]['angle'] for res in results]
    else:
        plt.xlabel('Result number')
        x_axis = [x for x in range(len(results * 2))]
    
    for idx in range(len(results), 0, -1):
        if type(results[idx-1]['a']) == list or type(results[idx-1]['b']) == list or type(results[idx-1]['c']) == list:
            results.pop(idx-1)
            x_axis.pop(idx-1)
    
    for phase in ['a', 'b', 'c']:
        plt.plot(
            x_axis,
            [res[phase]['flux'] for res in results] * 2
        )
    if title:
        plt.title(title)
    plt.ylabel('flux linkage (H)')
    plt.savefig(output_file)

def plot_torque(results_dict, output_file, title = None):
    results = deepcopy(results_dict)
    plt.figure()
    x_axis = None
    if 'angle' in results[0]:
        plt.xlabel('Angle (degrees)')
        x_axis = [res['angle'] for res in results]
    else:
        plt.xlabel('Result number')
        x_axis = [x for x in range(len(results))]
    
    for idx in range(len(results), 0, -1):
        if type(results[idx-1]['torque']) == list:
            results.pop(idx-1)
            x_axis.pop(idx-1)
    x_axis += [x_axis[-1] + x for x in x_axis]

    torques = [res['torque'] for res in results] * 2

    for i in range(3):
        plt.plot(
            x_axis,
            torques[int(len(results) * i / 3):] + torques[:int(len(results) * i / 3)],
            label=f'Phase {["a", "b", "c"][i]}'
        )
    if title:
        plt.title(title)
    plt.legend()
    plt.ylabel('Torque (N.m)')
    plt.savefig(output_file)

def plot_max_torque(results_dict, output_file, title = None):
    results = deepcopy(results_dict)
    plt.figure()
    x_axis = None
    if 'angle' in results[0]:
        plt.xlabel('Angle (degrees)')
        x_axis = [res['angle'] for res in results]
    else:
        plt.xlabel('Result number')
        x_axis = [x for x in range(len(results))]
    
    for idx in range(len(results), 0, -1):
        if type(results[idx-1]['torque']) == list:
            results.pop(idx-1)
            x_axis.pop(idx-1)
    x_axis += [x_axis[-1] + x for x in x_axis]

    plt.plot(
        x_axis,
        motor_specs.GetDrivenTorque(results, len(results) / 3, 3) * 2
    )
    if title:
        plt.title(title)
    plt.ylabel('Torque (N.m)')
    plt.savefig(output_file)

if __name__ == "__main__":
    parser = ArgumentParser(prog='result_plotter')
    parser.add_argument('file', type=str, help='simulation results file')
    args = parser.parse_args()
    results = None
    with open(args.file, 'r') as f:
        results = json.loads(f.read())
    # plot_flux_linkage(results, "flux.png")
    # plot_torque(results, "torque.png")
    plot_max_torque(results, "max_torque.png")

    