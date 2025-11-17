"""
Large-Scale Draft Simulation with Machine Learning

Generates 10,000 random valid team compositions and uses trained ML models
to predict outcomes, analyze patterns, and validate model performance.
"""

import argparse
import json
import hashlib
import math
import os
import random
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from itertools import count
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import heapq

# Try to import sklearn, provide helpful error if not available
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import cross_val_score, train_test_split
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠ scikit-learn not installed. Will use simple scoring method.")
    print("To install: pip install scikit-learn numpy")


ROLE_ORDER = ['Top', 'Jungle', 'Middle', 'Bottom', 'Support']
DUO_SYNERGY_PAIRS = [
    ('Top', 'Jungle'),
    ('Jungle', 'Middle'),
    ('Bottom', 'Support'),
    ('Support', 'Jungle')
]
MATCHUP_PRIOR_WEIGHT = 4.0  # Laplace smoothing weight for matchup win rates
_MATCHUP_CACHE_DIR = Path("data/cache/matchup_lookup")


def load_data(matches_path: Optional[Path] = None, matchups_path: Optional[Path] = None):
    """Load all necessary data"""
    # Champion data with attributes
    champions_path = Path("data/processed/champion_archetypes.json")
    with open(champions_path, 'r', encoding='utf-8') as f:
        champ_data = json.load(f)
    
    # Real match data
    matches_path = Path(matches_path) if matches_path else Path("data/matches/multi_region_10k.json")
    with open(matches_path, 'r', encoding='utf-8') as f:
        match_data = json.load(f)
    
    # Role-aware relationships
    relationships_path = Path("data/processed/role_aware_relationships.json")
    with open(relationships_path, 'r', encoding='utf-8') as f:
        relationships = json.load(f)
    
    matchup_stats = {"lane_matchups": {}, "duo_matchups": {}}
    matchups_path = Path(matchups_path) if matchups_path else Path("data/matches/lane_duo_stats.json")
    if matchups_path.exists():
        with open(matchups_path, 'r', encoding='utf-8') as f:
            matchup_stats = json.load(f)
    else:
        print(f"⚠ Lane/duo matchup stats not found at {matchups_path}. Continuing without them.")

    return champ_data, match_data['matches'], relationships, matchup_stats


def get_champion_by_position(champ_data: Dict, position: str) -> List[str]:
    """Get all champions that can play a specific position"""
    champions = []
    assignments = champ_data.get('assignments', {})
    
    for champ_name, champ_info in assignments.items():
        viable_positions = champ_info.get('viable_positions', [])
        if position in viable_positions:
            champions.append(champ_name)
    
    return champions


def build_role_champion_pool(champ_data: Dict) -> Dict[str, List[str]]:
    """Pre-compute viable champions per role to avoid repeated scans."""
    return {pos: get_champion_by_position(champ_data, pos) for pos in ROLE_ORDER}


def get_champion_attributes(champ_name: str, champ_data: Dict) -> List[str]:
    """Get attributes for a champion"""
    assignments = champ_data.get('assignments', {})
    return assignments.get(champ_name, {}).get('attributes', [])


def generate_random_team(
    champ_data: Dict,
    role_champions: Optional[Dict[str, List[str]]] = None,
    rng: Optional[random.Random] = None
) -> Dict[str, str]:
    """Generate a random valid team composition"""
    team = {}
    used_champions = set()
    role_pool = role_champions or build_role_champion_pool(champ_data)
    rng = rng or random
    
    for position, candidates in role_pool.items():
        # Remove already used champions
        available = [c for c in candidates if c not in used_champions]
        
        if available:
            champion = rng.choice(available)
            team[position] = champion
            used_champions.add(champion)
    
    return team


def _laplace_rate(successes: float, total: float, prior_weight: float = MATCHUP_PRIOR_WEIGHT) -> float:
    if total <= 0:
        return 0.5
    return (successes + 0.5 * prior_weight) / (total + prior_weight)


_MATCHUP_LOOKUP_CACHE: Dict[int, 'MatchupLookup'] = {}
_MATCHUP_DIGEST_CACHE: Dict[int, str] = {}


class MatchupLookup:
    """Vectorized lookup helper for matchup deltas with disk persistence."""

    def __init__(
        self,
        champ_to_idx: Dict[str, int],
        lane_advantage: Dict[str, np.ndarray],
        lane_games: Dict[str, np.ndarray],
        duo_synergy: Dict[str, np.ndarray],
        duo_games: Dict[str, np.ndarray]
    ) -> None:
        self.champ_to_idx = champ_to_idx
        self.idx_to_champ = [None] * len(champ_to_idx)
        for champ, idx in champ_to_idx.items():
            self.idx_to_champ[idx] = champ
        self.lane_advantage = lane_advantage
        self.lane_games = lane_games
        self.duo_synergy = duo_synergy
        self.duo_games = duo_games

    @classmethod
    def from_stats(cls, matchup_stats: Dict) -> 'MatchupLookup':
        lane_stats = matchup_stats.get('lane_matchups', {}) or {}
        duo_stats = matchup_stats.get('duo_matchups', {}) or {}
        champ_names = set()

        def _collect(entries: Dict[str, Dict]):
            for key in entries.keys():
                left, sep, right = key.partition('|')
                if sep:
                    champ_names.add(left)
                    champ_names.add(right)

        for entries in lane_stats.values():
            _collect(entries)
        for entries in duo_stats.values():
            _collect(entries)

        ordered = sorted(champ_names)
        champ_to_idx = {champ: idx for idx, champ in enumerate(ordered)}
        size = max(len(ordered), 1)

        lane_advantage: Dict[str, np.ndarray] = {}
        lane_games: Dict[str, np.ndarray] = {}
        for role, entries in lane_stats.items():
            advantage = np.zeros((size, size), dtype=np.float32)
            games = np.zeros((size, size), dtype=np.int32)
            for key, entry in entries.items():
                left, sep, right = key.partition('|')
                if not sep:
                    continue
                i = champ_to_idx.get(left)
                j = champ_to_idx.get(right)
                if i is None or j is None:
                    continue
                games[i, j] = entry.get('games', 0)
                if games[i, j]:
                    advantage[i, j] = _laplace_rate(entry.get('blue_wins', 0), games[i, j]) - 0.5
            lane_advantage[role] = advantage
            lane_games[role] = games

        duo_synergy: Dict[str, np.ndarray] = {}
        duo_games: Dict[str, np.ndarray] = {}
        for pair, entries in duo_stats.items():
            synergy = np.zeros((size, size), dtype=np.float32)
            games = np.zeros((size, size), dtype=np.int32)
            for key, entry in entries.items():
                left, sep, right = key.partition('|')
                if not sep:
                    continue
                i = champ_to_idx.get(left)
                j = champ_to_idx.get(right)
                if i is None or j is None:
                    continue
                games[i, j] = entry.get('games', 0)
                if games[i, j]:
                    synergy[i, j] = _laplace_rate(entry.get('wins', 0), games[i, j]) - 0.5
            duo_synergy[pair] = synergy
            duo_games[pair] = games

        return cls(champ_to_idx, lane_advantage, lane_games, duo_synergy, duo_games)

    @classmethod
    def from_file(cls, path: Path) -> 'MatchupLookup':
        with np.load(path, allow_pickle=True) as data:
            champions = data['champions'].tolist()
            champ_to_idx = {champ: idx for idx, champ in enumerate(champions)}
            lane_roles = data['lane_roles'].tolist()
            duo_pairs = data['duo_pairs'].tolist()
            lane_advantage = {
                role: data[f"lane_adv_{role}"] for role in lane_roles
            }
            lane_games = {
                role: data[f"lane_games_{role}"] for role in lane_roles
            }
            duo_synergy = {
                pair: data[f"duo_adv_{pair}"] for pair in duo_pairs
            }
            duo_games = {
                pair: data[f"duo_games_{pair}"] for pair in duo_pairs
            }
        return cls(champ_to_idx, lane_advantage, lane_games, duo_synergy, duo_games)

    def to_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'champions': np.array(self.idx_to_champ, dtype=object),
            'lane_roles': np.array(list(self.lane_advantage.keys()), dtype=object),
            'duo_pairs': np.array(list(self.duo_synergy.keys()), dtype=object)
        }
        for role, matrix in self.lane_advantage.items():
            payload[f"lane_adv_{role}"] = matrix
            payload[f"lane_games_{role}"] = self.lane_games[role]
        for pair, matrix in self.duo_synergy.items():
            payload[f"duo_adv_{pair}"] = matrix
            payload[f"duo_games_{pair}"] = self.duo_games[pair]
        np.savez_compressed(path, **payload)

    def lane(self, role: str, blue: str, red: str, include_details: bool) -> Tuple[float, Optional[Dict[str, float]]]:
        advantage = self.lane_advantage.get(role)
        games_arr = self.lane_games.get(role)
        if advantage is None or games_arr is None:
            return 0.0, None
        i = self.champ_to_idx.get(blue)
        j = self.champ_to_idx.get(red)
        if i is None or j is None:
            return 0.0, None
        games = int(games_arr[i, j])
        if games == 0:
            return 0.0, None
        delta = float(advantage[i, j])
        details = None
        if include_details:
            details = {
                'role': role,
                'blue_champion': blue,
                'red_champion': red,
                'blue_win_rate': delta + 0.5,
                'games_sampled': games
            }
        return delta, details

    def duo(self, pair: str, champ_a: str, champ_b: str, include_details: bool) -> Tuple[float, Optional[Dict[str, float]]]:
        synergy = self.duo_synergy.get(pair)
        games_arr = self.duo_games.get(pair)
        if synergy is None or games_arr is None:
            return 0.0, None
        i = self.champ_to_idx.get(champ_a)
        j = self.champ_to_idx.get(champ_b)
        if i is None or j is None:
            return 0.0, None
        games = int(games_arr[i, j])
        if games == 0:
            return 0.0, None
        delta = float(synergy[i, j])
        details = None
        if include_details:
            details = {
                'pair_key': pair,
                'champions': [champ_a, champ_b],
                'win_rate': delta + 0.5,
                'games_sampled': games
            }
        return delta, details


def lookup_lane_advantage(
    role: str,
    blue_champ: str,
    red_champ: str,
    matchup_stats: Dict,
    include_details: bool = False
) -> Tuple[float, Optional[Dict[str, float]]]:
    lookup = _get_matchup_lookup(matchup_stats)
    if lookup is None:
        return 0.0, None
    return lookup.lane(role, blue_champ, red_champ, include_details)


def lookup_duo_synergy(
    pair_name: str,
    champ_a: str,
    champ_b: str,
    matchup_stats: Dict,
    include_details: bool = False
) -> Tuple[float, Optional[Dict[str, float]]]:
    lookup = _get_matchup_lookup(matchup_stats)
    if lookup is None:
        return 0.0, None
    return lookup.duo(pair_name, champ_a, champ_b, include_details)


def _matchup_digest(matchup_stats: Dict) -> str:
    cache_key = id(matchup_stats)
    digest = _MATCHUP_DIGEST_CACHE.get(cache_key)
    if digest is not None:
        return digest
    serialized = json.dumps(matchup_stats, sort_keys=True, separators=(',', ':')).encode('utf-8')
    digest = hashlib.blake2s(serialized, digest_size=16).hexdigest()
    _MATCHUP_DIGEST_CACHE[cache_key] = digest
    return digest


def _matchup_cache_path(matchup_stats: Dict) -> Path:
    digest = _matchup_digest(matchup_stats)
    return _MATCHUP_CACHE_DIR / f"lookup_{digest}.npz"


def _get_matchup_lookup(matchup_stats: Dict) -> Optional[MatchupLookup]:
    if not matchup_stats:
        return None
    key = id(matchup_stats)
    cached = _MATCHUP_LOOKUP_CACHE.get(key)
    if cached is not None:
        return cached
    cache_path = _matchup_cache_path(matchup_stats)
    lookup: Optional[MatchupLookup] = None
    if cache_path.exists():
        try:
            lookup = MatchupLookup.from_file(cache_path)
        except Exception:
            lookup = None
    if lookup is None:
        lookup = MatchupLookup.from_stats(matchup_stats)
        try:
            lookup.to_file(cache_path)
        except Exception:
            # Ignore cache write failures; in-memory lookup still works
            pass
    _MATCHUP_LOOKUP_CACHE[key] = lookup
    return lookup


def compute_matchup_features(
    blue_team: Dict[str, str],
    red_team: Dict[str, str],
    matchup_stats: Dict,
    include_details: bool = False
) -> Tuple[Dict[str, float], Dict[str, Dict]]:
    """Compute matchup-derived advantages for blue side."""
    features: Dict[str, float] = {}
    details: Dict[str, Dict] = {
        'lane_matchups': {},
        'duo_synergies': {}
    } if include_details else {}

    # Lane vs lane advantages
    for role in ROLE_ORDER:
        blue_champ = blue_team.get(role)
        red_champ = red_team.get(role)
        if not blue_champ or not red_champ:
            continue
        advantage, info = lookup_lane_advantage(
            role,
            blue_champ,
            red_champ,
            matchup_stats,
            include_details=include_details
        )
        if advantage:
            features[f"lane_advantage_{role.lower()}"] = advantage
            if include_details and info:
                details['lane_matchups'][role] = {
                    'blue_champion': blue_champ,
                    'red_champion': red_champ,
                    'advantage': advantage,
                    'blue_win_rate': info['blue_win_rate'],
                    'games_sampled': info['games_sampled']
                }

    # Duo synergy deltas (blue - red)
    if include_details:
        duo_detail_container = details['duo_synergies']

    for role_a, role_b in DUO_SYNERGY_PAIRS:
        pair_key = f"{role_a}_{role_b}"
        blue_synergy = 0.0
        red_synergy = 0.0
        blue_info = None
        red_info = None
        blue_champ_a = blue_team.get(role_a)
        blue_champ_b = blue_team.get(role_b)
        red_champ_a = red_team.get(role_a)
        red_champ_b = red_team.get(role_b)

        if blue_champ_a and blue_champ_b:
            blue_synergy, blue_info = lookup_duo_synergy(
                pair_key,
                blue_champ_a,
                blue_champ_b,
                matchup_stats,
                include_details=include_details
            )
        if red_champ_a and red_champ_b:
            red_synergy, red_info = lookup_duo_synergy(
                pair_key,
                red_champ_a,
                red_champ_b,
                matchup_stats,
                include_details=include_details
            )

        delta = blue_synergy - red_synergy
        if delta:
            features[f"duo_synergy_delta_{pair_key.lower()}"] = delta
            if include_details:
                duo_detail_container[pair_key] = {
                    'blue_champions': [blue_champ_a, blue_champ_b],
                    'red_champions': [red_champ_a, red_champ_b],
                    'delta': delta,
                    'blue_win_rate': blue_info['win_rate'] if blue_info else None,
                    'red_win_rate': red_info['win_rate'] if red_info else None,
                    'blue_games': blue_info['games_sampled'] if blue_info else 0,
                    'red_games': red_info['games_sampled'] if red_info else 0
                }

    return features, details if include_details else {}


def build_match_feature_dict(
    blue_team: Dict[str, str],
    red_team: Dict[str, str],
    champ_data: Dict,
    matchup_stats: Dict,
    include_details: bool = False
) -> Tuple[Dict[str, float], Dict[str, Dict]]:
    """Combine team composition features with matchup deltas."""
    blue_features = extract_features_from_team(blue_team, champ_data)
    red_features = extract_features_from_team(red_team, champ_data)

    diff_features: Dict[str, float] = {}
    for name in set(blue_features) | set(red_features):
        diff_features[f"team_{name}"] = blue_features.get(name, 0.0) - red_features.get(name, 0.0)

    matchup_features, matchup_details = compute_matchup_features(
        blue_team,
        red_team,
        matchup_stats,
        include_details=include_details
    )
    diff_features.update(matchup_features)
    return diff_features, matchup_details


_CHAMP_ATTR_CACHE: Dict[int, Dict[str, Tuple[Tuple[str, ...], frozenset]]] = {}


def _get_champion_attribute_cache(champ_data: Dict) -> Dict[str, Tuple[Tuple[str, ...], frozenset]]:
    """Cache champion attribute tuples/sets per champion_data payload."""
    key = id(champ_data)
    cached = _CHAMP_ATTR_CACHE.get(key)
    if cached is not None:
        return cached
    assignments = champ_data.get('assignments', {})
    champ_cache: Dict[str, Tuple[Tuple[str, ...], frozenset]] = {}
    for champion, info in assignments.items():
        attrs = tuple(info.get('attributes', []) or [])
        champ_cache[champion] = (attrs, frozenset(attrs))
    _CHAMP_ATTR_CACHE[key] = champ_cache
    return champ_cache


def extract_features_from_team(team: Dict[str, str], champ_data: Dict) -> Dict[str, float]:
    """Extract normalized feature counts and pair synergies for a team."""
    features = defaultdict(float)
    champ_cache = _get_champion_attribute_cache(champ_data)

    attr_counter: Counter[str] = Counter()
    role_attr_sets: Dict[str, frozenset] = {}

    for role, champion in team.items():
        attrs, attr_set = champ_cache.get(champion, ((), frozenset()))
        if attrs:
            attr_counter.update(attrs)
        role_attr_sets[role] = attr_set

    if attr_counter:
        for attr, count in attr_counter.items():
            features[f"attr_{attr}"] += count / 5.0

    roles = list(role_attr_sets.keys())
    for i in range(len(roles)):
        for j in range(i + 1, len(roles)):
            role1, role2 = roles[i], roles[j]
            shared = role_attr_sets[role1] & role_attr_sets[role2]
            if shared:
                features[f"role_pair_{role1}_{role2}_shared"] = len(shared) / 10.0

    damage_types = ['damage_physical', 'damage_magic', 'damage_mixed', 'damage_true']
    for dt in damage_types:
        if dt in attr_counter:
            features[f"damage_{dt}"] = attr_counter[dt] / 5.0

    ranges = ['range_melee', 'range_short', 'range_medium', 'range_long']
    for r in ranges:
        if r in attr_counter:
            features[f"range_{r}"] = attr_counter[r] / 5.0

    mobilities = ['mobility_high', 'mobility_medium', 'mobility_low']
    for m in mobilities:
        if m in attr_counter:
            features[f"mobility_{m}"] = attr_counter[m] / 5.0

    scalings = ['scaling_early', 'scaling_mid', 'scaling_late']
    for s in scalings:
        if s in attr_counter:
            features[f"scaling_{s}"] = attr_counter[s] / 5.0

    cc_types = ['cc_hard', 'cc_soft', 'cc_aoe', 'cc_single']
    for cc in cc_types:
        if cc in attr_counter:
            features[f"cc_{cc}"] = attr_counter[cc] / 5.0

    return features


def features_to_vector(features: Dict[str, float], feature_names: List[str]) -> List[float]:
    """Convert feature dict to ordered vector"""
    return [features.get(name, 0.0) for name in feature_names]


def train_ml_models(matches: List[Dict], champ_data: Dict, matchup_stats: Dict):
    """
    Train multiple ML models on real match data
    
    Returns trained models and feature names
    """
    print("Extracting features from real matches...")
    
    feature_dicts = []
    y = []  # 1 for blue win, 0 for red win

    for match in matches:
        blue_team = match['blue_team']
        red_team = match['red_team']
        winner = match['winner']

        match_features, _ = build_match_feature_dict(blue_team, red_team, champ_data, matchup_stats)
        feature_dicts.append(match_features)
        y.append(1 if winner == 'blue' else 0)

    all_feature_names = set()
    for features in feature_dicts:
        all_feature_names.update(features.keys())
    feature_names = sorted(all_feature_names)

    print(f"✓ Extracted {len(feature_names)} features from {len(matches)} matches")

    X_vectors = [features_to_vector(f, feature_names) for f in feature_dicts]

    blue_win_prior = sum(y) / len(y) if y else 0.5

    if not SKLEARN_AVAILABLE:
        return None, feature_names, X_vectors, y, blue_win_prior

    X = np.array(X_vectors)
    y = np.array(y)
    
    print("\nTraining ML models...")
    
    # Train multiple models
    models = {}
    
    # 1. Logistic Regression
    print("  Training Logistic Regression...")
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X, y)
    models['logistic'] = lr
    
    # 2. Random Forest
    print("  Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X, y)
    models['random_forest'] = rf
    
    # 3. Gradient Boosting
    print("  Training Gradient Boosting...")
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
    gb.fit(X, y)
    models['gradient_boosting'] = gb
    
    print("\n✓ Trained 3 models")
    
    # Cross-validation scores
    print("\nCross-Validation Scores (5-fold):")
    for name, model in models.items():
        scores = cross_val_score(model, X, y, cv=5)
        print(f"  {name}: {scores.mean():.3f} (±{scores.std():.3f})")
    
    return models, feature_names, X, y, blue_win_prior


def predict_match_ml(
    blue_team: Dict,
    red_team: Dict,
    models: Dict,
    feature_names: List[str],
    champ_data: Dict,
    matchup_stats: Dict
) -> Dict:
    """Predict match outcome using ML models"""

    match_features, explanation = build_match_feature_dict(
        blue_team,
        red_team,
        champ_data,
        matchup_stats,
        include_details=True
    )
    diff = features_to_vector(match_features, feature_names)
    
    if SKLEARN_AVAILABLE and models:
        X = np.array([diff])
        
        predictions = {}
        probabilities = {}
        
        for name, model in models.items():
            pred = model.predict(X)[0]
            prob = model.predict_proba(X)[0]
            
            predictions[name] = 'blue' if pred == 1 else 'red'
            probabilities[name] = {
                'blue': float(prob[1]),
                'red': float(prob[0])
            }
        
        # Ensemble prediction (majority vote)
        blue_votes = sum(1 for p in predictions.values() if p == 'blue')
        ensemble_pred = 'blue' if blue_votes >= 2 else 'red'
        
        # Average probabilities
        avg_blue_prob = np.mean([p['blue'] for p in probabilities.values()])
        
        return {
            'ensemble_prediction': ensemble_pred,
            'blue_probability': float(avg_blue_prob),
            'red_probability': float(1 - avg_blue_prob),
            'individual_predictions': predictions,
            'individual_probabilities': probabilities,
            'feature_breakdown': explanation
        }
    else:
        # Simple fallback: sum of feature differences
        total_diff = sum(diff)
        prediction = 'blue' if total_diff > 0 else 'red'
        
        # Convert to pseudo-probability using sigmoid
        prob = 1 / (1 + math.exp(-total_diff))
        
        return {
            'ensemble_prediction': prediction,
            'blue_probability': prob,
            'red_probability': 1 - prob,
            'individual_predictions': {'simple': prediction},
            'individual_probabilities': {'simple': {'blue': prob, 'red': 1 - prob}},
            'feature_breakdown': explanation
        }


class PredictionAggregator:
    """Streaming aggregator so we can simulate millions of drafts without O(n) memory."""

    def __init__(self, sample_limit: int = 2000, extremes_limit: int = 10):
        self.sample_limit = sample_limit
        self.extremes_limit = extremes_limit
        self.sample_games: List[Dict] = []
        self.total_games = 0
        self.blue_wins = 0
        self.confidence_sum = 0.0
        self.blue_prob_sum = 0.0
        self.high_conf = 0
        self.medium_conf = 0
        self.low_conf = 0
        self._counter = count(1)
        self._top_blue: List[Tuple[float, int, Dict]] = []
        self._top_red: List[Tuple[float, int, Dict]] = []
        self._closest: List[Tuple[float, int, Dict]] = []

    def _push_descending(self, heap: List[Tuple[float, int, Dict]], key: float, game: Dict):
        entry = (key, next(self._counter), game)
        if len(heap) < self.extremes_limit:
            heapq.heappush(heap, entry)
            return
        if key > heap[0][0]:
            heapq.heapreplace(heap, entry)

    def add_game(self, game: Dict):
        prediction = game['prediction']
        blue_prob = prediction['blue_probability']
        red_prob = prediction['red_probability']
        confidence = max(blue_prob, red_prob)

        self.total_games += 1
        if prediction['ensemble_prediction'] == 'blue':
            self.blue_wins += 1
        self.confidence_sum += confidence
        self.blue_prob_sum += blue_prob

        if confidence >= 0.6:
            self.high_conf += 1
        elif confidence >= 0.55:
            self.medium_conf += 1
        else:
            self.low_conf += 1

        if len(self.sample_games) < self.sample_limit:
            self.sample_games.append(game)

        self._push_descending(self._top_blue, blue_prob, game)
        self._push_descending(self._top_red, red_prob, game)

        closeness = abs(blue_prob - 0.5)
        entry = (-closeness, next(self._counter), game)
        if len(self._closest) < self.extremes_limit:
            heapq.heappush(self._closest, entry)
        else:
            if -closeness > self._closest[0][0]:
                heapq.heapreplace(self._closest, entry)

    def _ordered(self, heap: List[Tuple[float, int, Dict]], reverse: bool = True) -> List[Dict]:
        if not heap:
            return []
        return [entry[2] for entry in sorted(heap, key=lambda x: x[0], reverse=reverse)]

    def export_state(self) -> Dict:
        return {
            'total_games': self.total_games,
            'blue_wins': self.blue_wins,
            'confidence_sum': self.confidence_sum,
            'blue_prob_sum': self.blue_prob_sum,
            'high_conf': self.high_conf,
            'medium_conf': self.medium_conf,
            'low_conf': self.low_conf,
            'samples': list(self.sample_games),
            'top_blue': self._ordered(self._top_blue, reverse=True),
            'top_red': self._ordered(self._top_red, reverse=True),
            'closest': [entry[2] for entry in sorted(self._closest, key=lambda x: x[0], reverse=True)]
        }

    def finalize(self) -> Dict:
        return build_analysis_from_states([self.export_state()], self.sample_limit, self.extremes_limit)


def build_analysis_from_states(states: List[Dict], sample_limit: int, extremes_limit: int) -> Dict:
    total_games = sum(state.get('total_games', 0) for state in states)
    if total_games == 0:
        return {}

    blue_wins = sum(state.get('blue_wins', 0) for state in states)
    confidence_sum = sum(state.get('confidence_sum', 0.0) for state in states)
    blue_prob_sum = sum(state.get('blue_prob_sum', 0.0) for state in states)
    high_conf = sum(state.get('high_conf', 0) for state in states)
    medium_conf = sum(state.get('medium_conf', 0) for state in states)
    low_conf = sum(state.get('low_conf', 0) for state in states)

    def _collect(key: str) -> List[Dict]:
        aggregated: List[Dict] = []
        for state in states:
            aggregated.extend(state.get(key, []))
        return aggregated

    samples = _collect('samples')[:sample_limit]

    def _select(games: List[Dict], key_func, reverse=True) -> List[Dict]:
        if not games:
            return []
        return sorted(games, key=key_func, reverse=reverse)[:extremes_limit]

    top_blue = _select(
        _collect('top_blue'),
        key_func=lambda g: g['prediction']['blue_probability'],
        reverse=True
    )
    top_red = _select(
        _collect('top_red'),
        key_func=lambda g: g['prediction']['red_probability'],
        reverse=True
    )
    closest = _select(
        _collect('closest'),
        key_func=lambda g: abs(g['prediction']['blue_probability'] - 0.5),
        reverse=False
    )

    blue_win_rate = blue_wins / total_games
    avg_confidence = confidence_sum / total_games

    return {
        'total_games': total_games,
        'blue_wins_predicted': blue_wins,
        'red_wins_predicted': total_games - blue_wins,
        'blue_win_rate': blue_win_rate,
        'average_confidence': avg_confidence,
        'confidence_distribution': {
            'high_confidence_60_plus': high_conf,
            'medium_confidence_55_60': medium_conf,
            'low_confidence_below_55': low_conf
        },
        'avg_blue_probability': blue_prob_sum / total_games,
        'most_confident_blue': top_blue,
        'most_confident_red': top_red,
        'closest_games': closest,
        'samples': samples
    }


def format_duration(seconds: float) -> str:
    if seconds is None or not math.isfinite(seconds) or seconds <= 0:
        return "calculating..."
    seconds = int(seconds)
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {sec}s"
    if minutes:
        return f"{minutes}m {sec}s"
    return f"{sec}s"


def save_checkpoint(analysis: Dict, games_completed: int, total_games: int,
                    sample_limit: int, extremes_limit: int):
    if not analysis:
        return
    checkpoint_dir = Path("data/simulations/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        'checkpoint_games_completed': games_completed,
        'total_target_games': total_games,
        'timestamp': datetime.now(UTC).isoformat(),
        'sample_limit': sample_limit,
        'extremes_limit': extremes_limit,
        'analysis': analysis
    }
    checkpoint_path = checkpoint_dir / f"simulation_checkpoint_{games_completed:07d}.json"
    with checkpoint_path.open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2)
    print(f"  💾 Checkpoint saved ({games_completed:,}/{total_games:,}) -> {checkpoint_path}")


def _simulate_prediction_chunk(
    start_game_id: int,
    n_games: int,
    champ_data: Dict,
    models: Dict,
    feature_names: List[str],
    matchup_stats: Dict,
    sample_limit: int,
    extremes_limit: int,
    role_champions: Dict[str, List[str]],
    seed: int
) -> Dict:
    rng = random.Random(seed)
    aggregator = PredictionAggregator(sample_limit=sample_limit, extremes_limit=extremes_limit)

    for i in range(n_games):
        game_id = start_game_id + i
        blue_team = generate_random_team(champ_data, role_champions, rng)
        red_team = generate_random_team(champ_data, role_champions, rng)
        prediction = predict_match_ml(blue_team, red_team, models, feature_names, champ_data, matchup_stats)

        game = {
            'game_id': game_id,
            'blue_team': blue_team,
            'red_team': red_team,
            'prediction': prediction
        }
        aggregator.add_game(game)

    return aggregator.export_state()


def simulate_predictions(
    n_games: int,
    champ_data: Dict,
    models: Dict,
    feature_names: List[str],
    matchup_stats: Dict,
    sample_limit: int = 2000,
    extremes_limit: int = 10,
    workers: int = 1,
    chunk_size: int = 50000,
    checkpoint_interval: int = 100000
) -> Dict:
    print(f"\nGenerating {n_games:,} random games...")
    role_champions = build_role_champion_pool(champ_data)
    start_time = time.perf_counter()

    if workers <= 1:
        aggregator = PredictionAggregator(sample_limit=sample_limit, extremes_limit=extremes_limit)
        progress_interval = 1000 if n_games <= 10000 else 50000
        next_checkpoint = checkpoint_interval if checkpoint_interval else float('inf')

        for i in range(n_games):
            blue_team = generate_random_team(champ_data, role_champions)
            red_team = generate_random_team(champ_data, role_champions)
            prediction = predict_match_ml(blue_team, red_team, models, feature_names, champ_data, matchup_stats)

            game = {
                'game_id': i + 1,
                'blue_team': blue_team,
                'red_team': red_team,
                'prediction': prediction
            }
            aggregator.add_game(game)

            games_done = i + 1

            if games_done % progress_interval == 0 or games_done == n_games:
                elapsed = time.perf_counter() - start_time
                rate = games_done / elapsed if elapsed else 0
                remaining = n_games - games_done
                eta_seconds = remaining / rate if rate else float('inf')
                eta_text = format_duration(eta_seconds)
                print(f"  Generated {games_done:,}/{n_games:,} games... ETA: {eta_text}")

            if checkpoint_interval and games_done >= next_checkpoint:
                snapshot = aggregator.finalize()
                save_checkpoint(snapshot, games_done, n_games, sample_limit, extremes_limit)
                next_checkpoint += checkpoint_interval

        print(f"✓ Generated and predicted {n_games:,} games")
        return aggregator.finalize()

    # Multi-process path
    workers = max(1, workers)
    chunk_size = max(1000, chunk_size)
    chunk_sample_limit = sample_limit if sample_limit <= 0 else max(1, min(sample_limit, sample_limit // workers or sample_limit))
    partial_states: List[Dict] = []
    games_completed = 0
    checkpoints_written = 0

    chunk_specs = []
    next_game_id = 1
    while next_game_id <= n_games:
        remaining = n_games - next_game_id + 1
        size = remaining if remaining < chunk_size else chunk_size
        chunk_specs.append((next_game_id, size))
        next_game_id += size

    seed_rng = random.Random(42)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = []
        for start_id, size in chunk_specs:
            seed = seed_rng.randrange(1, 10**9)
            futures.append(
                executor.submit(
                    _simulate_prediction_chunk,
                    start_id,
                    size,
                    champ_data,
                    models,
                    feature_names,
                    matchup_stats,
                    chunk_sample_limit,
                    extremes_limit,
                    role_champions,
                    seed
                )
            )

        for future in as_completed(futures):
            state = future.result()
            partial_states.append(state)
            games_completed += state.get('total_games', 0)

            elapsed = time.perf_counter() - start_time
            rate = games_completed / elapsed if elapsed else 0
            eta_seconds = (n_games - games_completed) / rate if rate else float('inf')
            eta_text = format_duration(eta_seconds)
            print(f"  Collected {games_completed:,}/{n_games:,} games across workers... ETA: {eta_text}")

            while checkpoint_interval and games_completed >= (checkpoints_written + 1) * checkpoint_interval:
                checkpoints_written += 1
                checkpoint_games = min(checkpoints_written * checkpoint_interval, games_completed)
                snapshot = build_analysis_from_states(partial_states, sample_limit, extremes_limit)
                save_checkpoint(snapshot, checkpoint_games, n_games, sample_limit, extremes_limit)

    analysis = build_analysis_from_states(partial_states, sample_limit, extremes_limit)
    print(f"✓ Generated and predicted {n_games:,} games (multi-process)")
    return analysis


def main():
    parser = argparse.ArgumentParser(description="Train ML models and run large-scale draft simulations")
    parser.add_argument('--matches-path', default='data/matches/euw1_matches.json', help='Path to real match dataset JSON')
    parser.add_argument('--simulations', type=int, default=10000, help='Number of random drafts to simulate')
    parser.add_argument('--sample-limit', type=int, default=2000, help='Number of simulated games to retain for examples')
    parser.add_argument('--extremes-limit', type=int, default=10, help='How many extreme examples to keep per bucket')
    default_workers = max(1, (os.cpu_count() or 1) // 2)
    parser.add_argument('--workers', type=int, default=default_workers, help='Number of worker processes for simulation')
    parser.add_argument('--chunk-size', type=int, default=50000, help='Games per worker chunk when running in parallel')
    parser.add_argument('--checkpoint-interval', type=int, default=100000, help='Games between checkpoints (set 0 to disable)')
    parser.add_argument('--matchups-path', default='data/matches/lane_duo_stats.json', help='Lane/duo matchup stats JSON path')
    args = parser.parse_args()
    print("=" * 80)
    print("LARGE-SCALE DRAFT SIMULATION WITH MACHINE LEARNING")
    print("=" * 80)
    print()
    
    # Load data
    print("Loading data...")
    champ_data, matches, relationships, matchup_stats = load_data(Path(args.matches_path), Path(args.matchups_path))
    print(f"✓ Loaded {len(matches)} real matches")
    print(f"✓ Loaded {len(champ_data.get('assignments', {}))} champions")
    print()
    
    # Train ML models
    models, feature_names, X, y, blue_win_prior = train_ml_models(matches, champ_data, matchup_stats)
    
    if SKLEARN_AVAILABLE and models:
        # Evaluate on real match data
        print("\n" + "=" * 80)
        print("MODEL PERFORMANCE ON REAL MATCHES")
        print("=" * 80)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        for name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            accuracy = (y_pred == y_test).mean()
            
            print(f"\n{name.upper()}:")
            print(f"  Test Accuracy: {accuracy:.1%}")
            
            # Classification report
            print(f"\n{classification_report(y_test, y_pred, target_names=['Red Win', 'Blue Win'])}")
    
    # Generate and predict 10,000 games
    print("\n" + "=" * 80)
    print("SIMULATING 10,000 RANDOM GAMES")
    print("=" * 80)
    
    n_games = args.simulations
    analysis = simulate_predictions(
        n_games,
        champ_data,
        models,
        feature_names,
        matchup_stats,
        sample_limit=args.sample_limit,
        extremes_limit=args.extremes_limit,
        workers=args.workers,
        chunk_size=args.chunk_size,
        checkpoint_interval=args.checkpoint_interval
    )
    
    # Analyze predictions
    print("\n" + "=" * 80)
    print("PREDICTION ANALYSIS")
    print("=" * 80)
    
    print("\nAnalyzing predictions...")
    print(f"\nTotal games simulated: {analysis['total_games']:,}")
    print(f"\nPrediction Distribution:")
    print(f"  Blue wins predicted: {analysis['blue_wins_predicted']:,} ({analysis['blue_win_rate']:.1%})")
    print(f"  Red wins predicted: {analysis['red_wins_predicted']:,} ({1 - analysis['blue_win_rate']:.1%})")
    print(f"\nAverage Confidence: {analysis['average_confidence']:.1%}")
    print(f"\nConfidence Distribution:")
    print(f"  High confidence (≥60%): {analysis['confidence_distribution']['high_confidence_60_plus']:,} games")
    print(f"  Medium confidence (55-60%): {analysis['confidence_distribution']['medium_confidence_55_60']:,} games")
    print(f"  Low confidence (<55%): {analysis['confidence_distribution']['low_confidence_below_55']:,} games")
    
    print("\n" + "-" * 80)
    print("Sample High-Confidence Blue Wins:")
    print("-" * 80)
    for i, game in enumerate(analysis['most_confident_blue'][:3], 1):
        print(f"\n{i}. Game #{game['game_id']} - Blue {game['prediction']['blue_probability']:.1%}")
        print(f"   Blue: {', '.join(f'{role}={champ}' for role, champ in game['blue_team'].items())}")
        print(f"   Red:  {', '.join(f'{role}={champ}' for role, champ in game['red_team'].items())}")
    
    print("\n" + "-" * 80)
    print("Sample Closest Games (Most Balanced):")
    print("-" * 80)
    for i, game in enumerate(analysis['closest_games'][:3], 1):
        print(f"\n{i}. Game #{game['game_id']} - Blue {game['prediction']['blue_probability']:.1%}")
        print(f"   Blue: {', '.join(f'{role}={champ}' for role, champ in game['blue_team'].items())}")
        print(f"   Red:  {', '.join(f'{role}={champ}' for role, champ in game['red_team'].items())}")
    
    # Save results
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    
    # Save full results (first 1000 games with details)
    output = {
        'metadata': {
            'total_games': n_games,
            'real_matches_used_for_training': len(matches),
            'features_extracted': len(feature_names),
            'models_used': list(models.keys()) if models else ['simple_scoring']
        },
        'analysis': {
            'prediction_distribution': {
                'blue_wins': analysis['blue_wins_predicted'],
                'red_wins': analysis['red_wins_predicted'],
                'blue_win_rate': analysis['blue_win_rate']
            },
            'confidence_metrics': {
                'average_confidence': analysis['average_confidence'],
                'high_confidence_games': analysis['confidence_distribution']['high_confidence_60_plus'],
                'medium_confidence_games': analysis['confidence_distribution']['medium_confidence_55_60'],
                'low_confidence_games': analysis['confidence_distribution']['low_confidence_below_55']
            }
        },
        'sample_games': {
            'high_confidence_blue': analysis['most_confident_blue'][:10],
            'high_confidence_red': analysis['most_confident_red'][:10],
            'closest_games': analysis['closest_games'][:10],
            'random_samples': analysis.get('samples', [])
        }
    }
    
    output_path = Path("data/simulations/simulation_10k_games.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Saved simulation results to: {output_path}")
    
    # Save trained models for ensemble prediction
    if models:
        import pickle
        models_path = Path("data/simulations/trained_models.pkl")
        # Save both models and feature names
        model_data = {
            'models': models,
            'feature_names': feature_names,
            'blue_side_prior': blue_win_prior
        }
        with open(models_path, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"✓ Saved trained models to: {models_path}")
    
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"✓ Trained ML models on {len(matches)} real Challenger matches")
    print(f"✓ Generated {n_games:,} random valid team compositions")
    print(f"✓ Predicted outcomes with {analysis['average_confidence']:.1%} average confidence")
    print(f"✓ Model shows {analysis['blue_win_rate']:.1%} vs {1 - analysis['blue_win_rate']:.1%} split")
    print(f"✓ {analysis['confidence_distribution']['high_confidence_60_plus']:,} games with ≥60% confidence")
    print()
    
    if abs(analysis['blue_win_rate'] - 0.5) < 0.05:
        print("✅ Model is well-balanced (within 5% of 50/50)")
    else:
        print(f"⚠ Model shows {abs(analysis['blue_win_rate'] - 0.5):.1%} deviation from balance")
    
    print()


if __name__ == "__main__":
    main()
