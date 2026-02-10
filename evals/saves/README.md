# CivBench Save Files

This directory holds Civilization VI save files (`.Civ6Save`) used as starting positions for benchmark scenarios. Save files are **gitignored** due to size.

## Required Saves

| File | Scenario | Description |
|------|----------|-------------|
| `early_game_50.Civ6Save` | `early_game_50` | Turn 1 Pangaea start, Prince difficulty |
| `mid_game_100.Civ6Save` | `mid_game_100` | Turn 1 Pangaea start, Prince difficulty |
| `crisis_response.Civ6Save` | `crisis_response` | Mid-game save with active barbarian threat, King difficulty |

## Creating Save Files

1. Launch Civ 6 with `EnableTuner = 1` in `AppOptions.txt`
2. Start a new game with the desired settings (map type, difficulty, civ)
3. For turn-1 saves: save immediately on the first turn
4. For mid-game saves: play to the desired state and save
5. Copy the `.Civ6Save` file to this directory

### Save file location (macOS)

```
~/Library/Application Support/Sid Meier's Civilization VI/Saves/Single/
```

## Running an Eval

Before running `inspect eval`, the game must be running with the correct save loaded:

1. Launch Civ 6 with FireTuner enabled
2. Load the benchmark save file through the game UI
3. (Optional) Start the web dashboard: `cd web && npm run dev`
4. Run the eval:

```bash
inspect eval evals/civbench.py@civbench_standard \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -T scenarios=early_game_50
```

The eval framework spawns the civ-mcp server as a subprocess, which connects to the running game on port 4318.
