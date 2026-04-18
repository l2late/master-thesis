import torch


# Helper function for Zero-Order Hold (piecewise constant)
@torch.jit.script
def zoh_interp(
    t: torch.Tensor, t_span: torch.Tensor, values: torch.Tensor
) -> torch.Tensor:
    """Performs zero-order hold interpolation."""
    t = t.contiguous()
    t_span = t_span.contiguous()
    values = values.contiguous()
    # Find the index of the last time point before or at `t`
    idx = torch.searchsorted(t_span, t, side="right") - 1
    # Clamp index to be within valid bounds [0, T-1]
    idx = torch.clamp(idx, 0, len(t_span) - 1)
    return values[:, idx, :]


# Helper function for Linear Interpolation (first-order hold)
def linear_interp(
    t: torch.Tensor, t_span: torch.Tensor, values: torch.Tensor
) -> torch.Tensor:
    """Performs linear interpolation."""
    t = t.contiguous()
    t_span = t_span.contiguous()
    values = values.contiguous()
    # Find the interval t is in
    idx = torch.searchsorted(t_span, t, side="right") - 1
    idx = torch.clamp(
        idx, 0, len(t_span) - 2
    )  # Ensure we have a `t1` to interpolate to

    t0, t1 = t_span[idx], t_span[idx + 1]
    v0, v1 = values[:, idx, :], values[:, idx + 1, :]

    # Calculate interpolation weight
    # Add a small epsilon to avoid division by zero if t_span has duplicate points
    alpha = (t - t0) / (t1 - t0 + 1e-8)

    # Perform linear interpolation (lerp)
    return v0 + alpha.unsqueeze(-1) * (v1 - v0)
