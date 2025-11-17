import React from 'react';
import './RecommendationPanel.css';
import { getChampionIconUrl } from '../utils/championAssets';

const LABEL_MAP = {
  balance: 'Balance',
  synergy: 'Synergy',
  counters: 'Counters',
  comfort: 'Playstyle',
  role_fit: 'Lane Fit'
};

const ROLE_THEME_CLASS = {
  TOP: 'role-top',
  JUNGLE: 'role-jungle',
  MIDDLE: 'role-middle',
  BOTTOM: 'role-bottom',
  UTILITY: 'role-utility'
};

const ROLE_GLYPH = {
  TOP: '▲',
  JUNGLE: '✦',
  MIDDLE: '◆',
  BOTTOM: '▼',
  UTILITY: '✚',
  FLEX: '⬡'
};

const getRoleClassName = (role) => {
  if (!role) return 'role-flex';
  const normalized = typeof role === 'string' ? role.toUpperCase() : role;
  return ROLE_THEME_CLASS[normalized] || 'role-flex';
};

const RoleBadge = ({ role, variant = 'pill', label }) => {
  const normalized = role && typeof role === 'string' && role.trim()
    ? role.trim().toUpperCase()
    : 'FLEX';
  const glyph = ROLE_GLYPH[normalized] || ROLE_GLYPH.FLEX;
  const displayLabel = label || normalized;
  const baseClass = variant === 'compact' ? 'slot-role' : 'role-pill';
  return (
    <span className={`${baseClass} ${getRoleClassName(normalized)}`} aria-label={`${displayLabel} role`}>
      <span className="role-glyph" aria-hidden="true">{glyph}</span>
      <span className="role-label-text">{displayLabel}</span>
    </span>
  );
};

const formatBreakdownLabel = (key) => LABEL_MAP[key] || key.replace(/_/g, ' ');

const PRO_IDENTITY_GUIDE = {
  'Hard Engage': {
    commitment: 'You are trading ult cooldowns for first move fights and need vision to start on your terms.',
    next: 'Layer dependable backline DPS or peel so the dive actually converts.'
  },
  'Protect the Carry': {
    commitment: 'You are protecting a single hyper-carry and playing for reset denial and anti-dive tools.',
    next: 'Stack peel or zone control so the backline survives long enough to win the fight.'
  },
  'Siege & Poke': {
    commitment: 'You are slow-playing waves, chipping plates, and forcing them to walk into long range skillshots.',
    next: 'Add disengage or a safety valve when they hard force through the poke line.'
  },
  'Pick Composition': {
    commitment: 'You are fishing for fog plays and trading cooldowns for pick pressure.',
    next: 'Secure reliable follow up or vision denial so every catch becomes a kill.'
  },
  'Bruiser Brawl': {
    commitment: 'You are building skirmish lanes that want to scrap in river and side bushes.',
    next: 'Round it out with burst or backline threat so the bruisers are not kited.'
  },
  'AoE Teamfight': {
    commitment: 'You are stacking wombo combos that demand strict setup and patience on timers.',
    next: 'Lock in steady engage or frontline HP so the combo ever lands.'
  },
  'Specialist Pocket': {
    commitment: 'You are enabling a niche pocket pick with very specific map states.',
    next: 'Draft insulation for its weak phases or tools that buy it time to scale.'
  },
  Flexible: {
    commitment: 'You are still hiding the real win condition and keeping lanes ambiguous.',
    next: 'Use the next slot to declare how you actually win fights.'
  }
};

const formatIdentityName = (identity) => {
  if (!identity || identity === 'Flexible') {
    return 'flexible';
  }
  return identity.toLowerCase();
};

const getIdentityGuide = (identity) => {
  if (!identity) return PRO_IDENTITY_GUIDE.Flexible;
  return PRO_IDENTITY_GUIDE[identity] || PRO_IDENTITY_GUIDE.Flexible;
};

const buildCommitmentLine = (champion, currentLean, futureLean) => {
  const futureGuide = getIdentityGuide(futureLean);
  const futureIdentity = futureLean && futureLean !== 'Flexible' ? futureLean : null;
  const currentIdentity = currentLean && currentLean !== 'Flexible' ? currentLean : null;

  if (!futureIdentity) {
    if (currentIdentity) {
      return `${champion} keeps you flirting with ${formatIdentityName(currentIdentity)} looks without declaring yet.`;
    }
    return `${champion} keeps the draft flexible, so coaches will still demand a declared win condition next.`;
  }

  if (!currentIdentity) {
    return `${champion} is the first real commit. ${futureGuide.commitment}`;
  }

  if (currentIdentity === futureIdentity) {
    return `${champion} doubles down on ${formatIdentityName(futureIdentity)} principles. ${futureGuide.commitment}`;
  }

  return `${champion} pivots you from ${formatIdentityName(currentIdentity)} into ${formatIdentityName(futureIdentity)} territory. ${futureGuide.commitment}`;
};

const buildNextAskLine = (futureLean) => {
  const guide = getIdentityGuide(futureLean);
  return `Next ask: ${guide.next}`;
};

const getTopBreakdownEntries = (breakdown = {}) => {
  return Object.entries(breakdown)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .slice(0, 3);
};

const formatPercent = (value) => {
  if (typeof value !== 'number') return '—';
  return `${(value * 100).toFixed(1)}%`;
};

const RecommendationPanel = ({
  slotRecommendations = [],
  loading,
  currentAction,
  onSelect,
  recommendationTeam,
  userFocusTeam,
  waitingForTurn,
  teamLeanSummaries = {},
  winProjection = null
}) => {
  const [activeFilters, setActiveFilters] = React.useState([]);

  const filterOptions = React.useMemo(() => {
    const counts = {};
    slotRecommendations.forEach(slot => {
      (slot.recommendations || []).forEach(rec => {
        (rec.rationale_tags || []).forEach(tag => {
          if (!tag) return;
          const normalized = tag.trim();
          if (!normalized) return;
          counts[normalized] = (counts[normalized] || 0) + 1;
        });
      });
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([tag, count]) => ({ tag, count }));
  }, [slotRecommendations]);

  React.useEffect(() => {
    if (!activeFilters.length) return;
    const available = new Set(filterOptions.map(option => option.tag));
    const filtered = activeFilters.filter(tag => available.has(tag));
    if (filtered.length !== activeFilters.length) {
      setActiveFilters(filtered);
    }
  }, [activeFilters, filterOptions]);

  const toggleFilter = React.useCallback((tag) => {
    setActiveFilters(prev => (
      prev.includes(tag)
        ? prev.filter(item => item !== tag)
        : [...prev, tag]
    ));
  }, []);

  const clearFilters = React.useCallback(() => {
    setActiveFilters([]);
  }, []);

  if (currentAction === 'ban') {
    return (
      <div className="recommendation-panel">
        <h3>💡 Recommendations</h3>
        <div className="no-recommendations">
          <p>The ban radar now lives inside the Ban Control panel.</p>
          <p className="hint">Use that space to auto-lock removals or skip a solo queue ban.</p>
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
  
  if (slotRecommendations.length === 0) {
    return (
      <div className="recommendation-panel">
        <h3>💡 Recommendations</h3>
        <div className="no-recommendations">
          {waitingForTurn ? (
            <>
              <p>Waiting for {recommendationTeam?.toUpperCase() || 'THE OTHER'} side to pick.</p>
              <p className="hint">We’ll analyze once it’s {userFocusTeam.toUpperCase()}’s turn.</p>
            </>
          ) : (
            <p>Start picking champions to see recommendations!</p>
          )}
        </div>
      </div>
    );
  }
  
  const projectionBlue = typeof winProjection?.blue === 'number' ? winProjection.blue : 0;
  const projectionRed = typeof winProjection?.red === 'number' ? winProjection.red : 0;
  const favoredSide = winProjection
    ? (winProjection.favored || (projectionBlue >= projectionRed ? 'blue' : 'red'))
    : null;

  return (
    <div className="recommendation-panel">
      <div className="panel-title-row">
        <h3>💡 Next Picks</h3>
        <span className="panel-subtitle">{(recommendationTeam || 'TEAM').toUpperCase()} SIDE</span>
      </div>
      <p className="panel-legend">Pro staffs ask what this lock commits you to; each card states the plan and the debt you still owe.</p>

      {winProjection && (
        <div className="win-projection-panel">
          <div className="win-strip" aria-label="Current win probability projection">
            <div
              className="win-segment blue"
              style={{ width: `${projectionBlue * 100}%` }}
            >
              <span>Blue {formatPercent(projectionBlue)}</span>
            </div>
            <div
              className="win-segment red"
              style={{ width: `${projectionRed * 100}%` }}
            >
              <span>Red {formatPercent(projectionRed)}</span>
            </div>
          </div>
          <div className="win-summary-row">
            <span className="favored-label">
              {favoredSide?.toUpperCase()} FAVORED
            </span>
            {typeof winProjection.confidence === 'number' && (
              <span className="confidence-chip">{(winProjection.confidence * 100).toFixed(0)}% model agreement</span>
            )}
            {winProjection.notes && winProjection.notes.length > 0 && (
              <span className="projection-note">{winProjection.notes[0]}</span>
            )}
          </div>
        </div>
      )}

      {slotRecommendations.length > 0 && (
        <div className="team-lean-overview">
          <div className="lean-card blue-lean">
            <span className="lean-label">Blue leaning</span>
            <span className="lean-value">{teamLeanSummaries.blue || 'Flexible'}</span>
          </div>
          <div className="lean-card red-lean">
            <span className="lean-label">Red leaning</span>
            <span className="lean-value">{teamLeanSummaries.red || 'Flexible'}</span>
          </div>
        </div>
      )}

      {filterOptions.length > 0 && (
        <div className="filter-toolbar" role="group" aria-label="Filter recommendation cards by composition needs">
          <div className="filter-scroll">
            {filterOptions.map(option => {
              const isActive = activeFilters.includes(option.tag);
              return (
                <button
                  key={option.tag}
                  type="button"
                  className={`filter-chip ${isActive ? 'active' : ''}`}
                  onClick={() => toggleFilter(option.tag)}
                  aria-pressed={isActive}
                >
                  <span className="filter-label">{option.tag}</span>
                  <span className="filter-count">{option.count}</span>
                </button>
              );
            })}
          </div>
          {activeFilters.length > 0 && (
            <button
              type="button"
              className="filter-reset"
              onClick={clearFilters}
            >
              Clear filters
            </button>
          )}
        </div>
      )}
      
      <div className="recommendation-columns">
        {slotRecommendations.map(slot => {
          const rawRecs = slot.recommendations || [];
          const slotRecs = activeFilters.length === 0
            ? rawRecs
            : rawRecs.filter(rec => {
                const tags = rec.rationale_tags || [];
                return activeFilters.every(tag => tags.includes(tag));
              });
          const filteredOut = activeFilters.length > 0 && rawRecs.length > 0 && slotRecs.length === 0;
          return (
            <div key={slot.slot_id} className="slot-column">
            <div className="slot-header">
              <div className="slot-id">{slot.slot_id}</div>
              <RoleBadge role={slot.role} label={slot.role || 'FLEX'} variant="compact" />
            </div>
            <div className="slot-team">{slot.team.toUpperCase()}</div>
            {slot.teamLeanLabel && (
              <div className="slot-lean">Current lean: {slot.teamLeanLabel}</div>
            )}

            {rawRecs.length === 0 && (
              <div className="no-recommendations">
                <p>No viable picks for this lane</p>
              </div>
            )}

            {filteredOut && (
              <div className="no-recommendations filtered" role="status">
                <p>No picks match the active filters here.</p>
                <button type="button" className="filter-reset inline" onClick={clearFilters}>Clear filters</button>
              </div>
            )}

            {slotRecs.slice(0, 5).map((rec, index) => {
              const highlights = rec.attribute_highlights || [];
              const cardClasses = ['recommendation-card'];
              const projectedTeamRate = typeof rec.projected_team_winrate === 'number'
                ? rec.projected_team_winrate
                : null;
              const displayRole = slot.role || rec.recommended_role;
              const displayRoleLabel = displayRole || 'FLEX';
              const roleAccentClass = displayRoleLabel
                ? `rec-role-${(displayRoleLabel || 'flex').toString().toLowerCase().replace(/[^a-z]/g, '')}`
                : 'rec-role-flex';
              cardClasses.push(roleAccentClass);
              const handleSelect = () => onSelect(rec.champion, displayRole);
              const handleKeyDown = (event) => {
                if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar') {
                  event.preventDefault();
                  handleSelect();
                }
              };
              const baseWinRate = slot.team === 'blue' ? projectionBlue : projectionRed;
              const winDelta = (typeof baseWinRate === 'number' && projectedTeamRate !== null)
                ? projectedTeamRate - baseWinRate
                : null;
              return (
                <div 
                  key={`${slot.slot_id}-${rec.champion}`}
                  className={cardClasses.join(' ')}
                  onClick={handleSelect}
                  role="button"
                  tabIndex={0}
                  onKeyDown={handleKeyDown}
                  aria-label={`Lock ${rec.champion} for ${displayRoleLabel} slot`}
                >
                <div className="rec-header">
                  <div className="rec-rank">#{index + 1}</div>
                  <div className="rec-main">
                    <img
                      className="rec-icon"
                      src={getChampionIconUrl(rec.champion)}
                      alt={rec.champion}
                    />
                    <div className="rec-info">
                      <div className="rec-champion-row">
                        <div className="rec-champion">{rec.champion}</div>
                        <RoleBadge role={displayRole} label={displayRoleLabel} />
                      </div>
                      <div className="rec-archetype">{rec.archetype}</div>
                    </div>
                  </div>
                  <div className="rec-score" title="Fit Score = synergy + counters + role fit">
                    <div className="score-bar">
                      <div 
                        className="score-fill" 
                        style={{ width: `${rec.score * 100}%` }}
                      ></div>
                    </div>
                    <div className="score-text">
                      <span className="score-value">{(rec.score * 100).toFixed(0)}%</span>
                      <span className="score-label">Fit Score</span>
                    </div>
                  </div>
                </div>

                {projectedTeamRate !== null && (
                  <div className="recommendation-meta">
                    <span className="meta-label">Team win chance if locked</span>
                    <span className="winrate-chip" title={winDelta !== null ? `Shift of ${(winDelta * 100).toFixed(1)} percentage points from current projection` : undefined}>
                      {(projectedTeamRate * 100).toFixed(1)}%
                      {winDelta !== null && (
                        <span className={`winrate-delta ${winDelta > 0 ? 'delta-positive' : winDelta < 0 ? 'delta-negative' : ''}`}>
                          {winDelta > 0 ? '+' : ''}{(winDelta * 100).toFixed(1)}%
                        </span>
                      )}
                    </span>
                  </div>
                )}

                {getTopBreakdownEntries(rec.score_breakdown).length > 0 && (
                  <div className="score-breakdown">
                    {getTopBreakdownEntries(rec.score_breakdown).map(([key, value]) => (
                      <div
                        key={key}
                        className={`breakdown-chip ${value >= 0 ? 'positive' : 'negative'}`}
                      >
                        <span className="chip-label">{formatBreakdownLabel(key)}</span>
                        <span className="chip-value">{value >= 0 ? '+' : ''}{Math.round(value * 100)}%</span>
                      </div>
                    ))}
                  </div>
                )}

                {rec.rationale_tags && rec.rationale_tags.length > 0 && (
                  <div className="rationale-tags">
                    {rec.rationale_tags.map(tag => (
                      <span key={tag} className="rationale-tag">{tag}</span>
                    ))}
                  </div>
                )}

                {highlights.length > 0 && (
                  <div className="attribute-tags">
                    {highlights.map(attr => (
                      <span key={attr} className="attribute-tag">{attr}</span>
                    ))}
                  </div>
                )}

                {rec.futureLeanLabel && (
                  <div className="future-lean">
                    Sways toward <span>{rec.futureLeanLabel}</span>
                  </div>
                )}

                <div className="pro-voice">
                  <div className="pro-line">
                    {buildCommitmentLine(rec.champion, slot.teamLeanLabel, rec.futureLeanLabel)}
                  </div>
                  <div className="pro-line next-callout">
                    {buildNextAskLine(rec.futureLeanLabel)}
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

                <div className="rec-cta" aria-hidden="true">
                  <span className="cta-icon">↳</span>
                  <span className="cta-text">Lock {rec.champion}</span>
                </div>
              </div>
              );
            })}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RecommendationPanel;
