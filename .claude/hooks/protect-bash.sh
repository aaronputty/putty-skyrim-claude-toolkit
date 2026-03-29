#!/bin/bash
# Protect against destructive or file-modifying bash commands in Skyrim VR modding environment
#
# SETUP: Update the JQ variable below to point to your jq installation.
#   Install jq: winget install jqlang.jq
#   Find path:  where jq

JQ="{{JQ_PATH}}"

INPUT=$(cat /dev/stdin)
COMMAND=$(echo "$INPUT" | "$JQ" -r '.tool_input.command // empty')

deny() { "$JQ" -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'; exit 0; }
ask()  { "$JQ" -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'; exit 0; }

# === HARD BLOCK ===
# Prevent deleting the game installation directory
echo "$COMMAND" | grep -qiE 'rm\s+(-[a-z]*f[a-z]*\s+)?["'"'"']?(C:/|/c/).*Skyrim' && deny "BLOCKED: Cannot delete the game installation directory."
# Prevent deleting Skyrim config directory
echo "$COMMAND" | grep -qiE 'rm\s+(-[a-z]*f[a-z]*\s+)?["'"'"']?(C:/|/c/).*Documents/My Games/Skyrim' && deny "BLOCKED: Cannot delete the Skyrim VR config directory."
# Prevent deleting Bethesda registry keys
echo "$COMMAND" | grep -qiE '(reg\s+delete|Remove-ItemProperty.*Bethesda)' && deny "BLOCKED: Cannot delete Bethesda registry keys."

# === CONFIRM -- destructive commands ===
echo "$COMMAND" | grep -qiE 'rm\s.*(Skyrim|/Data/)' && ask "Deleting files in game directory -- confirm: $COMMAND"

# === CONFIRM -- any command that modifies files in game/config directories ===
echo "$COMMAND" | grep -qiE '(mv|cp|move|copy)\s.*(Skyrim|/Data/|/My Games/Skyrim)' && ask "Moving/copying files in game directory -- confirm: $COMMAND"
echo "$COMMAND" | grep -qiE '>\s*["'"'"']?(C:/|/c/).*Skyrim' && ask "Redirecting output to game/config directory -- confirm: $COMMAND"
echo "$COMMAND" | grep -qiE 'sed\s+-i.*(Skyrim|/Data/|/My Games/Skyrim)' && ask "In-place edit in game directory -- confirm: $COMMAND"

# === CONFIRM -- plugin/archive/load order references ===
echo "$COMMAND" | grep -qiE '\.(esp|esm|esl|bsa|ba2)\b' && ask "Command references plugin/archive files -- confirm: $COMMAND"
echo "$COMMAND" | grep -qiE '(loadorder\.txt|plugins\.txt)' && ask "Command references load order -- confirm: $COMMAND"

exit 0
