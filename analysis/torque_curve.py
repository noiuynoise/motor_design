#!/bin/python3
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os
import json
from scipy.interpolate import RegularGridInterpolator
from typing import Tuple
import math

class SimulationResults:
    def __init__(self, loc: str, params, a_step, b_step, angle_step, turns):
        # flux is flux LINKAGE of coil
        self.results = {}
        self.a_step = a_step
        self.b_step = b_step
        self.angle_step = angle_step
        self.turns = turns
        self.params = params

        self.current_limit = 10
        self.bus_voltage = 6
        self.coil_resistance = 0.1

        for file in os.listdir(loc):
            ext = '_ordered.npy'
            if file[-len(ext):] == ext:
                self.results[file[:-len(ext)]] = np.load(loc + '/' + file)

        self.interpolators = {}
        shape = list(self.results.values())[0].shape
        self.a_max = shape[0] * self.a_step
        self.b_max = shape[1] * self.b_step
        self.angle_max = shape[2] * self.angle_step
        a_arr = np.linspace(0, self.a_max, shape[0])
        b_arr = np.linspace(0, self.b_max, shape[1])
        angle_arr = np.linspace(0, self.angle_max, shape[2])
        for result in self.results.keys():
            self.interpolators[result] = RegularGridInterpolator((a_arr, b_arr, angle_arr), self.results[result], bounds_error=False, fill_value=None)
        
        if self.current_limit > self.a_max and self.current_limit > self.b_max:
            print(f'error: current limit {self.current_limit} is greater than data range! Results will be inaccurate')
    
    def InterpolatePoint(self, a_current, b_current, angle, ax_out) -> float:
        interp = self.interpolators[ax_out]
        return float(interp([a_current, b_current, angle]))

    def InterpolateDerivative(self, a_current, b_current, angle, ax_out) -> Tuple[float, float, float]:
        a_start = self.InterpolatePoint(a_current - self.a_step / 2, b_current, angle, ax_out)
        a_end = self.InterpolatePoint(a_current + self.a_step / 2, b_current, angle, ax_out)
        a_slope = (a_end - a_start) / self.a_step

        b_start = self.InterpolatePoint(a_current, b_current - self.b_step / 2, angle, ax_out)
        b_end = self.InterpolatePoint(a_current, b_current + self.b_step / 2, angle, ax_out)
        b_slope = (b_end - b_start) / self.b_step

        angle_start = self.InterpolatePoint(a_current, b_current, angle - self.angle_step / 2, ax_out)
        angle_end = self.InterpolatePoint(a_current, b_current, angle + self.angle_step / 2, ax_out)
        angle_slope = (angle_end - angle_start) / self.angle_step
        return (a_slope, b_slope, angle_slope)

    # speed in RPM. CCW only (B is leading A)
    def GetEmf(self, a_current, a_didt, b_current, b_didt, angle, speed) -> float:
        speed_deg_s = speed * 360 / 60
        slope = self.InterpolateDerivative(a_current, b_current, angle, 'a_flux')
        return float(self.turns * (a_didt * slope[0] + b_didt * slope[1] + speed_deg_s * slope[2]))

    def FindMaxTorquePoint(self, speed, angle) -> float:
        VOLTAGE_TOLERANCE = 1e-8
        MAX_STEPS = 12
        current = self.current_limit if self.InterpolatePoint(self.current_limit, 0, angle, 'torque') > 0 else -self.current_limit
        coil_voltage = current * self.coil_resistance + self.GetEmf(current, 0, 0, 0, angle, speed)
        # check for CC region
        if coil_voltage < self.bus_voltage:
            return abs(self.InterpolatePoint(abs(current), 0, angle, 'torque'))
        for i in range(MAX_STEPS):
            # approximate with voltage ~ current
            current = current * (self.bus_voltage / coil_voltage)
            coil_voltage = current * self.coil_resistance + math.copysign(self.GetEmf(abs(current), 0, 0, 0, angle, speed), current)
            if abs(coil_voltage - self.bus_voltage) < VOLTAGE_TOLERANCE:
                return abs(self.InterpolatePoint(abs(current), 0, angle, 'torque'))
        print(f'error: max torque point not found after {MAX_STEPS} steps. Residual error: {coil_voltage - self.bus_voltage} V')
        return abs(self.InterpolatePoint(abs(current), 0, angle, 'torque'))

    # speed in RPM
    def GetRmsTorque(self, speed) -> float:
        phase_torques = [self.FindMaxTorquePoint(speed, x) for x in range(0, self.angle_max, self.angle_step)]
        output = []
        for angle in range(0, self.angle_max, self.angle_step):
            pole_pitch = 360 / self.params['stator']['slots']
            output.append(max(phase_torques[int(angle / self.angle_step)],
                              phase_torques[int(((angle + pole_pitch) % self.angle_max) / self.angle_step)],
                              phase_torques[int(((angle + pole_pitch * 2) % self.angle_max) / self.angle_step)]))
        # take the RMS
        output = [x ** 2 for x in output]
        return (sum(output) / len(output)) ** 0.5

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='3d plot')
    parser.add_argument('data_folder', type=str, help='location of data folder')
    args = parser.parse_args()

    # load data
    motor_params = None
    if os.path.isfile(args.data_folder + '/motor_params.json'):
        motor_params = json.load(open(args.data_folder + '/motor_params.json', 'r'))
    else:
        for folder in os.listdir(args.data_folder):
            if not os.path.isdir(args.data_folder + '/' + folder):
                continue
            if os.path.isfile(args.data_folder  + '/' + folder + '/motor_params.json'):
                motor_params = json.load(open(args.data_folder  + '/' + folder + '/motor_params.json', 'r'))
                break
    if motor_params is None:
        print(f'error: no motor_params.json found in {args.data_folder} or subfolders')
        exit(1)
    
    if not os.path.isdir(args.data_folder + '/combined'):
        print(f'error: no combined folder found in {args.data_folder}')
        exit(1)

    results = SimulationResults(args.data_folder + '/combined', motor_params,0.5, 0.5, 1, 10)

    plt.figure()
    plt.xlabel('speed (RPM)')
    plt.plot([x for x in range(0, 10000, 30)], [results.GetRmsTorque(x) for x in range(0, 10000, 30)])
    #plt.plot([x for x in range(90)], [results.GetEmf(10, 0, 0, 0, x, 1000) for x in range(90)])
    plt.ylabel('Torque (N.m)')
    plt.show()





        
