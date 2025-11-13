"""Match data fetcher for empirical synergy analysis.

Fetches REAL match data from Riot API (Diamond+ ranked games EUW/KR).
NO SAMPLE DATA - only actual game results.
"""

import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class MatchDataFetcher:
    """Fetches match data from Riot API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize fetcher with Riot API key."""
        self.api_key = api_key or "RGAPI-95df791c-5ac9-4230-ba2f-de7bf0aefe7c"
        self.regions = {
            'euw1': 'https://euw1.api.riotgames.com',
            'kr': 'https://kr.api.riotgames.com'
        }
        self.routing_regions = {
            'euw1': 'https://europe.api.riotgames.com',
            'kr': 'https://asia.api.riotgames.com'
        }
        self.rate_limit_delay = 1.2
        
    def _make_request(self, url: str) -> Optional[Dict]:
        """Make API request with rate limiting."""
        headers = {'X-Riot-Token': self.api_key}
        
        try:
            response = requests.get(url, headers=headers)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 120))
                print(f"⚠ Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                return self._make_request(url)
            else:
                print(f"✗ API error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"✗ Request failed: {e}")
            return None
    
    def get_high_elo_players(self, region: str = 'euw1', tiers: List[str] = ['challenger', 'grandmaster', 'master']) -> List[str]:
        """Get list of high elo player PUUIDs from multiple tiers.
        
        Args:
            region: Region code (euw1, kr)
            tiers: List of tiers to fetch from (challenger, grandmaster, master)
            
        Returns:
            List of PUUIDs
        """
        base_url = self.regions[region]
        puuids = []
        
        for tier in tiers:
            print(f"  Fetching {tier} players from {region.upper()}...")
            
            if tier in ['challenger', 'grandmaster']:
                # Challenger and Grandmaster use special endpoints
                url = f"{base_url}/lol/league/v4/{tier}leagues/by-queue/RANKED_SOLO_5x5"
                data = self._make_request(url)
                
                if data:
                    entries = data.get('entries', [])
                    for entry in entries:
                        if 'puuid' in entry:
                            puuids.append(entry['puuid'])
                    print(f"    ✓ Found {len(entries)} {tier} players")
            
            elif tier == 'master':
                # Master uses division endpoint
                url = f"{base_url}/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5"
                data = self._make_request(url)
                
                if data:
                    entries = data.get('entries', [])
                    for entry in entries:
                        if 'puuid' in entry:
                            puuids.append(entry['puuid'])
                    print(f"    ✓ Found {len(entries)} master players")
            
            elif tier == 'diamond':
                # Diamond uses entries endpoint with division
                for division in ['I', 'II', 'III', 'IV']:
                    url = f"{base_url}/lol/league/v4/entries/RANKED_SOLO_5x5/DIAMOND/{division}?page=1"
                    data = self._make_request(url)
                    
                    if data:
                        for entry in data[:50]:  # Limit to 50 per division to avoid too many
                            if 'puuid' in entry:
                                puuids.append(entry['puuid'])
                        print(f"    ✓ Found {len(data[:50])} Diamond {division} players")
        
        return list(set(puuids))  # Remove duplicates
    
    def get_match_ids_for_puuid(self, puuid: str, region: str = 'euw1', count: int = 20) -> List[str]:
        """Get recent match IDs for a player."""
        routing_url = self.routing_regions[region]
        url = f"{routing_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}&queue=420"
        
        data = self._make_request(url)
        return data if data else []
    
    def get_match_details(self, match_id: str, region: str = 'euw1') -> Optional[Dict]:
        """Get detailed match information."""
        routing_url = self.routing_regions[region]
        url = f"{routing_url}/lol/match/v5/matches/{match_id}"
        
        return self._make_request(url)
    
    def fetch_high_elo_matches(self, regions: List[str] = ['euw1', 'kr'], 
                              tiers: List[str] = ['challenger', 'grandmaster', 'master', 'diamond'],
                              count: int = 1000) -> List[Dict]:
        """Fetch high elo ranked matches from multiple regions and tiers.
        
        Args:
            regions: List of region codes (euw1, kr)
            tiers: List of tiers to fetch from (challenger, grandmaster, master, diamond)
            count: Target number of matches to fetch
            
        Returns:
            List of match data dictionaries
        """
        if not self.api_key or not self.api_key.startswith('RGAPI-'):
            print("✗ No valid Riot API key provided")
            return []
        
        print(f"\nFetching {count} matches from {', '.join([r.upper() for r in regions])}...")
        print(f"Tiers: {', '.join(tiers)}")
        
        all_match_ids = set()
        matches_per_region = count // len(regions)
        
        for region in regions:
            print(f"\n{'='*60}")
            print(f"REGION: {region.upper()}")
            print(f"{'='*60}")
            
            print("Step 1: Getting high elo players...")
            
            # Get high elo players from multiple tiers
            puuids = self.get_high_elo_players(region, tiers)
            if not puuids:
                print(f"✗ Failed to get players from {region}")
                continue
            
            print(f"✓ Found {len(puuids)} total players across all tiers")
            
            # Collect unique match IDs
            region_match_ids = set()
            print("\nStep 2: Collecting match IDs...")
            
            # Query more players to get enough unique matches
            players_to_query = min(len(puuids), 100)  # Query up to 100 players
            
            for i, puuid in enumerate(puuids[:players_to_query], 1):
                match_ids = self.get_match_ids_for_puuid(puuid, region, count=20)
                region_match_ids.update(match_ids)
                
                if i % 10 == 0 or i == players_to_query:
                    print(f"  Player {i}/{players_to_query}: {len(region_match_ids)} unique matches")
                
                if len(region_match_ids) >= matches_per_region:
                    break
            
            all_match_ids.update(list(region_match_ids)[:matches_per_region])
            print(f"✓ Collected {len(region_match_ids)} unique match IDs from {region.upper()}")
        
        # Fetch match details
        total_unique = len(all_match_ids)
        target_matches = min(count, total_unique)
        
        print(f"\n{'='*60}")
        print(f"Step 3: Fetching match details for {target_matches} matches...")
        print(f"{'='*60}")
        
        matches = []
        
        for i, match_id in enumerate(list(all_match_ids)[:count], 1):
            # Determine region from match ID (EUW1_xxx or KR_xxx)
            match_region = 'kr' if match_id.startswith('KR_') else 'euw1'
            
            match_data = self.get_match_details(match_id, match_region)
            if match_data:
                parsed = self._parse_match_data(match_data)
                if parsed:
                    matches.append(parsed)
                    print(f"  ✓ Match {i}/{count}: {match_id}")
            
            if i % 10 == 0:
                print(f"    Progress: {i}/{count} matches fetched")
        
        return matches
    
    def _parse_match_data(self, match_data: Dict) -> Optional[Dict]:
        """Parse Riot API match data into our format."""
        try:
            info = match_data.get('info', {})
            participants = info.get('participants', [])
            
            # Extract teams
            blue_team = {}
            red_team = {}
            winner = None
            
            for p in participants:
                champ = p.get('championName')
                team_id = p.get('teamId')
                position = p.get('teamPosition')  # TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY
                win = p.get('win')
                
                # Normalize position names
                position_map = {
                    'TOP': 'Top',
                    'JUNGLE': 'Jungle',
                    'MIDDLE': 'Middle',
                    'BOTTOM': 'Bottom',
                    'UTILITY': 'Support'
                }
                position = position_map.get(position, position)
                
                if team_id == 100:  # Blue team
                    blue_team[position] = champ
                    if win:
                        winner = 'blue'
                elif team_id == 200:  # Red team
                    red_team[position] = champ
                    if win:
                        winner = 'red'
            
            return {
                'match_id': match_data.get('metadata', {}).get('matchId'),
                'blue_team': blue_team,
                'red_team': red_team,
                'winner': winner,
                'date': datetime.fromtimestamp(info.get('gameCreation', 0) / 1000).isoformat(),
                'patch': info.get('gameVersion', '').split('.')[0:2],
                'duration': info.get('gameDuration', 0),
                'queue_id': info.get('queueId')
            }
        except Exception as e:
            print(f"✗ Failed to parse match: {e}")
            return None
    
    def fetch_pro_matches(self, tournament: str, year: int) -> List[Dict]:
        """Fetch professional match data.
        
        Args:
            tournament: Tournament name (e.g., "worlds", "msi", "lcs")
            year: Year of tournament
            
        Returns:
            List of match data dictionaries
        """
        # This would fetch from Oracle's Elixir or similar source
        print(f"\nTo fetch {tournament} {year} professional matches:")
        print("1. Use Oracle's Elixir API or similar")
        print("2. Download match history CSV")
        print("3. Parse with load_match_data_from_csv()")
        
        return []


def load_match_data_from_csv(csv_path: str) -> List[Dict]:
    """Load match data from CSV file (e.g., Oracle's Elixir export).
    
    Args:
        csv_path: Path to CSV file with match data
        
    Returns:
        List of parsed match dictionaries
    """
    import csv
    
    matches = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse match data
            # Expected columns: gameid, side, position, champion, result, ...
            match = {
                'match_id': row.get('gameid'),
                'side': row.get('side'),  # Blue or Red
                'position': row.get('position'),  # Top, Jungle, Mid, Bot, Support
                'champion': row.get('champion'),
                'win': row.get('result') == '1' or row.get('result') == 'Win',
                'date': row.get('date'),
                'patch': row.get('patch'),
                'league': row.get('league', 'Unknown')
            }
            matches.append(match)
    
    return matches


def parse_match_to_team_comp(match_data: List[Dict]) -> Dict:
    """Parse raw match data into team composition format.
    
    Args:
        match_data: List of player data for one match
        
    Returns:
        Dict with blue_team, red_team, winner
    """
    blue_team = {}
    red_team = {}
    winner = None
    
    for player in match_data:
        side = player.get('side', '').lower()
        position = player.get('position')
        champion = player.get('champion')
        win = player.get('win')
        
        if side == 'blue':
            blue_team[position] = champion
            if win:
                winner = 'blue'
        elif side == 'red':
            red_team[position] = champion
            if win:
                winner = 'red'
    
    return {
        'blue_team': blue_team,
        'red_team': red_team,
        'winner': winner,
        'match_id': match_data[0].get('match_id') if match_data else None,
        'date': match_data[0].get('date') if match_data else None,
        'patch': match_data[0].get('patch') if match_data else None,
        'league': match_data[0].get('league') if match_data else None
    }





def save_match_data(matches: List[Dict], output_path: str):
    """Save match data to JSON file."""
    output = {
        'metadata': {
            'total_matches': len(matches),
            'created': datetime.now().isoformat(),
            'source': 'Generated sample data'
        },
        'matches': matches
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Saved {len(matches)} matches to: {output_path}")


if __name__ == '__main__':
    import sys
    
    print("="*70)
    print("RIOT API MATCH DATA FETCHER - MULTI-REGION DIAMOND+ GAMES")
    print("="*70)
    
    fetcher = MatchDataFetcher()
    
    if not fetcher.api_key or not fetcher.api_key.startswith('RGAPI-'):
        print("\n✗ No valid Riot API key found")
        print("  Get one from: https://developer.riotgames.com/")
        sys.exit(1)
    
    print(f"\n✓ Riot API key loaded: {fetcher.api_key[:20]}...")
    
    # Parse arguments
    regions = ['euw1', 'kr']
    tiers = ['challenger', 'grandmaster', 'master', 'diamond']
    count = 1000
    
    if '--regions' in sys.argv:
        idx = sys.argv.index('--regions')
        if idx + 1 < len(sys.argv):
            regions = sys.argv[idx + 1].split(',')
    
    if '--tiers' in sys.argv:
        idx = sys.argv.index('--tiers')
        if idx + 1 < len(sys.argv):
            tiers = sys.argv[idx + 1].split(',')
    
    if '--count' in sys.argv:
        idx = sys.argv.index('--count')
        if idx + 1 < len(sys.argv):
            count = int(sys.argv[idx + 1])
    
    # Fetch matches
    matches = fetcher.fetch_high_elo_matches(regions=regions, tiers=tiers, count=count)
    
    if matches:
        # Save to combined file
        output_path = f"data/matches/multi_region_{count}_matches.json"
        output = {
            'metadata': {
                'total_matches': len(matches),
                'created': datetime.now().isoformat(),
                'source': f'Riot API - {", ".join([r.upper() for r in regions])}',
                'tiers': tiers,
                'regions': regions
            },
            'matches': matches
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Saved {len(matches)} matches to: {output_path}")
        print(f"✓ Successfully fetched {len(matches)} matches from {', '.join([r.upper() for r in regions])}")
    else:
        print("\n✗ No matches fetched")
    
    if '--count' in sys.argv:
        idx = sys.argv.index('--count')
        if idx + 1 < len(sys.argv):
            count = int(sys.argv[idx + 1])
    
    # Fetch matches
    matches = fetcher.fetch_high_elo_matches(regions=regions, tiers=tiers, count=count)
    
    if matches:
        # Save to combined file
        output_path = f"data/matches/multi_region_{count}_matches.json"
        output = {
            'metadata': {
                'total_matches': len(matches),
                'created': datetime.now().isoformat(),
                'source': f'Riot API - {", ".join([r.upper() for r in regions])}',
                'tiers': tiers,
                'regions': regions
            },
            'matches': matches
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Saved {len(matches)} matches to: {output_path}")
        print(f"✓ Successfully fetched {len(matches)} matches from {', '.join([r.upper() for r in regions])}")
        
        print("\nFirst 3 matches:")
        for i, match in enumerate(matches[:3], 1):
            print(f"\nMatch {i} (ID: {match['match_id']}):")
            print(f"  Blue: {', '.join([f'{p}={c}' for p, c in match['blue_team'].items()])}")
            print(f"  Red:  {', '.join([f'{p}={c}' for p, c in match['red_team'].items()])}")
            print(f"  Winner: {match['winner']}")
            print(f"  Duration: {match.get('duration', 'N/A')}s")
    else:
        print("\n✗ No matches fetched. Check API key and rate limits.")
