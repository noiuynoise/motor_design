import numpy as np
import os
import json
from scipy.interpolate import RegularGridInterpolator
from typing import Tuple
from utils.motor_config_helper import MotorConfig

class SimulationResults:
    def __init__(self, sim_results_loc: str, inverter_loc: str, config: MotorConfig):
        with open(sim_results_loc + '/step.json', 'r') as f:
            self.step = json.loads(f.read())
        
        self.results = {}
        self.a_step = self.step['a_step']
        self.b_step = self.step['b_step']
        self.angle_step = self.step['angle_step']
        self.config = config

        self.current_limit = 30
        self.bus_voltage = 24

        for file in os.listdir(sim_results_loc):
            ext = '_ordered.npy'
            if file[-len(ext):] == ext:
                self.results[file[:-len(ext)]] = np.load(sim_results_loc + '/' + file)

        self.interpolators = {}
        shape = list(self.results.values())[0].shape
        self.a_max = self.step['a_max']
        self.a_min = self.step['a_min']
        self.b_max = self.step['b_max']
        self.b_min = self.step['b_min']
        self.angle_max = self.step['angle_max']
        self.angle_min = self.step['angle_min']
        a_arr = np.linspace(self.a_min, self.a_max, shape[0])
        b_arr = np.linspace(self.b_min, self.b_max, shape[1])
        angle_arr = np.linspace(0, self.angle_max, shape[2])
        for result in self.results.keys():
            if self.b_min != self.b_max:
                self.interpolators[result] = RegularGridInterpolator((a_arr, b_arr, angle_arr), self.results[result], bounds_error=False, fill_value=None)
            else:
                self.interpolators[result] = RegularGridInterpolator((a_arr, angle_arr), self.results[result][:,0,:], bounds_error=False, fill_value=None)
        
        if self.current_limit > self.a_max and self.current_limit > self.b_max:
            print(f'error: current limit {self.current_limit} is greater than data range! Results will be inaccurate')
        
        print(f'loaded {shape} data points')
    
    def InterpolatePoint(self, a_current, b_current, angle, ax_out) -> float:
        interp = self.interpolators[ax_out]
        if self.b_min != self.b_max:
            return float(interp([a_current, b_current, angle]))
        else:
            return float(interp([a_current, angle]))

    def InterpolateDerivative(self, a_current, b_current, angle, ax_out) -> Tuple[float, float, float]:
        a_start = self.InterpolatePoint(a_current - self.a_step / 2, b_current, angle, ax_out)
        a_end = self.InterpolatePoint(a_current + self.a_step / 2, b_current, angle, ax_out)
        a_slope = (a_end - a_start) / self.a_step

        b_slope = 0
        if self.b_min != self.b_max:
            b_start = self.InterpolatePoint(a_current, b_current - self.b_step / 2, angle, ax_out)
            b_end = self.InterpolatePoint(a_current, b_current + self.b_step / 2, angle, ax_out)
            b_slope = (b_end - b_start) / self.b_step

        angle_start = self.InterpolatePoint(a_current, b_current, angle - self.angle_step / 2, ax_out)
        angle_end = self.InterpolatePoint(a_current, b_current, angle + self.angle_step / 2, ax_out)
        angle_slope = (angle_end - angle_start) / self.angle_step
        return (a_slope, b_slope, angle_slope)

    # speed in RPM. CCW only (B is leading A)
    def GetCoilEmf(self, a_current, a_didt, b_current, b_didt, angle, speed) -> float:
        # flux is total flux of coil.
        speed_deg_s = speed * 360 / 60
        slope = self.InterpolateDerivative(a_current, b_current, angle, 'a_flux')
        #print(f'angle: {angle}, slope: {slope}')
        return float(self.config['winding']['turns'] * (a_didt * slope[0] + b_didt * slope[1] + speed_deg_s * slope[2]))
    
    def GetEmf(self, a_current, a_didt, b_current, b_didt, angle, speed) -> float:
        if self.config.termination_type == 'parallel':
            return self.GetCoilEmf(a_current, a_didt, b_current, b_didt, angle, speed)
        else:
            return self.GetCoilEmf(a_current, a_didt, b_current, b_didt, angle, speed) * self.config.coils_per_phase