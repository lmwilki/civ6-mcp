#!/usr/bin/env python3
"""Extract per-player per-turn timelines from a Civ 6 save file.

Outputs diary-compatible JSONL: one row per player per turn, with fields
matching the PlayerRow schema used by the live diary system.

Usage:
    python scripts/parse_save.py saves/CHANDRAGUPTA*.Civ6Save
    python scripts/parse_save.py saves/CHANDRAGUPTA*.Civ6Save -o output.jsonl
    python scripts/parse_save.py saves/CHANDRAGUPTA*.Civ6Save --csv
"""

from __future__ import annotations

import argparse
import csv
import json
import struct
import sys
import zlib
from dataclasses import dataclass, field, asdict
from pathlib import Path


# ── Timeline names in the order they appear per player block ──────────────
# Group 1: 9 contiguous timelines per player
# Group 2: 3 contiguous timelines per player (later in the file)
TIMELINE_NAMES = [
    "Gold",
    "Culture",
    "Science",
    "Faith",
    "Score",
    "BarbariansKilled",
    "BarbarianCampsCleared",
    "CivicsAcquired",
    "TechsAcquired",
    "Favor",
    "ScienceVP",
    "DiploVP",
]

# Map timeline names → diary PlayerRow field names
# NOTE on approximate fields:
#   - Gold: treasury balance in both save and diary, but may diverge by ~10%
#     due to measurement timing within the turn (int truncation + frame difference)
#   - Science/Culture: per-turn yield, save truncates to int, diary stores float
#   - Faith: save stores per-turn YIELD, diary "faith" is treasury BALANCE;
#     we map to faith_per_turn to match correctly
TIMELINE_TO_DIARY = {
    "Score": "score",  # exact match (cumulative)
    "Gold": "gold",  # treasury balance (approximate, ±10%)
    "Science": "science",  # yield per turn (approximate, int vs float)
    "Culture": "culture",  # yield per turn (approximate, int vs float)
    "Faith": "faith_per_turn",  # per-turn yield (NOT faith balance)
    "Favor": "favor",  # cumulative (exact)
    "TechsAcquired": "techs_completed",  # cumulative (exact)
    "CivicsAcquired": "civics_completed",  # cumulative (exact)
    "BarbariansKilled": "barbarians_killed",  # cumulative (exact)
    "BarbarianCampsCleared": "barbarian_camps_cleared",  # cumulative (exact)
    "DiploVP": "diplo_vp",  # cumulative (exact)
    "ScienceVP": "sci_vp",  # cumulative (exact)
}

# Unique units/districts → civilization name
UNIQUE_ITEMS: dict[str, str] = {
    "UNIT_INDIAN_VARU": "India",
    "UNIT_MAYAN_HULCHE": "Maya",
    "UNIT_OTTOMAN_BARBARY_CORSAIR": "Ottomans",
    "UNIT_OTTOMAN_BOMBARD": "Ottomans",
    "UNIT_EGYPTIAN_CHARIOT_ARCHER": "Egypt",
    "UNIT_PERSIAN_IMMORTAL": "Persia",
    "UNIT_VIETNAMESE_VOI_CHIEN": "Vietnam",
    "UNIT_BRAZILIAN_MINAS_GERAES": "Brazil",
    "UNIT_ENGLISH_REDCOAT": "England",
    "UNIT_ENGLISH_SEA_DOG": "England",
    "UNIT_ROMAN_LEGION": "Rome",
    "UNIT_GREEK_HOPLITE": "Greece",
    "UNIT_AZTEC_EAGLE_WARRIOR": "Aztec",
    "UNIT_CHINESE_CROUCHING_TIGER": "China",
    "UNIT_JAPANESE_SAMURAI": "Japan",
    "UNIT_FRENCH_GARDE_IMPERIALE": "France",
    "UNIT_GERMAN_UBOAT": "Germany",
    "UNIT_RUSSIAN_COSSACK": "Russia",
    "UNIT_AMERICAN_ROUGH_RIDER": "America",
    "UNIT_ARABIAN_MAMLUK": "Arabia",
    "UNIT_SPANISH_CONQUISTADOR": "Spain",
    "UNIT_NORWEGIAN_BERSERKER": "Norway",
    "UNIT_NORWEGIAN_LONGSHIP": "Norway",
    "UNIT_SCYTHIAN_HORSE_ARCHER": "Scythia",
    "UNIT_KONGOLESE_NGAO_MBEBA": "Kongo",
    "UNIT_SUMERIAN_WAR_CART": "Sumeria",
    "UNIT_NUBIAN_PITATI": "Nubia",
    "UNIT_MACEDONIAN_HETAIROI": "Macedon",
    "UNIT_MACEDONIAN_HYPASPIST": "Macedon",
    "UNIT_POLISH_WINGED_HUSSAR": "Poland",
    "UNIT_AUSTRALIAN_DIGGER": "Australia",
    "UNIT_INDONESIAN_JONG": "Indonesia",
    "UNIT_CREE_OKIHTCITAW": "Cree",
    "UNIT_GEORGIAN_KHEVSURETI": "Georgia",
    "UNIT_KOREAN_HWACHA": "Korea",
    "UNIT_MAPUCHE_MALON_RAIDER": "Mapuche",
    "UNIT_MONGOLIAN_KESHIG": "Mongolia",
    "UNIT_SCOTTISH_HIGHLANDER": "Scotland",
    "UNIT_ZULU_IMPI": "Zulu",
    "UNIT_CANADIAN_MOUNTIE": "Canada",
    "UNIT_HUNGARIAN_HUSZAR": "Hungary",
    "UNIT_HUNGARIAN_BLACK_ARMY": "Hungary",
    "UNIT_INCA_WARAKAQ": "Inca",
    "UNIT_MALIAN_MANDEKALU_CAVALRY": "Mali",
    "UNIT_MAORI_TOA": "Maori",
    "UNIT_SWEDISH_CAROLEAN": "Sweden",
    "UNIT_PHOENICIAN_BIREME": "Phoenicia",
    "UNIT_COLOMBIAN_COMANDANTE_GENERAL": "Gran Colombia",
    "UNIT_ETHIOPIAN_OROMO_CAVALRY": "Ethiopia",
    "UNIT_BYZANTINE_DROMON": "Byzantium",
    "UNIT_BYZANTINE_TAGMA": "Byzantium",
    "UNIT_GAUL_GAESATAE": "Gaul",
    "UNIT_BABYLONIAN_SABUM_KIBITTUM": "Babylon",
    "UNIT_PORTUGUESE_NAU": "Portugal",
    # Unique districts
    "DISTRICT_OBSERVATORY": "Maya",
    "DISTRICT_THANH": "Vietnam",
    "DISTRICT_LAVRA": "Russia",
    "DISTRICT_BATH": "Rome",
    "DISTRICT_HANSA": "Germany",
    "DISTRICT_ACROPOLIS": "Greece",
    "DISTRICT_MBANZA": "Kongo",
    "DISTRICT_ROYAL_NAVY_DOCKYARD": "England",
    "DISTRICT_SEOWON": "Korea",
    "DISTRICT_ENCAMPMENT_IKANDA": "Zulu",
    "DISTRICT_SUGUBA": "Mali",
    "DISTRICT_COTHON": "Phoenicia",
    "DISTRICT_OPPIDUM": "Gaul",
    "DISTRICT_PAIRIDAEZA": "Persia",
    "DISTRICT_PRESERVE_VIETNAM": "Vietnam",
}

# City name substrings → civilization (fallback identification)
CITY_NAME_POOLS: dict[str, list[str]] = {
    "India": ["LOC_CITY_NAME_PATNA", "LOC_CITY_NAME_MUMBAI", "LOC_CITY_NAME_AGRA"],
    "Maya": ["LOC_CITY_NAME_TIKAL", "LOC_CITY_NAME_PALENQUE", "LOC_CITY_NAME_UXMAL"],
    "Ottomans": [
        "LOC_CITY_NAME_ISTANBUL",
        "LOC_CITY_NAME_IZMIR",
        "LOC_CITY_NAME_EDIRNE",
    ],
    "Egypt": ["LOC_CITY_NAME_THEBES", "LOC_CITY_NAME_RA_KEDET", "LOC_CITY_NAME_SAIS"],
    "Persia": ["LOC_CITY_NAME_PASARGADAE", "LOC_CITY_NAME_SUSA"],
    "Vietnam": ["LOC_CITY_NAME_THANG_LONG", "LOC_CITY_NAME_HUE"],
    "Rome": ["LOC_CITY_NAME_ROME", "LOC_CITY_NAME_OSTIA"],
    "Greece": ["LOC_CITY_NAME_ATHENS", "LOC_CITY_NAME_SPARTA"],
    "China": ["LOC_CITY_NAME_XIAN", "LOC_CITY_NAME_BEIJING"],
    "Japan": ["LOC_CITY_NAME_KYOTO", "LOC_CITY_NAME_OSAKA"],
    "France": ["LOC_CITY_NAME_PARIS", "LOC_CITY_NAME_LYON"],
    "Germany": ["LOC_CITY_NAME_AACHEN", "LOC_CITY_NAME_COLOGNE"],
    "Russia": ["LOC_CITY_NAME_ST_PETERSBURG", "LOC_CITY_NAME_MOSCOW"],
    "America": ["LOC_CITY_NAME_WASHINGTON", "LOC_CITY_NAME_BOSTON"],
    "England": ["LOC_CITY_NAME_LONDON", "LOC_CITY_NAME_LIVERPOOL"],
    "Brazil": ["LOC_CITY_NAME_SAO_PAULO", "LOC_CITY_NAME_RIO_DE_JANEIRO"],
    "Arabia": ["LOC_CITY_NAME_CAIRO", "LOC_CITY_NAME_MECCA"],
    "Spain": ["LOC_CITY_NAME_MADRID", "LOC_CITY_NAME_BARCELONA"],
    "Norway": ["LOC_CITY_NAME_NIDAROS", "LOC_CITY_NAME_BERGEN"],
    "Scythia": ["LOC_CITY_NAME_POKROVKA", "LOC_CITY_NAME_AKTAU"],
    "Kongo": ["LOC_CITY_NAME_MBANZA_KONGO"],
    "Sumeria": ["LOC_CITY_NAME_URUK", "LOC_CITY_NAME_UR"],
}


# ── Data types ────────────────────────────────────────────────────────────


@dataclass
class TimelineEntry:
    turn: int
    value: int


@dataclass
class PlayerTimelines:
    """All 12 timelines for one player."""

    player_index: int  # 0-based
    civ_name: str = "Unknown"
    timelines: dict[str, list[TimelineEntry]] = field(default_factory=dict)


@dataclass
class SaveMetadata:
    filename: str = ""
    game_turn: int = 0
    num_players: int = 0
    game_speed: str = ""
    map_size: str = ""


# ── Decompression ─────────────────────────────────────────────────────────


def decompress_save(save_data: bytes) -> bytes:
    """Decompress the zlib-compressed game data from a .Civ6Save file.

    The compressed region uses 64KB chunks with 4-byte spacers.
    """
    # Find the start of compressed data (after MOD_TITLE)
    mod_index = save_data.rfind(b"MOD_TITLE")
    if mod_index < 0:
        raise ValueError("Could not find MOD_TITLE marker in save file")

    buf_start = save_data.index(b"\x78\x9c", mod_index)  # zlib magic bytes
    buf_end = save_data.rfind(b"\x00\x00\xff\xff")
    if buf_end < buf_start:
        raise ValueError("Could not find end of compressed data")

    comp_data = save_data[buf_start : buf_end + 4]

    # Split into 64KB chunks, skip 4-byte spacers
    CHUNK_SIZE = 64 * 1024
    chunks = []
    pos = 0
    while pos < len(comp_data):
        chunks.append(comp_data[pos : pos + CHUNK_SIZE])
        pos += CHUNK_SIZE + 4  # skip 4-byte spacer

    combined = b"".join(chunks)
    d = zlib.decompressobj()
    decompressed = d.decompress(combined)
    decompressed += d.flush(zlib.Z_SYNC_FLUSH)
    return decompressed


# ── Header parsing (lightweight) ──────────────────────────────────────────


def parse_header_strings(save_data: bytes) -> SaveMetadata:
    """Extract game speed and map size from the header via string search."""
    meta = SaveMetadata()

    # Game speed
    idx = save_data.find(b"GAMESPEED_")
    if idx >= 0:
        end = save_data.index(b"\x00", idx)
        meta.game_speed = save_data[idx:end].decode("ascii")

    # Map size
    idx = save_data.find(b"MAPSIZE_")
    if idx >= 0:
        end = save_data.index(b"\x00", idx)
        meta.map_size = save_data[idx:end].decode("ascii")

    return meta


# ── Timeline extraction ──────────────────────────────────────────────────


def find_timeline_blocks(
    data: bytes, name: str, search_start: int = 15_000_000
) -> list[int]:
    """Find all timeline blocks for a given name. Returns list of offsets to the name string."""
    positions = []
    pos = search_start
    name_bytes = name.encode("ascii")
    name_len = len(name_bytes)

    while True:
        pos = data.find(name_bytes, pos)
        if pos < 0 or pos > len(data) - 20:
            break

        # Validate: 4 bytes before name should be its length
        pre_len = struct.unpack_from("<I", data, pos - 4)[0]
        if pre_len != name_len:
            pos += 1
            continue

        # After name: [4B flag=1][4B zeros][4B count]
        count_offset = pos + name_len + 8
        if count_offset + 4 > len(data):
            pos += 1
            continue

        count = struct.unpack_from("<I", data, count_offset)[0]
        if count > 0 and count <= 1000:  # reasonable turn count
            positions.append(pos)

        pos += name_len

    return positions


def read_timeline(data: bytes, name_pos: int, name_len: int) -> list[TimelineEntry]:
    """Read timeline entries starting from the name position."""
    count_offset = name_pos + name_len + 8
    count = struct.unpack_from("<I", data, count_offset)[0]
    data_start = count_offset + 4

    entries = []
    for i in range(count):
        off = data_start + i * 8
        turn = struct.unpack_from("<I", data, off)[0]
        value = struct.unpack_from("<i", data, off + 4)[0]
        entries.append(TimelineEntry(turn=turn, value=value))

    return entries


def extract_timelines(data: bytes) -> list[PlayerTimelines]:
    """Extract all 12 timelines for all players from decompressed save data.

    Uses Score timeline (major-civ-only) to determine player count, then
    picks the first N blocks of each timeline to match major civs.
    """
    # Score only exists for major civs — use it to determine player count
    score_positions = find_timeline_blocks(data, "Score")
    num_players = len(score_positions)

    if num_players == 0:
        raise ValueError("No Score timeline blocks found")

    # Determine turn count from first Score block
    first_entries = read_timeline(data, score_positions[0], len("Score"))
    turn_count = len(first_entries)

    players = [PlayerTimelines(player_index=i) for i in range(num_players)]

    for name in TIMELINE_NAMES:
        positions = find_timeline_blocks(data, name)

        # For timelines that exist for all entities (Gold, Culture, Science, Faith),
        # the first N blocks correspond to major civs in the same order as Score
        for i in range(min(num_players, len(positions))):
            entries = read_timeline(data, positions[i], len(name))
            # Sanity check: should have same turn count
            if len(entries) == turn_count:
                players[i].timelines[name] = entries
            else:
                print(
                    f"  WARN: {name} P{i} has {len(entries)} entries, expected {turn_count}",
                    file=sys.stderr,
                )

    return players


# ── Civ identification ────────────────────────────────────────────────────


def _scan_production_records(
    data: bytes,
    category: bytes,
) -> dict[int, set[str]]:
    """Scan production records for a category, returning {player_id: {entity_names}}.

    Record format after category name:
      [4B player_id][4B zeros][1B flag][4B value][4B zeros][4B entity_len][entity_name]
    Player IDs are 1-based in the save file.
    """
    result: dict[int, set[str]] = {}
    pos = 0
    while True:
        pos = data.find(category, pos)
        if pos < 0:
            break
        base = pos + len(category)
        if base + 22 > len(data):
            break

        player_id = struct.unpack_from("<I", data, base)[0]
        entity_len = struct.unpack_from("<I", data, base + 17)[0]

        if 0 < entity_len < 200 and base + 21 + entity_len <= len(data):
            entity = data[base + 21 : base + 21 + entity_len].decode(
                "ascii", errors="replace"
            )
            result.setdefault(player_id, set()).add(entity)

        pos += 1

    return result


def identify_civs(data: bytes, num_players: int) -> dict[int, str]:
    """Identify civilizations from unique units/districts in production records.

    Production records use 1-based player IDs; returned dict uses 0-based.
    Falls back to city name pool scanning for unidentified players.
    """
    player_civs: dict[int, str] = {}

    # Scan units and districts
    units = _scan_production_records(data, b"UnitsTrainedByType")
    districts = _scan_production_records(data, b"DistrictsBuiltByType")

    # Merge into one entity set per player
    all_entities: dict[int, set[str]] = {}
    for pid, names in units.items():
        all_entities.setdefault(pid, set()).update(names)
    for pid, names in districts.items():
        all_entities.setdefault(pid, set()).update(names)

    # Match unique items
    for pid_1based, entities in all_entities.items():
        pid = pid_1based - 1  # convert to 0-based
        if pid < 0 or pid >= num_players:
            continue
        for entity in entities:
            if entity in UNIQUE_ITEMS and pid not in player_civs:
                player_civs[pid] = UNIQUE_ITEMS[entity]

    # Fallback: scan city name pools in 1-8MB region for unidentified players
    if len(player_civs) < num_players:
        # Find LOC_CITY_NAME_ groups in per-player data blocks
        city_groups: list[tuple[int, list[str]]] = []
        city_locs: list[tuple[int, str]] = []
        search_pos = 500_000
        while search_pos < 10_000_000:
            search_pos = data.find(b"LOC_CITY_NAME_", search_pos)
            if search_pos < 0:
                break
            end = data.find(b"\x00", search_pos, search_pos + 200)
            if end < 0:
                search_pos += 1
                continue
            name = data[search_pos:end].decode("ascii", errors="replace")
            # Skip names with control chars (active city instances, not pool entries)
            if all(
                c.isascii() and (c.isalnum() or c in "_")
                for c in name[len("LOC_CITY_NAME_") :]
            ):
                city_locs.append((search_pos, name))
            search_pos = end

        # Group by proximity
        if city_locs:
            current: list[tuple[int, str]] = [city_locs[0]]
            for i in range(1, len(city_locs)):
                if city_locs[i][0] - city_locs[i - 1][0] < 200_000:
                    current.append(city_locs[i])
                else:
                    city_groups.append((current[0][0], [n for _, n in current]))
                    current = [city_locs[i]]
            city_groups.append((current[0][0], [n for _, n in current]))

        # Match groups to civs
        for group_idx, (offset, names) in enumerate(city_groups):
            if group_idx >= num_players or group_idx in player_civs:
                continue
            for civ_name, markers in CITY_NAME_POOLS.items():
                if any(m in names for m in markers):
                    player_civs[group_idx] = civ_name
                    break

    return player_civs


# ── JSONL output ──────────────────────────────────────────────────────────


def timelines_to_diary_rows(
    players: list[PlayerTimelines],
    meta: SaveMetadata,
) -> list[dict]:
    """Convert extracted timelines into diary-compatible JSONL rows.

    One row per player per turn, matching the PlayerRow schema.
    """
    rows = []

    for player in players:
        # Determine turn count from the first available timeline
        turn_count = 0
        for tl in player.timelines.values():
            if tl:
                turn_count = len(tl)
                break

        for t_idx in range(turn_count):
            row: dict = {
                "v": 2,
                "source": "save_extract",
                "game": meta.filename,
                "pid": player.player_index,
                "civ": player.civ_name,
                "leader": "",
                "is_agent": False,
            }

            # Fill in timeline-derived fields
            for tl_name, diary_field in TIMELINE_TO_DIARY.items():
                entries = player.timelines.get(tl_name, [])
                if t_idx < len(entries):
                    row["turn"] = entries[t_idx].turn
                    row[diary_field] = entries[t_idx].value

            rows.append(row)

    return rows


# ── Main ──────────────────────────────────────────────────────────────────


def parse_save(path: Path) -> tuple[SaveMetadata, list[PlayerTimelines]]:
    """Parse a .Civ6Save file and return metadata + player timelines."""
    save_data = path.read_bytes()
    meta = parse_header_strings(save_data)
    meta.filename = path.stem

    print(f"Decompressing {path.name} ({len(save_data):,} bytes)...", file=sys.stderr)
    data = decompress_save(save_data)
    print(f"Decompressed: {len(data):,} bytes", file=sys.stderr)

    # Detect game turn from the last entry in the first timeline found
    print("Extracting timelines...", file=sys.stderr)
    players = extract_timelines(data)
    meta.num_players = len(players)

    if players and players[0].timelines:
        first_tl = next(iter(players[0].timelines.values()))
        if first_tl:
            meta.game_turn = first_tl[-1].turn

    # Identify civilizations
    civ_map = identify_civs(data, len(players))
    for i, player in enumerate(players):
        if i in civ_map:
            player.civ_name = civ_map[i]

    print(f"Found {len(players)} players, {meta.game_turn} turns", file=sys.stderr)
    print(f"Speed: {meta.game_speed}, Map: {meta.map_size}", file=sys.stderr)
    for p in players:
        tl_count = sum(1 for tl in p.timelines.values() if tl)
        print(
            f"  P{p.player_index}: {p.civ_name} ({tl_count} timelines)",
            file=sys.stderr,
        )

    return meta, players


def main():
    parser = argparse.ArgumentParser(
        description="Extract Civ 6 save file timelines to JSONL"
    )
    parser.add_argument("save_file", type=Path, help="Path to .Civ6Save file")
    parser.add_argument(
        "-o", "--output", type=Path, help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--csv", action="store_true", help="Output CSV instead of JSONL"
    )
    parser.add_argument(
        "--player", type=int, default=None, help="Extract only this player (0-based)"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output raw timeline names instead of diary fields",
    )
    args = parser.parse_args()

    if not args.save_file.exists():
        print(f"File not found: {args.save_file}", file=sys.stderr)
        sys.exit(1)

    meta, players = parse_save(args.save_file)

    if args.player is not None:
        players = [p for p in players if p.player_index == args.player]

    rows = timelines_to_diary_rows(players, meta)

    # Output
    out = open(args.output, "w") if args.output else sys.stdout
    try:
        if args.csv:
            if not rows:
                return
            writer = csv.DictWriter(out, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        else:
            for row in rows:
                out.write(json.dumps(row, separators=(",", ":")) + "\n")
    finally:
        if args.output:
            out.close()

    n_rows = len(rows)
    n_players = len(set(r["pid"] for r in rows))
    n_turns = len(set(r.get("turn", 0) for r in rows))
    fmt = "CSV" if args.csv else "JSONL"
    dest = args.output or "stdout"
    print(
        f"\nWrote {n_rows} rows ({n_players} players × {n_turns} turns) as {fmt} to {dest}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    import signal

    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
