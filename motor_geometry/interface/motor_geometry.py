#!/bin/python3

from abc import ABC, abstractmethod


class MotorGeometry(ABC):
    def __init__(self, config_file: str, storage_folder: str):
        self.config_file = config_file
        self.storage_folder = storage_folder

    @abstractmethod
    def GenerateGeometry(self):
        pass

    @abstractmethod
    def GetRotateDiameter(self) -> float:
        pass
