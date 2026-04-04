# Skyrim VR Claude Code Modding Toolkit

An AI-assisted Skyrim modding environment for power users. Claude Code handles the mechanical work — porting mods across versions, inspecting and editing ESPs, debugging scripts, and building simple mods from scratch — with safety hooks, pre-loaded engine knowledge, and every tool pre-configured.

Built from hundreds of hours of hands-on Skyrim VR mod development.

---

## What Is Claude Code?

[Claude Code](https://claude.ai/code) is an AI assistant by Anthropic that runs directly on your computer. Unlike ChatGPT or regular Claude chat, it can **read your files, run commands, edit configs, execute scripts -- and do the mechanical work of modding for you** -- all with your permission. Think of it as having a modding expert sitting next to you who can actually touch your files.

This toolkit teaches Claude Code everything it needs to know about Skyrim VR modding, and adds safety rails so it can't accidentally break your install.

It's not perfect, and it will require some trial and error — especially for complex mods from scratch. But for the tedious parts of modding, it's significantly faster than doing it yourself.

---

## What You Get

This isn't a guide that tells you what to install and configure yourself. It's a **complete, ready-to-run modding environment** -- every tool pre-calibrated, every known Skyrim quirk already documented, every footgun already identified and protected against. Extract it into your game folder, paste one prompt, and you're working.

### A Toolset Built and Tested for Skyrim

Skyrim modding is full of undocumented engine quirks, version-specific differences, and tools that silently fail. This toolkit was built and tested on a live **Skyrim VR** install, but the knowledge, hooks, and scripts work across all versions — SE, AE, VR, and even LE where applicable. The knowledgebase includes version-specific sections so Claude knows what differs and what doesn't.

The clearest example: **xeditlib**. XEditLib.dll is the engine inside SSEEdit/xEdit -- the most powerful ESP editing tool in the Skyrim modding ecosystem. Getting it working from Node.js (so Claude Code could actually read and write ESP files) required cracking open the Delphi FFI layer and fixing a cascade of subtle bugs: strings encoded as UCS-2 instead of UTF-8, `InitXEdit()` silently corrupting the call stack when declared wrong, booleans that are actually 2-byte integers, a non-obvious two-step string-return pattern. None of this is documented anywhere. We debugged it, fixed it, and published the working wrapper as [xeditlib](https://github.com/WingedGuardian/xeditlib) on npm so you never have to deal with any of it. Claude Code can now read any ESP file and write new ones -- something that wouldn't work at all before this toolkit.

### Everything Included

- **600+ lines of Skyrim modding knowledge** -- Papyrus quirks, version-specific differences, xEdit pitfalls, engine bugs, and more (including VR-specific sections). Loaded into every Claude session automatically.
- **Safety hooks** -- Claude asks permission before editing any game file, won't touch ESP/ESM files directly, and automatically backs up everything it modifies with a full audit trail.
- **Confidence system** -- Claude rates its confidence (0-100%) and lists its assumptions before proposing any change. No guessing, no "this should work."
- **ESP editing via Spriggit** -- Serialize any ESP to human-readable YAML, edit it directly, deserialize back. Claude's native file editing works on YAML out of the box — no FFI layer, no scripting, and changes diff cleanly in git.
- **ESP analysis via xeditlib** -- Programmatic inspection, diffing, and bulk queries across records. The hard Delphi FFI work is already done. ([xeditlib on GitHub](https://github.com/WingedGuardian/xeditlib))
- **NIF mesh tools** -- Inspect, retexture, scale, fix eye-ghosting, and verify mesh files. Detect VR-breaking skeleton nodes.
- **BSA archive tools** -- Full read/write/merge/diff on BSA archives. Extract individual files, create new archives, update contents.
- **Audio processing** -- Extract, convert, and create Skyrim voice files (FUZ/XWM/WAV).
- **MCM menu generation** -- Programmatically create SkyUI mod configuration menus with toggles, sliders, and pages.
- **Save file analysis** -- Decompress and binary-scan .ess saves. Search for orphaned scripts, count effect accumulation, check mod footprint, detect save bloat.
- **Dry-run workflow** -- All ESP and asset changes go through a preview pass first. Claude shows you exactly what it will do before touching anything.
- **Claude Code skills** -- Slash commands like `/inspect-esp MyMod.esp`, `/port-to-vr`, and `/create-mod` that trigger guided workflows. Auto-loading context that injects critical Skyrim gotchas when Claude works with game files.
- **Auto-setup** -- One prompt installs prerequisites, configures paths, sets up hooks, and optionally installs modding tools (Champollion, Caprica, Spriggit, AutoMod CLI). No manual configuration.

---

## Setup (4 Steps)

### Step 1: Install Claude Code

1. **Sign up** at [claude.ai](https://claude.ai) if you don't have an account
2. **Subscribe** to Claude Pro ($20/month) or Max ($100/month) -- required for Claude Code
3. **Install Claude Code** -- pick one:

   **Desktop App (easiest):**
   Download from [claude.ai/code](https://claude.ai/code), install, open it.

   **Command Line:**
   Install [Node.js](https://nodejs.org/) (click the big green LTS button, install it).
   Then open **Windows Terminal** (search "Terminal" in Start menu) and run:
   ```
   npm install -g @anthropic-ai/claude-code
   ```

### Step 2: Extract This Toolkit Into a Folder

The toolkit lives **independently** from your game. If you use MO2, do **not** extract into your game folder.

1. Download this mod from Nexus (Manual Download)
2. Choose a folder for the toolkit -- somewhere outside your game directory, e.g.:
   - `C:\Users\YourName\Documents\SkyrimModding\Claude Code Setup\`
3. **Extract the zip into that folder**
   - Right-click the downloaded zip > Extract All > paste your chosen path > Extract

> **Vortex users:** Extract directly into your Skyrim VR folder as before. The toolkit will work from there.

### Step 3: Open Claude Code in the Toolkit Folder

**Desktop App:** Open Claude Code. Click the folder/path area and navigate to the toolkit folder (where you extracted in Step 2).

**Command Line:** Open Windows Terminal and type (replace with YOUR path):
```
cd "C:\Users\YourName\Documents\SkyrimModding\Claude Code Setup"
claude
```

### Step 4: Paste This Prompt

Copy this entire line and paste it into Claude Code:

```
I just installed the Skyrim Claude Code Modding Toolkit into this folder. Run "bash setup.sh" to set
  everything up. Install any missing prerequisites (jq, Node.js) for me. After setup, ask me which optional modding
  tools I'd like (xeditlib, Champollion, Caprica, Spriggit, AutoMod CLI) and install the ones I pick. AutoMod CLI adds
  NIF mesh editing, BSA archive tools, audio processing, and MCM menu generation. Be sure to tailor the environment
  specifically to my Skyrim version and install (may or may not be VR). Explain everything in plain English and ask me any
  questions you may need to.
```

Claude handles the rest. It will configure paths, install dependencies, set up the safety hooks, and walk you through optional tool installation. Just answer any questions it asks.

**That's it. You're done.**

---

## Using It

From now on, whenever you open Claude Code in your Skyrim VR folder, the toolkit loads automatically. Just start talking:

This toolkit fits best as a **power user tool** — particularly strong for investigating, porting, and debugging existing mods, making targeted record edits, and scripting assistance. For simpler mods (spells, powers, item records, short scripts), Claude can build these from scratch. For complex systems, expect some iteration.

---

**Porting mods across Skyrim versions (SSE to VR, Oldrim to SSE, SSE to AE, etc.):**
- *"This mod was made for SSE. Examine every VR incompatibility and fix each one"*
- *"Decompile this script and tell me what breaks in VR and how to fix it"*
- *"This mod uses PlayIdle() on the player -- that doesn't work in VR. Rewrite it to use timed Papyrus instead"*
- *"Port this SSE combat script to VR -- check the knowledgebase for anything that behaves differently"*

**Debugging and troubleshooting:**
- *"I'm getting a CTD when I equip this weapon in VR. Can you fix it?"*
- *"NPC dialogue stopped showing up after I installed a mod. Help me debug it."*
- *"Check my SkyrimVR.ini for settings that might cause problems"*
- *"NPC dialogue stopped showing up after I installed a mod. Help me debug it."*

**Making changes:**
- *"Set fUpdateBudgetMS to 2.0 in SkyrimVR.ini"*
- *"Help me create an ESP that adds a new spell"*
- *"Port this SSE Papyrus script to work in VR"*

**Building new mods from scratch (simpler ones work best):**
- *"Build me a power that lets me slow time for 10 seconds with a 60-second cooldown"*
- *"Create an ESP that adds a new two-handed katana with custom reach and a fire enchantment"*
- *"Write a Papyrus script that tracks how many enemies I've killed and shows a notification every 10 kills"*
- *"Make a spell that blinds nearby enemies for 5 seconds using a custom magic effect"*
- *"I want a Lesser Power that equips my best sword and shield automatically when I enter combat"*

**Whatever else you want:**
- *"Add a FOMOD installer to my mod"*
- *"Write a MCM menu config for my mod using SkyUI VR"*
- *"Scan my load order for mods known to break in VR"*
- *"My mod works in SSE but crashes in VR on startup -- let's figure out why"*

If it involves Skyrim, Papyrus, ESPs, INI files, scripts, or mod files of any kind, just ask. Claude has the full context of how the engine works and will figure out the path forward. It's significantly faster than doing it yourself — especially for the tedious parts.

---

## What's in the Knowledgebase?

The toolkit includes `KNOWLEDGEBASE.md` -- 600+ lines of documented knowledge:

| Topic | What's Covered |
|-------|---------------|
| **Papyrus Scripting** | Script lifecycle, threading, RemoveSpell vs DispelSpell, Wait() reliability, magic effects, performance pitfalls |
| **VR vs SSE Differences** | SKSE versions, skeleton CTDs, camera, physics (60Hz vs 90Hz), UI, input, mod compatibility matrix |
| **xEdit / ESP Editing** | VMAD fragility, plugin types (ESM/ESP/ESL), load order, BSA priority, navmesh, cleaning caveats |
| **Engine Quirks** | Ability spells, vanilla bugs, SKSE plugin compatibility warnings |
| **VR Controllers** | Why SKSE Input API fails in VR, VRIK API as the correct method, code examples |
| **Debugging** | Debug.Notification limitations, Debug.Trace patterns, concurrent script handling |

This knowledge grows over time -- Claude adds new discoveries as you work together.

---

## Safety Features

| Protection | What It Does |
|-----------|-------------|
| **Command guard** | Blocks deleting game files or registry keys. Confirms all file operations in game directories. |
| **File guard** | Blocks direct writes to ESP/ESM/BSA files. Confirms all other game file edits. |
| **Auto-backup** | Copies every file to `.claude/backups/` before modification, with full audit log. |
| **Confidence system** | Claude must rate confidence 0-100% and list assumptions before any change. |
| **Investigation-first** | Claude checks the knowledgebase and web-searches before touching anything. |

---

## FAQ

**Q: Does this work with flat Skyrim SE (non-VR)?**
A: Yes! The knowledgebase covers both. VR-specific sections only apply to VR. Safety hooks and workflow work for either.

**Q: Does this work with MO2?**
A: Yes. Extract the toolkit into a standalone folder (not inside the game directory). During setup, provide your MO2 base path, stock game root, and active profile name. Claude will look for INIs and load order in your MO2 profile folder, and mod files in your MO2 mods folder.

**Q: I use Root Builder -- where does the toolkit look for files?**
A: INIs and load order come from your MO2 profile. Individual mod files come from `<MO2>/mods/<mod-name>/`. Root Builder files (ENB, SKSE DLLs) live in `<MO2>/mods/<mod-name>/Root/`. xelib scripts need absolute paths to ESPs since MO2's virtual filesystem isn't active outside of MO2.

**Q: Can Claude break my mods or save files?**
A: The safety hooks prevent this. Claude can't edit ESP/ESM files directly, must ask permission for any edit, and backs everything up. But always keep your own backups too.

**Q: I'm getting "jq not found"**
A: Open Windows Terminal and run: `winget install jqlang.jq` -- then restart Claude Code.

**Q: How do I update the toolkit?**
A: Download the new version from Nexus and extract over the old one. Your knowledgebase additions are preserved.

---

## Contributing

Found a new Skyrim VR quirk? PRs welcome on [GitHub](https://github.com/WingedGuardian/skyrimvr-claude-toolkit) -- especially additions to `KNOWLEDGEBASE.md`.

## License

MIT -- see [LICENSE](LICENSE).

## Credits

- [xeditlib](https://github.com/WingedGuardian/xeditlib) -- Node.js wrapper for XEditLib.dll
- [zEdit](https://github.com/z-edit/zedit) -- Source of XEditLib.dll
- [Claude Code](https://claude.ai/code) by Anthropic
