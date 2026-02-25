# Game 11 — Mali (Mansa Musa) — Devlog

**Result: Science Victory at T271**
**Final Score: Mali 877 (#6) vs Gran Colombia 1151 (#1), Greece 1100, India 1085, Ottomans 982, Georgia 905**

A 271-turn science victory despite finishing last in score among surviving civilizations. Mali's gold engine funded rapid builder purchases and district construction, while a 10-city empire with strong Campus coverage drove the space race. The agent correctly identified Mali's gold-purchase synergy early and leveraged it throughout — buying builders, settlers, and military units with gold instead of suffering Mali's -30% production penalty. However, expansion was slow (3 cities at T80 vs the benchmark of 4), and the agent never achieved suzerainty over a single city-state in 271 turns. The Exoplanet Expedition launched at T243 but Gathering Storm's light-year travel mechanic — unknown to the agent — required an additional 28 turns of vessel transit plus a Terrestrial Laser project to accelerate it. Great Engineer Wernher von Braun's +1500 space production activation was the decisive play that shortened the vessel journey by ~7 light-years.

---

## Civ Kit & Opening Plan

**Mansa Musa of Mali** — Gold/faith economic powerhouse.
- **Songs of the Jeli**: City centers gain +1 faith and +1 food for each adjacent desert/desert hills tile
- **Saharan Merchants**: Mines receive +1 gold; -1 production and +4 gold from Mines over strategic/luxury resources; -30% production to all units/buildings
- **Suguba**: Unique district replacing Commercial Hub; gold/faith purchases discounted 20%
- **Mandekalu Cavalry**: Unique unit replacing Knight; adjacent traders immune to plundering

**Civ was randomly assigned.** The agent identified Mali's core loop immediately in the T1 diary: "Mali wants gold/faith engine: mines for gold, Holy Site for faith, Suguba for discounted purchases." The -30% production penalty makes conventional production painful — but gold purchases bypass it entirely, making Mali one of the strongest economic civs when played correctly.

**Victory Plan (T0)**: Science victory via gold economy. Mine everything for +4 gold, use gold purchases to bypass the production penalty, build Campuses for science. The agent planned: "T1-5: Build Scout, research Mining. T10-12: Consider Holy Site placement. T15: Second city settler."

**What actually happened to the kit**: The gold engine worked exactly as intended — the first builder was gold-purchased at T17 for 130g, and gold purchases remained the primary production method throughout the game. Mines generated massive gold income (+4 gold each from Mali's bonus). However, the Holy Site plan was repeatedly deferred. Despite planning for it from T1, the agent didn't build its first Holy Site until significantly later, missing the Great Prophet pool entirely. The Suguba was built in multiple cities and provided discounted purchases as intended. No Mandekalu Cavalry was ever produced — the agent went straight from Knights to modern units. Songs of the Jeli provided modest faith/food from desert adjacency but the agent never optimized city placement specifically for desert adjacency.

**Opening Build Order**: Scout → Slinger → Monument → Settler

---

## T1-20: Foundation & First Contact

**T1**: Founded Niani at (20,38) on a river with fresh water, surrounded by Plains Hills. Stone x2 and Copper nearby. Researched Mining first — the correct opener for Mali since mines are the foundation of the gold engine.

**T4-5**: Warrior explored east along a desert corridor, revealing Silver luxury at (24,38) and a mountain range forming a natural barrier to the south. Desert tiles east of the capital confirmed Mali's start bias.

**T6**: Scout completed and set to auto-explore. Slinger queued.

**T8**: Mining completed — first tech done. Switched to Pottery. Warrior discovered wheat floodplains at (24,34) and two more Silver luxuries. By this point, 4 Silver were visible — enormous trade leverage for later.

**T9**: Found Preslav (Militaristic city-state) at (24,30) and Geneva (Scientific city-state) at (29,31). Geneva's suzerainty bonus (+15% science in Campus cities) flagged as a priority target.

**T12**: Code of Laws civic completed. Set God King policy (+1 faith/turn) — first faith income. Foreign Trade civic began.

**T14**: **First major civ contact — Greece (Pericles)**. Mutual delegations exchanged. Warrior had pushed northeast past Geneva into Greek territory. Greece already at score 27 vs Mali's 14.

**T17**: Gold-purchased first builder for 130g — a signature Mali play that bypassed ~7 turns of -30% penalty production. Builder immediately began mining copper. Settler production started (7 turns).

**T20**: State of the empire: 1 city, pop 2, science 3.0/t, culture 3.6/t, gold 33 (+12 GPT), faith 8, military 44. Only 8% explored. Greece already founding its second city while Mali still on one. The agent noted: "Critical expansion deficit."

### Assessment: T1-20

**Strategic**: Mali's gold engine activated on schedule — Mining T8, first mine income T19, builder purchased T17. However, expansion was dangerously slow: 1 city at T20 with the settler still 4 turns out. The agent correctly identified this deficit but didn't prioritize the settler over the monument. A human Mali player would likely settler-first given the gold-purchase builder option.

**Rival context**: Greece already at score 27 vs Mali's 14. Only 1 of 7 rival civs met. The other 6 were expanding, scouting, and settling in territory Mali couldn't see — and wouldn't see for 100+ more turns.

**Tactical**: Exploration was competent — warrior pushed northeast finding 4 Silver, 2 city-states, and Greece within 20 turns. The builder purchase was the right call. Barbarian encounters were minimal (one scout spotted near Geneva, avoided).

**Tooling**: Clean first 20 turns. Scout auto-explore got stuck on a narrow coastal peninsula (T11) requiring manual intervention — a recurring issue with auto-explore in confined terrain.

**Hypothesis Quality**: T1 prediction "Expect to meet first neighbor by T8-10" was close (T14 actual). "Desert likely nearby given Mali start bias" confirmed immediately. The gold snowball hypothesis ("each mine = +4 gold, total GPT will jump to ~20+") proved accurate by T19.

---

## T21-40: Second City & Gold Engine Ignition

**T24**: Settler produced at T24, heading northeast to (23,36). First World Congress fired with 0 resolutions and 0 favor — nothing to do. Pericles praised us for leaving city-states alone (positive diplomacy event).

**T25**: **Disaster** — Builder killed by barbarians at (21,38) while units were immobilized from the diplomacy encounter skip. Lost 1 builder and the 3rd mine charge that would have triggered Craftsmanship eureka. The diplomacy skip bug (all units lose their moves after an AI encounter) had real consequences here.

**T28**: **Pantheon founded — Religious Idols** (+2 faith from mines on luxury/bonus resources). This was an excellent synergy pick for Mali: every mine on Silver, Copper, or Mercury generates both +4 gold (Mali mine bonus) AND +2 faith (Religious Idols). A single tile improvement now generates 6+ gold and 2 faith — the gold-faith dual engine the agent had been planning since T1.

**T29**: **Founded Tawdenni** at (23,36) — second city with desert hills adjacency for Songs of the Jeli faith/food bonus. Gold-purchased a builder immediately for the new city (130g). This is the core Mali pattern: produce settlers with production (which eats the -30% penalty), then instantly buy builders with gold (bypassing it).

**T31**: Slinger upgraded to Archer (40g). Trader built and sent to Geneva for +3 gold and envoy quest progress. Three warriors + archer now patrolling.

**T35**: Copper mine completed at (22,35) — the Religious Idols synergy tile: +2 gold (copper) + 4 gold (Mali mine bonus) + 2 faith (Religious Idols) = 6 gold and 2 faith from one improvement. GPT jumped to 22.6.

**T37**: **Friendship declared with Greece** — 30-turn protection. Pericles had 164 military vs our 86, so this was a critical diplomatic achievement. With Greek friendship secured, the agent could focus on economy and expansion.

**T39**: Appointed Pingala (The Educator) governor to Niani for +3 science/culture. Writing researching. Gold at 193 (+27 GPT).

**T40**: State of the empire: 2 cities, pop 4, science 5.0/t, culture 4.2/t, gold 221 (+27.4 GPT), faith 53 (+5.7 FPT), military 98. GNP rank #1 — but dead last in population and food. Only 10% explored with 6 of 7 rival civs still unmet. Era score 5/9 — dark age looming.

### Assessment: T21-40

**Strategic**: The gold engine was firing — 27.4 GPT at T40 is strong, and gold-purchased builders made up for the production penalty. Religious Idols was the ideal pantheon for Mali, creating a gold-faith dual engine from mines. However, only 2 cities at T40 against a benchmark of 3+ was concerning. Dead-last population and food is the price of Mali's production penalty — every city needs trade routes and granaries to compensate.

**Rival context**: Gran Colombia led at 349 score with 4 cities and 34 pop. Ottomans had 5 cities and 39 pop. Greece had 4 cities with 131 science — already 2.6x Mali's 5.0. Even Georgia and India had 5 cities each. Mali sat at 6th of 8 in score with the weakest population on the map. The agent's GNP #1 ranking masked a severe demographic deficit that would compound through the mid-game.

**Tactical**: The builder loss at T25 to barbarians was avoidable — units should never be left on exposed tiles when diplomacy encounters can freeze all movement. The barb camp south was never fully cleared despite sending warrior+archer pairs. The Greek friendship at T37 was well-timed and provided security for expansion.

**Tooling**: The diplomacy encounter unit-skip bug (T24-25) caused the builder death — a known issue where all units lose remaining moves after an AI diplomacy session. The agent adapted but lost a valuable builder in the process.

**Hypothesis Quality**: The T28 hypothesis about Religious Idols generating "12-16 faith/turn from 4 silver + copper + mercury mines" was directionally correct — by T40, faith was at 5.7/turn with only copper mined. The full potential would be realized as more mines came online. The "gold snowball" prediction continued to prove accurate with GPT growing from 16 to 27 in 20 turns.

---

## T41-60: Dark Age, Third City & Science Infrastructure

**T41**: **Dark Age entered** — era score only reached 5/9 at the era boundary. Chose Free Inquiry dedication, which gives +1 era score per Eureka and per science building. This turned the Dark Age into a recovery mechanism: every tech boost and Campus/Library would now count double toward escaping the Dark Age.

**T43**: Barb camp south kept spawning warriors. Gold-purchased an archer (160g) at Niani to deal with the threat. Three barb warriors clustered around camp at (22,44). This delayed the settler purchase — gold dropped to 150.

**T47**: Promoted Pingala with Researcher (+1 science per citizen). Niani science jumped from ~6 to ~10. Killed a barbarian warrior. Started Political Philosophy civic.

**T48**: **Gold-purchased settler** (290g), leaving only 10g. At +30 GPT this recovered quickly. Bronze Working completed, revealing Iron at (18,35) and (20,42). Both within city ranges — a strong strategic position.

**T50**: **Started Campus in Niani** at (21,36) with +3 adjacency bonus ("Splendid!"). Killed another barbarian with the promoted archer. Era score at 8/13.

**T53**: **Founded Awdaghust** at (19,42) — third city with Iron and Diamonds. Set Suguba (Mali's unique Commercial Hub) as first production. Faith at 127 — accumulating with nothing to spend it on since the agent chose science over religion.

**T56**: **Campus completed in Niani** — science jumped to 15.5. Era score hit 15, safely above the 13 Dark Age threshold. Started Library. The Free Inquiry dedication was paying off: each district completion and Eureka contributed era score.

**T57**: **Classical Republic adopted** — first real government. Policy setup: Urban Planning (+1 production), Caravansaries (+2 gold from trade routes), Charismatic Leader (+2 envoy influence), Conscription (-1 unit maintenance). Astrology completed, opening Holy Site option — but the agent correctly chose to skip religion and focus on science.

**T60**: State of the empire: 3 cities, pop 6, science 15.5/t, culture 7.1/t, gold 206 (+28.4 GPT), faith 177 (+4.7 FPT), military 117. Era score 22/26 — tantalizingly close to Golden Age after a goody hut provided a massive era score boost. GNP still #1, but science at 15.5 vs Greece's 33 — a 2x gap. Only 12% explored with 6 civs still unmet.

### Assessment: T41-60

**Strategic**: The Dark Age with Free Inquiry turned out well — era score recovered from 5 to 22 through Eurekas and science buildings, nearly reaching Golden Age (26). The gold-purchase economy continued performing: settler at T48, archer at T43, builder at T54 — all bypassing the -30% production penalty. However, 3 cities at T60 vs the benchmark of 3+ was only barely on track. Science at 15.5 was respectable but Greece at 33 was pulling ahead fast.

**Rival context**: Only 12% explored with 6 of 7 rivals unmet. The agent couldn't see it, but Gran Colombia already had 4 cities and 34 pop, the Ottomans had 5 cities and 39 pop, and India had 5 cities and 27 pop. Greece's 33 science was already double Mali's 15.5 — a gap that would widen to 3x by T70. The agent's world was limited to its immediate neighbors and two city-states.

**Tactical**: The barbarian camp at (22,44) consumed significant military attention for 15+ turns. The promoted archer (Volley + Arrow Storm, RS 37) became the primary defense unit and handled spawning warriors effectively. The camp was never fully cleared — just contained.

**Tooling**: Diplomacy encounter skip bug continued causing units to freeze (T57-58). Builder and unit movements disrupted after Pericles interactions. The agent adapted by re-issuing orders the following turn.

**Hypothesis Quality**: The T41 prediction about buying a settler at T43 for 310g was off by 5 turns (actual: T48 for 290g) due to the archer purchase diversion. The T56 prediction "Library brings science to ~17.5, Classical Republic multiplier" was directionally correct — science trajectory was improving. The T60 hypothesis about Golden Age + Monumentality (faith-bought settlers) showed good strategic thinking, though it would depend on earning 4 more era points.

---

## T61-80: Golden Age, Heroic Age & Rapid Expansion

**T61**: Achieved suzerainty over Geneva with 3 envoys — providing +2 science in capital with Campus and +1 favor/turn. Forest chopped at (20,37) to accelerate Library production.

**T62**: Market purchased at Awdaghust (255g) unlocking a second trade route. Science hit 19.7 with Library about to complete. **Golden Age confirmed** with era score 28 — though the agent recorded this, the actual transition happened at the era boundary.

**T63**: **Library completed in Niani** — science jumped to 22.3. Set Niani to produce Settler (8 turns). Second trade route started Niani→Geneva.

**T68**: Settler produced, heading to (26,34) for fourth city. Iron Working complete — Swordsmen available. Apprenticeship done — Industrial Zones unlocked.

**T73**: **Founded Timbuktu** at (26,34) — fourth city with Cotton luxury, near Silver and Iron. Bought Monument (160g). Greece complained about the forward settle near their territory — responded dismissively. This was the right call: expansion couldn't wait for Greek approval, and friendship was still active.

**T76-77**: Silver mine completed. Upgraded warrior to Swordsman → which auto-upgraded to **Man-at-Arms** (CS 45) — the strongest unit on the map. Niani Walls completed, boosting Engineering research.

**T79**: **Heroic Age!** Era score reached the threshold for a Heroic Age (coming from Dark Age). Chose three dedications: Monumentality + Free Inquiry + Pen/Brush/Voice. Immediately **bought TWO settlers with faith** (110 + 130 = 240 faith) — the Monumentality dedication the agent had been hypothesizing about since T60. This was the single best turn of the game so far: 240 faith converted to 2 settlers instantly, bypassing 16+ turns of production.

**T80**: **Zhang Qian (Great Merchant) activated** on Niani Suguba — +1 trade route capacity. State of the empire: 4 cities (2 settlers en route for cities 5-6), pop 10, science 34.7/t, culture 17.8/t, gold 227 (+61.2 GPT), faith 42 (+9.2 FPT), military 143. Science at 34.7 vs Greece's 85 — still a 2.5x gap, but the trajectory was improving with Campus infrastructure coming online in multiple cities.

### Assessment: T61-80

**Strategic**: The Heroic Age + Monumentality + faith settlers at T79 was the game's inflection point. Two settlers for 240 faith — when faith had been accumulating unused for 80 turns — was a massive efficiency gain. However, science at 34.7 vs Greece's 85 at T80 was concerning.

**Rival context**: At T80, the full leaderboard (invisible to the agent) was sobering. Greece led in science at 85, the Ottomans had 5 cities with 92 science, Gran Colombia had 4 cities but 349 score. Mali's 4 cities and 34.7 science placed it firmly in the bottom half. The agent had GNP #1 but was dead last in population and food — a pattern that would persist for 200 more turns. The silver lining: nobody was close to winning anything yet, and Mali's gold/faith economic engine was just starting to compound.

**Tactical**: The Man-at-Arms upgrade was a happy accident (Warrior → Swordsman → Man-at-Arms due to tech levels). At CS 45 it was the strongest garrison in the game. The barbarian camp at (22,44) continued to be a persistent nuisance but was effectively contained by the promoted archer.

**Tooling**: Diplomacy encounter skip bugs continued. The Greek forward-settle complaint was handled correctly — the agent dismissed it rather than letting diplomatic concerns override expansion needs.

**Hypothesis Quality**: The T60 hypothesis about "Golden Age → Monumentality → faith-bought settlers" came true at T79 — the agent predicted this 19 turns in advance and accumulated the faith to execute it. The T65 prediction of "4 cities by T80" was achieved at T73. However, the science gap prediction was consistently optimistic — the agent kept underestimating how far ahead Greece was.

---

## T81-120: Six Cities, Universities & Closing the Tech Gap

**T81**: Education research started (7 turns). Elite archer promoted with Expert Marksman (4th promotion — double-fire without moving). Bought builder at Tawdenni with Monumentality's +1 movement bonus. Two settlers advancing north toward city sites.

**T87**: **Founded Nioro** (city 5) at (21,27) with fresh water and Iron. Bought Monument immediately. Settler 2 still routing around mountains toward (20,29).

**T90**: Machinery complete — elite archer upgraded to **Crossbowman** (RS 40, 4 promotions!). This was the strongest ranged unit possible at this tech level. Timbuktu Suguba completed. Stirrups researching — unlocking Mandekalu Cavalry, Mali's unique unit.

**T93**: **Merchant Republic adopted** — +2 trade route capacity, +10% gold in cities with districts. This was a natural fit for Mali's gold-focused economy.

**T95**: **Founded Jenne** (city 6) at (18,29) on coast with Stone. Science at 56 with Natural Philosophy policy active.

**T100**: **Mid-game checkpoint**: 6 cities, pop 23, science 58.7/t, gold 76 (+91.3 GPT), faith 267, military 235. Science at 58 vs Greece's 131 — still a 2.2x gap but narrowing from the 3x gap at T70. GNP rank #1 at +91 GPT. Dead last in population and food — a persistent problem from Mali's production penalty slowing granaries and growth buildings.

**T105**: Bought Library at Awdaghust (190g), set University production. Castles research for Medieval Walls on vulnerable cities. Faith at 349.

**T110**: **Massive Monumentality turn** — faith-purchased a settler (150f), 2 builders (55f + 60f) via Monumentality+Suguba discount. 265 faith spent in one turn. Settler heading to (24,25) for a 7th city with 3 Diamonds + Horses + Niter. First Mandekalu Cavalry produced (CS 55). Gold at 642 — highest point so far. Military suddenly at 257, surpassing Greece.

**T115**: Greece friendship renewed (+30 turns). Bought University at Tawdenni — science jumped from 80 to 87.9. Second Mandekalu Cavalry produced. Military at 310 vs Greece's 100 — a 3:1 advantage, flipping from 1.6:1 disadvantage at T81.

**T116**: **Founded Kangaba** (city 7) at (24,25) with 3 Diamonds nearby.

**T120**: **Barbarian camp at (22,44) finally cleared** after ~80 turns of containment. State of the empire: 7 cities, pop 36, science 104.7/t, culture 34.4/t, gold 339 (+119 GPT), faith 339 (+17 FPT), military 330 (rank 1). Science gap: Mali 105 vs Greece 161 — still behind but closing. The agent had 29 techs vs Greece's 36. Recruited Great Merchant Ibn Fadlan.

### Assessment: T81-120

**Strategic**: The expansion burst from T79-T116 (3 cities in ~37 turns, from 4 to 7) was enabled by Monumentality faith purchases and Mali's gold economy. The agent used faith for settlers/builders and gold for monuments/markets/libraries — exactly the right split. Science grew from 34.7 to 104.7, a 3x increase driven by Universities and Campus infrastructure. However, the agent was still 7 techs behind Greece at T120 — the early science deficit from having only 1 city at T40 was proving hard to close.

**Rival context at T100**: Gran Colombia led the scoreboard (349) with 4 high-pop cities. Ottomans had 5 cities at 92 science. Greece had the highest science output (131, 2.2x Mali's 59). India quietly built 5 cities with 27 pop. Even Georgia had 5 cities. Mali ranked 6th of 8 in score. By T120, the picture improved — Mali's 7 cities and 105 science started closing the gap, and its 330 military suddenly outclassed everyone. But culture (34/t) was already a problem, with Greece at 47 and Gran Colombia at 42.

**Tactical**: The military transformation was dramatic — from 143 at T80 (Greek military 2x ours) to 330 at T120 (our military 3x Greece's). This came from Mandekalu Cavalry (CS 55) and Crossbowman upgrades, plus Merchant Republic's trade route economy funding unit purchases. The barbarian camp clearance at T120 after 80 turns was anticlimactic but removed a persistent drain on military attention.

**Tooling**: Builder improvement issues at T82 (couldn't farm hills tiles) required investigation — the agent correctly switched to mining. Trade proposals to Greece were all rejected despite friendship — relationship modifiers from forward settling made deals unprofitable.

**Hypothesis Quality**: The T81 prediction "Education in 7t → Universities" was accurate. The T90 target of "University in Niani by T100 → 60+ science" missed slightly (58.7 actual). The agent's persistent underestimation of the science gap was a recurring pattern — each checkpoint showed Greece further ahead than predicted.

---

## T121-160: Trade Empire, Alliance & Science Surge

**T121**: Activated Ibn Fadlan at Niani Suguba for trade route bonus. Science at 112, up from 34.7 at T80 — a 3.2x increase in 40 turns. Gunpowder researching for Musketmen.

**T125**: Metal Casting done. 10 trade routes active. Niani Industrial Zone started at (19,38) with +4 adjacency. Gold at +126 GPT with Bank income. Builder mining Niter at (24,28) for gunpowder-era unit upgrades.

**T130**: **10-turn checkpoint**: Recruited Raja Todar Mal (Great Merchant, +envoy tokens). 9 trade routes now active across the empire. Traded Silver for Tobacco and Turtles with Greece. Science 130.4 vs Greece ~160 — gap narrowing to 1.2x from the earlier 2.5x.

**T137**: **Research Alliance formed with Greece** (Level 1) — the first alliance of the game. This provided +33 diplomatic relationship, +5% science boost, and shared visibility. Diplomatic Service civic unlocked alliances, and the existing friendship made Greece an easy first ally.

**T140**: Traded 3 surplus luxuries to Greece for +7 GPT. Gold at 1130 (+172 GPT). Science at 141.5 vs Greece 178 — within striking distance. Line Infantry (Musketman upgrade) available. Settler heading east for coastal city.

**T145**: Gold at 1495 (+170 GPT) — approaching the point where gold literally couldn't be spent fast enough. Settler + Line Infantry escort heading to (31,36) for an ocean-access city. Scouted area revealed Tsingy natural wonder at (30,35) and multiple resources.

**T150**: **Patronized Brunelleschi** (Great Engineer, 1580g) for +315 production toward industrial buildings. Activated him at Niani's Industrial Zone — Factory nearly instant. Two settlers moving simultaneously: city 8 at (20,34), city 9 at (31,36). Science "recommended" at 60% — the gap was closing. Only 5 techs behind Greece (40 vs 45).

**T153**: **Founded Kumbi Saleh** (city 8) at (20,34) with 2 Amber luxuries.

**T155**: **Founded Gao** (city 9) at (31,36) — coastal with Tsingy natural wonder nearby. Victor governor assigned for loyalty near Greek territory. Coal Power Plant completing at Niani.

**T160**: **Science surpassed Greece** — Mali 196.1/t vs Greece 186/t. After 160 turns of being behind in science, the 7-campus, 5-university infrastructure finally overtook Greek output. State of the empire: 9 cities, pop 57, science 196/t, culture 64/t, gold 1669 (+299 GPT), faith 1425 (+40 FPT), military 436. 3 city-state suzerainties (Geneva, Preslav, Mogadishu). Diplomatic favor at 151 (+7/t). Still only 23% explored — remarkably low for T160.

### Assessment: T121-160

**Strategic**: This was the turning point era. Science grew from 105 to 196 (87% increase), gold from 119 to 299 GPT, and the empire expanded from 7 to 9 cities. The Research Alliance with Greece at T137 was well-timed — it provided science bonuses while guaranteeing peace with the nearest rival. The agent surpassed Greece in science at T160 — the culmination of 160 turns of Campus infrastructure investment.

**Rival context at T150**: Greece led in score (594) and science (173), but the Ottomans had quietly built a powerful empire (514 score, 6 cities, 60 pop, 144 science, 567 military). Gran Colombia was the demographic giant (582 score, 6 cities, 65 pop). India expanded to 8 cities with 57 pop. Mali's 442 score and 48 pop placed it 5th. The agent was winning in one dimension (GNP) while trailing in most others. Critically, culture was already diverging — Gran Colombia at 92/t, Greece at 103/t, vs Mali's 49/t. This 2:1 culture gap would widen to 4:1 by game end and cost the agent dozens of turns in civic unlocks.

**Tactical**: Relatively quiet militarily. No wars, no significant barbarian threats after the T120 camp clearance. The Mandekalu Cavalry were used as escorts and garrisons, never seeing combat. The Line Infantry provided forward security for settlers. Military strength was maintained through gold-purchased upgrades rather than production.

**Tooling**: Lua workarounds needed for research selection (Military Science, Mass Production). Some civic/tech paths required manual intervention when the standard tools couldn't set them. Trade proposals to Greece worked after the alliance was established.

**Hypothesis Quality**: The T130 prediction "science closing gap: 130 vs 160 Greece" was accurate. The T140 prediction about closing to 5 techs behind was confirmed. The agent's hypothesis that gold + trade routes would eventually fund enough infrastructure to overtake Greece proved correct at T160.

---

## T161-200: Space Race Setup & Military Dominance

**T165**: Pingala promoted with **Space Initiative** (+30% space project production) — a critical promotion for the science victory endgame. Spy trained at Niani for tech stealing from Athens. Faith at 1624 with no meaningful way to spend it (no religion, Monumentality expired).

**T170**: **Einstein recruited and activated** at Niani Campus — providing Eureka boosts to multiple Modern/Atomic era techs. Radio completing next turn for Modern Era entry. **Golden Age achieved** with era score 89. 10 cities, 68 pop, science 226, gold +363 GPT.

**T175**: Radio completed — Modern Era entered. Golden Age dedication chosen. Albert Einstein's boosts accelerated the tech tree significantly. Science at 260.

**T180**: **World Congress** — gained +2 DVP (now 4/20). But Greece at 11/20 DVP was alarming. Discovered 4 previously unmet civs through trade destinations: Ottomans (8 cities), Georgia (10 cities!), Scythia (5), Indonesia (4). Only 23% of the map explored at T180 — the agent had been playing almost blind for 180 turns.

**T185**: **Massive gold deployment** — purchased 5 Research Labs in one turn for 4,700g total. Science spiked from ~287 to 370+. Rocketry completing next turn. Gold at 3,047 after the spending spree — still healthy at +446 GPT.

**T190**: Spaceport building at Tawdenni (15 turns). Agent led in science output (384 vs Greece 259) but still trailed in total techs (53 vs 55). No one had launched space projects yet. DVP: Mali 4, Greece 11 — the diplomatic victory threat from Greece was real.

**T195**: Computers completed. Greek spies detected at Niani Suguba — deployed spy Kadidia on counterspy duty. Gold at nearly 7,000 with +453 GPT.

**T200**: State of the empire: 10 cities, pop 81, science 413/t, culture 90/t, gold 6,303 (+480 GPT), faith 2,219 (+55 FPT), military 1,057 (rank 1 — 4.5x Greece's 236). Tanks, Infantry, and Machine Guns replaced the earlier Mandekalu Cavalry and Crossbowmen. **Satellites + Spaceport completing simultaneously at T202** — the space race was about to begin. Greece had 3 Spaceports but 0 science VP — they hadn't started projects yet.

### Assessment: T161-200

**Strategic**: The gold-to-science conversion strategy reached its peak: buying 5 Research Labs in one turn for 4,700g was only possible because of Mali's +450 GPT income. Science grew from 196 to 413 — more than doubling in 40 turns. The Spaceport + Satellites synchronization at T202 showed good planning. However, Greece's 11/20 DVP was a serious threat that the agent flagged but couldn't fully address.

**Rival context at T200**: The full leaderboard revealed how isolated Mali's dominance was. Greece led in score (826) and techs (57), with 11 DVP making diplomatic victory a real threat. Gran Colombia was the demographic superpower (817 score, 10 cities, 101 pop, 154 culture). India had quietly expanded to 10 cities and 97 pop with 219 science — the only rival with competitive science output. The Ottomans fielded 521 military. Mali led only in science output (413 vs Greece's 251) and gold (480 GPT). In culture, the deficit was now catastrophic: Mali 90/t vs Gran Colombia 154/t, Greece 134/t, India 124/t. This meant civics like Space Race, which give space project production bonuses, were 20-30 turns further away for Mali than for rivals.

**Tactical**: Zero combat in this era. The military existed purely as deterrence — at 1,057 strength vs Greece's 236, no one would dare attack. The agent's military was overbuilt for a science victory, but Mali's gold economy made unit maintenance negligible.

**Tooling**: Research Lab purchases required gold (not faith), which was Mali's strength. The Greek spy incursion was detected and countered. Trade destinations revealed unmet civs — a useful side benefit of the trade network.

**Hypothesis Quality**: The T165 prediction "~20 turns to reach Rocketry" was close (actual: Rocketry at T186, 21 turns). The T170 prediction "Spaceport by T190" was slightly optimistic (actual: T202). The agent correctly identified Greece's DVP as the main threat but underestimated how difficult it would be to counter.

---

## T201-243: The Space Race

**T202**: **Earth Satellite launched** at Tawdenni — first science VP. Met Ottomans, Georgia, Scythia, and Indonesia via satellite visibility. Sent embassies to all four. Moon Landing started at Tawdenni (14 turns).

**T209**: **Moon Landing completed** (T223 projected). Nuclear Fission done. The agent discovered that space projects are sequential, not parallel — Mars Colony couldn't start until Moon Landing finished. This invalidated the dual-Spaceport acceleration plan.

**T210**: Purchased University at Kumbi Saleh (535g), Bank at Gao (620g), patronized John Roebling (1,430g). Multiple joint war proposals rejected from various civs — the agent stayed focused on the science path. Greece now had 4 Spaceports but still 0 science VP.

**T223**: **Moon Landing completed**. Mars Base started at Tawdenni (16 turns → T239). Carl Sagan at 1,861/2,260 Great Scientist points — close to free recruitment. Cold War civic completing.

**T229**: **World Congress** — queued 7 votes (126 favor) to strip Greece's 12 DVP via Option B. The vote didn't work — Greece stayed at 12 DVP. Reason unclear, but the concentrated voting approach failed for the first time.

**T239**: **Mars Base completed**! But the agent discovered **Exoplanet Expedition requires TECH_SMART_MATERIALS**, not the Nuclear Fusion it had assumed. Smart Materials was already researched, so the agent started the Exoplanet project immediately. Carl Sagan activated — **+3,000 production instantly completed the Exoplanet Expedition**. All 4 space projects done: Earth Satellite (T209), Moon Landing (T223), Mars Base (T239), Exoplanet (T243).

**T243**: **Exoplanet Expedition completed**. The agent expected victory. Instead: nothing. Victory progress showed 0.5/1.0 — the vessel needed to physically travel ~33 light-years to Alpha Centauri. This was the Gathering Storm expansion's light-year mechanic, completely unknown to the agent.

### Assessment: T201-243

**Strategic**: The space project execution was efficient — 4 projects in 34 turns (T209-T243) with no rival even starting their first project. Carl Sagan's +3,000 production activation on the Exoplanet was the best possible use of a Great Scientist. However, the agent's ignorance of the light-year travel mechanic meant the "victory at T243" hypothesis was wrong.

**Rival context at T243**: Gran Colombia dominated the scoreboard (1008, 14 cities, 134 pop) but had only 53 techs and no Spaceports. Greece (1004, 69 techs, 4 Spaceports) was the closest science competitor but still had 0 science VP — the agent's lead in project execution was decisive. India (899, 11 cities, 121 pop, 310 science) could have been a dark horse but had only 2 Spaceports and 58 techs. The real threat was diplomatic: Greece at 12 DVP (60% to victory) and Gran Colombia quietly accumulating favor. If the light-year transit had taken 10 more turns, a World Congress could have awarded Greece the final 8 DVP.

---

## T244-271: The Light-Year Sprint

**T244**: Discovery of the light-year mechanic. The vessel travels 1 ly/turn naturally, needing ~33 turns to arrive. But PROJECT_TERRESTRIAL_LASER and PROJECT_ORBITAL_LASER (requiring TECH_OFFWORLD_MISSION) could accelerate the vessel. The agent immediately pivoted: Advanced Power Cells (4t) → Predictive Systems → Advanced AI → Offworld Mission.

**T248**: Advanced Power Cells completed. The Future Era tech tree had no database prerequisites — the agent discovered unlock paths were code-based by checking `CanResearch()` each turn.

**T250**: Wernher von Braun (Great Engineer, +1,500 production toward space projects) patronized for 3,530g and moved to Tawdenni Spaceport. Put to sleep until Offworld Mission completed.

**T253**: **Second World Congress** — queued 9 votes (216 favor) targeting Greece's DVP. Failed again — Greece stayed at 12 DVP. Two concentrated WC attempts to strip Greek diplomatic progress, both unsuccessful.

**T255**: Predictive Systems completed → Advanced AI researching (4t). The tech chain was: APC → Predictive Systems → Advanced AI → Offworld Mission. Each Future Era tech took 3-5 turns at 450+ science/turn.

**T259**: Dark Age entered. Chose Sky and Stars dedication.

**T262**: **Offworld Mission completed!** Set Tawdenni to Terrestrial Laser (600 cost, 5 turns). **Activated Wernher von Braun** on the Spaceport — victory progress jumped from ~0.55 to 0.785. That single activation was worth approximately 9 light-years of travel, cutting the remaining journey nearly in half.

**T265**: **First Terrestrial Laser completed**. Victory progress 0.83. Queued second Laser. Attempted to queue at Nioro's Spaceport too, but encountered a CORRUPTED_QUEUE bug — the second Spaceport couldn't start laser production despite the item showing as available.

**T270**: 32/33 science VP — one light-year from victory. No rival had started any space project. Greece at 74 techs with 4 Spaceports, India at 73 techs with 2 Spaceports — both far too late.

**T271**: **SCIENCE VICTORY**. 34/33 VP. The Exoplanet vessel arrived at Alpha Centauri. Final stats: 10 cities, 77 techs, science 440/t, gold 34,990 (+464 GPT), faith 10,162 (+233 FPT), military 3,435 (rank 1). Score 877 — last among all surviving civilizations.

### Assessment: T244-271

**Strategic**: The recovery from the light-year surprise was excellent. The agent identified the acceleration mechanism (Terrestrial Laser), found the tech path (APC → PS → AAI → OWM), positioned Von Braun at the Spaceport, and executed the plan within 28 turns. Von Braun's activation was the game-winning move — without it, victory would have been ~T276 instead of T271. The CORRUPTED_QUEUE bug at Nioro's Spaceport cost 2-3 turns of potential acceleration.

**Tactical**: Zero military action in the entire endgame. The 3,400+ military strength was pure deterrence. No war was ever declared by or against Mali in the entire 271-turn game.

**Tooling**: The CORRUPTED_QUEUE bug after the first Terrestrial Laser completion was a significant tooling issue — `CanProduce` returned true but `RequestOperation` silently failed. This prevented parallel laser production at two Spaceports.

**Hypothesis Quality**: The T243 "victory this turn" prediction was wrong due to the unknown light-year mechanic — the biggest prediction failure of the game. The T262 prediction "victory ~T270" after Von Braun activation was nearly perfect (actual: T271).

---

## Final Assessment

### What Went Right

1. **Gold economy execution**: Mali's core identity — gold purchases bypassing the -30% production penalty — was leveraged from T17 (first builder purchase) through T271. The agent understood this from Turn 1 and never deviated.

2. **Religious Idols synergy**: Choosing a pantheon that gives +2 faith per mine on luxury/bonus resources created a dual gold-faith engine that powered the entire mid-game expansion.

3. **Monumentality faith settlers**: Accumulating faith for 79 turns, then spending 240 faith on 2 instant settlers during the Heroic Age was the game's single best economic play.

4. **Von Braun activation**: Patronizing Von Braun for 3,530g, positioning him at the Spaceport, and activating him for +1,500 space project production was the game-winning tactical decision — worth ~7 light-years, cutting the transit by ~21%.

5. **Peace through deterrence**: No wars in 271 turns. Friendship → alliance with Greece (the nearest threat), and military strength growing to rank 1 by T120, meant the agent was never attacked. But deterrence came at a cost (see below).

### What Went Wrong

1. **Expansion speed**: Only 2 cities at T40, 3 at T60 — consistently behind benchmarks. The early-game production penalty made settlers painful, and the agent didn't gold-purchase settlers early enough.

2. **Exploration**: Only 23% explored at T180. Six civilizations went unmet until satellite visibility at T209. The agent ran one scout for the entire game and never bought a second one. This is the 5th consecutive game with catastrophic exploration failure.

3. **Culture deficit**: Mali finished at 87 culture/turn — dead last among major powers. India produced 575/t (6.6x), Gran Colombia 369/t (4.2x), Greece 281/t (3.2x). Zero Theater Squares were built in 271 turns across 10 cities. The civic tree was the bottleneck for the entire late game: Space Race civic (bonus space project production) arrived turns later than it should have, and the agent never unlocked key tourism/cultural civics at all. This was not diagnosed during gameplay — the agent never once noted culture as a problem.

4. **Government stagnation**: Merchant Republic was adopted at T93 and never changed for 177 turns — the entire rest of the game. Democracy (+50% Great People points, better policy cards), Communism (+10% production, military policy slots), and Digital Democracy (future government) were all available and never considered. The agent's diary mentions "Merchant Republic" at T149 without questioning it. A government upgrade could have accelerated Great Scientist generation and provided better late-game policy options.

5. **Faith accumulation**: 10,162 faith at game end with +233/t still accumulating. This wasn't just "unused" — it represents quantifiable missed value. 10,162 faith could have purchased: ~6 Naturalists (1,600f each) for National Parks toward culture victory insurance, 8-10 Rock Bands for tourism bursts, multiple Apostles/Missionaries if a religion had been founded, or 3-4 additional Monumentality settlers during Golden Ages. The agent identified faith hoarding as a problem at T165 ("no meaningful way to spend it") and never found a solution in 106 remaining turns.

6. **World Congress voting**: Two concentrated DVP-stripping votes against Greece (T229: 126 favor, T253: 216 favor) both failed. 342 favor spent for zero return. **Root cause**: the agent never verified how DVP-stripping resolutions actually work. Option B of a DVP resolution targeting a player strips -1 DVP (not -2), and only if you *win* that outcome — which requires more votes than all opponents combined on that option. The agent dumped votes without understanding the voting mechanics, and the diary shows no post-mortem of why the T229 vote failed before attempting the identical strategy at T253. This is the reflection-action gap in microcosm: the agent observed failure, didn't diagnose it, and repeated the same approach.

7. **Light-year mechanic**: The agent didn't know about Gathering Storm's Exoplanet travel mechanic until T244. This is framed elsewhere as a "knowledge gap," but it's more accurately an information-gathering failure. The agent had `get_victory_progress` available from T1 and could have queried it to understand the full victory pipeline at any point during the 40-turn space race setup (T160-T200). The T200 diary says "nobody has launched space projects yet" — but the agent never asked "what happens after all 4 projects complete?" If `get_victory_progress` had been checked earlier, the light-year mechanic would have been visible, and the Offworld Mission tech chain could have started 15-20 turns sooner. Victory at ~T255 instead of T271.

8. **Military over-investment**: 3,435 military strength at game end, rank 1, with zero wars fought. This deterrence was valuable — but at what cost? Unit maintenance at this level was likely 40-60 GPT (8-12% of income). More importantly, the production and gold spent on Tanks, Infantry, Machine Guns, and Mandekalu Cavalry that never saw combat could have funded additional science infrastructure, builders, or districts. The agent built military because the military strength number was visible and reassuring, not because threats were identified and assessed.

### The Score Paradox

Mali won a science victory from 6th place (877 score) while Gran Colombia (1145), Greece (1098), India (1076), and the Ottomans (982) all scored higher. How?

Score in Civ 6 rewards breadth: population, territory, civics, wonders, Great People, and military. Mali was dead last in population (96 vs Gran Colombia's 149, India's 138), had fewer cities (10 vs Gran Colombia's 15, India's 11), fewer civics (from culture starvation), and fewer wonders. What Mali had was *depth in one dimension*: 77 techs and 440 science/turn, enough to complete all 4 space projects before any rival started their first.

Science victory doesn't require a high score — it requires completing a specific tech chain and project pipeline faster than anyone else. Mali's gold economy converted directly into science infrastructure (buying Research Labs, Universities, Campus buildings) while rivals distributed their output across military, culture, religion, and expansion. Gran Colombia's 15 cities and 149 population generated enormous *score* but only 353 science. India's 138 population and 514 science was competitive, but they started Spaceport construction too late (only 2 Spaceports, 0 VP by T270).

The lesson: score measures empire breadth, not victory proximity. A focused 10-city science empire can win before a sprawling 15-city empire completes its first space project. But this is also a warning — if the light-year transit had taken 15 more turns, Greece's diplomatic path (13 DVP, needing only 7 more from ~2 World Congress sessions) or India's late science surge (514/t) could have overtaken Mali.

### The Culture Deficit

Mali's culture output tells a story of total neglect:

| Turn | Mali Culture | Greece | India | Gran Colombia | Mali Rank |
|------|-------------|--------|-------|---------------|-----------|
| T100 | 34 | 47 | 26 | 42 | 4th |
| T150 | 49 | 103 | 57 | 92 | 6th |
| T200 | 90 | 134 | 124 | 154 | 7th |
| T270 | 87 | 281 | 575 | 369 | 8th (last) |

Zero Theater Squares were built in 271 turns across 10 cities. The agent's diary never once flagged culture as a problem — it simply wasn't monitored. Culture determines civic unlock speed, and civics gate critical game mechanics: government tiers, policy cards, Space Race production bonuses, and tourism multipliers.

The concrete cost: the Space Race civic (which gives production bonuses to space projects) was available to high-culture civs 20-30 turns before Mali could unlock it. Democracy (unlocked via civics) provides superior policy slots to Merchant Republic. Conservation (enables Naturalists for National Parks) was likely never reached. Every turn of delayed civic completion is a turn of missed policy bonuses, missed government options, and missed strategic flexibility.

The fix was simple: one Theater Square in the capital, with a Museum and Great Works, would have provided 15-20 culture/turn. Across 3-4 cities, this would have kept Mali's civic pace competitive. The agent built Campuses in every city but Theater Squares in none — a choice made by omission rather than analysis.

### Government Stagnation

Merchant Republic was adopted at T93. It was never changed. For 177 turns — 65% of the game — the agent used a Classical-era government in the Industrial, Modern, Atomic, and Information eras.

Available upgrades the agent never considered:
- **Democracy** (Modern): +1 GPP per speciality district, +50% Great People points, stronger economic/wildcard slots. Would have accelerated Great Scientist recruitment, directly feeding the science victory path.
- **Communism** (Modern): +0.6 production per population, +10% flat production, military policy slots. Would have addressed Mali's core weakness (production penalty) directly.
- **Synthetic Technocracy** (Future): +5% science per Campus with building, +100% boost effectiveness. Tailor-made for a science victory.

The Merchant Republic's trade route bonuses were valuable in the mid-game, but by T160+ the agent had more gold than it could spend (ending with 34,990). Switching to Democracy at T160 would have provided +50% Great People points for the remaining 111 turns — likely recruiting Sagan and Von Braun 10-15 turns earlier. Switching wasn't even free the first time (it was after the first government-tier upgrade), so the cost was just the anarchy turns — a trivial price.

The agent's diary at T149 notes "Merchant Republic active with 6 slots" as a statement of fact, not a question to revisit. The government was never re-evaluated because it was never re-queried.

### By the Numbers

| Metric | Value | Note |
|--------|-------|------|
| Victory | Science, T271 | 6th in score |
| Cities | 10 | 7 founded, 3 via Monumentality faith |
| Final Science | 440/t | Peak 498 at T260 |
| Final Gold | 34,990 (+464/t) | Peak GPT: 569 at T210 |
| Final Faith | 10,162 (+233/t) | Mostly unspent |
| Final Military | 3,435 | Rank 1, never at war |
| Techs | 77 | 4 ahead of Greece |
| Space Projects | 4/4 | T209/T223/T239/T243 |
| Great People Used | 6+ | Einstein, Von Braun, Sagan, Brunelleschi, Ibn Fadlan, Zhang Qian |
| Wars Fought | 0 | Peace through strength |
| Exploration | 23% at T180 | Dangerously low |
| Final Culture | 87/t | Dead last (India: 575, Gran Colombia: 369) |
| Theater Squares | 0 | Across 10 cities, 271 turns |
| Government Changes | 1 | Merchant Republic T93-T271 (177 turns) |
| Faith Unspent | 10,162 | +233/t still accumulating |
| WC Favor Spent | 342 | 0 return — both DVP votes failed |
| Final Score Rank | 6th of 8 | Won from behind |

### Civ Kit Utilization

| Element | Used? | Assessment |
|---------|-------|------------|
| Songs of the Jeli | Partially | Desert adjacency provided modest faith/food but cities weren't optimized for it |
| Saharan Merchants (+4g mines) | Fully | Core of the entire gold engine |
| Suguba (discount district) | Fully | Built in 7+ cities, 20% discount on faith/gold purchases |
| Mandekalu Cavalry | Barely | 2 produced, used as garrisons, never saw combat |
| -30% production penalty | Mitigated | Gold purchases bypassed it consistently |

The agent played Mali's economic identity correctly but left significant civ-kit value on the table. The Mandekalu Cavalry were never used offensively, Songs of the Jeli wasn't optimized through city placement, and the massive faith stockpile (from Religious Idols + God King) had no outlet after Monumentality expired. A human Mali player would likely have founded a religion for Tithe/Work Ethic, used Mandekalu to protect a vast trade network, and achieved victory 30-50 turns earlier through better expansion timing and exploration.

### Cross-Game Pattern Assessment

Comparing Game 11 against the 13 recurring failures identified in the [Cross-Game Analysis (Games 1-4)](../cross-game-analysis.md):

| # | Pattern | Games 1-4 | Game 11 Status |
|---|---------|-----------|----------------|
| 1 | **Sensorium Effect** | All 4 | **Partially improved.** `get_victory_progress` checked more often than Games 1-4, but culture output, government tier, and WC mechanics were never queried. The agent monitored science obsessively while culture, diplomacy, and faith spending went unexamined. |
| 2 | **Exploration Neglect** | All 4 | **Still present.** 23% at T180. One scout the entire game. 6 civs unmet until T209. The 5th consecutive game with this failure. |
| 3 | **Expansion Failure** | All 4 | **Improved but still slow.** 6 cities at T100, 10 at T173. Better than Games 1-4 (which had 2-4 cities at T100) but still behind benchmarks. The Monumentality faith purchase at T79 was the first time the agent used a non-production expansion method effectively. |
| 4 | **Diplomacy Passivity** | All 4 | **Partially improved.** Research Alliance with Greece at T137, 4 city-state suzerainties by T160, embassies sent to new civs. But still reactive — the agent waited for Greece to reach Friendly status rather than actively cultivating relationships with other civs. No alliances with any of the 6 civs met at T209. |
| 5 | **Unescorted Civilians** | 3/4 | **Improved.** Only 1 builder loss (T25, caused by diplomacy encounter bug). Settlers were generally escorted. |
| 6 | **Reactive Military** | 3/4 | **Mixed.** The barbarian camp at (22,44) was contained for 80 turns instead of being cleared — echoing Games 1-2. But military strength was maintained proactively, and the camp was eventually cleared at T120. |
| 7 | **Victory Tunnel Vision** | 3/4 | **Improved — but replaced by a different kind of tunnel vision.** The agent correctly identified science as viable and executed it. But it never assessed *other* victory paths as fallbacks. Greece's 12 DVP at T243 was 8 short of diplomatic victory — and the agent's two WC attempts to counter it both failed. No culture or diplomatic backup plan existed. |
| 8 | **Gold/Faith Hoarding** | 3/4 | **Gold: improved. Faith: still present.** Gold was deployed aggressively (Research Lab purchases, Great Person patronage, building buys). But 10,162 faith sat idle — the 4th game with unspent faith in the thousands. The agent diagnosed the problem at T165 and never solved it. |
| 9 | **Reflection-Action Gap** | 3/4 | **Still the defining meta-failure.** T165: "no meaningful way to spend faith" → 106 turns later, 10,162 faith idle. T229: WC vote fails → T253: identical strategy, identical failure. Culture never flagged despite being dead last. Government never re-evaluated despite being 3 tiers behind. The agent writes excellent analysis and doesn't execute on it. |
| 10 | **Trade Route Neglect** | 2/4 | **Resolved.** 14/14 trade routes active by T180. Trade infrastructure was built consistently. |
| 11 | **Religion/Faith Blindness** | 2/4 | **Partially resolved.** The agent chose not to found a religion (reasonable for science Mali). But it never monitored `get_religion_spread` to check if a rival was approaching religious victory. In this game it didn't matter — no one was close — but the behavior pattern persists. |
| 12 | **District Timing** | 2/4 | **Improved for Campuses, failed for everything else.** First Campus at T50 (reasonable), all 7 original cities had Campus+Library+University by T161. But zero Theater Squares, and Industrial Zones were late (first at T125). The agent's district strategy was "Campus in every city" — correct for science, but ignoring culture entirely. |
| 13 | **Civ Ability Waste** | 2/4 | **Partially improved.** The gold engine (Saharan Merchants, Suguba) was used perfectly. Religious Idols synergized with Mali's mine bonuses. But Mandekalu Cavalry were never used offensively, Songs of the Jeli wasn't optimized, and the massive faith engine had no late-game outlet. Better than Byzantium (Game 4) or Macedon (Game 3), but still left value on the table. |

**Summary**: Game 11 shows clear improvement in 5 of 13 patterns (expansion, civilian safety, gold spending, trade routes, civ abilities). 4 patterns persist unchanged (exploration, culture/district neglect, faith hoarding, reflection-action gap). 4 patterns show partial improvement but remain concerning (sensorium, diplomacy, victory tunnel vision, reactive military). The root cause hierarchy from the cross-game analysis — Sensorium → Exploration → Expansion → Victory — was partially disrupted by the gold economy bypassing the expansion bottleneck, but the Sensorium Effect's downstream consequences (culture blindness, government stagnation, WC ignorance) created new failure modes.

The most important finding: **this was a winnable game 30-50 turns earlier.** Better exploration (starting Offworld Mission tech sooner), a government upgrade to Democracy at T160, one Theater Square per city for civic pacing, and faith spending on Naturalists/Rock Bands would have compressed the timeline without requiring any fundamentally different strategy. The agent won despite these failures, not because of them.

---
