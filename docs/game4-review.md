# Game 4 Post-Mortem: Systematic Review

**Civ**: Byzantium (Basil II) | **Result**: Defeat T182 (Russia Religious Victory) | **Map**: Small, 4 players

---

## Part 1: Strategic Analysis from Timeline Data

### The Timeline Tells the Story

The exported game timeline (507 moments, 4 players) reveals a stark asymmetry between Russia and Byzantium that was invisible during gameplay.

#### Milestone Comparison

| Milestone | Byzantium | Russia | Mali | Indonesia |
|-----------|-----------|--------|------|-----------|
| Capital founded | T3 | T1 | T1 | T1 |
| Second city | T59 | T36 | T58 | T23 |
| First Pantheon | T52 | T33 | T16 | T13 |
| First Government | T81 | T62 | T68 | T66 |
| Religion Founded | never | **T70 (first!)** | T89 | T86 |
| First Wonder | never | **T76 (Pyramids)** | T95 | T176 |
| First Great Person | T115 | **T70 (John Baptist)** | T88 | T85 |
| First Strategic Unit | never | T91 | T95 | T145 |
| Met all civs | T125 | **T45 (first!)** | T125 | T92 |

**Byzantium was dead last in every single milestone.** Second city 23 turns behind Indonesia. Pantheon 39 turns behind. First government 19 turns behind Russia. No religion, no wonders, no strategic units ever.

#### Era Score Comparison

| Era | Byzantium | Russia | Mali | Indonesia |
|-----|-----------|--------|------|-----------|
| Ancient (T1-60) | **4** | **32** | 10 | 14 |
| Classical (T61-120) | 13 | **43** | 30 | 15 |
| Medieval (T121-171) | 10 | **42** | 4 | 13 |
| Renaissance (T172-182) | 1 | 17 | 4 | 9 |
| **TOTAL** | **28** | **134** | **48** | **51** |

Russia earned **4.8x** Byzantium's era score. This translated to:
- Russia: **Golden Age** (Classical) → **Golden Age** (Medieval) → Normal (Renaissance)
- Byzantium: **Dark Age** (Classical!) → Normal (Medieval) → Normal (Renaissance)

A Dark Age in Classical is catastrophic — reduced loyalty, fewer policies, weaker position exactly when snowballing should begin.

#### Russia's Victory Path: Religion

The religious victory was telegraphed from T70 onward:

| Turn | Event |
|------|-------|
| T33 | Russia founds pantheon |
| T60 | **Lavra built** (unique Holy Site replacement — extra Great Prophet points) |
| T70 | **Eastern Orthodoxy founded** (first in world, +3 era score) |
| T76 | **Pyramids built** (extra builder charge — economic acceleration) |
| T77 | **Stonehenge built** (free Great Prophet — already had religion, so extra religious unit) |
| T91 | Moscow founded near Mali (forward settling for religious pressure) |
| T101 | First Medieval tech in world (Apprenticeship) |
| T110 | **Largest civ by margin** — 5+ cities while others had 2-3 |
| T129 | **Inquisition launched** (first in world — religious defense) |
| T135 | **Max beliefs reached** (first in world — fully upgraded religion) |
| T145 | **Majapahit converted** (Indonesia's holy city falls to Orthodoxy!) |
| T156 | Smolensk founded near Mali (more forward settling) |
| T176 | Mali city converted during war |
| T179 | **Won Religious Emergency** as target (4 era score) |
| T182 | **Niani converted** (Mali's holy city) → Religious Victory |

Russia played a textbook religious game:
1. Lavra for GP points → early religion founding
2. Wonders for economic base (Pyramids, Stonehenge)
3. Forward cities for religious pressure (Moscow near Mali, Smolensk near Mali)
4. Inquisition for defense, then aggressive conversion
5. Converted both rival holy cities (Indonesia T145, Mali T182)

#### Battle Statistics

| Player | Total Battles | vs Barbarians | vs Players | vs City-States |
|--------|--------------|---------------|------------|----------------|
| Byzantium | 19 | 19 | **0** | **0** |
| Russia | 156 | 43 | **80 (vs Indo)** | **33** |
| Mali | 71 | 52 | 13 (vs Russia) | 6 |
| Indonesia | 97 | 65 | 32 (vs Russia) | 0 |

Russia fought **8x** as many battles as Byzantium. Russia was actively at war with Indonesia (70 battles!) and city-states (33 battles via levied militaries). Meanwhile Byzantium fought only barbarians — zero player-vs-player combat.

Russia's military aggression served the religious strategy: religious pressure from nearby cities + military conquest to flip cities.

#### Great People Race

| Player | Count | Notable Recruits |
|--------|-------|-------------------|
| Russia | **16** | John the Baptist, Zhang Heng, Aryabhata, Valmiki, Hannibal Barca, Homer, Hildegard, Sun Tzu, Galileo, Michelangelo, Rumi, Li Bai, James of St. George |
| Indonesia | 5 | Simon Peter, Hypatia, Emilie du Chatelet, Artemisia |
| Mali | 4 | Confucius, Zhang Qian, Marcus Crassus, Piero de' Bardi |
| Byzantium | **4** | Euclid (T115), Omar Khayyam (T143), Irene of Athens (T148), Newton (T174) |

Russia recruited **4x** as many Great People. They had the science (Aryabhata, Zhang Heng, Galileo), culture (Homer, Valmiki, Murasaki Shikibu, Li Bai, Rumi, Michelangelo), religion (John the Baptist, Hildegard), military (Hannibal, Sun Tzu), and engineering (James of St. George) covered. Byzantium got 4 scientists — a narrow specialization that never translated to victory.

### When Was the Game Lost?

**The game was effectively over by T70** when Russia founded the world's first religion with a Lavra already built. Key evidence:

1. **T60**: Russia builds Lavra — unique district generating extra Great Prophet points. With a Golden Age, Russia was snowballing hard.
2. **T61**: Byzantium enters a **Dark Age** while Russia enters a **Golden Age**. The gap was already 28 era score (32 vs 4).
3. **T70**: Eastern Orthodoxy founded. Russia now has a win condition active. Byzantium has no religion and never will.
4. **T91**: Russia forward-settles Moscow near Mali — aggressive religious expansion begins.
5. **T110**: Russia is the largest civ by a margin — more cities = more religious pressure = inevitable victory.

By T100, even if we'd detected the threat, countering a religious victory requires:
- A religion of our own (impossible — all GP slots likely filled by T89)
- Inquisitors to purge foreign religion (requires own religion)
- Or military conquest of Russia's holy city (but we had 0 military engagements with players)

**The only viable counterplay would have been:**
1. Detect Russia's religious trajectory by T70-80
2. Pivot to military — build an army, ally with Mali/Indonesia
3. Joint war declaration to capture St. Petersburg (Russia's holy city)
4. Without the holy city, Russia loses religious pressure and the snowball stops

This required: (a) visibility into Russia's religion founding, (b) understanding that religious victory was a threat, (c) diplomatic tools to form coalitions. The tools provided none of this.

---

## Part 2: Tool Gap Analysis

### What a Human Player Sees vs What the Agent Sees

The core principle of **player parity** is: the agent should have access to the same information and decisions a human player has from the standard game UI. Here are the critical gaps:

#### Gap 1: Religion Conversion Tracking (CRITICAL — Caused Defeat)

**Human sees**: Religion lens showing which religion is majority in each city, religious pressure arrows, conversion progress bars. World Rankings screen showing religion spread. "Foreign Religious Victory Imminent" notification appears ~5 turns before loss.

**Agent sees**: `get_victory_progress` shows `religion_cities` count per player and `religion_majority` per civ. But:
- No breakdown of **which** cities are converted
- No religious **pressure** data (incoming/outgoing)
- No tracking of **conversion velocity** (how fast is it spreading?)
- No alert when a single religion achieves majority in N-1 civilizations
- `get_victory_progress` was only called every 20-30 turns — T150 would have shown Russia at 20+ converted cities but we didn't check until T182

**Proposed fix**:
1. Add per-city religion majority to `get_cities` or a new `get_religion_status` tool
2. Add a **RELIGION VICTORY ALERT** to `end_turn` turn report when any player's religion is majority in 50%+ of civs
3. Track conversion delta between checks (e.g. "Russia: 20 → 26 converted cities in 30 turns")

#### Gap 2: No Automatic Victory Proximity Warning (CRITICAL)

**Human sees**: Victory advisor shows progress bars. When a civ is close to any victory, a prominent notification appears ("Foreign Culture Victory Imminent", etc.).

**Agent sees**: `get_victory_progress` only when manually called. The `end_turn` turn report includes notifications, but the "Foreign Victory Imminent" notification only fires 1-2 turns before loss — too late.

**Proposed fix**:
1. Run a lightweight victory proximity check inside `end_turn()` every turn (just check relCities count and majority religion of each civ — 3 lines of Lua)
2. When ANY foreign civ meets a threshold (e.g. religion majority in N-1 of N civs, or 15+ diplomatic VP, or 40+ science VP), emit a `!! VICTORY THREAT: Russia approaching Religious Victory (26/28 cities converted)` warning
3. This mirrors the human notification system but fires earlier (threshold-based, not game-notification-based)

#### Gap 3: Wonder/District Progress of Rivals (MEDIUM)

**Human sees**: When clicking on a rival city (if visible), the production queue shows what they're building, including wonders. The Technology & Civics advisor shows whether anyone else is researching the same tech.

**Agent sees**: Nothing. Russia built Pyramids, Stonehenge, Oracle, Great Library, Great Bath — 5 wonders — and the agent had no awareness of any of them during gameplay. Only the timeline reveals them post-game.

**Proposed fix**: Not easy to query via API (wonder construction is internal). However:
1. Add wonder existence check to `get_victory_progress`: scan `GameInfo.Buildings` for wonders and check which player owns them
2. This is read-only information visible on the world map — not cheating

#### Gap 4: City Count per Rival (EASY FIX — already partially there)

**Human sees**: World Rankings shows city count per civ. Score breakdown shows.

**Agent sees**: `get_victory_progress` now includes `num_cities` per player. But `get_diplomacy` doesn't show it, and the rivalry assessment in `narrate_victory_progress` doesn't flag city count disparity.

**Proposed fix**: Already implemented in PLAYER line. Just need to:
1. Add city count disparity warning in `narrate_victory_progress` when a rival has 2x+ our cities
2. Add city count to `narrate_diplomacy` output

#### Gap 5: No LOS Warning for Ranged Attacks (MEDIUM — Caused Multi-Turn Bug)

**Human sees**: When selecting a ranged unit, valid targets highlight in red. If LOS is blocked, the target simply doesn't highlight.

**Agent sees**: `get_units` shows "CAN ATTACK" for units with `CanStartOperation(RANGE_ATTACK)` returning true generically, but this doesn't check specific target LOS. The attack then silently fails because `GetOperationTargets(RANGE_ATTACK)` returns 0 targets from a forest tile.

**Proposed fix**:
1. In `build_attack_unit()`, before attempting the attack, check `GetOperationTargets(RANGE_ATTACK)` for the specific attacker and verify the target is in the list
2. If target is NOT in the operation targets list, return `ERR:NO_LOS — target at (X,Y) is not in valid targets. Unit may need to move to clear line of sight (forests block LOS).`
3. This exactly mirrors the human UI's target highlighting

#### Gap 6: Religious Emergency / Emergency System Visibility (MEDIUM)

**Human sees**: Emergency proposals appear as a notification. Can vote to join. Shows targets and rewards.

**Agent sees**: Nothing. Russia won a Religious Emergency as target at T179 (+4 era score) and the agent never knew an emergency was in progress.

**Proposed fix**: Add emergency detection to `get_notifications` or create a `get_emergencies` tool. The game has `Game.GetEmergencyManager()` API.

### Information the Agent Has But Doesn't Use Well

#### Military Strength Comparison (already in `get_victory_progress`)
The `PLAYER` line includes `milStr` but `narrate_diplomacy` doesn't cross-reference it. The plan from the previous session (Improvement 3) already covers this — needs implementation.

#### Threat Scan (already scans all players)
The `build_threat_scan_query()` already scans all players with fog-of-war filtering (not just barbarians). The previous plan's Improvement 2 was already implemented. What's missing is:
- Grouping by diplomatic relationship (at war / unfriendly / neutral) in narration
- Warning when foreign units are massing near border

#### Envoy Verification (already has async workaround)
The `send_envoy` already has a 0.1s sleep + verification. The previous plan's Improvement 5 was already partially implemented.

---

## Part 3: Tactical Review — Key Decision Points

### T1-30: Slow Start (Recoverable)

**What happened**: Constantinople founded T3. No scout built until later. No exploration.
**What should have happened**: Scout first, then settler. Explore aggressively.
**Impact**: Met Russia at T45 (vs Russia meeting Mali at T9). Missed goody huts (Russia got 8, Byzantium got 0).

### T30-60: No Second City Until T59 (Critical Mistake)

**What happened**: Byzantium built military units for defense, didn't prioritize settler.
**What should have happened**: Settler by T30-35 at latest. Russia had 2 cities by T36.
**Impact**: Halved growth rate. One city can't generate enough yields to compete.

### T52: Pantheon at T52 (Late but Acceptable)

**What happened**: Fourth to found a pantheon.
**Tool gap**: No tool showed that 3 other civs already had pantheons. Didn't know we were last.

### T61: Dark Age (Disaster)

**What happened**: Only 4 era score in Ancient era. Needed ~12+ for Normal age.
**Root cause**: No goody huts (0 vs Russia's 8), no barb camp kills, late meeting with civs, no natural wonders found early.
**Impact**: Dark Age means fewer policies, loyalty pressure, reduced effectiveness. Russia got Golden Age with 32 era score.

### T70-91: Religion Window Closes

**What happened**: Russia founded Eastern Orthodoxy at T70. Indonesia founded Hinduism T86. Mali founded Islam T89. All religion slots filled.
**Byzantium's play**: Should have prioritized Holy Site + Great Prophet if religious victory was possible. But Basil II's ability (Tagma units convert killed enemy cities) only works if you're at war — a military-religious hybrid that never materialized.
**Tool gap**: No tool flagged "2/2 religion slots filled — Great Prophet no longer available."

### T108: Largest City in World (Briefly Good)

**What happened**: Constantinople grew to be world's largest city.
**But**: Size without districts is just vanity. No campus until late, no districts producing yield multipliers.

### T115-174: Science Focus (Too Narrow, Too Late)

**What happened**: Recruited 4 Great Scientists (Euclid, Omar Khayyam, Irene of Athens, Newton). Science grew from ~20 to ~60/turn.
**Problem**: Science victory requires ~100+ sci/turn for 15+ turns of space projects. With 3 cities, the ceiling was too low. And Russia was already winning via religion.

### T145: Point of No Return

Russia converted Majapahit (Indonesia's holy city). This meant Indonesia had no religious defense. With only Mali's Islam remaining as competition, Russia's Orthodoxy could spread freely. Even a joint military response at this point would have been too slow — Russia had 11 cities and a fully upgraded religion.

### T176-182: The Invisible Defeat

The crossbow LOS bug consumed 3-4 turns of attention on a barbarian while Russia was converting the last cities. The agent had no visibility into the religious situation. The "Foreign Religious Victory Imminent" notification fired at T181 — one turn before defeat.

---

## Part 4: Tool Improvement Recommendations

### Priority 1: Victory Proximity Alert (in end_turn)

**Rationale**: A human player sees the Victory Advisor panel and gets notifications. The agent gets nothing until it's too late.

**Implementation**: In `end_turn()`, after the snapshot diff, add a lightweight Lua query:

```python
# Check all victory conditions quickly
for player in victory_data.players:
    if player.player_id == our_id:
        continue
    # Religious victory: majority in all civs
    if player.religion_cities >= total_cities * 0.7:
        events.append(f"!! VICTORY THREAT: {player.name} approaching Religious Victory ({player.religion_cities} cities converted)")
    # Diplomatic victory: 15+ VP
    if player.diplomatic_vp >= 15:
        events.append(f"!! VICTORY THREAT: {player.name} has {player.diplomatic_vp}/20 Diplomatic VP")
    # Science victory: 30+ VP
    if player.science_vp >= 30:
        events.append(f"!! VICTORY THREAT: {player.name} has {player.science_vp}/{player.science_vp_needed} Science VP")
```

**Cost**: One additional Lua query per turn (~50ms). Worth it.

### Priority 2: LOS Check Before Ranged Attack

**Rationale**: Wasted 3-4 turns discovering forest blocks LOS. A human would see no red highlight.

**Implementation**: In `build_attack_unit()`, before the attack:
```lua
-- Check if target is in valid operation targets
local targets = unit:GetOperationTargets(UnitOperationTypes.RANGE_ATTACK)
local found = false
if targets then
    for _, t in ipairs(targets) do
        if t.X == tx and t.Y == ty then found = true end
    end
end
if not found then
    print("ERR:NO_LOS|Target not in valid attack targets — LOS may be blocked by terrain")
    print(SENTINEL); return
end
```

### Priority 3: Religion Status Tool

**Rationale**: Religious victory was completely invisible. A human checks the Religion lens regularly.

**Implementation**: New `get_religion_status()` tool that returns:
- Per-civ: which religion is majority, how many cities follow each religion
- Global: total cities per religion, religions with 50%+ of world cities
- Religious units visible (missionaries, apostles, inquisitors)
- Holy city status per religion

### Priority 4: Automatic `get_victory_progress` Every 10 Turns

**Rationale**: The CLAUDE.md says "every 20-30 turns" but this game proved that's too infrequent. Russia went from "has a religion" to "won" in ~60 turns with no checkpoint.

**Implementation**: In `end_turn()`, every 10 turns, automatically run `get_victory_progress` and append a summary to the turn report. No new tool needed — just integrate the check.

### Priority 5: Rival City/Wonder Summary in `get_diplomacy`

**Rationale**: City count and wonder ownership are visible to human players via World Rankings.

**Implementation**: Add to the diplomacy Lua query:
```lua
-- Count cities
local nCities = 0
for _ in Players[i]:GetCities():Members() do nCities = nCities + 1 end
print("CIV_DETAIL|" .. i .. "|cities:" .. nCities)
```

And in narration, flag when a rival has significantly more cities.

### Priority 6: Era Score Tracking

**Rationale**: Byzantium's Dark Age in Classical was devastating. A human checks the era score panel each turn.

**Implementation**: Add to `get_game_overview`:
```lua
local eras = Game.GetEras()
local eraScore = eras:GetPlayerCurrentScore(me)
local darkThreshold = eras:GetPlayerDarkAgeThreshold(me)
local goldenThreshold = eras:GetPlayerGoldenAgeThreshold(me)
print("ERA_SCORE|" .. eraScore .. "|" .. darkThreshold .. "|" .. goldenThreshold)
```

This gives the agent turn-by-turn visibility into era score progress.

---

## Part 5: Strategic Lessons for Future Games

### Lesson 1: Expansion Speed is Everything

Russia had 2 cities by T36, 5 by T110, 11 by T182. Byzantium had 2 by T59, 3 by T102. More cities = more yields = more districts = more Great People = more era score = victory. The #1 priority in any game should be reaching 4 cities by T75.

### Lesson 2: Detect Victory Conditions Early

Russia's religious trajectory was clear from T70 (Orthodoxy founded) → T91 (forward settle) → T129 (Inquisition) → T145 (converted holy city). Each milestone should have triggered an escalating alert. By T145, military intervention was the only option, and even that was probably too late.

### Lesson 3: Byzantium's Abilities Were Wasted

Basil II's unique ability converts cities of killed enemy units to his religion. His unique unit (Tagma) gets bonus combat strength near a converted city. These abilities require **being at war** and **having a religion**. We had neither. We played a passive science game with a military-religious civ.

### Lesson 4: Dark Ages Must Be Avoided

4 era score in Ancient meant a Dark Age. The fix:
- Explore for goody huts (Russia found 8, we found 0)
- Find natural wonders (Russia found 2, we found 0 in Ancient)
- Meet other civs (Russia met 3 by T45, we met 0 by T45)
- Clear barbarian camps (Russia cleared 2, we cleared 0)

A scout on T5 would have earned 5-10 era score just from goody huts and meeting civs.

### Lesson 5: Don't Specialize Too Narrowly

4 Great Scientists with 3 cities can't win a science victory. The math doesn't work:
- Science victory needs ~100 sci/turn sustained
- 3 cities × Campus/University/Library ≈ 60 sci/turn max
- Need 5-6 cities with full campus districts

### Lesson 6: Monitor Rivals Actively

Call `get_victory_progress` every 10 turns, not 25-30. Check `get_diplomacy` for military buildup. Use `get_minimap` to spot expansion patterns.

---

## Part 6: Summary of Recommended Changes

| # | Change | Priority | Type | Files |
|---|--------|----------|------|-------|
| 1 | Victory proximity alert in `end_turn()` | P0 | New logic | `game_state.py` |
| 2 | LOS check before ranged attack | P1 | Bug fix | `lua_queries.py` |
| 3 | `get_religion_status` tool | P1 | New tool | `lua_queries.py`, `game_state.py`, `server.py` |
| 4 | Auto victory check every 10 turns in `end_turn` | P1 | Enhancement | `game_state.py` |
| 5 | City count + wonder count in `get_diplomacy` | P2 | Enhancement | `lua_queries.py`, `game_state.py` |
| 6 | Era score in `get_game_overview` | P2 | Enhancement | `lua_queries.py`, `game_state.py` |
| 7 | Rival military strength in `narrate_diplomacy` | P2 | Enhancement | `game_state.py` |
| 8 | "Religion slots filled" alert in `end_turn` notifications | P2 | Enhancement | `game_state.py` |
| 9 | Emergency system visibility | P3 | New tool | `lua_queries.py`, `server.py` |
| 10 | Wonder ownership tracking | P3 | Enhancement | `lua_queries.py` |

### Already Implemented (from previous plan)
- Threat scan scans all players (not just barbarians) ✅
- Pre-combat popup dismiss ✅ (partial)
- Military strength in diplomacy narration ✅ (in victory progress, not diplomacy)
- Post-combat HP verification warning ✅

### Not Yet Implemented (from previous plan)
- Threat grouping by diplomatic relationship in narration
- `send_envoy` stale readback fix (partially done)
