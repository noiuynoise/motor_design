
from typing import Dict, List, Any
import os
import json
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from motor_geometry.interface.motor_geometry_factory import MakeGeometry

def FlattenDict(entry: Dict[str, any]) -> Dict[str, float]:
    result_names = {}
    for key, value in entry.items():
        if isinstance(value, dict):
            for key2, value2 in FlattenDict(value).items():
                result_names[key + '_' + key2] = value2
        else:
            result_names[key] = value
    return result_names


def test_FlattenDict():
    # pytest is good
    test_dict = {'a': 1, 'b': {'c': 2, 'd': 3}}
    assert FlattenDict(test_dict) == {'a': 1, 'b_c': 2, 'b_d': 3}


class SimulationResults:
    GEOMETRY_FOLDER = '/geometry'
    COMBINED_FOLDER = '/combined'
    SIMULATION_INFO_FILE = COMBINED_FOLDER + '/simulation_info.json'
    SIMULATION_CONFIG_FILE = '/simulation_config.json'

    def __init__(self, results_folder: str):
        self.results_folder = results_folder
        self.info = {}
        self.data = {}
        if self.IsCombined():
            self.__LoadResults()
        else:
            self.__CombineResults()
        
        self.interpolators = {}
        input_axes = [np.linspace(0, self.info['angle_max'], self.info['angle_max'] // self.info['angle_step'])]
        for phase in self['driven_phases']:
            for value in phase['coils'].values():
                if value != list(phase['coils'].values())[0]:
                    raise ValueError('phase step values must be equal')
            input_axes.append(np.linspace(0, list(phase['coils'].values())[0] * phase['steps'], phase['steps']))
        input_axes = input_axes[::-1]
        self.axes_to_exclude = []
        for idx in range(len(input_axes)):
            if len(input_axes[idx]) == 1:
                self.axes_to_exclude.append(idx)
        for idx in self.axes_to_exclude[::-1]:
            del input_axes[idx]
        
        new_shape = []
        for axis in input_axes:
            new_shape.append(len(axis))
        
        # Create interpolators
        for key, value in self.data.items():
            self.interpolators[key] = RegularGridInterpolator(input_axes, np.reshape(value, new_shape), method='linear', bounds_error=False, fill_value=None)
    
    def __getitem__(self, key: str) -> Any:
        return self.info[key]
    
    def __setitem__(self, key: str, value: Any):
        self.info[key] = value

    def IsCombined(self) -> bool:
        return os.path.isfile(self.results_folder + self.SIMULATION_INFO_FILE)

    def __GetGeometryInfo(self):
        # don't import this unles we need it
        geometry = MakeGeometry(self.results_folder + self.GEOMETRY_FOLDER)

        # copy over the geometry info we need for analysis
        self['winding_area'] = geometry.GetWindingCrossSection()
        self['avg_coil_length'] = geometry.GetAvgCoilLength()
        self['slot_pitch'] = geometry.slot_pitch
        self['pole_pitch'] = geometry.pole_pitch
        self['num_slots'] = geometry.num_slots
        self['num_poles'] = geometry.num_poles

    def __CombineResults(self):
        # combine results from all runs into combined folder
        if not os.path.isdir(self.results_folder):
            raise FileNotFoundError('results folder not found')
        if not os.path.isdir(self.results_folder + self.COMBINED_FOLDER):
            os.mkdir(self.results_folder + self.COMBINED_FOLDER)
        
        sim_config_location = self.results_folder + self.SIMULATION_CONFIG_FILE
        if not os.path.isfile(sim_config_location):
            raise FileNotFoundError('no config file found')

        sim_config_file = open(sim_config_location, 'r')
        sim_config = json.loads(sim_config_file.read())

        self['angle_step'] = sim_config['angle_step']
        self['angle_max'] = sim_config['angle_max']
        self['driven_phases'] = sim_config['driven_phases']

        data_shape = [int(self['angle_max'] // self['angle_step'])]
        for phase in sim_config['driven_phases']:
            data_shape.append(phase['steps'])
        data_shape = data_shape[::-1]
        self['data_shape'] = data_shape

        first_result_file = open(self.results_folder + '/run_0/results.json', 'r')
        first_result = json.loads(first_result_file.read())
        if not isinstance(first_result, list):
            raise ValueError('results.json does not contain a list')
        first_result_entry = FlattenDict(first_result[0])

        for key in first_result_entry:
            self.data[key] = np.zeros(data_shape)
        
        # now we can iterate over all data
        for run_folder in os.listdir(self.results_folder):
            if not os.path.isdir(self.results_folder + '/' + run_folder):
                continue
            run_location = self.results_folder + '/' + run_folder
            if not os.path.isfile(run_location + '/results.json'):
                continue
            file = open(run_location + '/results.json', 'r')
            data = json.loads(file.read())
            run_number = int(''.join([char for char in run_folder[::-1] if char.isdigit()])[::-1])
            num_angle_steps = int(self['angle_max'] // self['angle_step'])
            for entry in data:
                flat_entry = FlattenDict(entry)
                angle_index = int(flat_entry['angle'] // self['angle_step'])
                for key, value in flat_entry.items():
                    np.put(self.data[key], (run_number * num_angle_steps) + angle_index, value)
        
        # load geometry info
        self.__GetGeometryInfo()

        # save the combined data
        for key in self.data:
            np.save(self.results_folder + self.COMBINED_FOLDER + '/' + key + '.npy', self.data[key])
        with open(self.results_folder + self.SIMULATION_INFO_FILE, 'w') as f:
            f.write(json.dumps(self.info, indent=1))

    def __LoadResults(self):
        # load results that have already been combined
        if not os.path.isfile(self.results_folder + self.SIMULATION_INFO_FILE):
            raise FileNotFoundError('simulation info file not found')
        with open(self.results_folder + self.SIMULATION_INFO_FILE, 'r') as f:
            self.info = json.loads(f.read())
        for file in os.listdir(self.results_folder + self.COMBINED_FOLDER):
            if os.path.isfile(self.results_folder + self.COMBINED_FOLDER + file) and file[-4:] == '.npy':
                self.data[file[:-4]] = np.load(self.results_folder + self.COMBINED_FOLDER + file)

    def InterpolatePoint(self, driven_coils: Dict[str, float], data_name: str, angle: float) -> float:
        phase_mmf_values = [0] * len(self['driven_phases'])
        for idx in range(len(self['driven_phases'])):
            phase = self['driven_phases'][idx]
            first_coil_key = list(phase['coils'].keys())[0]
            first_driven_coil_value = driven_coils[first_coil_key]

            for coil in phase['coils']:
                if coil not in driven_coils:
                    raise ValueError('Driven coils must contain all coils')
                if driven_coils[coil] != first_driven_coil_value:
                    raise ValueError(f'coil mmf values must be equal to {first_driven_coil_value} across phase')

            phase_mmf_values[idx] = driven_coils[first_coil_key]
        value_to_interpolate = ([angle] + phase_mmf_values)[::-1]
        for idx in self.axes_to_exclude[::-1]:
            del value_to_interpolate[idx]
        return self.interpolators[data_name](value_to_interpolate)



if __name__ == "__main__":
    results = SimulationResults('complete_runs/run_5')
    import matplotlib.pyplot as plt
    print(results.InterpolatePoint({'a1': 60, 'a2': 60, 'b1': 0, 'b2': 0, 'c1': 0, 'c2': 0}, 'torque', 30))
    print(results.data['torque'][0,0,15,15])
    plt.plot(results.data['torque'][0,0,30,:])
    plt.show()
