import React, { useMemo, useState } from 'react';
import './BanSelector.css';
import { getChampionIconUrl, getChampionIconFallbackUrl } from '../utils/championAssets';

const normalizeKey = (value = '') => value.toLowerCase().replace(/[^a-z0-9]/g, '');
const SKIP_BAN_SENTINEL = 'NONE';

const TEAM_LABEL = {
  blue: 'Blue Side',
  red: 'Red Side'
};

const BanSelector = ({
  banTeam = 'blue',
  banTurnLabel = '',
  availableChampions = [],
  onBanSelect,
  disabled = false,
  bansUsed = 0,
  maxBans = 5,
  banHistory = { blue: [], red: [] },
  banRecommendations = [],
  banRecommendationsLoading = false,
  banRecommendationContext = null,
  allowNoneBan = false
}) => {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState(null);
  const phaseLabel = banRecommendationContext?.phase
    ? banRecommendationContext.phase.replace(/_/g, ' ')
    : null;
  const targetTeam = banRecommendationContext?.target_team;
  const banTheme = banRecommendationContext?.target_theme;
  const ourTheme = banRecommendationContext?.our_theme;

  const filteredChampions = useMemo(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      return availableChampions.slice(0, 18);
    }
    const normalized = normalizeKey(trimmed);
    return availableChampions
      .filter(entry => {
        const key = normalizeKey(entry.name);
        if (!normalized) {
          return true;
        }
        return key.includes(normalized) || entry.name.toLowerCase().includes(trimmed.toLowerCase());
      })
      .slice(0, 18);
  }, [availableChampions, query]);

  const resetStatus = () => setStatus(null);

  const commitBan = (championName) => {
    if (disabled || !championName) {
      return;
    }
    onBanSelect?.(championName);
    if (championName === SKIP_BAN_SENTINEL) {
      setStatus({ type: 'success', message: 'No ban submitted this turn' });
    } else {
      setStatus({ type: 'success', message: `${championName} banned` });
    }
    setQuery('');
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setStatus({ type: 'error', message: 'Type a champion name to ban' });
      return;
    }
    const normalized = normalizeKey(trimmed);
    const exact = availableChampions.find(entry => normalizeKey(entry.name) === normalized);
    const fallback = exact || availableChampions.find(entry => entry.name.toLowerCase().includes(trimmed.toLowerCase()));
    if (!fallback) {
      setStatus({ type: 'error', message: `No champion matches "${trimmed}"` });
      return;
    }
    commitBan(fallback.name);
  };

  const renderHistoryLine = (team) => {
    const entries = banHistory?.[team] || [];
    if (!entries.length) {
      return '—';
    }
    return entries
      .map(entry => (entry === SKIP_BAN_SENTINEL ? 'None' : entry))
      .join(', ');
  };

  return (
    <section className="ban-selector" aria-labelledby="ban-selector-title">
      <div className="ban-selector-header">
        <div>
          <h3 id="ban-selector-title">🚫 Ban Control</h3>
          <p className="turn-label">Next turn: {banTurnLabel || '—'}</p>
          <p className="ban-progress">{bansUsed}/{maxBans} bans locked for {TEAM_LABEL[banTeam] || 'Draft'}</p>
        </div>
        <div className={`ban-team-chip ${banTeam}`} aria-label={`${TEAM_LABEL[banTeam] || 'Team'} banning`}>
          {TEAM_LABEL[banTeam] || 'Team'}
        </div>
      </div>

      <div className="ban-radar" aria-live="polite">
        <div className="ban-radar-header">
          <div>
            <p className="ban-radar-title">Automated ban radar</p>
            <div className="ban-radar-context">
              {phaseLabel && <span className="ban-phase-chip">{phaseLabel}</span>}
              {targetTeam && <span className="ban-context-line">Targeting {targetTeam.toUpperCase()}</span>}
              {banTheme && <span className="ban-context-line">Break: {banTheme}</span>}
              {ourTheme && <span className="ban-context-line">Protect: {ourTheme}</span>}
            </div>
          </div>
          {allowNoneBan && (
            <button
              type="button"
              className="skip-ban-button"
              onClick={() => commitBan(SKIP_BAN_SENTINEL)}
              disabled={disabled}
            >
              None / Skip
            </button>
          )}
        </div>
        {banRecommendationsLoading ? (
          <div className="ban-radar-loading">
            <div className="spinner" aria-hidden="true"></div>
            <p>Scouting ban priorities...</p>
          </div>
        ) : banRecommendations.length ? (
          <div className="ban-radar-grid">
            {banRecommendations.map((ban, index) => {
              const tags = ban.tags || [];
              const banScore = typeof ban.score === 'number' ? ban.score.toFixed(2) : null;
              const metaScore = typeof ban.metrics?.meta_score === 'number'
                ? ban.metrics.meta_score.toFixed(2)
                : null;
              return (
                <button
                  key={`${ban.champion}-${ban.category || index}`}
                  type="button"
                  className="ban-reco-card"
                  onClick={() => commitBan(ban.champion)}
                  disabled={disabled}
                >
                  <div className="ban-reco-rank">#{index + 1}</div>
                  <div className="ban-reco-main">
                    <img
                      className="ban-reco-icon"
                      src={getChampionIconUrl(ban.champion)}
                      alt={ban.champion}
                      onError={(event) => {
                        const fallback = getChampionIconFallbackUrl(ban.champion);
                        if (fallback && event.currentTarget.src !== fallback) {
                          event.currentTarget.src = fallback;
                        }
                      }}
                    />
                    <div className="ban-reco-info">
                      <div className="ban-reco-header">
                        <span className="ban-reco-name">{ban.champion}</span>
                        {ban.category && <span className="ban-reco-category">{ban.category}</span>}
                      </div>
                      <p className="ban-reco-reason">{ban.reason}</p>
                      <div className="ban-reco-tags">
                        {banScore && <span className="ban-score-chip">Score {banScore}</span>}
                        {metaScore && <span className="ban-score-chip">Meta {metaScore}</span>}
                        {tags.slice(0, 3).map(tag => (
                          <span key={tag} className="ban-tag">{tag}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <p className="ban-radar-empty">Lock a few more champs to surface automated bans.</p>
        )}
      </div>

      <form className="ban-search" onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          placeholder="Search champion to ban"
          aria-label="Search champion to ban"
          onChange={(event) => {
            resetStatus();
            setQuery(event.target.value);
          }}
          disabled={disabled}
        />
        <button type="submit" disabled={disabled}>Ban</button>
      </form>

      {status && (
        <div className={`ban-status ${status.type}`}>{status.message}</div>
      )}

      <div className="ban-history">
        <div>
          <span className="history-label">Blue:</span>
          <span>{renderHistoryLine('blue')}</span>
        </div>
        <div>
          <span className="history-label">Red:</span>
          <span>{renderHistoryLine('red')}</span>
        </div>
      </div>

      <div className="ban-grid" role="list">
        {filteredChampions.length === 0 ? (
          <div className="empty-search" role="status">No champions available</div>
        ) : (
          filteredChampions.map(champion => (
            <button
              key={champion.name}
              type="button"
              className="ban-card"
              onClick={() => commitBan(champion.name)}
              disabled={disabled}
            >
              <span className="ban-card-media">
                <img
                  src={getChampionIconUrl(champion.name)}
                  alt={champion.name}
                  onError={(event) => {
                    const fallback = getChampionIconFallbackUrl(champion.name);
                    if (fallback && event.currentTarget.src !== fallback) {
                      event.currentTarget.src = fallback;
                    }
                  }}
                />
              </span>
              <span className="ban-card-name">{champion.name}</span>
              <span className="ban-card-roles">{(champion.roles || []).join(' / ') || 'FLEX'}</span>
            </button>
          ))
        )}
      </div>
    </section>
  );
};

export default BanSelector;
