from motor_geometry.interface.motor_geometry import MotorGeometry
from motor_geometry.srm_design.srm_geometry import SrmGeometry
from motor_geometry.pcb_linear_motor.pcb_linear_motor_geometry import PcbLinearMotorGeometry
import os
import json

def MakeGeometry(folder: str) -> MotorGeometry:
    # load the json and look for the geometry label
    if not os.path.isfile(folder + '/motor_config.json'):
        raise FileNotFoundError('motor_config.json not found at: ' + folder + '/motor_config.json') 
    file =  open(folder + '/motor_config.json', 'r')
    config = json.load(file)
    if 'geometry' not in config:
        raise ValueError('geometry not specified in config')
    
    geometry = config['geometry']
    if geometry == 'srm':
        return SrmGeometry(folder)
    elif geometry == 'pcb_linear_motor':
        return PcbLinearMotorGeometry(folder)
    else:
        raise ValueError('unknown geometry type')