"""High-throughput sampling helpers for mass simulation."""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Tuple


def build_role_pools_indices(
    role_pools: Dict[str, List[str]],
    role_order: List[str]
) -> Tuple[Dict[str, np.ndarray], List[str]]:
    role_arrays: Dict[str, np.ndarray] = {}
    champion_to_idx: Dict[str, int] = {}
    next_idx = 0
    for role in role_order:
        champs = role_pools.get(role, [])
        unique = []
        for champ in champs:
            if champ not in champion_to_idx:
                champion_to_idx[champ] = next_idx
                next_idx += 1
            unique.append(champ)
        role_arrays[role] = np.array([champion_to_idx[c] for c in unique], dtype=np.int32)
    idx_to_champion = [None] * next_idx
    for champ, idx in champion_to_idx.items():
        idx_to_champion[idx] = champ
    return role_arrays, idx_to_champion


def sample_teams_numpy(
    generator: np.random.Generator,
    role_arrays: Dict[str, np.ndarray],
    idx_to_champion: List[str],
    role_order: List[str],
    batch_size: int
) -> Tuple[List[List[str]], List[List[str]]]:
    champion_count = len(idx_to_champion)
    blue_mask = np.zeros(champion_count, dtype=bool)
    red_mask = np.zeros(champion_count, dtype=bool)
    ordered_pools = [role_arrays.get(role) for role in role_order]

    blue_teams: List[List[str]] = []
    red_teams: List[List[str]] = []
    for _ in range(batch_size):
        blue_indices: List[int] = []
        red_indices: List[int] = []
        for pool in ordered_pools:
            if pool is None or pool.size == 0:
                continue
            blue_masked = pool[~blue_mask[pool]]
            if blue_masked.size == 0:
                blue_masked = pool
            blue_idx = int(generator.choice(blue_masked))
            blue_mask[blue_idx] = True
            blue_indices.append(blue_idx)

            red_masked = pool[~red_mask[pool]]
            if red_masked.size == 0:
                red_masked = pool
            red_idx = int(generator.choice(red_masked))
            red_mask[red_idx] = True
            red_indices.append(red_idx)

        blue_teams.append([idx_to_champion[idx] for idx in blue_indices])
        red_teams.append([idx_to_champion[idx] for idx in red_indices])

        for idx in blue_indices:
            blue_mask[idx] = False
        for idx in red_indices:
            red_mask[idx] = False

    return blue_teams, red_teams