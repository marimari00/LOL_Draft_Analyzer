import React from 'react';
import './DraftBoard.css';
import { getChampionIconUrl, getChampionIconFallbackUrl } from '../utils/championAssets';
import SlotChampionInput from './SlotChampionInput';

const SKIP_BAN_SENTINEL = 'NONE';

const formatArchetypeLabel = (value) => {
  if (!value) return null;
  return value
    .split('_')
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
};

const DraftBoard = ({
  bluePicks,
  redPicks,
  blueBans,
  redBans,
  currentTeam,
  currentAction = 'pick',
  activeSlotId = null,
  pickOrder,
  teamOrder = ['blue', 'red'],
  onMoveLane,
  onResetPickOrder,
  onBanClick,
  availableChampions = [],
  onInlinePick,
  championLookup = {},
  playmakerHighlight = null
}) => {
  const ROLE_THEME_CLASS = React.useMemo(() => ({
    TOP: 'role-top',
    JUNGLE: 'role-jungle',
    MIDDLE: 'role-middle',
    BOTTOM: 'role-bottom',
    UTILITY: 'role-utility'
  }), []);

  const slotRefs = React.useRef({});
  const slotsByTeam = React.useMemo(() => ({
    blue: pickOrder.filter(slot => slot.team === 'blue'),
    red: pickOrder.filter(slot => slot.team === 'red')
  }), [pickOrder]);

  const totalPickSlots = pickOrder?.length || 0;
  const lockedPickCount = (bluePicks?.length || 0) + (redPicks?.length || 0);
  const progressRatio = totalPickSlots ? Math.min(lockedPickCount / totalPickSlots, 1) : 0;
  const progressAriaMax = Math.max(totalPickSlots || 0, 1);
  const nextSlot = totalPickSlots ? pickOrder[lockedPickCount] : null;
  const upcomingQueue = totalPickSlots
    ? pickOrder.slice(lockedPickCount + 1, lockedPickCount + 3)
    : [];
  const picksRemaining = Math.max(totalPickSlots - lockedPickCount, 0);

  const teamData = {
    blue: { picks: bluePicks, bans: blueBans },
    red: { picks: redPicks, bans: redBans }
  };

  const pickBySlotId = React.useMemo(() => {
    const map = {};
    [...bluePicks, ...redPicks].forEach(pick => {
      if (pick && pick.slotId) {
        map[pick.slotId] = pick;
      }
    });
    return map;
  }, [bluePicks, redPicks]);

  const firstOpenSlotIndex = React.useMemo(() => {
    const index = pickOrder.findIndex(slot => !pickBySlotId[slot.id]);
    return index === -1 ? pickOrder.length : index;
  }, [pickOrder, pickBySlotId]);

  const timelineSlots = React.useMemo(() => (
    pickOrder.map((slot, index) => {
      const pick = pickBySlotId[slot.id];
      let status = 'upcoming';
      if (pick) {
        status = 'locked';
      } else if (currentAction === 'pick' && activeSlotId && slot.id === activeSlotId) {
        status = 'active';
      } else if (!pick && index === firstOpenSlotIndex) {
        status = 'next';
      }
      return {
        ...slot,
        pick,
        status
      };
    })
  ), [pickOrder, pickBySlotId, activeSlotId, currentAction, firstOpenSlotIndex]);

  const timelineStatusLabels = {
    locked: 'Locked pick',
    active: 'Current slot on the clock',
    next: 'Up next',
    upcoming: 'Queued slot'
  };

  const accessibleTeamName = (team) => (team === 'blue' ? 'Blue Team' : 'Red Team');

  const formatSlotLabel = (slot) => {
    if (!slot) return '—';
    const teamLabel = slot.team === 'blue' ? 'Blue' : 'Red';
    return `${teamLabel} ${slot.role || 'FLEX'}`;
  };

  const getRoleClassName = (role) => {
    if (!role) return 'role-flex';
    const normalized = typeof role === 'string' ? role.toUpperCase() : role;
    return ROLE_THEME_CLASS[normalized] || 'role-flex';
  };

  const registerSlotRef = React.useCallback((slotId) => (node) => {
    if (node) {
      slotRefs.current[slotId] = node;
    } else {
      delete slotRefs.current[slotId];
    }
  }, []);

  // Keep keyboard focus synced with the active pick slot so screen readers announce context changes.
  React.useEffect(() => {
    if (currentAction !== 'pick' || !activeSlotId) {
      return;
    }
    const node = slotRefs.current[activeSlotId];
    if (node && typeof node.focus === 'function') {
      node.focus();
    }
  }, [activeSlotId, currentAction]);

  const getPickForSlot = (picks, slotId) => {
    return picks.find(p => p.slotId === slotId);
  };

  const renderTeam = (team, headingId) => {
    const slots = slotsByTeam[team] || [];
    const { picks = [], bans = [] } = teamData[team] || {};
    const teamLabel = accessibleTeamName(team);

    return (
      <>
      <div className="team-header-row">
        <h3 className="team-header" id={headingId}>{team === 'blue' ? '🔵 Blue Team' : '🔴 Red Team'}</h3>
      </div>
      <div className="picks" role="list" aria-label={`${teamLabel} picks`}>
        {slots.map((slot, idx) => {
          const pick = getPickForSlot(picks, slot.id);
          const prevSlot = idx > 0 ? slots[idx - 1] : null;
          const nextSlot = idx < slots.length - 1 ? slots[idx + 1] : null;
          const prevLocked = prevSlot ? Boolean(getPickForSlot(picks, prevSlot.id)) : false;
          const nextLocked = nextSlot ? Boolean(getPickForSlot(picks, nextSlot.id)) : false;
          const isLocked = Boolean(pick);
          const canMoveUp = idx > 0 && !isLocked && !prevLocked;
          const canMoveDown = idx < slots.length - 1 && !isLocked && !nextLocked;
          const isActiveSlot = !pick && currentAction === 'pick' && activeSlotId === slot.id;
          const slotClasses = [
            'pick-slot',
            pick ? 'filled' : 'empty',
            isActiveSlot ? 'active-slot' : ''
          ].join(' ').trim();
          const championInfo = pick ? championLookup[pick.champion] : null;
          const archetypeLabel = championInfo?.archetype ? formatArchetypeLabel(championInfo.archetype) : null;
          const isPlaymaker = Boolean(
            playmakerHighlight &&
            pick &&
            playmakerHighlight.team === team &&
            playmakerHighlight.champion === pick.champion
          );
          const playmakerTitle = isPlaymaker
            ? (typeof playmakerHighlight.impactPct === 'number'
              ? `Projected playmaker • Model swing ${playmakerHighlight.impactPct.toFixed(1)}%`
              : 'Projected playmaker for this comp')
            : null;

          return (
            <div
              key={slot.id}
              className={slotClasses}
              role="listitem"
              tabIndex={isActiveSlot ? 0 : -1}
              aria-label={pick
                ? `${teamLabel} ${slot.role || 'flex'} slot locked as ${pick.champion}`
                : `${teamLabel} ${slot.role || 'flex'} slot waiting for pick`}
              ref={registerSlotRef(slot.id)}
            >
              <div className={`slot-order-controls ${pick ? 'locked' : ''}`}>
                {pick ? (
                  <span
                    className="slot-order-locked"
                    aria-label="Lane order locked once champion is selected"
                    title="Lane order locks once this slot is filled"
                  >
                    <span aria-hidden="true">🔒</span>
                    <span className="locked-text">Locked</span>
                  </span>
                ) : (
                  <>
                    <button
                      className="arrow-btn"
                      onClick={() => onMoveLane(slot.id, 'up')}
                      disabled={!canMoveUp}
                      aria-label={`Move ${slot.role || 'flex'} slot ${slot.id} up`}
                    >
                      ▲
                    </button>
                    <button
                      className="arrow-btn"
                      onClick={() => onMoveLane(slot.id, 'down')}
                      disabled={!canMoveDown}
                      aria-label={`Move ${slot.role || 'flex'} slot ${slot.id} down`}
                    >
                      ▼
                    </button>
                  </>
                )}
              </div>
              <div className="slot-body">
                <div className="slot-meta">
                  <span className="slot-id">{slot.id}</span>
                  <span
                    className={`slot-role ${getRoleClassName(slot.role)}`}
                    aria-label={`Assigned role ${slot.role || 'Flex'}`}
                  >
                    {slot.role || 'FLEX'}
                  </span>
                </div>
                {pick ? (
                  <div className="champion-info">
                    <img
                      className="champion-avatar"
                      src={getChampionIconUrl(pick.champion)}
                      alt={pick.champion}
                      onError={(event) => {
                        const fallback = getChampionIconFallbackUrl(pick.champion);
                        if (fallback && event.currentTarget.src !== fallback) {
                          event.currentTarget.src = fallback;
                        }
                      }}
                    />
                    <div className="champion-text">
                      <div className="champion-name-row">
                        <div className="champion-name">{pick.champion}</div>
                        {isPlaymaker && (
                          <span className="playmaker-star" title={playmakerTitle}>★</span>
                        )}
                      </div>
                      <div className="champion-role">{slot.role}</div>
                      {archetypeLabel && (
                        <div className="champion-archetype">{archetypeLabel}</div>
                      )}
                    </div>
                  </div>
                ) : (
                  <SlotChampionInput
                    slot={slot}
                    team={team}
                    champions={availableChampions}
                    isActive={isActiveSlot}
                    disabled={currentAction !== 'pick'}
                    onSubmit={(value) => onInlinePick ? onInlinePick(slot.id, value) : null}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="bans">
        <h4 id={`${team}-bans-label`}>Bans</h4>
        <div className="ban-list" role="group" aria-labelledby={`${team}-bans-label`}>
          {[0, 1, 2, 3, 4].map(i => (
            (() => {
              const bannedChampion = bans[i];
              const hasBan = Boolean(bannedChampion);
              const skippedBan = bannedChampion === SKIP_BAN_SENTINEL;
              const banLabel = skippedBan ? 'None' : bannedChampion;
              const ariaLabel = hasBan
                ? `Remove ban ${banLabel} slot ${i + 1} for ${teamLabel}`
                : `Empty ban slot ${i + 1} for ${teamLabel}`;
              return (
                <button
                  key={i}
                  type="button"
                  className={`ban-slot ${hasBan ? 'filled' : 'empty'}`}
                  onClick={() => hasBan && onBanClick(team, i)}
                  disabled={!hasBan}
                  aria-label={ariaLabel}
                  title={hasBan ? banLabel : 'Open ban slot'}
                >
                  {hasBan ? (
                    <>
                      {skippedBan ? (
                        <span className="ban-name skip-ban">None</span>
                      ) : (
                        <>
                          <span className="ban-avatar">
                            <img
                              src={getChampionIconUrl(bannedChampion)}
                              alt=""
                              aria-hidden="true"
                              onError={(event) => {
                                const fallback = getChampionIconFallbackUrl(bannedChampion);
                                if (fallback && event.currentTarget.src !== fallback) {
                                  event.currentTarget.src = fallback;
                                }
                              }}
                            />
                          </span>
                          <span className="ban-name">{bannedChampion}</span>
                        </>
                      )}
                    </>
                  ) : (
                    <span className="ban-placeholder">?</span>
                  )}
                </button>
              );
            })()
          ))}
        </div>
      </div>
      </>
    );
  };

  const formatTeamLabel = (team) => (team === 'blue' ? '🔵 Blue Team' : '🔴 Red Team');
  const orderedTeams = teamOrder.length === 2 ? teamOrder : ['blue', 'red'];
  const vsText = orderedTeams.map(formatTeamLabel);

  return (
    <div className="draft-board">
      <div className="draft-title">
        <h2>Draft Board</h2>
        <div className="draft-status">
          <span
            className={`team-indicator ${currentTeam}`}
            role="status"
            aria-live="polite"
            aria-atomic="true"
          >
            {currentTeam === 'blue' ? '🔵' : '🔴'} {currentTeam.toUpperCase()} SIDE'S TURN
          </span>
          <button
            className="reset-order"
            onClick={onResetPickOrder}
            aria-label="Reset pick order to default lane layout"
          >
            Reset Lanes
          </button>
        </div>
      </div>

      <div className="draft-progress" aria-label="Draft progress tracker">
        <div className="progress-meta">
          <span className="progress-count">{lockedPickCount}/{totalPickSlots} picks locked</span>
          <span className="progress-remaining">{picksRemaining} picks to go</span>
          <span className="progress-next">{nextSlot ? `Next: ${formatSlotLabel(nextSlot)}` : 'Draft complete'}</span>
        </div>
        <div
          className="progress-bar"
          role="progressbar"
          aria-valuemin={0}
          aria-valuenow={lockedPickCount}
          aria-valuemax={progressAriaMax}
          aria-label="Overall pick completion"
        >
          <div
            className="progress-fill"
            style={{ width: `${progressRatio * 100}%` }}
          />
        </div>
        {upcomingQueue.length > 0 && (
          <div className="progress-upcoming" aria-live="polite">
            Upcoming: {upcomingQueue.map(formatSlotLabel).join(' • ')}
          </div>
        )}
        {timelineSlots.length > 0 && (
          <div className="draft-timeline" role="list" aria-label="Full pick order timeline">
            {timelineSlots.map((slot) => {
              const roleLabel = slot.role || 'FLEX';
              const statusLabel = timelineStatusLabels[slot.status] || 'Queued slot';
              const lockSuffix = slot.pick ? ` locked as ${slot.pick.champion}` : '';
              const timelineClasses = [
                'timeline-slot',
                slot.team === 'blue' ? 'timeline-blue' : 'timeline-red',
                `timeline-${slot.status}`
              ].join(' ');
              return (
                <div
                  key={slot.id}
                  className={timelineClasses}
                  role="listitem"
                  aria-label={`${slot.id} ${roleLabel} ${slot.team} — ${statusLabel}${lockSuffix}`}
                >
                  <span className="timeline-order">{slot.id}</span>
                  <span className={`timeline-role-badge ${getRoleClassName(slot.role)}`}>
                    {roleLabel}
                  </span>
                  {slot.pick ? (
                    <span className="timeline-champion" title={slot.pick.champion}>{slot.pick.champion}</span>
                  ) : (
                    <span className="timeline-status-text">
                      {slot.status === 'active' ? 'On clock' : slot.status === 'next' ? 'Next' : 'Queued'}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
      
      <div className="teams-container">
        <section
          className={`team ${orderedTeams[0]}-team`}
          aria-labelledby={`${orderedTeams[0]}-team-heading`}
        >
          {renderTeam(orderedTeams[0], `${orderedTeams[0]}-team-heading`)}
        </section>
        
        <div className="vs-divider">
          <div className="vs-text">
            <span>{vsText[0]}</span>
            <span className="vs-label">VS</span>
            <span>{vsText[1]}</span>
          </div>
        </div>
        
        <section
          className={`team ${orderedTeams[1]}-team`}
          aria-labelledby={`${orderedTeams[1]}-team-heading`}
        >
          {renderTeam(orderedTeams[1], `${orderedTeams[1]}-team-heading`)}
        </section>
      </div>
    </div>
  );
};

export default DraftBoard;
