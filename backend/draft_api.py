"""
Draft Recommendation API

FastAPI server providing archetypal draft analysis endpoints.

Philosophy: Theoretical composition analysis, not data-driven meta chasing.
Focuses on archetype synergies, compositional balance, and strategic reasoning.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from pathlib import Path
import json
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from validation.ensemble_prediction import load_ensemble_predictor, PredictionResult


app = FastAPI(
    title="League of Legends Draft Analyzer",
    description="Archetypal composition analysis using theoretical frameworks",
    version="1.0.0"
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


# === Request/Response Models ===

class DraftState(BaseModel):
    """Current state of champion draft."""
    blue_picks: List[str] = Field(default_factory=list, max_items=5)
    blue_bans: List[str] = Field(default_factory=list, max_items=5)
    red_picks: List[str] = Field(default_factory=list, max_items=5)
    red_bans: List[str] = Field(default_factory=list, max_items=5)
    next_pick: str = Field(..., pattern="^(blue|red)$")


class RecommendationRequest(BaseModel):
    """Request for champion recommendations."""
    draft_state: DraftState
    role: Optional[str] = Field(None, pattern="^(TOP|JUNGLE|MIDDLE|BOTTOM|UTILITY)$")
    limit: int = Field(5, ge=1, le=20)


class ChampionRecommendation(BaseModel):
    """Individual champion recommendation."""
    champion: str
    score: float
    archetype: str
    reasoning: List[str]


class RecommendationResponse(BaseModel):
    """Response with champion recommendations."""
    recommendations: List[ChampionRecommendation]
    draft_analysis: Dict[str, any]


class AnalysisRequest(BaseModel):
    """Request for team composition analysis."""
    blue_team: List[str] = Field(..., min_items=5, max_items=5)
    blue_roles: List[str] = Field(..., min_items=5, max_items=5)
    red_team: List[str] = Field(..., min_items=5, max_items=5)
    red_roles: List[str] = Field(..., min_items=5, max_items=5)


class AnalysisResponse(BaseModel):
    """Response with composition analysis."""
    prediction: Dict[str, any]
    blue_analysis: Dict[str, any]
    red_analysis: Dict[str, any]
    archetypal_insights: List[str]


# === Startup/Shutdown ===

@app.on_event("startup")
async def startup_event():
    """Load models and data on startup."""
    global predictor, champion_data, attribute_data
    
    try:
        print("Loading ensemble predictor...")
        predictor = load_ensemble_predictor()
        
        print("Loading champion data...")
        with open("data/processed/champion_archetypes.json", "r", encoding="utf-8") as f:
            champion_data = json.load(f)
        
        with open("data/processed/archetype_attributes.json", "r", encoding="utf-8") as f:
            attribute_data = json.load(f)
        
        print("✓ API ready")
    
    except Exception as e:
        print(f"⚠️  Error loading data: {e}")
        print("Run ml_simulation.py first to train models")


# === Endpoints ===

@app.get("/")
async def root():
    """API health check."""
    return {
        "status": "online",
        "version": "1.0.0",
        "philosophy": "Archetypal draft analysis - theory over meta"
    }


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
    
    # Determine which team we're picking for
    our_team = draft.blue_picks if draft.next_pick == "blue" else draft.red_picks
    enemy_team = draft.red_picks if draft.next_pick == "blue" else draft.blue_picks
    
    # Score each available champion
    recommendations = []
    
    for champion in available:
        # Skip if role filter provided and champion doesn't play that role
        if request.role:
            champ_info = champion_data["assignments"][champion]
            positions = champ_info.get("positions", {})
            if request.role not in positions:
                continue
        
        # Calculate score based on:
        # 1. Synergy with our team
        # 2. Counter advantage vs enemy team
        # 3. Fills missing archetypes
        
        score, reasoning = _score_champion_for_draft(
            champion, our_team, enemy_team, request.role
        )
        
        champ_info = champion_data["assignments"][champion]
        
        recommendations.append(ChampionRecommendation(
            champion=champion,
            score=score,
            archetype=champ_info["primary_archetype"],
            reasoning=reasoning
        ))
    
    # Sort by score and take top N
    recommendations.sort(key=lambda x: x.score, reverse=True)
    top_recommendations = recommendations[:request.limit]
    
    # Analyze current draft state
    draft_analysis = _analyze_draft_state(our_team, enemy_team)
    
    return RecommendationResponse(
        recommendations=top_recommendations,
        draft_analysis=draft_analysis
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
    
    # Get prediction
    result: PredictionResult = predictor.predict(
        request.blue_team,
        request.blue_roles,
        request.red_team,
        request.red_roles
    )
    
    # Analyze each team
    blue_analysis = _analyze_team_composition(request.blue_team, request.blue_roles)
    red_analysis = _analyze_team_composition(request.red_team, request.red_roles)
    
    return AnalysisResponse(
        prediction={
            "winner": result.winner,
            "confidence": result.confidence,
            "blue_win_probability": result.blue_win_probability,
            "red_win_probability": result.red_win_probability,
            "model_breakdown": result.model_breakdown
        },
        blue_analysis=blue_analysis,
        red_analysis=red_analysis,
        archetypal_insights=result.reasoning
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
        "attributes": champ_info.get("archetype_attributes", []),
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

def _score_champion_for_draft(
    champion: str,
    our_team: List[str],
    enemy_team: List[str],
    role: Optional[str]
) -> tuple[float, List[str]]:
    """
    Score a champion for current draft.
    
    Returns (score, reasoning)
    """
    score = 0.5  # Base score
    reasoning = []
    
    champ_info = champion_data["assignments"][champion]
    champ_archetype = champ_info["primary_archetype"]
    champ_attributes = set(champ_info.get("archetype_attributes", []))
    
    # Get team archetypes
    our_archetypes = [
        champion_data["assignments"][c]["primary_archetype"]
        for c in our_team if c in champion_data["assignments"]
    ]
    
    enemy_archetypes = [
        champion_data["assignments"][c]["primary_archetype"]
        for c in enemy_team if c in champion_data["assignments"]
    ]
    
    # 1. Check if fills missing archetype need
    archetype_counts = {
        "damage": sum(1 for a in our_archetypes if "mage" in a or "assassin" in a or "marksman" in a),
        "tank": sum(1 for a in our_archetypes if "tank" in a or "warden" in a),
        "fighter": sum(1 for a in our_archetypes if "diver" in a or "skirmisher" in a or "juggernaut" in a),
        "support": sum(1 for a in our_archetypes if "enchanter" in a or "catcher" in a)
    }
    
    # Reward filling gaps
    if archetype_counts["damage"] == 0 and ("mage" in champ_archetype or "marksman" in champ_archetype):
        score += 0.15
        reasoning.append("Fills critical damage dealer gap")
    
    if archetype_counts["tank"] == 0 and ("tank" in champ_archetype or "warden" in champ_archetype):
        score += 0.15
        reasoning.append("Provides missing frontline presence")
    
    # 2. Check attribute synergies with team
    team_attributes = set()
    for champ in our_team:
        if champ in champion_data["assignments"]:
            team_attributes.update(champion_data["assignments"][champ].get("archetype_attributes", []))
    
    # Key synergies
    if "engage" in champ_attributes and "damage_burst" in team_attributes:
        score += 0.10
        reasoning.append("Engage synergizes with team's burst damage")
    
    if "range_long" in champ_attributes and "engage" in team_attributes:
        score += 0.08
        reasoning.append("Poke/range complements team's engage")
    
    if "enchanter" in champ_archetype and "marksman" in " ".join(our_archetypes):
        score += 0.12
        reasoning.append("Enchanter synergizes with marksman")
    
    # 3. Counter enemy threats
    enemy_attributes = set()
    for champ in enemy_team:
        if champ in champion_data["assignments"]:
            enemy_attributes.update(champion_data["assignments"][champ].get("archetype_attributes", []))
    
    if "assassin" in " ".join(enemy_archetypes) and "warden" in champ_archetype:
        score += 0.15
        reasoning.append("Counters enemy assassin threat")
    
    if "mobility_high" in enemy_attributes and "cc_hard" in champ_attributes:
        score += 0.10
        reasoning.append("Hard CC counters enemy mobility")
    
    if "range_long" in enemy_attributes and "engage" in champ_attributes:
        score += 0.08
        reasoning.append("Engage counters enemy poke")
    
    # 4. Role appropriateness bonus
    if role:
        positions = champ_info.get("positions", {})
        if role in positions:
            role_rating = positions[role]
            if role_rating == "primary":
                score += 0.05
                reasoning.append(f"Optimal for {role} role")
            elif role_rating == "viable":
                reasoning.append(f"Can play {role} role")
    
    # Ensure score stays in [0, 1]
    score = max(0.0, min(1.0, score))
    
    if not reasoning:
        reasoning.append("Solid pick for composition")
    
    return score, reasoning


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
        
        champ_attrs = champ_info.get("archetype_attributes", [])
        
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


# === Entry Point ===

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Draft Analyzer API...")
    print("=" * 60)
    print("Endpoints:")
    print("  POST /draft/recommend - Get champion recommendations")
    print("  POST /draft/analyze - Analyze team compositions")
    print("  GET  /champions/{name} - Get champion details")
    print("  GET  /archetypes - List all archetypes")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
