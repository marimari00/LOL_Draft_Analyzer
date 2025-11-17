import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import './CoachTraining.css';
import { getChampionIconUrl, getChampionIconFallbackUrl } from '../utils/championAssets';

const ROLE_ORDER = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'];
const MINIMUM_CHAMPIONS = 12;

const formatPercent = (value) => `${(value * 100).toFixed(1)}%`;
const formatLabel = (value = '') => value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
const createDuelStats = () => ({
  attempts: 0,
  correct: 0,
  streak: 0,
  bestStreak: 0
});
const createPickStats = () => ({
  attempts: 0,
  perfect: 0,
  positive: 0,
  streak: 0,
  bestStreak: 0,
  score: 0
});

const shuffleArray = (items = []) => {
  const clone = [...items];
  for (let i = clone.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [clone[i], clone[j]] = [clone[j], clone[i]];
  }
  return clone;
};

const MAX_DUEL_HISTORY = 3;
const MAX_PICK_HISTORY = 4;
const DUEL_LABEL_STORAGE_KEY = 'coach_training_duel_labels_v1';

const storage = typeof window !== 'undefined' ? window.localStorage : null;

const safeReadLabels = () => {
  if (!storage) return {};
  try {
    const raw = storage.getItem(DUEL_LABEL_STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (error) {
    console.warn('Failed to read duel labels from storage', error);
    return {};
  }
};

const safeWriteLabels = (data) => {
  if (!storage) return;
  try {
    storage.setItem(DUEL_LABEL_STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.warn('Failed to persist duel labels', error);
  }
};

const persistDuelLabel = (setter, entryId, winner) => {
  if (!entryId) return;
  setter(prev => {
    const next = { ...prev };
    if (winner) {
      next[entryId] = winner;
    } else {
      delete next[entryId];
    }
    safeWriteLabels(next);
    return next;
  });
};

const formatTimeLabel = (value) => {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch (error) {
    return '—';
  }
};

const formatDurationLabel = (ms) => {
  if (typeof ms !== 'number' || Number.isNaN(ms) || ms < 0) return null;
  if (ms < 1000) return `${ms} ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)} s`;
  return `${Math.round(ms / 60000)} min`;
};

const formatTeamPreview = (team = []) => {
  if (!Array.isArray(team) || !team.length) return '—';
  return team.map(pick => pick?.champion || 'Unknown').join(', ');
};

const CoachTraining = ({ championPool = [], championLookup = {}, apiBase }) => {
  const [duelState, setDuelState] = useState(null);
  const [duelLoading, setDuelLoading] = useState(false);
  const [duelError, setDuelError] = useState(null);
  const [duelFeedback, setDuelFeedback] = useState(null);
  const [duelLabelCache, setDuelLabelCache] = useState(() => safeReadLabels());
  const [duelHistory, setDuelHistory] = useState([]);
  const [labelingOutcome, setLabelingOutcome] = useState(false);
  const [historyLabelLoading, setHistoryLabelLoading] = useState({});

  const [pickScenario, setPickScenario] = useState(null);
  const [pickLoading, setPickLoading] = useState(false);
  const [pickFeedback, setPickFeedback] = useState(null);
  const [pickError, setPickError] = useState(null);
  const [duelStats, setDuelStats] = useState(() => createDuelStats());
  const [pickStats, setPickStats] = useState(() => createPickStats());
  const [pickHistory, setPickHistory] = useState([]);

  const canRunExercises = championPool.length >= MINIMUM_CHAMPIONS;
  const resetDuelStats = () => setDuelStats(createDuelStats());
  const resetPickStats = () => setPickStats(createPickStats());
  const clearPickHistory = () => setPickHistory([]);

  const pickChampion = (preferredRole, used) => {
    const roleMatches = championPool.filter(entry => !used.has(entry.name) && entry.roles?.includes(preferredRole));
    const fallback = championPool.filter(entry => !used.has(entry.name));
    const pool = roleMatches.length ? roleMatches : fallback;
    if (!pool.length) {
      return null;
    }
    const choice = pool[Math.floor(Math.random() * pool.length)];
    used.add(choice.name);
    return {
      champion: choice.name,
      role: preferredRole ?? choice.roles?.[0] ?? null
    };
  };

  const generateFullDraft = () => {
    const used = new Set();
    const blueTeam = ROLE_ORDER.map(role => pickChampion(role, used)).filter(Boolean);
    const redTeam = ROLE_ORDER.map(role => pickChampion(role, used)).filter(Boolean);
    if (blueTeam.length < 5 || redTeam.length < 5) {
      throw new Error('Not enough unique champions to build a duel.');
    }
    return { blueTeam, redTeam };
  };

  const requestDuelAnalysis = async (blueTeam, redTeam, options = {}) => {
    const payload = {
      blue_team: blueTeam.map(pick => pick.champion),
      blue_roles: blueTeam.map(pick => pick.role),
      red_team: redTeam.map(pick => pick.champion),
      red_roles: redTeam.map(pick => pick.role)
    };
    if (options.actualWinner) {
      payload.actual_winner = options.actualWinner;
    }
    const response = await axios.post(`${apiBase}/draft/analyze`, payload);
    return response.data;
  };

  const summarizeDuelScenario = (blueTeam, redTeam, analysis, overrides = {}) => {
    if (!analysis?.prediction) return null;
    const prediction = analysis.prediction;
    const matchupDetails = analysis.matchup_context || {};
    const winnerSide = prediction.winner === 'red' ? 'Red' : 'Blue';
    let winrate = null;
    if (prediction.winner === 'blue' && typeof prediction.blue_win_probability === 'number') {
      winrate = prediction.blue_win_probability * 100;
    } else if (prediction.winner === 'red' && typeof prediction.red_win_probability === 'number') {
      winrate = prediction.red_win_probability * 100;
    }
    const confidenceSource = typeof matchupDetails.confidence === 'number'
      ? matchupDetails.confidence
      : typeof prediction.confidence === 'number'
        ? prediction.confidence
        : null;
    const confidencePct = confidenceSource !== null ? confidenceSource * 100 : null;
    const favoredInsights = Array.isArray(matchupDetails.favored_insights) ? matchupDetails.favored_insights : [];
    const underdogInsights = Array.isArray(matchupDetails.underdog_insights) ? matchupDetails.underdog_insights : [];
    const archetypeFallback = Array.isArray(analysis.archetypal_insights) ? analysis.archetypal_insights : [];
    const winnerLabel = matchupDetails.favored_label || winnerSide;
    const noteSource = winnerSide === winnerLabel ? favoredInsights : underdogInsights;
    const note = (noteSource && noteSource[0]) || archetypeFallback[0] || '';
    return {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      blueTeam: blueTeam.map(p => ({ ...p })),
      redTeam: redTeam.map(p => ({ ...p })),
      winner: winnerSide,
      winrate,
      confidence: confidencePct,
      note,
      actualWinner: overrides.actualWinner ?? null
    };
  };

  const pushDuelHistory = (entry, replaceId = null) => {
    if (!entry) return;
    const cachedWinner = duelLabelCache?.[entry.id];
    const finalEntry = cachedWinner && !entry.actualWinner
      ? { ...entry, actualWinner: cachedWinner }
      : entry;
    setDuelHistory(prev => {
      const filtered = replaceId ? prev.filter(item => item.id !== replaceId) : prev;
      return [finalEntry, ...filtered].slice(0, MAX_DUEL_HISTORY);
    });
  };

  const updateHistoryEntry = (entryId, updates) => {
    if (!entryId) return;
    setDuelHistory(prev => prev.map(item => (
      item.id === entryId ? { ...item, ...updates } : item
    )));
  };

  const pushPickHistory = (entry) => {
    if (!entry) return;
    setPickHistory(prev => [entry, ...prev].slice(0, MAX_PICK_HISTORY));
  };

  const handleGenerateDuel = async () => {
    if (!canRunExercises) {
      setDuelError('Load champion data before running exercises.');
      return;
    }
    setDuelLoading(true);
    setDuelError(null);
    setDuelFeedback(null);
    try {
      const { blueTeam, redTeam } = generateFullDraft();
      const analysis = await requestDuelAnalysis(blueTeam, redTeam);
      if (!analysis?.prediction) {
        throw new Error('Model did not return a prediction.');
      }
      const summary = summarizeDuelScenario(blueTeam, redTeam, analysis);
      const cachedWinner = summary?.id ? duelLabelCache?.[summary.id] : null;
      const resolvedSummary = cachedWinner && !summary.actualWinner
        ? { ...summary, actualWinner: cachedWinner }
        : summary;
      setDuelState({
        blueTeam,
        redTeam,
        analysis,
        historyId: resolvedSummary?.id || null,
        actualWinner: resolvedSummary?.actualWinner || null
      });
      pushDuelHistory(resolvedSummary);
    } catch (error) {
      console.error('Failed to generate duel scenario', error);
      setDuelError(error.message || 'Unable to build duel scenario.');
      setDuelState(null);
    } finally {
      setDuelLoading(false);
    }
  };

  const handleRematch = async (historyEntry) => {
    if (!historyEntry?.blueTeam?.length || !historyEntry?.redTeam?.length) return;
    setDuelLoading(true);
    setDuelError(null);
    setDuelFeedback(null);
    try {
      const analysis = await requestDuelAnalysis(historyEntry.blueTeam, historyEntry.redTeam);
      if (!analysis?.prediction) {
        throw new Error('Model did not return a prediction.');
      }
      const summary = summarizeDuelScenario(
        historyEntry.blueTeam,
        historyEntry.redTeam,
        analysis,
        { actualWinner: historyEntry.actualWinner }
      );
      const cachedWinner = summary?.id ? duelLabelCache?.[summary.id] : null;
      const resolvedSummary = cachedWinner && !summary.actualWinner
        ? { ...summary, actualWinner: cachedWinner }
        : summary;
      setDuelState({
        blueTeam: historyEntry.blueTeam,
        redTeam: historyEntry.redTeam,
        analysis,
        historyId: resolvedSummary?.id || null,
        actualWinner: resolvedSummary?.actualWinner || null
      });
      pushDuelHistory(resolvedSummary, historyEntry.id);
    } catch (error) {
      console.error('Failed to rematch duel scenario', error);
      setDuelError(error.message || 'Unable to rerun duel scenario.');
    } finally {
      setDuelLoading(false);
    }
  };

  const labelDuelOutcome = async (winner) => {
    if (!duelState || labelingOutcome) return;
    setLabelingOutcome(true);
    try {
      await requestDuelAnalysis(duelState.blueTeam, duelState.redTeam, { actualWinner: winner });
      setDuelState(prev => (prev ? { ...prev, actualWinner: winner } : prev));
      if (duelState.historyId) {
        updateHistoryEntry(duelState.historyId, { actualWinner: winner });
        persistDuelLabel(setDuelLabelCache, duelState.historyId, winner);
      }
    } catch (error) {
      console.error('Failed to log duel outcome', error);
      setDuelError(error.message || 'Unable to log duel outcome.');
    } finally {
      setLabelingOutcome(false);
    }
  };

  const labelHistoryOutcome = async (entry, winner) => {
    if (!entry) return;
    setHistoryLabelLoading(prev => ({ ...prev, [entry.id]: true }));
    try {
      await requestDuelAnalysis(entry.blueTeam, entry.redTeam, { actualWinner: winner });
      updateHistoryEntry(entry.id, { actualWinner: winner });
      persistDuelLabel(setDuelLabelCache, entry.id, winner);
      if (duelState?.historyId === entry.id) {
        setDuelState(prev => (prev ? { ...prev, actualWinner: winner } : prev));
      }
    } catch (error) {
      console.error('Failed to log history outcome', error);
      setDuelError(error.message || 'Unable to log duel outcome.');
    } finally {
      setHistoryLabelLoading(prev => ({ ...prev, [entry.id]: false }));
    }
  };

  const handleDuelGuess = (team) => {
    if (!duelState?.analysis?.prediction) return;
    const { prediction } = duelState.analysis;
    const winner = prediction.blue_win_probability >= prediction.red_win_probability ? 'blue' : 'red';
    const correct = team === winner;
    setDuelFeedback({ team, correct });
    setDuelStats(prev => {
      const attempts = prev.attempts + 1;
      const correctCount = prev.correct + (correct ? 1 : 0);
      const streak = correct ? prev.streak + 1 : 0;
      const bestStreak = Math.max(prev.bestStreak, streak);
      return {
        attempts,
        correct: correctCount,
        streak,
        bestStreak
      };
    });
  };

  useEffect(() => {
    if (!duelLabelCache || !Object.keys(duelLabelCache).length) return;
    setDuelHistory(prev => prev.map(entry => (
      duelLabelCache[entry.id] && entry.actualWinner !== duelLabelCache[entry.id]
        ? { ...entry, actualWinner: duelLabelCache[entry.id] }
        : entry
    )));
  }, [duelLabelCache]);

  const chooseRolesForCount = (count) => {
    const choices = [];
    const available = [...ROLE_ORDER];
    for (let i = 0; i < count; i += 1) {
      if (!available.length) {
        choices.push(ROLE_ORDER[i % ROLE_ORDER.length]);
        continue;
      }
      const [role] = available.splice(Math.floor(Math.random() * available.length), 1);
      choices.push(role);
    }
    return choices;
  };

  const buildPartialTeam = (count, used) => {
    const roles = chooseRolesForCount(count);
    const picks = [];
    roles.forEach(role => {
      const pick = pickChampion(role, used);
      if (pick) {
        picks.push(pick);
      }
    });
    return picks;
  };

  const findNextSlot = (teamPicks) => {
    for (const role of ROLE_ORDER) {
      if (!teamPicks.some(pick => pick.role === role)) {
        return role;
      }
    }
    return null;
  };

  const requestRecommendations = async (blueTeam, redTeam, nextTeam, nextRole) => {
    const payload = {
      draft_state: {
        blue_picks: blueTeam.map(p => p.champion),
        blue_roles: blueTeam.map(p => p.role),
        blue_bans: [],
        red_picks: redTeam.map(p => p.champion),
        red_roles: redTeam.map(p => p.role),
        red_bans: [],
        next_pick: nextTeam
      },
      upcoming_slots: [
        {
          slot_id: 'COACH_SLOT',
          team: nextTeam,
          role: nextRole
        }
      ],
      limit: 5
    };
    const response = await axios.post(`${apiBase}/draft/recommend`, payload);
    const slotEntry = response.data?.slots?.[0];
    if (!slotEntry) {
      throw new Error('No recommendations returned.');
    }
    return slotEntry;
  };

  const handleGeneratePickChallenge = async () => {
    if (!canRunExercises) {
      setPickError('Load champion data before running exercises.');
      return;
    }
    setPickLoading(true);
    setPickFeedback(null);
    setPickError(null);
    try {
      const used = new Set();
      const blueCount = Math.floor(Math.random() * 3) + 2; // 2-4 picks
      const redCount = Math.floor(Math.random() * 3) + 2;
      const blueTeam = buildPartialTeam(blueCount, used);
      const redTeam = buildPartialTeam(redCount, used);
      let nextTeam = Math.random() > 0.5 ? 'blue' : 'red';
      if (blueTeam.length >= 5) nextTeam = 'red';
      if (redTeam.length >= 5) nextTeam = 'blue';
      const nextRole = findNextSlot(nextTeam === 'blue' ? blueTeam : redTeam);
      const slot = await requestRecommendations(blueTeam, redTeam, nextTeam, nextRole);
      const rankedRecommendations = slot.recommendations || [];
      const optionOrder = shuffleArray(rankedRecommendations.map(rec => rec.champion));
      setPickScenario({
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        blueTeam,
        redTeam,
        nextTeam,
        nextRole,
        recommendations: rankedRecommendations,
        projection: slot.win_projection || null,
        optionOrder,
        startedAt: Date.now()
      });
    } catch (error) {
      console.error('Failed to build pick challenge', error);
      setPickError(error.message || 'Unable to build pick challenge.');
      setPickScenario(null);
    } finally {
      setPickLoading(false);
    }
  };

  const handlePickGuess = (champion) => {
    if (!pickScenario?.recommendations?.length) return;
    const [best] = pickScenario.recommendations;
    const bestRate = typeof best?.projected_team_winrate === 'number' ? best.projected_team_winrate : null;
    let positiveCandidates = [];
    if (bestRate !== null) {
      positiveCandidates = pickScenario.recommendations.filter(rec => {
        if (typeof rec.projected_team_winrate !== 'number') {
          return false;
        }
        return bestRate - rec.projected_team_winrate <= 0.005;
      });
    }
    if (!positiveCandidates.length) {
      positiveCandidates = pickScenario.recommendations.slice(0, 3);
    }
    const positiveSet = new Set(positiveCandidates.map(rec => rec.champion));
    const bestMatch = champion === best?.champion;
    const positiveMatch = positiveSet.has(champion);
    setPickFeedback({ choice: champion, bestMatch, positiveMatch, best });
    const awarded = bestMatch ? 2 : positiveMatch ? 1 : 0;
    setPickStats(prev => {
      const attempts = prev.attempts + 1;
      const perfect = prev.perfect + (bestMatch ? 1 : 0);
      const positive = prev.positive + (positiveMatch ? 1 : 0);
      const streak = bestMatch ? prev.streak + 1 : 0;
      const bestStreak = Math.max(prev.bestStreak, streak);
      const score = prev.score + awarded;
      return {
        attempts,
        perfect,
        positive,
        streak,
        bestStreak,
        score
      };
    });

    if (pickScenario) {
      const guessRec = pickScenario.recommendations.find(rec => rec.champion === champion) || null;
      const guessWinrate = typeof guessRec?.projected_team_winrate === 'number' ? guessRec.projected_team_winrate : null;
      const bestWinrate = typeof best?.projected_team_winrate === 'number' ? best.projected_team_winrate : null;
      const bestNotes = Array.isArray(best?.reasoning) ? best.reasoning.slice(0, 2) : [];
      pushPickHistory({
        id: pickScenario.id,
        timestamp: Date.now(),
        durationMs: pickScenario.startedAt ? Date.now() - pickScenario.startedAt : null,
        blueTeam: pickScenario.blueTeam,
        redTeam: pickScenario.redTeam,
        nextTeam: pickScenario.nextTeam,
        nextRole: pickScenario.nextRole,
        guess: champion,
        guessWinrate,
        bestChampion: best?.champion || null,
        bestWinrate,
        bestNotes,
        correct: bestMatch,
        partial: !bestMatch && positiveMatch,
        scoreDelta: awarded,
        projection: pickScenario.projection || null,
        recommendations: pickScenario.recommendations,
        optionOrder: pickScenario.optionOrder,
        startedAt: pickScenario.startedAt
      });
    }
  };

  const handleReviewPickHistory = (entry) => {
    if (!entry?.recommendations?.length) return;
    setPickFeedback(null);
    setPickError(null);
    setPickScenario({
      id: `${entry.id}-review-${Date.now()}`,
      blueTeam: entry.blueTeam || [],
      redTeam: entry.redTeam || [],
      nextTeam: entry.nextTeam,
      nextRole: entry.nextRole,
      recommendations: entry.recommendations,
      projection: entry.projection || null,
      optionOrder: entry.optionOrder?.length ? entry.optionOrder : entry.recommendations.map(rec => rec.champion),
      startedAt: Date.now()
    });
  };

  const renderTeamColumn = (team, label) => (
    <div className={`team-column ${team}`}>
      <div className="team-header">{label}</div>
      <ul>
        {(team === 'blue' ? duelState?.blueTeam : duelState?.redTeam)?.map(pick => (
          <li key={`${team}-${pick.role}`} className="team-entry">
            <img
              className="mini-avatar"
              src={getChampionIconUrl(pick.champion)}
              alt={pick.champion}
              onError={(event) => {
                const fallback = getChampionIconFallbackUrl(pick.champion);
                if (fallback && event.currentTarget.src !== fallback) {
                  event.currentTarget.src = fallback;
                }
              }}
            />
            <div className="team-entry-details">
              <div className="team-entry-title">
                <strong>{pick.role}:</strong> {pick.champion}
              </div>
              {championLookup[pick.champion]?.archetype && (
                <span className="champ-note">{formatLabel(championLookup[pick.champion].archetype)}</span>
              )}
            </div>
          </li>
        )) || <li>No picks generated yet.</li>}
      </ul>
    </div>
  );

  const renderPickTeam = (team, label) => {
    const picks = team === 'blue' ? pickScenario?.blueTeam : pickScenario?.redTeam;
    return (
      <div className={`team-column ${team}`}>
        <div className="team-header">{label}</div>
        <ul>
          {(picks && picks.length)
            ? picks.map((pick, idx) => (
                <li key={`${team}-${pick.role}-${idx}`} className="team-entry">
                  <img
                    className="mini-avatar"
                    src={getChampionIconUrl(pick.champion)}
                    alt={pick.champion}
                    onError={(event) => {
                      const fallback = getChampionIconFallbackUrl(pick.champion);
                      if (fallback && event.currentTarget.src !== fallback) {
                        event.currentTarget.src = fallback;
                      }
                    }}
                  />
                  <div className="team-entry-details">
                    <div className="team-entry-title">
                      <strong>{pick.role}:</strong> {pick.champion}
                    </div>
                    {championLookup[pick.champion]?.archetype && (
                      <span className="champ-note">{formatLabel(championLookup[pick.champion].archetype)}</span>
                    )}
                  </div>
                </li>
              ))
            : <li>No picks yet</li>}
        </ul>
      </div>
    );
  };

    const pickRecommendations = useMemo(() => pickScenario?.recommendations || [], [pickScenario?.recommendations]);
    const pickRecommendationMap = useMemo(() => (
      pickRecommendations.reduce((acc, rec) => {
        acc[rec.champion] = rec;
        return acc;
      }, {})
    ), [pickRecommendations]);
    const pickOptionOrder = useMemo(() => {
      if (pickScenario?.optionOrder?.length) {
        return pickScenario.optionOrder;
      }
      return pickRecommendations.map(rec => rec.champion);
    }, [pickScenario?.optionOrder, pickRecommendations]);
    const pickOptions = useMemo(() => pickOptionOrder
      .map(name => pickRecommendationMap[name] || pickRecommendations.find(rec => rec.champion === name))
      .filter(Boolean), [pickOptionOrder, pickRecommendationMap, pickRecommendations]);

  if (!canRunExercises) {
    return (
      <div className="coach-training">
        <p className="coach-notice">
          Load champion data on the Draft Assistant tab to unlock training mode.
        </p>
      </div>
    );
  }

  const duelPrediction = duelState?.analysis?.prediction;
  const matchupContext = duelState?.analysis?.matchup_context || {};
  const archetypalInsights = duelState?.analysis?.archetypal_insights || [];
  const massSimulation = matchupContext.mass_simulation || null;
  const favoredSide = matchupContext.favored || duelPrediction?.winner || 'blue';
  const duelWinnerLabel = matchupContext.favored_label || (favoredSide === 'blue' ? 'Blue' : 'Red');
  const duelUnderdogLabel = matchupContext.underdog_label || (favoredSide === 'blue' ? 'Red' : 'Blue');
  const favoredAnalysis = favoredSide === 'blue'
    ? duelState?.analysis?.blue_analysis
    : duelState?.analysis?.red_analysis;
  const underdogAnalysis = favoredSide === 'blue'
    ? duelState?.analysis?.red_analysis
    : duelState?.analysis?.blue_analysis;
  const favoredPivot = matchupContext.favored_playmaker || null;
  const underdogPivot = matchupContext.underdog_threat || null;
  const duelAccuracy = duelStats.attempts ? (duelStats.correct / duelStats.attempts) * 100 : 0;
  const pickPerfectRate = pickStats.attempts ? (pickStats.perfect / pickStats.attempts) * 100 : 0;
  const pickPositiveRate = pickStats.attempts ? (pickStats.positive / pickStats.attempts) * 100 : 0;

  const buildFavoredFallback = () => {
    const compLabel = formatLabel(favoredAnalysis?.composition_type || 'mixed');
    const archetypeLabel = favoredAnalysis?.archetypes?.length
      ? formatLabel(favoredAnalysis.archetypes[0])
      : null;
    return [
      `${duelWinnerLabel} comp leans ${compLabel} — keep forcing that style of fight.`,
      archetypeLabel ? `Play through your ${archetypeLabel} pieces to stay ahead.` : null
    ].filter(Boolean);
  };

  const buildComebackFallback = () => {
    const compLabel = formatLabel(underdogAnalysis?.composition_type || 'mixed');
    const archetypeLabel = underdogAnalysis?.archetypes?.length
      ? formatLabel(underdogAnalysis.archetypes[0])
      : null;
    return [
      `${duelUnderdogLabel} needs to drag the game into a ${compLabel} setup.`,
      archetypeLabel ? `Look for windows where your ${archetypeLabel} picks can punish missteps.` : 'Delay objectives and trade sides until a pick appears.'
    ].filter(Boolean);
  };

  const insightCandidates = (list) => (Array.isArray(list) ? list.filter(Boolean) : []);
  const favoredInsightCandidates = insightCandidates(matchupContext.favored_insights);
  const underdogInsightCandidates = insightCandidates(matchupContext.underdog_insights);
  const archetypeFavoredFallback = insightCandidates(archetypalInsights.slice(0, 3));
  const archetypeUnderdogFallback = insightCandidates(archetypalInsights.slice(3, 6));
  const duelFavoredList = (favoredInsightCandidates.length
    ? favoredInsightCandidates
    : (archetypeFavoredFallback.length ? archetypeFavoredFallback : buildFavoredFallback())).slice(0, 3);
  const duelComebackList = (underdogInsightCandidates.length
    ? underdogInsightCandidates
    : (archetypeUnderdogFallback.length ? archetypeUnderdogFallback : buildComebackFallback())).slice(0, 3);

  const formatPivotImpact = (pivot) => {
    if (!pivot) return null;
    if (typeof pivot.impact_pct === 'number') {
      return pivot.impact_pct;
    }
    if (typeof pivot.impact === 'number') {
      return pivot.impact * 100;
    }
    return null;
  };

  const renderPivotCard = (pivot, label, accent) => {
    if (!pivot?.champion) return null;
    const impactValue = formatPivotImpact(pivot);
    const impactText = typeof impactValue === 'number'
      ? `${impactValue >= 0 ? '+' : ''}${impactValue.toFixed(1)}% win impact`
      : null;
    return (
      <div className={`pivot-card ${accent}`}>
        <div className="pivot-avatar">
          <img
            src={getChampionIconUrl(pivot.champion)}
            alt={pivot.champion}
            onError={(event) => {
              const fallback = getChampionIconFallbackUrl(pivot.champion);
              if (fallback && event.currentTarget.src !== fallback) {
                event.currentTarget.src = fallback;
              }
            }}
          />
        </div>
        <div className="pivot-body">
          <div className="pivot-headline">
            <span className="pivot-label">{label}</span>
            {pivot.role && <span className="pivot-role">{pivot.role}</span>}
          </div>
          <div className="pivot-name">{pivot.champion}</div>
          {impactText && <div className="pivot-impact">{impactText}</div>}
        </div>
      </div>
    );
  };

  const renderMassSimulationChip = () => {
    if (!massSimulation || typeof massSimulation.blue_win_rate !== 'number') return null;
    const delta = typeof massSimulation.blue_delta === 'number'
      ? massSimulation.blue_delta
      : massSimulation.blue_win_rate - 0.5;
    const gamesLabel = typeof massSimulation.games === 'number' && massSimulation.games > 0
      ? `${massSimulation.games.toLocaleString()} sims`
      : null;
    return (
      <span className="projection-chip neutral">
        15M sims: {formatLabel(massSimulation.blue_comp || 'mixed')} vs {formatLabel(massSimulation.red_comp || 'mixed')}
        {' '}{formatPercent(massSimulation.blue_win_rate)} blue
        {typeof delta === 'number' ? ` (${delta >= 0 ? '+' : ''}${(delta * 100).toFixed(1)}pp)` : ''}
        {gamesLabel ? ` • ${gamesLabel}` : ''}
      </span>
    );
  };

  return (
    <div className="coach-training">
      <section className="coach-card">
        <div className="card-header">
          <div>
            <h2>Draft Duel</h2>
            <p>Guess which team wins the draft before revealing the model verdict.</p>
          </div>
          <button className="ghost" onClick={handleGenerateDuel} disabled={duelLoading}>
            {duelLoading ? 'Building...' : 'New Duel'}
          </button>
        </div>
        <div className="stats-bar">
          <div className="stat-block">
            <span className="stats-label">Attempts</span>
            <span className="stats-value">{duelStats.attempts}</span>
          </div>
          <div className="stat-block">
            <span className="stats-label">Accuracy</span>
            <span className="stats-value">{duelAccuracy.toFixed(0)}%</span>
          </div>
          <div className="stat-block">
            <span className="stats-label">Streak</span>
            <span className="stats-value">{duelStats.streak}/{duelStats.bestStreak}</span>
          </div>
          <button className="stats-reset" onClick={resetDuelStats} disabled={!duelStats.attempts}>
            Reset
          </button>
        </div>

        {duelError && <div className="error-banner">{duelError}</div>}

        {duelState ? (
          <div className="duel-grid">
            {renderTeamColumn('blue', 'Blue Team')}
            <div className="guess-panel">
              <p>Which draft is ahead?</p>
              <div className="guess-buttons">
                <button onClick={() => handleDuelGuess('blue')} disabled={duelLoading}>Blue Wins</button>
                <button onClick={() => handleDuelGuess('red')} disabled={duelLoading}>Red Wins</button>
              </div>
              {duelFeedback && duelPrediction && (
                <>
                  <div className={`feedback ${duelFeedback.correct ? 'success' : 'fail'}`}>
                    {duelFeedback.correct ? 'Correct!' : 'Not quite.'}
                    <div className="feedback-detail">
                      Blue {formatPercent(duelPrediction.blue_win_probability)} • Red {formatPercent(duelPrediction.red_win_probability)}
                    </div>
                  </div>
                  {(typeof matchupContext.favored_winrate_pct === 'number' || typeof matchupContext.confidence === 'number') && (
                    <div className="projection-chips">
                      {typeof matchupContext.favored_winrate_pct === 'number' && (
                        <span className="projection-chip primary">
                          Favored win chance {matchupContext.favored_winrate_pct.toFixed(1)}%
                        </span>
                      )}
                      {typeof matchupContext.confidence === 'number' && matchupContext.confidence > 0 && (
                        <span className="projection-chip">
                          Model confidence {(matchupContext.confidence * 100).toFixed(1)}%
                        </span>
                      )}
                      {renderMassSimulationChip()}
                    </div>
                  )}
                  {duelState && (
                    <div className="label-outcome">
                      <span className="label-text">Log actual result for calibration:</span>
                      <div className="label-buttons">
                        <button
                          type="button"
                          onClick={() => labelDuelOutcome('blue')}
                          disabled={labelingOutcome || duelState.actualWinner === 'blue'}
                        >
                          Blue won
                        </button>
                        <button
                          type="button"
                          onClick={() => labelDuelOutcome('red')}
                          disabled={labelingOutcome || duelState.actualWinner === 'red'}
                        >
                          Red won
                        </button>
                      </div>
                      {duelState.actualWinner && (
                        <span className="label-status">
                          Recorded {duelState.actualWinner === 'blue' ? 'Blue' : 'Red'} victory — thanks!
                        </span>
                      )}
                    </div>
                  )}
                  <div className="duel-explanation-grid">
                    <div className={`duel-explanation favored ${duelPrediction.winner}`}>
                      <h5>Why {duelWinnerLabel} is ahead</h5>
                      <ul>
                        {duelFavoredList.map((insight, idx) => (
                          <li key={`favored-${idx}`}>{insight}</li>
                        ))}
                      </ul>
                    </div>
                    <div className={`duel-explanation comeback ${duelPrediction.winner === 'blue' ? 'red' : 'blue'}`}>
                      <h5>{duelUnderdogLabel} win condition</h5>
                      <ul>
                        {duelComebackList.map((insight, idx) => (
                          <li key={`comeback-${idx}`}>{insight}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                  {(favoredPivot || underdogPivot) && (
                    <div className="duel-pivot-grid">
                      {renderPivotCard(favoredPivot, `${duelWinnerLabel} playmaker`, duelPrediction.winner)}
                      {renderPivotCard(underdogPivot, `${duelUnderdogLabel} threat`, duelPrediction.winner === 'blue' ? 'red' : 'blue')}
                    </div>
                  )}
                </>
              )}
            </div>
            {renderTeamColumn('red', 'Red Team')}
          </div>
        ) : (
          <p className="coach-placeholder">Generate a duel to start testing.</p>
        )}

        {duelHistory.length > 0 && (
          <div className="duel-history">
            <h4>Recent scenarios</h4>
            <ul>
              {duelHistory.map(entry => (
                <li key={entry.id}>
                  <div className="history-header">
                    <span className={`history-winner ${entry.winner.toLowerCase()}`}>
                      {entry.winner} favored
                    </span>
                    {typeof entry.winrate === 'number' && (
                      <span className="history-metric">{entry.winrate.toFixed(1)}%</span>
                    )}
                  </div>
                  <div className="history-footer">
                    {typeof entry.confidence === 'number' && (
                      <span className="history-confidence">Confidence {entry.confidence.toFixed(1)}%</span>
                    )}
                    {entry.note && <span className="history-note">{entry.note}</span>}
                  </div>
                  <div className="history-actions">
                    <button
                      type="button"
                      onClick={() => handleRematch(entry)}
                      disabled={duelLoading}
                      aria-label="Run this duel again"
                    >
                      Rematch
                    </button>
                  </div>
                  {entry.actualWinner ? (
                    <div className="history-label-status">
                      Logged {entry.actualWinner === 'blue' ? 'Blue' : 'Red'} win
                    </div>
                  ) : (
                    <div className="history-labels">
                      <span>Log actual result:</span>
                      <div className="history-label-buttons">
                        <button
                          type="button"
                          onClick={() => labelHistoryOutcome(entry, 'blue')}
                          disabled={historyLabelLoading[entry.id]}
                        >
                          Blue won
                        </button>
                        <button
                          type="button"
                          onClick={() => labelHistoryOutcome(entry, 'red')}
                          disabled={historyLabelLoading[entry.id]}
                        >
                          Red won
                        </button>
                      </div>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="coach-card">
        <div className="card-header">
          <div>
            <h2>Pick Challenge</h2>
            <p>Given an in-progress draft, choose the optimal next pick.</p>
          </div>
          <button className="ghost" onClick={handleGeneratePickChallenge} disabled={pickLoading}>
            {pickLoading ? 'Building...' : 'New Scenario'}
          </button>
        </div>
        <div className="stats-bar">
          <div className="stat-block">
            <span className="stats-label">Score</span>
            <span className="stats-value">{pickStats.score}</span>
          </div>
          <div className="stat-block">
            <span className="stats-label">Attempts</span>
            <span className="stats-value">{pickStats.attempts}</span>
          </div>
          <div className="stat-block">
            <span className="stats-label">Perfect Rate</span>
            <span className="stats-value">{pickPerfectRate.toFixed(0)}%</span>
          </div>
          <div className="stat-block">
            <span className="stats-label">Positive Rate</span>
            <span className="stats-value">{pickPositiveRate.toFixed(0)}%</span>
          </div>
          <div className="stat-block">
            <span className="stats-label">Streak</span>
            <span className="stats-value">{pickStats.streak}/{pickStats.bestStreak}</span>
          </div>
          <button
            className="stats-reset"
            onClick={() => {
              resetPickStats();
              clearPickHistory();
            }}
            disabled={!pickStats.attempts && !pickHistory.length}
          >
            Reset
          </button>
        </div>

        {pickError && <div className="error-banner">{pickError}</div>}

        {pickScenario ? (
          <>
            <div className="duel-grid">
              {renderPickTeam('blue', 'Blue Team')}
              <div className="guess-panel">
                <p>Next pick: <strong>{pickScenario.nextTeam.toUpperCase()}</strong> • {pickScenario.nextRole || 'FLEX'}</p>
                <div className="options-grid">
                  {pickOptions.length ? pickOptions.map(rec => (
                    <button
                      key={rec.champion}
                      onClick={() => handlePickGuess(rec.champion)}
                      title={rec.reasoning?.[0] || 'Model insight'}
                      aria-label={`Pick ${rec.champion}`}
                    >
                      <img
                        className="option-avatar"
                        src={getChampionIconUrl(rec.champion)}
                        alt={rec.champion}
                        onError={(event) => {
                          const fallback = getChampionIconFallbackUrl(rec.champion);
                          if (fallback && event.currentTarget.src !== fallback) {
                            event.currentTarget.src = fallback;
                          }
                        }}
                      />
                      <span className="option-label">{rec.champion}</span>
                    </button>
                  )) : <span className="coach-placeholder">Model returned no candidates.</span>}
                </div>
                {pickFeedback && pickScenario && (
                  <div className={`feedback ${pickFeedback.bestMatch ? 'success' : pickFeedback.positiveMatch ? 'warn' : 'fail'}`}>
                    {pickFeedback.bestMatch && 'Perfect — you matched the top pick!'}
                    {!pickFeedback.bestMatch && pickFeedback.positiveMatch && 'Solid pick — within touching distance of the optimal win rate.'}
                    {!pickFeedback.bestMatch && !pickFeedback.positiveMatch && 'Model prefers a different direction.'}
                    {pickFeedback.best?.projected_team_winrate && (
                      <div className="feedback-detail">
                        Best: {pickFeedback.best.champion} → {(pickFeedback.best.projected_team_winrate * 100).toFixed(1)}%
                      </div>
                    )}
                    {pickFeedback.best?.reasoning?.length && (
                      <ul className="reasoning-list">
                        {pickFeedback.best.reasoning.slice(0, 2).map((note, idx) => (
                          <li key={idx}>{note}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
              {renderPickTeam('red', 'Red Team')}
            </div>
          </>
        ) : (
          <p className="coach-placeholder">Generate a pick scenario to practice recommendations.</p>
        )}

        {pickHistory.length > 0 && (
          <div className="pick-history">
            <h4>Recent Pick Drills</h4>
            <ul>
              {pickHistory.map(entry => {
                const outcomeClass = entry.correct ? 'perfect' : entry.partial ? 'positive' : 'miss';
                const outcomeLabel = entry.correct ? 'Perfect read' : entry.partial ? 'Positive pick' : 'Missed line';
                const timeLabel = formatTimeLabel(entry.timestamp);
                const durationLabel = formatDurationLabel(entry.durationMs);
                const bestNotes = entry.bestNotes || [];
                return (
                  <li key={entry.id}>
                    <div className="pick-history-header">
                      <span className={`pick-outcome-chip ${outcomeClass}`}>{outcomeLabel}</span>
                      <span className="pick-history-meta">
                        {timeLabel}
                        {durationLabel ? ` • ${durationLabel}` : ''}
                      </span>
                    </div>
                    <div className="pick-history-body">
                      <div className="pick-history-slot">
                        {entry.nextTeam?.toUpperCase()} • {entry.nextRole || 'FLEX'}
                      </div>
                      <div className="pick-history-choices">
                        <span className="choice-label">You</span>
                        <span>{entry.guess || '—'}</span>
                        <span className="choice-label best">Optimal</span>
                        <span>{entry.bestChampion || '—'}</span>
                      </div>
                      <div className="pick-history-teams">
                        <span>Blue: {formatTeamPreview(entry.blueTeam)}</span>
                        <span>Red: {formatTeamPreview(entry.redTeam)}</span>
                      </div>
                      {(entry.bestWinrate !== null || entry.guessWinrate !== null) && (
                        <div className="pick-history-winrates">
                          {typeof entry.bestWinrate === 'number' && (
                            <span>Optimal {(entry.bestWinrate * 100).toFixed(1)}%</span>
                          )}
                          {typeof entry.guessWinrate === 'number' && (
                            <span>Your pick {(entry.guessWinrate * 100).toFixed(1)}%</span>
                          )}
                        </div>
                      )}
                    </div>
                    {bestNotes.length > 0 && (
                      <ul className="pick-history-notes">
                        {bestNotes.map((note, idx) => (
                          <li key={`${entry.id}-note-${idx}`}>{note}</li>
                        ))}
                      </ul>
                    )}
                    <div className="pick-history-actions">
                      <button
                        type="button"
                        onClick={() => handleReviewPickHistory(entry)}
                        disabled={pickLoading}
                      >
                        Review scenario
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </section>
    </div>
  );
};

export default CoachTraining;
