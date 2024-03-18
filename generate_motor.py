#!/bin/bash

from motor_geometry.srm_design.srm_geometry import SrmGeometry
import os
import femm

# This script is used to generate the motor geometry to be used for simulation
if __name__ == "__main__":
    os.makedirs("run/geometry", exist_ok=True)
    os.system("cp motor_config.json run/geometry/motor_config.json")
    motor = SrmGeometry("run/geometry")
    femm.openfemm()
    motor.GenerateGeometry()
    femm.closefemm()
