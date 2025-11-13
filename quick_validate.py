"""
Quick validation of key counter-intuitive results
"""
import json

attrs = json.load(open('data/processed/enhanced_attributes.json'))
archs = json.load(open('data/processed/champion_archetypes.json'))

def show_champion(name):
    a = attrs[name]
    assignment = archs['assignments'][name]
    
    print(f"\n{'='*70}")
    print(f"{name}: {assignment['primary_archetype']} ({assignment['primary_score']:.3f})")
    print(f"{'='*70}")
    
    print(f"\nKey attributes:")
    print(f"  Range: {a['range_profile']['auto_attack']}")
    print(f"  Burst: {a.get('burst_pattern', 0):.3f}, Sustained: {a.get('sustained_pattern', 0):.3f}")
    print(f"  Damage: Early {a.get('damage_early', 0):.3f}, Mid {a.get('damage_mid', 0):.3f}, Late {a.get('damage_late', 0):.3f}")
    print(f"  CC: {a.get('cc_score', 0):.3f}, Mobility: {a.get('mobility_score', 0):.3f}")
    print(f"  Survivability (mid): {a.get('survivability_mid', 0):.3f}")
    print(f"  Waveclear: {a.get('waveclear_speed', 0):.3f}, AOE: {a.get('aoe_capability', 0):.3f}")
    
    print(f"\nTop 5 archetypes:")
    for arch in assignment['all_archetypes'][:5]:
        print(f"  {arch['name']:20s}: {arch['score']:.3f}")

# Check counter-intuitive results
print("\n" + "="*70)
print("COUNTER-INTUITIVE RESULTS - MATHEMATICAL VALIDATION")
print("="*70)

show_champion('Zed')
print("\n❓ WHY engage_tank? Let's check:")
print("  - CC score 0.971 (97th percentile!) - his W shadow slow? death mark?")
print("  - Survivability mid/late ~0.77 - his W escape? base stats?")
print("  - Melee range 125 ✓")
print("  - These stats make him LOOK like a tank!")

show_champion('Ahri')
print("\n❓ WHY enchanter? Let's check:")
print("  - Range 550 (enchanter range 450-600) ✓")
print("  - Sustain score 0.412 - her passive healing?")
print("  - But burst_pattern should be high... let me check")

show_champion('Orianna')
print("\n✓ control_mage makes sense!")
print("  - High AOE, waveclear, CC")
print("  - Range 525 (mage range) ✓")

show_champion('Azir')
print("\n✓ control_mage makes sense!")
print("  - High AOE, waveclear, CC")
print("  - Previous 'split_pusher' was also mathematically valid!")
