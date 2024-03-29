#!/bin/python3

import femm
import os
import json
from argparse import ArgumentParser
from colorama import Fore, Style
from motor_geometry.interface.motor_geometry import MotorGeometry
from typing import Dict
# for debug
from motor_geometry.srm_design.srm_geometry import SrmGeometry

def simulate_motor(geometry: MotorGeometry, angle: float, circuit_mmf: Dict[str, float], image_path: str = None, temp_path: str = None):
    remaining_attempts = 3
    last_result = None
    while remaining_attempts > 0:
        last_result, success = run_simulation(geometry, angle, circuit_mmf, image_path, temp_path)
        if success:
            return last_result
        remaining_attempts -= 1
    print(Fore.RED + f'!!! failed to simulate at angle {angle} with circuit mmf {circuit_mmf} !!!\n' + Style.RESET_ALL)
    return last_result

def run_simulation(geometry: MotorGeometry, angle: float, circuit_mmf: Dict[str, float], image_path: str = None, temp_path: str = None):
    tempfile_fem = 'temp.FEM'
    tempfile_ans = 'temp.ans'

    if temp_path:
        tempfile_fem = temp_path + '/temp.FEM'
        tempfile_ans = temp_path + '/temp.ans'

    if os.path.isfile(tempfile_fem):
        os.remove(tempfile_fem)
    if os.path.isfile(tempfile_ans):
        os.remove(tempfile_ans)
    if not os.path.isfile(geometry.femm_file):
        raise ValueError('file not found')

    os.system(f'cp {geometry.femm_file} ' + tempfile_fem)

    femm.opendocument(tempfile_fem)

    geometry.RotateRotor(angle)

    for circuit, mmf in circuit_mmf.items():
        femm.mi_setcurrent(circuit, mmf)

    femm.mi_analyze()

    femm.mi_loadsolution()

    femm.mo_seteditmode('area')
    femm.mo_clearblock()
    femm.mo_groupselectblock(1)
    
    circuit_props = {}
    for circuit in circuit_mmf.keys():
        circuit_props[circuit] = femm.mo_getcircuitproperties(circuit)
    torque = femm.mo_blockintegral(22)

    if image_path:
        femm.main_resize(1200, 1600)
        femm.mo_zoom(1, 1, -1, -1)
        femm.mo_zoomnatural()
        femm.mo_showdensityplot(1, 0, 2.0, 0, 'bmag')
        femm.mo_clearblock()
        femm.mo_savebitmap(image_path)

    femm.mo_close()
    femm.mi_close()

    success = True
    if type(torque) == list:
        success = False
    
    output = {
        'circuits': {},
        'torque': 0,
        'angle': 0
    }
    for circuit in circuit_props.keys():
        output['circuits'][circuit] = {
            'current': 0,
            'voltage': 0,
            'flux': 0
        }


    try:
        output = {
            'torque': torque,
            'angle': angle,
            'circuits': {}
        }
        for circuit in circuit_props.keys():
            output['circuits'][circuit] = {
                'current': circuit_props[circuit][0],
                'voltage': circuit_props[circuit][1],
                'flux': circuit_props[circuit][2]
            }
    except IndexError:
        success = False

    os.remove(tempfile_ans)
    os.remove(tempfile_fem)

    return (output, success)

if __name__ == "__main__":
    parser = ArgumentParser(prog='motor_simulator')
    parser.add_argument('angle', type=float, help='rotor angle in degrees')
    args = parser.parse_args()
    geometry = SrmGeometry('test/geometry')
    currents = {
        'a1': 50,
        'a2': 50,
        'b1': 0,
        'b2': 0,
        'c1': 0,
        'c2': 0
    }
    femm.openfemm()
    output = simulate_motor(geometry, args.angle, currents, image_path = 'test/results/output.png', temp_path='test')
    with open('test/results/output.json', 'w') as f:
        f.write(json.dumps(output, indent=1))
    print(json.dumps(output, indent=1))
    femm.closefemm()

