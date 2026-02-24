# Fixture Data

Sample game data for local development and testing. Contains 4 completed games (with ELO data) and 1 in-progress game, enough to populate the dashboard, leaderboard, and diary views.

## Loading

```bash
./fixtures/load.sh
```

This copies the JSONL files into `~/.civ6-mcp/`, which is where the web dashboard reads data from by default.

Alternatively, you can point the dashboard at the fixtures directory directly:

```bash
CIV6_DIARY_DIR=./fixtures CIV6_LOG_DIR=./fixtures bun dev
```

## What's included

| File | Description |
|------|-------------|
| `diary_demo_elo1.jsonl` | Game 1 — Russia/Peter (claude-opus-4-6) vs Rome, Egypt, Japan. Science victory (Russia). |
| `diary_demo_elo2.jsonl` | Game 2 — Greece/Pericles (claude-sonnet-4-6) vs Germany, Spain, Brazil. Science victory (Germany). |
| `diary_demo_elo3.jsonl` | Game 3 — America/Teddy Roosevelt (gpt-5) vs Rome, Egypt, India. Diplomatic victory (America). |
| `diary_demo_elo4.jsonl` | Game 4 — Rome/Trajan (claude-opus-4-6) vs India, Mongolia, Spain. **Defeat** — India religious victory T195. |
| `diary_demo_model_pill_20260224.jsonl` | In-progress game — Russia/Peter (claude-opus-4-6) vs Rome. |
| `log_demo_elo{1,2,3,4}.jsonl` | Tool call logs and game-over events for the 4 completed games. |
