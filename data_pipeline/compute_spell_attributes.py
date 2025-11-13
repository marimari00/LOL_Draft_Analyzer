"""Compute champion attributes directly from complete spell data."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class ChampionStats:
    """Contextual stats for damage calculations."""
    level: int = 11
    base_ad: float = 70.0
    bonus_ad: float = 60.0
    total_ad: float = 130.0
    ap: float = 80.0
    attack_range: float = 550.0


class SpellAttributeComputer:
    """Derive high level attributes from raw spell data."""

    HARD_CC_WEIGHTS: Dict[str, float] = {
        'stun': 1.0,
        'knock_up': 1.0,
        'suppress': 1.0,
        'root': 0.9,
        'charm': 0.9,
        'fear': 0.9,
        'taunt': 0.9,
        'sleep': 0.9,
    }

    SOFT_CC_WEIGHTS: Dict[str, float] = {
        'silence': 0.6,
        'blind': 0.5,
        'slow': 0.3,
        'snare': 0.4,
        'ground': 0.4,
    }

    MOBILITY_KEYWORDS: Tuple[Tuple[str, float], ...] = (
        ('dash', 1.2),
        ('blink', 1.5),
        ('teleport', 1.5),
        ('leap', 1.2),
        ('hook to terrain', 1.1),
        ('pulls self', 1.0),
        ('dashes', 1.2),
        ('flies', 1.1),
        ('untargetable', 0.8),
        ('camouflage', 0.4),
        ('stealth', 0.4),
        ('ghosted', 0.4),
        ('movement speed', 0.3),
        ('movespeed', 0.3),
    )

    def __init__(self, data_dir: str = "data/processed", raw_dir: str = "data/raw") -> None:
        self.data_dir = Path(data_dir)
        self.raw_dir = Path(raw_dir)

        with open(self.data_dir / "complete_spell_database.json", "r", encoding="utf-8") as f:
            spell_data = json.load(f)
        self.spells: Dict[str, Dict[str, Dict]] = spell_data["spells"]

        with open(self.raw_dir / "data_dragon_champions.json", "r", encoding="utf-8") as f:
            self.data_dragon = json.load(f)["champions"]

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _build_champion_stats(self, champion: str) -> ChampionStats:
        stats_block = self.data_dragon[champion]["stats"]["base_stats"]
        level = 11
        base_ad = stats_block["attack_damage"] + stats_block["attack_damage_per_level"] * (level - 1)
        bonus_ad = 60.0  # assumed mid-game AD itemisation
        total_ad = base_ad + bonus_ad
        ap = 80.0  # assumed mid-game AP itemisation
        attack_range = stats_block["attack_range"]
        
        # Store additional stats for auto-attack DPS
        self._last_stats = {
            'attack_speed': (stats_block.get("attack_speed", 62.5) + stats_block.get("attack_speed_per_level", 3.0) * (level - 1)) / 100.0,
            'total_ad': total_ad
        }
        
        return ChampionStats(level, base_ad, bonus_ad, total_ad, ap, attack_range)

    def _spell_damage(self, spell: Dict, champ_stats: ChampionStats) -> float:
        base_damage = spell.get("base_damage")
        if base_damage is None:
            return 0.0

        return (
            base_damage
            + spell.get("ad_ratio", 0.0) * champ_stats.total_ad
            + spell.get("bonus_ad_ratio", 0.0) * champ_stats.bonus_ad
            + spell.get("ap_ratio", 0.0) * champ_stats.ap
        )

    def _cc_weight(self, spell: Dict) -> float:
        cc_type = spell.get("cc_type")
        if not cc_type:
            return 0.0

        if cc_type in self.HARD_CC_WEIGHTS:
            return self.HARD_CC_WEIGHTS[cc_type]
        return self.SOFT_CC_WEIGHTS.get(cc_type, 0.0)

    def _mobility_score(self, spell: Dict) -> float:
        description = (spell.get("description") or "").lower()
        score = 0.0
        for keyword, weight in self.MOBILITY_KEYWORDS:
            if keyword in description:
                score = max(score, weight)
        return score

    def _damage_profile(self, champion_spells: Dict[str, Dict]) -> str:
        total_ap = 0.0
        total_ad = 0.0
        for spell in champion_spells.values():
            total_ap += spell.get("ap_ratio", 0.0)
            total_ad += spell.get("ad_ratio", 0.0) + spell.get("bonus_ad_ratio", 0.0)

        if total_ap == 0 and total_ad == 0:
            return "neutral"
        if total_ap >= total_ad * 1.2:
            return "ap"
        if total_ad >= total_ap * 1.2:
            return "ad"
        return "hybrid"

    # ------------------------------------------------------------------
    # Core computation
    # ------------------------------------------------------------------
    def compute_attributes(self) -> Dict[str, Dict[str, float]]:
        attributes: Dict[str, Dict[str, float]] = {}

        for champion, champion_spells in self.spells.items():
            champ_stats = self._build_champion_stats(champion)

            burst_damage = 0.0
            sustained_damage = 0.0
            cc_score = 0.0
            mobility_score = 0.0
            max_range = champ_stats.attack_range

            for spell in champion_spells.values():
                cd = max(spell.get("cooldown", 10.0), 1.0)
                damage = self._spell_damage(spell, champ_stats)

                # Burst damage: assume one cast in opener
                burst_damage += damage

                # Sustained damage over 10 seconds
                # How many times can this spell be cast in 10 seconds?
                casts_over_10 = math.ceil(10.0 / cd)
                sustained_damage += damage * casts_over_10

                # CC contribution
                weight = self._cc_weight(spell)
                if weight > 0.0:
                    duration = spell.get("cc_duration", 0.0)
                    targets = spell.get("target_count", 1.0)
                    cc_score += weight * duration * targets / cd

                # Mobility tools
                mobility_score += self._mobility_score(spell)

                # Range profile
                max_range = max(max_range, spell.get("range", 0.0))

            # Add auto-attack damage contribution
            # This is critical for marksmen and fighters who rely on AAs
            attack_speed = self._last_stats.get('attack_speed', 0.625)
            ad = self._last_stats.get('total_ad', 100.0)
            
            # Estimate how many AAs fit in combat windows
            # Burst window (3s): typically 2-4 autos depending on AS
            aa_burst_count = attack_speed * 3.0  # AAs in 3 second burst
            aa_burst_damage = aa_burst_count * ad
            
            # Sustained window (10s): more AAs possible, but still limited by positioning/kiting
            # Assume ~60% uptime on auto-attacking in sustained fights
            aa_sustained_count = attack_speed * 10.0 * 0.6
            aa_sustained_damage = aa_sustained_count * ad
            
            # Add AA damage to totals
            burst_damage += aa_burst_damage
            sustained_damage += aa_sustained_damage

            sustained_dps = sustained_damage / 10.0 if sustained_damage > 0 else 0.0
            burst_dps = burst_damage / 3.0 if burst_damage > 0 else 0.0
            burst_ratio = burst_damage / sustained_damage if sustained_damage > 0 else 0.0

            # Burst index: combine front-loaded ratio with absolute burst magnitude
            burst_baseline = 1000.0  # rough mid-game burst target
            burst_magnitude_factor = min(1.0, burst_damage / burst_baseline)
            burst_index = burst_ratio * burst_magnitude_factor

            attributes[champion] = {
                "burst_damage": round(burst_damage, 2),
                "burst_dps": round(burst_dps, 2),
                "sustained_damage": round(sustained_damage, 2),
                "sustained_dps": round(sustained_dps, 2),
                "burst_ratio": round(burst_ratio, 3),
                "burst_index": round(burst_index, 3),
                "cc_score": round(cc_score, 3),
                "mobility_score": round(mobility_score, 2),
                "max_range": round(max_range, 1),
                "damage_profile": self._damage_profile(champion_spells),
            }

        return attributes

    def save_attributes(self, attributes: Dict[str, Dict[str, float]]) -> Path:
        output_file = self.data_dir / "spell_based_attributes.json"
        payload = {
            "metadata": {
                "source": "Derived from complete_spell_database.json",
                "note": "Burst/sustained damage, CC, mobility, range computed directly from spell numbers",
            },
            "attributes": attributes,
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return output_file


def main() -> None:
    computer = SpellAttributeComputer()
    attributes = computer.compute_attributes()
    output_file = computer.save_attributes(attributes)

    # Quick sanity print
    print("=" * 70)
    print("Spell-based attributes computed")
    print(f"Champions processed: {len(attributes)}")
    print(f"Saved to: {output_file}")
    print("Example entries:")
    for champ in ["Zed", "Ahri", "Leona", "Jinx"]:
        if champ in attributes:
            print(f"  {champ}: {attributes[champ]}")


if __name__ == "__main__":
    main()
