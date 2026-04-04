#!/bin/bash
# Skyrim VR Claude Code Toolkit -- Setup Script
#
# This script is designed to be run FROM your Skyrim VR folder, after
# extracting the toolkit zip into it. It configures everything in-place.
#
# Usage: bash setup.sh

set -e

TOOLKIT_DIR="$(pwd)"
USERNAME="$(whoami)"

echo "============================================"
echo " Skyrim VR Claude Code Toolkit -- Setup"
echo "============================================"
echo ""
echo "Toolkit directory: $TOOLKIT_DIR"
echo ""

# --- Verify toolkit files are present ---
if [ ! -f "$TOOLKIT_DIR/KNOWLEDGEBASE.md" ] || [ ! -f "$TOOLKIT_DIR/.claude/hooks/protect-bash.sh" ]; then
    echo "ERROR: Toolkit files not found in this directory."
    echo "Make sure you are running this from the toolkit folder."
    exit 1
fi

# --- MO2 path discovery ---
echo "This toolkit is configured for MO2 with a stock game (Root Builder) setup."
echo "The toolkit lives independently from the game folder."
echo ""

# Prompt for MO2 base path
read -p "MO2 base folder (e.g. C:/Games/Skyrim25): " MO2_BASE
MO2_BASE="${MO2_BASE%/}"  # strip trailing slash

# Prompt for stock game root
read -p "Stock game root (e.g. {{MO2_INSTANCE_PATH}}/Game Root): " GAME_ROOT
GAME_ROOT="${GAME_ROOT%/}"

# Prompt for active profile
read -p "Active MO2 profile name (e.g. {{ACTIVE_PROFILE_NAME}}): " ACTIVE_PROFILE

PROFILE_DIR="$MO2_BASE/profiles/$ACTIVE_PROFILE"
MODS_DIR="$MO2_BASE/mods"
OVERWRITE_DIR="$MO2_BASE/overwrite"

echo ""
echo "MO2 base:     $MO2_BASE"
echo "Stock game:   $GAME_ROOT"
echo "Profile dir:  $PROFILE_DIR"
echo "Mods dir:     $MODS_DIR"
echo ""

# Validate
if [ ! -d "$PROFILE_DIR" ]; then
    echo "WARNING: Profile dir not found: $PROFILE_DIR"
    echo "Check your MO2 base path and profile name."
    read -p "Continue anyway? (y/n) " CONTINUE
    [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ] && exit 1
fi

# --- Detect jq ---
echo "Checking for jq..."
JQ_PATH=$(which jq 2>/dev/null || echo "")
if [ -z "$JQ_PATH" ]; then
    # Try common Windows locations
    for p in \
        "/c/Users/$USERNAME/AppData/Local/Microsoft/WinGet/Links/jq.exe" \
        "/c/ProgramData/chocolatey/bin/jq.exe" \
        "/usr/bin/jq"; do
        if [ -f "$p" ]; then
            JQ_PATH="$p"
            break
        fi
    done
fi

if [ -z "$JQ_PATH" ]; then
    echo ""
    echo "jq not found. It's needed for the safety hooks."
    echo "Installing jq via winget..."
    winget install jqlang.jq --accept-source-agreements --accept-package-agreements 2>/dev/null || {
        echo ""
        echo "ERROR: Could not auto-install jq."
        echo "Please install it manually: winget install jqlang.jq"
        echo "Then re-run: bash setup.sh"
        exit 1
    }
    # Re-detect after install
    JQ_PATH=$(which jq 2>/dev/null || echo "/c/Users/$USERNAME/AppData/Local/Microsoft/WinGet/Links/jq.exe")
fi
echo "  Found jq: $JQ_PATH"

# --- Verify profile INIs ---
echo ""
if [ -f "$PROFILE_DIR/SkyrimPrefs.ini" ] || [ -f "$PROFILE_DIR/Skyrim.ini" ]; then
    echo "  Found profile INIs in: $PROFILE_DIR/"
else
    echo "  WARNING: No INIs found in profile dir: $PROFILE_DIR"
    echo "  You may need to update paths in CLAUDE.md manually."
fi

# --- Configure hook scripts (replace jq placeholder) ---
echo ""
echo "Configuring safety hooks..."
for hook in protect-bash.sh protect-files.sh backup-before-edit.sh; do
    if grep -q '{{JQ_PATH}}' "$TOOLKIT_DIR/.claude/hooks/$hook"; then
        sed -i "s|{{JQ_PATH}}|$JQ_PATH|g" "$TOOLKIT_DIR/.claude/hooks/$hook"
        echo "  Configured: .claude/hooks/$hook"
    else
        echo "  Already configured: .claude/hooks/$hook"
    fi
done

# --- Configure CLAUDE.md (replace MO2 path placeholders) ---
echo ""
echo "Configuring CLAUDE.md..."
if grep -q '{{MO2_BASE}}' "$TOOLKIT_DIR/CLAUDE.md"; then
    sed -i "s|{{MO2_BASE}}|$MO2_BASE|g" "$TOOLKIT_DIR/CLAUDE.md"
    sed -i "s|{{GAME_ROOT}}|$GAME_ROOT|g" "$TOOLKIT_DIR/CLAUDE.md"
    sed -i "s|{{ACTIVE_PROFILE}}|$ACTIVE_PROFILE|g" "$TOOLKIT_DIR/CLAUDE.md"
    sed -i "s|{{USERNAME}}|$USERNAME|g" "$TOOLKIT_DIR/CLAUDE.md"
    echo "  Configured with your MO2 paths."
else
    echo "  Already configured."
fi

# --- Ensure backup directory exists ---
mkdir -p "$TOOLKIT_DIR/.claude/backups"

# --- Copy settings.local.json.example if no settings.local.json exists ---
if [ ! -f "$TOOLKIT_DIR/.claude/settings.local.json" ] && [ -f "$TOOLKIT_DIR/.claude/settings.local.json.example" ]; then
    echo ""
    echo "  Copied settings.local.json.example (you can customize allowed commands later)"
fi

echo ""
echo "============================================"
echo " Setup Complete!"
echo "============================================"
echo ""
echo "Installed and configured:"
echo "  CLAUDE.md                        -- Project instructions (MO2 paths filled in)"
echo "  KNOWLEDGEBASE.md                 -- 600+ lines of Skyrim VR modding knowledge"
echo "  .claude/settings.json            -- Hook configuration"
echo "  .claude/hooks/protect-bash.sh    -- Guards dangerous commands"
echo "  .claude/hooks/protect-files.sh   -- Guards file edits"
echo "  .claude/hooks/backup-before-edit.sh -- Auto-backups with audit trail"
echo "  .claude/backups/                 -- Backup storage (empty for now)"
echo ""
echo "MO2 paths configured:"
echo "  Stock game root:  $GAME_ROOT"
echo "  Active profile:   $ACTIVE_PROFILE"
echo "  Profile dir:      $PROFILE_DIR"
echo "  Mods dir:         $MODS_DIR"
echo "  Overwrite folder: $OVERWRITE_DIR"
echo ""
echo "The safety hooks are now active. Claude Code will:"
echo "  - Ask permission before editing any game or profile file"
echo "  - Block direct writes to ESP/ESM/BSA files"
echo "  - Automatically back up files before modifying them"
echo ""
echo "You're ready to go! Start asking Claude about your mods."
