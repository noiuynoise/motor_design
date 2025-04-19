import json
import matplotlib.pyplot as plt
import argparse

def plot_force(run_folder: str):
    with open(run_folder + '/results.json', 'r') as f:
        results = json.load(f)
    rotor_force = results['rotor_weight'] / 1000 * 9.81
    frequencies = [result['frequency'] for result in results['data']]
    force_x = [result['force_x'] for result in results['data']]
    force_y = [result['force_y'] for result in results['data']]
    plt.plot(frequencies, force_x, label='force_x')
    plt.plot(frequencies, force_y, label='force_y')
    plt.plot(frequencies, [rotor_force] * len(frequencies), label='rotor_force')
    x_min_idx = force_x.index(min(force_x))
    plt.axvline(frequencies[x_min_idx], color='r', linestyle='--')
    ax = plt.gca()
    ax.set_xscale('log')
    plt.legend()
    plt.xlabel('frequency (Hz)')
    plt.ylabel('force (N)')
    plt.title('Force vs Frequency')
    print(f'X max at {frequencies[x_min_idx]} Hz')
    print(f'Y force {force_y[x_min_idx]} N')
    print(f'X force {force_x[x_min_idx]} N')
    print(f'({force_x[x_min_idx] / rotor_force * 100}%)')
    STATOR_LENGTH = 90
    print(f'voltage {(results["data"][x_min_idx]["circuits"]["A"]["voltage_re"] ** 2 + results["data"][x_min_idx]["circuits"]["A"]["voltage_im"] ** 2) ** 0.5 * STATOR_LENGTH / results["stator_length"]}')
    print(f'current {(results["data"][x_min_idx]["circuits"]["A"]["current_re"] ** 2 + results["data"][x_min_idx]["circuits"]["A"]["current_im"] ** 2) ** 0.5}')
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='induction force plotter')
    parser.add_argument('run_folder', type=str, help='run folder to plot from')
    args = parser.parse_args()
    plot_force(args.run_folder)