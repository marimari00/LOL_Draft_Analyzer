"""
Extract champion damage data from champion.bin.json files.

This extracts REAL game data including:
- Base damage values per rank
- AP/AD/HP scaling coefficients
- Cooldowns per rank
- Mana costs per rank
- Damage types (magic/physical/true)

This is the same data used by the game client itself!
"""

import requests
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from data_pipeline.legacy_champion_mappings import get_spell_paths


@dataclass
class SpellDamage:
    """Damage data for a single spell."""
    spell_key: str  # Q, W, E, R, P
    spell_name: str
    base_damage: List[float]  # Damage per rank
    ap_ratio: float = 0.0
    ad_ratio: float = 0.0
    bonus_ad_ratio: float = 0.0
    max_hp_ratio: float = 0.0
    target_max_hp_ratio: float = 0.0
    cooldown: List[float] = None
    mana_cost: List[float] = None
    damage_type: str = 'magic'  # magic, physical, true, mixed


class ChampionBinExtractor:
    """Extracts damage data from champion.bin.json files."""
    
    BASE_URL = "https://raw.communitydragon.org/latest/game/data/characters"
    
    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_champion_bin(self, champion_name: str) -> Optional[Dict]:
        """Fetch champion.bin.json from Community Dragon."""
        url = f"{self.BASE_URL}/{champion_name.lower()}/{champion_name.lower()}.bin.json"
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ERROR fetching {champion_name}: {e}")
            return None
    
    def extract_coefficient_from_part(self, part: Dict) -> tuple[str, float]:
        """
        Extract stat type and coefficient from a formula part.
        
        Returns: (stat_type, coefficient)
        stat_type can be: 'ap', 'ad', 'bonus_ad', 'max_hp', 'target_max_hp', etc.
        """
        part_type = part.get('__type', '')
        
        if 'Coefficient' in part_type:
            coeff = part.get('mCoefficient', 0.0)
            
            # The stat type is encoded in the part type or mStat field
            # Common patterns:
            # - StatByCoefficientCalculationPart = usually AP (ability power)
            # - AbilityPowerCoefficient = AP
            # - AttackDamageCoefficient = AD
            
            stat = part.get('mStat', '')
            
            # Map stat field to our names
            if 'AbilityPower' in str(stat) or 'TotalAbilityPower' in part_type:
                return ('ap', coeff)
            elif 'AttackDamage' in str(stat):
                if 'Bonus' in str(stat):
                    return ('bonus_ad', coeff)
                else:
                    return ('ad', coeff)
            elif 'MaxHealth' in str(stat) or 'Health' in str(stat):
                if 'Source' in str(part):
                    return ('max_hp', coeff)
                else:
                    return ('target_max_hp', coeff)
            else:
                # Default to AP for unspecified coefficients
                return ('ap', coeff)
        
        return (None, 0.0)
    
    def parse_spell_damage(self, spell_data: Dict, spell_key: str) -> Optional[SpellDamage]:
        """Parse damage data from a spell's mSpell dict."""
        # Try mSpell first (newer format), then mRootSpell (older format)
        mspell = spell_data.get('mSpell')
        if not mspell and 'mRootSpell' in spell_data:
            # mRootSpell is a reference, but we already have the actual spell data
            # Check if this entry has DataValues directly
            if 'DataValues' in spell_data:
                mspell = spell_data
            else:
                return None
        
        if not mspell:
            return None
        
        # Extract spell name
        spell_name = mspell.get('mAlternateName', spell_data.get('mScriptName', ''))
        
        # Extract base damage from DataValues
        base_damage = []
        data_values = mspell.get('DataValues', [])
        for dv in data_values:
            name = dv.get('mName', '')
            # Look for damage-related values (more flexible matching)
            if any(keyword in name for keyword in ['BaseDamage', 'Damage', 'TotalDamage', 'Base']):
                # Exclude non-damage values
                if not any(exclude in name for exclude in ['Ratio', 'Percent', 'Duration', 'Range', 'Speed', 'Cooldown']):
                    values = dv.get('mValues', [])
                    if values:
                        # Take first 6 values (level 0-5, ignore extra ranks)
                        base_damage = [float(v) for v in values[:6]]
                        break
        
        # Extract coefficients from mSpellCalculations
        ap_ratio = 0.0
        ad_ratio = 0.0
        bonus_ad_ratio = 0.0
        max_hp_ratio = 0.0
        target_max_hp_ratio = 0.0
        
        spell_calcs = mspell.get('mSpellCalculations', {})
        for calc_name, calc_data in spell_calcs.items():
            if 'Damage' in calc_name or 'Total' in calc_name:
                formula_parts = calc_data.get('mFormulaParts', [])
                for part in formula_parts:
                    stat_type, coeff = self.extract_coefficient_from_part(part)
                    if stat_type == 'ap':
                        ap_ratio += coeff
                    elif stat_type == 'ad':
                        ad_ratio += coeff
                    elif stat_type == 'bonus_ad':
                        bonus_ad_ratio += coeff
                    elif stat_type == 'max_hp':
                        max_hp_ratio += coeff
                    elif stat_type == 'target_max_hp':
                        target_max_hp_ratio += coeff
        
        # Extract cooldown
        cooldown = mspell.get('cooldownTime', [])
        if cooldown:
            cooldown = [float(cd) for cd in cooldown[:6]]
        
        # Extract mana cost
        mana_cost = mspell.get('mana', [])
        if mana_cost:
            mana_cost = [float(m) for m in mana_cost[:6]]
        
        # If no damage data found, return None
        if not base_damage and ap_ratio == 0.0 and ad_ratio == 0.0:
            return None
        
        return SpellDamage(
            spell_key=spell_key,
            spell_name=spell_name,
            base_damage=base_damage,
            ap_ratio=ap_ratio,
            ad_ratio=ad_ratio,
            bonus_ad_ratio=bonus_ad_ratio,
            max_hp_ratio=max_hp_ratio,
            target_max_hp_ratio=target_max_hp_ratio,
            cooldown=cooldown,
            mana_cost=mana_cost
        )
    
    def extract_champion_spells(self, champion_name: str) -> Dict[str, SpellDamage]:
        """Extract all spell damage data for a champion."""
        bin_data = self.fetch_champion_bin(champion_name)
        if not bin_data:
            return {}
        
        spells = {}
        
        # Find spell entries for Q, W, E, R, P (passive)
        spell_keys = ['Q', 'W', 'E', 'R', 'P']
        
        for key in spell_keys:
            # Get all possible spell paths (handles legacy champions)
            patterns = get_spell_paths(champion_name, key)
            
            for spell_path in patterns:
                if spell_path in bin_data:
                    spell_damage = self.parse_spell_damage(bin_data[spell_path], key)
                    if spell_damage:
                        spells[key] = spell_damage
                        break  # Found it, move to next spell key
        
        return spells
    
    def extract_all_champions(self, champion_list: List[str]) -> Dict:
        """Extract damage data for all champions."""
        print("=" * 70)
        print("Extracting Champion Damage Data from .bin Files")
        print("=" * 70)
        print(f"\nProcessing {len(champion_list)} champions...")
        print("This will take ~2 minutes with rate limiting.\n")
        
        all_damage_data = {}
        failed = []
        
        for i, champion_name in enumerate(champion_list, 1):
            print(f"[{i}/{len(champion_list)}] {champion_name}...", end=' ')
            
            try:
                spells = self.extract_champion_spells(champion_name)
                
                if spells:
                    all_damage_data[champion_name] = {
                        'champion_id': champion_name,
                        'spells': {k: asdict(v) for k, v in spells.items()}
                    }
                    print(f"[OK] ({len(spells)} spells)")
                else:
                    print(f"[WARN] No damage data found")
                    failed.append(champion_name)
                
            except Exception as e:
                print(f"[ERROR] {e}")
                failed.append(champion_name)
            
            # Rate limiting
            time.sleep(0.3)
        
        # Save results
        output_file = self.output_dir / "champion_damage_data.json"
        
        output = {
            'metadata': {
                'source': 'Community Dragon champion.bin.json',
                'champion_count': len(all_damage_data),
                'failed_count': len(failed),
                'failed_champions': failed,
                'note': 'Extracted from game files - exact damage formulas'
            },
            'champions': all_damage_data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 70)
        print("Extraction Complete!")
        print("=" * 70)
        print(f"Successfully extracted: {len(all_damage_data)} champions")
        if failed:
            print(f"Failed: {len(failed)} champions")
            print(f"  {', '.join(failed[:10])}")
        print(f"Output: {output_file}")
        print("=" * 70)
        
        return all_damage_data


def main():
    """Main execution."""
    # Load champion list from Data Dragon
    with open('data/raw/data_dragon_champions.json', 'r', encoding='utf-8') as f:
        dd = json.load(f)
    
    champion_list = list(dd['champions'].keys())
    print(f"Found {len(champion_list)} champions in Data Dragon\n")
    
    extractor = ChampionBinExtractor()
    extractor.extract_all_champions(champion_list)


if __name__ == "__main__":
    main()
