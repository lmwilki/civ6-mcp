# Civ 6 MCP — Agent Playbook

## What This Is

An MCP server that connects to a running Civilization VI game via the FireTuner debug protocol. You can read full game state and issue commands as if you were a human player clicking the UI. All commands respect game rules (no cheats).

## Coordinate System

**The hex grid uses (X, Y) where higher Y = visually south (down on screen).**

- Y increases going **down** (south on the map)
- Y decreases going **up** (north on the map)
- X increases going **right** (east)
- X decreases going **left** (west)
- The ocean/coast tends to be at low X values (west edge)

When reasoning about directions, remember: moving a unit from (9,24) to (9,26) moves it **south** (down), not north.

## Turn Loop

Follow this pattern every turn:

1. `get_game_overview` — orient: turn, yields, research, score, favor
2. `get_units` — see all units, positions, HP, moves, charges, nearby threats
3. `get_map_area` around your city/units — see terrain, resources, **enemy units**
4. For each unit: decide action based on context (threats, resources, terrain)
5. `get_cities` — check production queues, pillaged districts, growth
6. `get_district_advisor` if building a district — find the best adjacency tile
7. `set_city_production` / `set_research` if needed
8. `get_empire_resources` every 10 turns — check for unimproved luxuries, nearby strategics
9. `get_victory_progress` every 20-30 turns — track who's winning and adjust strategy
10. `end_turn` — auto-checks for blockers and reports events

**Periodic checks (every 15-25 turns):**
- `get_minimap` — ASCII overview of the entire map. Reveals territory shape, fog boundaries, expansion corridors
- `get_strategic_map` — fog boundaries per city + unclaimed resources. Flags directions that need exploration
- `get_global_settle_advisor` — top 10 settle sites across entire revealed map (not just near a settler)
- `get_diplomacy` — check relationship trends, defensive pacts, alliances, available actions
- `get_deal_options` — scan what civs have to trade before proposing deals

## Combat & Threat Awareness

**ALWAYS check the map before moving units.** `get_map_area` shows hostile units with `**[Barbarian WARRIOR]**` markers. This is your only source of threat information.

- Barbarians are player 63
- City-state units show with their city-state name
- Check radius 3-4 around your cities every few turns for approaching threats

**Unit strengths to know:**
- Warrior CS:20, Archer CS:25 RS:25 (range 2), Slinger CS:5 RS:15 (range 1)
- Barbarian warriors have CS:20 — as strong as your warriors
- Slingers are very weak in melee (CS:5) — keep them behind military units

**Combat tips:**
- Ranged units (slinger range 1, archer range 2) attack without taking damage
- Melee attacks move your unit onto the target tile if the enemy dies
- Fortified units get +4 defense and heal faster — use for damaged units
- The `attack` action auto-runs a combat estimator showing expected damage before committing
- Mountains block line of sight for ranged attacks — the generic CAN ATTACK check doesn't verify LOS
- Crossbows (RS:40) deal near-zero damage to Industrial-era units (CS:65+) — don't waste attacks
- City ranged attacks (with walls) are powerful defense — 14-19 damage against Infantry-class units
- Never position ranged units adjacent to melee-capable enemies — they melt in melee combat

## Unit Stacking Rules

Civ 6 does NOT allow two units of the same formation class on the same tile:
- **Military** (FORMATION_CLASS_LAND_COMBAT): warriors, archers, slingers, etc.
- **Civilian** (FORMATION_CLASS_CIVILIAN): builders, settlers, traders
- You CAN have 1 military + 1 civilian on the same tile
- The `move` action pre-checks for stacking conflicts: `ERR:STACKING_CONFLICT`

## Builder Management

- Builders have limited charges (shown as `charges:N` in `get_units`)
- They are consumed when charges reach 0
- **Builders are civilians with CS:0** — barbarians will capture them instantly
- NEVER send builders to border tiles without checking `get_map_area` for threats first
- Common improvements: `IMPROVEMENT_FARM`, `IMPROVEMENT_MINE`, `IMPROVEMENT_QUARRY`, `IMPROVEMENT_PLANTATION`, `IMPROVEMENT_PASTURE`, `IMPROVEMENT_CAMP`
- Builders can only improve tiles in YOUR territory (`owned by player 0` in map output)

## Unit Actions Reference

| Action | Effect | Notes |
|--------|--------|-------|
| `skip` | Ends the unit's turn | Always works (GameCore FinishMoves) |
| `fortify` | +4 defense, heals each turn | Military only. Non-melee (slingers/archers) sleep instead |
| `heal` | Fortify until healed, then wake | Like fortify but auto-stops at full HP |
| `alert` | Sleep but auto-wake on enemy sight | Good for sentries guarding an area |
| `sleep` | Sleep until manually woken | Unit won't wake on its own |
| `automate` | Auto-explore each turn | Great for scouts |
| `delete` | Permanently disband the unit | Removes maintenance cost |
| `move` | Move to target tile | Requires target_x, target_y |
| `attack` | Attack enemy at target tile | Melee (adjacent) or ranged (within range) |
| `found_city` | Settle a city | Settlers only |
| `improve` | Build an improvement | Builders only, requires improvement name |
| `trade_route` | Start a trade route | Traders only. Requires target_x, target_y of destination city |
| `teleport` | Move trader to a different city | Traders only, must be idle. Requires target_x, target_y of city |
| `activate` | Activate a Great Person | GP must be on completed matching district |

- Already-fortified units return `ALREADY_FORTIFIED` — just skip them
- Fortified/alert units auto-wake when enemies approach, then need new orders

## End Turn Blockers

`end_turn` checks for mandatory blockers before advancing. Common ones:
- **Units** — unmoved units need orders (move, skip, or fortify)
- **Production** — a city finished building and needs new orders
- **Research/Civic** — tech or civic completed, choose next
- **Governor** — governor point available, must appoint (Early Empire civic grants first)
- **Promotion** — unit has enough XP, must promote
- **Policy Slot** — empty policy slots to fill
- **Pantheon** — enough faith accumulated, must choose a pantheon belief
- **Envoys** — envoy token(s) available, must assign to a city-state
- **Dedication** — new era started, must choose a dedication (use `get_dedications` then `choose_dedication`)

The tool returns the blocker type and which tool to use to resolve it.

## Diplomacy

- AI encounters (first meetings, denouncements, agenda complaints) block turn progression
- `end_turn` detects pending diplomacy and tells you to use `diplomacy_respond`
- Most AI encounters are informational (1-2 rounds of POSITIVE/NEGATIVE)
- First meetings typically need 2-3 rounds of responses
- The tool auto-closes "goodbye" phases
- **Diplomacy encounters reset ALL unit orders.** After resolving diplomacy, use `skip_remaining_units` to re-fortify/skip idle units

### Proactive Diplomacy (CRITICAL — do from Turn 1)

Diplomacy is not just "respond to encounters." It is a **yield source** and **victory enabler** that compounds over time. Start early:

- **Delegations** (25 gold): Send to every civ immediately after meeting. Gives visibility and opinion bonus.
- **Friendships**: `send_diplomatic_action(action="DECLARE_FRIENDSHIP")` — now returns ACCEPTED/REJECTED (not just SENT). Requires the AI to be Friendly. Each friendship = +1 diplomatic favor/turn.
- **Open Borders**: `send_diplomatic_action(action="OPEN_BORDERS")` — returns ACCEPTED/REJECTED based on visibility change.
- **Embassies** (requires Writing tech): Gives permanent visibility and favor bonus.
- **Alliances**: Use `form_alliance(other_player_id, alliance_type)`. Requires declared friendship + Diplomatic Service civic. Types: MILITARY, RESEARCH, CULTURAL, ECONOMIC, RELIGIOUS. +1 favor/turn, era score, shared visibility. Alliances level up over time (Lv1→Lv2→Lv3).

### Defensive Pacts

`get_diplomacy` shows `!! DEFENSIVE PACTS with: Kongo (player 3)` when civs have mutual defense agreements. **Always check pacts before declaring war** — attacking one civ may trigger war with their pact partner(s). This is invisible without the tool.

### Trade Deals

- `get_deal_options(player_id)` — **call this first** to see what both sides can put on the table (gold, GPT, favor, luxuries, strategics, open borders, alliance eligibility). Like opening the trade screen.
- `propose_trade` — compose and send a trade deal. Supports:
  - Gold/GPT: `offer_gold=100`, `offer_gold_per_turn=5`, `request_gold=200`, `request_gold_per_turn=3`
  - Resources: `offer_resources="RESOURCE_FURS"`, `request_resources="RESOURCE_TEA,RESOURCE_SILK"`
  - Diplomatic favor: `offer_favor=20`, `request_favor=10`
  - Open borders: `offer_open_borders=True`, `request_open_borders=True`
  - Joint war: `joint_war_target=3` (player ID of war target, added to both sides)
  - Returns **ACCEPTED**, **REJECTED**, or **PROPOSED** (async/unclear)
- `get_pending_deals` — check for incoming trade offers from AI
- `respond_to_deal` — accept or reject incoming deals

### Alliances

- `form_alliance(other_player_id, alliance_type)` — propose an alliance
  - Types: MILITARY, RESEARCH, CULTURAL, ECONOMIC, RELIGIOUS
  - **Prerequisites**: declared friendship (30 turns) + Diplomatic Service civic
  - Returns ACCEPTED or REJECTED with details
- `get_diplomacy` shows current alliances with level (Lv1/Lv2/Lv3) and available actions including MAKE_ALLIANCE
- Alliance workflow: meet civ → delegation → friendship (30 turns) → research Diplomatic Service → form_alliance

### Peace Deals

- `propose_peace(other_player_id=X)` — offer white peace to a civ you're at war with
- Requires 10-turn war cooldown to pass (`CanMakePeaceWith` check)
- Returns ACCEPTED or REJECTED based on war score and relationship

### Diplomatic Favor

Favor is earned from: friendships (+1/turn each), alliances (+1/turn), suzerainties (+2/turn each), government legacy bonuses. Spend it in World Congress for extra votes. **Never let favor sit idle — vote aggressively in Congress for Diplomatic Victory Points.**

## Async Behavior

Several operations are asynchronous in the game engine:
- **Move**: `RequestOperation(MOVE_TO)` queues pathfinding. The response shows target coordinates, not final position. Verify with `get_units` next turn.
- **Found city**: city appears next frame, not immediately
- **Production**: takes effect next frame

## Common Mistakes to Avoid

1. **Moving military units onto tiles with other military units** — use the map to check first
2. **Sending builders to unescorted border tiles** — barbarians WILL capture them
3. **Ignoring `get_map_area` threats** — always scan before committing units
4. **Trying to build improvements outside territory** — only owned tiles work
5. **Not setting production after a build completes** — city sits idle
6. **Forgetting to choose research/civic after completion** — wastes turns
7. **Not building districts by turn 50** — Campus and Commercial Hub are the midgame engine
8. **Not building trade routes** — free yields from turn 1 of the route
9. **Ignoring amenities** — improve luxuries first, not bonus resources
10. **Exploring with warriors instead of scouts** — warriors should guard, scouts should explore
11. **Hoarding gold** — buy tiles for luxuries, buy builders, invest in growth
12. **Not exploring aggressively** — fog of war hides settle sites, barbarian camps, and resources. Use `get_strategic_map` to find unexplored directions. A scout at T20 prevents a barbarian crisis at T150.
13. **Ignoring diplomacy** — never let favor sit idle, always send delegations on first meeting, pursue friendships with FRIENDLY civs. Diplomatic favor compounds.
14. **Not checking defensive pacts before declaring war** — can trigger surprise multi-front wars
15. **Not reassessing victory path every 50 turns** — geography, tech gaps, and diplomatic positions change. Use `get_victory_progress` and be willing to pivot.
16. **Stacking units on city tiles blocks production** — if a city can't produce a unit, check for stacking conflicts

## Production & Research

- Use `get_city_production` to see what's available — shows both production cost and **gold purchase cost**
- Use `get_tech_civics` to see available research options
- Use `purchase_item` to buy units/buildings with gold instantly (shows cost vs balance on failure)
- Early priorities: Scout (exploration), Slinger/Archer (defense), Builder (improvements), Monument (culture/borders)
- Key early techs: Pottery (granary), Archery (archers), Mining (mines), Bronze Working (iron)
- Key early civics: Code of Laws (policies), Foreign Trade (trade routes), Early Empire (governors)

## City-States & Envoys

- Use `get_city_states` to see known city-states with their types, your envoy counts, and suzerain status
- Use `send_envoy` to send envoy tokens — bonuses at 1/3/6 envoys, suzerain at most envoys (min 3)
- City-state types: Scientific (+science), Industrial (+production), Trade (+gold), Cultural (+culture), Religious (+faith), Militaristic (+units)
- Envoy tokens come from civics (Mysticism, etc.) and are blocking notifications — must assign them

## Pantheon & Religion

- Use `get_available_beliefs` to see available pantheon beliefs with descriptions
- Use `choose_pantheon` to found a pantheon once you have 25 faith
- Pantheon is a blocking notification — game won't advance until you pick one
- Good early picks: God of the Forge (+25% military production), Fertility Rites (free builder + 10% growth), Lady of the Reeds (+2 production from marsh/floodplains)

## Unit Upgrades

- Use `upgrade_unit` to upgrade a unit (e.g. slinger → archer) — requires the right tech, enough gold, and moves remaining
- Common upgrade paths: Slinger → Archer (needs Archery), Warrior → Swordsman (needs Iron Working + iron), Scout → Ranger
- Upgrading consumes all movement for the turn

## Exploration (CRITICAL — the foundation of expansion)

**Exploration is not optional.** You cannot settle what you cannot see. You cannot plan around geography you haven't mapped. Fog of war hides resources, city sites, and barbarian camps.

- Build a Scout first or second (before military in most cases)
- Use `automate` to auto-explore each turn — scouts are fire-and-forget
- Use `get_strategic_map` every 15-20 turns to check fog boundaries per city
- Use `get_minimap` to see the map shape — coastlines, mountain walls, territory patterns
- **Explore TOWARD fog boundaries near your cities.** If a city has 5+ unexplored directions, something valuable is likely hiding there
- Destroy barbarian camps early (T50-80) before they become unmanageable sieges
- Use `get_global_settle_advisor` to find the best settle sites across the entire revealed map

**Lesson from Game 1:** A river valley with 3 rice, a luxury, and a strategic resource sat 5 tiles from Lublin for 323 turns because no scout was ever sent south. Two barbarian camps that spawned 150 turns of siege were 6 tiles from the nearest city. One scout at T50 would have found both.

## Strategic Benchmarks

By turn 25: Scout exploring, warrior guarding, settle site identified via `get_settle_advisor`
By turn 50: 2 cities, 1-2 builders, scout exploring edges of map, 2-3 military units, 1+ luxury improved, delegations sent to all met civs
By turn 75: 3 cities, Campus in progress, 1+ trade routes, 10+ science/turn, iron/horses located, friendships declared
By turn 100: 3-4 cities, Campus + Commercial Hub built, 20+ science, Classical/Medieval era techs, alliances forming

Score targets: Stay within 20% of AI leaders. If behind by 50%+, prioritize settlers and builders.

### Strategic Reassessment (every 50 turns)

Use `get_victory_progress` and `get_diplomacy` to answer:
1. Which victory path is most viable given current position?
2. Am I on track for the chosen path? What's the gap to the leader?
3. Should I pivot? (e.g. boxed in geographically → pivot from Science to Diplomatic)
4. What are rivals closest to winning? Can I counter?

**Geography determines strategy.** If boxed into 3-4 cities by T100, Science victory requires 100+ sci/turn which is very hard. Consider Diplomatic (favor from friendships + Congress votes) or tall empire strategies instead.

## Midgame Priorities (Turns 50-100)

1. **Districts are king.** Campus first (science compounds), then Commercial Hub (trade routes + gold).
   Use `get_district_advisor` to find the best adjacency tile BEFORE starting production.
   **Build Commercial Hub early** — it unlocks Market (trade route capacity), Bank (gold), and lets you activate Great Merchants.
2. **Trade routes = free yields.** Build a Trader as soon as you have Foreign Trade civic.
   Domestic routes to your newest city for food+production. International for gold.
3. **Improve luxuries BEFORE bonus resources.** Each luxury = +1 amenity empire-wide.
   Zero amenities = growth penalty = falling behind. Use `get_empire_resources` to track.
4. **Builders > military in peacetime.** 2-3 builders cycling improvements is more valuable
   than a 5th warrior sitting idle. Each improved tile = permanent yield increase.
5. **Expand aggressively.** Use `get_global_settle_advisor` to find the best sites. 4 cities minimum by T100.
   More cities = more districts = more yields = victory. Geography that limits you to 3-4 cities requires a strategy pivot.
6. **Diplomacy maintenance.** By T75: delegations to all, friendships with FRIENDLY civs, envoys to city-states.
   By T100: embassies, alliances forming, 3+ suzerainties for favor income.

## District Placement

Use `get_district_advisor(city_id, district_type)` to see valid tiles ranked by adjacency.
Then use `set_city_production(city_id, "DISTRICT", "DISTRICT_CAMPUS", target_x=X, target_y=Y)`.

Key adjacency tips:
- Campus: mountains (+1 each), jungles (+1 per 2), geothermal/reef (+2)
- Holy Site: mountains (+1 each), forests (+1 per 2), natural wonders (+2)
- Industrial Zone: mines (+1 each), quarries (+1 each), aqueducts (+2)
- Commercial Hub: adjacent to river (+2 flat bonus), harbors (+2)
- Theater: wonders (+1 each), Entertainment Complex (+2)

## Economy & Trade

- `get_purchasable_tiles` shows tiles you can buy with gold — prioritize luxury resources
- `purchase_tile` to buy them instantly
- `propose_trade` to trade resources/gold with other civs — trade surplus luxuries for gold per turn
- Government changes use `change_government` — first switch after new tier is free
- `set_city_focus` to bias citizen assignment (production focus for builders, food for growth)
- `get_great_people` to track Great Person recruitment race
- **Spend gold aggressively.** Gold above 500 should be invested: buy builders, buy tiles for luxuries, buy buildings to skip production time. Hoarding helps nothing.

## Trade Routes

- Use `get_trade_destinations(unit_id)` to see available destinations for a trader
- Use `execute_unit_action(unit_id, action='trade_route', target_x=X, target_y=Y)` to start a route
- **Domestic routes** send food + production to the destination city (good for new cities)
- **International routes** generate gold for the origin city
- Trader must be in a city with moves remaining
- Route capacity: 1 from Foreign Trade civic, +1 per Market/Lighthouse

## Great People

- Use `get_great_people` to see available GP candidates and recruitment progress
- When you recruit a GP, move it to the matching completed district (e.g. Great Scientist → Campus)
- Use `execute_unit_action(unit_id, action='activate')` to activate — unit is consumed
- The district must be **completed** (not just placed) for activation to work

## World Congress

- `get_world_congress` shows session status, active/passed resolutions, and voting options
- When in session (blocks turn): vote on each resolution with `vote_world_congress`
- Each resolution has two options (A/B) and a target to choose from a list
- 1 free vote per resolution, extra votes cost diplomatic favor (10/30/60/100/150)
- After voting on all resolutions, congress auto-submits
- Between sessions: shows passed resolutions and turns until next session
- The `ENDTURN_BLOCKING_WORLD_CONGRESS_LOOK` blocker (review results) is auto-resolved by `end_turn`

## Victory Conditions

Use `get_victory_progress` every 20-30 turns to track the race. There are 6 victory types:

| Victory | Condition | Key Metric |
|---------|-----------|------------|
| **Science** | Complete 4 space projects (satellite, moon, Mars, exoplanet) | Science VP (0/50) |
| **Domination** | Own every other civ's original capital | Capitals controlled |
| **Culture** | Your foreign tourists > every civ's domestic tourists | Tourism vs staycationers |
| **Religious** | Your religion is majority in all civilizations | Cities converted |
| **Diplomatic** | Earn 20 diplomatic victory points | Diplo VP from World Congress |
| **Score** | Highest score at turn 500 | Total score |

**Strategic awareness:**
- Science: Track techs researched — the tech leader will reach space race first. Need Rocketry → Spaceport → 4 projects (~15 turns each). Requires 4+ cities with strong science output.
- Domination: Watch military strength — a civ with 300+ military and your neighbor is a threat. Losing your capital = game over. Requires massive military production base.
- Culture: You need more tourists visiting FROM each civ than their domestic tourists (staycationers). Theater Squares, Great Works, Wonders, National Parks drive tourism.
- Religion: Must have FOUNDED a religion (not just a pantheon). Need religious units (Missionaries, Apostles) to spread. If you haven't founded a religion by Medieval era, this path is closed.
- Diplomatic: Favor from friendships, alliances, suzerainties. Spend in World Congress for VP. 20 VP is a long game but viable for small empires. **Start building favor income from T1.**
- Score: Fallback — whoever is ahead at turn 500 wins. Track rankings in `get_game_overview`.

**`get_victory_progress` includes:**
- Per-civ rival intelligence: city count, science/culture/gold yields, military strength
- Victory assessment: 0-100% viability score per path with recommended strategy
- Use this to decide when to pivot strategies

## Game Recovery & Save Management

When the game hangs (e.g. AI turn stuck in infinite loop), use these tools:

- `quicksave` — save current game state (works in-game via FireTuner)
- `list_saves` — show available save files with indices
- `load_save(save_index)` — reload a save file (in-game, FireTuner connection survives)
- `kill_game` — kill the Civ 6 process, waits 10s for Steam deregister
- `launch_game` — start Civ 6 via Steam, waits for main menu
- `load_save_from_menu(save_name)` — navigate main menu via OCR to load a specific save
- `restart_and_load(save_name)` — **full recovery**: kill + launch + load (60-120s)

**Common recovery scenario (AI turn hang):**
1. Call `restart_and_load("AutoSave_0221")` — handles everything automatically
2. Wait ~10 seconds after it completes
3. Call `get_game_overview` to verify the game loaded

**Save names:** Use autosave names without extension (e.g. `"AutoSave_0221"`, not `"AutoSave_0221.Civ6Save"`). If `save_name` is omitted, loads the most recent autosave.

**OCR tools require:** `uv pip install 'civ6-mcp[launcher]'` (pyobjc for macOS Vision framework). The `kill_game` and `launch_game` tools work without this dependency.

**Guardrails:** All lifecycle tools are hardcoded to Civ 6 only — process names, Steam app ID, and save directory are constants. No arbitrary system commands or config modifications are possible.

## Code Architecture

- `lua_queries.py` — Lua code builders (`build_*`) and response parsers (`parse_*`). Internal helpers: `_bail()` (error+sentinel pattern), `_lua_get_unit()` / `_lua_get_city()` (lookup boilerplate), `_ITEM_TABLE_MAP` / `_ITEM_PARAM_MAP` (production/purchase constants). All queries use pipe-delimited output and `---END---` sentinel.
- `game_state.py` — `GameState` class. High-level async methods that call `lua_queries` builders, execute via `connection`, and parse responses. Also contains narration methods for human-readable output.
- `server.py` — MCP tool definitions. Calls `GameState` methods only (never imports `lua_queries` directly).
- `game_launcher.py` — Game lifecycle management (kill/launch/OCR save loading). Standalone module with no FireTuner dependency.
- `connection.py` — Low-level TCP connection to FireTuner. Handles sentinel parsing.

## Project Conventions

- Use `uv` for Python package management
- Track progress in `DEVLOG.md`
