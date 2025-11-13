"""
Extract damage values from Community Dragon ability tooltips.
Parses tooltip text to find damage formulas when champion.bin data is incomplete.
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple


class TooltipDamageExtractor:
    """Extract damage formulas from ability tooltips."""
    
    def __init__(self, raw_dir: str = "data/raw"):
        self.raw_dir = Path(raw_dir)
        
        with open(self.raw_dir / "community_dragon_champions.json", "r", encoding="utf-8") as f:
            self.cd_data = json.load(f)["champions"]
        
        with open(self.raw_dir / "champion_damage_data.json", "r", encoding="utf-8") as f:
            self.bin_data = json.load(f)["champions"]
    
    def extract_damage_from_description(self, description: str) -> Optional[Dict]:
        """
        Parse ability description to extract damage values.
        
        Returns:
            Dict with base_damage, ratios, or None if no damage found
        """
        if not description:
            return None
        
        # Common damage patterns in League tooltips
        patterns = [
            # "70/110/150/190/230 (+0.6 AP)"
            r'(\d+(?:/\d+){4})\s*\(\+(\d+\.?\d*)\s*(AP|AD|bonus AD)',
            # "70/110/150/190/230 physical damage"
            r'(\d+(?:/\d+){4})\s*(?:physical|magic|true)?\s*damage',
            # "70-230 (+60% AP)"
            r'(\d+)[-–](\d+)\s*\(\+(\d+)%\s*(AP|AD|bonus AD)',
            # Just flat damage
            r'(\d{2,3})\s*(?:physical|magic|true)\s*damage',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                # Parse base damage
                if '/' in groups[0]:
                    # Multiple ranks: 70/110/150/190/230
                    base_values = [float(x) for x in groups[0].split('/')]
                    base_damage = max(base_values)  # Use max rank
                elif '-' in groups[0] or '–' in groups[0]:
                    # Range: use max
                    base_damage = float(groups[1])
                else:
                    base_damage = float(groups[0])
                
                # Parse ratios
                ad_ratio = 0.0
                ap_ratio = 0.0
                bonus_ad_ratio = 0.0
                
                if len(groups) > 2:
                    ratio_value = float(groups[1]) if '.' in groups[1] else float(groups[1]) / 100
                    ratio_type = groups[2].upper()
                    
                    if 'BONUS AD' in ratio_type:
                        bonus_ad_ratio = ratio_value
                    elif 'AD' in ratio_type:
                        ad_ratio = ratio_value
                    elif 'AP' in ratio_type:
                        ap_ratio = ratio_value
                
                return {
                    'base_damage': base_damage,
                    'ad_ratio': ad_ratio,
                    'ap_ratio': ap_ratio,
                    'bonus_ad_ratio': bonus_ad_ratio,
                    'source': 'tooltip_extraction'
                }
        
        return None
    
    def patch_missing_damage(self, output_file: Path):
        """
        Patch champion_damage_data.json with tooltip-extracted damage.
        Only adds damage for abilities that have no damage in champion.bin.
        """
        patched_count = 0
        champion_patches = {}
        
        print("=" * 70)
        print("Patching missing spell damage from tooltips")
        print("=" * 70)
        
        for champ_name, cd_champ in self.cd_data.items():
            if champ_name not in self.bin_data:
                continue
            
            bin_spells = self.bin_data[champ_name].get('spells', {})
            cd_abilities = cd_champ.get('abilities', {})
            
            patches_for_champ = []
            
            for spell_key in ['Q', 'W', 'E', 'R']:
                # Check if champion.bin has this spell
                bin_has_spell = spell_key in bin_spells
                bin_has_damage = False
                
                if bin_has_spell:
                    bin_spell = bin_spells[spell_key]
                    # Check if it has any damage data
                    has_base = bin_spell.get('base_damage') and len(bin_spell.get('base_damage', [])) > 0
                    has_ratios = (bin_spell.get('ad_ratio', 0) != 0 or 
                                 bin_spell.get('ap_ratio', 0) != 0 or 
                                 bin_spell.get('bonus_ad_ratio', 0) != 0)
                    bin_has_damage = has_base or has_ratios
                
                # If no damage in bin, try to extract from tooltip
                if not bin_has_damage and spell_key in cd_abilities:
                    cd_spell = cd_abilities[spell_key]
                    description = cd_spell.get('description', '')
                    
                    extracted = self.extract_damage_from_description(description)
                    
                    if extracted:
                        patched_count += 1
                        patches_for_champ.append({
                            'spell': spell_key,
                            'name': cd_spell.get('name', spell_key),
                            **extracted
                        })
            
            if patches_for_champ:
                champion_patches[champ_name] = patches_for_champ
        
        # Save patches
        patch_data = {
            'metadata': {
                'source': 'Extracted from Community Dragon ability tooltips',
                'note': 'Supplements champion.bin damage data where missing',
                'patched_abilities': patched_count
            },
            'patches': champion_patches
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(patch_data, f, indent=2)
        
        print(f"\nExtracted damage for {patched_count} abilities across {len(champion_patches)} champions")
        print(f"Saved to: {output_file}")
        
        # Show examples
        print("\nExamples:")
        for champ, patches in list(champion_patches.items())[:5]:
            print(f"\n{champ}:")
            for patch in patches:
                print(f"  {patch['spell']} - {patch['name']}: {patch['base_damage']} base")


def main():
    extractor = TooltipDamageExtractor()
    output_file = Path("data/processed/tooltip_damage_patches.json")
    extractor.patch_missing_damage(output_file)


if __name__ == '__main__':
    main()
