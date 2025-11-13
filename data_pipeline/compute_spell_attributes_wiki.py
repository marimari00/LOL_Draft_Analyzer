"""
Compute champion attributes from wiki spell database (single source of truth).
"""

import json
import math
from pathlib import Path
from typing import Dict

class SpellAttributeComputer:
    """Derive high-level attributes from wiki spell data."""

    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        
        # Load wiki spell database
        with open(self.data_dir / "spell_database_wiki.json", "r", encoding="utf-8") as f:
            self.spell_db = json.load(f)
        
        # Group spells by champion
        self.champion_spells = {}
        for spell_id, spell_data in self.spell_db.items():
            champion = spell_data['champion']
            if champion not in self.champion_spells:
                self.champion_spells[champion] = {}
            spell_key = spell_data['spell_key']
            self.champion_spells[champion][spell_key] = spell_data

    def _spell_damage(self, spell: Dict) -> float:
        """Calculate spell damage at mid-game (level 11, 60 bonus AD, 80 AP)."""
        base_damage = spell.get("base_damage", [])
        if not base_damage:
            return 0.0
        
        # Use rank 3 damage (level 11 typically has Q/W/E at rank 3, R at rank 1-2)
        rank_index = min(2, len(base_damage) - 1)
        base = base_damage[rank_index] if base_damage else 0.0
        
        # Mid-game stats
        total_ad = 130.0  # 70 base + 60 bonus
        bonus_ad = 60.0
        ap = 80.0
        
        return (
            base
            + spell.get("ad_ratio", 0.0) * total_ad
            + spell.get("bonus_ad_ratio", 0.0) * bonus_ad
            + spell.get("ap_ratio", 0.0) * ap
        )

    def _damage_profile(self, champion_spells: Dict[str, Dict]) -> str:
        """Determine damage profile weighted by base damage."""
        weighted_ap = 0.0
        weighted_ad = 0.0
        
        for spell in champion_spells.values():
            base_dmg_list = spell.get("base_damage", [])
            base_dmg = base_dmg_list[0] if base_dmg_list else 0.0
            
            # Weight ratios by base damage (utility spells won't dominate)
            weight = max(base_dmg, 50.0)
            
            ap_ratio = spell.get("ap_ratio", 0.0)
            ad_ratio = spell.get("ad_ratio", 0.0) + spell.get("bonus_ad_ratio", 0.0)
            
            weighted_ap += ap_ratio * weight
            weighted_ad += ad_ratio * weight

        if weighted_ap == 0 and weighted_ad == 0:
            return "neutral"
        if weighted_ap >= weighted_ad * 1.2:
            return "ap"
        if weighted_ad >= weighted_ap * 1.2:
            return "ad"
        return "hybrid"

    def compute_attributes(self) -> Dict[str, Dict]:
        """Compute attributes for all champions."""
        attributes = {}
        
        for champion, spells in self.champion_spells.items():
            burst_damage = 0.0
            sustained_damage = 0.0
            max_range = 550.0  # Default AA range
            
            for spell_key, spell in spells.items():
                cd_list = spell.get("cooldown", [])
                cd = cd_list[0] if cd_list else 10.0  # Use rank 1 cooldown
                cd = max(cd, 1.0)
                
                damage = self._spell_damage(spell)
                
                # Burst damage: one cast
                burst_damage += damage
                
                # Sustained damage over 10 seconds
                casts_over_10 = math.ceil(10.0 / cd)
                sustained_damage += damage * casts_over_10
            
            # Add auto-attack damage (critical for marksmen/fighters)
            # Mid-game: 130 AD, 0.65 AS (typical)
            aa_damage = 130.0
            attack_speed = 0.65
            
            # Burst window (3s)
            aa_burst_count = attack_speed * 3.0
            aa_burst_damage = aa_burst_count * aa_damage
            
            # Sustained window (10s) with 60% uptime
            aa_sustained_count = attack_speed * 10.0 * 0.6
            aa_sustained_damage = aa_sustained_count * aa_damage
            
            burst_damage += aa_burst_damage
            sustained_damage += aa_sustained_damage
            
            # Calculate DPS metrics
            sustained_dps = sustained_damage / 10.0
            burst_dps = burst_damage / 3.0
            burst_ratio = burst_damage / sustained_damage if sustained_damage > 0 else 0.0
            
            # Burst potential (normalized to mid-game baseline)
            burst_baseline = 1000.0
            burst_potential = min(1.0, burst_damage / burst_baseline)
            
            # Total AD ratios (critical for marksman classification)
            total_ad_ratio = sum(
                s.get("ad_ratio", 0) + s.get("bonus_ad_ratio", 0)
                for s in spells.values()
            )
            
            # Total AP ratios
            total_ap_ratio = sum(s.get("ap_ratio", 0) for s in spells.values())
            
            attributes[champion] = {
                "burst_damage": round(burst_damage, 2),
                "burst_dps": round(burst_dps, 2),
                "sustained_damage": round(sustained_damage, 2),
                "sustained_dps": round(sustained_dps, 2),
                "burst_ratio": round(burst_ratio, 3),
                "burst_potential": round(burst_potential, 3),
                "max_range": round(max_range, 1),
                "damage_profile": self._damage_profile(spells),
                "total_ad_ratio": round(total_ad_ratio, 2),
                "total_ap_ratio": round(total_ap_ratio, 2),
            }
        
        return attributes

    def save_attributes(self, attributes: Dict) -> Path:
        """Save computed attributes to file."""
        output_file = self.data_dir / "spell_based_attributes_wiki.json"
        payload = {
            "metadata": {
                "source": "spell_database_wiki.json (single source of truth)",
                "note": "Computed from clean wiki data, fixes Braum false positive (0.0 AD not 4.0)",
            },
            "attributes": attributes,
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return output_file


def main():
    print("="*60)
    print("Computing spell attributes from wiki data...")
    print("="*60)
    
    computer = SpellAttributeComputer()
    attributes = computer.compute_attributes()
    output_file = computer.save_attributes(attributes)
    
    print(f"\n✓ Processed {len(attributes)} champions")
    print(f"✓ Saved to: {output_file}")
    
    # Show key examples
    print("\nKey validations:")
    
    if "Braum" in attributes:
        braum = attributes["Braum"]
        print(f"\nBraum (should NOT be marksman):")
        print(f"  Sustained DPS: {braum['sustained_dps']}")
        print(f"  Total AD ratio: {braum['total_ad_ratio']} (was 4.0 in old data!)")
        print(f"  Damage profile: {braum['damage_profile']}")
    
    if "Caitlyn" in attributes:
        cait = attributes["Caitlyn"]
        print(f"\nCaitlyn (true marksman):")
        print(f"  Sustained DPS: {cait['sustained_dps']}")
        print(f"  Total AD ratio: {cait['total_ad_ratio']}")
        print(f"  Damage profile: {cait['damage_profile']}")
    
    if "Jhin" in attributes:
        jhin = attributes["Jhin"]
        print(f"\nJhin (marksman with burst):")
        print(f"  Sustained DPS: {jhin['sustained_dps']}")
        print(f"  Burst ratio: {jhin['burst_ratio']}")
        print(f"  Total AD ratio: {jhin['total_ad_ratio']}")


if __name__ == "__main__":
    main()
