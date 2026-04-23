## Introduction

This repository contains code for the Master Thesis of Luca de Laat, student at the Delft Center for Systems and Control at Delft University of Technology.

The thesis focuses on the application of deep learning techniques for system identification and control of building HVAC systems.

The codebase uses MATLAB for data generation (via the [BRCM Toolbox](https://www.brcm.ethz.ch/)) and Python/PyTorch for model training and controller evaluation.

Everything was tested on Manjaro Linux with Python 3.10 and MATLAB R2021a.

## Prerequisites

- Python 3.10
- MATLAB R2021a (for me the BRCM Toolbox did not work nicely with newer versions of MATLAB, your experience may vary)
- Weights & Biases account (for logging and storing artifacts)
- CUDA-compatible GPU (for training the model)

For training on cloud GPUs with Vast AI, you will also need:
- A Vast AI account
- Docker

## Installing Python dependencies
This project uses [uv](https://docs.astral.sh/uv/) for dependency management and virtual environments.
Make sure you have it installed or install it with pip:
```bash
pip install uv
```

Then, you can install the dependencies by running the following command in the project root directory:
```bash
uv sync
```

You can now use `uv run <file.py>` to execute any Python script within the project's virtual environment with all dependencies installed.

## Quick start with TensorBoard logging
You can test if the training is running:

```bash
uv run python scripts/train.py logger=tensorboard
```

This uses the TensorBoard logger, which does not require any setup and will log the training metrics to the `runs` directory. You can then visualize the training metrics with TensorBoard by running:

```bash
uv run tensorboard --logdir logs/
```

Open the URL shown in the terminal (usually http://localhost:6006) to view training metrics.

## Using Weights & Biases for logging

The codebase relies on Weights & Biases (WandB) for logging and storing artifacts (configs and model checkpoints). This allows you to easily track and compare different runs of the experiment and keep all the relevant information in one place.

WandB offers a generous free tier for academics, and even the standard free plan should be more than sufficient for this project. You can sign up on their [website](https://wandb.ai/site/research/).

### Setting up WandB
You first need to create a WandB account and generate an API key, a project name, and an entity name.
Check the WandB documentation for how to do this.

Now you need to set a few environment variables with the WandB credentials you just created. You can do this in two ways:

#### Manually
On linux

```bash
export WANDB_API_KEY=<your_wandb_api_key>
export WANDB_PROJECT=<your_wandb_project_name>
export WANDB_ENTITY=<your_wandb_entity_name>
```

#### Store them in a .env file

You can also add the environment variables to the example `.env_example` file and rename it to `.env`.
Make sure `.env` is never committed to version control, as it contains sensitive information (the `.gitignore` already excludes it).

You can now use the method of your choice to load the .env file and set the environment variables.

For the simplest approach, pass the file directly to `uv`:

```bash
uv run --env-file .env scripts/train.py logger=wandb
```

or use a tool like [direnv](https://direnv.net/) to automatically load the .env file when you enter the project directory (recommended for development). In this case you can simply run the training script without specifying the env file:

```bash
uv run python scripts/train.py logger=wandb
```

## Training the model

To start a training run, use the following command:
```bash
uv run python scripts/train.py
```

The PyTorch Lightning module resides at `/src/alphabuilding/infrastructure/lightning/modules/discrete_observer_ode.py`.
It is instantiated in `train.py` using Hydra.

The training script uses [Hydra](https://hydra.cc/) for configuration management which allows you to easily manage and override configuration options from the command line and run multiple training runs with different configurations.

Have a look at the `conf` directory for the default configuration options.
Especially look at the configurations defined in `conf/train.yaml` and `conf/model/default.yaml`.
The different experiment configurations (topologies and instability penalty) can be found in `conf/experiment`.

With Hydra you can easily override any configuration option from the command line using the following syntax:
```bash
uv run python scripts/train.py <config_option>=<value>
```

Example:
```bash
uv run python scripts/train.py experiment=physical_no_latent_states_soft_stable
uv run python scripts/train.py experiment=physical_1-to-1_soft_stable
```

### Experiments

Different experiments configurations (topology, instability penalty...) are defined in the `conf/experiment` directory. You can specify which experiment to run by using the `experiment` configuration option.
Example:
```bash
uv run python scripts/train.py experiment=physical_1-to-1_non_stable
```


### Training on cloud GPU with Vast AI

While the model and dataset are small enough to run on a consumer GPU, cloud GPUs can speed up training significantly.
You can also use CUDA MPS to train multiple runs in parallel on a single GPU — see the related section below.

#### Docker image for training on Vast AI
The repository provides scripts to build Docker images suitable for training on cloud GPUs with [Vast AI](https://vast.ai/).

You can build the Docker image with the following command:
```bash
./docker/docker_build_and_push.sh
```

This builds the Docker image and pushes it to Docker Hub. You can then use the image on Vast AI with their documentation on custom Docker images.

To build the image without pushing:

```bash
./docker/docker_build_and_push.sh --no-push
```

### Training multiple runs in parallel with CUDA MPS
If you have access to a GPU that supports [CUDA MPS](https://docs.nvidia.com/deploy/mps/introduction.html), you can train multiple runs in parallel on the same GPU.

The script `scripts/orchestrate_multi_process_on_single_gpu.py` orchestrates multiple training runs in parallel on a single GPU using CUDA MPS.

#### Example:
Running 50 runs with different seeds and two different variants of the experiment in parallel on a single GPU with a maximum of 10 jobs running in parallel.

Be sure to adjust the `--max-jobs` option based on the available CUDA cores and memory in order to avoid throttling. You can monitor the GPU memory usage on a Vast AI instance with `nvtop`.
Tested on an NVIDIA RTX 3090 (5 jobs), 4090 (7 jobs) and 5090 (10 jobs).

```bash
uv run python scripts/orchestrate_multi_process_on_single_gpu.py \
        --train-script scripts/train.py \
        --num-seeds 50 \
        --base-seed 1000 \
        --reserve-cpus 1 \
        --max-jobs 10 \
        --variants 'experiment=physical_1-to-1_non_stable' 'experiment=physical_1-to-1_soft_stable' \
        -- trainer.max_epochs=500 logger=wandb 'datamodule.noise_stds=[2, 60]'
```

The last line allows you to specify hydra configs and overrides for each run.
the `--variants` option allows you to specify different variants for the experiment (the runs within each variant are run sequentially). 
See the script for more details on the available command-line arguments.

## Evaluating the trained models

The evaluation script downloads a trained model from Weights & Biases and runs a comprehensive evaluation pipeline on the test set.

Basic usage:
```bash
uv run python scripts/eval.py
```

This will automatically select the best run from WandB based on the lowest `val/rmse_celsius` metric, download the model checkpoint and config, and run a full evaluation pipeline.

### Selecting which model to evaluate

By default, the script auto-selects the best run from WandB. You can override this behavior:

| Command | Description |
| --- | --- |
| `uv run python scripts/eval.py` | Auto-select best run by `val/rmse_celsius` |
| `uv run python scripts/eval.py --run-id abc123xyz` | Evaluate a specific run by its WandB run ID |
| `uv run python scripts/eval.py --metric-key val/mae_celsius` | Use a different metric for auto-selection |


### What the evaluation does

The evaluation pipeline (`alphabuilding.analysis.evaluation.evaluate_model_predictions`) runs a comprehensive analysis of the model including:
- System analysis (eigenvalues/poles)
- Comparison of model predictions on the test dataset

## Controller tuning and evaluation

### Controller hyperparameters tuning
The repository already contains the results of the hyperparameter tuning for the MPC and RBC (hysteresis) controllers in `output/eval_hopt` but you can also run the hyperparameter tuning yourself.

You can run the MPC and RBC (hysteresis) hyperparameter tuning with [Optuna](https://optuna.org/):
```bash
uv run python scripts/control/mpc_hopt.py
```
or
```bash
uv run python scripts/control/rbc_hopt.py
```

Use the `--help` flag to see the available command line arguments and options for the hyperparameter tuning scripts.

### Comparison of MPC with Rule-Based Controller (RBC)

Evaluate and Compare the performance of the RBC and MPC controller with the trained model on the building plant model by running:
```bash
uv run python scripts/control/evaluate_rbc_and_mpc.py
```


## Training Data generation

The training data is generated with MATLAB. 
The data files are already present in the `/data` directory, but you can also generate them yourself by running the MATLAB script.

The code is a modified version of the code used for the paper "Online Feedback Equilibrium Seeking" by G. Belgioioso et al. 2022. The original code can be found in the [GitHub repository of the paper](https://gitlab.nccr-automation.ch/mbadyn/fes-cdc-examples). 

The modified code and input files for this thesis can be found in the `matlab` directory. The main script can be found in `matlab/fes-cdc-examples-master/buildings/generate_data.m`. This script generates the training data and saves it in the `data` directory. The generated data is in the form of .csv files.

The script also allows to save the A,B,C,D matrices of the BRCM building in a .mat file (`data/building_plant_data.mat`), which can then be used as the plant model for evaluation of the controller with the trained model.
Currently the MATLAB script saves the `.mat` file in the MATLAB working directory rather than the `data` directory. You can move it manually or modify the script to output to the desired location.

