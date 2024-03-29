
from typing import Tuple, List

# Get the min and max flux values in the simulation. Remeber that this must be divided by current to get the inductance (for driven coils)
def GetFluxPeaks(results, phase) -> Tuple[float, float]:
    min_result = min([result[phase]['flux'] for result in results])
    max_result = max([result[phase]['flux'] for result in results])
    return (min_result, max_result)

def GetDrivenTorque(results, phase_shift, num_phases) -> List[float]:
    result_length = len(results)
    output = [0] * result_length
    for index in range(result_length):
        for phase in range(num_phases):
            output[index] = max(output[index], results[int((index + phase_shift * phase) % result_length)]['torque'])
    return output