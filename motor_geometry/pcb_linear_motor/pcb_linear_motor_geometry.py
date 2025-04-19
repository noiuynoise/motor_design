#!/bin/python3
import math
import sys

from typing import Dict, Any, List
from motor_geometry.drawing_tools.geometry_collection import *
from motor_geometry.interface.motor_geometry import MotorGeometry
from copy import deepcopy

import os
if 'SIM_RUNNER' in os.environ:
    import femm

class PcbLinearMotorGeometry(MotorGeometry):
    def __init__(self, config_file: str):
        super().__init__(config_file)

    def build_pcb(self) -> GeometryCollection:
        pcb = GeometryCollection()
        pcb_top_y = self.config['pcb']['core_thickness'] / 2
        pcb_copper_top_y = pcb_top_y - self.config['pcb']['copper_thickness']

        trace_width = self.config['pcb']['trace_width']
        trace_pitch = self.config['pcb']['trace_pitch']
        num_traces = self.config['pcb']['num_traces']

        traces_per_coil = self.config['winding']['traces_per_coil']
        num_phases = int(self.config['winding']['num_phases'])
        series_layers = self.config['pcb']['series_layers']
        for i in range(num_traces):
            x = i * trace_pitch - trace_pitch * num_traces/2
            phase_idx = int(i / traces_per_coil) % (num_phases * 2)
            trace_label = {
            "name": self.config['winding']['coil_material'],
            "automesh": self.config['simulation']['automesh'],
            "meshsize": self.config['simulation']['mesh_size'],
            "circuit": chr( ord('A') + phase_idx % num_phases),
            "group": 0,
            "turns": series_layers if (phase_idx < num_phases) else -series_layers
            }
            pcb.add_rectangle((x + trace_width/2, pcb_copper_top_y), (x - trace_width/2, pcb_top_y))
            pcb.add_label((x, (pcb_top_y + pcb_copper_top_y) / 2), trace_label)
            if self.config['pcb']['both_sides']:
                pcb.add_rectangle((x + trace_width/2, -pcb_copper_top_y), (x - trace_width/2, -pcb_top_y))
                pcb.add_label((x, (pcb_top_y + pcb_copper_top_y) / -2), trace_label)

        air_label = {
            "name": self.config['simulation']['outer_material'],
            "automesh": self.config['simulation']['automesh'],
            "meshsize": self.config['simulation']['mesh_size'],
            "circuit": 0,
            "group": 0,
            "turns": 0
        }
        pcb.add_label((0, 0), air_label)
        margin = self.config['simulation']['boundary_margin']
        backer_thickness = self.config['pcb']['backer_thickness']
        backer_spacing = self.config['pcb']['backer_spacing']
        pcb.add_rectangle((-trace_width/2 - trace_pitch * num_traces/2 - margin, pcb_top_y + margin), (trace_pitch * num_traces/2 + trace_width/2 + margin, -pcb_top_y - margin - backer_thickness - backer_spacing))

        pcb.add_rectangle((-trace_width/2 - trace_pitch * num_traces/2, -pcb_top_y - backer_spacing), (trace_pitch * num_traces/2 + trace_width/2, -pcb_top_y - backer_spacing - backer_thickness))
        backer_label = {
            "name": self.config['pcb']['backer_material'],
            "automesh": self.config['simulation']['automesh'],
            "meshsize": self.config['simulation']['mesh_size'],
            "circuit": 0,
            "group": 0,
            "turns": 0
        }
        pcb.add_label((0, -pcb_top_y - backer_spacing - backer_thickness/2), backer_label)

        return pcb

    def build_rotor(self) -> GeometryCollection:
        rotor = GeometryCollection()
        pcb_top_y = self.config['pcb']['core_thickness'] / 2
        rotor_bottom_y = pcb_top_y + self.config['rotor']['rotor_spacing']
        rotor_top_y = rotor_bottom_y + self.config['rotor']['rotor_thickness']
        rotor_length = self.config['rotor']['rotor_length']

        rotor.add_rectangle((-rotor_length/2, rotor_top_y),(rotor_length/2, rotor_bottom_y))
        rotor_label = {
            "name": self.config['rotor']['rotor_material'],
            "automesh": self.config['simulation']['automesh'],
            "meshsize": self.config['simulation']['mesh_size'],
            "circuit": 0,
            "group": 1,
            "turns": 0
        }
        rotor.add_label((0,(rotor_top_y + rotor_bottom_y) / 2), rotor_label)
        
        return rotor

    def GetCircuits(self):
        circuit_names = []
        for i in range(self.config['winding']['num_phases']):
            circuit_names.append(chr(ord('A') + i))
        return circuit_names

    def GenerateGeometry(self):
        pcb = self.build_pcb()
        rotor = self.build_rotor()

        femm.newdocument(0)

        define_problem(self.config)
        load_materials(self.config)
        add_circuits(self.GetCircuits())

        pcb.draw()
        rotor.draw()

        femm.mi_saveas(self.femm_file)
        femm.mi_close()

    def GetRotorWeight(self) -> float:
        rotor_height = self.config['rotor']['rotor_thickness']
        rotor_length = self.config['rotor']['rotor_length']
        rotor_depth = self.config['simulation']['depth']
        COPPER_DENSITY = 0.008935
        return rotor_height * rotor_length * rotor_depth * COPPER_DENSITY
        

    # dissipation is in W/cm2
    def GetCurrentForDissipation(self, dissipation: float) -> Dict[str, complex]:
        circuit_names = self.GetCircuits()
        num_circuits = len(circuit_names)
        trace_pitch = self.config['pcb']['trace_pitch']
        num_traces = self.config['pcb']['num_traces']
        depth = self.config['simulation']['depth']
        series_layers = self.config['pcb']['series_layers']
        board_area_cm2 = trace_pitch * depth * num_traces / 100

        COPPER_RESISTIVITY = 1.68e-8
        resistance_per_meter = COPPER_RESISTIVITY / self.GetWindingCrossSection()
        circuit_resistance = resistance_per_meter * self.GetAvgCoilLength() * series_layers
        all_circuit_resistance = circuit_resistance * num_circuits
        all_rms_current = math.sqrt(dissipation * board_area_cm2 / all_circuit_resistance)
        currents = {}
        for i in range(num_circuits):
            currents[circuit_names[i]] = (all_rms_current / 0.707) * (math.cos(i * 2 * math.pi / num_circuits) + 1j * math.sin(i * 2 * math.pi / num_circuits))
        return currents

    def GetRotateDiameter(self) -> float:
        return 0.0
    
    def RotateRotor(self, angle: float):
        femm.mi_selectcircle(0, 0, self.GetRotateDiameter() / 2, 4)
        femm.mi_selectgroup(1)
        femm.mi_moverotate(0, 0, angle)
    
    def GetAvgCoilLength(self) -> float:
        return self.config['pcb']['series_layers'] * self.config['pcb']['num_traces'] \
            / len(self.GetCircuits()) * self.config['simulation']['depth'] / 1000

    def GetWindingCrossSection(self) -> float:
        return self.config['pcb']['trace_width'] * self.config['pcb']['copper_thickness'] / 1000000

    def SetFrequency(self, frequency: float):
        config = deepcopy(self.config)
        config['simulation']['frequency'] = frequency
        define_problem(config)


if __name__ == "__main__":
    # TODO: how test?
    filepath = 'test/geometry'
    femm.openfemm()
    try:
        geometry = PcbLinearMotorGeometry(filepath)
        geometry.GenerateGeometry()
    except Exception as e:
        print(e)
    femm.closefemm()
