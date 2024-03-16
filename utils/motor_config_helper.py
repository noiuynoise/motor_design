import json
import math
import argparse
import os

# from: https://www.powerstream.com/Wire_Size.htm
AWG_DIAMETER = {
    "10 AWG": 2.58826,
    "12 AWG": 2.05232,
    "14 AWG": 1.62814,
    "16 AWG": 1.29032,
    "18 AWG": 1.02362,
    "20 AWG": 0.8128,
    "22 AWG": 0.64516,
    "24 AWG": 0.51054,
    "26 AWG": 0.40386,
    "28 AWG": 0.32004,
    "30 AWG": 0.254,
    "32 AWG": 0.2032,
    "34 AWG": 0.16002,
    "36 AWG": 0.127
}


class MotorConfig:
    def __init__(self, config):
        if type(config) == str:
            if not os.path.isfile(config):
                raise ValueError('config not found')
            with open(config, 'r') as f:
                self.config = json.load(f)
                return
        elif type(config) == dict:
            self.config = config
            return

        raise ValueError('MotorConfig requires either a file or a dictionary')

    def __getitem__(self, key):
        return self.config[key]

    @property
    def termination_type(self):
        termination = self['winding']['termination']
        if termination != 'parallel' and termination != 'series':
            raise ValueError(f'Unsupported termination type: {termination}')
        return termination

    @property
    def wire_name(self):
        materials = self['materials']
        for material in materials:
            if material['name'] == self['winding']['material']:
                return material['library']

    @property
    def wire_diameter(self):
        if self.wire_name not in AWG_DIAMETER:
            raise ValueError(f'Unsupported wire gauge: {self.wire_name}')
        return AWG_DIAMETER[self.wire_name]

    @property
    def slot_pitch(self):
        return 360 / self['stator']['slots']

    @property
    def pole_pitch(self):
        return 360 / self['rotor']['poles']

    def GetCircuits(self):
        windings = self["winding"]["order"]
        circuit_names = []
        for winding in windings:
            # check that the last character is a + or -
            if winding[-1] != "+" and winding[-1] != "-":
                raise ValueError('winding name must end with + or -')
            if winding[:-1] not in circuit_names:
                circuit_names.append(winding[:-1])
        return circuit_names

    @property
    def num_phases(self):
        return len(list(set(self.GetCircuits())))

    @property
    def coils_per_phase(self):
        return self['stator']['slots'] / self.num_phases

    def EstimateCoilResistance(self):
        COPPER_RESISTIVITY = 1.68e-8
        resistance_per_meter = COPPER_RESISTIVITY / \
            (math.pi * ((self.wire_diameter / 1000 / 2) ** 2))

        # Calculate loop length
        depth = self['simulation']['depth']
        tooth_width = (self['stator']['tooth_tip_width'] +
                       self['stator']['tooth_root_width']) / 2

        # Estimate coil distance over tooth as average of tooth width and width at the pole pitch radius
        stator_center_radius = (self['stator']['inner_diameter'] + self['stator']
                                ['outer_diameter'] - self['stator']['spine_width'] * 2) / 2 / 2
        pole_width = 2 * math.pi / \
            self['stator']['slots'] * stator_center_radius
        over_tooth = (pole_width + tooth_width) / 2

        loop_length = 2 * (depth + over_tooth)

        return resistance_per_meter * (loop_length / 1000) * self['winding']['turns']

    def EstimatePhaseResistance(self):
        if self.termination_type == 'parallel':
            return self.EstimateCoilResistance() / self.coils_per_phase
        else:
            return self.EstimateCoilResistance() * self.coils_per_phase

    def GetCoilCurrent(self, phase_current):
        if self.termination_type == 'parallel':
            return phase_current / self.num_phases
        else:
            return phase_current


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='estimate_params')
    parser.add_argument('file', type=str, help='motor params file')
    args = parser.parse_args()

    config = MotorConfig(args.file)

    print(config.EstimateCoilResistance())
