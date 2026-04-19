#!/bin/bash

# Exit immediately if a command exits with a non-zero status, if an unset
# variable is used, or if a command in a pipeline fails.
set -euo pipefail

# Docker repository (e.g., your Docker Hub username)
readonly DOCKER_REPO="l2late"
# The name for your Docker image
readonly IMAGE_NAME="my-vastai"

# Get the absolute path of the directory where the script is located.
# This makes the script runnable from anywhere.
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
# Define the build context and Dockerfile path relative to the script's parent directory.
readonly BUILD_CONTEXT="$SCRIPT_DIR/../"
readonly DOCKERFILE_PATH="$SCRIPT_DIR/../docker/Dockerfile.train"

main() {
	check_dependencies

	local push_image=true
	local version=""

	# Parse command-line arguments
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--no-push)
			push_image=false
			shift
			;;
		-*)
			echo "ERROR: Unknown option $1" >&2
			exit 1
			;;
		*)
			# Treat any non-flag argument as the version
			version="$1"
			shift
			;;
		esac
	done

	# Use the provided version, or default to the short git commit hash
	version=${version:-$(git -C "$BUILD_CONTEXT" rev-parse --short HEAD)}
	echo "INFO: Using version tag: $version"

	local image_with_version_tag="$DOCKER_REPO/$IMAGE_NAME:$version"
	local image_with_latest_tag="$DOCKER_REPO/$IMAGE_NAME:latest"

	echo "INFO: Building image with tags '$version' and 'latest'..."
	docker build \
		--progress=plain \
		-t "$image_with_version_tag" \
		-t "$image_with_latest_tag" \
		-f "$DOCKERFILE_PATH" \
		"$BUILD_CONTEXT"

	# Conditionally push based on the flag
	if [[ "$push_image" == true ]]; then
		echo "INFO: Pushing both tags to Docker repository..."
		docker push "$image_with_version_tag"
		docker push "$image_with_latest_tag"
		echo "✅ Successfully built and pushed $DOCKER_REPO/$IMAGE_NAME with tags '$version' and 'latest'."
	else
		echo "✅ Successfully built $DOCKER_REPO/$IMAGE_NAME."
		echo "ℹ️ Skipped push. The image is available locally for testing."
	fi
}

check_dependencies() {
	# Check if Docker is installed
	if ! command -v docker &>/dev/null; then
		echo "ERROR: 'docker' command not found. Please install Docker." >&2
		exit 1
	fi

	# Check if Git is installed (for default versioning)
	if ! command -v git &>/dev/null; then
		echo "ERROR: 'git' command not found. Please install Git or provide a version tag." >&2
		exit 1
	fi

	# Check if Dockerfile exists
	if [[ ! -f "$DOCKERFILE_PATH" ]]; then
		echo "ERROR: Dockerfile not found at: $DOCKERFILE_PATH" >&2
		exit 1
	fi
}

# --- Script Execution ---
# Call the main function with all script arguments
main "$@"
