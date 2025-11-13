"""Validate synergy matrix against known team compositions."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_pipeline.score_team_composition import (
    score_team_synergy, 
    analyze_team_composition,
    load_relationships
)


def validate_known_compositions():
    """Test synergy scoring against known strong/weak compositions."""
    
    synergy_matrix, _ = load_relationships()
    
    print("="*70)
    print("SYNERGY MATRIX VALIDATION")
    print("="*70)
    
    # Known strong compositions (should have high synergy)
    strong_comps = {
        "Protect the Kog": {
            "champions": ['Leona', 'KogMaw', 'Lulu', 'Orianna', 'Braum'],
            "expected": "High synergy (>0.5)",
            "reasoning": "Frontline + marksman + enchanter + peel"
        },
        "Dive Squad": {
            "champions": ['Vi', 'Zed', 'Diana', 'Yasuo', 'Leona'],
            "expected": "High synergy (>0.5)",
            "reasoning": "Multiple dive threats + engage"
        },
        "Poke Comp": {
            "champions": ['Xerath', 'Caitlyn', 'Janna', 'Lux', 'Thresh'],
            "expected": "Moderate synergy (>0.3)",
            "reasoning": "Poke + disengage + waveclear"
        }
    }
    
    # Known weak compositions (should have low/negative synergy)
    weak_comps = {
        "5 Assassins": {
            "champions": ['Zed', 'Talon', 'Akali', 'Katarina', 'Evelynn'],
            "expected": "Low synergy (<0.5)",
            "reasoning": "No frontline, no peel, all squishy"
        },
        "5 Tanks": {
            "champions": ['Leona', 'Braum', 'Alistar', 'Nautilus', 'Maokai'],
            "expected": "Moderate synergy (overlapping roles)",
            "reasoning": "All engage/peel, no damage threats"
        }
    }
    
    print("\n" + "="*70)
    print("STRONG COMPOSITIONS (Should have high synergy)")
    print("="*70)
    
    for name, comp in strong_comps.items():
        analysis = analyze_team_composition(comp['champions'])
        
        print(f"\n{name}")
        print(f"  Champions: {', '.join(comp['champions'])}")
        print(f"  Archetypes: {', '.join(analysis['archetypes'])}")
        print(f"  Composition Type: {analysis['composition_type']}")
        print(f"  Synergy Score: {analysis['synergy_score']:.3f}")
        print(f"  Expected: {comp['expected']}")
        print(f"  Reasoning: {comp['reasoning']}")
        
        if analysis['synergy_score'] >= 0.5:
            print(f"  ✓ PASS - High synergy detected")
        else:
            print(f"  ✗ FAIL - Expected high synergy, got {analysis['synergy_score']:.3f}")
    
    print("\n" + "="*70)
    print("WEAK COMPOSITIONS (Should have low synergy)")
    print("="*70)
    
    for name, comp in weak_comps.items():
        analysis = analyze_team_composition(comp['champions'])
        
        print(f"\n{name}")
        print(f"  Champions: {', '.join(comp['champions'])}")
        print(f"  Archetypes: {', '.join(analysis['archetypes'])}")
        print(f"  Composition Type: {analysis['composition_type']}")
        print(f"  Synergy Score: {analysis['synergy_score']:.3f}")
        print(f"  Expected: {comp['expected']}")
        print(f"  Reasoning: {comp['reasoning']}")
        
        if analysis['synergy_score'] < 0.5:
            print(f"  ✓ PASS - Low synergy detected")
        else:
            print(f"  ⚠ WARNING - Expected low synergy, got {analysis['synergy_score']:.3f}")


def validate_specific_synergies():
    """Test specific archetype pair synergies."""
    
    synergy_matrix, _ = load_relationships()
    
    print("\n" + "="*70)
    print("SPECIFIC SYNERGY VALIDATION")
    print("="*70)
    
    # Known strong synergies
    strong_pairs = [
        ("marksman", "engage_tank", 2, "Tank protects marksman"),
        ("marksman", "enchanter", 2, "Enchanter enables marksman"),
        ("burst_assassin", "diver", 2, "Multiple dive threats"),
        ("burst_mage", "engage_tank", 2, "CC setup for burst"),
    ]
    
    # Known weak synergies
    weak_pairs = [
        ("marksman", "burst_assassin", -1, "Both squishy, need peel"),
        ("engage_tank", "warden", -1, "Overlapping tank roles"),
        ("enchanter", "catcher", -1, "Overlapping support roles"),
    ]
    
    print("\nStrong Synergies (Expected +2):")
    for arch1, arch2, expected, reason in strong_pairs:
        actual = synergy_matrix.get(arch1, {}).get(arch2, 0)
        status = "✓" if actual == expected else "✗"
        print(f"  {status} {arch1:15s} + {arch2:15s} = {actual:2d} (expected {expected:2d}) - {reason}")
    
    print("\nWeak/Anti-Synergies (Expected -1):")
    for arch1, arch2, expected, reason in weak_pairs:
        actual = synergy_matrix.get(arch1, {}).get(arch2, 0)
        status = "✓" if actual == expected else "✗"
        print(f"  {status} {arch1:15s} + {arch2:15s} = {actual:2d} (expected {expected:2d}) - {reason}")


def validate_counter_relationships():
    """Test specific counter relationships."""
    
    _, counter_matrix = load_relationships()
    
    print("\n" + "="*70)
    print("COUNTER RELATIONSHIP VALIDATION")
    print("="*70)
    
    # Known hard counters
    hard_counters = [
        ("burst_assassin", "marksman", 2, "Assassin deletes immobile marksman"),
        ("warden", "burst_assassin", 2, "Warden negates assassin burst"),
        ("warden", "burst_mage", 2, "Shields block burst damage"),
    ]
    
    # Known soft counters
    soft_counters = [
        ("engage_tank", "marksman", 1, "Tank can reach backline"),
        ("catcher", "marksman", 1, "Hook = death for immobile ADC"),
    ]
    
    print("\nHard Counters (Expected +2):")
    for arch1, arch2, expected, reason in hard_counters:
        actual = counter_matrix.get(arch1, {}).get(arch2, 0)
        status = "✓" if actual == expected else "✗"
        print(f"  {status} {arch1:15s} counters {arch2:15s} = {actual:2d} (expected {expected:2d})")
        print(f"     → {reason}")
    
    print("\nSoft Counters (Expected +1):")
    for arch1, arch2, expected, reason in soft_counters:
        actual = counter_matrix.get(arch1, {}).get(arch2, 0)
        status = "✓" if actual == expected else "✗"
        print(f"  {status} {arch1:15s} counters {arch2:15s} = {actual:2d} (expected {expected:2d})")
        print(f"     → {reason}")


if __name__ == '__main__':
    validate_known_compositions()
    validate_specific_synergies()
    validate_counter_relationships()
    
    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70)
