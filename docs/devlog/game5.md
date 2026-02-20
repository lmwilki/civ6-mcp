# Game 5 — Macedon (Alexander) — Devlog

## Civ Kit & Strategy

**Alexander of Macedon** — Domination civ.
- **To the World's End**: No war weariness, +5 CS when attacking
- **Hellenistic Fusion**: Eurekas/Inspirations from conquering cities with Campuses/Encampments
- **Hypaspist** (replaces Swordsman): +5 CS besieging, +50% support bonus
- **Hetairoi** (replaces Horseman): +5 CS near Great General, GP points on kill, free promotion
- **Basilikoi Paides** (Encampment building): +25% XP, science from training military

**Victory Plan**: Military expansion. Settle 3-4 cities fast, build Encampment with Basilikoi Paides for science-from-military engine, rush Iron Working + Horseback Riding for unique units, conquer a neighbor by T80-100.

## T1-T17: Opening

**T1**: Settled Pella at (28,14) — river + coast. Good food from floodplains, access to Pearls luxury. Started Scout → Slinger build order. Research: Mining.

**T3**: Warrior explored south, discovered Uluru at (24,14) — natural wonder! Boosted Astrology and Sailing from coast settle.

**T7**: Scout built, set to auto-explore. Started Slinger (7 turns). Got a free second scout (goody hut?) — automated it too.

**T16-17**: Code of Laws complete. Set Discipline + Urban Planning policies. Damaged barbarian Spearman (CS:25, 29 HP) spotted at (22,13) — 2 tiles from scout. Met a city-state.

**State at T17**:
- Score: 15 | Gold: 91 (+6/turn) | Sci: 3.0 | Cul: 1.6 | Faith: 2
- 1 city (Pella), 3 units (warrior exploring south, 2 scouts auto-exploring)
- 9% explored (85/890 tiles) — need to keep pushing
- Era score: 5/11 for Dark Age threshold — need 6 more era score
- Research: Animal Husbandry (reveals horses for Hetairoi planning)
- Building: Slinger

**Immediate priorities**:
1. Set civic research (Foreign Trade for trade routes)
2. Handle barbarian spearman threat (it's damaged — warrior could finish it with Discipline bonus)
3. Keep scouts exploring — 9% is terrible, need 15%+ by T25
4. Slinger finishes → Settler next (MUST have 2 cities by T40)

**Self-check: Am I following the playbook?**
- [x] Scout built and automated
- [x] Second scout automated (bonus unit)
- [x] Warrior exploring (not sitting in city)
- [ ] !! I fortified the scout in the city instead of automating it — caught by user. Classic sensorium failure. Fixed immediately.
- [ ] Civic research not yet set — need to do this
- [ ] No delegation sent yet — haven't met a major civ
- [ ] Gold: 91 — fine for now, watch for spending triggers

## T18-T30: Diplomacy Bugs & Settler Phase

**T21**: Met Sumeria (Gilgamesh). Sent delegation (rejected). Killed barbarian spearman with scout — earned eureka for Archery progress.

**T21-32**: **Lost 11 turns to a tooling bug.** AI-initiated delegation offer from Gilgamesh during end_turn processing created a half-dismissed diplomacy popup. The DiplomacyActionView was hidden via SetHide(true) but the session wasn't closed and ShowIngameUI wasn't called (race condition — check `IsHidden()` after `SetHide(true)` always returns false). Turns auto-advanced through the blocker resolution loop without me getting to act. **Fixed three bugs**: (1) dismiss_popup race condition, (2) orphaned session recovery in end_turn, (3) specific blocker messages instead of generic fallback.

**T32**: Settler complete. Set Pella to build Builder. 3 scouts auto-exploring, warrior heading west to scout mountain range near (25,22-25). Found Chinguetti (Religious city-state), sent 1 envoy.

**T32**: Promoted both scouts (Ranger — faster in woods/jungle). Identified settle target: (26,20) with fresh water, Coffee + Jade luxuries, Horses nearby.

## T30-T40: City #2 Founded, Capital Under Siege

**T36**: Archery researched! Barbarian galley at (28,13) and quadrireme at (27,12) have been attacking Pella for multiple turns — **completely unnoticed.** The `get_cities` tool only showed `Def:18` with no HP information. User caught this via screenshot: Pella's health bar was visibly depleted. **Fixed tooling**: added city HP display (garrison HP was already collected, just hidden when no walls built).

**T39**: Founded Methone at (26,20). Upgraded slinger→archer (60g). Set Methone to build Monument. God of the Forge pantheon (+25% military production).

**T39-40**: Discovered **archer upgrade bug**: upgrading on the same turn as end_turn leaves the new unit with 0 moves / 0 attacks on the next turn. `get_units` shows full moves but Lua confirms 0. Workaround: `UnitManager.RestoreMovement()` in GameCore. Also discovered **ranged attack LOS bug**: `GetOperationTargets(RANGE_ATTACK)` returns empty list even for valid targets (naval units adjacent to land). `CanStartOperation` with target params works correctly. **Fixed**: replaced GetOperationTargets LOS check with CanStartOperation params check. Needs MCP restart.

**T40**: Hit galley with archer (42→25 HP). City retaliation should finish it. Builder improving wheat at (27,16). Switched research from Bronze Working (21 turns!) to Pottery (8 turns) for Granaries. Foreign Trade civic completes next turn — trade routes incoming.

**State at T40**:
- Score: 37 vs Sumeria 49 | Gold: 268 (+4/turn) | Sci: 3.5 | Cul: 2.9 | Faith: 8
- 2 cities (Pella pop 2, Methone pop 1)
- Pella HP: 69/200 — under naval siege
- 6 units: archer, warrior, 3 scouts, builder
- 26% explored (237/890 tiles) — ahead of benchmark
- Era: Ancient, score 14 (past dark age threshold 11, golden needs 25)
- 2 unimproved luxuries: Coffee, Pearls
- Only met Sumeria — 2 civs still unmet

**Critical failures this phase**:
1. **Naval siege blindness**: Barbarians attacked Pella for 10+ turns unnoticed because city HP wasn't displayed. Classic sensorium failure.
2. **Archer couldn't fire for 2 turns**: Upgrade move bug + LOS check bug compounded. Tooling blocked valid attacks.
3. **Lost turns to auto-advancing**: Turns 21-32 passed without agency due to diplomacy popup bug.
4. **Never checked `get_map_area` around capital**: Violated my own "check radius 3-4 around cities every few turns" rule.

**Lessons applied to tooling**:
- City HP now visible in `get_cities` output
- LOS check uses `CanStartOperation` (authoritative) instead of `GetOperationTargets` (unreliable)
- `dismiss_popup` properly closes diplomacy sessions before hiding UI
- `end_turn` detects orphaned diplomacy sessions and provides specific blocker info

**Priorities for T40-60**:
1. Kill naval barbarians, heal Pella
2. Build Campus in Pella (science is critical — 3.5/turn is terrible)
3. Improve Coffee luxury (amenities emergency)
4. Foreign Trade → build Trader, domestic route to Methone
5. Meet the other 2 civs — scouts are exploring
6. Third city by T60

## T41-T60: Promotion Bug Saga & Quadrireme Kill

### Tooling Fixes (T41-T53)

This phase was dominated by fixing the **unit promotion bug** — a persistent engine-level failure that had plagued Games 1, 4, and 5.

**The problem**: InGame `RequestCommand(unit, PROMOTE, {promotionHash})` silently fails. `CanStartCommand` returns true, the command appears to execute, but `HasPromotion()` returns false. The promotion never applies. Meanwhile `NEEDS_PROMOTION` blocks ALL unit operations — the unit can't move, attack, skip, or do anything. The archer was stuck at Pella for 15+ turns, unable to fire at the barbarian quadrireme sieging the city.

**Root cause**: `RequestCommand(PROMOTE)` is broken at the Firaxis engine level for InGame context. GameCore `exp:SetPromotion(promo.Index)` writes the flag directly and works reliably.

**Fix**: Rewrote `build_promote_unit` in `lua_queries.py`:
- Changed from InGame `RequestCommand(PROMOTE)` to GameCore `SetPromotion(promo.Index)`
- Added validation chain: `CanPromote()` → `SetPromotion()` → `HasPromotion()` verify
- Heals unit to full HP (`SetDamage(0)`) — matches normal promotion behavior
- Consumes movement (`FinishMoves()`) — promotions end the turn
- Follow-up InGame call dismisses `ENDTURN_BLOCKING_UNIT_PROMOTION` notifications (GameCore promotion doesn't clear InGame notification system)

**Collateral damage**: During debugging, the original archer got a GameCore/InGame desync — GameCore showed the promotion applied, InGame didn't. This made the unit permanently broken (ranged attacks dealt 0 damage despite appearing to fire). Had to delete the archer and build a fresh one.

**T43**: Bought Trader (170g), started domestic route Pella→Methone (+1 food, +1 production).

**T47**: Builder improved wheat farm at (27,16), moved to floodplains at (28,15). Deleted broken archer. Set Pella to build new Archer with Agoge policy (+50% military production, 6 turns).

### Quadrireme Kill & Validation (T53-T55)

**T53**: New archer built at Pella. First ranged attack test: **22 damage dealt** (quadrireme 76→54 HP). Both fixes confirmed working:
- **LOS fix**: `CanStartOperation` with target params correctly identifies valid targets (was blocked before by empty `GetOperationTargets`)
- **Promotion tool**: Ready for next XP threshold (not needed yet on fresh unit)
- Note: the intermediate damage display still shows "damage dealt:0" — only the "Post-combat:" line shows real damage. Known display bug, not a real issue.

**T54**: Second shot — quadrireme 54→30 HP.

**T55**: Third shot — **quadrireme killed**. The 15+ turn naval siege of Pella is finally over. Pella can heal.

### Expansion & Economy (T55-T60)

**T55-58**: Pottery researched. Bronze Working completed (iron revealed — none in territory). Craftsmanship civic done. Early Empire civic completed — unlocks Colonization policy (+50% settler production) and governor appointment.

**T58**: Methone finished Monument, set to build Builder (15 turns — slow, pop 2). Pella set to build Settler.

**T60**: Foreign Trade civic was already done from earlier. Settler built at Pella. Need to find a settle site for city #3.

### State at T61

| Metric | Value | Benchmark |
|--------|-------|-----------|
| Turn | 61 | — |
| Score | 55 vs Sumeria 83 | Behind by 28 |
| Cities | 2 | Should be 3 by T60 (BEHIND) |
| Gold | 201 (+4/turn) | Spending trigger at 300 |
| Science | 4.4/turn | Terrible — need Campus |
| Culture | 4.3/turn | Adequate for now |
| Faith | 37 | Slow accumulation |
| Favor | 6 (+0/turn) | Need friendships |
| Explored | 29% (264/890) | Target 35% by T75 |
| Era Score | 17/46 golden, 17/32 dark | 15 short of dark age avoidance |
| Military | 111 vs Sumeria 113 | Rough parity |

**Cities**:
- Pella (pop 3, HP 141/200 healing): No production set. Settler just built.
- Methone (pop 2, HP 200/200): Building Builder (5 turns). 0 amenities — growth stalled (26 turns to next pop).

**Units**: Settler ready at Pella. Archer defending Pella. Warrior at Methone. 3 scouts auto-exploring. Builder (1 charge remaining) at (27,17). Trader on domestic route.

**Diplomacy**: Only met Sumeria — neutral (+3), mutual delegations. 2 civs still unmet. Suzerain of Chinguetti (Religious). 2 envoys in Vilnius (Cultural).

**Resources**: 3 unimproved luxuries (Jade, Coffee, Pearls). 0 strategic resources (no iron, no horses in territory). Horses nearby at (29,18) and (29,20) — potential settle target.

**Religion**: No religion founded by anyone. 3 slots remain. Not pursuing — Macedon has no religious bonuses.

**Victory Assessment**: Culture rated 70% viable (surprising — low tourism gap). Science 60% but 3 techs behind Sumeria and no Campus yet. Domination 40% — strong military but only 2 cities. Religion permanently closed (no Holy Site, turn 61).

### Blockers to Resolve

1. **Governor appointment**: 1 point available. Magnus (Provision — settlers don't consume population) or Pingala (science/culture boost) are top candidates.
2. **Dedication**: Classical era — Free Inquiry (+1 era score per eureka/science building) or Monumentality (+1 per specialty district) best fits.
3. **Research**: Writing (Campus unlock, 4 turns boosted) is critical.
4. **Civic**: Mysticism (envoys, 10 turns boosted) or Military Tradition (10 turns boosted).
5. **Pella production**: Needs new build order — Campus is the priority.
6. **Settle city #3**: Settler ready. Need to identify location and escort.
7. **Policies**: Swap Agoge→Colonization? No — settler already built. Keep Discipline for barbarian defense.
8. **Amenities emergency**: Methone at 0 amenities. Builder has 1 charge left — should improve Coffee or Jade.

### Critical Failures This Phase

1. **Promotion bug cost 15+ turns of archer utility.** The quadrireme siege lasted from ~T36 to T55 because the archer couldn't fire. Tooling fix prevents this from happening again.
2. **Still only 2 cities at T61.** Benchmark says 3 by T60. Settler is built now — must settle immediately.
3. **No Campus at T61.** Science is 4.4/turn — catastrophically low. Every other civ has 5-10 sci/turn. Campus in Pella is the single most important production item.
4. **0 amenities in Methone.** Growth penalty active. Builder's last charge should go to Coffee (26,19) for empire-wide amenity.
5. **Score gap widening.** Sumeria 83 vs Macedon 55 — they have 3 cities and more techs. Need aggressive expansion and Campus buildout to close the gap.
6. **Sumerian pincer on Methone unnoticed.** War Cart (CS:30) at (27,19) and Warrior (CS:20) at (27,21) flanking Methone from 1 tile away. Only defender is a CS:20 warrior garrison. Sensorium failure — I had the threat data in `get_units` output ("Nearby threats: Sumeria 2 units") but didn't act on it. Classic case of reading data without processing implications.

## T61-T70: Expansion & Diplomacy Turnaround

### Key Actions

**T64**: Founded Alexandria Troas at (29,18) — fresh water, Horses, Jade, Wheat nearby. Top-ranked global settle site (score 248). Warrior garrison fortified. Set to build Monument. Pella started Campus at (27,13) with +2 adjacency (9 turns). Writing tech completed — Currency boosted from trade route.

**T64**: Appointed Pingala (Educator) and assigned to Pella for science/culture bonus. Chose Free Inquiry dedication (+1 era score per eureka/science building). Set Limitanei policy for +2 loyalty in garrisoned cities (Alexandria Troas was losing loyalty at pop 1).

**T67**: Jade luxury improved at (24,20) — amenities from 0 to 1 in Methone and Alexandria Troas. Built a second warrior and positioned at (27,17) to screen against the Sumerian War Cart that kept patrolling the area.

**T68**: Gilgamesh declared friendship! Earlier rejection at Neutral was followed by an AI-initiated "good friend and ally" dialogue. Friendship confirmed (+21 modifier, +9 for declared friend, +12 for Gilgamesh liking friends). War Cart threat neutralized diplomatically. Sumeria now strongest ally.

**T69**: Military Tradition civic completed. Mysticism completed earlier (gave envoy — sent to Vilnius for 3 envoys, cultural bonuses). Set State Workforce civic.

### State at T70

| Metric | T61 | T70 | Delta |
|--------|-----|-----|-------|
| Score | 55 | 76 | +21 |
| Cities | 2 | 3 | +1 |
| Gold | 201 (+4) | 207 (+4) | stable |
| Science | 4.4 | 6.1 | +1.7 |
| Culture | 4.3 | 8.6 | +4.3 (doubled!) |
| Faith | 37 | 46 | +9 |
| Favor | 6 (+0) | 20 (+0) | +14 |
| Explored | 29% | 32% | +3% |
| Military | 111 | 132 | +21 |
| Era Score | 17 | 20 | +3 (still 12 short of dark age) |

**Cities**:
- Pella (pop 4): Campus building (4 turns left). Amenities 3. Pingala establishing.
- Methone (pop 2): Granary building (10 turns). Amenities 1 (Jade). Growth now 7 turns (was 22).
- Alexandria Troas (pop 1): Monument building (11 turns). Amenities 1. Growing in 1 turn.

**Diplomacy**: Sumeria declared friend (+21). Suzerain of Chinguetti. 3 envoys in Vilnius. 2 civs still unmet.

**Resources**: Jade improved. Horses at +2/turn (from Alexandria Troas territory). Iron importing 2 (from where?). Coffee and Pearls still unimproved — need Irrigation (2 turns) for Coffee.

**Tech/Civic**: Irrigation in 2 turns (enables Coffee plantation). State Workforce in 7 turns (more district policies). 7 techs, 6 civics completed.

### Strategic Assessment

**What's working**:
- Expansion finally happening — 3 cities, triangular layout with 4-6 tile spacing
- Gilgamesh friendship secures southern border for 30 turns
- Military strongest on the map (132 vs Sumeria's 118)
- Culture doubled from civic completions + Vilnius envoys
- Jade luxury solved amenities crisis

**What's not working**:
- Science still terrible at 6.1/turn vs Sumeria's 16. Campus completes T74 but Library needs Currency tech. This is a 10+ turn gap before meaningful science income.
- Era score 20/32 — heading for Dark Age in Classical. Need 12 more era score in remaining turns. Building Campus (+1 from Free Inquiry) helps but probably not enough.
- Gold flat at +4/turn despite 3 cities. No Commercial Hub, only 1 trade route. Need Currency → Market for trade route capacity.
- 2 civs still unmet — missing delegation/friendship favor income. Scouts are exploring but slowly.
- Still 2 unimproved luxuries (Coffee, Pearls).

### Fog-of-War Cheating Fix (T70)

Discovered that several tools were reading game data through fog of war. `GetResourceType()` and `GetYield()` in GameCore return real values for ALL tiles regardless of player visibility. Five tools were affected:

- **Settle advisors** (both per-settler and global): scored workable tiles within radius 3 without checking `IsRevealed` — yields and resources from fog-of-war tiles inflated scores
- **Minimap**: showed `*` (strategic) and `+` (luxury) markers for resources the player hasn't unlocked the prereq tech for (e.g. Niter before Military Engineering)
- **District advisor**: counted hidden sea resources for Harbor adjacency
- **Purchasable tiles**: displayed resource names/classes without tech gating

Fixed all five by adding `vis:IsRevealed(tPlot:GetIndex())` checks to yield loops and `PrereqTech` gates to resource displays. Global settle advisor top score dropped from 248 → 196 after fix.

**Impact on earlier decisions**: The settle site for Alexandria Troas (29,18) was identified partly using inflated scores that included unrevealed tile yields. The decision may have been different with accurate scoring, though (29,18) was still a strong site with fresh water, visible Horses, and proximity to Jade. Earlier `get_strategic_map` unclaimed resource listings and minimap resource markers may have also revealed resources we shouldn't have known about. Going forward, all tools respect fog of war.

### Strategy Going Forward

**Victory path**: Domination is the natural Macedon path but requires unique units (Hypaspist needs Iron Working, Hetairoi needs Horseback Riding — both 20 turns at current science). Near-term focus should be **science infrastructure** to unlock the military techs faster.

**Immediate priorities (T70-80)**:
1. Campus completes T74 → Library immediately (needs Currency — research after Irrigation)
2. Irrigation T72 → builder improves Coffee → amenities for all cities
3. Currency after Irrigation → Market → +1 trade route capacity, Commercial Hub unlock
4. State Workforce T77 → more policy slots for upcoming government change
5. Send new builder to Pearls (29,13) after Coffee
6. Alexandria Troas: Monument → Granary → Campus
7. Methone: Granary → Campus or Encampment

**T80 checkpoint targets**:
- 4+ cities (need another settler by T85)
- Campus + Library in Pella (15+ sci/turn)
- All luxuries improved
- Horseback Riding or Iron Working started

## T80-T83: Library Completion & Crash

**T80**: Strategic checkpoint. Science jumped to 16.2/turn (from 4.4 at T61 — Campus + Pingala Researcher doing heavy lifting). Bought builder at Pella (230g). Set Colonization + Conscription policies. Horseback Riding researching, Political Philosophy civic in progress. Methone building Settler with Colonization (+50% production). Trade route running Pella → Alexandria Troas.

**T80 (rendering bug)**: Gilgamesh 3D model stuck over entire map after rejected OPEN_BORDERS action. Diplomacy session cleanup, popup dismissal, ShowIngameUI all failed — 3D scene is graphics-layer, not Lua-clearable. Required full game restart.

**T83**: Library completed at Pella (+2 science). Builder farmed Wheat at (28,16). Set Government Plaza production at Pella (6 turns — fast, enables Ancestral Hall for free builders on settle). Game crashed immediately after builder improvement + district advisor query.

### UI.LookAtPlot Crash Fix

Both the T73 and T83 crashes shared a common code path: `UI.LookAtPlot()` camera pan inside `build_improve_tile()`, called immediately before `RequestOperation(BUILD_IMPROVEMENT)`. The Lua queries returned successfully both times — crash was asynchronous, likely in the rendering pipeline (which was already unstable per the Gilgamesh 3D model bug at T80).

`UI.LookAtPlot` is purely cosmetic — pans the game camera. Removed all 8 instances across 7 functions:
- `build_move_unit`, `build_attack_unit`, `build_found_city`, `build_improve_tile`
- `build_set_city_production`, `build_purchase_item`, `build_purchase_tile`, `build_make_trade_route`

No functional impact — all operations work without camera panning.

### State at T83

| Metric | T70 | T83 | Delta |
|--------|-----|-----|-------|
| Score | 76 | 93 | +17 |
| Cities | 3 | 3 | +0 |
| Gold | 207 (+4) | 0 (+6) | spent on builder |
| Science | 6.1 | 16.2 | +10.1 (Campus+Library+Pingala) |
| Culture | 8.6 | 10.8 | +2.2 |
| Faith | 46 | 62 | +16 |
| Favor | 20 (+0) | 40 (+0) | +20 |
| Explored | 32% | 32% | +0% (scouts stuck?) |
| Era Score | 20/32 | 22/32 | +2 (Dark Age likely) |

**Production**: Pella (Library done → Government Plaza 6t), Methone (Settler ~14t), Alexandria Troas (Granary ~7t)
**Research**: Horseback Riding (3t) | Political Philosophy (3t)
**Diplomacy**: Sumeria friend. 2 civs unmet. Score gap: Sumeria 144 vs us 93.
- Meet remaining 2 civs

## T83+: Information Leakage Fix

Before continuing play, audited and fixed information leakage across 3 tools:

**Problem**: `get_victory_progress` exposed full per-civ stats (score, science, military, cities, techs) for ALL civs including unmet ones. A real player only sees the Demographics panel (anonymized rank/value/best/avg/worst) and per-civ data only for civs they've met.

**Fix**:
1. **`build_victory_progress_query`** — gated all PLAYER/CULTURE/CAPITAL/RELMAJ/RELFOUNDED output on `pDiplo:HasMet(i)`. Added demographics collection for all alive majors (anonymized aggregates matching in-game Demographics panel: Population, Soldiers, Crop Yield, GNP, Land, Goods).
2. **`build_victory_proximity_query`** — gated DIPLO_THREAT and SCI_THREAT on HasMet. Religion creator shows "Unknown civilization" for unmet founders.
3. **`build_overview_query`** — gated REL lines on HasMet (keep religion slot count as aggregate).
4. **Narration** — added Demographics section, updated victory assessments to use demographics best/worst instead of naming unmet rivals.

**Bug found during testing**: `c:GetOwnedPlotCount()` doesn't exist on city objects in InGame context. Fixed with `#Map.GetCityPlots():GetPurchasedPlots(c)`. Also used raw yield indices `c:GetYield(0)` instead of `GameInfo.Yields` lookup for food/production.

## Trade Route Investigation

Deep investigation of trade route "ghost" bug revealed a **misdiagnosis**:

1. **Initial assumption**: Trader at Pella had full moves (2/2) → must be idle → route counter (1/1) is a stale ghost → save+reload needed.
2. **Reality**: Traders on active routes have full moves at start-of-turn. They move during turn processing. The Pella → Methone domestic route was working the whole time (+1 Food, +1 Prod to Pella).

**Actual bug in `build_make_trade_route`**: Code bypassed `CanStartOperation` (which correctly said "capacity full at 1/1") and fired `RequestOperation` blindly. `RequestOperation` silently failed but the code reported "TRADE_ROUTE_STARTED" — a lie.

**Root cause from game source** (`TradeRouteChooser.lua:826-844`): Game uses 4 params: `PARAM_X0/Y0` (destination) + `PARAM_X1/Y1` (trader origin). Our code only sent `PARAM_X/Y` (= X0/Y0, destination only). Missing origin params may have contributed to earlier route issues.

**Fixes**:
- `build_make_trade_route`: proper 4-param format + `CanStartOperation` check + honest error ("CAPACITY_FULL" not fake success)
- `build_trade_destinations_query`: same 4-param format + capacity warning
- `build_trade_routes_query`: ghost detection = trader unit dead/captured only (NOT moves > 0)
- Key lesson: `movesRemaining > 0` does NOT indicate idle for traders

## T85: Resume After Reload

Loaded AutoSave_0085 after save/reload cycle. State: Score 95, Gold 28 (+5/turn), Science 18.5, Culture 10.8. Research and Civic both unset (need to choose). Trade route Pella → Methone active. Builder at (28,17) with 2 charges.

**T85-89**: Set research to Astrology (1t) → Iron Working (6t). Set civic to Drama and Poetry. Builder moved to mine Jade at (30,17). Met Spain (Philip II) — sent delegation (rejected). Government Plaza completed at Pella T89. Appointed Magnus governor, assigned to Pella. Alexandria Troas building Warrior.

## T90-91: Strategic Checkpoint & Government Fix

### The Government Oversight (Critical Error)

Discovered at T90 that we were **still on Chieftainship** — the Tier 0 starting government. Political Philosophy was researched around T83 but we never switched to a Tier 1 government. This caused two cascading failures:

1. **Gov Plaza buildings locked for 7 turns**: After Government Plaza completed at T89, Ancestral Hall / Warlord's Throne / Audience Chamber all showed CANNOT_PRODUCE. Spent an entire turn building Water Mill as placeholder before diagnosing the cause.
2. **Lost ~30 turns of Oligarchy bonus**: +4 CS to all military units (melee, ranged, anti-cav) from Oligarchy's innate bonus. Every battle fought since T83 was at -4 CS compared to what it should have been.

**Fix**: Changed government to Oligarchy at T90. Set policies: Agoge (military production), Conscription (maintenance reduction), Colonization (settler production), Charismatic Leader (envoy influence). Gov Plaza buildings immediately appeared in production — switched Pella from Water Mill to Ancestral Hall (15 turns).

### State at T91

| Metric | T83 | T91 | Delta |
|--------|-----|-----|-------|
| Score | 93 | 114 | +21 |
| Cities | 3 | 3 (+settler ready) | settler produced |
| Gold | 0 (+6) | 35 (+5) | stable |
| Science | 16.2 | 12.5 | -3.7 (Pingala moved?) |
| Culture | 10.8 | 11.9 | +1.1 |
| Faith | 62 | 77 | +15 |
| Favor | 40 (+0) | 63 (+0) | +23 |
| Explored | 32% | 34% | +2% (terrible) |
| Era Score | 22/32 | 28/32 | +6 (4 short of Normal!) |
| Military | — | 117 | — |

### Strategic Overview & Victory Path Assessment

**The Scoreboard Reality**:
- Sumeria: 209 score, 4 cities, 43 sci/turn, 38 cul/turn, 136 military
- Macedon: 114 score, 3 cities, 12.5 sci/turn, 11.9 cul/turn, 117 military
- Spain: 104 score, 1 city, 15 sci/turn, 13 cul/turn, 50 military
- Unmet civ: unknown stats, demographics suggest 159 military (best)

Sumeria has **nearly 2x our score** and **3.4x our science output**. They have a 3-tech lead (15 vs 12), 4 cities vs our 3, and are pulling away in every metric. The unmet civ has the strongest military on the map (159 from demographics).

**Domination viability (our stated goal)**: 15% per victory assessment. Problems:
1. Iron Working is 7 turns away — Hypaspists (our UU) still not buildable
2. Military 117 vs demographics best 159 — we're rank 3 in soldiers
3. Gilgamesh is our declared friend — can't attack for ~20 more turns
4. Spain is 1 city and far away — easy conquest but minimal strategic gain
5. No Encampment built → no Basilikoi Paides (Macedon's science-from-military engine)

**Culture viability**: 70% per assessment (RECOMMENDED). We need 10 tourists vs Sumeria's 10 domestic, and 6 vs Spain's 6. But we have 0 Theater Squares and 0 Great Works. This rating seems optimistic given no infrastructure.

**Science viability**: 60%. 3 techs behind Sumeria. 12.5 sci/turn is terrible — Sumeria has 43. We'd need 4+ cities with Campuses to catch up. Possible if we expand fast.

**Realistic assessment**: We're behind in everything. The next 30 turns are critical:
1. **Expand to 5 cities** — settler ready now, another needed by T110
2. **Campus in every city** — science must triple to compete
3. **Iron Working → Hypaspist + Encampment** — start the military-science engine
4. **Evaluate war target after friendship expires** — Sumeria is the real threat but also the strongest

### Immediate Actions Taken (T91)

- Settler completed at Methone — target: (32,20), score 218, fresh water, Jade+Coffee+Deer+Horses
- New warrior completed at Alexandria Troas — 2 warriors available for escort/garrison
- All 3 scouts automated for exploration
- Builder (1 charge) moving to farm Wheat at (26,14) for Pella food
- New builder (3 charges) spawned at Methone — origin unclear (civic reward?)
- Warrior moving east to pre-position near settle site
- Pella: Ancestral Hall (15 turns) — free builder with each new city
- Spain friendship rejected (relationship too low at +2)

### Dark Age Risk

Era score 28 out of 32 needed to avoid Dark Age (46 for Golden). With only a few turns left in Classical era, we need 4 more era score. Possible sources:
- Settling 4th city (+1-3 era score from new settlement/meeting)
- Iron Working completion (potential eureka era score)
- Building first unique unit
- Any new civic/tech boosts

Dark Age in Medieval would mean loyalty pressure, reduced yields, but access to powerful Dark Age policies (Twilight Valor: +5 CS all melee). For a domination-focused civ, Dark Age isn't catastrophic — but the loyalty penalties could threaten Alexandria Troas (already low loyalty concerns).

## T99-T103: War, City Loss, and Founding Fix

### War Declaration (T99)
Sumeria declared war after friendship expired at T92. Alexandria Troas fell immediately — single warrior garrison vs 2 War Carts + 2 Warriors. Critical strategic failure: all military had been pulled east to escort settler to (32,20).

### City Founding Bug (T99-T103)
`found_city` returned "FOUNDED|32,20" at T99 but city never appeared — settler remained alive. Root cause: `RequestOperation(FOUND_CITY)` is async; the Lua unconditionally printed success. The war declaration's diplomacy popup likely blocked the operation silently. **Fixed**: added popup dismissal before RequestOperation + post-verification via second TCP round-trip using `Plot:IsCity()`. Alexandroupoli successfully founded at T103 with the fix.

### Missing Sensor: Loyalty (T103 — BUG/GAP)
Discovered loyalty data was **never being queried or displayed**. Alexandroupoli is losing 11.4 loyalty/turn and will flip in 9 turns. Methone losing 3.2/turn (31 turns to flip). This was completely invisible until manually probing the Lua API.

Available API: `city:GetCulturalIdentity()` → `GetLoyalty()`, `GetLoyaltyPerTurn()`, `GetTurnsToConversion()`, `GetIdentitySourcesBreakdown()` (PopulationPressure, Governors, Happiness, Other).

**This is a textbook sensorium problem.** Loyalty is a critical game mechanic — cities can flip to free cities or rival empires — and we had zero visibility. Need to add loyalty to `get_cities` output immediately.

### Loyalty Sensor Implemented (T103)
Added loyalty visibility to two tools:

**`get_cities`** — now shows loyalty warnings on cities with negative loyalty/turn or loyalty below 75. Uses `GetCulturalIdentity()` API (InGame-only). Output: `!! Loyalty: 97/100 (-3.2/turn, flips in 31 turns)`.

**`get_settle_advisor` / `get_global_settle_advisor`** — estimates loyalty pressure at candidate settle sites using the real game formula: `pop * (10 - dist) / 10` with linear decay (range 0-9 tiles), 1.5x capital bonus. Converts raw pressure to approximate loyalty/turn and penalizes score for negative-pressure sites. Era factors (Golden/Dark age multipliers) omitted since `HasGoldenAge()` is InGame-only and settle advisors run in GameCore.

### City Founding Fix (T103)
`found_city` now dismisses diplomacy popups before `RequestOperation` and does a second TCP round-trip with `Plot:IsCity()` to verify the city actually appeared. Returns `FOUND_FAILED` with settle advisor suggestions if verification fails.

### State at T103
| Metric | Value |
|--------|-------|
| Score | 113 (4th of 4) |
| Cities | 3 (Pella, Methone, Alexandroupoli) — Alexandria Troas lost |
| Gold | 120 (+4/turn) |
| Science | 12.5 |
| Culture | 6.7 |
| Faith | 105 |
| Military | At war with Sumeria, no Hypaspists yet |
| Loyalty Crisis | Alexandroupoli: -11.4/turn, flips in 9 turns |

## T109: Strategic Sit Rep

### Am I winning? No.

Last place. Sumeria 255, Canada 197, Spain 140, Macedon 132. The gap is narrowing slightly (was 2x behind Sumeria at T90, now 1.9x) but we are behind on every demographic: population, military, crop yield, GNP, land, and goods. Rank 3 or 4 in everything.

### The war with Sumeria

Ongoing since T99. We lost Alexandria Troas (captured T101) and our archer. We gained one Hypaspist (CS:38, upgraded from warrior at T107). Sumeria has 5 cities, military 113 vs our 69. They're sending waves — War Carts (CS:30) and warriors — but they're arriving damaged and piecemeal, which is the only reason we haven't lost more.

**Alexandria Troas** is slowly losing loyalty (-0.2/turn, at 54/100) due to our nearby city pressure. It won't flip anytime soon (258 turns) but it IS bleeding. A governor or more nearby cities could accelerate this.

### Loyalty crisis resolved

Alexandroupoli loyalty stabilized after Pingala established (+8 loyalty). Was -11.4/turn, now the city is holding. Methone barely losing at -0.1/turn (985 turns to flip — effectively stable).

### Victory path assessment

| Path | Viability | Notes |
|------|-----------|-------|
| Science | 60% (recommended) | 14 techs vs Sumeria's 18. Need Campus in every city + libraries. Hypatia (Great Scientist) available to recruit. |
| Culture | 40% | Zero Theater Squares. Need 17 more tourists vs Sumeria. Very behind. |
| Domination | 15% | Military 69 vs Canada's 182. Can't take a capital. |
| Diplomatic | 20% | 117 favor banked, 0 VP. No World Congress votes yet. |
| Religion | 0% | All 3 slots filled. Permanently closed. |

### What needs to happen to win

**Science is the only realistic path.** Requirements:

1. **Expand to 5 cities** — Settler finishing at Pella in 4 turns. Need one more after. Best sites: (35,19) score 221, (36,20) score 206 — both safe from loyalty pressure.
2. **Campus in every city** — Only Pella has one. Methone and Alexandroupoli need Campuses immediately.
3. **Recruit Hypatia** — Great Scientist available (61/60 points). Activating on Pella's Campus with Library gives bonus science.
4. **Build Libraries everywhere** — Each Campus + Library = ~8 science. Need to 3x our science output (15 → 45+) to compete with Sumeria's 37.
5. **End the war** — Sumeria is draining resources. Need peace to build infrastructure. 10-turn war cooldown has passed.
6. **Trade routes to new cities** — Domestic routes for food+production to bootstrap new settlements.
7. **Build Commercial Hubs** — Need gold income. Currently at +2/turn, nearly broke after Hypaspist upgrade.

### Critical gaps (sensorium)

- **Enemy city loyalty not surfaced by any tool.** Alexandria Troas losing loyalty is only visible via manual Lua probe. Should add rival city loyalty to diplomacy or strategic map output.
- **No visibility into Sumeria's army composition or direction.** We see threats near our cities but not what's coming from further away.

### State at T109

| Metric | Value |
|--------|-------|
| Score | 132 (4th of 4) |
| Cities | 3 (Pella, Methone, Alexandroupoli) |
| Gold | 12 (+2/turn) |
| Science | 15.2 |
| Culture | 7.6 |
| Faith | 121 |
| Favor | 117 |
| Military | 69 (last place) — 1 Hypaspist, 3 scouts |
| War | vs Sumeria since T99, their military 113 |
| Loyalty | All cities stable. Enemy Alex Troas at 54/100 (-0.2/turn) |

## T109 Strategic Sitrep & Plan

### Tooling Upgrade
- Added visible enemy city data to `get_diplomacy` — now shows per-city name, pop, position, loyalty, walls for all revealed enemy cities. Previously only showed a total count. Closes the biggest sensorium gap.

### Current Position (T109)
- **Score**: 132 (4th of 4) — Sumeria 255, Canada 197, Spain 140
- **Cities**: 3 vs Sumeria's 5, Canada's 5 — critically behind
- **Science**: 15.2 vs Sumeria's 37 — half their output
- **Military**: 69 (last) — 2 Hypaspists, 3 scouts. Canada 182, Sumeria 113
- **Gold**: 12 (+2/turn) — near broke
- **Faith**: 121, no religion (slots filled) — available for Great Person patronage
- **Favor**: 117 (+0/turn) — no friendships/alliances generating favor
- **Exploration**: 45% — adequate but gaps remain east

### Assessment: Science Victory Is the Only Path
- **Religion**: Permanently closed (all 3 slots filled)
- **Domination**: Military is weakest by far (69 vs 182 Canada). Would need to 3x military.
- **Culture**: Zero Theater Squares at T109. No Great Works.
- **Diplomatic**: 0/20 VP. Low favor income. Viable as backup but slow.
- **Science**: 4 techs behind Sumeria but closable with Campus spam. **RECOMMENDED**.

### The Plan: Science Sprint (T109-T200)

**Phase 1: Infrastructure (T109-T130)**
1. Recruit Hypatia → activate on Pella Campus (Library + instant Library bonus)
2. Settler finishing T113 → settle at (35,19) — score 225, fresh water, 9 resources
3. Campus in Methone (started, 14 turns)
4. Campus in Alexandroupoli after Monument finishes
5. Propose peace with Sumeria — war is pure drain with no conquest target
6. Promote Magnus → Provision (settlers don't cost pop) — need governor point
7. Build 2nd settler immediately after 1st
8. Improve Pearls (luxury) and Stone (quarry)
9. Declare friendship with Canada (FRIENDLY) for +1 favor/turn

**Phase 2: Science Engine (T130-T160)**
1. 5 cities, each with Campus + Library = ~50 science/turn
2. Commercial Hubs in 2-3 cities for gold + trade routes
3. Research → Industrial Zone techs → Apprenticeship → Universities
4. Trade routes: domestic to new cities for food+production
5. Build alliances when Diplomatic Service unlocks

**Phase 3: Space Race (T160-T300)**
1. Universities in all cities → target 80+ science/turn
2. Research toward Rocketry → build Spaceport
3. Activate Great Scientists on Campuses
4. Space projects: Earth Satellite → Moon Landing → Mars Colony → Exoplanet

### Immediate Actions This Turn (T109)
- [x] Recruit Hypatia (Great Scientist)
- [x] Move Hypatia to Pella Campus (27,13)
- [x] Set Methone → Campus at (25,21) +2 adj
- [x] Assign Victor to Methone
- [x] Automate all 3 scouts
- [x] Attack barbarian swordsman at (25,21)
- [x] Move builders toward improvements
- [ ] Propose peace with Sumeria (after 10-turn cooldown check)
- [ ] Try to declare friendship with Canada

## Concession — T110

### Why We're Stopping

Last place at T110 with no realistic path to recovery. Sumeria has 2x our score (256 vs 139), 3.4x our science (39 vs 16), and 5 cities to our 3. Canada has 2.1x our military. The science sprint plan required tripling science output and expanding to 5 cities — possible in theory, but we'd be playing from behind for 200+ turns with zero margin for error.

More importantly, this game served its real purpose: **stress-testing the tooling.** Every major system — combat, diplomacy, production, city founding, promotions, trade routes, loyalty, fog-of-war — was exercised and debugged. The game is unwinnable, but the tools are substantially better.

### Tooling Developed During Game 5

**Bugs fixed (13):**
1. Diplomacy popup race condition — `SetHide(true)` didn't close sessions, causing 11-turn blackout (T21-32)
2. City HP display — hidden when no walls built, naval siege went unnoticed for 10+ turns
3. Archer upgrade movement bug — upgrading consumed next turn's moves, workaround via `RestoreMovement()`
4. Ranged attack LOS check — `GetOperationTargets` unreliable, replaced with `CanStartOperation` params check
5. Unit promotion engine failure — `RequestCommand(PROMOTE)` silently fails in InGame, rewrote to use GameCore `SetPromotion()`
6. Fog-of-war information leakage — 5 tools read through fog (settle advisors, minimap, district advisor, purchasable tiles)
7. Victory progress information leakage — exposed full stats for unmet civs, added `HasMet()` gating
8. 3D leader scene persistence — `Events.HideLeaderScreen()` as kill switch, added to all diplomacy tools
9. `UI.LookAtPlot` async crashes — removed all 8 camera pan calls across 7 functions
10. City founding async failure — added popup dismissal + post-verification via `Plot:IsCity()`
11. Trade route ghost misdiagnosis — traders have full moves on active routes, fixed idle detection
12. Trade route missing params — added `PARAM_X1/Y1` (origin) matching game source
13. Overview query fog leakage — religion founder names gated on `HasMet()`

**Sensors added (4):**
1. City HP in `get_cities` — visible when damaged or has walls
2. Loyalty warnings in `get_cities` — shows loyalty/turn and flip timer for at-risk cities
3. Loyalty pressure estimation in settle advisors — predicts loyalty viability before settling
4. Visible enemy city details in `get_diplomacy` — name, population, position, loyalty, walls

**Other improvements:**
- `end_turn` detects orphaned diplomacy sessions with specific blocker messages
- `dismiss_popup` properly closes sessions before hiding UI
- Demographics section added to victory progress (anonymized, matches in-game panel)
- `found_city` returns `FOUND_FAILED` with settle suggestions on verification failure

### Lessons for Game 6

**Strategic:**
- Switch government the turn you unlock it. The T83-T90 Chieftainship oversight cost +4 CS on every combat for 7 turns.
- Macedon's kit requires an Encampment with Basilikoi Paides to generate science from military. We never built one — the entire civ ability was wasted.
- Don't pull all military to escort a settler during an active war. Alexandria Troas fell because every unit was east of (30,20).
- Expansion benchmarks are real. 3 cities at T110 is a death sentence regardless of other play.

**Tooling:**
- Every sensor gap becomes a strategic blind spot. If the tool doesn't surface it, it doesn't exist. Audit for gaps *before* playing, not after losing cities.
- Write operations need verification round-trips. `RequestOperation` returning doesn't mean it worked — async confirmation is mandatory.
- GameCore vs InGame API split is the #1 source of bugs. Maintain the reference table in MEMORY.md and check it before writing any new Lua.
- The promotion bug, the founding bug, and the diplomacy popup bug all shared a root cause: **Firaxis APIs that silently fail.** Never trust a void return. Always verify state after mutation.

### Final State

| Metric | T1 | T40 | T70 | T110 | Benchmark |
|--------|-----|-----|-----|------|-----------|
| Cities | 1 | 2 | 3 | 3 | 5 by T100 |
| Science | 3.0 | 3.5 | 6.1 | 16.2 | 25+ by T100 |
| Score | — | 37 | 76 | 139 | Competitive |
| Military | — | — | 132 | 91 | 150+ |
| Explored | 9% | 26% | 32% | 47% | 50% by T100 |

**Result: Conceded at T110. 4th of 4 civilizations. Primary value was tooling development.**
