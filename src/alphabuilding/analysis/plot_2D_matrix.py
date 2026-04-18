import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import CenteredNorm


def plot_2d_matrix(matrix: np.ndarray):
    assert matrix.ndim == 2, "A_matrix must be 2D"

    # Compute eigenvalues of A
    eigvals = np.linalg.eigvals(matrix)
    eigvals_sorted = np.sort(eigvals.real)[::-1]  # Sort descending, take real part

    vmin = matrix.min()
    vmax = matrix.max()

    shared_norm = CenteredNorm(vcenter=0, halfrange=max(abs(vmin), abs(vmax)))

    # Calculate figure size based on matrix dimensions for equal pixel size
    rows, cols = matrix.shape

    # Determine scale factor
    scale_factor = min(8.0 / cols, 6.0 / rows)

    # Calculate subplot widths proportional to matrix columns
    width = cols * scale_factor
    total_width = width + 2.0
    height = rows * scale_factor + 1.0

    fig = plt.figure(figsize=(total_width, height))
    plt.suptitle(r"$\dot{x} = Ax + Bu$", fontsize=16)

    cmap = "seismic"

    # Create subplots with proportional widths
    gs = fig.add_gridspec(
        1,
        2,
        width_ratios=[cols, 0],
        left=0.1,
        right=0.85,
        top=0.9,
        bottom=0.1,
    )

    # Plot A matrix
    ax1 = fig.add_subplot(gs[0, 0])
    im1 = ax1.imshow(matrix, cmap=cmap, norm=shared_norm, aspect="equal")
    ax1.set_title(f"Matrix (size: {matrix.shape[0]}x{matrix.shape[1]})")
    ax1.set_xlabel("Columns")
    ax1.set_ylabel("Rows")

    # Add block structure lines to A matrix
    line_color = "lime"
    ax1.axhline(y=4.5, color=line_color, linewidth=2, linestyle="-", alpha=0.8)
    ax1.axvline(x=4.5, color=line_color, linewidth=2, linestyle="-", alpha=0.8)

    # Add shared colorbar
    cbar_ax = fig.add_axes((0.87, 0.1, 0.03, 0.8))
    fig.colorbar(im1, cax=cbar_ax)

    # Add eigenvalues text
    print(f"Eigenvalues: {eigvals_sorted}")
    # eig_text = f"Eigenvalues : {', '.join([f'{v:.3f}' for v in eigvals_sorted])}"
    # fig.text(0.5, 0.02, eig_text, ha="center", fontsize=10, wrap=True)

    plt.show()
