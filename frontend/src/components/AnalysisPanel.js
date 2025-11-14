import React from 'react';
import './AnalysisPanel.css';

const AnalysisPanel = ({ analysis }) => {
  if (!analysis) return null;
  
  const { prediction, blue_analysis, red_analysis, archetypal_insights } = analysis;
  
  return (
    <div className="analysis-panel">
      <h3>📊 Composition Analysis</h3>
      
      <div className="prediction-section">
        <div className="prediction-header">
          <div className="winner-badge">
            {prediction.winner === 'blue' ? '🔵' : '🔴'} 
            <span className="winner-text">
              {prediction.winner.toUpperCase()} TEAM FAVORED
            </span>
          </div>
          <div className="confidence-badge">
            Confidence: {(prediction.confidence * 100).toFixed(1)}%
          </div>
        </div>
        
        <div className="probability-bars">
          <div className="prob-bar blue">
            <div className="prob-label">Blue Team</div>
            <div className="bar-container">
              <div 
                className="bar-fill blue-fill" 
                style={{ width: `${prediction.blue_win_probability * 100}%` }}
              >
                <span className="bar-text">
                  {(prediction.blue_win_probability * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
          
          <div className="prob-bar red">
            <div className="prob-label">Red Team</div>
            <div className="bar-container">
              <div 
                className="bar-fill red-fill" 
                style={{ width: `${prediction.red_win_probability * 100}%` }}
              >
                <span className="bar-text">
                  {(prediction.red_win_probability * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="model-breakdown">
          <h4>Model Consensus</h4>
          <div className="models">
            {Object.entries(prediction.model_breakdown).map(([model, prob]) => (
              <div key={model} className="model-item">
                <span className="model-name">{model.toUpperCase()}</span>
                <span className="model-prob">{(prob * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      <div className="insights-section">
        <h4>💡 Archetypal Insights</h4>
        <div className="insights-list">
          {archetypal_insights.map((insight, i) => (
            <div key={i} className="insight-item">
              <span className="insight-bullet">→</span>
              {insight}
            </div>
          ))}
        </div>
      </div>
      
      <div className="composition-details">
        <div className="comp-column">
          <h4 className="blue-header">🔵 Blue Composition</h4>
          <div className="comp-type">{blue_analysis.composition_type}</div>
          <div className="archetype-tags">
            {blue_analysis.archetypes.map((arch, i) => (
              <span key={i} className="archetype-tag">{arch}</span>
            ))}
          </div>
        </div>
        
        <div className="comp-column">
          <h4 className="red-header">🔴 Red Composition</h4>
          <div className="comp-type">{red_analysis.composition_type}</div>
          <div className="archetype-tags">
            {red_analysis.archetypes.map((arch, i) => (
              <span key={i} className="archetype-tag">{arch}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisPanel;
