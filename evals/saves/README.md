# CivBench Save Files

This directory holds Civilization VI save files (`.Civ6Save`) used as starting positions for benchmark scenarios. Save files are **gitignored** due to size (~500KB each).

## Required Saves

Each scenario needs 3-5 saves with different map seeds for statistical coverage. Start with one save per scenario; add more later.

Naming convention: `{SCENARIO_ID}_S{LETTER}.Civ6Save`

### A: Ground Control

| File | Settings |
|------|----------|
| `GROUND_CONTROL_SA.Civ6Save` | Babylon (Hammurabi), Pangaea Standard, Warlord, Quick, 7 opponents |

**Opponents:** Korea (Seondeok), Scotland (Robert the Bruce), Australia (John Curtin), Japan (Hojo Tokimune), Rome (Trajan), Mapuche (Lautaro), Netherlands (Wilhelmina)

### B: Empty Canvas

| File | Settings |
|------|----------|
| `EMPTY_CANVAS_SB.Civ6Save` | Kongo (Mvemba a Nzinga), Pangaea Small, Prince, Quick, 5 opponents |

**Opponents:** Greece (Pericles), Brazil (Pedro II), Babylon (Hammurabi), Rome (Trajan), France (Catherine de Medici - Magnificence)

### C: Deus Vult

| File | Settings |
|------|----------|
| `DEUS_VULT_SC.Civ6Save` | Germany (Frederick Barbarossa), Pangaea Small, King, Quick, 5 opponents |

**Opponents:** Russia (Peter), Spain (Philip II), Arabia (Saladin - Vizier), Rome (Trajan), Japan (Hojo Tokimune)

### D: Snowflake

| File | Settings |
|------|----------|
| `SNOWFLAKE_SD.Civ6Save` | Korea (Seondeok), Six-Armed Snowflake Small, Emperor, Quick, 5 opponents |

**Opponents:** Macedon (Alexander), Zulu (Shaka), Aztec (Montezuma), Persia (Cyrus), Scythia (Tomyris)

### E: Cry Havoc

| File | Settings |
|------|----------|
| `CRY_HAVOC_SE.Civ6Save` | Sumeria (Gilgamesh), Pangaea Tiny, Immortal, Quick, 3 opponents |

**Opponents:** Korea (Seondeok), Brazil (Pedro II), Canada (Wilfrid Laurier)

## Common Settings (All Scenarios)

| Parameter | Value |
|-----------|-------|
| Game Speed | Quick |
| Start Era | Ancient |
| Game Modes | None |
| DLC | Gathering Storm + all leader packs |
| Barbarians | On |
| City-States | Default for map size |
| Duplicate Leaders | Off |
| Victory Conditions | All enabled |

## Creating Save Files

1. Launch Civ 6 with `EnableTuner = 1` in `AppOptions.txt`
2. Start a new game with the exact settings above
3. **Save immediately on Turn 1** (before taking any actions)
4. Copy the `.Civ6Save` file to this directory with the correct name
5. Record the map seed and game seed (visible in game setup or save metadata)

### Save file location (macOS)

```
~/Library/Application Support/Sid Meier's Civilization VI/Saves/Single/
```

### Verification checklist

For each save file:
- [ ] Correct civilisation and leader
- [ ] Correct opponents (check in-game diplomacy screen after loading)
- [ ] Correct difficulty
- [ ] Quick game speed
- [ ] Turn 1 (no actions taken)
- [ ] Gathering Storm rules active

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
