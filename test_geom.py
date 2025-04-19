import femm
from math import sin, cos, pi
from motor_geometry.pcb_linear_motor.pcb_linear_motor_geometry import PcbLinearMotorGeometry
from simulation.simulate_induction_motor import simulate_induction_motor
import json

if __name__ == "__main__":
    geometry = PcbLinearMotorGeometry('test/geometry')
    femm.openfemm()
    geometry.GenerateGeometry()
    # currents = {}
    # for i in range(3):
    #     currents[chr(ord('A') + i)] = cos(i * 2 * pi / 3) + 1j * sin(i * 2 * pi / 3)
    # output = simulate_induction_motor(geometry, 10000, currents, image_path = 'test/results/output.png', temp_path='test')
    # with open('test/results/output.json', 'w') as f:
    #     f.write(json.dumps(output, indent=1))
    # print(json.dumps(output, indent=1))
    femm.closefemm()