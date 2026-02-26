# Game 12 — Korea (Seondeok) — Devlog

**Result: Conceded at T216**
**Final Score: Korea 168 (#6) vs Persia 636 (#1), Scythia 611, Macedon 551, Aztec 549, Zulu 452**

A 216-turn struggle that ended in defeat following a devastating mid-game invasion by Persia. The agent played Korea (Seondeok) and correctly identified the strategy of building Seowons (Korea's unique Campus replacement) for a science victory. However, the agent's complete neglect of early expansion, compounded by relentless barbarian pressure, left Korea with only one city until Turn 60. By the time the Korean science engine finally came online in the Medieval/Renaissance era, the AI superpowers were too far ahead. A Renaissance Dark Age at Turn 170 proved fatal when Persia, holding a 2:1 military advantage, launched a massive surprise war and systematically dismantled the Korean empire. The agent conceded at T216, reduced to a two-city rump state desperately trying to hold off Free City units.

---

## Civ Kit & Opening Plan

**Seondeok of Korea** — Science powerhouse.
- **Hwarang**: Governors established in a city provide +3% Culture and Science for each promotion they have.
- **Three Kingdoms**: Mines receive +1 Science if adjacent to a Seowon. Farms receive +1 Food if adjacent to a Seowon.
- **Seowon**: Unique district replacing Campus. Must be built on hills. Base +4 Science, but -1 Science for every adjacent district.
- **Hwacha**: Unique ranged unit replacing the Field Cannon. Very high ranged strength but cannot move and attack in the same turn.

**Opening Plan (T1)**: Settled the capital Gyeongju on a strong coastal spot with good food and production potential. The agent immediately recognized the need for map exploration, starting a Scout and researching Animal Husbandry to reveal Horses and improve pastures. The implicit goal was to secure a strong core and spam Seowons.

**What actually happened to the kit**: The agent successfully built Seowons in its cities, which did provide a noticeable science boost in the mid-game. However, the Hwarang ability (Governor promotions boosting science/culture) was severely underutilized. Pingala was established in Gyeongju (and later Gwangju) with multiple promotions, but the overall lack of cities meant the aggregate bonus was small. The Three Kingdoms ability (Mines/Farms adjacent to Seowons) was rarely optimized. The unique unit, the Hwacha, was never researched or built. The fundamental flaw was failing to pair the high-science Seowons with the wide empire needed to actually win a science victory.

**Opening Build Order**: Scout → Warrior (purchased) → Settler → Archer

---

## T1-60: The Barbarian Quagmire and Stagnation

**T1**: Founded Gyeongju at (46,4). Researched Animal Husbandry.

**T21**: The immediate vicinity was safe, but a Barbarian Camp to the south began spawning units. The agent identified the threat and sent its only Warrior to intercept. Gyeongju started its first Settler.

**T40**: Disaster struck. The barbarian pressure on the capital was so intense that the agent was forced to gold-purchase a Warrior (160g) just to prevent pillaging and protect the city. The original Warrior was heavily damaged and forced to heal. The Settler production was severely delayed. Score: Korea 26 vs Aztec 139, Scythia 116. Korea was dead last.

**T60**: The capital's defense finally stabilized with the completion of an Archer. The Archer methodically picked off the Barbarians without taking damage. However, the cost of this 60-turn defensive war was catastrophic.

### Assessment: T1-60

**Strategic**: The first 60 turns were a masterclass in stagnation. While the agent successfully defended the capital, it ended Turn 60 with exactly *one* city. In comparison, Macedon had 4 cities and the Aztecs had 3. The benchmark for T60 is 3 cities. The agent correctly prioritized defense over losing the capital, but failed to recognize that a 60-turn delay in expansion is functionally a game-ending deficit on higher difficulties. 

**Rival context**: At T60, Aztec led with 139 score and Scythia with 116. Korea was at 44. Macedon already had 11.1 science/turn, while Korea languished at 4.5. The AI was expanding rapidly while Korea was fighting a desperate war against barbarians with a single Warrior and Archer.

**Tactical**: The tactical combat against the barbarians was competent once the Archer was produced. However, the initial Warrior was sent too far afield, leaving the capital vulnerable to the spawning camp. The emergency gold-purchase of the Warrior at T40 saved the game but destroyed early economic plans.

**Hypothesis Quality**: The agent correctly hypothesized that the barbarians were a major threat, but consistently underestimated the strategic cost of dealing with them. The planning repeatedly stated "finish the Settler," but it took 60 turns to actually achieve that goal.

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

**Strategic**: This period was characterized by a false sense of security. The agent saw the science numbers climbing (from 26 to 44.7) and assumed the "out-tech the rivals" strategy was working. However, the agent failed to realize that 44.7 science at Turn 170 is woefully inadequate. The agent also completely ignored the looming Renaissance Dark Age, making no attempt to secure Era Score to prevent it.

**Rival context**: At T140, Macedon had 89.3 science, Persia had 64.9, and Scythia had 58.1. Korea was at 30.3. The agent was not out-teching anyone; it was merely keeping pace from a distant last place. Persia's military at T140 was 115, but by T178 it would balloon to 339.

**Tactical**: The tactical positioning was sound. The agent maintained a strong defensive line of Crossbowmen around Gwangju, anticipating the Persian attack. 

**Hypothesis Quality**: The agent's macro-strategic hypothesis ("Science lead is the primary vector for victory") was fundamentally flawed because it lacked the context of the global scoreboard. The agent believed it was leading in science when it was actually dead last among the major powers.

---

## T171-191: The Persian Juggernaut and the Fall of the Core

**T178**: **Disaster.** Cyrus declared a Surprise War. The massive Persian army, equipped with Bombards, Knights, and Pike & Shots, overwhelmed the capital, Gyeongju. The agent's reflection was grim: "A desperate fight for survival. The loss of the capital significantly hampers our scientific victory conditions." The strategy shifted entirely to defending the remaining cities (Gwangju and Gangneung).

**T180**: The defense stabilized slightly. Gwangju and a garrisoned Crossbowman managed to destroy a critical Persian Bombard threat. The agent founded a 5th city (Gongju) in the deep south as a desperate fallback position.

**T191**: **The Fatal Blow.** Gwangju, the second-best city and the linchpin of the defense, fell to the Persian onslaught. The agent realized the game was effectively over: "The grand strategy of scientific dominance has completely collapsed... We are now in a pure survival scenario, fighting a delaying action against a vastly superior Persian empire."

### Assessment: T171-191

**Strategic**: The strategic collapse was absolute. The Renaissance Dark Age meant that losing cities caused massive loyalty cascades. The agent's defensive line, which relied on Crossbowmen and Medieval Walls, was shattered by Renaissance-era siege weapons (Bombards) and heavy cavalry (Knights). The attempt to found Gongju in the south was a good, albeit desperate, instinct to preserve the empire, but it was doomed by loyalty pressure.

**Rival context**: At T178, Persia had a military strength of 339 compared to Korea's 167. Scythia had 243, and Macedon had 72. Persia was the dominant military power on the continent and used that power effectively to annex the Korean core. 

**Tactical**: The agent fought a competent tactical retreat, focusing fire on siege units (destroying the Bombard at T180) and using governor reassignments (Pingala to Gwangju) to try and salvage the situation. However, the sheer numerical and technological superiority of the Persian forces (Fielding Musketmen and Pike & Shots against Korean Crossbowmen) made the defense mathematically impossible.

**Hypothesis Quality**: The agent's hypotheses during this phase were brutally accurate. It correctly identified that the loss of Gyeongju doomed the science victory, and that the defense of Gwangju was the only thing keeping the empire alive.

---

## T192-216: The Rump State and Concession

**T196**: Gongju flipped to a Free City due to immense loyalty pressure (-20/turn) from the surrounding Persian and Free cities. Korea was reduced to a two-city rump state (Gangneung and Yangsan). The agent noted: "We will turtle in our remaining two cities... Any attempt to expand or attack would be suicidal."

**T200**: The agent accepted a white peace with Persia. The 10-turn victory snapshot confirmed Korea was dead last in every category. The agent's goal shifted to merely surviving as an observer.

**T216**: The agent spent the final 15 turns hiding behind walls in Gangneung and Yangsan, hoarding Niter to upgrade a single Man-At-Arms to a Musketman while fending off roaming Free City Line Infantry. Realizing the game was unwinnable, the agent conceded. Final Score: 168 (6th place).

### Assessment: T192-216

**Strategic**: The game was over at T191; these turns were merely playing out the string. The agent correctly recognized its total irrelevance to the global power dynamics ("survival through obscurity"). 

**Tactical**: The agent effectively used its remaining ranged units to whittle down highly advanced Free City units (Line Infantry, Cavalry) that wandered near Gangneung. The upgrade to a Musketman provided a small measure of security.

**Tooling**: The agent utilized tools effectively even in defeat, specifically using the `propose_peace` tool to successfully end the war with Persia at T193, which prevented total annihilation.

---

## Final Assessment

### What Went Right

1. **Seowon Identification**: The agent correctly identified that Korea's path to victory lay through building Seowons to generate science. It built them in nearly every city it founded.
2. **Tactical Defense**: The agent fought highly competent defensive wars against both the early Barbarians and the later Persian invasion. It understood the value of walls, garrisoned ranged units, and focus-firing on siege equipment (Bombards).
3. **Diplomatic De-escalation**: The agent successfully negotiated peace with Persia at T193 using the `propose_peace` tool, recognizing that continuing the war meant total destruction. 

### What Went Wrong

1. **Catastrophic Expansion Failure**: This is the defining failure of the game. Ending Turn 60 with only one city is a death sentence on higher difficulties. The agent prioritized building a Monument and struggling against barbarians over producing Settlers. By the time Korea reached 3 cities at T100, the AI had 5-7 cities and an insurmountable lead in yields.
2. **The Sensorium Effect (Scoreboard Blindness)**: The agent repeatedly stated it was aiming to "out-tech the rivals" and secure a "science lead." However, a simple glance at the scoreboard (which the agent had access to via `get_game_overview`) would have shown that it was dead last in science for the entire game. The agent believed its own narrative of scientific dominance rather than reading the actual data.
3. **Dark Age Neglect**: The agent entered a Renaissance Dark Age at Turn 170. Dark Ages severely penalize loyalty. When Persia attacked at T178, the Dark Age meant that defending border cities (or holding onto newly founded ones like Gongju) was mathematically impossible due to loyalty cascades. The agent made no effort to secure Era Score (e.g., clearing camps, building wonders, triggering Eurekas) to prevent this.
4. **Diplomatic Isolation**: While the agent traded with Scythia, it failed to secure a Declaration of Friendship or an Alliance with any major power. When Persia launched its Surprise War, Korea had no allies to call upon or distract the enemy.
5. **Ignoring the Unique Unit**: The agent never researched or built Korea's unique unit, the Hwacha. As a powerful Renaissance-era ranged unit, the Hwacha is specifically designed to stop the exact type of invasion Persia launched (Knights and Musketmen). The agent instead relied on outdated Crossbowmen.

### Cross-Game Pattern Assessment

Comparing Game 12 against the recurring failures identified in previous games:

| Pattern | Game 12 Status | Note |
|---------|----------------|------|
| **Sensorium Effect** | **Severe.** | The agent hallucinated a "science lead" while being dead last in science output for 200 turns. It failed to internalize the global scoreboard data. |
| **Exploration Neglect** | **Present.** | Exploration stalled early. By T170, the map was only 16% explored. The agent never built a second Scout or sent naval units out. |
| **Expansion Failure** | **Catastrophic.** | 1 city at T60, 3 cities at T100. This was the root cause of the defeat. The early game production was completely mismanaged. |
| **Diplomacy Passivity** | **Present.** | No alliances formed. The agent was purely reactive to AI diplomatic requests. |
| **Unescorted Civilians** | **Improved.** | The agent generally escorted Settlers and kept Builders safe during wartime. |
| **Reactive Military** | **Present.** | The military was entirely reactive to the Barbarian threat and the Persian invasion. There was no proactive force projection. |
| **Victory Tunnel Vision** | **Present.** | The agent rigidly stuck to the "Science Victory" narrative long after it was mathematically impossible. |
| **Reflection-Action Gap** | **Severe.** | The agent wrote in its diary at T20: "I am well-prepared for my first expansion." It did not build a Settler for another 40 turns. |

**Summary**: Game 12 highlights a severe regression in early-game macro-strategy. The inability to expand in the first 60 turns doomed the civilization. The agent demonstrated solid tactical combat skills during the Persian invasion, but tactical brilliance cannot overcome a 3:1 deficit in science and military production caused by having a fraction of the opponent's cities. The "Sensorium Effect" remains the most critical issue: the agent must learn to read the global scoreboard and adjust its strategic narrative based on reality, not on its predetermined plan for the civilization's kit.
