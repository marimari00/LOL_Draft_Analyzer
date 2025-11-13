"""
Build spell database from wiki data (single source of truth).
Replaces the old champion.bin + Data Dragon mixed approach.
"""

import json
from pathlib import Path
from typing import Dict, List

def load_wiki_data() -> Dict:
    """Load champion ability data from wiki."""
    wiki_file = Path('data/processed/wiki_champion_data.json')
    with open(wiki_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_spell_database():
    """Build complete spell database from wiki data."""
    print("Loading wiki champion data...")
    wiki_data = load_wiki_data()
    
    spell_database = {}
    
    for champion_name, champ_data in wiki_data.items():
        print(f"Processing {champion_name}...")
        
        abilities = champ_data['abilities']
        
        for ability_key, ability_data in abilities.items():
            # Skip passive for now
            if ability_key == 'P':
                continue
            
            # Map ability key to spell index (Q=0, W=1, E=2, R=3)
            spell_index = {'Q': 0, 'W': 1, 'E': 2, 'R': 3}.get(ability_key)
            if spell_index is None:
                continue
            
            # Create spell ID
            spell_id = f"{champion_name}_{ability_key}"
            
            # Build spell entry with wiki damage data (single source of truth)
            spell_entry = {
                'champion': champion_name,
                'spell_key': ability_key,
                'name': ability_data.get('name', 'Unknown'),
                
                # Damage data from wiki (accurate!)
                'base_damage': ability_data.get('base_damage', []),
                'ad_ratio': ability_data.get('ad_ratio', 0.0),
                'bonus_ad_ratio': ability_data.get('bonus_ad_ratio', 0.0),
                'ap_ratio': ability_data.get('ap_ratio', 0.0),
                'total_ad_ratio': ability_data.get('ad_ratio', 0.0) + ability_data.get('bonus_ad_ratio', 0.0),
                
                # Cooldown from wiki
                'cooldown': ability_data.get('cooldown', []),
                'maxrank': len(ability_data.get('base_damage', [])) if ability_data.get('base_damage') else 5,
            }
            
            spell_database[spell_id] = spell_entry
    
    return spell_database

def main():
    print("="*60)
    print("Building spell database from wiki data...")
    print("="*60)
    
    spell_db = build_spell_database()
    
    # Save to file
    output_file = Path('data/processed/spell_database_wiki.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(spell_db, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✓ Saved {len(spell_db)} spells to {output_file}")
    print(f"{'='*60}")
    
    # Show sample: Braum Q
    if 'Braum_Q' in spell_db:
        braum_q = spell_db['Braum_Q']
        print(f"\nBraum Q (Winter's Bite):")
        print(f"  Base damage: {braum_q['base_damage']}")
        print(f"  Total AD ratio: {braum_q['total_ad_ratio']} (was 4.0 in old data!)")
        print(f"  Bonus AD ratio: {braum_q['bonus_ad_ratio']}")
        print(f"  AP ratio: {braum_q['ap_ratio']}")
    
    # Show sample: Caitlyn Q
    if 'Caitlyn_Q' in spell_db:
        cait_q = spell_db['Caitlyn_Q']
        print(f"\nCaitlyn Q (Piltover Peacemaker):")
        print(f"  Base damage: {cait_q['base_damage']}")
        print(f"  Total AD ratio: {cait_q['total_ad_ratio']}")
        print(f"  Bonus AD ratio: {cait_q['bonus_ad_ratio']}")
        print(f"  AP ratio: {cait_q['ap_ratio']}")

if __name__ == '__main__':
    main()
