# Putty Sentinel Mages — Addon Series

Armor distribution addons for the "Putty Sentinel Mages" series. Each addon wraps a third-party outfit mod in leveled lists and wires it into the Elementalist distribution system via Skypatcher.

## Addon structure

Every addon follows this pattern:

```
<Mod folder>/
  PuttyElementalist<Name>Addon.esp
  SKSE/Plugins/SkyPatcher/leveledList/<AddonName>/<AddonName>.ini
```

### ESP contents (all ESL-flagged, FormIDs start at 000800)

1. **Per-slot leveled lists** — `CalculateFromAllLevelsLessThanOrEqualPlayer`, one per equip slot. Each entry is a variant of that slot (e.g. Black vs White jacket). Single-variant mods still get individual per-slot lists for extensibility.
2. **Master outfit list** — `UseAll`, contains all per-slot lists. This is the record that Skypatcher injects into a distribution list.
3. **One OTFT record** (`POFT_<Name>`) — references the master list; available for direct outfit assignment if needed.

### Skypatcher config format

Configs live at `SKSE/Plugins/SkyPatcher/leveledList/<AddonName>/<AddonName>.ini`.

Use EditorIDs directly (no `plugin|FormID` prefix):
```ini
filterByLLs=PNecromancerOutfitList:addToLLs=LYoRHa559SOutfit~1~1
```
Format: `filterByLLs=<target list EditorID>:addToLLs=<item EditorID>~<level>~<count>`

For NPC leveled lists (LChar* style), use `filterByLLNPCs` instead of `filterByLLs`.

### Building an ESP

Spriggit YAML source goes in `C:/tmp/<AddonName>/`. Deserialize with:
```
dotnet tool run spriggit deserialize --InputPath C:/tmp/<AddonName> --OutputPath C:/tmp/<AddonName>.esp
```
Requires a `spriggit-meta.json` in the source folder:
```json
{"PackageName": "Spriggit.Yaml.Skyrim", "Version": "0.40.0", "Release": "SkyrimSE", "ModKey": "<AddonName>.esp"}
```

---

## Distribution lists (`PuttyElementalistArmorIntegration.esp`)

| EditorID | FormID | Distributed to |
|---|---|---|
| PNecromancerOutfitList | 000821 | Necromancers |
| PCultistOutfitList | 000824 | Cultists |
| PConjurerOutfitList | 000823 | Conjurers |
| PDarkWarriorOutfitList | 000813 | Dark Warriors |
| PSpellSwordKnightOutfitList | 00081D | Spellsword Knights |

---

## Completed addons

### YoRHa Type 55-9S (`ksa_YoRHa559S.esp`)
- **Mod folder:** `Putty Sentinel Mages - Yorha Type 55 95 Outfit Addon`
- **ESP:** `PuttyElementalistYoRHa559SAddon.esp`
- **Master list:** `LYoRHa559SOutfit` → `PNecromancerOutfitList`
- **Type:** Clothing, two color variants

| Slot | EditorID | Black FormID | White FormID |
|---|---|---|---|
| Body | LYoRHa559SJackets | 000800 | 0002D4 |
| Hands | LYoRHa559SGloves | 000801 | 0002D5 |
| Feet | LYoRHa559SBoots | 000802 | 0002D6 |
| Head (hair slot) | LYoRHa559SHeads | 000D6A | 0002D7 |

---

### Kreiste's Summoner Outfit (`kho_wol_smn.esp`)
- **Mod folder:** `Putty Sentinel Mages - Kreiste's Summoner Outfit Addon`
- **ESP:** `PuttyElementalistSummonerOutfitAddon.esp`
- **Master list:** `LSummonerOutfit` → `PConjurerOutfitList`
- **Type:** Clothing, single variant ("Evoker's" set)

| Slot | EditorID | FormID |
|---|---|---|
| Body | LSummonerCoats | 000808 |
| Feet | LSummonerBoots | 000805 |
| Hands | LSummonerWristlets | 000806 |
| Head | LSummonerHorns | 000807 |
| Pelvis | LSummonerWaistguards | 00080A |

---

### Kreiste's Mascot Outfits (`kho_wol_mct.esp`)
- **Mod folder:** `Putty Sentinel Mages - Kreiste's Mascot Outfits Addon`
- **ESP:** `PuttyElementalistMascotOutfitsAddon.esp`
- **Master list:** `LMascotOutfit` → `PCultistOutfitList` + `PDarkWarriorOutfitList`
- **Type:** Clothing, two character variants (Aldy / Parthy)

| Slot | EditorID | Aldy FormID | Parthy FormID |
|---|---|---|---|
| Body | LMascotArmors | 000805 | 00081C |
| Feet | LMascotBoots | 000804 | 00081B |
| Hands | LMascotGauntlets | 000806 | 00081D |
| Head | LMascotHelmets | 000808 | 00081E |
| Shield | LMascotShields | 000824 (Heaven's Edge) | 000828 (Lux) |

---

### Fierce Deity Armor (`ksa_lnk7.esp`)
- **Mod folder:** `Putty Sentinel Mages - Fierce Deity Armor Addon`
- **ESP:** `PuttyElementalistFierceDeityArmorAddon.esp`
- **Master list:** `LFierceDeityOutfit` → `PDarkWarriorOutfitList`
- **Type:** Clothing, single variant

| Slot | EditorID | FormID |
|---|---|---|
| Body | LFierceDeityGarbs | 00080A |
| Feet | LFierceDeityBoots | 000809 |
| Hands | LFierceDeityBracers | 00080B |
| Head (circlet slot) | LFierceDetyCaps | 00080C |

---

## Next task: enchanted variants

Create enchanted versions of each armor set and distribute them alongside the base versions, level-gated within the per-slot lists.

**Key decisions to make before starting:**
- Which enchantments for which sets (thematic: Summoner → Conjuration, Fierce Deity → warrior, YoRHa → ?, Mascot → ?)
- Whether enchanted variants are new ARMO records or existing ARMOs with ENCH attached (new records is standard)
- Level threshold for enchanted entries (e.g. base at level 1, enchanted at level 20+)
- Whether to add level-gated entries to existing per-slot lists or create a parallel `Enchanted` sub-list per slot
- All new ARMO records must use FormVersion 44 (SSE/VR)
