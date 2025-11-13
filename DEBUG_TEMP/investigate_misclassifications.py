"""
Detailed investigation of the most egregious archetype misclassifications.
"""

import json

with open('data/processed/champion_archetypes.json', 'r') as f:
    data = json.load(f)

with open('data/processed/enhanced_attributes.json', 'r') as f:
    attributes = json.load(f)

assignments = data['assignments']

print("="*80)
print("DETAILED INVESTIGATION: MOST QUESTIONABLE CLASSIFICATIONS")
print("="*80)

# Most egregious cases to investigate
cases = [
    ("Jinx", "ADC classified as ENCHANTER", "marksman/hypercarry"),
    ("Ezreal", "ADC classified as BURST_ASSASSIN", "marksman"),
    ("Yuumi", "Enchanter classified as SPLIT_PUSHER", "enchanter"),
    ("Rammus", "Tank classified as CONTROL_MAGE", "engage_tank"),
    ("Zed", "Assassin classified as EARLY_GAME_BULLY", "burst_assassin"),
    ("Katarina", "Assassin classified as DIVER", "burst_assassin"),
    ("Malphite", "Tank classified as EARLY_GAME_BULLY", "engage_tank"),
    ("Orianna", "Control mage classified as ENCHANTER", "control_mage"),
]

for champ, issue, expected in cases:
    if champ not in assignments:
        continue
        
    info = assignments[champ]
    attrs = attributes.get(champ, {})
    
    print(f"\n{'='*80}")
    print(f"🔍 {champ}: {issue}")
    print(f"{'='*80}")
    
    print(f"\nPrimary: {info['primary_archetype']} (score: {info['primary_score']:.3f})")
    print(f"Expected: {expected}")
    
    # Show key attributes
    print(f"\nKey Attributes:")
    print(f"  damage_pattern: {attrs.get('damage_pattern', '?')}")
    print(f"  burst_pattern: {attrs.get('burst_pattern', 0):.3f}")
    print(f"  sustained_pattern: {attrs.get('sustained_pattern', 0):.3f}")
    print(f"  mobility_score: {attrs.get('mobility_score', 0):.3f}")
    print(f"  survivability_late: {attrs.get('survivability_late', 0):.3f}")
    print(f"  gold_dependency: {attrs.get('gold_dependency', 0):.3f}")
    print(f"  cc_score: {attrs.get('cc_score', 0):.3f}")
    print(f"  damage_early: {attrs.get('damage_early', 0):.3f}")
    print(f"  damage_mid: {attrs.get('damage_mid', 0):.3f}")
    print(f"  damage_late: {attrs.get('damage_late', 0):.3f}")
    
    # Show top 5 archetype matches
    print(f"\nTop 5 Archetype Matches:")
    for i, arch in enumerate(info['all_archetypes'][:5], 1):
        marker = "✓" if expected.lower() in arch['name'].lower() else " "
        print(f"  {marker} {i}. {arch['name']:20s}: {arch['score']:.3f}")
    
    # Find expected archetype
    print(f"\nExpected Archetype Scores:")
    for arch in info['all_archetypes']:
        if any(exp_word in arch['name'].lower() for exp_word in expected.lower().split('/')):
            print(f"  - {arch['name']:20s}: {arch['score']:.3f}")

print("\n" + "="*80)
print("PATTERN ANALYSIS")
print("="*80)

print("\n1. ALL ADCs ARE MISCLASSIFIED")
print("   - None classified as 'marksman' (only 2 champions total have marksman)")
print("   - 0 classified as 'hypercarry' (only 1 champion total has hypercarry)")
print("   - Issue: Likely archetype definitions too strict or missing key attributes")

print("\n2. MOST ASSASSINS ARE MISCLASSIFIED")
print("   - Zed, Talon, Katarina, Akali, etc. NOT burst_assassin")
print("   - They have high burst_pattern scores but classified as diver/early_game_bully")
print("   - Issue: Other archetypes may have overlapping criteria")

print("\n3. MANY TANKS ARE MISCLASSIFIED")
print("   - Malphite, Rammus, Braum, Cho'Gath NOT engage_tank")
print("   - Issue: May lack clear survivability + CC identifiers")

print("\n4. CONTROL MAGES ARE MISCLASSIFIED")
print("   - Only 3 control_mage total (should be ~15)")
print("   - Orianna, Syndra, Viktor, Azir all wrong")
print("   - Issue: control_mage definition may be too narrow")

print("\n5. MARKSMAN ARCHETYPE IS NEARLY EMPTY")
print("   - Only 2 champions as marksman (should be ~15)")
print("   - Issue: Gold dependency or sustained damage criteria too strict")

print("\n" + "="*80)
print("ROOT CAUSE HYPOTHESIS")
print("="*80)

print("\nThe issue is likely in config/archetypes_v2.json:")
print("1. Archetype criteria may be too strict (narrow ranges)")
print("2. Missing key differentiating attributes")
print("3. Weight/priority issues - generic archetypes winning over specific ones")
print("4. 'early_game_bully', 'enchanter', 'diver' may be too broadly defined")
print("\nSuggested fixes:")
print("- Widen ranges for marksman gold_dependency")
print("- Add damage_type attribute (physical vs magic)")
print("- Add class hints (Fighter, Mage, Marksman, Support, Tank)")
print("- Adjust archetype weights or use hierarchical classification")
