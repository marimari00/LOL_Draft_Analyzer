"""
Filter false positive damage from champion_damage_data_patched.json.

Strategy:
1. Load Data Dragon descriptions for context
2. For each spell with damage, check if it's likely a false positive:
   - Description contains utility keywords (wall, frost, slow, stealth, etc.)
   - Base damage values are suspiciously high (>500) for non-ultimate
   - Damage values match common utility numbers (70, 80, 100, 200, etc.)
3. Set base_damage to [] for false positives
4. Output filtered data to champion_damage_data_filtered.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set

# Utility keywords that indicate non-damage abilities
UTILITY_KEYWORDS = {
    # CC/Debuff keywords
    'frost', 'chill', 'freeze', 'slow', 'stun', 'root',
    # Visibility keywords
    'stealth', 'invisible', 'hidden', 'reveal', 'vision',
    # Movement keywords (non-damage)
    'speed', 'movement', 'accelerate', 'dash', 'leap',
    # Structure/terrain keywords
    'wall', 'terrain', 'impassable', 'block',
    # Resource/mechanic keywords
    'stack', 'charge', 'resource', 'mana', 'energy',
    # Duration keywords (often extracted as damage)
    'duration', 'lasting', 'persist',
    # Percentage values (often extracted as base damage)
    'percent', '%', 'percentage'
}

# Champions with known false positive extractions
# Format: {champion: {spell_key: reason}}
KNOWN_FALSE_POSITIVES = {
    'Sejuani': {'E': 'frost stack buildup, not damage'},
    'Anivia': {'W': 'wall duration/size, not damage'},
    'Karthus': {'W': 'slow percentage, not damage'},
    'Azir': {'R': 'wall range, not damage'},
    'Twitch': {'Q': 'stealth duration, not damage'},
    'Caitlyn': {'W': 'trap arm time, not damage'},
    'Draven': {'W': 'movement speed buff, not damage'},
    'Teemo': {'Q': 'blind duration, not damage'},
}


def should_filter_damage(champ_name: str, spell_key: str, spell_data: Dict, 
                        description: str) -> tuple[bool, str]:
    """
    Determine if damage values should be filtered.
    
    Returns:
        (should_filter, reason)
    """
    # Check known false positives first
    if champ_name in KNOWN_FALSE_POSITIVES:
        if spell_key in KNOWN_FALSE_POSITIVES[champ_name]:
            return True, KNOWN_FALSE_POSITIVES[champ_name][spell_key]
    
    base_damage = spell_data.get('base_damage', [])
    if not base_damage:
        return False, ""
    
    max_damage = max(base_damage)
    desc_lower = description.lower() if description else ""
    
    # Rule 1: Extremely high damage for non-ultimate (likely range/duration)
    if spell_key != 'R' and max_damage > 800:
        return True, f"non-ult with {max_damage} damage (likely range/duration)"
    
    # Rule 2: Description contains utility keywords
    utility_matches = [kw for kw in UTILITY_KEYWORDS if kw in desc_lower]
    if utility_matches:
        # Check if damage seems plausible despite keywords
        # E.g., "slows and deals damage" is OK, but "creates wall" is not
        damage_keywords = ['deal', 'damage', 'strike', 'hit', 'attack']
        has_damage_context = any(kw in desc_lower for kw in damage_keywords)
        
        # If it has strong utility keywords but weak damage context, filter it
        strong_utility = any(kw in desc_lower for kw in ['wall', 'invisible', 'block', 'terrain'])
        if strong_utility and not has_damage_context:
            return True, f"utility ability: {', '.join(utility_matches[:3])}"
    
    # Rule 3: Suspiciously round numbers at high values (often config values)
    if max_damage in [800, 1000, 1200, 1500, 2000, 2500, 3000]:
        if spell_key != 'R':  # Ults can have round numbers
            return True, f"suspicious round number: {max_damage}"
    
    return False, ""


def filter_damage_data():
    """Filter false positive damage from champion data."""
    print("=" * 70)
    print("Filtering False Positive Damage")
    print("=" * 70)
    
    # Load data
    with open('data/processed/champion_damage_data_patched.json', 'r', encoding='utf-8') as f:
        damage_data = json.load(f)
    
    with open('data/raw/data_dragon_champions.json', 'r', encoding='utf-8') as f:
        dd_data = json.load(f)['champions']
    
    filtered_count = 0
    filter_log = []
    
    # Process each champion
    for champ_name, champ_data in damage_data['champions'].items():
        if champ_name not in dd_data:
            continue
        
        dd_abilities = dd_data[champ_name].get('abilities', {})
        
        for spell_key, spell_data in champ_data['spells'].items():
            # Get description for context
            description = ""
            if spell_key in dd_abilities:
                description = dd_abilities[spell_key].get('description', '')
            
            # Check if should filter
            should_filter, reason = should_filter_damage(
                champ_name, spell_key, spell_data, description
            )
            
            if should_filter:
                # Clear damage data
                spell_data['base_damage'] = []
                spell_data['ad_ratio'] = 0.0
                spell_data['ap_ratio'] = 0.0
                spell_data['bonus_ad_ratio'] = 0.0
                
                filtered_count += 1
                filter_log.append(f"{champ_name:12s} {spell_key}: {reason}")
    
    # Save filtered data
    output_path = Path('data/processed/champion_damage_data_filtered.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(damage_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nFiltered {filtered_count} false positive abilities")
    print(f"\nFiltered abilities:")
    for log in filter_log[:20]:  # Show first 20
        print(f"  {log}")
    if len(filter_log) > 20:
        print(f"  ... and {len(filter_log) - 20} more")
    
    print(f"\nSaved to: {output_path}")
    
    return filtered_count


if __name__ == '__main__':
    filter_damage_data()
