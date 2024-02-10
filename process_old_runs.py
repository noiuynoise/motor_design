import femm
import os
import json
import analysis.make_plots

if __name__ == "__main__":
    for i in range(4, 10):
        width = i / 2
        test_folder = f'old_runs/test_i_{width}'
        file = open(test_folder + '/results.json', 'r')
        results = json.loads(file.read())
        analysis.make_plots.plot_flux_linkage(results, test_folder + '/flux.png', title = f'test {width} flux linkage')
        analysis.make_plots.plot_torque(results, test_folder + '/torque.png', title = f'test {width} torque')
        analysis.make_plots.plot_max_torque(results, test_folder + '/max_torque.png', title = f'test {width} maximum torque')
        