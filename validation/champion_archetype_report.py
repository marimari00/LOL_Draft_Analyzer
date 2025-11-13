"""Generate comprehensive champion archetype validation report."""

import json
from pathlib import Path


def load_data():
    """Load all necessary data files."""
    with open('data/processed/spell_based_attributes.json', 'r', encoding='utf-8') as f:
        attrs_data = json.load(f)
    
    with open('data/processed/archetype_assignments.json', 'r', encoding='utf-8') as f:
        assignments_data = json.load(f)
    
    with open('data/processed/archetype_definitions.json', 'r', encoding='utf-8') as f:
        definitions = json.load(f)
    
    return attrs_data['attributes'], assignments_data, definitions


def validate_mathematics(attrs, assignments):
    """Validate mathematical consistency."""
    issues = []
    
    for champ, champ_attrs in attrs.items():
        # Check for NaN, inf, or invalid values
        for attr_name, value in champ_attrs.items():
            if isinstance(value, (int, float)):
                if value != value:  # NaN check
                    issues.append(f"{champ}: {attr_name} is NaN")
                elif value == float('inf') or value == float('-inf'):
                    issues.append(f"{champ}: {attr_name} is infinite")
        
        # Validate burst_ratio calculation
        burst_dmg = champ_attrs.get('burst_damage', 0)
        sustained_dmg = champ_attrs.get('sustained_damage', 0)
        burst_ratio = champ_attrs.get('burst_ratio', 0)
        
        if sustained_dmg > 0:
            expected_ratio = burst_dmg / sustained_dmg
            if abs(expected_ratio - burst_ratio) > 0.001:
                issues.append(f"{champ}: burst_ratio mismatch (expected {expected_ratio:.3f}, got {burst_ratio:.3f})")
        
        # Validate burst_index calculation
        burst_index = champ_attrs.get('burst_index', 0)
        if burst_dmg > 0:
            burst_magnitude = min(1.0, burst_dmg / 1000.0)
            expected_index = burst_ratio * burst_magnitude
            if abs(expected_index - burst_index) > 0.001:
                issues.append(f"{champ}: burst_index mismatch (expected {expected_index:.3f}, got {burst_index:.3f})")
    
    return issues


def generate_report():
    """Generate comprehensive validation report."""
    attrs, assignments_data, definitions = load_data()
    assignments = assignments_data['assignments']  # Get nested assignments dict
    
    print("=" * 100)
    print("CHAMPION ARCHETYPE VALIDATION REPORT")
    print("=" * 100)
    
    # Mathematical validation
    print("\n1. MATHEMATICAL CONSISTENCY CHECK")
    print("-" * 100)
    math_issues = validate_mathematics(attrs, assignments)
    if math_issues:
        print(f"❌ Found {len(math_issues)} mathematical issues:")
        for issue in math_issues[:10]:
            print(f"   {issue}")
        if len(math_issues) > 10:
            print(f"   ... and {len(math_issues) - 10} more")
    else:
        print("✓ All mathematical calculations are consistent")
    
    # Archetype distribution
    print("\n2. ARCHETYPE DISTRIBUTION")
    print("-" * 100)
    distribution = assignments_data['distribution']
    total = assignments_data['metadata']['total_champions']
    
    for archetype, count in sorted(distribution.items(), key=lambda x: -x[1]):
        pct = 100 * count / total
        bar = "█" * int(pct / 2)
        print(f"  {archetype:20s} {count:3d} ({pct:5.1f}%) {bar}")
    
    # Sample champions by archetype
    print("\n3. SAMPLE CHAMPIONS BY ARCHETYPE")
    print("-" * 100)
    
    # Group champions by archetype
    by_archetype = {}
    for champ, data in assignments.items():
        archetype = data.get('primary_archetype')
        if archetype and archetype not in by_archetype:
            by_archetype[archetype] = []
        if archetype:
            by_archetype[archetype].append(champ)
    
    for archetype in sorted(by_archetype.keys()):
        champs = sorted(by_archetype[archetype])
        print(f"\n{archetype.upper()} ({len(champs)} champions):")
        print(f"  {', '.join(champs[:15])}")
        if len(champs) > 15:
            print(f"  ... and {len(champs) - 15} more")
    
    # Detailed attribute ranges by archetype
    print("\n4. ATTRIBUTE RANGES BY ARCHETYPE")
    print("-" * 100)
    
    marksmen = [c for c, d in assignments.items() if c not in ['metadata', 'distribution'] 
                and d.get('primary_archetype') == 'marksman']
    
    if marksmen:
        print(f"\nMARKSMAN ARCHETYPE ({len(marksmen)} champions):")
        print(f"Champions: {', '.join(sorted(marksmen))}")
        print("\nAttribute ranges:")
        
        attr_names = ['sustained_dps', 'max_range', 'mobility_score', 'burst_index', 'total_ad_ratio']
        for attr in attr_names:
            values = [attrs[c][attr] for c in marksmen if c in attrs and attr in attrs[c]]
            if values:
                print(f"  {attr:18s}: min={min(values):7.2f}  max={max(values):7.2f}  avg={sum(values)/len(values):7.2f}")
    
    # Check marksman requirements
    print("\n5. MARKSMAN REQUIREMENT VALIDATION")
    print("-" * 100)
    
    marksman_reqs = definitions['archetypes']['marksman']['requirements']
    print("Current requirements:")
    for req_name, req_data in marksman_reqs.items():
        print(f"  {req_name:18s}: {req_data}")
    
    print("\nChampions meeting/failing each requirement:")
    for req_name, req_data in marksman_reqs.items():
        meeting = []
        failing = []
        
        for champ in marksmen:
            if champ in attrs:
                value = attrs[champ].get(req_name, 0)
                
                # Check if requirement is met
                if 'min' in req_data and value < req_data['min']:
                    failing.append(f"{champ}({value:.1f})")
                elif 'max' in req_data and value > req_data['max']:
                    failing.append(f"{champ}({value:.1f})")
                elif 'allowed' in req_data and value not in req_data['allowed']:
                    failing.append(f"{champ}({value})")
                else:
                    if isinstance(value, (int, float)):
                        meeting.append(f"{champ}({value:.1f})")
                    else:
                        meeting.append(f"{champ}({value})")
        
        if failing:
            print(f"\n  {req_name}: ❌ {len(failing)} failing")
            print(f"    Failing: {', '.join(failing[:5])}")
        else:
            print(f"\n  {req_name}: ✓ All {len(meeting)} marksmen meet requirement")
    
    # Check for edge cases
    print("\n6. EDGE CASES & INTERESTING CLASSIFICATIONS")
    print("-" * 100)
    
    # Find champions with conflicting scores
    conflicts = []
    for champ, data in assignments.items():
        scores = data.get('all_scores', {})
        primary = data.get('primary_archetype')
        primary_score = scores.get(primary, 0)
        
        # Find close competitors
        competitors = [(arch, score) for arch, score in scores.items() 
                      if arch != primary and score >= primary_score * 0.9]
        
        if competitors:
            conflicts.append((champ, primary, primary_score, competitors))
    
    if conflicts:
        print(f"\nChampions with close archetype scores (within 10%):")
        for champ, primary, p_score, competitors in sorted(conflicts, key=lambda x: -len(x[3]))[:10]:
            comp_str = ', '.join([f"{arch}({score:.2f})" for arch, score in competitors[:3]])
            print(f"  {champ:14s} → {primary}({p_score:.2f}) vs {comp_str}")
    
    print("\n" + "=" * 100)
    print("REPORT COMPLETE")
    print("=" * 100)


if __name__ == '__main__':
    generate_report()
