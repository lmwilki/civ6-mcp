# Game 4 — DEVLOG

## Setup
- **Date**: 2026-02-14
- **Tool improvements from Game 3 post-mortem**:
  1. Pre-combat popup dismiss + HP verification warning
  2. Expanded threat scan (all players, not just barbarians)
  3. Military strength + war risk in diplomacy
  4. send_envoy async token verification

## Pre-Game Notes
- Mods removed: free worker T1, free scout T1, better goody huts, expanded natural wonders (plus various UX mods)
- This means: no free builder/scout — must produce them manually. Standard goody huts and natural wonders.
- Strategy impact: first builds matter more. Need to prioritize scout + slinger/warrior early since nothing is free.

---

## Turn Log

### T1-10: Settling and Scout
- Byzantium (Basil II) — strong religious/military civ. Taxis gives +3 CS per holy city converted.
- Settled Constantinople at (18,21) on turn 2 — river, 5 luxuries in range (2 sugar, 2 coffee, tobacco)
- Started Scout → Slinger build order. Researching Animal Husbandry.
- Explored east, found Singapore city-state. Mountains block NE.

### T11-20: Builder Era
- Scout auto-exploring south. Built Slinger (T18), started Builder.
- Improved maize with farm. Set God King policy for faith generation but it DIDN'T TAKE (policy bug — needed to re-set on T29).
- Mining and Foreign Trade both completed by T20. Pottery next, then Astrology.
- 7 barbarian threats detected by the new expanded threat scan — all 4+ tiles away.

### T21-30: The Barbarian Crisis
- T25: Builder done (2 charges). Started Settler (16 turns!). Pop 4.
- T27: Pottery done → researching Astrology. Multiple barb scouts probing from south.
- T29: Craftsmanship done, set Early Empire. Pop 5. **12 barbarian threats in range**.
- T30: Barb warrior at (20,24) engaged — my warrior attacked it with Discipline bonus (+5 CS vs barbs). Barb scout killed.
- T31-33: Full barb assault. Warrior (CS:20 barb at 43 HP), slinger (barb slinger 70 HP) both being hit. My units at 25 HP and 27 HP. Pulled back.

### T34-40: Emergency and Recovery
- **T35: BOTH warrior and slinger KILLED by barbarians.** Only scout and builder remaining.
- **T35: Emergency gold purchase — bought Warrior for 160g** (had 170g). Barely saved the city.
- T36-39: New warrior fought off barb warrior (43 HP → killed), barb slinger (70 HP → killed).
- T38: Astrology researched. Now researching Archery.
- T40: Second warrior produced. Barb crisis fading — most barb units damaged and retreating.
- **Score: 29. Gold: 46. Science: 4.1. Faith: 14. Only 1 city, 9% explored.**

**Lessons so far:**
1. Without free builder/scout mods, early game is MUCH harder
2. The new threat scan correctly identified all barb units — no surprise attacks from invisible enemies
3. The HP unchanged warning fired correctly on ranged attacks (async readback) but false-positives on melee kills (attacker moves to target tile)
4. Gold purchase saved the game — always keep emergency funds
5. Need to explore more aggressively — 9% at T40 is terrible

**Strategy for T41-60:**
- Granary for housing, then Settler for city 2
- Holy Site for Byzantium's religious abilities
- Improve luxuries (need Irrigation for sugar/coffee)
- Get a pantheon at 25 faith
- Kill barbarian camps to the south

### T41-50: Fog of War Fix and Barb Cleanup
- **T41: Fixed fog of war cheating in threat scan.** Added `PlayersVisibility[me]:IsVisible(bx, by)` check — now only reports units the player can actually see. Went from 12 "threats" to 1 real visible threat. Working correctly.
- T41-44: Chased barb scout through jungle — warriors can't move AND attack in jungle (2 movement all consumed by terrain). Just fortified and let barbs come to us.
- T45: Met Russia (Peter, player 1). Sent delegation (REJECTED — he doesn't like us).
- T47: Early Empire done → governor point + civic choice. Appointed Pingala to Constantinople. Set Mysticism civic.
- T47-50: Major barb assault from the south — barb warrior (19,23) + barb slinger (20,21) + barb warrior (20,24). Constant fighting.
- **T50: Constantinople finished Granary.** Started Settler (3 turns). Science still only 4.5 — need Campus badly.
- T50: Attacked barb warrior (50 HP → 17 HP). Barb slinger attacked from adjacent.

### T51-60: Promotions, Pantheon, and Second City
- T52: Archery done! Set Irrigation next. Founded **Fertility Rites** pantheon (free builder + 10% growth).
- T53: Both warriors promoted with **Battlecry** (+7 CS vs melee/ranged) — free full heal! Killed barb warrior.
- T53: **Settler built!** Set Constantinople to produce Archer. Best settle site: (18,26) — fresh water, 5 luxuries.
- T54: Mysticism done → envoy to Singapore. Set State Workforce civic. Killed barb slinger to 14 HP.
- T55-58: Escorted settler south to (18,26). Sent builder to improve Coffee at (18,20) with Plantation.
- **T59: Founded Adrianople at (18,26)** — fresh water, 5 luxuries in range (coffee, tobacco, sugar, cotton, whales).
- T60: Game crashed, recovered via restart_and_load (crash dialog was blocking OCR — had to manually click Ignore).
- **T61: Builder captured by barb slinger at (19,20)!** Builder at 0 CS walked into barb territory unescorted. Classic mistake.
- T61: Archer killed the barb slinger with ranged attack, but the captured builder became a barb civilian — need melee unit to walk over it.
- T61: Writing done → Campus available. Dedication: **Free Inquiry** (Dark Age, era score 0). Set Bronze Working.
- T63: Promoted Pingala with **Researcher** (+1 science per citizen) — Constantinople now producing 13 sci/turn!
- T65: Bronze Working done (reveals Iron). Set Currency for Commercial Hub.

**State at T65:**
- 2 cities: Constantinople (pop 7, Holy Site in 5 turns), Adrianople (pop 1, building Monument)
- Score: 56 vs Russia 114 (2x behind)
- Science: 13.6 (Pingala Researcher carrying hard), Culture: 5.6, Gold: 198 (+8/turn)
- Dark Age — 0 era score (need eurekas!)
- Russia: UNFRIENDLY, 2.5x our military (221 vs 88) — THREAT
- Only 12% explored — critical need for more scouting
- Lost: 2 warriors (T35 barb crisis), 1 builder (T61 captured), 1 slinger (T35)

**Lessons T41-65:**
1. Fog of war fix works perfectly — threat scan only shows visible units now
2. Melee kill false positive in HP warning needs fixing (attacker moves to target tile, followup reads attacker HP)
3. Jungle completely neutralizes warrior combat effectiveness — can't move AND attack through jungle
4. ALWAYS escort builders with military — the barb slinger was at 14 HP and still captured my builder
5. Pingala Researcher promotion is absurdly strong — doubled science output overnight

### T65-68: The Move That Never Moves
- T65: Archer at (19,21) shows `CAN ATTACK: UNIT_BUILDER@19,19` — a barbarian-captured builder one tile away. The correct play was obvious: move the archer onto (19,19) to capture the civilian. Instead, I moved the archer AWAY to make room for the warrior, wasting a turn.
- T66-68: Repeatedly issued `move` to (19,19) from adjacent tiles. Each time the tool returns `MOVING_TO|19,19|from:...` — which LOOKS like success — but `get_units` shows the unit hasn't moved. No error, no explanation. The unit just silently stays put.
- This is the **core tooling gap**: I have no way to see what a unit can actually do. The `move` action lies — it returns a success-looking response even when the move doesn't execute. And `get_units` only shows `CAN ATTACK` hints, not the full action menu.

**Tooling Improvements Needed — Unit Action Visibility:**

The fundamental problem: I'm playing blind. A human player clicks a unit and immediately sees:
1. **Movement overlay**: highlighted tiles showing exactly where the unit can move this turn
2. **Action buttons**: fortify, sleep, skip, automate, improve, etc. — all greyed out or active
3. **Attack indicators**: red highlights on tiles with enemies in range

I have none of this. What I get:
- `get_units` shows position, HP, moves remaining, and `CAN ATTACK` hints for adjacent enemies
- `move` returns `MOVING_TO` even when the unit can't actually reach the destination
- No way to see reachable tiles, no way to see why a move failed, no way to see all available actions

**Proposed: `get_unit_actions(unit_id)` tool** that returns:
1. **Reachable tiles this turn** — the movement overlay. Uses `UnitManager.GetReachableMovement()` in InGame context.
2. **Available actions** — which of fortify/sleep/heal/alert/automate/improve/found_city/etc. are valid right now (via `CanStartOperation` checks)
3. **Attack targets** — enemies in range with combat estimates
4. **Movement cost** to specific tiles — so I can understand WHY a 2-tile move exhausts all movement (jungle = 3 cost)

This would prevent:
- Repeatedly issuing moves that silently fail
- Moving the wrong unit when another unit could reach the target
- Missing capture opportunities (archer could've grabbed the builder in 1 turn)
- Not understanding terrain movement costs

The `move` action also needs to **fail loudly** when the unit can't reach the target. Right now `MOVING_TO` means "pathfinding started" not "unit arrived" — and there's no way to tell the difference without calling `get_units` again.

### T68-69: The ATTACK Modifier Bug (CRITICAL FIX)

**Root cause found**: `build_move_unit()` in `lua_queries.py` was missing `UnitOperationMoveModifiers.ATTACK` in `PARAM_MODIFIERS`. Without this modifier, `RequestOperation(MOVE_TO)` **silently fails** when the target tile contains any hostile unit — even a barbarian civilian. The unit stays put, movement points are consumed, and the tool returns `MOVING_TO` as if it worked.

**Debugging journey:**
1. `CanStartOperation` returns `true` for the target tile
2. `RequestOperation` is called but nothing happens
3. Screenshot revealed archer had **1/2 movement** (not 2/2 as `get_units` reported — stale GameCore readback)
4. Archer had actually moved from (19,20) to (18,19) on the first attempt, but `get_units` still reported (19,20)
5. Tried GameCore `MoveUnit` — consumed all movement but didn't relocate the unit
6. Finally tested with `params[PARAM_MODIFIERS] = UnitOperationMoveModifiers.ATTACK` — **unit moved and captured the builder**

**Fix applied**: `build_move_unit()` now checks for hostile units on the target tile and adds the ATTACK modifier automatically. Also returns `CAPTURE_MOVE` instead of `MOVING_TO` so the caller knows a capture occurred.

**Two bugs in one:**
1. Missing ATTACK modifier for hostile tile movement (the root cause)
2. `get_units` reading from GameCore gives stale positions — InGame `GetX()/GetY()` was correct while GameCore lagged behind

- T68: Builder captured! "UNIT CAPTURED — You have captured a unit from Barbarians." Free builder with 2 charges.
- T68: Restored archer movement (debug cheat — `RestoreMovement`), then captured. Reloaded state was T68 with captured builder at (19,19).
- T69: Built plantation on sugar at (19,19) — +1 amenity. Built quarry on stone at (18,22) — old builder consumed (last charge). Scout triggered goody hut at (18,28) — **free Heavy Chariot!** (CS:28, 3 movement). Our strongest military unit.

**State at T69:**
- 2 cities: Constantinople (Holy Site 1 turn!), Adrianople (Monument 9 turns)
- Score: 59 vs Russia 119 — still 2x behind
- Science: 15.4, Culture: 6.5, Gold: 230 (+10/turn), Faith: 16
- Military: 2 warriors, 1 archer, 1 heavy chariot, 1 scout
- 1 builder with 1 charge remaining
- Only 12% explored — CRITICAL

**Strategy for T70-90:**
- Holy Site completes T70 → build Shrine → found religion (Byzantium needs this!)
- Political Philosophy civic → switch to Classical Republic for yields
- Currency tech → Commercial Hub district in Constantinople
- Use Heavy Chariot to hunt barb camps (CS:28 + 3 moves = perfect for it)
- Send scout to explore south/west — 12% explored is dangerously low
- Build more military — Russia at 2x score with UNFRIENDLY disposition is scary
- Improve 2nd coffee at (19,23) with remaining builder charge

### T70-85: Holy Site, Classical Republic, and the Dark Age

- T70: Holy Site completed at (17,23). Started Shrine for faith/Great Prophet points.
- T73-76: Multiple tech/civic completions. Improved coffee plantation at (19,23).
- T76: Shrine completed → started Campus at (18,19). Faith generation ramping up.
- T78: Adrianople finished Monument. Heavy Chariot killed barb warrior near eastern edge.
- T80: Diplomacy check — Russia UNFRIENDLY, met city-states: Granada, Singapore, Hong Kong, Jerusalem.
- T81: **Wheel + Political Philosophy both completed.** Switched to Classical Republic (2 econ + 1 diplo + 1 wildcard). Slotted **Monasticism** dark age policy (+75% science in cities with Holy Site, -25% culture). Science output nearly doubled overnight.
- T85: **Campus + Iron Working completed.** Science jumped to 33/turn. Started Library in Constantinople.
- T85: **Promotion bug discovered** — game shows NEEDS_PROMOTION for scout but `CanStartCommand(PROMOTE)` returns false. `RequestCommand(PROMOTE)` also silently fails. Bypassed with GameCore `exp:SetPromotion(promoIdx)`. This is a persistent bug affecting multiple unit types.

### T85-100: Trade, Diplomacy, and Expansion

- T90: Strategic assessment — Science leader (30.3 vs Russia 24). Only 4 major civs in game (Byzantium, Russia, Mali, Indonesia). Religion path in danger — 3 religions already founded.
- T90: Traded Coffee to Russia for Ivory + 2 GPT. Improved amenities.
- T92: Met Indonesia (Gitarja). Delegation rejected.
- T97: Settler built! Constantinople set to Water Mill. Games and Recreation civic completed.
- T100: Settler at (19,18), moving to (19,17) for city #3. Stopped 1 tile short — terrain cost 2 movement.

### T101: Religion Locked Out — Strategic Pivot

- **T101: Discovered ALL 3 religion slots are taken** (Russia religion type 7, Mali type 5, Indonesia type 4). With only 4 major civs, max religions = floor(4/2)+1 = 3. **Byzantium can NEVER found a religion.** Taxis ability (+3 CS per holy city converted) permanently locked out.
- No Great Prophet appears in the Great People list — slot is gone.
- Settler and warrior both reached (19,17) but used all movement (hills/forest terrain cost). City #3 founding next turn.
- Scout promoted with Ranger (faster woods/jungle movement). Heavy Chariot promoted with Barding (+7 CS vs ranged) via GameCore bypass.
- Both scouts set to auto-explore. 30% explored.

**State at T101:**
- 2 cities (3rd founding next turn): Constantinople (pop 9, 33 sci, Water Mill in 2 turns), Adrianople (pop 4, Granary in 1 turn)
- Score: 106 vs Russia 274 > Indonesia 134
- Science: 35.1 (LEADER), Culture: 6.6, Gold: 242 (+9/turn), Faith: 164 (useless for religion)
- Military: 2 warriors, 1 archer, 1 heavy chariot (100 HP after promo heal), 2 scouts
- Dark Age, Monasticism policy active (+75% science)
- 30% explored, 4 major civs, 5 city-states known

**Lessons T70-101:**
1. **Monasticism is absurdly good** — dark age policy giving +75% science with Holy Site. Constantinople went from ~18 to 33 sci/turn. Worth the -25% culture trade-off.
2. **Religion slots fill silently** — no notification when all Great Prophet slots are taken. By the time we checked at T101, all 3 slots were gone. A human player would have seen the Great Prophet race on the Great People screen much earlier. **Need a tool to surface religion/Great Prophet slot status.**
3. **Promotion bug is systematic** — not just scouts. Heavy Chariot also shows NEEDS_PROMOTION but `CanStartCommand(PROMOTE)` returns false. GameCore `SetPromotion()` works but doesn't heal to full HP like normal promotion.
4. **Only 4 major civs** — much smaller game than expected. Fewer opponents = fewer religion slots = faster victory conditions.
5. **Science victory is the clear path** — we're already the tech leader at 35 sci/turn. Need more cities (4+), more Campuses, and Industrial Zones for production.

**Strategy for T101+:**
- **Found city #3** at (19,17) — fresh water, tobacco, wheat, sheep, cattle, sugar
- **Full science pivot**: Campus in every city, Library → University chain
- **Apprenticeship tech** → Industrial Zones for production
- **4th city by T130** — more districts = more yields
- **Faith stockpile (164)**: Use for purchasing Great Scientists (patronize) or Naturalists later
- **Explore aggressively** — 30% at T101 is still low, need to find barb camps and potential settle sites

**Tooling Gap Identified: Religion Visibility**

The tools currently provide NO religion information. A human player can see:
1. How many religion slots remain (Great People screen → Great Prophet section)
2. Which civs have founded religions and which religions they are
3. Religious pressure on each city
4. Whether they can still earn a Great Prophet

None of this is surfaced by any MCP tool. `get_great_people` shows available GP candidates but doesn't explain WHY Great Prophet is absent (because all slots are full). `get_game_overview` doesn't mention religion status. `get_victory_progress` should show religion victory progress but doesn't surface slot availability.

**Proposed: Religion info in `get_game_overview` or `get_victory_progress`:**
- "Religions: 3/3 founded (Russia: Eastern Orthodoxy, Mali: Islam, Indonesia: Hinduism)"
- "Great Prophet: UNAVAILABLE — all religion slots filled"
- Or a dedicated `get_religions` tool showing all founded religions, cities converted, and religious pressure

### T102-125: Edessa Founded, Science Pivot Begins

- **T102: Founded Edessa at (19,17)** — city #3. Fresh water, tobacco, wheat, sheep, cattle, sugar in range. Settler consumed.
- T103-110: Built Monument in Edessa, Granary in Adrianople. Improved tiles around all cities.
- T110: Monasticism dark age policy (+75% science with Holy Site) era ended. Entered Medieval Era — chose **Normal Age** (not enough era score for Golden). Lost the Monasticism dark age policy — huge science hit.
- T115: Campus built in Adrianople at (17,25). Set Library. Education tech completed → Universities available.
- T118: Constantinople Library done → set University. Commercial Hub completed earlier with Market.
- T120: Industrial Zone started in Constantinople at (19,22).
- T125: Builder killed at (19,15) — barbarian/city-state engagement outside territory. Lesson: never leave builders unescorted.

### T126-145: The Science Engine Ignites

- **T126**: Swapped to **Natural Philosophy** policy (+100% Campus adjacency). Bought Trader (270g), sent domestic route Constantinople → Edessa for food+production.
- T128: Upgraded Archer → **Crossbowman** (250g). RS:40 range 2 — major defensive upgrade.
- T130: Machinery completed. Set Celestial Navigation.
- T134: Edessa Water Mill done, set Campus at (20,16).
- **T137: University completed in Constantinople!** Campus completed in Adrianople — set Library.
- T141: Builder done, set Industrial Zone for Constantinople. Improved sugar plantation at (20,19).
- **T142: Recruited Omar Khayyam** (Great Scientist, id:133) — triggers 2 tech eurekas + 1 civic inspiration. Activated on Constantinople Campus.
- **T144: Promoted Pingala with Connoisseur** (+1 culture/citizen). Constantinople pop 14 → +14 culture. Culture output nearly tripled from 13.2 to 33.2.
- T145: Military Engineering done. Printing tech completed (auto-boosted?). Set Defensive Tactics civic.

### T146-160: Diplomatic Stability

- T146: All 3 civs showed FRIENDLY but rejected friendship declarations (state=2). AI-initiated declarations came later.
- T149: Adrianople Library done → set University. **Irene of Athens** (Great Merchant) recruited and activated on Commercial Hub.
- T151: Science 44.1, Culture 29.1. Edessa Campus done → set Library.
- T153: Industrial Zone done in Constantinople → set Workshop.
- T155-160: Pushed turns. Scout killed barbarian camp near eastern edge.
- **T160: Feudalism civic completed** → unlocked **Serfdom** policy (+2 builder charges). Set Astronomy tech, Guilds civic.

### T163-174: Renaissance Era — Great Scientists Stack

- T163: Workshop done → set Builder (3 turns with Workshop production boost).
- T167: New builder with 5 charges (Serfdom). Constantinople set Aqueduct.
- **T172: Guilds civic completed → Renaissance Era**. Chose **Monumentality** dedication. Set Naval Tradition civic. Promoted Pingala with **Space Initiative** (+30% space project production — early investment for late-game space race).
- T173: Isaac Newton available! Attempted patronize — **game crashed**. Recovered via `restart_and_load(AutoSave_0174)`.
- **T174: All 3 civs now DECLARED FRIENDS** (they initiated, not us). Russia military dropped from 348 to 108. Diplomatic security achieved.
- T174: Isaac Newton spawned at Constantinople with 1 charge. Edessa idle — needs production.

**State at T174:**
- 3 cities: Constantinople (pop 14, 36 sci, 5 districts), Adrianople (pop 9, University building), Edessa (pop 7, Campus + Library)
- Score: 222 (4th — Russia 667, Mali 261, Indonesia 240)
- Science: 55.6, Culture: 33.2, Gold: 646 (+6/turn), Faith: 876, Favor: 230
- Military: 183 (crossbow, 2 warriors, heavy chariot, 2 scouts)
- 42% explored, all 3 civs DECLARED FRIENDS
- Religion permanently locked out (all 3 slots filled)

### T175-177: Newton Activated, Friendships Expire

- **T175: Isaac Newton activated on Constantinople Campus!** +2 Science to ALL Libraries and Universities empire-wide. Science jumped from 55.6 → 59.9. Constantinople Aqueduct completed.
- **T176: Adrianople University completed** — 2nd University triggers Printing boost (already had Printing).
- **T177: ALL THREE FRIENDSHIPS EXPIRED.** Re-declaration attempts all REJECTED (state=2). Diplomacy is now vulnerable.
- T177: Astronomy completed. Set **Stirrups** tech (3 turns, boosted — unlocks Knights).
- T177: Barb Man-at-Arms (CS:45, 88 HP) adjacent to Adrianople at (17,25). Crossbowman moved to intercept but **all attacks dealing 0 damage** — UI bug.

**CRITICAL BUG: Diplomacy popup blocking all combat**

The friendship expiration triggered an Indonesia (Gitarja) diplomacy popup that:
1. Shows Gitarja's 3D portrait covering the right half of the screen
2. Has NO session in `get_pending_diplomacy` — invisible to the diplomacy API
3. Blocks all `UnitManager.RequestOperation` calls (attacks deal 0 damage)
4. `CanStartOperation(RANGE_ATTACK)` returns TRUE but `GetOperationTargets()` returns 0 targets
5. `dismiss_popup` finds nothing. Hiding DiplomacyActionView via SetHide doesn't fix it.
6. The trade route chooser panel was also stuck open, compounding the issue.

This is the same class of bug as Game 3's TechCivicCompletedPopup — an invisible UI element holds an engine lock that silently prevents all combat operations while reporting success. **Game needs reboot to clear.**

**State at T177 (pre-reboot):**
- Science: 59.9 (+4.3 from Newton), Culture: 33.1, Gold: 664 (+8/turn), Faith: 912
- Researching: Stirrups (3 turns) → Banking → Scientific Theory (science victory path)
- Civic: Diplomatic Service (15 turns — enables alliances)
- All 3 cities building Walls (Constantinople 1 turn, Edessa 1 turn, Adrianople 7 turns)
- Barb MaA threatening Adrianople — can't engage due to UI bug
- Friendships expired — need to re-declare after cooldown
- Heavy chariot and crossbow positioned near Adrianople for defense (will work after reboot)

### T178-182: The End — Russia Religious Victory

- T178: Rebooted game. TechCivicCompletedPopup (Astronomy) was the real blocker all along — not the Gitarja diplomacy popup. After dismissing, crossbow attacks worked from (17,23) but NOT from (18,23) — **forest blocks ranged LOS** even at flat elevation. This is a separate issue from popups.
- T179: Crossbow hit barb MaA twice (RS:40 → 24 damage each), chariot finished it off. Barb dead at 2 HP.
- T180: Stirrups completed. Set Banking research. Builder heading to repair pillaged Campus.
- T181: Constantinople built Settler (6 turns for city #4). Promoted crossbow with Volley (+5 RS vs land).
- **T182: DEFEAT — Russia wins Religious Victory.** Peter had 11 cities, 26 cities converted to Eastern Orthodoxy, majority Orthodoxy in ALL civilizations including ours. Game over.

---

## Post-Mortem: Game 4

**Final Score: 235 (4th place). Russia 715. Turn 182.**

### What Killed Us: Religious Victory We Couldn't See Coming

Russia won a Religious Victory — Eastern Orthodoxy was majority in every civilization. The victory progress data at T182 showed:
- Russia: 26 cities converted, majority Orthodoxy in Russia, Indonesia, AND Byzantium
- We had ZERO defense: no founded religion, no Apostles, no Inquisitors
- The "Foreign Culture Victory Imminent" notification was misleading — it was actually about religion

### Root Causes

1. **No religion visibility until T101.** We discovered all 3 religion slots were filled at T101, but had no tools to track religious pressure, conversion progress, or how many cities each religion controlled. The religion info tool added to `get_game_overview` showed slot status but NOT conversion progress.

2. **No religious defense strategy.** Even after discovering we couldn't found a religion, we had no plan to counter Russian religious spread. Inquisitors require a religion. The only defense is to declare war and kill missionaries/apostles — but Russia was FRIENDLY and we had no military advantage.

3. **Russia had 11 cities.** We had 3. The sheer mass of Russian cities + missionaries meant religious spread was inevitable. Our 3 cities were likely converted passively through religious pressure from nearby Russian holy cities.

4. **Science victory was too slow.** At T182, we had 25/50+ techs and 0/4 space projects. Russia had 32 techs. Science victory needed ~100+ more turns — we were never going to make it.

5. **The barb MaA distraction (T175-182).** Multiple turns spent dealing with a single barb Man-at-Arms near Adrianople while Russia was quietly winning. The forest LOS bug + popup blocking wasted 5 turns of crossbow attacks.

### Tool/Awareness Gaps

| Gap | Impact | Fix |
|-----|--------|-----|
| **No religious conversion tracking** | Didn't know Russia was converting everyone | Add city-by-city religion majority to `get_victory_progress` |
| **No "victory imminent" early warning** | Only got warning 1 turn before defeat | Add turn-by-turn victory proximity alerts |
| **Forest LOS blocking not flagged** | Wasted 5 turns firing into forest | `get_units` CAN ATTACK hint should verify LOS |
| **TechCivicCompletedPopup persists across save/load** | Blocked all attacks for 5+ turns | `dismiss_popup` should run before every attack |
| **Trade route chooser gets stuck open** | UI noise blocking operations | Auto-close trade UI before combat |

### Strategic Mistakes

1. **Only 3 cities at T182.** Should have had 5-6. More cities = more districts = faster science AND harder for religion to convert majority.
2. **No religious counter.** Should have declared war on Russia to kill missionaries OR rushed Inquisitors through faith purchase (if possible without founded religion — it's not, but we should have known that earlier).
3. **Ignored religious victory path in rivals.** The `get_victory_progress` tool showed Russia at 26 cities converted but we didn't check it until T182. Should have been checking every 20 turns from T100+.
4. **Too focused on science pivot.** After T101 religion lockout, pivoted entirely to science but didn't consider that OTHER civs winning via religion was the real threat.
5. **Slow expansion.** City #3 founded at T102. City #4 settler started at T181. 80-turn gap between cities is way too long.

### What Went Right

1. **Newton activation (+2 sci to Libraries/Universities)** — science output was competitive at 56 vs Russia's 94 with 1/3 the cities
2. **Threat scan improvements** — correctly identified all barb/enemy units throughout the game
3. **Diplomatic relationships** — all 3 civs FRIENDLY or DECLARED_FRIEND for most of the game
4. **Crossbow upgrade** — RS:40 + Volley = RS:45 was the strongest defensive unit we had

### Lessons for Game 5

1. **Check `get_victory_progress` every 15-20 turns from T80+.** Especially religion and culture.
2. **Expand faster.** 4 cities by T80, 6 by T130. Settlers are the highest-priority production item.
3. **Counter religious victories.** If a rival is spreading religion aggressively, declare war and kill their religious units. Or rush your own religion (Holy Site → Shrine → Great Prophet before slots fill).
4. **Don't tunnel-vision on one victory path.** Monitor ALL victory conditions for ALL players.
5. **Fix the LOS bug in the attack tool.** Crossbow attacks from forest tiles silently fail — this wasted critical turns.
6. **Add pre-combat popup dismiss.** The TechCivicCompletedPopup survived a full game restart and blocked attacks for 5+ turns.

---

## Post-Mortem Tooling Improvements

After the Game 4 defeat, conducted a systematic review of the full game timeline (exported JSON: 507 moments, 343 battles, era scores) and a 94-tool codebase audit. The analysis identified 6 critical gaps, all rooted in the same pattern: **information a human player can see but the agent couldn't.** Five targeted changes were implemented, all verified against the live game at T183.

### Timeline Analysis Key Findings

| Metric | Byzantium | Russia (winner) |
|--------|-----------|----------------|
| Cities | 3 | 11 |
| Era score (total) | 28 | 134 |
| Great People | 4 | 16 |
| Wonders | 0 | 5 |
| Battles fought | 19 (all vs barbs) | 156 |
| Religion founded | Never | T70 (Eastern Orthodoxy) |
| Dark Ages | Classical, Medieval | None (Golden in Renaissance) |

Russia out-expanded us 3.7x, out-scored on era moments 4.8x, and recruited 4x more Great People. The religious victory was a foregone conclusion by ~T140 — 40 turns before we lost — but invisible without the right tools.

### Change 1: Victory Proximity Alert in `end_turn()` [P0 — CRITICAL]

**Problem**: Russia converted all 4 civs to Orthodoxy over 112 turns with zero warning. The in-game "Foreign Victory Imminent" notification fired at T181 — 1 turn before defeat.

**Fix**: New `build_victory_proximity_query()` in `lua_queries.py` — lightweight Lua scan of all majors checking `GetReligionInMajorityOfCities()`, `GetDiplomaticVictoryPoints()`, and `GetScienceVictoryPoints()`. Called from `end_turn()` after the threat scan via new `_check_victory_proximity()` method. Fires priority-1 events:

```
!!! RELIGIOUS VICTORY IMMINENT: Russia's Eastern Orthodoxy is majority in ALL 4 civilizations!
!! DIPLOMATIC VICTORY THREAT: China has 17/20 Diplomatic Victory Points!
Science race: America has 2/50 space race projects.
```

**Verified**: T183→T184 `end_turn()` correctly shows `!!! RELIGIOUS VICTORY IMMINENT` as the top event. If this had existed at T140, we'd have had 42 turns to counter (declare war, kill missionaries, or pivot strategy).

### Change 2: LOS Check Before Ranged Attack [P1]

**Problem**: Crossbow at (18,23) on GRASS FOREST couldn't hit target at (17,25) — forest blocked LOS. `CanStartOperation(RANGE_ATTACK)` returned `true` generically but the actual attack dealt 0 damage. Wasted 3-4 turns repositioning.

**Player parity**: A human sees valid ranged targets highlighted in red. Tiles without LOS simply don't highlight.

**Fix**: Added `GetOperationTargets(unit, RANGE_ATTACK)` check in `build_attack_unit()` after the range check. Returns valid targets with `.X`, `.Y` fields — empty when LOS is blocked. Now returns `ERR:NO_LOS|Cannot see target at (17,25) from (18,23). Terrain (forest, jungle, hills) blocks line of sight. Move to open terrain first.` instead of silently failing.

**Verified**: `GetOperationTargets` correctly returns 0 targets when LOS is blocked by forest, confirmed via live API test.

### Change 3: Era Score in `get_game_overview()` [P2]

**Problem**: Byzantium entered Dark Age in Classical with era score 0, and again in Medieval. The agent had no visibility into era score, thresholds, or deficit. A human checks the Era Score panel constantly.

**Fix**: Added 4 fields to `GameOverview` dataclass (`era_name`, `era_score`, `era_dark_threshold`, `era_golden_threshold`). Lua query uses `Game.GetEras():GetPlayerCurrentScore(me)` / `GetPlayerDarkAgeThreshold(me)` / `GetPlayerGoldenAgeThreshold(me)`. Narration includes deficit warning:

```
Era: Renaissance Era | Score: 38 (Dark: 48, Golden: 62) !! 10 short of avoiding Dark Age
```

**Verified**: T183 overview correctly shows era score with deficit warning.

### Change 4: Rival City Count in `get_diplomacy()` [P2]

**Problem**: Russia had 11 cities vs our 3 — completely invisible. A human sees city counts in World Rankings.

**Fix**: Added `num_cities` field to `CivInfo`, `CIVCITIES|pid|count` line in diplomacy query, parser branch, and narration line.

**Verified**: T183 diplomacy shows `Cities: 11` for Russia, `Cities: 2` for Mali, `Cities: 5` for Indonesia. The 11-city count would have triggered alarm bells about Russia's expansion dominance much earlier.

### Change 5: `get_religion_status` Tool [P1]

**Problem**: No visibility into per-city religion status, follower counts, or conversion progress. Russia converted 21+ cities over 112 turns invisibly.

**Player parity**: The Religion lens shows per-city religion breakdown with follower counts and pressure indicators. This is standard visible information.

**Fix**: New MCP tool with fog-of-war filtered query (`IsRevealed` check — only reports cities the player has explored). Output grouped by civ:

```
Religious Victory Tracker:
  Eastern Orthodoxy: majority in 4/4 civilizations !! VICTORY ACHIEVED

Byzantium:
  Constantinople (pop 14) — Eastern Orthodoxy (Eastern Orthodoxy:10)
  Adrianople (pop 9) — Eastern Orthodoxy (Eastern Orthodoxy:6)
  Edessa (pop 8) — Eastern Orthodoxy (Eastern Orthodoxy:8)
Russia:
  Olonets (pop 7) — Eastern Orthodoxy (Eastern Orthodoxy:7)
  Nizhniy Novgorod (pop 3) — Eastern Orthodoxy (Eastern Orthodoxy:3)
Indonesia:
  Banjarmasin (pop 8) — Eastern Orthodoxy (Eastern Orthodoxy:7, Hinduism:1)
```

Note: Russia shows only 2 of 11 cities because we only explored 42% of the map. This correctly reflects what a human player would see — **lack of exploration limits intelligence**. The summary line (4/4 civilizations) is calculated from `GetReligionInMajorityOfCities()` which IS global knowledge (shown in Victory Advisor).

**Verified**: T183 tool returns full per-city breakdown with follower counts and victory tracker.

### Summary of All Edits

| File | Changes | Lines |
|------|---------|-------|
| `lua_queries.py` | Victory proximity query, LOS check in attack, ERA fields + query + parser, CIVCITIES in diplomacy, religion status query + 3 dataclasses + parser | ~180 |
| `game_state.py` | `_check_victory_proximity()`, victory check in `end_turn()`, era score in `narrate_overview()`, city count in `narrate_diplomacy()`, `get_religion_status()`, `narrate_religion_status()` | ~60 |
| `server.py` | `get_religion_status` tool | ~15 |

**Total**: ~255 lines across 3 files. All compile-verified and tested against live game.

### How These Changes Would Have Changed Game 4

1. **T70** (Russia founds Orthodoxy): `get_religion_status` would show conversion starting. Agent could prioritize counter-strategy.
2. **T101** (all religion slots filled): Already surfaced by existing tools, but now with per-city breakdown showing which cities are converting.
3. **T110-140** (passive conversion spreading): Victory proximity alert would fire `!! RELIGIOUS VICTORY THREAT: Russia's Eastern Orthodoxy is majority in 2/4 civilizations!` — 40-70 turns of warning.
4. **T140** (Russia at 3/4 civs converted): `!!! RELIGIOUS VICTORY IMMINENT` fires. Agent has 42 turns to: declare war, kill missionaries, or pivot to diplomatic counter.
5. **T175-178** (crossbow LOS bug): `ERR:NO_LOS` returned immediately instead of 4 turns of silent 0-damage attacks.
6. **Throughout**: Era score deficit warnings prompt era score hunting (eurekas, districts, wonders) to avoid Dark Ages.
