# ESP Inspection Script -- CONTAINER SIDE, READ-ONLY
#
# Validates plugin metadata with esplugin, then serializes records to YAML
# with Spriggit for deep inspection. Works entirely from the read-only
# /skyrim/mods mount -- no MO2 VFS required.
#
# Usage (in devcontainer):
#   python examples/inspect-esp.py /skyrim/mods/MyMod/MyMod.esp
#
# The SKYRIM_MODS_DIR env var is set automatically in the devcontainer.
# Requires: esplugin (pip install -r requirements.txt)
#           spriggit  (dotnet tool restore)

import os
import sys
import subprocess
import tempfile
from pathlib import Path

try:
    import esplugin
except ImportError:
    print("ERROR: esplugin not installed. Run: pip install -r requirements.txt")
    sys.exit(1)


def inspect_plugin(esp_path: Path) -> None:
    print(f"=== ESP Inspection: {esp_path.name} ===\n")

    # ------------------------------------------------------------------
    # esplugin: fast metadata and validity check
    # ------------------------------------------------------------------
    print("--- Plugin Metadata (esplugin) ---")
    plugin = esplugin.Plugin(esplugin.GameId.SkyrimSe, str(esp_path))
    plugin.parse(load_header_only=False)

    print(f"  Valid:        {plugin.is_valid()}")
    print(f"  Description:  {plugin.description()!r}")
    print(f"  Masters:      {plugin.masters()}")
    print(f"  Record count: {plugin.record_and_group_count()}")
    print(f"  Is light:     {plugin.is_light_plugin()}")
    print(f"  Is medium:    {plugin.is_medium_plugin()}")
    print()

    # ------------------------------------------------------------------
    # Spriggit: serialize to YAML for deep record inspection
    # ------------------------------------------------------------------
    print("--- Record Groups (Spriggit) ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [
                "dotnet", "tool", "run", "spriggit", "serialize",
                "--InputPath", str(esp_path),
                "--OutputPath", tmpdir,
                "--GameRelease", "SkyrimSE",
                "--PackageName", "Spriggit.Yaml.Skyrim",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  Spriggit failed:\n{result.stderr.strip()}")
            print("  (Is 'dotnet tool restore' done? Is Spriggit in .config/dotnet-tools.json?)")
            return

        yaml_root = Path(tmpdir)
        record_dirs = sorted(d for d in yaml_root.iterdir() if d.is_dir())

        if not record_dirs:
            print("  No record groups found.")
            return

        for group_path in record_dirs:
            yaml_files = list(group_path.glob("**/*.yaml"))
            print(f"  {group_path.name:<12} {len(yaml_files)} record(s)")

        # Show a sample of the first non-empty group
        first = next((d for d in record_dirs if list(d.glob("**/*.yaml"))), None)
        if first:
            samples = sorted(first.glob("**/*.yaml"))[:3]
            print(f"\n  Sample from [{first.name}]:")
            for f in samples:
                print(f"    {f.relative_to(yaml_root)}")
            if len(list(first.glob("**/*.yaml"))) > 3:
                print("    ...")

    print()
    print("Tip: to inspect full record YAML, run Spriggit directly:")
    print(f'  dotnet tool run spriggit serialize \\')
    print(f'    --InputPath "{esp_path}" \\')
    print(f'    --OutputPath ./output/{esp_path.stem} \\')
    print(f'    --GameRelease SkyrimSE \\')
    print(f'    --PackageName Spriggit.Yaml.Skyrim')
    print()
    print("=== Inspection complete ===")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        mods_dir = os.environ.get("SKYRIM_MODS_DIR", "/skyrim/mods")
        print("Usage: python examples/inspect-esp.py <path-to-esp>")
        print(f"  Mod ESPs are mounted at: {mods_dir}/<mod-name>/<ModName>.esp")
        sys.exit(1)

    esp = Path(sys.argv[1])
    if not esp.exists():
        print(f"ERROR: File not found: {esp}")
        sys.exit(1)
    if esp.suffix.lower() not in {".esp", ".esm", ".esl"}:
        print(f"WARNING: {esp.name} doesn't look like a plugin file — continuing anyway")

    inspect_plugin(esp)
