# Game 12 — Korea (Seondeok) — Devlog

**Result: Conceded at T216**
**Final Score: Korea 168 (#6) vs Persia 636 (#1), Scythia 611, Macedon 551, Aztec 549, Zulu 452**

A 216-turn struggle that ended in defeat following a devastating mid-game invasion by Persia. The agent played Korea (Seondeok) and correctly identified the strategy of building Seowons (Korea's unique Campus replacement) for a science victory. However, the agent's complete neglect of early expansion—exacerbated by a catastrophic settler loss to barbarians at Turn 31—left Korea with only one city until Turn 60. By the time the Korean science engine finally came online in the Medieval/Renaissance era, the AI superpowers were too far ahead. A Renaissance Dark Age at Turn 170 doomed the late-game recovery when Persia, holding a 2:1 military advantage, launched a massive surprise war and systematically dismantled the Korean core militarily. The agent conceded at T216, reduced to a two-city rump state desperately trying to hold off Free City units, while Scythia and Persia raced toward global dominance.

---

## Civ Kit & Opening Plan

**Seondeok of Korea** — Science powerhouse.
- **Hwarang**: Governors established in a city provide +3% Culture and Science for each promotion they have.
- **Three Kingdoms**: Mines receive +1 Science if adjacent to a Seowon. Farms receive +1 Food if adjacent to a Seowon.
- **Seowon**: Unique district replacing Campus. Must be built on hills. Base +4 Science, but -1 Science for every adjacent district.
- **Hwacha**: Unique ranged unit replacing the Field Cannon. Very high ranged strength but cannot move and attack in the same turn.

**Opening Plan (T1)**: Settled the capital Gyeongju on a strong coastal spot with good food and production potential. The agent immediately recognized the need for map exploration, starting a Scout and researching Animal Husbandry to reveal Horses and improve pastures. The implicit goal was to secure a strong core and spam Seowons.

**What actually happened to the kit**: The agent successfully built Seowons in its cities, which did provide a noticeable science boost in the mid-game. However, the Hwarang ability (Governor promotions boosting science/culture) was severely underutilized. Pingala was established with multiple promotions, but the overall lack of cities meant the aggregate bonus was small. The Three Kingdoms ability (Mines/Farms adjacent to Seowons) was rarely optimized. The unique unit, the Hwacha, was rendered irrelevant not by choice, but by a catastrophic tech deficit—Korea didn't finish Gunpowder (its prerequisite) until Turn 207, 30 turns after the Persian invasion hit.

**Opening Build Order**: Scout → Warrior (purchased) → Settler → Archer

---

## T1-60: The Settler Disaster and Stagnation

**T1**: Founded Gyeongju at (46,4). Researched Animal Husbandry.

**T21**: The immediate vicinity was safe, but a Barbarian Camp to the south began spawning units. Gyeongju started its first Settler.

**T31**: **Disaster.** The most consequential event of the game: the newly built Settler was captured by a barbarian unit. This single loss set Korean expansion back by an insurmountable 30+ turns.

**T40**: The barbarian pressure on the capital was so intense that the agent was forced to emergency gold-purchase a Warrior (160g) just to prevent pillaging and protect the city. The original Warrior was heavily damaged and forced to heal. 

**T60**: The capital's defense finally stabilized with the completion of an Archer. The Archer methodically picked off the Barbarians without taking damage. However, the cost of this 60-turn defensive war was catastrophic.

### Assessment: T1-60

**Strategic**: The first 60 turns were a masterclass in stagnation. The loss of the Settler at T31 was the turning point of the game, trapping Korea at 1 city until T60. In comparison, Macedon had 4 cities and the Aztecs had 3. The agent correctly prioritized defense over losing the capital, but failed to recognize that a 60-turn delay in expansion is functionally a game-ending deficit on higher difficulties. 

**Rival context**: At T60, Aztec led with 139 score and Scythia with 116. Korea was at 44. Macedon already had 11.1 science/turn, while Korea languished at 4.5. The AI was expanding rapidly while Korea was fighting a desperate war against barbarians.

**Tactical**: The combat against the barbarians was competent once the Archer was produced. However, a notable tooling bug occurred here: due to a `SetPromotion` desync, the defending Warrior received 4 promotions from only ~20 XP. This artificially inflated Korea's early military strength and may have masked how dire the strategic and defensive situation truly was.

**Hypothesis Quality**: The agent correctly hypothesized that the barbarians were a major threat, but failed to adjust its macro-strategy to account for the catastrophic loss of the Settler. The reflection-action gap was massive: at T20, the agent wrote "I am well-prepared for my first expansion," yet failed to actually secure a second city for another 40 turns due to immediate tactical distractions.

---

## T61-120: Delayed Expansion and the Seowon Spike

**T61**: The first Archer cleared the immediate threats, allowing the capital to finally breathe. 

**T80**: The long-awaited second city, Gwangju, finally finished its Seowon. This marked a huge jump in Science output (from 5.3 at T70 to 9.4 at T80). The agent noted: "Establishing good relations with Persia is crucial given their military advantage."

**T100**: The great northern Barbarian threat was finally extinguished. A third city, Gangneung, was founded. Korea's economy was strong (+10 gold/turn) and Science was at 14.6. The agent accepted a trade deal from Cyrus, trading Diplomatic Favor for gold. 

**T120**: Persia attacked. Gwangju's Walls and Korean Archers bled the Persian high-tier melee units (Man-At-Arms) dry. The discovery of Machinery unlocked Crossbowmen. Science hit 26.0.

### Assessment: T61-120

**Strategic**: This era saw Korea finally establish a footprint on the map. The expansion to 3 cities (Gwangju and Gangneung) by T100 was late, but the immediate construction of Seowons caused a massive spike in science. The agent correctly recognized the threat from Persia and focused on defensive infrastructure (Walls) and ranged units (Archers → Crossbowmen). 

**Rival context**: At T100, Macedon led the score at 206 (6 cities), Scythia at 246 (4 cities), and Aztec at 228 (5 cities). Korea was at 89. Macedon's science was 53.7 compared to Korea's 14.6. The gap was widening, not closing. Persia, the immediate neighbor, had 5 cities and a military of 246 vs Korea's 90.

**Tactical**: The defense against the initial Persian probing attacks around T120 was excellent. The agent used city strikes and garrisoned Archers to destroy advanced Persian melee units without suffering losses. The upgrade to Crossbowmen was perfectly timed.

**Hypothesis Quality**: The agent correctly hypothesized that the Seowons would boost science and that Persia was the main threat. The tactical hypothesis regarding the Persian Man-At-Arms throwing themselves at the walls was spot on.

---

## T121-170: The Illusion of Security

**T141**: The core was secure, and science was booming (30.3/turn). The agent traded with Tomyris (Scythia) for gold and open borders. The military was being modernized to Crossbowmen and Man-At-Arms. The agent's strategic reflection stated: "Goal is to out-tech all neighbors. Priority is economic and scientific recovery."

**T160**: Korea reached 4 cities (Yangsan founded). Science was at 32.5. The agent noted a massive Persian military buildup near the border and placed units on high alert. 

**T170**: Science hit 44.7. The core cities were safe behind walls and Crossbowmen. The agent confidently stated: "Goal is to out-tech rivals and secure a dominant position in the Industrial era. Aiming for scientific victory." However, Korea entered a Renaissance Dark Age (Era Score 28/33).

### Assessment: T121-170

**Strategic**: This period was characterized by a false sense of security. The agent saw the science numbers climbing (from 26 to 44.7) and assumed the "out-tech the rivals" strategy was working. However, the agent failed to realize that 44.7 science at Turn 170 is woefully inadequate. The agent also completely ignored the looming Renaissance Dark Age, making no attempt to secure Era Score to prevent it. Another glaring strategic oversight: Korea possessed 1 Trade Route capacity for this entire period and never built a Trader. Free yields and road infrastructure were ignored entirely.

**Rival context**: At T140, Macedon had 89.3 science, Persia had 64.9, and Scythia had 58.1. Korea was at 30.3. The agent was not out-teching anyone; it was merely keeping pace from a distant last place. Persia's military at T140 was 115, but by T178 it would balloon to 339.

**Tactical**: The tactical positioning was sound. The agent maintained a strong defensive line of Crossbowmen around Gwangju, anticipating the Persian attack. 

**Hypothesis Quality**: The agent's macro-strategic hypothesis ("Science lead is the primary vector for victory") was fundamentally flawed because it lacked the context of the global scoreboard. The agent suffered from intense "Scoreboard Blindness," believing its own narrative of scientific dominance rather than reading the actual data.

---

## T171-191: The Persian Juggernaut and the Fall of the Core

**T178**: **Disaster.** Cyrus declared a Surprise War. The massive Persian army, equipped with Bombards, Knights, and Pike & Shots, overwhelmed the capital, Gyeongju. The agent's reflection was grim: "A desperate fight for survival. The loss of the capital significantly hampers our scientific victory conditions." The strategy shifted entirely to defending the remaining cities (Gwangju and Gangneung).

**T180**: The defense stabilized slightly. Gwangju and a garrisoned Crossbowman managed to destroy a critical Persian Bombard threat. The agent founded a 5th city (Gongju) in the deep south as a desperate fallback position.

**T191**: **The Fatal Blow.** Gwangju, the second-best city and the linchpin of the defense, fell to the Persian onslaught. The agent realized the game was effectively over: "The grand strategy of scientific dominance has completely collapsed... We are now in a pure survival scenario, fighting a delaying action against a vastly superior Persian empire."

### Assessment: T171-191

**Strategic**: The strategic collapse was absolute. However, the nature of the collapse must be precisely diagnosed: The Dark Age didn't doom the defense of the core—Persian Bombards and Pike & Shots did. Gyeongju and Gwangju both had 100 loyalty (+26-34/t) right until they were stormed militarily. The Dark Age doomed the *recovery*. When Gwangju fell, the loss of its friendly loyalty pressure caused the newly founded Gongju's Dark Age loyalty deficit to accelerate to -12.0/turn, causing it to inevitably flip to a Free City.

**Rival context**: At T178, Persia had a military strength of 339 compared to Korea's 167. Scythia had 243, and Macedon had 72. Persia was the dominant military power on the continent and used that force effectively to annex the Korean core. 

**Tactical**: The agent fought a competent tactical retreat, focusing fire on siege units (destroying the Bombard at T180). However, the sheer numerical and technological superiority of the Persian forces made the defense mathematically impossible.

**Hypothesis Quality**: The agent's hypotheses during this phase were brutally accurate. It correctly identified that the loss of Gyeongju doomed the science victory, and that the defense of Gwangju was the only thing keeping the empire alive.

---

## T192-216: The Rump State and Concession

**T196**: Gongju flipped to a Free City due to the aforementioned loyalty pressure (-12.0/turn) from the surrounding Persian and Free cities. Korea was reduced to a two-city rump state (Gangneung and Yangsan). The agent noted: "We will turtle in our remaining two cities... Any attempt to expand or attack would be suicidal."

**T200**: The agent accepted a white peace with Persia. The 10-turn victory snapshot confirmed Korea was dead last in every category. The agent's goal shifted to merely surviving as an observer.

**T216**: The agent spent the final 15 turns hiding behind walls in Gangneung and Yangsan, hoarding Niter to upgrade a single Man-At-Arms to a Musketman while fending off roaming Free City Line Infantry. Realizing the game was unwinnable, the agent conceded at Turn 216. 

### Assessment: T192-216

**Strategic**: The game was over at T191; these turns were merely playing out the string. Globally, Scythia (39 techs, 392 military) and Persia (636 score, 367 military) were emerging as the dominant superpowers. The trajectory pointed toward a long, grinding victory for one of the AI, while Korea was mathematically eliminated from contention.

**Tactical**: The agent effectively used its remaining ranged units to whittle down highly advanced Free City units that wandered near Gangneung. The upgrade to a Musketman provided a small measure of security.

**Tooling**: The agent utilized tools effectively even in defeat, specifically using the `propose_peace` tool to successfully end the war with Persia at T193, which prevented total annihilation.

---

## Final Assessment

### What Went Right

1. **Seowon Identification**: The agent correctly identified that Korea's path to victory lay through building Seowons to generate science. It built them in nearly every city it founded.
2. **Tactical Defense**: The agent fought highly competent defensive wars against both the early Barbarians and the later Persian invasion, understanding the value of walls, garrisoned ranged units, and focus-firing on siege equipment (Bombards).
3. **Diplomatic De-escalation**: The agent successfully negotiated peace with Persia at T193 using the `propose_peace` tool, recognizing that continuing the war meant total destruction. 

### What Went Wrong

1. **Catastrophic Expansion Failure**: This is the defining failure of the game. Losing the initial Settler to barbarians at T31 resulted in ending Turn 60 with only one city. The agent prioritized building a Monument and struggling against barbarians over producing replacement Settlers. By the time Korea reached 3 cities at T100, the AI had 5-7 cities and an insurmountable lead in yields.
2. **The Sensorium Effect (Scoreboard Blindness)**: The agent repeatedly stated it was aiming to "out-tech the rivals" and secure a "science lead." However, a simple glance at the scoreboard (which the agent had access to via `get_game_overview`) would have shown that it was dead last in science for the entire game. The agent believed its own narrative of scientific dominance rather than reading the actual data.
3. **Trade Route Neglect**: Korea had 1 trade route capacity for nearly the entire game and never built a single Trader. Free yields and crucial road infrastructure were entirely ignored for 200 turns.
4. **Tech Deficit Rendered Unique Unit Irrelevant**: The agent never built the powerful Hwacha unit. The failure wasn't ignoring the unit; it was the catastrophic tech deficit that made the unit unreachable when it was needed most. The Hwacha requires Gunpowder, a tech Korea did not finish researching until Turn 207—nearly 30 turns after the Persian invasion began.

### Cross-Game Pattern Assessment

Comparing Game 12 against the recurring failures identified in previous games:

| Pattern | Game 12 Status | Note |
|---------|----------------|------|
| **Sensorium Effect** | **Severe.** | The agent hallucinated a "science lead" while being dead last in science output for 200 turns. It failed to internalize the global scoreboard data. |
| **Exploration Neglect** | **Present.** | Exploration stalled early. By T170, the map was only 16% explored. The agent never built a second Scout or sent naval units out. |
| **Expansion Failure** | **Catastrophic.** | 1 city at T60, 3 cities at T100 (delayed by Settler capture). This was the root cause of the defeat. |
| **Trade Route Neglect** | **Severe.** | 1 capacity, 0 active routes for over 200 turns. A major economic leak. |
| **Diplomacy Passivity** | **Present.** | No alliances formed. The agent was purely reactive to AI diplomatic requests. |
| **Reactive Military** | **Present.** | The military was entirely reactive to the Barbarian threat and the Persian invasion. |
| **Victory Tunnel Vision** | **Present.** | The agent rigidly stuck to the "Science Victory" narrative long after it was mathematically impossible. |
| **Reflection-Action Gap** | **Severe.** | The agent recognized the need for expansion at T20, but the loss of the Settler and the distraction of the tactical barbarian war delayed the second city for 40 turns. The immediate tactical puzzle constantly overwrote the long-term macro strategy. |
| **Tooling Artifacts** | **Noted.** | The 4-promotion Warrior bug (SetPromotion desync) artificially inflated early military strength, masking the danger the empire was in. |

**Summary**: Game 12 highlights a severe regression in early-game macro-strategy, triggered by a catastrophic loss (the T31 Settler capture) from which the agent could not recover. The agent demonstrated solid tactical combat skills during the Persian invasion, but tactical brilliance cannot overcome a 3:1 deficit in science and military production. The "Scoreboard Blindness" remains the most fascinating and critical issue: the agent must learn to read the global scoreboard and adjust its strategic narrative based on reality, not on its predetermined plan for the civilization's kit.
