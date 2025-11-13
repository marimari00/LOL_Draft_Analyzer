"""
Parse Data Dragon effect_burn arrays to extract damage values.
effect_burn contains ability scaling values indexed by effect slot.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class DataDragonDamageExtractor:
    """Extract damage from Data Dragon effect_burn arrays."""
    
    def __init__(self, raw_dir: str = "data/raw"):
        self.raw_dir = Path(raw_dir)
        
        with open(self.raw_dir / "data_dragon_champions.json", "r", encoding="utf-8") as f:
            self.dd_data = json.load(f)["champions"]
        
        with open(self.raw_dir / "champion_damage_data.json", "r", encoding="utf-8") as f:
            self.bin_data = json.load(f)["champions"]
    
    def parse_effect_burn(self, effect_burn: List, description: str, ability_name: str = "") -> Optional[Dict]:
        """
        Parse effect_burn array to find damage values and ratios.
        
        Strategy: If effect_burn has any numeric progressions (5-rank arrays), 
        assume the highest values are base damage, lower values are ratios.
        This is more aggressive but necessary because Data Dragon descriptions
        don't always explicitly mention "damage" (e.g., Lucian Q).
        """
        if not effect_burn:
            return None
        
        # Find effect_burn slots with numeric progressions
        base_damage_candidates = []
        ratio_candidates = []
        
        for idx, value in enumerate(effect_burn):
            if value and isinstance(value, str) and value != '0':
                # Parse "70/110/150/190/230" format
                if '/' in value:
                    try:
                        numbers = [float(x) for x in value.split('/')]
                        # Must have 5 ranks (Q/W/E/R level 1-5)
                        if len(numbers) == 5:
                            # Heuristic: base damage usually > 5, ratios usually < 5
                            if max(numbers) > 5:
                                base_damage_candidates.append({
                                    'slot': idx,
                                    'values': numbers,
                                    'max_value': max(numbers)
                                })
                            elif max(numbers) <= 5 and min(numbers) >= 0.5:
                                # Likely a ratio (0.5-5.0 range)
                                ratio_candidates.append({
                                    'slot': idx,
                                    'values': numbers,
                                    'avg_value': sum(numbers) / len(numbers)
                                })
                    except ValueError:
                        pass
        
        # Pick highest base damage
        result = {}
        if base_damage_candidates:
            best_base = max(base_damage_candidates, key=lambda x: x['max_value'])
            result['base_damage'] = best_base['values']
            result['effect_slot'] = best_base['slot']
        
        # Pick ratio if exists (assume AD ratio for now, could be refined)
        if ratio_candidates:
            best_ratio = max(ratio_candidates, key=lambda x: x['avg_value'])
            result['ad_ratio'] = best_ratio['values'][-1]  # Use max rank ratio
            result['ratio_slot'] = best_ratio['slot']
        
        if result:
            result['source'] = 'effect_burn_extraction'
            return result
        
        return None
    
    def extract_missing_damage(self) -> Dict:
        """
        Extract damage for abilities missing in champion.bin.
        Returns dict of {champion_name: {spell_key: damage_data}}
        """
        extracted = {}
        
        print("=" * 70)
        print("Extracting damage from Data Dragon effect_burn")
        print("=" * 70)
        
        for champ_name, dd_champ in self.dd_data.items():
            if champ_name not in self.bin_data:
                continue
            
            bin_spells = self.bin_data[champ_name].get('spells', {})
            dd_abilities = dd_champ.get('abilities', {})
            
            champ_extracted = {}
            
            for spell_key in ['Q', 'W', 'E', 'R']:
                # Check if spell key exists in champion.bin at all
                bin_missing = spell_key not in bin_spells
                
                # Try to extract from Data Dragon if spell is completely missing
                if bin_missing and spell_key in dd_abilities:
                    dd_ability = dd_abilities[spell_key]
                    
                    effect_burn = dd_ability.get('effect_burn', [])
                    description = dd_ability.get('description', '')
                    cooldown = dd_ability.get('cooldown', [])
                    ability_name = dd_ability.get('name', spell_key)
                    
                    damage_data = self.parse_effect_burn(effect_burn, description, ability_name)
                    
                    if damage_data:
                        champ_extracted[spell_key] = {
                            'name': dd_ability.get('name', spell_key),
                            'cooldown': cooldown,
                            **damage_data
                        }
            
            if champ_extracted:
                extracted[champ_name] = champ_extracted
        
        return extracted
    
    def save_patches(self, extracted: Dict, output_file: Path):
        """Save extracted damage as patch file."""
        
        patch_count = sum(len(spells) for spells in extracted.values())
        
        patch_data = {
            'metadata': {
                'source': 'Extracted from Data Dragon effect_burn arrays',
                'note': 'Supplements champion.bin where damage is missing',
                'patched_abilities': patch_count,
                'champions': len(extracted)
            },
            'patches': extracted
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(patch_data, f, indent=2)
        
        print(f"\nExtracted {patch_count} abilities across {len(extracted)} champions")
        print(f"Saved to: {output_file}")
        
        # Show examples
        print("\nExamples:")
        for champ, spells in list(extracted.items())[:10]:
            print(f"\n{champ}:")
            for key, data in spells.items():
                base = data.get('base_damage', [])
                if base:
                    print(f"  {key} - {data['name']}: {base[0]:.0f} -> {base[-1]:.0f} damage")


def main():
    extractor = DataDragonDamageExtractor()
    extracted = extractor.extract_missing_damage()
    
    output_file = Path("data/processed/effect_burn_damage_patches.json")
    extractor.save_patches(extracted, output_file)


if __name__ == '__main__':
    main()
