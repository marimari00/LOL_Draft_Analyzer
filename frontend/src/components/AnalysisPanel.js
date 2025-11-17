import React, { useEffect, useMemo, useState } from 'react';
import './AnalysisPanel.css';
import { getChampionIconUrl, getChampionIconFallbackUrl } from '../utils/championAssets';

const COMPOSITION_GUIDES = {
  front_to_back: 'frontline for carries, set vision first, and kite fights when cooldowns are down',
  dive: 'chain engages together, crash on backline, and end fights before the reset tools arrive',
  poke: 'chip towers, deny engages with spacing, and only commit once enemies drop to half HP',
  skirmish: 'fight in small numbers, keep tempo with constant skirmishes, and never let the map reset',
  split_push: 'keep a side lane pushed, drag opponents across the map, and punish slow rotations',
  pick: 'fish for fog-of-war catches, instantly convert into objectives, then reset vision again',
  mixed: 'stay flexible, trade sides instead of mirroring, and lean into the lanes that get priority'
};

const formatLabel = (value = '') => value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

const safeArray = (value) => (Array.isArray(value) ? value : []);

const countMatchingArchetypes = (distribution = {}, keywords = []) => (
  Object.entries(distribution).reduce((sum, [arch, count]) => (
    keywords.some(keyword => arch.includes(keyword)) ? sum + count : sum
  ), 0)
);

const buildDistributionEntries = (analysis) => {
  const distribution = analysis?.archetype_distribution || {};
  const total = Object.values(distribution).reduce((acc, val) => acc + val, 0) || 1;
  return Object.entries(distribution)
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => ({
      name,
      label: formatLabel(name),
      count,
      percent: (count / total) * 100
    }));
};

const useMediaQuery = (query) => {
  const getMatch = () => {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return true;
    }
    return window.matchMedia(query).matches;
  };

  const [matches, setMatches] = useState(getMatch);

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return undefined;
    }
    const mediaQueryList = window.matchMedia(query);
    const handler = (event) => setMatches(event.matches);
    if (mediaQueryList.addEventListener) {
      mediaQueryList.addEventListener('change', handler);
    } else {
      mediaQueryList.addListener(handler);
    }
    setMatches(mediaQueryList.matches);
    return () => {
      if (mediaQueryList.removeEventListener) {
        mediaQueryList.removeEventListener('change', handler);
      } else {
        mediaQueryList.removeListener(handler);
      }
    };
  }, [query]);

  return matches;
};

const summarizeTeam = (analysis = {}) => {
  if (!analysis || typeof analysis !== 'object') {
    return null;
  }

  const compositionKey = analysis.composition_type || 'mixed';
  const distributionEntries = buildDistributionEntries(analysis);
  const archetypeDistribution = analysis.archetype_distribution || {};
  const damageTypes = safeArray(analysis.damage_types);
  const rangeProfile = safeArray(analysis.range_profile);
  const mobilityProfile = safeArray(analysis.mobility_profile);
  const ccProfile = safeArray(analysis.cc_profile);
  const archetypes = safeArray(analysis.archetypes);

  const hasMagic = damageTypes.some(type => type.includes('magic'));
  const hasPhysical = damageTypes.some(type => type.includes('physical'));

  const summary = {
    compositionKey,
    composition: formatLabel(compositionKey),
    distributionEntries,
    archetypes,
    archetypeDistribution,
    damageTypes,
    rangeProfile,
    mobilityProfile,
    ccProfile,
    engageSources: countMatchingArchetypes(archetypeDistribution, ['engage', 'diver', 'assassin']),
    rangeThreats: rangeProfile.filter(entry => entry.includes('range_long') || entry.includes('range_artillery') || entry.includes('poke')).length,
    hardCC: ccProfile.filter(entry => entry.includes('hard')).length,
    sustainSources: countMatchingArchetypes(archetypeDistribution, ['enchanter', 'warden', 'juggernaut']),
    peelSources: countMatchingArchetypes(archetypeDistribution, ['enchanter', 'catcher', 'warden']),
    mobilityCount: mobilityProfile.length,
    hasMagic,
    hasPhysical
  };

  summary.hasMixedDamage = summary.hasMagic && summary.hasPhysical;
  return summary;
};

const buildTeamSnapshot = (summary) => {
  if (!summary) {
    return [];
  }

  const describeDamage = () => {
    if (summary.hasMixedDamage) return 'Mixed damage profile';
    if (summary.hasMagic && !summary.hasPhysical) return 'Magic leaning';
    if (summary.hasPhysical && !summary.hasMagic) return 'Physical leaning';
    return 'Needs damage diversity';
  };

  const formatList = (items) => (items.length ? items.map(formatLabel).join(', ') : 'No data yet');

  return [
    {
      label: 'Composition',
      value: summary.composition,
      detail: formatList(summary.archetypes)
    },
    {
      label: 'Damage Profile',
      value: describeDamage(),
      detail: formatList(summary.damageTypes)
    },
    {
      label: 'Engage & Peel',
      value: `${summary.engageSources} engage • ${summary.peelSources} peel`,
      detail: `Hard CC tools: ${summary.hardCC}`
    },
    {
      label: 'Range & Mobility',
      value: `${summary.rangeThreats} range threats • ${summary.mobilityCount} mobile`,
      detail: formatList(summary.rangeProfile)
    }
  ];
};

const buildCoachNotes = (summary) => {
  if (!summary) return [];
  const notes = [];

  if (summary.engageSources >= 2) {
    notes.push('Multiple engage starters — secure deep vision and force on your timings.');
  } else if (summary.engageSources === 0) {
    notes.push('No true engage; play for wave pressure, poke, or flanks before committing.');
  }

  if (summary.peelSources === 0) {
    notes.push('Backline has no peel pieces. Track divers and hold defensive summoners.');
  } else if (summary.peelSources >= 2) {
    notes.push('Layer peel tools to keep carries upright through enemy dive windows.');
  }

  if (!summary.hasMixedDamage) {
    notes.push('Damage is skewed. Accelerate before opponents stack the correct resistances.');
  }

  if (summary.rangeThreats >= 2) {
    notes.push('You outrange opponents — chip objectives before forcing a full fight.');
  } else if (summary.mobilityCount >= 3) {
    notes.push('High mobility core. Look for flank wards and cross-map collapses.');
  }

  const identityGuide = COMPOSITION_GUIDES[summary.compositionKey];
  if (identityGuide) {
    notes.push(`Identity check: ${identityGuide}.`);
  }

  return notes.slice(0, 4);
};

const buildPickDebtItems = (summary) => {
  if (!summary) return [];
  const debts = [];
  const addDebt = (id, severity, text, hint) => {
    debts.push({ id, severity, text, hint });
  };

  if (summary.engageSources === 0) {
    addDebt('engage', 'critical', 'Need a reliable engage starter', 'Draft a tank support/jungle with hard CC.');
  } else if (summary.engageSources === 1 && summary.compositionKey === 'dive') {
    addDebt('secondary-engage', 'warning', 'Dive comp is single-threaded', 'Add a second diver or catcher to keep pressure.');
  }

  if (!summary.hasMixedDamage) {
    addDebt(
      'damage-mix',
      'warning',
      summary.hasMagic ? 'Add a strong physical threat' : 'Add a credible magic threat',
      'Force opponents to split their defensive items.'
    );
  }

  if (summary.peelSources === 0 && summary.compositionKey === 'front_to_back') {
    addDebt('peel', 'critical', 'Front-to-back needs peel', 'Secure an enchanter/warden to protect carries.');
  }

  if (summary.rangeThreats < 1 && summary.compositionKey === 'poke') {
    addDebt('poke', 'warning', 'Poke win-con missing artillery threat', 'Lock an artillery mage or long-range marksman.');
  }

  if (summary.sustainSources === 0 && summary.compositionKey === 'front_to_back') {
    addDebt('sustain', 'warning', 'No sustain tools for long fights', 'Consider shielding/healing support or bruiser.');
  }

  return debts;
};

const buildPivotNote = (pivot, label, context) => {
  if (!pivot) return '';
  const swing = typeof pivot.impact_pct === 'number'
    ? pivot.impact_pct.toFixed(1)
    : typeof pivot.impact === 'number'
      ? (pivot.impact * 100).toFixed(1)
      : null;

  if (!swing) {
    return `${pivot.champion} anchors ${label} game plan.`;
  }

  if (context === 'favored') {
    return `${pivot.champion} keeps ${label} ahead — removing them drops win chance by ${swing} pts.`;
  }
  return `${pivot.champion} is the comeback lever — when they pop off, win chance swings +${swing} pts.`;
};

const ChampionPivot = ({ pivot, label, accent = 'blue' }) => {
  const championName = pivot?.champion || '';
  const [imgSrc, setImgSrc] = useState(championName ? getChampionIconUrl(championName) : '');

  useEffect(() => {
    if (!championName) return;
    setImgSrc(getChampionIconUrl(championName));
  }, [championName]);

  if (!pivot) {
    return null;
  }

  const impactText = typeof pivot.impact_pct === 'number'
    ? `${pivot.impact_pct.toFixed(1)} pt swing`
    : typeof pivot.impact === 'number'
      ? `${(pivot.impact * 100).toFixed(1)} pt swing`
      : null;

  return (
    <div className={`champion-pivot ${accent}`}>
      <div className="pivot-avatar">
        <img
          src={imgSrc}
          alt={pivot.champion}
          onError={() => setImgSrc(getChampionIconFallbackUrl(pivot.champion))}
        />
      </div>
      <div className="pivot-body">
        <div className="pivot-heading">
          <span>{label}</span>
          {pivot.role && <span className="pivot-role">{pivot.role}</span>}
        </div>
        <div className="pivot-name">{pivot.champion}</div>
        {impactText && <div className="pivot-impact">{impactText}</div>}
        {pivot.note && <div className="pivot-note">{pivot.note}</div>}
      </div>
    </div>
  );
};

const DistributionBar = ({ entries = [], team = 'blue' }) => {
  if (!entries.length) {
    return <div className="distribution-bar empty">No archetype data</div>;
  }
  return (
    <div className={`distribution-bar ${team}`}>
      {entries.map(entry => (
        <div
          key={entry.name}
          className="distribution-segment"
          style={{ width: `${entry.percent}%` }}
          title={`${entry.label} • ${entry.count} pick${entry.count > 1 ? 's' : ''}`}
        >
          <span>{entry.label}</span>
        </div>
      ))}
    </div>
  );
};

const buildComparisons = (blueSummary, redSummary) => {
  if (!blueSummary || !redSummary) return [];
  const comparisons = [];

  const evaluateMetric = (key, label, formatter, minDiff = 1) => {
    const blueValue = blueSummary[key] || 0;
    const redValue = redSummary[key] || 0;
    const diff = blueValue - redValue;
    if (Math.abs(diff) < minDiff) return;
    const leader = diff > 0 ? 'blue' : 'red';
    const leadValue = diff > 0 ? blueValue : redValue;
    const trailValue = diff > 0 ? redValue : blueValue;
    comparisons.push({
      team: leader,
      text: formatter(leader, leadValue, trailValue, label)
    });
  };

  evaluateMetric('engageSources', 'engage starters', (team, lead, trail) => (
    `${team === 'blue' ? 'Blue' : 'Red'} threatens ${lead} engage opener${lead > 1 ? 's' : ''} (${trail} on the other side).`
  ));

  evaluateMetric('rangeThreats', 'range threats', (team, lead, trail) => (
    `${team === 'blue' ? 'Blue' : 'Red'} outranges the opponent (${lead} long-range champions vs ${trail}).`
  ));

  evaluateMetric('hardCC', 'hard CC tools', (team, lead, trail) => (
    `${team === 'blue' ? 'Blue' : 'Red'} brings ${lead} hard CC tool${lead > 1 ? 's' : ''} (${trail} for the opponent).`
  ));

  evaluateMetric('sustainSources', 'peel/sustain', (team, lead, trail) => (
    `${team === 'blue' ? 'Blue' : 'Red'} protects carries better (${lead} peel piece${lead > 1 ? 's' : ''} vs ${trail}).`
  ));

  evaluateMetric('mobilityCount', 'mobility threats', (team, lead, trail) => (
    `${team === 'blue' ? 'Blue' : 'Red'} has ${lead} mobility pieces to reach targets (${trail} on foe).`
  ), 2);

  return comparisons;
};

const buildAdvantageNarrative = (favoredSummary, favoredLabel, underSummary, underLabel) => {
  if (!favoredSummary || !underSummary) return [];
  const lines = [];
  const compLine = COMPOSITION_GUIDES[favoredSummary.compositionKey];
  if (compLine) {
    lines.push(`${favoredLabel} drafted ${favoredSummary.composition} — they win when they ${compLine}`);
  }

  if (favoredSummary.engageSources > underSummary.engageSources && favoredSummary.engageSources >= 2) {
    lines.push(`${favoredLabel} control fight starts with ${favoredSummary.engageSources} engage tools; ${underLabel} must wait for mistakes or picks (only ${underSummary.engageSources} engage starter${underSummary.engageSources > 1 ? 's' : ''}).`);
  } else if (favoredSummary.engageSources > underSummary.engageSources) {
    lines.push(`${favoredLabel} have cleaner engage windows (${favoredSummary.engageSources} vs ${underSummary.engageSources}), so they can force ${underLabel} into reactionary plays.`);
  }

  if (favoredSummary.hasMixedDamage && !underSummary.hasMixedDamage) {
    const underType = !underSummary.hasMagic ? 'armor' : 'MR';
    lines.push(`${favoredLabel} force split item builds with mixed damage; ${underLabel} can only stack ${underType} and remain vulnerable elsewhere.`);
  } else if (!favoredSummary.hasMixedDamage && favoredSummary.rangeThreats >= 2) {
    lines.push(`${favoredLabel} have ${favoredSummary.rangeThreats} long-range poke champions to chip towers and zone before fights even start.`);
  }

  if (favoredSummary.rangeThreats > underSummary.rangeThreats && favoredSummary.rangeThreats >= 2) {
    lines.push(`${favoredLabel} outrange ${underLabel} significantly (${favoredSummary.rangeThreats} long-range vs ${underSummary.rangeThreats}), letting them chip objectives and force engages on their terms.`);
  }

  if (favoredSummary.peelSources > underSummary.peelSources && favoredSummary.peelSources >= 1) {
    lines.push(`${favoredLabel} protect their carries with ${favoredSummary.peelSources} peel piece${favoredSummary.peelSources > 1 ? 's' : ''}; ${underLabel} divers will struggle to reach backline targets.`);
  }

  if (favoredSummary.hardCC > underSummary.hardCC && favoredSummary.hardCC >= 2) {
    lines.push(`${favoredLabel} chain ${favoredSummary.hardCC} hard CC tools to lock down priority targets; ${underLabel} need cleanse/QSS or perfect spacing.`);
  }

  if (favoredSummary.mobilityCount > underSummary.mobilityCount && favoredSummary.mobilityCount >= 2) {
    lines.push(`${favoredLabel} threaten flanks with ${favoredSummary.mobilityCount} mobile champion${favoredSummary.mobilityCount > 1 ? 's' : ''}; ${underLabel} must maintain vision control or risk getting picked off-angle.`);
  }

  if (lines.length < 2) {
    const fallbackNotes = buildCoachNotes(favoredSummary).filter(note =>
      !note.includes('play for wave pressure') && !note.includes('No true engage')
    );
    lines.push(...fallbackNotes.slice(0, 3 - lines.length));
  }

  return lines.slice(0, 4);
};

const buildComebackNarrative = (favoredSummary, favoredLabel, underSummary, underLabel) => {
  if (!favoredSummary || !underSummary) return [];
  const lines = [];
  const compLine = COMPOSITION_GUIDES[underSummary.compositionKey];
  if (compLine) {
    lines.push(`${underLabel} need to execute ${underSummary.composition} properly: they must ${compLine}`);
  }

  if (underSummary.engageSources < favoredSummary.engageSources && favoredSummary.engageSources >= 2) {
    lines.push(`${underLabel} trail engage tools (${underSummary.engageSources} vs ${favoredSummary.engageSources}), so they should bait around key cooldowns or punish ${favoredLabel}'s overextensions rather than forcing blind fights.`);
  } else if (underSummary.engageSources < favoredSummary.engageSources) {
    lines.push(`${underLabel} must create picks or flanks because ${favoredLabel} control standard 5v5 starts (${favoredSummary.engageSources} engage vs ${underSummary.engageSources}).`);
  }

  if (!underSummary.hasMixedDamage && favoredSummary.hasMixedDamage) {
    const underType = !underSummary.hasMagic ? 'physical' : 'magic';
    lines.push(`${underLabel} deal mostly ${underType} damage; they need early leads before ${favoredLabel} stack the right resistances and neutralize their threats.`);
  } else if (!underSummary.hasMixedDamage) {
    lines.push(`${underLabel} lack mixed damage, so ${favoredLabel} can itemize greedily. ${underLabel} must snowball lanes before defensive scaling kicks in.`);
  }

  if (underSummary.rangeThreats < favoredSummary.rangeThreats && favoredSummary.rangeThreats >= 2) {
    lines.push(`${underLabel} will bleed towers to ${favoredLabel}'s poke (${favoredSummary.rangeThreats} long-range champions); they should force scrappy fights off waves to avoid slow sieges.`);
  }

  if (underSummary.peelSources < favoredSummary.engageSources && favoredSummary.engageSources >= 2) {
    lines.push(`${underLabel} have limited peel (${underSummary.peelSources} tool${underSummary.peelSources !== 1 ? 's' : ''}) against ${favoredLabel}'s dive; stopwatches, defensive vision, and split pressure become mandatory.`);
  } else if (underSummary.peelSources === 0 && favoredSummary.mobilityCount >= 2) {
    lines.push(`${underLabel} lack backline protection against ${favoredSummary.mobilityCount} mobile threats; carries need perfect positioning or the fight collapses instantly.`);
  }

  if (underSummary.mobilityCount < favoredSummary.mobilityCount && favoredSummary.mobilityCount >= 2) {
    lines.push(`${underLabel} cannot match ${favoredLabel}'s flank threat (${favoredSummary.mobilityCount} mobile champions vs ${underSummary.mobilityCount}); deep wards and grouped farming are critical to avoid isolated deaths.`);
  }

  if (underSummary.hardCC < favoredSummary.hardCC && favoredSummary.hardCC >= 2) {
    lines.push(`${underLabel} bring less hard CC (${underSummary.hardCC} vs ${favoredSummary.hardCC}), making it harder to lock priority targets; they rely on kiting and poke rather than setups.`);
  }

  if (lines.length < 2) {
    const fallbackNotes = buildCoachNotes(underSummary).filter(note =>
      note.includes('flank') || note.includes('poke') || note.includes('No true engage')
    );
    lines.push(...fallbackNotes.slice(0, 3 - lines.length));
  }

  return lines.slice(0, 4);
};

const AnalysisPanel = ({ analysis }) => {
  const blueSummary = useMemo(() => (
    analysis ? summarizeTeam(analysis.blue_analysis) : null
  ), [analysis]);
  const redSummary = useMemo(() => (
    analysis ? summarizeTeam(analysis.red_analysis) : null
  ), [analysis]);
  const comparisonNarrative = useMemo(() => buildComparisons(blueSummary, redSummary), [blueSummary, redSummary]);
  const isDesktopLayout = useMediaQuery('(min-width: 1200px)');
  const [collapsedSections, setCollapsedSections] = useState({ blue: false, red: false });

  useEffect(() => {
    setCollapsedSections(prev => {
      const next = { blue: !isDesktopLayout, red: !isDesktopLayout };
      if (prev.blue === next.blue && prev.red === next.red) {
        return prev;
      }
      return next;
    });
  }, [isDesktopLayout]);

  const toggleSection = (team) => {
    setCollapsedSections(prev => ({ ...prev, [team]: !prev[team] }));
  };

  if (!analysis) return null;

  const {
    prediction,
    blue_analysis,
    red_analysis,
    archetypal_insights = [],
    matchup_context: matchupContext = {}
  } = analysis;

  if (!prediction) {
    return null;
  }

  const favoredLabel = matchupContext.favored_label || (prediction.winner === 'blue' ? 'Blue' : 'Red');
  const underdogLabel = matchupContext.underdog_label || (prediction.winner === 'blue' ? 'Red' : 'Blue');
  const favoredSide = matchupContext.favored || prediction.winner;
  const underdogSide = favoredSide === 'blue' ? 'red' : 'blue';

  const favoredWinratePct = typeof matchupContext.favored_winrate_pct === 'number'
    ? matchupContext.favored_winrate_pct
    : null;
  const simulatedWinratePct = typeof matchupContext.simulated_winrate_pct === 'number'
    ? matchupContext.simulated_winrate_pct
    : null;
  const contextConfidencePct = typeof matchupContext.confidence === 'number'
    ? matchupContext.confidence * 100
    : null;
  const showMatchupChips = (
    favoredWinratePct !== null ||
    simulatedWinratePct !== null ||
    (contextConfidencePct !== null && contextConfidencePct > 0)
  );

  const resolvedBlueSummary = blueSummary || summarizeTeam(blue_analysis);
  const resolvedRedSummary = redSummary || summarizeTeam(red_analysis);
  const blueDebts = buildPickDebtItems(resolvedBlueSummary);
  const redDebts = buildPickDebtItems(resolvedRedSummary);
  const blueCollapsed = collapsedSections.blue;
  const redCollapsed = collapsedSections.red;

  const favoredComparisons = comparisonNarrative.filter(item => item.team === prediction.winner);
  const unfavoredComparisons = comparisonNarrative.filter(item => item.team !== prediction.winner);

  const defaultFavoredNarrative = favoredComparisons.map(item => item.text);
  const defaultUnderdogNarrative = unfavoredComparisons.map(item => item.text);

  const favoredResolvedSummary = favoredSide === 'blue' ? resolvedBlueSummary : resolvedRedSummary;
  const underdogSummary = favoredSide === 'blue' ? resolvedRedSummary : resolvedBlueSummary;

  const autoFavoredNarrative = buildAdvantageNarrative(favoredResolvedSummary, favoredLabel, underdogSummary, underdogLabel);
  const autoUnderdogNarrative = buildComebackNarrative(favoredResolvedSummary, favoredLabel, underdogSummary, underdogLabel);

  const favoredNarrative = (matchupContext.favored_insights && matchupContext.favored_insights.length)
    ? matchupContext.favored_insights
    : (defaultFavoredNarrative.length ? defaultFavoredNarrative : (autoFavoredNarrative.length ? autoFavoredNarrative : archetypal_insights));
  const underdogNarrative = (matchupContext.underdog_insights && matchupContext.underdog_insights.length)
    ? matchupContext.underdog_insights
    : (defaultUnderdogNarrative.length ? defaultUnderdogNarrative : (autoUnderdogNarrative.length ? autoUnderdogNarrative : archetypal_insights));

  const blueSnapshot = buildTeamSnapshot(resolvedBlueSummary);
  const redSnapshot = buildTeamSnapshot(resolvedRedSummary);

  const favoredPlaymaker = matchupContext.favored_playmaker
    ? {
        ...matchupContext.favored_playmaker,
        note: buildPivotNote(matchupContext.favored_playmaker, favoredLabel, 'favored')
      }
    : null;
  const underdogThreat = matchupContext.underdog_threat
    ? {
        ...matchupContext.underdog_threat,
        note: buildPivotNote(matchupContext.underdog_threat, underdogLabel, 'underdog')
      }
    : null;

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

        {showMatchupChips && (
          <div className="favored-chips">
            {favoredWinratePct !== null && (
              <span className="favored-chip primary">
                Favored win chance {favoredWinratePct.toFixed(1)}%
              </span>
            )}
            {simulatedWinratePct !== null && (
              <span className="favored-chip">
                Simulated win chance {simulatedWinratePct.toFixed(1)}%
              </span>
            )}
            {contextConfidencePct !== null && contextConfidencePct > 0 && (
              <span className="favored-chip">
                Model confidence {contextConfidencePct.toFixed(1)}%
              </span>
            )}
          </div>
        )}
      </div>

      <div className="composition-details">
        <div className={`comp-column ${blueCollapsed ? 'collapsed' : ''}`}>
          <div className="comp-header">
            <div className="comp-header-main">
              <h4 className="blue-header">🔵 Blue Composition</h4>
              <span className="comp-type-pill">{resolvedBlueSummary?.composition}</span>
            </div>
            <button
              type="button"
              className="comp-collapse-toggle"
              onClick={() => toggleSection('blue')}
              aria-expanded={!blueCollapsed}
              aria-controls="blue-comp-body"
            >
              {blueCollapsed ? 'Expand' : 'Collapse'}
            </button>
          </div>
          <div className="comp-body" id="blue-comp-body" hidden={blueCollapsed}>
            <DistributionBar entries={resolvedBlueSummary?.distributionEntries} team="blue" />
            <div className="team-snapshot">
              {blueSnapshot.map((item, idx) => (
                <div key={`blue-snap-${idx}`} className="snapshot-row">
                  <div className="snapshot-label">{item.label}</div>
                  <div className="snapshot-value">{item.value}</div>
                  {item.detail && <div className="snapshot-detail">{item.detail}</div>}
                </div>
              ))}
            </div>
            <div className="coach-notes">
              {buildCoachNotes(resolvedBlueSummary).map((note, idx) => (
                <div key={idx} className="coach-note">{note}</div>
              ))}
            </div>
          </div>
        </div>

        <div className={`comp-column ${redCollapsed ? 'collapsed' : ''}`}>
          <div className="comp-header">
            <div className="comp-header-main">
              <h4 className="red-header">🔴 Red Composition</h4>
              <span className="comp-type-pill">{resolvedRedSummary?.composition}</span>
            </div>
            <button
              type="button"
              className="comp-collapse-toggle"
              onClick={() => toggleSection('red')}
              aria-expanded={!redCollapsed}
              aria-controls="red-comp-body"
            >
              {redCollapsed ? 'Expand' : 'Collapse'}
            </button>
          </div>
          <div className="comp-body" id="red-comp-body" hidden={redCollapsed}>
            <DistributionBar entries={resolvedRedSummary?.distributionEntries} team="red" />
            <div className="team-snapshot">
              {redSnapshot.map((item, idx) => (
                <div key={`red-snap-${idx}`} className="snapshot-row">
                  <div className="snapshot-label">{item.label}</div>
                  <div className="snapshot-value">{item.value}</div>
                  {item.detail && <div className="snapshot-detail">{item.detail}</div>}
                </div>
              ))}
            </div>
            <div className="coach-notes">
              {buildCoachNotes(resolvedRedSummary).map((note, idx) => (
                <div key={idx} className="coach-note">{note}</div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="pick-debt-section">
        <div className="pick-debt-header">
          <h4>Pick Debt Tracker</h4>
          <p>Outstanding composition commitments each team still owes this draft.</p>
        </div>
        <div className="pick-debt-grid">
          <div className="debt-column blue">
            <div className="debt-team-label">Blue owes</div>
            {blueDebts.length ? (
              <ul className="debt-list">
                {blueDebts.map(item => (
                  <li key={`blue-${item.id}`} className={`debt-item ${item.severity}`}>
                    <span className="debt-pill">{item.text}</span>
                    {item.hint && <span className="debt-hint">{item.hint}</span>}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="debt-cleared">No outstanding debts — composition commitments covered.</div>
            )}
          </div>
          <div className="debt-column red">
            <div className="debt-team-label">Red owes</div>
            {redDebts.length ? (
              <ul className="debt-list">
                {redDebts.map(item => (
                  <li key={`red-${item.id}`} className={`debt-item ${item.severity}`}>
                    <span className="debt-pill">{item.text}</span>
                    {item.hint && <span className="debt-hint">{item.hint}</span>}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="debt-cleared">No outstanding debts — composition commitments covered.</div>
            )}
          </div>
        </div>
      </div>

      {(favoredPlaymaker || underdogThreat) && (
        <div className="key-matchups">
          <h4>Key Champion Pivots</h4>
          <div className="pivot-grid">
            {favoredPlaymaker && (
              <ChampionPivot
                pivot={favoredPlaymaker}
                label={`${favoredLabel} playmaker`}
                accent={favoredSide}
              />
            )}
            {underdogThreat && (
              <ChampionPivot
                pivot={underdogThreat}
                label={`${underdogLabel} comeback threat`}
                accent={underdogSide}
              />
            )}
          </div>
        </div>
      )}

      <div className="analysis-grid">
        <div className="insights-section">
          <h4>💡 Archetypal Insights</h4>
          <div className="insights-list">
            {(archetypal_insights || []).map((insight, i) => (
              <div key={i} className="insight-item">
                <span className="insight-bullet">→</span>
                {insight}
              </div>
            ))}
          </div>
        </div>

        <div className="why-favored">
          <div className="why-header">
            <h4>{favoredLabel} Win Conditions</h4>
            <p>Auto-generated leverage points for the favored side.</p>
          </div>
          {favoredNarrative.length ? (
            <ul>
              {favoredNarrative.map((line, idx) => (
                <li key={`favored-line-${idx}`}>{line}</li>
              ))}
            </ul>
          ) : (
            <p>No favored-specific narrative available.</p>
          )}

          <div className="why-header" style={{ marginTop: 16 }}>
            <h4>{underdogLabel} Comeback Plan</h4>
            <p>How the underdog can flip fights and tempo.</p>
          </div>
          {underdogNarrative.length ? (
            <ul>
              {underdogNarrative.map((line, idx) => (
                <li key={`underdog-line-${idx}`}>{line}</li>
              ))}
            </ul>
          ) : (
            <p>No comeback guidance available.</p>
          )}
        </div>
      </div>

      {!!comparisonNarrative.length && (
        <div className="comparison-columns">
          <div className={`comparison-card ${comparisonNarrative.some(item => item.team === 'blue') ? 'blue' : 'subdued'}`}>
            <h5>Blue Levers</h5>
            <ul>
              {comparisonNarrative.filter(item => item.team === 'blue').map((item, idx) => (
                <li key={`blue-comp-${idx}`}>{item.text}</li>
              ))}
            </ul>
          </div>
          <div className={`comparison-card ${comparisonNarrative.some(item => item.team === 'red') ? 'red' : 'subdued'}`}>
            <h5>Red Levers</h5>
            <ul>
              {comparisonNarrative.filter(item => item.team === 'red').map((item, idx) => (
                <li key={`red-comp-${idx}`}>{item.text}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisPanel;
