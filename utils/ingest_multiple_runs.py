import os
import argparse
import json
import numpy as np

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='data ingest')
    parser.add_argument('run_location', type=str, help='location of run folder')
    args = parser.parse_args()

    run_folders = os.listdir(args.run_location)
    num_folders = sum([1 if os.path.isdir(args.run_location + '/' + x) else 0 for x in run_folders])
    print(f'ingesting {num_folders} folders\n')

    # figure out what the array dimensions should be
    num_angle_steps = None
    combined_data = None

    num_folders = 0

    for run_folder in run_folders:
        run_location = args.run_location + '/' + run_folder
        if not os.path.isdir(run_location):
            print(f'{run_location} is not a directory. Skipping\n')
            continue
        
        file_to_ingest = None
        if os.path.isfile(run_location + '/results.json'):
            file_to_ingest = run_location + '/results.json'
        elif os.path.isdir(run_location + '/test'):
            if os.path.isfile(run_location + '/test/results.json'):
                file_to_ingest = run_location + '/test/results.json'
        
        if file_to_ingest is None:
            print(f'error: {run_location} does not contain results.json. Skipping\n')
            continue

        file = open(file_to_ingest, 'r')
        data = json.loads(file.read())

        if combined_data is None:
            combined_data = {}
            num_angle_steps = len(data)
            for key in data[0].keys():
                if isinstance(data[0][key], dict):
                    for key2 in data[0][key].keys():
                        combined_data[key + '_' + key2] = np.empty((0, num_angle_steps), np.double)
                else:
                    combined_data[key] = np.empty((0, num_angle_steps), np.double)
            continue

        if num_angle_steps != len(data):
            print(f'error: {run_location} has {len(data)} angle steps, expected {num_angle_steps}. Skipping\n')
            continue
        
        for key in data[0].keys():
            if isinstance(data[0][key], dict):
                for key2 in data[0][key].keys():
                    combined_data[key + '_' + key2] = np.append(combined_data[key + '_' + key2], np.array([[data[i][key][key2] for i in range(num_angle_steps)]]), axis=0)
            else:
                combined_data[key] = np.append(combined_data[key], np.array([[data[i][key] for i in range(num_angle_steps)]]), axis=0)

        num_folders = num_folders + 1

    print(f'ingested {num_folders} runs\n')

    if not os.path.isdir(args.run_location + '/combined'):
        os.mkdir(args.run_location + '/combined')

    for key in combined_data.keys():
        try:
            os.remove(args.run_location + '/combined/' + key + '.npy')
        except:
            pass
        np.save(args.run_location + '/combined/' + key + '.npy', combined_data[key])
        print(f'{key}: {combined_data[key].shape}')
    
    # sort into angle / current A / current B array
    a_step = 0.5
    b_step = 0.5
    angle_step = 1

    a_max = 20
    b_max = 20
    angle_max = 90

    a_current = np.ndarray.flatten(combined_data['a_current'])
    b_current = np.ndarray.flatten(combined_data['b_current'])
    angle = np.ndarray.flatten(combined_data['angle'])

    flattened_data = {}
    ordered_data = {}

    for key in combined_data.keys():
        if key == 'a_current' or key == 'b_current' or key == 'angle':
            continue
        flattened_data[key] = np.ndarray.flatten(combined_data[key])
        ordered_data[key] = np.empty((int(a_max / a_step), int(b_max / b_step), int(angle_max / angle_step)), np.double)

    for i in range(len(a_current)):
        for key in combined_data.keys():
            if key == 'a_current' or key == 'b_current' or key == 'angle':
                continue
            a_current_index = int(a_current[i] / a_step)
            b_current_index = int(b_current[i] / b_step)
            angle_index = int(angle[i] / angle_step)
            ordered_data[key][a_current_index, b_current_index, angle_index] = flattened_data[key][i]

    for key in ordered_data.keys():
        try:
            os.remove(args.run_location + '/combined/' + key + '_ordered.npy')
        except:
            pass
        np.save(args.run_location + '/combined/' + key + '_ordered.npy', ordered_data[key])
        


        

    
