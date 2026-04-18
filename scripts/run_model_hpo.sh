#!/usr/bin/env bash

# 1. Configure PyTorch Memory Allocator
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# 2. Start MPS Daemon (suppress error if already running)
echo "Starting NVIDIA MPS daemon..."
nvidia-cuda-mps-control -d 2>/dev/null || echo "MPS daemon is already running."

# 3. Setup a Trap to catch Ctrl+C
# This ensures that if you abort the script, it kills all 15 background
# Python workers and shuts down the MPS daemon safely.
cleanup() {
	echo -e "\nCaught Ctrl+C! Cleaning up background workers..."
	# Kill all child processes attached to this script
	pkill -P $$
	echo "Stopping NVIDIA MPS daemon..."
	echo quit | nvidia-cuda-mps-control
	echo "Cleanup complete. Exiting."
	exit 1
}
trap cleanup SIGINT SIGTERM

# 4. Launch the 15 parallel workers
echo "Launching 15 Optuna workers in parallel..."
for i in {1..15}; do
	# You can pipe output to /dev/null if you don't want 15 progress bars
	# fighting over your terminal output, or leave it as is to see the logs.
	python scripts/model_hpo.py &
done

echo "All workers launched! Waiting for trials to complete (Press Ctrl+C to abort)..."

# 5. Wait for all background jobs to finish naturally
wait

# 6. Normal cleanup if the 500 trials finish successfully
echo "All 500 trials finished successfully!"
echo "Stopping NVIDIA MPS daemon..."
echo quit | nvidia-cuda-mps-control
echo "Done."
