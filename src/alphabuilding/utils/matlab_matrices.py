import numpy as np
import scipy.io

from analysis.plot_2D_matrix import plot_2d_matrix
from analysis.plot_system_matrices import plot_A_and_B_matrices

# Load the specific struct


def get_matlab_conductance_matrix(data_file: str):
    data = scipy.io.loadmat(data_file)
    capacitance_matrix = data["capacitances"]

    return capacitance_matrix


def get_matlab_A_and_Bu_matrices(data_file: str):
    data = scipy.io.loadmat(data_file)
    model = data["continuous_time_model"]

    for key in model.dtype.names:
        array = model[key][0, 0]
        print(f"{key}: {array.shape}")
        sum_of_absolute_elements = abs(array.flatten()).sum()
        print(f"Sum of absolute elements in {key}: {sum_of_absolute_elements}\n")

    A_matrix = model["A"][0, 0]
    Bu_matrix = model["Bu"][0, 0]
    return A_matrix, Bu_matrix


if __name__ == "__main__":
    # AB_data_file = "/home/l2late/stack/Master/Thesis/master-thesis-code/alpha_building_model/matlab/cdc-feedback-es/buildings/continuous_time_model.mat"
    # A_matrix, Bu_matrix = get_matlab_A_and_Bu_matrices(AB_data_file)
    # plot_A_and_B_matrices(A_matrix, Bu_matrix)
    print("Plotted A and Bu matrices from MATLAB struct.")

    Caps_data_file = "/home/l2late/stack/Master/Thesis/master-thesis-code/alpha_building_model/matlab/cdc-feedback-es/buildings/capacitances.mat"
    capacitance_matrix = get_matlab_conductance_matrix(Caps_data_file)
    plot_2d_matrix(capacitance_matrix)
    print("Plotted capacitance matrix from MATLAB struct.")
    average_capacitance = np.diag(capacitance_matrix).mean()
    print(f"Average capacitance (diagonal mean): {average_capacitance}")
    min_capacitance = np.diag(capacitance_matrix).min()
    print(f"Minimum capacitance (diagonal min): {min_capacitance}")
    max_capacitance = np.diag(capacitance_matrix).max()
    print(f"Maximum capacitance (diagonal max): {max_capacitance}")

    # plot histogram of capacitances distribution, using N bins with exponentially increasing bin sizes
    N = 20
    bins = np.logspace(np.log10(min_capacitance), np.log10(max_capacitance), N)
    import matplotlib.pyplot as plt

    plt.figure(figsize=(8, 6))
    plt.hist(np.diag(capacitance_matrix), bins=bins, edgecolor="black")
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Capacitance (log scale)")
    plt.ylabel("Frequency (log scale)")
    plt.title("Histogram of Capacitance Distribution")
    plt.grid(True, which="both", ls="--", lw=0.5)
    plt.show()
