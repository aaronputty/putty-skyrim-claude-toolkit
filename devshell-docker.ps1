# Start the dev container via Docker directly and open an interactive shell.
# Usage: .\devshell-docker.ps1 [-Rebuild]
#
# Prerequisites:
#   - Docker Desktop running (no other dependencies)
#
# Pass -Rebuild to force a fresh image build even if one already exists.
#
# Full feature parity with devshell.ps1: Node 20, .NET 9, Python 3.11, LLVM 17
# (clang-cl, lld-link), xmake, and the xwin Windows SDK are all baked into the
# image. postCreateCommand (pip install / npm install / dotnet tool restore) runs
# automatically inside the container before the shell opens.

param(
    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ImageTag   = "skyrim-toolkit"
$ContainerName = "skyrim-toolkit-dev"
$MO2Path    = "C:/Games/Skyrim25"

# --- Build image ---
$imageExists = $false
try {
docker image inspect $ImageTag 2>&1 | Out-Null
} catch {
    Write-Host "An error occurred when looking for the container. Rebuilding..."
}
if ($LASTEXITCODE -eq 0) { $imageExists = $true }

if ($Rebuild -or -not $imageExists) {
    Write-Host "Building $ImageTag from .devcontainer/Dockerfile..."
    docker build `
        -f "$ScriptDir/.devcontainer/Dockerfile" `
        -t $ImageTag `
        $ScriptDir
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# --- Clean up any leftover container from a previous session ---
try {
docker rm -f $ContainerName 2>&1 | Out-Null
}catch {
    Write-Host "An error occured removing the container. Likely doesn't exist yet..."
}

# --- Stop and remove container on exit ---
try {
    # --- Start container detached ---
    # sleep infinity keeps it alive so we can exec into it.
    Write-Host "Starting container..."
    docker run -d `
        --name $ContainerName `
        -v "${ScriptDir}:/workspace" `
        -w /workspace `
        -v "${MO2Path}/mods:/skyrim/mods:ro" `
        -v "${MO2Path}/profiles:/skyrim/profiles:ro" `
        -v "${MO2Path}/overwrite:/skyrim/overwrite:ro" `
        -v "${MO2Path}/Game Root/Data:/skyrim/game-data:ro" `
        -e SKYRIM_MODS_DIR=/skyrim/mods `
        -e SKYRIM_PROFILES_DIR=/skyrim/profiles `
        -e SKYRIM_OVERWRITE_DIR=/skyrim/overwrite `
        -e SKYRIM_GAME_DATA_DIR=/skyrim/game-data `
        -e XWIN_DIR=/opt/xwin `
        -e "XWIN_INCLUDE=/opt/xwin/crt/include:/opt/xwin/sdk/include/ucrt:/opt/xwin/sdk/include/um:/opt/xwin/sdk/include/shared" `
        -e "XWIN_LIB_X64=/opt/xwin/crt/lib/x86_64:/opt/xwin/sdk/lib/um/x86_64" `
        $ImageTag `
        sleep infinity
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    # --- postCreateCommand ---
    #Write-Host "Running postCreateCommand (pip install / npm install / dotnet tool restore)..."
    docker exec $ContainerName bash -c "pip install -r requirements.txt && npm install && dotnet tool restore"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    # --- Interactive shell ---
    Write-Host "Done. Opening shell (exit to stop the container)..."
    docker exec -it $ContainerName bash

} finally {
    Write-Host "Stopping container..."
    docker rm -f $ContainerName 2>&1 | Out-Null
}
