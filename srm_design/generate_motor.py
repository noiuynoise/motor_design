import femm
import os
import json
import math

from typing import Dict, Any, List

PRECISION = 1e-6

class Line:
    def __init__(self, start: tuple[float, float], end: tuple[float, float]):
        self.start = start
        self.end = end

class Arc:
    def __init__(self, start: tuple[float, float], end: tuple[float, float], angle: float):
        self.start = start
        self.end = end
        self.angle = angle

# Rotate a point around a center point by a given angle counterclockwise
def rotate_point(point: tuple[float, float], center: tuple[float, float], angle: float) -> tuple[float, float]:
    rot_x = point[0] - center[0]
    rot_y = point[1] - center[1]
    new_x = rot_x * math.cos(angle) - rot_y * math.sin(angle)
    new_y = rot_x * math.sin(angle) + rot_y * math.cos(angle)
    return (new_x + center[0], new_y + center[1])

# polar point - angle is counterclockwise from the y-axis
def polar_point(radius: float, angle: float) -> tuple[float, float]:
    return rotate_point((0, radius), (0, 0), angle)

class GeometryCollection:
    def __init__(self):
        self.points = []
        self.arcs = []
        self.lines = []
        self.labels = []
        self.radii = []
    
    def add_radius(self, point: tuple[float, float], radius: float):
        self.radii.append((point, radius))

    def add_label(self, point: tuple[float, float], text: str):
        self.labels.append((point, text))

    def add_point(self, point: tuple[float, float]):
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
    
    def add_line(self, start: tuple[float, float], end: tuple[float, float]):
        self.add_line_obj(Line(start, end))

    def add_arc_obj(self, arc: Arc):
        self.add_point(arc.start)
        self.add_point(arc.end)
        self.arcs.append(arc)

    # positive angle is counterclockwise points from start to end
    def add_arc(self, start: tuple[float, float], end: tuple[float, float], angle: float):
        self.add_arc_obj(Arc(start, end, angle))
    
    def circular_pattern(self, center: tuple[float, float], count: int):
        output = GeometryCollection()
        for i in [x * 2 * math.pi / count for x in range(count)]:
            for point in self.points:
                output.add_point(rotate_point(point, center, i))
            for line in self.lines:
                output.add_line(rotate_point(line.start, center, i), rotate_point(line.end, center, i))
            for arc in self.arcs:
                output.add_arc(rotate_point(arc.start, center, i), rotate_point(arc.end, center, i), arc.angle)
            for label in self.labels:
                output.add_label(rotate_point(label[0], center, i), label[1])
            for radius in self.radii:
                output.add_radius(rotate_point(radius[0], center, i), radius[1])
        return output
    
    def draw(self):
        for point in self.points:
            femm.mi_clearselected()
            femm.mi_addnode(point[0], point[1])
        for line in self.lines:
            femm.mi_clearselected()
            femm.mi_addsegment(line.start[0], line.start[1], line.end[0], line.end[1])
        for arc in self.arcs:
            femm.mi_clearselected()
            angle = arc.angle * 180 / math.pi
            if angle < 0:
                femm.mi_addarc(arc.end[0], arc.end[1], arc.start[0], arc.start[1], -angle, 1)
            else:
                femm.mi_addarc(arc.start[0], arc.start[1], arc.end[0], arc.end[1], angle, 1)
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
            femm.mi_setblockprop(label[1]['name'], automesh, label[1]['meshsize'], label[1]['circuit'], 0, label[1]['group'], label[1]['turns'])

def add_winding_labels(config, points, geometry):
    order = config['winding']['order']
    if len(order) != len(points):
        raise ValueError('winding order does not match number of winding points')
    base_label = {
        "name": config['winding']['material'],
        "automesh": config['simulation']['automesh'],
        "meshsize": config['simulation']['mesh_size'],
        "circuit": 0,
        "group": 2,
        "turns": config['winding']['turns']
    }
    for i in range(len(order)):
        winding = order[i]
        label = base_label.copy()
        label['circuit'] = winding[:-1]
        if winding[-1] == '-':
            label['turns'] = -label['turns']
        geometry.add_label(points[i], label)


def build_stator(config) -> GeometryCollection:
    stator_slice = GeometryCollection()
    stator_slot_angle = 2 * math.pi / config['stator']['slots']
    
    # OD curve
    outer_radius = config['stator']['outer_diameter'] / 2
    od_end = (0, outer_radius)
    od_start = polar_point(outer_radius, -stator_slot_angle)
    stator_slice.add_arc(od_start, od_end, stator_slot_angle)
    
    # ID curves
    tooth_curve_angle = math.asin(config['stator']['tooth_tip_width'] / (config['stator']['inner_diameter']))

    inner_radius = config['stator']['inner_diameter'] / 2
    id1_end = (0, inner_radius)
    id1_start = polar_point(inner_radius, -tooth_curve_angle)

    id2_start = polar_point(inner_radius, -stator_slot_angle)
    id2_end = polar_point(inner_radius, -stator_slot_angle + tooth_curve_angle)

    stator_slice.add_arc(id1_start, id1_end, tooth_curve_angle)
    stator_slice.add_arc(id2_start, id2_end, tooth_curve_angle)

    # Teeth
    spine_radius = config['stator']['outer_diameter'] / 2 - config['stator']['spine_width']
    tooth_root_angle = math.asin(config['stator']['tooth_root_width'] / 2 / spine_radius)

    tooth1_start = id1_start
    tooth1_end = polar_point(spine_radius, -tooth_root_angle)

    tooth2_start = id2_end
    tooth2_end = polar_point(spine_radius, -stator_slot_angle + tooth_root_angle)

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
    stator_slice.add_arc(id1_start, coil_line_end, -stator_slot_angle / 2 + tooth_curve_angle)
    stator_slice.add_arc(coil_line_end, id2_end, -stator_slot_angle / 2 + tooth_curve_angle)

    # Air simulation boundary
    air_radius = config['simulation']['outer_diameter'] / 2
    stator_slice.add_arc((0, air_radius), polar_point(air_radius, stator_slot_angle), stator_slot_angle)

    # Radii
    if config['stator']['tooth_root_radius'] > 0:
        stator_slice.add_radius(tooth1_end, config['stator']['tooth_root_radius'])
        stator_slice.add_radius(tooth2_end, config['stator']['tooth_root_radius'])
    
    if config['stator']['tooth_tip_radius'] > 0:
        raise NotImplementedError('tooth tip radius not yet supported')
        stator_slice.add_radius(tooth1_start, config['stator']['tooth_tip_radius'])
        stator_slice.add_radius(tooth2_start, config['stator']['tooth_tip_radius'])

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
            polar_point(winding_annotation_radius, -i * stator_slot_angle + ((stator_slot_angle / 2) + tooth_curve_angle) / 2)
        )
        winding_annotations.append(
            polar_point(winding_annotation_radius, -i * stator_slot_angle - ((stator_slot_angle / 2) + tooth_curve_angle) / 2)
        )
    add_winding_labels(config, winding_annotations, stator)

    return stator

def build_rotor(config) -> GeometryCollection:
    rotor_slice = GeometryCollection()
    rotor_slot_angle = 2 * math.pi / config['rotor']['poles']

    # tip curve
    rotor_radius = config['rotor']['outer_diameter'] / 2
    pole_tip_angle = math.asin(config['rotor']['pole_tip_width'] / 2 / rotor_radius)
    pole_tip_start = polar_point(rotor_radius, -pole_tip_angle)
    pole_tip_end = polar_point(rotor_radius, pole_tip_angle)
    rotor_slice.add_arc(pole_tip_start, pole_tip_end, 2 * pole_tip_angle)

    # pole lines
    pole_root_radius = config['rotor']['shaft_diameter'] / 2 + config['rotor']['rib_width']
    pole_root_angle = math.asin(config['rotor']['pole_root_width'] / 2 / pole_root_radius)
    pole_root_right = polar_point(pole_root_radius, -pole_root_angle)
    pole_root_left = polar_point(pole_root_radius, pole_root_angle)

    rotor_slice.add_line(pole_tip_start, pole_root_right)
    rotor_slice.add_line(pole_tip_end, pole_root_left)

    # rib arcs
    rib_arc_angle = -rotor_slot_angle + 2 * pole_root_angle
    rib_arc_end = polar_point(pole_root_radius, rib_arc_angle - pole_root_angle)

    rotor_slice.add_arc(pole_root_right, rib_arc_end, rib_arc_angle)

    # shaft
    shaft_radius = config['rotor']['shaft_diameter'] / 2
    shaft_end = (0, shaft_radius)
    shaft_start = polar_point(shaft_radius, -rotor_slot_angle)

    rotor_slice.add_arc(shaft_start, shaft_end, rotor_slot_angle)

    # Radii
    if config['rotor']['pole_tip_radius'] > 0:
        rotor_slice.add_radius(pole_tip_start, config['rotor']['pole_tip_radius'])
        rotor_slice.add_radius(pole_tip_end, config['rotor']['pole_tip_radius'])
    
    if config['rotor']['pole_root_radius'] > 0:
        rotor_slice.add_radius(pole_root_right, config['rotor']['pole_root_radius'])
        rotor_slice.add_radius(pole_root_left, config['rotor']['pole_root_radius'])

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

    airgap_annotation = (rotor_radius + config['stator']['inner_diameter'] / 2) / 2
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

def load_materials(config):
    for material in config['materials']:
        if 'library' in material:
            femm.mi_getmaterial(material['library'])
            femm.mi_modifymaterial(material['library'], 0, material['name'])
        else:
            raise NotImplementedError('custom materials not yet supported')

def add_circuits(config) -> List[str]:
    windings = config["winding"]["order"]
    circuit_names = []
    for winding in windings:
        # check that the last character is a + or -
        if winding[-1] != "+" and winding[-1] != "-":
            raise ValueError('winding name must end with + or -')
        if winding[:-1] not in circuit_names:
            circuit_names.append(winding[:-1])
    
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
    femm.mi_probdef(freq, units, problem_type, precision, depth, min_angle, solver)

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


if __name__ == "__main__":
    filepath = 'motor_config.json'
    if not os.path.isfile(filepath):
        raise ValueError('config not found')
    
    config_json = open(filepath, 'r')

    config = json.loads(config_json.read())
    print(generate_motor(config, 'motor.FEM'))