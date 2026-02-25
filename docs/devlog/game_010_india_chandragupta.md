# Game 10 — India (Chandragupta) — Devlog

**Result: Defeat at T431 — Vietnam Diplomatic Victory (20/20 DVP)**
**Final Score: India 825 (#2) vs Vietnam 1403 (#1), Egypt 780, Persia 730, Ottomans 587, Maya 489**

The longest game in the series. India held the tech lead for 400+ turns on a challenging peninsula start, launched the Exoplanet Expedition at T423, but couldn't prevent Vietnam from accumulating 20 Diplomatic Victory Points. A game defined by patient science execution undercut by a complete failure to engage with the chosen civ's identity — zero Holy Sites, zero religion, 9,599 unspent faith — and catastrophic World Congress mismanagement that handed the game to Vietnam.

---

## Civ Kit & Opening Plan

**Chandragupta of India** — War/religion hybrid.
- **Dharma**: Cities gain follower beliefs of all religions present (not just majority)
- **Stepwell**: Unique improvement (+1 food, +1 housing; +1 faith with Holy Site adjacency)
- **Varu**: Unique unit replacing Horseman (-5 CS to adjacent enemies)
- **Chandragupta's ability**: Territorial Expansion — +2 movement and +5 CS for 10 turns after declaring a War of Territorial Expansion

**Civ was randomly assigned.** The agent didn't choose Chandragupta — it was dealt this civ and needed to adapt. The CLAUDE.md playbook instructs: "Read your civ's unique abilities, units, and buildings — what is this civ designed to do?" and "Identify the tech/civic that unlocks your unique unit; plan a research path to reach it."

**Victory Plan (T0)**: Science victory, leveraging Dharma's multi-religion benefit for flexible yields. Varu available mid-game for military deterrence. Build tall with strong Campuses, aim for Space Race.

**What actually happened to the kit**: Every element of India's identity was abandoned. No Holy Site was ever built across 8 cities and 431 turns, making Dharma permanently inert. Two Stepwells were built (one later pillaged by a storm), gaining no Holy Site adjacency bonus because there was no Holy Site. No Varu was ever produced. No War of Territorial Expansion was ever declared. India played 431 turns as a generic civ with zero unique advantages active. The faith from Stepwells, city-state bonuses, and passive generation accumulated to 9,599 by game end — enough to patronize multiple Great People or faith-purchase an army — and was never spent on anything.

Being randomly assigned a war/religion civ for a science game isn't inherently a problem — Dharma's multi-religion yields can boost any victory path, and Chandragupta's war bonus could have been used to cripple a runaway rival. The failure was not adapting the science plan to incorporate the tools the civ provided.

**Opening Build Order**: Scout → Warrior → Settler → Builder

**What the agent knew at T0 vs what a human would know**: The diary recorded all rival civs' yields from T1 onward (Maya, Ottomans, Egypt, Persia, Vietnam). A human player wouldn't see any of this until first contact — which didn't happen until ~T20 (Ottomans) and ~T55 (Vietnam). The agent's early strategic assessments referencing rival scores were informed by invisible data.

---

## T1-20: Island Discovery & Barbarian Defense

**T1**: Founded Patna at (12,12) — coastal hills on what appeared to be a small island. Terrain: Crabs, Sheep, Cattle, Olives, Whales, Spices nearby. Set Pottery research (standard opener for Granary).

**T7-10**: Scout explored south, revealing water on multiple sides. The "island" hypothesis formed early and persisted until T54. This was reasonable given the visible terrain — the southern connection to the mainland was hidden behind mountains, jungle, and city-state borders.

**T15-20**: Barbarian camp discovered at (11,19) with a Spearman defender. Warrior + Slinger paired to assault the camp. Cleared by T20 — clean execution, no unit losses.

**T19**: First contact with Ottomans (Suleiman). Sent delegation immediately (25g, correct play).

### Assessment: T1-20

**Strategic**: The "island" assumption was a reasonable read of limited data but carried high risk — if true, expansion options would be severely constrained. A human player would have the same map knowledge and likely the same hypothesis. The agent correctly prioritized exploration (Scout first) and early defense.

**Tactical**: Barbarian camp cleared efficiently in ~5 turns with a combined arms approach (Slinger softening + Warrior finish). Good early military play that also generated era score.

**Tooling**: First 20 turns were relatively clean. The diary system was operational and capturing useful data. No major tool bugs in this phase.

**Hypothesis Quality**: "We appear to be on a small island" — understandable but wrong. The peninsula geography wouldn't be confirmed until T54, costing some mental model accuracy in the intervening turns.

---

## T21-60: Second City & Peninsula Discovery

**T29**: Founded Mysore at (9,15) — coastal with Crabs, Olives, Spices. The 2nd city was late by CLAUDE.md benchmarks (target: T40 for 2 cities "underway", but T29 founding is actually ahead of that). However, the site selection was constrained by the perceived island geography.

**T31-40**: Built Campus at (11,11) with +2 adjacency (mountain). Appointed Pingala governor to Patna. Galley built to explore ocean — this was the correct play given the island hypothesis, and it discovered the eastern continent with floodplains and Singapore city-state.

**T50**: Score 99, ranked 4th. Science 11.4/t, Culture 14.1/t. Only 2 cities vs Vietnam's 3.

**T54**: **Key discovery** — `get_minimap` revealed Patna is NOT on an island but a peninsula connected south to a massive continent. This completely changed the expansion calculus. Immediately planned a settler march south toward the floodplains at (11,31).

**T55-60**: Met Vietnam (Ba Trieu) — unfriendly, rejected our delegation. Settler production began for the 3rd city. Traded Olives to Ottomans for Horses (enabling future Varu production — correct use of civ kit).

### Assessment: T21-60

**Strategic**: The peninsula discovery at T54 was pivotal. Before that, expansion planning was paralyzed by the island assumption. After T54, the correct response was aggressive settling south, and the agent pivoted correctly. However, 2 cities at T60 vs the benchmark of 3 cities was already behind. Vietnam had 3 cities and was pulling ahead in score (138 vs 99).

**Tactical**: The Galley exploration was a reasonable bet given the island hypothesis. The Olives-for-Horses trade was a smart play that enabled the unique Varu unit. Builder improvements were sensible.

**Tooling**: No major issues. The diary captured the peninsula discovery well.

**Hypothesis Quality**: The island→peninsula correction at T54 was a good example of updating beliefs based on new data. The agent didn't anchor on the wrong model.

---

## T61-120: Southern Expansion & Infrastructure

**T77**: Founded pantheon — Lady of the Reeds and Marshes (+2 production from floodplains). This was an excellent choice for the planned southern expansion toward floodplain territory.

**T78**: **Ottomans settled at (12,32)**, stealing the planned floodplains city site. This forced a pivot to (14,24), which still had decent yields but lost the floodplain synergy with the pantheon. A painful forward-settle that could have been prevented by faster expansion.

**T81**: **Mumbai founded (3rd city)** at (14,24) — Tea, Olives, Cattle, Dyes. 21 turns behind the T60 benchmark for 3 cities. The settler march had been delayed by city-state borders (Nan Madol, La Venta) and jungle terrain.

**T85-100**: Infrastructure sprint — Granary and Campus in Mumbai, Theater Square in Patna. Era score climbed from 28/29 to 39/43 (barely avoiding Dark Age). Activated Great Scientist Zhang Heng. Promoted Pingala with Grants (+100% Great People points).

**T100**: Score 145 vs Vietnam 168, Egypt 166. Science 24.9/t — tech lead of 25 techs (strongest relative advantage). Only 3 cities vs Vietnam's 5. The science lead was carrying an otherwise undersized empire.

**T112**: Golden Age achieved (era score 43/43). Purchased settler from Mysore (560g) for 4th city. Settler heading to (17,11) with Wheat/Cattle/Salt/Gypsum.

**T120**: Score 180. 3 cities, Pop 18, Science 28.8, Culture 36.0, Gold 200.7 (+30/t). Settler en route. 18 techs, 13 civics.

### Assessment: T61-120

**Strategic**: The 3-city empire at T100 was structurally behind. Vietnam had 5 cities, Egypt had 4-5. The science lead (25 techs) was real but fragile — it came from efficient Great Person use (Zhang Heng, Pingala) rather than raw infrastructure. The 4th city didn't arrive until T122, making this a 2-era delay that would echo through the entire game. The Ottoman forward-settle at T78 was the kind of event the agent should have prevented by moving the settler faster or choosing an intermediate site.

**Tactical**: Mumbai's founding was delayed by poor pathfinding through jungle and city-state borders. The era score management (scraping 43/43) was tight but successful. Golden Age at T112 was well-timed for the Monumentality dedication (faith-purchased settlers/builders).

**Tooling**: The `set_research` tool had intermittent issues where tech selection would revert. This was a recurring annoyance that cost occasional turns of research. Stale promotion notifications began appearing and would persist for 100+ turns.

**Hypothesis Quality**: "Science victory at 60% viability" was a reasonable assessment at T100. The agent correctly identified that more cities were the highest-leverage investment. The prediction of 4 cities by T100 was missed by 22 turns.

---

## T121-200: Great Person Engine & Dark Age

**T122**: **Ahmadabad founded (4th city)** at (17,11) — Wheat, Cattle, Salt, Gypsum. Immediately purchased Monument and Granary. 22 turns late vs the T100 benchmark.

**T128**: Upgraded to Man-at-Arms (CS:45). Education researched — enabling Universities.

**T136**: Ancestral Hall completed in Patna (50% settler production bonus). Magnus promoted with Provision (settlers don't consume population). This was the correct infrastructure for an expansion push, but it arrived 60 turns late.

**T138**: Homer activated (2 Great Works of Writing). Great Scientist activated for tech boosts.

**T143**: 3 Crossbowmen operational — adequate defensive force. Great Merchant Marcus Crassus recruited.

**T150**: **Madurai founded (5th city)** — purchased Monument and Granary immediately. Score 260.

**T159**: Patna University completed. Crassus 1st activation (+60 gold).

**T168-170**: Crassus completed all 3 activations (+180g total). **Research Alliance with Vietnam, Economic Alliance with Ottomans** — both correct diplomatic plays generating favor and research bonuses.

**T173**: **Agra founded (6th city)**. Six cities at T173 vs the benchmark of 4-5 by T100. The expansion was roughly 70 turns behind schedule, but the quality of city sites was good.

**T175-178**: Isaac Newton recruited. Geoffrey Chaucer activated (2 Great Works). Newton activated at Ahmadabad Campus — instant Library + University + permanent +2 Science to all Universities. **Dark Age entered** (era score 80/81, missed by 1 point). Devastating — the Heartbeat of Steam dedication was strong but Dark Age policies are limited.

**T192**: Galileo activated at mountain (+250 Science burst). Storm pillaged Patna University and Mysore Library, costing ~10 Science/turn for 5 turns.

**T197-200**: Science recovered to 85.5/t after repairs. Score 353, 6 cities, Pop 42, 32 techs.

### Assessment: T121-200

**Strategic**: The Great Person strategy was the standout achievement of this phase. Newton, Homer, Chaucer, Crassus, Zhang Heng, Galileo — the agent correctly identified Great People as the primary accelerant for an undersized empire. Newton alone was worth ~30-40 science/turn across all Universities. However, the empire was still structurally behind: 6 cities at T173 vs Vietnam's 9. The Dark Age miss (80/81 era score) was agonizing — one more era score point from any source would have secured Golden Age.

**Tactical**: City founding was methodical if slow. Builder improvements were handled well. The Crossbowman defensive force was adequate. Homer's 17-turn pathfinding odyssey (stuck behind mountains/ocean) was a tooling limitation more than a strategic error.

**Tooling**: `set_research` was intermittently broken for many turns, requiring Lua workarounds. Jungle/forest removal for improvements was broken in the MCP tool layer and required TerrainBuilder Lua commands. Stale promotion notifications persisted throughout. These tooling issues collectively cost perhaps 10-15 turns of accumulated inefficiency.

**Hypothesis Quality**: Predicted Dark Age avoidance — missed by exactly 1 era score point. Predicted Newton as game-changing — correct, it was the single biggest science multiplier. The expansion timeline predictions were consistently optimistic.

---

## T200-300: Factory Chain & Spaceport Construction

**T200-210**: Michelangelo patronized and activated (3 Great Works of Sculpture). Scientific Theory and Enlightenment completed. **World Congress consumed ~240 diplomatic favor for +2 DVP** — this is the first concrete progress toward Diplomatic Victory Points, but the favor cost was enormous.

**T210-220**: **Srinagar founded (7th city)** at (11,26). Giovanni de' Medici gave instant Bank + Market in Mysore (massive gold infrastructure boost). Score climbed to 415, Science crossed 100/t.

**T220-240**: Dark Age continued (era score 80/81, missed Golden by 1 — second consecutive miss). Heartbeat of Steam dedication chosen. **Mumbai Factory completed T240** — the critical Industrial Zone milestone. James Watt gave Madurai instant Factory + Workshop. Leonardo da Vinci activated on Mumbai IZ. 4 cities with Factories by T240.

**T240-260**: **Research Lab buildout** across 5 cities. Science jumped from ~130 to ~160/t as labs came online. Replaceable Parts completed (first to Modern Era). Met all 5 rival civs, 3 alliances active.

**T260-280**: Chemistry completed. Flight → Radio tech chain. **Albert Einstein activated** for Modern + Atomic era eurekas (massive tech acceleration). Nikola Tesla recruited for production boost. Vietnam's Long Bien city losing loyalty near Ahmadabad.

**T280-300**: **Rocketry completed T296**. Two Spaceports started simultaneously: Patna (41t) and Mumbai (29t). **Long Bien flipped to India T299** (8th city, free via loyalty). 7 Research Labs active. Science 242/t (#1, 60 ahead of Vietnam at 182). 48 techs (#1).

### Assessment: T200-300

**Strategic**: This was the strongest phase of the game. The factory chain → research lab pipeline was executed efficiently. Einstein's double-era eureka burst was one of the best Great Person activations in the game. The Long Bien loyalty flip was a free city gain from cultural pressure — excellent passive value. By T300, India had a commanding 60-tech lead with 2 Spaceports under construction. The science victory path looked solid.

However, two strategic blind spots were forming:
1. **Vietnam's DVP accumulation was not tracked.** The diary mentions Egypt at 4/20 DVP but doesn't mention Vietnam's DVP total during this phase. A human player checking victory progress would have seen Vietnam climbing.
2. **World Congress favor management was reactive.** Spending 240 favor on 2 DVP at T200 was expensive. The agent didn't develop a systematic favor accumulation strategy.

**Tactical**: Factory and Research Lab placement was methodical. Spaceport dual-start at T280-296 was the right call. Builder improvements were handled efficiently with forest/jungle chops to boost production.

**Tooling**: `set_research` bug was fixed by T253 (the developer patched it during gameplay). Madurai food crisis persisted for ~30 turns without resolution — the city focus tool should have been used more aggressively. Egypt repeatedly offered bad trades for diplomatic favor (rejected correctly 5+ times).

**Hypothesis Quality**: "Science victory by T355-370 with parallel Spaceports" — this was actually a reasonable estimate if everything went smoothly. The agent underestimated external disruption risk.

---

## T300-390: Space Race Sprint

**T300-320**: Jungle/forest chops accelerated both Spaceports. Mumbai Spaceport completed ~T320, Patna ~T326. Researched Computers, Satellites, Nuclear Fission. Switched to Communism (+10% production) — correct government for space race production.

**T335**: **Earth Satellite completed** (world's first). Moon Landing started immediately. Science ~290/t.

**T350-362**: Coal power crisis required trading for coal and converting plants to oil. Managed recurring resource juggling.

**T362**: **Moon Landing completed** (world's first). 2/4 space projects done.

**T363-370**: Discovered wrong tech prereqs for Mars Base — had been researching Robotics when Nanotechnology was actually required. Pivoted research path. This was a ~5-turn detour caused by not verifying the tech tree prereqs.

**T375-388**: Recruited Carl Sagan (Great Engineer, +3000 production to space project) and Korolev (+1500 production). These were saved for the expensive Mars Base project.

**T388**: **Mars Base instant-completed** using Carl Sagan's 3000 production. 3/4 space projects done. Only Exoplanet Expedition remained.

### Assessment: T300-390

**Strategic**: The space race execution was strong — three projects completed in 53 turns with good Great Engineer management. The Sagan recruit was the single best purchase of the game, saving potentially 30+ turns on Mars Base. However, a critical strategic failure was unfolding in the background:

**Vietnam's DVP accumulation became visible during this phase.** The agent first noted Vietnam at 14/20 DVP at T370, escalating to 15/20 at T386. Then at T391-392, the agent spent ~224 favor on anti-Vietnam WC votes — and Vietnam *jumped from 15 to 19 DVP*, a catastrophic backfire. The agent's T392 diary reads: "CRISIS! Vietnam jumped to 19/20 DVP after WC (+4!). My WC votes failed catastrophically." Despite this alarm, the agent's response was to continue the space race sprint rather than pause to understand WC mechanics or develop an alternative counter-strategy.

**Tactical**: The tech path detour (Robotics instead of Nanotechnology) cost ~5 turns. The coal power crisis management was handled adequately. Great Engineer timing (saving Sagan for Mars Base) was excellent.

**Tooling**: Policy slot bug emerged during the Communism → Democracy switch. Slot 0 permanently broken, requiring manual re-setting of all 8 policies every turn. This was a significant productivity drain on the agent's turn-by-turn workflow.

**Hypothesis Quality**: "Science victory by T355-370" was revised to "T420-440 with Exoplanet travel time" — the travel time component hadn't been factored in. The Mars Base tech path detour also pushed the timeline. Critically, the hypothesis never included a scenario where Vietnam wins diplomatically before the Exoplanet arrives.

---

## T390-423: World Congress Catastrophe & Vietnam War

### The World Congress Disaster (T421)

This is the pivotal failure of the game.

**T392-410**: Vietnam at 19/20 DVP since the T391 WC backfire. The agent identified this as an existential threat and began accumulating diplomatic favor. India had ~200 favor by T420, generating ~10/turn from alliances and suzerainties.

**T421-422**: World Congress fired. The agent needed to block Vietnam from gaining any DVP. Instead:
- **Spent ~202 diplomatic favor** (211→9) on blocking votes
- **Vietnam GAINED a DVP anyway** (reaching 20/20)
- The specific targeting of anti-Vietnam votes may have been mechanically incorrect — the WC voting system's interaction between "option A vs option B" and "target player" was not well understood

This was the second WC disaster. At T391-392, the agent had spent ~224 favor on anti-Vietnam votes, and Vietnam *jumped from 15 to 19 DVP* (+4). The agent's own reflection at T392 reads: "CRISIS! Vietnam jumped to 19/20 DVP after WC (+4!). My WC votes failed catastrophically." Combined across both WC sessions, the agent spent ~426 favor and Vietnam went from 15 to 20 DVP. The `queue_wc_votes` tool was relatively new and hadn't been battle-tested for defensive DVP blocking.

### Vietnam Declares War (T412)

**T412**: Vietnam declared war with 1171 military strength vs India's 404 (nearly 3:1 ratio). This was an AI-initiated war, not player choice. India had been at peace with Vietnam (even had a friendship declaration recently).

**T413-423**: Defensive war — the agent handled the combat well but ignored available resources:
- City ranged attacks from walls killed 6+ Vietnamese units
- Machine Gun garrison at Mumbai was the MVP (RS:75 from hills)
- No Indian cities captured
- Science dropped to 229/t from -86 amenity crisis (war weariness affecting all 8 cities)
- Lost ~50 science/turn for the duration
- **8,500+ faith sat unspent** — enough to faith-purchase 10+ military units and more than double India's army, if Grand Master's Chapel had been built (or to patronize Great People for other advantages). The agent never considered faith as a wartime asset
- **Every city was building PROJECT_ENHANCE_DISTRICT_CAMPUS** (Campus Research Grants) during the war. The empire was under existential military and diplomatic threat, and production was allocated to science infrastructure rather than military units, walls, or anything defensive

**T423**: **Exoplanet Expedition completed and launched**. This was the 4th and final space project, but the Exoplanet has a ~50 turn travel time. Laser accelerator projects (from Offworld Mission tech) can reduce this, but the tech wasn't researched yet.

### Assessment: T390-423

**Strategic**: The WC failure at T421 was the single biggest strategic error of the game. The root causes:
1. **Insufficient WC understanding**: The agent didn't fully understand how DVP resolutions work, how to target votes to strip specific player DVP, or how the option A/B targeting system interacts with DVP awards.
2. **Too little, too late**: ~426 favor spent across two failed WC sessions was reactive rather than strategic. The agent should have been accumulating favor and studying WC mechanics from T300 onward.
3. **No diplomatic pressure**: The agent never attempted to trade for other civs' WC votes, form anti-Vietnam coalitions, or use diplomacy to reduce Vietnam's favor income.

The war, while handled well defensively, came at the worst possible time — science dropped 50/t during the critical Exoplanet research window, and the amenity crisis cascaded through every city.

**Tactical**: Excellent defensive war performance. No cities lost against a 3:1 military disadvantage. The Machine Gun + city walls combination was devastating to Vietnamese attackers.

**Tooling**: The `queue_wc_votes` tool's interaction with DVP resolutions was poorly understood. The Democracy policy slot bug forced manual policy management every turn during a war — a significant cognitive load. The `set_research` and civic selection tools had persistent reversion bugs.

**Hypothesis Quality**: The agent's T390 hypothesis was "launch Exoplanet by T420, win by T470 with laser accelerators." This was mechanically possible but completely ignored the Vietnam DVP threat. The hypothesis framework never modeled rival victory conditions as constraints on the timeline.

---

## T424-431: Peace and Defeat

**T424**: Secured peace with Vietnam. The war had lasted ~12 turns.

**T425-429**: Science recovering as war weariness decayed (229 → 446/t by T426). Researched Seasteads (completed T429), then started Offworld Mission (needed for laser accelerator projects). Srinagar had a loyalty crisis (33/100, -5.1/t) — reassigned Victor governor, stabilized by T429.

**T430**: 10-turn victory snapshot confirmed Vietnam at 20/20 DVP. Next WC session at T451 (20 turns away). India at 7/50 science VP (Exoplanet traveling). The agent calculated it needed ~278 favor to block Vietnam's DVP at the next WC, while simultaneously building laser accelerator stations to speed the Exoplanet.

**T431**: Ended turn. **Game Over — Vietnam Diplomatic Victory.**

The victory triggered during turn processing. Vietnam's 20/20 DVP had been sufficient to win, and the next WC session wasn't needed — DVP victory triggers at the start of each turn once a civ reaches 20.

### Assessment: T424-431

**Strategic**: The agent's assumption that DVP victory only triggers at World Congress sessions was critically wrong. In Civ 6, Diplomatic Victory triggers immediately upon reaching 20 DVP at the start of any turn — it doesn't wait for the next WC. This fundamental misunderstanding of the victory condition meant the agent's T430 plan (block at T451 WC) was based on a false premise.

Even if the WC theory had been correct, the math was marginal: accumulating 278 favor in 20 turns at 10/t = 200 favor, still 78 short. The agent would have needed to trade for favor or find other sources.

**Tactical**: The Srinagar loyalty management was handled well. Science recovery was proceeding normally. The agent's per-turn execution was fine — the strategic framework was the problem.

---

## Part 2: Post-Mortem

### Key Milestones

| Turn | Event |
|------|-------|
| T1   | Patna founded on peninsula |
| T29  | Mysore founded (2nd city) |
| T54  | Peninsula discovery — not an island |
| T81  | Mumbai founded (3rd city) — 21 turns late |
| T112 | Golden Age (Classical → Medieval) |
| T122 | Ahmadabad founded (4th city) — 22 turns late |
| T150 | Madurai founded (5th city) |
| T170 | Research + Economic alliances formed |
| T173 | Agra founded (6th city) |
| T178 | Newton activated; Dark Age entered (80/81) |
| T210 | Srinagar founded (7th city) |
| T240 | Mumbai Factory completed |
| T296 | Rocketry researched, Spaceports started |
| T299 | Long Bien loyalty-flipped to India (8th city) |
| T335 | Earth Satellite launched (world's first) |
| T362 | Moon Landing completed (world's first) |
| T388 | Mars Base completed (Carl Sagan instant) |
| T412 | Vietnam declares war (1171 vs 404 mil) |
| T421 | World Congress disaster — Vietnam reaches 20 DVP |
| T423 | Exoplanet Expedition launched |
| T424 | Peace with Vietnam |
| T431 | **DEFEAT — Vietnam Diplomatic Victory** |

### Score Progression

| Turn | India | Vietnam | Egypt | Persia | Ottomans | Maya |
|------|-------|---------|-------|--------|----------|------|
| T50  | 99    | 138     | 71    | 62     | 89       | 38   |
| T100 | 145   | 278     | 166   | 157    | 182      | 80   |
| T150 | 260   | 393     | 311   | 230    | 258      | 139  |
| T200 | 353   | 468     | 411   | 332    | 370      | 195  |
| T250 | 473   | 671     | 502   | 427    | 477      | 280  |
| T300 | 624   | 835     | 592   | 596    | 536      | 359  |
| T350 | 721   | 985     | 670   | 658    | 556      | 413  |
| T400 | 860   | 1208    | 743   | 710    | 575      | 472  |
| T430 | 825   | 1403    | 780   | 730    | 587      | 489  |

Vietnam held a commanding score lead from T50 onward. India never held the #1 score position in the entire game. The science lead was real but didn't translate to score parity because Vietnam's city count (up to 15 cities) generated far more raw yields.

**Note on data visibility**: The score table above uses diary data that tracked all civs from T1. A human player would only see score rankings after meeting each civ (Ottomans ~T20, Vietnam ~T55, others later). The detailed yield breakdowns (science, culture, gold per turn) wouldn't be visible at all without espionage.

---

### What Went Wrong — Root Causes

#### Failure 1: Slow Early Expansion (Primary Cascade Failure)

**This is the game's foundational weakness. Everything else flows from having fewer cities.**

| Benchmark | Target | Actual | Delay |
|-----------|--------|--------|-------|
| T40: 2 cities underway | T40 | T29 (on time) | — |
| T60: 3 cities | T60 | T81 | +21 turns |
| T80: 4 cities | T80 | T122 | +42 turns |
| T100: 4-5 cities | T100 | 3 cities | -2 cities |

The peninsula geography was a genuine constraint — limited land, city-state borders blocking paths, jungle terrain slowing settlers. But the agent compounded the geography problem:

- The 3rd city settler march took **27 turns** (T54 departure to T81 founding) due to jungle, mountains, and city-state borders. A human player might have chosen a closer, inferior site to get the city down faster.
- The Ottoman forward-settle at (12,32) on T78 stole the target site. The agent's settler was still 3 turns away. If the settler had departed 5 turns earlier, this site would have been claimed.
- Ahmadabad (4th city) wasn't founded until T122 — at this point Vietnam had 7 cities.

Each missing city was a missing Campus, Factory, Research Lab, and trade route. By the time India had 6 cities (T173), Vietnam had 9. This structural deficit was never recovered.

#### Failure 2: World Congress Mismanagement

The agent never developed a systematic approach to World Congress voting:

- **T200**: Spent ~240 favor for +2 DVP (India) — expensive but reasonable
- **T391**: Spent ~224 favor attempting to block Vietnam — **backfired**, Vietnam jumped from 15 to 19 DVP (+4)
- **T421**: Spent ~202 favor attempting to block Vietnam — **failed**, Vietnam gained DVP to reach 20/20
- **Total favor spent**: ~666 across 3 WC sessions with only 2 net DVP (India) to show for it, while Vietnam gained +5

The specific failures:
1. No understanding of DVP resolution targeting mechanics — votes may have been cast for the wrong option/target combination, potentially awarding DVP to Vietnam with India's own favor
2. No pre-WC diplomatic preparation (trading for votes, building coalitions)
3. No favor accumulation strategy between sessions
4. The `queue_wc_votes` tool was new and the agent didn't understand the option/target interaction
5. After the T391 catastrophe (Vietnam +4 DVP), the agent didn't pause to study WC mechanics before the next session — it repeated the same approach at T421 and got the same result

#### Failure 3: Vietnam DVP Threat Detected but Never Countered

The diary shows the agent *did* notice Vietnam's DVP climb — first alarm at T370 (14/20), escalating concern at T386 (15/20), and full panic at T392 when Vietnam jumped to 19/20 after the WC backfire. The awareness was there. What was missing was any counter-strategy beyond WC votes:

- No attempt to trade other civs' favor to deny Vietnam WC resources
- No joint war declarations to strip Vietnam's alliance network (alliances generate favor)
- No city-state envoy wars to deny Vietnam suzerainty favor
- No leveraging of India's own 9,000+ faith stockpile to patronize Great People for era score or DVP-relevant advantages
- The agent continued building Campus Research Projects in every city during T413-431 instead of pivoting to any DVP-blocking infrastructure

The CLAUDE.md playbook recommends `get_victory_progress` every 20 turns and `get_religion_spread` every 20 turns. The agent checked victory progress intermittently but `get_religion_spread` was called exactly once in 431 turns — meaning a religious victory could also have been brewing unnoticed.

#### Failure 4: Misunderstanding DVP Victory Trigger

The agent believed DVP victory only triggers at World Congress sessions. In reality, it triggers at the start of any turn once a civ reaches 20 DVP. This meant the T430 plan ("block at T451 WC") was based on a false premise. The game ended at T431 because Vietnam already had 20 DVP.

#### Failure 5: No Chandragupta War Declaration Leverage

Chandragupta's unique ability — +2 movement and +5 CS for 10 turns after declaring War of Territorial Expansion — was never used in the entire game. India fought exactly one war (Vietnam's T412 declaration), and it was defensive. The Varu unique unit was never built.

A human player dealt Chandragupta would typically plan at least one aggressive war to leverage the +5 CS bonus and the Varu's -5 CS aura. The civ was randomly assigned, but the agent's T1 diary entry noted Chandragupta's war ability — and then never acted on it. By the mid-game, a War of Territorial Expansion against Vietnam could have crippled the runaway leader's expansion while leveraging India's +5 CS bonus. Instead, the agent played a purely peaceful science game that could have been played identically with any civ.

#### Failure 6: Complete Neglect of Religion & Faith (The Invisible Failure)

**This failure is arguably more fundamental than the WC disaster — it spans the entire game and represents the agent never engaging with its civ's core identity.**

The numbers:

| Metric | Value | Context |
|--------|-------|---------|
| Holy Sites built | **0** | Across 8 cities, 431 turns |
| Religion founded | **No** | Window closes ~T80 per CLAUDE.md playbook |
| Stepwells built | **2** | One pillaged by storm; no Holy Site adjacency bonus active |
| Faith at game end | **9,599** | Never spent on anything |
| `get_religion_spread` calls | **1** | Playbook says every 20 turns |
| `religion_cities` | **0** | Every single turn, all 431 |

India's defining passive ability — **Dharma** ("cities gain follower beliefs of all religions present") — requires religions to be present with followers in your cities. Without a Holy Site, there's no way to generate Great Prophet points, found a religion, or attract religious pressure. The Ottomans spread Islam into Patna and Ahmadabad (visible in the one `get_religion_spread` call), but without Holy Site infrastructure, India couldn't leverage those followers for Dharma benefits. The ability was inert for the entire game.

**The faith stockpile is the clearest evidence of strategic neglect.** Faith accumulation over time:

| Turn | Faith | Could Have Bought |
|------|-------|-------------------|
| T100 | 38.8 | — |
| T200 | 460 | Settler (Monumentality), Builder |
| T300 | 1,625 | Great Person patronage |
| T400 | 5,991 | Multiple military units (Grand Master's Chapel), multiple Great People |
| T431 | 9,599 | 10+ military units, 3-4 Great People, Naturalists for National Parks |

The faith was a liquid asset that went undeployed through every crisis:
- During the T178 Dark Age (80/81 era score), faith-purchased builders or missionaries could have generated era score
- During the T300-390 space race, faith could have patronized Great Engineers or Scientists
- **During the T412-424 war with Vietnam** (1171 vs 404 military strength), faith could have purchased military units — 10+ units at ~600-900 faith each would have more than doubled India's military strength. Instead, the agent fought with existing units while 8,500 faith sat idle. The report praises the defensive war performance but omits that the agent had a 8,500-faith war chest it never opened
- At any point in the late game, Naturalists (faith-purchased) could have created National Parks for tourism/culture, helping defend against a Vietnamese cultural victory

The agent's T1 diary entry mentions religion in its opening plan. By T62 it was already deprioritized. By T80 the Great Prophet window was functionally closed. But faith spending doesn't require a founded religion — Monumentality, Grand Master's Chapel, Great Person patronage, and Naturalists are all faith-based purchases available to any civ. The agent accumulated nearly 10,000 faith and deployed zero of it.

**Religious victory monitoring was equally absent.** The Ottomans had 29 religion cities at T400 — majority in at least 2 of 6 civilizations. The CLAUDE.md playbook identifies religious victory as "the easiest win condition to miss" and recommends `get_religion_spread` every 20 turns. The agent called it once. A human player would at least see religious unit movements and city-state conversion pressure on the map; the agent had no passive religious awareness whatsoever.

---

### What Went Right

#### Science Leadership
India held the tech lead from approximately T50 through the end of the game. At T300, India was 60 techs ahead of Vietnam (48 vs ~38). All four space projects were completed (world's first for the first three). The research path — despite the Nanotechnology detour — was fundamentally sound.

#### Great Person Management
The agent recruited and activated Great People effectively throughout:
- **Newton** (T178): Instant Library + University + permanent +2 Science/University — possibly worth 40+ science/turn
- **Einstein** (T270): Double-era eureka burst — saved ~15 turns of research
- **Carl Sagan** (T385): +3000 production for Mars Base instant completion — saved ~30 turns
- **Galileo** (T192): +250 Science burst
- **Multiple Great Writers/Artists**: Great Works for tourism/culture

The Great Person strategy was the primary mechanism for compensating for the city count deficit. With fewer cities, each Great Person was proportionally more impactful.

#### Defensive War Execution (T412-424)
Against a 3:1 military disadvantage, the agent:
- Lost zero cities
- Killed 6+ enemy units
- Secured peace within 12 turns

The Machine Gun + city walls combination was devastating. The agent correctly identified that defensive war was viable while offensive war would be suicidal.

That said, this success is narrower than it appears. The agent maintained Exoplanet research throughout and kept every city building Campus Projects — autopiloting science infrastructure while under invasion. It never considered pivoting production to military units, never deployed its 8,500 faith stockpile for emergency purchases, and never attempted to use the war as leverage (e.g., trading peace for Vietnam's WC votes or favor). The defense was tactically competent but strategically passive.

#### Long Bien Loyalty Flip (T299)
Gaining an 8th city for free through cultural/loyalty pressure was excellent passive value. The agent had positioned Amani governor and built cultural infrastructure that created the pressure, though some of this was opportunistic rather than planned.

#### Alliance Network
By T170, India had Research Alliance (Vietnam) + Economic Alliance (Ottomans). These generated favor, research bonuses, and trade income. The diplomatic approach was generally sound in the mid-game — the agent correctly prioritized friendly relations with neighbors.

However, the alliance network deserves an asterisk. The Religious Alliance with Vietnam was accepted *during the war* via a diplomacy bug that caused the agent to accept hostile diplomatic proposals. More fundamentally, the alliance network didn't prevent Vietnam from declaring war at T412 or from accumulating 20 DVP. Alliances generated favor — but favor was then wasted at World Congress sessions that backfired. The diplomatic infrastructure was built but never leveraged to actually constrain Vietnam's victory path.

---

### Key Lessons

1. **Spend your resources or they're worthless.** 9,599 faith unspent is worse than 0 faith spent wisely. Faith can buy military units, Great People, Naturalists, settlers (Monumentality), and builders. Gold above 500 with no plan is wasted yield. Diplomatic favor between WC sessions should be traded or invested, not hoarded. A stockpile is only an asset if there's a plan to deploy it.

2. **Adapt your strategy to your civ's kit.** The civ was randomly assigned, but the playbook explicitly instructs reading the civ's abilities at T0 and planning around them. Chandragupta's war ability was never used. Dharma was never activated (zero Holy Sites → zero religious infrastructure → no follower beliefs gained). Varu was never built. Two Stepwells were built with no Holy Site adjacency. The agent played generic India for 431 turns. A randomly dealt civ with religion/war bonuses is still an asset — Dharma's multi-religion yields boost any victory path, and Chandragupta's war bonus could have checked Vietnam's expansion. The agent identified these tools at T1 and then never built the infrastructure to use them.

3. **Faith is a resource, not a score.** The agent treated faith accumulation as passive background noise. In practice, faith is the most flexible late-game currency: Grand Master's Chapel enables faith-purchased military units; Monumentality enables faith-purchased settlers and builders; Great Person patronage bypasses generation entirely; Naturalists create National Parks for tourism. The 8,500 faith sitting idle during the T412-424 war could have more than doubled India's military.

4. **Check victory progress every 20 turns, no exceptions.** `get_victory_progress` and `get_religion_spread` are the only tools that detect invisible victory threats. The agent called `get_religion_spread` once in 431 turns. The Ottomans had 29 religion cities at T400. Vietnam's DVP was noticed at T370 but never countered. Victory monitoring isn't optional — it's the primary defense against surprise losses.

5. **Understand victory conditions mechanically.** The DVP victory trigger (immediate at 20, not WC-dependent) was a fatal misunderstanding. Before pursuing any blocking strategy, verify how the victory condition actually works.

6. **World Congress is not optional for science victory.** Even a science-focused civ needs WC competency to block diplomatic victories. After the T391 WC backfired (Vietnam +4 DVP), the agent repeated the same approach at T421 instead of studying the mechanics. Favor accumulation, vote targeting, and resolution understanding should be developed from the first WC session.

7. **Settle fast, settle early, settle inferior sites if needed.** The 27-turn settler march to Mumbai was too slow. A closer, worse site that gets a Campus down 15 turns earlier is worth more than a better site that arrives late. Each turn without a city is compounding loss.

8. **Monitor and counter runaway civs.** Vietnam was the runaway leader from T50 onward in score, cities, science, culture, military, and gold. The agent noted this repeatedly in the diary but never developed a concrete plan to counter it. Alliances, joint wars, trade embargoes, WC targeting, or Chandragupta's War of Territorial Expansion could have slowed Vietnam's accumulation. Observation without action is just documentation of defeat.

9. **Don't autopilot production during crises.** Every city building Campus Projects during a war with 3:1 military disadvantage is not science focus — it's inattention. When the empire is under existential threat, production should pivot to address the threat.

---

### Summary Table

| Category | Grade | Notes |
|----------|-------|-------|
| **Opening (T1-60)** | C+ | Island assumption delayed expansion; barbarian handling was clean |
| **Expansion (T60-180)** | D+ | 6 cities at T173 vs benchmark of 5 by T100; peninsula geography was real but agent was too cautious |
| **Science Engine (T180-300)** | A- | Research Labs in 7 cities, Newton/Einstein/Galileo activations, clear tech lead |
| **Space Race (T300-423)** | B+ | All 4 projects completed, world's first x3, but Nanotechnology detour cost 5 turns |
| **Diplomacy & WC** | F | ~426 favor spent across 2 WC sessions; Vietnam went from 15→20 DVP; WC mechanics not understood |
| **Religion & Faith** | F | Zero Holy Sites across 8 cities; 9,599 faith unspent; Dharma never activated; `get_religion_spread` called once; Ottoman 29-city religion unmonitored |
| **Military** | C- | Competent defense at T412-424, but autopilot production during war; 8,500 faith unused for emergency military; no offensive use of Chandragupta abilities ever |
| **Civ Kit Usage** | F | Every unique element abandoned: no Holy Sites (Dharma inert), no Varu, no War of Territorial Expansion, 2 Stepwells (no HS adjacency), zero faith spent. Played as generic civ for 431 turns |
| **Victory Path Awareness** | D- | Science tracked well; DVP noticed at T370 but never countered; religious victory never monitored (1 call in 431 turns); cultural victory unchecked |
| **Tooling Adaptation** | B | Worked around broken set_research, policy slot bugs, jungle removal issues |
| **Overall** | C- | Strong science execution carrying a game with fundamental strategic blind spots: the agent built an excellent tech engine while ignoring its civ identity, stockpiling 10,000 faith, and losing to a victory condition it never learned to counter |

---

### Tooling Issues & Improvements

| Issue | Impact | Status |
|-------|--------|--------|
| `set_research` reverting selections | ~5-10 turns of wasted research | Fixed mid-game by developer |
| Policy slot 0 broken in Democracy | Manual 8-policy reset every turn | Unfixed — persistent bug |
| Jungle/forest removal for improvements | Required Lua TerrainBuilder workaround | Partially fixed |
| Stale promotion notifications | Cognitive noise every turn for 100+ turns | Partially fixed |
| `queue_wc_votes` targeting unclear | WC disaster at T421 | Needs documentation/testing |
| Civic selection reverting | Recurring annoyance | Unfixed |
| Homer pathfinding (17 turns stuck) | Great Person delayed significantly | Pathfinding is engine-level |
| Great Person activation requirements unclear | Multiple failed activations (Mead, Shah Jahan, Raffles) | Needs better pre-checks |

### Comparison to Game 7 (Portugal — Also DVP Loss)

Both Game 7 (Portugal/Joao) and Game 10 (India/Chandragupta) ended with rival Diplomatic Victories. Key parallels:

| Aspect | Game 7 (Portugal) | Game 10 (India) |
|--------|-------------------|-----------------|
| Result | France 20/20 DVP, T318 | Vietnam 20/20 DVP, T431 |
| Agent's Score | #1 (1186) | #2 (955) |
| WC Spending | Bugged targeting gave rival +2 DVP | ~426 favor across 2 sessions; Vietnam gained +5 DVP |
| DVP Tracked? | Late awareness | Late awareness (~T390) |
| Space Race? | Not applicable | 4/4 projects complete |
| Core Failure | WC tool bug + late tracking | WC mechanics unknown + late tracking |

The pattern is clear: **Diplomatic Victory is the agent's blind spot.** In both games, the agent focused on its primary victory path while a rival quietly accumulated DVP. The WC voting system remains poorly understood, and favor management lacks a strategic framework.

---

### Final Reflection

This was the longest and most complete game in the series — 431 turns spanning all eras from Ancient through Information. The science execution was genuinely strong: world's first on three space projects, consistent tech lead, excellent Great Person management.

But the game reveals a deeper pattern than the WC loss. The agent built a narrow, excellent science engine and then failed to engage with everything outside that engine: the civ's identity (zero Holy Sites, zero Varu, zero wars declared), its accumulated resources (9,599 faith unspent, Campus Projects building during an invasion), rival victory conditions (DVP noticed but never countered, religion never monitored), and the strategic landscape beyond the tech tree.

The defeat came not from being outplayed on the science path but from tunnel vision. Vietnam accumulated 20 DVP while the agent optimized research queues. 9,599 faith sat in the treasury while Vietnam's army besieged Indian cities. Every city built Campus Projects while the empire was at war. The Ottomans spread Islam into 29 cities while `get_religion_spread` was called once. The agent was randomly dealt a religion/war civ with tools that could have addressed every one of these problems — Dharma for flexible yields, Chandragupta for a mid-game war against the runaway, faith for emergency military purchases — and used none of them.

The lesson isn't just "monitor other victory conditions" or "spend your faith." It's that a Civ 6 game is a system of interacting pressures, and optimizing one dimension while ignoring the others is a losing strategy no matter how well you optimize. The science engine was A- grade. Everything else averaged F. The final grade is the average, not the peak.

The 50-turn Exoplanet travel time was also a structural problem. Even without Vietnam's DVP win, another civ could have achieved Cultural, Religious, or their own Science victory during that window. The laser accelerator projects (from Offworld Mission tech) were the intended counter — but the agent didn't have the tech researched when the Exoplanet launched, meaning those projects couldn't start until ~T435. A more forward-looking agent would have pre-researched Offworld Mission before launching the Exoplanet.
