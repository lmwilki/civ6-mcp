"""Server-side narration — human-readable text formatting for LLM consumption.

All functions are pure: data in, string out. No side effects, no I/O.
"""

from __future__ import annotations

from civ_mcp import lua as lq


def narrate_overview(ov: lq.GameOverview) -> str:
    lines = [
        f"Turn {ov.turn} | {ov.civ_name} ({ov.leader_name}) | Score: {ov.score}",
        f"Gold: {ov.gold:.0f} ({ov.gold_per_turn:+.0f}/turn) | Science: {ov.science_yield:.1f} | Culture: {ov.culture_yield:.1f} | Faith: {ov.faith:.0f} | Favor: {ov.diplomatic_favor} ({ov.favor_per_turn:+d}/turn)",
        f"Research: {ov.current_research} | Civic: {ov.current_civic}",
        f"Cities: {ov.num_cities} | Population: {ov.total_population} | Units: {ov.num_units}",
    ]
    if ov.total_land > 0:
        pct = ov.explored_land * 100 // ov.total_land
        lines.append(
            f"Explored: {pct}% of land ({ov.explored_land}/{ov.total_land} tiles)"
        )
    if ov.religions_max > 0:
        if ov.our_religion:
            lines.append(
                f"Religion: {ov.our_religion} ({ov.religions_founded}/{ov.religions_max} slots)"
            )
        elif ov.religions_founded >= ov.religions_max:
            others = ", ".join(
                f"{r.civ_name}: {r.religion_name}" for r in (ov.founded_religions or [])
            )
            lines.append(
                f"Religion: NONE — all {ov.religions_max} slots filled ({others})"
            )
        else:
            remaining = ov.religions_max - ov.religions_founded
            lines.append(
                f"Religion: none yet ({remaining}/{ov.religions_max} slots remaining — Great Prophet needed)"
            )
    if ov.era_name:
        score_status = ""
        if ov.era_score >= ov.era_golden_threshold:
            score_status = " -> GOLDEN AGE"
        elif ov.era_score < ov.era_dark_threshold:
            deficit = ov.era_dark_threshold - ov.era_score
            score_status = f" !! {deficit} short of avoiding Dark Age"
        lines.append(
            f"Era: {ov.era_name} | Score: {ov.era_score} (Dark: {ov.era_dark_threshold}, Golden: {ov.era_golden_threshold}){score_status}"
        )
    if ov.rankings:
        all_scores = [(ov.civ_name, ov.score)] + [
            (r.civ_name, r.score) for r in ov.rankings
        ]
        all_scores.sort(key=lambda x: x[1], reverse=True)
        rank_strs = [f"{name} {score}" for name, score in all_scores]
        lines.append(f"Rankings: {' > '.join(rank_strs)}")
    return "\n".join(lines)


_RANK_NAMES = {1: "Recruit", 2: "Agent", 3: "Special Agent", 4: "Senior Agent"}


def narrate_spies(spies: list[lq.SpyInfo]) -> str:
    if not spies:
        return "No spies available yet."
    lines = [f"Spies ({len(spies)}):"]
    for s in spies:
        rank_name = _RANK_NAMES.get(s.rank, f"Rank {s.rank}")
        loc = f"({s.x},{s.y})"
        if s.city_name != "none":
            owner_tag = " [own]" if s.city_owner == 0 else ""
            loc = f"{s.city_name}{owner_tag} ({s.x},{s.y})"
        ops = ", ".join(s.available_ops) if s.available_ops else "none"
        mission_tag = f" | mission: {s.current_mission}" if s.current_mission != "none" else ""
        lines.append(
            f"  id:{s.unit_id} [{rank_name}] {s.name} — at {loc} | moves:{s.moves}"
            f" | xp:{s.xp}{mission_tag} | ops: {ops}"
        )
    lines.append("")
    lines.append("Actions:")
    lines.append(
        "  Travel: spy_action(unit_id, action='travel', target_x, target_y)"
        " — send spy to own city or city-state"
    )
    lines.append(
        "  Mission: spy_action(unit_id, action=MISSION_TYPE, target_x, target_y)"
        " — spy must already be in target city"
    )
    lines.append(
        "  Mission types: COUNTERSPY, GAIN_SOURCES, SIPHON_FUNDS, STEAL_TECH_BOOST,"
        " SABOTAGE_PRODUCTION, GREAT_WORK_HEIST, RECRUIT_PARTISANS,"
        " NEUTRALIZE_GOVERNOR, FABRICATE_SCANDAL"
    )
    return "\n".join(lines)


def narrate_units(
    units: list[lq.UnitInfo],
    threats: list[lq.ThreatInfo] | None = None,
    trade_status: lq.TradeRouteStatus | None = None,
) -> str:
    if not units:
        return "No units."
    # Build trader route lookup: unit_id -> TraderInfo
    trader_routes: dict[int, lq.TraderInfo] = {}
    if trade_status:
        for t in trade_status.traders:
            if t.on_route:
                trader_routes[t.unit_id] = t
    lines = [f"{len(units)} units:"]
    for u in units:
        strength = ""
        if u.combat_strength > 0:
            strength = f" CS:{u.combat_strength}"
            if u.ranged_strength > 0:
                strength += f" RS:{u.ranged_strength}"
        status = ""
        if u.health < u.max_health:
            status = f" [HP: {u.health}/{u.max_health}]"
        if u.moves_remaining < 0.01:
            status += " (no moves)"
        # Annotate traders on active routes
        route_flag = ""
        if u.unit_id in trader_routes:
            tr = trader_routes[u.unit_id]
            route_type = "Domestic" if tr.is_domestic else "International"
            route_flag = (
                f" [ON ROUTE: {tr.route_origin} -> {tr.route_dest} ({route_type})]"
            )
        charges = f" charges:{u.build_charges}" if u.build_charges > 0 else ""
        religion_flag = ""
        if u.religion:
            short = u.religion.replace("RELIGION_", "")
            religion_flag = f" [{short}]"
        promo_flag = " **NEEDS PROMOTION**" if u.needs_promotion else ""
        upgrade_flag = ""
        if u.can_upgrade:
            upgrade_flag = f" **CAN UPGRADE to {u.upgrade_target} ({u.upgrade_cost}g)**"
        moves_disp = (
            f"{int(u.moves_remaining)}/{int(u.max_moves)}"
            if u.moves_remaining == int(u.moves_remaining)
            else f"{u.moves_remaining:.1f}/{int(u.max_moves)}"
        )
        lines.append(
            f"  {u.name} ({u.unit_type}) at ({u.x},{u.y}) —{strength} "
            f"moves {moves_disp}{charges}{religion_flag}{status}{route_flag}{promo_flag}{upgrade_flag} "
            f"[id:{u.unit_id}, idx:{u.unit_index}]"
        )
        if u.targets:
            for t in u.targets:
                lines.append(f"    >> CAN ATTACK: {t}")
        if u.valid_improvements:
            lines.append(f"    >> Can build: {', '.join(u.valid_improvements)}")
    if threats:
        lines.append("")
        lines.append(f"Nearby threats ({len(threats)}):")
        # Group threats by owner
        from collections import defaultdict

        by_owner: dict[int, list[lq.ThreatInfo]] = defaultdict(list)
        for t in threats:
            by_owner[t.owner_id].append(t)
        # Sort: at-war/barbarian owners first, then by unit count
        for owner_id in sorted(
            by_owner.keys(),
            key=lambda oid: (0 if oid == 63 else 1, -len(by_owner[oid])),
        ):
            owner_threats = by_owner[owner_id]
            owner_name = owner_threats[0].owner_name
            if owner_id == 63:
                label = f"Barbarian ({len(owner_threats)} unit{'s' if len(owner_threats) != 1 else ''}):"
            else:
                cs_tag = " (city-state)" if owner_threats[0].is_city_state else ""
                label = f"{owner_name}{cs_tag} ({len(owner_threats)} unit{'s' if len(owner_threats) != 1 else ''}):"
            lines.append(f"  {label}")
            for t in sorted(owner_threats, key=lambda t: t.distance):
                rs_str = f" RS:{t.ranged_strength}" if t.ranged_strength > 0 else ""
                lines.append(
                    f"    {t.unit_type} at ({t.x},{t.y}) — CS:{t.combat_strength}{rs_str} "
                    f"HP:{t.hp}/{t.max_hp} ({t.distance} tiles away)"
                )
    return "\n".join(lines)


def narrate_cities(
    cities: list[lq.CityInfo], distances: list[str] | None = None
) -> str:
    if not cities:
        return "No cities."
    lines = [f"{len(cities)} cities:"]
    for c in cities:
        building = (
            c.currently_building
            if c.currently_building not in ("NONE", "nothing")
            else "nothing"
        )
        prod_str = f"Building: {building}"
        if building != "nothing" and c.production_turns_left > 0:
            prod_str += f" ({c.production_turns_left} turns)"
        defense = ""
        if c.wall_max_hp > 0:
            defense = (
                f" | Walls {c.wall_hp}/{c.wall_max_hp}"
                f" Garrison {c.garrison_hp}/{c.garrison_max_hp}"
                f" Def:{c.defense_strength}"
            )
        elif c.garrison_max_hp > 0:
            defense = (
                f" | HP:{c.garrison_hp}/{c.garrison_max_hp} Def:{c.defense_strength}"
            )
        elif c.defense_strength > 0:
            defense = f" | Def:{c.defense_strength}"
        garrison_str = (
            c.garrison_unit.replace("UNIT_", "") if c.garrison_unit else "none"
        )
        if defense:
            defense += f" Gar:{garrison_str}"
        else:
            defense = f" | Gar:{garrison_str}"
        loyalty_str = ""
        if c.loyalty_per_turn < 0 or c.loyalty < 75:
            flip_info = (
                f", flips in {c.turns_to_loyalty_flip} turns"
                if c.turns_to_loyalty_flip > 0
                else ""
            )
            loyalty_str = f" | !! Loyalty: {c.loyalty:.0f}/{c.loyalty_max:.0f} ({c.loyalty_per_turn:+.1f}/turn{flip_info})"
        # Growth display: show surplus and progress, not just turns
        if c.turns_to_grow <= 0 or c.food_surplus <= 0:
            growth_str = f"STAGNANT ({c.food_surplus:+.1f} food/t)"
        elif c.turns_to_grow <= 5:
            growth_str = f"{c.food_stored:.0f}/{c.growth_threshold} food ({c.turns_to_grow}t, {c.food_surplus:+.1f}/t)"
        else:
            growth_str = f"{c.food_stored:.0f}/{c.growth_threshold} food ({c.turns_to_grow}t, {c.food_surplus:+.1f}/t)"
        lines.append(
            f"  {c.name} (pop {c.population}) at ({c.x},{c.y}) — "
            f"Food {c.food:.0f} Prod {c.production:.0f} Gold {c.gold:.0f} "
            f"Sci {c.science:.0f} Cul {c.culture:.0f} | "
            f"Housing {c.housing:.0f} Amenities {c.amenities} | "
            f"Growth: {growth_str} | {prod_str}{defense}{loyalty_str} "
            f"[id:{c.city_id}]"
        )
        # Growth warnings
        if c.food_surplus < 0:
            lines.append(
                f"    !! STARVING: {c.food_surplus:+.1f} food/t — city will lose population!"
            )
        elif c.food_surplus == 0 and c.turns_to_grow <= 0:
            lines.append(
                f"    !! STAGNANT: 0 food surplus — needs farm, granary, or trade route"
            )
        elif c.turns_to_grow > 15:
            lines.append(
                f"    !! SLOW GROWTH: {c.turns_to_grow} turns to next pop — needs farm, granary, or trade route"
            )
        if c.currently_building == "CORRUPTED_QUEUE":
            lines.append(
                f"    !! CORRUPTED QUEUE: ghost entry (hash=0). Load earlier autosave to fix."
            )
        for t in c.attack_targets:
            lines.append(f"    >> CAN ATTACK: {t}")
        if c.districts:
            dist_strs = []
            for d in c.districts:
                dtype, coords = d.split("@")
                short = dtype.replace("DISTRICT_", "")
                dist_strs.append(f"{short}({coords})")
            lines.append(f"    Districts: {' '.join(dist_strs)}")
        if c.pillaged_districts or c.pillaged_buildings:
            pill_names = [d.replace("DISTRICT_", "") for d in c.pillaged_districts]
            pill_bldgs = [b.replace("BUILDING_", "") for b in c.pillaged_buildings]
            all_pillaged = pill_names + pill_bldgs
            lines.append(f"    !! PILLAGED: {', '.join(all_pillaged)}")
    if distances:
        lines.append("")
        lines.append("City Distances:")
        for d in distances:
            lines.append(f"  {d}")
    return "\n".join(lines)


def narrate_combat_estimate(est: lq.CombatEstimate) -> str:
    atk_type = "Ranged" if est.is_ranged else "Melee"
    mods_str = ", ".join(est.modifiers) if est.modifiers else "none"
    lines = [
        f"Combat Estimate ({atk_type}):",
        f"  {est.attacker_type} (CS:{est.attacker_cs}, HP:{est.attacker_hp}) vs "
        f"{est.defender_type} (CS:{est.defender_cs}, HP:{est.defender_hp})",
        f"  Modifiers: {mods_str}",
        f"  Est damage to defender: ~{est.est_damage_to_defender}",
    ]
    if not est.is_ranged:
        lines.append(f"  Est damage to attacker: ~{est.est_damage_to_attacker}")
    if est.est_damage_to_defender >= est.defender_hp:
        lines.append("  -> LIKELY KILL")
    elif not est.is_ranged and est.est_damage_to_attacker >= est.attacker_hp:
        lines.append("  -> WARNING: attacker likely dies!")
    return "\n".join(lines)


def narrate_city_production(options: list[lq.ProductionOption]) -> str:
    if not options:
        return "No production options available."
    units = [o for o in options if o.category == "UNIT"]
    buildings = [o for o in options if o.category == "BUILDING"]
    districts = [o for o in options if o.category == "DISTRICT"]
    projects = [o for o in options if o.category == "PROJECT"]

    def _fmt(o: lq.ProductionOption) -> str:
        t = f", {o.turns} turns" if o.turns > 0 else ""
        buy = f", buy: {o.gold_cost}g" if o.gold_cost > 0 else ""
        return f"  {o.item_name} (cost {o.cost}{t}{buy})"

    lines = []
    if units:
        lines.append("Units:")
        for o in units:
            lines.append(_fmt(o))
    if buildings:
        lines.append("Buildings:")
        for o in buildings:
            lines.append(_fmt(o))
    if districts:
        lines.append("Districts:")
        for o in districts:
            lines.append(_fmt(o))
    if projects:
        lines.append("Projects:")
        for o in projects:
            lines.append(_fmt(o))
    return "\n".join(lines)


def narrate_map(tiles: list[lq.TileInfo]) -> str:
    if not tiles:
        return "No tiles."
    lines = [f"{len(tiles)} tiles:"]
    for t in tiles:
        parts = [t.terrain.replace("TERRAIN_", "")]
        if t.is_hills:
            parts.append("Hills")
        if t.feature:
            parts.append(t.feature.replace("FEATURE_", ""))
        if t.resource:
            res_label = t.resource.replace("RESOURCE_", "")
            if t.resource_class == "strategic":
                res_label += "*"
            elif t.resource_class == "luxury":
                res_label += "+"
            parts.append(f"[{res_label}]")
        if t.is_river:
            parts.append("River")
        if t.is_coastal:
            parts.append("Coast")
        if t.is_fresh_water and not t.is_river:
            # Fresh water from lake/oasis (river already implies fresh water)
            parts.append("FreshWater")
        if t.improvement:
            imp_label = t.improvement.replace("IMPROVEMENT_", "")
            if t.is_pillaged:
                imp_label += " PILLAGED"
            parts.append(f"({imp_label})")
        if t.district:
            parts.append(f"[{t.district.replace('DISTRICT_', '')}]")
        if t.yields:
            f, p, g = t.yields[0], t.yields[1], t.yields[2]
            yield_str = f"F:{f} P:{p}"
            if g > 0:
                yield_str += f" G:{g}"
            # Include science/culture/faith only if non-zero
            for label, val in [
                ("S", t.yields[3]),
                ("C", t.yields[4]),
                ("Fa", t.yields[5]),
            ]:
                if val > 0:
                    yield_str += f" {label}:{val}"
            parts.append(f"{{{yield_str}}}")
        owner = f" (owned by player {t.owner_id})" if t.owner_id >= 0 else ""
        vis_tag = ""
        if t.visibility == "revealed":
            vis_tag = " [fog]"
        unit_str = ""
        if t.units:
            unit_str = f" **[{', '.join(t.units)}]**"
        lines.append(f"  ({t.x},{t.y}): {' '.join(parts)}{owner}{vis_tag}{unit_str}")
    return "\n".join(lines)


def narrate_strategic_map(data: lq.StrategicMapData) -> str:
    dir_names = ["N", "NE", "SE", "S", "SW", "NW"]
    lines = ["=== STRATEGIC MAP ===", ""]

    # Fog boundaries
    lines.append("FOG BOUNDARIES (distance to unexplored, -1 = fully explored):")
    for fb in data.fog_boundaries:
        dir_strs = []
        explore_dirs = []
        for i, d in enumerate(fb.fog_distances):
            label = dir_names[i] if i < len(dir_names) else f"D{i}"
            if d == -1:
                dir_strs.append(f"{label}:clear")
            else:
                dir_strs.append(f"{label}:{d}")
                if d <= 5:
                    explore_dirs.append(label)
        suffix = ""
        if explore_dirs:
            suffix = f" <- EXPLORE {'/'.join(explore_dirs)}!"
        lines.append(
            f"  {fb.city_name} ({fb.city_x},{fb.city_y}): {' '.join(dir_strs)}{suffix}"
        )

    # Unclaimed resources
    luxuries = [r for r in data.unclaimed_resources if "LUXURY" in r.resource_class]
    strategics = [
        r for r in data.unclaimed_resources if "STRATEGIC" in r.resource_class
    ]
    if luxuries or strategics:
        lines.append("")
        lines.append("UNCLAIMED RESOURCES (revealed, unowned):")
        for r in luxuries:
            name = r.resource_type.replace("RESOURCE_", "")
            lines.append(f"  {name}+ at ({r.x},{r.y}) — luxury")
        for r in strategics:
            name = r.resource_type.replace("RESOURCE_", "")
            lines.append(f"  {name}* at ({r.x},{r.y}) — strategic")
    elif not data.fog_boundaries:
        lines.append("\nNo data available.")

    return "\n".join(lines)


def narrate_minimap(data: lq.MinimapData) -> str:
    if not data.rows:
        return "No minimap data available."
    lines = [
        "=== MINIMAP ===",
        "Legend: O=our city, X=enemy city, !=barbarian",
        "  UPPER=our territory, lower=enemy territory",
        "  ~=water, ^=mountain, #=hills, T=forest/jungle, .=flat",
        "  +=luxury resource, *=strategic resource, ' '=unexplored",
        "",
    ]
    # Render rows with hex offset (even rows shift right)
    for y in sorted(data.rows.keys()):
        row_str = data.rows[y]
        # Hex grid: offset even rows by half-cell
        prefix = " " if y % 2 == 1 else ""
        # Add spacing between characters for readability
        spaced = " ".join(row_str)
        lines.append(f"{y:3d}|{prefix}{spaced}")
    return "\n".join(lines)


def narrate_settle_candidates(candidates: list[lq.SettleCandidate]) -> str:
    if not candidates:
        return "No valid settle locations found within 5 tiles."
    lines = [f"Top {len(candidates)} settle locations:"]
    _WATER = {"fresh": "fresh water", "coast": "coast", "none": "no water"}
    for i, c in enumerate(candidates, 1):
        water = _WATER.get(c.water_type, c.water_type)
        loy_warn = ""
        if c.loyalty_pressure < -1:
            loy_warn = (
                f" | !! Loyalty: ~{c.loyalty_pressure:+.0f}/turn (enemy pressure)"
            )
        header = f"  #{i} ({c.x},{c.y}): Score {c.score:.0f} — F:{c.total_food} P:{c.total_prod} — {water}, defense:{c.defense_score}{loy_warn}"
        lines.append(header)
        if c.resources:
            # Format: [S] IRON, [L] DIAMONDS, [B] WHEAT
            res_parts = []
            for r in c.resources:
                if ":" in r:
                    prefix, name = r.split(":", 1)
                    res_parts.append(f"[{prefix}] {name}")
                else:
                    res_parts.append(r)
            lines.append(f"     {', '.join(res_parts)}")
    return "\n".join(lines)


def narrate_empire_resources(
    stockpiles: list[lq.ResourceStockpile],
    owned: list[lq.OwnedResource],
    nearby: list[lq.NearbyResource],
    luxuries: dict[str, int],
) -> str:
    if not stockpiles and not owned and not nearby and not luxuries:
        return "No resources found in or near your empire."
    _CLASS_PREFIX = {"strategic": "S", "luxury": "L", "bonus": "B"}
    lines = ["Empire Resources:"]
    # Strategic stockpiles
    visible_strats = [s for s in stockpiles]
    if visible_strats:
        lines.append("\nStrategic Stockpiles:")
        for s in visible_strats:
            net = s.per_turn - s.demand
            net_str = f"+{net}" if net >= 0 else str(net)
            parts = [f"  {s.name}: {s.amount}/{s.cap} ({net_str}/turn)"]
            details = []
            if s.per_turn > 0:
                details.append(f"income {s.per_turn}")
            if s.imported > 0:
                details.append(f"import {s.imported}")
            if s.demand > 0:
                details.append(f"demand {s.demand}")
            if details:
                parts.append(f" [{', '.join(details)}]")
            lines.append("".join(parts))
    # Luxury summary
    if luxuries:
        lines.append("\nLuxury Resources:")
        for name, count in sorted(luxuries.items()):
            extra = f" ({count - 1} tradeable)" if count > 1 else ""
            lines.append(f"  {name}: {count}{extra}")
    # Owned tile resources grouped by class
    for cls, label in [
        ("strategic", "Strategic Tiles"),
        ("luxury", "Luxury Tiles"),
        ("bonus", "Bonus Tiles"),
    ]:
        items = [r for r in owned if r.resource_class == cls]
        if not items:
            continue
        lines.append(f"\n{label}:")
        for r in items:
            if r.improved:
                lines.append(f"  {r.name} — improved at ({r.x},{r.y})")
            elif cls in ("luxury", "strategic"):
                lines.append(
                    f"  !! {r.name} — UNIMPROVED at ({r.x},{r.y}) — needs builder!"
                )
            else:
                lines.append(f"  {r.name} — UNIMPROVED at ({r.x},{r.y})")
    # Nearby unclaimed
    if nearby:
        lines.append("\nNearby Unclaimed:")
        for r in nearby:
            prefix = _CLASS_PREFIX.get(r.resource_class, "?")
            lines.append(
                f"  [{prefix}] {r.name} at ({r.x},{r.y}) — {r.distance} tiles from {r.nearest_city}"
            )
    return "\n".join(lines)


def narrate_diplomacy(civs: list[lq.CivInfo]) -> str:
    if not civs:
        return "No known civilizations."
    lines = [f"{len(civs)} civilizations:"]
    for c in civs:
        if not c.has_met:
            lines.append(f"  {c.civ_name} ({c.leader_name}) — not met")
            continue
        # Header with state and score
        war_str = " **AT WAR**" if c.is_at_war else ""
        if c.alliance_type:
            level_str = f" Lv{c.alliance_level}" if c.alliance_level > 0 else ""
            alliance_str = f" ({c.alliance_type} alliance{level_str})"
        else:
            alliance_str = ""
        lines.append(
            f"  {c.civ_name} ({c.leader_name}) — {c.diplomatic_state} ({c.relationship_score:+d}){war_str}{alliance_str} [player {c.player_id}]"
        )
        # City details
        if c.num_cities > 0:
            if c.visible_cities:
                city_parts = []
                for vc in c.visible_cities:
                    loy_warn = ""
                    if vc.loyalty_per_turn < -0.5 or vc.loyalty < 50:
                        loy_warn = (
                            f" !! loy {vc.loyalty:.0f} ({vc.loyalty_per_turn:+.1f}/t)"
                        )
                    walls_str = " [walls]" if vc.has_walls else ""
                    city_parts.append(
                        f"{vc.name} pop {vc.population} ({vc.x},{vc.y}){walls_str}{loy_warn}"
                    )
                hidden = c.num_cities - len(c.visible_cities)
                fog_str = f" + {hidden} in fog" if hidden > 0 else ""
                lines.append(
                    f"    Cities ({c.num_cities}): {'; '.join(city_parts)}{fog_str}"
                )
            else:
                lines.append(f"    Cities: {c.num_cities} (all in fog)")
        # Military strength comparison
        if c.military_strength > 0:
            # Find our military strength from the MILITARY line (stored per-civ parse)
            our_mil = getattr(c, "_our_military", 0)
            if our_mil > 0:
                ratio = c.military_strength / our_mil
                ratio_str = f" ({ratio:.1f}x)" if ratio >= 1.2 or ratio <= 0.8 else ""
                threat_flag = ""
                if ratio >= 1.5 and c.diplomatic_state in (
                    "UNFRIENDLY",
                    "DENOUNCED",
                    "WAR",
                ):
                    threat_flag = " !! MILITARY THREAT"
                elif ratio >= 2.0:
                    threat_flag = " !! MUCH STRONGER"
                lines.append(
                    f"    Military: {c.military_strength} vs our {our_mil}{ratio_str}{threat_flag}"
                )
            else:
                lines.append(f"    Military: {c.military_strength}")
        # Access: delegations/embassies
        access = []
        if c.has_delegation:
            access.append("we have delegation")
        if c.they_have_delegation:
            access.append("they have delegation")
        if c.has_embassy:
            access.append("we have embassy")
        if c.they_have_embassy:
            access.append("they have embassy")
        if c.grievances > 0:
            access.append(f"grievances: {c.grievances}")
        if access:
            lines.append(f"    Access: {', '.join(access)}")
        # Relationship modifiers
        if c.modifiers:
            for m in c.modifiers:
                lines.append(f"    {m.score:+d} {m.text}")
        # Defensive pacts
        if c.defensive_pacts:
            pact_names = []
            for pid in c.defensive_pacts:
                # Find the civ name for this player ID
                pact_civ = next((ci for ci in civs if ci.player_id == pid), None)
                if pact_civ:
                    pact_names.append(f"{pact_civ.civ_name} (player {pid})")
                else:
                    pact_names.append(f"player {pid}")
            lines.append(f"    !! DEFENSIVE PACTS with: {', '.join(pact_names)}")
        # Available actions
        if c.available_actions:
            actions_str = ", ".join(
                a.replace("_", " ").title() for a in c.available_actions
            )
            lines.append(f"    Can: {actions_str}")
    return "\n".join(lines)


def narrate_diplomacy_sessions(sessions: list[lq.DiplomacySession]) -> str:
    if not sessions:
        return "No pending diplomacy sessions."
    lines = [f"{len(sessions)} pending diplomacy session(s):"]
    for s in sessions:
        lines.append(
            f"  {s.other_civ_name} ({s.other_leader_name}) — "
            f"session {s.session_id}, player {s.other_player_id}"
        )
        if s.dialogue_text:
            lines.append(f'  Says: "{s.dialogue_text}"')
        if s.reason_text:
            lines.append(f"  Reason: {s.reason_text}")
        if s.buttons:
            lines.append(f"  Buttons: {s.buttons}")
        # Phase-appropriate guidance
        if s.deal_summary:
            lines.append(f"  Deal: {s.deal_summary}")
            lines.append(
                f"  This is a DEAL proposal — use respond_to_trade(other_player_id={s.other_player_id}, accept=True/False)"
            )
        elif s.buttons == "GOODBYE":
            lines.append(
                "  Phase: GOODBYE — respond with POSITIVE or NEGATIVE (auto-closes)"
            )
        else:
            lines.append("  Respond with: POSITIVE (friendly) or NEGATIVE (dismissive)")
    return "\n".join(lines)


def narrate_tech_civics(tc: lq.TechCivicStatus) -> str:
    lines = []
    completed = ""
    if tc.completed_tech_count > 0 or tc.completed_civic_count > 0:
        completed = f" | Completed: {tc.completed_tech_count} techs, {tc.completed_civic_count} civics"
    if tc.current_research != "None":
        lines.append(
            f"Researching: {tc.current_research} ({tc.current_research_turns} turns){completed}"
        )
    else:
        lines.append(f"No technology being researched!{completed}")
    if tc.current_civic != "None":
        lines.append(f"Civic: {tc.current_civic} ({tc.current_civic_turns} turns)")
    else:
        lines.append("No civic being progressed!")
    if tc.available_techs:
        lines.append("\nAvailable techs:")
        for t in tc.available_techs:
            boost_str = " BOOSTED" if t.boosted else ""
            boost_desc = f" [Boost: {t.boost_desc}]" if t.boost_desc else ""
            unlocks = f" -> {t.unlocks}" if t.unlocks else ""
            lines.append(
                f"  {t.name} ({t.tech_type}) — {t.progress_pct}%, {t.turns} turns{boost_str}{boost_desc}{unlocks}"
            )
    if tc.available_civics:
        lines.append("\nAvailable civics:")
        for c in tc.available_civics:
            boost_str = " BOOSTED" if c.boosted else ""
            boost_desc = f" [Boost: {c.boost_desc}]" if c.boost_desc else ""
            lines.append(
                f"  {c.name} ({c.civic_type}) — {c.progress_pct}%, {c.turns} turns{boost_str}{boost_desc}"
            )
    if tc.locked_civics:
        lines.append("\nLocked civics (prerequisites missing):")
        for lc in tc.locked_civics:
            lines.append(
                f"  {lc.name} ({lc.civic_type}) — needs: {', '.join(lc.missing_prereqs)}"
            )
    return "\n".join(lines)


def narrate_pending_deals(deals: list[lq.PendingDeal]) -> str:
    if not deals:
        return "No pending trade deals."
    lines = [f"{len(deals)} pending trade deal(s):"]
    for d in deals:
        lines.append(
            f"\n  From: {d.other_player_name} ({d.other_leader_name}) [player {d.other_player_id}]"
        )

        # Detect mutual items (same name on both sides — alliances, open borders, joint wars)
        their_names = {i.name for i in d.items_from_them}
        our_names = {i.name for i in d.items_from_us}
        mutual_names = their_names & our_names

        mutual = [i for i in d.items_from_them if i.name in mutual_names]
        their_only = [i for i in d.items_from_them if i.name not in mutual_names]
        our_only = [i for i in d.items_from_us if i.name not in mutual_names]

        if mutual:
            lines.append("  Mutual:")
            for item in mutual:
                dur = f" for {item.duration} turns" if item.duration > 0 else ""
                lines.append(f"    = {item.name}{dur}")
        if their_only:
            lines.append("  They offer:")
            for item in their_only:
                dur = f" for {item.duration} turns" if item.duration > 0 else ""
                amt = (
                    f" x{item.amount}"
                    if item.amount > 1 or item.item_type == "GOLD"
                    else ""
                )
                lines.append(f"    + {item.name}{amt}{dur}")
        if our_only:
            lines.append("  They want:")
            for item in our_only:
                dur = f" for {item.duration} turns" if item.duration > 0 else ""
                amt = (
                    f" x{item.amount}"
                    if item.amount > 1 or item.item_type == "GOLD"
                    else ""
                )
                lines.append(f"    - {item.name}{amt}{dur}")
        lines.append(
            f"  -> respond_to_trade(other_player_id={d.other_player_id}, accept=True/False)"
        )
    return "\n".join(lines)


def narrate_deal_options(opts: lq.DealOptions) -> str:
    lines = [
        f"Trade options with {opts.other_civ_name} (player {opts.other_player_id}):"
    ]
    lines.append(f"\nEconomy:")
    lines.append(
        f"  Our gold: {opts.our_gold} ({opts.our_gpt:+d}/turn) | Favor: {opts.our_favor}"
    )
    lines.append(
        f"  Their gold: {opts.their_gold} ({opts.their_gpt:+d}/turn) | Favor: {opts.their_favor}"
    )
    if opts.our_luxuries or opts.our_strategics:
        lines.append(f"\nOur tradeable resources:")
        if opts.our_luxuries:
            lines.append(f"  Luxuries: {', '.join(opts.our_luxuries)}")
        if opts.our_strategics:
            lines.append(f"  Strategics: {', '.join(opts.our_strategics)}")
    if opts.their_luxuries or opts.their_strategics:
        lines.append(f"\nTheir tradeable resources:")
        if opts.their_luxuries:
            lines.append(f"  Luxuries: {', '.join(opts.their_luxuries)}")
        if opts.their_strategics:
            lines.append(f"  Strategics: {', '.join(opts.their_strategics)}")
    lines.append(f"\nAgreements:")
    ob_status = "active" if opts.has_open_borders else "not active (available)"
    lines.append(f"  Open borders: {ob_status}")
    if opts.current_alliance:
        lines.append(f"  Alliance: {opts.current_alliance} (active)")
    elif opts.alliance_eligible:
        lines.append(
            f"  Alliance: eligible (MILITARY, RESEARCH, CULTURAL, ECONOMIC, RELIGIOUS)"
        )
    else:
        lines.append(
            f"  Alliance: not eligible (requires declared friendship + Diplomatic Service civic)"
        )
    return "\n".join(lines)


def narrate_policies(gov: lq.GovernmentStatus) -> str:
    lines = [f"Government: {gov.government_name} ({gov.government_type})"]

    if gov.slots:
        lines.append(f"\n{len(gov.slots)} policy slots:")
        for s in gov.slots:
            slot_label = s.slot_type.replace("SLOT_", "").title()
            if s.current_policy:
                lines.append(
                    f"  Slot {s.slot_index} ({slot_label}): {s.current_policy_name} ({s.current_policy})"
                )
            else:
                lines.append(f"  Slot {s.slot_index} ({slot_label}): EMPTY")

    if gov.available_policies:
        by_type: dict[str, list[lq.PolicyInfo]] = {}
        for p in gov.available_policies:
            by_type.setdefault(p.slot_type, []).append(p)
        lines.append("\nAvailable policies:")
        for slot_type in [
            "SLOT_MILITARY",
            "SLOT_ECONOMIC",
            "SLOT_DIPLOMATIC",
            "SLOT_WILDCARD",
        ]:
            policies = by_type.get(slot_type, [])
            if policies:
                label = slot_type.replace("SLOT_", "").title()
                lines.append(f"  {label}:")
                for p in policies:
                    lines.append(f"    {p.name} ({p.policy_type}): {p.description}")

    lines.append(
        "\nUse set_policies with slot assignments, e.g. '0=POLICY_AGOGE,1=POLICY_URBAN_PLANNING'"
    )
    lines.append("Wildcard slots can accept any policy type.")
    return "\n".join(lines)


def narrate_governors(gov: lq.GovernorStatus) -> str:
    lines = [
        f"Governor Points: {gov.points_available} available, {gov.points_spent} spent"
    ]
    if gov.can_appoint:
        lines.append("** Can appoint a new governor! **")

    if gov.appointed:
        lines.append(f"\nAppointed ({len(gov.appointed)}):")
        for g in gov.appointed:
            if g.assigned_city_id >= 0:
                est = (
                    " (established)"
                    if g.is_established
                    else f" ({g.turns_to_establish} turns to establish)"
                )
                lines.append(
                    f"  {g.name} ({g.governor_type}) — {g.assigned_city_name}{est}"
                )
            else:
                lines.append(f"  {g.name} ({g.governor_type}) — Unassigned")
            if g.available_promotions:
                lines.append("    Available promotions:")
                for p in g.available_promotions:
                    lines.append(
                        f"      {p.name} ({p.promotion_type}): {p.description}"
                    )

    if gov.available_to_appoint:
        lines.append(f"\nAvailable to appoint ({len(gov.available_to_appoint)}):")
        for g in gov.available_to_appoint:
            lines.append(f"  {g.name} — {g.title} ({g.governor_type})")

    lines.append(
        "\nUse appoint_governor/assign_governor/promote_governor(governor_type, promotion_type)."
    )
    return "\n".join(lines)


def narrate_unit_promotions(status: lq.UnitPromotionStatus) -> str:
    if not status.promotions:
        return f"No promotions available for {status.unit_type} (id:{status.unit_id})."
    lines = [f"Promotions for {status.unit_type} (id:{status.unit_id}):"]
    for p in status.promotions:
        lines.append(f"  {p.name} ({p.promotion_type}): {p.description}")
    lines.append("\nUse promote_unit(unit_id, promotion_type) to apply.")
    return "\n".join(lines)


def narrate_city_states(status: lq.EnvoyStatus) -> str:
    lines = [f"Envoy tokens available: {status.tokens_available}"]
    if not status.city_states:
        lines.append("No known city-states.")
    else:
        lines.append(f"\n{len(status.city_states)} known city-states:")
        for cs in status.city_states:
            suz = f" (Suzerain: {cs.suzerain_name})" if cs.suzerain_id >= 0 else ""
            can = (
                " [can send]"
                if cs.can_send_envoy and status.tokens_available > 0
                else ""
            )
            lines.append(
                f"  {cs.name} ({cs.city_state_type}) — {cs.envoys_sent} envoys{suz}{can} [player {cs.player_id}]"
            )
    if status.tokens_available > 0:
        lines.append("\nUse send_envoy(player_id) to send an envoy.")
    return "\n".join(lines)


def narrate_pantheon_status(status: lq.PantheonStatus) -> str:
    lines = []
    if status.has_pantheon:
        lines.append(
            f"Pantheon: {status.current_belief_name} ({status.current_belief})"
        )
        lines.append(f"Faith: {status.faith_balance:.0f}")
    else:
        lines.append(f"No pantheon selected. Faith: {status.faith_balance:.0f}")
        if status.available_beliefs:
            lines.append(f"\n{len(status.available_beliefs)} available beliefs:")
            for b in status.available_beliefs:
                lines.append(f"  {b.name} ({b.belief_type}): {b.description}")
            lines.append("\nUse choose_pantheon(belief_type) to found a pantheon.")
        else:
            lines.append("No beliefs available (all taken or insufficient faith).")
    return "\n".join(lines)


def narrate_religion_founding_status(status: lq.ReligionFoundingStatus) -> str:
    lines = []
    if status.has_religion:
        lines.append(f"Religion: {status.religion_name} ({status.religion_type})")
        lines.append(f"Faith: {status.faith_balance:.0f}")
        lines.append("You have already founded a religion.")
    else:
        lines.append(f"No religion founded. Faith: {status.faith_balance:.0f}")
        if status.pantheon_index >= 0:
            lines.append(f"Pantheon: index {status.pantheon_index}")
        else:
            lines.append("No pantheon selected.")

        if status.available_religions:
            lines.append(f"\nAvailable religions ({len(status.available_religions)}):")
            for rtype, rname in status.available_religions:
                lines.append(f"  {rname} ({rtype})")

        for cls_name, beliefs in status.beliefs_by_class.items():
            short = cls_name.replace("BELIEF_CLASS_", "").title()
            lines.append(f"\n{short} beliefs ({len(beliefs)}):")
            for b in beliefs:
                lines.append(f"  {b.name} ({b.belief_type}): {b.description}")

        if status.available_religions and status.beliefs_by_class:
            lines.append(
                "\nUse found_religion(religion_type, follower_belief, founder_belief) "
                "after your Great Prophet has activated on a Holy Site."
            )
    return "\n".join(lines)


def narrate_dedications(status: lq.DedicationStatus) -> str:
    era_names = {
        0: "Ancient",
        1: "Classical",
        2: "Medieval",
        3: "Renaissance",
        4: "Industrial",
        5: "Modern",
        6: "Atomic",
        7: "Information",
    }
    era_name = era_names.get(status.era, f"Era {status.era}")
    lines = [
        f"{status.age_type} Age — {era_name} Era",
        f"Era Score: {status.era_score} (Dark: {status.dark_threshold}, Golden: {status.golden_threshold})",
    ]
    if status.active:
        lines.append(f"\nActive dedications: {', '.join(status.active)}")
    if status.selections_allowed > 0:
        lines.append(f"\n{status.selections_allowed} dedication(s) to choose:")
        for c in status.choices:
            desc = (
                c.golden_desc
                if status.age_type in ("Golden", "Heroic")
                else (c.dark_desc if status.age_type == "Dark" else c.normal_desc)
            )
            lines.append(f"  [{c.index}] {c.name}: {desc}")
        lines.append("\nUse choose_dedication(dedication_index=N) to select.")
    elif not status.active:
        lines.append("\nNo dedications available or required.")
    return "\n".join(lines)


def narrate_district_advisor(
    placements: list[lq.DistrictPlacement], district_type: str
) -> str:
    if not placements:
        return f"No valid placement tiles for {district_type}."
    lines = [f"{district_type} placement options ({len(placements)} tiles):"]
    for i, p in enumerate(placements, 1):
        adj_parts = [f"{v} {k}" for k, v in p.adjacency.items()]
        adj_str = ", ".join(adj_parts) if adj_parts else "no adjacency"
        lines.append(
            f"  #{i} ({p.x},{p.y}) Adj: +{p.total_adjacency} ({adj_str}) — {p.terrain_desc}"
        )
    return "\n".join(lines)


def narrate_wonder_advisor(
    placements: list[lq.WonderPlacement], wonder_name: str
) -> str:
    if not placements:
        return f"No valid placement tiles for {wonder_name} in this city."
    short_name = wonder_name.replace("BUILDING_", "").replace("_", " ").title()
    lines = [f"{wonder_name} placement options ({len(placements)} tiles):"]
    for i, p in enumerate(placements, 1):
        # Build terrain description
        terrain = p.terrain.replace("TERRAIN_", "").replace("_", " ").lower()
        feat = ""
        if p.feature != "none":
            feat = " " + p.feature.replace("FEATURE_", "").replace("_", " ").lower()
        tags = []
        if p.has_river:
            tags.append("river")
        if p.is_coastal:
            tags.append("coastal")
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        warn_parts = []
        if p.improvement != "none":
            imp = p.improvement.replace("IMPROVEMENT_", "").replace("_", " ").lower()
            warn_parts.append(f"⚠ REMOVES {imp}")
        if p.resource != "none":
            res = p.resource.replace("RESOURCE_", "").replace("_", " ").lower()
            warn_parts.append(f"⚠ DISPLACES {res}")
        warn_str = f" — {', '.join(warn_parts)}" if warn_parts else ""
        prefix = "!!" if warn_parts else "  "
        lines.append(
            f"{prefix} #{i} ({p.x},{p.y}) {terrain}{feat}{tag_str}"
            f" — score:{p.displacement_score}{warn_str}"
        )
    best = placements[0]
    lines.append(
        f"\nRecommended: ({best.x},{best.y}) — lowest displacement"
    )
    lines.append(
        f"Use: set_city_production(city_id=<id>, item_type=\"BUILDING\","
        f" item_name=\"{wonder_name}\", target_x={best.x}, target_y={best.y})"
    )
    return "\n".join(lines)


def narrate_purchasable_tiles(tiles: list[lq.PurchasableTile]) -> str:
    if not tiles:
        return "No purchasable tiles."
    lines = [f"{len(tiles)} purchasable tiles:"]
    for t in tiles:
        res_str = ""
        if t.resource:
            cls_tag = {"strategic": "*", "luxury": "+", "bonus": ""}.get(
                t.resource_class or "", ""
            )
            res_str = f" [{t.resource}{cls_tag}]"
        lines.append(f"  ({t.x},{t.y}): {t.cost}g — {t.terrain}{res_str}")
    return "\n".join(lines)


def narrate_great_people(gp: list[lq.GreatPersonInfo]) -> str:
    if not gp:
        return "No Great People in timeline."
    lines = [f"{len(gp)} Great People:"]
    for g in gp:
        progress = f"{g.player_points}/{g.cost}"
        recruit_tag = " [CAN RECRUIT]" if g.can_recruit else ""
        entry = f"  {g.class_name}: {g.individual_name} ({g.era_name}) — {g.claimant} — your points: {progress}{recruit_tag}"
        if g.ability:
            entry += f"\n    Ability: {g.ability}"
        # Show patronize costs (skip INT_MAX values which mean unavailable)
        costs = []
        if 0 < g.gold_cost < 2_000_000_000:
            costs.append(f"{g.gold_cost}g")
        if 0 < g.faith_cost < 2_000_000_000:
            costs.append(f"{g.faith_cost}f")
        if costs:
            entry += f"\n    Patronize: {' / '.join(costs)}"
        entry += f"\n    (individual_id: {g.individual_id})"
        lines.append(entry)
    return "\n".join(lines)


def narrate_religion_status(rs: lq.ReligionStatus) -> str:
    if not rs.cities and not rs.summary:
        return "No religion data available."
    lines: list[str] = []
    # Summary — religious victory proximity
    if rs.summary:
        lines.append("Religious Victory Tracker:")
        for s in rs.summary:
            warning = ""
            if s.civs_with_majority >= s.total_majors:
                warning = " !! VICTORY ACHIEVED"
            elif s.civs_with_majority >= s.total_majors - 1:
                warning = " !! IMMINENT"
            lines.append(
                f"  {s.religion_name}: majority in {s.civs_with_majority}/{s.total_majors} civilizations{warning}"
            )
    # Per-civ city breakdown
    if rs.cities:
        by_civ: dict[str, list[lq.CityReligionInfo]] = {}
        for c in rs.cities:
            by_civ.setdefault(c.civ_name, []).append(c)
        lines.append("")
        for civ_name, cities in by_civ.items():
            lines.append(f"{civ_name}:")
            for c in cities:
                follower_str = ""
                if c.followers:
                    parts = [f"{name}:{count}" for name, count in c.followers.items()]
                    follower_str = f" ({', '.join(parts)})"
                lines.append(
                    f"  {c.city_name} (pop {c.population}) — {c.majority_religion}{follower_str}"
                )
    return "\n".join(lines)


def narrate_trade_routes(status: lq.TradeRouteStatus) -> str:
    lines = [f"Trade Routes: {status.active_count}/{status.capacity} active"]
    on_route = [t for t in status.traders if t.on_route]
    idle = [t for t in status.traders if not t.on_route]
    if on_route:
        lines.append(f"\nOn route ({len(on_route)}):")
        for t in on_route:
            origin = t.route_origin or "?"
            dest = t.route_dest or "?"
            # Owner label
            if t.is_domestic:
                label = "Domestic"
            elif t.is_city_state:
                label = f"City-State"
            else:
                label = t.route_owner or "?"
            parts = [f"  Trader (id:{t.unit_id}) {origin} -> {dest} ({label})"]
            # Yields
            yields = []
            if t.origin_yields:
                yields.append(t.origin_yields)
            if t.dest_yields:
                yields.append(f"-> dest: {t.dest_yields}")
            if yields:
                parts.append(" | " + " ".join(yields))
            # Flags
            flags = []
            if t.has_quest:
                flags.append("[QUEST]")
            if t.pressure_out > 0 and t.religion_out:
                flags.append(f"{t.religion_out} -> {t.pressure_out}")
            if t.pressure_in > 0 and t.religion_in:
                flags.append(f"{t.religion_in} <- {t.pressure_in}")
            if flags:
                parts.append(" | " + " ".join(flags))
            lines.append("".join(parts))
    if idle:
        lines.append(f"\nIdle ({len(idle)}):")
        for t in idle:
            lines.append(
                f"  Trader (id:{t.unit_id}) at ({t.x},{t.y}) — needs trade_route or teleport"
            )
    if not status.traders:
        lines.append("\nNo trader units.")
    free_slots = status.capacity - status.active_count
    if free_slots > 0:
        lines.append(f"\n{free_slots} free route slot(s) — build/buy a Trader to fill.")
    if status.ghost_count > 0:
        engine_total = status.active_count + status.ghost_count
        lines.append(
            f"\nWARNING: {status.ghost_count} ghost route record(s) in engine "
            f"(engine reports {engine_total}, only {status.active_count} have living traders)."
        )
    return "\n".join(lines)


def narrate_trade_destinations(dests: list[lq.TradeDestination]) -> str:
    if not dests:
        return "No valid trade route destinations. Check that your trader is in a city and has moves."
    domestic = [d for d in dests if d.is_domestic]
    foreign = [d for d in dests if not d.is_domestic]
    lines = [f"{len(dests)} trade route destinations:"]

    def _fmt_dest(d: lq.TradeDestination, show_owner: bool = False) -> str:
        owner = f" ({d.owner_name})" if show_owner and d.owner_name else ""
        parts = [f"  {d.city_name}{owner} at ({d.x},{d.y})"]
        # Yields
        yields = []
        if d.origin_yields:
            yields.append(d.origin_yields)
        if d.dest_yields:
            yields.append(f"-> dest: {d.dest_yields}")
        if yields:
            parts.append(" | " + " ".join(yields))
        # Flags
        flags = []
        if d.has_quest:
            flags.append("[QUEST]")
        if d.has_trading_post:
            flags.append("Trading Post")
        if d.pressure_out > 0 and d.religion_out:
            flags.append(f"{d.religion_out} -> {d.pressure_out}")
        if d.pressure_in > 0 and d.religion_in:
            flags.append(f"{d.religion_in} <- {d.pressure_in}")
        if flags:
            parts.append(" | " + " ".join(flags))
        return "".join(parts)

    if domestic:
        lines.append("\nDomestic (food + production to destination):")
        for d in domestic:
            lines.append(_fmt_dest(d))
    if foreign:
        lines.append("\nInternational (gold to origin):")
        for d in foreign:
            lines.append(_fmt_dest(d, show_owner=True))
    # Summarize city-state quests
    quest_cs = [d.city_name for d in dests if d.has_quest]
    if quest_cs:
        lines.append(
            f"\nCity-state quests (send trade route for envoy): {', '.join(quest_cs)}"
        )
    lines.append("\nUse unit_action with action='trade_route', target_x=X, target_y=Y")
    return "\n".join(lines)


def narrate_world_congress(status: lq.WorldCongressStatus) -> str:
    lines = []
    imminent = not status.is_in_session and status.turns_until_next <= 0

    if status.is_in_session or imminent:
        if status.is_in_session:
            lines.append("World Congress: IN SESSION (vote required!)")
        else:
            lines.append(
                "World Congress: FIRES THIS TURN — use queue_wc_votes() before end_turn()!"
            )
        # Build clear cost table: "N votes = X favor total"
        costs = status.favor_costs
        if costs and len(costs) > 1:
            cost_entries = []
            for i, c in enumerate(costs):
                n = i + 1  # 1-indexed vote count
                if n == 1:
                    cost_entries.append(f"1 vote=free")
                else:
                    cost_entries.append(f"{n}={c}")
                if c > status.favor:
                    break  # stop showing costs we can't afford
            costs_str = ", ".join(cost_entries)
        else:
            costs_str = "1 vote=free, 2=10, 3=30, 4=60, 5=100, 6=150, 7=210, 8=280, 9=360, 10=450, 11=550"
        lines.append(f"Favor: {status.favor} | Vote costs (cumulative): {costs_str}")
    else:
        if status.turns_until_next >= 0:
            lines.append(
                f"World Congress: Next session in {status.turns_until_next} turns"
            )
        else:
            lines.append("World Congress: Not yet convened")
        lines.append(f"Favor: {status.favor}")

    if status.resolutions:
        lines.append("")
        for i, r in enumerate(status.resolutions, 1):
            if status.is_in_session:
                # Active session — show full voting details
                lines.append(f"Resolution #{i}: {r.name} (hash: {r.resolution_hash})")
                lines.append(f"  Target type: {r.target_kind}")
                if r.effect_a:
                    lines.append(f"  Option A: {r.effect_a}")
                if r.effect_b:
                    lines.append(f"  Option B: {r.effect_b}")
                if r.possible_targets:
                    tgt_strs = []
                    for t in r.possible_targets:
                        if ":" in t:
                            tid, tname = t.split(":", 1)
                            tgt_strs.append(f"[target={tid}] {tname}")
                        else:
                            tgt_strs.append(t)
                    lines.append(f"  Targets: {', '.join(tgt_strs)}")
                lines.append(
                    f"  -> vote_world_congress(resolution_hash={r.resolution_hash}, option=1or2, target_index=N, num_votes=1)"
                )
            elif imminent:
                # Imminent but not yet in session — resolutions are LAST SESSION's passed outcomes
                # Show as active effects, not as upcoming votes
                outcome = "A" if r.winner == 0 else "B" if r.winner == 1 else "?"
                effect = (
                    r.effect_a if r.winner == 0 else r.effect_b if r.winner == 1 else ""
                )
                chosen = f" ({r.chosen_thing})" if r.chosen_thing else ""
                lines.append(f"  {r.name} — Outcome {outcome}{chosen}: {effect}")
            else:
                outcome = "A" if r.winner == 0 else "B" if r.winner == 1 else "?"
                effect = (
                    r.effect_a if r.winner == 0 else r.effect_b if r.winner == 1 else ""
                )
                chosen = f" ({r.chosen_thing})" if r.chosen_thing else ""
                lines.append(f"  {r.name} — Outcome {outcome}{chosen}: {effect}")

        if imminent:
            lines.append("")
            lines.append(
                "NOTE: Above are ACTIVE EFFECTS from last session. Upcoming resolutions will be different."
            )
            lines.append(
                "The handler resolves targets at runtime during the WC session."
            )
            lines.append("")
            lines.append(
                'To vote: queue_wc_votes(votes=\'[{"hash": <hash>, "option": 1or2, "target": <player_id>, "votes": N}, ...]\')'
            )
            lines.append(
                "Common hashes: Diplomatic Victory = 334823573. Use get_diplomacy for player IDs."
            )
            lines.append("Then call end_turn() — handler fires during WC processing.")

    if status.proposals:
        lines.append("\nProposals:")
        for p in status.proposals:
            lines.append(f"  {p.sender_name} -> {p.target_name}: {p.description}")

    return "\n".join(lines)


def narrate_victory_progress(vp: lq.VictoryProgress) -> str:
    if not vp.players:
        return "No victory data available."

    lines = ["=== VICTORY PROGRESS ===", ""]

    # Find our player (player_id 0 typically, or first non-Unmet)
    us = next((p for p in vp.players if p.name != "Unmet"), None)

    # --- Science Victory ---
    lines.append("SCIENCE VICTORY (launch 4 space projects = 50 VP)")
    sci_sorted = sorted(
        vp.players, key=lambda p: (p.science_vp, p.techs_researched), reverse=True
    )
    for p in sci_sorted:
        marker = " <--" if us and p.player_id == us.player_id else ""
        sp_info = ""
        if p.spaceports > 0 or p.space_progress:
            sp_info = f" | {p.spaceports} spaceport(s) [{p.space_progress}]"
        lines.append(
            f"  {p.name}: {p.science_vp}/{p.science_vp_needed} VP | {p.techs_researched} techs{sp_info}{marker}"
        )

    # --- Domination Victory ---
    lines.append("")
    lines.append("DOMINATION (own all original capitals)")
    for p in vp.players:
        holds = vp.capitals_held.get(p.name, True)
        status = "holds own capital" if holds else "CAPITAL LOST"
        marker = " <--" if us and p.player_id == us.player_id else ""
        lines.append(f"  {p.name}: {status} | military {p.military_strength}{marker}")

    # --- Culture Victory ---
    lines.append("")
    lines.append("CULTURE (your tourists > every civ's domestic tourists)")
    if us:
        lines.append(f"  Our domestic tourists: {us.staycationers}")
        for name, our_tourists in vp.our_tourists_from.items():
            their_dom = vp.their_staycationers.get(name, 0)
            gap = their_dom - our_tourists
            status = "DOMINANT" if gap <= 0 else f"need {gap} more"
            lines.append(f"  vs {name}: {our_tourists}/{their_dom} tourists ({status})")

    # --- Religious Victory ---
    lines.append("")
    slots_str = (
        f" — slots: {vp.religions_founded}/{vp.religions_max}"
        if vp.religions_max > 0
        else ""
    )
    lines.append(f"RELIGION (your religion majority in all civs{slots_str})")
    for p in vp.players:
        rel = vp.religion_majority.get(p.name, "none")
        rel_short = rel.replace("RELIGION_", "").title() if rel != "none" else "none"
        founded_name = vp.religion_founded_names.get(p.name)
        founded = f" (FOUNDED: {founded_name})" if founded_name else ""
        marker = " <--" if us and p.player_id == us.player_id else ""
        lines.append(
            f"  {p.name}: majority={rel_short}{founded} | {p.religion_cities} cities converted{marker}"
        )
    if vp.religions_max > 0 and vp.religions_founded >= vp.religions_max:
        lines.append(
            f"  !! All {vp.religions_max} religion slots filled — no more Great Prophets available"
        )

    # --- Diplomatic Victory ---
    lines.append("")
    lines.append("DIPLOMATIC (20 VP from World Congress)")
    diplo_sorted = sorted(vp.players, key=lambda p: p.diplomatic_vp, reverse=True)
    for p in diplo_sorted:
        marker = " <--" if us and p.player_id == us.player_id else ""
        lines.append(f"  {p.name}: {p.diplomatic_vp}/20 VP{marker}")

    # --- Score Victory ---
    lines.append("")
    lines.append("SCORE (highest at turn 500)")
    score_sorted = sorted(vp.players, key=lambda p: p.score, reverse=True)
    for p in score_sorted:
        marker = " <--" if us and p.player_id == us.player_id else ""
        lines.append(f"  {p.name}: {p.score}{marker}")

    # --- Rival Intelligence (met civs only) ---
    lines.append("")
    lines.append("RIVAL INTELLIGENCE (met civilizations)")
    for p in sorted(vp.players, key=lambda p: p.score, reverse=True):
        marker = " <--" if us and p.player_id == us.player_id else ""
        lines.append(
            f"  {p.name}: {p.num_cities} cities | "
            f"Sci {p.science_yield:.0f} Cul {p.culture_yield:.0f} Gold {p.gold_yield:+.0f} | "
            f"Mil {p.military_strength}{marker}"
        )

    # --- Demographics (all civilizations, anonymized) ---
    if vp.demographics:
        lines.append("")
        lines.append("DEMOGRAPHICS (all civilizations)")
        label_map = {
            "Population": "Population",
            "Soldiers": "Soldiers",
            "CropYield": "Crop Yield",
            "GNP": "GNP",
            "Land": "Land",
            "Goods": "Goods",
        }
        for key in ["Population", "Soldiers", "CropYield", "GNP", "Land", "Goods"]:
            d = vp.demographics.get(key)
            if d:
                label = label_map.get(key, key)
                lines.append(
                    f"  {label:12s} Rank {d.rank} | "
                    f"Ours: {d.value:.0f} | Best: {d.best:.0f} | "
                    f"Avg: {d.average:.1f} | Worst: {d.worst:.0f}"
                )

    # --- Victory Path Assessment ---
    if us:
        lines.append("")
        lines.append("VICTORY ASSESSMENT")
        assessments: list[tuple[str, int, str]] = []  # (type, viability 0-100, reason)

        # Science: assess by tech count relative to met leaders and science VP progress
        sci_leader = max(vp.players, key=lambda p: p.techs_researched)
        sci_gap = sci_leader.techs_researched - us.techs_researched
        best_label = f"best known: {sci_leader.name} ({sci_leader.techs_researched})"
        if us.science_vp > 0:
            assessments.append(
                (
                    "Science",
                    80,
                    f"Space race started ({us.science_vp}/{us.science_vp_needed} VP)",
                )
            )
        elif sci_gap <= 5:
            assessments.append(
                ("Science", 60, f"Near tech lead ({sci_gap} behind {best_label})")
            )
        elif sci_gap <= 15:
            assessments.append(
                ("Science", 30, f"Behind in tech ({sci_gap} behind {best_label})")
            )
        else:
            assessments.append(
                ("Science", 10, f"Far behind in tech ({sci_gap} behind {best_label})")
            )

        # Domination: check our military vs all civs (use demographics Soldiers for full picture)
        soldiers_demo = vp.demographics.get("Soldiers")
        our_holds = vp.capitals_held.get(us.name, True)
        best_mil = (
            soldiers_demo.best
            if soldiers_demo
            else max(p.military_strength for p in vp.players)
        )
        if not our_holds:
            assessments.append(("Domination", 5, "CAPITAL LOST — defensive priority!"))
        elif us.military_strength >= best_mil * 0.8:
            rivals_with_caps = sum(
                1
                for name, holds in vp.capitals_held.items()
                if holds and name != us.name
            )
            assessments.append(
                (
                    "Domination",
                    40,
                    f"Strong military ({us.military_strength} vs best {best_mil:.0f}), {rivals_with_caps} known capitals to capture",
                )
            )
        else:
            assessments.append(
                (
                    "Domination",
                    15,
                    f"Military too weak ({us.military_strength} vs best {best_mil:.0f})",
                )
            )

        # Culture: compare our tourists vs their staycationers
        if vp.our_tourists_from:
            culture_gaps = []
            for name, our_tourists in vp.our_tourists_from.items():
                their_dom = vp.their_staycationers.get(name, 0)
                culture_gaps.append(their_dom - our_tourists)
            max_gap = max(culture_gaps) if culture_gaps else 999
            if max_gap <= 0:
                assessments.append(
                    ("Culture", 95, "CULTURALLY DOMINANT over all civs!")
                )
            elif max_gap <= 10:
                assessments.append(
                    ("Culture", 70, f"Close to cultural victory (max gap: {max_gap})")
                )
            elif max_gap <= 30:
                assessments.append(
                    ("Culture", 40, f"Tourism growing (max gap: {max_gap})")
                )
            else:
                assessments.append(
                    ("Culture", 15, f"Large tourism gap (max gap: {max_gap})")
                )
        else:
            assessments.append(("Culture", 20, "No tourism data"))

        # Religion: check if we founded one
        if us.has_religion:
            total_civs = len([p for p in vp.players if p.name != "Unmet"])
            our_rel = vp.religion_majority.get(us.name, "none")
            converted = sum(
                1 for rel in vp.religion_majority.values() if rel == our_rel
            )
            assessments.append(
                (
                    "Religion",
                    min(70, converted * 100 // total_civs),
                    f"Religion in {converted}/{total_civs} civs",
                )
            )
        else:
            assessments.append(("Religion", 0, "No founded religion — path closed"))

        # Diplomatic: steady accumulation
        if us.diplomatic_vp >= 15:
            assessments.append(("Diplomatic", 80, f"{us.diplomatic_vp}/20 VP — close!"))
        elif us.diplomatic_vp >= 8:
            assessments.append(
                ("Diplomatic", 50, f"{us.diplomatic_vp}/20 VP — mid-game")
            )
        else:
            assessments.append(
                ("Diplomatic", 20, f"{us.diplomatic_vp}/20 VP — slow accumulation")
            )

        # Score: always a fallback — use demographics rank if available
        pop_demo = vp.demographics.get("Population")
        if pop_demo:
            assessments.append(
                (
                    "Score",
                    50 if pop_demo.rank <= 2 else 25,
                    f"Rank #{pop_demo.rank} by population (proxy for score)",
                )
            )
        else:
            our_rank = sorted(vp.players, key=lambda p: p.score, reverse=True)
            our_pos = (
                next(
                    (i for i, p in enumerate(our_rank) if p.player_id == us.player_id),
                    0,
                )
                + 1
            )
            assessments.append(
                (
                    "Score",
                    50 if our_pos <= 2 else 25,
                    f"Rank #{our_pos} by score (met civs only)",
                )
            )

        # Sort by viability and display
        assessments.sort(key=lambda a: a[1], reverse=True)
        best = assessments[0]
        for vtype, viability, reason in assessments:
            bar = "#" * (viability // 10) + "-" * (10 - viability // 10)
            rec = " ** RECOMMENDED **" if vtype == best[0] and viability >= 30 else ""
            lines.append(f"  {vtype:12s} [{bar}] {viability}% — {reason}{rec}")

    return "\n".join(lines)


def narrate_notifications(notifs: list[lq.GameNotification]) -> str:
    if not notifs:
        return "No active notifications."

    action_required = [n for n in notifs if n.is_action_required]
    info_notifs = [n for n in notifs if not n.is_action_required]

    lines = []
    if action_required:
        lines.append(f"== Action Required ({len(action_required)}) ==")
        for n in action_required:
            hint = f"  -> Use: {n.resolution_hint}" if n.resolution_hint else ""
            loc = f" at ({n.x},{n.y})" if n.x >= 0 else ""
            lines.append(f"  * {n.message}{loc}{hint}")

    if info_notifs:
        if lines:
            lines.append("")
        lines.append(f"== Notifications ({len(info_notifs)}) ==")
        for n in info_notifs:
            loc = f" at ({n.x},{n.y})" if n.x >= 0 else ""
            lines.append(f"  - {n.message}{loc}")

    return "\n".join(lines)
