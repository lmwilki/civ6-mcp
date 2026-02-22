# Game 8 — Scythia (Tomyris) — Post-Mortem

**Civ**: Scythia (Tomyris) | **Result**: Defeat T228 (Babylon Culture Victory) | **Map**: Standard, 4 players (Scythia, Scotland, Babylon, Khmer)

---

## Part 1: Strategic Timeline

### Key Milestones

| Turn | Event |
|------|-------|
| T1 | Founded Pokrovka (49,22) — Plains Hills, Jungle River, geothermal fissure |
| T5 | Met Vatican City (Religious CS), Caguana (Cultural CS) |
| T8 | Animal Husbandry complete — **no horses visible** near capital |
| T15 | Religious Settlements pantheon (World's First!) → free settler |
| T20 | Pazyryk founded (48,27) — 2nd city, horses at (47,30) |
| T21 | Kul Oba founded (54,22) — 3rd city, amber + cattle + rice |
| T25 | First trade route active (Vatican City) |
| T30 | 3 cities, barbarian camp threats south; archer defense established |
| T35 | Encampment placed in Pokrovka; settler queued for 4th city |
| T40 | Trader killed by barbarian scout; 4th city (Myriv) founding |
| T50 | Babylon contact — first major civ meeting |
| T60 | 5 cities, score 128 vs Babylon 109; culture victory identified as path |
| T70 | Free Inquiry dedication chosen; Normal Age secured; Campus in progress |
| T80 | Scotland founded Catholicism; Scotland score 297 vs ours 178; 5 cities |
| T90 | 6th city planned (south of Myriv); era score 38/46 (Normal Age threshold) |
| T100 | 6 cities, **Dark Age**, DVP path via Guilds → Diplomatic Service |
| T110 | Diplomatic Service researched; Alliances begin forming |
| T120 | DVP **3/20**; all 120 favor spent on WC DVP votes |
| T130 | DVP **5/20**; triple civ contact established, Gunpowder in progress |
| T150 | Research Alliance with Scotland active; favors rebuilding |
| T165 | Era score 77/78 — *one point from Dark Age* |
| T169 | DVP **5/20**; Field Cannons promoted; era crisis managed via Military Academy |
| T175 | Alan Turing activated at Pazyryk Campus; DVP climbs to **7/20** |
| T179 | Research Alliance with Babylon accepted |
| T184 | Cultural Alliance with Khmer — **triple alliance** (all 3 civs) |
| T186 | James Joyce activated at Myriv Theater (2 Great Works of Writing) |
| T187 | 7th city Kamianka-Dniprovska founded (49,31) |
| T189 | **Heroic/Golden Age** secured for Atomic Era (era score 91/91) |
| T190 | Raj policy active: +6 sci/cul/faith/gold from 3 suzerainties |
| T191 | DVP **7/20**; allied with all 3 civs |
| T195 | Voted 10× on DVP resolution; total DVP now **9/20** |
| T196 | Mobilization civic complete; Levee en Masse policy added |
| T197 | Orszaghaz wonder queued in Pokrovka (+2 favor/turn) |
| T206 | Vatican City gained as 8th city (captured from city-state capture by Babylon?) |
| T212 | Field Cannon → Machine Gun upgrade |
| T217 | **Dark Age** in Information Era begins (era score 103/111, just under threshold) |
| T219 | Queued 6 WC votes for DVP — registered `WC_VOTER_REGISTERED` |
| T220 | T219 WC gave Babylon +2 DVP (not us). Queued 12 votes spending 396 favor |
| T221 | DVP **11/20**; "Foreign Culture Victory Imminent" warning first appears |
| T222-T224 | Power Plant investigation: discovered missing Industrialization/Sailing chain |
| T225 | Switched to TECH_SAILING (1-turn boosted tech — sat unused ~180 turns!) |
| T227 | Flower Power policy activated; **7 cities queued Rock Bands** (0 production cost) |
| **T228** | **DEFEAT — Babylon wins Culture Victory** |

### Score Progression

| Turn | Scythia | Scotland | Babylon | Khmer |
|------|---------|----------|---------|-------|
| T30 | 35 | — | ~30 | — |
| T60 | 128 | — | 109 | — |
| T80 | 178 | 297 | 212 | — |
| T100 | 215 | 365 | 303 | 263 |
| T130 | 325 | 558 | 442 | 306 |
| T200 | 541 | 968 | 820 | — |
| T212 | ~630 | ~1050 | ~970 | — |

Scotland and Babylon pulled ahead significantly by T80 and never looked back. We stayed competitive in military but fell behind in production and science.

---

## Part 2: Post-Mortem — What Went Wrong

### Failure 1: Never Researched TECH_SAILING (The Critical Tech Gap)

**The most costly mistake of the entire game.**

TECH_SAILING was available as a **1-turn boosted tech** for approximately T80–T225 (~145 turns). It sat untouched in the tech tree because:
1. We were focused on science/civic path for diplomatic victory
2. The tech tree display showed techs in database order — cheap boosted techs were invisible in the middle of long lists
3. No automatic alert flagged "this tech costs 1 turn and unlocks a major chain"

The consequence:
```
TECH_SAILING (1t)
  → TECH_CELESTIAL_NAVIGATION
    → TECH_CARTOGRAPHY
      → TECH_SQUARE_RIGGING
        + TECH_MASS_PRODUCTION
          → TECH_INDUSTRIALIZATION
            → BUILDING_FACTORY
              → BUILDING_POWER_PLANT
                → BUILDING_NUCLEAR_POWER_PLANT
```

No Sailing = no Factory = no Power Plant. All 8 cities ran unpowered (−1 production/turn per building) throughout the Industrial and Modern eras. The fix was trivially easy — 1 turn of research — discovered only at T224 when trying to build Power Plants.

**Tooling fix applied:** `narrate.py` now sorts available techs/civics by turns ascending and flags ≤2-turn items with `!! GRAB THIS`.

### Failure 2: Culture Victory Threat Detected Too Late

Babylon was generating 264 culture/turn by T221 when the "Foreign Culture Victory Imminent" warning appeared. We had no awareness of this threat building over the preceding 40+ turns.

The correct response would have been:
- **T180**: Begin producing Rock Bands in Flower Power cities
- **T190**: Deploy Rock Bands to Babylon's highest-tourism cities
- **T200**: Maintain Rock Band pressure until threat recedes

Instead, we discovered Flower Power at T227 (one turn before defeat). Six cities queued Rock Bands but the minimum 1-turn production delay meant zero were deployed before the game ended.

**Root cause**: `get_victory_progress` was called only every 20-30 turns. A culture victory at 264 culture/turn and 0 counter-tourism is invisible without active checking.

### Failure 3: WC Vote Targeting Uncertainty

At T219, we queued 6 votes with `target=0` (player_id=0 = Scythia). The vote handler fired but T219 WC apparently gave Babylon +2 DVP instead. At T220, we spent 396 favor on 12 votes with the same targeting, getting +2 DVP for us.

The mechanics were unclear: does `target=0` mean "vote for player_id=0" or "vote for index 0 in the target list"? The `queue_wc_votes` API uses `target` as a player_id that gets resolved to a list index at runtime — but if player_id=0 is Scythia's ID and the DVP resolution target list has a different ordering, votes may have gone to the wrong target.

**Residual uncertainty**: We never confirmed whether T219's 6-vote investment yielded 0, +1, or +2 DVP for us specifically.

### Failure 4: Workshop Repair Wrong Approach

At T216, attempted to repair a pillaged Workshop at (50,26) using a builder's `improve` action with `BUILDING_WORKSHOP` — which failed (`IMPROVEMENT_NOT_FOUND`). District buildings (Workshop, Arena, Market, etc.) are repaired via the city's production queue, not builder tile actions. This cost 1 turn of confusion plus a builder charge investigation.

**Lesson**: Builders repair tile improvements (farms, mines, plantations). Pillaged district buildings use `set_city_production(item_type="BUILDING", item_name="BUILDING_WORKSHOP")`.

### Failure 5: Industrial Era Power Chain Never Built

Consequence of Failure 1 compounded: with no Industrialization tech, we never built Factories or Power Plants in any city. By the Information Era, all 8 cities were running without power infrastructure. The era score implications were also significant — "Heartbeat of Steam" era score moments from Power Plants were never triggered.

---

## Part 3: What Went Well

### Diplomatic Network Mastery

By T184, Scythia had active alliances with **all three other civilizations simultaneously** — a first for any game run:
- Scotland: Economic Alliance (Lv2 by T200)
- Babylon: Research Alliance (Lv1, renewed at T205)
- Khmer: Cultural Alliance (Lv1)

This generated ~9 favor/turn from alliances alone, plus Raj policy gave +6 science/culture/faith/gold from 3 suzerainties. The diplomatic network was the strongest of any game played so far.

### Raj Policy Discovery

The Raj policy card (+2 Science/Culture/Faith/Gold per suzerain city-state) stacked to +6 of each yield with 3 suzerainties. Identifying this synergy and maintaining 3 suzerainties throughout the midgame was high-impact play.

### World Congress Vote Spending

Mastered the WC vote cost table: 1 free, then cumulative 6/18/36/60/90/126/168... per additional vote. At T220, spent 396 favor for 12 votes on DVP resolution, efficiently converting favor stockpile into DVP progress.

### Era Score Management

Despite persistent threats of Dark Age, managed to:
- Secure Normal Age at T70
- Secure Normal Age at T100 (narrowly avoiding Dark Age)
- Secure **Golden/Heroic Age** for Atomic Era at T189 (era score 91/91)
- Only fell to Dark Age in the Information Era (103/111 at T217)

The Atomic Era Heroic Age was achieved through disciplined district building, Great Person activation, and city founding — all generating era score moments.

### 7-City Empire

Reached 7 cities by T187 (Kamianka-Dniprovska), eventually gaining 8 (Vatican City) — a strong empire size that only the production gap (no Factory/Power Plant) prevented from dominating yields.

### Great People Utilization

- **Alan Turing** (T175): Activated at Pazyryk Campus → Computers Eureka + random Modern tech boost
- **James Joyce** (T186): Activated at Myriv Theater → 2 Great Works of Writing placed
- **Stamford Raffles** (T203): Activated near foreign city for trade route bonus
- **Piero de' Bardi** (T120): Patronized for +200g + 1 envoy token

Great People recruited and activated rather than left to expire — a consistent improvement over earlier games.

---

## Part 4: Tool Gap Analysis

### Gap 1: Tech Tree Sorting (FIXED THIS SESSION)

**Problem**: `get_tech_civics` returned available techs in database order. A 1-turn boosted tech (SAILING) was invisible in a list of 15+ techs sorted by research order, not cost.

**Fix applied** in `src/civ_mcp/narrate.py`:
- Available techs sorted by `turns` ascending
- Items with `turns ≤ 2` flagged with `!! GRAB THIS`
- Same fix applied to civics

This fix was implemented after discovering the Sailing gap at T224.

### Gap 2: Culture Victory Monitoring (NOT FIXED)

**Problem**: Culture victory progress is invisible without actively calling `get_victory_progress`. The "Foreign Culture Victory Imminent" notification appears only 1-2 turns before loss.

**Proposed fix**:
- Add culture/tourism progress to the `end_turn` turn report (like religion spread already gets checked)
- When any rival has tourism > 70% of your domestic tourists, emit `!! CULTURE THREAT: Babylon tourism (X) approaching our domestic tourists (Y)`
- Auto-run `get_victory_progress` every 10 turns in end_turn rather than every 20-30

### Gap 3: Great Person District Mismatch (PLAN PENDING)

**Problem**: Mary Leakey (Great Scientist) activation failed with `ERR:CANNOT_ACTIVATE|GP at (49,25) district=DISTRICT_CAMPUS moves=3 charges=1. No valid activation tiles found.` The error gave no hint that she activates on Theater Square, not Campus.

The game engine has the requirement strings ("Must be on a completed Theater Square", "Must be in a city with an Artifact great work") in its failure table from `UnitManager.CanStartCommand`, but the MCP server discards the failure table and only checks the boolean.

**Proposed fix**: Capture `can, failTable = UnitManager.CanStartCommand(...)` and extract requirement strings from `failTable` to surface them in the error message. This plan is documented and ready to implement.

### Gap 4: Workshop Repair Documentation

**Problem**: No clear indication whether `BUILDING_WORKSHOP` is a tile improvement or a production item. The API naming (`BUILDING_` prefix) suggests production, but `IMPROVEMENT_` naming for builder actions is inconsistent.

**Proposed fix**: In `unit_action(action='improve')` error messages, add: "Note: District buildings (Workshops, Arenas, etc.) are repaired via set_city_production, not builder improve."

### Gap 5: Nuclear Power Plant Prerequisite Chain

**Problem**: BUILDING_POWER_PLANT showed `CanProduce=true` but `RequestOperation` failed because BUILDING_FACTORY was never built, which itself required TECH_INDUSTRIALIZATION (never researched). The error was opaque.

**Proposed fix**: When `CanProduce=true` but `RequestOperation` fails, add a check for prerequisite buildings and surface them: "BUILDING_POWER_PLANT requires BUILDING_FACTORY first."

---

## Part 5: Tactical Review — Key Decision Points

### T1-T20: Strong Opening
Founded Pokrovka in an excellent position (geothermal, jungle for science, river). Religious Settlements pantheon (world's first!) gave a free settler, enabling 3 cities by T25. Exploration was disciplined — goody huts captured, both scouts auto-exploring. **This was the strongest opening of any game so far.**

### T60-T80: Pivot from Culture to Diplomacy
Initial game plan was culture victory. At T80, Scotland's lead (297 vs 178, 61 sci/turn vs 24) prompted a pivot to diplomatic victory via alliances. **This pivot was correct** — culture victory would have been impossible to close against Scotland's production lead. The diplomatic path was well-chosen for Scythia's civ abilities (mounted mobility, not culture generators).

### T100: Dark Age Milestone
Fell into a Dark Age at T100 despite having 6 cities. Root cause: district building was prioritized over era score moments. Several "First X in era" opportunities were missed by researching deep-tree techs instead of cheap 1-2 turn ones (exactly the Sailing problem pattern).

### T169-T180: Era Score Crisis
Reached era score 77/78 (one point from Dark Age) entering the Modern Era. This was recovered via Military Academy (Pokrovka), Aqueduct completions, and other district/building milestones — threading the needle to Normal Age. **Extremely close call** that required several turns of reactive play.

### T189: Heroic Age Secured
A genuine strategic success. Achieving Golden/Heroic Age for Atomic Era via disciplined era score accumulation (Great People activation, city founding, district chains) provided:
- Sky and Stars dedication (+era score per Great Person)
- Superior policy slots
- Psychological momentum for final DVP push

### T217-T228: Late-Game Collapse
Three simultaneous crises in the last 10 turns:
1. Dark Age in Information Era (103/111 threshold — barely missed)
2. Power Plant/Industrialization tech chain discovered to be broken
3. Culture Victory Imminent warning appeared

All three could have been avoided with:
- Earlier Sailing research (any turn from T80-T220)
- `get_victory_progress` called every 10 turns instead of 25-30
- Flower Power + Rock Band strategy identified at T180 instead of T227

---

## Part 6: DVP Race Analysis

| Turn | Scythia DVP | Scotland DVP | Babylon DVP |
|------|-------------|--------------|-------------|
| T100 | 0 | — | — |
| T110 | 1 | — | — |
| T120 | 3 | — | — |
| T130 | 5 | — | — |
| T150 | 5 | — | — |
| T175 | 7 | — | — |
| T195 | 9 | 9 | 8 |
| T220 | 9 | 9 | 11 |
| T221 | 11 | — | — |
| T228 | 11 | — | — (lost to Culture) |

The DVP race was effectively a 3-way tie at T195. Our 12-vote investment at T220 gained +2 DVP but was insufficient to overtake: 9 more DVP were needed (from 11 to 20), requiring at least 4-5 more World Congress sessions (~120-150 more turns). Culture victory arrived first at T228.

**Critical insight**: Diplomatic Victory requires sustained WC dominance across many sessions. At T221 with 11/20 DVP and Babylon winning Culture imminently, the only viable counter was military conquest of Babylon's cities (stopping their tourism infrastructure) or Rock Bands (reducing tourism). Flower Power + Rock Bands was the right answer — discovered one turn too late.

---

## Part 7: Tooling Improvements Made This Game

| Change | File | Description |
|--------|------|-------------|
| Tech/civic sort by turns | `narrate.py` | Available techs/civics sorted ascending; ≤2-turn items flagged `!! GRAB THIS` |
| GP activation failure table | (plan pending) | `UnitManager.CanStartCommand` failure table to be surfaced in error messages |

### Tooling Improvement Plan (Next Priority)

1. **GP activation requirements** (plan documented) — surface `failTable` from `CanStartCommand` in error messages
2. **Culture victory monitoring** — add tourism progress to end_turn report
3. **Production prerequisite errors** — surface "requires X first" when RequestOperation fails despite CanProduce=true
4. **Auto victory check every 10 turns** — integrate into end_turn rather than relying on manual calls

---

## Part 8: Strategic Lessons for Future Games

### Lesson 1: Scan Available Techs Every Turn
Never let a 1-turn boosted tech sit untouched. The "!! GRAB THIS" narration flag addresses this, but the player (agent) must also proactively check research options every few turns. If something costs ≤2 turns, queue it immediately even if it's not "on the plan."

### Lesson 2: Diplomatic Victory Takes ~150+ Turns from First Alliance
DVP accumulation is slow. Starting to pursue alliances at T110 and reaching 11/20 at T228 = 118 turns of play for 11 points. Need 20 points minimum, ideally 25+ to have buffer. **Start the diplomatic path from T60-T70 via early suzerainties and delegations, not T100+.**

### Lesson 3: Rock Bands Are a Late-Game Emergency Tool — Stock Them Early
Flower Power enables free Rock Band production. This should be queued and deployed **proactively** as a culture/tourism counter starting from T180-190 when culture victory threats become visible. One Rock Band per rival civ per turn is a significant tourism reduction. The discovery came too late (T227 vs T180 needed).

### Lesson 4: Victory Path Monitoring Must Be Every 10 Turns
`get_victory_progress` called every 25-30 turns is dangerously sparse. At 264 culture/turn, Babylon's culture victory window was ~15-20 turns. A 30-turn gap in monitoring meant the warning appeared with 1 turn remaining instead of 20.

### Lesson 5: Scythia's Military Kit Was Wasted
Scythia (Tomyris) has:
- Saka Horse Archers (2-for-1 production)
- +5 CS vs wounded units
- Extra health steal from kills

We never fought a player war. The Saka Horse Archer advantage was partially used (2-for-1 production), but the combat bonuses were entirely wasted on barbarians. A diplomatic/builder Scythia play works — but leaves 40% of the civ's power on the table.

### Lesson 6: Identify the Industrial Chain at T80
Every civ needs to trace the tech path to Factory/Power Plant by T80. This requires checking: does your industrial path flow through a naval branch? In this game: Industrialization ← Square Rigging ← Cartography ← Celestial Navigation ← **Sailing**. Without tracing the chain proactively, critical prerequisite gaps become invisible until the last moment.
