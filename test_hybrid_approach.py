"""
Strategy: Use BOTH data sources optimally:
- Champion.bin: damage numbers, ratios (the good stuff)
- Data Dragon: cooldowns, descriptions, CC info (the reliable stuff)

This hybrid approach gives us accurate damage AND accurate cooldowns.
"""
import json
import requests
from typing import Dict, List, Optional
from pathlib import Path

print("=" * 80)
print("BUILDING COMPLETE SPELL DATABASE")
print("=" * 80)

# Load what we have
with open('data/raw/champion_damage_data.json', 'r') as f:
    damage_data = json.load(f)

with open('data/raw/data_dragon_champions.json', 'r', encoding='utf-8') as f:
    dd_data = json.load(f)

# Test: Can we merge Zed's data?
print("\nTEST: Merging Zed's data from both sources")
print("=" * 80)

zed_damage = damage_data['champions']['Zed']['spells']
zed_dd = dd_data['champions']['Zed']['abilities']

print("\nFrom champion.bin (damage data):")
for spell_key, spell_data in zed_damage.items():
    print(f"  {spell_key}: {spell_data['spell_name']}")
    print(f"    Base damage: {spell_data['base_damage']}")
    print(f"    AD ratio: {spell_data.get('ad_ratio', 0)} / Bonus AD: {spell_data.get('bonus_ad_ratio', 0)}")
    print(f"    Cooldown (champion.bin): {spell_data['cooldown']}")

print("\nFrom Data Dragon (descriptions/cooldowns):")
for spell_key in ['Q', 'W', 'E', 'R']:
    if spell_key in zed_dd:
        spell = zed_dd[spell_key]
        print(f"  {spell_key}: {spell['name']}")
        print(f"    Cooldown (Data Dragon): {spell.get('cooldown', 'N/A')}")
        print(f"    Description: {spell['description'][:100]}...")

# Propose merged structure
print("\n" + "=" * 80)
print("PROPOSED MERGED STRUCTURE")
print("=" * 80)

merged_zed = {}
for spell_key in ['Q', 'W', 'E', 'R']:
    merged_spell = {
        'key': spell_key,
        'name': None,
        'description': None,
        'cooldown': None,
        'base_damage': None,
        'ad_ratio': 0,
        'ap_ratio': 0,
        'bonus_ad_ratio': 0,
        'damage_type': None,
        'mana_cost': None,
        # To be computed:
        'cc_type': None,  # From description parsing
        'cc_duration': None,
        'range': None,  # From Data Dragon
        'is_skillshot': False,
        'is_aoe': False,
        'target_count': 1.0
    }
    
    # Merge from Data Dragon (cooldown, description)
    if spell_key in zed_dd:
        dd_spell = zed_dd[spell_key]
        merged_spell['name'] = dd_spell.get('name')
        merged_spell['description'] = dd_spell.get('description')
        merged_spell['cooldown'] = dd_spell.get('cooldown', [10])[0]  # Use rank 1
        merged_spell['mana_cost'] = dd_spell.get('cost', [0])[0]
        merged_spell['range'] = dd_spell.get('range', [0])[0]
    
    # Merge from champion.bin (damage data)
    if spell_key in zed_damage:
        bin_spell = zed_damage[spell_key]
        base_dmg = bin_spell.get('base_damage', [])
        merged_spell['base_damage'] = base_dmg[0] if base_dmg else None
        merged_spell['ad_ratio'] = bin_spell.get('ad_ratio', 0)
        merged_spell['ap_ratio'] = bin_spell.get('ap_ratio', 0)
        merged_spell['bonus_ad_ratio'] = bin_spell.get('bonus_ad_ratio', 0)
        merged_spell['damage_type'] = bin_spell.get('damage_type', 'physical')
    
    merged_zed[spell_key] = merged_spell

print("\nMerged Zed spells:")
import pprint
pprint.pprint(merged_zed, depth=2)

print("\n" + "=" * 80)
print("VALIDATION")
print("=" * 80)

# Check if this gives us complete data
complete_count = 0
for spell_key, spell in merged_zed.items():
    has_cooldown = spell['cooldown'] is not None
    has_damage = spell['base_damage'] is not None
    is_complete = has_cooldown and (has_damage or spell_key == 'W')  # W might be utility
    
    status = "✓ COMPLETE" if is_complete else "✗ INCOMPLETE"
    print(f"{spell_key}: {status}")
    print(f"  Cooldown: {spell['cooldown']}")
    print(f"  Base damage: {spell['base_damage']}")
    
    if is_complete:
        complete_count += 1

print(f"\nResult: {complete_count}/4 spells have complete data")
