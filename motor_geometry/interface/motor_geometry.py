#!/bin/python3

from abc import ABC, abstractmethod
import json
import os

class MotorGeometry(ABC):
    def __init__(self, folder: str):
        self.folder = folder
        config_file = folder + '/motor_config.json'
        if type(config_file) == str:
            if not os.path.isfile(config_file):
                raise ValueError('config not found')
            with open(config_file, 'r') as f:
                self.config = json.load(f)
                return
        elif type(config_file) == dict:
            self.config = config_file
            return

        raise ValueError('MotorConfig requires either a file or a dictionary')

    @property
    def femm_file(self):
        return self.folder + '/motor.FEM'

    @property
    def is_geometry_generated(self):
        return os.path.isfile(self.femm_file)
    
    @abstractmethod
    def SetFrequency(self, frequency: float):
        raise NotImplementedError("SetFrequency not implemented")
    
    @abstractmethod
    def RotateRotor(self, angle: float):
        raise NotImplementedError("RotateRotor not implemented")

    @abstractmethod
    def GenerateGeometry(self):
        raise NotImplementedError("GenerateGeometry not implemented")

    @abstractmethod
    def GetWindingCrossSection(self) -> float:
        # Get the area of the winding cross section (all conductors) in m^2
        raise NotImplementedError("GetWindingCrossSection not implemented")

    @abstractmethod
    def GetAvgCoilLength(self) -> float:
        # Get the average wire length of a single coil in m - includes wire going through and between slots but not motor leads
        raise NotImplementedError("GetAvgCoilLength not implemented")

    @property
    def slot_pitch(self) -> float:
        return 360 / self.config['stator']['slots']

    @property
    def pole_pitch(self) -> float:
        return 360 / self.config['rotor']['poles']

    @property
    def num_slots(self) -> int:
        return self.config['stator']['slots']

    @property
    def num_poles(self) -> int:
        return self.config['rotor']['poles']

    def GetCircuits(self):
        windings = self.config["winding"]["order"]
        circuit_names = []
        for winding in windings:
            # check that the last character is a + or -
            if winding[-1] != "+" and winding[-1] != "-":
                raise ValueError('winding name must end with + or -')
            if winding[:-1] not in circuit_names:
                circuit_names.append(winding[:-1])
        return circuit_names
