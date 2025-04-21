
from analysis.simulation_results import SimulationResults
import os
import json
from typing import Any, List, Dict
import math

# from: https://www.powerstream.com/Wire_Size.htm
# diameter in mm
AWG_DIAMETER = {
    10: 2.58826,
    12: 2.05232,
    14: 1.62814,
    16: 1.29032,
    18: 1.02362,
    20: 0.8128,
    22: 0.64516,
    24: 0.51054,
    26: 0.40386,
    28: 0.32004,
    30: 0.254,
    32: 0.2032,
    34: 0.16002,
    36: 0.127
}

class MotorAnalyser:
    def __init__(self, analysis_config: str, results: str):
        if not os.path.isfile(analysis_config):
            raise FileNotFoundError('analysis config file not found')
        if not os.path.isdir(results):
            raise FileNotFoundError('results folder not found')

        config = open(analysis_config, 'r')
        self.analysis_config = json.loads(config.read())
        self.results = SimulationResults(results)

        if self.GetFillFactor() > 1:
            print('Warning: fill factor exceeds 1')

    def __getitem__(self, key: str) -> Any:
        return self.analysis_config[key]

    def GetConductorArea(self) -> float:
        # conductor area in m^2
        conductor_gauge = self['motor']['wire_gauge']
        if conductor_gauge not in AWG_DIAMETER:
            raise ValueError(f'Unsupported wire gauge: {conductor_gauge}')

        single_conductor_area = (AWG_DIAMETER[conductor_gauge] / 2) ** 2 * math.pi
        num_conductors = self['motor']['parallel_strands'] * self['motor']['number_of_turns']

        all_conductors_area_mm2 = single_conductor_area * num_conductors
        all_conductors_area_m2 = all_conductors_area_mm2 * 1e-6
        return all_conductors_area_m2

    def GetFillFactor(self) -> float:
        # assume all windings equal area
        return self.GetConductorArea() / self.results['winding_area']
    
    def GetWindingResistance(self) -> float:
        # winding resistance in ohms
        conductor_gauge = self['motor']['wire_gauge']
        if conductor_gauge not in AWG_DIAMETER:
            raise ValueError(f'Unsupported wire gauge: {conductor_gauge}')

        single_conductor_area = (AWG_DIAMETER[conductor_gauge] / 2) ** 2 * math.pi
        num_conductors = self['motor']['parallel_strands']

        total_area_m2 = single_conductor_area * num_conductors * 1e-6
        total_length_m = self.results['avg_coil_length'] * self['motor']['number_of_turns']

        COPPER_RESISTIVITY = 1.68e-8
        resistance_per_meter = COPPER_RESISTIVITY / total_area_m2

        return resistance_per_meter * total_length_m

    def GetPhaseResistance(self) -> float:
        # TODO: account for lead resistance + interconnect resistance
        if self['motor']['termination'] == 'parallel':
            return self.GetWindingResistance() / self.GetCoilsPerPhase()
        elif self['motor']['termination'] == 'series':
            return self.GetWindingResistance() * self.GetCoilsPerPhase()
        else:
            raise ValueError('unsupported winding termination')
    
    def GetCoilsPerPhase(self) -> int:
        # TODO: this should come from a better parameter
        return len(self.results['driven_phases'][0]['coils'])
    
    def EstimateTorqueCurve(self, speed_start, speed_end) -> Dict[str, List[float]]:
        if speed_start >= speed_end:
            raise ValueError('speed_start must be less than speed_end')
        if speed_start < 0:
            raise ValueError('speed_start must be positive')
        
        curr_speed = speed_start
        results = {}
        while curr_speed < speed_end:
            # TODO: This should be an easy multiprocessing target
            speed_result = self.SimulateRotation(curr_speed)
            for key in speed_result:
                if key not in results:
                    results[key] = []
                results[key].append(speed_result[key])
        return results
    
    def SimulateRotation(self, speed: float) -> Dict[str, List[float]]:
        # simulate rotation at a given speed (in RPM)
        results = {"speed": speed, "flux": []}
        for angle in range(0, 360, self['motor']['angle_step']):
            pass

        # return torque, current, etc
        return results




if __name__ == "__main__":
    analyser = MotorAnalyser('analysis/analysis_config.json', 'complete_runs/run_5')
    print(analyser.GetFillFactor())
    print(analyser.GetConductorArea())
    print(analyser['motor']['wire_gauge'])
    print(analyser['motor']['parallel_strands'])
    print(analyser['motor']['number_of_turns'])
    print(analyser.results['winding_area'])
    print(analyser.results['winding_area'] / analyser.GetConductorArea())