#!/bin/python3

import femm
import os
import json
from colorama import Fore, Style
from motor_geometry.interface.motor_geometry import MotorGeometry
from typing import Dict
# for debug
from motor_geometry.pcb_linear_motor.pcb_linear_motor_geometry import PcbLinearMotorGeometry
from math import sin, cos, pi

def simulate_induction_motor(geometry: MotorGeometry, frequency: float, circuit_mmf: Dict[str, complex], image_path: str = None, temp_path: str = None):
    remaining_attempts = 3
    last_result = None
    while remaining_attempts > 0:
        last_result, success = run_simulation(geometry, frequency, circuit_mmf, image_path, temp_path)
        if success:
            return last_result
        remaining_attempts -= 1
    print(Fore.RED + f'!!! failed to simulate at frequency {frequency} with circuit mmf {circuit_mmf} !!!\n' + Style.RESET_ALL)
    return last_result

def run_simulation(geometry: MotorGeometry, frequency: float, circuit_mmf: Dict[str, complex], image_path: str = None, temp_path: str = None):
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

    for circuit, mmf in circuit_mmf.items():
        femm.mi_setcurrent(circuit, mmf)
    
    geometry.SetFrequency(frequency)

    femm.mi_analyze()

    femm.mi_loadsolution()

    femm.mo_seteditmode('area')
    femm.mo_clearblock()
    femm.mo_groupselectblock(1)
    
    circuit_props = {}
    for circuit in circuit_mmf.keys():
        circuit_props[circuit] = femm.mo_getcircuitproperties(circuit)
    torque = femm.mo_blockintegral(22)
    force_x = femm.mo_blockintegral(18)
    force_y = femm.mo_blockintegral(19)

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
        'force_x': 0,
        'force_y': 0,
        'frequency': 0,
    }
    for circuit in circuit_props.keys():
        output['circuits'][circuit] = {
            'current_re': 0,
            'current_im': 0,
            'voltage_re': 0,
            'voltage_im': 0,
            'flux_re': 0,
            'flux_im': 0
        }


    try:
        output = {
            'torque': torque,
            'force_x': force_x,
            'force_y': force_y,
            'frequency': frequency,
            'circuits': {}
        }
        for circuit in circuit_props.keys():
            output['circuits'][circuit] = {
                'current_re': circuit_props[circuit][0].real,
                'current_im': circuit_props[circuit][0].imag,
                'voltage_re': circuit_props[circuit][1].real,
                'voltage_im': circuit_props[circuit][1].imag,
                'flux_re': circuit_props[circuit][2].real,
                'flux_im': circuit_props[circuit][2].imag,
            }
    except IndexError:
        success = False
    
    for out in output.values():
        if type(out) == list:
            success = False
    
    for circuit in circuit_props.keys():
        for out in output['circuits'][circuit].values():
            if type(out) == list:
                success = False

    os.remove(tempfile_ans)
    os.remove(tempfile_fem)

    return (output, success)

if __name__ == "__main__":
    geometry = PcbLinearMotorGeometry('test/geometry')
    currents = {}
    for i in range(3):
        currents[chr(ord('A') + i)] = cos(i * 2 * pi / 3) + 1j * sin(i * 2 * pi / 3)
    femm.openfemm()
    output = simulate_induction_motor(geometry, 10000, currents, image_path = 'test/results/output.png', temp_path='test')
    with open('test/results/output.json', 'w') as f:
        f.write(json.dumps(output, indent=1))
    print(json.dumps(output, indent=1))
    femm.closefemm()

