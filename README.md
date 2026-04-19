## Introduction

This repository contains code for the Master Thesis of Luca de Laat, student at the Delft Center for Systems and Control at the Delft University of Technology.

This thesis focuses on the application of deep learning techniques for system identification and control of building 

The code base uses MATLAB for data generation (using the BRCM Toolbox) and Python/Pytorch for training the model and evaluating the controller. 

All the code is tested on Manjaro Linux with Python 3.10 and MATLAB R2022b.

## Data generation

The training data is generated with MATLAB. The code is a modified version of the code used for the paper "Online Feedback Equilibrium Seeking" by G. Belgioioso et al. 2022. The original code can be found in the [GitHub repository of the paper](https://gitlab.nccr-automation.ch/mbadyn/fes-cdc-examples). 

The modified code and input files for this thesis can be found in the `matlab` directory. The main script can be found in `matlab/fes-cdc-examples-master/buildings/generate_data.m`. This script generates the training data and saves it in the `data` directory. The generated data is in the form of .csv files.

The script also allows to save the A,B,C,D matrices of the BRCM building in a .mat file (`data/building_plant_data.mat`), which can then be used as the plant model for evaluation of the controller with the trained model.
Currently the matlab script does does not save the .mat file in the `data` directory (it saves it in the MATLAB running directory), but you can easily move it manually or modify the script to save it in the desired location.

## Installing dependencies
This project uses [uv](https://docs.astral.sh/uv/) for dependency management and virtual environments.
Make sure you have it installed or install it with pip:
```bash
pip install uv
```

Then, you can install the dependencies by running the following command in the project root directory:
```bash
uv sync
```

## Training the model

To start a training run, use the following command:
```bash
uv run python scripts/train.py
```

The training script uses [Hydra](https://hydra.cc/) for configuration management.
Have a look at the `conf` directory for the default configuration options.
You can override any configuration option from the command line by using the syntax:
```bash
uv run python scripts/train.py <config_option>=<value>
```

Example:
```bash
uv run python scripts/train.py trainer.max_epochs=500 model.lr=0.001
```

### Experiments

Different experiments configurations (topology, instability penalty...) are defined in the `conf/experiment` directory. You can specify which experiment to run by using the `experiment` configuration option.
Example:
```bash
uv run python scripts/train.py experiment=physical_1-to-1_non_stable
```

## Options
### Using Weights & Biases for logging

If you want to use Weights & Biases for logging, 
You first need to set up your wandb account and get you API key, project name and entity name.
Then add these to the `.env_example` file and rename it to `.env`.
Make sure it is not committed to version control as it contains sensitive information.
The current `.gitignore` file already ignores the `.env` file, so you should be safe.

Now you can run the training script with wandb logging enabled by using the following command:

```bash
uv run python scripts/train.py logger=wandb
```

## Training on cloud GPU with Vast AI

While the model and dataset are very small and easily fit on a consumer GPU. You can speed up training with Cloud GPUs.
Also, you can use the CUDA MPS to train multiple runs in parallel on a single GPU.

### Docker image for training on Vast AI
The repository provide necessary scripts build Docker images suitable for training on cloud GPUs with [Vast AI](https://vast.ai/).

You can build the Docker image with the following command:
```bash
./docker/docker_build_and_push.sh
```

This will build the Docker image and push it to Docker Hub. You can then use this image to train on Vast AI by following their documentation on how to use custom Docker images.

```bash
./docker/docker_build_and_push.sh --no-push
```

## Training multiple runs in parallel with CUDA MPS
If you have access to a GPU that supports CUDA MPS, you can train multiple runs in parallel on the same GPU.

The script `scripts/orchstraate_multi_process_on_single_gpu.py` can be used to orchestrate multiple training runs in parallel on a single GPU using CUDA MPS.

### Example:
Running 50 runs with different seeds and two different variants of the experiment in parallel on a single GPU with a maximum of 10 jobs running in parallel.

Be sure to adjust the `--max-jobs` option based on the available GPU memory in order to avoid throttling. You can monitor the GPU memory usage on a Vast AI instance with `nvtop`.
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
the `--variants` option allows you to specify different variants each run the experiment, which will be used to create different runs in wandb. In this example, we are creating two variants of the experiment, one with a non-stable building and one with a soft-stable building. The `trainer.max_epochs=500 logger=wandb 'datamodule.noise_stds=[2, 60]'` part allows you to specify additional hydra overrides that will be applied to all runs.
See the script for more details on the available command line arguments.

