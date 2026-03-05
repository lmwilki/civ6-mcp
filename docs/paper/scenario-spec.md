# Benchmark Scenario Specification

Three scenarios forming an evaluation battery, ordered by difficulty. Each isolates a specific capability the sensorium effect undermines. All use Quick speed (330-turn game length) to keep per-game cost and wall-clock time practical across multi-model comparison.

## Common Settings

| Parameter | Value |
|-----------|-------|
| Game Speed | Quick |
| Start Era | Ancient |
| Game Modes | None |
| DLC | Gathering Storm (no Leader Pass on Linux) |
| Barbarians | On |
| City-States | Default for map size |
| Duplicate Leaders | Off |
| Save Format | T1 save files for exact reproducibility |

Record map seed, game seed, game version, and DLC list for each save. One save per scenario — all models play the exact same map for comparison clarity.

---

## Scenario A — "Ground Control"

**Tests:** Does the agent monitor the race it thinks it's winning?

| Parameter | Value |
|-----------|-------|
| Agent Civ | Babylon (Hammurabi) |
| Map | Pangaea, Standard |
| Difficulty | Prince |
| Victory | All types enabled |
| Opponents | Korea (Seondeok), Scotland (Robert the Bruce), Australia (John Curtin), Japan (Hojo Tokimune), Rome (Trajan), Mapuche (Lautaro), Netherlands (Wilhelmina) |

The experimental control. Babylon is a science civ with a unique mechanic: eurekas grant the full technology instead of a 50% boost. The agent's default preference for science is correct here. Prince difficulty provides a level playing field — the agent should pursue a science victory with no AI bonuses or penalties. The variable under test is not whether it wins, but whether it knows it's winning.

Three opponents are genuine science competitors: Korea (Seowon engine), Scotland (science when happy + Great Scientists), Australia (production bonuses for space projects). On Warlord they are slower than the agent, but they still pursue the space race. Netherlands adds balanced trade/science competition. Rome, Mapuche, and Japan provide non-science pressure (expansion, loyalty/combat) without derailing the science race framing.

Babylon's eureka mechanic adds a secondary signal: eurekas reward engagement with wider game mechanics — building specific improvements, meeting civilisations, training units, founding cities, winning combats. An agent that pursues eureka conditions is interacting with the full game; an agent that brute-forces research is ignoring its kit and playing a generic science civ.

**Key metrics:** `get_victory_progress` call frequency, turn of Spaceport completion, space projects completed vs nearest rival at game end, Great Scientists recruited vs available, eureka completion rate, victory type and turn.

---

## Scenario B — "Snowflake"

**Tests:** Can the agent reframe its tools when its default goal is removed?

| Parameter | Value |
|-----------|-------|
| Agent Civ | Korea (Seondeok) |
| Map | Six-Armed Snowflake, Small |
| Difficulty | King |
| Victory | **Domination only** (Science, Culture, Religious, Diplomatic disabled) |
| Opponents | Macedon (Alexander), Aztec (Montezuma), Scythia (Tomyris), Brazil (Pedro II), Kongo (Mvemba a Nzinga) |

Korea is the purest science civ in the game — Seowon districts, Hwacha unique unit, science-focused leader ability. But science victory is disabled. The agent must recognise this and reframe: science is now a *weapon* (faster military tech), not a victory path.

The Six-Armed Snowflake map places each civ on a peninsular arm radiating from a resource-rich central hub (the "Promised Land"). Arms have room for 2-3 cities with mountains (excellent Seowon adjacency) but late-game strategic resources — niter, coal, uranium — are concentrated exclusively in the center. The agent must push through its chokepoint to access these resources.

Three opponents are aggressive: Macedon (early conquest, anti-wonder), Aztec (eagle warriors, luxury combat bonuses), and Scythia (double cavalry production). They will contest the center. Two opponents are passive: Brazil (culture-focused) and Kongo (culture/great works, cannot found religion). The passive civs are softer targets once the agent controls the center.

The scenario has a natural three-act structure:
- **Act 1 (T1-50):** Develop the arm. Seowon engine works — mountains are on the arms. Tech faster than everyone. But limited to warriors/slingers without center resources.
- **Act 2 (T50-120):** Push into the center. Contest Macedon/Aztec/Scythia for iron, niter, horses. Korea's tech lead means fielding crossbowmen while others have warriors.
- **Act 3 (T120+):** Use tech + resource advantage to push down remaining arms and capture capitals.

King difficulty keeps survival manageable so the variable under test is strategic adaptation, not raw difficulty pressure.

**Key metrics:** Turn agent first acknowledges domination-only in diary, turn of first military unit beyond starting warrior, turn agent first moves toward center, turn agent secures first strategic resource from center, tech lead at T50/T100 (does it have crossbowmen while others have warriors?), cities captured by T100/T150/T200, Seowon count, `get_victory_progress` call frequency.

---

## Scenario C — "Cry Havoc"

**Tests:** Does the agent see that the rules have changed?

| Parameter | Value |
|-----------|-------|
| Agent Civ | Sumeria (Gilgamesh) |
| Map | Pangaea, Tiny (4 players) |
| Difficulty | Immortal |
| Victory | All types enabled |
| Opponents | Korea (Seondeok), Brazil (Pedro II), Canada (Wilfrid Laurier) |

On Immortal the AI gets +40% yields, +3 combat strength, and 2 free Warriors. The agent's default playbook (Scout → Settler → Campus → science snowball) is unviable against AI civilisations with a 40% yield head start that compounds every turn.

Gilgamesh is the strongest possible hint. War Carts require zero tech, have 30 CS and 3 movement, and outclass every other Ancient era unit. Ziggurats provide +2 science and +1 culture with no tech requirement. The civ's identity is "attack immediately."

Opponents are deliberately non-aggressive (Korea, Brazil, Canada) — giving the agent a brief window where War Carts dominate before the AI's yield bonuses produce stronger units and walls. This is the most forgiving possible Immortal configuration.

Tiny Pangaea (4 players) ensures the agent finds opponents quickly and that each conquest is decisive. Capturing 1 of 3 capitals = 33% domination progress.

**Key metrics:** Build order (first 5 items), turn of first military attack, War Carts produced by T25, AI cities captured by T40, diary mentions of Immortal/AI bonuses, Ziggurat utilisation.

---

## Summary

| | Ground Control | Snowflake | Cry Havoc |
|--|---|---|---|
| **Letter** | A | B | C |
| **Civ** | Babylon | Korea | Sumeria |
| **Map** | Pangaea, Standard | Snowflake, Small | Pangaea, Tiny |
| **Difficulty** | Prince | King | Immortal |
| **Victory** | All | Domination only | All |
| **Opponents** | Korea/Scotland/Australia/Japan/Rome/Mapuche/Netherlands | Macedon/Aztec/Scythia/Brazil/Kongo | Korea/Brazil/Canada |
| **Blind spot** | Tempo awareness | Strategic reframing | Difficulty context |
| **Default path blocked by** | — (science is correct) | Science victory disabled | Immortal yield math |
