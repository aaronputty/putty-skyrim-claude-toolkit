#!/usr/bin/env bash
# Start the dev container via Docker directly and open an interactive shell.
# Usage: ./devshell-docker.sh [--rebuild]
#
# Prerequisites:
#   - Docker Desktop running (no other dependencies)
#
# Pass --rebuild to force a fresh image build even if one already exists.
#
# Full feature parity with devshell.sh: Node 20, .NET 9, Python 3.11, LLVM 17
# (clang-cl, lld-link), xmake, and the xwin Windows SDK are all baked into the
# image. postCreateCommand (pip install / npm install / dotnet tool restore) runs
# automatically inside the container before the shell opens.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_TAG="skyrim-toolkit"
CONTAINER_NAME="skyrim-toolkit-dev"
MO2_PATH="C:/Games/Skyrim25"

# --- Build image ---
if [[ "$1" == "--rebuild" ]] || ! docker image inspect "$IMAGE_TAG" &>/dev/null; then
    echo "Building $IMAGE_TAG from .devcontainer/Dockerfile..."
    docker build \
        -f "$SCRIPT_DIR/.devcontainer/Dockerfile" \
        -t "$IMAGE_TAG" \
        "$SCRIPT_DIR"
fi

# --- Clean up any leftover container from a previous session ---
docker rm -f "$CONTAINER_NAME" &>/dev/null || true

# --- Stop and remove container on exit ---
trap 'echo "Stopping container..."; docker rm -f "$CONTAINER_NAME" &>/dev/null || true' EXIT

# --- Start container detached ---
# sleep infinity keeps it alive so we can exec into it.
echo "Starting container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -v "$SCRIPT_DIR:/workspace" \
    -w /workspace \
    -v "$MO2_PATH/mods:/skyrim/mods:ro" \
    -v "$MO2_PATH/profiles:/skyrim/profiles:ro" \
    -v "$MO2_PATH/overwrite:/skyrim/overwrite:ro" \
    -v "$MO2_PATH/Game Root/Data:/skyrim/game-data:ro" \
    -e SKYRIM_MODS_DIR=/skyrim/mods \
    -e SKYRIM_PROFILES_DIR=/skyrim/profiles \
    -e SKYRIM_OVERWRITE_DIR=/skyrim/overwrite \
    -e SKYRIM_GAME_DATA_DIR=/skyrim/game-data \
    -e XWIN_DIR=/opt/xwin \
    -e "XWIN_INCLUDE=/opt/xwin/crt/include:/opt/xwin/sdk/include/ucrt:/opt/xwin/sdk/include/um:/opt/xwin/sdk/include/shared" \
    -e "XWIN_LIB_X64=/opt/xwin/crt/lib/x86_64:/opt/xwin/sdk/lib/um/x86_64" \
    "$IMAGE_TAG" \
    sleep infinity

# --- postCreateCommand ---
echo "Running postCreateCommand (pip install / npm install / dotnet tool restore)..."
docker exec "$CONTAINER_NAME" bash -c \
    "pip install -r requirements.txt && npm install && dotnet tool restore"

# --- Interactive shell ---
echo "Done. Opening shell (exit to stop the container)..."
docker exec -it "$CONTAINER_NAME" bash
