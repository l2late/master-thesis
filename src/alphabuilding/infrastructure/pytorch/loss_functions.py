import torch


def trace_mse(predicted: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """
    Computes Trace Mean Squared Error (TMSE) in a fully vectorized manner.

    Args:
        predicted (torch.Tensor): Predicted tensor of shape [T, B, C] (Time, Batch, Channels)
        target (torch.Tensor): Target tensor of shape [T, B, C]

    Returns:
        torch.Tensor: Scalar tensor representing the TMSE loss.
    """
    # 1. Calculate the element-wise squared errors
    # Shape: [T, B, C]
    squared_errors = (predicted - target).pow(2)

    # 2. Calculate the cumulative sum of squared errors along the time dimension (T).
    # This gives us the sum of errors for each sub-horizon [1, ..., t] efficiently.
    # Shape: [T, B, C]
    cumulative_squared_errors = torch.cumsum(squared_errors, dim=0)

    # 3. Create a tensor representing the number of elements for each sub-horizon's MSE calculation.
    # For horizon t, the number of elements is t * B * C.
    T, B, C = predicted.shape
    # horizons will be [1, 2, 3, ..., T]
    horizons = torch.arange(1, T + 1, device=predicted.device, dtype=predicted.dtype)
    # Reshape for broadcasting: [T, 1, 1]
    # num_elements_per_horizon will be [1*B*C, 2*B*C, ..., T*B*C]
    num_elements_per_horizon = horizons.view(T, 1, 1) * (B * C)

    # 4. Calculate the MSE for each sub-horizon in parallel.
    # This is the key vectorized step.
    # Shape: [T, B, C]
    mse_per_horizon = cumulative_squared_errors / num_elements_per_horizon

    # 5. Sum all the per-horizon MSEs to get the final TMSE.
    # We sum over all dimensions to get a single scalar value.
    normalized_tmse_loss = torch.sum(mse_per_horizon) / T

    return normalized_tmse_loss
