#!/bin/python3

import femm
import math

from typing import Dict, Any, List
from utils.motor_config_helper import MotorConfig
from drawing_tools.geometry_collection import *
from interface.motor_geometry import MotorGeometry

def build_stator(config) -> GeometryCollection:
    stator_slice = GeometryCollection()
    stator_slot_angle = 2 * math.pi / config['stator']['slots']

    # OD curve
    outer_radius = config['stator']['outer_diameter'] / 2
    od_end = (0, outer_radius)
    od_start = polar_point(outer_radius, -stator_slot_angle)
    stator_slice.add_arc(od_start, od_end, stator_slot_angle)

    # ID curves
    tooth_curve_angle = math.asin(
        config['stator']['tooth_tip_width'] / (config['stator']['inner_diameter']))

    inner_radius = config['stator']['inner_diameter'] / 2
    id1_end = (0, inner_radius)
    id1_start = polar_point(inner_radius, -tooth_curve_angle)

    id2_start = polar_point(inner_radius, -stator_slot_angle)
    id2_end = polar_point(inner_radius, -stator_slot_angle + tooth_curve_angle)

    stator_slice.add_arc(id1_start, id1_end, tooth_curve_angle)
    stator_slice.add_arc(id2_start, id2_end, tooth_curve_angle)

    # Teeth
    spine_radius = config['stator']['outer_diameter'] / \
        2 - config['stator']['spine_width']
    tooth_root_angle = math.asin(
        config['stator']['tooth_root_width'] / 2 / spine_radius)

    tooth1_start = id1_start
    tooth1_end = polar_point(spine_radius, -tooth_root_angle)

    tooth2_start = id2_end
    tooth2_end = polar_point(
        spine_radius, -stator_slot_angle + tooth_root_angle)

    stator_slice.add_line(tooth1_start, tooth1_end)
    stator_slice.add_line(tooth2_start, tooth2_end)

    # Spine
    spine_start = tooth2_end
    spine_middle = polar_point(spine_radius, -stator_slot_angle / 2)
    spine_end = tooth1_end
    spine_angle = stator_slot_angle - 2 * tooth_root_angle
    stator_slice.add_arc(spine_start, spine_middle, spine_angle / 2)
    stator_slice.add_arc(spine_middle, spine_end, spine_angle / 2)

    # Coils
    coil_line_end = polar_point(inner_radius, -stator_slot_angle / 2)

    stator_slice.add_line(spine_middle, coil_line_end)
    stator_slice.add_arc(id1_start, coil_line_end, -
                         stator_slot_angle / 2 + tooth_curve_angle)
    stator_slice.add_arc(coil_line_end, id2_end, -
                         stator_slot_angle / 2 + tooth_curve_angle)

    # Air simulation boundary
    air_radius = config['simulation']['outer_diameter'] / 2
    stator_slice.add_arc((0, air_radius), polar_point(
        air_radius, stator_slot_angle), stator_slot_angle)

    # Radii
    if config['stator']['tooth_root_radius'] > 0:
        stator_slice.add_radius(
            tooth1_end, config['stator']['tooth_root_radius'])
        stator_slice.add_radius(
            tooth2_end, config['stator']['tooth_root_radius'])

    if config['stator']['tooth_tip_radius'] > 0:
        raise NotImplementedError('tooth tip radius not yet supported')
        stator_slice.add_radius(
            tooth1_start, config['stator']['tooth_tip_radius'])
        stator_slice.add_radius(
            tooth2_start, config['stator']['tooth_tip_radius'])

    stator = stator_slice.circular_pattern((0, 0), config['stator']['slots'])

    # Annotations
    stator_annotation = (outer_radius + inner_radius) / 2
    stator_label = {
        "name": config['stator']['material'],
        "automesh": config['simulation']['automesh'],
        "meshsize": config['simulation']['mesh_size'],
        "circuit": 0,
        "group": 2,
        "turns": 0
    }
    stator.add_label((0, stator_annotation), stator_label)

    air_annotation = (outer_radius + air_radius) / 2
    air_label = {
        "name": config['simulation']['outer_material'],
        "automesh": config['simulation']['automesh'],
        "meshsize": config['simulation']['mesh_size'],
        "circuit": 0,
        "group": 2,
        "turns": 0
    }
    stator.add_label((0, air_annotation), air_label)

    winding_annotations = []
    winding_annotation_radius = (inner_radius + spine_radius) / 2
    for i in range(config['stator']['slots']):
        winding_annotations.append(
            polar_point(winding_annotation_radius, -i * stator_slot_angle +
                        ((stator_slot_angle / 2) + tooth_curve_angle) / 2)
        )
        winding_annotations.append(
            polar_point(winding_annotation_radius, -i * stator_slot_angle -
                        ((stator_slot_angle / 2) + tooth_curve_angle) / 2)
        )
    add_winding_labels(config, winding_annotations, stator)

    return stator


def build_rotor(config) -> GeometryCollection:
    rotor_slice = GeometryCollection()
    rotor_slot_angle = 2 * math.pi / config['rotor']['poles']

    # tip curve
    rotor_radius = config['rotor']['outer_diameter'] / 2
    pole_tip_angle = math.asin(
        config['rotor']['pole_tip_width'] / 2 / rotor_radius)
    pole_tip_start = polar_point(rotor_radius, -pole_tip_angle)
    pole_tip_end = polar_point(rotor_radius, pole_tip_angle)
    rotor_slice.add_arc(pole_tip_start, pole_tip_end, 2 * pole_tip_angle)

    # pole lines
    pole_root_radius = config['rotor']['shaft_diameter'] / \
        2 + config['rotor']['rib_width']
    pole_root_angle = math.asin(
        config['rotor']['pole_root_width'] / 2 / pole_root_radius)
    pole_root_right = polar_point(pole_root_radius, -pole_root_angle)
    pole_root_left = polar_point(pole_root_radius, pole_root_angle)

    rotor_slice.add_line(pole_tip_start, pole_root_right)
    rotor_slice.add_line(pole_tip_end, pole_root_left)

    # rib arcs
    rib_arc_angle = -rotor_slot_angle + 2 * pole_root_angle
    rib_arc_end = polar_point(
        pole_root_radius, rib_arc_angle - pole_root_angle)

    rotor_slice.add_arc(pole_root_right, rib_arc_end, rib_arc_angle)

    # shaft
    shaft_radius = config['rotor']['shaft_diameter'] / 2
    shaft_end = (0, shaft_radius)
    shaft_start = polar_point(shaft_radius, -rotor_slot_angle)

    rotor_slice.add_arc(shaft_start, shaft_end, rotor_slot_angle)

    # Radii
    if config['rotor']['pole_tip_radius'] > 0:
        rotor_slice.add_radius(
            pole_tip_start, config['rotor']['pole_tip_radius'])
        rotor_slice.add_radius(
            pole_tip_end, config['rotor']['pole_tip_radius'])

    if config['rotor']['pole_root_radius'] > 0:
        rotor_slice.add_radius(
            pole_root_right, config['rotor']['pole_root_radius'])
        rotor_slice.add_radius(
            pole_root_left, config['rotor']['pole_root_radius'])

    rotor = rotor_slice.circular_pattern((0, 0), config['rotor']['poles'])

    # Annotations
    rotor_annotation = rotor_radius / 2
    rotor_label = {
        "name": config['rotor']['material'],
        "automesh": config['simulation']['automesh'],
        "meshsize": config['simulation']['mesh_size'],
        "circuit": 0,
        "group": 1,
        "turns": 0
    }
    rotor.add_label((0, rotor_annotation), rotor_label)

    shaft_label = {
        "name": config['rotor']['shaft_material'],
        "automesh": config['simulation']['automesh'],
        "meshsize": config['simulation']['mesh_size'],
        "circuit": 0,
        "group": 1,
        "turns": 0
    }
    rotor.add_label((0, 0), shaft_label)

    airgap_annotation = (
        rotor_radius + config['stator']['inner_diameter'] / 2) / 2
    airgap_label = {
        "name": config['simulation']['airgap_material'],
        "automesh": config['simulation']['automesh'],
        "meshsize": config['simulation']['mesh_size'],
        "circuit": 0,
        "group": 2,
        "turns": 0
    }
    rotor.add_label((0, airgap_annotation), airgap_label)

    return rotor



def generate_motor(config, output) -> Dict[str, Any]:
    stator = build_stator(config)
    rotor = build_rotor(config)

    femm.openfemm()
    femm.newdocument(0)

    define_problem(config)
    load_materials(config)
    circuits = add_circuits(config)

    stator.draw()
    rotor.draw()

    femm.mi_saveas(output)
    femm.mi_close()

    return {
        "rotor_od": (config['rotor']['outer_diameter'] + config['stator']['inner_diameter']) / 2,
        "circuit_names": circuits
    }


class SrmGeometry(MotorGeometry):
    def __init__(self, config_file: str, storage_folder: str):
        self.rotate_diameter = None
        self.circuit_names = None
        super().__init__(config_file, storage_folder)

    def GenerateGeometry(self):
        params = generate_motor(self.config_file, self.storage_folder)
        self.rotate_diameter = params['rotor_od']
        self.circuit_names = params['circuit_names']

    def GetRotateDiameter(self) -> float:
        return self.rotate_diameter
        

if __name__ == "__main__":
    filepath = 'sample_config.json'
    config = MotorConfig(filepath)
    print(generate_motor(config, 'motor.FEM'))
