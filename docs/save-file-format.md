# Civ 6 Save File Format

Reverse-engineered from `CHANDRAGUPTA 215 1520 AD.Civ6Save` (1,799,939 bytes).
Based on community tools ([pydt/civ6-save-parser](https://github.com/pydt/civ6-save-parser), [lucienmaloney/civ6save-editing](https://github.com/lucienmaloney/civ6save-editing)) plus original analysis.

## Overview

A `.Civ6Save` file has two parts:

```
[Uncompressed header ~390KB] [Zlib-compressed game data ~1.4MB → 16MB]
```

The header contains game configuration (speed, map, difficulty, localization JSON, installed leader/civ pools). The compressed section contains all game state: map tiles, fog-of-war, per-player timelines, city records, replay datasets, and modifier definitions.

## Header

Starts with magic bytes `CIV6`. Tagged key-value pairs using 4-byte marker IDs:

| Marker | Field | Type |
|--------|-------|------|
| `9D 2C E6 BD` | GAME_TURN | int32 |
| `99 B0 D9 05` | GAME_SPEED | string (e.g. `GAMESPEED_STANDARD`) |
| `40 5C 83 0B` | MAP_SIZE | string (e.g. `MAPSIZE_SMALL`) |

Type bytes after marker: `1`=bool, `2`=int32, `5`=string, `6`=UTF string, `0x0A`=array.

The header also contains the full leader/civilization pool (every installed DLC leader), NOT just the active players. Active players must be identified from game state data.

### Finding the Compressed Data

```python
mod_index = save_data.rfind(b'MOD_TITLE')
buf_start = save_data.index(b'\x78\x9c', mod_index)  # zlib magic
```

## Decompression

The compressed data uses **zlib in 64KB chunks with 4-byte spacers**. Standard `zlib.decompress()` fails.

```python
import zlib

buf_end = save_data.rfind(b'\x00\x00\xff\xff')
comp_data = save_data[buf_start:buf_end + 4]

# Split into 64KB chunks, strip 4-byte spacers between chunks
CHUNK_SIZE = 64 * 1024
chunks = []
pos = 0
while pos < len(comp_data):
    chunks.append(comp_data[pos:pos + CHUNK_SIZE])
    pos += CHUNK_SIZE + 4  # skip 4-byte spacer

combined = b''.join(chunks)
d = zlib.decompressobj()
decompressed = d.decompress(combined)
decompressed += d.flush(zlib.Z_SYNC_FLUSH)
```

Result: ~16MB binary blob.

## Decompressed Data Layout

```
Offset      Size        Content
─────────────────────────────────────────────
0x000000    ~1.2MB      Map data (tiles, terrain, features, improvements)
~1.2MB      ~7MB        Per-player data blocks (one per civ + city-states)
~8MB        ~6MB        City-state data, modifier definitions
~14.6MB     ~0.4MB      Citizen names, river names, geographic features
~15.0MB     ~0.5MB      Modifier/requirement definitions (GAME_EFFECTS)
~15.47MB    ~0.3MB      Replay dataset labels + notification templates
~15.77MB    ~0.5MB      Per-player per-turn timelines (yields, stats, score)
~15.74MB    ~0.03MB     Per-city production history records
~16.0MB     ~0.3MB      (sparse/zero padding)
```

### Map Dimensions

Map size is encoded as tile count. Known sizes:

| Tiles | Dimensions | Map Size |
|-------|-----------|----------|
| 1144 | 44×26 | Duel |
| 2280 | 60×38 | Tiny |
| 3404 | 74×46 | Small |
| 4536 | 84×54 | Standard |
| 5760 | 96×60 | Large |
| 6996 | 106×66 | Huge |

Find dimensions by searching for the pattern `[tiles, width, tiles]` as three consecutive int32s.

### Fog-of-War

Per-team, **byte-per-tile** (NOT per-bit). Each byte is `0x00` (fog) or `0x01` (revealed).

```
17 teams × 3,404 bytes = 57,868 bytes of fog data
```

Teams are groups of 5 int16 arrays (observation, modifiers, resources, roads, unknown), each of `tile_count` entries, with 12-byte markers between team boundaries.

India (Team 16 in our save) had 2,255/3,404 tiles revealed (66.2%).

### Tile Data Section

Located by searching for the marker:
```
[0x0E, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00]
```

Each tile is variable-length:
```
base:       55 bytes (terrain hash, feature hash, road level, appeal, etc.)
+ overlay:  24 bytes if overlay flag at byte 51 is non-zero
+ ownership: 17 bytes if ownership byte at byte 49 >= 64
```

Terrain/feature type hashes in the save don't match FNV-1a — Civ 6 uses a different hash algorithm (not yet identified). Ocean vs land is distinguishable from landmass indices.

## Per-Player Per-Turn Timelines

12 named timeline arrays, each containing 215 entries (one per turn) as `(turn: int32, value: int32)` pairs. Six blocks per name = one per major civilization.

### Available Timelines

| Name | Type | Description |
|------|------|-------------|
| `Score` | cumulative | Total score |
| `Gold` | snapshot | Gold treasury balance |
| `Science` | snapshot | Science yield per turn |
| `Culture` | snapshot | Culture yield per turn |
| `Faith` | snapshot | Faith yield per turn |
| `Favor` | cumulative | Diplomatic favor accumulated |
| `TechsAcquired` | cumulative | Technologies researched |
| `CivicsAcquired` | cumulative | Civics completed |
| `BarbariansKilled` | cumulative | Barbarian units killed |
| `BarbarianCampsCleared` | cumulative | Barb camps cleared |
| `DiploVP` | cumulative | Diplomatic victory points |
| `ScienceVP` | cumulative | Science victory points |

### Locating Timelines

Search for the timeline name as a length-prefixed string, followed by `0xD7000000` (count=215), then 215 pairs of `(turn: uint32, value: int32)`.

```python
name_pos = data.find(b'Gold')  # in the 15.77M+ region
count_pos = name_pos + len('Gold') + padding  # skip to count
assert struct.unpack('<I', data[count_pos:count_pos+4]) == (215,)

for i in range(215):
    turn = struct.unpack_from('<I', data, count_pos + 4 + i*8)[0]
    value = struct.unpack_from('<i', data, count_pos + 4 + i*8 + 4)[0]
```

### Example: Score Timeline

```
Player 1: T1=4   T50=49   T100=145  T150=250  T200=353  T215=402
Player 2: T1=0   T50=34   T100=75   T150=182  T200=301  T215=329
Player 3: T1=0   T50=47   T100=131  T150=248  T200=330  T215=329
Player 4: T1=0   T50=48   T100=166  T150=304  T200=426  T215=447
Player 5: T1=0   T50=42   T100=143  T150=260  T200=350  T215=373
Player 6: T1=0   T50=65   T100=168  T150=293  T200=468  T215=524
```

## Replay Datasets

30 named dataset categories found at ~15.47M. These are labels/metadata that map to the actual timeline data:

| Dataset | What it tracks |
|---------|---------------|
| SCOREPERTURN | Score per turn |
| SCIENCEPERTURN | Science yield per turn |
| CULTURE | Culture yield per turn |
| FAITHPERTURN | Faith yield per turn |
| TOTALGOLD | Gold treasury |
| ERASCORE | Era score |
| TOTALCITIESBUILT | Cities founded (cumulative) |
| TOTALCITIESDESTROYED | Cities razed |
| TOTALCITIESCAPTURED | Cities captured |
| TOTALCITIESLOST | Cities lost |
| TOTALDISTRICTSBUILT | Districts constructed |
| TOTALBUILDINGSBUILT | Buildings completed |
| TOTALWONDERSBUILT | Wonders completed |
| TOTALUNITSDESTROYED | Enemy units killed |
| TOTALPLAYERUNITSDESTROYED | Own units lost |
| TOTALCOMBATS | Total combats fought |
| TOTALWARSDECLARED | Wars declared |
| TOTALWARSWON | Wars won |
| TOTALWARSAGAINSTPLAYER | Wars declared against player |
| TOTALRELIGIONSFOUNDED | Religions founded |
| TOTALPANTHEONSFOUNDED | Pantheons founded |
| GREATPEOPLEEARNED | Great people recruited |
| GOVERNORS | Governors appointed |
| GOVERNORTITLES | Governor titles earned |

## Per-City Production History

Located at ~15.74M. Each city record contains:

```
TurnFounded: <turn_number>
  BuildingsBuiltByType:  <player_id> → BUILDING_name
  UnitsTrainedByType:    <player_id> → UNIT_name
  UnitsKilledByType:     <player_id> → UNIT_name (killed FROM this city)
  UnitsLostByType:       <player_id> → UNIT_name (lost FROM this city)
  DistrictsBuiltByType:  <player_id> → DISTRICT_name
  WondersBuiltByType:    <player_id> → BUILDING_name
  GovernmentInUseByType: <player_id> → GOVERNMENT_name
  CurrentGovernment:     <player_id> → GOVERNMENT_name
```

Records exist for all cities (major civ cities, city-states, captured cities).

### Category Record Format

```
[4B string_len]["CategoryName"][4B player_id][4B zeros][1B flag][4B value][4B zeros]
[4B string_len]["ENTITY_NAME"]
```

Player IDs in city records are the same as in the timeline blocks (1-6 for major civs).

### Identifying Civilizations

The save header contains ALL installed leaders (80+ with DLC), not just the active 6. Active players must be identified from unique units/districts in the production records:

| Unique Item | Civilization |
|------------|-------------|
| UNIT_MAYAN_HULCHE | Maya |
| UNIT_EGYPTIAN_CHARIOT_ARCHER | Egypt |
| UNIT_PERSIAN_IMMORTAL | Persia |
| DISTRICT_OBSERVATORY | Maya |
| DISTRICT_THANH | Vietnam |

Players without unique items in the production record require cross-referencing city names from the per-player data blocks (each major civ has a ~1MB data block containing its city name pool).

## Per-Player Data Blocks

Each major civilization has a ~1MB block in the 1-8MB region containing:
- City name pool (LOC_CITY_NAME_* strings)
- Unit data, improvement data, tile ownership
- City-specific state (yields, buildings, population)

City name strings identify the civilization:
```
1.4MB-1.6MB: India (Patna, Mysore, Mumbai, Ahmadabad, Madurai, Agra)
2.6MB-2.7MB: Maya (Naranjo, Tikal, Palenque, Uxmal, Coba)
4.6MB-4.8MB: Ottoman (Istanbul, Izmir, Sivas, Edirne)
5.9MB-6.1MB: Egypt (Ra-Kedet, Sais, Thebes, Abydos, Swenett)
7.1MB-7.3MB: Persia (Mashhad, Susa, Pasargadae, Bakhtri, Hagmatana)
```

City-states occupy the 8-14MB region:
```
La Venta, Yerevan, Nan Madol, Caguana, Singapore,
Akkad, Kumasi, Geneva, Kandy, Shahr-i-Qumis
```

## What's NOT in the Save File

The save stores **cumulative counters and snapshots**, not event logs:

- **No per-turn action log**: Individual unit moves, tile-by-tile decisions, and research order changes are not recorded. Only cumulative counts (units trained, techs acquired) exist.
- **No combat details**: Total combats and kills are tracked, but not which units fought where or damage dealt.
- **No diplomacy event history**: No record of when friendships, alliances, or wars started — only current state.
- **No production queue history**: Only what was built in each city, not the order or what was swapped out.

### Implications for Expert Play Database

To build a database of expert human play, the save file alone is insufficient. You get:
- **Macro curves**: How yields, score, techs, civics grow over 215 turns
- **What was built**: Every unit, building, district, wonder — and which city produced it
- **Strategic milestones**: Exact turns for tech/civic completions, wonder builds, camp clears, wars
- **Government choices**: Which governments were adopted and when

You do NOT get:
- **Micro decisions**: Unit movement, tile improvement order, combat tactics
- **Why**: No reasoning or decision context
- **Research path**: Only completion turns, not what was queued or switched

For full action-level data, you'd need to either:
1. Record MCP tool calls during live gameplay (our diary system does this)
2. Hook into the game's Lua event system to log actions in real-time
3. Parse multiple sequential autosaves to diff game state changes
