import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.colors import CenteredNorm


def _to_numpy(x: torch.Tensor) -> np.ndarray:
    return x.detach().cpu().numpy()


def summarize_param_to_matrix_mapping(dynamics) -> dict:
    """
    Build a structured mapping from learned parameters to A/B matrix entries.
    Returns a dict with numpy arrays and lists, easy to print or tabulate.
    """
    A = dynamics.A_matrix
    B = dynamics.B_matrix

    C = torch.exp(dynamics._log_capacitances)
    R_edges = torch.exp(dynamics._log_resistances)
    G_edges = 1.0 / R_edges
    R_amb = torch.exp(dynamics._log_ambient_resistances)
    G_amb = 1.0 / R_amb

    num_states = dynamics.num_states
    num_inputs = dynamics.num_inputs
    num_disturbances = dynamics.num_disturbances
    start_idx = num_states - dynamics.num_exterior_walls

    # Edge indices used to place conductances into W
    row_idx = dynamics.row_indices
    col_idx = dynamics.col_indices

    mapping = {
        "A": _to_numpy(A),
        "B": _to_numpy(B),
        "C": _to_numpy(C),
        "R_edges": _to_numpy(R_edges),
        "G_edges": _to_numpy(G_edges),
        "R_amb": _to_numpy(R_amb),
        "G_amb": _to_numpy(G_amb),
        "edges": [
            {
                "k": int(k),
                "i": int(i),
                "j": int(j),
                "R": float(R_edges[k].item()),
                "G": float(G_edges[k].item()),
                # A[i, j] = G_ij / C_i, A[j, i] = G_ij / C_j
                "A_coords": [(int(i), int(j)), (int(j), int(i))],
            }
            for k, (i, j) in enumerate(zip(row_idx.tolist(), col_idx.tolist()))
        ],
        # Ambient is applied to last num_exterior_walls states
        "ambient": [
            {
                "idx": int(i),
                "R": float(R_amb[m].item()),
                "G": float(G_amb[m].item()),
                # A[ii, ii] accumulates G_amb_i/C_i, B[ii, num_inputs] = G_amb_i/C_i
                "A_coord": (int(i), int(i)),
                "B_coord": (int(i), int(num_inputs)) if num_disturbances > 0 else None,
            }
            for m, i in enumerate(range(int(start_idx), int(num_states)))
        ],
        # HVAC inputs map as B[i, i] = 1/C_i for i < num_inputs
        "hvac": [
            {
                "idx": int(i),
                "B_coord": (int(i), int(i)),
            }
            for i in range(min(num_states, num_inputs))
        ],
    }
    return mapping


def plot_params_and_matrices(mapping: dict):
    A = mapping["A"]
    B = mapping["B"]
    C = mapping["C"]

    vmin = min(A.min(), B.min())
    vmax = max(A.max(), B.max())
    norm = CenteredNorm(vcenter=0, halfrange=max(abs(vmin), abs(vmax)))

    A_rows, A_cols = A.shape
    B_rows, B_cols = B.shape

    scale_factor = min(8.0 / max(A_cols, B_cols), 6.0 / A_rows)
    A_width = A_cols * scale_factor
    B_width = B_cols * scale_factor
    total_width = A_width + B_width + 6.0
    height = A_rows * scale_factor + 3.0

    fig = plt.figure(figsize=(total_width, height))
    plt.suptitle(r"$\dot{x} = Ax + Bu$ with parameter mapping", fontsize=14)

    gs = fig.add_gridspec(
        2,
        3,
        width_ratios=[A_cols, B_cols, 8],
        height_ratios=[1, 1],
        left=0.05,
        right=0.95,
        wspace=0.25,
        hspace=0.35,
    )

    # Heatmap A
    axA = fig.add_subplot(gs[0, 0])
    imA = axA.imshow(A, cmap="seismic", norm=norm, aspect="equal")
    axA.set_title(f"A {A_rows}x{A_cols}")
    axA.set_xlabel("j")
    axA.set_ylabel("i")

    # Heatmap B
    axB = fig.add_subplot(gs[0, 1])
    imB = axB.imshow(B, cmap="seismic", norm=norm, aspect="equal")
    axB.set_title(f"B {B_rows}x{B_cols}")
    axB.set_xlabel("col")
    axB.set_ylabel("row")

    # Colorbar
    cbar_ax = fig.add_subplot(gs[:, 2])
    fig.colorbar(imA, cax=cbar_ax)

    # Overlay markers for mappings
    # Interior edges (off-diagonal contributions in A)
    for e in mapping["edges"]:
        i, j = e["i"], e["j"]
        axA.scatter(
            [j],
            [i],
            s=40,
            marker="o",
            color="yellow",
            edgecolors="k",
            linewidths=0.5,
            label="G_ij/C_i" if "edge_once" not in axA.__dict__ else None,
        )
        axA.scatter(
            [i], [j], s=40, marker="o", color="yellow", edgecolors="k", linewidths=0.5
        )
        axA.__dict__["edge_once"] = True

    # Ambient contributions: diagonal of A and disturbance column in B
    num_inputs = B_cols - max(0, B_cols - B_rows)  # robust-ish; use provided below
    for a in mapping["ambient"]:
        ii = a["idx"]
        axA.scatter(
            [ii],
            [ii],
            s=80,
            marker="s",
            color="orange",
            edgecolors="k",
            linewidths=0.5,
            label="G_amb_i/C_i" if "amb_once" not in axA.__dict__ else None,
        )
        if a["B_coord"] is not None:
            r, c = a["B_coord"]
            axB.scatter(
                [c],
                [r],
                s=80,
                marker="x",
                color="orange",
                linewidths=1.0,
                label="(G_amb_i/C_i) in B[:, d]",
            )
        axA.__dict__["amb_once"] = True

    # HVAC inputs in B diagonal 1/C_i
    for h in mapping["hvac"]:
        r, c = h["B_coord"]
        axB.scatter(
            [c],
            [r],
            s=50,
            marker="^",
            color="lime",
            edgecolors="k",
            linewidths=0.5,
            label="1/C_i in B[i,i]" if "hvac_once" not in axB.__dict__ else None,
        )
        axB.__dict__["hvac_once"] = True

    # Legends (deduplicate labels)
    handlesA, labelsA = axA.get_legend_handles_labels()
    by_labelA = dict(zip(labelsA, handlesA))
    if by_labelA:
        axA.legend(by_labelA.values(), by_labelA.keys(), loc="upper right", fontsize=8)

    handlesB, labelsB = axB.get_legend_handles_labels()
    by_labelB = dict(zip(labelsB, handlesB))
    if by_labelB:
        axB.legend(by_labelB.values(), by_labelB.keys(), loc="upper right", fontsize=8)

    plt.show()


def visualize_dynamics_with_param_mapping(dynamics):
    if hasattr(dynamics, "_log_capacitances"):
        mapping = summarize_param_to_matrix_mapping(dynamics)
        # Print a concise table to stdout for exact mapping
        print("=== Capacitances C ===")
        print("index, C[i]")
        for i, c in enumerate(mapping["C"].tolist()):
            print(f"{i}, {c:.6g}")

        print("\n=== Interior Resistances (edges) ===")
        print("k, i, j, R_ij, G_ij")
        for e in mapping["edges"]:
            print(f"{e['k']}, {e['i']}, {e['j']}, {e['R']:.6g}, {e['G']:.6g}")

        print("\n=== Ambient Resistances ===")
        print("i, R_amb, G_amb")
        for a in mapping["ambient"]:
            print(f"{a['idx']}, {a['R']:.6g}, {a['G']:.6g}")

        plot_params_and_matrices(mapping)
