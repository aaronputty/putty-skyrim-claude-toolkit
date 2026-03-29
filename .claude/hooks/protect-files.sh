#!/bin/bash
# Protect ALL files from unnoticed edits. Every edit requires explicit confirmation
# unless it's in our own workspace (.claude/hooks, .claude/plans, .claude/backups).
#
# SETUP: Update the JQ variable below to point to your jq installation.

JQ="{{JQ_PATH}}"

INPUT=$(cat /dev/stdin)
FILE_PATH=$(echo "$INPUT" | "$JQ" -r '.tool_input.file_path // empty')

[ -z "$FILE_PATH" ] && exit 0

deny() { "$JQ" -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'; exit 0; }
ask()  { "$JQ" -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'; exit 0; }

# === HARD BLOCK -- binary plugin/archive files ===
echo "$FILE_PATH" | grep -qiE '\.(esp|esm|esl|bsa|ba2)$' && deny "BLOCKED: Cannot directly write to plugin/archive files. Use xelib or modding tools."

# === WHITELIST -- our own workspace (no confirmation needed) ===
echo "$FILE_PATH" | grep -qiE '\.claude/(hooks|plans|backups|memory)/' && exit 0
echo "$FILE_PATH" | grep -qiE '\.claude/projects/' && exit 0

# === HIGH-PRIORITY CONFIRM (specific message) ===
echo "$FILE_PATH" | grep -qiE '(Skyrim\.ini|SkyrimVR\.ini|SkyrimPrefs\.ini|SkyrimCustom\.ini)$' && ask "EDITING SKYRIM CONFIG: $FILE_PATH"
echo "$FILE_PATH" | grep -qiE 'Data/SKSE/Plugins/.*\.ini$' && ask "EDITING SKSE PLUGIN CONFIG: $FILE_PATH"
echo "$FILE_PATH" | grep -qiE '(loadorder\.txt|plugins\.txt)$' && ask "EDITING LOAD ORDER FILE: $FILE_PATH"
echo "$FILE_PATH" | grep -qiE '\.(pex|psc)$' && ask "EDITING PAPYRUS SCRIPT: $FILE_PATH"

# === CATCH-ALL -- any file in game directory or config directory ===
echo "$FILE_PATH" | grep -qiE '(Skyrim VR|Skyrim Special Edition|My Games/Skyrim)' && ask "Editing file in game/config directory: $FILE_PATH"

exit 0
