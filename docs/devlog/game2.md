# Civ 6 MCP — Game 2 Development Log

Previous game log archived in `DEVLOG-game1.md` (3525 lines, 323 turns as Poland, conceded at T323).

## Tooling State at Game Start

The MCP server has 45+ tools built over Game 1, including 3 spatial awareness tools and 4 diplomatic tools added in the final session:

**Core loop:** get_game_overview, get_units, get_cities, get_map_area, execute_unit_action, set_city_production, set_research, end_turn

**Spatial awareness (new):** get_minimap (ASCII map), get_strategic_map (fog boundaries + unclaimed resources), get_global_settle_advisor (top 10 settle sites across entire map)

**Diplomacy (enhanced):** get_diplomacy (now shows defensive pacts), send_diplomatic_action (friendship/OB now returns ACCEPTED/REJECTED), propose_trade (gold, resources, gold/turn), propose_peace (white peace with cooldown check)

**Intelligence:** get_victory_progress (rival yields, victory assessment 0-100%), combat estimator (auto-runs before attacks), get_empire_resources (highlights unimproved luxuries)

**Efficiency:** skip_remaining_units (auto-fortify military, skip civilians), end_turn blocker detection (production, research, diplomacy, governors, envoys, dedications, congress)

## Lessons from Game 1 (Key Takeaways)

1. **Explore early and aggressively.** A river valley with 3 rice, tea, and coal sat 5 tiles from our 3rd city for 323 turns unscouted. One scout at T50 changes the entire game.
2. **Diplomacy is a yield source.** 588 diplomatic favor was invisible for the entire game due to a GameCore/InGame API context bug (now fixed). Friendships, alliances, and suzerainties compound favor income.
3. **Spend gold and faith.** We ended with 1,618 gold and 2,818 faith unspent. Buy builders, tiles, buildings. Hoarding helps nothing.
4. **Reassess victory path every 50 turns.** We committed to Science in a 4-city peninsula. Diplomatic was viable but never attempted because the favor display showed 0.
5. **Districts are the multiplier.** Every Campus = compound science growth. Every Commercial Hub = trade route capacity + gold. Build them in every city by T75.
6. **Barbarian camps must be destroyed early.** Two camps spawned 150 turns of Line Infantry (CS:65) waves. A warrior at T80 prevents a crisis at T200.
7. **Geography determines strategy.** Small empires (3-4 cities) can't win Science against 10-city empires. Pivot to Diplomatic, Culture, or tall strategies.

---

## Game 2: Rome (Trajan) — Classical Republic Science Push

### Turns 1-20: Founding & Survival

**Setup:** Standard map, started at (13,10) on a grassy river plain with furs, stone, horses, and a mountain to the northeast. Trajan's free monument in every city means instant culture growth.

**Key events:**
- T1-10: Built scout → slinger → warrior. Explored north and south. Spotted furs (13,8) and stone (13,11).
- T11: Met Yerevan (Religious city-state) to the southwest.
- T18-25: **Barbarian crisis.** Wave of warriors and slingers from the northwest. Warrior had to retreat to city center for defense bonus. The slinger couldn't deal damage from the city tile (possible stacking/LOS bug). Killed our first barb warrior in melee and promoted the slinger with Volley.
- T19: Mining + Craftsmanship completed same turn. Switched to Archery + Foreign Trade.

**Mistakes:** Sent builder too close to barbarian territory. Lucky it wasn't captured. Should have cleared the barb camp at (11,6) earlier.

### Turns 20-40: Expansion & Economy

**Key events:**
- T26: Archery eureka (slinger combat kill). Both slingers upgraded to archers for 120g total. Builder improved furs (camp). Set Agoge policy for military production boost.
- T29: Foreign Trade civic complete — trade routes unlocked.
- T35: **Founded Ravenna** at (15,13) — diamonds, furs, spices, amber in range. Score 32 vs America 71.
- T37: Trader built, domestic route Rome→Ravenna for +2 food, +1 prod, +3 gold.
- T34-35: Cleared barbarian camp at (11,6) with warrior.
- T42: Early Empire complete. Appointed Pingala (The Educator) → Rome for +15% science/culture.

**Strategic assessment at T40:** Two cities, one archer defending each area. Behind America by 40+ points. Need Campus urgently. Builder economy is solid with camp, mine, quarry, farms.

### Turns 40-60: Science Foundation

**Key events:**
- T45: Bronze Working reveals iron at (14,12) between both cities. Ravenna builder built.
- T50: Writing + State Workforce complete. Campus placed at (14,10) with +1 mountain adjacency. Appointed Magnus → Ravenna (chop bonus).
- T54-57: Second barb wave — warrior took 84 damage from barb archer. Retreated, used our archers to eliminate threats.
- T58: **Campus complete in Rome.** Library started.

**Mistakes:** Governor promotion system broken — all Pingala promotions return false despite having points. Worked around by appointing Magnus instead. Scout at (7,7) permanently stuck with NEEDS_PROMOTION blocker.

### Turns 60-77: Classical Republic & Dark Age

**Key events:**
- T61: Entered **Dark Age** (Classical Era, era score 0). Chose Free Inquiry dedication (+1 era score per eureka/science building). Ravenna archer completed.
- T61-67: Prolonged fight with barb archer at (17,11). **Ranged attacks from (16,12) dealt 0 damage due to mountain at (16,11) blocking LOS.** Had to reposition to (17,12) for clear line of fire. Lost one archer in the process before realizing the LOS issue.
- T67: **Political Philosophy complete!** Switched to Classical Republic (+15% Great People points). Policies: Urban Planning, Caravansaries, Charismatic Leader, Conscription (wildcard).
- T67: Iron mine built at (14,12) — Iron Working eureka.
- T70: **Ravenna Campus complete.** Library started.
- T71: Rome Commercial Hub complete. Settler started (7 turns).
- T72: Pasture on horses at (14,9) — Horseback Riding eureka.
- T75: Rome grew to pop 8. Envoy sent to Yerevan.
- T76: Both libraries done. Water Mill started in Ravenna. Masonry complete.
- T77: Researching Construction. **Game crashed/disconnected during stuck research notification blocker.**

**State at T77:**
- Score: 81 vs America 155 (still 48% behind)
- Science: 15.5/turn (2 Campuses + 2 Libraries + Pingala)
- Gold: 393 (+12/turn)
- Government: Classical Republic
- Rome (pop 8): Settler in production (~4 turns)
- Ravenna (pop 5): Water Mill in production
- Techs: 11 completed, researching Construction
- Civics: 7 completed, researching Drama and Poetry
- Military: 2 archers, 2 warriors (can upgrade to swordsmen/legions for 150g each)
- Known civs: America (only one met)
- Known city-states: Yerevan (1 envoy)

### Reflection at T77

**What's working:**
1. Science engine is online. Two campuses + libraries + Pingala = 15.5 science/turn. This will compound.
2. Gold economy stabilized at +12/turn with Commercial Hub + Caravansaries + Conscription.
3. Barbarian defense finally adequate — archer pair at Ravenna covers the eastern approach.

**What's not working:**
1. **Only 2 cities at T77 is terrible.** The benchmark says 3-4 cities by T100. Need 3rd city by T85 at latest.
2. **Score gap is massive** (48% behind America). America likely has 4+ cities and more districts.
3. **Only met 1 civ and 1 city-state.** We're diplomatically isolated. Need exploration for eurekas, city-states, and trading partners.
4. **No religion, no faith income.** Pantheon was never triggered (0 faith). This closes off pantheon bonuses and religious victory entirely.
5. **Dark Age penalties.** No era score progress means likely another Dark Age next era unless we trigger many eurekas.
6. **LOS bug cost an archer.** The mountain-blocked ranged attack wasted 3 turns and lost a unit. Need to always verify LOS before committing archers.

**Next priorities:**
1. Finish settler, found 3rd city at a strong location (ideally with new luxury + district adjacency)
2. Build Market in Rome (unlocks 2nd trade route)
3. Research Construction → Engineering for Aqueducts
4. Upgrade warriors to Legions (Rome UU, CS:36, can build roads/forts)
5. Explore south/east — we've only seen a tiny slice of the map
6. Build Ancient Walls in both cities (Masonry complete)

### Turns 77-103: The Barb Wars & Expansion

**Key events:**
- T78: Settler built in Rome. Market started. Drama and Poetry civic complete.
- T84: **Founded Ostia** at (15,17) — 3rd city near Vesuvius. Iron, spices, amber, copper in range.
- T85: Accepted American trade: 17 favor for 7g + 3gpt + open borders. Market done in Rome.
- T87: Upgraded warrior to Legion (CS:40) at Ostia for 150g.
- T88-97: **The Great Barb Invasion.** 2 swordsmen (CS:35), 1 archer, 1 spearman poured in from the east. Lost 2 archers learning hard lessons about mountain LOS blocking and melee vs ranged matchups. Eventually killed both swordsmen with a combination of city ranged strikes (Ravenna), Legion melee, and archer softening.
- T90: Entered Dark Age. Walls completed in Rome.
- T91: Upgraded second warrior to Legion. The upgrade gave Rome's UU (CS:40, 1 build charge) instead of generic swordsman — unexpected bonus.
- T92: Promoted surviving archer to Arrow Storm (+7 RS vs land).
- T93: Appointed Victor (The Castellan) → Ostia. Pingala reassigned to Rome.
- T96: Ravenna Walls complete. Horseback Riding + Mysticism done. Ostia Bath started.
- T99: Zhang Qian (Great Merchant) recruited — free Trader + trade route capacity.
- T99: **Founded pantheon: Fertility Rites** (free builder + 10% growth empire-wide).
- T99: Met Nubia (Amanitore) — friendly first contact. Second civ discovered.
- T101: Ostia Bath complete. Mathematics done. Hypatia activated on Campus (+1 science per library).
- T102: Settler completed in Rome. Heading to (12,14) for 4th city.
- T103: Zhang Qian ready to activate on Commercial Hub.

**State at T103:**
- Score: 176 (3rd) vs America 242, Unmet 206, Nubia 205
- Science: 23.1/turn | Culture: 14.5 | Gold: 343 (+23/turn) | Faith: 3
- Rome (pop 8): Settler in production, Walls, Campus+Library, Commercial Hub+Market, Pingala
- Ravenna (pop 8): Market (3 turns), Walls, Campus+Library, Commercial Hub, Magnus
- Ostia (pop 3): Campus (16 turns), Bath complete, Granary, Victor
- Research: Apprenticeship (Industrial Zones). Civic: Military Training.
- Military: 2 Legions (CS:40), 1 Archer (Arrow Storm), 131 strength
- 3 Great People recruited: Zhang Heng, Hypatia, Zhang Qian
- Government: Classical Republic (Urban Planning, Caravansaries, Charismatic Leader, Conscription)
- Luxuries: Amber, Furs (2), Spices | Strategics: Horses, Iron (capped)
- Known civs: America (unfriendly), Nubia (friendly), 1 unmet
- Known CS: Yerevan (Religious, 3 envoys, America is suzerain)

### Reflection at T103: Empire Assessment & Victory Path

**The score gap is closing but slowly.** At T77 we were 48% behind America. At T103 we're 27% behind (176 vs 242). But a 3rd civ (Nubia) appeared at 205, and an unmet civ at 206. We're 4th of 4. The settler heading to (12,14) for our 4th city is critical — America has 5 cities, Nubia has 5, the unmet civ has 4.

**Science is our strongest path (60% assessment).** We're only 1 tech behind America (16 vs 17 completed) despite having 2 fewer cities. Hypatia + Pingala + 2 campuses with libraries = 23.1 science/turn. Ostia's +5 adjacency campus will add ~7 science when complete. The 4th city campus will add more. If we can reach 40+ science by T150 and 80+ by T200, the space race is winnable.

**Culture is weak (14.5 vs America's 32).** No Theater Squares, no Great Works, no wonders. Culture is purely from monuments + government. This means slower civic progression and fewer policy options. We should build Theater Squares in Ravenna and Rome once infrastructure stabilizes.

**Religion is permanently closed.** All 3 other civs founded religions. We have a pantheon (Fertility Rites) but no Holy Sites and no way to found a religion. This means no Religious Victory and limited faith income. Faith is basically useless now — should have been more aggressive about this in the early game.

**Diplomacy is neutral.** America is unfriendly (they hate our lack of "appealing areas" — probably a terrain beauty agenda). Nubia is friendly. We should send a delegation to Nubia and pursue friendship. The unmet civ is a wildcard. Diplomatic Victory requires World Congress VP, which we haven't engaged with yet.

**Military is adequate but fragile.** 2 Legions + 1 Archer = 131 strength. Nubia leads with 200. The barb invasion from T88-97 exposed that our military was too thin — we lost 2 archers (one to LOS bug, one to being outnumbered). We need at least 1 more ranged unit and should research Machinery for crossbowmen eventually.

**Economy is strong.** 343 gold stockpile with +23/turn is healthy. We have 3 luxuries generating amenities and can sell the extra Furs. Trade routes are underutilized — we should have 2-3 active routes but only 1. Zhang Qian will help with +1 capacity.

**What went right (T77-103):**
1. Ostia founding at T84 with Vesuvius adjacency (+5 campus!) was the best settle decision of the game.
2. Legion upgrades were decisive in the barb crisis. CS:40 vs CS:35 swordsmen is a comfortable margin.
3. Three Great People recruited by T103 — Zhang Heng (science boost), Hypatia (+1 library science), Zhang Qian (+1 trade route). Great Person generation is a genuine advantage.
4. Pantheon timing at T99 was late but Fertility Rites (free builder + 10% growth) is one of the best picks.

**What went wrong (T77-103):**
1. **Lost 2 archers to barbs.** The mountain LOS bug at (16,11) cost the first one. The second died to a swordsman melee attack at 12 HP because I kept it in a forward position too long. Military positioning needs more caution.
2. **Production constantly cancelled by diplomacy popups.** At least 4 times, set_city_production was silently cleared when a diplomacy encounter triggered. This is the most frustrating tooling bug — entire turns of production lost.
3. **3 cities at T103 is behind schedule.** Benchmark says 3-4 cities by T100. We'll have 4 at ~T110. America and Nubia have 5 each. The 2-city bottleneck from T35-84 (49 turns!) was too long.
4. **No religion, no faith income.** 25 faith total by T99 means we had almost zero faith generation. A single shrine or Holy Site at T50 could have given us a pantheon by T60 and opened more options.
5. **Trade routes underutilized.** We had capacity for 2 routes but only ran 1 for most of this period. Free yields sitting on the table.
6. **Unexplored map.** We only know ~30% of the map. The unmet civ is out there somewhere. More exploration could reveal city-states, natural wonders, and settle locations.

### Tooling Reflections (Session 2)

**What works well:**
- `get_game_overview` + `get_units` + `get_cities` provides excellent orientation each turn.
- `get_global_settle_advisor` found the Vesuvius spot that became Ostia's +5 campus. Map-wide analysis is invaluable.
- `get_district_advisor` consistently finds optimal placements. The +5 campus at (17,16) was a great find.
- `get_victory_progress` provides strategic clarity — the Science 60% recommendation aligned with our strengths.
- `execute_city_action(attack)` for city ranged strikes worked perfectly against the barb swordsman at Ravenna.
- `upgrade_unit` is clean and reliable (warrior→legion was seamless).
- `choose_pantheon` / `send_envoy` / `get_available_beliefs` — all clean UX for blocking notifications.

**What needs work:**
1. **Production cleared by diplomacy popups.** This is the #1 pain point. When a diplomacy session triggers between `set_city_production` and `end_turn`, the production is silently cleared. Workaround: always re-check cities after diplomacy. Possible fix: `end_turn` could re-verify and re-apply production.
2. **Great Person claiming has no dedicated tool.** Had to write raw Lua (`UI.RequestPlayerOperation(me, PlayerOperations.RECRUIT_GREAT_PERSON, ...)`) to claim Zhang Qian and Hypatia. Should be a `claim_great_person` MCP tool.
3. **Hex adjacency is opaque.** The Legion repeatedly showed NOT_ADJACENT errors at tiles that looked adjacent. The game's hex coordinate system doesn't match intuitive neighbor calculations. The `move` action should handle move-attack transparently when the target tile has an enemy.
4. **Builder improvement failures are silent.** Builder at (15,18) couldn't build a mine initially (CanStartOperation returned false) with no explanation. Later it worked. The improvement system needs better error messages.
5. **Research notification blocker still sticks occasionally.** The force-end-turn Lua workaround (dismiss all notifications + UI.RequestAction) works but shouldn't be needed.
6. **No repair improvement action.** The pillaged farm at (16,13) needs repair but there's no documented way to repair pillaged improvements via the MCP tools.

**New patterns learned:**
- City ranged attacks are powerful for barb defense — walls pay for themselves immediately.
- Legion (Rome UU) is strictly better than swordsman — CS:40 vs CS:36, plus 1 build charge for roads/forts. Always upgrade to Legion when possible.
- Promote-to-heal is a crucial tactic. Arrow Storm promotion on a 12 HP archer = full heal + permanent RS bonus.
- Great People compound: Hypatia's "+1 science per library" applies to ALL libraries, making future library builds more valuable.
- Dark Age isn't catastrophic with good economy — we entered Classical Dark Age at T61 but the extra policy card options (Twilight Valor, Isolationism) could be useful.

**Next priorities (T103+):**
1. Found 4th city at (12,14) — horses, stone, iron, maize, spices in range. Immediately build Campus.
2. Activate Zhang Qian on Rome's Commercial Hub — +1 trade route capacity + free Trader.
3. Fill all trade route slots (should have 3 after Zhang Qian). Domestic to Ostia and new city.
4. Research Apprenticeship → Industrial Zone in Rome for production multiplier.
5. Build Market in Ravenna (3 turns) → then Theater Square for culture catch-up.
6. Send delegation to Nubia, pursue friendship for trade and safety.
7. Explore west/south for the unmet civ and more city-states.
8. Repair pillaged farm at (16,13). Improve unimproved cattle at (15,13).
9. Policy swap: Natural Philosophy (+100% Campus adjacency) instead of Caravansaries once Ravenna Market finishes.
10. Consider Machinery tech for crossbowmen — archers are fragile against medieval units.

### Turns 103-117: Heroic Age & The Vesuvius Crisis

**Key events:**
- T104: **Founded Lugdunum** at (12,14) — 4th city. Horses, stone, iron, maize, spices in range.
- T104: Assigned Liang (Surveyor) governor to Lugdunum for builder charges bonus.
- T105: Builder improved maize at (11,13) with farm. Builder at (15,16) built lumber mill.
- T106: Accepted Nubia trade deal — 11 gpt for furs + spices. Good early trade income.
- T108: **Entered Heroic Golden Age!** Dark Age → Heroic. Picked 3 dedications: Free Inquiry (science eurekas), Monumentality (30% cheaper faith/gold civilian purchase, builders +2 movement), Pen Brush & Voice (culture).
- T109: Theology + Education completed. Sent envoy to Mitla (Scientific CS). Appointed Reyna governor to Aquileia.
- T110: Ostia Campus complete! +5 adjacency from Vesuvius mountain/geothermal.
- T113: Claimed Great Merchant Colaeus via Lua (no MCP tool for GP recruitment yet).
- T115: Barb archer spotted at (17,13) approaching Ravenna. Archer ranged attack + Ravenna city strike eliminated it.
- T116: Rome's Campus shown as PILLAGED (unclear when this happened).
- T117: **"Megacolossal Volcano Erupts!" at Vesuvius (17,17).** Pillaged Ostia's campus district.

**The Vesuvius Production Queue Corruption (T117):**

This is the second time we've hit a fatal production queue corruption (first was Game 1, T180). The pattern is identical:

1. Vesuvius eruption pillages Ostia's campus district
2. Game auto-queues a district repair entry: `{BuildingType=4, Directive=1, Location=table, Modifiers=0}`
3. `bq:GetSize()` returns 1 but `bq:GetCurrentProductionTypeHash()` returns 0 (hash=0)
4. This hash=0 ghost entry blocks ALL production operations — `set_city_production` appears to succeed ("PRODUCING|UNIT_BUILDER|5 turns") but the underlying hash stays 0
5. The `ENDTURN_BLOCKING_PRODUCTION` notification fires but cannot be resolved
6. `UI.RequestAction(ActionTypes.ACTION_ENDTURN)` silently fails — turn stays at 117

**Everything we tried (all failed):**
- `CityManager.RequestOperation` with every insert mode (REPLACE_AT, EXCLUSIVE, CLEAR, REMOVE_AT, POP_FRONT)
- `CityManager.RequestCommand(city, CityCommandTypes.CANCEL, {})`
- `NotificationManager.Dismiss()` on all notifications
- GameCore `bq:FinishProgress()` — succeeded but didn't clear queue
- GameCore `campus:SetPillaged(false)` — unpillaged the district but queue entry persisted
- `WorldBuilder.CityManager():RemoveDistrict()` + `CreateDistrict()` — appeared to succeed, no effect
- `Game.SetCurrentGameTurn(118)` — desynced GameCore (118) from InGame (117), made things worse
- Opening ProductionPanel Lua UI — panel opened but didn't resolve
- Multiple `UI.RequestAction(ACTION_ENDTURN)` with 5-8 second waits — turn never advances

**Root cause (revised):** The actual blocker was the `NaturalDisasterPopup` UI, which uses `ExclusivePopupManager` to hold an **engine lock** (`UI.ReferenceCurrentEvent()`). This lock prevents ALL game processing until released. Our `dismiss_popup` tool only called `SetHide(true)` on the popup, which hides the UI but does NOT release the engine lock. The "corrupted production queue" (hash=0) was likely a transient state during the eruption event, not permanent corruption.

**Actual fix:** Pressing ESC in the game UI called the popup's `Close()` function, which triggers `m_kPopupMgr:Unlock()` → `UI.ReleaseEventID()`. The engine lock was released, and the turn proceeded normally. **No autosave reload was needed.**

**Code fix applied:** Enhanced `dismiss_popup()` to call `Close()`/`OnClose()` in the popup's own Lua state (which properly releases the engine lock), and to clear `m_kQueuedPopups` first so multiple queued disaster events are handled.

**State at T117 (stuck):**
- Score: ~195 vs America ~260, Nubia ~220, Khmer ~215 (still 4th)
- Science: ~28/turn | Culture: ~18 | Gold: ~350 (+25/turn)
- 4 cities: Rome (pop 9), Ravenna (pop 9), Ostia (pop 5), Lugdunum (pop 2)
- Heroic Golden Age with 3 dedications active
- Ostia's production queue permanently corrupted — game stuck at T117
- Need to load autosave to continue

### Reflection at T117: The Popup Engine Lock Problem

**The real blocker was the NaturalDisasterPopup's engine lock, not production queue corruption.** The `ExclusivePopupManager` system holds a `UI.ReferenceCurrentEvent()` lock that prevents ALL game processing. Our `dismiss_popup` was calling `SetHide(true)` which hides the UI but doesn't release the lock. This made it look like the production queue was corrupted (hash=0), when it was actually just the engine being frozen mid-event.

**Tooling improvements applied:**
1. **dismiss_popup Phase 1:** Now clears `m_kQueuedPopups` and calls `Close()` in the popup's own Lua state → properly triggers `m_kPopupMgr:Unlock()` → `UI.ReleaseEventID()`
2. **dismiss_popup Phase 2:** Now also tries `UIManager:DequeuePopup()` + `Input.PopContext()` as fallback
3. **end_turn retry:** Increased popup dismiss attempts from 2 to 5 for multiple queued popups
4. **Detection:** `get_cities` flags hash=0 as CORRUPTED_QUEUE (still useful for the actual Game 1 corruption case)

**Gameplay takeaway:** Vesuvius cities are viable — the +5 campus adjacency is worth the eruption risk now that the popup handling is fixed. But volcanic eruptions can still pillage districts and damage improvements, so keep builders nearby for repairs.

### Turns 117-140: Science Engine Online

**Key events:**
- T118-122: Resolved multiple engine lock popups (Vesuvius aftermath). Fixed `dismiss_popup` to properly call `Close()` in popup Lua states. MCP server restarted with all bug fixes active.
- T122: **Founded Aquileia** at (7,10) — 5th city. Amber, horses, furs in range. Score 227 vs America 315.
- T125: Upgraded Aquileia archer to crossbow (250g). Recruited Great Scientist Abu al-Qasim al-Zahrawi, activated on Rome's Campus for science boost.
- T126: Military Engineering + Ravenna Bath complete. Rejected terrible Nubia trade deal (wanted horses + favor + OB + GPT for a single great work). Set Ostia → Commercial Hub at (14,17).
- T128: Feudalism civic complete — slotted Serfdom (+2 builder charges on new builders = 5-6 charges each). Natural Philosophy (+100% Campus adjacency) for science.
- T130-138: **Eastern barb crisis.** Two Man-at-Arms (CS:45) spawned from eastern camp. Crossbow + MaA coordinated defense over 8 turns. Both barbs eliminated. Key lesson: crossbows deal 0 damage if they move through hills first (2/2 movement consumed), and mountains block LOS even at range 2.
- T133: Celestial Navigation complete (1 turn freebie via eureka). Castles researched.
- T136: Bought Rome Water Mill (320g). Set Astronomy tech (boosted, 7 turns). Medieval Faires civic started.
- T139: Lugdunum Campus placed at (14,14). Aquileia Campus at (8,9). Both ~20 turns out.
- T140: Ravenna University + Ostia Commercial Hub complete. **Philadelphia (American city) flipped to us via loyalty!** Game crashed trying to resolve the "Keep or Free City" blocker — no Lua mechanism found. Reloaded T140 autosave. Recruited Marco Polo (Great Merchant — free trade route when activated).

**State at T140:**
- Score: 262 vs America 340, Nubia 337 (still 3rd, gap narrowing)
- Science: 68.3/turn (+26 from universities), Culture: 28.6, Gold: 207 (+26/turn), Faith: 168, Favor: 70
- 5 cities: Rome (pop 9, Settler 3t), Ravenna (pop 9, Amphitheater 8t), Ostia (pop 5, Market 9t), Lugdunum (pop 4, Campus 28t), Aquileia (pop 4, Campus 19t)
- Researching Astronomy (boosted), Civic Medieval Faires (boosted)
- Military: Crossbow (17,12), MaA healing (18,13), 2 Legions garrisoned, Scout automated
- Great People: 5 recruited (Zhang Heng, Hypatia, Zhang Qian, al-Zahrawi, Marco Polo pending activation)

### Reflection at T140: The Science Bet is Paying Off

**Science engine is online and accelerating.** 68 sci/turn at T140 vs America's 44 means we're pulling ahead on the tech tree despite having fewer cities. Two more campuses coming online (Lugdunum T168, Aquileia T159) will push us past 90. The key inflection: universities double campus output. Every city needs Campus → Library → University as fast as possible.

**The score gap is misleading.** America leads 340 vs our 262, but they have more cities and military. Our science lead (68 vs 44) and tech count advantage will compound. By T200, we should be 1-2 eras ahead in critical techs.

**Philadelphia loyalty flip is a wildcard.** If it flips again at T141, we gain a free 6th city near America without warmongering penalties. **Fixed:** Found the Lua API — `CityManager.RequestCommand(city, CityCommandTypes.DESTROY, {PARAM_FLAGS=CityDestroyDirectives.KEEP})` on the city from `GetNextRebelledCity()`. Added auto-resolve to `end_turn()` and `execute_city_action` supports keep/reject/raze/liberate.

**What went right (T117-140):**
1. Science jumped from 28 → 68 in 23 turns. Universities are the multiplier.
2. Serfdom policy = 5-6 charge builders. Each builder does 2x the work.
3. Great Person generation remains strong — 5 recruited by T140.
4. Eastern barb crisis handled without losses. Crossbow + MaA is a solid defensive combo.
5. Trade income stable at +26 gpt. Not amazing but sufficient.

**What went wrong (T117-140):**
1. **Game crashed from loyalty flip blocker.** NotificationManager has no Activate method for the "Keep or Free City" notification. This is a tooling gap.
2. **Diplomacy stalled.** Friendship rejected by both America and Nubia. Favor income is 0/turn. Need alliances for diplomatic backup plan.
3. **Culture still weak.** 28.6 culture/turn means slow civic progression. No Theater Squares yet. Amphitheater coming in Ravenna will help slightly.
4. **Only 2 luxuries improved** (Amber, Furs). Amenities are barely positive. Need to improve diamonds and spices.
5. **Eastern barb camp still alive.** It will keep spawning units until destroyed. Need to send a force to clear it.

**Strategic priorities T140-160:**
1. Settler finishes T143 → found 6th city (use `get_global_settle_advisor` for site)
2. Activate Marco Polo on Commercial Hub → free trade route capacity
3. Ostia Market (T149) → activate idle traders
4. Aquileia/Lugdunum campuses → push science past 90
5. Clear eastern barb camp to stop spawns
6. Build Theater Square in Rome for culture catch-up
7. Research toward Industrialization → factories for production multiplier
8. Improve diamonds + spices for amenities

### Turns 140-150: Science Supremacy & 7 Cities

**Key events:**
- T141: **Philadelphia loyalty-flipped from America** — kept the city. Free 6th city at (18,20) with existing library infrastructure, near Ostia. Set Library production.
- T143: **Founded Mediolanum** at (16,9) — 7th city. Set Water Mill for growth.
- T144: Promoted Pingala with Connoisseur (+1 culture per citizen in city). Rome now generating 22 culture.
- T145: Set Rome → Industrial Zone at (14,11). This will be the production engine.
- T146: Builder improvements across empire — lumber mill, pasture, mine, farm.
- T148: MaA attacked barb spearman at (20,9) — reduced to 3 HP but couldn't finish (moves exhausted). Crossbow LOS blocked by hills again.
- T149: Promoted scout with Ranger promotion, automated exploration. Set Mercenaries civic (after completing Guilds).
- T150: America turned FRIENDLY (from unfriendly). Opportunity for friendship declaration.

**Trade Route Ghost Bug (T148-150):**
Discovered a critical engine bug: `CountOutgoingRoutes()` returns stale records from historical routes pointing to deleted/consumed traders. The engine thinks 5/6 routes are active when 0 are. Routes started via tools are cancelled during turn processing because the engine count exceeds capacity. **No Lua API exists to purge ghost records — only fix is save+reload.** Added detection and warnings to tooling.

**Governor Promotion Tooling Fix (T150):**
Fixed two bugs preventing governor promotions from displaying:
1. `GovernorPromotionSets` entries use field `GovernorPromotion` (NOT `GovernorPromotionType` which returns nil)
2. `HasPromotion` must be called on the individual governor object `g` with `.Index` (NOT on the collection `pGovs` with `.Hash`)

**State at T150:**
- Score: 312 (4th) vs Nubia 388, America 364, Unmet 358
- Science: **99.8/turn** (DOUBLE nearest rival Nubia at 52) | Culture: 46.9 | Gold: 218 (+25/turn) | Faith: 188 | Favor: 80
- 7 cities: Rome (pop 10), Ravenna (pop 10), Ostia (pop 6), Lugdunum (pop 4), Aquileia (pop 6), Philadelphia (pop 4), Mediolanum (pop 2)
- 26 techs (tied with America at #1) | 18 civics
- Researching Military Tactics (1 turn) | Civic Mercenaries (6 turns)
- Military: 2 Crossbows, 2 MaA, 1 Scout = 176 strength (vs America 267, Nubia 100)
- Diplomacy: America FRIENDLY, Nubia NEUTRAL (-9), 1 unmet civ
- Victory: Science 60% recommended. Tech leader, science output 2x nearest rival.

### Reflection at T150: The Compound Interest of Science

**100 science/turn at T150 is a commanding position.** We're generating double what Nubia (52) and America (47) produce. With Aquileia Campus (2 turns) and Lugdunum Campus (5 turns) about to come online, we'll hit 110+ soon. Universities in those cities will push past 130. The science snowball is real — each tech completes faster, unlocking better buildings that generate more science.

**The score gap is deceptive.** We're 4th in score (312 vs Nubia 388) but 1st in science by a massive margin. Score counts cities, population, wonders, military — things that matter for Score Victory. But for Science Victory, what matters is tech progression speed. We're tied at 26 techs despite lower score because our yield-per-city is much higher.

**7 cities is a solid base.** More than any rival. Philadelphia was free (loyalty flip), Mediolanum rounds out the core. Each city gets a campus → library → university pipeline. The key now is getting libraries and universities in the newer cities ASAP.

**Critical issues:**
1. **Trade routes broken.** 0/6 active due to ghost route bug. That's ~15-20 gold/turn and 6-10 food+production per turn we're missing. Save+reload is needed.
2. **Favor income is 0/turn.** 80 favor sitting idle. America is FRIENDLY — declare friendship for +1/turn. Need alliances (requires Diplomatic Service civic, 13 turns) for more.
3. **Culture is the weakest yield.** 46.9 vs Nubia's 64 and America's 52. No Theater Squares. Civic progression is slow. This limits policy options.
4. **Eastern barbs won't stop.** Spearman at 3 HP still alive. Camp keeps spawning. Need to clear it.

**Priorities T150-170:**
1. Declare friendship with America (FRIENDLY, eligible)
2. Fix trade routes (save+reload or work around ghost bug)
3. Banking tech (boosted, 4 turns) → banks for gold income
4. Aquileia/Lugdunum campuses → libraries → universities
5. Industrial Zone in Rome → Workshop → Factory for production
6. Clear eastern barb camp
7. Research toward Industrialization for factories
8. Diplomatic Service civic for alliances (long-term favor income)

### Turns 155-160: The Science Flywheel Engages

**Key events:**
- T155: Entered Dark Age (Renaissance Era). Chose Monumentality dedication (+1 era score per district). Nubia sent positive agenda message — we satisfy Sympathizer (Dark Age empathy).
- T155: Banking + Mercenaries completed same window. Swapped Serfdom → Urban Planning (builders no longer priority). Diplomatic Service civic started (8 turns to alliances).
- T156: Nubia asked to establish embassy in our capital — accepted. Relationship now +11 (NEUTRAL, warming).
- T158: Aquileia Library complete → University started. **Galileo Galilei recruited** — activated on Rome's Campus (+250 science per adjacent mountain). **Irene of Athens recruited** — activated on Ravenna Commercial Hub.
- T159: Gunpowder researched (boosted by Galileo's science injection). Pingala promoted with **Grants** (+100% Great People points in Rome). Governor tooling finally working — promotions display correctly with descriptions.
- T160: **Rome Industrial Zone complete.** Workshop started (7 turns → Factory after). Ravenna IZ finishes next turn. Mediolanum Campus started (24 turns).

**State at T160:**
- Score: 356 (4th) vs Nubia 405, America 388, Unmet 380
- Science: **108/turn** | Culture: 49.5 | Gold: 605 (+27/turn) | Faith: 208 | Favor: 90 (+0/turn)
- 7 cities, 30 techs (2 ahead of nearest rival), 19 civics
- Researching Metal Casting (2 turns) | Civic: Diplomatic Service (8 turns)
- 8 Great People recruited lifetime (7 activated)
- Military: 2 Crossbows, 2 MaA = 230 strength (vs America 347)
- Trade routes: **0/6 active** (ghost route bug — 10+ turns of lost yields)

### Reflection at T160: Deep Strategic Assessment

**The Science Asymmetry**

108 science/turn. The nearest rival generates 56. We produce nearly *double* the science of every other civilization. This is the defining fact of the game at T160, and it has profound implications.

At this pace, we complete a tech roughly every 3-4 turns. Rivals complete one every 6-8. By T200, we'll be in the Industrial era while they're still in Renaissance. By T250, we'll be reaching Modern era techs while they hit Industrial. The space race requires Rocketry (roughly 15 techs away) → Spaceport district → 4 sequential projects. Rough estimate: Rocketry by ~T210, Spaceport built by ~T225, all 4 projects by ~T280-290. That's a Science Victory around T280-290 if production holds.

But science alone doesn't win. **Production is the real bottleneck for the space race.** Each space project needs 1500-3000 production. At 26 production/turn, Rome would take 60-115 turns per project. That's unacceptable. We need:
- Workshop (7 turns) → Factory → Coal Power Plant in Rome
- Industrial Zones in Ravenna (finishing T161), then Workshop → Factory
- Vertical Integration on Magnus or factory regional bonuses reaching multiple cities
- Eventually: 50+ production in the Spaceport city

**Why We're 4th in Score Despite Leading Science**

Score is a composite: population, territory, techs, civics, wonders, great people, military. We lead techs and great people but lag badly on:
- **Wonders:** 0 built (every wonder notification has been an AI completing one). Rome focused on infrastructure, not prestige.
- **Culture/Civics:** 19 civics vs likely 22-25 for the leaders. Culture at 49.5 is behind Nubia (80) and Unmet (64). No Theater Squares anywhere.
- **Military:** 230 vs America's 347. Adequate for defense, poor for score.
- **Population:** 47 total pop across 7 cities. Decent but not exceptional.

Score ranking doesn't matter for Science Victory. But it does matter for the AI's opinion of us and for tiebreakers. More importantly, the culture deficit means slower civic progression, which delays critical policies and government upgrades.

**The Trade Route Crisis**

This is the most damaging ongoing problem. Ghost route records (stale `CountOutgoingRoutes()` values from deleted traders) cause the engine to cancel every route we start during turn processing. We've restarted routes every single turn for 10+ turns — all cancelled. The impact:
- ~15-20 gold/turn lost (3 international routes)
- ~6-10 food+production/turn lost (3 domestic routes to new cities)
- Mediolanum and Lugdunum growing slower than they should
- Opportunity cost of 3 trader units sitting idle

The only fix is save+reload to clear the stale route records. No Lua API exists to purge them. **This should be priority #1 before next session.**

**Diplomatic Stagnation**

0 favor/turn at T160 is terrible. 90 favor stockpile earning nothing. The path to fixing this:
1. Diplomatic Service civic (8 turns) → unlocks alliances
2. Declare friendship with Nubia (+11, should accept) → +1 favor/turn
3. Try friendship with America again (FRIENDLY +5, rejected before)
4. Alliance with Nubia → +1 favor/turn + shared visibility
5. Suzerainties (need more envoys) → +2 favor/turn each
6. Eventually: vote aggressively in World Congress for Diplo VP

The 4th civ (China?) remains unmet at T160. They're at 380 score with 56 science — the second-strongest science civ. Meeting them opens trade, diplomacy, and era score opportunities. But they're far east on the map.

**The Niter Problem**

Gunpowder is researched but we have 0 niter. Can't build Musketmen. Three niter deposits are unclaimed:
- (14,20) — 3 tiles from Ostia (closest, likely acquirable via culture expansion)
- (8,17) — 5 from Lugdunum
- (6,15) — 5 from Aquileia

Need to either buy the tile at (14,20) for Ostia or wait for border growth. Musketmen (CS:55) would be a significant military upgrade from MaA (CS:45), especially with America at 347 military strength.

**What's Working (T150-160):**
1. Science engine is self-reinforcing: more science → faster techs → better buildings → more science. Galileo's activation alone gave ~250 science instant boost.
2. Great Person generation is strong: 8 recruited by T160 with Pingala's Grants now doubling GP points in Rome.
3. District pipeline is solid: Rome IZ done, Ravenna IZ tomorrow, Lugdunum/Aquileia/Ostia all building campus chain. Mediolanum campus started.
4. Gold economy healthy at 605 stockpile (+27/turn). Can buy tiles, units, or buildings when needed.
5. **Governor tooling finally works.** Promotions display correctly — this was blocking strategic governor use for 100+ turns.

**What's Not Working (T150-160):**
1. **Trade routes completely non-functional.** Ghost bug has persisted 10+ turns. Massive yield loss.
2. **Culture is the weakest link.** 49.5 vs Nubia 80 means we're falling behind on civic progression. No Theater Squares anywhere. This delays alliances (Diplomatic Service), government upgrades, and critical policies.
3. **No niter = no military modernization.** Musketmen are available but unbuildable.
4. **4th civ still unmet.** Missing diplomatic opportunities, trade routes, era score.
5. **Dark Age penalties.** Loyalty pressure on edge cities. No Golden Age bonuses.
6. **Insulae policy won't slot.** Attempted 3 times — keeps reverting to empty. Possible tooling bug with `set_policies` or a game-side prerequisite issue. Workaround: using Urban Planning instead.

**Strategic Plan T160-180:**

*Immediate (T160-165):*
1. Save+reload to fix ghost trade routes (tell user)
2. Rome Workshop → Factory (production is the bottleneck)
3. Ravenna IZ → Workshop → Factory
4. Buy niter tile at (14,20) for Ostia

*Medium-term (T165-175):*
5. Diplomatic Service civic → declare friendship with Nubia → alliance
6. Start building Theater Squares (Rome first, for culture catch-up)
7. Complete university chain in all cities (Ostia T174, Aquileia T172, Philadelphia T182)
8. Research toward Industrialization for Factories

*Long-term (T175-200):*
9. Scientific Theory → try for Oxford University
10. Get Spaceport prerequisites lined up (Rocketry tech)
11. Aim for 150+ science/turn by T200 (7 campuses with universities + Natural Philosophy)
12. Identify Spaceport city (Rome: best production + Pingala's Space Initiative promotion later)

**The Exploration Failure — Repeating Game 1's Mistake**

Game 1's #1 lesson was: "A river valley with 3 rice, tea, and coal sat 5 tiles from our 3rd city for 323 turns because no scout was ever sent south. One scout at T50 would have found both." We wrote it in bold in the playbook. We added strategic benchmarks. We built `get_strategic_map` and `get_minimap` specifically to catch this.

And we're doing it again.

The strategic map at T160 tells the story:
```
Aquileia (9,10):  SW:3  NW:4  ← fog 3 tiles away!
Mediolanum (16,9): N:4  NE:4  ← fog 4 tiles away!
Philadelphia (18,20): NE:3  S:4  ← fog 3 tiles away!
```

Three tiles. That's a warrior's single-turn move. We have fog of war *three tiles* from our cities at Turn 160. In Game 1 this is exactly how barbarian camps festered unseen — and we noted "Two barbarian camps that spawned 150 turns of siege were 6 tiles from the nearest city."

What's hiding in those fog gaps right now? We don't know. That's the point.

**What we know we're missing:**
- The 4th civilization (likely China at ~42,21) — **unmet at Turn 160.** That's 160 turns of missed trade, missed delegations, missed friendship/alliance favor, missed era score from first contact. Every turn of unmet civ is compound lost yield.
- Unclaimed diamonds at (7,12) and (8,14) — luxury resources that would fix our amenity problems, sitting in fog-adjacent territory west of Lugdunum.
- Unclaimed amber at (22,9) — far east, probably near the unmet civ.
- Potential city-states, natural wonders, barbarian camps — all unknown.
- The *shape* of the map beyond our corridor. We occupy a north-south strip from (7,8) to (18,20). What's east? What's far south? Is there a landmass we're missing?

**Why did this happen again?**

We built one scout at T1. It explored the immediate area, then got stuck with a NEEDS_PROMOTION blocker for 50+ turns (tooling bug). When we fixed the promotion and automated it at ~T149, it started exploring... directly into barb galleys northwest of Aquileia. It's been ping-ponging near (7,8) for 10 turns, exploring already-visible coastal tiles instead of pushing into real fog.

The auto-explore AI is notoriously bad at prioritizing fog gaps. It moves toward the nearest unexplored tile, which near Aquileia is the ocean — not the strategically valuable land fog to the south and east.

**What should have happened:**
- T25: Scout automated, exploring edges of known map.
- T50: Second scout built. First scout should have pushed east toward unmet civs.
- T75: Both scouts covering different quadrants. Met all civs by now.
- T100: Scouts on alert at strategic chokepoints or sent to find remaining city-states.

What actually happened: One scout, stuck for 50 turns, then auto-exploring into ocean. Zero dedicated exploration after T1.

**The deeper pattern:** We optimize what we measure. The turn loop checks `get_units`, `get_cities`, `get_map_area` around known positions. It doesn't prompt "what DON'T you see?" The `get_strategic_map` tool exists but we've barely used it. The `get_minimap` exists but we look at it and don't *act* on the blank spaces. Information about unknown territory produces no notifications, no blockers, no action items. So it gets deprioritized in favor of the constant stream of production queues, unit orders, and tech choices.

This is the core problem: **exploration has no urgency signal.** Building a monument has a blocker notification. An unmoved unit has a blocker. But "you haven't explored southwest of your 5th city" has no notification. It requires the player (or agent) to proactively notice the absence of information and act on it. That's hard for humans and apparently hard for AI agents too.

**Concrete fixes:**
1. *Immediately:* Send MaA at (20,8) to explore east — it's healed, idle, and the eastern fog at Mediolanum NE:4 is close. It can fight barbarians if it finds a camp.
2. *This session:* Build or buy a second scout. Auto-explore south/east.
3. *Tooling idea:* Add an exploration check to `end_turn` — if any city has fog < 5 tiles in any direction, emit a warning. Make the invisible visible.
4. *Playbook update:* "Check `get_strategic_map` every 10 turns" isn't enough. Need: "If any direction shows < 6, send a unit THAT TURN."

**The cost of not exploring at T160:**
- 0 favor from 4th civ friendship (potentially +1/turn since T40 = ~120 favor lost)
- Unknown number of undiscovered city-states (envoy bonuses, suzerainty favor)
- Amenity crisis partially caused by not securing diamonds at (7,12)
- Blind to barbarian camp locations (the barb builder at (18,15) came from somewhere)
- No visibility into rival expansion, military movements, wonder construction
- Cannot plan 8th city without knowing the full map

We have the tools. We wrote the lessons. We just didn't follow them. That's the hardest kind of mistake to fix — not a tooling gap, but an attention gap.

**The core insight at T160:** We've won the science race already — the question is whether we can convert that science lead into a timely Science Victory before someone else wins via Diplomacy, Culture, or Religion. Production, not science, is now the binding constraint. And exploration — the foundation that informs every other strategic decision — remains neglected for the second game running.

### Tooling: Exploration Coverage in Game Overview (T160)

**Problem:** The agent repeatedly ignores exploration because unknown territory generates no signal. The turn loop focuses on what's visible — production, units, techs — and never prompts "what don't you see?"

**Fix:** Added exploration coverage stats to `get_game_overview`. Every turn now shows:
```
Explored: 34% of land (306/896 tiles)
```

This is a permanent nudge. When the agent sees "34% explored" every single turn, the 66% unknown becomes impossible to ignore. The implementation counts all revealed non-water tiles via `PlayersVisibility[id]:IsRevealed()` in the InGame Lua context. Minimal performance cost — iterates 2280 tiles once per overview call.

**Files changed:** `lua_queries.py` (Lua query + dataclass + parser), `game_state.py` (narration). Four surgical edits, no new tools needed.

### Turns 160-185: Trade Route Renaissance & 47% Explored

**Key events:**
- T161-165: Ravenna IZ complete → Workshop. Rome Workshop complete → Factory started. Banking researched.
- T163: Diplomatic Service civic complete. Declared friendship with Nubia (+1 favor/turn). Sent delegation to China (4th civ, finally met via scout).
- T165: **Trade routes finally working** after save+reload cleared ghost records. 3 routes active: Rome→Lugdunum (domestic), Ravenna→Philadelphia (domestic), Aquileia→Mediolanum (domestic). New cities getting food+prod boost.
- T168: Lugdunum Campus complete → Library started. China (Qin Shi Huang) declared friendship.
- T170: Rome Factory complete. Rome now 42 production/turn — the Spaceport city is taking shape. Ravenna Workshop → Factory.
- T172: Aquileia University complete. Science hits 125/turn.
- T175: Ostia University complete. Science at 138/turn. Niter tile bought at (14,20) for Ostia → Musketmen available.
- T178: Exploration push — MaA sent east, scout sent south. Found Buenos Aires (Industrial CS) and Cahokia (Industrial CS). 3 new city-states discovered in 3 turns.
- T180: Raja Todar Mal (Great Merchant) activated on Rome Commercial Hub (+500 gold). Gold stockpile: 798.
- T182: Philadelphia University complete. 7/7 campuses now have libraries, 5/7 have universities.
- T185: Aquileia Market complete (+1 trade route capacity, now 8). Science: 152/turn. Culture: 57/turn.

**State at T185:**
- Score: ~441 (4th behind China 478, Nubia 463, America 448)
- Science: **152/turn** (rivals at ~60-70) | Culture: 57 | Gold: 798 (+48.5/turn) | Faith: ~200 | Favor: 90 (+1/turn)
- 7 cities, all with Campuses, 5 with Universities
- Explored: 47% of land (up from 34% at T160)
- Researching: Square Rigging | Civic: Mercantilism
- Policies: Natural Philosophy, Serfdom, Charismatic Leader, Conscription
- 3 trade routes active, 1 idle trader, capacity 8

### Tooling: Enriched Trade Routes for Game Parity (T185)

**Problem:** The `get_trade_routes` and `get_trade_destinations` tools showed bare minimum info — destination city name, domestic/international flag, and coordinates. A human player sees much more: **yield breakdown**, **religious pressure** (bidirectional), **destination civilization**, **trading post status**, and **city-state quest alignment**. This made it impossible to optimize trade route decisions.

Additionally, the active route detection (using `moves==0`) was unreliable, and `GetNumOutgoingRoutes()` counted ghost records toward capacity.

**Investigation findings:**
- `GetOutgoingRoutes()` exists on **city** trade object (not player), returns route records with yield data
- `TradeManager:CalculateOriginYieldsFromPotentialRoute()` returns **flat arrays** `[food, prod, gold, sci, cul, faith]` — NOT `{YieldIndex, Amount}` tables like route records
- `CalculateDestinationReligiousPressureFromPotentialRoute(oP, oCID, dP, dCID, relIdx)` gives outgoing religion pressure (base 1.0)
- `CalculateOriginReligiousPressureFromPotentialRoute(...)` gives **incoming** religion pressure (base 0.5) — critical for defense against religious spread
- `Game.GetQuestsManager():HasActiveQuestFromPlayer(me, csPlayer, questIdx)` detects city-state trade route quests
- `city:GetTrade():HasActiveTradingPost(playerID)` shows established trading posts (bonus yields)
- Ghost routes detected by cross-referencing `TraderUnitID` in route records against living UNIT_TRADER units

**Solution:** Complete rewrite of both trade route queries and parsers.

`get_trade_routes` now shows:
```
Trade Routes: 3/8 active (4 ghost records in engine)

On route (3):
  Trader (3145728) Rome -> Philadelphia (Domestic) | Food:3 Prod:2 Gold:1 | Trading Post
  Trader (1966089) Aquileia -> Kawa (Nubia) | Gold:6 Faith:1 | Eastern Orthodoxy -> 1.0 | Protestantism <- 0.5
  Trader (2818058) Rome -> Caguana (City-State) | Gold:4 | [QUEST]

Idle (1):
  Trader (2883594) at (13,10) — has moves
```

`get_trade_destinations` now shows:
```
Domestic (4):
  Philadelphia at (18,20) | Food:2 Prod:3 Gold:1 -> dest: Food:4 Prod:2

International (8):
  Kawa (Nubia) at (23,18) | Gold:6 Faith:1 | Eastern Orthodoxy -> 1.0 | Protestantism <- 0.5
  Caguana (City-State) at (22,23) | Gold:4 | [QUEST] Trading Post

City-state trade route quests: Caguana, Valletta
```

Key design decisions:
- **Bidirectional religion**: Shows both `{Religion} -> X` (our faith spreading to them) and `{Religion} <- X` (their faith spreading to us). Critical for civs with religious concerns.
- **Compact yield format**: `F3P2G4` in Lua → parsed to `Food:3 Prod:2 Gold:4` in Python. Minimizes Lua output size.
- **Cross-reference ghost detection**: Route is "real" only if its `TraderUnitID` maps to a living UNIT_TRADER unit. Engine's `GetNumOutgoingRoutes()` is unreliable.
- **City-state quest highlight**: `[QUEST]` flag makes it obvious when sending a route earns a free envoy.

**Files changed:** `lua_queries.py` (dataclasses, 2 Lua query builders, 2 parsers, `_parse_compact_yields` helper), `game_state.py` (2 narration methods).

### Tooling: Trade Deal API & Spectator Experience (T185-186)

**Trade Deal Fixes (Critical):**

Three bugs discovered and fixed in the trade proposal system:

1. **Backwards deal direction.** `propose_trade` was calling `SendWorkingDeal(PROPOSED)` without first opening a diplomacy session via `DiplomacyManager.RequestSession(me, target, "MAKE_DEAL")`. This caused deals to appear as if the OTHER player was proposing to us — essentially cheating. The game's own `DiplomacyActionView.lua:457` always opens a session first. Fixed by adding `RequestSession` before `SendWorkingDeal` in both `build_propose_trade` and `build_form_alliance`.

2. **HUD disappearing after trade proposals.** `RequestSession` triggers `DiplomacyActionView_HideIngameUI` → `BulkHide(true, "Diplomacy")` + `Input.PushActiveContext(Diplomacy)` (InGame.lua:316). Our session cleanup via `CloseSession`/`AddResponse` does NOT trigger the reverse. Without calling `LuaEvents.DiplomacyActionView_ShowIngameUI()`, the entire HUD (top bar, unit panel, end turn button) disappears permanently. Fixed by adding `ShowIngameUI()` after ALL diplomacy session cleanup in 5 functions: `propose_trade`, `form_alliance`, `propose_peace`, `send_diplo_action`, `diplomacy_respond`.

3. **dismiss_popup was slow and incomplete.** Old implementation: Phase 1 looped through every Lua state with "Popup"/"Wonder"/"Moment" in its name (15+ TCP roundtrips). Phase 2 checked 9 named popups individually (9 more roundtrips). Never handled diplomacy screens (`DiplomacyActionView`, `DiplomacyDealView`, `LeaderScene`). New implementation: single batched InGame Lua call checking all popup AND diplomacy screen names, includes `ShowIngameUI()` and camera reset. Phase 2 (slow per-state scan) only runs if Phase 1 found nothing.

**Spectator Experience Improvements:**

The game was unwatchable for spectators — camera never followed actions, and event popups were instantly dismissed before they could be read.

*Camera follow:* Added `UI.LookAtPlot(x, y)` to 8 action builders:
- Unit actions: `build_move_unit`, `build_attack_unit`, `build_found_city`, `build_improve_tile`
- City actions: `build_produce_item`, `build_purchase_item`, `build_make_trade_route`, `build_purchase_tile`

*Popup display delay:* Changed `end_turn` popup handling:
1. Removed upfront `dismiss_popup()` call — event popups (wonders, techs, disasters, era changes) now render naturally instead of being pre-dismissed
2. Added 1.5s display delay before dismissing blocking popups mid-turn — spectators see the popup content before it's cleared

**Files changed:** `lua_queries.py` (camera follow in 8 functions, diplomacy session fixes in 5 functions), `game_state.py` (dismiss_popup rewrite, end_turn popup timing), `CLAUDE.md` (trade/alliance documentation).

### Tooling: Great Person Abilities & Purchase Tools (T187)

**Problem 1 — GP abilities invisible.** `get_great_people` showed class, name, era, and cost — but not what the Great Person actually *does*. Without ability descriptions, patronize/reject decisions are blind.

**Investigation:** Great Person abilities come from a 3-tier fallback chain in the game data:
1. `ActionEffectTextOverride` on `GreatPersonIndividuals` — direct localized text (best)
2. `LOC_GREATPERSON_<NAME>_ACTIVE` — localization key pattern
3. Synthesized from `GreatPersonIndividualActionModifiers` + `GreatPersonIndividualBirthModifiers` + `GreatWorkCollection` — parsed modifier chains

Added `getAbility(idx)` Lua function implementing all 3 tiers. Now shows: `Ability: Instantly creates a Bombard unit with 1 promotion level.`

**Problem 2 — No GP purchase/reject tools.** The game's `get_great_people` tool showed available GPs but there was no way to patronize (buy with gold/faith) or reject (pass to the next GP in that class). Had to use raw Lua.

**Investigation:** Found the full GP action API in `GreatPeoplePopup.lua:886-931`:
- `Game.GetGreatPeople():CanRecruitPerson(me, idx)` / `CanPatronizePerson(me, idx, yieldIdx)` / `CanRejectPerson(me, idx)`
- `GetPatronizeCost(me, idx, yieldIdx)` / `GetRejectCost(me, idx)`
- PlayerOperations: `RECRUIT_GREAT_PERSON`, `PATRONIZE_GREAT_PERSON`, `REJECT_GREAT_PERSON`
- `PARAM_GREAT_PERSON_INDIVIDUAL_TYPE` uses raw individual ID (same as GameInfo Index, NOT Hash)
- `PARAM_YIELD_TYPE` uses `YieldTypes.GOLD` (2) or `YieldTypes.FAITH` (5)

**Solution:** Added 3 new MCP tools: `recruit_great_person`, `patronize_great_person`, `reject_great_person`. Enhanced `get_great_people` output to show `[CAN RECRUIT]` tag, patronize costs (gold/faith), and ability descriptions. `individual_id` field added for action targeting.

**Files changed:** `lua_queries.py` (GP ability query, patronize costs, 3 new action builders), `game_state.py` (3 new methods, narration updates), `server.py` (3 new MCP tools).

### Tooling: NaturalWonderPopup HUD Crash Fix (T188)

**Problem:** Discovering Ha Long Bay triggered the NaturalWonderPopup. `dismiss_popup` Phase 1 caught the cinematic camera mode and set `dismissed=True`, preventing Phase 2 from running. Phase 2 would have called `Close()` in the popup's own Lua state. Instead, the popup was hidden via `SetHide(true)` which does NOT fire `LuaEvents.NaturalWonderPopup_Closed()`, leaving InGame.lua's `m_bulkHideTracker` counter elevated at 1.

**Result:** All 5 UI group containers (WorldViewControls, HUD, PartialScreens, Screens, TopLevelHUD) stayed hidden. The entire HUD disappeared — no top bar, no unit panel, no end turn button.

**Investigation:**
- `ContextPtr:BulkHide(false, ...)` is a C++ method — completely different from InGame.lua's local `BulkHide()` function
- `UI.ToggleHideUI()` (F10 key) is yet another mechanism — cycles between 3 states, partially restored top bar only
- All UI elements reported `isHidden=false` because their **parent containers** were hidden, not the elements themselves
- The real mechanism: `LuaEvents.NaturalWonderPopup_Shown()` → InGame.lua `BulkHide(true, "NaturalWonder")` increments `m_bulkHideTracker` counter → hides 5 UI groups
- Only `LuaEvents.NaturalWonderPopup_Closed()` fires `BulkHide(false, "NaturalWonder")` which decrements the counter back to 0

**Fix:** Added Phase 3 safety net to `dismiss_popup()` — after ANY dismiss (Phase 1 or 2), always fires ALL ExclusivePopupManager Close LuaEvents:
```python
pcall(function() LuaEvents.NaturalWonderPopup_Closed() end)
pcall(function() LuaEvents.WonderBuiltPopup_Closed() end)
pcall(function() LuaEvents.ProjectBuiltPopup_Closed() end)
pcall(function() LuaEvents.EraCompletePopup_Closed() end)
pcall(function() LuaEvents.NaturalDisasterPopup_Closed() end)
pcall(function() UI.ReleaseCurrentEvent() end)
```

Also fixed Phase 1: added `NaturalWonderPopup` to popup names list, corrected `DiplomacyActionView_HideIngameUI` → `ShowIngameUI` (was firing HIDE instead of SHOW!), added `UI.ClearTemporaryPlotVisibility("NaturalWonder")` to cinematic reset.

**Key discovery:** The ExclusivePopupManager BulkHide counter is the master UI visibility gate. Any popup that calls `_Shown()` LuaEvent without a matching `_Closed()` will permanently hide the HUD. The safety net approach — firing all Close events after every dismiss — is aggressive but safe because `pcall` swallows errors when no popup is active, and the counter can't go below 0 (InGame.lua checks before decrementing).

**Files changed:** `game_state.py` (dismiss_popup Phase 3, Phase 1 fixes).

### Turns 189-193: Production Pipeline & Diplomatic Tooling Gap

**Gameplay:**
- T189: Set Aquileia → Bank (13t), Mediolanum → Commercial Hub at (18,8). Activated James of St. George at Lugdunum for instant walls (1 charge used, 1 remaining).
- T190: Rome → Trader (3t), Lugdunum Commercial Hub complete → Market (7t). Builder farmed (12,12). New trader sent to Valletta (city-state trade route quest for envoy).
- T191: Mercantilism civic complete → Naval Tradition. Sanitation tech complete → Industrialization (boosted, 4t). Rejected America's bad trade offer (3 gpt for our only Furs copy — losing the amenity isn't worth it).
- T193: Rome → Stock Exchange (9t), Ostia → Bank (11t). Builder planted SPICES at (14,7) — luxury improved! Builder quarried STONE at (18,12). Dmitri Mendeleev (Great Scientist) auto-recruited, spawned at Rome. New trader sent to Meroë (Nubia) for 6 gold/turn.

**Friendship Declaration Bug (Critical Tooling Gap):**

All 3 civs (America +11, Nubia +19, China -1) are FRIENDLY. Attempted `send_diplomatic_action(action="DECLARE_FRIENDSHIP")` on all three. Tool returned raw BulkHide debug output (`"Request to BulkHide( false, Diplomacy ), Show on 0 = -1"`) instead of ACCEPTED/REJECTED. Diplomacy check confirmed: no friendships declared.

**Root cause investigation:**
1. `_action_result()` takes `lines[0]` — the BulkHide debug print from `ShowIngameUI()` was captured as the first line, masking the actual OK/ERR result.
2. The friendship Lua code uses `AddResponse(POSITIVE)` + `CloseSession()` in a tight loop. But `CloseSession()` terminates the session before the AI processes the friendship acceptance. The friendship never completes.
3. `DiplomacyManager.RequestSession(me, target, "DECLARE_FRIENDSHIP")` doesn't actually create a session — `FindOpenSessionID()` returns nil. The action is fire-and-forget but state doesn't change same-frame.
4. `DiplomacyManager.SendAction(me, target, hash)` — executes without error but state also doesn't change same-frame.

**Fixes applied:**
1. **`_action_result()`**: Now scans ALL lines for OK:/ERR: prefixes instead of just `lines[0]`. Handles spurious output from LuaEvent callbacks.
2. **`build_send_diplo_action()`**: Rewrote to use `AddStatement(sid, me, actionHash)` to formally propose the action through the diplomacy system (instead of `AddResponse` which only responds to AI dialogue). Session cleanup loop uses `AddResponse(POSITIVE)` without premature `CloseSession`.

**Game crash discovery:** Attempting to `AddStatement` a DECLARE_FRIENDSHIP action hash on a MAKE_DEAL session caused a C++ crash. **Never mix session types.** The diplomacy engine has no safety check for mismatched statement types, and the resulting out-of-bounds access kills the process.

**Open question:** Friendship declarations may be inherently async — processed on the next frame/turn rather than same-frame. The correct approach may be: fire the action, return "PROPOSED", and verify on next `get_diplomacy` call. Need to test after game restart.

**Files changed:** `lua_queries.py` (build_send_diplo_action rewrite), `game_state.py` (_action_result fix).

### Turns 193-207: Friendship Fix, Monarchy, & the Factory Era

**Friendship Declaration Root Cause (Critical Discovery):**

Deep investigation into the game source `DiplomacyActionView.lua` revealed the actual root cause: **session strings differ from DIPLOACTION_ names.** The button for "Declare Friendship" maps to session string `"DECLARE_FRIEND"` — NOT `"DECLARE_FRIENDSHIP"`. Our code was calling `RequestSession(me, target, "DECLARE_FRIENDSHIP")` which silently creates no session (returns nil).

**Correct session string mapping:**
| Action | Session String |
|--------|---------------|
| DECLARE_FRIENDSHIP | `"DECLARE_FRIEND"` |
| DIPLOMATIC_DELEGATION | `"DIPLOMATIC_DELEGATION"` |
| RESIDENT_EMBASSY | `"RESIDENT_EMBASSY"` |
| DENOUNCE | `"DENOUNCE"` |
| OPEN_BORDERS | `"OPEN_BORDERS"` |

**Correct flow:** Clean stale sessions → `RequestSession(me, target, sessionString)` → 2x `AddResponse(sid, me, "POSITIVE")` → `CloseSession(sid)` → `ShowIngameUI()`. No `AddStatement` needed (that crashes on mismatched session types).

Successfully declared friendship with Nubia (+1 favor/turn). America and China rejected (both NEUTRAL despite appearing FRIENDLY in some contexts).

**Delegation obsolescence discovery:** All delegation attempts returned invalid with no failure reasons. Investigation revealed `InitiatorObsoleteCivic = CIVIC_DIPLOMATIC_SERVICE` — once Diplomatic Service is researched, delegations (25g) become invalid. Must use embassies (50g) instead. Successfully sent embassies to all 3 civs.

**Gameplay (T193-207):**
- T194: Sent 2 envoys to Yerevan (became suzerain, 6 envoys). Philadelphia → Trader.
- T195: New era (Industrial). Chose Heartbeat of Steam dedication. Steam Power (boosted, 4t). Ravenna → Factory.
- T196: Lugdunum Market done → Water Mill. Activated James at Aquileia for medieval walls.
- T197-198: Steam Power + Divine Right complete. **Changed government to Monarchy** (6 slots: 2 military, 1 economic, 1 diplomatic, 2 wildcard). +1 housing per district is massive. Policies: Craftsmen (100% IZ adjacency), Conscription, Natural Philosophy, Charismatic Leader, Republican Legacy, Triangular Trade.
- T198: Recruited Jakob Fugger (Great Merchant). Activated at Rome's Commercial Hub (+200g, +2 envoy tokens). Sent 2 envoys to Mitla (reclaim suzerainty).
- T200: Strategic assessment — Score 506 (2nd), Science 158 (DOUBLE rivals), 40 techs (7 ahead). Science victory recommended at 60%.
- T201: Set Mediolanum → University, Rome/Ravenna/Ostia → Factories. Bought builder in Aquileia (440g) for coal at (8,8).
- T204: Exploration civic complete. Swapped Conscription → Drill Manuals (+1 coal/niter per improved tile). Set Colonialism civic.
- T206: Both coal mines complete at (16,20) and (8,8). Lugdunum → Trader (filled trade route slot). Mediolanum University complete → Industrial Zone.
- T207: Rome Factory complete → Coal Power Plant. Ravenna Factory complete → Coal Power Plant. Trader sent to Valletta (quest for envoy).

**State at T207:**
- Score: 522 (3rd) vs Nubia 533, China 528, America 519
- Science: **169/turn** (rivals ~70-80) | Culture: 63 | Gold: 1888 (+120/turn) | Faith: 372 | Favor: 190 (+0/turn, Nubia friendship active)
- 7 cities, 41 techs (tech leader), 26 civics
- Researching: Electricity (4t) | Civic: Colonialism (1t)
- Coal Power Plants building in Rome + Ravenna (factory regional bonus + power)
- Friendship with Nubia, Embassies with all 3 civs, Suzerain of Yerevan + Mitla
- 6 active trade routes out of 9 capacity

**The T208 Freeze (InGame State Corruption):**

Used `propose_trade` to sell surplus luxuries (Furs to Nubia, Spices to America). The tool was running OLD code that didn't properly open/close diplomacy sessions. This corrupted the InGame UnitManager state:

- ALL `UnitManager.CanStartOperation()` calls returned `false` for ALL units and ALL operation types
- Units couldn't move, skip, sleep, fortify, or do anything via InGame context
- GameCore FinishMoves worked but didn't sync to InGame
- Turn couldn't advance despite `UI.CanEndTurn()` returning true
- Not fixable via: FinishMoves, RestoreMovement, MoveUnit, InputContext reset, BulkHide toggle, EndTurnDirty events, AutoplayManager, QuickSave/QuickLoad LuaEvents

**Root cause:** The old `propose_trade` code opened a `MAKE_DEAL` diplomacy session without proper cleanup, leaving InGame's unit command processing locked. **Fix:** Reloaded T207 autosave + restarted MCP server to pick up fixed code.

**Files changed:** `lua_queries.py` (build_send_diplo_action rewrite with session_string_map), memory files (diplomacy-sessions.md, gameplay-bugs.md).

### Reflection at T207: The Production + Power Inflection

**Science supremacy is total.** 169 sci/turn vs ~75 for the nearest rival. 41 techs, 7+ ahead of everyone. We complete a tech every 3 turns. The science victory path is clear: Electricity → Radio → Rocketry → Spaceport → 4 space projects.

**Production is the binding constraint.** Coal Power Plants in Rome and Ravenna will provide power to boost factory output across 5 cities (factory bonus extends 6 tiles). This is the critical infrastructure for space projects, which need 1500-3000 production each.

**Gold hoarding needs to stop.** 1888 gold at +120/turn. Should be buying: builders (improve tiles), buildings (skip production time), tiles (secure resources). Anything above 500 gold should be invested.

**Diplomatic favor is underperforming.** 190 favor but only +0/turn displayed (Nubia friendship should give +1). Need alliances (requires Diplomatic Service which we have). Alliance with Nubia should be priority for +1 favor/turn + shared visibility.

**Tooling lesson:** NEVER use `propose_trade` or `send_diplomatic_action` on an unrestarted MCP server after code changes. The InGame state corruption from bad diplomacy sessions is unrecoverable without a reload.

---

### T209-212: Oxford University, Trade Routes, Second Freeze

**T209:** Recruited Filippo Brunelleschi (Great Engineer, +315 prod to wonder). Ravenna Coal Power Plant came online — first powered city. Colonialism civic completed. Rejected America's bad deal. Sent 2 envoys to Caguana (now 6). Set Opera and Ballet civic.

**T210-211:** Moved Brunelleschi toward Ravenna's IZ at (17,14). Built coal mines at (8,8) and (16,20). Set Lugdunum → Trader.

**T212 — Electricity Era:**
- Electricity tech complete! Flight (9t) researched next — on path to Rocketry
- Aquileia finished Stock Exchange → Industrial Zone at (7,9) with +1 adjacency
- Oxford University requires placement coords (it's a wonder, not building) — set at (15,12) adjacent to Campus
- Brunelleschi activated on (15,12) — Oxford reduced from 20 to 14 turns
- Set up 3 trade routes: 2× Meroë (12-13 gold each), 1× Valletta (quest envoy)
- Gold: 2529 (+156/turn). Score: 541 (1st)

**T212 FREEZE — InGame UnitManager frozen again:**
China diplomacy encounter appeared between T211-212. Responded POSITIVE, session auto-closed. But then ALL unit operations returned false — same symptom as T208. Root cause analysis revealed TWO bugs:

1. **`diplomacy_respond` bug**: When the session continues after CloseSession (game creates new goodbye-phase session), the code reached the `SESSION_CONTINUES` path which did NOT call `ShowIngameUI()`. This left the DiplomacyActionView's state partially active.

2. **WonderBuiltPopup infinite loop**: 3+ wonder events queued. `dismiss_popup` Phase 1 (SetHide) doesn't release ExclusivePopupManager engine locks. Phase 2 (Close() in own state) was SKIPPED when Phase 1 found anything. So popups kept regenerating from the engine event queue.

**Combination**: The diplomacy encounter + unresolved ExclusivePopupManager locks together created an irrecoverable InGame state corruption.

**Three fixes applied:**
1. `diplomacy_respond`: Now calls `ShowIngameUI()` in ALL paths including SESSION_CONTINUES
2. `dismiss_popup` Phase 2: Always runs (not skipped when Phase 1 finds something), loops up to 20× to drain engine event queue
3. `end_turn`: Pre-dismisses popups before attempting turn advance

**Reload required:** T211 autosave. Need MCP server restart to pick up fixes.

### Turns 216-221: Great People, Volcanic Destruction, Blocker Hardening

**T216-218: Great Person activations & trade routes**
- James Young (Great Scientist) activated on Rome's Campus → bonus science
- Filippo Brunelleschi (Great Engineer) activated at Oxford University site (15,12) — reduced from 10 to 5 turns
- Set up 3 trade routes (2× Meroë, 1× Baltimore)
- Builders farming tiles around empire

**T218-220: Volcanic eruption crisis at Aquileia**
- Vesuvius erupted, pillaging Aquileia's Campus, Commercial Hub, AND Industrial Zone
- Workshop being built on the IZ became a **ghost queue entry** (hash=0, Location=-9999,-9999)
- InGame BuildQueue has NO Remove/Clear methods — the corruption is permanent
- Adam Smith (Great Merchant) recruited → activated on Commercial Hub for +500 gold
- Upgraded Musketman to Line Infantry. Promoted Pingala with Space Initiative (+30% space projects)

**T221: Triple blocker crisis & fixes**
Three blockers stacked, each requiring manual Lua intervention:
1. **Stale envoy notification** — `ENDTURN_BLOCKING_GIVE_INFLUENCE_TOKEN` with 0 tokens available (game bug). Fix: `SetGivingTokensConsidered(true)`
2. **Civic desync** — InGame `GetProgressingCivic()` returns stale value (completed Opera & Ballet) while GameCore shows -1. `UI.RequestPlayerOperation(PROGRESS_CIVIC)` silently fails. Fix: GameCore `SetProgressingCivic(idx)` directly
3. **Production queue corruption** — Aquileia's ghost entry blocks turn. Fix: `NotificationManager.Dismiss(me, nid)` to force-dismiss the production notification

**Code changes (5 edits across 2 files):**
1. `end_turn` envoy auto-resolve: clears stale envoy blocker when 0 tokens available
2. `end_turn` production corruption: attempts `NotificationManager.Dismiss()` on ghost queue entries
3. `set_civic` GameCore fallback: verifies InGame accepted the civic, falls back to `SetProgressingCivic` on desync
4. `build_set_civic_gamecore()`: new Lua query for GameCore civic setting
5. `BLOCKING_TOOL_MAP`: added envoy blocker entry

**T222: AI turn hang (America) — forced reload to T221**
After ending T221 successfully, America's AI (player 1) hung during T222 processing for 15+ minutes. Investigation:
- All 12 American units had full moves (AI hadn't started processing any)
- No popups, diplomacy sessions, or notifications found
- City queues all normal from InGame context
- Settler on deep ocean (TERRAIN_OCEAN) and Great Writer on water — suspicious but likely coincidental
- No Lua API exists to force-end another player's turn (C++ controlled)
- Only destructive option found: `Game.RetirePlayer` (kills the civ)
- **Reloaded T221 autosave**

**Empire state at T221:** Science 159.7/turn, Gold 4186 (+117/turn), 7 cities, Score 574 (2nd behind Nubia 582). Researching Replaceable Parts (4 turns). Aquileia has 3 pillaged districts + corrupted queue.

### Sidequest: Programmatic Game Launch & Save Loading

**Problem:** AI turn hang at T221→222 requires reloading autosave. Doing this manually is tedious and breaks the automation loop. Need programmatic save/load.

**Research findings — FireTuner protocol at main menu:**
- Port 4318 is OPEN at main menu (TCP accepts connections)
- But handshake gets NO response — FireTuner protocol handler only active in-game
- GameCore/InGame Lua states don't exist at the main menu
- Cannot use MCP tools to interact with the main menu at all

**In-game save/load API (InGame Lua context only):**
- `Network.SaveGame(gameFile)` — synchronous, works for quicksave
- `Network.LoadGame(fileEntry, ServerType.SERVER_TYPE_NONE)` — needs async file query first
- `UI.QuerySaveGameList()` → async callback via `LuaEvents.FileListQueryResults`
- Two-step pattern: query saves → stash in `ExposedMembers` → second call loads
- `Network.LeaveGame()` required before `Network.LoadGame()`
- After load: entire Lua environment destroyed and rebuilt, TCP connection survives

**New MCP tools added:** `quicksave`, `list_saves`, `load_save` — work when in-game via FireTuner.

**Bypassing the Aspyr launcher:**
- Steam launch option: set `Civ6_Exe_Child %command%` to skip Aspyr launcher GUI
- `open "steam://run/289070"` then launches directly to game
- `pkill -9 -f Civ6` reliably kills the game (osascript quit does NOT work)

**AppOptions.txt — PlayNowSave:**
- Located at `~/Library/Application Support/Sid Meier's Civilization VI/Firaxis Games/Sid Meier's Civilization VI/AppOptions.txt`
- `PlayNowSave <name>` changes main menu to show "Play Now" button instead of normal menu
- Tried `AutoSave_0221` (no extension) and full path — both show "Play Now" but clicking fails to load
- Tried `AutoSave_0221.Civ6Save` — also fails after clicking
- The save loads briefly but then errors out; likely needs a specific internal format or relative path
- **Conclusion: PlayNowSave is unreliable for autosaves. Don't use it.**

**OCR-based menu navigation (working approach):**
- macOS Vision framework (`VNRecognizeTextRequest`) for text recognition on screenshots
- `screencapture -x` for screenshots, Quartz `CGEventCreateMouseEvent` for clicks
- Vision returns bounding boxes in normalized coords (0-1, origin bottom-left) — must flip Y and scale by image dimensions, then divide by 2 for Retina
- **This works reliably:** OCR finds "Play Now" text, calculates screen coords, clicks it
- Next step: build full menu navigation harness (Single Player → Load Game → select save file)

**Key engine facts discovered:**
- Autosaves at `~/Library/Application Support/Sid Meier's Civilization VI/Sid Meier's Civilization VI/Saves/Single/auto/AutoSave_NNNN.Civ6Save`
- `EnableTuner 1` and `EnableDebugMenu 1` in AppOptions.txt
- Game renders at 1280x800 scaled to 146% on Retina displays
- `Civ6_Exe` (8.8MB) is parent/launcher, `Civ6_Exe_Child` (60.8MB) is the actual game
- AI turn hang: confirmed via web research that C++ AI pathfinding loop is inaccessible from Lua. Land units on ocean tiles cause infinite pathfinding loops. Only fix is reload.

**Full menu navigation harness built and integrated as MCP tools:**

4 new MCP tools for game lifecycle management:
- `kill_game` — kills Civ 6, waits 10s for Steam to deregister
- `launch_game` — starts Civ 6 via Steam, waits for process + main menu
- `load_save_from_menu(save_name)` — OCR-navigates: Single Player → Load Game → Autosaves → select save → Load Game button → CONTINUE GAME
- `restart_and_load(save_name)` — full recovery: kill + launch + OCR load (60-120s)

Safety guardrails for automated agents:
- All process names, Steam app ID, and save directory are hardcoded constants
- No config file modifications (AppOptions.txt is never touched)
- No arbitrary system commands — only Civ 6 process management
- pyobjc GUI deps are optional (`[launcher]` extra) — tools fail gracefully without them

OCR fix: "Load Game" appears twice on the load screen (title at top, button at bottom). Added `prefer_bottom` parameter to `_find_text()` — step 5 (clicking the button) uses `prefer_bottom=True` to disambiguate.

**Tested:** `restart_and_load("AutoSave_0221")` successfully killed game, relaunched via Steam, navigated all 6 menu steps via OCR, and loaded T221 save. MCP connection verified with `get_game_overview`.

**Files:** `src/civ_mcp/game_launcher.py` (new, 340 lines), `src/civ_mcp/server.py` (+4 tools), `pyproject.toml` (`[launcher]` optional deps).

### Reflection at T221: The Road to Space

**State at T221:**
- Score: 574 (2nd behind Nubia 582)
- Science: **166/turn** (rivals: America 93, China 87, Nubia 85) — nearly **2x** the nearest rival
- Culture: 63.6 (rivals: Nubia 135, America 116, China 115) — **half** the weakest rival
- Gold: 3936 (+147/turn) — massive stockpile, hoarding problem
- Faith: 524, Favor: 216 — both sitting idle
- 7 cities, 45 techs (7 ahead of China at 38), 27 civics
- Military: 517 strength (strongest by far, America 2nd at 322)
- Explored: 53% of land
- 4 cities had corrupted production queues from volcanic eruptions — now fixed
- Diplomatic VP: 6/20 (leading all civs)

**The Science Victory Path**

Science Victory is the clear recommendation at 60%. Nobody has started the space race. We lead with 45 techs, 7 ahead of the nearest rival, and produce nearly double the science. The tech path to Rocketry:

1. **Replaceable Parts** (researching, 5 turns, boosted) → Infantry, Food Market
2. **Computers** → leads toward modern era
3. **Advanced Flight** → Fighters, Bombers
4. **Rocketry** (Atomic era) → Spaceport district

Rough timeline: Rocketry by ~T240, Spaceport built by ~T250-255, 4 space projects by ~T290-310. That's a Science Victory around T300 if production holds.

**The Binding Constraint: Production**

Science isn't the problem — production is. Each space project needs 1500-3000 production. Current city production:
- Rome: 46/turn (Coal Power Plant done, Factory done — best city)
- Ravenna: 65/turn (highest, but building Museum now)
- Aquileia: 37/turn (Workshop starting, IZ pillaged)
- Ostia: 48/turn (Stock Exchange building)
- Philadelphia: 24/turn (Workshop building)
- Mediolanum: 21/turn (Workshop starting)
- Lugdunum: 29/turn (Stock Exchange building)

At 46 prod/turn, Rome would take 33-65 turns per space project. **Unacceptable.** Need to reach 80+ production in the Spaceport city. The path:
1. Ruhr Valley wonder in Rome/Ravenna (+20% prod, +1 per mine/quarry) — probably the single most impactful build
2. Coal Power Plants in all cities with IZ → +4 production per building
3. Workshop → Factory chain in Aquileia, Mediolanum, Philadelphia
4. Production policies: Five-Year Plan, Craftsmen, etc.

**What We Must Do to Win**

*Critical (do NOW):*
1. ~~Set research~~ Done (Replaceable Parts)
2. ~~Fix 4 corrupted production queues~~ Done
3. Spend the 3936 gold — buy buildings to skip production time, buy tiles, buy builders
4. Advance the turn (stuck on a blocker — need to dismiss popup)

*Next 20 turns (T221-240):*
5. Research path: Replaceable Parts → Chemistry → Rocketry (trace exact prereq chain)
6. Build Workshop → Factory → Coal Power Plant in every city with an IZ
7. Build Ruhr Valley (massive production wonder) in Ravenna (65 prod/turn)
8. Activate Adam Smith (Great Merchant, 1 charge) for gold/economic boost
9. Declare friendship with America (FRIENDLY +5, eligible)
10. Vote aggressively in World Congress — we have 216 favor and lead at 6 VP

*Turns 240-260:*
11. Research Rocketry → Build Spaceport in Rome (highest adjacency + Pingala's Space Initiative)
12. Get all cities to Workshop/Factory/Power Plant for regional production bonuses
13. Target 80+ production in Rome for space projects
14. Continue accumulating Diplomatic VP as backup victory path

**What Could Go Wrong**

1. **AI turn hang repeats.** America's AI has hung before on T222. We now have `restart_and_load` to recover, but each reload costs time. The root cause (land units on ocean tiles) may recur.
2. **Culture deficit.** 63 vs 115-135 means slow civic progression. We may miss critical policies (Democracy government, New Deal policy). Building a Museum in Ravenna helps but won't close the gap.
3. **Gold hoarding.** 3936 gold earning nothing. Every turn of hoarding is wasted yield. Need to invest aggressively: buy workshops, buy buildings, buy tiles.
4. **Volcanic eruptions.** Vesuvius has already pillaged Aquileia's districts twice. Another eruption could destroy the IZ chain we're rebuilding. Consider moving production focus away from Vesuvius cities.
5. **Another civ wins first.** China at 87 sci/turn with 38 techs could reach space race by T280-290. We need to maintain our 7-tech lead.

**The 3936 Gold Problem**

This is the most actionable issue. With 3936 gold and +147/turn, we should immediately:
- Buy Workshop in Mediolanum (780g) — saves 8 turns of 21 prod/turn
- Buy Workshop in Aquileia (780g) — saves 5 turns of 37 prod/turn
- Buy builders for tile improvements (470g each)
- Buy tiles for strategic resources if any are adjacent

That's ~2000g invested immediately, still leaving 1900+ buffer. Much better than sitting at 3936.
