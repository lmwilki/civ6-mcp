# Civ 6 MCP — Agent Playbook

## What This Is

An MCP server that connects to a running Civilization VI game via the FireTuner debug protocol. You can read full game state and issue commands as if you were a human player clicking the UI. All commands respect game rules (no cheats).

## The Sensorium Problem (READ THIS FIRST)

You have a fundamental perceptual limitation. A human player passively absorbs dozens of game-state signals per second through vision — the minimap, score ticker, religion lens, unit health bars, fog boundaries, rival army movements. You have none of this. **You only know what you explicitly query. Information you don't ask for does not exist in your world model.**

This means:
- A rival can build 11 cities while you have 3, and you won't notice unless you check.
- A religion can convert every city on the map over 100 turns without you ever seeing a missionary.
- Barbarian camps 6 tiles from your cities can spawn 150 turns of siege because you never scouted that direction.
- Gold can pile up to 4,000 while you write reflections saying "I should spend gold."

**The antidote is not intelligence — it is discipline.** You already know what to do. The failure mode is not doing it. Every rule below that starts with IF/WHEN is a hard trigger, not a suggestion. Treat violations as bugs.

## Coordinate System

**The hex grid uses (X, Y) where higher Y = visually south (down on screen).**

- Y increases going **down** (south on the map)
- Y decreases going **up** (north on the map)
- X increases going **right** (east)
- X decreases going **left** (west)
- The ocean/coast tends to be at low X values (west edge)

When reasoning about directions, remember: moving a unit from (9,24) to (9,26) moves it **south** (down), not north.

## Turn 0: Game Start Checklist

Before your first turn, do this ONCE:

1. **Read your civ's abilities.** What makes this civ unique? Military? Religious? Scientific? Culture?
2. **Plan around your civ's strengths.** If your civ has religious bonuses, you MUST prioritize founding a religion (Holy Site by T30, Shrine by T40). If military, plan early aggression. If scientific, still expand — science victory needs 4+ cities.
3. **Write down your unique units/buildings and their unlock techs/civics.** These are research milestones — plan your tech path to reach them. If your UU unlocks at Iron Working, that's an early priority. If your unique building requires an Encampment, plan to build one by T60-70. A civ kit that never gets used is a wasted civ pick.
4. **Set a victory path hypothesis** — but hold it loosely until T80-100 when geography is clearer.
5. **Commit to the opening build order:** Scout → Slinger → Settler (adjust for civ-specific needs, e.g. Holy Site rush for religious civs).

## Turn Loop

Follow this pattern every turn:

1. `get_game_overview` — orient: turn, yields, research, score, favor, era score. If resuming after a context compaction or new session, also call `get_diary` to restore strategic memory from previous turns.
2. `get_units` — see all units, positions, HP, moves, charges, nearby threats
3. `get_map_area` around your city/units — see terrain, resources, **enemy units**
4. For each unit: decide action based on context (threats, resources, terrain)
5. `get_cities` — check production queues, pillaged districts, growth
6. `get_district_advisor` if building a district — find the best adjacency tile
7. `set_city_production` / `set_research` if needed
8. **Run the Strategic Checkpoint** (see below) if it's due this turn
9. `end_turn` — auto-checks for blockers and reports events (includes victory proximity alerts). **All 5 diary reflection fields are required** — they form your persistent memory across sessions:
   - `tactical`: What happened this turn — combat results, unit movements, improvements built. Name specific units, tiles, and outcomes.
   - `strategic`: Current standing vs rivals — yields, city count, victory path viability. Include numbers (e.g. "42 sci/turn, 4 cities vs Kongo's 6").
   - `tooling`: Tool issues or observations. Write "No issues" if none — this forces you to confirm you checked.
   - `planning`: Concrete actions for the next 5-10 turns. Not vague intentions — specific builds, moves, research targets with turn estimates.
   - `hypothesis`: Predictions — when will the enemy attack? When will you hit a tech milestone? What's the biggest risk? Be specific and falsifiable.

### Diary Quality Standards (READ THIS)

The diary is your ONLY memory between sessions. When context compacts or a new session starts, `get_diary` is the only way to recover strategic context. **Terse entries destroy your future self's ability to make informed decisions.**

Each field MUST be at least 1-2 substantive sentences. One-word or one-phrase entries like "Moved units" or "Fine" are bugs. Write entries that would let a fresh agent reconstruct the game state and strategic reasoning without access to any other context.

Bad: `tactical: "Built farm. Moved warrior."` — WHERE? WHY? What was the result?
Good: `tactical: "Builder improved wheat at (14,22), +2 food for Alexandria (now 6.2 food surplus). Warrior moved to (16,20) to escort settler toward settle site at (18,19). Archer fortified at (12,24) guarding northern approach — barb camp spotted 5 tiles north last turn."`

Bad: `planning: "Build more units."` — WHAT units? WHERE? For what purpose?
Good: `planning: "T85-90: Finish Campus in Memphis (3 turns), start Commercial Hub. Buy builder in Thebes (280g) to improve horses at (9,17). Research Apprenticeship (8 turns) for Industrial Zone adjacency. Need 2 more archers before T100 — Sumeria has 180 military strength vs our 95."`

## Strategic Checkpoint (MANDATORY — every 10 turns)

On every turn divisible by 10 (T10, T20, T30, ...), run this checklist. **Do not skip it.** This is the primary defense against the sensorium problem.

### Every 10 turns:
- `get_empire_resources` — check for unimproved luxuries and nearby strategics
- **Gold check**: IF gold > 500, decide RIGHT NOW what to buy (builder, tile, building, unit). List the purchase and execute it before ending the turn. Do not defer.
- **Faith check**: IF faith > 200 and you have a use for it (Great Person patronage, faith purchases), spend it now.
- **Expansion check**: Compare your city count to the benchmarks below. IF behind, the next production item in your capital MUST be a Settler. No exceptions.
- **Trade route check**: IF trade route capacity > active routes, build or reassign a Trader immediately.
- **Government check**: IF a new government tier has been unlocked by a civic (Political Philosophy → Classical, Exploration → Renaissance, Ideology civics → Modern) and you haven't switched, switch NOW. First switch per tier is free (no anarchy). Oligarchy (+4 CS to all melee/ranged/anti-cav) is almost always the correct Classical choice.
- **Era score check**: Check era score vs thresholds in `get_game_overview`. IF heading for Dark Age and era is ending soon, prioritize era-score actions (settling cities, building districts, meeting civs, clearing barbarian camps, building wonders).
- **Great People check**: `get_great_people` — IF you can recruit any Great Person, do it immediately. Great People are one-time opportunities — if you don't recruit them, a rival will. Move recruited GPs to their matching district and activate.

### Every 20 turns:
- `get_diplomacy` — check relationships. For each civ:
  - IF met and no delegation sent → send delegation (25 gold)
  - IF FRIENDLY and no friendship declared → declare friendship
  - IF friendship active 30+ turns and Diplomatic Service researched → propose alliance
  - IF at war → check if peace is available and desirable
- `get_victory_progress` — track who is winning. Check EVERY victory type, not just yours.
- `get_religion_spread` — check religious spread across all visible cities. IF any rival religion is majority in 50%+ of civilizations, this is an emergency.
- `get_minimap` — check map shape, territory, fog boundaries

### Every 30 turns:
- `get_strategic_map` — fog boundaries per city + unclaimed resources
- `get_global_settle_advisor` — top settle sites across revealed map
- **Victory reassessment**: Answer these questions explicitly:
  1. What is my city count vs rivals? (visible in `get_diplomacy`)
  2. Is my chosen victory path still mathematically viable?
  3. Is any rival close to winning a victory I'm not tracking?
  4. Should I pivot? (See Victory Kill Criteria below)

## Hard Rules (Mandatory — Not Advisory)

These are rules with specific triggers. Violating them is a bug in your play.

### Civilian Safety Gate
**BEFORE moving any civilian unit (builder, settler, trader):**
1. Call `get_map_area` centered on the destination tile, radius 2
2. IF any hostile unit is within 2 tiles of the path or destination → DO NOT move the civilian
3. Escort with a military unit first, or choose a different path

No exceptions. Civilians have 0 combat strength. A single barbarian warrior will capture them instantly. The cost of losing a builder (5-7 turns of production + 3 improvement charges) always exceeds the cost of one extra turn of caution.

### Gold Spending Triggers
- **IF gold > 500**: You MUST spend down to under 500 before ending the turn. Buy the highest-impact item: builder > tile with luxury > building that skips 5+ turns of production > military unit if threatened.
- **IF gold > 300 AND a city has no production set**: Purchase a builder or building immediately rather than waiting for production.
- **Exception**: Save gold for a specific planned purchase (settler buy, unit upgrade) — but name the purchase and the turn you'll make it. "Saving for later" without a specific plan is hoarding.

### Expansion Triggers
Settlers are the highest-impact production item in the first 100 turns. Each city = districts = compound yield growth.

- **IF turn > 30 AND cities < 2**: Your capital's next production MUST be a Settler.
- **IF turn > 60 AND cities < 3**: Your capital's next production MUST be a Settler.
- **IF turn > 80 AND cities < 4**: Your capital's next production MUST be a Settler. Also consider purchasing one.
- **IF turn > 100 AND cities < 5**: You are critically behind. Evaluate whether geography is the constraint (no settle sites) or production priority (building infrastructure instead of settling).
- Infrastructure (monuments, granaries, campuses) in existing cities can wait. A new city with a monument produces more total output than a granary in an existing city.
- **Loyalty check before settling**: `get_settle_advisor` includes loyalty pressure estimates. Avoid sites with projected negative loyalty unless you have a governor (Victor or Amani) ready to assign immediately. A city that flips to a Free City wastes the settler, the escort, and all the production that went into them.

### Growth Triggers
Population is compound interest — each pop point unlocks a citizen slot that works a tile and generates yields. Stagnant cities fall behind exponentially. `end_turn` now reports STARVING/STAGNANT/SLOW GROWTH warnings automatically.

- **IF any city has food surplus <= 0**: That city is STARVING or STAGNANT. Fix it THIS TURN. Options: build a Farm (builder), build a Granary, send a domestic Trade Route, or reassign citizens away from production toward food.
- **IF any city has turns-to-growth > 15**: That city needs a Farm, Granary, or Trade Route. Add it to the production queue or buy a builder.
- **IF total empire population < turn / 10** (e.g. pop < 5 at T50, pop < 8 at T80): Growth is critically behind. Prioritize food infrastructure across all cities.
- **Never ignore growth warnings in the turn report.** A city at pop 1 for 30 turns produces a fraction of what a pop 4 city does.

### Exploration Triggers
- **IF turn > 15 AND no scout is auto-exploring**: Build or buy a scout and set it to `automate`.
- **IF a scout dies or gets stuck**: Build a replacement immediately. Do not leave exploration to chance.
- **IF turn > 50 AND exploration < 25%**: This is an emergency. Build a second scout. Consider sending a warrior to explore in a different direction.
- **IF turn > 100 AND exploration < 40%**: You are blind. Exploration should be 50%+ by T100. Dedicate 2 units to exploration.
- Scouts are cheap (30 production). The information they reveal (settle sites, barbarian camps, rival positions, resources) is worth 10x their cost.

### Diplomacy Triggers
- **WHEN you meet a new civ**: Send a delegation (25 gold) in the same turn. Do not defer.
- **WHEN a civ becomes FRIENDLY**: Declare friendship immediately. Each friendship = +1 favor/turn.
- **WHEN Writing tech is researched**: Send embassies to all civs with delegations.
- **WHEN Diplomatic Service civic is researched AND friendships are 30+ turns old**: Propose alliances. Research alliances give +science, which compounds.
- **IF favor > 100 AND no World Congress is imminent**: You are stockpiling favor without a plan. Check if alliances or trade deals could convert favor to value.

### Wartime Garrison Rule
**IF at war, every city MUST have at least one military unit garrisoned or within 1 tile.** Do not strip garrisons to escort civilians or reinforce an attack. The cost of losing a city (production, districts, population, territory, era score penalty) always exceeds the benefit of one extra unit on offense.

- Before moving a garrison unit away from a city during wartime, verify another military unit is covering it.
- Settlers and builders can wait — cities cannot be rebuilt.

### Peace Trigger
- **IF at war AND your military strength < enemy's AND you are not actively conquering cities**: Propose peace after the 10-turn cooldown. Wars of attrition against a stronger opponent drain gold, production, and units while the rest of the map pulls ahead.
- **IF at war AND a third civ is pulling ahead in score/science**: Consider peace even if you're winning the war. A pyrrhic victory against one rival while another runs away with science is still a loss.

### Military Readiness (Peacetime)
War doesn't announce itself. If a neighbor has 3x your military, they WILL attack — the AI sees weakness and exploits it. No amount of science or religion compensates for losing half your empire to an invasion you could have deterred.

- **Every 20 turns**: Check rival military strength in `get_diplomacy`. IF any neighbor has 2x+ your military strength AND is not a declared friend/ally, you are in danger.
- **IF military ratio > 3:1 against you**: EMERGENCY. Pause all civilian production. Build military units until ratio drops below 2:1. Walls in border cities. Move units to defensive positions.
- **Minimum peacetime military**: 1 garrison unit per city + 1 mobile unit. Never drop below this. A city without a garrison is an invitation to attack.
- **Upgrade units when techs unlock**: Slingers → Archers (Archery), Warriors → Swordsmen (Iron Working), Archers → Crossbowmen (Machinery). Outdated units are free kills for upgraded enemies.

### Religion Monitoring
Religious victory is the most invisible win condition in the game. It requires zero military, zero wonders, zero space projects — just missionaries converting cities over 100+ turns. It has been the #1 cause of agent defeats. This section is non-negotiable.

- **IF playing a religious civ**: Holy Site must be your first or second district. Shrine immediately after. You MUST compete for a Great Prophet. Failing to found a religion with a religious civ wastes the entire civ kit.
- **IF NOT playing a religious civ**: Still check `get_religion_spread` every 20 turns after T60.
- **IF you have founded a religion**: You MUST maintain at least one city with Holy Site + Shrine where YOUR religion is majority. This is your missionary production city. Without it, you cannot produce religious counter-units. If your holy city flips to a rival religion, flip it back immediately — this is a higher priority than any other production.
- **IF any rival religion is majority in 2+ of N civilizations**: THREAT. Start producing missionaries/apostles NOW. Do not wait until it reaches N-1. Every turn you delay makes the problem exponentially harder to reverse.
- **IF any rival religion is majority in N-1 of N civilizations**: EMERGENCY. You are 1 conversion from losing. Options: declare war on the religious civ (kills missionaries in your territory), buy Inquisitors (requires your own religion), or conquer the religious civ's holy city.
- **CRITICAL: Missionaries match the CITY's majority religion, NOT your founded religion.** If you buy a missionary from a Catholic-majority city, you get a Catholic missionary — working against you. Always buy religious units from a city where YOUR religion is majority. Check `get_religion_spread` before purchasing.
- **Trade routes spread religion.** Each trade route applies religious pressure of the origin city's majority religion to the destination. If your cities have been converted to a rival religion and you run trade routes from them, you are actively spreading the rival religion. Be aware of this when routing trade.

### Victory Kill Criteria
Do not commit to a victory path that is mathematically impossible. Check these:

- **Science**: Requires 4+ cities with Campuses + Universities to generate 80+ sci/turn by T150. IF cities < 4 at T100 and no expansion room, science victory is not viable. Pivot.
- **Domination**: Requires 200+ military strength and proximity to rival capitals. IF you can't reach a rival capital within 10 turns of travel, domination is slow. Consider alternative.
- **Culture**: Requires Theater Squares in most cities + Great Works + Wonders. IF zero Theater Squares at T100, culture is severely behind. Build them or pivot.
- **Religious**: Requires founding a religion. IF no religion by T80, this path is permanently closed.
- **Diplomatic**: Always viable as a backup for small empires. Requires friendships (+favor), alliances (+favor), suzerainties (+favor), and World Congress votes. Start building favor infrastructure from T1 regardless of primary victory path.

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
- Mountains and forests block line of sight for ranged attacks — the tool checks LOS before firing and reports `ERR:NO_LOS` if blocked
- Crossbows (RS:40) deal near-zero damage to Industrial-era units (CS:65+) — don't waste attacks
- City ranged attacks (with walls) are powerful defense — 14-19 damage against Infantry-class units
- Never position ranged units adjacent to melee-capable enemies — they melt in melee combat

### Barbarian Camp Doctrine
Barbarian camps spawn progressively stronger units as the game advances. A camp left alone at T50 spawns warriors; at T150 it spawns Man-at-Arms; at T200 it spawns Line Infantry. **Destroy camps proactively, not reactively.**

- **IF `get_map_area` reveals a barbarian camp within 8 tiles of any city**: Send a military unit to destroy it within 10 turns. Do not wait for it to spawn more units.
- **IF barbarian units are attacking and you don't know where the camp is**: Use `get_map_area` with radius 4 in the direction they came from. Find and destroy the source.
- Fast units (cavalry, heavy chariots) are ideal for camp clearing — they can reach and destroy camps in 2-3 turns.

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
- See Civilian Safety Gate above — this is mandatory, not advisory
- Common improvements: `IMPROVEMENT_FARM`, `IMPROVEMENT_MINE`, `IMPROVEMENT_QUARRY`, `IMPROVEMENT_PLANTATION`, `IMPROVEMENT_PASTURE`, `IMPROVEMENT_CAMP`
- Builders can only improve tiles in YOUR territory (`owned by player 0` in map output)
- **Priority**: Luxury resources first (amenities), then strategic resources (iron, horses, niter), then bonus resources (farms, mines)

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

The tool returns the blocker type and which tool to use to resolve it. `end_turn` also runs a victory proximity scan every turn — pay attention to its warnings.

## Diplomacy

- AI encounters (first meetings, denouncements, agenda complaints) block turn progression
- `end_turn` detects pending diplomacy and tells you to use `respond_to_diplomacy`
- Most AI encounters are informational (1-2 rounds of POSITIVE/NEGATIVE)
- First meetings typically need 2-3 rounds of responses
- The tool auto-closes "goodbye" phases
- **Diplomacy encounters reset ALL unit orders.** After resolving diplomacy, use `skip_remaining_units` to re-fortify/skip idle units

### Proactive Diplomacy (CRITICAL — do from Turn 1)

Diplomacy is a **yield source**, not an interruption. Each friendship = +1 favor/turn. Each alliance = +1 favor/turn + shared visibility + era score. Each suzerainty = +2 favor/turn. Favor compounds. Start building income immediately.

- **Delegations** (25 gold): Send to every civ immediately after meeting. See Diplomacy Triggers above.
- **Friendships**: `send_diplomatic_action(action="DECLARE_FRIENDSHIP")` — returns ACCEPTED/REJECTED. Requires the AI to be Friendly.
- **Open Borders**: `send_diplomatic_action(action="OPEN_BORDERS")` — returns ACCEPTED/REJECTED.
- **Embassies** (requires Writing tech): Gives permanent visibility and favor bonus.
- **Alliances**: Use `form_alliance(other_player_id, alliance_type)`. Requires declared friendship + Diplomatic Service civic. Types: MILITARY, RESEARCH, CULTURAL, ECONOMIC, RELIGIOUS. Alliances level up over time (Lv1→Lv2→Lv3).

### Defensive Pacts

`get_diplomacy` shows `!! DEFENSIVE PACTS with: Kongo (player 3)` when civs have mutual defense agreements. **Always check pacts before declaring war** — attacking one civ may trigger war with their pact partner(s).

### Trade Deals

- `get_trade_options(player_id)` — **call this first** to see what both sides can put on the table (gold, GPT, favor, luxuries, strategics, open borders, alliance eligibility). Like opening the trade screen.
- `propose_trade` — compose and send a trade deal. Supports:
  - Gold/GPT: `offer_gold=100`, `offer_gold_per_turn=5`, `request_gold=200`, `request_gold_per_turn=3`
  - Resources: `offer_resources="RESOURCE_FURS"`, `request_resources="RESOURCE_TEA,RESOURCE_SILK"`
  - Diplomatic favor: `offer_favor=20`, `request_favor=10`
  - Open borders: `offer_open_borders=True`, `request_open_borders=True`
  - Joint war: `joint_war_target=3` (player ID of war target, added to both sides)
  - Returns **ACCEPTED**, **REJECTED**, or **PROPOSED** (async/unclear)
- `get_pending_trades` — check for incoming trade offers from AI
- `respond_to_trade` — accept or reject incoming deals

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

## Production & Research

- Use `get_city_production` to see what's available — shows both production cost and **gold purchase cost**
- Use `get_tech_civics` to see available research options
- Use `purchase_item` to buy units/buildings with gold instantly (shows cost vs balance on failure)

### Opening Build Order (first 40 turns)
1. **Scout** — exploration is the foundation of everything
2. **Slinger** — early defense + upgrade to Archer with Archery tech
3. **Settler** — second city is the highest priority after basic defense
4. **Builder** — improve luxuries for amenities, then strategic resources
5. **Monument** (if not built via civic) — culture for borders and civic progression

### Early Tech Priority
Pottery (granary) → Archery (upgrade slinger) → Mining (mines) → Animal Husbandry (horses/pastures) → Bronze Working (iron reveal)

### Early Civic Priority
Code of Laws (policies) → Foreign Trade (trade routes) → Early Empire (governors + settler policy card)

### Production Priority Framework
When choosing what to produce, follow this priority order:
1. **Settler** (if below city count benchmark AND a settle site is identified)
2. **Military unit** (if under active threat or no garrison)
3. **Builder** (if unimproved luxury/strategic resources exist)
4. **Trader** (if trade route capacity > active routes)
5. **District** (Campus first, then Commercial Hub, then situational)
6. **Buildings** (Library, Market, etc. within completed districts)
7. **Infrastructure** (Granary, Water Mill, Monument)

## City-States & Envoys

- Use `get_city_states` to see known city-states with their types, your envoy counts, and suzerain status
- Use `send_envoy` to send envoy tokens — bonuses at 1/3/6 envoys, suzerain at most envoys (min 3)
- City-state types: Scientific (+science), Industrial (+production), Trade (+gold), Cultural (+culture), Religious (+faith), Militaristic (+units)
- Envoy tokens come from civics (Mysticism, etc.) and are blocking notifications — must assign them
- Suzerainties provide +2 diplomatic favor/turn — target 3+ suzerainties by midgame

## Pantheon & Religion

- Use `get_pantheon_beliefs` to see available pantheon beliefs with descriptions
- Use `choose_pantheon` to found a pantheon once you have 25 faith
- Pantheon is a blocking notification — game won't advance until you pick one
- Good early picks: God of the Forge (+25% military production), Fertility Rites (free builder + 10% growth), Lady of the Reeds (+2 production from marsh/floodplains)
- **IF playing a religious civ**: See Religion Monitoring under Hard Rules. Founding a religion is non-negotiable.
- **Monitor rival religions** via `get_religion_spread` every 20 turns after T60. Religious victory is the most invisible win condition in the game.

## Unit Upgrades

- Use `upgrade_unit` to upgrade a unit (e.g. slinger → archer) — requires the right tech, enough gold, and moves remaining
- Common upgrade paths: Slinger → Archer (needs Archery), Warrior → Swordsman (needs Iron Working + iron), Scout → Ranger
- Upgrading consumes all movement for the turn

## Exploration (NON-NEGOTIABLE)

**Exploration is the foundation of every other strategic decision.** You cannot settle what you cannot see. You cannot counter threats you don't know exist. Exploration generates no notifications — it requires active discipline.

- Build a Scout first. Set it to `automate` immediately.
- IF the scout dies, build another. Always have at least 1 scout auto-exploring.
- Build a second scout by T40-50 if exploration < 20%.
- Use `get_strategic_map` every 30 turns to check fog boundaries per city.
- Use `get_minimap` every 20 turns to see the map shape — coastlines, mountain walls, territory patterns.
- **Explore TOWARD fog boundaries near your cities.** If a city has 5+ unexplored directions, something valuable is likely hiding there.
- Use `get_global_settle_advisor` every 30 turns to find the best settle sites across the entire revealed map.

### Exploration Benchmarks
- T25: 15%+ explored
- T50: 25%+ explored
- T75: 35%+ explored
- T100: 50%+ explored

IF below these benchmarks, exploration is an emergency. See Exploration Triggers above.

## Strategic Benchmarks

By turn 25: Scout auto-exploring, warrior guarding, settle site identified via `get_settle_advisor`
By turn 40: 2 cities, 1 builder, slinger/archer for defense, delegation sent to any met civ
By turn 60: 3 cities, Campus in progress, 1+ trade routes, luxuries being improved, friendships pursued
By turn 80: 3-4 cities, Campus built, 15+ science/turn, Commercial Hub in progress, iron/horses located
By turn 100: 4-5 cities, Campus + Commercial Hub built, 25+ science, 2+ trade routes, alliances forming

**IF behind on city count**: Settlers take absolute priority over everything except immediate defense.
**IF behind on score by 50%+**: Diagnose why. Usually it's city count. Build settlers.

### Strategic Reassessment (every 30 turns starting at T60)

Use `get_victory_progress`, `get_diplomacy`, and `get_religion_spread` to answer:
1. What is my city count vs rivals?
2. Is my chosen victory path still viable? (Check kill criteria above)
3. Is any rival close to winning ANY victory type?
4. Should I pivot?
5. Am I spending my gold/faith or hoarding it?
6. **Am I using my civ's unique kit?** Check: have I built the unique district/building? Have I researched the tech for my unique unit? If not, why not — and is this civ pick being wasted?

**Do not just answer these questions — act on the answers this turn.**

## Midgame Priorities (Turns 50-100)

1. **Expand aggressively.** Settlers first. 4-5 cities by T100. More cities = more districts = more yields = victory. This is the single most important thing you can do.
2. **Districts are the yield engine.** Campus first (science compounds), then Commercial Hub (trade routes + gold). Use `get_district_advisor` for placement.
3. **Trade routes = free yields.** Build a Trader as soon as you have Foreign Trade civic. Domestic routes to new cities for food+production. International for gold. IF capacity > active routes, fix immediately.
4. **Improve luxuries FIRST.** Each luxury = +1 amenity empire-wide. Zero amenities = growth penalty. Use `get_empire_resources` to find unimproved luxuries.
5. **Diplomacy is a yield.** By T75: delegations to all, friendships with FRIENDLY civs, envoys to city-states. By T100: embassies, alliances forming, 3+ suzerainties.
6. **Culture matters.** Build at least 1-2 Theater Squares by T100. Culture unlocks critical civics (Diplomatic Service for alliances, better governments, powerful policy cards). Zero Theater Squares = falling behind on civics permanently.

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
- **See Gold Spending Triggers above.** Gold above 500 must be invested immediately.

## Trade Routes

- Use `get_trade_destinations(unit_id)` to see available destinations for a trader
- Use `unit_action(unit_id, action='trade_route', target_x=X, target_y=Y)` to start a route
- **Domestic routes** send food + production to the destination city (good for new cities)
- **International routes** generate gold for the origin city
- Trader must be in a city with moves remaining
- Route capacity: 1 from Foreign Trade civic, +1 per Market/Lighthouse
- **IF capacity > active routes**: This is free yield being wasted. Build or reassign a Trader immediately.

## Great People

- Use `get_great_people` to see available GP candidates and recruitment progress
- When you recruit a GP, move it to the matching completed district (e.g. Great Scientist → Campus)
- Use `unit_action(unit_id, action='activate')` to activate — unit is consumed
- The district must be **completed** (not just placed) for activation to work
- **Do NOT delete Great People.** They look like "0 charges" because GP charges use a different API than builder charges. If activation fails, move the GP to a different tile or district — don't delete.

## World Congress

World Congress fires as a turn segment during `end_turn()`. The WC session opens and closes synchronously within `ACTION_ENDTURN` — there is no pause for interactive voting. You MUST register your votes BEFORE calling `end_turn()`.

### Voting Flow (CRITICAL)
1. Check `get_world_congress()` — when `turns_until_next` is 0, WC fires this turn
2. Review resolutions: each has options A/B, a target list, and favor costs
3. Call `queue_wc_votes(votes=[...])` to register your vote preferences as an event handler
4. Call `end_turn()` — handler fires during WC processing, deploys your favor, turn advances

`end_turn()` will **block and warn you** if WC is imminent and no handler is registered. This prevents accidentally wasting your favor on default 1-vote-per-resolution.

### `queue_wc_votes` Format
```
queue_wc_votes(votes='[{"hash": -513644209, "option": 1, "target": 0, "votes": 5}]')
```
- `hash`: resolution type hash (from `get_world_congress`)
- `option`: 1 for A, 2 for B
- `target`: 0-based index into the resolution's possible targets list
- `votes`: max votes to allocate (handler uses as many as favor allows)

### Key Points
- Each resolution has two options (A/B) and a target to choose from a list
- 1 free vote per resolution; extras cost increasing diplomatic favor (10/30/60/100/150)
- Between sessions: `get_world_congress` shows passed resolutions and turns until next session
- The `ENDTURN_BLOCKING_WORLD_CONGRESS_LOOK` blocker (review results) is auto-resolved by `end_turn`
- **Vote for Diplomatic Victory Points when available.** This is the primary use of accumulated favor.
- **Deploy ALL your diplomatic favor** on key resolutions — hoarded favor is wasted favor.

## Victory Conditions

Use `get_victory_progress` every 20 turns to track the race. There are 6 victory types:

| Victory | Condition | Key Metric |
|---------|-----------|------------|
| **Science** | Complete 4 space projects (satellite, moon, Mars, exoplanet) | Science VP (0/50) |
| **Domination** | Own every other civ's original capital | Capitals controlled |
| **Culture** | Your foreign tourists > every civ's domestic tourists | Tourism vs staycationers |
| **Religious** | Your religion is majority in all civilizations | Cities converted |
| **Diplomatic** | Earn 20 diplomatic victory points | Diplo VP from World Congress |
| **Score** | Highest score at turn 500 | Total score |

**Strategic awareness:**
- Science: Requires 4+ cities with full Campus chains. Need Rocketry → Spaceport → 4 projects (~15 turns each). IF < 4 cities at T100, science is not viable.
- Domination: Watch military strength — a civ with 300+ military and your neighbor is a threat. Losing your capital = game over.
- Culture: Theater Squares + Great Works + Wonders + National Parks drive tourism. IF zero Theater Squares at T100, culture victory is closed.
- Religion: Must have FOUNDED a religion (not just a pantheon). IF no religion by T80, this path is permanently closed. Monitor rival religions — religious victory is invisible without active checking.
- Diplomatic: Always viable as a backup. Favor from friendships, alliances, suzerainties. Spend in World Congress for VP. **Start building favor income from T1 regardless of primary victory path.**
- Score: Fallback — whoever is ahead at turn 500 wins.

**`get_victory_progress` includes:**
- Per-civ rival intelligence: city count, science/culture/gold yields, military strength
- Victory assessment: 0-100% viability score per path with recommended strategy
- Use this to decide when to pivot strategies

**`end_turn` includes a victory proximity alert** that fires warnings when any rival is close to winning. Pay attention to these — they are your last line of defense against invisible victories.

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

- `lua/` — Package of Lua code builders (`build_*`) and response parsers (`parse_*`), split by domain: `overview`, `units`, `cities`, `map`, `tech`, `diplomacy`, `governance`, `religion`, `economy`, `victory`, `notifications`. Shared helpers in `_helpers.py`, all dataclasses in `models.py`. Re-exported via `__init__.py` so `from civ_mcp import lua as lq` works.
- `game_state.py` — `GameState` class. High-level async methods that call `lua` builders, execute via `connection`, and parse responses. Query + action methods only.
- `narrate.py` — All `narrate_*` functions (pure transforms from data → human-readable strings). Extracted from GameState.
- `end_turn.py` — End-turn state machine (`execute_end_turn`): blocker resolution, turn advancement, post-turn snapshot/diff.
- `game_lifecycle.py` — Infrastructure: `dismiss_popup`, `quicksave`, `list_saves`, `load_save`, `execute_lua`.
- `diary.py` — Per-turn diary read/write (JSONL format).
- `server.py` — MCP tool definitions. Calls `GameState` methods + `narrate` functions.
- `game_launcher.py` — Game lifecycle management (kill/launch/OCR save loading). Standalone module with no FireTuner dependency.
- `connection.py` — Low-level TCP connection to FireTuner. Handles sentinel parsing.

## Project Conventions

- Use `uv` for Python package management
- Track progress in `DEVLOG.md`
