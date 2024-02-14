import matplotlib.pyplot as plt
import numpy as np
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='3d plot')
    parser.add_argument('data_folder', type=str, help='location of data folder')
    args = parser.parse_args()

    # load data
    torque = np.load(args.data_folder + '/torque.npy')
    a_current = np.load(args.data_folder + '/a_current.npy')
    b_current = np.load(args.data_folder + '/b_current.npy')
    angle = np.load(args.data_folder + '/angle.npy')

    num_excluded = 0

    for i in range(angle.shape[0]):
        for j in range(angle.shape[1]):
            if b_current[i][j] != 0:
                torque[i][j] = 0
                a_current[i][j] = 0
                b_current[i][j] = 0
                angle[i][j] = 0
                num_excluded += 1
    
    print(f'excluded {num_excluded} points\n')

    # make 3d
    num_points = angle.shape[0] * angle.shape[1]
    x = np.zeros(num_points)
    y = np.zeros(num_points)
    z = np.zeros(num_points)
    for i in range(angle.shape[0]):
        for j in range(angle.shape[1]):
            x[i * angle.shape[1] + j] = angle[i][j]
            y[i * angle.shape[1] + j] = a_current[i][j]
            z[i * angle.shape[1] + j] = torque[i][j]

    ax = plt.figure().add_subplot(projection='3d')

    # Plot the surface with face colors taken from the array we made.
    surf = ax.scatter(x, y, z, linewidth=0)
    ax.set_xlabel('Angle')
    ax.set_ylabel('Current')
    ax.set_zlabel('Torque')
    #ax.autoscale()

    plt.show()