import React from 'react';
import './TeamSummary.css';

const formatPercent = (value) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '—';
  }
  return `${(value * 100).toFixed(1)}%`;
};

const TeamSummary = ({
  label,
  team = 'blue',
  picks = 0,
  bans = 0,
  identity = 'Flexible',
  winRate = null,
  confidence = null,
  favored = null
}) => {
  const teamClasses = ['team-summary-card', team];
  return (
    <div className={teamClasses.join(' ')}>
      <div className="team-summary-header">
        <span className="team-summary-label">{label}</span>
        <span className="team-summary-winrate">{formatPercent(winRate)}</span>
      </div>
      <div className="team-summary-identity">{identity}</div>
      <div className="team-summary-meta">
        <span>{picks}/5 picks locked</span>
        <span>{bans}/5 bans used</span>
      </div>
      <div className="team-summary-footer">
        {favored && favored === team && (
          <span className="favored-chip">Favored</span>
        )}
        {typeof confidence === 'number' && (
          <span className="confidence-chip">{(confidence * 100).toFixed(0)}% confidence</span>
        )}
      </div>
    </div>
  );
};

export default TeamSummary;
