"""
Compute champion attributes from raw Data Dragon data.

This module implements the mathematical formulas for calculating:
- CC Score: Σ(duration × reliability × target_count × uptime)
- Mobility Score: Weighted sum of dashes, blinks, MS buffs
- Survivability Index: EHP × threat_evasion × sustain
- Waveclear Speed: AOE damage potential
- Range Profiles: Auto-attack, ability, threat, escape ranges
- Gold Dependency: Calculated from base stats vs scaling
- Sustain Score: Healing/shielding per second

These are the fundamental attributes from which strategic archetypes emerge.
"""

import json
import re
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RangeProfile:
    """Champion range profile in game units."""
    auto_attack: int
    effective_ability: int  # Max poke/engage range
    threat: int  # Where champion becomes dangerous
    escape: int  # Total mobility distance


@dataclass
class ChampionAttributes:
    """Computed attributes for a champion."""
    champion_id: str
    cc_score: float  # 0-1 normalized
    mobility_score: float  # 0-1 normalized
    survivability_early: float  # 0-1 normalized
    survivability_mid: float  # 0-1 normalized
    survivability_late: float  # 0-1 normalized
    waveclear_speed: float  # 0-1 normalized
    gold_dependency: float  # 0-1 normalized
    sustain_score: float  # 0-1 normalized
    range_profile: RangeProfile
    aoe_capability: float  # 0-1 normalized
    dueling_power: float  # 0-1 normalized
    damage_pattern: str  # 'burst', 'sustained', 'poke', 'sustained_aoe'


class AttributeComputer:
    """Computes champion attributes from raw data."""
    
    # CC type weights (hard CC >> soft CC)
    CC_TYPE_WEIGHT = {
        'stun': 1.0,
        'root': 1.0,
        'knock up': 1.0,
        'charm': 1.0,
        'fear': 1.0,
        'taunt': 1.0,
        'suppress': 1.2,  # Ultimate-only, very powerful
        'snare': 1.0,  # Same as root
        'silence': 0.4,  # Soft CC
        'slow': 0.2,  # Soft CC
    }
    
    # CC reliability weights (from config)
    CC_RELIABILITY = {
        'point_click': 1.0,
        'conditional': 0.7,
        'easy_skillshot': 0.6,
        'hard_skillshot': 0.3
    }
    
    # CC target count multipliers
    CC_TARGET_MULTIPLIER = {
        'single': 1.0,
        'small_aoe': 1.5,
        'medium_aoe': 2.0,
        'large_aoe': 2.5
    }
    
    # Mobility type weights
    MOBILITY_WEIGHTS = {
        'dash': 1.0,
        'blink': 1.2,
        'movespeed_buff': 0.5,
        'unstoppable': 1.5
    }
    
    def __init__(self, data_dragon_path: str = "data/raw/data_dragon_champions.json"):
        """Initialize with Data Dragon data."""
        with open(data_dragon_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.champions = data['champions']
        self.version = data['metadata']['version']
        
    def compute_cc_score(self, champion_data: Dict, wiki_data: Optional[Dict] = None) -> float:
        """
        Calculate CC score: Σ(duration × reliability × target_count × uptime)
        
        Formula breakdown:
        - duration: seconds of CC effect
        - reliability: how likely it is to land (point-click=1.0, skillshot=0.3-0.6)
        - target_count: single=1.0, AOE=1.5-2.5
        - uptime: 1 / (cooldown + cast_time)
        
        Args:
            champion_data: Data Dragon champion data
            wiki_data: Optional wiki data for more accurate CC info
            
        Returns:
            Raw CC score (will be normalized later)
        """
        abilities = champion_data['abilities']
        total_cc = 0.0
        
        # Analyze each ability (Q, W, E, R)
        for ability_key in ['Q', 'W', 'E', 'R']:
            if ability_key not in abilities:
                continue
            
            ability = abilities[ability_key]
            
            # Check description for CC keywords
            description = ability.get('description', '').lower()
            
            # Detect CC type and estimate duration
            cc_info = self._detect_cc_in_description(description)
            
            if cc_info:
                cc_type, duration = cc_info
                
                # Get CC type weight (hard CC vs soft CC)
                cc_weight = self.CC_TYPE_WEIGHT.get(cc_type, 0.5)
                
                # Estimate reliability (would be better with wiki data)
                reliability = self._estimate_cc_reliability(description, ability)
                
                # Estimate target count (AOE check)
                target_count = self._estimate_target_count(description)
                
                # Calculate uptime
                cooldown = ability.get('cooldown', [10])
                if isinstance(cooldown, list):
                    # Use max rank cooldown (index -1)
                    cooldown = cooldown[-1] if cooldown else 10
                
                # Assume 0.25s cast time if not specified
                uptime = 1.0 / (cooldown + 0.25) if cooldown > 0 else 0
                
                # Compute contribution with CC type weight
                cc_contribution = cc_weight * duration * reliability * target_count * uptime
                total_cc += cc_contribution
        
        return total_cc
    
    def _detect_cc_in_description(self, description: str) -> Optional[Tuple[str, float]]:
        """
        Detect CC type and duration from ability description.
        
        Returns:
            (cc_type, duration) or None
        """
        # Typical CC durations when not specified in description
        typical_durations = {
            'stun': 1.5, 'root': 2.0, 'knock up': 1.0,
            'charm': 1.5, 'fear': 1.5, 'taunt': 1.5,
            'silence': 2.0, 'slow': 2.0, 'suppress': 2.5, 'snare': 2.0
        }
        
        # CC types with duration patterns (HARD CC FIRST, then soft CC)
        # Order matters! Check specific patterns before generic ones
        cc_patterns = {
            'knock up': r'knock(?:s|ing|ed)?.*?(?:up|into\s+the\s+air|airborne)',
            'suppress': r'suppress(?:es|ing|ed)?',
            'stun': r'stun(?:s|ning|ned)?',
            'root': r'(?:root|bind)(?:s|ing|ed)?',  # root or bind
            'snare': r'snare(?:s|ing|ed)?',
            'charm': r'charm(?:s|ing|ed)?',
            'fear': r'fear(?:s|ing|ed)?',
            'taunt': r'taunt(?:s|ing|ed)?',
            'silence': r'silence(?:s|d)?',
            'slow': r'slow(?:s|ing|ed)?',
        }
        
        # Try to find explicit duration: "for X seconds" or just "X seconds"
        duration_pattern = r'(?:for\s+)?([\d\.]+)\s*(?:second|sec)'
        
        for cc_type, pattern in cc_patterns.items():
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                # Try to find duration near the CC keyword
                duration = typical_durations.get(cc_type, 1.5)
                
                # Look for explicit duration in the sentence containing this CC
                duration_match = re.search(duration_pattern, description, re.IGNORECASE)
                if duration_match:
                    try:
                        duration = float(duration_match.group(1))
                    except ValueError:
                        pass  # Use typical duration
                
                return (cc_type, duration)
        
        return None
    
    def _estimate_cc_reliability(self, description: str, ability: Dict) -> float:
        """Estimate how reliably CC lands."""
        desc_lower = description.lower()
        
        # Check for skillshot indicators
        if any(word in desc_lower for word in ['skillshot', 'line', 'projectile']):
            # Check width/speed for difficulty
            if 'narrow' in desc_lower or 'fast' in desc_lower:
                return self.CC_RELIABILITY['hard_skillshot']
            return self.CC_RELIABILITY['easy_skillshot']
        
        # Check for conditional requirements
        if any(word in desc_lower for word in ['if', 'when', 'after', 'marked']):
            return self.CC_RELIABILITY['conditional']
        
        # Likely point-click or guaranteed
        return self.CC_RELIABILITY['point_click']
    
    def _estimate_target_count(self, description: str) -> float:
        """Estimate number of targets that can be CC'd."""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['all', 'enemies', 'area', 'around', 'nearby']):
            if 'large' in desc_lower or 'all' in desc_lower:
                return self.CC_TARGET_MULTIPLIER['large_aoe']
            elif 'small' in desc_lower:
                return self.CC_TARGET_MULTIPLIER['small_aoe']
            return self.CC_TARGET_MULTIPLIER['medium_aoe']
        
        return self.CC_TARGET_MULTIPLIER['single']
    
    def compute_mobility_score(self, champion_data: Dict) -> float:
        """
        Calculate mobility score from dashes, blinks, and MS buffs.
        
        Args:
            champion_data: Data Dragon champion data
            
        Returns:
            Raw mobility score
        """
        abilities = champion_data['abilities']
        stats = champion_data['stats']
        
        mobility_count = 0.0
        
        # Base movement speed contribution (normalized around 325-400)
        base_ms = stats['base_stats']['move_speed']
        ms_contribution = (base_ms - 325) / 75  # 0 at 325, 1 at 400
        mobility_count += max(0, ms_contribution) * 0.2  # Weight MS lower
        
        # Analyze abilities for mobility spells
        for ability_key in ['Q', 'W', 'E', 'R']:
            if ability_key not in abilities:
                continue
            
            ability = abilities[ability_key]
            description = ability.get('description', '').lower()
            
            # Detect dashes
            if any(word in description for word in ['dash', 'dashes', 'leap', 'lunge']):
                mobility_count += self.MOBILITY_WEIGHTS['dash']
            
            # Detect blinks
            if any(word in description for word in ['blink', 'teleport', 'flash']):
                mobility_count += self.MOBILITY_WEIGHTS['blink']
            
            # Detect movement speed buffs
            if re.search(r'(?:gain|increase).*?movement speed', description):
                mobility_count += self.MOBILITY_WEIGHTS['movespeed_buff']
            
            # Detect unstoppable/CC immunity during dash
            if 'unstoppable' in description or 'cannot be stopped' in description:
                mobility_count += self.MOBILITY_WEIGHTS['unstoppable'] * 0.3
        
        return mobility_count
    
    def compute_survivability(self, champion_data: Dict, game_time: str) -> float:
        """
        Calculate survivability: EHP × threat_evasion × sustain
        
        Formula:
        - EHP = HP × (1 + Armor/100) × (1 + MR/100)
        - Threat_evasion = mobility_score × untargetability
        - Sustain = healing/shielding from abilities
        
        Args:
            champion_data: Data Dragon champion data
            game_time: 'early', 'mid', or 'late'
            
        Returns:
            Raw survivability score
        """
        stats = champion_data['stats']['base_stats']
        
        # Determine level based on game time
        level_map = {'early': 6, 'mid': 11, 'late': 18}
        level = level_map[game_time]
        
        # Calculate stats at level
        hp = stats['hp'] + stats['hp_per_level'] * (level - 1)
        armor = stats['armor'] + stats['armor_per_level'] * (level - 1)
        mr = stats['magic_resist'] + stats['magic_resist_per_level'] * (level - 1)
        
        # Effective HP calculation
        ehp = hp * (1 + armor / 100) * (1 + mr / 100)
        
        # Threat evasion (mobility helps survive)
        mobility = self.compute_mobility_score(champion_data)
        threat_evasion = 1.0 + (mobility * 0.2)  # Mobility adds 0-40% evasion
        
        # Sustain from abilities (shields, heals)
        sustain_mult = 1.0 + self._compute_sustain_contribution(champion_data)
        
        # Combined survivability
        survivability = ehp * threat_evasion * sustain_mult
        
        return survivability
    
    def _compute_sustain_contribution(self, champion_data: Dict) -> float:
        """Calculate healing/shielding contribution to survivability."""
        abilities = champion_data['abilities']
        sustain = 0.0
        
        for ability_key in ['Q', 'W', 'E', 'R', 'Passive']:
            if ability_key not in abilities:
                continue
            
            description = abilities[ability_key].get('description', '').lower()
            
            # Detect healing
            if any(word in description for word in ['heal', 'restore', 'regenerate']):
                sustain += 0.3
            
            # Detect shields
            if 'shield' in description:
                sustain += 0.25
            
            # Detect lifesteal/spellvamp
            if any(word in description for word in ['lifesteal', 'omnivamp', 'spellvamp']):
                sustain += 0.2
        
        return sustain
    
    def compute_waveclear_speed(self, champion_data: Dict) -> float:
        """
        Calculate waveclear speed based on AOE damage abilities.
        
        Args:
            champion_data: Data Dragon champion data
            
        Returns:
            Raw waveclear score
        """
        abilities = champion_data['abilities']
        waveclear = 0.0
        
        for ability_key in ['Q', 'W', 'E', 'R']:
            if ability_key not in abilities:
                continue
            
            ability = abilities[ability_key]
            description = ability.get('description', '').lower()
            
            # Check for AOE damage
            is_aoe = any(word in description for word in [
                'area', 'enemies', 'all', 'nearby', 'around', 'line', 'cone', 'circle'
            ])
            
            if is_aoe:
                # Check cooldown (lower = better waveclear)
                cooldown = ability.get('cooldown', [10])
                if isinstance(cooldown, list):
                    cooldown = cooldown[-1] if cooldown else 10
                
                # Low cooldown AOE = good waveclear
                if cooldown <= 6:
                    waveclear += 1.0
                elif cooldown <= 10:
                    waveclear += 0.6
                else:
                    waveclear += 0.3
        
        return waveclear
    
    def compute_range_profile(self, champion_data: Dict) -> RangeProfile:
        """
        Calculate range profile for the champion.
        
        Args:
            champion_data: Data Dragon champion data
            
        Returns:
            RangeProfile object
        """
        stats = champion_data['stats']['base_stats']
        abilities = champion_data['abilities']
        
        # Auto-attack range from stats
        aa_range = int(stats['attack_range'])
        
        # Find max ability range
        max_ability_range = aa_range
        escape_distance = 0
        
        for ability_key in ['Q', 'W', 'E', 'R']:
            if ability_key not in abilities:
                continue
            
            ability = abilities[ability_key]
            ability_range = ability.get('range', [0])
            
            if isinstance(ability_range, list):
                ability_range = max(ability_range) if ability_range else 0
            
            # Cap absurd ranges (globals like Jinx R, Ashe R, etc.)
            # Anything over 3000 is essentially global, cap at 2500 for practical purposes
            if ability_range > 3000:
                ability_range = 2500
            
            # Check if it's a damaging ability (for threat range)
            description = ability.get('description', '').lower()
            if any(word in description for word in ['damage', 'deals', 'attacks']):
                max_ability_range = max(max_ability_range, int(ability_range))
            
            # Check if it's a mobility spell (for escape)
            if any(word in description for word in ['dash', 'blink', 'leap', 'teleport']):
                # Estimate dash distance (usually 300-800 range)
                estimated_distance = min(int(ability_range), 800) if ability_range > 0 else 400
                escape_distance += estimated_distance
        
        # Threat range is typically slightly less than max ability range
        # Melee champions need to get close
        if aa_range <= 200:  # Melee
            threat_range = min(aa_range + 200, max_ability_range)
        else:  # Ranged
            threat_range = max_ability_range
        
        return RangeProfile(
            auto_attack=aa_range,
            effective_ability=max_ability_range,
            threat=threat_range,
            escape=escape_distance
        )
    
    def compute_gold_dependency(self, champion_data: Dict) -> float:
        """
        Calculate gold dependency: how much champion scales with items vs base kit.
        
        Methodology:
        1. Champion class baseline (Marksmen/Assassins = high, Tanks/Supports = low)
        2. Scaling ratios (AD/AP ratios on abilities)
        3. Base stat strength (high base damage = less item dependent)
        4. Utility vs damage focus (more utility = less gold dependent)
        
        Args:
            champion_data: Data Dragon champion data
            
        Returns:
            Gold dependency score (0 = low, 1 = high)
        """
        stats = champion_data['stats']['base_stats']
        abilities = champion_data['abilities']
        tags = champion_data.get('tags', [])
        
        # 1. Champion class baseline
        class_scores = {
            'Marksman': 0.9,     # ADCs scale heavily with crit/AS items
            'Assassin': 0.7,     # Need lethality/AP items for burst
            'Mage': 0.65,        # Need AP items for damage
            'Fighter': 0.5,      # Mixed - some bruisers scale, some are base kit
            'Tank': 0.3,         # Mostly base stats + tank items (cheaper)
            'Support': 0.25,     # Utility-focused, less gold dependent
        }
        
        base_score = 0.5
        for tag in tags:
            if tag in class_scores:
                base_score = class_scores[tag]
                break  # Use first matching tag
        
        # 2. Count and weight scaling ratios
        total_scaling = 0.0
        ability_count = 0
        
        for ability_key in ['Q', 'W', 'E', 'R']:
            if ability_key not in abilities:
                continue
            
            ability = abilities[ability_key]
            vars_list = ability.get('vars', [])
            
            # Weight by scaling type
            for var in vars_list:
                coef = var.get('coef', [])
                if not isinstance(coef, list):
                    coef = [coef]
                
                # Sum max rank coefficients
                if coef:
                    max_coef = max(coef) if coef else 0
                    
                    # AD scaling typically means physical itemization
                    if 'attack' in var.get('link', '').lower():
                        total_scaling += max_coef * 0.7  # AD items are expensive
                    # AP scaling means AP itemization  
                    elif 'magic' in var.get('link', '').lower() or '@' in var.get('link', ''):
                        total_scaling += max_coef * 0.6  # AP items moderate cost
                    else:
                        total_scaling += max_coef * 0.5
            
            ability_count += 1
        
        # Normalize scaling (typical range 0-10)
        scaling_factor = min(total_scaling / 10.0, 1.0)
        
        # 3. Base stat strength (inverse - high base = low gold need)
        base_damage = stats['attack_damage']
        base_armor = stats['armor']
        hp_level_1 = stats['hp']
        
        # Normalize base strength (strong base stats = less gold dependent)
        # Typical ranges: AD 50-70, Armor 20-40, HP 500-650
        base_strength = ((base_damage - 50) / 20 +
                        (base_armor - 20) / 20 +
                        (hp_level_1 - 500) / 150) / 3
        base_strength = max(0, min(base_strength, 1.0))
        
        # 4. Calculate final score
        # High class score + high scaling + low base stats = high gold dependency
        gold_dependency = (base_score * 0.5 +           # Class baseline (50%)
                          scaling_factor * 0.35 +        # Scaling ratios (35%)
                          (1 - base_strength) * 0.15)    # Inverse base stats (15%)
        
        return max(0.0, min(gold_dependency, 1.0))
    
    def compute_aoe_capability(self, champion_data: Dict) -> float:
        """Calculate AOE damage and CC potential."""
        abilities = champion_data['abilities']
        aoe_score = 0.0
        
        for ability_key in ['Q', 'W', 'E', 'R']:
            if ability_key not in abilities:
                continue
            
            description = abilities[ability_key].get('description', '').lower()
            
            # Check for AOE indicators
            aoe_keywords = ['area', 'enemies', 'all', 'nearby', 'line', 'cone', 'circle']
            if any(word in description for word in aoe_keywords):
                # R abilities weighted higher
                weight = 1.5 if ability_key == 'R' else 1.0
                aoe_score += weight
        
        return aoe_score
    
    def determine_damage_pattern(self, champion_data: Dict) -> str:
        """
        Determine primary damage pattern: burst, sustained, poke, or sustained_aoe.
        
        Logic:
        - DPS: High attack speed, low cooldown autos (ADCs)
        - Sustained: Low cooldown abilities (< 5s) that enable extended fights
        - Burst: Long cooldown, high damage windows
        - Poke: Long range (>900) spammable abilities
        - Sustained AOE: Multiple AOE abilities with decent uptime
        
        Args:
            champion_data: Data Dragon champion data
            
        Returns:
            Damage pattern string
        """
        abilities = champion_data['abilities']
        stats = champion_data['stats']['base_stats']
        
        # Check if champion is auto-attack focused (ADC/marksman pattern)
        base_as = stats['attack_speed']
        as_per_level = stats['attack_speed_per_level']
        attack_range = stats['attack_range']
        
        # ADCs have high attack speed and are ranged
        is_adc_pattern = (base_as >= 0.625 and attack_range >= 500) or \
                        (as_per_level >= 3.0 and attack_range >= 500)
        
        if is_adc_pattern:
            return 'sustained'  # DPS/sustained pattern
        
        # Analyze ability patterns
        short_cd_count = 0  # <= 7s = sustained (adjusted for champions like Fiora)
        spammable_long_range = 0  # Low CD + long range = poke
        high_cd_count = 0  # >= 15s = burst
        aoe_count = 0
        
        for ability_key in ['Q', 'W', 'E']:  # Don't count R for pattern detection
            if ability_key not in abilities:
                continue
            
            ability = abilities[ability_key]
            description = ability.get('description', '').lower()
            
            # Check cooldown
            cooldown = ability.get('cooldown', [10])
            if isinstance(cooldown, list):
                cooldown = cooldown[-1] if cooldown else 10
            
            # Check range (only for non-ultimate abilities)
            ability_range = ability.get('range', [0])
            if isinstance(ability_range, list):
                ability_range = max(ability_range) if ability_range else 0
            
            # Cap absurd ranges (globals)
            if ability_range > 2000:
                ability_range = 0  # Ignore globals for pattern detection
            
            # Classify by cooldown
            if cooldown <= 7:  # Adjusted threshold
                short_cd_count += 1
                # Spammable long range = poke
                if ability_range > 900:
                    spammable_long_range += 1
            elif cooldown >= 15:
                high_cd_count += 1
            
            # Check AOE (must be damaging AOE, not just utility)
            is_aoe = any(word in description for word in ['area', 'all enemies', 'enemies in'])
            
            # More specific AOE indicators (avoid false positives from utility text)
            if 'nearby' in description:
                # Only count as AOE if it explicitly deals damage in area
                if any(dmg in description for dmg in ['damage', 'deals']):
                    is_aoe = True
            
            if is_aoe:
                aoe_count += 1
        
        # Decision tree
        # 1. Poke: Multiple spammable long-range abilities
        if spammable_long_range >= 2:
            return 'poke'
        
        # 2. Sustained AOE: Lots of AOE + sustained damage
        if aoe_count >= 3:
            return 'sustained_aoe'
        
        # 3. Burst: Has high CD mobility/setup spell (suggests burst windows)
        # OR low number of spammable spells (damage is cooldown-gated)
        if high_cd_count >= 1 and short_cd_count <= 1:
            return 'burst'
        
        # 4. Sustained: Multiple short cooldown abilities (skirmishers, bruisers, ADCs)
        if short_cd_count >= 2:
            return 'sustained'
        
        # 5. Default based on cooldown pattern
        if high_cd_count >= 1:
            return 'burst'
        
        # Default to sustained for ambiguous cases
        return 'sustained'
    
    def compute_all_attributes(self, champion_id: str) -> ChampionAttributes:
        """
        Compute all attributes for a champion.
        
        Args:
            champion_id: Champion identifier
            
        Returns:
            ChampionAttributes object
        """
        champion_data = self.champions[champion_id]
        
        # Compute each attribute
        cc_score = self.compute_cc_score(champion_data)
        mobility_score = self.compute_mobility_score(champion_data)
        survivability_early = self.compute_survivability(champion_data, 'early')
        survivability_mid = self.compute_survivability(champion_data, 'mid')
        survivability_late = self.compute_survivability(champion_data, 'late')
        waveclear_speed = self.compute_waveclear_speed(champion_data)
        gold_dependency = self.compute_gold_dependency(champion_data)
        sustain_score = self._compute_sustain_contribution(champion_data)
        range_profile = self.compute_range_profile(champion_data)
        aoe_capability = self.compute_aoe_capability(champion_data)
        damage_pattern = self.determine_damage_pattern(champion_data)
        
        # Dueling power (heuristic: mobility + survivability - gold dependency)
        dueling_power = (mobility_score * 0.3 + 
                        (survivability_mid / 10000) * 0.4 +  # Normalize survivability
                        (1 - gold_dependency) * 0.3)
        
        return ChampionAttributes(
            champion_id=champion_id,
            cc_score=cc_score,
            mobility_score=mobility_score,
            survivability_early=survivability_early,
            survivability_mid=survivability_mid,
            survivability_late=survivability_late,
            waveclear_speed=waveclear_speed,
            gold_dependency=gold_dependency,
            sustain_score=sustain_score,
            range_profile=range_profile,
            aoe_capability=aoe_capability,
            dueling_power=dueling_power,
            damage_pattern=damage_pattern
        )
    
    def compute_all_champions(self, output_path: str = "data/processed/computed_attributes.json") -> Dict:
        """
        Compute attributes for all champions and normalize scores.
        
        Args:
            output_path: Path to save output
            
        Returns:
            Dictionary of all champion attributes
        """
        print(f"Computing attributes for {len(self.champions)} champions...")
        
        # Compute raw attributes for all champions
        all_attributes = {}
        for champion_id in self.champions:
            print(f"Computing {champion_id}...", end=' ')
            attributes = self.compute_all_attributes(champion_id)
            all_attributes[champion_id] = attributes
            print("✓")
        
        # Normalize scores to 0-1 range
        print("\nNormalizing scores...")
        normalized = self._normalize_attributes(all_attributes)
        
        # Save to disk
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON-serializable format
        json_data = {
            'metadata': {
                'version': self.version,
                'champion_count': len(normalized)
            },
            'champions': {}
        }
        
        for champion_id, attrs in normalized.items():
            json_data['champions'][champion_id] = {
                'cc_score': attrs.cc_score,
                'mobility_score': attrs.mobility_score,
                'survivability_early': attrs.survivability_early,
                'survivability_mid': attrs.survivability_mid,
                'survivability_late': attrs.survivability_late,
                'waveclear_speed': attrs.waveclear_speed,
                'gold_dependency': attrs.gold_dependency,
                'sustain_score': attrs.sustain_score,
                'aoe_capability': attrs.aoe_capability,
                'dueling_power': attrs.dueling_power,
                'damage_pattern': attrs.damage_pattern,
                'range_profile': {
                    'auto_attack': attrs.range_profile.auto_attack,
                    'effective_ability': attrs.range_profile.effective_ability,
                    'threat': attrs.range_profile.threat,
                    'escape': attrs.range_profile.escape
                }
            }
        
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved computed attributes to {output}")
        return normalized
    
    def _normalize_attributes(self, all_attributes: Dict[str, ChampionAttributes]) -> Dict[str, ChampionAttributes]:
        """
        Normalize all numeric attributes to 0-1 scale using percentile ranking.
        
        Args:
            all_attributes: Raw computed attributes
            
        Returns:
            Normalized attributes
        """
        # Extract arrays for each attribute
        # NOTE: cc_score is kept as raw value, NOT normalized
        # Raw CC scores are more meaningful for thresholds (e.g., >0.3 = high CC)
        attributes_to_normalize = [
            'mobility_score', 'survivability_early', 
            'survivability_mid', 'survivability_late', 'waveclear_speed',
            'gold_dependency', 'sustain_score', 'aoe_capability', 'dueling_power'
        ]
        
        normalized = {}
        
        for attr_name in attributes_to_normalize:
            values = [getattr(attrs, attr_name) for attrs in all_attributes.values()]
            
            # Use percentile ranking
            percentiles = np.argsort(np.argsort(values)) / (len(values) - 1)
            
            for i, champion_id in enumerate(all_attributes.keys()):
                if champion_id not in normalized:
                    # Copy the original attributes
                    normalized[champion_id] = all_attributes[champion_id]
                
                # Update with normalized value
                setattr(normalized[champion_id], attr_name, float(percentiles[i]))
        
        return normalized


def main():
    """Main execution function."""
    print("=" * 60)
    print("Attribute Computation Engine")
    print("=" * 60)
    
    computer = AttributeComputer()
    computer.compute_all_champions()
    
    print("\n" + "=" * 60)
    print("Computation complete!")
    print("Output: data/processed/computed_attributes.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
