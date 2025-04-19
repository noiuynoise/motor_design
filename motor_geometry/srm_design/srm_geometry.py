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

class SrmGeometry(MotorGeometry):
    def __init__(self, config_file: str):
        super().__init__(config_file)

    def build_stator(self) -> GeometryCollection:
        stator_slice = GeometryCollection()
        stator_slot_angle = 2 * math.pi / self.config['stator']['slots']

        # OD curve
        outer_radius = self.config['stator']['outer_diameter'] / 2
        od_end = (0, outer_radius)
        od_start = polar_point(outer_radius, -stator_slot_angle)
        stator_slice.add_arc(od_start, od_end, stator_slot_angle)

        # ID curves
        tooth_curve_angle = math.asin(
            self.config['stator']['tooth_tip_width'] / (self.config['stator']['inner_diameter']))

        inner_radius = self.config['stator']['inner_diameter'] / 2
        id1_end = (0, inner_radius)
        id1_start = polar_point(inner_radius, -tooth_curve_angle)

        id2_start = polar_point(inner_radius, -stator_slot_angle)
        id2_end = polar_point(
            inner_radius, -stator_slot_angle + tooth_curve_angle)

        stator_slice.add_arc(id1_start, id1_end, tooth_curve_angle)
        stator_slice.add_arc(id2_start, id2_end, tooth_curve_angle)

        # Teeth
        spine_radius = self.config['stator']['outer_diameter'] / \
            2 - self.config['stator']['spine_width']
        tooth_root_angle = math.asin(
            self.config['stator']['tooth_root_width'] / 2 / spine_radius)

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
        air_radius = self.config['simulation']['outer_diameter'] / 2
        stator_slice.add_arc((0, air_radius), polar_point(
            air_radius, stator_slot_angle), stator_slot_angle)

        # Radii
        if self.config['stator']['tooth_root_radius'] > 0:
            stator_slice.add_radius(
                tooth1_end, self.config['stator']['tooth_root_radius'])
            stator_slice.add_radius(
                tooth2_end, self.config['stator']['tooth_root_radius'])

        if self.config['stator']['tooth_tip_radius'] > 0:
            raise NotImplementedError('tooth tip radius not yet supported')
            stator_slice.add_radius(
                tooth1_start, self.config['stator']['tooth_tip_radius'])
            stator_slice.add_radius(
                tooth2_start, self.config['stator']['tooth_tip_radius'])

        stator = stator_slice.circular_pattern(
            (0, 0), self.config['stator']['slots'])

        # Annotations
        stator_annotation = (outer_radius + inner_radius) / 2
        stator_label = {
            "name": self.config['stator']['material'],
            "automesh": self.config['simulation']['automesh'],
            "meshsize": self.config['simulation']['mesh_size'],
            "circuit": 0,
            "group": 2,
            "turns": 0
        }
        stator.add_label((0, stator_annotation), stator_label)

        air_annotation = (outer_radius + air_radius) / 2
        air_label = {
            "name": self.config['simulation']['outer_material'],
            "automesh": self.config['simulation']['automesh'],
            "meshsize": self.config['simulation']['mesh_size'],
            "circuit": 0,
            "group": 2,
            "turns": 0
        }
        stator.add_label((0, air_annotation), air_label)

        winding_annotations = []
        winding_annotation_radius = (inner_radius + spine_radius) / 2
        for i in range(self.config['stator']['slots']):
            winding_annotations.append(
                polar_point(winding_annotation_radius, -i * stator_slot_angle +
                            ((stator_slot_angle / 2) + tooth_curve_angle) / 2)
            )
            winding_annotations.append(
                polar_point(winding_annotation_radius, -i * stator_slot_angle -
                            ((stator_slot_angle / 2) + tooth_curve_angle) / 2)
            )
        add_winding_labels(self.config, winding_annotations, stator)

        return stator

    def build_rotor(self) -> GeometryCollection:
        rotor_slice = GeometryCollection()
        rotor_slot_angle = 2 * math.pi / self.config['rotor']['poles']

        # tip curve
        rotor_radius = self.config['rotor']['outer_diameter'] / 2
        pole_tip_angle = math.asin(
            self.config['rotor']['pole_tip_width'] / 2 / rotor_radius)
        pole_tip_start = polar_point(rotor_radius, -pole_tip_angle)
        pole_tip_end = polar_point(rotor_radius, pole_tip_angle)
        rotor_slice.add_arc(pole_tip_start, pole_tip_end, 2 * pole_tip_angle)

        # pole lines
        pole_root_radius = self.config['rotor']['shaft_diameter'] / \
            2 + self.config['rotor']['rib_width']
        pole_root_angle = math.asin(
            self.config['rotor']['pole_root_width'] / 2 / pole_root_radius)
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
        shaft_radius = self.config['rotor']['shaft_diameter'] / 2
        shaft_end = (0, shaft_radius)
        shaft_start = polar_point(shaft_radius, -rotor_slot_angle)

        rotor_slice.add_arc(shaft_start, shaft_end, rotor_slot_angle)

        # Radii
        if self.config['rotor']['pole_tip_radius'] > 0:
            rotor_slice.add_radius(
                pole_tip_start, self.config['rotor']['pole_tip_radius'])
            rotor_slice.add_radius(
                pole_tip_end, self.config['rotor']['pole_tip_radius'])

        if self.config['rotor']['pole_root_radius'] > 0:
            rotor_slice.add_radius(
                pole_root_right, self.config['rotor']['pole_root_radius'])
            rotor_slice.add_radius(
                pole_root_left, self.config['rotor']['pole_root_radius'])

        rotor = rotor_slice.circular_pattern((0, 0), self.config['rotor']['poles'])

        # Annotations
        rotor_annotation = rotor_radius / 2
        rotor_label = {
            "name": self.config['rotor']['material'],
            "automesh": self.config['simulation']['automesh'],
            "meshsize": self.config['simulation']['mesh_size'],
            "circuit": 0,
            "group": 1,
            "turns": 0
        }
        rotor.add_label((0, rotor_annotation), rotor_label)

        shaft_label = {
            "name": self.config['rotor']['shaft_material'],
            "automesh": self.config['simulation']['automesh'],
            "meshsize": self.config['simulation']['mesh_size'],
            "circuit": 0,
            "group": 1,
            "turns": 0
        }
        rotor.add_label((0, 0), shaft_label)

        airgap_annotation = (
            rotor_radius + self.config['stator']['inner_diameter'] / 2) / 2
        airgap_label = {
            "name": self.config['simulation']['airgap_material'],
            "automesh": self.config['simulation']['automesh'],
            "meshsize": self.config['simulation']['mesh_size'],
            "circuit": 0,
            "group": 2,
            "turns": 0
        }
        rotor.add_label((0, airgap_annotation), airgap_label)

        return rotor

    def GenerateGeometry(self):
        stator = self.build_stator()
        rotor = self.build_rotor()

        femm.newdocument(0)

        define_problem(self.config)
        load_materials(self.config)
        add_circuits(self.GetCircuits())

        stator.draw()
        rotor.draw()

        femm.mi_saveas(self.femm_file)
        femm.mi_close()

    def GetRotateDiameter(self) -> float:
        return (self.config['rotor']['outer_diameter'] + self.config['stator']['inner_diameter']) / 2
    
    def RotateRotor(self, angle: float):
        femm.mi_selectcircle(0, 0, self.GetRotateDiameter() / 2, 4)
        femm.mi_selectgroup(1)
        femm.mi_moverotate(0, 0, angle)  

    def GetAvgCoilLength(self) -> float:
        tooth_tip_width = self.config['stator']['tooth_tip_width']
        tooth_root_width = self.config['stator']['tooth_root_width']
        winding_outer_radius = self.config['stator']['outer_diameter'] / 2 - self.config['stator']['spine_width']
        tooth_mid_angle = math.asin(
            (tooth_root_width + tooth_tip_width) / 4 / winding_outer_radius)
        
        outer_winding_angle = math.pi / self.config['stator']['slots']

        winding_centerpoint_angle = (outer_winding_angle + tooth_mid_angle) / 2
    
        winding_inner_radius = self.config['stator']['inner_diameter'] / 2 - self.config['stator']['winding_inner_clearance']
        winding_avg_radius = (winding_inner_radius + winding_outer_radius) / 2

        winding_top_length = winding_avg_radius * winding_centerpoint_angle * 2

        total_length_mm =  (winding_top_length + self.config['simulation']['depth']) * 2
        return total_length_mm / 1000

    def GetWindingCrossSection(self) -> float:
        # approximate the winding cross section
        winding_inner_radius = self.config['stator']['inner_diameter'] / 2 - self.config['stator']['winding_inner_clearance']
        tooth_tip_width = self.config['stator']['tooth_tip_width']
        tooth_root_width = self.config['stator']['tooth_root_width']
        winding_outer_radius = self.config['stator']['outer_diameter'] / 2 - self.config['stator']['spine_width']
        #tooth_mid_angle = math.asin(
        #    (tooth_root_width + tooth_tip_width) / 4 / winding_outer_radius)
        
        outer_winding_angle = math.pi / self.config['stator']['slots']
        #winding_angle = outer_winding_angle - tooth_mid_angle

        outer_annulus_area = (winding_outer_radius ** 2) * math.pi * (outer_winding_angle / (2 * math.pi))
        inner_annulus_area = (winding_inner_radius ** 2) * math.pi * (outer_winding_angle / (2 * math.pi))
        
        annulus_area = outer_annulus_area - inner_annulus_area

        rectangle_area = ((tooth_tip_width + tooth_root_width) / 2) * (winding_outer_radius - winding_inner_radius) / 2

        area_estimate_mm2 = annulus_area - rectangle_area
        
        area_estimate_m2 = area_estimate_mm2 / 1e6
        # good 'nuff but will not work as well for low slot counts
        return area_estimate_m2

    def SetFrequency(self, frequency: float):
        config = deepcopy(self.config)
        config['simulation']['frequency'] = frequency
        define_problem(config)


if __name__ == "__main__":
    # TODO: how test?
    filepath = 'test/geometry'
    femm.openfemm()
    try:
        geometry = SrmGeometry(filepath)
        geometry.GenerateGeometry()
        print(geometry.GetAvgCoilLength())
    except Exception as e:
        print(e)
    femm.closefemm()
