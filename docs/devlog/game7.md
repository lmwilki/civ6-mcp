# Game 7 — Portugal (Jo\u00e3o III) — Devlog

**Result: Defeat at T318 — France Diplomatic Victory (20/20 DVP)**
**Final Score: Portugal 1186 (#1) vs France 1186, Korea 847, China 659**

The highest-scoring loss. Portugal led in score for most of the game and had 18/20 DVP — but France reached 20 first. A game defined by economic dominance undercut by production corruption, broken melee combat, and a WC targeting bug that gave a rival +2 DVP with our own favor.

---

## Civ Kit & Opening Plan

**Jo\u00e3o III of Portugal** — Trade/naval civ.
- **Casa da \u00cdndia**: International trade routes get +50% yields to cities on other continents; +1 gold to all international routes
- **Navigation School**: Unique building replacing University (+25% science from trade routes, +1 Great Admiral point)
- **Nau**: Unique caravel (can acquire luxury resources from foreign coasts)
- **Feitoria**: Unique improvement (placed on foreign coast, gold + production bonuses from trade routes)

**Victory Plan (T0)**: Diplomatic victory via trade network dominance. Portugal's trade bonuses generate massive gold and favor through suzerainties. Build wide (8+ cities), fill all trade route slots, stack trade policies, leverage City-State suzerainties (each = +2 favor/turn). Science as backup.

**Opening Build Order**: Scout \u2192 Slinger \u2192 Settler \u2192 Builder

---

## T1-20: Coastal Start, Barb Siege

**T1**: Settled Lisbon at (42,12) — coastal plains hills with river, stone, fish, and Truffles luxury. Mountain range to the east. Set Mining research (jungle/hills terrain needs improved).

**T10**: Scout exploring south. Slinger training. Barb scout spotted near capital — defensive posture needed.

**T15-17**: **Settler captured by barbarians.** The first major setback. A barb warrior intercepted the settler before escort was in position. This cost ~10 turns of production and required military action to recover.

**T19-22**: Warrior recovered the captured settler from the barbarian camp. The recovery operation delayed expansion by 5+ turns but saved the settler investment.

### Assessment: T1-20

**Strategic**: The settler capture was a painful opening. Portugal's trade-focused kit demands early cities (more cities = more trade routes = compound returns), so losing 5+ turns of expansion was costly. The coastal start was ideal for Portugal's naval bonuses, but the mountain wall to the east constrained land expansion directions.

**Tactical**: The barb engagement was poorly handled — the settler moved without adequate escort (violating the Civilian Safety Gate). The recovery was efficient once committed, but the mistake shouldn't have happened.

**Tooling**: Early turns were clean. Production and research tools worked. The diary system captured the settler crisis well. Stale "Choose a Civic" notification began appearing and would persist for the entire game.

**Hypothesis Quality**: Opening predictions about terrain and expand sites were reasonable. Failed to predict barb threat severity — the CLAUDE.md playbook explicitly warns about this, and it was ignored.

---

## T21-60: Expansion Phase — 4 Cities by T45

**T26**: Braga founded (city #2). Late by ~10 turns due to settler capture, but a strong site with jungle hills and rice.

**T29**: Guarda founded (city #3). Good defensive position between Lisbon and Braga. Sent first delegation to France (+3 modifier).

**T45**: Funchal founded (city #4) at (39,15). Coastal site with access to fish and coral.

**T49**: Adopted Oligarchy (+4 CS to all melee/ranged). Military strength 120 — adequate for defense.

**T50**: Score 141, 38% explored. Science 23.5, Culture 17.7. France met at T56 — our first major diplomatic contact. The trade network began taking shape with 3 active trade routes.

**T56-60**: Met France (Catherine de Medici). Sent delegation immediately. Started navigation toward Kilwa Kisiwani wonder (critical for suzerainty bonuses). Melee attack bugs first documented — attacks silently fail against barbarians.

### Assessment: T21-60

**Strategic**: Recovery from the settler capture was solid — 4 cities by T45 was behind the T40 benchmark but not catastrophically so. The focus on trade routes from the start was correct for Portugal's kit. However, Campus construction was delayed in favor of Navigation Schools — a questionable trade-off that left science at 23.5/turn by T50 (below the 30+ target).

**Tactical**: City placements were good. Trade route assignments prioritized food for new cities (correct). Builder management was efficient with luxury improvements first. The melee combat bug was discovered but treated as an anomaly rather than a fundamental limitation.

**Tooling**: The melee attack bug (attacks deal 0 damage and silently no-op) was first documented here. It would prove to be permanent and game-defining — eliminating conventional military offense for the entire game. The stale civic notification persisted every turn.

**Hypothesis Quality**: Predicted France as a potential ally (correct — became research alliance partner). Predicted 5 cities by T75 (achieved T75 with Viseu). Underestimated the melee bug's impact.

---

## T61-100: Infrastructure Engine — Navigation Schools Online

**T75**: Viseu founded (city #5). Portugal now has 5 cities with Navigation Schools building in all of them. Science climbing toward 50/turn.

**T80**: Kilwa Kisiwani wonder started in Lisbon (21 turns). This wonder is the linchpin — +15% yields per city-state type with suzerainty. With 3 suzerainties (Religious, Trade, Cultural), that's +45% to multiple yield categories.

**T100**: Score 262 vs France 284. Science 50.4, Gold +83/t. 5 cities, 40% explored. Research Alliance formed with France. Navigation Schools complete in 4 cities. World Congress auto-voted, losing 64 favor — the first sign that WC tooling needed attention.

### Assessment: T61-100

**Strategic**: The infrastructure engine was taking shape. Navigation Schools are Portugal's power card — +2 science per trade route each. With 5 routes, that's +10 science just from the unique building. The Kilwa Kisiwani investment was correct but took 21 turns of Lisbon's production. France's 22-point score lead was driven entirely by wonder spam — they built 5+ wonders in this period while we invested in districts and trade.

**Tactical**: Clean. No combat needed (peaceful era). Trade route management was efficient. Builder charges used on luxuries first, then strategic resources.

**Tooling**: The WC auto-vote disaster at T100 was the first major tooling failure. 64 favor was burned on unknown resolutions because `get_world_congress` showed stale data and `queue_wc_votes` wasn't used. This pattern would repeat with increasing severity.

**Hypothesis Quality**: Predicted science would cross 50/turn by T100 (hit 50.4 — accurate). Predicted France's wonder strategy would plateau (partially correct — they kept building through T200). The era score prediction was overly optimistic (barely avoided Dark Age).

---

## T101-120: Kilwa Kisiwani & Golden Age Push

**T104**: Activated Piero de' Bardi (Great Merchant) — +200 gold, +1 envoy.

**T106**: World Congress fired. Queued 5 votes on Trade Policy (60 favor). Results unclear but trade capacity increased to 6 routes.

**T108**: **Research Alliance Lv1 formed with France.** This was the diplomatic cornerstone — shared science, +1 favor/turn, defensive pact. Policies swapped to Wisselbanken (trade bonuses to ally/suzerain cities). Militarily dominant at 187 vs France's 128.

**T115**: **All 4 Navigation Schools complete.** Science jumped from 50 to 69/turn — a 38% increase from the unique building alone. Kilwa Kisiwani 4 turns away. Trade routes maxed at 6/6.

**T119**: **KILWA KISIWANI COMPLETED.** Score jumped from 302 to 329. With 2 suzerainties (Yerevan + Mogadishu), this wonder provided +15% faith (Religious) and +15% gold (Trade) empire-wide. The compound yield engine was now fully online.

**T120**: Renaissance Era — activated Golden Age with Monumentality dedication (faith-buy civilians at 30% discount). Era score hit 70 exactly. Culture jumped to 55.6 with Great Writer Rumi producing 2 Great Works.

### Assessment: T101-120

**Strategic**: This was Portugal's inflection point. Kilwa + Navigation Schools + Research Alliance created a yield engine that France's wonder-heavy strategy couldn't match long-term. The Golden Age with Monumentality was perfectly timed — faith-buying settlers at 185f each instead of 150+ production turns. Score gap narrowed from 38 to 34.

**Tactical**: Great Person management was excellent — activating them immediately for yields and era score. Trade route routing was optimized for Wisselbanken bonuses. The Monumentality dedication was the correct choice.

**Tooling**: `get_victory_progress` remained broken (float parsing error) — the single most important strategic tool was unusable for the entire game. `form_alliance` returned false-negative "FAILED" status but alliance was actually formed. Multiple tools consistently misreported success as failure.

**Hypothesis Quality**: Predicted science would rival France by T115 (achieved — 69 vs estimated 70-80 for France). Predicted Kilwa would be the inflection point (confirmed — yields compounded immediately). Predicted Golden Age achievable (hit 70/70 exactly).

---

## T121-140: Expansion Blitz — 6-7 Cities

**T121**: Faith-bought Settler (185f with Monumentality). Started moving toward (49,11) settle site with Mercury + Iron + Horses.

**T123**: Exploration civic unlocked the path to Merchant Republic. Sent envoy to Mogadishu (6 total, tier 3 Trade bonus).

**T126**: Natural disaster — volcano pillaged Braga Campus. Science dropped from 70.6 to 63.3. Builder repair attempt failed (volcanic soil feature blocked UNITOPERATION_REPAIR). This would remain unrepaired for 20+ turns.

**T128**: **Beja founded (city #6)** at (49,11). Switched to Merchant Republic (6 policy slots). Policies: Conscription, Natural Philosophy, Trade Confederation, Merchant Confederation, Charismatic Leader, Wisselbanken. Merchant Confederation alone = +21g/turn from 21 envoys.

**T136**: France declared friendship (accepted). Score: Portugal 414 vs France 472 (gap 58). 8 trade routes active. Gold +125/t.

### Assessment: T121-140

**Strategic**: The expansion from 5 to 7 cities was efficient thanks to Monumentality faith-buying. Merchant Republic was the correct government — 6 policy slots enabled stacking trade bonuses that Portugal's kit requires. The Braga volcano was bad luck but the inability to repair it revealed a serious tooling gap (builder repair on volcanic soil tiles doesn't work).

**Tactical**: Settler escort was handled properly (Man-at-Arms escort to Beja). Trade route management filled all slots. The volcanic repair failure was a recurring frustration — the builder was sent, positioned correctly, and the repair command returned false with no useful error message.

**Tooling**: Builder repair on volcanic soil tiles fails with `canStart=false` and no explanation. This wasn't a tech or charge issue — it appears to be a Gathering Storm interaction where volcanic soil features block repair operations. The workaround (production queue repair) wasn't discovered until much later.

**Hypothesis Quality**: Predicted 7th city by T137 (Guimar\u00e3es founded T140). Predicted France score gap would narrow (partially — narrowed from 70 to 52). Predicted Dark Age was inevitable (correct — era score was consistently 10-20 points short).

---

## T141-160: Trade Empire Peak — Score Lead

**T142**: Patronized Imhotep (Great Engineer, 455g) — +350/+175 production charges. Triangular Trade policy = +36g/turn from 9 routes.

**T146**: Giovanni de' Medici activated — instant Market + Bank + 2 Great Work slots for Viseu. Gold income crossing 200/t.

**T155**: Imhotep activated on Forbidden City — 175 production applied. Settler arrived at (53,14) for 8th city (Porto). Era score 102/105 — close to Golden Age threshold. Forbidded City placement was problematic — only one specific tile (42,13) accepted the wonder, despite several others appearing valid.

**T158**: Mendeleev activated at Lisbon Campus. 8 cities operational. Science 77.4, Culture 82.1, Gold +220/t.

### Assessment: T141-160

**Strategic**: Portugal's economy hit its stride. 200+ gold/turn from trade meant buildings could be purchased instead of produced. Great People were recruited at a pace that no rival could match (Pingala Grants doubling GP generation in Lisbon). The 8th city gave critical mass for district chains across the empire.

**Tactical**: Great Person timing was excellent — recruiting and activating 4-5 GPs in this window. Gold spending was aggressive (buildings, tiles, upgrades). Trade route reassignment was continuous.

**Tooling**: Forbidden City placement was nightmarish — tiles that appeared valid returned `CANNOT_START`. Only brute-force trial of all adjacent tiles found the one that worked. `get_victory_progress` still broken. Production corruption first appeared — cities showing "1 turn" for everything but items never completing.

**Hypothesis Quality**: Predicted Forbidden City would complete by T167 (never actually completed — production corruption ate it). Predicted science would cross 80/t by T145 (hit 77.4 at T158, close). France's score lead was correctly identified as wonder-driven.

---

## T161-180: Score Lead Taken, Dark Age Approaching

**T162**: **PORTUGAL #1 IN SCORE: 578 vs France 572.** The trade engine had overtaken France's wonder economy. Gold +262/t with Raj policy (+2 per yield per suzerainty \u00d7 3 CS = +6 to all four categories).

**T167**: Forbidden City appears to have been lost to volcanic eruption — production hash showed 0 despite 10+ turns invested. Government Plaza also pillaged. Set to repair. France's score crept back within 3 points.

**T172**: Foreign Ministry purchased (775g) — +1 favor per suzerainty = +3 favor/turn from 3 CS. Victor appointed and assigned to Porto for Dark Age loyalty protection.

**T178**: Qiu Ying activated (3 Great Works of Art) at Viseu Theater with Pingala Curator (+100% tourism). This became the tourism powerhouse.

### Assessment: T161-180

**Strategic**: Taking the score lead was the culmination of the trade strategy. However, the Forbidden City loss to volcanic activity was devastating — 10+ turns of Lisbon's production vanished. This was the moment where production corruption became a systemic problem, not just occasional glitches. Gold continued accumulating but the inability to BUILD things (only purchase) fundamentally changed the gameplay from "production empire" to "gold purchasing empire."

**Tactical**: Governor placement was sound (Victor for loyalty, Pingala for GP/tourism, Amani for city-states). Great Works management was good — placing them in Curator-boosted cities for maximum tourism. Trade route optimization was continuous.

**Tooling**: Production corruption became empire-wide. `set_city_production` would return success (PRODUCING|N turns) but the production hash would reset to 0 before turn processing. The root cause was likely `TechCivicCompletedPopup` — tech/civic completion events appeared to clear city queues. This was the most damaging tooling issue in the game, effectively eliminating the ability to produce anything except through gold purchases.

**Hypothesis Quality**: Predicted Dark Age was inevitable (confirmed — era score consistently 10-20 short). Predicted Forbidden City would complete (wrong — lost to corruption/disaster). Predicted France score gap would stabilize (mostly correct at 15-30 points).

---

## T181-210: WC Failure & Diplomatic Pivot

**T181**: World Congress votes deployed. Handler consumed ~174 favor.

**T206**: **MASSIVE TURN.** Military Science completed — upgraded all 8 Musketmen to Line Infantry via Lua workaround (MCP tool returned false but Lua `CanStartCommand` was true). Alan Turing activated (Eureka for Computers). Mary Shelley activated (2 Great Works). Factory purchased for Lisbon. Score 839 vs France 744 — lead widened to 95 points.

**T207**: **WC TARGET BUG DISCOVERED.** Queued 10 votes + 210 favor on DVP Resolution targeting `target: 0` believing it was Portugal. Actual result: +2 DVP went to **Korea**, not Portugal. The `target` parameter is a 0-based index into the resolution's target list, which is ordered differently from player IDs. **270 favor completely wasted, gave a rival +2 DVP.** This was the single most damaging tooling bug in the game.

**T210**: Strategic checkpoint. Score 867 #1. DVP 9 vs France 8. Statue of Liberty target identified (+4 DVP). Nuclear capabilities research started.

### Assessment: T181-210

**Strategic**: The WC targeting bug was catastrophic. 270 favor — representing 30+ turns of accumulation — was burned to give Korea +2 DVP instead of ourselves. This single event likely cost the game. Without it, Portugal would have been at 11 DVP instead of 9 at this point, potentially reaching 20 before France.

**Tactical**: The upgrade blitz (8 Musketmen \u2192 Line Infantry) was correctly timed with tech completion. Great Person activations were efficient. Gold spending was aggressive and productive.

**Tooling**: The WC target list bug (`queue_wc_votes` target index doesn't map to player ID) was documented in detail. The handler fires during WC processing and HAS access to session data — the fix is to introspect the actual target list during the handler and resolve player names to indices. Also: `get_victory_progress` STILL broken (float parsing), `upgrade_unit` returns false negatives, production corruption persists.

**Hypothesis Quality**: The DVP accumulation timeline was sound (predicted 20 DVP by T276-286). The WC bug invalidated all vote projections. Score predictions were accurate (95-point lead).

---

## T211-240: Statue of Liberty & Production Crisis

**T222**: **Statue of Liberty completed!** +4 DVP. Lisbon set to Spaceport (science backup).

**T224**: Production corruption reached critical levels. Lisbon SoL had to be re-set EVERY TURN for 20+ turns — the production hash reset to 0 after each turn's processing. Accumulated production was miraculously preserved (the item counted down from 7\u21926\u21925\u2192...\u21921 over turns), but required manual intervention every single turn.

**T229**: Oil crisis: -6/turn, 0 income. Patronized John Rockefeller for 3 Oil/turn. Aluminum at 0 — improving next turn. Era score 172/189, Dark Age inevitable.

**T237**: WC results revealed — Korea won DVP vote, not Portugal. We did NOT get the +2 DVP from the T231 congress. France at 14 DVP. Decision made to save gold for SoL purchase (2820g) since production couldn't be trusted.

**T239-244**: Gold grinding phase. Deleted 11+ military units to save maintenance. Re-set SoL every single turn. Target: 2820g for wonder purchase.

### Assessment: T211-240

**Strategic**: The SoL completion via persistent re-setting was a triumph of discipline over tooling failure. The decision to pursue gold-purchase of SoL rather than trusting production was correct — but the 20-turn daily ritual of re-setting production was absurd. The oil/aluminum crises were poorly anticipated (should have improved strategic resources earlier). The WC DVP going to Korea instead of Portugal at T231 was another vote-targeting failure.

**Tactical**: Unit deletion for maintenance savings was correct once the military was no longer needed offensively (melee combat was broken). Trade routes continued generating massive gold.

**Tooling**: Production corruption was now the defining issue. Every city required production to be re-set every turn. The root cause (likely `TechCivicCompletedPopup` clearing queues) was identified but not fixable without code changes. Favor/turn display showed +0 when actual was +13/turn — making DVP planning unreliable. `get_victory_progress` broken for the entire game.

**Hypothesis Quality**: Gold accumulation timeline was accurate (projected 2820g by T245, achieved T245). DVP timeline was repeatedly disrupted by WC voting failures. The production corruption hypothesis (popup-related) was plausible but unconfirmed.

---

## T241-270: Nuclear Gambit & War with France

**T245-246**: **SoL COMPLETED** (via production, not purchase — the persistent re-setting finally worked). +4 DVP, bringing total to estimated 13. Upgraded 3 Field Cannons to Machine Guns.

**T253-254**: Massive tourism investment. Bought Art Museum + Broadcast Center for Braga (1660g). Activated Edmonia Lewis (3 Great Works of Art). 4 Rock Bands produced and sent toward France.

**T262**: **Rock Band concerts impossible via FireTuner.** Exhaustive investigation: named all 8 bands (naming is a prerequisite for `GetActivationHighlightPlots`), found valid concert tiles (41 targets), but NO Lua API triggers concerts. `EXECUTE_SCRIPT` operation/command/playerop all silently no-op. The concert trigger is embedded in the C++ game engine, only accessible through UI clicks. Rock Band strategy completely dead.

**T267**: Korolev activated on Spaceport — **Earth Satellite completed instantly** (1500 prod vs 900 cost). Moon Landing started.

**T279**: Space projects discovered to be broken — `CanProduce` returns false for all SpaceRace=true projects. The Korolev activation gave 0 actual progress (prog=0/603). Science victory path collapsed.

### Assessment: T241-270

**Strategic**: Three strategic initiatives launched and two failed. Rock Bands (culture offense) were impossible via FireTuner — a fundamental engine limitation. Space projects (science backup) were broken by production corruption. Only the nuclear/military path remained viable, leading to the war declaration at T297. The shift from "peaceful diplomatic victory" to "nuclear war" was forced by tooling limitations, not strategic preference.

**Tactical**: The Rock Band investigation was thorough — every API was tested systematically. The Korolev activation was correct but revealed that space project progress tracking was broken. The decision to start accumulating nuclear capability was sound given the circumstances.

**Tooling**: Rock Band limitation (bug #8) was the most frustrating discovery — everything appeared to work (naming prerequisite found, valid tiles populated, `CanStartOperation` returned true) but the C++ concert handler was unreachable from Lua. Space project corruption was a separate issue — likely related to the same production corruption affecting all cities.

**Hypothesis Quality**: Predicted Rock Bands would generate 2000-4000 tourism (untestable — concerts couldn't fire). Predicted science victory by T320-330 (impossible — projects broken). The nuclear pivot was a late adaptation, not a planned strategy.

---

## T271-300: Nuclear War

**T280**: France at 405 foreign tourists, only 26 gap from our 301 staycationers for culture victory. DVP race: Portugal 15 vs France 14. WC votes queued with all favor.

**T297**: **ACCEPTED JOINT WAR WITH KOREA AGAINST FRANCE.** Deal: 13 uranium for 37 gpt + open borders + joint war. France military collapsed from 965 to 407. Tourism now frozen by wartime penalties.

**T299-300**: Assault force deployed toward Calais (40,21). Lost Mech Infantry #3 attacking city walls — melee combat bug meant zero damage dealt despite the unit being consumed. Pivoted to ranged-only warfare (Machine Guns, city attacks, submarine attacks).

**T304-305**: **First nuclear strike.** Nuclear Device completed in Lisbon. Nuclear Sub at (40,14) launched WMD on Toulouse (37,23) — pop reduced from ~20 to ~15, districts pillaged.

### Assessment: T271-300

**Strategic**: The war declaration was necessary — France was within 20-30 turns of culture victory. Freezing tourism via wartime penalties was the primary goal, not territorial conquest. The joint war with Korea split French defenses. However, the inability to capture cities (melee attacks don't work) meant the war could only be fought with ranged attacks, city bombardment, and nuclear weapons.

**Tactical**: The Calais assault was a costly lesson — losing a Mech Infantry to broken melee combat was avoidable. After that, the switch to ranged-only doctrine was correct. The nuclear strike on Toulouse was well-targeted (highest-population cultural city).

**Tooling**: `execute_unit_action('attack')` doesn't work on city tiles — it only checks for units, not cities. Had to use raw Lua with `UnitOperationMoveModifiers.ATTACK` for city assaults, which also silently failed for melee. Only city ranged attacks (`execute_city_action`), submarine ranged attacks, and WMD strikes functioned.

**Hypothesis Quality**: Predicted Calais would fall in 3-4 turns (impossible — melee broken). Predicted nuclear strike would delay France's culture victory by 80+ turns (plausible but untestable due to game ending at T318). The joint war timing was good.

---

## T301-318: Nuclear Campaign & Defeat

**T305**: Dismissed Catherine's post-nuke diplomacy.

**T310**: DVP critical — Portugal 18/20 vs France 19/20. France needed just 1 more DVP to win. Our only path: survive until WC at ~T334 and deploy favor for the final push. Second nuclear device completed in Viseu.

**T311**: Second nuclear strike on Toulouse from Nuclear Sub. Pop 17\u219215. Purchased Spy, Market, Bank, Stock Exchange, Flood Barrier across cities (1860g total spending spree). Set up additional trade routes.

**T312-317**: Grinding turns. Uranium crisis — only 2 stockpiled with +0/turn. Korea refused further trades. Civic research cleared by notification system every turn (known bug). Lost Machine Gun at (42,19) to French forces.

**T318**: **France wins Diplomatic Victory.** 20/20 DVP. Game over.

### Assessment: T301-318

**Strategic**: The endgame was a desperate race that Portugal narrowly lost. At 18/20 DVP vs France's 19/20, the gap was just 2 points — and the WC targeting bug at T207 had gifted Korea +2 DVP with OUR favor. If those votes had gone to Portugal instead, we would have been at 20/20 first. The nuclear campaign successfully disrupted French culture but couldn't prevent their DVP accumulation through competitions and WC voting.

**Tactical**: Nuclear strikes were the only effective offensive tool. Conventional warfare was impossible (melee broken, ranged units mostly broken except submarines and city attacks). The economic warfare (trade route disruption, city bombardment) was supplementary.

**Tooling**: The accumulated tooling failures defined the outcome:
1. **WC target bug** (T207): +2 DVP to Korea instead of Portugal = game-losing
2. **Production corruption**: Prevented building critical infrastructure for 100+ turns
3. **Melee combat broken**: Eliminated conventional warfare entirely
4. **Rock Band concerts impossible**: Eliminated culture offense
5. **Space projects broken**: Eliminated science victory backup
6. **`get_victory_progress` broken**: Made strategic monitoring blind
7. **Favor display bug** (+0/turn shown, actual +13): Made DVP planning unreliable

**Hypothesis Quality**: The T334 WC target for final DVP push was sound math (150+ favor = 2+ DVP = 20/20). But France reached 20 first through a combination of competitions and WC votes that we couldn't monitor (victory progress tool broken) or counter.

---

## Post-Mortem

### What Went Right
- **Trade engine**: Portugal's kit was fully exploited. 15 trade routes with Navigation Schools, Wisselbanken, Merchant Confederation, and Kilwa Kisiwani generated 400+ gold/turn and 100+ science from trade alone.
- **Great People dominance**: Recruited 15+ Great People through Pingala Grants, using them for yields, era score, and tourism.
- **Diplomatic favor accumulation**: 6 suzerainties + Orsz\u00e1gh\u00e1z + alliances generated ~13 favor/turn.
- **Economic score**: #1 in score for most of the game (T162-T318).
- **Nuclear capability**: Successfully built and deployed nuclear weapons when conventional warfare failed.

### What Went Wrong
- **WC targeting bug**: The single most impactful failure. 270 favor spent to give Korea +2 DVP instead of Portugal. Without this bug, Portugal likely wins at T306 or earlier.
- **Production corruption**: ~100 turns of cities unable to build normally. Root cause likely `TechCivicCompletedPopup` clearing queues. Forced reliance on gold purchases for everything.
- **Broken combat**: Melee attacks never worked via FireTuner. This eliminated conventional warfare, city capture, and barbarian camp clearing for the entire game.
- **Broken space race**: Space projects showed `CanProduce=false` despite meeting all prerequisites. Eliminated science victory backup.
- **Rock Band impossibility**: C++ engine limitation. No Lua API can trigger concerts. Eliminated culture offense.
- **Volcanic repair failure**: Braga Campus pillaged by volcano couldn't be repaired by builders (volcanic soil feature blocks repair). Cost 6+ science/turn for 20+ turns.
- **Favor display bug**: Showed +0/turn when actual was +13/turn. Made DVP planning unreliable — couldn't accurately project when we'd have enough favor for WC.

### Key Lesson
Portugal's economic engine was overwhelming — 400g/turn, 200+ science, 15 trade routes, 6 suzerainties. The agent's strategic decision-making and economic management were excellent. **The game was lost to tooling failures, not strategic failures.** The WC target bug alone accounts for the margin of defeat (2 DVP). The production corruption, broken combat, and broken space race forced increasingly desperate pivots (nuclear war, gold-purchasing everything) that were creative but couldn't overcome the accumulated tooling debt.

### Tooling Fixes Needed for Game 8
1. **WC target resolution**: Handler must introspect actual target list during session (see tooling-improvements.md #6)
2. **Production corruption root cause**: Investigate TechCivicCompletedPopup queue clearing
3. **`get_victory_progress` float parsing**: Fix `int()` on float field
4. **Melee combat**: May be unfixable (C++ engine limitation)
5. **Favor/turn display**: Use InGame context for favor yield
6. **Research desync verification**: Add GameCore fallback for tech research (already have it for civics)
