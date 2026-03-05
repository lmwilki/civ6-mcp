# Civ 6 MCP — Agent Reference

An MCP server connecting to a live Civilization VI game via FireTuner. You can read full game state and issue commands. All commands respect game rules.

**You only know what you explicitly query.** A human player passively absorbs the score ticker, religion lens, unit health bars — you have none of that. Information you don't ask for simply doesn't enter your world model. The patterns below exist to compensate for this.

`end_turn` now runs **empire warnings** automatically — alerts for loyalty crises, idle trade routes, gold deficits, resource caps, scoreboard position, and military imbalance. These compensate for the most common blind spots, but don't replace periodic deep checks (victory progress, religion spread, diplomacy).

## Coordinate System

**Hex grid: (X, Y) where higher Y = visually south.**
- Y increases → south (down). Y decreases → north (up).
- X increases → east. X decreases → west.
- Moving from (9,24) to (9,26) is **south**, not north.

## Game Start

Before your first turn:
1. Read your civ's unique abilities, units, and buildings — what is this civ designed to do?
2. Identify the tech/civic that unlocks your unique unit; plan a research path to reach it.
3. Form a working hypothesis for a victory path. Hold it loosely — geography and rivals will clarify things through the Classical era.

Early choices compound. Each decision shapes what's available 20, 40, 60 turns later. A scout reveals the map early; a defensive unit lets your settlers move safely; more cities mean more districts which mean more everything. Religious civs often benefit from Holy Site infrastructure before the Great Prophet pool fills. What you don't build early, you pay for later.

## Turn Loop

Each turn in order:
1. `get_game_overview` — turn, yields, research, score, era score, difficulty. If resuming after context compaction, call `get_diary` first.
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

Reflections are recorded **before** AI processing begins — write what YOU observed and did this turn. Anything that surfaces after `end_turn` (a diplomacy proposal, AI units entering your territory, events in the turn result) belongs in the **next** turn's diary, not this one.

Five reflection fields each turn (all required, non-empty):
- **tactical**: What happened — specific units, tiles, outcomes.
- **strategic**: Standings vs rivals — yields, city count, victory path viability with numbers.
- **tooling**: Tool issues observed, or "No issues".
- **planning**: Concrete actions for the next 5-10 turns — specific builds, moves, research targets with turn estimates.
- **hypothesis**: Specific predictions — attack timing, milestone turns, biggest risks.

## Strategic Checkpoints

Periodic checks worth doing regularly. The game doesn't surface most of this proactively.

### Around every 10 turns:
- `get_empire_resources` — unimproved luxuries and nearby strategics
- Surplus luxuries: duplicates beyond 1 copy provide zero amenity benefit. Trade them via `propose_trade` for GPT, strategic resources, or luxury types you don't own (each new type = +1 amenity to 4 cities). Even 5 GPT per surplus luxury adds up over 30 turns.
- Gold/faith balance: if either is accumulating with no plan, spend it — `purchase_item`, `purchase_tile`, `patronize_great_person`
- City count vs time in game — if expansion is behind, a settler tends to be the highest-leverage production choice
- `get_trade_routes` — check for idle routes; idle routes are free yields going uncollected
- Government tier — `change_government` when a new tier unlocks (free the first time)
- Era score vs thresholds — shown in `get_game_overview`; a Dark Age is recoverable but costly
- Great People — `get_great_people`; rivals will recruit what you don't

### Around every 20 turns:
- `get_diplomacy` — delegations to new civs, friendships with Friendly civs, alliances if eligible
- `get_victory_progress` — check all 6 victory types, not just your own path
- `get_religion_spread` — religious victory is invisible without active checking; a rival with majority in most civs is a serious threat

### Around every 30 turns:
- `get_strategic_map` — fog per city + unclaimed resources
- `get_global_settle_advisor` — best remaining settle sites
- Wonder scan: `get_city_production` in your best city — wonders that align with your victory path are worth considering
- Victory path check: is your chosen path still viable? Is any rival close to winning something you haven't been tracking?
- Civ kit check: are you building/using your unique units, buildings, or improvements? If not, you're playing a generic civ and giving up your structural advantage. The unique unit often requires a specific tech — if that tech isn't on your current research path, that's a problem.

## Strategic Patterns

### Moving Civilians
Before moving a builder, settler, or trader to a new tile, `get_map_area` (radius 2) around the destination is worth the query. Civilians have zero combat strength — a single barbarian scout captures them. The cost of losing a builder (5-7 turns of production + charges) is almost always worse than taking one extra turn to check or escort.

Hills cost 2 movement, forests/jungles cost 2, and they stack (forest-hills = 3+). A settler or builder with 2 base moves arriving on forest-hills uses all movement and can't act until next turn. Route through flat terrain when possible, or plan to arrive one turn early.

`get_pathing_estimate(unit_id, target_x, target_y)` estimates how many turns a unit needs to reach a destination, using the game's actual pathfinding. Use it before committing units to long marches.

### Builder Management
Idle builders are wasted production. `get_builder_tasks` shows all tiles needing improvements across your empire, prioritized (URGENT > HIGH > NORMAL), with the nearest idle builder for each task. Call it once per turn during the builder phase, then dispatch builders top-down by priority.

Don't skip builders that are 3-4 tiles from a task — a few turns of walking is better than sitting idle forever. For long-distance dispatches, use `get_pathing_estimate` to verify the route. Map tiles now show movement cost (`[mv:2]`, `[mv:3]`) and road presence — route builders along roads when possible.

After context compaction, call `get_builder_tasks` again to reconstruct your builder situation. The tool provides a fresh snapshot — no need to remember previous assignments.

### Spending Gold & Faith
Gold and faith sitting idle lose value over time. `purchase_item(city_id, item_type, item_name)` buys units/buildings instantly with gold (or faith via `yield_type="YIELD_FAITH"`). `purchase_tile(city_id, x, y)` buys a specific tile. `patronize_great_person` buys a GP outright. If you're saving, name the item and the turn — otherwise, deploy it.

### Expansion
Each city multiplies your districts, yields, and Great Person generation. The gap between a 3-city and 5-city empire by the Medieval era is hard to recover from. If city count is lagging, a settler is typically the highest-impact production choice — more so than most infrastructure in existing cities. Check loyalty before settling: negative-loyalty sites near rivals need a governor assigned immediately via `assign_governor(governor_type, city_id)` or they'll flip.

### Growth
Stagnant cities fall behind exponentially. If any city has food surplus ≤ 0, that's worth fixing this turn (Farm, Granary, domestic Trade Route, or `set_city_focus(city_id, "FOOD")`). Turns-to-growth over 15 is a signal the city needs food infrastructure.

### Exploration
You can't settle what you can't see, and you can't counter threats you don't know exist. A scout set to `automate` is one of the best investments in the early game. If a scout is lost or stuck, replacing it early keeps the information flow going.

### Diplomacy
Diplomacy generates yield: each alliance +1 favor/turn per alliance level, each suzerainty +1 favor/turn. Government tier also gives favor. This compounds. Friendships don't give favor directly but enable alliances (which do). Delegations (25g) are cheap on first meeting. Friendships open up when a civ is Friendly. Alliances require friendship (30+ turns) and Diplomatic Service civic. Embassies are available once Writing is researched.

If favor is accumulating above 100 with no World Congress imminent, it's worth thinking about whether it could be better deployed in trade or alliance building.

### Wartime
During war, keeping a military unit garrisoned in or near each city is worth the tradeoff against offensive strength. Cities with walls can fire at enemies via `city_action(city_id, "attack", target_x, target_y)` (range 2). Cities that fall are expensive to recover — when you capture a city, `city_action` with `keep`, `raze`, or `liberate_founder`/`liberate_previous` resolves the decision. If your military strength is significantly below an enemy's and you're not making progress, `propose_peace(player_id)` — available after a 10-turn cooldown — is usually better than a war of attrition while the rest of the map moves on.

### Military Readiness
Check rival military strength in `get_diplomacy` periodically. A neighbor at 2x+ your strength who isn't a friend or ally is a risk worth taking seriously. Minimum useful peacetime: 1 garrison per city plus a mobile unit. Units become progressively weaker relative to rivals if not upgraded (Slinger→Archer with Archery, Warrior→Swordsman with Iron Working) — use `upgrade_unit`.

### Barbarian Camps
Camps upgrade with the era — an Ancient-era camp spawns Warriors; the same camp in the Medieval era spawns Man-at-Arms. Clearing a camp within a few turns of finding it is almost always easier than fighting the units it produces over many turns.

### Religion
Religious victory is the easiest win condition to miss because it produces no notifications and unfolds slowly. `get_religion_spread` shows the picture. If a rival religion reaches majority in most civs, the window for a response narrows quickly. Religious units bought from a city carry **that city's majority religion** — buy them from cities where your own religion is majority, not a converted city.

To found a religion: build a Holy Site → earn a Great Prophet → `get_religion_beliefs()` to see available beliefs → `found_religion(name, beliefs)`. The Great Prophet pool fills early (roughly half the major civs).

Trade routes spread the origin city's religion to the destination — worth factoring into routing decisions if conversion pressure is a concern.

### Victory Path Viability
Some paths close. It's worth checking periodically via `get_victory_progress`:

- **Science**: Campuses → Universities → Spaceport → 4 space projects. Research Alliances and Great Scientists accelerate.
- **Culture**: Tourism (offense) vs rival domestic tourists (defense). Theater Squares, Great Works, Wonders, Open Borders (+25%), Trade Routes (+25%). Late-game: National Parks, Rock Bands, Seaside Resorts.
- **Religious**: Requires a founded religion (Great Prophet pool fills early). Missionaries spread; Apostles fight theological combat (killing = 250 pressure in 10-tile radius). Buy religious units only from cities where your religion is majority.
- **Diplomatic**: 20 DVP. World Congress resolutions, scored competitions, wonders. Favor from government tier, alliances, suzerainties. If a DVP-stripping resolution targets you, vote Option B on yourself (net 0 vs -2).

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
- Combat estimates include promotion CS bonuses, flanking (+2 per adjacent friendly to defender), support (+2 per defender's adjacent friendly), and forest/jungle defense (+3)

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
| `improve` | Build improvement | Builders and Military Engineers; see improvements below |
| `remove_feature` | Chop/harvest feature | Builders only; removes forest, jungle, or marsh from tile |
| `build_route` | Build road/railroad | Military Engineers only; on current tile; no charges used |
| `trade_route` | Start route | Traders; target_x/y of destination city |
| `teleport` | Move idle trader | Traders only; target_x/y of city |
| `activate` | Use Great Person | Must be on completed matching district |
| `spread_religion` | Spread religion | Missionaries/Apostles |

Common improvements: `IMPROVEMENT_FARM`, `IMPROVEMENT_MINE`, `IMPROVEMENT_QUARRY`, `IMPROVEMENT_PLANTATION`, `IMPROVEMENT_PASTURE`, `IMPROVEMENT_CAMP`, `IMPROVEMENT_FISHING_BOATS`, `IMPROVEMENT_LUMBER_MILL`

Feature removal: Forest, jungle, and marsh tiles block most improvements (e.g. Farm). Use `remove_feature` to chop/harvest the feature first, then `improve` to build. Lumber Mill and Camp work on forest/jungle without removal. Check `valid_improvements` in `get_units` output — if FARM isn't listed on a tile you expect it, the tile likely has a blocking feature.

Builders repair tile improvements. Pillaged **district buildings** (Workshop, Arena, etc.) are repaired via `set_city_production`.

`get_cities` shows unimproved resource tiles and pillaged improvements/districts per city — use this to prioritize builder work without needing to scan `get_map_area` manually.

Military Engineers (requires Encampment + Armory): `build_route` builds a railroad on the current tile (no charges consumed; costs 1 Iron + 1 Coal per tile). `improve` with `IMPROVEMENT_FORT` or `IMPROVEMENT_AIRSTRIP` uses charges. Building a railroad consumes all movement — one tile per engineer per turn.

| Other unit tools | |
|--------|--------|
| `skip_remaining_units` | Skip all units with remaining moves (useful after diplomacy) |
| `upgrade_unit(unit_id)` | Upgrade to next type (requires tech + resources + gold) |

## End Turn Blockers

`end_turn` resolves blockers before advancing. If it returns a blocker:
- **Units**: unmoved units need orders (move / skip / fortify)
- **Production**: city queue empty — set new production
- **Research/Civic**: completed — choose next
- **Governor**: point available — `get_governors` → `appoint_governor` / `assign_governor(governor_type, city_id)` / `promote_governor(governor_type, promotion_type)`
- **Promotion**: unit has XP — `get_unit_promotions` → `promote_unit`
- **Policy Slot**: empty — `get_policies` → `set_policies`
- **Pantheon/Religion**: faith threshold reached — `get_pantheon_beliefs` → `choose_pantheon`; for founding: `get_religion_beliefs` → `found_religion`
- **Envoys**: tokens available — `get_city_states` → `send_envoy`
- **Dedication**: new era — `get_dedications` → `choose_dedication`
- **City Capture**: conquered or disloyal city — `city_action(city_id, "keep"/"raze"/"liberate_founder"/"liberate_previous")`
- Move responses show the **target tile**, not arrival position (async pathfinding)

## Diplomacy

**Reactive (AI-initiated):** AI encounters block turn progression. Use `respond_to_diplomacy` (POSITIVE/NEGATIVE, 2-3 rounds). Diplomacy sessions do not affect unit movement or orders — continue commanding units normally afterward.

**Proactive:**
- `send_diplomatic_action(action="DIPLOMATIC_DELEGATION")` — 25g, worth sending on first meeting
- `send_diplomatic_action(action="DECLARE_FRIENDSHIP")` — requires Friendly status
- `send_diplomatic_action(action="RESIDENT_EMBASSY")` — requires Writing tech
- `form_alliance(player_id, type)` — types: MILITARY/RESEARCH/CULTURAL/ECONOMIC/RELIGIOUS; requires friendship 30t + Diplomatic Service civic
- `propose_trade(player_id, ...)` — trade gold/GPT/resources/favor/open borders
- `propose_peace(player_id)` — white peace; 10t war cooldown required
- `get_trade_options(other_player_id)` — see what a civ has available to trade
- `get_pending_trades` — check incoming trade offers; `respond_to_trade(player_id, accept)` to accept/reject
- Check `get_diplomacy` for defensive pacts before declaring war
- `get_diplomacy` shows leader agendas — historical agendas are always visible; random agendas require Secret diplomatic visibility (spy in their capital or alliance). Use agendas to predict AI behavior and avoid relationship penalties.

**Espionage:** `get_spies` → `spy_action(spy_id, action, ...)`. Actions: `travel` to a city first, then run operations (steal tech, neutralize governors, etc.). Offensive missions only work after the spy arrives.

**City-states:** `get_city_states` → `send_envoy`. Suzerainty = +1 favor/turn. Types: Scientific/Industrial/Trade/Cultural/Religious/Militaristic.

**Diplomatic Favor:** earned from government tier (base +1, scales with tier), alliances (+1/t per level), suzerainties (+1/t). Spend in World Congress for Diplomatic Victory Points.

## Production & Research

Wonders — high-production cities can slot these between infrastructure. Use `get_wonder_advisor(city_id, wonder_name)` for placement, then `set_city_production` with target_x/y. Science: Great Library, Oxford University, Kilwa Kisiwani. Culture: Chichen Itza, Forbidden City. General: Ancestral Hall, Pyramids.

**Research:** `get_tech_civics` sorts by turns ascending; items ≤ 2 turns are flagged `!! GRAB THIS` — cheap boosted techs are easy to miss and can unblock entire production chains.

**Purchasing:** `purchase_item(city_id, item_type, item_name)` — buy units or buildings instantly with gold (default) or faith (`yield_type="YIELD_FAITH"`). `get_city_production` shows purchasable items and costs.

**Tiles:** `get_purchasable_tiles(city_id)` → `purchase_tile(city_id, x, y)` — buy border tiles with gold for strategic resources or district placement.

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

- `get_trade_routes` — see all active routes and idle traders
- `get_trade_destinations(unit_id)` → available destinations
- `unit_action(action='trade_route', target_x, target_y)` → start route
- Domestic routes: food + production to new cities. International: gold.
- Capacity: 1 from Foreign Trade civic, +1 per Market/Lighthouse
- Idle routes are free yields going uncollected

## Great People

- `get_great_people` — candidates, recruitment progress, and costs
- `recruit_great_person(individual_id)` — recruit with accumulated GP points (check `[CAN RECRUIT]`)
- `patronize_great_person(individual_id)` — buy instantly with gold or faith
- `reject_great_person(individual_id)` — pass, advance to next candidate in that class
- Rivals will recruit what you pass on — recruiting quickly tends to be worth it
- Once recruited, move the GP to its matching completed district; `unit_action(action='activate')`
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
- DVP resolutions: read what each option actually awards before voting. Concentrate favor on the single most impactful resolution rather than spreading thin. Verify your vote blocks the rival, not accidentally helps them

## Victory Conditions

| Victory | Win Condition | Monitor Via |
|---------|---------------|-------------|
| Science | 4 space projects complete | `get_victory_progress` |
| Domination | Own all rival original capitals | military strength in `get_diplomacy` |
| Culture | Foreign tourists > every civ's domestic | tourism in `get_victory_progress` |
| Religious | Your religion majority in ALL civs | `get_religion_spread` regularly |
| Diplomatic | 20 diplomatic victory points | World Congress votes |
| Score | Highest score at turn limit | fallback |

All victories trigger immediately when the condition is met — they do not wait for a turn boundary or WC session. A rival reaching 20 DVP wins before your next turn. The only counter is stripping DVP at a World Congress *before* they reach 20.

`end_turn` runs a victory proximity scan every turn and a full snapshot every 10 turns. These warnings are the primary signal for invisible victories — worth paying attention to.

## Game Recovery

**MCP autosaves:** `end_turn` automatically saves every turn as `0_MCP_NNNN` (last 5 kept). These are your primary recovery points.

**Load by name** (preferred — no `list_saves` needed):
```
load_game_save("0_MCP_0079")  # load specific turn (~5s via Lua, ~90s via menu fallback)
get_game_overview              # verify load
```

**When the game hangs** (AI turn loop):
```
restart_and_load("0_MCP_NNNN")   # kill + relaunch + load (~90s)
get_game_overview                 # verify load
```

**Turn regression detection:** If you accidentally load a wrong save (e.g. the T1 scenario save instead of your autosave), `end_turn` will emit a CRITICAL warning with the correct autosave name to reload.

Other tools: `quicksave`, `list_saves`, `load_save(index)`, `kill_game`, `launch_game`, `load_save_from_menu(name)`.
Save names omit extension: `"AutoSave_0221"` not `"AutoSave_0221.Civ6Save"`.
