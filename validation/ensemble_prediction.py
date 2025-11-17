"""
Ensemble Prediction System

Combines Logistic Regression, Random Forest, and Gradient Boosting models
using weighted averaging based on prediction confidence.

Philosophy: Theoretical archetypal analysis, not live data competition.
"""

import json
import math
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

try:
    from validation.ml_simulation import build_match_feature_dict, features_to_vector
except ModuleNotFoundError:
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).parent.parent))
    from validation.ml_simulation import build_match_feature_dict, features_to_vector


BLUE_PRIOR_FALLBACK = 0.4545
EPSILON = 1e-6


def _logit(value: float) -> float:
    """Numerically stable logit."""
    clipped = min(max(value, EPSILON), 1 - EPSILON)
    return math.log(clipped / (1 - clipped))


def _sigmoid(value: float) -> float:
    """Numerically stable sigmoid."""
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


@dataclass
class PredictionResult:
    """Result from ensemble prediction."""
    winner: str  # "blue" or "red"
    confidence: float  # 0-1
    blue_win_probability: float  # 0-1
    red_win_probability: float  # 0-1
    model_breakdown: Dict[str, float]  # Individual model predictions
    reasoning: List[str]  # Archetypal reasoning
    feature_breakdown: Optional[Dict] = None


class EnsemblePredictor:
    """
    Ensemble predictor combining multiple ML models with archetypal analysis.
    
    Weights models by their cross-validation performance and prediction confidence.
    """
    
    def __init__(
        self,
        models: Dict,  # {"lr": model, "rf": model, "gb": model}
        feature_names: List[str],  # Feature names used during training
        champion_data: Dict,
        attribute_data: Dict,
        relationships: Dict,
        matchup_stats: Optional[Dict],
        blue_side_prior: Optional[float] = None,
        logit_shift: float = 0.0
    ):
        self.models = models
        self.feature_names = feature_names
        self.champion_data = champion_data
        self.attribute_data = attribute_data
        self.relationships = relationships
        self.matchup_stats = matchup_stats or {}
        fallback = BLUE_PRIOR_FALLBACK
        self.blue_side_prior = blue_side_prior if blue_side_prior is not None else fallback
        self.logit_shift = logit_shift
        self.base_weights = {
            "logistic": 0.543,
            "gradient_boosting": 0.500,
            "random_forest": 0.505
        }
        total = sum(self.base_weights.values())
        self.base_weights = {k: v / total for k, v in self.base_weights.items()}
        
    def _to_lane_map(self, team: List[str], roles: List[str]) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        for champion, role in zip(team, roles):
            if not champion:
                continue
            lane = None
            if isinstance(role, str) and role:
                lane = role.title()
            if lane is None:
                continue
            if lane not in mapping:
                mapping[lane] = champion
        return mapping

    def build_feature_vector(
        self,
        blue_team: List[str],
        blue_roles: List[str],
        red_team: List[str],
        red_roles: List[str],
        *,
        include_feature_breakdown: bool = True
    ) -> Tuple[List[float], Optional[Dict]]:
        blue_team_dict = self._to_lane_map(blue_team, blue_roles)
        red_team_dict = self._to_lane_map(red_team, red_roles)
        feature_dict, feature_breakdown = build_match_feature_dict(
            blue_team_dict,
            red_team_dict,
            self.champion_data,
            self.matchup_stats,
            include_details=include_feature_breakdown
        )
        feature_vector = features_to_vector(feature_dict, self.feature_names)
        return feature_vector, feature_breakdown if include_feature_breakdown else None

    def predict(
        self,
        blue_team: List[str],
        blue_roles: List[str],
        red_team: List[str],
        red_roles: List[str],
        *,
        include_reasoning: bool = True,
        include_feature_breakdown: bool = True
    ) -> PredictionResult:
        feature_vector, feature_breakdown = self.build_feature_vector(
            blue_team,
            blue_roles,
            red_team,
            red_roles,
            include_feature_breakdown=include_feature_breakdown
        )

        model_predictions = {}
        model_confidences = {}
        for model_name, model in self.models.items():
            blue_prob = model.predict_proba([feature_vector])[0][1]
            model_predictions[model_name] = blue_prob
            model_confidences[model_name] = abs(blue_prob - 0.5) * 2

        raw_prediction = self._weighted_average(
            model_predictions, model_confidences
        )
        ensemble_prediction = self._apply_logit_shift(raw_prediction)
        ensemble_confidence = self._calculate_ensemble_confidence(
            model_predictions, model_confidences
        )
        reasoning: List[str] = []
        if include_reasoning:
            reasoning = self._generate_reasoning(
                blue_team, blue_roles, red_team, red_roles,
                ensemble_prediction, model_predictions
            )
        winner = "blue" if ensemble_prediction > 0.5 else "red"
        return PredictionResult(
            winner=winner,
            confidence=ensemble_confidence,
            blue_win_probability=ensemble_prediction,
            red_win_probability=1 - ensemble_prediction,
            model_breakdown=model_predictions,
            reasoning=reasoning,
            feature_breakdown=feature_breakdown
        )

    def batch_predict_from_vectors(
        self,
        feature_vectors: List[List[float]] | np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        matrix = np.asarray(feature_vectors, dtype=float)
        if matrix.ndim != 2:
            raise ValueError("feature_vectors must be a 2D array")
        model_probs = {}
        model_conf = {}
        weighted_sum = np.zeros(matrix.shape[0], dtype=float)
        total_weight = np.zeros(matrix.shape[0], dtype=float)
        for model_name, model in self.models.items():
            probs = model.predict_proba(matrix)[:, 1]
            conf = np.abs(probs - 0.5) * 2
            weight = self.base_weights[model_name] * (1 + conf)
            weighted_sum += probs * weight
            total_weight += weight
            model_probs[model_name] = probs
            model_conf[model_name] = conf
        raw_prediction = np.divide(
            weighted_sum,
            total_weight,
            out=np.full_like(weighted_sum, 0.5),
            where=total_weight > 0
        )
        ensemble_prediction = self._apply_logit_shift_array(raw_prediction)
        ensemble_confidence = self._calculate_batch_confidence(model_probs, model_conf)
        red_probs = 1.0 - ensemble_prediction
        return ensemble_prediction, red_probs, ensemble_confidence

    def _apply_logit_shift_array(self, probabilities: np.ndarray) -> np.ndarray:
        if abs(self.logit_shift) < 1e-9:
            return probabilities
        clipped = np.clip(probabilities, EPSILON, 1 - EPSILON)
        logits = np.log(clipped / (1 - clipped)) - self.logit_shift
        return 1.0 / (1.0 + np.exp(-logits))

    def _calculate_batch_confidence(
        self,
        model_predictions: Dict[str, np.ndarray],
        model_confidences: Dict[str, np.ndarray]
    ) -> np.ndarray:
        if not model_predictions:
            return np.zeros(0, dtype=float)
        winner_matrix = np.stack([preds > 0.5 for preds in model_predictions.values()], axis=1)
        first_col = winner_matrix[:, [0]]
        agreement = np.where(np.all(winner_matrix == first_col, axis=1), 1.0, 0.5)
        avg_conf = np.mean(np.stack(list(model_confidences.values()), axis=1), axis=1)
        return agreement * avg_conf

    def _apply_logit_shift(self, probability: float) -> float:
        """Adjust probability using learned logit shift to remove global bias."""
        if abs(self.logit_shift) < 1e-9:
            return probability
        logit_value = _logit(probability) - self.logit_shift
        return _sigmoid(logit_value)
    
    def _weighted_average(
        self,
        predictions: Dict[str, float],
        confidences: Dict[str, float]
    ) -> float:
        """
        Weighted average combining base weights and prediction confidence.
        
        Models that are more confident get higher weight.
        """
        weighted_sum = 0
        total_weight = 0
        
        for model_name, prediction in predictions.items():
            # Combine base weight with confidence
            base_w = self.base_weights[model_name]
            conf_w = confidences[model_name]
            
            # Weight = base_performance * prediction_confidence
            weight = base_w * (1 + conf_w)  # Boost by confidence
            
            weighted_sum += prediction * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    def _calculate_ensemble_confidence(
        self,
        predictions: Dict[str, float],
        confidences: Dict[str, float]
    ) -> float:
        """
        Calculate ensemble confidence based on model agreement.
        
        High confidence if:
        1. Models agree on winner
        2. Individual models are confident
        """
        # Check agreement: all predict same winner?
        winners = [1 if p > 0.5 else 0 for p in predictions.values()]
        agreement = 1.0 if len(set(winners)) == 1 else 0.5
        
        # Average model confidence
        avg_confidence = np.mean(list(confidences.values()))
        
        # Combine agreement and confidence
        # High confidence requires both agreement and individual confidence
        return agreement * avg_confidence
    
    def _generate_reasoning(
        self,
        blue_team: List[str],
        blue_roles: List[str],
        red_team: List[str],
        red_roles: List[str],
        prediction: float,
        model_predictions: Dict[str, float]
    ) -> List[str]:
        """
        Generate archetypal reasoning for prediction.
        
        Analyzes team compositions from theoretical perspective:
        - Archetype synergies
        - Role distributions
        - Compositional advantages
        """
        reasoning = []
        
        # Get archetypes for each team
        blue_archetypes = self._get_team_archetypes(blue_team)
        red_archetypes = self._get_team_archetypes(red_team)
        
        # Analyze archetype distribution
        reasoning.extend(self._analyze_archetype_composition(
            blue_archetypes, red_archetypes, prediction > 0.5
        ))
        
        # Analyze key attributes
        reasoning.extend(self._analyze_key_attributes(
            blue_team, blue_roles, red_team, red_roles, prediction > 0.5
        ))
        
        # Model consensus analysis
        reasoning.extend(self._analyze_model_consensus(model_predictions))
        
        return reasoning
    
    def _get_team_archetypes(self, team: List[str]) -> List[str]:
        """Get primary archetypes for team."""
        archetypes = []
        for champ in team:
            if champ in self.champion_data["assignments"]:
                archetype = self.champion_data["assignments"][champ]["primary_archetype"]
                archetypes.append(archetype)
        return archetypes

    def _get_champion_attributes(self, champion: str) -> List[str]:
        """Return attribute list regardless of field naming."""
        info = self.champion_data["assignments"].get(champion, {})
        attrs = info.get("archetype_attributes")
        if attrs is None:
            attrs = info.get("attributes", [])
        return list(attrs or [])
    
    def _analyze_archetype_composition(
        self,
        blue_archetypes: List[str],
        red_archetypes: List[str],
        blue_favored: bool
    ) -> List[str]:
        """Analyze archetype composition patterns."""
        reasoning = []
        
        # Count archetype categories
        def categorize(archetypes):
            damage_dealers = sum(1 for a in archetypes if "mage" in a or "assassin" in a or "marksman" in a)
            tanks = sum(1 for a in archetypes if "tank" in a or "warden" in a)
            fighters = sum(1 for a in archetypes if "diver" in a or "skirmisher" in a or "juggernaut" in a)
            supports = sum(1 for a in archetypes if "enchanter" in a or "catcher" in a)
            return damage_dealers, tanks, fighters, supports
        
        blue_comp = categorize(blue_archetypes)
        red_comp = categorize(red_archetypes)
        
        favored_team = "Blue" if blue_favored else "Red"
        favored_comp = blue_comp if blue_favored else red_comp
        
        # Compositional advantage analysis
        if favored_comp[1] > 1:  # Multiple tanks
            reasoning.append(f"{favored_team} team has strong frontline ({favored_comp[1]} tanks) enabling backline protection")
        
        if favored_comp[0] >= 3:  # Heavy damage
            reasoning.append(f"{favored_team} team has diverse damage threats ({favored_comp[0]} damage dealers) spreading enemy resources")
        
        if favored_comp[2] >= 2:  # Multiple fighters
            reasoning.append(f"{favored_team} team has strong skirmishing potential ({favored_comp[2]} fighters)")
        
        return reasoning
    
    def _analyze_key_attributes(
        self,
        blue_team: List[str],
        blue_roles: List[str],
        red_team: List[str],
        red_roles: List[str],
        blue_favored: bool
    ) -> List[str]:
        """Analyze key attribute advantages."""
        reasoning = []
        
        # Count key attributes for each team
        def count_attributes(team):
            counts = {
                "engage": 0,
                "disengage": 0,
                "mobility_high": 0,
                "range_long": 0,
                "cc_hard": 0,
                "damage_burst": 0,
                "damage_sustained": 0
            }
            for champ in team:
                if champ in self.champion_data["assignments"]:
                    attrs = self._get_champion_attributes(champ)
                    for attr in counts.keys():
                        if attr in attrs:
                            counts[attr] += 1
            return counts
        
        blue_attrs = count_attributes(blue_team)
        red_attrs = count_attributes(red_team)
        
        favored_team = "Blue" if blue_favored else "Red"
        favored_attrs = blue_attrs if blue_favored else red_attrs
        other_attrs = red_attrs if blue_favored else blue_attrs
        
        # Key attribute advantages
        if favored_attrs["engage"] > other_attrs["disengage"]:
            reasoning.append(f"{favored_team} team has engage advantage ({favored_attrs['engage']} vs {other_attrs['disengage']} disengage)")
        
        if favored_attrs["mobility_high"] > other_attrs["cc_hard"]:
            reasoning.append(f"{favored_team} team has mobility advantage ({favored_attrs['mobility_high']} mobile vs {other_attrs['cc_hard']} hard CC)")
        
        if favored_attrs["range_long"] >= 2:
            reasoning.append(f"{favored_team} team has strong poke/range control ({favored_attrs['range_long']} long-range champions)")
        
        if favored_attrs["damage_burst"] >= 2 and favored_attrs["damage_sustained"] >= 2:
            reasoning.append(f"{favored_team} team has balanced damage profile (burst + sustained)")
        
        return reasoning
    
    def _analyze_model_consensus(
        self,
        model_predictions: Dict[str, float]
    ) -> List[str]:
        """Analyze model agreement and disagreement."""
        reasoning = []
        
        # Check if models agree
        blue_wins = sum(1 for p in model_predictions.values() if p > 0.5)
        
        if blue_wins == 3:
            reasoning.append("All models agree on outcome (strong consensus)")
        elif blue_wins == 0:
            reasoning.append("All models agree on outcome (strong consensus)")
        elif blue_wins == 2:
            reasoning.append("Model majority agrees (moderate consensus)")
        else:
            reasoning.append("Models are split (low confidence, close matchup)")
        
        return reasoning


def load_ensemble_predictor(
    models_path: str = "data/simulations/trained_models.pkl",
    champion_path: str = "data/processed/champion_archetypes.json",
    attribute_path: str = "data/processed/archetype_attributes.json",
    relationships_path: str = "data/processed/role_aware_relationships.json",
    matchups_path: str = "data/matches/lane_duo_stats.json",
    calibration_path: str = "data/simulations/calibration.json"
) -> EnsemblePredictor:
    """
    Load trained models and create ensemble predictor.
    
    Args:
        models_path: Path to saved models (from ml_simulation.py)
        champion_path: Path to champion archetype data
        attribute_path: Path to attribute definitions
        relationships_path: Path to role-aware relationships
    
    Returns:
        Configured EnsemblePredictor instance
    """
    import pickle
    
    # Load models
    with open(models_path, "rb") as f:
        model_data = pickle.load(f)
    
    # Extract models and feature names
    models = model_data['models']
    feature_names = model_data['feature_names']
    blue_side_prior = model_data.get('blue_side_prior')
    
    # Load champion data
    with open(champion_path, "r", encoding="utf-8") as f:
        champion_data = json.load(f)
    
    # Load attribute data
    with open(attribute_path, "r", encoding="utf-8") as f:
        attribute_data = json.load(f)
    
    # Load relationships
    with open(relationships_path, "r", encoding="utf-8") as f:
        relationships = json.load(f)

    matchup_stats: Dict = {}
    try:
        with open(matchups_path, "r", encoding="utf-8") as f:
            matchup_stats = json.load(f)
    except FileNotFoundError:
        matchup_stats = {}
    except json.JSONDecodeError:
        matchup_stats = {}

    logit_shift = 0.0
    if calibration_path:
        try:
            with open(calibration_path, "r", encoding="utf-8") as f:
                calibration_data = json.load(f)
                logit_shift = float(calibration_data.get("logit_shift", 0.0))
        except FileNotFoundError:
            logit_shift = 0.0
        except (json.JSONDecodeError, ValueError, TypeError):
            logit_shift = 0.0
    
    return EnsemblePredictor(
        models=models,
        feature_names=feature_names,
        champion_data=champion_data,
        attribute_data=attribute_data,
        relationships=relationships,
        matchup_stats=matchup_stats,
        blue_side_prior=blue_side_prior,
        logit_shift=logit_shift
    )


def main():
    """Test ensemble prediction with example teams."""
    print("Ensemble Prediction System - Archetypal Draft Analysis")
    print("=" * 60)
    
    # Example 1: Front-to-back vs Dive comp
    print("\n🎮 Example 1: Front-to-back vs Dive Composition")
    print("-" * 60)
    
    blue_team = ["Jinx", "Leona", "Orianna", "Vi", "Darius"]
    blue_roles = ["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"]
    
    red_team = ["Caitlyn", "Thresh", "Zed", "Lee Sin", "Renekton"]
    red_roles = ["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"]
    
    print(f"Blue Team: {', '.join(blue_team)}")
    print(f"Red Team:  {', '.join(red_team)}")
    
    try:
        predictor = load_ensemble_predictor()
        result = predictor.predict(blue_team, blue_roles, red_team, red_roles)
        
        print(f"\n✅ Prediction: {result.winner.upper()} team wins")
        print(f"Confidence: {result.confidence:.1%}")
        print(f"Blue win probability: {result.blue_win_probability:.1%}")
        print(f"Red win probability: {result.red_win_probability:.1%}")
        
        print("\n📊 Model Breakdown:")
        for model, prob in result.model_breakdown.items():
            print(f"  {model.upper()}: {prob:.1%} blue win")
        
        print("\n💡 Archetypal Reasoning:")
        for i, reason in enumerate(result.reasoning, 1):
            print(f"  {i}. {reason}")
    
    except FileNotFoundError as e:
        print(f"\n⚠️  Error: {e}")
        print("Run ml_simulation.py first to train models")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
