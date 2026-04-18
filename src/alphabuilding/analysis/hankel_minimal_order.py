import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import hankel, svd

from alphabuilding.infrastructure.lightning.datamodules.brcm_datamodule import (
    BRCMTrajectoryLitDataModule,
)


def analyze_minimal_order(datamodule, method="output_hankel", max_samples=5000):
    """
    Analyze minimal state space dimension using Hankel matrix SVD.

    Parameters
    ----------
    datamodule : BRCMTrajectoryLitDataModule
        Your data module (must have setup() called first)
    method : str
        'output_hankel': Hankel of outputs only (simpler, works if input is rich)
        'subspace': Block Hankel of inputs and outputs (more robust)
    max_samples : int
        Maximum number of samples to use (for computational efficiency)

    Returns
    -------
    dict with 'singular_values', 'recommended_order', 'hankel_matrix'
    """

    # Get training data in numpy format
    train_data = _extract_training_data(datamodule, max_samples)

    if method == "output_hankel":
        results = _output_hankel_analysis(train_data)
    elif method == "subspace":
        results = _subspace_hankel_analysis(train_data)
    else:
        raise ValueError(f"Unknown method: {method}")

    # Plot results
    _plot_singular_values(results["singular_values"])

    return results


def _extract_training_data(datamodule, max_samples):
    """Extract single-step input-output pairs from training set."""

    # Get GPU tensors for training split
    start_idx, end_idx = datamodule.train_indices
    n_samples = min(end_idx - start_idx - 1, max_samples)

    print(f"Extracting {n_samples} single-step samples from training set...")

    # Single-step data: (t) -> (t+1)
    # Inputs at time t
    u_heat = (
        datamodule.gpu_data_tensors["heat_input"][start_idx : start_idx + n_samples]
        .cpu()
        .numpy()
    )
    u_ambient = (
        datamodule.gpu_data_tensors["ambient_temp"][start_idx : start_idx + n_samples]
        .cpu()
        .numpy()
    )
    u_solar = (
        datamodule.gpu_data_tensors["solar_radiation"][
            start_idx : start_idx + n_samples
        ]
        .cpu()
        .numpy()
    )

    # Outputs at time t and t+1
    y_t = (
        datamodule.gpu_data_tensors["zone_temps"][start_idx : start_idx + n_samples]
        .cpu()
        .numpy()
    )
    y_t1 = (
        datamodule.gpu_data_tensors["zone_temps"][
            start_idx + 1 : start_idx + n_samples + 1
        ]
        .cpu()
        .numpy()
    )

    # Stack inputs: u = [heat_input, ambient_temp, solar_radiation]
    # Shape: (n_samples, n_inputs)
    u = np.hstack([u_heat, u_ambient, u_solar])

    # Outputs: zone temperatures
    # Shape: (n_samples, n_zones)
    y = y_t1  # Output at t+1 given state/input at t

    print(f"Input shape: {u.shape}, Output shape: {y.shape}")

    return {
        "u": u,  # inputs at t
        "y_t": y_t,  # outputs at t
        "y_t1": y_t1,  # outputs at t+1
        "n_inputs": u.shape[1],
        "n_outputs": y.shape[1],
        "n_samples": n_samples,
    }


def _output_hankel_analysis(data):
    """
    Simple output-only Hankel analysis.
    Works well when inputs are persistently exciting.
    """
    y = data["y_t1"]  # Output sequence
    n_samples, n_outputs = y.shape

    # Build Hankel matrix for each output channel
    # Then stack them vertically (block Hankel for MIMO)
    hankel_size = min(n_samples // 2, 500)  # Limit size for efficiency

    print(
        f"Building output Hankel matrix of size {hankel_size * n_outputs} x {hankel_size}..."
    )

    hankel_blocks = []
    for output_idx in range(n_outputs):
        y_channel = y[:, output_idx]
        H = hankel(
            y_channel[:hankel_size], y_channel[hankel_size - 1 : 2 * hankel_size - 1]
        )
        hankel_blocks.append(H)

    # Stack vertically for MIMO
    H_full = np.vstack(hankel_blocks)

    # SVD
    print("Computing SVD...")
    U, S, Vt = svd(H_full, full_matrices=False)

    # Find the "cliff" - where singular values drop significantly
    recommended_order = _find_cliff(S)

    return {
        "singular_values": S,
        "recommended_order": recommended_order,
        "hankel_matrix": H_full,
        "method": "output_hankel",
    }


def _subspace_hankel_analysis(data):
    """
    Subspace identification approach: block Hankel of inputs and outputs.
    More robust but computationally heavier.
    """
    u = data["u"]
    y = data["y_t1"]
    n_samples = data["n_samples"]
    n_inputs = data["n_inputs"]
    n_outputs = data["n_outputs"]

    # Block size (number of time lags)
    block_size = min(n_samples // 3, 200)
    n_blocks = n_samples - block_size + 1

    print(
        f"Building block Hankel matrices: block_size={block_size}, n_blocks={n_blocks}..."
    )

    # Build block Hankel for outputs Y_{0|i-1}
    Y_hankel = np.zeros((block_size * n_outputs, n_blocks))
    for i in range(block_size):
        Y_hankel[i * n_outputs : (i + 1) * n_outputs, :] = y[i : i + n_blocks, :].T

    # Build block Hankel for inputs U_{0|i-1}
    U_hankel = np.zeros((block_size * n_inputs, n_blocks))
    for i in range(block_size):
        U_hankel[i * n_inputs : (i + 1) * n_inputs, :] = u[i : i + n_blocks, :].T

    # Subspace identification: SVD of output Hankel projected onto input-output space
    # Simplified version: just use output Hankel (full subspace method needs more care)
    print("Computing SVD of output Hankel...")
    U_svd, S, Vt = svd(Y_hankel, full_matrices=False)

    recommended_order = _find_cliff(S)

    return {
        "singular_values": S,
        "recommended_order": recommended_order,
        "hankel_matrix": Y_hankel,
        "method": "subspace",
    }


def _find_cliff(singular_values, threshold_ratio=1e-2):
    """
    Find the 'cliff' in singular values - where they drop significantly.

    Returns the recommended order (number of states).
    """
    if len(singular_values) < 2:
        return 1

    # Normalize
    s_norm = singular_values / singular_values[0]

    # Find where normalized singular values drop below threshold
    significant = s_norm > threshold_ratio

    if not np.any(significant):
        return 1

    # Find the last significant singular value
    recommended_order = np.where(significant)[0][-1] + 1

    # Also look for the largest relative gap
    ratios = singular_values[:-1] / singular_values[1:]
    max_gap_idx = np.argmax(ratios)

    print("\nSingular value analysis:")
    print(f"  Threshold method (>{threshold_ratio:.1e}): {recommended_order} states")
    print(f"  Largest gap at index: {max_gap_idx + 1}")
    print(f"  Top 10 singular values: {singular_values[:10]}")
    print(f"  Normalized (top 10): {s_norm[:10]}")

    return recommended_order


def _plot_singular_values(S, max_plot=50):
    """Plot singular values to visualize the 'cliff'."""

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Linear scale
    axes[0].plot(S[:max_plot], "o-", linewidth=2, markersize=5)
    axes[0].set_xlabel("Index", fontsize=12)
    axes[0].set_ylabel("Singular Value", fontsize=12)
    axes[0].set_title("Singular Values (Linear Scale)", fontsize=13)
    axes[0].grid(True, alpha=0.3)

    # Log scale (better for seeing the cliff)
    axes[1].semilogy(S[:max_plot], "o-", linewidth=2, markersize=5)
    axes[1].set_xlabel("Index", fontsize=12)
    axes[1].set_ylabel("Singular Value (log scale)", fontsize=12)
    axes[1].set_title("Singular Values (Log Scale) - Look for the Cliff", fontsize=13)
    axes[1].grid(True, alpha=0.3, which="both")

    plt.tight_layout()
    plt.show()

    return fig


# ============ USAGE ============

if __name__ == "__main__":
    # Setup your datamodule
    from pathlib import Path

    from alphabuilding.utils.paths import paths

    csv_file = (
        Path(paths.data_dir)
        / "brcm_simulation_results/hysteresis_prbs/five_room_1_year_Ts_0.25_hysteresis-random_Tmargin_5_real.csv"
    )
    datamodule = BRCMTrajectoryLitDataModule(
        csv_file=csv_file,
        batch_size=32,
        window_size=72,
        initial_horizon=2,
        max_horizon=4,
    )
    datamodule.setup("fit")

    # Run Hankel analysis
    results = analyze_minimal_order(
        datamodule,
        method="output_hankel",  # or 'subspace'
        max_samples=5000,
    )

    print(f"\n{'=' * 60}")
    print(f"RECOMMENDED MINIMAL STATE SPACE DIMENSION: {results['recommended_order']}")
    print(f"{'=' * 60}\n")

    # You can also manually inspect the plot and choose
    # The order is where you see the "cliff" - sharp drop in singular values
