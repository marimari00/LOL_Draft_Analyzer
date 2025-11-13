"""Assign archetypes to champions using fuzzy scoring."""

import json


def fuzzy_score(value, requirement):
    """Calculate fuzzy membership score."""
    # Handle non-dict requirements (skip)
    if not isinstance(requirement, dict):
        return 1.0
    
    min_thresh = requirement.get('min', requirement.get('min_threshold', float('-inf')))
    max_thresh = requirement.get('max', requirement.get('max_threshold', float('inf')))
    fuzzy_range = requirement.get('fuzzy_range', 0.0)
    
    if value < min_thresh:
        if fuzzy_range > 0 and value >= min_thresh - fuzzy_range:
            return (value - (min_thresh - fuzzy_range)) / fuzzy_range
        return 0.0
    
    if value > max_thresh:
        if fuzzy_range > 0 and value <= max_thresh + fuzzy_range:
            return (max_thresh + fuzzy_range - value) / fuzzy_range
        return 0.0
    
    return 1.0


def score_archetype(champion_attrs, archetype_def):
    """Score champion's fit to an archetype."""
    requirements = archetype_def.get('requirements', {})
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for attr_name, requirement in requirements.items():
        value = champion_attrs.get(attr_name, 0.0)
        
        # Convert string values to float
        if isinstance(value, str):
            try:
                value = float(value)
            except (ValueError, TypeError):
                value = 0.0
        
        score = fuzzy_score(value, requirement)
        
        # Weight is inside the requirement dict in our format
        weight = requirement.get('weight', 1.0) if isinstance(requirement, dict) else 1.0
        
        weighted_sum += score * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0


def main():
    with open('data/processed/spell_based_attributes.json', 'r', encoding='utf-8') as f:
        champion_attrs = json.load(f)['attributes']
    
    with open('data/processed/archetype_definitions.json', 'r', encoding='utf-8') as f:
        archetypes = json.load(f)['archetypes']
    
    results = {}
    archetype_counts = {name: 0 for name in archetypes.keys()}
    
    print("=" * 70)
    print("Assigning Archetypes")
    print("=" * 70)
    
    for champ_name, champ_attrs in champion_attrs.items():
        scores = {}
        
        for archetype_name, archetype_def in archetypes.items():
            score = score_archetype(champ_attrs, archetype_def)
            scores[archetype_name] = score
        
        primary_name = max(scores, key=scores.get)
        primary_score = scores[primary_name]
        
        results[champ_name] = {
            'primary_archetype': primary_name,
            'primary_score': primary_score,
            'all_scores': scores,
            'attributes': champ_attrs
        }
        
        archetype_counts[primary_name] += 1
    
    output = {
        'metadata': {
            'total_champions': len(results),
            'archetypes': list(archetypes.keys())
        },
        'distribution': archetype_counts,
        'assignments': results
    }
    
    with open('data/processed/archetype_assignments.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nAssigned {len(results)} champions")
    print("\nArchetype Distribution:")
    for archetype, count in sorted(archetype_counts.items(), key=lambda x: -x[1]):
        pct = 100.0 * count / len(results)
        print(f"  {archetype:20s}: {count:3d} ({pct:5.1f}%)")
    
    print("\nSaved to: data/processed/archetype_assignments.json")


if __name__ == '__main__':
    main()
