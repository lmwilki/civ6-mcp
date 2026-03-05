# CivBench Save Files

This directory holds Civilization VI save files (`.Civ6Save`) used as starting positions for benchmark scenarios. Save files are **gitignored** due to size (~500KB each).

## Required Saves

Naming convention: `0{LETTER}_{SCENARIO_NAME}.Civ6Save` — the `0` prefix ensures saves sort to the top of Civ 6's Load Game screen.

### A: Ground Control

| File | Settings |
|------|----------|
| `0A_GROUND_CONTROL.Civ6Save` | Babylon (Hammurabi), Pangaea Standard, Prince, Quick, 7 opponents |

**Victory:** All types enabled
**Opponents:** Korea (Seondeok), Scotland (Robert the Bruce), Australia (John Curtin), Japan (Hojo Tokimune), Rome (Trajan), Mapuche (Lautaro), Netherlands (Wilhelmina)

### B: Snowflake

| File | Settings |
|------|----------|
| `0B_SNOWFLAKE.Civ6Save` | Korea (Seondeok), Six-Armed Snowflake Small, King, Quick, 5 opponents |

**Victory:** Domination only (Science, Culture, Religious, Diplomatic disabled)
**Opponents:** Macedon (Alexander), Aztec (Montezuma), Scythia (Tomyris), Brazil (Pedro II), Kongo (Mvemba a Nzinga)

### C: Cry Havoc

| File | Settings |
|------|----------|
| `0C_CRY_HAVOC.Civ6Save` | Sumeria (Gilgamesh), Pangaea Tiny, Immortal, Quick, 3 opponents |

**Victory:** All types enabled
**Opponents:** Korea (Seondeok), Brazil (Pedro II), Canada (Wilfrid Laurier)

## Common Settings (All Scenarios)

| Parameter | Value |
|-----------|-------|
| Game Speed | Quick |
| Start Era | Ancient |
| Game Modes | None |
| DLC | Gathering Storm (no Leader Pass on Linux) |
| Barbarians | On |
| City-States | Default for map size |
| Duplicate Leaders | Off |

## Creating Save Files

### A: Ground Control

1. Create Game > Single Player
2. **Leader:** Babylon — Hammurabi
3. **Difficulty:** Prince
4. **Game Speed:** Quick
5. **Map Type:** Pangaea
6. **Map Size:** Standard (8 players)
7. **Add opponents** (7 total): Korea (Seondeok), Scotland (Robert the Bruce), Australia (John Curtin), Japan (Hojo Tokimune), Rome (Trajan), Mapuche (Lautaro), Netherlands (Wilhelmina)
8. **Victory Conditions:** All enabled (default)
9. Start game. **Save immediately on Turn 1** before any actions.
10. Copy save to this directory as `0A_GROUND_CONTROL.Civ6Save`

### B: Snowflake

1. Create Game > Single Player
2. **Leader:** Korea — Seondeok
3. **Difficulty:** King
4. **Game Speed:** Quick
5. **Map Type:** Six-Armed Snowflake
6. **Map Size:** Small (6 players)
7. **Add opponents** (5 total): Macedon (Alexander), Aztec (Montezuma), Scythia (Tomyris), Brazil (Pedro II), Kongo (Mvemba a Nzinga)
8. **Victory Conditions:** DOMINATION ONLY — disable Science, Culture, Religious, Diplomatic, Score
9. Start game. **Save immediately on Turn 1** before any actions.
10. Copy save to this directory as `0B_SNOWFLAKE.Civ6Save`

### C: Cry Havoc

1. Create Game > Single Player
2. **Leader:** Sumeria — Gilgamesh
3. **Difficulty:** Immortal
4. **Game Speed:** Quick
5. **Map Type:** Pangaea
6. **Map Size:** Tiny (4 players)
7. **Add opponents** (3 total): Korea (Seondeok), Brazil (Pedro II), Canada (Wilfrid Laurier)
8. **Victory Conditions:** All enabled (default)
9. Start game. **Save immediately on Turn 1** before any actions.
10. Copy save to this directory as `0C_CRY_HAVOC.Civ6Save`

### Save file location

| Platform | Path |
|----------|------|
| macOS | `~/Library/Application Support/Sid Meier's Civilization VI/Saves/Single/` |
| Windows | `%USERPROFILE%\Documents\My Games\Sid Meier's Civilization VI\Saves\Single\` |
| Linux | `~/.local/share/aspyr-media/Sid Meier's Civilization VI/Saves/Single/` |

### Verification checklist

For each save file:
- [ ] Correct civilisation and leader
- [ ] Correct opponents (check in-game diplomacy screen after loading)
- [ ] Correct difficulty
- [ ] Quick game speed
- [ ] Turn 1 (no actions taken)
- [ ] Gathering Storm rules active
- [ ] Victory conditions correct (Snowflake = domination only)

## Running an Eval

The game must be running with FireTuner enabled before starting an eval. The agent loads the correct save via `list_saves` / `load_save`.

```bash
# Single scenario
inspect eval evals/civbench.py@civbench_standard \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -T scenarios=ground_control

# All scenarios
uv run python evals/runner.py --model anthropic/claude-sonnet-4-5-20250929

# Multiple models
uv run python evals/runner.py \
    --models anthropic/claude-sonnet-4-5-20250929,openai/gpt-4o,google/gemini-2.5-pro
```

The eval framework spawns the civ-mcp server as a subprocess, which connects to the running game on port 4318.
