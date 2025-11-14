import React from 'react';
import './RecommendationPanel.css';

const RecommendationPanel = ({ recommendations, loading, currentAction, onSelect }) => {
  if (currentAction === 'ban') {
    return (
      <div className="recommendation-panel">
        <h3>💡 Recommendations</h3>
        <div className="no-recommendations">
          <p>No recommendations for bans.</p>
          <p className="hint">Select champions manually for strategic bans.</p>
        </div>
      </div>
    );
  }
  
  if (loading) {
    return (
      <div className="recommendation-panel">
        <h3>💡 Recommendations</h3>
        <div className="loading">
          <div className="spinner"></div>
          <p>Analyzing composition...</p>
        </div>
      </div>
    );
  }
  
  if (recommendations.length === 0) {
    return (
      <div className="recommendation-panel">
        <h3>💡 Recommendations</h3>
        <div className="no-recommendations">
          <p>Start picking champions to see recommendations!</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="recommendation-panel">
      <h3>💡 Top Recommendations</h3>
      <p className="panel-subtitle">Archetypal composition analysis</p>
      
      <div className="recommendations-list">
        {recommendations.slice(0, 5).map((rec, index) => (
          <div 
            key={index} 
            className="recommendation-card"
            onClick={() => onSelect(rec.champion)}
          >
            <div className="rec-header">
              <div className="rec-rank">#{index + 1}</div>
              <div className="rec-info">
                <div className="rec-champion">{rec.champion}</div>
                <div className="rec-archetype">{rec.archetype}</div>
              </div>
              <div className="rec-score">
                <div className="score-bar">
                  <div 
                    className="score-fill" 
                    style={{ width: `${rec.score * 100}%` }}
                  ></div>
                </div>
                <div className="score-text">{(rec.score * 100).toFixed(0)}%</div>
              </div>
            </div>
            
            <div className="rec-reasoning">
              {rec.reasoning.slice(0, 2).map((reason, i) => (
                <div key={i} className="reason-item">
                  <span className="reason-bullet">→</span>
                  {reason}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecommendationPanel;
