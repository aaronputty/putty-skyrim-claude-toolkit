# Container vs. Windows — Tool Routing Guide

Default to the container for any task. Only cross to Windows/MO2 when the task
genuinely requires the Windows DLL or the active MO2 virtual filesystem.

---

## Decision Table

| Task | Where | Tool |
|------|-------|------|
| Validate plugin metadata (masters, FormIDs, overlap) | Container | `esplugin` (Python) |
| Inspect ESP records | Container | `spriggit serialize` → YAML |
| Diff two ESPs | Container | `spriggit serialize` both → `diff -r` |
| Author new ESP records | Container | Spriggit YAML → `spriggit deserialize` |
| Generate FOMOD XML | Container | Node.js (`fast-xml-parser`) |
| Validate JSON schemas | Container | Node.js (`ajv`, `zod`) |
| Unit test mod logic | Container | `pytest` |
| Read INI / load order files | Container | Read from `/skyrim/profiles/` mount |
| Load-order-dependent ESP edits | Windows (MO2) | xelib (`examples/inspect-esp.js`, etc.) |
| Override chain resolution across full load order | Windows (MO2) | xelib |
| Decompile Papyrus `.pex` → `.psc` | Windows | Champollion |
| Compile Papyrus `.psc` → `.pex` | Windows | Caprica |

---

## Why xelib is Windows-only

MO2's virtual filesystem is only active while MO2 is running. xelib scripts launched
outside MO2 cannot see the merged load order — they only see ESPs that physically exist
in the stock game's `Data/` folder.

Spriggit and esplugin read individual `.esp` files by path. Because the devcontainer
mounts `/skyrim/mods` read-only, they reach any installed mod's ESP directly without
MO2 needing to be active.

---

## Spriggit vs. xelib

| Capability | Spriggit | xelib |
|-----------|----------|-------|
| Read records | Yes (YAML) | Yes |
| Write records | Yes (YAML round-trip) | Yes |
| Resolve override chain | No — single file only | Yes (needs MO2 VFS) |
| See all masters' records | No | Yes |
| Cross-platform | Yes (.NET 9) | No (Windows DLL) |
| Works outside MO2 | Yes | No |
| Best for | Inspection, diffs, simple creation | Load-order-dependent edits |

If in doubt, try Spriggit first. Only escalate to xelib if Spriggit can't express
the operation.

---

## Spriggit command reference

```bash
# Serialize ESP → YAML (inspection or editing)
dotnet tool run spriggit serialize \
  --InputPath /skyrim/mods/MyMod/MyMod.esp \
  --OutputPath ./output/MyMod \
  --GameRelease SkyrimSE \
  --PackageName Spriggit.Yaml.Skyrim

# Deserialize YAML → ESP (after editing YAML)
dotnet tool run spriggit deserialize \
  --InputPath ./output/MyMod \
  --OutputPath ./output/MyMod.esp

# Diff two ESPs (serialize both, then diff)
dotnet tool run spriggit serialize --InputPath Original.esp --OutputPath /tmp/orig --GameRelease SkyrimSE --PackageName Spriggit.Yaml.Skyrim
dotnet tool run spriggit serialize --InputPath Modified.esp --OutputPath /tmp/mod  --GameRelease SkyrimSE --PackageName Spriggit.Yaml.Skyrim
diff -r /tmp/orig /tmp/mod
```

---

## esplugin quick reference

```python
import esplugin

plugin = esplugin.Plugin(esplugin.GameId.SkyrimSe, "/skyrim/mods/MyMod/MyMod.esp")
plugin.parse(load_header_only=False)

print(plugin.is_valid())           # True/False
print(plugin.masters())            # ['Skyrim.esm', ...]
print(plugin.record_and_group_count())
print(plugin.is_light_plugin())    # ESL flag
print(plugin.is_medium_plugin())   # ESM medium flag
```

See `examples/inspect-esp.py` for a complete script combining both tools.

---

## When xelib is the right call

Only cross to Windows/xelib when you need one of these:

1. **Override chain resolution** — "what does the winning override of record X look
   like given this specific load order?"
2. **Cross-plugin record operations** — adding masters, copying records between files
   where the source needs to be resolved through the VFS
3. **Executing a `conversion_plan.json`** — the `esp_runner/` scripts consume plans
   produced by the container side and execute them via xelib

Everything else belongs in the container.
