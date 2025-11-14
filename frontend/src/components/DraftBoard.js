import React from 'react';
import './DraftBoard.css';

const DraftBoard = ({ bluePicks, redPicks, blueBans, redBans, currentTeam }) => {
  const roles = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'];
  
  const getPickForRole = (picks, role) => {
    return picks.find(p => p.role === role);
  };
  
  return (
    <div className="draft-board">
      <div className="draft-title">
        <h2>Draft Board</h2>
        <div className="draft-status">
          <span className={`team-indicator ${currentTeam}`}>
            {currentTeam === 'blue' ? '🔵' : '🔴'} {currentTeam.toUpperCase()} SIDE'S TURN
          </span>
        </div>
      </div>
      
      <div className="teams-container">
        {/* Blue Team */}
        <div className="team blue-team">
          <h3 className="team-header">🔵 Blue Team</h3>
          
          <div className="picks">
            {roles.map(role => {
              const pick = getPickForRole(bluePicks, role);
              return (
                <div key={role} className={`pick-slot ${pick ? 'filled' : 'empty'}`}>
                  <div className="role-label">{role}</div>
                  {pick ? (
                    <div className="champion-info">
                      <div className="champion-name">{pick.champion}</div>
                    </div>
                  ) : (
                    <div className="empty-slot">?</div>
                  )}
                </div>
              );
            })}
          </div>
          
          <div className="bans">
            <h4>Bans</h4>
            <div className="ban-list">
              {[0, 1, 2, 3, 4].map(i => (
                <div key={i} className={`ban-slot ${blueBans[i] ? 'filled' : 'empty'}`}>
                  {blueBans[i] || '?'}
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* VS Divider */}
        <div className="vs-divider">
          <div className="vs-text">VS</div>
        </div>
        
        {/* Red Team */}
        <div className="team red-team">
          <h3 className="team-header">🔴 Red Team</h3>
          
          <div className="picks">
            {roles.map(role => {
              const pick = getPickForRole(redPicks, role);
              return (
                <div key={role} className={`pick-slot ${pick ? 'filled' : 'empty'}`}>
                  <div className="role-label">{role}</div>
                  {pick ? (
                    <div className="champion-info">
                      <div className="champion-name">{pick.champion}</div>
                    </div>
                  ) : (
                    <div className="empty-slot">?</div>
                  )}
                </div>
              );
            })}
          </div>
          
          <div className="bans">
            <h4>Bans</h4>
            <div className="ban-list">
              {[0, 1, 2, 3, 4].map(i => (
                <div key={i} className={`ban-slot ${redBans[i] ? 'filled' : 'empty'}`}>
                  {redBans[i] || '?'}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DraftBoard;
