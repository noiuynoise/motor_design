#!/bin/python3

import femm
import math

from typing import List, Tuple
from utils.motor_config_helper import MotorConfig

PRECISION = 1e-6


class Line:
    def __init__(self, start: Tuple[float, float], end: Tuple[float, float]):
        self.start = start
        self.end = end


class Arc:
    def __init__(self, start: Tuple[float, float], end: Tuple[float, float], angle: float):
        self.start = start
        self.end = end
        self.angle = angle


def rotate_point(point: Tuple[float, float], center: Tuple[float, float], angle: float) -> Tuple[float, float]:
    # Rotate a point around a center point by a given angle counterclockwise
    rot_x = point[0] - center[0]
    rot_y = point[1] - center[1]
    new_x = rot_x * math.cos(angle) - rot_y * math.sin(angle)
    new_y = rot_x * math.sin(angle) + rot_y * math.cos(angle)
    return (new_x + center[0], new_y + center[1])


def polar_point(radius: float, angle: float) -> Tuple[float, float]:
    # polar point - angle is counterclockwise from the y-axis
    return rotate_point((0, radius), (0, 0), angle)


class GeometryCollection:
    def __init__(self):
        self.points = []
        self.arcs = []
        self.lines = []
        self.labels = []
        self.radii = []

    def add_radius(self, point: Tuple[float, float], radius: float):
        self.radii.append((point, radius))

    def add_label(self, point: Tuple[float, float], text: str):
        self.labels.append((point, text))

    def add_point(self, point: Tuple[float, float]):
        match = False
        for p in self.points:
            if math.fabs(p[0] - point[0]) < PRECISION and math.fabs(p[1] - point[1]) < PRECISION:
                match = True
                break
        if not match:
            self.points.append(point)

    def add_line_obj(self, line: Line):
        self.add_point(line.start)
        self.add_point(line.end)
        self.lines.append(line)

    def add_line(self, start: Tuple[float, float], end: Tuple[float, float]):
        self.add_line_obj(Line(start, end))

    def add_arc_obj(self, arc: Arc):
        self.add_point(arc.start)
        self.add_point(arc.end)
        self.arcs.append(arc)

    # positive angle is counterclockwise points from start to end
    def add_arc(self, start: Tuple[float, float], end: Tuple[float, float], angle: float):
        self.add_arc_obj(Arc(start, end, angle))

    def circular_pattern(self, center: Tuple[float, float], count: int):
        output = GeometryCollection()
        for i in [x * 2 * math.pi / count for x in range(count)]:
            for point in self.points:
                output.add_point(rotate_point(point, center, i))
            for line in self.lines:
                output.add_line(rotate_point(line.start, center, i),
                                rotate_point(line.end, center, i))
            for arc in self.arcs:
                output.add_arc(rotate_point(arc.start, center, i),
                               rotate_point(arc.end, center, i), arc.angle)
            for label in self.labels:
                output.add_label(rotate_point(label[0], center, i), label[1])
            for radius in self.radii:
                output.add_radius(rotate_point(
                    radius[0], center, i), radius[1])
        return output

    def draw(self):
        for point in self.points:
            femm.mi_clearselected()
            femm.mi_addnode(point[0], point[1])
        for line in self.lines:
            femm.mi_clearselected()
            femm.mi_addsegment(
                line.start[0], line.start[1], line.end[0], line.end[1])
        for arc in self.arcs:
            femm.mi_clearselected()
            angle = arc.angle * 180 / math.pi
            if angle < 0:
                femm.mi_addarc(arc.end[0], arc.end[1],
                               arc.start[0], arc.start[1], -angle, 1)
            else:
                femm.mi_addarc(arc.start[0], arc.start[1],
                               arc.end[0], arc.end[1], angle, 1)
        for radius in self.radii:
            femm.mi_clearselected()
            femm.mi_createradius(radius[0][0], radius[0][1], radius[1])
        for label in self.labels:
            femm.mi_clearselected()
            femm.mi_addblocklabel(label[0][0], label[0][1])
            femm.mi_selectlabel(label[0][0], label[0][1])
            automesh = 0
            if label[1]['automesh']:
                automesh = 1
            femm.mi_setblockprop(label[1]['name'], automesh, label[1]['meshsize'],
                                 label[1]['circuit'], 0, label[1]['group'], label[1]['turns'])


def add_winding_labels(config, points, geometry):
    order = config['winding']['order']
    if len(order) != len(points):
        raise ValueError(
            'winding order does not match number of winding points')
    base_label = {
        "name": config['winding']['material'],
        "automesh": config['simulation']['automesh'],
        "meshsize": config['simulation']['mesh_size'],
        "circuit": 0,
        "group": 2,
        # Turns is set to 1 so that we can use amp-turn units for driving the motor
        "turns": 1
        #"turns": config['winding']['turns']
    }
    for i in range(len(order)):
        winding = order[i]
        label = base_label.copy()
        label['circuit'] = winding[:-1]
        if winding[-1] == '-':
            label['turns'] = -label['turns']
        geometry.add_label(points[i], label)


def load_materials(config):
    for material in config['materials']:
        if 'library' in material:
            femm.mi_getmaterial(material['library'])
            femm.mi_modifymaterial(material['library'], 0, material['name'])
            if 'saturation' in material:
                femm.mi_addbhpoint(
                    material['name'], material['saturation'], 1e10)
        else:
            raise NotImplementedError('custom materials not yet supported')


def add_circuits(config) -> List[str]:
    circuit_names = list(set(config.GetCircuits()))

    for name in circuit_names:
        femm.mi_addcircprop(name, 0, 1)

    return circuit_names


def define_problem(config):
    freq = config['simulation']['frequency']
    units = config['simulation']['units']
    problem_type = config['simulation']['problem_type']
    precision = config['simulation']['precision']
    depth = config['simulation']['depth']
    min_angle = config['simulation']['min_angle']
    solver = config['simulation']['solver']
    femm.mi_probdef(freq, units, problem_type,
                    precision, depth, min_angle, solver)


def load_materials(config):
    for material in config['materials']:
        if 'library' in material:
            femm.mi_getmaterial(material['library'])
            femm.mi_modifymaterial(material['library'], 0, material['name'])
            if 'saturation' in material:
                femm.mi_addbhpoint(
                    material['name'], material['saturation'], 1e10)
        else:
            raise NotImplementedError('custom materials not yet supported')
