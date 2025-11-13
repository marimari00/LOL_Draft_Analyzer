"""
Apply manual damage patches to champion_damage_data_merged.json.
This adds/replaces damage data for abilities that are missing or incorrect.
"""

import json
from pathlib import Path


def apply_manual_patches():
    # Load merged damage data
    merged_path = Path("data/processed/champion_damage_data_merged.json")
    with open(merged_path, 'r', encoding='utf-8') as f:
        merged_data = json.load(f)
    
    # Load manual patches
    patches_path = Path("data/processed/manual_damage_patches.json")
    with open(patches_path, 'r', encoding='utf-8') as f:
        patches_data = json.load(f)
    
    patches = patches_data['patches']
    
    print("=" * 70)
    print("Applying Manual Damage Patches")
    print("=" * 70)
    
    patched_count = 0
    
    for champ_name, champ_patches in patches.items():
        if champ_name not in merged_data['champions']:
            print(f"Warning: {champ_name} not in champion data")
            continue
        
        if 'spells' not in merged_data['champions'][champ_name]:
            merged_data['champions'][champ_name]['spells'] = {}
        
        champ_spells = merged_data['champions'][champ_name]['spells']
        
        for spell_key, spell_patch in champ_patches.items():
            # Replace or add the spell data
            champ_spells[spell_key] = {
                'name': spell_patch.get('name', spell_key),
                'base_damage': spell_patch.get('base_damage', []),
                'ad_ratio': spell_patch.get('ad_ratio', 0.0),
                'ap_ratio': spell_patch.get('ap_ratio', 0.0),
                'bonus_ad_ratio': spell_patch.get('bonus_ad_ratio', 0.0),
                'cooldown': spell_patch.get('cooldown', []),
                'source': 'manual_patch'
            }
            patched_count += 1
            
            base = spell_patch.get('base_damage', [])
            base_str = f"{base[0]}-{base[-1]}" if base else "0"
            ad_ratio = spell_patch.get('ad_ratio', 0)
            bonus_ad_ratio = spell_patch.get('bonus_ad_ratio', 0)
            
            ratio_str = ""
            if ad_ratio > 0:
                ratio_str = f" + {ad_ratio:.1f} AD"
            elif bonus_ad_ratio > 0:
                ratio_str = f" + {bonus_ad_ratio:.1f} bonus AD"
            
            print(f"Patched {champ_name} {spell_key}: {base_str}{ratio_str}")
    
    # Save patched data
    output_path = Path("data/processed/champion_damage_data_patched.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2)
    
    print(f"\n{patched_count} abilities patched")
    print(f"Saved to: {output_path}")


if __name__ == '__main__':
    apply_manual_patches()
