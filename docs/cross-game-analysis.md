# Cross-Game Strategic Analysis (Games 1-4)

Meta-analysis of 4 games played by an LLM agent via the Civ 6 MCP harness. Purpose: identify recurring strategic weaknesses to refine the agent playbook (CLAUDE.md).

## Games Played

| Game | Civ | Turns | Outcome | Victory Type |
|------|-----|-------|---------|-------------|
| 1 | Poland | 323 | Conceded (loss) | Kongo winning Science/Diplo |
| 2 | Rome/Trajan | 221+ | Ongoing (behind) | Science path, 60% viability |
| 3 | Macedon/Alexander | 70 | Eliminated | Sweden military conquest |
| 4 | Byzantium | 182 | Defeated | Russia Religious Victory |

---

## Tier 1: Universal Failures (all 4 games)

### 1. The Sensorium Effect — Information Not Queried Doesn't Exist

The defining weakness across all games. A human player passively absorbs 50+ game-state signals per second through vision — minimap, score ticker, religion lens, unit health bars, fog boundaries, AI army movements. The agent has none of this. It only knows what it explicitly queries.

**Manifestations:**
- **Game 1**: Never checked diplomacy state, victory progress, or strategic map. 495 favor accumulated invisibly. Favor display bug (showed 0) went unquestioned for 200+ turns.
- **Game 2**: Periodic checks prescribed in playbook but not followed. `get_strategic_map` used once at T160 (when exploration failure was finally noticed). Self-diagnosed at T160: *"We optimize what we measure. The turn loop doesn't prompt 'what DON'T you see?'"*
- **Game 3**: No proactive scanning before moving civilians. No `get_diplomacy` after Sweden's denouncement. No `get_map_area` before settler movement.
- **Game 4**: `get_victory_progress` never checked between T0 and T182 (defeat turn). Russia converted all 21 cities to Orthodoxy over 112 turns with zero awareness.

**The pattern**: The agent only processes information that is pushed to it (notifications, blockers, combat encounters). Information requiring active polling (diplomacy trends, victory progress, map exploration, religion spread) goes unchecked until a crisis forces attention.

**Agent's own diagnosis (Game 2, T160)**: *"The ratio is roughly: 60% information gathering, 10% thinking, 25% execution, 5% reacting. I process ~3 state queries per 'look' at the game... I never see tiles I don't explicitly query."*

---

### 2. Exploration Neglect — The Foundation of Every Other Failure

You cannot settle what you cannot see. You cannot counter threats you don't know exist. Exploration generates no notifications, no blockers, no urgency signals — so it is perpetually deprioritized.

**Manifestations:**
- **Game 1**: 0 scouts after T54 (scout killed, never replaced). A river valley with 3 Rice, Tea, and Coal sat 5 tiles from Lublin for 323 turns unscouted. Two barbarian camps spawned 150 turns of siege from 6 tiles away. *"One scout at T50 would have found both."*
- **Game 2**: Scout stuck with NEEDS_PROMOTION blocker for 50+ turns. No second scout built. 34% explored at T160. China not met until T163. 3 city-states discovered in 3 turns at T178 — proving how little effort was needed.
- **Game 3**: 11% explored at T70 (game end). Scout built T1 but never mentioned again — likely killed or idle.
- **Game 4**: 9% at T40, 42% at T182. Only 1 scout built the entire game. Agent noted "CRITICAL — need more scouting" at T40, T65, T101 — never produced another scout.

**The compounding cost**: Every other failure (expansion, diplomacy, barbarians, religion blindness) traces back to not knowing the map. You can't settle optimal sites, meet civs for diplomacy, find barbarian camps, or see religious missionaries if you haven't explored.

---

### 3. Expansion Failure — The Yield Gap That Compounds Forever

More cities = more districts = more yields = victory. Each delayed city means a later Campus, later Library, later University — and the compound growth gap widens every turn.

**Manifestations:**
- **Game 1**: City 2 at T62 (benchmark: T30-40). City 3 at T124 (benchmark: T50-75). City 4 at T189 (benchmark: T80-100). Each 12-100 turns late. 4 cities vs Kongo's 10-15.
- **Game 2**: 49-turn gap between cities 2 and 3 (T35-T84). 2 cities at T77 vs AI's 5. Self-diagnosed: *"The 2-city bottleneck from T35-84 was too long."*
- **Game 3**: City 2 at T40 (settler captured at T27, 13-turn delay). No city 3. Sweden attacked a 2-city empire.
- **Game 4**: City 2 at T59. City 3 at T102. City 4 never founded (settler started T181, 1 turn before defeat). 3 cities vs Russia's 11.

**Root cause**: The agent builds infrastructure in existing cities (monuments, granaries, water mills, campuses) instead of producing settlers. Settlers are never treated as the highest-priority production item despite being the single highest-impact investment in the first 100 turns.

---

### 4. Diplomacy Passivity — A Yield Source Treated as an Interruption

Diplomacy generates favor (+1/turn per friendship, +1/turn per alliance, +2/turn per suzerainty), unlocks alliances (shared visibility, era score), and enables Diplomatic Victory. The agent treated it as something to respond to when prompted, never as something to actively pursue.

**Manifestations:**
- **Game 1**: 495 favor, 0 alliances, 0 friendships, 0 suzerainties in 323 turns. Diplomacy was purely reactive (responding to AI encounters).
- **Game 2**: 0 favor/turn for first 163 turns. Friendship available from Nubia at T99 but not pursued until T163. 216 favor idle at T221. No alliances despite having Diplomatic Service civic for 58 turns.
- **Game 3**: Sent delegations (both rejected), no follow-up. No friendship attempts, no trade deals. Diplomatically isolated when Sweden attacked.
- **Game 4**: All friendship attempts rejected repeatedly. 230 favor accumulated but never spent on World Congress votes. AI civs had to initiate friendships (T174), which expired 3 turns later.

**The compounding cost**: Each turn without friendships/alliances = missed favor income. Over 100 turns, the difference between 0 favor/turn and 5 favor/turn is 500 favor — enough for 5+ World Congress votes toward Diplomatic Victory.

---

## Tier 2: Frequent Failures (3 of 4 games)

### 5. Unescorted Civilians — The Rule That's Written and Violated Every Game

The playbook explicitly states: *"NEVER send builders to border tiles without checking get_map_area for threats."* This rule was violated in Games 1, 3, and 4, resulting in 8+ captured/killed builders and 1 captured settler.

- **Game 1**: 5+ builders lost to barbarians. Each loss acknowledged with "lesson learned" — then repeated.
- **Game 3**: Builder captured T19, settler captured T27. The settler loss delayed city 2 by 13 turns and was the proximate cause of elimination.
- **Game 4**: Builder captured T61, builder killed T125. Despite noting "ALWAYS escort builders" after the first loss.

**The pattern**: The agent checks `get_map_area` around cities and known threats but not along the path a civilian is about to take. The fix is simple: scan the destination tile and adjacent tiles before moving any civilian.

---

### 6. Reactive Military / Barbarian Camp Neglect

Barbarian camps spawn progressively stronger units as the game advances (Warriors → Swordsmen → Man-at-Arms → Line Infantry). Camps that aren't destroyed early become exponentially harder to clear later. The agent consistently fought barbarians defensively instead of proactively clearing camps.

- **Game 1**: Two camps spawned 150 turns of siege. Line Infantry (CS:65) terrorized Lublin while the agent had Crossbows (RS:40). Camps were never found because exploration failed.
- **Game 2**: "The Great Barb Invasion" at T88-97. Eastern camp spawned units for 100+ turns. Agent noted "camp keeps spawning" but never sent a force to destroy it.
- **Game 4**: 20 turns of barbarian crisis T21-T40. Man-at-Arms distraction consumed final 7 turns before Russia's victory.

---

### 7. Victory Path Tunnel Vision — Science Fixation Despite Impossible Odds

The agent consistently committed to Science Victory and never seriously reconsidered, even when the math was impossible.

- **Game 1**: Committed to science at T160 despite being 18 techs behind Kongo's 15-city empire. Diplomatic Victory was viable (588 favor, 4 friendly civs) but ignored until T300.
- **Game 2**: Science at 60% viability. Zero Theater Squares built across 7 cities in 221 turns. No backup victory path developed.
- **Game 4**: Science with 3 cities and 55 sci/turn vs Russia's 94 sci/turn and 11 cities. Promoted Pingala with Space Initiative at T172 (0/50 science VP). Never checked victory progress.

**Root cause**: The agent defaults to "build Campus, research tech" regardless of strategic context. Science feels productive because it always shows progress (tech completed!), but it requires 4+ cities with full district chains to actually win. The agent never asks "can I actually win science from this position?"

---

### 8. Gold/Faith Hoarding — Resources That Depreciate While Sitting Idle

The playbook says "Gold above 500 should be invested." This rule was violated in every game where the agent survived past T100.

- **Game 1**: Ended with 1,618 gold + 2,818 faith. Never spent faith on anything.
- **Game 2**: 3,936 gold at T221 (+147/turn). Wrote an analysis called "The 3936 Gold Problem" listing exactly what to buy — then didn't buy it.
- **Game 4**: 646 gold + 876 faith idle at T174. Could have purchased builders, tiles, or Great Scientists.

**The pattern**: The agent recognizes hoarding as a problem in every reflection but lacks a trigger to spend. Gold/faith accumulation is passive and invisible — it requires active checking and decision-making to deploy.

---

### 9. The Reflection-Action Gap — Excellent Analysis, Zero Follow-Through

The most striking meta-pattern: the agent writes correct, detailed strategic analyses in every major reflection, then fails to execute on any of them.

- **Game 2, T77**: "Explore south/east — we've only seen a tiny slice of the map." → No action taken.
- **Game 2, T103**: "Send delegation to Nubia, pursue friendship." → Not done for 60+ turns.
- **Game 2, T207**: "Gold hoarding needs to stop. 1888 gold." → Gold doubled to 3,936 by T221.
- **Game 3**: Wrote detailed lessons from Games 1 and 2 (civilian safety, exploration, gold spending). Violated nearly every lesson within 30 turns.
- **Game 4, T40**: "CRITICAL — need more scouting." → No additional scouts produced in 142 remaining turns.

The agent produces strategy-guide-quality analysis but operates as if each turn is independent of the last. There is no mechanism to carry forward commitments from one reflection to the next turn.

---

## Tier 3: Recurring Failures (2 of 4 games)

### 10. Trade Route Neglect
- **Game 1**: Foreign Trade completed ~T65, first trader built ~T125 (60 turns idle).
- **Game 2**: Unlocked T29, first route T37, but underutilized for 136 turns. Ghost bug disabled routes T148-165.

### 11. Religion/Faith Blindness
- **Game 2**: No Holy Site ever built. 524 faith with no expenditure path. Religion permanently closed.
- **Game 4**: Playing Byzantium (a religious civ!) without monitoring religion. Russia converted all cities over 112 turns. The civ's signature abilities were permanently locked out by not founding a religion.

### 12. District Timing
- **Game 1**: Zero districts at T75. First Campus at T94.
- **Game 2**: Zero Theater Squares in 221 turns across 7 cities. Culture at half of every rival.

### 13. Civ Ability Waste
- **Game 3**: Alexander's domination kit (Hypaspists, Hetairoi, no war weariness) completely unused. Played a generic science opening instead of the military opening the civ demands.
- **Game 4**: Byzantium's Taxis ability (+3 CS per holy city converted) permanently locked by not founding a religion. Played as a generic civ with no bonuses for 182 turns.

---

## Root Cause Hierarchy

The patterns are not independent. They form a causal chain:

```
1. Sensorium Effect (root cause)
   └→ 2. Exploration Neglect (can't see what you don't query)
       └→ 3. Expansion Failure (can't settle what you can't see)
           └→ 4. Fewer Cities → fewer districts → less output
               └→ 5. Victory Path Impossible (science needs 4+ cities)
                   └→ 6. Tunnel Vision (committed to losing path)

   └→ 7. Diplomacy Passivity (not actively monitored)
       └→ 8. No favor income → no alliances → no shared visibility
           └→ 9. Diplomatic Victory path closed

   └→ 10. Religion Blindness (not actively monitored)
       └→ 11. Rival religious victory invisible until 1 turn before loss
```

**Gold hoarding** and **unescorted civilians** are independent execution failures that compound the strategic problems but don't cause them.

**The reflection-action gap** is the meta-failure: the agent can diagnose every problem correctly but lacks the discipline to execute on its own prescriptions.

---

## Implications for CLAUDE.md Revision

The current playbook contains correct advice for almost every failure above. The problem is structural:

1. **Soft suggestions don't change behavior.** "Don't hoard gold" has been in the playbook since Game 1. Gold hoarding occurred in Games 2, 3, and 4.

2. **Periodic checks are never performed.** "Check `get_strategic_map` every 15-25 turns" is advice that requires the agent to count turns and remember to check. It never does.

3. **The turn loop is tactical, not strategic.** The current loop (get_overview → get_units → move → get_cities → set_production → end_turn) handles immediate mechanics well. It has no strategic checkpoint forcing the agent to ask "am I expanding? am I checking victory progress? am I spending gold?"

4. **Benchmarks exist but aren't enforced.** "4 cities by T100" is written but the agent never compares actual state to the benchmark and decides "I'm behind — build a settler NOW."

### What needs to change:

- **Hard triggers over soft advice.** "IF gold > 500, list 3 things to buy this turn" not "don't hoard gold."
- **Mandatory strategic checkpoints tied to turn numbers.** Every 10 turns: check exploration %, city count vs benchmark, gold/faith balance, diplomatic status.
- **Expansion framed as non-negotiable.** Settlers are the #1 production priority until city count benchmarks are met. Infrastructure comes second.
- **Civ-specific strategy at game start.** Before T1, read the civ's abilities and identify what makes this civ different. Don't play Byzantium like Rome.
- **Victory reassessment with kill criteria.** "If city_count < 4 at T100, science victory is not viable. Pivot now."
- **Civilian safety as a pre-move gate.** Before moving ANY civilian: scan destination + adjacent tiles. No exceptions.
