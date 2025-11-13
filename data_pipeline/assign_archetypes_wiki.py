"""
Assign archetypes to champions using wiki data (single source of truth).
"""

import json
from pathlib import Path

def fuzzy_score(value, requirement):
    """Calculate fuzzy membership score."""
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
        
        # Handle categorical requirements (e.g., damage_profile)
        if isinstance(requirement, dict) and 'allowed' in requirement:
            allowed_values = requirement['allowed']
            if value in allowed_values:
                score = 1.0
            else:
                score = 0.0
            weight = requirement.get('weight', 1.0)
            weighted_sum += score * weight
            total_weight += weight
            continue
        
        # Convert string values to float
        if isinstance(value, str):
            try:
                value = float(value)
            except (ValueError, TypeError):
                value = 0.0
        
        score = fuzzy_score(value, requirement)
        weight = requirement.get('weight', 1.0) if isinstance(requirement, dict) else 1.0
        
        weighted_sum += score * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0


def main():
    print("="*60)
    print("Assigning Archetypes (Wiki Data)")
    print("="*60)
    
    # Load wiki-based attributes
    with open('data/processed/spell_based_attributes_wiki.json', 'r', encoding='utf-8') as f:
        champion_attrs = json.load(f)['attributes']
    
    # Load archetype definitions
    with open('data/processed/archetype_definitions.json', 'r', encoding='utf-8') as f:
        archetypes = json.load(f)['archetypes']
    
    results = {}
    archetype_counts = {name: 0 for name in archetypes.keys()}
    
    for champ_name, champ_attrs in champion_attrs.items():
        scores = {}
        
        for archetype_name, archetype_def in archetypes.items():
            score = score_archetype(champ_attrs, archetype_def)
            scores[archetype_name] = score
        
        # Find max score
        max_score = max(scores.values())
        tied_archetypes = [name for name, score in scores.items() if score == max_score]
        
        # Tiebreaker: marksman preference only if truly marksman-like
        if (len(tied_archetypes) > 1 and 'marksman' in tied_archetypes and 
            scores['marksman'] >= 0.95 and champ_attrs.get('sustained_dps', 0) >= 119.2):
            primary_name = 'marksman'
        else:
            primary_name = max(scores, key=scores.get)
        
        primary_score = scores[primary_name]
        
        results[champ_name] = {
            'primary_archetype': primary_name,
            'primary_score': primary_score,
            'all_scores': scores,
            'attributes': champ_attrs
        }
        
        archetype_counts[primary_name] += 1
    
    # Save results
    output = {
        'metadata': {
            'source': 'spell_based_attributes_wiki.json',
            'note': 'Uses clean wiki data - fixes Braum false positive',
            'total_champions': len(results),
            'archetypes': list(archetypes.keys())
        },
        'distribution': archetype_counts,
        'assignments': results
    }
    
    with open('data/processed/archetype_assignments_wiki.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Assigned {len(results)} champions")
    print("\nArchetype Distribution:")
    for archetype, count in sorted(archetype_counts.items(), key=lambda x: -x[1]):
        pct = 100.0 * count / len(results)
        print(f"  {archetype:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Show marksmen assignments
    marksmen = [name for name, data in results.items() 
                if data['primary_archetype'] == 'marksman']
    
    print(f"\n{'='*60}")
    print(f"Marksmen ({len(marksmen)}):")
    print('='*60)
    for marksman in sorted(marksmen):
        attrs = results[marksman]['attributes']
        score = results[marksman]['primary_score']
        print(f"  {marksman:15s}: DPS={attrs['sustained_dps']:6.1f}, "
              f"AD_ratio={attrs['total_ad_ratio']:4.2f}, score={score:.3f}")
    
    # Check if Braum is classified as marksman
    if 'Braum' in results:
        braum_arch = results['Braum']['primary_archetype']
        if braum_arch == 'marksman':
            print(f"\n⚠️  WARNING: Braum still classified as marksman!")
        else:
            print(f"\n✓ Braum correctly classified as: {braum_arch}")
    
    print(f"\nSaved to: data/processed/archetype_assignments_wiki.json")


if __name__ == '__main__':
    main()
