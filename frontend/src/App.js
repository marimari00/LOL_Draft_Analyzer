import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import DraftBoard from './components/DraftBoard';
import RecommendationPanel from './components/RecommendationPanel';
import AnalysisPanel from './components/AnalysisPanel';
import ChampionSelector from './components/ChampionSelector';

const API_BASE = 'http://localhost:8000';

function App() {
  // Draft state
  const [bluePicks, setBluePicks] = useState([]);
  const [redPicks, setRedPicks] = useState([]);
  const [blueBans, setBlueBans] = useState([]);
  const [redBans, setRedBans] = useState([]);
  const [currentTeam, setCurrentTeam] = useState('blue'); // 'blue' or 'red'
  const [currentAction, setCurrentAction] = useState('pick'); // 'pick' or 'ban'
  const [selectedRole, setSelectedRole] = useState(null);
  
  // Recommendations
  const [recommendations, setRecommendations] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Available champions
  const [champions, setChampions] = useState([]);
  
  // Load champions on mount
  useEffect(() => {
    loadChampions();
  }, []);
  
  // Get recommendations when draft changes
  useEffect(() => {
    if (bluePicks.length + redPicks.length > 0) {
      getRecommendations();
    }
  }, [bluePicks, redPicks, blueBans, redBans, selectedRole]);
  
  // Get analysis when both teams have 5 picks
  useEffect(() => {
    if (bluePicks.length === 5 && redPicks.length === 5) {
      getAnalysis();
    }
  }, [bluePicks, redPicks]);
  
  const loadChampions = async () => {
    try {
      // Load from local champion data
      const response = await fetch('/champion_archetypes.json');
      const data = await response.json();
      const championList = Object.keys(data.assignments).sort();
      setChampions(championList);
    } catch (error) {
      console.error('Error loading champions:', error);
      // Fallback to a few champions for testing
      setChampions([
        'Aatrox', 'Ahri', 'Akali', 'Alistar', 'Amumu', 'Anivia', 'Annie',
        'Ashe', 'Blitzcrank', 'Brand', 'Braum', 'Caitlyn', 'Cassiopeia',
        'Darius', 'Diana', 'Draven', 'Ekko', 'Ezreal', 'Fiora', 'Garen',
        'Gragas', 'Graves', 'Hecarim', 'Irelia', 'Janna', 'Jarvan IV',
        'Jax', 'Jayce', 'Jhin', 'Jinx', 'Karma', 'Katarina', 'Kayle',
        'LeBlanc', 'Lee Sin', 'Leona', 'Lissandra', 'Lucian', 'Lulu',
        'Lux', 'Malphite', 'Maokai', 'Master Yi', 'Miss Fortune', 'Morgana',
        'Nami', 'Nautilus', 'Nidalee', 'Orianna', 'Pantheon', 'Poppy',
        'Rakan', 'Rammus', 'Renekton', 'Riven', 'Rumble', 'Ryze',
        'Sejuani', 'Shen', 'Shyvana', 'Singed', 'Sona', 'Soraka',
        'Syndra', 'Tahm Kench', 'Talon', 'Thresh', 'Tristana', 'Trundle',
        'Twisted Fate', 'Twitch', 'Urgot', 'Varus', 'Vayne', 'Veigar',
        'Vi', 'Viktor', 'Vladimir', 'Volibear', 'Warwick', 'Wukong',
        'Xayah', 'Xerath', 'Xin Zhao', 'Yasuo', 'Yorick', 'Zac',
        'Zed', 'Ziggs', 'Zilean', 'Zoe', 'Zyra'
      ]);
    }
  };
  
  const getRecommendations = async () => {
    if (currentAction === 'ban') return; // No recommendations for bans
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/draft/recommend`, {
        draft_state: {
          blue_picks: bluePicks.map(p => p.champion),
          blue_bans: blueBans,
          red_picks: redPicks.map(p => p.champion),
          red_bans: redBans,
          next_pick: currentTeam
        },
        role: selectedRole,
        limit: 10
      });
      setRecommendations(response.data.recommendations);
    } catch (error) {
      console.error('Error getting recommendations:', error);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };
  
  const getAnalysis = async () => {
    try {
      const response = await axios.post(`${API_BASE}/draft/analyze`, {
        blue_team: bluePicks.map(p => p.champion),
        blue_roles: bluePicks.map(p => p.role),
        red_team: redPicks.map(p => p.champion),
        red_roles: redPicks.map(p => p.role)
      });
      setAnalysis(response.data);
    } catch (error) {
      console.error('Error getting analysis:', error);
      setAnalysis(null);
    }
  };
  
  const handleChampionPick = (champion) => {
    if (currentAction === 'pick') {
      const picks = currentTeam === 'blue' ? bluePicks : redPicks;
      if (picks.length >= 5) return;
      
      const newPick = {
        champion,
        role: selectedRole || getRoleForPosition(picks.length)
      };
      
      if (currentTeam === 'blue') {
        setBluePicks([...bluePicks, newPick]);
      } else {
        setRedPicks([...redPicks, newPick]);
      }
      
      // Auto-advance to next team
      advanceToNextPick();
    } else {
      // Ban
      const bans = currentTeam === 'blue' ? blueBans : redBans;
      if (bans.length >= 5) return;
      
      if (currentTeam === 'blue') {
        setBlueBans([...blueBans, champion]);
      } else {
        setRedBans([...redBans, champion]);
      }
      
      advanceToNextPick();
    }
  };
  
  const advanceToNextPick = () => {
    // Simple alternating pattern
    setCurrentTeam(currentTeam === 'blue' ? 'red' : 'blue');
  };
  
  const getRoleForPosition = (position) => {
    const roles = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'];
    return roles[position] || 'TOP';
  };
  
  const resetDraft = () => {
    setBluePicks([]);
    setRedPicks([]);
    setBlueBans([]);
    setRedBans([]);
    setCurrentTeam('blue');
    setCurrentAction('pick');
    setSelectedRole(null);
    setRecommendations([]);
    setAnalysis(null);
  };
  
  const getAvailableChampions = () => {
    const picked = [
      ...bluePicks.map(p => p.champion),
      ...redPicks.map(p => p.champion)
    ];
    const banned = [...blueBans, ...redBans];
    return champions.filter(c => !picked.includes(c) && !banned.includes(c));
  };
  
  return (
    <div className="App">
      <header className="App-header">
        <h1>⚔️ LoL Draft Analyzer</h1>
        <p className="subtitle">Archetypal Composition Analysis</p>
      </header>
      
      <div className="controls">
        <div className="control-group">
          <label>Current Action:</label>
          <button 
            className={currentAction === 'pick' ? 'active' : ''}
            onClick={() => setCurrentAction('pick')}
          >
            Pick
          </button>
          <button 
            className={currentAction === 'ban' ? 'active' : ''}
            onClick={() => setCurrentAction('ban')}
          >
            Ban
          </button>
        </div>
        
        <div className="control-group">
          <label>Current Team:</label>
          <button 
            className={currentTeam === 'blue' ? 'active blue' : 'blue'}
            onClick={() => setCurrentTeam('blue')}
          >
            Blue Side
          </button>
          <button 
            className={currentTeam === 'red' ? 'active red' : 'red'}
            onClick={() => setCurrentTeam('red')}
          >
            Red Side
          </button>
        </div>
        
        <div className="control-group">
          <label>Role Filter:</label>
          {['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'].map(role => (
            <button
              key={role}
              className={selectedRole === role ? 'active role' : 'role'}
              onClick={() => setSelectedRole(selectedRole === role ? null : role)}
            >
              {role}
            </button>
          ))}
        </div>
        
        <button className="reset-button" onClick={resetDraft}>
          🔄 Reset Draft
        </button>
      </div>
      
      <div className="main-content">
        <div className="left-panel">
          <DraftBoard
            bluePicks={bluePicks}
            redPicks={redPicks}
            blueBans={blueBans}
            redBans={redBans}
            currentTeam={currentTeam}
          />
          
          {analysis && (
            <AnalysisPanel analysis={analysis} />
          )}
        </div>
        
        <div className="right-panel">
          <RecommendationPanel
            recommendations={recommendations}
            loading={loading}
            currentAction={currentAction}
            onSelect={handleChampionPick}
          />
          
          <ChampionSelector
            champions={getAvailableChampions()}
            onSelect={handleChampionPick}
            currentAction={currentAction}
          />
        </div>
      </div>
      
      <footer className="App-footer">
        <p>Theory over meta • Archetypes over win rates</p>
      </footer>
    </div>
  );
}

export default App;
