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

1. `get_game_overview` — orient: turn, yields, research, score
2. `get_units` — see all units, their positions, HP, moves, charges
3. `get_map_area` around your city/units — see terrain, resources, **enemy units**
4. For each unit: decide action based on context (threats, resources, terrain)
5. `get_cities` — check production queues
6. `get_district_advisor` if building a district — find the best adjacency tile
7. `set_city_production` / `set_research` if needed
8. `get_empire_resources` every 10 turns — check for unimproved luxuries, nearby strategics
9. `end_turn` — auto-checks for blockers and reports events

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
- The `attack` action checks for enemy presence first; `ERR:NO_ENEMY` means the target tile is clear

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

## Strategic Benchmarks

By turn 50: 2 cities, 1-2 builders, scout exploring, 2-3 military units, at least 1 luxury improved
By turn 75: 3 cities, Campus in progress, 1+ trade routes, 10+ science/turn, iron/horses located
By turn 100: 3-4 cities, Campus + Commercial Hub built, 20+ science, Classical/Medieval era techs

Score targets: Stay within 20% of AI leaders. If behind by 50%+, prioritize settlers and builders.

## Midgame Priorities (Turns 50-100)

1. **Districts are king.** Campus first (science compounds), then Commercial Hub (trade routes + gold).
   Use `get_district_advisor` to find the best adjacency tile BEFORE starting production.
2. **Trade routes = free yields.** Build a Trader as soon as you have Foreign Trade civic.
   Domestic routes to your newest city for food+production. International for gold.
3. **Improve luxuries BEFORE bonus resources.** Each luxury = +1 amenity empire-wide.
   Zero amenities = growth penalty = falling behind. Use `get_empire_resources` to track.
4. **Builders > military in peacetime.** 2-3 builders cycling improvements is more valuable
   than a 5th warrior sitting idle. Each improved tile = permanent yield increase.
5. **Don't over-explore with military.** Send scouts to explore, keep warriors near cities.
   A warrior 10 tiles from home can't defend against barbarian raids.

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
- Government changes use `change_government` — first switch after new tier is free
- `set_city_focus` to bias citizen assignment (production focus for builders, food for growth)
- `get_great_people` to track Great Person recruitment race

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

## Code Architecture

- `lua_queries.py` — Lua code builders (`build_*`) and response parsers (`parse_*`). Internal helpers: `_bail()` (error+sentinel pattern), `_lua_get_unit()` / `_lua_get_city()` (lookup boilerplate), `_ITEM_TABLE_MAP` / `_ITEM_PARAM_MAP` (production/purchase constants). All queries use pipe-delimited output and `---END---` sentinel.
- `game_state.py` — `GameState` class. High-level async methods that call `lua_queries` builders, execute via `connection`, and parse responses. Also contains narration methods for human-readable output.
- `server.py` — MCP tool definitions. Calls `GameState` methods only (never imports `lua_queries` directly).
- `connection.py` — Low-level TCP connection to FireTuner. Handles sentinel parsing.

## Project Conventions

- Use `uv` for Python package management
- Track progress in `DEVLOG.md`
