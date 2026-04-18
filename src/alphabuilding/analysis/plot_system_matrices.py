import logging

import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.colors import CenteredNorm

logger = logging.getLogger(__name__)


def plot_A_and_B_matrices(A_matrix: np.ndarray, B_matrix: np.ndarray):
    assert A_matrix.ndim == 2, "A_matrix must be 2D"
    assert B_matrix.ndim == 2, "B_matrix must be 2D"
    assert A_matrix.shape[0] == B_matrix.shape[0], "Row counts of A and B must match"

    # Compute eigenvalues of A
    eigvals = np.linalg.eigvals(A_matrix)
    eigvals_sorted = np.sort(eigvals.real)[::-1]  # Sort descending, take real part

    # Check stability: all eigenvalues must have negative real parts
    if not np.all(eigvals.real < 0):
        logger.warning(
            "A matrix is not stable.\nEigenvalues:\n%s\nAll real parts must be negative for stability.\n",
            eigvals,
        )

    vmin = min(A_matrix.min(), B_matrix.min())
    vmax = max(A_matrix.max(), B_matrix.max())

    shared_norm = CenteredNorm(vcenter=0, halfrange=max(abs(vmin), abs(vmax)))

    # Calculate figure size based on matrix dimensions for equal pixel size
    A_rows, A_cols = A_matrix.shape
    _, B_cols = B_matrix.shape

    # Determine scale factor
    scale_factor = min(8.0 / max(A_cols, B_cols), 6.0 / A_rows)

    # Determine scale factor
    scale_factor = min(8.0 / max(A_cols, B_cols), 6.0 / A_rows)

    # Calculate subplot widths proportional to matrix columns
    A_width = A_cols * scale_factor
    B_width = B_cols * scale_factor
    total_width = A_width + B_width + 2.0
    height = A_rows * scale_factor + 1.0

    fig = plt.figure(figsize=(total_width, height))
    plt.suptitle(r"$\dot{x} = Ax + Bu$", fontsize=16)

    # cmap = "seismic"
    cmap = "RdBu_r"

    # Create subplots with proportional widths
    gs = fig.add_gridspec(
        1,
        2,
        width_ratios=[A_cols, B_cols],
        left=0.1,
        right=0.85,
        top=0.9,
        bottom=0.1,
    )

    # Plot A matrix
    ax1 = fig.add_subplot(gs[0, 0])
    im1 = ax1.imshow(A_matrix, cmap=cmap, norm=shared_norm, aspect="equal")
    ax1.set_title(f"A (size: {A_matrix.shape[0]}x{A_matrix.shape[1]})")
    ax1.set_xlabel("Columns")
    ax1.set_ylabel("Rows")

    # Add block structure lines to A matrix
    line_color = "black"
    ax1.axhline(y=4.5, color=line_color, linewidth=2, linestyle="-", alpha=0.8)
    ax1.axvline(x=4.5, color=line_color, linewidth=2, linestyle="-", alpha=0.8)

    # Plot B matrix
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.imshow(B_matrix, cmap=cmap, norm=shared_norm, aspect="equal")
    ax2.set_title(f"B (size: {B_matrix.shape[0]}x{B_matrix.shape[1]})")
    ax2.set_xlabel("Columns")
    ax2.set_ylabel("Rows")
    # set x axis ticks to be integers only and at 0 and 5
    ax2.set_xticks([0, 5])

    # Add block structure lines to B matrix
    ax2.axhline(y=4.5, color=line_color, linewidth=2, linestyle="-", alpha=0.8)

    # Add shared colorbar
    cbar_ax = fig.add_axes((0.87, 0.1, 0.03, 0.8))
    fig.colorbar(im1, cax=cbar_ax)

    # Add eigenvalues text
    # eig_text = f"\nEigenvalues of A: {', '.join([f'{v:.3f}' for v in eigvals_sorted])}"
    # fig.text(0.5, 0.02, eig_text, ha="center", fontsize=10, wrap=True)
    n_hidden_states = A_matrix.shape[0] - 5
    plt.savefig(f"A_and_B_matrices_{n_hidden_states}_latent_states.png", dpi=300)

    plt.show()


def plot_histogram_of_A_eigenvalues(dynamics_module: torch.nn.Module):
    # Plot histogram of eigenvalues of A matrix
    A_eigvals = torch.linalg.eigvals(dynamics_module.A_matrix).detach().cpu().numpy()
    A_eigenvals_pos = A_eigvals[A_eigvals.real > 0]
    A_eigenvals_neg = A_eigvals[A_eigvals.real <= 0]
    max_abs = np.max(np.abs(A_eigvals.real))
    bins = np.linspace(-max_abs, max_abs, 21)  # 21 edges for 20 total bins
    # Plot both histograms on the same axes
    plt.figure(figsize=(10, 6))
    plt.hist(
        A_eigenvals_pos,
        bins=bins,
        color="salmon",
        edgecolor="black",
        alpha=0.8,
    )
    plt.hist(
        A_eigenvals_neg,
        bins=bins,
        color="skyblue",
        edgecolor="black",
        alpha=0.8,
    )
    plt.title("$Re(\\lambda(A))$ Histogram")
    plt.xlabel("Real Part of Eigenvalues")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(axis="y", alpha=0.5)
    plt.show()
