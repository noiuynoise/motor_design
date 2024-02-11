#!/bin/python3

import femm
import simulate_motor
import matplotlib.pyplot as plt
import matplotlib
import json
import datetime

ANGLE_STEP = 1
A_CURRENT = 10
ROTOR_RADIUS = 6.1
FILE = 'srm.FEM'

if __name__ == "__main__":
    # femm.openfemm()
    # results = []
    # for angle in range(0, 90, ANGLE_STEP):
    #     print(f'simulating at {angle} degrees')
    #     results.append(simulate_motor.simulate_motor(FILE, ROTOR_RADIUS, angle, A_CURRENT, 0, 0))
    # femm.closefemm()

    # now = datetime.datetime.now()
    # with open(f'{FILE}-s{ANGLE_STEP}-i{A_CURRENT}-{now.strftime("%Y%m%d%H%M%S")}.json', 'w') as f:
    #     f.write(json.dumps(results, indent=4))

    # results = None
    # with open('srm.FEM-s1-i10-20240206065128.json', 'r') as f:
    #     results = json.loads(f.read())

    # plt.plot([i for i in range(0, 90, ANGLE_STEP)], [result['A']['flux'] / result['A']['current'] for result in results], 'b-')
    # plt.xlabel('Angle (degrees)')
    # plt.ylabel('flux linkage (H)')
    # plt.savefig('flux.png')

    # plt.plot([i for i in range(0, 90, ANGLE_STEP)], [result['torque'] for result in results], 'b-')
    # plt.xlabel('Angle (degrees)')
    # plt.ylabel('torque (N.m)')
    # plt.savefig('torque.png')
