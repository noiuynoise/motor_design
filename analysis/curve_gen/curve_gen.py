from abc import ABC, abstractmethod
from .simulation_results import SimulationResults
from .inverter_properties import InverterProperties
from dataclasses import dataclass

@dataclass
class MotorState:
    a_current: float
    b_current: float
    c_current: float

    a_voltage: float
    b_voltage: float
    c_voltage: float

    angle: float
    speed: float

@dataclass
class MotorCommand:
    a: float
    b: float
    c: float

    current_command: bool = False

class DriveAlgorithm(ABC):
    @abstractmethod
    def GetCommand(self, state: MotorState) -> MotorCommand:
        pass

    def
        

class CurveGen(ABC):
    @abstractmethod
    def GetTorque(self, state: MotorState) -> float:
        pass
    def GetPowerInput(self, state: MotorState) -> float:
        pass
    def GetLosses(self, state: MotorState) -> float:
        pass


class SrmCurveGen(CurveGen):
    def __init__(self, results: SimulationResults, inverter: InverterProperties, drive_algotithm: DriveAlgorithm):
        self.results = results
        self.inverter = inverter
        self.drive_algorithm = drive_algotithm

    def GetTorque(self, state: MotorState) -> float:
        