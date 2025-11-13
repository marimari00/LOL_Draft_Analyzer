"""
Compute enhanced champion attributes using REAL damage data from game files.

This replaces heuristic-based damage pattern classification with actual
damage calculations from champion.bin files.

Key improvements:
- Burst vs Sustained: Based on actual ability rotation damage
- Timing curves: Early/mid/late calculated with real base damage + typical items
- Damage patterns: Uses real cooldowns and damage formulas
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple


class EnhancedAttributeComputer:
    """Computes champion attributes using real damage formulas."""
    
    # Typical item stats at different game phases
    EARLY_STATS = {'ap': 40, 'ad': 30, 'bonus_ad': 15, 'level': 6}
    MID_STATS = {'ap': 150, 'ad': 80, 'bonus_ad': 50, 'level': 11}
    LATE_STATS = {'ap': 400, 'ad': 250, 'bonus_ad': 200, 'level': 16}
    
    def __init__(self, data_dragon_path: str = "data/raw/data_dragon_champions.json",
                 damage_data_path: str = "data/raw/champion_damage_data.json",
                 output_dir: str = "data/processed"):
        self.data_dragon_path = Path(data_dragon_path)
        self.damage_data_path = Path(damage_data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        with open(self.data_dragon_path, 'r', encoding='utf-8') as f:
            self.data_dragon = json.load(f)
        
        with open(self.damage_data_path, 'r', encoding='utf-8') as f:
            self.damage_data = json.load(f)
    
    def calculate_spell_damage(self, spell: Dict, stats: Dict) -> float:
        """
        Calculate total damage for a spell at given stats.
        
        Args:
            spell: Spell data with base_damage, ap_ratio, ad_ratio, etc.
            stats: Dict with 'ap', 'ad', 'bonus_ad', 'level' keys
        
        Returns:
            Total damage at the specified level
        """
        level = stats['level']
        
        # Get base damage at this level (1-indexed, but level 6 = rank 3, level 11 = rank 5, etc.)
        # Abilities rank up: Q at 1/3/5/7/9, W at 1/3/5/7/9, E at 2/4/6/8/10, R at 6/11/16
        if level <= 3:
            rank = 0  # Rank 1
        elif level <= 5:
            rank = 1  # Rank 2
        elif level <= 7:
            rank = 2  # Rank 3
        elif level <= 9:
            rank = 3  # Rank 4
        else:
            rank = 4  # Rank 5
        
        base_damage_array = spell.get('base_damage', [])
        if not base_damage_array:
            base_damage = 0
        else:
            # Skip level 0 if it exists (some spells have 7 values)
            if len(base_damage_array) > 5 and base_damage_array[0] < 0:
                base_damage_array = base_damage_array[1:]
            rank = min(rank, len(base_damage_array) - 1)
            base_damage = base_damage_array[rank] if rank >= 0 else 0
        
        # Calculate scaling damage
        scaling_damage = 0
        scaling_damage += spell.get('ap_ratio', 0) * stats['ap']
        scaling_damage += spell.get('ad_ratio', 0) * stats['ad']
        scaling_damage += spell.get('bonus_ad_ratio', 0) * stats['bonus_ad']
        # Note: HP ratios would need champion base HP, skipping for now
        
        return max(0, base_damage + scaling_damage)
    
    def calculate_rotation_damage(self, champion_id: str, stats: Dict) -> Tuple[float, List[float], List[float]]:
        """
        Calculate full rotation damage (Q+W+E+R) and individual spell damages.
        
        Returns:
            (total_rotation_damage, spell_damages, cooldowns)
        """
        champ_damage = self.damage_data['champions'].get(champion_id)
        if not champ_damage:
            return 0, [], []
        
        spells = champ_damage.get('spells', {})
        spell_damages = []
        cooldowns = []
        
        for key in ['Q', 'W', 'E', 'R']:
            if key in spells:
                spell = spells[key]
                damage = self.calculate_spell_damage(spell, stats)
                spell_damages.append(damage)
                
                # Get cooldown at appropriate rank
                cd_array = spell.get('cooldown', [])
                if cd_array:
                    level = stats['level']
                    if level <= 3:
                        rank = 0
                    elif level <= 5:
                        rank = 1
                    elif level <= 7:
                        rank = 2
                    elif level <= 9:
                        rank = 3
                    else:
                        rank = 4
                    rank = min(rank, len(cd_array) - 1)
                    cd = cd_array[rank] if rank >= 0 else 10
                else:
                    cd = 10  # Default
                cooldowns.append(cd)
            else:
                spell_damages.append(0)
                cooldowns.append(10)
        
        total_damage = sum(spell_damages)
        return total_damage, spell_damages, cooldowns
    
    def compute_burst_vs_sustained(self, champion_id: str) -> Tuple[float, float]:
        """
        Classify burst vs sustained damage pattern using REAL damage formulas.
        
        Burst: High upfront damage in single rotation with long cooldowns
        Sustained: Consistent DPS with short cooldowns/spam
        
        Returns:
            (burst_score, sustained_score) each in [0, 1]
        """
        # Calculate damage at mid game
        mid_damage, spell_damages, cooldowns = self.calculate_rotation_damage(
            champion_id, self.MID_STATS
        )
        
        if not spell_damages or mid_damage == 0:
            return 0.5, 0.5  # Unknown, neutral
        
        # Burst indicators:
        # 1. High single-rotation damage (>1500 at mid game)
        # 2. Long cooldowns (can't spam)
        # 3. Damage concentrated in few abilities
        
        avg_cooldown = np.mean(cooldowns) if cooldowns else 10
        max_spell_damage = max(spell_damages) if spell_damages else 0
        damage_concentration = max_spell_damage / mid_damage if mid_damage > 0 else 0
        
        # Burst score
        burst_indicators = 0
        if mid_damage > 1500:  # High rotation damage
            burst_indicators += 1
        if avg_cooldown > 8:  # Long cooldowns
            burst_indicators += 1
        if damage_concentration > 0.4:  # Damage concentrated in one spell
            burst_indicators += 1
        
        burst_score = burst_indicators / 3.0
        
        # Sustained score (inverse relationship but not perfect)
        sustained_indicators = 0
        if avg_cooldown < 6:  # Short cooldowns (spammable)
            sustained_indicators += 1
        if damage_concentration < 0.35:  # Damage spread across spells
            sustained_indicators += 1
        if mid_damage < 1200:  # Lower burst, implies more sustained pattern
            sustained_indicators += 0.5
        
        sustained_score = min(1.0, sustained_indicators / 2.5)
        
        # Normalize so they don't both = 0
        total = burst_score + sustained_score
        if total > 0:
            burst_score = burst_score / total
            sustained_score = sustained_score / total
        else:
            burst_score = 0.5
            sustained_score = 0.5
        
        return burst_score, sustained_score
    
    def compute_timing_curve(self, champion_id: str) -> Tuple[float, float, float]:
        """
        Calculate early/mid/late game damage strength using real formulas.
        
        Returns:
            (damage_early, damage_mid, damage_late) normalized 0-1
        """
        early_dmg, _, _ = self.calculate_rotation_damage(champion_id, self.EARLY_STATS)
        mid_dmg, _, _ = self.calculate_rotation_damage(champion_id, self.MID_STATS)
        late_dmg, _, _ = self.calculate_rotation_damage(champion_id, self.LATE_STATS)
        
        # Normalize by typical damage values at each phase
        # Early: 400-800, Mid: 1000-2000, Late: 2000-4000
        damage_early = np.clip(early_dmg / 800, 0, 1)
        damage_mid = np.clip(mid_dmg / 2000, 0, 1)
        damage_late = np.clip(late_dmg / 4000, 0, 1)
        
        return damage_early, damage_mid, damage_late
    
    def compute_all_attributes(self) -> Dict:
        """Compute enhanced attributes for all champions."""
        print("=" * 70)
        print("Computing Enhanced Attributes with Real Damage Data")
        print("=" * 70)
        print(f"\nProcessing {len(self.data_dragon['champions'])} champions...\n")
        
        all_attributes = {}
        
        # First pass: compute raw values
        raw_data = {}
        for champion_id, dd_data in self.data_dragon['champions'].items():
            # Get existing basic attributes (CC, mobility, survivability, etc.)
            # We'll re-use these since they're not damage-related
            abilities = dd_data.get('abilities', {})
            
            # Compute new damage-based attributes
            burst, sustained = self.compute_burst_vs_sustained(champion_id)
            dmg_early, dmg_mid, dmg_late = self.compute_timing_curve(champion_id)
            
            raw_data[champion_id] = {
                'burst_pattern': burst,
                'sustained_pattern': sustained,
                'damage_early': dmg_early,
                'damage_mid': dmg_mid,
                'damage_late': dmg_late
            }
            
            print(f"[{champion_id}] Burst: {burst:.2f}, Sustained: {sustained:.2f}, "
                  f"Early: {dmg_early:.2f}, Mid: {dmg_mid:.2f}, Late: {dmg_late:.2f}")
        
        # Load existing attributes for non-damage stats
        with open('data/processed/computed_attributes.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        existing_attrs = existing_data.get('champions', existing_data)  # Handle both wrapped and flat format
        
        # Second pass: merge with existing attributes, replacing damage patterns
        for champion_id in raw_data:
            old_attrs = existing_attrs.get(champion_id, {})
            
            # Determine categorical damage_pattern for archetype compatibility
            burst_score = raw_data[champion_id]['burst_pattern']
            sustained_score = raw_data[champion_id]['sustained_pattern']
            if burst_score > sustained_score:
                damage_pattern = "burst"
            else:
                damage_pattern = "sustained"
            
            # Start with old attributes, then add/override with new damage data
            all_attributes[champion_id] = {}
            all_attributes[champion_id].update(old_attrs)  # All old attributes
            all_attributes[champion_id].update({  # Override/add new damage attributes
                'damage_pattern': damage_pattern,  # Categorical for archetypes
                'burst_pattern': burst_score,  # Numeric score
                'sustained_pattern': sustained_score,  # Numeric score
                'damage_early': raw_data[champion_id]['damage_early'],
                'damage_mid': raw_data[champion_id]['damage_mid'],
                'damage_late': raw_data[champion_id]['damage_late']
            })
        
        # Save results
        output_file = self.output_dir / "enhanced_attributes.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_attributes, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 70)
        print("Enhanced Attribute Computation Complete!")
        print("=" * 70)
        print(f"Output: {output_file}")
        print(f"Champions processed: {len(all_attributes)}")
        print("=" * 70)
        
        return all_attributes


def main():
    """Main execution."""
    computer = EnhancedAttributeComputer()
    computer.compute_all_attributes()


if __name__ == "__main__":
    main()
