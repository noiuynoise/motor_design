#!/bin/bash

from motor_geometry.srm_design.srm_geometry import SrmGeometry
import os
import json

# This script is used to generate the motor geometry to be used for simulation
if __name__ == "__main__":
    os.mkdir("run/geometry")
    os.system("cp config.json run/geometry/config.json")
    motor = SrmGeometry("run/geometry/config.json",
                        "run/geometry/motor.FEM")
    motor.GenerateGeometry()
    sim_info = {
        "rotate_diameter": motor.GetRotateDiameter(),
        # TODO: This should be calculated from the config file to be the minimum necessary to simulate the motor
        "pole_pitch": 90
    }
    with open('run/geometry/sim_info.json', 'w') as f:
        f.write(json.dumps(sim_info, indent=4))
