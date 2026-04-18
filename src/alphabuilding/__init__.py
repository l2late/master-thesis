import os

import torch

# needed to avoid errors when loading certain model checkpoints
os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"

# Set default dtype. 64 bit precision is important for simulation and control applications.
torch.set_default_dtype(torch.float64)
