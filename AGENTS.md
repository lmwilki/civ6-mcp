# Civ 6 MCP — Agent Reference

An MCP server connecting to a live Civilization VI game via FireTuner. You can read full game state and issue commands. All commands respect game rules.

## Sensorium Awareness

**You only know what you explicitly query.** A human player passively absorbs the minimap, score ticker, religion lens, unit health bars — you have none of that. Information you don't ask for simply doesn't enter your world model. The checkpoints and patterns below exist to compensate for this.

## Coordinate System

**Hex grid: (X, Y) where higher Y = visually south.**
- Y increases → south (down). Y decreases → north (up).
- X increases → east. X decreases → west.
- Moving from (9,24) to (9,26) is **south**, not north.

## Game Start

Before your first turn:
1. Read your civ's unique abilities, units, and buildings — what is this civ designed to do?
2. Identify the tech/civic that unlocks your unique unit; plan a research path to reach it.
3. Form a working hypothesis for a victory path. Hold it loosely — geography and rivals will clarify things by T80-100.

Early choices compound. What you build first shapes what's available at T20, T40, T60. A scout reveals the map early; a defensive unit lets your settlers move safely; more cities mean more districts which mean more everything. Religious civs often benefit from Holy Site infrastructure before the Great Prophet pool fills. What you don't build early, you pay for later.

## Turn Loop

Each turn in order:
1. `get_game_overview` — turn, yields, research, score, era score. If resuming after context compaction, call `get_diary` first.
2. `get_units` — positions, HP, moves, charges, nearby threats
3. `get_map_area` around cities/units — terrain, resources, enemy units
4. Move/action each unit
5. `get_cities` — queues, growth, pillaged districts
6. `get_district_advisor` if placing a new district
7. `set_city_production` / `set_research` if needed
8. Run **Strategic Checkpoints** if it's time
9. `end_turn`

## Diary

The diary is your persistent memory across sessions. When context compacts or you return to a game, `get_diary` is how you reconstruct where you were and why you made the decisions you did. Entries with specific details — unit names, coordinates, yield numbers, reasoning — are far more useful to your future self than brief summaries.

Five fields each turn:
- **tactical**: What happened — specific units, tiles, outcomes.
- **strategic**: Standings vs rivals — yields, city count, victory path viability with numbers.
- **tooling**: Tool issues observed, or "No issues".
- **planning**: Concrete actions for the next 5-10 turns — specific builds, moves, research targets with turn estimates.
- **hypothesis**: Specific predictions — attack timing, milestone turns, biggest risks.

## Strategic Checkpoints

Periodic checks worth doing regularly. The game doesn't surface most of this proactively.

### Around every 10 turns:
- `get_empire_resources` — unimproved luxuries and nearby strategics
- Gold balance: if gold is accumulating above ~500 with no specific plan, deploying it (builder, tile, building, unit) is usually better than holding it
- Faith balance: high faith is most valuable when spent — Great Person patronage, faith purchases, religious units
- City count vs benchmarks (see below) — if expansion is behind, a settler tends to be the highest-leverage production choice
- Trade route capacity — idle routes are free yields going uncollected
- Government tier — switching when a new tier unlocks is free the first time
- Era score vs thresholds — shown in `get_game_overview`; a Dark Age is recoverable but costly
- Great People — `get_great_people`; rivals will recruit what you don't

### Around every 20 turns:
- `get_diplomacy` — delegations to new civs, friendships with Friendly civs, alliances if eligible
- `get_victory_progress` — check all 6 victory types, not just your own path
- `get_religion_spread` — religious victory is invisible without active checking; a rival with majority in most civs is a serious threat
- `get_minimap` — map shape, territory, fog boundaries

### Around every 30 turns:
- `get_strategic_map` — fog per city + unclaimed resources
- `get_global_settle_advisor` — best remaining settle sites
- Victory path check: is your chosen path still viable? Is any rival close to winning something you haven't been tracking?
- Civ kit check: are you building/using your unique units, buildings, or improvements? If not, you're playing a generic civ and giving up your structural advantage. The unique unit often requires a specific tech — if that tech isn't on your current research path, that's a problem.

## Strategic Patterns

### Moving Civilians
Before moving a builder, settler, or trader to a new tile, `get_map_area` (radius 2) around the destination is worth the query. Civilians have zero combat strength — a single barbarian scout captures them. The cost of losing a builder (5-7 turns of production + charges) is almost always worse than taking one extra turn to check or escort.

### Gold
Gold sitting above 500 with no specific plan is usually better deployed. A builder, a luxury tile, a building that skips 5+ turns of production — these compound. Saving for a specific purchase is fine, but it helps to name the item and the turn.

### Expansion
Each city multiplies your districts, yields, and Great Person generation. The gap between a 3-city and 5-city empire at T100 is hard to recover from. By the mid-game benchmarks:
- T40: 2 cities underway
- T60: 3 cities
- T80: 4 cities
- T100: 4-5 cities
If city count is lagging, a settler is typically the highest-impact production choice — more so than most infrastructure in existing cities. Check loyalty before settling: negative-loyalty sites near rivals need a governor (Victor or Amani) assigned immediately or they'll flip.

### Growth
Stagnant cities fall behind exponentially. If any city has food surplus ≤ 0, that's worth fixing this turn (Farm, Granary, domestic Trade Route, or citizen reassignment). Turns-to-growth over 15 is a signal the city needs food infrastructure.

### Exploration
You can't settle what you can't see, and you can't counter threats you don't know exist. A scout set to `automate` is one of the best investments in the early game. If a scout is lost or stuck, replacing it early keeps the information flow going. Exploration benchmarks: T25 ≥15%, T50 ≥25%, T75 ≥35%, T100 ≥50%.

### Diplomacy
Diplomacy generates yield: each friendship is +1 favor/turn, each alliance +1 favor/turn, each suzerainty +2 favor/turn. This compounds. Delegations (25g) are cheap on first meeting. Friendships open up when a civ is Friendly. Alliances require friendship (30+ turns) and Diplomatic Service civic. Embassies are available once Writing is researched.

If favor is accumulating above 100 with no World Congress imminent, it's worth thinking about whether it could be better deployed in trade or alliance building.

### Wartime
During war, keeping a military unit garrisoned in or near each city is worth the tradeoff against offensive strength. Cities that fall are expensive to recover. If your military strength is significantly below an enemy's and you're not making progress, peace — available after a 10-turn cooldown — is usually better than a war of attrition while the rest of the map moves on.

### Military Readiness
Check rival military strength in `get_diplomacy` periodically. A neighbor at 2x+ your strength who isn't a friend or ally is a risk worth taking seriously. Minimum useful peacetime: 1 garrison per city plus a mobile unit. Units become progressively weaker relative to rivals if not upgraded when new techs unlock (Slinger→Archer with Archery, Warrior→Swordsman with Iron Working).

### Barbarian Camps
Camps upgrade with the era — a camp at T50 spawns Warriors; the same camp at T150 spawns Man-at-Arms. Clearing a camp within a few turns of finding it is almost always easier than fighting the units it produces over 100 turns.

### Religion
Religious victory is the easiest win condition to miss because it produces no notifications and unfolds slowly. `get_religion_spread` shows the picture. If a rival religion reaches majority in most civs, the window for a response narrows quickly. Religious units bought from a city carry **that city's majority religion** — buy them from cities where your own religion is majority, not a converted city.

Trade routes spread the origin city's religion to the destination — worth factoring into routing decisions if conversion pressure is a concern.

### Victory Path Viability
Some paths close. It's worth checking periodically:
- **Science**: realistically needs 4+ cities with Campuses and Universities generating 80+ science by ~T150
- **Culture**: Theater Squares in most cities, Great Works, Wonders — zero Theater Squares at T100 puts this path very far behind
- **Religious**: requires a founded religion; if T80 arrives with no religion, this path is closed
- **Diplomatic**: viable at most empire sizes; favor income from alliances/friendships/suzerainties, spent at World Congress

## Combat Quick Reference

| Unit | CS | RS | Range |
|------|----|----|-------|
| Warrior | 20 | — | — |
| Slinger | 5 | 15 | 1 |
| Archer | 25 | 25 | 2 |
| Barbarian Warrior | 20 | — | — |

- Ranged attacks don't take damage; melee attacks do
- Forests/mountains block ranged LOS → `ERR:NO_LOS`
- Fortified units: +4 defense, heal each turn

## Unit Actions Reference

| Action | Effect | Notes |
|--------|--------|-------|
| `move` | Move to tile | target_x, target_y required |
| `attack` | Attack enemy | Shows damage estimate; melee/ranged auto-detected |
| `fortify` | +4 defense, heals | Military only |
| `heal` | Fortify until full HP | Auto-wakes at full HP |
| `alert` | Sleep, wake on enemy | Sentry use |
| `sleep` | Sleep indefinitely | Manual wake required |
| `skip` | End unit's turn | Always works |
| `automate` | Auto-explore | Scouts only |
| `delete` | Disband unit | Removes maintenance |
| `found_city` | Settle | Settlers only |
| `improve` | Build improvement | Builders only; see improvements below |
| `trade_route` | Start route | Traders; target_x/y of destination city |
| `teleport` | Move idle trader | Traders only; target_x/y of city |
| `activate` | Use Great Person | Must be on completed matching district |
| `spread_religion` | Spread religion | Missionaries/Apostles |

Common improvements: `IMPROVEMENT_FARM`, `IMPROVEMENT_MINE`, `IMPROVEMENT_QUARRY`, `IMPROVEMENT_PLANTATION`, `IMPROVEMENT_PASTURE`, `IMPROVEMENT_CAMP`, `IMPROVEMENT_FISHING_BOATS`

Builders repair tile improvements. Pillaged **district buildings** (Workshop, Arena, etc.) are repaired via `set_city_production`.

## End Turn Blockers

`end_turn` resolves blockers before advancing. If it returns a blocker:
- **Units**: unmoved units need orders (move / skip / fortify)
- **Production**: city queue empty — set new production
- **Research/Civic**: completed — choose next
- **Governor**: point available — `get_governors` → `appoint_governor`
- **Promotion**: unit has XP — `get_unit_promotions` → `promote_unit`
- **Policy Slot**: empty — `get_policies` → `set_policies`
- **Pantheon/Religion**: faith threshold reached — `get_pantheon_beliefs` → `choose_pantheon`
- **Envoys**: tokens available — `get_city_states` → `send_envoy`
- **Dedication**: new era — `get_dedications` → `choose_dedication`
- Move responses show the **target tile**, not arrival position (async pathfinding)

## Diplomacy

**Reactive (AI-initiated):** AI encounters block turn progression. Use `respond_to_diplomacy` (POSITIVE/NEGATIVE, 2-3 rounds). After any diplomacy session, call `skip_remaining_units` — encounters reset unit orders.

**Proactive:**
- `send_diplomatic_action(action="DIPLOMATIC_DELEGATION")` — 25g, worth sending on first meeting
- `send_diplomatic_action(action="DECLARE_FRIENDSHIP")` — requires Friendly status
- `send_diplomatic_action(action="RESIDENT_EMBASSY")` — requires Writing tech
- `form_alliance(player_id, type)` — types: MILITARY/RESEARCH/CULTURAL/ECONOMIC/RELIGIOUS; requires friendship 30t + Diplomatic Service civic
- `propose_trade(player_id, ...)` — trade gold/GPT/resources/favor/open borders
- `propose_peace(player_id)` — white peace; 10t war cooldown required
- Check `get_diplomacy` for defensive pacts before declaring war

**City-states:** `get_city_states` → `send_envoy`. Suzerainty = +2 favor/turn. Types: Scientific/Industrial/Trade/Cultural/Religious/Militaristic.

**Diplomatic Favor:** earned from friendships (+1/t), alliances (+1/t), suzerainties (+2/t). Spend in World Congress for Diplomatic Victory Points.

## Production & Research

**Common early tech path:** Pottery → Archery → Mining → Animal Husbandry → Bronze Working

**Common early civics:** Code of Laws → Foreign Trade → Early Empire

**Production priority guidance:**
1. Settler — if city count is behind benchmarks and a good site is identified
2. Military unit — if under threat or a city has no garrison
3. Builder — if unimproved luxury/strategic resources exist
4. Trader — if route capacity exceeds active routes
5. District — Campus compounds well early; Commercial Hub provides trade routes and gold
6. Buildings — Library, Market within completed districts
7. Infrastructure — Granary, Water Mill, Monument

**Research:** `get_tech_civics` sorts by turns ascending; items ≤ 2 turns are flagged `!! GRAB THIS` — cheap boosted techs are easy to miss and can unblock entire production chains.

## District Placement

Use `get_district_advisor(city_id, district_type)` for ranked tiles. Then `set_city_production` with target_x/y.

| District | Adjacency bonuses |
|----------|------------------|
| Campus | +1 per mountain, +1 per 2 jungles, +2 geothermal/reef |
| Holy Site | +1 per mountain, +1 per 2 forests, +2 natural wonder |
| Industrial Zone | +1 per mine/quarry, +2 aqueduct |
| Commercial Hub | +2 adjacent river, +2 harbor |
| Theater Square | +1 per wonder, +2 Entertainment Complex |
| Encampment | cannot be adjacent to city center |

## Trade Routes

- `get_trade_destinations(unit_id)` → available destinations
- `unit_action(action='trade_route', target_x, target_y)` → start route
- Domestic routes: food + production to new cities. International: gold.
- Capacity: 1 from Foreign Trade civic, +1 per Market/Lighthouse
- Idle routes are free yields going uncollected

## Great People

- `get_great_people` — candidates and recruitment progress
- Rivals will recruit what you pass on — recruiting quickly tends to be worth it
- Move GP to its matching completed district; `unit_action(action='activate')`
- If activation fails, the error message includes the requirements (district type, buildings needed)
- Don't delete GPs — they show 0 builder charges but that's a different system; they're not consumed until activated

## World Congress

WC fires synchronously inside `end_turn()` — register votes **before** calling end_turn.

**Voting flow:**
1. `get_world_congress()` — when `turns_until_next = 0`, WC fires this turn
2. Review resolutions (options A/B, target list, favor costs)
3. `queue_wc_votes(votes='[{"hash": H, "option": 1, "target": 0, "votes": N}]')`
4. `end_turn()` — handler fires, votes deploy, turn advances

- `hash`: from `get_world_congress`; `option`: 1=A / 2=B; `target`: player_id resolved to list index at runtime; `votes`: max to spend
- 1 free vote per resolution (costs nothing — worth casting)
- Extra votes cost 6/18/36/60/90/126... cumulative favor
- Keeping 50-100 favor in reserve between sessions provides flexibility for the next session

## Victory Conditions

| Victory | Win Condition | Monitor Via |
|---------|---------------|-------------|
| Science | 4 space projects complete | `get_victory_progress` |
| Domination | Own all rival original capitals | military strength in `get_diplomacy` |
| Culture | Foreign tourists > every civ's domestic | tourism in `get_victory_progress` |
| Religious | Your religion majority in ALL civs | `get_religion_spread` every 20t |
| Diplomatic | 20 diplomatic victory points | World Congress votes |
| Score | Highest score at T500 | fallback |

`end_turn` runs a victory proximity scan every turn and a full snapshot every 10 turns. These warnings are the primary signal for invisible victories — worth paying attention to.

## Game Recovery

When the game hangs (AI turn loop):
```
restart_and_load("AutoSave_NNNN")   # kill + relaunch + load (~90s)
# wait 10s, then:
get_game_overview                    # verify load
```

Other tools: `quicksave`, `list_saves`, `load_save(index)`, `kill_game`, `launch_game`, `load_save_from_menu(name)`.
Save names omit extension: `"AutoSave_0221"` not `"AutoSave_0221.Civ6Save"`.
