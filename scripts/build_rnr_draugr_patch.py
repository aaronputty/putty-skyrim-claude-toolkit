"""
Build RnR Bandits -> Putty Humanoid Draugr patch ESP (container-side).

Reads serialized Spriggit YAML for:
  - PuttyHumanoidDraugrTemplates.esp  (source of PUT_ appearance templates)
  - Rogues 'n Raiders.esp             (source bandit NPCs)

For each humanoid bandit NPC, generates a Spriggit YAML override that:
  - Sets Template -> best-matching PUT_ template (matched on gender, role, level)
  - Sets TemplateFlags: [ModelAnimation]   (inherit skeleton/animations only)
  - Sets Race -> PuttyDraugrRace
  - Sets Voice -> DraugrVoice
  - Clears face appearance data (HeadParts, FaceMorph, TintLayers, etc.)
  - Keeps everything else: name, stats, perks, inventory, outfit, combat style, AI

Usage:
  python scripts/build_rnr_draugr_patch.py            # dry run (no files written)
  python scripts/build_rnr_draugr_patch.py --commit   # write output YAML

Then to produce the binary ESP:
  dotnet tool run spriggit -- deserialize \\
    --InputPath output/PuttyRnRHumanoidDraugrBandits \\
    --OutputPath output/PuttyRnRHumanoidDraugrBandits.esp
"""

import copy
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import re

import yaml

# ---------------------------------------------------------------------------
# YAML helpers: preserve Spriggit hex literals (e.g. Fluff: 0x000000)
# ---------------------------------------------------------------------------
# PyYAML loads "0x000000" as int(0) and dumps it back as "0" (1 char), which
# Spriggit's ReadBytes() rejects ("not a multiple of 2").  We keep hex scalars
# as a thin str subclass so the original representation survives the round-trip.
_HEX_RE = re.compile(r"^0x[0-9a-fA-F]+$")


class _HexStr(str):
    """str subclass that remembers it should be written as a plain hex scalar."""


class _SpriggitLoader(yaml.SafeLoader):
    pass


def _int_constructor_preserve_hex(loader, node):
    """Int constructor that returns _HexStr for hex literals instead of int."""
    value = loader.construct_scalar(node)
    if _HEX_RE.match(value):
        return _HexStr(value)
    return int(value, 0)


# Override the built-in int constructor so hex scalars survive the round-trip.
_SpriggitLoader.add_constructor(
    "tag:yaml.org,2002:int", _int_constructor_preserve_hex
)


class _SpriggitDumper(yaml.Dumper):
    pass


def _hex_representer(dumper, data):
    # Output as a plain (unquoted) scalar so Spriggit reads it as raw hex bytes.
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="")


_SpriggitDumper.add_representer(_HexStr, _hex_representer)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
TOOLKIT_DIR = Path(__file__).resolve().parent.parent

# Spriggit-serialized input directories (produced by build step, not checked in)
TEMPLATES_YAML_DIR = Path("C:/Temp/spriggit-templates")
RNR_YAML_DIR = Path("C:/Temp/spriggit-rnr")

OUTPUT_DIR = TOOLKIT_DIR / "output" / "PuttyRnRHumanoidDraugrBandits"
OUTPUT_MOD_NAME = "PuttyRnRHumanoidDraugrBandits.esp"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PUTTY_DRAUGR_RACE = "00098E:PuttyHumanoidDraugrTemplates.esp"
DRAUGR_VOICE = "01F1CD:Skyrim.esm"

HUMANOID_RACES = {
    "013742:Skyrim.esm",  # Dunmer
    "013744:Skyrim.esm",  # Imperial
    "013746:Skyrim.esm",  # Nord
    "013748:Skyrim.esm",  # Redguard
    "013743:Skyrim.esm",  # Altmer
    "013747:Skyrim.esm",  # Orc
    "013749:Skyrim.esm",  # Bosmer
    "013745:Skyrim.esm",  # Khajiit
    "013740:Skyrim.esm",  # Argonian
}

# RnR class FormKey -> combat role used for template matching
RNR_CLASS_TO_ROLE = {
    "28DEAE:Rogues 'n Raiders.esp": "Archer",       # Bandit Archer
    "39A679:Rogues 'n Raiders.esp": "Mage",          # Bandit Battlemage
    "158ECF:Rogues 'n Raiders.esp": "Warrior2H",     # Bandit Berserker
    "56C5FC:Rogues 'n Raiders.esp": "Warrior1H",     # Bandit Bloodletter
    "57B916:Rogues 'n Raiders.esp": "Boss",           # Bandit Bloodletter Boss
    "AAA6F5:Rogues 'n Raiders.esp": "Warrior1H",     # Bandit Brawler
    "EA97B0:Rogues 'n Raiders.esp": "Warrior1H",     # Bandit Bruiser
    "186853:Rogues 'n Raiders.esp": "Warrior2H",     # Bandit Brute
    "52F9B2:Rogues 'n Raiders.esp": "Warrior1H",     # Bandit Enforcer
    "33A22E:Rogues 'n Raiders.esp": "Mage",           # Bandit Mage
    "5CC955:Rogues 'n Raiders.esp": "Archer",         # Bandit Manhunter
    "45AEBE:Rogues 'n Raiders.esp": "Warrior2H",     # Bandit Ravager
    "31BB5D:Rogues 'n Raiders.esp": "Archer",         # Bandit Rogue
    "2EA949:Rogues 'n Raiders.esp": "Warrior1H",     # Bandit Shadowblade
    "186852:Rogues 'n Raiders.esp": "Warrior1H",     # Bandit Tank
    "08937B:Rogues 'n Raiders.esp": "Warrior1H",     # Bandit Warrior 1H
    "0DA3F3:Rogues 'n Raiders.esp": "Warrior2H",     # Bandit Warrior 2H
    "54A7F0:Rogues 'n Raiders.esp": "Warrior2H",     # Bandit Wildling
    "4D9824:Rogues 'n Raiders.esp": "Warrior1H",     # Unresolved — default 1H
    "A7CDB4:Rogues 'n Raiders.esp": "Boss",           # Prophet/Cultist Boss
    "140B5C:Rogues 'n Raiders.esp": "Boss",
    "8690EB:Rogues 'n Raiders.esp": "Warrior1H",
    "68EA40:Rogues 'n Raiders.esp": "Mage",
    "A034C6:Rogues 'n Raiders.esp": "Warrior2H",
    "4DE933:Rogues 'n Raiders.esp": "Boss",
    "4DE932:Rogues 'n Raiders.esp": "Warrior1H",
}

# Fields that carry original-race appearance data — cleared in overrides
APPEARANCE_FIELDS = [
    "HeadParts", "HeadTexture", "FaceMorph", "TintLayers",
    "HairColor", "TextureLighting", "FaceParts",
]

ESP_MASTERS = [
    "Skyrim.esm",
    "Dawnguard.esm",
    "Dragonborn.esm",
    "Playable Draugr.esp",
    "PuttyHumanoidDraugrTemplates.esp",
    "Rogues 'n Raiders.esp",
]

# ---------------------------------------------------------------------------
# Template loading and matching
# ---------------------------------------------------------------------------

def _infer_template_role(edid: str) -> str:
    eu = edid.upper()
    if "MISSILE" in eu or "ARCHER" in eu or "BOW" in eu:
        return "Archer"
    if "2H" in eu or "BERSERKER" in eu:
        return "Warrior2H"
    if "1H" in eu or "ONEHANDED" in eu:
        return "Warrior1H"
    if "MAGE" in eu or "MAGIC" in eu:
        return "Mage"
    if "WARLORD" in eu or "OVERLORD" in eu or "DEATHLORD" in eu or "BOSS" in eu:
        return "Boss"
    return "Warrior1H"  # fallback for ambiguous names


def load_template_index(templates_dir: Path) -> dict:
    """
    Returns {(gender, role): [(level, formkey, edid), ...]} sorted by level.
    """
    index: dict = defaultdict(list)
    for f in sorted((templates_dir / "Npcs").iterdir()):
        if f.suffix != ".yaml":
            continue
        data = yaml.load(f.read_text(encoding="utf-8"), Loader=_SpriggitLoader)
        cfg = data.get("Configuration", {}) or {}
        flags = cfg.get("Flags", []) or []
        gender = "F" if "Female" in flags else "M"
        level_obj = cfg.get("Level", {}) or {}
        level = int(level_obj.get("Level", level_obj.get("LevelMult", 1)) or 1)
        edid = data.get("EditorID", "")
        formkey = data.get("FormKey", "")
        role = _infer_template_role(edid)
        index[(gender, role)].append((level, formkey, edid))
    for key in index:
        index[key].sort()
    return dict(index)


def find_best_template(
    index: dict, gender: str, role: str, level: int
) -> tuple[int, str, str]:
    """
    Returns (template_level, formkey, edid) for the closest level match.

    Tries both genders for the requested role and picks whichever has the
    closer level match — so a female with no good female template at her
    level will be matched to the nearest male template instead.
    Falls back to Warrior1H if the role has no templates at all.
    """
    # Gather all candidates for this role across both genders
    candidates = []
    for try_gender in (gender, "M" if gender == "F" else "F"):
        key = (try_gender, role)
        if key in index:
            candidates.extend(index[key])

    if not candidates:
        # Role has no templates at all - fall back to Warrior1H
        for try_gender in (gender, "M"):
            key = (try_gender, "Warrior1H")
            if key in index:
                candidates.extend(index[key])

    if not candidates:
        raise RuntimeError(f"No template found for (role={role}, lvl={level})")

    # Nearest level; prefer lower on equal distance
    return min(candidates, key=lambda x: (abs(x[0] - level), -x[0]))


# ---------------------------------------------------------------------------
# NPC loading
# ---------------------------------------------------------------------------

def _effective_level(data: dict) -> int:
    """Extract a single level value from an NPC's Configuration.Level block."""
    cfg = data.get("Configuration", {}) or {}
    level_obj = cfg.get("Level", {}) or {}
    obj_type = level_obj.get("MutagenObjectType", "")
    if obj_type == "PcLevelMult":
        # Use CalcMinLevel as proxy; fall back to 1
        return int(cfg.get("CalcMinLevel", 1) or 1)
    return int(level_obj.get("Level", 1) or 1)


def load_rnr_bandits(rnr_dir: Path) -> list[tuple[Path, dict]]:
    """Load all humanoid zzRnR_ NPC YAML files."""
    results = []
    for f in sorted((rnr_dir / "Npcs").iterdir()):
        if f.suffix != ".yaml":
            continue
        edid = f.stem.split(" - ")[0]
        if not edid.startswith("zzRnR_"):
            continue
        data = yaml.load(f.read_text(encoding="utf-8"), Loader=_SpriggitLoader)
        if data.get("Race", "") not in HUMANOID_RACES:
            continue
        results.append((f, data))
    return results


# ---------------------------------------------------------------------------
# Override generation
# ---------------------------------------------------------------------------

def build_override(rnr_data: dict, template_formkey: str) -> dict:
    """
    Deep-copy the RnR NPC and apply all conversion changes.
    """
    override = copy.deepcopy(rnr_data)

    # Appearance template link (ModelAnimation only — keeps RnR stats/AI/inventory)
    override["Template"] = template_formkey
    cfg = override.setdefault("Configuration", {})
    cfg["TemplateFlags"] = ["ModelAnimation"]

    # Race and attack animations -> draugr
    override["Race"] = PUTTY_DRAUGR_RACE
    if "AttackRace" in override:
        override["AttackRace"] = PUTTY_DRAUGR_RACE

    # Voice -> draugr
    override["Voice"] = DRAUGR_VOICE

    # Clear original-race appearance data
    for field in APPEARANCE_FIELDS:
        override.pop(field, None)

    return override


# ---------------------------------------------------------------------------
# Output writing
# ---------------------------------------------------------------------------

def _formkey_to_filename(edid: str, formkey: str) -> str:
    """'DB668D:Rogues n Raiders.esp' -> 'EditorID - DB668D_Rogues n Raiders.esp.yaml'"""
    return f"{edid} - {formkey.replace(':', '_')}.yaml"


def write_record_data(output_dir: Path) -> None:
    # Write as a template string to preserve exact Spriggit formatting (e.g. "0.40")
    masters_yaml = "\n".join(
        f"  - Master: {m}\n    FileSize: 0" for m in ESP_MASTERS
    )
    content = f"""SpriggitSource:
  PackageName: Spriggit.Yaml.Skyrim
  Version: '0.40'
ModKey: {OUTPUT_MOD_NAME}
GameRelease: SkyrimSE
ModHeader:
  Flags:
  - Small
  Author: ''
  MasterReferences:
{masters_yaml}
"""
    (output_dir / "RecordData.yaml").write_text(content, encoding="utf-8")


def write_spriggit_meta(output_dir: Path) -> None:
    meta = {
        "PackageName": "Spriggit.Yaml.Skyrim",
        "Version": "0.40.0",
        "Release": "SkyrimSE",
        "ModKey": OUTPUT_MOD_NAME,
    }
    (output_dir / "spriggit-meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    dry_run = "--commit" not in sys.argv

    print("=== RnR Bandits -> Humanoid Draugr Patch Builder ===")
    print(f"Mode: {'DRY RUN (no files written)' if dry_run else 'COMMIT'}\n")

    # --- Load templates ---
    print("Loading PUT_ templates...")
    if not TEMPLATES_YAML_DIR.exists():
        print(f"ERROR: {TEMPLATES_YAML_DIR} not found.")
        print("Run Spriggit serialize on PuttyHumanoidDraugrTemplates.esp first.")
        sys.exit(1)
    template_index = load_template_index(TEMPLATES_YAML_DIR)
    total_tpl = sum(len(v) for v in template_index.values())
    print(f"  {total_tpl} templates across {len(template_index)} role/gender buckets\n")

    # --- Load RnR bandits ---
    print("Loading RnR bandit NPCs...")
    if not RNR_YAML_DIR.exists():
        print(f"ERROR: {RNR_YAML_DIR} not found.")
        print("Run Spriggit serialize on 'Rogues 'n Raiders.esp' first.")
        sys.exit(1)
    bandits = load_rnr_bandits(RNR_YAML_DIR)
    print(f"  {len(bandits)} humanoid bandit NPCs loaded\n")

    # --- Plan conversions ---
    print("Planning conversions...")
    conversions = []
    fallbacks: list[str] = []

    for source_file, data in bandits:
        edid = data.get("EditorID", "")
        cfg = data.get("Configuration", {}) or {}
        flags = cfg.get("Flags", []) or []
        gender = "F" if "Female" in flags else "M"
        level = _effective_level(data)
        cls = str(data.get("Class", ""))
        role = RNR_CLASS_TO_ROLE.get(cls, "Warrior1H")

        tpl_level, tpl_formkey, tpl_edid = find_best_template(
            template_index, gender, role, level
        )

        # Flag cases where template level differs significantly from source level
        if abs(tpl_level - level) > 10 and level > 1:
            fallbacks.append(
                f"  {gender} {role:12} lvl={level:2} -> {tpl_edid} (tpl lvl={tpl_level})  [{edid}]"
            )

        conversions.append({
            "source_file": source_file,
            "data": data,
            "gender": gender,
            "level": level,
            "role": role,
            "tpl_level": tpl_level,
            "tpl_formkey": tpl_formkey,
            "tpl_edid": tpl_edid,
        })

    # --- Summary ---
    role_counts = Counter(c["role"] for c in conversions)
    gender_counts = Counter(c["gender"] for c in conversions)
    print(f"  Total: {len(conversions)} NPCs")
    print(f"  Gender: {dict(gender_counts)}")
    print("  By role:")
    for role, cnt in sorted(role_counts.items(), key=lambda x: -x[1]):
        print(f"    {cnt:4d}  {role}")

    if fallbacks:
        print(f"\n  Note — {len(fallbacks)} NPCs matched to a template >10 levels away:")
        for msg in fallbacks[:10]:
            print(msg)
        if len(fallbacks) > 10:
            print(f"  ... and {len(fallbacks) - 10} more")

    if dry_run:
        print("\nSample conversions (first 15):")
        for c in conversions[:15]:
            edid = c["data"].get("EditorID", "")
            print(
                f"  {c['gender']} {c['role']:12} lvl={c['level']:2} -> "
                f"{c['tpl_edid']} (tpl lvl={c['tpl_level']})"
            )
        print(f"\n*** DRY RUN complete — {len(conversions)} conversions planned ***")
        print("Run with --commit to write output files.")
        return

    # --- Write output ---
    print(f"\nWriting output to {OUTPUT_DIR} ...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    npc_out_dir = OUTPUT_DIR / "Npcs"
    npc_out_dir.mkdir(parents=True)

    for c in conversions:
        override = build_override(c["data"], c["tpl_formkey"])
        edid = override.get("EditorID", "")
        formkey = override["FormKey"]
        filename = _formkey_to_filename(edid, formkey)
        (npc_out_dir / filename).write_text(
            yaml.dump(override, Dumper=_SpriggitDumper, allow_unicode=True,
                      sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )

    write_record_data(OUTPUT_DIR)
    write_spriggit_meta(OUTPUT_DIR)

    print(f"  {len(conversions)} NPC override files written")
    print("  RecordData.yaml + spriggit-meta.json written")
    print(f"\nTo produce the binary ESP, run:")
    print(
        f'  dotnet tool run spriggit -- deserialize \\\n'
        f'    --InputPath "{OUTPUT_DIR}" \\\n'
        f'    --OutputPath "output/{OUTPUT_MOD_NAME}"'
    )
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
