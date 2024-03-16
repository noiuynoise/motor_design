#!/bin/python3
import os

if __name__ == '__main__':
    folders = os.listdir('complete_runs')
    last_run = 0
    for folder in folders:
        if folder[:4] == 'run_':
            last_run = max(last_run, int(folder[4:]))
    print(f'runs/run_{last_run + 1}')