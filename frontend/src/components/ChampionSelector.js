import React, { useState } from 'react';
import './ChampionSelector.css';

const ChampionSelector = ({ champions, onSelect, currentAction }) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredChampions = champions.filter(champ =>
    champ.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  return (
    <div className="champion-selector">
      <div className="selector-header">
        <h3>
          {currentAction === 'pick' ? '⚔️ Select Champion' : '🚫 Select Ban'}
        </h3>
        <p className="selector-subtitle">
          {filteredChampions.length} available
        </p>
      </div>
      
      <input
        type="text"
        placeholder="Search champions..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="search-input"
      />
      
      <div className="champions-grid">
        {filteredChampions.map(champion => (
          <div
            key={champion}
            className={`champion-card ${currentAction}`}
            onClick={() => onSelect(champion)}
          >
            <div className="champion-name">{champion}</div>
          </div>
        ))}
      </div>
      
      {filteredChampions.length === 0 && (
        <div className="no-results">
          <p>No champions found</p>
          <p className="hint">Try a different search term</p>
        </div>
      )}
    </div>
  );
};

export default ChampionSelector;
