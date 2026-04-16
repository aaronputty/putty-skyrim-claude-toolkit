# Changelog

## v2.1 — Windows cross-compilation build environment (2026-04-15/16)

### Added

#### Dev container — Dockerfile
- Replaced `devcontainer.json` feature-based image with a custom `Dockerfile` so
  all tooling is baked into the image and both launch scripts have full feature
  parity without requiring the devcontainer CLI.
- **LLVM 17** (`clang-17`, `clang-cl-17`, `lld-17`, `lld-link-17`, `llvm-lib-17`,
  `llvm-ar-17`) — installed from the official LLVM apt repo (Bullseye ships only
  LLVM 13). Symlinked to `/usr/local/bin` without version suffixes.
- **Node.js 20 LTS** — installed via NodeSource apt setup script, replacing the
  former devcontainer `node:1` feature.
- **.NET 9** — installed via Microsoft's `dotnet-install.sh`, replacing the former
  devcontainer `dotnet:2` feature. `DOTNET_ROOT` and `PATH` set accordingly.
- **xmake** — installed via `xmake.io/shget.text`. Lands at `/root/.local/bin/xmake`.
  Two gotchas resolved:
  - The install script sources `~/.xmake/profile` via an internal `/bin/sh`
    subprocess regardless of `SHELL` directive; exit code suppressed (`|| true`).
  - xmake refuses to run as root without `--root`; fixed with `ENV XMAKE_ROOT=y`.
  - `ENV XMAKE_BUILD_PATH=/root/.local/bin` added for build-time path references.
- **xwin 0.6.5** — pre-built musl binary at `/usr/local/bin/xwin`.
  `ENV XWIN_ACCEPT_LICENSE=true` set for non-interactive splat.
- **Windows SDK + MSVC CRT** — splatted to `/opt/xwin` at image build time
  (~700 MB, cached in a Docker layer). x86_64 only. Build-time use under EULA.

#### Dev container — fixes
- Removed Yarn apt source (`yarn.list` / `yarn.gpg`) from base image — GPG key
  is expired, breaking every subsequent `apt-get update`.
- Removed `features` block from `devcontainer.json` — Node and .NET now in Dockerfile.
- Added `XWIN_DIR`, `XWIN_INCLUDE`, `XWIN_LIB_X64` to `devcontainer.json` `remoteEnv`.

#### Launch scripts
Four scripts for starting the container and dropping into a shell without VS Code:

| Script | Requires |
|--------|----------|
| `devshell.sh` | `@devcontainers/cli` globally installed (`npm install -g @devcontainers/cli`) |
| `devshell.ps1` | Same — PowerShell, avoids MSYS path mangling |
| `devshell-docker.sh` | Docker Desktop only |
| `devshell-docker.ps1` | Docker Desktop only — PowerShell, `-Rebuild` switch |

Docker-direct scripts start the container detached (`sleep infinity`), run
`postCreateCommand` via `docker exec`, open the interactive shell via a second
`docker exec -it`, then stop and remove the container on exit via `trap`/`finally`.

#### Toolchain
- `toolchains/clang-cl-xwin.lua` — reusable xmake toolchain for cross-compiling
  Windows PE/COFF binaries from Linux. Sets `clang-cl`/`lld-link`, wires in xwin
  SDK headers and libs, targets `x86_64-pc-windows-msvc`.

### Fixed
- `requirements.txt` — removed `esplugin==4.0.0`. Package does not exist on PyPI
  (`esplugin` is a Rust crate with no published Python bindings).
  `examples/inspect-esp.py` already handles the missing import gracefully.
- `CLAUDE.md` — corrected `esplugin` entries, updated architecture table, Dev
  Container section, and container-side tools table to reflect actual tooling.

---

## v2.0

### New Capabilities
- **ESP editing via Spriggit** — Serialize any ESP to human-readable YAML, edit directly, deserialize back. Now the primary recommended workflow for record editing.
- **AutoMod CLI integration** — NIF mesh inspection and editing, BSA archive CRUD, audio file processing (FUZ/XWM/WAV), and MCM menu generation via SpookyPirate's AutoMod Toolkit.
- **Save file analysis** — New `scripts/read-save.py` + `skyrim-save` skill. Decompress .ess saves, extract the full plugin list, search for orphaned scripts, detect effect accumulation, check mod footprint, and monitor save bloat over time.
- **8 Claude Code skills** — Auto-loading slash commands: `/inspect-esp`, `/port-to-vr`, `/create-mod`. Auto-context for NIFs, BSAs, audio files, save files, and general Skyrim modding context.

### Changes
- Version-agnostic: fully supports SE, AE, VR, and LE. Not VR-exclusive despite VR origins.
- Framing updated to reflect actual strengths: power user tool for porting, debugging, and editing — complex mods from scratch require iteration.
- Setup prompt updated to include AutoMod CLI as an optional install.
- Knowledgebase expanded with save file format documentation.
- README reordered: porting and debugging examples now lead; new-mod-from-scratch examples follow with honest caveats.

---

## v1.4

- Added `scripts/read-save.py` (LZ4 decompression, plugin list parsing, binary search)
- Added `skyrim-save` skill
- Save File Analysis section added to knowledgebase

## v1.3

- SpookyPirate AutoMod CLI integrated (NIF, BSA, audio, MCM modules)
- AutoMod CLI safety hooks added to `protect-bash.sh`
- `automod-cli.sh` wrapper script added

## v1.2

- Spriggit added as primary ESP editing workflow
- `inspect-esp`, `port-to-vr`, `create-mod` skills added
- `skyrim-nif`, `skyrim-bsa`, `skyrim-audio`, `skyrim-mcm` skills added
- CLAUDE.md template generalized with `{{GAME_ROOT}}` / `{{USERNAME}}` placeholders

## v1.1

- Knowledgebase generalized from VR-specific to version-agnostic (SE/AE/VR/LE)
- VR-specific content moved to labeled subsections
- setup.sh detects both `Skyrim VR` and `Skyrim Special Edition` document paths

## v1.0

- Initial release
- xeditlib integration (Delphi FFI fixes published as npm package)
- Safety hooks: command guard, file guard, auto-backup with audit log
- Confidence system and investigation-first workflow
- 600+ line Skyrim knowledgebase
- `skyrim-context` skill (auto-loads for .psc, .pex, Data/, .ini files)
