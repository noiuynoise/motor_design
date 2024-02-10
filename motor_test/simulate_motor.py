#!/bin/python3

import femm
import os
import json
from argparse import ArgumentParser
from colorama import Fore, Style

def simulate_motor(motor_file, radius, angle, i_a, i_b, i_c, image_path = None):
    remaining_attempts = 3
    last_result = None
    while remaining_attempts > 0:
        last_result, success = run_simulation(motor_file, radius, angle, i_a, i_b, i_c, image_path)
        if success:
            return last_result
        remaining_attempts -= 1
    print(Fore.RED + f'!!! failed to simulate at angle {angle} with {i_a}, {i_b}, {i_c} !!!\n' + Style.RESET_ALL)
    return last_result

def run_simulation(motor_file, radius, angle, i_a, i_b, i_c, image_path = None):
    if os.path.isfile('temp.FEM'):
        os.remove('temp.FEM')
    if os.path.isfile('temp.ans'):
        os.remove('temp.ans')
    if not os.path.isfile(motor_file):
        raise ValueError('file not found')

    os.system(f'cp {motor_file} temp.FEM')

    femm.opendocument('temp.FEM')

    femm.mi_selectcircle(0, 0, radius, 4)
    femm.mi_selectgroup(1)
    femm.mi_moverotate(0, 0, angle)    

    femm.mi_setcurrent('a', i_a)
    femm.mi_setcurrent('b', i_b)
    femm.mi_setcurrent('c', i_c)

    femm.mi_analyze()

    femm.mi_loadsolution()

    femm.mo_seteditmode('area')
    femm.mo_clearblock()
    femm.mo_groupselectblock(1)
    
    props_a = femm.mo_getcircuitproperties('a')
    props_b = femm.mo_getcircuitproperties('b')
    props_c = femm.mo_getcircuitproperties('c')
    torque = femm.mo_blockintegral(22)

    if image_path:
        femm.mo_zoom(1, 1, -1, -1)
        femm.mo_zoomnatural()
        femm.mo_showdensityplot(1, 0, 1.75, 0, 'bmag')
        femm.mo_clearblock()
        femm.mo_savebitmap(image_path)

    femm.mo_close()
    femm.mi_close()

    success = True
    if len(props_a) != 3 or len(props_b) != 3 or len(props_c) != 3 or type(torque) == list:
        success = False
    
    output = {
        'a': {'current': props_a[0], 'voltage': props_a[1], 'flux': props_a[2]},
        'b': {'current': props_b[0], 'voltage': props_b[1], 'flux': props_b[2]},
        'c': {'current': props_c[0], 'voltage': props_c[1], 'flux': props_c[2]},
        'torque': torque,
        'angle': angle
    }

    os.remove('temp.ans')
    os.remove('temp.FEM')

    return (output, success)

if __name__ == "__main__":
    parser = ArgumentParser(prog='motor_simulator')
    parser.add_argument('file', type=str, help='motor FEMM file')
    parser.add_argument('radius', type=float, help='rotor radius')
    parser.add_argument('angle', type=float, help='rotor angle in degrees')
    parser.add_argument('i_a', type=float, help='phase A current')
    parser.add_argument('i_b', type=float, help='phase B current')
    parser.add_argument('i_c', type=float, help='phase C current')
    args = parser.parse_args()
    femm.openfemm()
    output = simulate_motor(args.file, args.radius, args.angle, args.i_a, args.i_b, args.i_c, image_path = 'output.png')
    with open('output.json', 'w') as f:
        f.write(json.dumps(output, indent=4))
    print(json.dumps(output, indent=4))
    femm.closefemm()

