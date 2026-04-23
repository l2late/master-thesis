import json
from pathlib import Path

import lightning as L
import matplotlib.pyplot as plt
import numpy as np
import torch
from hydra.utils import instantiate
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from numpy.linalg import cond, matrix_power, matrix_rank
from omegaconf import OmegaConf
from scipy.linalg import solve_continuous_lyapunov, solve_discrete_lyapunov

from alphabuilding.analysis.plot_dynamics_param_mapping import (
    visualize_dynamics_with_param_mapping,
)
from alphabuilding.analysis.plot_system_matrices import (
    plot_A_and_B_matrices,
    plot_histogram_of_A_eigenvalues,
)
from alphabuilding.analysis.visualize_time_stepper_predictions import plot_predictions

# from infrastructure.lightning.modules.utils import get_latest_ckpt_path
from alphabuilding.models.lightning_modules.utils import (
    direct_multi_stepping_prediction,
)
from alphabuilding.utils.chooser import choose_run_dir
from alphabuilding.utils.instantiation import init_module_trained_from_cfg
from alphabuilding.utils.paths import paths
from alphabuilding.utils.state_space import (
    diagnose_continuous_system,
    discretize_system,
    get_continuous_A_B_C_D_from_dynamics_module,
)


def format_predictions_tensor_dict_to_numpy(results: dict):
    plotting_data = {}

    for key, value in results.items():
        if key == "timestamps":
            plotting_data[key] = (
                results[key].cpu().numpy().astype("int64").astype("datetime64[ns]")
            )
        elif key == "ambient_temp":
            plotting_data[key] = (
                value.detach().squeeze().cpu().numpy()
            )  # 1D tensor so no transpose
        elif key == "solar_radiation":
            plotting_data[key] = (
                value.detach().squeeze().cpu().numpy()
            )  # 1D tensor so no transpose
        else:
            plotting_data[key] = value.detach().squeeze().cpu().numpy().T

    return plotting_data


def plot_initial_states_distribution(
    initial_zone_temps: np.ndarray,
    initial_latent_states: np.ndarray,
    ambient_temp: float,
) -> plt.Figure:
    fig = plt.figure(figsize=(8, 4))
    plt.hist(
        [initial_zone_temps, initial_latent_states, ambient_temp],
        bins=30,
        color=["green", "orange", "blue"],
        label=["Zone Temps", "Latent States", "Ambient Temp"],
    )
    plt.title("Histogram of Initial States")
    plt.xlabel("Temperature (°C)")
    plt.ylabel("Frequency")
    plt.legend()
    return fig


def denormalize_temperature(datamodule: L.LightningDataModule, tensor: torch.Tensor):
    """Denormalize a tensor using the datamodule's scalers."""
    original_preds_shape = tensor.shape
    scaler = datamodule.zone_temp_scaler
    tensor_inverse_transformed = scaler.inverse_transform(tensor.reshape(-1, 1))
    denormalized_tensor = tensor_inverse_transformed.reshape(original_preds_shape)
    return denormalized_tensor


def _compute_auto_zoom_box(
    eigenvalues,
    discrete=False,
    n_zoom=None,
    min_x_span=None,
    min_y_span=None,
    pad_frac=0.25,
):
    eig = np.asarray(eigenvalues)

    if eig.size == 0:
        return None

    # Pick the cluster center automatically:
    # continuous -> poles closest to 0
    # discrete   -> poles closest to 1 + 0j
    target = 1.0 + 0j if discrete else 0.0 + 0j
    score = np.abs(eig - target)

    if n_zoom is None:
        n_zoom = min(max(3, eig.size // 3), 6)

    idx = np.argsort(score)[:n_zoom]
    cluster = eig[idx]

    xr = cluster.real
    yi = cluster.imag

    x0, x1 = xr.min(), xr.max()
    y0, y1 = yi.min(), yi.max()

    xspan = x1 - x0
    yspan = y1 - y0

    # Make sure the inset is visible even if poles are nearly identical
    if min_x_span is None:
        min_x_span = 0.06 if discrete else 0.12
    if min_y_span is None:
        min_y_span = 0.03 if discrete else 0.08

    xspan = max(xspan, min_x_span)
    yspan = max(yspan, min_y_span)

    xmid = 0.5 * (x0 + x1)
    ymid = 0.5 * (y0 + y1)

    hx = 0.5 * xspan * (1 + pad_frac)
    hy = 0.5 * yspan * (1 + pad_frac)

    return (xmid - hx, xmid + hx, ymid - hy, ymid + hy)


def plot_poles_publication(
    eigenvalues,
    title,
    discrete=False,
    add_zoom=True,
    zoom_box=None,
    n_zoom=None,
    figsize=None,
):
    eig = np.asarray(eigenvalues)

    if figsize is None:
        figsize = (8.8, 4.2) if not discrete else (7.4, 4.8)

    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(
        eig.real,
        eig.imag,
        marker="x",
        color="royalblue",
        s=42,
        linewidths=1.3,
        label="Poles",
        zorder=3,
    )

    ax.set_title(title)
    ax.set_xlabel("Real Part")
    ax.set_ylabel("Imaginary Part")
    ax.axhline(0, color="0.35", linewidth=0.7, linestyle="--", zorder=1)
    ax.axvline(0, color="0.35", linewidth=0.7, linestyle="--", zorder=1)
    ax.grid(True, linestyle=":", linewidth=0.6, color="0.75")
    # ax.legend(loc="upper left", frameon=True)

    if discrete:
        theta = np.linspace(0, 2 * np.pi, 400)
        ax.plot(np.cos(theta), np.sin(theta), "k--", linewidth=1.0, label="_nolegend_")
        ax.set_aspect("equal", adjustable="box")

        # Keep the unit circle nicely framed
        ax.set_xlim(min(-1.05, eig.real.min() - 0.05), max(1.1, eig.real.max() + 0.05))
        y_abs = max(1.05, np.max(np.abs(eig.imag)) + 0.05)
        ax.set_ylim(-y_abs, y_abs)
    else:
        # Nice framing for continuous poles
        xpad = 0.25
        ax.set_xlim(eig.real.min() - xpad, max(0.1, eig.real.max() + 0.05))
        y_abs = max(2.0, np.max(np.abs(eig.imag)) + 0.2)
        ax.set_ylim(-y_abs, y_abs)
        ax.set_box_aspect(0.5)

    if add_zoom:
        # Skip auto-zoom if there aren't enough poles to make it meaningful
        if n_zoom is not None and eig.size <= n_zoom + 1 and zoom_box is None:
            add_zoom = False
        if add_zoom and zoom_box is None:
            zoom_box = _compute_auto_zoom_box(eig, discrete=discrete, n_zoom=n_zoom)

        if zoom_box is not None:
            x0, x1, y0, y1 = zoom_box

            # Reserve room on the right for the inset
            fig.subplots_adjust(right=0.68)

            # Place inset fully outside the main axes
            axins = inset_axes(
                ax,
                width="100%",
                height="100%",
                loc="upper left",
                bbox_to_anchor=(1.2, 0.18, 0.28, 0.56),  # (x, y, w, h) in axes coords
                bbox_transform=ax.transAxes,
                borderpad=0,
            )

            axins.scatter(
                eig.real,
                eig.imag,
                marker="x",
                color="royalblue",
                s=42,
                linewidths=1.3,
                zorder=3,
            )
            axins.axhline(0, color="0.35", linewidth=0.5, linestyle="--", zorder=1)
            axins.axvline(0, color="0.35", linewidth=0.5, linestyle="--", zorder=1)
            axins.grid(True, linestyle=":", linewidth=0.5, color="0.8")
            axins.set_xlim(x0, x1)
            axins.set_ylim(y0, y1)
            axins.tick_params(labelsize=8)

            if discrete:
                axins.plot(np.cos(theta), np.sin(theta), "k--", linewidth=0.8)

            # Rectangle + connectors
            indicator = ax.indicate_inset_zoom(axins, edgecolor="0.4", linewidth=0.9)

            # Optional: hide connectors you don't like
            # for c in indicator.connectors:
            #     c.set_linewidth(0.8)
            #     c.set_color("0.4")

    return fig


def plot_continuous_dynamics_poles(dynamics_module: torch.nn.Module) -> plt.Figure:
    A_cont, _, _, _ = get_continuous_A_B_C_D_from_dynamics_module(dynamics_module)
    continuous_poles = np.linalg.eigvals(A_cont)
    print(f"Continuous System Poles:\n{continuous_poles}\n")

    fig = plot_poles_publication(
        continuous_poles,
        "Continuous-Time System Poles",
        discrete=False,
        add_zoom=True,
        n_zoom=4,  # nearest poles to 0
    )
    return fig


def plot_discrete_dynamics_poles(
    dynamics_module: torch.nn.Module, dt_hours: float
) -> plt.Figure:
    import control as ct

    A_cont, B_cont, C, D = get_continuous_A_B_C_D_from_dynamics_module(dynamics_module)
    A_disc, B_disc = discretize_system(A_cont, B_cont, C, dt_hours)

    sys = ct.ss(A_disc, B_disc, C, D, dt=dt_hours)
    discrete_poles = sys.poles()
    print(f"Discrete System Poles:\n{discrete_poles}\n")

    fig = plot_poles_publication(
        discrete_poles,
        "Discrete-Time System Poles",
        discrete=True,
        add_zoom=True,
        n_zoom=4,  # nearest poles to 1
    )
    return fig


def analyze_observer_stability(model):
    # 1. Extract Matrices
    # Physical system matrix A_phys (unscaled)
    A = model.dynamics.A_matrix.detach().cpu().numpy()

    # Observer gain L_raw from the wrapper logic
    # Note: model.observer.gain is (Outputs, States), so we transpose to get (States, Outputs)
    K = model.observer.gain.detach().t().cpu().numpy()

    # Output matrix C (Physical)
    C = model.C.detach().cpu().numpy()

    # TODO: this formula needs to be adjusted to the new filtering observer architecture
    A_cl = A - K @ C

    # Compute Eigenvalues
    cl_observer_poles = np.linalg.eigvals(A_cl)

    # Analyze Stability
    max_real_part = np.max(cl_observer_poles.real).item()
    is_stable = max_real_part < -1e-5

    print(f"Max Real Part of Eigenvalues: {max_real_part:.4f}")
    print(f"Stable: {is_stable}")

    # TODO: this formula needs to be adjusted to the new filtering observer architecture: see above
    plot_poles(cl_observer_poles, "(A - KC) Observer Poles", discrete=False)


def analyze_discrete_controlability_gramian(A_d, B_d, C):
    Wc = solve_discrete_lyapunov(A_d, B_d @ B_d.T)
    cond_ctrb = np.linalg.cond(Wc)

    print("Discrete Gramian Controllability:")
    print(f"  Condition Num: {cond_ctrb:.2e}")
    if cond_ctrb > 1e6:
        print("  ⚠️  Warning: System is practically uncontrollable (ill-conditioned).")

    return cond_ctrb


def analyze_discrete_observability_gramian(A_d, B_d, C):
    Wo = solve_discrete_lyapunov(A_d.T, C.T @ C)
    cond_obsv = np.linalg.cond(Wo)

    print("Discrete Gramian Observability:")
    print(f"  Condition Num: {cond_obsv:.2e}")
    if cond_obsv > 1e6:
        print(
            "  ⚠️  Warning: System is practically unobservable. Observer will struggle."
        )

    return cond_obsv


def analyze_discrete_gramian_properties(A_d, B_d, C):
    return {
        "cond_ctrb": analyze_discrete_controlability_gramian(A_d, B_d, C),
        "cond_obsv": analyze_discrete_observability_gramian(A_d, B_d, C),
    }


def analyze_continuous_gramian_properties(A, B, C):
    # Method 1: Using scipy directly
    Wc = solve_continuous_lyapunov(A, -B @ B.T)
    Wo = solve_continuous_lyapunov(A.T, -C.T @ C)

    cond_ctrb = np.linalg.cond(Wc)
    cond_obsv = np.linalg.cond(Wo)

    print("Continuous Gramian Controllability:")
    print(f"  Condition Num: {cond_ctrb:.2e}")
    if cond_ctrb > 1e6:
        print("  ⚠️  Warning: System is practically uncontrollable (ill-conditioned).")

    print("Continuous Gramian Observability:")
    print(f"  Condition Num: {cond_obsv:.2e}")
    if cond_obsv > 1e6:
        print(
            "  ⚠️  Warning: System is practically unobservable. Observer will struggle."
        )

    return {
        "cond_ctrb": cond_ctrb,
        "cond_obsv": cond_obsv,
    }


def analyze_observability_controlability_properties(A, B, C, label="System"):
    """
    Analyzes observability and controllability of state-space system (A, B, C).

    Args:
        A (np.ndarray): State transition matrix (n x n)
        B (np.ndarray): Input matrix (n x m) - Note: use B (control), not Bd (disturbance)
        C (np.ndarray): Output matrix (p x n)
        label (str): Name for print output
    """
    n = A.shape[0]

    print(f"\n--- {label} Structural Analysis (n={n}) ---")

    # 1. Controllability Matrix: [B, AB, A^2B, ...]
    # We stack them horizontally
    Ctrb = B
    for i in range(1, n):
        Ctrb = np.hstack((Ctrb, matrix_power(A, i) @ B))

    rank_ctrb = matrix_rank(Ctrb)
    cond_ctrb = cond(Ctrb)

    print("Controllability:")
    print(f"  Rank: {rank_ctrb}/{n} " + ("✅" if rank_ctrb == n else "❌"))
    print(f"  Condition Num: {cond_ctrb:.2e}")
    if cond_ctrb > 1e6:
        print("  ⚠️  Warning: System is practically uncontrollable (ill-conditioned).")

    # 2. Observability Matrix: [C; CA; CA^2; ...]
    # We stack them vertically
    Obsv = C
    for i in range(1, n):
        Obsv = np.vstack((Obsv, C @ matrix_power(A, i)))

    rank_obsv = matrix_rank(Obsv)
    cond_obsv = cond(Obsv)

    print("Observability:")
    print(f"  Rank: {rank_obsv}/{n} " + ("✅" if rank_obsv == n else "❌"))
    print(f"  Condition Num: {cond_obsv:.2e}")
    if cond_obsv > 1e6:
        print(
            "  ⚠️  Warning: System is practically unobservable. Observer will struggle."
        )

    return {
        "rank_ctrb": rank_ctrb,
        "cond_ctrb": cond_ctrb,
        "rank_obsv": rank_obsv,
        "cond_obsv": cond_obsv,
    }


def evaluate_model_predictions(
    ckpt_path: Path,
    config_path: Path,
    save_path: Path | None = None,
    start_idx: int = 0,
) -> None:

    if not ckpt_path.exists():
        raise FileNotFoundError(f"Missing checkpoint: {ckpt_path}")
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config: {config_path}")

    cfg = OmegaConf.load(config_path)

    if save_path is None:
        save_path = (
            Path(paths.report_results_dir)
            / f"{cfg.model.topology}_nl_{cfg.model.num_latent_states}"
            / f"lambda_{cfg.model.lambda_eigenvals_stability_penalty}"
            / f"{cfg.datamodule.noise_stds}"
        )
        save_path.mkdir(parents=True, exist_ok=True)
    else:
        assert save_path.is_dir(), "save_path must be a directory"

    print(f"Evaluating model from checkpoint: {ckpt_path}")
    print(f"Using config: {config_path}")
    print(f"Saving results to: {save_path}")

    cfg.paths = paths
    cfg.datamodule.batch_size = 1
    cfg.datamodule.num_workers = 1

    large_batch_cfg = OmegaConf.load(config_path)
    large_batch_cfg.paths = paths
    large_batch_cfg.datamodule.batch_size = 512
    large_batch_cfg.datamodule.num_workers = 1

    if cfg.get("seed"):
        L.seed_everything(cfg.seed)

    datamodule: L.LightningDataModule = instantiate(cfg.datamodule)
    datamodule_test: L.LightningDataModule = instantiate(large_batch_cfg.datamodule)

    # # Untrained Model
    # module = instantiate(cfg.model)
    module = init_module_trained_from_cfg(cfg, ckpt_path)
    # visualize_dynamics_with_param_mapping(module.dynamics)

    continuous_system_poles = plot_continuous_dynamics_poles(module.dynamics)
    continuous_system_poles.savefig(save_path / "continuous_system_poles.pdf", dpi=300)

    discrete_system_poles = plot_discrete_dynamics_poles(module.dynamics, dt_hours=0.25)
    discrete_system_poles.savefig(save_path / "discrete_system_poles.pdf", dpi=300)

    A_c, B_c, C, D = get_continuous_A_B_C_D_from_dynamics_module(module.dynamics)
    # if hasattr(module, "observer"):
    #     analyze_observer_stability(module)

    # TODO: add norm of learned K matrix: hypothesis: larger noise, larger K gain to reject noise

    # plot_histogram_of_A_eigenvalues(module.dynamics)

    dt_hours = 0.25  # 15 minutes in hours
    # diagnose_continuous_system(A_c, B_c, dt_hours)
    A_d, B_d = discretize_system(A_c, B_c, C, dt_hours=dt_hours)
    # plot_A_and_B_matrices(A_c, B_c)
    # plot_A_and_B_matrices(A_d, B_d)

    datamodule.setup("test")
    datamodule_test.setup("test")

    test_dataloader = datamodule.test_dataloader()

    trainer = L.Trainer(accelerator="auto", devices=1, logger=False)
    test_results = trainer.test(module, datamodule=datamodule_test, verbose=False)
    test_metrics_dict = test_results[0]

    # Save the metrics to a JSON file in the save_path directory
    metrics_file = save_path / "test_metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(test_metrics_dict, f, indent=4)

    print(f"\nSaved test metrics to: {metrics_file}")
    for key, val in test_metrics_dict.items():
        if "rmse" in key:
            print(f"{key}: {val:.4f}")

    results, initial_states, batch = direct_multi_stepping_prediction(
        module, test_dataloader, start_idx=start_idx
    )
    ambient_temp = batch.past_ambient_temp[0, -1].detach().cpu().numpy()
    plotting_data = format_predictions_tensor_dict_to_numpy(results)
    prediction_trajectories = plot_predictions(plotting_data, datamodule=datamodule)
    prediction_trajectories.savefig(save_path / "prediction_trajectories.pdf", dpi=300)

    # Plot histogram of initial states with ambient temperature
    initial_states = initial_states.unsqueeze(0).cpu().numpy()  # add batch dim
    assert initial_states.shape[0] == 1, "Works only for batch size = 1"  # batch size 1
    normalized_initial_states = denormalize_temperature(datamodule, initial_states)
    initial_zone_temps = normalized_initial_states[0, 0, :5]
    initial_latent_states = normalized_initial_states[0, 0, 5:]
    initial_states_dist = plot_initial_states_distribution(
        initial_zone_temps, initial_latent_states, ambient_temp
    )
    initial_states_dist.savefig(save_path / "initial_states_histogram.pdf", dpi=300)

    print("\nContinuous-Time System Analysis (Inputs):")
    B_control = B_c[:, :5]  # Consider only control inputs for controllability
    stats = analyze_observability_controlability_properties(A_c, B_control, C)
    stats = analyze_continuous_gramian_properties(A_c, B_control, C)

    print("\nContinuous-Time System Analysis (Disturbances):")
    B_c_dist = B_c[:, 5:6]
    stats = analyze_observability_controlability_properties(A_c, B_c_dist, C)
    B_d_control = B_d[:, :5]  # Consider only control inputs for controllability

    print("\nDiscrete-Time System Analysis: (Inputs)")
    stats = analyze_observability_controlability_properties(A_d, B_d_control, C)
    print("\nDiscrete-Time Gramian Properties: (Inputs)")
    gramian_stats = analyze_discrete_gramian_properties(A_d, B_d_control, C)
