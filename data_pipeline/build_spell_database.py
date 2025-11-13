"""
Build complete spell database by merging champion.bin and Data Dragon data.

Strategy:
- Champion.bin: damage numbers, ratios (when available)
- Data Dragon: cooldowns, mana costs, descriptions, ranges (always available)
- Result: Complete spell data for all 171 champions × 4 spells = 684 spells
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SpellDatabaseBuilder:
    """Merges champion.bin damage data with Data Dragon metadata."""
    
    # CC detection patterns (in priority order - check hard CC first)
    CC_PATTERNS = {
        'stun': r'stun(?:s|ning|ned)?',
        'knock_up': r'knock(?:s|ing|ed)?.*?(?:up|into\s+the\s+air|airborne)',
        'suppress': r'suppress(?:es|ing|ed)?',
        'root': r'(?:root|immobilize)(?:s|ing|ed)?',
        'charm': r'charm(?:s|ing|ed)?',
        'fear': r'fear(?:s|ing|ed)?',
        'taunt': r'taunt(?:s|ing|ed)?',
        'sleep': r'sleep(?:s|ing)?|asleep',
        'silence': r'silence(?:s|d)?',
        'blind': r'blind(?:s|ing|ed)?',
        'slow': r'slow(?:s|ing|ed)?',
        'snare': r'(?:snare|bind)(?:s|ing|ed)?',
        'ground': r'ground(?:s|ing|ed)?',
    }
    
    # CC type classifications
    HARD_CC = {'stun', 'knock_up', 'suppress', 'root', 'charm', 'fear', 'taunt', 'sleep'}
    SOFT_CC = {'slow', 'blind', 'silence', 'snare', 'ground'}
    
    def __init__(self, data_dir: str = "data/raw", output_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load source data - prefer patched data if available
        print("Loading source data...")
        patched_path = self.output_dir / 'champion_damage_data_patched.json'
        merged_path = self.output_dir / 'champion_damage_data_merged.json'
        
        if patched_path.exists():
            print(f"  Using patched damage data: {patched_path}")
            with open(patched_path, 'r', encoding='utf-8') as f:
                self.damage_data = json.load(f)['champions']
        elif merged_path.exists():
            print(f"  Using merged damage data: {merged_path}")
            with open(merged_path, 'r', encoding='utf-8') as f:
                self.damage_data = json.load(f)['champions']
        else:
            print(f"  Using original damage data: {self.data_dir / 'champion_damage_data.json'}")
            with open(self.data_dir / 'champion_damage_data.json', 'r') as f:
                self.damage_data = json.load(f)['champions']
        
        with open(self.data_dir / 'data_dragon_champions.json', 'r', encoding='utf-8') as f:
            self.dd_data = json.load(f)['champions']
        
        print(f"  Damage data: {len(self.damage_data)} champions")
        print(f"  Data Dragon: {len(self.dd_data)} champions")
    
    def detect_cc(self, description: str) -> Optional[Tuple[str, float]]:
        """
        Detect CC type and duration from ability description.
        
        Returns:
            (cc_type, duration) or None if no CC found
        """
        if not description:
            return None
        
        desc_lower = description.lower()
        
        # Try to find explicit duration first
        duration_match = re.search(r'(?:for\s+)?([\d\.]+)\s*(?:second|sec)', desc_lower)
        default_duration = float(duration_match.group(1)) if duration_match else None
        
        # Check each CC pattern (hard CC first due to dict ordering)
        for cc_type, pattern in self.CC_PATTERNS.items():
            if re.search(pattern, desc_lower):
                # Use extracted duration or typical duration for this CC type
                if default_duration is None:
                    typical_durations = {
                        'stun': 1.5, 'knock_up': 1.0, 'suppress': 2.5,
                        'root': 2.0, 'charm': 1.5, 'fear': 1.5, 'taunt': 1.5, 'sleep': 2.0,
                        'silence': 2.0, 'blind': 2.0, 'slow': 2.0, 'snare': 2.0, 'ground': 2.0
                    }
                    duration = typical_durations.get(cc_type, 1.5)
                else:
                    duration = default_duration
                
                # Sanity check: if CC duration is >10s, likely a false positive
                # (e.g., seed lasting 60s, zone lasting 30s, etc.)
                if duration > 10.0:
                    continue
                
                return (cc_type, duration)
        
        return None
    
    def detect_skillshot(self, description: str) -> bool:
        """Check if ability is a skillshot."""
        if not description:
            return False
        
        desc_lower = description.lower()
        skillshot_keywords = [
            'skillshot', 'fires', 'throws', 'shoots', 'hurls', 'launches',
            'sends', 'projectile', 'missile', 'line', 'cone', 'bolt'
        ]
        return any(kw in desc_lower for kw in skillshot_keywords)
    
    def detect_aoe(self, description: str) -> Tuple[bool, float]:
        """
        Check if ability is AOE and estimate target count.
        
        Returns:
            (is_aoe, target_count_multiplier)
        """
        if not description:
            return False, 1.0
        
        desc_lower = description.lower()
        
        # Large AOE indicators
        if any(kw in desc_lower for kw in ['all enemies', 'all champions', 'all nearby', 'massive area']):
            return True, 3.0
        
        # Medium AOE indicators
        if any(kw in desc_lower for kw in ['nearby enemies', 'area', 'enemies in', 'around', 'surrounding', 'aoe']):
            return True, 2.0
        
        # Small AOE indicators
        if any(kw in desc_lower for kw in ['enemies hit', 'multiple', 'splash']):
            return True, 1.5
        
        return False, 1.0
    
    def merge_spell_data(self, champion_name: str, spell_key: str) -> Optional[Dict]:
        """Merge spell data from both sources for a single spell."""
        merged = {
            'champion': champion_name,
            'key': spell_key,
            'name': None,
            'description': None,
            'cooldowns': [],
            'cooldown': None,
            'mana_costs': [],
            'mana_cost': None,
            'ranges': [],
            'range': None,
            'base_damage_ranks': [],
            'base_damage': None,
            'ad_ratio': 0.0,
            'ap_ratio': 0.0,
            'bonus_ad_ratio': 0.0,
            'damage_type': None,
            'cc_type': None,
            'cc_duration': None,
            'is_hard_cc': False,
            'is_skillshot': False,
            'is_aoe': False,
            'target_count': 1.0,
        }
        
        # Get Data Dragon data (always available)
        if champion_name not in self.dd_data:
            return None
        
        dd_abilities = self.dd_data[champion_name].get('abilities', {})
        if spell_key not in dd_abilities:
            return None
        
        dd_spell = dd_abilities[spell_key]
        merged['name'] = dd_spell.get('name')
        merged['description'] = dd_spell.get('description', '')
        
        # Cooldown: use max rank (last value)
        cooldowns = dd_spell.get('cooldown', [10])
        merged['cooldowns'] = cooldowns if isinstance(cooldowns, list) else [cooldowns]
        cooldown = merged['cooldowns'][-1] if merged['cooldowns'] else 10.0
        
        # Validate cooldown (flag suspicious values)
        if cooldown < 1.0:  # Likely cast time, not cooldown
            # For abilities with very short "cooldowns", estimate reasonable value
            # Most damaging spells: 3-20s, Utility: 10-30s, Ults: 60-120s
            if spell_key == 'R':
                cooldown = 100.0  # Ult default
            else:
                cooldown = 10.0  # Basic ability default
        
        merged['cooldown'] = cooldown
        
        # Mana cost: use rank 1 (first value)
        costs = dd_spell.get('cost', [0])
        merged['mana_costs'] = costs if isinstance(costs, list) else [costs]
        merged['mana_cost'] = merged['mana_costs'][0] if merged['mana_costs'] else 0.0
        
        # Range: use max range (last value)
        ranges = dd_spell.get('range', [0])
        merged['ranges'] = ranges if isinstance(ranges, list) else [ranges]
        merged['range'] = merged['ranges'][-1] if merged['ranges'] else 0.0
        
        # Get champion.bin damage data (if available)
        if champion_name in self.damage_data:
            bin_spells = self.damage_data[champion_name].get('spells', {})
            if spell_key in bin_spells:
                bin_spell = bin_spells[spell_key]
                
                # Base damage: use max rank
                base_dmg = bin_spell.get('base_damage', [])
                merged['base_damage_ranks'] = base_dmg
                merged['base_damage'] = base_dmg[-1] if base_dmg else None
                
                merged['ad_ratio'] = bin_spell.get('ad_ratio', 0.0)
                merged['ap_ratio'] = bin_spell.get('ap_ratio', 0.0)
                merged['bonus_ad_ratio'] = bin_spell.get('bonus_ad_ratio', 0.0)
                merged['damage_type'] = bin_spell.get('damage_type')
        
        # Parse description for CC and mechanics
        if merged['description']:
            cc_info = self.detect_cc(merged['description'])
            if cc_info:
                merged['cc_type'] = cc_info[0]
                merged['cc_duration'] = cc_info[1]
                merged['is_hard_cc'] = cc_info[0] in self.HARD_CC
            
            merged['is_skillshot'] = self.detect_skillshot(merged['description'])
            merged['is_aoe'], merged['target_count'] = self.detect_aoe(merged['description'])
        
        return merged
    
    def build_database(self) -> Dict:
        """Build complete spell database for all champions."""
        print("\n" + "=" * 70)
        print("Building Complete Spell Database")
        print("=" * 70)
        
        database = {}
        stats = {
            'total_champions': 0,
            'total_spells': 0,
            'spells_with_damage': 0,
            'spells_with_cc': 0,
            'spells_missing_cooldown': 0
        }
        
        for champion_name in self.dd_data.keys():
            champion_spells = {}
            
            for spell_key in ['Q', 'W', 'E', 'R']:
                spell_data = self.merge_spell_data(champion_name, spell_key)
                
                if spell_data:
                    champion_spells[spell_key] = spell_data
                    stats['total_spells'] += 1
                    
                    if spell_data['base_damage']:
                        stats['spells_with_damage'] += 1
                    if spell_data['cc_type']:
                        stats['spells_with_cc'] += 1
                    if not spell_data['cooldown']:
                        stats['spells_missing_cooldown'] += 1
            
            if champion_spells:
                database[champion_name] = champion_spells
                stats['total_champions'] += 1
        
        print(f"\nExtraction complete!")
        print(f"  Champions: {stats['total_champions']}")
        print(f"  Total spells: {stats['total_spells']}")
        print(f"  Spells with damage data: {stats['spells_with_damage']}")
        print(f"  Spells with CC: {stats['spells_with_cc']}")
        print(f"  Spells missing cooldown: {stats['spells_missing_cooldown']}")
        
        # Save to file
        output_file = self.output_dir / 'complete_spell_database.json'
        output_data = {
            'metadata': {
                'source': 'Merged from champion.bin + Data Dragon',
                'note': 'Complete spell data: damage, cooldowns, CC, ranges',
                **stats
            },
            'spells': database
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved to: {output_file}")
        
        return database


def main():
    """Build and save complete spell database."""
    builder = SpellDatabaseBuilder()
    database = builder.build_database()
    
    # Show example
    print("\n" + "=" * 70)
    print("EXAMPLE: Zed's Spells")
    print("=" * 70)
    
    if 'Zed' in database:
        import pprint
        pprint.pprint(database['Zed'], depth=2)


if __name__ == '__main__':
    main()
