"""
Mathematical Validation of Archetype System

Validates that:
1. Attributes are computed correctly from raw champion data
2. Archetype scoring logic is mathematically sound
3. Results reflect actual champion capabilities, not preconceptions

Scientific approach: If math is correct, counter-intuitive results might be TRUE insights.
"""

import json
from pathlib import Path


def load_data():
    """Load all required data files."""
    with open('data/processed/enhanced_attributes.json', 'r') as f:
        attributes = json.load(f)
    
    with open('data/processed/champion_archetypes.json', 'r') as f:
        archetypes = json.load(f)
    
    with open('config/archetypes_v2.json', 'r') as f:
        archetype_defs = json.load(f)
    
    return attributes, archetypes, archetype_defs


def validate_champion_attributes(champ_name, attributes):
    """
    Validate that a champion's attributes make mathematical sense.
    Returns detailed attribute breakdown with source validation.
    """
    attrs = attributes[champ_name]
    
    print(f"\n{'='*80}")
    print(f"CHAMPION: {champ_name}")
    print(f"{'='*80}")
    
    # 1. Damage Pattern Validation
    print(f"\n[DAMAGE PATTERNS - from real game data]")
    print(f"  burst_pattern:     {attrs.get('burst_pattern', 'N/A'):.4f}")
    print(f"  sustained_pattern: {attrs.get('sustained_pattern', 'N/A'):.4f}")
    print(f"  Sum check:         {attrs.get('burst_pattern', 0) + attrs.get('sustained_pattern', 0):.4f} (should ≈ 1.0)")
    
    # 2. Timing Curves
    print(f"\n[DAMAGE TIMING - from spell base damages at different levels]")
    print(f"  damage_early (lvl 1-6):   {attrs.get('damage_early', 'N/A'):.4f}")
    print(f"  damage_mid   (lvl 7-11):  {attrs.get('damage_mid', 'N/A'):.4f}")
    print(f"  damage_late  (lvl 12-18): {attrs.get('damage_late', 'N/A'):.4f}")
    
    # Check if timing makes sense (should generally early >= mid >= late for non-scalers)
    early = attrs.get('damage_early', 0)
    mid = attrs.get('damage_mid', 0)
    late = attrs.get('damage_late', 0)
    
    if late > early:
        print(f"  → SCALING CHAMPION: Late game power ({late:.3f}) > Early game ({early:.3f})")
    elif early > late:
        print(f"  → EARLY GAME CHAMPION: Early power ({early:.3f}) > Late game ({late:.3f})")
    else:
        print(f"  → CONSISTENT CHAMPION: Relatively flat power curve")
    
    # 3. Range Profile
    print(f"\n[RANGE PROFILE - from champion.json]")
    range_profile = attrs.get('range_profile', {})
    print(f"  Auto-attack range:     {range_profile.get('auto_attack', 'N/A')}")
    print(f"  Effective ability:     {range_profile.get('effective_ability', 'N/A')}")
    print(f"  Threat range:          {range_profile.get('threat', 'N/A')}")
    print(f"  Escape range:          {range_profile.get('escape', 'N/A')}")
    
    auto_range = range_profile.get('auto_attack', 0)
    if auto_range >= 500:
        print(f"  → RANGED CHAMPION (AA range >= 500)")
    else:
        print(f"  → MELEE CHAMPION (AA range < 500)")
    
    # 4. Core Stats
    print(f"\n[COMPUTED STATS - from base stats and ratios]")
    print(f"  cc_score:           {attrs.get('cc_score', 'N/A'):.4f}")
    print(f"  mobility_score:     {attrs.get('mobility_score', 'N/A'):.4f}")
    print(f"  survivability_mid:  {attrs.get('survivability_mid', 'N/A'):.4f}")
    print(f"  dueling_power:      {attrs.get('dueling_power', 'N/A'):.4f}")
    print(f"  waveclear_speed:    {attrs.get('waveclear_speed', 'N/A'):.4f}")
    print(f"  aoe_capability:     {attrs.get('aoe_capability', 'N/A'):.4f}")
    print(f"  sustain_score:      {attrs.get('sustain_score', 'N/A'):.4f}")
    
    # 5. Gold Dependency (KNOWN ISSUE - needs investigation)
    gold_dep = attrs.get('gold_dependency', 'N/A')
    print(f"\n[GOLD DEPENDENCY - FLAGGED FOR REVIEW]")
    print(f"  gold_dependency:    {gold_dep:.4f}")
    if isinstance(gold_dep, float) and gold_dep < 0.1:
        print(f"  ⚠ WARNING: Very low value (<0.1) - may be incorrectly normalized")
    
    return attrs


def calculate_archetype_score_manual(attrs, archetype_name, archetype_def):
    """
    Manually recalculate archetype score to verify the algorithm.
    """
    primary_attrs = archetype_def.get('primary_attributes', {})
    range_constraints = archetype_def.get('range_constraints', {})
    exclusions = archetype_def.get('exclusions', {})
    
    scores = {}
    total = 0
    count = 0
    
    print(f"\n[SCORING: {archetype_name}]")
    print(f"Archetype definition: {archetype_def.get('description', 'No description')}")
    print(f"\nAttribute requirements:")
    
    # Score primary attributes
    for attr_name, attr_range in primary_attrs.items():
        champ_value = attrs.get(attr_name, 0.5)
        min_val, max_val = attr_range
        
        # Calculate score using trapezoidal function
        if min_val <= champ_value <= max_val:
            score = 1.0
        elif champ_value < min_val:
            distance = min_val - champ_value
            score = max(0.0, 1.0 - (distance * 2.0))  # PENALTY_FACTOR = 2.0
        else:
            distance = champ_value - max_val
            score = max(0.0, 1.0 - (distance * 2.0))
        
        scores[attr_name] = score
        total += score
        count += 1
        
        status = "✓" if score >= 0.6 else "✗"
        print(f"  {status} {attr_name:20s}: {champ_value:.4f} (want: [{min_val:.2f}, {max_val:.2f}]) → score: {score:.4f}")
    
    # Score range constraints
    for range_type, range_bounds in range_constraints.items():
        range_profile = attrs.get('range_profile', {})
        champ_range = range_profile.get(range_type, 0)
        min_range, max_range = range_bounds
        
        if min_range <= champ_range <= max_range:
            score = 1.0
        elif champ_range < min_range:
            distance = min_range - champ_range
            normalized_distance = distance / 500.0
            score = max(0.0, 1.0 - (normalized_distance * 2.0))
        else:
            distance = champ_range - max_range
            normalized_distance = distance / 500.0
            score = max(0.0, 1.0 - (normalized_distance * 2.0))
        
        scores[f'range_{range_type}'] = score
        total += score
        count += 1
        
        status = "✓" if score >= 0.6 else "✗"
        print(f"  {status} range_{range_type:15s}: {champ_range} (want: [{min_range}, {max_range}]) → score: {score:.4f}")
    
    # Score exclusions (reverse logic)
    for excl_type, excl_bounds in exclusions.items():
        if excl_type == 'auto_attack_range':
            range_profile = attrs.get('range_profile', {})
            champ_range = range_profile.get('auto_attack', 0)
            min_excl, max_excl = excl_bounds
            
            if min_excl <= champ_range <= max_excl:
                score = 0.0  # In exclusion zone = bad
            else:
                score = 1.0  # Outside exclusion zone = good
            
            scores[f'exclusion_{excl_type}'] = score
            total += score
            count += 1
            
            status = "✓" if score >= 0.6 else "✗"
            print(f"  {status} EXCLUSION (not in [{min_excl}, {max_excl}]): {champ_range} → score: {score:.4f}")
    
    # Calculate final score
    avg_score = total / count if count > 0 else 0.0
    weight = archetype_def.get('weight', 1.0)
    weighted_score = min(1.0, avg_score * weight)
    
    print(f"\n  Raw average:     {avg_score:.4f} (sum={total:.2f}, count={count})")
    print(f"  Archetype weight: {weight}")
    print(f"  FINAL SCORE:     {weighted_score:.4f}")
    
    return weighted_score, scores


def analyze_champion_comprehensive(champ_name, attributes, archetypes, archetype_defs):
    """
    Complete mathematical validation for a single champion.
    """
    # Get champion data
    attrs = validate_champion_attributes(champ_name, attributes)
    
    # Get assigned archetypes
    assignment = archetypes['assignments'][champ_name]
    primary = assignment['primary_archetype']
    primary_score = assignment['primary_score']
    all_archetypes = assignment['all_archetypes']
    
    print(f"\n{'='*80}")
    print(f"ARCHETYPE ASSIGNMENT VALIDATION")
    print(f"{'='*80}")
    print(f"\nAssigned PRIMARY: {primary} (score: {primary_score:.4f})")
    
    # Show top 5 archetype matches
    print(f"\nTop 5 archetype matches:")
    for i, arch in enumerate(all_archetypes[:5], 1):
        print(f"  {i}. {arch['name']:20s}: {arch['score']:.4f} ({arch['strength']})")
    
    # Manually recalculate top 3 to verify math
    print(f"\n{'='*80}")
    print(f"MATHEMATICAL VERIFICATION - Recalculating Top 3")
    print(f"{'='*80}")
    
    for arch_data in all_archetypes[:3]:
        arch_name = arch_data['name']
        reported_score = arch_data['score']
        arch_def = archetype_defs['archetypes'][arch_name]
        
        calculated_score, breakdown = calculate_archetype_score_manual(attrs, arch_name, arch_def)
        
        diff = abs(calculated_score - reported_score)
        if diff < 0.001:
            print(f"\n✓ VERIFIED: Reported {reported_score:.4f} matches calculated {calculated_score:.4f}")
        else:
            print(f"\n✗ MISMATCH: Reported {reported_score:.4f} vs calculated {calculated_score:.4f} (diff: {diff:.4f})")


def main():
    """Run comprehensive mathematical validation."""
    print("="*80)
    print("MATHEMATICAL VALIDATION OF ARCHETYPE SYSTEM")
    print("="*80)
    print("\nObjective: Verify that archetype assignments are mathematically sound")
    print("Approach: Check attribute computation + scoring logic + final assignments")
    print("\nIf math is correct, counter-intuitive results may reveal TRUE insights!")
    
    attributes, archetypes, archetype_defs = load_data()
    
    # Test cases: Champions with "surprising" assignments
    test_champions = [
        'Caitlyn',    # Assigned burst_assassin
        'Jinx',       # Assigned utility_carry
        'Azir',       # Assigned split_pusher
        'Orianna',    # Assigned early_game_bully
        'Zed',        # Should check if assassin
        'Malphite',   # Should check if tank
    ]
    
    for champ in test_champions:
        analyze_champion_comprehensive(champ, attributes, archetypes, archetype_defs)
        print("\n" + "="*80)
        print("="*80)
        input("\nPress Enter to continue to next champion...")


if __name__ == "__main__":
    main()
