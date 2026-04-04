# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A modded Skyrim VR installation managed by MO2 (Mod Organizer 2) with the Root Builder plugin and a stock game folder setup. The toolkit lives in a separate folder from the game; MO2 presents a virtual `Data/` filesystem at runtime by merging individual mod folders.

## Key Paths

- **MO2 base**: `{{MO2_INSTANCE_PATH}}/`
- **Stock game root**: `{{MO2_INSTANCE_PATH}}/Game Root/`
- **Active profile**: `{{ACTIVE_PROFILE_NAME}}`
- **User INI configs**: `{{MO2_INSTANCE_PATH}}/profiles/{{ACTIVE_PROFILE_NAME}}/` (Skyrim.ini, SkyrimVR.ini, SkyrimPrefs.ini)
- **Load order**: `{{MO2_INSTANCE_PATH}}/profiles/{{ACTIVE_PROFILE_NAME}}/loadorder.txt` and `plugins.txt`
- **Mod data**: `{{MO2_INSTANCE_PATH}}/mods/<mod-name>/` — MO2 mounts these into a virtual `Data/` at runtime; no flat `Data/` exists on disk
- **SKSE plugin configs**: `{{MO2_INSTANCE_PATH}}/mods/<mod-name>/SKSE/Plugins/` (per mod) or `{{MO2_INSTANCE_PATH}}/overwrite/SKSE/Plugins/`
- **Root Builder files**: `{{MO2_INSTANCE_PATH}}/mods/<mod-name>/Root/` — copied into game root at launch, removed on exit
- **Overwrite folder**: `{{MO2_INSTANCE_PATH}}/overwrite/` — receives files written directly to the game root while MO2 is running
- **Toolkit**: `{{TOOLKIT_PATH}}`

## MO2 Virtual Filesystem

MO2 does **not** maintain a real merged `Data/` folder on disk. At launch it mounts a virtual filesystem combining:
1. `{{MO2_INSTANCE_PATH}}/Game Root/Data/` (stock game + DLC ESMs/BSAs)
2. Each enabled mod's `{{MO2_INSTANCE_PATH}}/mods/<name>/` folder (higher priority wins on conflict)
3. `{{MO2_INSTANCE_PATH}}/overwrite/` (highest priority — catches files written during a session)

**Implications for tooling:**
- When inspecting a mod's files, look in `{{MO2_INSTANCE_PATH}}/mods/<mod-name>/`, not `Data/`
- ESP files for installed mods live in `{{MO2_INSTANCE_PATH}}/mods/<mod-name>/<ModName>.esp`
- Papyrus source files for a mod live in `{{MO2_INSTANCE_PATH}}/mods/<mod-name>/Scripts/Source/`
- xelib/XEditLib loads ESPs from the registry game path — ensure the SSE registry key points to `{{MO2_INSTANCE_PATH}}/Game Root/`
- Root Builder files (ENB, SKSE DLLs, d3dx, etc.) live in `Root/` subfolder of a mod, not directly in the mod's data folder

## Architecture

### Container First

Default to the container for any task. Only cross to Windows/MO2 when the task genuinely requires it.

| Task | Where | Tool |
|------|-------|------|
| Validate plugin metadata (masters, FormIDs, overlap) | Container | `esplugin` (Python) |
| Inspect ESP records | Container | `spriggit serialize` → YAML |
| Diff two ESPs | Container | `spriggit serialize` both → `diff` |
| Author new ESP records | Container | Spriggit YAML → `spriggit deserialize` |
| Generate FOMOD XML | Container | Node.js (`fast-xml-parser`) |
| Validate JSON schemas | Container | Node.js (`ajv`, `zod`) |
| Unit test mod logic | Container | `pytest` |
| Load-order-dependent ESP edits | Windows (MO2) | xelib |
| Decompile Papyrus `.pex` → `.psc` | Windows | Champollion |
| Compile Papyrus `.psc` → `.pex` | Windows | Caprica |

### Why xelib is Windows-only

`XEditLib.dll` is a Delphi-compiled Windows DLL. It cannot run in a Linux container and requires the MO2 virtual filesystem to see the full load order. It must be launched through MO2's executable list.

Anything achievable with Spriggit or esplugin should use those instead. xelib is reserved for operations that need the fully resolved load order or that Spriggit cannot express.

### Output contract

The container side produces artifacts consumed by the Windows side:
- `conversion_plan.json` — record operations for `esp_runner/` to execute via xelib
- Spriggit YAML — ESP source files that `spriggit deserialize` compiles to binary
- FOMOD `ModuleConfig.xml` — installer definition

Nothing in `esp_runner/` should contain logic. The container makes all decisions.

---

## Development Environment

### Python — pyenv-win + venv

Python version management uses `pyenv-win`. The project Python interpreter is pinned
in `.python-version` and is completely separate from any system Python on the host.

```powershell
# First time setup on a new Windows machine
pyenv install 3.11.9
pyenv local 3.11.9
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

For Windows-side execution only:
```powershell
pip install -r requirements-windows.txt
```

### Node.js — fnm

Node version management uses `fnm`. The project Node version is pinned in
`.node-version`. fnm auto-switches when you `cd` into the project folder if shell
integration is configured.

```powershell
# First time setup
fnm install 24.14.1
fnm use 24.14.1
npm install
```

### Dev Container

The `.devcontainer/devcontainer.json` sets up Python 3.11 + Node 20 + .NET 9. It
bind-mounts the MO2 mods, profiles, overwrite, and game Data folders **read-only** so
container scripts can read real mod files without MO2 needing to be active.

Mounted paths inside the container:

| Host path | Container path | Env var |
|-----------|---------------|---------|
| `{{MO2_INSTANCE_PATH}}/mods` | `/skyrim/mods` | `SKYRIM_MODS_DIR` |
| `{{MO2_INSTANCE_PATH}}/profiles` | `/skyrim/profiles` | `SKYRIM_PROFILES_DIR` |
| `{{MO2_INSTANCE_PATH}}/overwrite` | `/skyrim/overwrite` | `SKYRIM_OVERWRITE_DIR` |
| `{{MO2_INSTANCE_PATH}}/Game Root/Data` | `/skyrim/game-data` | `SKYRIM_GAME_DATA_DIR` |

Open in VS Code and select "Reopen in Container" to use the containerized environment.

---

## MO2 / xEditLib Integration

### Critical: Always Launch Through MO2

Python scripts that call `XEditLib.dll` **must** be launched through MO2's executable
list. If run outside MO2, xEditLib cannot see the virtualized mod files or the full
load order.

**MO2 executable entry:**
- Binary: `C:\<project-path>\.venv\Scripts\python.exe`
- Arguments: `esp_runner\run_conversion.py`
- Start in: `C:\<project-path>`

This ensures the correct isolated Python interpreter is used and the MO2 VFS is active.

### Rootbuilder

Rootbuilder manages root-level game files outside the Data folder. It is unrelated to
the Python/Node tooling and does not need to be considered during script execution.

---

---

## Dependencies

### requirements.txt (container + dev)

```
esplugin==4.0.0
pydantic==2.6.0
cattrs==23.2.0
PyYAML==6.0.1
pytest==8.0.0
pytest-cov==4.1.0
ruff==0.3.0
mypy==1.9.0
```

### requirements-windows.txt (Windows execution only)

```
pywin32==306
# xEditLib Python wrapper — add when confirmed
```

### package.json dependencies

```
fast-xml-parser  — FOMOD ModuleConfig.xml generation and validation
ajv              — JSON schema validation for conversion_plan.json
zod              — runtime schema validation
```
---

## Modding Tools

### Container side

| Tool | Purpose | Usage |
|------|---------|-------|
| **esplugin** (Python) | Validate plugin metadata: masters, FormID ranges, overlap, record count | `import esplugin` — see `examples/inspect-esp.py` |
| **Spriggit** (.NET) | ESP ↔ YAML/JSON round-trip — read, diff, and author records as text | `dotnet tool run spriggit serialize --InputPath <esp> --OutputPath <dir> --GameRelease SkyrimSE --PackageName Spriggit.Yaml.Skyrim` |
| **Node.js** | FOMOD generation, JSON schema validation | `fast-xml-parser`, `ajv`, `zod` — see `examples/` |

Spriggit is installed as a .NET local tool via `dotnet tool restore` — no manual installation needed.

### Windows only

These tools require Windows and must **not** be used for tasks the container can handle.

| Tool | Purpose | Usage |
|------|---------|-------|
| **XEditLib.dll** | Load-order-dependent ESP reads and writes via FFI | Load with koffi in Node.js (see below) — must run through MO2 |
| **Champollion** | Decompile Papyrus `.pex` → `.psc` | `tools/Champollion/Champollion.exe input.pex` |
| **Caprica** | Compile Papyrus `.psc` → `.pex` | `tools/Caprica/Caprica.exe --game skyrim --import "{{MO2_INSTANCE_PATH}}/Game Root/Data/Scripts/Source" input.psc` — add `--import` for each mod's `Scripts/Source/` folder as needed |

Install Windows tools into `tools/` inside the toolkit directory. See the [xeditlib](https://github.com/WingedGuardian/xeditlib) repo for XEditLib setup.

## XEditLib.dll API — Windows Only

> **Requires Windows + MO2 VFS.** Do not use for tasks that Spriggit or esplugin can handle.
> See `docs/container-vs-windows.md` for the decision guide.

The DLL is Delphi-compiled. These quirks caused hours of debugging:

1. **All strings are UCS-2/UTF-16LE** (Delphi `PWideChar`), never UTF-8:
   ```js
   function wcb(s) { const b = Buffer.alloc((s.length+1)*2,0); b.write(s,0,'ucs2'); return b; }
   ```

2. **`InitXEdit()` and `CloseXEdit()` are VOID**, not bool. Declaring them as bool corrupts the call stack.

3. **`WordBool` = `uint16`** (2 bytes), not bool/uint8.

4. **String return pattern**: Functions don't return strings directly. They write a length to a `PInteger` param, then you call `GetResultString(buffer, len)` to retrieve the actual value:
   ```js
   function getString(fn) {
       const lenBuf = Buffer.alloc(4, 0);
       fn(lenBuf);
       const len = lenBuf.readInt32LE(0);
       if (len < 1) return '';
       const strBuf = Buffer.alloc(len * 2, 0);
       GetResultString(strBuf, len);
       return strBuf.toString('utf16le', 0, len * 2);
   }
   ```

5. **Game mode enum**: gmFNV=0, gmFO3=1, gmTES4=2, gmTES5=3, **gmSSE=4** (use this for Skyrim VR), gmFO4=5

6. **Registry requirement**: XEditLib reads game path from `HKLM\SOFTWARE\WOW6432Node\Bethesda Softworks\Skyrim Special Edition` (the SSE key, not the VR key, because game mode 4 = SSE). For a stock game setup this key must point to `{{MO2_INSTANCE_PATH}}/\Game Root\` — not the original Steam path.

7. **xelib.js wrapper**: See [xeditlib on GitHub](https://github.com/WingedGuardian/xeditlib) for the full wrapper with all 163 functions.

## INI Config Hierarchy

Settings load in this order (later overrides earlier):
1. `Skyrim.ini` -- base settings
2. `SkyrimVR.ini` -- VR-specific overrides
3. `SkyrimPrefs.ini` -- user preferences (loaded last)

## Nexus Mod Research (Standing Rule)

**Always search a mod's Nexus mod page before investigating it.** Check the description, tutorials/articles, comments, and bug reports before going in blind. This saves enormous time -- most issues have been seen and documented by other users.

## Knowledgebase

`KNOWLEDGEBASE.md` (project root) is the master reference for all discovered quirks, gotchas, and cross-version differences. **Always consult it before making changes** to avoid repeating past mistakes.

**Standing instruction**: After every debugging session, mod investigation, or web research, extract any new facts (engine quirks, VR vs SSE differences, API gotchas, tool limitations) and add them to KNOWLEDGEBASE.md. We learn from everything we come into contact with.

## Top Gotchas (Always In Context)

These are the most dangerous/common pitfalls. Consult `KNOWLEDGEBASE.md` for full details.

1. **RemoveSpell doesn't fire OnEffectFinish** -- use `DispelSpell` when cleanup logic exists
2. **All effects on a spell must have the same casting type** -- mismatches cause silent failure
3. **VMAD editing is fragile** -- use `GetFormFromFile()` to minimize properties; xEdit can't add scripts to VMAD
4. **PlayIdle fails in VR** -- VRIK overrides skeleton IK; bypass with timed Papyrus scripts
5. **Wait() unreliable under 100ms** -- merge sub-100ms gaps; use `RegisterForSingleUpdate` when possible
6. **SSE != VR** for: camera, skeleton, collision, UI, input, SKSE addresses, physics (60Hz->90Hz)
7. **ESL FormIDs must be in xx000800-xx000FFF** -- exceeding = crash or data corruption
8. **Loose files always override BSAs** -- check for loose file conflicts before assuming BSA content wins
9. **Condition OR has precedence over AND** -- `A AND B OR C` != what you'd expect
10. **Non-auto properties don't restore from master on save/load** -- they stay blank
11. **PreWEAPON/PreSHIELD skeleton nodes cause CTD in VR** -- must be removed
12. **ONAM required for ESM temp record overrides** -- missing ONAM = game silently ignores overrides
13. **SetVehicle causes HMD desync in VR** -- avoid entirely
14. **GoToState("") in OnUnload -> Self=None crash** -- move to OnLoad instead
15. **Navmesh creation is CK-only** -- xEdit can only delete, never recreate

## xelib Dry-Run Convention

All ESP modifications via xelib scripts must follow this two-pass workflow:
1. **Read-only pass**: load the ESP, log what would change (records added/modified/removed), print to console -- do NOT call `SaveFile()`
2. **User reviews** the proposed changes
3. **Write pass**: only after user approval, run again with `SaveFile()` enabled

This prevents accidental ESP corruption. The hook system blocks direct ESP writes, but xelib operates through Bash and can write via `SaveFile()`.

## Safety Rules

Hooks in `.claude/settings.json` enforce these automatically:

### Hard blocked (cannot proceed)
- Deleting the game installation directory or config directory
- Deleting Bethesda registry keys
- Directly writing to ESP/ESM/ESL/BSA/BA2 files (use xelib or modding tools)

### Requires user confirmation
- **Any edit to ANY file** in the game directory or config directory (catch-all)
- Papyrus scripts (`.psc`, `.pex`)
- Skyrim INI files (Skyrim.ini, SkyrimVR.ini, SkyrimPrefs.ini)
- SKSE plugin configs (`Data/SKSE/Plugins/*.ini`)
- Load order files (loadorder.txt, plugins.txt)
- Any `rm`, `mv`, `cp`, redirect, or `sed -i` touching game/config directories
- Any bash command referencing plugin/archive files

### General rules
- **Always review changes before applying** -- this is a delicate install
- Never modify ESP/ESM files directly -- use xelib programmatically or Spriggit
- MO2 manages load order -- direct edits to loadorder.txt/plugins.txt in the profile folder may be overwritten by MO2
- User is knowledgeable about Skyrim modding and INI settings

### Safety improvement loop
After every session, near-miss, or unexpected outcome, evaluate whether a new hook, expanded protection, or knowledgebase entry could have prevented or caught the issue. Propose new hooks when a pattern of risk emerges -- not reactively after damage, but proactively when you notice a gap. Document proposed hooks in the "Hook Candidates" section of `KNOWLEDGEBASE.md` even if not immediately implemented.

### Audit trail
- Every file edit is auto-backed up to `.claude/backups/` with timestamp
- An audit log at `.claude/backups/AUDIT_LOG.txt` records every file touched, when, and by which tool

## Confidence Levels (Mandatory)

**Before proposing ANY change** to game files, configs, scripts, or ESP records, you MUST:

1. **State a confidence level** (0-100%) for each proposed change
2. **List assumptions** that the confidence level depends on
3. **Investigate before acting**: Check the knowledgebase, read relevant source files, and web-search for Skyrim/VR-specific quirks before committing to an approach. Skyrim has many built-in bugs and version-specific differences -- things frequently do NOT work as expected.
4. **Target >= 90% confidence** before touching anything. If below 90%, document what's uncertain and what additional research would raise it.
5. **Never assume Skyrim SE behavior = Skyrim VR behavior.** Always verify VR-specific differences.

### Confidence scale
| Range | Meaning | Action |
|-------|---------|--------|
| 95-100% | Verified via testing, docs, or authoritative source | Proceed with user confirmation |
| 80-94% | Strong evidence but not fully verified | Proceed with caveats noted |
| 60-79% | Reasonable assumption, some unknowns | Research more before proceeding |
| < 60% | Speculative | Do NOT proceed -- investigate first |

### Investigation checklist (before any change)
- [ ] Consulted `KNOWLEDGEBASE.md` for known quirks
- [ ] Read the actual source files involved
- [ ] Checked if VR differs from SSE for this feature
- [ ] Web-searched for known issues with this approach
- [ ] Considered rollback path if the change breaks something
- [ ] Evaluated whether this task reveals a gap in current hook coverage
