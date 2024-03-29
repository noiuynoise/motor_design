#!/bin/bash

from motor_geometry.interface.motor_geometry_factory import MakeGeometry
import os
import femm

# This script is used to generate the motor geometry to be used for simulation
if __name__ == "__main__":
    os.makedirs("run/geometry", exist_ok=True)
    os.system("cp motor_config.json run/geometry/motor_config.json")
    motor = MakeGeometry("run/geometry")
    femm.openfemm()
    motor.GenerateGeometry()
    femm.closefemm()
