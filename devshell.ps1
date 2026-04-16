# Start the dev container (builds image if needed) and open an interactive shell.
# Usage: .\devshell.ps1
#
# Prerequisites:
#   - Node.js (npm) installed locally
#   - @devcontainers/cli installed globally: npm install -g @devcontainers/cli
#   - Docker Desktop running
#
# If you don't have the devcontainer CLI, use .\devshell-docker.ps1 instead —
# it drives Docker directly with no extra dependencies.

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

devcontainer up --workspace-folder $ScriptDir
devcontainer exec --workspace-folder $ScriptDir bash
