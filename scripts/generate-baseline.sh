#!/bin/bash
# Generate SHA256 checksums for critical game files
# Run manually to create a baseline snapshot for drift detection
#
# Usage: bash scripts/generate-baseline.sh
#
# For MO2 + Root Builder setups, set these env vars or edit the defaults below:
#   TOOLKIT_DIR  -- path to this toolkit folder
#   MO2_BASE     -- MO2 installation folder
#   GAME_ROOT    -- stock game folder (Root Builder copy)
#   PROFILE_NAME -- active MO2 profile name

TOOLKIT_DIR="${TOOLKIT_DIR:-$(pwd)}"
MO2_BASE="${MO2_BASE:-C:/Games/Skyrim25}"
GAME_ROOT="${GAME_ROOT:-{{MO2_INSTANCE_PATH}}/Game Root}"
PROFILE_NAME="${PROFILE_NAME:-{{ACTIVE_PROFILE_NAME}}}"

PROFILE_DIR="$MO2_BASE/profiles/$PROFILE_NAME"
OUTPUT="$TOOLKIT_DIR/.claude/baseline_checksums.txt"

echo "Generating baseline checksums..."
echo "Toolkit dir:  $TOOLKIT_DIR"
echo "Game root:    $GAME_ROOT"
echo "Profile dir:  $PROFILE_DIR"
echo ""

echo "# Baseline checksums generated $(date '+%Y-%m-%d %H:%M:%S')" > "$OUTPUT"
echo "# Compare with: diff <(bash scripts/generate-baseline.sh --stdout) .claude/baseline_checksums.txt" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# INI configs (MO2 profile folder)
echo "## INI Configs (MO2 profile: $PROFILE_NAME)" >> "$OUTPUT"
for f in "$PROFILE_DIR"/*.ini; do
    [ -f "$f" ] && sha256sum "$f" >> "$OUTPUT"
done

# SKSE plugin configs -- check overwrite folder and stock game
echo "" >> "$OUTPUT"
echo "## SKSE Plugin Configs (overwrite)" >> "$OUTPUT"
find "$MO2_BASE/overwrite/SKSE/Plugins" -maxdepth 1 -name "*.ini" -exec sha256sum {} \; >> "$OUTPUT" 2>/dev/null

echo "" >> "$OUTPUT"
echo "## SKSE Plugin Configs (stock game root)" >> "$OUTPUT"
find "$GAME_ROOT/Data/SKSE/Plugins" -maxdepth 1 -name "*.ini" -exec sha256sum {} \; >> "$OUTPUT" 2>/dev/null

# ESP/ESM files in stock game Data/ (vanilla + DLC masters)
echo "" >> "$OUTPUT"
echo "## Plugin Files in Stock Game Root" >> "$OUTPUT"
find "$GAME_ROOT/Data" -maxdepth 1 \( -name "*.esp" -o -name "*.esm" -o -name "*.esl" \) -exec sha256sum {} \; >> "$OUTPUT" 2>/dev/null

# Load order files (MO2 profile)
echo "" >> "$OUTPUT"
echo "## Load Order Files (MO2 profile)" >> "$OUTPUT"
[ -f "$PROFILE_DIR/loadorder.txt" ] && sha256sum "$PROFILE_DIR/loadorder.txt" >> "$OUTPUT"
[ -f "$PROFILE_DIR/plugins.txt" ] && sha256sum "$PROFILE_DIR/plugins.txt" >> "$OUTPUT"

# Toolkit files
echo "" >> "$OUTPUT"
echo "## Toolkit Files" >> "$OUTPUT"
sha256sum "$TOOLKIT_DIR/CLAUDE.md" >> "$OUTPUT" 2>/dev/null
sha256sum "$TOOLKIT_DIR/KNOWLEDGEBASE.md" >> "$OUTPUT" 2>/dev/null

LINES=$(wc -l < "$OUTPUT")
echo "Baseline written to $OUTPUT ($LINES lines)"
echo "Note: MO2 mod folder ESPs are not checksummed here -- check individual mod folders as needed."
echo "Re-run anytime to compare against current state."
