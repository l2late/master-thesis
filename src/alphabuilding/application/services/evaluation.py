from typing import Iterator

import lightning as L
import torch
from tqdm import tqdm


class MultiStepEvaluator:
    """Orchestrates the direct multi-stepping evaluation of a model."""

    def __init__(self, module: L.LightningModule, prediction_horizon: int):
        self._module = module
        self._prediction_horizon = prediction_horizon
        self._module.eval()
        self._module.to("cpu")

    def evaluate(self, dataloader_iterator: Iterator) -> dict[str, torch.Tensor]:
        """Runs the evaluation and returns the concatenated results."""
        results = []
        with torch.no_grad():
            self._perform_initial_step(results, dataloader_iterator)
            self._simulate_remaining_horizon(results, dataloader_iterator)
        return self._concatenate_results(results)

    def _perform_initial_step(self, results: list[dict], dataloader_iterator: Iterator):
        batch = self._get_next_batch(dataloader_iterator)
        # Create the initial state from the historical data in the first batch
        initial_temps = batch["past_zone_temps_traj"][:, -2]
        initial_result = {
            "preds": initial_temps,
            "target_temps": initial_temps,
            "ambient_temps": batch["past_ambient_temp_traj"][:, -2],
            "heat_inputs": batch["past_heat_input_traj"][:, -2],
            "timestamps": batch["measurement_traj_timestamps"][:, -2],
        }
        results.append(initial_result)
        # The first prediction is also based on this batch
        results.append(self._module._step(batch, prefix="test"))

    def _simulate_remaining_horizon(
        self, results: list[dict], dataloader_iterator: Iterator
    ):
        for _ in tqdm(range(1, self._prediction_horizon), desc="Direct time stepping"):
            batch = self._get_next_batch(dataloader_iterator)
            results.append(self._module._step(batch, prefix="test"))

    def _get_next_batch(self, dataloader_iterator: Iterator) -> dict:
        try:
            batch = next(dataloader_iterator)
            return {k: v.to("cpu") for k, v in batch.items()}
        except StopIteration:
            raise ValueError(
                "Dataloader does not have enough data for the prediction horizon."
            )

    @staticmethod
    def _concatenate_results(results: list[dict]) -> dict[str, torch.Tensor]:
        # ... (concatenation logic remains the same, but now it's a private method)
        keys_to_process = [
            "preds",
            "target_temps",
            "ambient_temps",
            "heat_inputs",
            "timestamps",
        ]
        concatenated_results = {}
        for key in keys_to_process:
            values = [res[key] for res in results if res and key in res]
            concatenated_results[key] = torch.cat(values, dim=0)
        return concatenated_results


# The original function becomes a much simpler entry point
def direct_multi_stepping_evaluation(
    module: L.LightningModule,
    dataloader,
    start_idx: int = 0,
    prediction_horizon: int | None = 1,
) -> dict:
    # --- Validation logic remains here ---
    if start_idx < 0:
        raise ValueError("Start index must be non-negative.")
    # ... more validation ...
    if prediction_horizon is None:
        prediction_horizon = len(dataloader) - start_idx

    # --- Dataloader iteration setup ---
    main_iter = iter(dataloader)
    for _ in range(start_idx):
        try:
            next(main_iter)
        except StopIteration:
            raise ValueError(f"Start position {start_idx} exceeds dataloader length.")

    # --- Delegate to the service ---
    evaluator = MultiStepEvaluator(module=module, prediction_horizon=prediction_horizon)
    return evaluator.evaluate(dataloader_iterator=main_iter)
