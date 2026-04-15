"""
Generate Spriggit YAML + _MUS.ini for the Castlevania Music MTD conversion.

Scans music/ in the source mod, pairs finale tracks, maps paths to MUSC EditorIDs,
and writes:
  - /tmp/cv_spriggit/  (Spriggit YAML ready for deserialization)
  - /tmp/cv_mus.ini    (MTD ini)
  - /tmp/cv_summary.txt (human-readable mapping review)
"""

import os
import shutil
import json
from pathlib import Path
from collections import defaultdict

# ── Config ─────────────────────────────────────────────────────────────────────

SOURCE_MUSIC = Path("C:/Games/Skyrim25/mods/Castlevania Music Style Overhaul/music")
ESP_NAME     = "CastlevaniaMusic.esp"
SPRIGGIT_OUT = Path("C:/Users/miked/AppData/Local/Temp/cv_spriggit")
INI_OUT      = Path("C:/Users/miked/AppData/Local/Temp/cv_mus.ini")
SUMMARY_OUT  = Path("C:/Users/miked/AppData/Local/Temp/cv_summary.txt")

# Data-relative path prefix for MUST TrackFilename fields
DATA_PREFIX  = r"\Data\Music\Castlevania"

# FormID counter (starts at 0x800, matching existing mods)
FORM_ID_START = 0x800

# ── MUSC mapping ──────────────────────────────────────────────────────────────

# Returns (musc_editorid, skip_reason) — musc is None if track should be skipped
def get_musc(rel_path: str):
    """Map a relative path (from music/) to a MUSC EditorID."""
    p = rel_path.replace("\\", "/")
    parts = p.split("/")
    root = parts[0]
    fname = parts[-1].lower()

    # Skip: finale files are embedded in their parent MUST record
    if "_finale" in fname:
        return None, "finale — embedded in parent MUST record"

    # ── combat ────────────────────────────────────────────────────────────────
    if root == "combat":
        if "boss" in fname:
            return "MUSCombatBoss", None
        return "MUSCombat", None

    # ── DLC1 ──────────────────────────────────────────────────────────────────
    if root == "dlc1":
        if len(parts) > 1 and "dawnguard" in parts[1].lower():
            return "MUSCombatBossDLC1", None
        if len(parts) > 1 and parts[1] == "dungeon":
            if "vampirecastle" in fname:
                return "MUSCastle", None
            if "soulcairn" in fname:
                return "MUSDungeonDLC1SoulCairn", None
        if len(parts) > 1 and parts[1] == "explore":
            return "MUSExploreDLC1FalmerValley", None
        return None, f"DLC1 — unrecognised path: {p}"

    # ── dread ─────────────────────────────────────────────────────────────────
    if root == "dread":
        if "discover" in fname:
            return "MUSDiscoverDread", None
        return "MUSDread", None

    # ── dungeon ───────────────────────────────────────────────────────────────
    if root == "dungeon":
        if len(parts) > 1:
            sub = parts[1]
            if sub == "cave":
                return "MUSDungeonCave", None
            if sub == "fort":
                return "MUSDungeonFort", None
            if sub == "ice":
                return "MUSDungeonIce", None
        return "MUSDungeon", None

    # ── explore ───────────────────────────────────────────────────────────────
    if root == "explore":
        if len(parts) == 2:
            # Flat file directly in explore/
            if "day" in fname:
                return "MUSExploreDay", None
            if "night" in fname:
                return "MUSExploreNight", None
            if "morning" in fname:
                return "MUSExploreMorning", None
            if "dusk" in fname:
                return "MUSExploreDusk", None
            return None, f"explore flat file — unrecognised: {fname}"
        if len(parts) > 1:
            sub = parts[1].lower()
            if sub == "forestfall":   return "MUSExploreForestFall", None
            if sub == "forestpine":   return "MUSExploreForestPine", None
            if sub == "mountain":     return "MUSExploreMountain", None
            if sub == "reach":        return "MUSExploreReach", None
            if sub == "snow":         return "MUSExploreSnow", None
            if sub == "tundra":       return "MUSExploreTundra", None
            if sub == "sovngarde":    return "MUSExploreSovngarde", None
            return None, f"explore subdir — unrecognised: {sub}"

    # ── tavern ────────────────────────────────────────────────────────────────
    if root == "tavern":
        return "MUSTavern", None

    # ── town ──────────────────────────────────────────────────────────────────
    if root == "town":
        if "village" in fname:
            return "MUSVillage", None
        return "MUSTownDay", None

    # ── reveal / reward / stinger ─────────────────────────────────────────────
    if root == "reveal":   return "MUSReveal", None
    if root == "reward":   return "MUSReward", None
    if root == "stinger":  return "MUSStinger", None

    # ── special ───────────────────────────────────────────────────────────────
    if root == "special":
        if "failure" in p:
            return "MUSFailure", None
        if "wordofpower" in fname:
            return "MUSWordWall", None
        if "maintheme" in fname or fname == "mus_intro.xwm":
            return None, "main menu / intro — skipped intentionally"
        if "cartintro" in fname:
            return None, "cart intro — skipped (one-shot cinematic)"
        return None, f"special — unrecognised: {fname}"

    # ── MBT (Miraak Boss Track) ───────────────────────────────────────────────
    if root == "MBT":
        return "MUSCombatBossDLC2Miraak", None

    # ── root-level files ──────────────────────────────────────────────────────
    if len(parts) == 1:
        if "castle_imperial"        in fname: return "MUSCastleImperial", None
        if "castle_stormcloaks"     in fname: return "MUSCastleStormcloaks", None
        if "discover_genericlocation" in fname: return "MUSDiscoverGenericLocation", None
        if "discover_highhrothgar"  in fname: return "MUSDiscoverHighHrothgar", None
        if "dlc2boatarrival"        in fname: return "MUSDragonbornBoatArrival", None
        if "dlc2apocrypha"          in fname: return "MUSApocrypha", None
        if "dlc2solstheim"          in fname: return "MUSExploreDragonborn", None
        if "levelup"                in fname: return "MUSLevelUp", None
        return None, f"root-level — unrecognised: {fname}"

    return None, f"unrecognised path: {p}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def to_data_path(rel_path: str) -> str:
    """Convert relative path (from music/) to \Data\Music\Castlevania\... form."""
    p = rel_path.replace("/", "\\")
    return DATA_PREFIX + "\\" + p


def editor_id(rel_path: str) -> str:
    """Derive an EditorID from the relative path."""
    stem = Path(rel_path).stem          # e.g. mus_combat_01
    # Sanitize
    safe = stem.replace("-", "_").replace(" ", "_")
    return f"cv_{safe}"


def fmt_form_id(n: int) -> str:
    return f"0x{n:X}"


def fmt_form_key(n: int, esp: str) -> str:
    return f"{n:06X}:{esp}"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Collect all xwm files
    all_xwm = sorted(
        str(p.relative_to(SOURCE_MUSIC)).replace("\\", "/")
        for p in SOURCE_MUSIC.rglob("*.xwm")
    )

    # Build finale lookup: stem_without_finale → finale_rel_path
    finale_map = {}
    for rp in all_xwm:
        stem = Path(rp).stem
        if "_finale" in stem:
            base_stem = stem.replace("_finale", "")
            base_dir  = str(Path(rp).parent).replace("\\", "/")
            finale_map[f"{base_dir}/{base_stem}"] = rp

    # Process tracks
    records = []   # list of dicts
    skipped = []   # (rel_path, reason)
    form_id = FORM_ID_START

    for rp in all_xwm:
        fname_stem = Path(rp).stem
        # Skip finale files (handled as part of parent record)
        if "_finale" in fname_stem:
            continue

        musc, skip_reason = get_musc(rp)
        if musc is None:
            skipped.append((rp, skip_reason or "no MUSC mapping"))
            continue

        # Check for a paired finale
        dir_part  = str(Path(rp).parent).replace("\\", "/")
        stem_key  = f"{dir_part}/{fname_stem}"
        finale_rp = finale_map.get(stem_key)

        rec = {
            "form_id":    form_id,
            "editor_id":  editor_id(rp),
            "track":      to_data_path(rp),
            "finale":     to_data_path(finale_rp) if finale_rp else None,
            "musc":       musc,
            "source":     rp,
        }
        records.append(rec)
        form_id += 1

    # ── Write Spriggit YAML ────────────────────────────────────────────────────

    if SPRIGGIT_OUT.exists():
        shutil.rmtree(SPRIGGIT_OUT)
    SPRIGGIT_OUT.mkdir(parents=True)
    (SPRIGGIT_OUT / "MusicTracks").mkdir()

    # spriggit-meta.json
    meta = {
        "PackageName": "Spriggit.Yaml.Skyrim",
        "Version": "0.40.0",
        "Release": "SkyrimSE",
        "ModKey": ESP_NAME,
    }
    (SPRIGGIT_OUT / "spriggit-meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    # RecordData.yaml (mod header)
    record_data = f"""SpriggitSource:
  PackageName: Spriggit.Yaml.Skyrim
  Version: 0.40
ModKey: {ESP_NAME}
GameRelease: SkyrimSE
ModHeader:
  Flags:
  - Small
  Author: ''
  MasterReferences:
  - Master: Skyrim.esm
    FileSize: 0
"""
    (SPRIGGIT_OUT / "RecordData.yaml").write_text(record_data, encoding="utf-8")

    # One YAML per MUST record
    for rec in records:
        fid_hex6 = f"{rec['form_id']:06X}"
        yaml_filename = f"{rec['editor_id']} - {fid_hex6}_{ESP_NAME}.yaml"
        yaml_path = SPRIGGIT_OUT / "MusicTracks" / yaml_filename

        lines = [
            f"FormKey: {fmt_form_key(rec['form_id'], ESP_NAME)}",
            f"EditorID: {rec['editor_id']}",
            "FormVersion: 44",
            "Type: SingleTrack",
            f"TrackFilename: {rec['track']}",
        ]
        if rec["finale"]:
            lines.append(f"FinaleFilename: {rec['finale']}")

        yaml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ── Write _MUS.ini ─────────────────────────────────────────────────────────

    # Group FormIDs by MUSC
    musc_to_records = defaultdict(list)
    for rec in records:
        musc_to_records[rec["musc"]].append(rec)

    ini_lines = [
        "; Castlevania Music Style Overhaul — MTD Additive Conversion",
        "; Adds Castlevania tracks to vanilla playlists without replacing them.",
        "; Uncertain MUSC EditorIDs are marked VERIFY — check MusicTypeDistributor.log",
        "; after first launch with bDumpMusicTypes=true.",
        "",
        "[General]",
    ]

    # Confident mappings first, then uncertain
    UNCERTAIN = {
        "MUSDungeonDLC1SoulCairn", "MUSExploreDLC1FalmerValley",
        "MUSDiscoverDread", "MUSExploreDay", "MUSExploreNight",
        "MUSExploreMorning", "MUSExploreDusk", "MUSExploreSovngarde",
        "MUSVillage", "MUSCastleImperial", "MUSCastleStormcloaks",
        "MUSDiscoverGenericLocation", "MUSDiscoverHighHrothgar",
        "MUSDragonbornBoatArrival", "MUSApocrypha", "MUSExploreDragonborn",
        "MUSLevelUp", "MUSReveal", "MUSReward", "MUSStinger",
        "MUSFailure", "MUSWordWall", "MUSCombatBossDLC2Miraak",
        "MUSTownDay",
    }

    for musc in sorted(musc_to_records.keys()):
        recs = musc_to_records[musc]
        form_ids_str = ", ".join(
            f"{fmt_form_id(r['form_id'])}~{ESP_NAME}"
            for r in recs
        )
        comment = "  ; VERIFY EditorID in log" if musc in UNCERTAIN else ""
        ini_lines.append(f"{musc} = {form_ids_str}{comment}")

    INI_OUT.write_text("\n".join(ini_lines) + "\n", encoding="utf-8")

    # ── Write summary ─────────────────────────────────────────────────────────

    summary_lines = [
        f"=== Castlevania MTD Conversion Summary ===",
        f"Total MUST records: {len(records)}",
        f"Skipped:            {len(skipped)}",
        f"FormID range:       {fmt_form_id(FORM_ID_START)} – {fmt_form_id(form_id - 1)}",
        "",
        "── MUSC breakdown ──",
    ]
    for musc, recs in sorted(musc_to_records.items()):
        flag = " [VERIFY]" if musc in UNCERTAIN else ""
        summary_lines.append(f"  {musc}{flag}: {len(recs)} track(s)")

    summary_lines += ["", "── Skipped files ──"]
    for path, reason in skipped:
        summary_lines.append(f"  {path}  →  {reason}")

    SUMMARY_OUT.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print("\n".join(summary_lines).encode("ascii", errors="replace").decode("ascii"))
    print(f"\nSpriggit YAML -> {SPRIGGIT_OUT}")
    print(f"INI            -> {INI_OUT}")


if __name__ == "__main__":
    main()
