from .curve_gen import CurveGen
import math

def BldcTorqueCurve(kv, rpm_max, rm, vbus, ilim):
    output = []
    kt = (3/2) / ((3 ** 0.5) * 2 * math.pi / 60) / kv
    for rpm in range(rpm_max):
        current = (vbus - rpm / kv) / rm
        if current > ilim:
            current = ilim
        output.append(max(kt * current, 0))
    
    return output

class BldcCurveGen(CurveGen):
    def __init__(self, kv, rm, vbus, ilim):
        self.kv = kv
        self.rm = rm
        self.vbus = vbus
        self.ilim = ilim
    
    @property
    def kt(self):
        return (3/2) / ((3 ** 0.5) * 2 * math.pi / 60) / self.kv