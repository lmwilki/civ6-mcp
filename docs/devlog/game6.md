# Game 6 — India (Gandhi) — Devlog

**Result: Defeat at T245 — France Religious Victory**
**Final Score: 408 (4th) vs France 821, China 611, Babylon 507**

This devlog reconstructs the full game from diary entries, with candid assessment of strategic decision-making, tactical execution, tooling limitations, and hypothesis quality at each phase.

---

## Civ Kit & Opening Plan

**Gandhi of India** — Faith/peacetime civ.
- **Satyagraha**: +5 faith per turn for each met civ that has founded a religion
- **Dharma**: Indian cities gain follower beliefs of all religions present (not just their own)
- **Stepwell**: Unique improvement (food + faith, bonus with Holy Site/farm adjacency)
- **Varu**: Unique unit replacing Horseman (-5 CS to adjacent enemies)

**Victory Plan (T0)**: Found a religion early using India's faith bonuses, then pivot to science. Use faith as a secondary economic engine. Stepwells for growth, religion for era score and follower belief stacking.

**Opening Build Order**: Scout → Slinger → Builder → Settler

---

## T1-20: The Opening

**T3**: Settled Delhi at (31,15) — river hills with Mercury and Ivory luxuries, mountains for Campus adjacency, geothermal fissure nearby. Strong site. Research: Mining → Astrology for Holy Site unlock.

**T11**: Scout built and automated. Started Slinger. Astrology research started (20 turns — painfully slow without natural wonder boost). Barb scout spotted near Delhi.

**T13**: Goody huts delivered a free scout + natural wonder Astrology boost (cutting research from 20t to ~9t). Exploration accelerated with 3 scouts covering different directions. Met Antananarivo (Cultural CS) and Akkad (Militaristic CS).

**T15**: Code of Laws complete — set Discipline (+5 vs barbs) and God King (+1 faith). Met China (Kublai Khan). Delegation rejected. Foreign Trade civic boosted.

**T20 Strategic Checkpoint**: Score 24, leading (China 20). 1 city, pop 2, 25% explored. Gold 142 at +11/t. Faith 5 at +1/t. Sent delegation to China (accepted, +3 modifier).

### Assessment: T1-20

**Strategic**: Solid opening. The early goody huts were lucky — free scout and Astrology boost saved 10+ turns. God King for faith was correct for the religion plan. However, 1 city at T20 is already behind the expansion benchmarks in CLAUDE.md (should have 2 by T40). The explorer-heavy opening (3 scouts) was good for map knowledge but delayed military and expansion.

**Tactical**: Clean. No lost units, no failed moves. Barb scout noted but not engaged (correct — not a threat to Delhi with slinger building).

**Tooling**: Production didn't stick on the first `set_city_production` call — needed a retry. This was a known async issue. Research notification needed manual clearing — an early signal of the notification persistence bug that would plague the entire game. Diary mode activated and working.

**Hypothesis Quality**: Good. Predicted meeting first civ by T10-15 (happened T13). Predicted peninsula geography (confirmed). Correctly identified Satyagraha faith income as dependent on meeting religious civs (but wouldn't activate until a civ actually founds a religion — a subtle misunderstanding that turned out not to matter).

---

## T21-40: Delayed Expansion

**T22**: Builder completed (3 charges). Set Settler production (10 turns). All three civs now met: China, France (Eleanor), Babylon (Hammurabi).

**T23**: Astrology complete — Holy Site available. Best placement at (30,14) with +2 adjacency. But Settler takes priority over district placement. Research: Pottery for Granary.

**T24**: Met Babylon. Score 32, now leading (China 28).

**T27**: Killed a barb warrior but warrior dropped to 30 HP. Barb spearman (CS:25) at (36,34) forced retreat. Farm completed at (31,14).

**T35**: **City #2 (Agra) founded!** Purchased Monument (240g). Holy Site started in Delhi. Craftsmanship complete — unlocked policies. Set Early Empire civic for governors.

**T36**: **Pantheon Founded: Divine Spark** (+1 GP from Holy Sites, Campuses, Theater Squares). This accelerates Great Prophet race. Score 50 — game leading!

### Assessment: T21-40

**Strategic**: The Settler came at T34, which is late but within acceptable bounds for a faith-focused civ. The real mistake was building order: Builder before Settler meant the Builder arrived at T22 but the Settler didn't complete until T34. Should have built Settler first, Builder second — the 12-turn delay cost compound growth. Divine Spark was an excellent pantheon choice for the Great Prophet race.

**Tactical**: The barb engagement south was a net negative — warrior took heavy damage fighting a barb warrior on hills, then had to retreat from a spearman. Could have just avoided the engagement entirely since it was far from Delhi. Builder improvements (Maize farm, Copper mine) were well-prioritized.

**Tooling**: Research notification kept going stale every turn. Each turn required manual Lua clear. The fix was written but needed an MCP restart — and the user hadn't restarted yet, so I was manually working around it for 20 turns. This is a pattern: code fixes require server restart, which creates a gap between "fix identified" and "fix deployed."

**Hypothesis Quality**: Mixed. Predicted Settler by T30 (came T34 — delayed by builder priority). Predicted China at 1 city (correct, but they were catching up). Incorrectly assumed barb camp was at (27,31) based on approach direction — it turned out to be further south. Era score prediction (Golden Age achievable) was overly optimistic but turned out correct due to lucky era score from goody huts and city founding.

---

## T41-60: Religion Founded, But Falling Behind

**T44-46**: Holy Site almost done. China complained about our "weak empire" — a diplomatic modifier we couldn't ignore. Bought Trader in Agra (180g) for domestic route to Delhi.

**T48**: Trade route started (Agra → Delhi, +2F +1P). Cleared barb camp at (27,31). Military Tradition civic boosted.

**T52**: Upgraded slinger to archer (60g). Bronze Working researching for iron reveal.

**T56**: Settler heading to 3rd city site at (27,18). All 3 civs are declared friends. But score has slipped to 3rd (63 vs Babylon 73, China 68).

**T60 Strategic Checkpoint**: 2 cities, pop 3, 43% explored. Score 66, now 4th (China 78, Babylon 77, France 65). Era score 23/25 for Golden Age — settling 3rd city would clinch it. Science only 5.3/turn — critically low. Need Campus urgently.

### Assessment: T41-60

**Strategic**: This is where the game started slipping. At T60, I had only 2 cities and 5.3 science/turn. The CLAUDE.md benchmark says 3 cities by T60 — I was one city short. The delay was partly terrain (jungle/hills slowing settler movement) and partly production priority (Holy Site + Shrine + Settler instead of Settler first). The religion focus was correct for India's kit, but the opportunity cost of the Holy Site rush was a delayed 3rd city.

**Tactical**: The barb camp clear was good (+era score). Trader purchase for Agra was necessary (the city was stagnating at 0 food surplus). Archer upgrade was efficient.

**Tooling**: Missionary spread religion had no tool support yet — had to use raw Lua. The `set_research` notification bug was still being manually cleared each turn. Trade route tooling worked correctly on first try.

**Hypothesis Quality**: Predicted settling 3rd city by T55 (actually T62 — terrain costs underestimated). Predicted faith would trickle — correct but too slow (only 166 faith by T60 despite God King active). The era score prediction (23+3 = 26, Golden Age at 25) was accurate and actually achieved.

---

## T61-80: Religion Founded, 4th City Delayed

**T62**: City #3 founded. Chose Free Inquiry dedication for Classical Era. Promoted Magnus with Provision (settlers don't consume population) — a game-changing ability for expansion.

**T64-69**: **Great Prophet John the Baptist recruited! Founded Hinduism with Work Ethic (+production from faith adjacency) and Stewardship (+1 science per Campus, +1 gold per Commercial Hub in holy cities).** Religion is online. Score 87, still leading.

**T71-76**: Builder improving tiles. Delhi settler in production with Colonization policy (+50% settler production). Agra Campus building (very slow — 42 turns due to low production).

**T80**: Settler at target site (30,20) but used all moves to arrive. Will found T81. Score 120, still competitive.

### Assessment: T61-80

**Strategic**: Founding Hinduism at T69 was the key milestone. Work Ethic + Stewardship were excellent beliefs — they compound with district building. But the 4th city didn't arrive until T81, which is on the T80 benchmark (just barely making it). The real issue: Agra's Campus was going to take 42 turns at 4 production. That's a dead city contributing almost nothing to science.

**Tactical**: The Magnus Provision promotion was the right call — it enables settler spam without growth penalty. Builder charges were well-spent on luxuries (Mercury, Truffles) and farms. The warrior was finally brought home to Delhi after spending 30+ turns exploring/fighting barbarians in the south.

**Tooling**: Promotion desync emerged as a serious bug. `SetPromotion()` in GameCore doesn't advance the unit's level counter, so the game perpetually shows "needs promotion." This would become a recurring headache. No easy fix — the level counter API doesn't exist.

**Hypothesis Quality**: Predicted city #4 by T78-80 (actually T81 — close). Predicted era score sufficient for Normal Age (correct). Predicted Agra Campus completion time — grossly underestimated. The 42-turn Campus in a pop 2 city was a strategic error: should have built something faster or faith-purchased a builder to improve Agra's tiles first.

---

## T81-100: Spreading Religion, Science Engine Starting

**T82**: Calcutta (4th city) founded. Missionary purchased to spread Hinduism for Stewardship bonuses. Era score 39/38 — safe from Dark Age.

**T88-90**: Spread Hinduism to Delhi and Agra. Missionary heading to remaining cities. Currency researching for Commercial Hub. All friendships expired — re-declaration rejected (cooldown).

**T94-95**: Activated Great Scientist Aryabhata on Agra Campus (triggered tech eurekas). Built tobacco plantation. Theology completed — Temples and Apostles available.

**T100 Strategic Checkpoint**: 4 cities, pop 13, 58% explored. Score 166, 3rd place (France 198 leads). Science 14.4/turn — still very low. Behind in pop (12 vs 26 best), tech (12 vs 18 Babylon), cities (4 vs 5 France/China). Selected science victory path — need Campuses in every city.

### Assessment: T81-100

**Strategic**: This is the phase where I should have been alarmed. At T100, science was only 14.4/turn with 4 cities — way below the CLAUDE.md benchmark of 25+ science by T100. The problem was cascading: slow expansion → delayed districts → low yields → slower everything. I identified science victory as the path, but the foundation wasn't there yet. Critically, I noted France had 5 cities and stronger military, but didn't register the religious threat from French Catholicism.

**Tactical**: Aryabhata activation was well-timed. Religion spread to 4 cities means Stewardship bonuses coming online. Trade routes active. But Agra was stagnating at pop 2 (!) — a city that never grew because no one invested in food infrastructure there.

**Tooling**: Spread religion via raw Lua was working but tedious. The `spread_religion` action was eventually added to `execute_unit_action`. The purchase_item tool had a faith/gold bug — purchases intended for faith were charged as gold. This was not caught for many turns. The open borders diplomatic action caused AI turn hangs — had to be blacklisted.

**Hypothesis Quality**: Predicted science would hit 25+ by T120 (actually hit 45+ at T123 with Natural Philosophy). The science acceleration was faster than predicted due to Natural Philosophy policy (+100% Campus adjacency). But the strategic prediction — that France was "not a threat" at score 198 — was deeply wrong. France's score came from cities and religion, both of which would become existential threats.

---

## T101-120: Science Surges, But the Score Gap Widens

**T102**: 5th city (Mumbai) founded. Builder improving ivory. Diplomacy woke all units — a recurring disruption.

**T104**: Set Calcutta Campus. Delhi damaged by volcano (pop dropped to 2). Lost Antananarivo suzerainty.

**T109-110**: Delhi Campus started at (30,16) with +3 adjacency. Settler heading to 6th city site. Score 188, 3rd place. France 236, China 211. Era score 51/52 — need 1 more for Golden Age.

**T116-119**: Founded Mysore (6th city). Medieval Era — **Monumentality Golden Age!** Faith-purchased a builder. Bought Honey tile for amenities.

**T120 Strategic Checkpoint**: 6 cities. Delhi Campus + Library done — science jumped to 30+/turn. **Catholicism spreading to Mumbai.** Faith-purchased settler for 7th city. Era score 57/80 for next era.

### Assessment: T101-120

**Strategic**: The empire was finally hitting critical mass — 6 cities with campuses building. Natural Philosophy policy (+100% adjacency) was the science breakthrough. But **this is where the religious threat first appeared and I failed to prioritize it.** The T120 diary notes "Catholicism spreading to my Mumbai!" as a passing concern, but the response was limited to "counter French Catholicism with Missionary purchase." No urgency. No missionaries were actually purchased. This was the critical window — 120 turns in, with France already spreading to 2/4 civs, and I treated it as a footnote.

**Tactical**: Settling cities efficiently. Magnus Provision making settler spam painless. Monumentality Golden Age + faith stockpile enabled rapid expansion (faith-buy builders and settlers). Delhi volcano was bad luck but recoverable.

**Tooling**: Game crashed and reloaded multiple times. AI turn processing would hang, requiring `restart_and_load`. The promotion desync remained — the swordsman accumulated 7 phantom promotions because each `SetPromotion` call added a real promotion without advancing level. Eventually deleted the unit. `get_great_people` didn't show `individual_id` in its output — needed raw Lua to find the GP ID for patronization.

**Hypothesis Quality**: Predicted science would hit 30+/turn by T125 — it hit 45.9 by T123 (underpredicted the impact of Natural Philosophy). Predicted France's score lead came from "5 cities" — partially correct, but missed that religious spread was the real accelerant. **This is the key failing: the hypothesis about France was wrong, and the wrong hypothesis led to no counter-strategy.**

---

## T121-140: Peak Science, War Erupts, Religion Ignored

**T123**: Science surged to 45.9/turn — **now leading all civs** (France 40, China 40). Natural Philosophy policy carrying hard. Education researching for Universities.

**T127**: Deleted bugged swordsman. Education complete — Universities unlocked. Started University in Delhi (+3 adjacency campus). Engineering research for Aqueducts.

**T129**: **Feudalism complete — Natural Philosophy policy active.** Delhi Campus adjacency doubled from +3 to +6. Science at 54.6/turn.

**T130**: **7th city (Srinagar) founded.** Faith-purchased 2 missionaries and 1 builder. French missionary spotted near Srinagar. Science at 57/turn.

**T135**: Great Scientist Hildegard activated (+100 faith). Spread Hinduism at Mumbai. Delhi University complete — **science 73/turn, dominant lead.** Commercial Hub started.

**T137-140**: 3rd and 4th spreads at Mumbai. Religion counter-offensive ongoing. Military Engineering complete (reveals Niter). **But at T140: France has Cuirassier (CS:64) units. War is coming.**

### Assessment: T121-140

**Strategic**: This was the peak of the science game — 73 science/turn with Universities rolling out, clearly leading all civs. But the strategic disaster was already unfolding. The diary entries from this period show a pattern: science gets 80% of the attention, religion gets 20%. I was spreading Hinduism reactively (only after cities flipped) rather than proactively. I bought missionaries to counter French spread in my own cities but never sent missionaries to convert other civs' cities. France was quietly converting Babylon and China while I was focused on my own borders.

The CLAUDE.md playbook explicitly says: "IF any rival religion is majority in 50%+ of civilizations, this is an emergency." At T135, the diary notes "CULTURE VICTORY IMMINENT warning" but doesn't check religion status. The victory proximity alerts in `end_turn` were designed exactly for this — but I was racing through turns and not fully processing the warnings.

**Tactical**: Newton patronized (T178 in the diary, but planned here). Missionaries deployed to Mumbai for 4 spreads. Builder improvements continuing. Military fortified. Adequate defense positioning.

**Tooling**: The `purchase_item` tool was charging gold instead of faith for missionary purchases — the YIELD_FAITH parameter was being ignored. This was noted as a bug ("CRITICAL FINDING") but not fixed during gameplay. The missionaries still purchased (with gold), so the impact was treasury drain rather than failure. Religious unit faith purchases must NOT include PARAM_MILITARY_FORMATION_TYPE — this was discovered the hard way.

**Hypothesis Quality**: Predicted science would hit 65+ after Delhi University (actually 73 — underpredicted again). Predicted France culture victory threat — this was wrong; the real threat was religious. The diary mentions culture victory warnings but the actual imminent threat was religious. **This is a recurring pattern: I was tracking the wrong rival victory condition.** The hypothesis about France was always "culture or score threat" when it should have been "religious threat."

---

## T141-160: War with France — Catastrophic Losses

**T142**: Recruited Great Scientist. Game reloaded after AI hang at T141.

**T144**: Domestic trade route to Agra. Spread Hinduism at Srinagar. Delhi building builder.

**T147**: Purchased Apostle with Proselytizer promotion (400 faith). Machinery researching for Crossbowmen.

**T149-153**: **War with France erupted.** France attacked with Musketmen (CS:55), Knights, and multiple armies. Lost Srinagar and Mumbai within turns. Science dropped from 90+ to 84.5. Cities fell from 7 to 5.

**T158-164**: **Lost Hyderabad and Calcutta.** Down to 3 cities (Delhi, Agra, Mysore). Science crashed to 55.1. Score plummeted from 290 to 264.

**T164**: **Peace with France secured.** Reassigned governors. Started rebuilding.

### Assessment: T141-160

**Strategic**: This was the catastrophe. France declared war with massively superior military — Cuirassiers (CS:64), Musketmen (CS:55), Knights vs. my Crossbowmen (CS:30 melee, RS:40 ranged) and Warriors. I had no answer to their technological military advantage. Lost 4 cities in ~15 turns, destroying the science engine I'd spent 140 turns building.

The root cause was strategic: I invested everything in science and religion, nothing in military. At T150, my military strength was ~95 vs France's ~490. The CLAUDE.md playbook warns: "IF at war AND your military strength < enemy's AND you are not actively conquering cities: Propose peace after the 10-turn cooldown." I should have been preparing for this possibility — France was unfriendly with 2x my score and I had no defensive army.

**Tactical**: Defense was hopeless given the strength differential. Crossbowmen behind walls were the only viable tactic — and they did kill several French units — but France had overwhelming numbers. The 4-city loss was inevitable once war started.

**Tooling**: AI turn hangs required multiple `restart_and_load` operations. The China AI kept getting stuck in pathfinding loops — resolved by killing specific Chinese units via Lua before ending the turn. This workaround (kill a hung AI's unit) became a recurring pattern. The `CAN_ATTACK` display showed French units as attackable during peacetime — a display bug that didn't check war state.

**Hypothesis Quality**: The hypothesis at T140 was "France will continue religious spread — need domestic tourists via Theater Squares." This was partially right but missed the more immediate threat: France declaring war. The diary notes France had 8 units on the border but the hypothesis was "they're testing our resolve" rather than "they're about to attack." A human player would see the army massing and prepare. I saw the data but drew the wrong conclusion.

---

## T161-180: Post-War Recovery

**T164**: Peace secured. 3 cities remaining (Delhi, Agra, Mysore). Settled 4th city at (28,17). Activated Ibn Khaldun and Colaeus (Great People) for science and gold boosts.

**T170**: Gunpowder complete. Metal Casting researching. Popup blocking issues consuming turns.

**T175**: Delhi Bank complete. Agra food crisis fixed. Mysore loyalty stabilizing with Victor governor. Industrial Zone building in Delhi.

**T178-180**: **Patronized Isaac Newton for 900 faith!** Newton activated on Agra Campus — instant Library + University, +2 Science to all Universities empire-wide. Science recovered to 73/turn. World Congress voted.

### Assessment: T161-180

**Strategic**: Recovery was methodical but the damage was permanent. The 4 lost cities meant 4 lost Campuses, 4 lost districts, and population that took 140 turns to build. The Newton purchase (900 faith) was the right play — instant University in Agra dramatically accelerated science recovery. But the score gap was now insurmountable: France 476 vs India 297 at T164.

The fatal error was not pivoting strategy. Even after losing the war, the plan was still "rebuild science engine → space race." But France's religious victory was already at 3/4 civs by this point. The diary noted it but the response was "Kolar Holy Site will fix it" — a 15-turn fix for a 5-turn problem.

**Tactical**: Good rebuilding mechanics. Victor governor for loyalty. Settler with escort. Builder improvements. Newton activation was well-executed. But the Varu unique unit was terrible — CS:40 vs Cuirassiers at CS:64. India's UU was designed for Classical era, not Renaissance.

**Tooling**: World Congress voting required extensive tooling work. The auto-voter handler, interactive voting flow, and gate mechanism were all developed during this phase. Multiple iterations: auto-submit (broke), event handler (bare globals _G=nil bug), interactive gate (worked). The WC tooling consumed significant agent attention that could have gone to gameplay.

**Hypothesis Quality**: Predicted Srinagar would flip back from France via loyalty (correct — it eventually did). Predicted science recovery to 80+ by T190 (actually 73 by T180, close). But the hypothesis about religious defense ("Kolar Holy Site in 15 turns will fix it") was tragically wrong — 15 turns was far too late.

---

## T181-200: Religious Emergency Escalates

**T181**: 6 envoys to Nalanda for science bonus. 3 trade routes active. French border still hot — 8 units visible. Babylon Cultural Alliance + defensive pact active.

**T184**: Apostle spread at Kolar. Mysore flipped — lost to loyalty. Builder improving rice.

**T187-189**: Kolar Campus started. Builder improving tiles. Walls purchased for Kolar. French units retreating.

**T193**: Settler for 5th city. Policies swapped for defense (Bastions +6 defense, +5 ranged). Scientific Theory researching.

**T196**: **RELIGIOUS EMERGENCY**: France Catholicism majority in 3/4 civs including India (Delhi 5C/3H, Agra 3C/2H, Mysore 3C/1H — only Kolar holds Hindu). Purchased 2 missionaries at Delhi — **DISASTER: they were Catholic missionaries** (city majority was Catholic). Deleted them. Used Hindu Apostle to flip Delhi back. Purchased walls for Delhi.

**T200 Checkpoint**: 5 cities, pop 26. France at 2/4 Catholic majority (down from 3/4 after Delhi spread). Agra tied. Need Kolar Holy Site for Hindu missionary production.

### Assessment: T181-200

**Strategic**: The religious emergency finally got the attention it deserved — but 80 turns too late. The T196 missionary disaster (purchasing Catholic missionaries from Catholic-majority Delhi) was a direct consequence of not understanding the purchase mechanic: missionaries match the city's majority religion, not the player's founded religion. This wasted 380 gold and multiple turns of repositioning.

The fundamental problem was clear: **I had zero religious infrastructure.** One Holy Site in Delhi, no Shrine in any city except Delhi, no Temple, no Apostles, no Inquisitors. The entire religion game was "build one Holy Site, found the religion, then ignore it for 100 turns." This is the exact opposite of what India's kit demands.

**Tactical**: The Delhi flip-back was well-executed (Apostle spread). Defensive positioning was solid. The Bastions policy was a good call for crossbowmen. But the Catholic missionary purchase was an unforced error — should have checked city majority before purchasing.

**Tooling**: The `purchase_item` yield_type bug was finally understood: the faith parameter was being passed but the display showed gold costs. Actual deduction was from faith — confusing but functional in some cases. More critically, the purchase from Catholic-majority cities producing Catholic missionaries was not flagged by any tool. A human player would see the missionary's religion in the production queue.

**Hypothesis Quality**: Predicted "France needs China conversion to win, which is stalling" — partially correct but underestimated how quickly France could convert the remaining holdouts. Predicted Kolar Holy Site + missionaries would fix the problem — too optimistic about the timeline. The hypothesis at T196 was "if I can break Catholic majority in India, France drops to 2/4, buying significant time" — correct logic, but the execution gap (no Holy Site in Kolar, no missionary production capacity) made it academic.

---

## T201-245: World Congress, Final Defense, Defeat

**T201**: Changed to Merchant Republic. Activated Giovanni de Medici for free Bank + Market. Spread Hindu at Agra. Set Delhi to Castle. Killed Chinese Pike and Shot to bypass AI hang.

**T203**: Giovanni activated — Bank + Market in Delhi (major gold boost). Hindu spread at Delhi. Siege Tactics researching.

**T210**: War with France again. Crossbow defense along Delhi-Agra corridor. Varu attacked French Man-at-Arms. Era score 77/82 — Dark Age likely.

**T211-217**: Defensive war. Killed 7 French units (2 Cuirassiers, Bombard, 2 Man-at-Arms, 2 Knights, Musketman). Lost only 1 crossbow. **T217: Peace with France accepted!** Kolar set to Holy Site (16 turns).

**T219**: Activated Charles Darwin for 500 science (completed Ballistics). Accepted Babylon embassy. **Religious emergency: France Catholicism majority in 3/4 civs. 3/5 Indian cities Catholic. Need Kolar Holy Site + Shrine to produce Hindu missionaries.**

**T233**: Attempted faith-buy Missionary in Delhi — spawned as CATHOLICISM (majority religion). Deleted immediately (230 faith wasted). The same mistake as T196, repeated because no tooling prevented it.

**T236-238**: Kolar Holy Site completed. Shrine started (6 turns). Agra Commercial Hub completed. But the timeline was too slow — Shrine wouldn't finish until T242+, then need to actually produce missionaries.

**T239**: **World Congress session.** Deployed 420 favor across 2 resolutions (Migration Treaty targeting France, Mercenary Companies reducing military costs). Won both. This was the culmination of weeks of WC tooling development.

**T244**: Final pre-defeat state. 6 cities, 95.8 science/turn. Settler ready for 7th city. But France Catholicism had converted nearly all civilizations.

**T245**: **France wins Religious Victory. Game Over.**

### Assessment: T201-245

**Strategic**: The endgame was a race between two clocks: my science engine (which was competitive at 90+ sci/turn) and France's religious spread (which was unstoppable). The science clock lost. At T245, I had 95.8 science/turn and was researching Industrial-era techs — but the space race was still 80+ turns away. France's religious victory needed zero techs, zero production — just missionaries, which they'd been building for 150 turns.

The 2nd war with France (T210-217) was better managed than the 1st — killed 7 units and secured peace quickly. But it consumed turns and production that should have gone to religious defense.

The WC tooling was a significant engineering achievement — multiple iterations of auto-voter, interactive gate, event handler — but its gameplay impact was minimal (2 resolutions won, favor spent). The tooling development consumed far more agent attention than the favor it deployed was worth.

**Tactical**: Defensive combat was excellent in the 2nd war. Crossbowmen behind walls with Bastions policy dealt consistent damage. The Garde Imperiale (CS:70) never arrived before peace was signed. LOS blocking by forest/hills was a constant tactical constraint that the tool eventually learned to pre-check.

**Tooling**: The game-over detection feature was developed at T244-245 after the defeat screen blocked further play. This was the right feature — it prevents the agent from issuing commands into a dead game. The implementation checked `/InGame/EndGameMenu` visibility (the reliable signal) and used heuristic victory type detection (since `Game.TestVictory()` returns false on the defeat screen). The WC voting went through 6+ iterations before working reliably: auto-submit → event handler (\_G nil crash) → bare globals → interactive gate → queue_wc_votes with pre-registration.

**Hypothesis Quality**: The final hypotheses were resigned: "France religious victory is 5-10 turns away if unchecked. Hindu missionaries from Kolar are the counter." This was accurate but represented a failure to act earlier. The hypothesis at T238 ("France will NOT win religious victory this era — they still need to convert China") was wrong — France converted China by T245.

---

## Post-Mortem: What Killed This Game

### Primary Cause: Religious Victory Ignored for 150 Turns

France's religious spread was visible from T120 (Catholicism in Mumbai) but not treated as an emergency until T196 — 76 turns later. By T196, 3/4 civilizations were Catholic majority and India had 4/5 cities Catholic. The response was to start building a Holy Site in Kolar (a city founded at T116 that still didn't have a Holy Site at T236).

**The CLAUDE.md playbook explicitly warns**: "IF NOT playing a religious civ: Still check `get_religion_status` every 20 turns after T60." India IS a religious civ, making this even more critical. The playbook also says: "IF any rival religion is majority in N-1 of N civilizations: EMERGENCY." France hit 3/4 by T196 at the latest, possibly earlier. This should have triggered immediate counter-action.

### Secondary Cause: No Military Deterrent

France attacked because they could. At T150, French military was 490 vs India's 95. The CLAUDE.md playbook says: "Wartime Garrison Rule: IF at war, every city MUST have at least one military unit garrisoned." The lack of military investment meant:
1. No deterrent against French aggression
2. No ability to fight back when war came
3. Catastrophic city losses (4 cities in the first war)

### Tertiary Cause: Slow Expansion

City milestones:
| Turn | Cities | Benchmark |
|------|--------|-----------|
| 30 | 1 | 2 |
| 60 | 2 | 3 |
| 80 | 3 | 4 |
| 100 | 4 | 5 |

Consistently 1 city behind the benchmarks. Each missing city = missing Campus = missing yields = weaker position.

### What Went Right

1. **Science engine**: 95.8 sci/turn at T245, consistently leading all civs from T123 onward
2. **Natural Philosophy timing**: +100% Campus adjacency doubled science overnight
3. **Newton patronization**: 900 faith well-spent for instant University + empire-wide bonus
4. **Defensive combat**: Killed 7 French units in 2nd war with minimal losses
5. **WC tooling**: Successfully deployed 420 favor across 2 resolutions
6. **Game-over detection**: New feature correctly identifies defeat screen and victory type

### Tooling Developed During This Game

| Feature | Impact |
|---------|--------|
| WC voting gate + queue_wc_votes | Prevents blind WC sessions, deploys favor strategically |
| Game-over detection (EndGameMenu) | Stops agent from issuing commands into dead game |
| spread_religion action | Proper tool support for missionary/apostle spread |
| Promotion desync workaround | GameCore SetPromotion + FinishMoves bypass |
| AI hang diagnosis (IsTurnActive) | Identify hung AI player for targeted intervention |
| Production readback (CurrentlyBuilding) | GameCore verification after InGame RequestOperation |
| City attack (ALREADY_FIRED/NO_WALLS) | Clear error messages for city bombardment |
| LOS pre-check for ranged | ERR:NO_LOS before wasting attacks |

### Lessons for Game 7

1. **Check religion every 20 turns from T60.** Non-negotiable. Use `get_religion_status` and act on findings immediately.
2. **Build military proportional to neighbors.** At minimum, 1 garrison per city + 1 mobile army. Never let military strength fall below 50% of strongest neighbor.
3. **Expand faster.** Settlers are highest priority. 4 cities by T80 is the minimum.
4. **Don't tunnel-vision on science.** Science is the victory path, but surviving to win requires military and religious defense.
5. **Faith-buy missionaries from YOUR religion's holy city.** Never buy religious units from Catholic-majority cities.
6. **The WC tooling works.** Deploy favor aggressively for Diplomatic VP as a backup win condition.
7. **AI turn hangs are manageable.** Kill the hung AI's problematic unit, or restart_and_load. Budget 2-3 restarts per game.

---

## Meta: The Agentic Rig

This game exposed a fundamental tension in the agent architecture: **tooling development competes with gameplay for context window and attention.**

The WC voting system went through 6+ iterations during live gameplay (T238-239 alone has 8 diary entries from retries). Each iteration required: understanding the bug → writing a fix → telling the user to restart → retesting. This consumed roughly 30-40 turns of agent attention that could have been spent on strategic play.

Similarly, the promotion desync, AI turn hangs, and production readback bugs each consumed 5-10 turns of debugging. The agent was simultaneously playing Civ 6 and developing the tools to play Civ 6 — two full-time jobs sharing one context window.

The diary system itself was valuable for reconstruction but had a cost: 5 mandatory reflection fields per turn consumed output tokens and occasionally became formulaic ("No issues" for tooling, repetitive planning). The most useful diary fields were `strategic` (catching yield/score trends) and `hypothesis` (predictions to evaluate against outcomes). The `tactical` field was often just a move log, and `tooling` was either "No issues" or a multi-paragraph bug report.

**The sensorium problem from CLAUDE.md is real.** I had the tools to check religion status every 20 turns. The playbook told me to check. I simply... didn't, for 76 turns. Not because of tooling gaps — because of attention allocation. When science is surging and you're leading all civs in research, religion feels like someone else's problem. It isn't. The discipline to run the full strategic checkpoint on schedule — especially the parts that seem irrelevant — is the difference between surviving and losing to an invisible victory condition.
