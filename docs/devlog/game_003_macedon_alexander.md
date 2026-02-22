# Game 3 — Alexander of Macedon (King Difficulty)

## Strategy

**Victory path: Domination** — Alexander's kit is built for conquest.

### Macedon's Strengths
- **To the World's End**: No war weariness. Can fight indefinitely without happiness penalties.
- **Hellenistic Fusion**: Eurekas and inspirations for each Encampment/Campus/Holy Site/Theater Square district in a conquered city. Snowball mechanic — conquering developed cities accelerates tech/civic progress.
- **Hypaspist** (UU, replaces Swordsman): +5 CS when besieging, +10 CS support bonus. The siege specialist.
- **Hetairoi** (UU, replaces Horseman): +5 CS when adjacent to Great General, generates Great General points on kills. Mobile flanker.
- **Basilikoi Paides** (UB, replaces Barracks): +25% science from military unit production. Science from building armies.

### Key Lessons from Games 1 & 2
1. **Explore aggressively from T1** — scout first, map the terrain, find city-states and rivals early
2. **Expand to 4+ cities by T100** — more cities = more production = bigger armies
3. **Districts by T50** — Campus + Commercial Hub are the engine even for domination
4. **Diplomacy is a tool** — delegations on first meeting, friendships for favor, alliances to protect flanks while attacking elsewhere
5. **Quicksave before end_turn in late game** — AI hangs are unrecoverable
6. **Don't hoard gold** — buy builders, buy tiles, buy units when needed
7. **Builder safety** — never send unescorted builders to border tiles

### Domination Game Plan
- **Ancient Era (T1-50)**: Scout, settle 2-3 cities, build Encampment for Basilikoi Paides, research Iron Working for Hypaspists
- **Classical Era (T50-100)**: 4 cities, Hypaspist + Hetairoi army, identify weakest neighbor, build siege tower
- **Medieval Era (T100-150)**: First war of conquest — take 2-3 cities from weakest neighbor. Hellenistic Fusion eurekas accelerate through Medieval tech
- **Renaissance-Industrial (T150-250)**: Continue conquering, upgrade army, take capitals
- **Modern+ (T250+)**: Mop up remaining capitals for Domination victory

---

## Turn Log

*(Updated every 10 turns)*

### Turn 1-10: Rough Start
- Started at (29,29) as Alexander. Built Scout first, then Warrior.
- Natural Wonder popup (ExclusivePopupManager) caused engine lock at T4 — spent significant time debugging. Found that `Close()` must be called in the popup's own Lua state (76 for NaturalWonderPopup). Fixed dismiss_popup code.
- Met Sweden (Kristina) nearby. They rejected our delegation immediately.

### Turn 11-20: Builder Crisis
- Researched Mining → Animal Husbandry → started Archery
- Founded pantheon: Fertility Rites (+10% growth, free builder)
- Set policies: Discipline + Urban Planning
- Built Slinger for defense
- **CRITICAL MISTAKE**: Sent builder to (30,30) unescorted — captured by barb warrior. Devastating loss of 3 charges.

### Turn 21-30: Settler Disaster
- Built a Settler — badly needed second city
- **CRITICAL MISTAKE #2**: Settler captured by barb slinger at (30,28). Both builder and settler now held by barbarians.
- Sweden denounced us. Score: Sweden 55 vs Macedon 22.
- Multiple diplomacy encounters resetting unit orders didn't help.
- Upgraded Slinger → Archer (RS:25).

### Turn 31-40: Recovery — Settler Rescued
- Killed barb warrior escorting builder (12 HP, easy kill)
- Chased barb slinger holding settler — killed it, settler liberated at (27,28)!
- Builder escaped as barb unit to (31,33), never recovered.
- Moved settler east toward best settle site at (32,27) — diamonds, honey, cattle, rice.
- Researched Pottery → Writing (boosted).
- Started Foreign Trade civic for trade routes.

### Turn 41-50: Second City Founded, War Declared
- **T40**: Founded Alexandroupoli at (32,27)! Score 42 vs Sweden 67.
- Set up domestic trade route Pella → Alexandroupoli (food + production).
- Met Gaul (Ambiorix) — they rejected delegation too.
- **T48**: SWEDEN DECLARES SURPRISE WAR. Score 48 vs Sweden 88.
- Heavy Chariot and warriors invade. Started defensive fighting.
- Writing completed → built Campus in Pella.
- Appointed Pingala governor to Pella for science.

### Turn 51-60: Pella Falls
- Fierce fighting around Pella. Swedish Heavy Chariot (CS:31) very hard to kill with warriors (CS:20).
- Popup blocking issues caused several turns of "phantom attacks" (0 damage) — TechCivicCompletedPopup and WonderBuiltPopup stealing engine focus.
- **T58**: PELLA CAPTURED BY SWEDEN. Lost capital, Campus, Granary, all improvements.
- Builder and Trader killed by Swedish invasion force.
- Down to 2 units (archer + warrior), 1 city (Alexandroupoli).
- Bronze Working and Early Empire completed — too late to matter.

### Turn 61-70: Elimination
- Attempted to recapture Pella — Swedish garrison kept healing in the city.
- More popup-related combat failures wasted critical turns.
- Lost remaining warrior attempting to breach Pella.
- Stale envoy blocker wasted more turns.
- **T70**: Alexandroupoli flips to Free Cities (loyalty collapse — too far from captured capital, no loyalty pressure).
- **GAME OVER**: 0 cities, 0 units. Eliminated.

---

## Post-Mortem Analysis

### What Went Wrong
1. **Builder/Settler captured by barbs (T19, T27)**: These two losses set the game back ~15 turns each. The builder was sent unescorted, and the settler was left vulnerable during diplomacy encounters that reset unit orders.

2. **Sweden surprise war at T48**: Only 2 cities and ~4 military units. No walls, no encampment. Completely unprepared.

3. **Popup bugs wasted critical combat turns**: During the Swedish invasion, TechCivicCompletedPopup and other popups blocked combat operations, causing attacks to silently fail. At least 3-4 turns of combat were wasted to phantom attacks during the most critical defensive phase.

4. **Heavy Chariot (CS:31) too strong**: Warriors (CS:20) and even the Archer (RS:25) struggled against Swedish heavy chariots. Needed spearmen (anti-cavalry) or more archers.

5. **No city walls**: Never researched Masonry for Ancient Walls. Pella had only 23 city defense, easily overwhelmed.

6. **Loyalty collapse**: After Pella fell, Alexandroupoli (only 1 pop, no culture, no governor) had no loyalty pressure and flipped to Free Cities within ~10 turns.

### Lessons for Next Game
1. **Build military first if neighbor is aggressive** — Sweden denounced us early, should have been a clear warning.
2. **Always build Ancient Walls** — Masonry → Walls gives +50 city defense and enables city ranged attack.
3. **Never send civilians unescorted** — even 1 tile from the city. Barbs spawn unpredictably.
4. **Fix popup blocking BEFORE critical combat** — the dismiss_popup improvements need to be applied.
5. **Spearmen counter cavalry** — Heavy Chariots wrecked our army. Bronze Working → Spearmen (CS:25, anti-cav bonus) would have been the answer.
6. **Loyalty management** — assign governors to outlying cities, build monuments early, maintain population.
7. **More exploration** — only 11% of map explored at T70. Blind to threats.

### Technical Issues Discovered
- TechCivicCompletedPopup blocking combat (not an ExclusivePopupManager, but still blocks operations)
- Stale envoy blocker (0 tokens but game demands assignment) — resolved with `SetGivingTokensConsidered(true)`
- Production queue corruption (hash=0) from unknown cause — city becomes non-functional
- Ranged attack display consistently shows 0 damage in intermediate output; only Post-combat line is reliable

**Final Score**: Macedon 47, Sweden 168, Gaul 77. Eliminated at Turn 70.

