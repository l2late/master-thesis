## Installing dependencies

Make sure you have uv installed or install it with pip:
```bash
pip install uv
```

Then, you can install the dependencies with:
```bash
uv sync
```

## Running the application

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

## Options
### Using Weights & Biases for logging

If you want to use Weights & Biases for logging, 
You first need to set up your wandb account and get you API key, project name and entity name.
Then add these to the .env_example file and rename it to .env.
Make sure it is not committed to version control as it contains sensitive information.
The current .gitignore file already ignores the .env file, so you should be safe.

Now you can run the training script with wandb logging enabled by using the following command:
```bash
uv run python scripts/train.py logger=wandb
```

### 



