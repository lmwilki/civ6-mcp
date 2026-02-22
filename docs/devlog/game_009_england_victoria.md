# Game 9 — England (Victoria) — Post-Mortem

**Civ**: England (Victoria, Age of Empire) | **Result**: Conceded T135 (irrecoverable deficit) | **Map**: Standard, 6+ players

---

## Part 1: Timeline

### Key Milestones

| Turn | Event |
|------|-------|
| T1   | London founded |
| T~30 | Scout built; first contact with Brussels (Industrial CS) and Vatican City (Religious CS) |
| T~50 | First contact with Ottomans (Suleiman) |
| T~70 | Barbarian waves begin — camp location unknown |
| T85  | London Campus placed. Era score 9/14. Barb Warrior at (7,40), Barb Scout at (12,41) |
| T86  | Warrior kills barb at (7,40). Camp still unfound. |
| T87–T94 | **10-turn camp search going EAST** — camp was actually NORTHWEST at (3,43) |
| T95  | Camp finally confirmed at (3,43) via Lua test query. Barb camp visibility tool bug identified and fixed. |
| T95–T107 | Camp clearing operation: Spearman CS:34 fortified on hills; multiple failed/misrouted attacks |
| T108 | Camp captured! Era score jumps to 15. Normal Age secured by 1 point. |
| T110 | London Settler complete — 3rd city Settler dispatched |
| T112 | Sheffield founded at (7,39) — **17 turns behind T100 benchmark** |
| T115 | 3 cities: London pop 8, Manchester pop 6, Sheffield pop 1. Science 23.9 vs Ottoman 45 |
| T117 | Medieval Era begins. Diamond territory revealed south of Vatican City |
| T121 | London begins Settler for 4th city (24 turns) |
| T123 | Mathematics complete. Apprenticeship started (15t). Southern polar ice confirmed — no resources |
| T127 | Sheffield Monument complete → Granary queued. Manchester at -2 amenity deficit |
| T130 | T130 snapshot: Rank 6/6 in population, soldiers, land, crop yield, goods. Science 25 vs Ottoman 58. |
| T131 | Jade trade with Ottomans (5 GPT). Manchester amenities fixed at 3 |
| T134 | Apprenticeship complete. Education started (15t). Victor appointed for future 4th city |
| T135 | **Conceded** — unrecoverable deficit |

### Score Progression

| Turn | England | Ottomans |
|------|---------|----------|
| T85  | 79      | ~150     |
| T100 | 97      | ~200     |
| T115 | 116     | 223      |
| T130 | 131     | 296      |
| T135 | 131     | ~310     |

Ottomans held 2.5–3x lead in score throughout. The gap was never closing.

---

## Part 2: What Went Wrong — Root Causes

### Failure 1: The Barbarian Camp (Primary Cascade Failure)

**This is the game's central failure. Everything else flows from it.**

From approximately T70, barbarian units were spawning from a camp at **(3,43)** — north of London. The camp generated Swordsmen (CS:35) and Spearmen (CS:34) that threatened London's development corridor and consumed all available military attention for 40+ turns.

**The specific failures:**

**1a. Camp not detected for ~25 turns.**
The camp at (3,43) was revealed but not visible (in fog of war). The `get_map_area` tool only queried `GetImprovementType()` inside the `if visible then` Lua block, so barbarian camp improvements on revealed-but-not-visible tiles were completely invisible. The camp never appeared in any map query. It was discovered at T95 only by running a direct Lua test query — 25 turns after the first barb units appeared.

**1b. Search sent east when camp was northwest.**
When the camp was first suspected, the eastern Warrior was moved northeast — away from London, toward the Ottoman border. The barb Scout had been spotted at (12,41), which anchored my assumption that the camp was east. In reality the spawned barbs were just patrolling after moving far from their origin. Ten turns of Warrior movement in entirely the wrong direction.

The correct play would have been to immediately call `get_map_area` in concentric rings around London to find the source. Instead I relied on where I'd seen barbs roam.

**1c. Camp terrain extremely defensive.**
When the camp was finally found (T95), the defender was a Spearman on hills with fortification bonus — CS:34 effective. A Warrior (CS:20) couldn't engage it directly. Getting the Archer into fire position took another 12 turns due to ZoC issues, terrain pathfinding costs, and a 0-damage display bug that caused repeated uncertainty about whether attacks were landing.

**Net cost of the barbarian camp:**
- 40+ turns of primary military focus
- 3rd city delayed from ~T80 to T112 (Settler production couldn't start until the threat was managed)
- Era score nearly reaching Dark Age threshold — scraped through at 15/14 minimum
- Eastern Warrior wasted 10 turns going the wrong direction
- Archer exposed and damaged during the clearance operation

**Tool fix applied this game:** Improvements now queried for all *revealed* tiles, not just visible ones. Future camps will appear in map data immediately.

**What should have happened:** On first barb sighting (~T70), immediately spiral-scan with `get_map_area` radius 3 around each barb unit position to locate the camp. The camp was only 6 tiles from London — it would have appeared within 2-3 queries. Then: fortify London Warrior as garrison, purchase a second military unit immediately with the gold on hand (~200+g available), and assault the camp before it could spawn another wave.

---

### Failure 2: Expansion Catastrophically Slow

By the T100 benchmark, the game expected 4 cities underway. We had 2.

| Benchmark | Target | Actual |
|-----------|--------|--------|
| T40: 2nd city underway | T40 | ~T40 (on time) |
| T60: 3 cities | T60 | 2 cities |
| T80: 4 cities | T80 | 2 cities |
| T100: 4-5 cities | T100 | 2 cities |
| T112: 3 cities | T112 | 3 cities (12 turns late) |
| T135 (concession): 4 cities | ~T145 | never founded |

The root cause was the barbarian camp consuming all Warrior attention, making it unsafe to move a Settler across the map. But there were compounding failures:

- London was producing a Settler when the camp crisis hit, and the Settler was delayed while military was redirected
- After the camp was cleared (T108), 3rd city was founded at (7,39) — a fine location, but then London immediately started building **Walls** (11 turns) before the next Settler. That was 11 turns before 4th city production could even start
- The 4th city Settler wasn't queued until T121 with a 24-turn build time — meaning 4th city would have arrived at T145+ if the game continued

With 6 rival civs on a standard map and Ottomans already at 6 cities by T130, having 3 cities at concession was a structural defeat. Each missing city was a missing Campus, a missing Library, missing trade route income, and missing Great People generation.

---

### Failure 3: No Iron — Military Permanently Stuck in Ancient Era

No Iron was found in England's territory at any point. Searches covered east (Ottoman territory), south (polar ice), and west (auto-scout). The empire had Warriors (CS:20) and 1 Archer (RS:25) throughout the entire game while Brussels city-state units were fielding Man-at-Arms (CS:45) and Crossbowmen (RS:40) by T126.

This wasn't a recoverable failure — without Iron, Swordsmen (the primary military upgrade path) were unavailable regardless of tech. But the failure to *discover* this resource gap early enough to seek Iron through trade or aggressive scouting compounded the problem. The Ottoman trade option at T120 (Open Borders for Horses) was correctly rejected as too dangerous, but no alternative Iron-access plan was formed.

---

### Failure 4: London's Housing Cap Never Solved

London hit the housing cap (pop 8 / housing 8) and stayed there from approximately T100 to concession. At the housing cap, growth drops to 25% of normal rate — effectively 1.5 food/turn net instead of 6. London gained barely 3 population in ~35 turns.

The tooling correctly flagged this as an issue. The actual problem was architectural: no Aqueduct, Harbor, Royal Navy Dockyard, or Granary placement was valid for London due to terrain. This was identified but never solved. The correct response would have been to investigate tile positions more carefully — the Royal Navy Dockyard (Victoria's unique district, gives +2 housing) might have had valid placement on a coastal tile adjacent to London that wasn't surfaced by the district advisor.

This froze London's yields and Great People generation at T100 levels for the remainder of the game.

---

### Failure 5: Science Path Started Too Late

| Tech Milestone | Actual Turn |
|----------------|-------------|
| Campus (London)   | ~T80 |
| Campus (Manchester) | T124 |
| Library (Manchester) | ~T136 |
| Education tech    | T135+ (never completed) |
| University        | never |

Universities — the core science multiplier for science victory — were never built. The tech path was: Apprenticeship → Mathematics (required both) → Education → University. This chain wasn't begun in earnest until T123 (Apprenticeship), with Education starting only at T135 when the game was conceded.

With Ottoman science at 58/turn vs England at 25/turn, the gap required not just catching up but overtaking. That required Universities, Campuses in every city, and research agreements. None of these were achievable on the trajectory we were on.

The pivot to science victory was correct based on the T100 recommendation (60% viable). But the infrastructure to execute it — 4+ cities with Campuses, Libraries, and Universities generating 80+ science by T150 — simply wasn't in place. A science victory requires building the science stack from T40 onward. We started building it at T80.

---

## Part 3: What Went Well

### Era Score Management
Starting the Classical era at 9/14 and ending at 16 was genuinely hard. The camp capture (+3 era score at T108) combined with the trade route (+1) and 3rd city founding (+1) threading through multiple tense turns. The Barbarian camp fix actually enabled this — it was unclickable in the tool until the bug was discovered. The Free Inquiry dedication in the Medieval era was the right call: science buildings and Eurekas both generate era score, perfectly matching the science victory path.

### Diplomatic Adaptability
Correctly rejected the Ottoman Open Borders deal at T120 (Unfriendly + 2.5x military strength = too dangerous). When Ottomans turned Friendly at T130, pivoted immediately to trade diplomacy — Jade trade for 5 GPT resolved Manchester's amenity crisis within 1 turn. This was the right read: take deals that don't create military exposure, extract luxuries and resources when the relationship allows.

### Pingala + Grants
Appointing Pingala to London and promoting with Grants was the right call. Double Great Person points in London accelerated the Great Scientist pipeline (129/310 points at T130). Had the game continued, a Great Scientist would have triggered Education's Eureka — a significant science boost that was deliberately set up.

### Barbarian Camp Visibility Fix
Identifying the tool bug and fixing it mid-game was the most valuable technical work of this session. The fix (moving `GetImprovementType()` outside the `if visible then` block) is permanent and will prevent this class of failure in future games.

### Owner Name Enrichment
Completed the plan to display `"owned by Vatican City [City-State]"` instead of `"owned by player 13"` in map output. Small change but eliminates confusion about whether a border is a city-state vs major civ.

---

## Part 4: Tool Gap Analysis

### Gap 1: No Barbarian Camp Proximity Alert

**Problem**: A barbarian camp 6 tiles from London spawned Swordsmen for 40+ turns without appearing in any tool output.

**Root cause**: Fixed this game — improvements now visible on revealed tiles, not just visible ones.

**Remaining gap**: Even with the fix, the camp was never explicitly flagged as a threat. `end_turn` threat scan detects barbarian *units* but not the *camp* itself. A camp within 8 tiles of any city should generate a `!! BARB CAMP: BARBARIAN_CAMP at (X,Y) — N tiles from [City]` warning in the end_turn report.

**Proposed fix**: In the end_turn threat scan Lua query, check all revealed plots for `IMPROVEMENT_BARBARIAN_CAMP` and emit a warning if within 10 tiles of any owned city.

---

### Gap 2: Map Query Routing — No Spiral Search Helper

**Problem**: When barbarian camp location was unknown, systematic search required manually calling `get_map_area` at different centers. With no helper, the agent relied on where barbs were *seen* (which could be far from their origin camp after several turns of movement).

**Proposed fix**: Camps can be found by checking the `plot:GetOwner() == 63` (Barbarian owner) combined with the improvement fix. Alternatively, a simple strategic note: **whenever a barbarian unit is spotted, call `get_map_area` centered on it at radius 3 to look for the camp immediately.** Camps rarely spawn units that travel more than 5 tiles in the first few turns.

---

### Gap 3: Housing Cap Not Flagged as Growth-Blocking

**Problem**: London's "SLOW GROWTH: 40 turns to next pop" warning appeared every turn but didn't distinguish between *slow growth from food deficit* vs *slow growth from housing cap*. Both appear identical in the output.

**Proposed fix**: In city narration, when `pop >= housing`, add `!! HOUSING CAP: Pop equals housing — growth throttled to 25%. Fix: Aqueduct, Granary, or Harbor.` The current warning says "needs farm, granary, or trade route" which is misleading when the actual problem is the housing ceiling, not food supply.

---

### Gap 4: No Resource Gap Warning

**Problem**: Iron and Horses were absent from England's empire throughout the entire game. This was visible in `get_empire_resources` but was never automatically surfaced as a military readiness problem.

**Proposed fix**: In `end_turn`, if any strategic resource used by available units is at 0 and the player's era is Classical or later, emit: `!! STRATEGIC RESOURCE GAP: No Iron — Swordsmen unavailable. Check empire resources and consider trade.`

---

### Gap 5: Barbarian Wave Identification

**Problem**: When barbarians appeared near London, there was no signal distinguishing "barb unit wandering from a distant camp" vs "barb unit from a camp 5 tiles away." The wandering barb near (12,41) anchored the wrong belief that the camp was east.

**Proposed fix**: When a barbarian unit is first detected as a threat, immediately call `get_map_area` at radius 3 centered on that unit to look for the camp tile. If `BARBARIAN_CAMP` appears, emit its location immediately. This is now technically possible with the improvement visibility fix.

---

## Part 5: Strategic Lessons for Future Games

### Lesson 1: Barbarian Camp = Immediate Full Response

The moment a barbarian unit is spotted, treat the camp as a 3-turn emergency:
1. Call `get_map_area` radius 3 centered on the barb to find the camp
2. If not visible, spiral outward until found
3. Purchase a second military unit immediately (don't wait for production)
4. Move to destroy the camp before it spawns another wave

Every turn the camp survives spawns more units and compounds the problem. The cost of a 160g Warrior purchase to deal with a camp immediately is trivial compared to 40 turns of disrupted development.

### Lesson 2: Expansion Comes Before Everything Else

At T80, England had 2 cities. The CLAUDE.md benchmark says 4 cities by T80. The gap was 2 full cities — an enormous deficit that was never recovered.

Each missing city at T80 translates to:
- 1 missing Campus (source of all science)
- 1 missing trade route (gold/food)
- 2-4 fewer population (all yields)
- Fewer Great People points

The rule should be: if behind on city count benchmarks, a Settler is more important than almost any other production decision, including defensive units, unless there is an active military threat.

### Lesson 3: Identify the Unique Unit's Prerequisites and Build Around It

Victoria's unique district is the Royal Navy Dockyard (Harbor replacement, gives +2 housing, +1 gold, extra trade routes). England's naval identity requires coastal city placement — cities adjacent to coast where the Dockyard can be placed. London's landlocked coastal position (city center not adjacent to water) meant Victoria's primary unique advantage was unavailable for the entire game.

When playing a naval civ, verify that the capital and at least 1-2 cities can actually build the unique district before committing to those city sites.

### Lesson 4: Science Victory Requires Science Infrastructure from Turn 1

A science victory needs Universities in 4+ cities generating 80+ science by ~T150. The path is:
- Campus built by T60-70 per city
- Library immediately after Campus
- Education tech by T100
- University immediately after Education

This game had London's Campus around T80, Manchester's Campus at T124, Education tech started at T135. That's 50-70 turns behind schedule in every metric. Science victory was theoretically the right path, but the infrastructure simply wasn't there.

### Lesson 5: District Housing Math Matters

When London hit the housing cap at pop 8, it effectively stopped growing. The housing formula in Civ 6 means pop = housing = growth rate collapses to 25%. This is severe and immediate. Diagnosing it as "needs granary or trade route" is wrong — granary was either already built or unavailable. The correct diagnosis was "needs a new district that provides +2 housing" — Aqueduct, Harbor, or Royal Navy Dockyard. Identifying this at T85 instead of T115 would have changed the city's trajectory significantly.

### Lesson 6: Scout West Earlier

Our only contact was with Ottomans (east) and city-states (surrounding area). Two-thirds of the map was unexplored at concession. The automated Scout eventually found polar ice to the south, but the western continent (where Iron might have existed, where other civs might have been reachable for trade and alliance) was never explored. A dedicated exploration path west by T60-70 would have opened diplomatic options and potentially found Iron.

---

## Part 6: Summary Table

| Category | Grade | Notes |
|----------|-------|-------|
| Opening expansion | D | 2 cities at T80 vs benchmark of 4 |
| Barbarian response | F | 40-turn delay from camp 6 tiles away |
| Science infrastructure | D | Education tech never completed |
| Diplomacy | B | Correctly handled Ottoman relationship, Jade trade good |
| Era score management | C | Survived Normal Age by 1 point — too close |
| Military | D | No Iron, no medieval units, 3x weaker than Ottomans |
| Unique civ usage | F | Victoria's naval identity was entirely unused |
| Tool adaptation | A | Found and fixed barb camp visibility bug mid-game |

**Overall assessment**: The game was likely unwinnable from approximately T90, when the combination of 2-city expansion, no military upgrades, and a 25-turn barbarian camp stalemate had compounded into a structural deficit. The correct concession point was probably T110 — once Sheffield was founded and the science gap (45 vs 23) was visible, the trajectory was clear. Continuing to T135 confirmed the diagnosis but didn't change it.

---

## Part 7: Tooling Improvements Made This Game

| Change | File | Description |
|--------|------|-------------|
| Barb camp visibility | `src/civ_mcp/lua/map.py` | `GetImprovementType()` now runs on all revealed tiles, not just visible ones |
| Owner name resolution | `src/civ_mcp/lua/map.py`, `models.py`, `narrate.py` | Tile ownership shows `"owned by Vatican City [City-State]"` not `"owned by player 13"` |

### Tooling Improvements Recommended (Next Game)

| # | Change | Priority | Description |
|---|--------|----------|-------------|
| 1 | Barb camp proximity alert in `end_turn` | P0 | Warn when `BARBARIAN_CAMP` is within 10 tiles of any owned city |
| 2 | Housing cap vs food deficit distinction | P1 | When `pop >= housing`, flag as housing cap, not food deficit |
| 3 | Strategic resource gap warning | P1 | Alert when Iron/Horses/etc. at 0 in Classical+ era |
| 4 | Spiral-search tip for unknown camp location | P2 | CLAUDE.md note: always `get_map_area` around each spotted barb unit |
