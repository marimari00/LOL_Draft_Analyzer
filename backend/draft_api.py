"""
Draft Recommendation API

FastAPI server providing archetypal draft analysis endpoints.

Philosophy: Theoretical composition analysis, not data-driven meta chasing.
Focuses on archetype synergies, compositional balance, and strategic reasoning.
"""

from __future__ import annotations

from collections import defaultdict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Set, Tuple, Literal
from pathlib import Path
from datetime import datetime, timezone
import json
import sys
import hashlib
import math
import os

import joblib
import numpy as np

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from validation.ensemble_prediction import load_ensemble_predictor, PredictionResult
from validation.ml_simulation import extract_features_from_team, features_to_vector
from backend.telemetry import log_prediction_event


APP_VERSION = "1.0.0"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
TELEMETRY_DIR = DATA_DIR / "telemetry"
TELEMETRY_LOG_PATH = TELEMETRY_DIR / "prediction_log.jsonl"
CALIBRATION_REPORT_PATH = TELEMETRY_DIR / "calibration_report.json"


simulation_summary_cache: Dict[str, Any] = {}
simulation_matchup_table: Dict[Tuple[str, str], Dict[str, Any]] = {}
simulation_composition_table: Dict[str, Any] = {}


def _resolve_simulation_summary_path() -> Path:
    """Pick the most relevant simulation summary JSON."""
    env_override = os.environ.get("SIMULATION_SUMMARY_PATH")
    if env_override:
        return Path(env_override).expanduser()

    simulations_dir = DATA_DIR / "simulations"
    newest_mass_file: Optional[Path] = None
    newest_mtime = -1.0
    if simulations_dir.exists():
        for candidate in simulations_dir.glob("mass_simulation*.json"):
            try:
                mtime = candidate.stat().st_mtime
            except OSError:
                continue
            if mtime > newest_mtime:
                newest_mtime = mtime
                newest_mass_file = candidate

    if newest_mass_file is not None:
        return newest_mass_file

    return simulations_dir / "simulation_10k_games.json"


SIMULATION_SUMMARY_PATH = _resolve_simulation_summary_path()
MATCHES_PATH = DATA_DIR / "matches" / "multi_region_10k.json"
OPENING_BAN_COUNT = 6
BAN_MODES = {
    "pro": "pro",
    "soloq": "soloq"
}

app = FastAPI(
    title="League of Legends Draft Analyzer",
    description="Archetypal composition analysis using theoretical frameworks",
    version=APP_VERSION
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global predictor (loaded on startup)
predictor = None
champion_data = None
attribute_data = None
simulation_model = None
simulation_feature_names: List[str] = []
solo_queue_ban_stats: Dict[str, Dict[str, float]] = {}
flex_priority_scores: Dict[str, float] = {}

ROLE_ORDER = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
POSITION_TO_ROLE = {
    "Top": "TOP",
    "Jungle": "JUNGLE",
    "Middle": "MIDDLE",
    "Mid": "MIDDLE",
    "Bottom": "BOTTOM",
    "Bot": "BOTTOM",
    "Carry": "BOTTOM",
    "Support": "UTILITY",
    "Utility": "UTILITY"
}

ROLE_TO_POSITION = {
    "TOP": "Top",
    "JUNGLE": "Jungle",
    "MIDDLE": "Middle",
    "BOTTOM": "Bottom",
    "UTILITY": "Support"
}

ROLE_ARCHETYPE_BONUS = {
    "TOP": {
        "juggernaut": 0.03,
        "skirmisher": 0.025,
        "warden": 0.02,
        "diver": 0.015
    },
    "JUNGLE": {
        "diver": 0.035,
        "engage_tank": 0.03,
        "skirmisher": 0.02
    },
    "MIDDLE": {
        "burst_mage": 0.03,
        "battle_mage": 0.025,
        "burst_assassin": 0.02,
        "artillery_mage": 0.015
    },
    "BOTTOM": {
        "marksman": 0.04,
        "artillery_mage": 0.02
    },
    "UTILITY": {
        "engage_tank": 0.035,
        "warden": 0.03,
        "catcher": 0.025,
        "enchanter": 0.02,
        "battle_mage": 0.015
    }
}

ROLE_PLACEHOLDER_CHAMPIONS = {
    "TOP": "Gnar",
    "JUNGLE": "Lee Sin",
    "MIDDLE": "Orianna",
    "BOTTOM": "Jinx",
    "UTILITY": "Nami"
}

DEFAULT_PLACEHOLDER_CHAMPION = "Orianna"
MIN_TEAM_PICKS_FOR_PROJECTION = 2

ARCHETYPE_FAMILY_KEYWORDS = [
    ("marksman", "backline_marksman", "backline marksman"),
    ("artillery_mage", "artillery_mage", "artillery mage"),
    ("battle_mage", "battle_mage", "battle mage"),
    ("burst_mage", "burst_mage", "burst mage"),
    ("burst_assassin", "assassin", "burst assassin"),
    ("assassin", "assassin", "assassin"),
    ("diver", "dive_bruiser", "dive bruiser"),
    ("skirmisher", "dive_bruiser", "dive bruiser"),
    ("juggernaut", "frontline_bruiser", "juggernaut bruiser"),
    ("engage_tank", "primary_engage", "primary engage"),
    ("tank", "primary_engage", "primary engage"),
    ("warden", "frontline_support", "warden frontliner"),
    ("catcher", "support_pick", "pick support"),
    ("enchanter", "support_enchanter", "enchanter support"),
    ("specialist", "specialist", "specialist pocket")
]

TEAM_THEME_LABELS = {
    "poke": "Siege & Poke",
    "dive": "Hard Engage",
    "protect": "Protect the Carry",
    "bruiser": "Bruiser Brawl",
    "flex": "Flexible"
}

RATIONALE_TAG_PATTERNS = [
    ("primary engage tool", "Fixes engage gap"),
    ("adds reliable lockdown", "Adds hard CC"),
    ("crowd control", "Stacks lockdown"),
    ("introduces first magic damage", "Adds magic damage"),
    ("first consistent physical damage", "Adds physical damage"),
    ("balances physical-heavy", "Adds mixed damage"),
    ("rebalances magic-heavy", "Adds mixed damage"),
    ("long-range pressure", "Unlocks poke win"),
    ("sustain mitigates", "Adds sustain"),
    ("peels against enemy dive", "Adds peel tools"),
    ("frontline presence", "Adds frontline"),
    ("frontline durability", "Bolsters frontline"),
    ("counters enemy assassin", "Shuts down assassins"),
    ("hard cc counters", "Stops mobile threats"),
    ("engage counters enemy poke", "Punishes poke comps"),
    ("enchanter synergizes", "Buffers hyper-carry"),
    ("engage synergizes", "Sets up burst"),
    ("poke/range complements", "Adds siege pressure"),
    ("fills critical damage dealer", "Adds carry threat"),
    ("provides missing frontline", "Adds frontline"),
    ("supplies much-needed frontline", "Bolsters frontline"),
    ("mobile kit can dodge", "Safe blind pick"),
    ("optimal comfort pick", "Comfort pick"),
    ("fills empty", "Covers missing role")
]

# Blue-side baseline derived from training data (fallback to historical 45.45%).
BLUE_PRIOR_FALLBACK = 0.4545
blue_side_prior = BLUE_PRIOR_FALLBACK
PROBABILITY_EPSILON = 1e-6
FAMILY_STACK_PENALTY = 0.02
ROLE_STACK_PENALTY = 0.015


def _champ_info_attributes(champ_info: Optional[Dict[str, Any]]) -> List[str]:
    """Return archetype attribute list regardless of key name."""
    if not champ_info:
        return []
    attrs = champ_info.get("archetype_attributes")
    if attrs is None:
        attrs = champ_info.get("attributes")
    return list(attrs or [])


def _champion_attributes(champion: str) -> List[str]:
    """Fetch attributes for a champion safely from the global dataset."""
    if champion_data is None:
        return []
    champ_info = champion_data["assignments"].get(champion)
    return _champ_info_attributes(champ_info)


def _initialize_ban_datasets():
    """Load SoloQ performance baselines and flex scores for ban logic."""
    global solo_queue_ban_stats, flex_priority_scores
    matches = []
    if MATCHES_PATH.exists():
        try:
            with MATCHES_PATH.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            matches = payload.get("matches", [])
        except Exception as exc:
            print(f"Failed to load match dataset for bans: {exc}")

    if matches:
        solo_queue_ban_stats = _compute_solo_queue_ban_table(matches)
    else:
        solo_queue_ban_stats = {}

    flex_priority_scores = _compute_flex_priority_scores()


def _compute_solo_queue_ban_table(matches: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    stats: Dict[str, Dict[str, int]] = {}
    total_entries = max(len(matches) * 10, 1)

    for match in matches:
        winner = match.get("winner")
        for champion in match.get("blue_team", {}).values():
            entry = stats.setdefault(champion, {"games": 0, "wins": 0})
            entry["games"] += 1
            if winner == "blue":
                entry["wins"] += 1
        for champion in match.get("red_team", {}).values():
            entry = stats.setdefault(champion, {"games": 0, "wins": 0})
            entry["games"] += 1
            if winner == "red":
                entry["wins"] += 1

    table: Dict[str, Dict[str, float]] = {}
    for champion, entry in stats.items():
        games = entry["games"]
        if games == 0:
            continue
        wins = entry["wins"]
        win_rate = wins / games
        presence = games / total_entries
        score = (win_rate - 0.5) * 0.6 + presence * 0.4
        table[champion] = {
            "games": games,
            "wins": wins,
            "win_rate": win_rate,
            "presence": presence,
            "score": score
        }
    return table


def _compute_flex_priority_scores() -> Dict[str, float]:
    scores: Dict[str, float] = {}
    if not champion_data:
        return scores
    assignments = champion_data.get("assignments", {})
    for champion, info in assignments.items():
        roles = set()
        primary = info.get("primary_position")
        if primary:
            roles.add(POSITION_TO_ROLE.get(primary, primary.upper()))
        for pos in info.get("viable_positions", []):
            roles.add(POSITION_TO_ROLE.get(pos, pos.upper()))
        flex_count = max(len(roles), 1)
        flex_score = min(flex_count, 4) / 4.0
        meta_score = solo_queue_ban_stats.get(champion, {}).get("score", 0.0)
        scores[champion] = flex_score * 0.7 + meta_score * 0.3
    return scores


def _champion_theme_tags(champion: str) -> Set[str]:
    tags: Set[str] = set()
    attrs = _champion_attributes(champion)
    if not attrs:
        return tags
    if any(attr in {"range_long", "damage_aoe", "poke_pressure"} for attr in attrs):
        tags.add("poke")
    if any(attr.startswith("engage") or attr in {"utility_engage", "engage_backline_access"} for attr in attrs):
        tags.add("dive")
    if any(attr in {"utility_peel", "utility_heal", "utility_shields", "survive_shields"} for attr in attrs):
        tags.add("protect")
    if any(attr in {"survive_tank", "survive_sustain", "damage_sustained"} for attr in attrs):
        tags.add("bruiser")
    return tags


def _classify_team_theme(team: List[str]) -> str:
    counts: Dict[str, int] = defaultdict(int)
    for champion in team:
        for tag in _champion_theme_tags(champion):
            counts[tag] += 1
    if not counts:
        return "flex"
    theme, value = max(counts.items(), key=lambda item: item[1])
    if value < 2:
        return "flex"
    return theme


def _remaining_champions(draft: DraftState) -> Set[str]:
    available = set(champion_data["assignments"].keys()) if champion_data else set()
    taken = set(draft.blue_bans + draft.red_bans + draft.blue_picks + draft.red_picks)
    return available - taken


def _generate_solo_ban_recommendations(available: Set[str], limit: int) -> List[BanRecommendation]:
    ranked = sorted(
        available,
        key=lambda champ: solo_queue_ban_stats.get(champ, {}).get("score", 0.0),
        reverse=True
    )
    recs: List[BanRecommendation] = []
    for champion in ranked:
        data = solo_queue_ban_stats.get(champion)
        if not data:
            continue
        win_rate = data.get("win_rate", 0.5)
        presence = data.get("presence", 0.0)
        roles = _get_champion_roles(champion)
        reason = (
            f"{champion} wins {win_rate:.1%} of high-ELO SoloQ drafts and shows up in {presence * 100:.1f}% of games."
        )
        recs.append(BanRecommendation(
            champion=champion,
            score=data.get("score", 0.0),
            category="meta_power",
            reason=reason,
            roles=roles,
            tags=["Meta threat"],
            metrics={
                "win_rate": win_rate,
                "presence": presence,
                "games": data.get("games", 0)
            }
        ))
        if len(recs) >= limit:
            break
    return recs


def _generate_pro_ban_recommendations(
    draft: DraftState,
    acting_team: str,
    available: Set[str],
    limit: int
) -> Tuple[List[BanRecommendation], Dict[str, Any]]:
    total_bans = len(draft.blue_bans) + len(draft.red_bans)
    target_team = "red" if acting_team == "blue" else "blue"
    context = {
        "phase": "opening" if total_bans < OPENING_BAN_COUNT else "second",
        "target_team": target_team,
        "target_theme": None,
        "our_theme": None
    }

    enemy_picks = draft.red_picks if acting_team == "blue" else draft.blue_picks
    our_picks = draft.blue_picks if acting_team == "blue" else draft.red_picks

    enemy_theme = _classify_team_theme(enemy_picks)
    our_theme = _classify_team_theme(our_picks)
    context["target_theme"] = TEAM_THEME_LABELS.get(enemy_theme, "Flexible")
    context["our_theme"] = TEAM_THEME_LABELS.get(our_theme, "Flexible")

    if context["phase"] == "opening":
        recs = _pro_opening_bans(available, limit)
    else:
        enemy_roles = draft.red_roles if acting_team == "blue" else draft.blue_roles
        recs = _pro_second_phase_bans(
            available,
            limit,
            enemy_picks,
            enemy_roles,
            enemy_theme,
            our_theme
        )

    return recs, context


def _pro_opening_bans(available: Set[str], limit: int) -> List[BanRecommendation]:
    ranked = sorted(
        available,
        key=lambda champ: flex_priority_scores.get(champ, 0.0),
        reverse=True
    )
    recs: List[BanRecommendation] = []
    for champion in ranked:
        flex_score = flex_priority_scores.get(champion, 0.0)
        roles = _get_champion_roles(champion)
        if not roles:
            continue
        reason = f"{champion} keeps lanes ambiguous ({'/'.join(roles[:3])}) and warps first rotation reveals."
        tags = ["Flex threat"]
        meta = solo_queue_ban_stats.get(champion, {})
        recs.append(BanRecommendation(
            champion=champion,
            score=flex_score,
            category="flex_threat",
            reason=reason,
            roles=roles,
            tags=tags,
            metrics={
                "flex_roles": len(roles),
                "meta_score": meta.get("score", 0.0)
            }
        ))
        if len(recs) >= limit:
            break
    return recs


def _pro_second_phase_bans(
    available: Set[str],
    limit: int,
    enemy_team: List[str],
    enemy_roles: List[str],
    enemy_theme: str,
    our_theme: str
) -> List[BanRecommendation]:
    enemy_needed_roles = _get_needed_roles([role for role in enemy_roles if role])
    counter_table = {
        "protect": {"dive": 0.25},
        "poke": {"dive": 0.2},
        "dive": {"protect": 0.2},
        "bruiser": {"poke": 0.2}
    }
    recs: List[BanRecommendation] = []

    def _score_champion(champion: str) -> Tuple[float, List[str], str]:
        tags = _champion_theme_tags(champion)
        score = solo_queue_ban_stats.get(champion, {}).get("score", 0.0) * 0.25
        reason_bits: List[str] = []
        if enemy_theme in tags:
            score += 0.45
            reason_bits.append(f"Reinforces their {TEAM_THEME_LABELS.get(enemy_theme, 'Flexible')} plan")
        ally_counters = counter_table.get(our_theme, {})
        for tag, bonus in ally_counters.items():
            if tag in tags:
                score += bonus
                reason_bits.append("Counters our identity")
        roles = _get_champion_roles(champion)
        if enemy_needed_roles and any(role in enemy_needed_roles for role in roles):
            score += 0.2
            reason_bits.append("Fills their missing role")
        if not reason_bits:
            reason_bits.append("High-impact comfort pick for them")
        reason = "; ".join(reason_bits)
        display_tags = []
        if enemy_theme in tags:
            display_tags.append(f"Boosts {TEAM_THEME_LABELS.get(enemy_theme, enemy_theme)}")
        if ally_counters and any(tag in tags for tag in ally_counters):
            display_tags.append("Covers our weakness")
        if not display_tags:
            display_tags.append("Meta threat")
        return score, display_tags, reason

    scored = []
    for champion in available:
        score, tag_list, reason = _score_champion(champion)
        if score <= 0:
            continue
        scored.append((score, champion, tag_list, reason))

    scored.sort(key=lambda item: item[0], reverse=True)
    for score, champion, tag_list, reason in scored[:limit]:
        recs.append(BanRecommendation(
            champion=champion,
            score=score,
            category="theme_block",
            reason=reason,
            roles=_get_champion_roles(champion),
            tags=tag_list,
            metrics={
                "meta_score": solo_queue_ban_stats.get(champion, {}).get("score", 0.0)
            }
        ))
    return recs


# === Request/Response Models ===

class DraftState(BaseModel):
    """Current state of champion draft."""
    blue_picks: List[str] = Field(default_factory=list, max_items=5)
    blue_roles: List[str] = Field(default_factory=list, max_items=5)
    blue_bans: List[str] = Field(default_factory=list, max_items=5)
    red_picks: List[str] = Field(default_factory=list, max_items=5)
    red_roles: List[str] = Field(default_factory=list, max_items=5)
    red_bans: List[str] = Field(default_factory=list, max_items=5)
    next_pick: str = Field(..., pattern="^(blue|red)$")


class PickSlot(BaseModel):
    """Represents a specific pick slot in the draft order."""
    slot_id: str
    team: str = Field(..., pattern="^(blue|red)$")
    role: Optional[str] = Field(None, pattern="^(TOP|JUNGLE|MIDDLE|BOTTOM|UTILITY)$")


class RecommendationRequest(BaseModel):
    """Request for champion recommendations."""
    draft_state: DraftState
    role: Optional[str] = Field(None, pattern="^(TOP|JUNGLE|MIDDLE|BOTTOM|UTILITY)$")
    upcoming_slots: Optional[List[PickSlot]] = None
    limit: int = Field(5, ge=1, le=20)


class ChampionRecommendation(BaseModel):
    """Individual champion recommendation."""
    champion: str
    score: float
    archetype: str
    recommended_role: Optional[str] = None
    attribute_highlights: List[str] = Field(default_factory=list)
    reasoning: List[str]
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    rationale_tags: List[str] = Field(default_factory=list)
    projected_blue_winrate: Optional[float] = None
    projected_team_winrate: Optional[float] = None
    winrate_delta: Optional[float] = None
    simulation_matchup: Optional[Dict[str, Any]] = None


class SlotRecommendations(BaseModel):
    """Recommendations targeted for a specific pick slot."""
    slot_id: str
    team: str
    role: Optional[str]
    recommendations: List[ChampionRecommendation]


class RecommendationResponse(BaseModel):
    """Response with champion recommendations."""
    slots: List[SlotRecommendations]
    draft_analysis: Dict[str, Any]
    win_projection: Optional[Dict[str, Any]] = None


class AnalysisRequest(BaseModel):
    """Request for team composition analysis."""
    blue_team: List[str] = Field(..., min_items=5, max_items=5)
    blue_roles: List[str] = Field(..., min_items=5, max_items=5)
    red_team: List[str] = Field(..., min_items=5, max_items=5)
    red_roles: List[str] = Field(..., min_items=5, max_items=5)
    actual_winner: Optional[str] = Field(None, pattern="^(blue|red)$")


class AnalysisResponse(BaseModel):
    """Response with composition analysis."""
    prediction: Dict[str, Any]
    blue_analysis: Dict[str, Any]
    red_analysis: Dict[str, Any]
    archetypal_insights: List[str]
    matchup_context: Dict[str, Any] = Field(default_factory=dict)


class BanRecommendation(BaseModel):
    champion: str
    score: float
    category: str
    reason: str
    tags: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)


class BanRecommendationResponse(BaseModel):
    team: str
    mode: str
    phase: str
    target_team: str
    target_theme: Optional[str] = None
    our_theme: Optional[str] = None
    recommendations: List[BanRecommendation]


class BanRecommendationRequest(BaseModel):
    mode: Literal["pro", "soloq"] = BAN_MODES["pro"]
    team: Literal["blue", "red"]
    draft_state: DraftState
    limit: int = Field(default=5, ge=1, le=10)


# === Startup/Shutdown ===

@app.on_event("startup")
async def startup_event():
    """Load models and data on startup."""
    global predictor, champion_data, attribute_data, simulation_model, simulation_feature_names, blue_side_prior
    
    try:
        print("Loading ensemble predictor...")
        predictor = load_ensemble_predictor(matchups_path="data/matches/lane_duo_stats.json")
        if predictor and hasattr(predictor, "blue_side_prior"):
            try:
                prior = float(predictor.blue_side_prior)
                if 0.0 < prior < 1.0:
                    blue_side_prior = prior
            except (TypeError, ValueError):
                blue_side_prior = BLUE_PRIOR_FALLBACK
        
        print("Loading champion data...")
        with open("data/processed/champion_archetypes.json", "r", encoding="utf-8") as f:
            champion_data = json.load(f)
        
        with open("data/processed/archetype_attributes.json", "r", encoding="utf-8") as f:
            attribute_data = json.load(f)

        _initialize_ban_datasets()
        _refresh_mass_simulation_tables()

        model_path = Path("models/simulated_sgd.pkl")
        if model_path.exists():
            try:
                bundle = joblib.load(model_path)
                simulation_model = bundle.get("model")
                simulation_feature_names = bundle.get("feature_names", []) or []
                if simulation_model and simulation_feature_names:
                    print("Loaded simulation-trained SGD model")
                else:
                    print("Simulation-trained model bundle missing data; skipping")
            except Exception as exc:
                print(f"Simulation model load failed: {exc}")
        else:
            print("Simulation-trained model not found (models/simulated_sgd.pkl)")
        
        print("API ready")
    
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Run ml_simulation.py first to train models")


# === Endpoints ===

@app.get("/")
async def root():
    """API health check."""
    return {
        "status": "online",
        "version": APP_VERSION,
        "philosophy": "Archetypal draft analysis - theory over meta",
        "health_endpoint": "/health"
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Detailed health snapshot with model + telemetry diagnostics."""
    return _build_health_payload()


@app.get("/simulations/summary")
async def simulation_summary() -> Dict[str, Any]:
    """Expose metadata from the latest ml_simulation run."""
    return _load_simulation_summary()


@app.post("/draft/recommend", response_model=RecommendationResponse)
async def recommend_champions(request: RecommendationRequest):
    """
    Recommend champions for current draft state.
    
    Analyzes:
    - Team composition needs (missing archetypes)
    - Counter-pick opportunities vs enemy team
    - Role synergies with existing picks
    - Archetypal balance
    
    Returns top N recommendations with reasoning.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    draft = request.draft_state

    # Determine which champions are still available
    all_champions = set(champion_data["assignments"].keys())
    banned = set(draft.blue_bans + draft.red_bans)
    picked = set(draft.blue_picks + draft.red_picks)
    available = all_champions - banned - picked

    slot_requests = request.upcoming_slots or [
        PickSlot(slot_id="next_pick", team=draft.next_pick, role=request.role)
    ]

    slot_recommendations: List[SlotRecommendations] = []

    for slot in slot_requests:
        slot_role = None
        if isinstance(slot.role, str):
            slot_role = slot.role.upper()
        elif isinstance(request.role, str):
            slot_role = request.role.upper()
        team_picks = draft.blue_picks if slot.team == "blue" else draft.red_picks
        enemy_picks = draft.red_picks if slot.team == "blue" else draft.blue_picks
        team_roles = draft.blue_roles if slot.team == "blue" else draft.red_roles
        normalized_roles = [role.upper() for role in team_roles if isinstance(role, str)]

        slot_recommendations.append(SlotRecommendations(
            slot_id=slot.slot_id,
            team=slot.team,
            role=slot_role,
            recommendations=_generate_recommendations_for_slot(
                available,
                team_picks,
                enemy_picks,
                normalized_roles,
                slot_role,
                request.limit
            )
        ))

    win_projection = _predict_blue_win_probability(
        draft.blue_picks,
        draft.blue_roles,
        draft.red_picks,
        draft.red_roles
    )

    for slot in slot_recommendations:
        for rec in slot.recommendations:
            resolved_role = slot.role or rec.recommended_role
            projected = _project_pick_win_probability(
                draft,
                slot.team,
                rec.champion,
                resolved_role
            )
            rec.winrate_delta = None
            if not projected:
                continue

            projected_blue = projected.get("blue")
            projected_red = projected.get("red")
            if projected_blue is not None:
                rec.projected_blue_winrate = projected_blue
            if slot.team == "blue" and projected_blue is not None:
                rec.projected_team_winrate = projected_blue
            elif slot.team == "red" and projected_red is not None:
                rec.projected_team_winrate = projected_red
        _sort_slot_recommendations(slot)

    draft_analysis = _analyze_draft_state(draft.blue_picks, draft.red_picks)

    return RecommendationResponse(
        slots=slot_recommendations,
        draft_analysis=draft_analysis,
        win_projection=win_projection
    )


@app.post("/draft/analyze", response_model=AnalysisResponse)
async def analyze_composition(request: AnalysisRequest):
    """
    Analyze complete team compositions.
    
    Provides:
    - Win probability prediction
    - Model consensus breakdown
    - Archetypal composition analysis
    - Strategic insights and reasoning
    
    Returns comprehensive analysis from theoretical perspective.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    # Validate champion names
    valid_champions = set(champion_data["assignments"].keys())
    all_champs = set(request.blue_team + request.red_team)
    invalid = all_champs - valid_champions
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid champion names: {', '.join(invalid)}"
        )
    
    # Get base ensemble prediction for reasoning/model breakdown
    result: PredictionResult = predictor.predict(
        request.blue_team,
        request.blue_roles,
        request.red_team,
        request.red_roles
    )

    # Generate blended projection so win rates match the draft view
    projection = _predict_blue_win_probability(
        request.blue_team,
        request.blue_roles,
        request.red_team,
        request.red_roles
    )
    favored_side = projection.get("favored", result.winner) if projection else result.winner
    blue_probability = projection.get("blue", result.blue_win_probability) if projection else result.blue_win_probability
    red_probability = projection.get("red", result.red_win_probability) if projection else result.red_win_probability
    confidence = projection.get("confidence", result.confidence) if projection else result.confidence
    
    # Analyze each team
    blue_analysis = _analyze_team_composition(request.blue_team, request.blue_roles)
    red_analysis = _analyze_team_composition(request.red_team, request.red_roles)

    matchup_context = _build_matchup_context(
        request.blue_team,
        request.blue_roles,
        request.red_team,
        request.red_roles,
        blue_analysis,
        red_analysis,
        projection,
        result
    )
    
    response = AnalysisResponse(
        prediction={
            "winner": favored_side,
            "confidence": confidence,
            "blue_win_probability": blue_probability,
            "red_win_probability": red_probability,
            "model_breakdown": result.model_breakdown
        },
        blue_analysis=blue_analysis,
        red_analysis=red_analysis,
        archetypal_insights=result.reasoning,
        matchup_context=matchup_context
    )

    _record_analysis_telemetry(request, response.prediction, matchup_context)
    return response


@app.post("/draft/bans", response_model=BanRecommendationResponse)
async def recommend_bans(request: BanRecommendationRequest):
    if request.mode not in BAN_MODES:
        raise HTTPException(status_code=400, detail="Unsupported ban mode")

    available = _remaining_champions(request.draft_state)
    if not available:
        raise HTTPException(status_code=400, detail="Champion catalog unavailable")

    limit = min(request.limit, len(available))
    if request.mode == BAN_MODES["soloq"]:
        recommendations = _generate_solo_ban_recommendations(available, limit)
        context = {
            "phase": "solo_meta",
            "target_team": "meta",
            "target_theme": None,
            "our_theme": None
        }
    else:
        recommendations, context = _generate_pro_ban_recommendations(
            request.draft_state,
            request.team,
            available,
            limit
        )

    if not recommendations:
        raise HTTPException(status_code=404, detail="No ban recommendations available")

    return BanRecommendationResponse(
        team=request.team,
        mode=request.mode,
        phase=context.get("phase", "unknown"),
        target_team=context.get("target_team", "unknown"),
        target_theme=context.get("target_theme"),
        our_theme=context.get("our_theme"),
        recommendations=recommendations
    )


@app.get("/champions/{champion_name}")
async def get_champion_info(champion_name: str):
    """
    Get detailed information about a champion.
    
    Returns:
    - Primary archetype
    - Viable roles
    - Key attributes
    - Archetypal characteristics
    """
    if champion_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    if champion_name not in champion_data["assignments"]:
        raise HTTPException(status_code=404, detail=f"Champion '{champion_name}' not found")
    
    champ_info = champion_data["assignments"][champion_name]
    
    return {
        "name": champion_name,
        "archetype": champ_info["primary_archetype"],
        "secondary_archetypes": champ_info.get("secondary_archetypes", []),
        "riot_roles": champ_info.get("riot_roles", []),
        "positions": champ_info.get("positions", {}),
        "attributes": _champ_info_attributes(champ_info),
        "description": _get_archetype_description(champ_info["primary_archetype"])
    }


@app.get("/archetypes")
async def list_archetypes():
    """
    List all archetypes with descriptions.
    
    Returns archetype taxonomy used for analysis.
    """
    if attribute_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    archetypes = {}
    for archetype, data in attribute_data.get("archetype_descriptions", {}).items():
        archetypes[archetype] = {
            "name": archetype,
            "description": data.get("description", ""),
            "key_attributes": data.get("key_attributes", []),
            "example_champions": data.get("examples", [])
        }
    
    return archetypes


# === Helper Functions ===

def _summarize_team_profile(team: List[str]) -> Dict[str, int]:
    """Aggregate coarse attribute counts for synergy and counter scoring."""
    profile = {
        "magic_damage": 0,
        "physical_damage": 0,
        "hard_cc": 0,
        "engage": 0,
        "poke": 0,
        "peel": 0,
        "mobility": 0,
        "frontline": 0,
        "sustain": 0
    }

    for champion in team:
        info = champion_data["assignments"].get(champion) if champion_data else None
        if not info:
            continue
        attrs = _champ_info_attributes(info)
        for attr in attrs:
            if "damage_magic" in attr:
                profile["magic_damage"] += 1
            if "damage_physical" in attr:
                profile["physical_damage"] += 1
            if attr == "cc_hard":
                profile["hard_cc"] += 1
            if attr.startswith("engage") or attr == "utility_engage":
                profile["engage"] += 1
            if attr == "range_long" or attr == "damage_aoe":
                profile["poke"] += 1
            if attr in {"utility_peel", "utility_shields"}:
                profile["peel"] += 1
            if attr == "mobility_high":
                profile["mobility"] += 1
            if attr in {"survive_tank", "engage_frontline", "survive_shields"}:
                profile["frontline"] += 1
            if attr == "survive_sustain" or attr == "survive_heal" or attr == "utility_heal":
                profile["sustain"] += 1

    return profile


def _default_role_for_index(index: int) -> str:
    """Return a fallback role for incomplete draft slots."""
    if index < len(ROLE_ORDER):
        return ROLE_ORDER[index]
    return ROLE_ORDER[index % len(ROLE_ORDER)]


def _rebalance_probability(probability: Optional[float], baseline: float) -> Optional[float]:
    """Remove a constant side bias by shifting odds back toward 50/50."""
    if probability is None:
        return None
    if baseline <= 0.0 or baseline >= 1.0:
        return probability

    clipped_prob = min(max(probability, PROBABILITY_EPSILON), 1.0 - PROBABILITY_EPSILON)
    baseline_clipped = min(max(baseline, PROBABILITY_EPSILON), 1.0 - PROBABILITY_EPSILON)

    current_odds = clipped_prob / (1.0 - clipped_prob)
    baseline_odds = baseline_clipped / (1.0 - baseline_clipped)
    adjusted_odds = current_odds / baseline_odds
    adjusted_prob = adjusted_odds / (1.0 + adjusted_odds)
    return adjusted_prob


def _prepare_team_for_prediction(
    picks: List[str],
    roles: List[Optional[str]]
) -> Tuple[List[str], List[str]]:
    """Return the real champions/roles only; no placeholder padding."""
    champions: List[str] = []
    assigned_roles: List[str] = []

    for idx, champion in enumerate(picks):
        if not champion:
            continue
        champions.append(champion)
        provided_role = roles[idx] if idx < len(roles) else None
        if isinstance(provided_role, str) and provided_role:
            assigned_roles.append(provided_role.upper())
        else:
            assigned_roles.append(_default_role_for_index(len(assigned_roles)))

    return champions, assigned_roles


def _build_position_team(champions: List[str], roles: List[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for idx, champion in enumerate(champions):
        if not champion:
            continue
        role_value = roles[idx] if idx < len(roles) else None
        normalized = role_value.upper() if isinstance(role_value, str) else None
        position = ROLE_TO_POSITION.get(normalized) if normalized else None
        if position is None and normalized:
            position = normalized.title()
        if position is None and idx < len(ROLE_ORDER):
            fallback_role = ROLE_ORDER[idx]
            position = ROLE_TO_POSITION.get(fallback_role, fallback_role.title())
        if position:
            mapping[position] = champion
    return mapping


def _predict_simulation_probability(
    blue_team: List[str],
    blue_roles: List[str],
    red_team: List[str],
    red_roles: List[str]
) -> Optional[float]:
    if simulation_model is None or not simulation_feature_names or champion_data is None:
        return None

    try:
        blue_map = _build_position_team(blue_team, blue_roles)
        red_map = _build_position_team(red_team, red_roles)
        blue_features = extract_features_from_team(blue_map, champion_data)
        red_features = extract_features_from_team(red_map, champion_data)
        blue_vector = features_to_vector(blue_features, simulation_feature_names)
        red_vector = features_to_vector(red_features, simulation_feature_names)
        diff = np.array([[b - r for b, r in zip(blue_vector, red_vector)]], dtype=float)
        prob = simulation_model.predict_proba(diff)[0][1]
        return float(prob)
    except Exception as exc:
        print(f"Simulation probability failed: {exc}")
        return None


def _predict_blue_win_probability(
    blue_picks: List[str],
    blue_roles: List[Optional[str]],
    red_picks: List[str],
    red_roles: List[Optional[str]]
) -> Optional[Dict[str, Any]]:
    """Run predictor on the current (possibly incomplete) draft state."""
    if predictor is None:
        return None

    cleaned_blue = [pick for pick in blue_picks if pick]
    cleaned_red = [pick for pick in red_picks if pick]
    total_real_picks = len(cleaned_blue) + len(cleaned_red)
    if total_real_picks <= 1:
        return {
            "blue": 0.5,
            "red": 0.5,
            "ensemble_blue": 0.5,
            "ensemble_red": 0.5,
            "simulated_blue": None,
            "simulated_red": None,
            "confidence": 0.0,
            "favored": "blue",
            "notes": [
                "Even draft — not enough picks locked yet for matchup edges."
            ]
        }

    blue_team, resolved_blue_roles = _prepare_team_for_prediction(blue_picks, blue_roles)
    red_team, resolved_red_roles = _prepare_team_for_prediction(red_picks, red_roles)

    if len(blue_team) < 2 and len(red_team) < 2:
        return {
            "blue": 0.5,
            "red": 0.5,
            "ensemble_blue": 0.5,
            "ensemble_red": 0.5,
            "simulated_blue": None,
            "simulated_red": None,
            "confidence": 0.0,
            "favored": "blue",
            "notes": [
                "Need more picks on each side before projecting meaningful edges."
            ]
        }

    if len(blue_team) < MIN_TEAM_PICKS_FOR_PROJECTION or len(red_team) < MIN_TEAM_PICKS_FOR_PROJECTION:
        return {
            "blue": 0.5,
            "red": 0.5,
            "ensemble_blue": 0.5,
            "ensemble_red": 0.5,
            "simulated_blue": None,
            "simulated_red": None,
            "confidence": 0.0,
            "favored": "blue",
            "notes": [
                "Hold projections until each side locks at least two real champions."
            ]
        }

    try:
        result: PredictionResult = predictor.predict(
            blue_team,
            resolved_blue_roles,
            red_team,
            resolved_red_roles
        )
    except Exception as exc:
        print(f"Win projection failed: {exc}")
        return None

    simulated_prob = _predict_simulation_probability(
        blue_team,
        resolved_blue_roles,
        red_team,
        resolved_red_roles
    )

    ensemble_blue = _rebalance_probability(result.blue_win_probability, blue_side_prior)
    ensemble_red = 1.0 - ensemble_blue
    if simulated_prob is not None:
        corrected_sim = _rebalance_probability(simulated_prob, blue_side_prior)
        blended_blue = float(ensemble_blue * 0.65 + corrected_sim * 0.35)
    else:
        corrected_sim = None
        blended_blue = ensemble_blue
    blended_red = 1.0 - blended_blue

    favored_side = "blue" if blended_blue >= blended_red else "red"

    return {
        "blue": blended_blue,
        "red": blended_red,
        "ensemble_blue": ensemble_blue,
        "ensemble_red": ensemble_red,
        "simulated_blue": corrected_sim,
        "simulated_red": 1.0 - corrected_sim if corrected_sim is not None else None,
        "confidence": result.confidence,
        "favored": favored_side,
        "notes": result.reasoning[:3]
    }


def _project_pick_win_probability(
    draft: DraftState,
    team: str,
    champion: str,
    role: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Predict win probability after hypothetically locking a recommendation."""
    if not champion:
        return None

    blue_picks = list(draft.blue_picks)
    blue_roles = list(draft.blue_roles)
    red_picks = list(draft.red_picks)
    red_roles = list(draft.red_roles)
    existing_picks = len(blue_picks) + len(red_picks)

    if existing_picks == 0:
        # Pure blind pick: no real champions locked yet, so keep 50/50 baseline.
        return {
            "blue": 0.5,
            "red": 0.5
        }

    resolved_role = role.upper() if isinstance(role, str) else None

    if team == "blue":
        if len(blue_picks) >= 5:
            return None
        blue_picks.append(champion)
        blue_roles.append(resolved_role)
    else:
        if len(red_picks) >= 5:
            return None
        red_picks.append(champion)
        red_roles.append(resolved_role)

    return _predict_blue_win_probability(blue_picks, blue_roles, red_picks, red_roles)


def _contextual_noise(champion: str, our_team: List[str], enemy_team: List[str], requested_role: Optional[str]) -> float:
    """Context-aware jitter so early-draft recommendations vary per slot."""
    context_string = f"{champion}|{len(our_team)}|{len(enemy_team)}|{requested_role or 'flex'}"
    digest = hashlib.sha256(context_string.encode("utf-8")).hexdigest()
    return (int(digest[:8], 16) % 1000) / 100000.0


def _resolve_archetype_family(archetype: Optional[str]) -> tuple[str, str]:
    """Map archetypes into broader families for diversity heuristics."""
    if not archetype:
        return "flex", "flex pick"

    lowered = archetype.lower()
    for keyword, family_key, family_label in ARCHETYPE_FAMILY_KEYWORDS:
        if keyword in lowered:
            return family_key, family_label

    label = archetype.replace('_', ' ')
    return archetype, label


def _extract_rationale_tags(reasoning: List[str]) -> List[str]:
    """Convert verbose reasoning sentences into short badge labels."""
    tags: List[str] = []
    seen: Set[str] = set()

    for line in reasoning:
        lowered = line.lower()
        for pattern, label in RATIONALE_TAG_PATTERNS:
            if pattern in lowered and label not in seen:
                tags.append(label)
                seen.add(label)
                break
        if len(tags) >= 3:
            break

    if not tags:
        for line in reasoning:
            cleaned = line.replace('.', '').strip()
            if cleaned and cleaned not in seen:
                tags.append(cleaned)
                break

    return tags[:3]

def _score_champion_for_draft(
    champion: str,
    our_team: List[str],
    enemy_team: List[str],
    our_roles: List[str],
    requested_role: Optional[str],
    enemy_sim_comp: Optional[str] = None
) -> tuple[float, List[str], Optional[str], Dict[str, float], Optional[Dict[str, Any]]]:
    """Score a champion for current draft and suggest an optimal role."""
    score = 0.4  # Base score leaves room for differentiation
    reasoning: List[str] = []
    components = {
        "synergy": 0.0,
        "counters": 0.0,
        "role_fit": 0.0,
        "balance": 0.0,
        "comfort": 0.0,
        "diversity": 0.0
    }

    champ_info = champion_data["assignments"][champion]
    champ_archetype = champ_info["primary_archetype"]
    champ_attributes = set(_champ_info_attributes(champ_info))
    requested_role_upper = requested_role.upper() if requested_role else None

    our_archetypes = [
        champion_data["assignments"][c]["primary_archetype"]
        for c in our_team if c in champion_data["assignments"]
    ]

    family_counts: Dict[str, int] = {}
    for archetype in our_archetypes:
        family_key, _ = _resolve_archetype_family(archetype)
        family_counts[family_key] = family_counts.get(family_key, 0) + 1

    enemy_archetypes = [
        champion_data["assignments"][c]["primary_archetype"]
        for c in enemy_team if c in champion_data["assignments"]
    ]

    archetype_counts = {
        "damage": sum(1 for a in our_archetypes if "mage" in a or "assassin" in a or "marksman" in a),
        "tank": sum(1 for a in our_archetypes if "tank" in a or "warden" in a),
        "fighter": sum(1 for a in our_archetypes if "diver" in a or "skirmisher" in a or "juggernaut" in a),
        "support": sum(1 for a in our_archetypes if "enchanter" in a or "catcher" in a)
    }

    our_profile = _summarize_team_profile(our_team)
    enemy_profile = _summarize_team_profile(enemy_team)

    has_magic_damage = any("damage_magic" in attr for attr in champ_attributes)
    has_physical_damage = any("damage_physical" in attr for attr in champ_attributes)
    has_hard_cc = "cc_hard" in champ_attributes
    has_engage = any(attr.startswith("engage") or attr == "utility_engage" for attr in champ_attributes)
    has_poke = "range_long" in champ_attributes
    has_peel = any(attr in {"utility_peel", "utility_shields"} for attr in champ_attributes)
    has_frontline = any(attr in {"survive_tank", "engage_frontline", "survive_shields"} for attr in champ_attributes)
    has_mobility = "mobility_high" in champ_attributes
    has_sustain = any(attr in {"survive_sustain", "survive_heal", "utility_heal"} for attr in champ_attributes)

    if requested_role_upper and requested_role_upper in ROLE_ARCHETYPE_BONUS:
        archetype_bonus = ROLE_ARCHETYPE_BONUS[requested_role_upper].get(champ_archetype, 0.0)
        if archetype_bonus:
            score += archetype_bonus
            components["role_fit"] += archetype_bonus
            friendly = champ_archetype.replace('_', ' ')
            reasoning.append(f"{requested_role_upper.title()} slot values {friendly} archetype")

    if archetype_counts["damage"] == 0 and ("mage" in champ_archetype or "marksman" in champ_archetype):
        delta = 0.15
        score += delta
        components["balance"] += delta
        reasoning.append("Fills critical damage dealer gap")

    if archetype_counts["tank"] == 0 and ("tank" in champ_archetype or "warden" in champ_archetype):
        delta = 0.15
        score += delta
        components["balance"] += delta
        reasoning.append("Provides missing frontline presence")

    team_attributes = set()
    for champ in our_team:
        if champ in champion_data["assignments"]:
            team_attributes.update(_champion_attributes(champ))

    family_key, family_label = _resolve_archetype_family(champ_archetype)
    duplicate_family_count = family_counts.get(family_key, 0)
    if len(our_team) >= 3 and duplicate_family_count >= 2:
        penalty = 0.04 + min(duplicate_family_count - 1, 3) * 0.02
        score -= penalty
        components["diversity"] -= penalty
        reasoning.append(
            f"Already {duplicate_family_count} {family_label} picks locked — diversify threats"
        )

    if "engage" in champ_attributes and "damage_burst" in team_attributes:
        delta = 0.10
        score += delta
        components["synergy"] += delta
        reasoning.append("Engage synergizes with team's burst damage")

    if "range_long" in champ_attributes and "engage" in team_attributes:
        delta = 0.08
        score += delta
        components["synergy"] += delta
        reasoning.append("Poke/range complements team's engage")

    if "enchanter" in champ_archetype and "marksman" in " ".join(our_archetypes):
        delta = 0.12
        score += delta
        components["synergy"] += delta
        reasoning.append("Enchanter synergizes with marksman")

    enemy_attributes = set()
    for champ in enemy_team:
        if champ in champion_data["assignments"]:
            enemy_attributes.update(_champion_attributes(champ))

    if "assassin" in " ".join(enemy_archetypes) and "warden" in champ_archetype:
        delta = 0.15
        score += delta
        components["counters"] += delta
        reasoning.append("Counters enemy assassin threat")

    if "mobility_high" in enemy_attributes and "cc_hard" in champ_attributes:
        delta = 0.10
        score += delta
        components["counters"] += delta
        reasoning.append("Hard CC counters enemy mobility")

    if "range_long" in enemy_attributes and "engage" in champ_attributes:
        delta = 0.08
        score += delta
        components["counters"] += delta
        reasoning.append("Engage counters enemy poke")

    # Damage profile balancing
    if has_magic_damage:
        if our_profile["magic_damage"] == 0:
            delta = 0.12
            score += delta
            components["balance"] += delta
            reasoning.append("Introduces first magic damage threat")
        elif our_profile["magic_damage"] + 1 < our_profile["physical_damage"]:
            delta = 0.05
            score += delta
            components["balance"] += delta
            reasoning.append("Balances physical-heavy composition")
    elif our_profile["magic_damage"] == 0 and len(our_team) >= 2:
        score -= 0.04
        components["balance"] -= 0.04
        reasoning.append("Lineup still lacks dependable magic damage")

    if has_physical_damage:
        if our_profile["physical_damage"] == 0:
            delta = 0.12
            score += delta
            components["balance"] += delta
            reasoning.append("Adds first consistent physical damage")
        elif our_profile["physical_damage"] + 1 < our_profile["magic_damage"]:
            delta = 0.05
            score += delta
            components["balance"] += delta
            reasoning.append("Rebalances magic-heavy loadout")
    elif our_profile["physical_damage"] == 0 and len(our_team) >= 2:
        score -= 0.04
        components["balance"] -= 0.04
        reasoning.append("Still missing a physical threat")

    if has_hard_cc:
        if our_profile["hard_cc"] == 0:
            delta = 0.09
            score += delta
            components["synergy"] += delta
            reasoning.append("Adds reliable lockdown")
        elif our_profile["hard_cc"] >= 2:
            delta = 0.03
            score += delta
            components["synergy"] += delta
            reasoning.append("Stacks even more crowd control")

    if has_engage and our_profile["engage"] == 0:
        delta = 0.08
        score += delta
        components["synergy"] += delta
        reasoning.append("Provides the team's primary engage tool")

    if has_poke and our_profile["poke"] == 0:
        delta = 0.04
        score += delta
        components["synergy"] += delta
        reasoning.append("Adds long-range pressure for sieges")

    if has_frontline and our_profile["frontline"] == 0:
        delta = 0.10
        score += delta
        components["balance"] += delta
        reasoning.append("Supplies much-needed frontline durability")

    if has_peel and enemy_profile["engage"] >= 2:
        delta = 0.07
        score += delta
        components["counters"] += delta
        reasoning.append("Peels against enemy dive threats")

    if has_sustain and enemy_profile["poke"] >= 2:
        delta = 0.05
        score += delta
        components["counters"] += delta
        reasoning.append("Sustain mitigates poke damage")

    if has_engage and enemy_profile["poke"] >= 2:
        delta = 0.08
        score += delta
        components["counters"] += delta
        reasoning.append("Engage punishes enemy poke setup")

    if has_hard_cc and enemy_profile["mobility"] >= 2:
        delta = 0.06
        score += delta
        components["counters"] += delta
        reasoning.append("Locks down mobile threats")

    if has_frontline and enemy_profile["physical_damage"] >= 3:
        delta = 0.05
        score += delta
        components["counters"] += delta
        reasoning.append("Frontline absorbs heavy AD pressure")

    if has_peel and enemy_profile["magic_damage"] >= 3:
        delta = 0.04
        score += delta
        components["counters"] += delta
        reasoning.append("Protects carries from heavy AP burst")

    if has_mobility and enemy_profile["hard_cc"] >= 2:
        delta = 0.04
        score += delta
        components["comfort"] += delta
        reasoning.append("Mobile kit can dodge layered CC")

    same_archetype_count = our_archetypes.count(champ_archetype)
    if same_archetype_count >= 2:
        penalty = min(0.08, 0.04 * (same_archetype_count - 1))
        score -= penalty
        components["balance"] -= penalty
        reasoning.append("Avoids stacking another {} pick".format(champ_archetype.replace('_', ' ')))

    recommended_role, role_bonus, role_reasoning = _select_role_for_champion(
        champion,
        our_roles,
        requested_role
    )
    score += role_bonus
    components["role_fit"] += role_bonus
    reasoning.extend(role_reasoning)

    simulation_context: Optional[Dict[str, Any]] = None
    if simulation_matchup_table:
        team_with_candidate = list(our_team)
        team_with_candidate.append(champion)
        our_sim_comp = _infer_mass_composition(team_with_candidate)
        opponent_sim_comp = enemy_sim_comp or _infer_mass_composition(enemy_team)
        simulation_context = _lookup_mass_matchup(our_sim_comp, opponent_sim_comp)
        if simulation_context and simulation_context.get("win_rate") is not None:
            delta = float(simulation_context.get("delta") or 0.0)
            swing = max(-0.08, min(0.08, delta * 2.5))
            if swing:
                score += swing
                components["simulation_bias"] = round(components.get("simulation_bias", 0.0) + swing, 3)
            comp_label = _format_label(simulation_context.get("our_comp"))
            enemy_label = _format_label(simulation_context.get("enemy_comp"))
            win_pct = simulation_context["win_rate"] * 100.0
            sample = ""
            games = simulation_context.get("games")
            if isinstance(games, int) and games > 0:
                sample = f" over {games:,} sims"
            reasoning.append(
                f"15M sims: {comp_label} vs {enemy_label} wins {win_pct:.1f}%{sample}"
            )
            context_copy = dict(simulation_context)
            context_copy["score_bonus"] = swing
            simulation_context = context_copy

    score += _contextual_noise(champion, our_team, enemy_team, requested_role)

    score = max(0.0, min(1.0, score))

    if not reasoning:
        reasoning.append("Solid pick for composition")

    components = {k: round(v, 3) for k, v in components.items() if abs(v) > 0.001}
    return score, reasoning, recommended_role, components, simulation_context


def _generate_recommendations_for_slot(
    available_champions: Set[str],
    our_team: List[str],
    enemy_team: List[str],
    our_roles: List[str],
    requested_role: Optional[str],
    limit: int
) -> List[ChampionRecommendation]:
    """Generate sorted recommendations for a single pick slot."""
    recommendations: List[ChampionRecommendation] = []
    enemy_sim_comp = _infer_mass_composition(enemy_team)

    for champion in available_champions:
        if requested_role:
            champion_roles = _get_champion_roles(champion)
            if requested_role not in champion_roles:
                continue

        score, reasoning, recommended_role, breakdown, sim_context = _score_champion_for_draft(
            champion,
            our_team,
            enemy_team,
            our_roles,
            requested_role,
            enemy_sim_comp
        )

        champ_info = champion_data["assignments"][champion]

        recommendations.append(ChampionRecommendation(
            champion=champion,
            score=score,
            archetype=champ_info["primary_archetype"],
            recommended_role=recommended_role,
            attribute_highlights=_get_attribute_highlights(champ_info),
            reasoning=reasoning,
            score_breakdown=breakdown,
            rationale_tags=_extract_rationale_tags(reasoning),
            simulation_matchup=sim_context
        ))

    recommendations.sort(key=lambda x: x.score, reverse=True)
    recommendations = _apply_recommendation_diversity_penalty(recommendations)
    return _round_robin_sample_recommendations(recommendations, limit)


def _apply_recommendation_diversity_penalty(
    ranked_recommendations: List[ChampionRecommendation]
) -> List[ChampionRecommendation]:
    """Down-rank repeated archetype families and roles to avoid clones."""
    family_counts: Dict[str, int] = defaultdict(int)
    role_counts: Dict[str, int] = defaultdict(int)
    adjusted: List[ChampionRecommendation] = []

    for rec in ranked_recommendations:
        family_key, _ = _resolve_archetype_family(rec.archetype)
        family_penalty = family_counts[family_key] * FAMILY_STACK_PENALTY

        role_penalty = 0.0
        if rec.recommended_role:
            role_penalty = role_counts[rec.recommended_role] * ROLE_STACK_PENALTY

        total_penalty = family_penalty + role_penalty

        if total_penalty > 0:
            breakdown = dict(rec.score_breakdown)
            breakdown["diversity_penalty"] = round(
                breakdown.get("diversity_penalty", 0.0) - total_penalty,
                3
            )
            rec = rec.copy(update={
                "score": max(0.0, rec.score - total_penalty),
                "score_breakdown": breakdown
            })

        adjusted.append(rec)
        family_counts[family_key] += 1
        if rec.recommended_role:
            role_counts[rec.recommended_role] += 1

    adjusted.sort(key=lambda x: x.score, reverse=True)
    return adjusted


def _round_robin_sample_recommendations(
    ranked_recommendations: List[ChampionRecommendation],
    limit: int
) -> List[ChampionRecommendation]:
    """Distribute recommendations across archetype families to ensure variety."""
    if limit <= 0:
        return []
    if len(ranked_recommendations) <= limit:
        return ranked_recommendations

    grouped: Dict[str, List[ChampionRecommendation]] = {}
    for rec in ranked_recommendations:
        family_key, _ = _resolve_archetype_family(rec.archetype)
        grouped.setdefault(family_key, []).append(rec)

    if not grouped:
        return ranked_recommendations[:limit]

    for family_list in grouped.values():
        family_list.sort(key=lambda x: x.score, reverse=True)

    family_order = sorted(
        grouped.keys(),
        key=lambda key: grouped[key][0].score,
        reverse=True
    )

    cursors = {key: 0 for key in family_order}
    sampled: List[ChampionRecommendation] = []

    while len(sampled) < limit:
        progressed = False
        for family_key in family_order:
            cursor = cursors[family_key]
            family_list = grouped[family_key]
            if cursor >= len(family_list):
                continue
            sampled.append(family_list[cursor])
            cursors[family_key] += 1
            progressed = True
            if len(sampled) == limit:
                break
        if not progressed:
            break

    return sampled


def _analyze_draft_state(our_team: List[str], enemy_team: List[str]) -> Dict:
    """Analyze current draft state."""
    analysis = {
        "our_composition": {
            "picks": len(our_team),
            "archetypes": [],
            "missing_roles": []
        },
        "enemy_composition": {
            "picks": len(enemy_team),
            "archetypes": [],
            "threats": []
        }
    }
    
    # Our composition
    if our_team:
        our_archetypes = [
            champion_data["assignments"][c]["primary_archetype"]
            for c in our_team if c in champion_data["assignments"]
        ]
        analysis["our_composition"]["archetypes"] = list(set(our_archetypes))
        
        # Check missing roles
        has_damage = any("mage" in a or "assassin" in a or "marksman" in a for a in our_archetypes)
        has_tank = any("tank" in a or "warden" in a for a in our_archetypes)
        has_support = any("enchanter" in a or "catcher" in a for a in our_archetypes)
        
        missing = []
        if not has_damage:
            missing.append("damage_dealer")
        if not has_tank:
            missing.append("tank")
        if not has_support:
            missing.append("support")
        
        analysis["our_composition"]["missing_roles"] = missing
    
    # Enemy composition
    if enemy_team:
        enemy_archetypes = [
            champion_data["assignments"][c]["primary_archetype"]
            for c in enemy_team if c in champion_data["assignments"]
        ]
        analysis["enemy_composition"]["archetypes"] = list(set(enemy_archetypes))
        
        # Identify threats
        threats = []
        if "burst_assassin" in enemy_archetypes:
            threats.append("assassin_threat")
        if sum(1 for a in enemy_archetypes if "mage" in a) >= 2:
            threats.append("heavy_magic_damage")
        if "artillery_mage" in enemy_archetypes:
            threats.append("poke_threat")
        
        analysis["enemy_composition"]["threats"] = threats
    
    return analysis


def _get_champion_roles(champion: str) -> List[str]:
    """Return normalized lane roles for a champion."""
    if champion_data is None:
        return []

    champ_info = champion_data["assignments"].get(champion)
    if not champ_info:
        return []

    roles: List[str] = []

    def _add_role(position: Optional[str]):
        if not position:
            return
        normalized = POSITION_TO_ROLE.get(position, position.upper())
        if normalized not in roles:
            roles.append(normalized)

    _add_role(champ_info.get("primary_position"))
    for pos in champ_info.get("viable_positions", []):
        _add_role(pos)

    return roles


def _get_needed_roles(current_roles: List[str]) -> List[str]:
    """Determine which standard roles have not been drafted yet."""
    counts = {role: 0 for role in ROLE_ORDER}
    for role in current_roles:
        if role in counts:
            counts[role] += 1

    missing = [role for role in ROLE_ORDER if counts[role] == 0]
    return missing


def _select_placeholder_champion(role: str) -> str:
    """Select a balanced champion to stand in for missing roles during projections."""
    candidate = ROLE_PLACEHOLDER_CHAMPIONS.get(role)
    assignments = champion_data.get("assignments", {}) if champion_data else {}
    if candidate in assignments:
        return candidate
    for fallback in ROLE_PLACEHOLDER_CHAMPIONS.values():
        if fallback in assignments:
            return fallback
    # Final fallback: return any champion in the dataset
    if assignments:
        return next(iter(assignments.keys()))
    return DEFAULT_PLACEHOLDER_CHAMPION


def _select_role_for_champion(
    champion: str,
    our_roles: List[str],
    requested_role: Optional[str]
) -> tuple[Optional[str], float, List[str]]:
    """Choose the best role fit for a recommendation."""
    reasoning: List[str] = []
    bonus = 0.0

    requested_upper = requested_role.upper() if isinstance(requested_role, str) else None
    champion_roles = _get_champion_roles(champion)
    needed_roles = _get_needed_roles(our_roles)

    recommended_role: Optional[str] = None

    if requested_upper and requested_upper in champion_roles:
        recommended_role = requested_upper
        bonus += 0.06
        reasoning.append(f"Optimal comfort pick for {requested_upper} role")

    if recommended_role is None:
        for role in needed_roles:
            if role in champion_roles:
                recommended_role = role
                bonus += 0.08
                reasoning.append(f"Fills empty {role} slot")
                break

    if recommended_role is None and champion_roles:
        recommended_role = champion_roles[0]
        if requested_upper and requested_upper not in champion_roles:
            bonus -= 0.03
            reasoning.append(f"Prefers {recommended_role} over requested {requested_upper}")

    if recommended_role is None and requested_upper:
        recommended_role = requested_upper

    return recommended_role, bonus, reasoning


def _format_label(value: Optional[str]) -> str:
    if not value:
        return "Flexible"
    return value.replace('_', ' ').title()


def _infer_mass_composition(team: List[str]) -> Optional[str]:
    if not team or not champion_data:
        return None
    assignments = champion_data.get("assignments", {})
    archetypes: List[str] = []
    range_sources = 0
    for champion in team:
        info = assignments.get(champion)
        if not info:
            continue
        archetype = info.get("primary_archetype")
        if archetype:
            archetypes.append(archetype)
        attrs = _champ_info_attributes(info)
        if any(attr.startswith("range_") for attr in attrs):
            range_sources += 1
    if not archetypes:
        return None

    if sum(1 for a in archetypes if "diver" in a or "assassin" in a) >= 2:
        return "dive"
    if "artillery_mage" in archetypes and range_sources >= 2:
        return "poke"
    has_tank = any("tank" in a or "warden" in a for a in archetypes)
    has_marksman = any("marksman" in a for a in archetypes)
    has_enchanter = any("enchanter" in a for a in archetypes)
    if has_tank and has_marksman and has_enchanter:
        return "protect_the_carry"
    if sum(1 for a in archetypes if "skirmisher" in a or "juggernaut" in a) >= 2:
        return "bruiser"
    return "mixed"


def _lookup_mass_matchup(
    our_comp: Optional[str],
    enemy_comp: Optional[str]
) -> Optional[Dict[str, Any]]:
    if not our_comp or not enemy_comp:
        return None
    entry = simulation_matchup_table.get((our_comp, enemy_comp))
    orientation = "blue"
    if entry is None:
        entry = simulation_matchup_table.get((enemy_comp, our_comp))
        orientation = "red"
    if entry is None:
        return None
    if orientation == "blue":
        win_rate = entry.get("avg_blue_win_prob")
        ci = entry.get("blue_ci_half_width")
    else:
        win_rate = entry.get("avg_red_win_prob")
        ci = entry.get("red_ci_half_width")
    if not isinstance(win_rate, (int, float)):
        return None
    delta = win_rate - 0.5
    return {
        "our_comp": our_comp,
        "enemy_comp": enemy_comp,
        "win_rate": win_rate,
        "delta": delta,
        "games": entry.get("games"),
        "ci": ci
    }


def _mass_matchup_snapshot(
    blue_comp: Optional[str],
    red_comp: Optional[str]
) -> Optional[Dict[str, Any]]:
    if not blue_comp or not red_comp:
        return None
    entry = simulation_matchup_table.get((blue_comp, red_comp))
    if entry is None:
        return None
    blue_wr = entry.get("avg_blue_win_prob")
    red_wr = entry.get("avg_red_win_prob")
    return {
        "blue_comp": blue_comp,
        "red_comp": red_comp,
        "blue_win_rate": blue_wr,
        "red_win_rate": red_wr,
        "games": entry.get("games"),
        "blue_delta": (blue_wr - 0.5) if isinstance(blue_wr, (int, float)) else None,
        "red_delta": (red_wr - 0.5) if isinstance(red_wr, (int, float)) else None,
        "blue_ci": entry.get("blue_ci_half_width"),
        "red_ci": entry.get("red_ci_half_width"),
    }


def _count_archetypes_by_keywords(analysis: Dict[str, Any], keywords: List[str]) -> int:
    distribution = analysis.get("archetype_distribution", {}) if analysis else {}
    return sum(
        count
        for name, count in distribution.items()
        if any(keyword in name for keyword in keywords)
    )


def _count_profile_entries(entries: List[str], keyword: str) -> int:
    if not entries:
        return 0
    return sum(1 for value in entries if keyword in value)


def _build_team_profile(analysis: Dict[str, Any]) -> Dict[str, int]:
    """Summarize key profile counts used for matchup narratives."""
    return {
        "range": _count_profile_entries(analysis.get("range_profile", []), "long"),
        "poke": _count_profile_entries(analysis.get("range_profile", []), "poke"),
        "hard_cc": _count_profile_entries(analysis.get("cc_profile", []), "hard"),
        "magic": _count_profile_entries(analysis.get("damage_types", []), "magic"),
        "physical": _count_profile_entries(analysis.get("damage_types", []), "physical"),
        "mobility": len(analysis.get("mobility_profile", []) or []),
        "peel": _count_archetypes_by_keywords(analysis, ["enchanter", "warden", "catcher"]),
        "engage": _count_archetypes_by_keywords(analysis, ["engage", "diver"]),
        "sustain": _count_archetypes_by_keywords(analysis, ["enchanter", "warden"]),
        "bruiser": _count_archetypes_by_keywords(analysis, ["juggernaut", "skirmisher"])
    }


def _build_counter_statements(
    favored_label: str,
    underdog_label: str,
    favored_analysis: Dict[str, Any],
    underdog_analysis: Dict[str, Any],
    favored_pct: float,
    sim_pct: Optional[float]
) -> tuple[List[str], List[str]]:
    favored_comp = _format_label(favored_analysis.get("composition_type"))
    underdog_comp = _format_label(underdog_analysis.get("composition_type"))

    favored_insights: List[str] = []
    comeback_insights: List[str] = []

    favored_profile = _build_team_profile(favored_analysis)
    underdog_profile = _build_team_profile(underdog_analysis)

    engage_favored = favored_profile["engage"]
    engage_underdog = underdog_profile["engage"]
    engage_adv = engage_favored - engage_underdog
    poke_threat = underdog_profile["range"]

    peel_favored = favored_profile["peel"]
    peel_underdog = underdog_profile["peel"]
    peel_adv = peel_favored - peel_underdog
    diver_threat = _count_archetypes_by_keywords(underdog_analysis, ["diver", "assassin"])

    bruiser_favored = favored_profile["bruiser"]
    bruiser_underdog = underdog_profile["bruiser"]
    bruiser_gap = bruiser_favored - bruiser_underdog

    if engage_adv >= 1:
        favored_insights.append(
            f"{favored_label} control fight starts with {engage_favored} engage tool{'s' if engage_favored > 1 else ''}; {underdog_label} must wait for mistakes or picks (only {engage_underdog} engage starter{'s' if engage_underdog > 1 else ''})."
        )
        comeback_insights.append(
            f"{underdog_label} trail engage tools ({engage_underdog} vs {engage_favored}), so they should bait around key cooldowns or punish {favored_label}'s overextensions rather than forcing blind fights."
        )
    elif engage_favored >= 2:
        favored_insights.append(
            f"{favored_label} have cleaner engage windows ({engage_favored} starters), so they can force {underdog_label} into reactionary plays."
        )

    if peel_adv > 0 and peel_favored >= 1:
        favored_insights.append(
            f"{favored_label} protect their carries with {peel_favored} peel piece{'s' if peel_favored > 1 else ''}; {underdog_label} divers will struggle to reach backline targets."
        )
        if diver_threat > 0:
            comeback_insights.append(
                f"{underdog_label} have limited peel ({peel_underdog} tool{'s' if peel_underdog != 1 else ''}) against {favored_label}'s dive; stopwatches, defensive vision, and split pressure become mandatory."
            )
        else:
            comeback_insights.append(
                f"{underdog_label} lack backline protection; carries need perfect positioning or the fight collapses instantly."
            )

    if bruiser_gap >= 2:
        favored_insights.append(
            f"{favored_label} bring {bruiser_favored} bruiser{'s' if bruiser_favored > 1 else ''} to dominate extended skirmishes; {underdog_label} cannot match them in melee."
        )
        comeback_insights.append(
            f"{underdog_label} must avoid prolonged brawls where {favored_label}'s bruisers thrive; trade objectives and kite instead."
        )

    favored_range = favored_profile["range"]
    underdog_range = underdog_profile["range"]
    if favored_range >= 2 and favored_range > underdog_range:
        favored_insights.append(
            f"{favored_label} outrange {underdog_label} significantly ({favored_range} long-range vs {underdog_range}), letting them chip objectives and force engages on their terms."
        )
        comeback_insights.append(
            f"{underdog_label} will bleed towers to {favored_label}'s poke ({favored_range} long-range champions); they should force scrappy fights off waves to avoid slow sieges."
        )

    favored_hard_cc = favored_profile["hard_cc"]
    underdog_hard_cc = underdog_profile["hard_cc"]
    if favored_hard_cc >= 2 and favored_hard_cc > underdog_hard_cc:
        favored_insights.append(
            f"{favored_label} chain {favored_hard_cc} hard CC tools to lock down priority targets; {underdog_label} need cleanse/QSS or perfect spacing."
        )
        comeback_insights.append(
            f"{underdog_label} bring less hard CC ({underdog_hard_cc} vs {favored_hard_cc}), making it harder to lock priority targets; they rely on kiting and poke rather than setups."
        )

    favored_magic = favored_profile["magic"] > 0
    favored_physical = favored_profile["physical"] > 0
    underdog_magic = underdog_profile["magic"] > 0
    underdog_physical = underdog_profile["physical"] > 0

    if favored_magic and favored_physical and (not (underdog_magic and underdog_physical)):
        underdog_type = 'armor' if not underdog_magic else 'MR'
        favored_insights.append(
            f"{favored_label} force split item builds with mixed damage; {underdog_label} can only stack {underdog_type} and remain vulnerable elsewhere."
        )
        underdog_damage_type = 'physical' if not underdog_magic else 'magic'
        comeback_insights.append(
            f"{underdog_label} deal mostly {underdog_damage_type} damage; they need early leads before {favored_label} stack the right resistances and neutralize their threats."
        )

    favored_mobility = favored_profile["mobility"]
    underdog_mobility = underdog_profile["mobility"]
    if favored_mobility >= 2 and favored_mobility > underdog_mobility:
        favored_insights.append(
            f"{favored_label} threaten flanks with {favored_mobility} mobile champion{'s' if favored_mobility > 1 else ''}; {underdog_label} must maintain vision control or risk getting picked off-angle."
        )
        comeback_insights.append(
            f"{underdog_label} cannot match {favored_label}'s flank threat ({favored_mobility} mobile champions vs {underdog_mobility}); deep wards and grouped farming are critical to avoid isolated deaths."
        )

    if favored_profile["sustain"] > underdog_profile["sustain"] and favored_profile["sustain"] >= 1:
        favored_insights.append(
            f"{favored_label} have {favored_profile['sustain']} sustain/shield source{'s' if favored_profile['sustain'] > 1 else ''} to extend fights and reset after trades."
        )
        comeback_insights.append(
            f"{underdog_label} must burst quickly before {favored_label}'s shields and heals reset the fight; avoid drawn-out skirmishes."
        )

    if not comeback_insights:
        comeback_insights.append(
            f"{underdog_label} need to execute {underdog_comp} properly: find picks, avoid grouped 5v5s where {favored_label} have the edge, and punish cooldown windows."
        )

    if not favored_insights:
        favored_insights.append(
            f"{favored_label} drafted {favored_comp} — they win by controlling engages ({favored_profile['engage']} starter{'s' if favored_profile['engage'] > 1 else ''}) and layering CC ({favored_hard_cc} hard lockdown tool{'s' if favored_hard_cc > 1 else ''})."
        )

    return favored_insights[:4], comeback_insights[:4]


def _swap_champion_for_impact(
    team: List[str],
    roles: List[str],
    index: int
) -> tuple[List[str], List[str], str]:
    new_team = list(team)
    new_roles = list(roles)
    if index >= len(new_roles):
        return team, roles, ROLE_ORDER[index % len(ROLE_ORDER)]
    role_value = new_roles[index] or ROLE_ORDER[index % len(ROLE_ORDER)]
    placeholder = DEFAULT_PLACEHOLDER_CHAMPION
    new_team[index] = placeholder
    return new_team, new_roles, role_value


def _identify_key_champions(
    blue_team: List[str],
    blue_roles: List[str],
    red_team: List[str],
    red_roles: List[str],
    base_projection: Dict[str, Any]
) -> Dict[str, Any]:
    if not base_projection:
        return {}

    favored_side = base_projection.get("favored", "blue")
    base_blue = base_projection.get("blue", 0.5)
    base_favored = base_blue if favored_side == "blue" else 1 - base_blue

    favored_team = blue_team if favored_side == "blue" else red_team
    favored_roles = blue_roles if favored_side == "blue" else red_roles
    underdog_team = red_team if favored_side == "blue" else blue_team
    underdog_roles = red_roles if favored_side == "blue" else blue_roles

    playmaker: Optional[Dict[str, Any]] = None
    playmaker_impact = 0.0

    for idx, champion in enumerate(favored_team):
        swapped_team, swapped_roles, role_value = _swap_champion_for_impact(favored_team, favored_roles, idx)
        if favored_side == "blue":
            projection = _predict_blue_win_probability(swapped_team, swapped_roles, underdog_team, underdog_roles)
        else:
            projection = _predict_blue_win_probability(underdog_team, underdog_roles, swapped_team, swapped_roles)
        if not projection:
            continue
        alt_blue = projection.get("blue", base_blue)
        alt_favored = alt_blue if favored_side == "blue" else 1 - alt_blue
        impact = base_favored - alt_favored
        if impact > playmaker_impact + 1e-4:
            playmaker_impact = impact
            playmaker = {
                "champion": champion,
                "role": role_value,
                "impact": impact,
                "impact_pct": impact * 100.0
            }

    threat: Optional[Dict[str, Any]] = None
    threat_impact = 0.0

    for idx, champion in enumerate(underdog_team):
        swapped_team, swapped_roles, role_value = _swap_champion_for_impact(underdog_team, underdog_roles, idx)
        if favored_side == "blue":
            projection = _predict_blue_win_probability(favored_team, favored_roles, swapped_team, swapped_roles)
        else:
            projection = _predict_blue_win_probability(swapped_team, swapped_roles, favored_team, favored_roles)
        if not projection:
            continue
        alt_blue = projection.get("blue", base_blue)
        alt_favored = alt_blue if favored_side == "blue" else 1 - alt_blue
        swing = alt_favored - base_favored
        if swing > threat_impact + 1e-4:
            threat_impact = swing
            threat = {
                "champion": champion,
                "role": role_value,
                "impact": swing,
                "impact_pct": swing * 100.0
            }

    result: Dict[str, Any] = {}
    if playmaker and playmaker_impact > 0:
        result["favored_playmaker"] = playmaker
    if threat and threat_impact > 0:
        result["underdog_threat"] = threat
    return result


def _build_matchup_context(
    blue_team: List[str],
    blue_roles: List[str],
    red_team: List[str],
    red_roles: List[str],
    blue_analysis: Dict[str, Any],
    red_analysis: Dict[str, Any],
    base_projection: Optional[Dict[str, Any]] = None,
    raw_result: Optional[PredictionResult] = None
) -> Dict[str, Any]:
    projection = base_projection or _predict_blue_win_probability(blue_team, blue_roles, red_team, red_roles)

    if projection:
        blended_blue = projection.get("blue", raw_result.blue_win_probability if raw_result else 0.5)
        blended_red = projection.get("red", raw_result.red_win_probability if raw_result else 0.5)
        simulated_blue = projection.get("simulated_blue")
        simulated_red = projection.get("simulated_red")
        favored_side = projection.get("favored", raw_result.winner if raw_result else ("blue" if blended_blue >= blended_red else "red"))
        confidence = projection.get("confidence", raw_result.confidence if raw_result else 0.0)
        base_projection_payload = projection
    else:
        blended_blue = raw_result.blue_win_probability if raw_result else 0.5
        blended_red = raw_result.red_win_probability if raw_result else 0.5
        simulated_blue = None
        simulated_red = None
        favored_side = raw_result.winner if raw_result else "blue"
        confidence = raw_result.confidence if raw_result else 0.0
        base_projection_payload = {
            "blue": blended_blue,
            "red": blended_red,
            "favored": favored_side
        }

    favored_label = "Blue" if favored_side == "blue" else "Red"
    underdog_side = "red" if favored_side == "blue" else "blue"
    underdog_label = "Red" if underdog_side == "red" else "Blue"

    favored_analysis_obj = blue_analysis if favored_side == "blue" else red_analysis
    underdog_analysis_obj = red_analysis if favored_side == "blue" else blue_analysis

    favored_probability = blended_blue if favored_side == "blue" else blended_red
    favored_pct = favored_probability * 100.0
    sim_pct = None
    if simulated_blue is not None:
        sim_value = simulated_blue if favored_side == "blue" else (1.0 - simulated_blue)
        sim_pct = sim_value * 100.0

    favored_insights, comeback_insights = _build_counter_statements(
        favored_label,
        underdog_label,
        favored_analysis_obj,
        underdog_analysis_obj,
        favored_pct,
        sim_pct
    )

    context: Dict[str, Any] = {
        "favored": favored_side,
        "favored_label": favored_label,
        "underdog_label": underdog_label,
        "favored_probability": favored_probability,
        "favored_winrate_pct": favored_pct,
        "blended_blue": blended_blue,
        "blended_red": blended_red,
        "simulated_blue": simulated_blue,
        "simulated_red": simulated_red,
        "simulated_winrate_pct": sim_pct,
        "confidence": confidence,
        "favored_composition": _format_label(favored_analysis_obj.get("composition_type")),
        "underdog_composition": _format_label(underdog_analysis_obj.get("composition_type")),
        "favored_insights": favored_insights,
        "underdog_insights": comeback_insights
    }

    context.update(_identify_key_champions(
        blue_team,
        blue_roles,
        red_team,
        red_roles,
        base_projection_payload
    ))

    sim_snapshot = _mass_matchup_snapshot(
        _infer_mass_composition(blue_team),
        _infer_mass_composition(red_team)
    )
    if sim_snapshot:
        context["mass_simulation"] = sim_snapshot

    return context


def _record_analysis_telemetry(
    request: AnalysisRequest,
    prediction_block: Dict[str, Any],
    matchup_context: Dict[str, Any]
) -> None:
    """Persist telemetry for downstream calibration without impacting API latency."""
    if not prediction_block:
        return

    try:
        payload = {
            "blue_team": request.blue_team,
            "blue_roles": request.blue_roles,
            "red_team": request.red_team,
            "red_roles": request.red_roles,
            "prediction": {
                "winner": prediction_block.get("winner"),
                "confidence": prediction_block.get("confidence"),
                "blue_win_probability": prediction_block.get("blue_win_probability"),
                "red_win_probability": prediction_block.get("red_win_probability"),
            },
            "favored_context": {
                "favored": matchup_context.get("favored"),
                "favored_winrate_pct": matchup_context.get("favored_winrate_pct"),
                "simulated_winrate_pct": matchup_context.get("simulated_winrate_pct"),
                "playmaker": matchup_context.get("favored_playmaker"),
                "threat": matchup_context.get("underdog_threat"),
            },
            "actual_winner": request.actual_winner,
        }
        log_prediction_event("draft_analyze", payload)
    except Exception as exc:
        print(f"Telemetry logging skipped: {exc}")


def _sort_slot_recommendations(slot: SlotRecommendations) -> None:
    """Order recommendations by projected win rate, fallback to fit score."""

    def _sort_key(rec: ChampionRecommendation) -> Tuple[int, float]:
        team_rate = rec.projected_team_winrate
        if isinstance(team_rate, (int, float)):
            return (0, float(team_rate))
        score = rec.score if isinstance(rec.score, (int, float)) else 0.0
        return (1, float(score))

    slot.recommendations.sort(key=_sort_key, reverse=True)


def _analyze_team_composition(team: List[str], roles: List[str]) -> Dict:
    """Analyze a complete team composition."""
    archetypes = []
    attributes = {
        "damage_types": [],
        "range_profile": [],
        "mobility_profile": [],
        "cc_profile": []
    }
    
    for champion in team:
        if champion not in champion_data["assignments"]:
            continue
        
        champ_info = champion_data["assignments"][champion]
        archetypes.append(champ_info["primary_archetype"])
        
        champ_attrs = _champ_info_attributes(champ_info)
        
        # Categorize attributes
        for attr in champ_attrs:
            if "damage_" in attr:
                attributes["damage_types"].append(attr)
            elif "range_" in attr:
                attributes["range_profile"].append(attr)
            elif "mobility_" in attr or "dash" in attr or "blink" in attr:
                attributes["mobility_profile"].append(attr)
            elif "cc_" in attr:
                attributes["cc_profile"].append(attr)
    
    return {
        "archetypes": list(set(archetypes)),
        "archetype_distribution": {
            archetype: archetypes.count(archetype)
            for archetype in set(archetypes)
        },
        "damage_types": list(set(attributes["damage_types"])),
        "range_profile": list(set(attributes["range_profile"])),
        "mobility_profile": list(set(attributes["mobility_profile"])),
        "cc_profile": list(set(attributes["cc_profile"])),
        "composition_type": _infer_composition_type(archetypes, attributes)
    }


def _infer_composition_type(archetypes: List[str], attributes: Dict) -> str:
    """Infer high-level composition type."""
    # Dive comp: multiple divers/assassins
    if sum(1 for a in archetypes if "diver" in a or "assassin" in a) >= 2:
        return "dive"
    
    # Poke comp: artillery mage + long range
    if "artillery_mage" in archetypes and len(attributes["range_profile"]) >= 2:
        return "poke"
    
    # Front-to-back: tank + marksman + enchanter
    has_tank = any("tank" in a or "warden" in a for a in archetypes)
    has_marksman = "marksman" in archetypes
    has_enchanter = "enchanter" in archetypes
    if has_tank and has_marksman and has_enchanter:
        return "front_to_back"
    
    # Skirmish: multiple fighters
    if sum(1 for a in archetypes if "skirmisher" in a or "juggernaut" in a) >= 2:
        return "skirmish"
    
    return "mixed"


def _get_archetype_description(archetype: str) -> str:
    """Get description for archetype."""
    descriptions = {
        "marksman": "Ranged sustained damage dealer, scales with items, vulnerable but high DPS",
        "burst_mage": "High burst magic damage, skill-shot dependent, fragile but threatening",
        "burst_assassin": "High mobility single-target burst, excels at eliminating carries",
        "engage_tank": "Initiates teamfights with hard CC, soaks damage for team",
        "warden": "Protective tank, excels at peeling for carries",
        "diver": "Jumps onto backline, disrupts and threatens enemy carries",
        "juggernaut": "Low mobility high durability fighter, dominates melee range",
        "skirmisher": "Sustained damage fighter, excels in extended 1v1s",
        "battle_mage": "Short-range sustained magic damage, durable mage",
        "enchanter": "Heals and shields allies, enables carries to survive",
        "catcher": "Picks off enemies with long-range CC, creates picks",
        "artillery_mage": "Long-range poke, controls zones, siege specialist",
        "specialist": "Unique mechanics, doesn't fit standard patterns"
    }
    return descriptions.get(archetype, "Unique playstyle")


def _format_attribute_label(attribute: str) -> str:
    """Convert attribute keys into human-friendly labels."""
    if not attribute:
        return ""
    return attribute.replace("_", " ").title()


def _get_attribute_highlights(champ_info: Dict[str, Any]) -> List[str]:
    """Return a concise list of standout attributes for UI display."""
    highlights: List[str] = []
    for attribute in _champ_info_attributes(champ_info):
        label = _format_attribute_label(attribute)
        if label and label not in highlights:
            highlights.append(label)
        if len(highlights) == 3:
            break
    return highlights


# === Health Helpers ===

def _normalize_simulation_metadata(metadata: Optional[Dict[str, Any]], summary: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Ensure total_games is populated for dashboard consumers."""
    normalized = dict(metadata or {})
    total_games = normalized.get("total_games") or normalized.get("games")
    if total_games is None and summary:
        overall = summary.get("overall") or {}
        total_games = overall.get("total_games")
    if total_games is not None:
        normalized["total_games"] = total_games
    return normalized


def _convert_mass_summary_to_analysis(summary: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Adapt mass-simulation payloads to the legacy dashboard schema."""
    if not summary:
        return None

    overall = summary.get("overall") or {}
    blue_wr = overall.get("avg_blue_win_probability")
    prediction_distribution: Dict[str, Any] = {}
    if isinstance(blue_wr, (int, float)):
        prediction_distribution["blue_win_rate"] = blue_wr
        prediction_distribution["red_win_rate"] = 1.0 - blue_wr
    avg_conf = overall.get("avg_confidence")
    if isinstance(avg_conf, (int, float)):
        prediction_distribution["average_confidence"] = avg_conf
    conf_half = overall.get("confidence_half_width")
    if isinstance(conf_half, (int, float)):
        prediction_distribution["confidence_half_width"] = conf_half

    confidence_metrics = {
        "average_confidence": avg_conf,
        "confidence_half_width": conf_half,
    }

    analysis: Dict[str, Any] = {
        "prediction_distribution": prediction_distribution,
        "confidence_metrics": confidence_metrics,
        "top_matchups": summary.get("top_matchups"),
        "bottom_matchups": summary.get("bottom_matchups"),
        "composition_totals": summary.get("composition_totals"),
    }

    if summary.get("raw_matchups"):
        analysis["raw_matchups"] = summary["raw_matchups"]
    if summary.get("raw_compositions"):
        analysis["raw_compositions"] = summary["raw_compositions"]

    return analysis


def _load_simulation_summary() -> Dict[str, Any]:
    """Load metadata and analysis from the latest simulation summary file."""
    payload: Dict[str, Any] = {
        "path": str(SIMULATION_SUMMARY_PATH),
        "exists": SIMULATION_SUMMARY_PATH.exists(),
        "last_modified": None,
        "metadata": None,
        "analysis": None,
        "sample_games": None,
        "status": "missing"
    }

    if not payload["exists"]:
        return payload

    try:
        payload["last_modified"] = _safe_iso_timestamp(SIMULATION_SUMMARY_PATH.stat().st_mtime)
    except OSError as exc:
        payload["stat_error"] = str(exc)

    try:
        with SIMULATION_SUMMARY_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        summary_block = data.get("summary")
        metadata_block = _normalize_simulation_metadata(data.get("metadata"), summary_block)
        analysis_block = data.get("analysis") or _convert_mass_summary_to_analysis(summary_block)
        payload["metadata"] = metadata_block
        payload["analysis"] = analysis_block
        payload["sample_games"] = data.get("sample_games")
        payload["status"] = "ready"
    except Exception as exc:
        payload["status"] = "error"
        payload["load_error"] = str(exc)

    return payload


def _refresh_mass_simulation_tables() -> None:
    """Hydrate lookup tables from the latest simulation summary for fast access."""
    global simulation_summary_cache, simulation_matchup_table, simulation_composition_table
    payload = _load_simulation_summary()
    simulation_summary_cache = payload
    analysis = payload.get("analysis") or {}
    raw_matchups = analysis.get("raw_matchups") or {}
    matchups: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for key, entry in raw_matchups.items():
        blue_comp = entry.get("blue_comp")
        red_comp = entry.get("red_comp")
        if not blue_comp or not red_comp:
            try:
                blue_comp, red_comp = key.split("__vs__")
            except ValueError:
                continue
        matchups[(blue_comp, red_comp)] = {
            "blue_comp": blue_comp,
            "red_comp": red_comp,
            "games": entry.get("games", 0),
            "avg_blue_win_prob": entry.get("avg_blue_win_prob"),
            "avg_red_win_prob": entry.get("avg_red_win_prob"),
            "blue_ci_half_width": entry.get("blue_ci_half_width"),
            "red_ci_half_width": entry.get("red_ci_half_width")
        }
    simulation_matchup_table = matchups
    simulation_composition_table = analysis.get("raw_compositions") or {}


def _safe_iso_timestamp(raw_ts: Optional[float]) -> Optional[str]:
    """Convert raw seconds timestamp to ISO-8601 string."""
    if raw_ts is None:
        return None
    try:
        return datetime.fromtimestamp(float(raw_ts), tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except Exception:
        return None


def _model_status() -> Dict[str, Any]:
    """Report whether core artifacts finished loading."""
    return {
        "predictor_loaded": predictor is not None,
        "champion_index_loaded": bool(champion_data),
        "attribute_index_loaded": bool(attribute_data),
        "simulation_model_loaded": simulation_model is not None,
        "simulation_features": len(simulation_feature_names or []),
    }


def _telemetry_status() -> Dict[str, Any]:
    """Summarize backlog characteristics for telemetry log."""
    stats: Dict[str, Any] = {
        "log_path": str(TELEMETRY_LOG_PATH),
        "log_exists": TELEMETRY_LOG_PATH.exists(),
        "backlog_events": 0,
        "size_bytes": 0,
        "last_event_ts": None,
    }

    if not stats["log_exists"]:
        return stats

    try:
        stats["size_bytes"] = TELEMETRY_LOG_PATH.stat().st_size
    except OSError as exc:
        stats["size_bytes_error"] = str(exc)

    backlog = 0
    last_line = ""
    try:
        with TELEMETRY_LOG_PATH.open("r", encoding="utf-8") as handle:
            for backlog, line in enumerate(handle, start=1):
                if line.strip():
                    last_line = line
    except Exception as exc:
        stats["read_error"] = str(exc)
        return stats

    stats["backlog_events"] = backlog
    if last_line:
        try:
            record = json.loads(last_line)
            stats["last_event_ts"] = _safe_iso_timestamp(record.get("ts"))
        except Exception as exc:
            stats["last_event_error"] = str(exc)

    return stats


def _calibration_status() -> Dict[str, Any]:
    """Expose last calibration metadata + timestamp."""
    status: Dict[str, Any] = {
        "report_path": str(CALIBRATION_REPORT_PATH),
        "report_exists": CALIBRATION_REPORT_PATH.exists(),
        "last_report_ts": None,
        "samples": None,
        "ece": None,
        "brier": None,
        "bins": None,
    }

    if not status["report_exists"]:
        return status

    try:
        status["last_report_ts"] = _safe_iso_timestamp(CALIBRATION_REPORT_PATH.stat().st_mtime)
    except OSError as exc:
        status["last_report_error"] = str(exc)

    try:
        with CALIBRATION_REPORT_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        status.update({
            "samples": payload.get("samples"),
            "ece": payload.get("ece"),
            "brier": payload.get("brier"),
            "bins": payload.get("bins"),
        })
    except Exception as exc:
        status["parse_error"] = str(exc)

    return status


def _build_health_payload() -> Dict[str, Any]:
    """Combine subsystem snapshots for /health."""
    service_state = "online" if predictor is not None else "degraded"
    return {
        "status": service_state,
        "version": APP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "models": _model_status(),
        "telemetry": _telemetry_status(),
        "calibration": _calibration_status(),
        "simulation_summary": _load_simulation_summary(),
    }


# === Entry Point ===

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Draft Analyzer API...")
    print("=" * 60)
    print("Endpoints:")
    print("  GET  / - Basic status ping")
    print("  GET  /health - Health metrics")
    print("  POST /draft/recommend - Get champion recommendations")
    print("  POST /draft/analyze - Analyze team compositions")
    print("  GET  /champions/{name} - Get champion details")
    print("  GET  /archetypes - List all archetypes")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
