"""
Merge effect_burn damage patches into champion_damage_data.json.
This supplements missing damage data from champion.bin.
"""

import json
from pathlib import Path


def merge_damage_patches():
    # Load original champion.bin data
    bin_path = Path("data/raw/champion_damage_data.json")
    with open(bin_path, encoding='utf-8') as f:
        bin_data = json.load(f)
    
    # Load effect_burn patches
    patch_path = Path("data/processed/effect_burn_damage_patches.json")
    with open(patch_path, encoding='utf-8') as f:
        patch_data = json.load(f)
    
    patches = patch_data['patches']
    
    # Merge patches
    merged_count = 0
    
    print("=" * 70)
    print("Merging effect_burn patches into champion damage data")
    print("=" * 70)
    
    for champ_name, champ_patches in patches.items():
        if champ_name not in bin_data['champions']:
            print(f"Warning: {champ_name} not in champion.bin data")
            continue
        
        if 'spells' not in bin_data['champions'][champ_name]:
            bin_data['champions'][champ_name]['spells'] = {}
        
        champ_spells = bin_data['champions'][champ_name]['spells']
        
        for spell_key, spell_patch in champ_patches.items():
            # Only add if spell is completely missing
            if spell_key not in champ_spells:
                champ_spells[spell_key] = {
                    'name': spell_patch.get('name', spell_key),
                    'base_damage': spell_patch.get('base_damage', []),
                    'ad_ratio': spell_patch.get('ad_ratio', 0.0),
                    'ap_ratio': spell_patch.get('ap_ratio', 0.0),
                    'bonus_ad_ratio': 0.0,
                    'cooldown': spell_patch.get('cooldown', []),
                    'source': 'effect_burn_extraction'
                }
                merged_count += 1
                print(f"Added {champ_name} {spell_key}: {spell_patch.get('name')}")
    
    # Save merged data
    output_path = Path("data/processed/champion_damage_data_merged.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(bin_data, f, indent=2)
    
    print(f"\n{merged_count} abilities merged")
    print(f"Saved to: {output_path}")


if __name__ == '__main__':
    merge_damage_patches()
