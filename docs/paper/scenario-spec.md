# Benchmark Scenario Specification

Five scenarios forming an evaluation battery, ordered by difficulty. Each isolates a specific capability the sensorium effect undermines. All use Quick speed.

## Common Settings

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
| Save Format | T1 save files for exact reproducibility |

Record map seed, game seed, game version, and DLC list for each save. Create 3-5 saves per scenario with different seeds for statistical coverage.

---

## Scenario A — "Ground Control"

**Tests:** Does the agent monitor the race it thinks it's winning?

| Parameter | Value |
|-----------|-------|
| Agent Civ | Babylon (Hammurabi) |
| Map | Pangaea, Standard |
| Difficulty | Warlord |
| Opponents | Korea (Seondeok), Scotland (Robert the Bruce), Australia (John Curtin), Japan (Hojo Tokimune), Rome (Trajan), Mapuche (Lautaro) |

The experimental control. Babylon is a science civ with a unique mechanic: eurekas grant the full technology instead of a 50% boost. The agent's default preference for science is correct here. Warlord difficulty removes survival pressure entirely — the agent should cruise to a science victory. The variable under test is not whether it wins, but whether it knows it's winning.

Three opponents are genuine science competitors: Korea (Seowon engine), Scotland (science when happy + Great Scientists), Australia (production bonuses for space projects). On Warlord they are slower than the agent, but they still pursue the space race. Rome and Mapuche provide non-science pressure (expansion, loyalty/combat) without derailing the science race framing.

Babylon's eureka mechanic adds a secondary signal: eurekas reward engagement with wider game mechanics — building specific improvements, meeting civilisations, training units, founding cities, winning combats. An agent that pursues eureka conditions is interacting with the full game; an agent that brute-forces research is ignoring its kit and playing a generic science civ.

**Key metrics:** `get_victory_progress` call frequency, turn of Spaceport completion, space projects completed vs nearest rival at game end, Great Scientists recruited vs available, eureka completion rate, victory type and turn.

---

## Scenario B — "Empty Canvas"

**Tests:** Does the agent see its own civ kit?

| Parameter | Value |
|-----------|-------|
| Agent Civ | Kongo (Mvemba a Nzinga) |
| Map | Pangaea, Small |
| Difficulty | Prince |
| Opponents | Greece (Pericles), Brazil (Pedro II), Babylon (Hammurabi), Rome (Trajan) |

Kongo cannot found a religion (hard-blocked). It has zero science bonuses. What it has is the strongest cultural kit in the game: 2x Great Work slots, +50% Great Writer/Artist/Musician/Merchant points, Mbanza unique district available at Guilds civic. Science victory is possible but actively disadvantaged — the agent is playing a generic civ with no bonuses. Cultural victory is overwhelmingly signposted by the kit.

Greece and Brazil compete for Great Writers/Artists/Musicians — the agent faces cultural rivals on its own turf. Babylon will out-science a Kongo trying to science-tunnel. Rome expands aggressively as baseline pressure. Prince difficulty keeps the environment gentle so the variable under test is kit adaptation, not survival.

**Key metrics:** Theater Squares built, Great Works collected, tourism output at checkpoints, victory type stated in diary, Mbanza utilisation, turns to first Theater Square.

---

## Scenario C — "Deus Vult"

**Tests:** Does the agent see what it doesn't query?

| Parameter | Value |
|-----------|-------|
| Agent Civ | Germany (Frederick Barbarossa) |
| Map | Pangaea, Small |
| Difficulty | King |
| Opponents | Russia (Peter), Spain (Philip II), Arabia (Saladin), Rome (Trajan), Japan (Hojo Tokimune) |

Germany has zero religious affinity. Any religious monitoring is purely proactive. Three opponents are among the most aggressive religious civs in the game: Russia (Lavra faith engine), Spain (Inquisitors remove 100% heresy, combat bonus vs other religions), Arabia (guaranteed Great Prophet, free worship building). On small Pangaea they will flood the map with missionaries and apostles by T50-70.

Religious victory requires majority in ALL civs — the agent is a conversion target whether it engages or not. The data is available via `get_religion_spread`. The playbook says check every 20 turns. Historical call frequency: once in 431 turns (Game 10), zero (Games 11-12).

Rome and Japan are balanced expanders who build large empires — conversion targets for the three religious civs. Neither is religious, so the 3-vs-2 dynamic stays clean.

**Key metrics:** `get_religion_spread` call frequency, turn of first religious threat detection, response latency (turns between detection and first defensive action), agent cities converted to foreign religion, faith spending on Inquisitors/Apostles.

---

## Scenario D — "Snowflake"

**Tests:** Does the agent see the army at the gate?

| Parameter | Value |
|-----------|-------|
| Agent Civ | Korea (Seondeok) |
| Map | Six-Armed Snowflake, Small |
| Difficulty | Emperor |
| Opponents | Macedon (Alexander), Zulu (Shaka), Aztec (Montezuma), Persia (Cyrus), Scythia (Tomyris) |

A deliberately adversarial scenario. The map generates six peninsular arms radiating from a central hub — isolated early, inevitable collision at chokepoints. All five opponents are domination-oriented. Korea is a pure science civ with no military bonuses. Emperor gives AI +20% yields and +2 combat strength.

The scenario targets reactive military decision-making under sustained pressure — a missed `get_map_area` scan means an undetected army at the chokepoint.

Recreation of Game 12 at Quick speed. The Standard speed game ran 216 turns before concession.

**Key metrics:** Cities at T40/T60/T80/T100, settler losses, military strength vs nearest rival at war declaration, cities lost/recaptured, `get_map_area` scan frequency around chokepoints, Seowon/Hwacha utilisation, exploration %.

---

## Scenario E — "Cry Havoc"

**Tests:** Does the agent see that the rules have changed?

| Parameter | Value |
|-----------|-------|
| Agent Civ | Sumeria (Gilgamesh) |
| Map | Pangaea, Tiny (4 players) |
| Difficulty | Immortal |
| Opponents | Korea (Seondeok), Brazil (Pedro II), Canada (Wilfrid Laurier) |

On Immortal the AI gets +40% yields, +3 combat strength, and 2 free Warriors. The agent's default playbook (Scout → Settler → Campus → science snowball) is unviable against AI civilisations with a 40% yield head start that compounds every turn.

Gilgamesh is the strongest possible hint. War Carts require zero tech, have 30 CS and 3 movement, and outclass every other Ancient era unit. Ziggurats provide +2 science and +1 culture with no tech requirement. The civ's identity is "attack immediately."

Opponents are deliberately non-aggressive (Korea, Brazil, Canada) — giving the agent a brief window where War Carts dominate before the AI's yield bonuses produce stronger units and walls. This is the most forgiving possible Immortal configuration.

Tiny Pangaea (4 players) ensures the agent finds opponents quickly and that each conquest is decisive. Capturing 1 of 3 capitals = 33% domination progress.

**Key metrics:** Build order (first 5 items), turn of first military attack, War Carts produced by T25, AI cities captured by T40, diary mentions of Immortal/AI bonuses, Ziggurat utilisation.

---

## Summary

| | Ground Control | Empty Canvas | Deus Vult | Snowflake | Cry Havoc |
|--|---|---|---|---|---|
| **Civ** | Babylon | Kongo | Germany | Korea | Sumeria |
| **Map** | Pangaea, Standard | Pangaea, Small | Pangaea, Small | Snowflake, Small | Pangaea, Tiny |
| **Difficulty** | Warlord | Prince | King | Emperor | Immortal |
| **Opponents** | Korea/Scotland/Australia/Japan/Rome/Mapuche | Greece/Brazil/Babylon/Rome | Russia/Spain/Arabia/Rome/Japan | Macedon/Zulu/Aztec/Persia/Scythia | Korea/Brazil/Canada |
| **Blind spot** | Tempo awareness | Own civ kit | Invisible rival victory | Military threats | Difficulty context |
| **Science blocked by** | — (science is correct) | No science bonuses | Religious time pressure | Military destruction | Immortal yield math |
