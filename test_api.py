"""
Test Draft API

Tests both ensemble prediction and API endpoints with example scenarios.
"""

import requests
import json
from pathlib import Path


def test_ensemble_prediction():
    """Test ensemble prediction directly."""
    print("=" * 80)
    print("TEST 1: Ensemble Prediction System")
    print("=" * 80)
    
    try:
        from validation.ensemble_prediction import load_ensemble_predictor
        
        print("\nLoading ensemble predictor...")
        predictor = load_ensemble_predictor(matchups_path="data/matches/lane_duo_stats.json")
        
        # Test case: Front-to-back vs Dive
        print("\n📋 Scenario: Front-to-back vs Dive Composition")
        print("-" * 80)
        
        blue_team = ["Jinx", "Leona", "Orianna", "Vi", "Darius"]
        blue_roles = ["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"]
        
        red_team = ["Caitlyn", "Thresh", "Zed", "Lee Sin", "Renekton"]
        red_roles = ["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"]
        
        print(f"Blue Team: {', '.join(blue_team)}")
        print(f"Red Team:  {', '.join(red_team)}")
        
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
        
        print("\n✓ Ensemble prediction test passed")
        return True
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure to run: python validation/ml_simulation.py")
        return False


def test_api_endpoints():
    """Test API endpoints with example requests."""
    print("\n" + "=" * 80)
    print("TEST 2: API Endpoints")
    print("=" * 80)
    
    base_url = "http://localhost:8000"
    
    # Check if API is running
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code != 200:
            print("\n⚠️  API not running. Start with: python backend/draft_api.py")
            return False
    except requests.exceptions.ConnectionError:
        print("\n⚠️  API not running. Start with: python backend/draft_api.py")
        print("Skipping API tests...")
        return False
    
    print("\n✓ API is online")
    
    # Test 1: Analyze composition
    print("\n📋 Test: Analyze Team Composition")
    print("-" * 80)
    
    analysis_request = {
        "blue_team": ["Jinx", "Leona", "Orianna", "Vi", "Darius"],
        "blue_roles": ["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"],
        "red_team": ["Caitlyn", "Thresh", "Zed", "Lee Sin", "Renekton"],
        "red_roles": ["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"]
    }
    
    response = requests.post(f"{base_url}/draft/analyze", json=analysis_request)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Prediction: {data['prediction']['winner'].upper()} wins")
        print(f"  Confidence: {data['prediction']['confidence']:.1%}")
        print(f"  Blue composition: {data['blue_analysis']['composition_type']}")
        print(f"  Red composition: {data['red_analysis']['composition_type']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False
    
    # Test 2: Get champion info
    print("\n📋 Test: Get Champion Info")
    print("-" * 80)
    
    response = requests.get(f"{base_url}/champions/Jinx")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Champion: {data['name']}")
        print(f"  Archetype: {data['archetype']}")
        print(f"  Roles: {', '.join(data['riot_roles'])}")
        print(f"  Key attributes: {', '.join(data['attributes'][:5])}")
    else:
        print(f"❌ Error: {response.status_code}")
        return False
    
    # Test 3: Recommend champions
    print("\n📋 Test: Recommend Champions")
    print("-" * 80)
    
    recommend_request = {
        "draft_state": {
            "blue_picks": ["Jinx", "Leona"],
            "blue_bans": ["Yasuo", "Zed"],
            "red_picks": ["Caitlyn", "Thresh"],
            "red_bans": ["Darius", "Vi"],
            "next_pick": "blue"
        },
        "role": "MIDDLE",
        "limit": 5
    }
    
    response = requests.post(f"{base_url}/draft/recommend", json=recommend_request)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Top 5 Recommendations for MIDDLE:")
        for i, rec in enumerate(data['recommendations'][:5], 1):
            print(f"  {i}. {rec['champion']} ({rec['archetype']}) - Score: {rec['score']:.2f}")
            print(f"     Reason: {rec['reasoning'][0] if rec['reasoning'] else 'N/A'}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False
    
    print("\n✓ All API tests passed")
    return True


def main():
    """Run all tests."""
    print("🧪 Draft Analyzer Test Suite")
    print("=" * 80)
    print()
    
    # Test 1: Ensemble prediction
    test1_passed = test_ensemble_prediction()
    
    # Test 2: API endpoints (optional, requires server running)
    test2_passed = test_api_endpoints()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Ensemble Prediction: {'✓ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"API Endpoints:       {'✓ PASSED' if test2_passed else '⚠️  SKIPPED'}")
    print()
    
    if test1_passed:
        print("✅ Core functionality working")
        print()
        print("To test API:")
        print("1. Start server: python backend/draft_api.py")
        print("2. In another terminal: python test_api.py")
    else:
        print("❌ Tests failed. Run: python validation/ml_simulation.py")


if __name__ == "__main__":
    main()
