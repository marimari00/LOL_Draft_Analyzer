"""Define archetype attributes for granular analysis.

Instead of treating archetypes as atomic units, we break them down into
fundamental attributes. This allows us to discover WHY certain combinations work.

Example: "burst_assassin + burst_assassin" has 70% WR not because of the archetype,
but because: high_mobility + backline_access + burst_damage synergize well.
"""

import json
from typing import Dict, List

# Define all possible attributes
ARCHETYPE_ATTRIBUTES = {
    # Damage attributes
    'damage_physical': 'Primary damage is physical',
    'damage_magic': 'Primary damage is magic',
    'damage_mixed': 'Deals both physical and magic damage',
    'damage_true': 'Has true damage in kit',
    'damage_burst': 'Delivers damage in short windows',
    'damage_sustained': 'Consistent damage over time',
    'damage_aoe': 'Strong area-of-effect damage',
    'damage_single_target': 'Focused on single targets',
    
    # Range attributes
    'range_melee': 'Melee range (<200)',
    'range_short': 'Short range (200-500)',
    'range_medium': 'Medium range (500-600)',
    'range_long': 'Long range (>600)',
    
    # Mobility attributes
    'mobility_high': 'Multiple dashes/blinks',
    'mobility_medium': 'Single dash or movement speed',
    'mobility_low': 'Limited mobility',
    'mobility_stealth': 'Has stealth/invisibility',
    
    # Engage pattern
    'engage_dive': 'Dives into enemy team',
    'engage_flank': 'Flanks from side/back',
    'engage_frontline': 'Fights from front',
    'engage_backline_access': 'Can reach enemy carries',
    'engage_zone_control': 'Controls areas',
    
    # Survivability
    'survive_tank': 'High base HP/resistances',
    'survive_shields': 'Has shields in kit',
    'survive_sustain': 'Has healing/lifesteal',
    'survive_mobility': 'Survives via mobility',
    'survive_range': 'Survives by staying far',
    
    # Utility/CC
    'cc_hard': 'Has hard CC (stun/root/suppress)',
    'cc_soft': 'Has soft CC (slow/silence/ground)',
    'cc_aoe': 'AoE crowd control',
    'cc_single': 'Single-target CC',
    'utility_peel': 'Protects allies',
    'utility_engage': 'Initiates fights',
    'utility_vision': 'Provides vision control',
    'utility_terrain': 'Creates/destroys terrain',
    
    # Scaling
    'scaling_early': 'Strong early game (levels 1-6)',
    'scaling_mid': 'Power spike mid game (7-13)',
    'scaling_late': 'Scales into late game (14+)',
    'scaling_items': 'Item-dependent power',
    'scaling_levels': 'Level-dependent power',
    
    # Role flexibility
    'flexible_multi_role': 'Can play multiple roles',
    'flexible_multi_lane': 'Can play multiple lanes',
    
    # Special mechanics
    'special_reset': 'Has reset mechanics',
    'special_execute': 'Has execute abilities',
    'special_global': 'Has global abilities',
    'special_transformation': 'Has transformation',
}


# Map each archetype to its attributes
ARCHETYPE_ATTRIBUTE_MAP = {
    'marksman': [
        'damage_physical', 'damage_sustained', 'damage_single_target',
        'range_long', 'mobility_low', 'engage_backline_access',
        'survive_range', 'scaling_late', 'scaling_items',
    ],
    
    'burst_assassin': [
        'damage_physical', 'damage_burst', 'damage_single_target',
        'range_melee', 'mobility_high', 'engage_dive', 'engage_flank', 'engage_backline_access',
        'survive_mobility', 'scaling_mid', 'scaling_items',
        'special_reset',
    ],
    
    'skirmisher': [
        'damage_physical', 'damage_sustained', 'damage_single_target',
        'range_melee', 'mobility_high', 'engage_dive',
        'survive_mobility', 'survive_sustain', 'scaling_items',
    ],
    
    'diver': [
        'damage_physical', 'damage_sustained', 'damage_aoe',
        'range_melee', 'mobility_medium', 'engage_dive', 'engage_backline_access',
        'survive_tank', 'survive_shields', 'cc_hard', 'cc_aoe',
        'utility_engage', 'scaling_mid',
    ],
    
    'juggernaut': [
        'damage_physical', 'damage_sustained', 'damage_aoe',
        'range_melee', 'mobility_low', 'engage_frontline',
        'survive_tank', 'survive_sustain', 'cc_soft',
        'scaling_items', 'scaling_levels',
    ],
    
    'engage_tank': [
        'damage_physical', 'damage_magic', 'damage_aoe',
        'range_melee', 'mobility_medium', 'engage_dive', 'engage_frontline',
        'survive_tank', 'survive_shields', 'cc_hard', 'cc_aoe',
        'utility_engage', 'utility_peel', 'scaling_early', 'scaling_mid',
    ],
    
    'warden': [
        'damage_physical', 'damage_magic', 'damage_sustained',
        'range_melee', 'range_short', 'mobility_low', 'engage_frontline',
        'survive_tank', 'survive_shields', 'cc_hard', 'cc_single',
        'utility_peel', 'scaling_levels',
    ],
    
    'burst_mage': [
        'damage_magic', 'damage_burst', 'damage_aoe',
        'range_medium', 'range_long', 'mobility_low', 'engage_zone_control',
        'survive_range', 'cc_hard', 'cc_aoe',
        'scaling_mid', 'scaling_items',
    ],
    
    'battle_mage': [
        'damage_magic', 'damage_sustained', 'damage_aoe',
        'range_short', 'range_medium', 'mobility_medium', 'engage_frontline', 'engage_zone_control',
        'survive_tank', 'survive_sustain', 'cc_soft', 'cc_aoe',
        'scaling_items', 'scaling_levels',
    ],
    
    'artillery_mage': [
        'damage_magic', 'damage_burst', 'damage_aoe',
        'range_long', 'mobility_low', 'engage_zone_control',
        'survive_range', 'cc_soft', 'cc_aoe',
        'scaling_late', 'scaling_items',
    ],
    
    'enchanter': [
        'damage_magic', 'damage_sustained', 'damage_single_target',
        'range_medium', 'range_long', 'mobility_low', 'engage_backline_access',
        'survive_range', 'utility_peel', 'utility_vision',
        'scaling_items',
    ],
    
    'catcher': [
        'damage_magic', 'damage_burst', 'damage_single_target',
        'range_medium', 'range_long', 'mobility_low', 'engage_zone_control',
        'survive_range', 'cc_hard', 'cc_single', 'cc_aoe',
        'utility_engage', 'utility_peel', 'utility_vision',
        'scaling_early', 'scaling_mid',
    ],
    
    'specialist': [
        'damage_mixed', 'damage_sustained',
        'range_medium', 'mobility_medium',
        'survive_mobility', 'flexible_multi_role', 'flexible_multi_lane',
        'special_transformation', 'special_global',
    ],
}


def add_attributes_to_champions():
    """Add attribute tags to champion archetype data."""
    # Load existing champion data
    with open('data/processed/champion_archetypes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    champions = data['assignments']
    
    # Add attributes to each champion based on their archetype
    for champ_name, champ_data in champions.items():
        archetype = champ_data['primary_archetype']
        
        if archetype in ARCHETYPE_ATTRIBUTE_MAP:
            champ_data['attributes'] = ARCHETYPE_ATTRIBUTE_MAP[archetype]
        else:
            print(f"⚠ No attributes defined for archetype: {archetype}")
            champ_data['attributes'] = []
    
    # Save updated data
    with open('data/processed/champion_archetypes.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Added attributes to {len(champions)} champions")
    
    # Show examples
    print("\nExample attribute assignments:")
    examples = ['Zed', 'Jinx', 'Leona', 'Orianna', 'Darius']
    for champ in examples:
        if champ in champions:
            attrs = champions[champ]['attributes']
            print(f"\n{champ} ({champions[champ]['primary_archetype']}):")
            for attr in attrs[:5]:  # Show first 5
                print(f"  - {attr}")
            if len(attrs) > 5:
                print(f"  ... and {len(attrs) - 5} more")


def save_attribute_definitions():
    """Save attribute definitions to file for reference."""
    output = {
        'metadata': {
            'description': 'Champion archetype attributes for granular synergy analysis',
            'total_attributes': len(ARCHETYPE_ATTRIBUTES),
        },
        'attributes': ARCHETYPE_ATTRIBUTES,
        'archetype_profiles': ARCHETYPE_ATTRIBUTE_MAP,
    }
    
    with open('data/processed/archetype_attributes.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Saved {len(ARCHETYPE_ATTRIBUTES)} attribute definitions")


if __name__ == '__main__':
    print("="*70)
    print("DEFINING ARCHETYPE ATTRIBUTES")
    print("="*70)
    
    save_attribute_definitions()
    add_attributes_to_champions()
    
    print("\n✓ Attribute system ready for analysis")
