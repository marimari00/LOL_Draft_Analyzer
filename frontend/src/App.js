import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import './App.css';
import DraftBoard from './components/DraftBoard';
import RecommendationPanel from './components/RecommendationPanel';
import AnalysisPanel from './components/AnalysisPanel';
import TeamSummary from './components/TeamSummary';
import CoachTraining from './components/CoachTraining';
import HealthDashboard from './components/HealthDashboard';
import BanSelector from './components/BanSelector';

const API_BASE = 'http://localhost:8000';
const ROLE_ORDER = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'];
const ROLE_PRIORITY = ROLE_ORDER.reduce((acc, role, idx) => {
  acc[role] = idx;
  return acc;
}, {});
const PICK_ORDER_TEMPLATE = [
  { id: 'B1', team: 'blue', role: 'TOP' },
  { id: 'R1', team: 'red', role: 'TOP' },
  { id: 'R2', team: 'red', role: 'JUNGLE' },
  { id: 'B2', team: 'blue', role: 'JUNGLE' },
  { id: 'B3', team: 'blue', role: 'MIDDLE' },
  { id: 'R3', team: 'red', role: 'MIDDLE' },
  { id: 'R4', team: 'red', role: 'BOTTOM' },
  { id: 'B4', team: 'blue', role: 'BOTTOM' },
  { id: 'B5', team: 'blue', role: 'UTILITY' },
  { id: 'R5', team: 'red', role: 'UTILITY' }
];

const BAN_TURN_SEQUENCE = [
  { id: 'B1', team: 'blue' },
  { id: 'R1', team: 'red' },
  { id: 'B2', team: 'blue' },
  { id: 'R2', team: 'red' },
  { id: 'B3', team: 'blue' },
  { id: 'R3', team: 'red' },
  { id: 'R4', team: 'red' },
  { id: 'B4', team: 'blue' },
  { id: 'B5', team: 'blue' },
  { id: 'R5', team: 'red' }
];

const OPENING_BAN_COUNT = 6;
const OPENING_PICK_COUNT = 6;

const BAN_MODES = {
  PRO: 'pro',
  SOLOQ: 'soloq'
};

const SKIP_BAN_SENTINEL = 'NONE';

const createDefaultPickOrder = () => PICK_ORDER_TEMPLATE.map(slot => ({ ...slot }));
const MIN_UNIQUE_CHAMPIONS_FOR_RANDOM_DRAFT = 20;
const POSITION_MAP = {
  Top: 'TOP',
  Jungle: 'JUNGLE',
  Middle: 'MIDDLE',
  Mid: 'MIDDLE',
  Bottom: 'BOTTOM',
  Bot: 'BOTTOM',
  Carry: 'BOTTOM',
  Support: 'UTILITY',
  Utility: 'UTILITY'
};

const normalizeRole = (position) => {
  if (!position) return null;
  return POSITION_MAP[position] || position.toUpperCase();
};

const normalizeChampionKey = (value = '') => value.toLowerCase().replace(/[^a-z0-9]/g, '');

const ARCHETYPE_TO_FAMILY = {
  engage_tank: 'hard_engage',
  diver: 'hard_engage',
  catcher: 'pick',
  burst_assassin: 'pick',
  burst_mage: 'burst',
  battle_mage: 'aoe',
  artillery_mage: 'poke',
  marksman: 'carry',
  enchanter: 'protect',
  warden: 'protect',
  juggernaut: 'bruiser',
  skirmisher: 'bruiser',
  specialist: 'specialist'
};

const FAMILY_DISPLAY_NAMES = {
  hard_engage: 'Hard Engage',
  pick: 'Pick Composition',
  poke: 'Siege & Poke',
  burst: 'Burst Control',
  aoe: 'AoE Teamfight',
  protect: 'Protect the Carry',
  carry: 'Carry Scaling',
  bruiser: 'Bruiser Brawl',
  specialist: 'Specialist Pocket',
  flex: 'Flexible'
};

const buildChampionEntry = (name, info = {}) => {
  const roles = [];
  const pushRole = (pos) => {
    const normalized = normalizeRole(pos);
    if (normalized && !roles.includes(normalized)) {
      roles.push(normalized);
    }
  };

  pushRole(info.primary_position);
  (info.viable_positions || []).forEach(pushRole);

  return {
    name,
    roles,
    archetype: info.primary_archetype || 'Unknown',
    attributes: info.archetype_attributes ?? info.attributes ?? []
  };
};

const alignTeamPicksToSlots = (picks, slots) => {
  if (!picks.length) return picks;
  const sorted = [...picks].sort((a, b) => {
    const aIdx = ROLE_PRIORITY[a.role] ?? ROLE_ORDER.length;
    const bIdx = ROLE_PRIORITY[b.role] ?? ROLE_ORDER.length;
    if (aIdx !== bIdx) {
      return aIdx - bIdx;
    }
    return 0;
  });
  return sorted.map((pick, idx) => {
    const slot = slots[idx];
    if (!slot) return pick;
    return {
      ...pick,
      slotId: slot.id,
      role: slot.role
    };
  });
};

const formatArchetypeName = (archetype) => {
  if (!archetype) return 'Flexible';
  return archetype
    .split('_')
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
};

const deriveFamilyLabel = (family) => FAMILY_DISPLAY_NAMES[family] || formatArchetypeName(family);
const formatCompositionIdentity = (value) => formatArchetypeName(value);

const deriveIdentityFromCounts = (counts, sortedEntries) => {
  const get = (key) => counts[key] || 0;
  if (get('hard_engage') >= 2) return 'Hard Engage';
  if (get('protect') >= 1 && get('carry') >= 1) return 'Protect the Carry';
  if (get('poke') >= 2) return 'Siege & Poke';
  if (get('pick') >= 2) return 'Pick Composition';
  if (get('bruiser') >= 3) return 'Bruiser Brawl';
  if (get('aoe') >= 2) return 'AoE Teamfight';
  if (get('specialist') >= 2) return 'Specialist Pocket';
  if (sortedEntries.length > 0) {
    return sortedEntries[0].label;
  }
  return 'Flexible';
};

const summarizeTeamFamilies = (picks, lookup) => {
  if (!picks || picks.length === 0) {
    return { entries: [], identity: 'Flexible' };
  }
  const counts = {};
  picks.forEach(pick => {
    const archetype = lookup[pick.champion]?.archetype;
    if (!archetype) return;
    const family = ARCHETYPE_TO_FAMILY[archetype] || archetype || 'flex';
    counts[family] = (counts[family] || 0) + 1;
  });
  const entries = Object.entries(counts)
    .map(([family, count]) => ({
      family,
      count,
      label: deriveFamilyLabel(family)
    }))
    .sort((a, b) => b.count - a.count);
  return {
    entries,
    identity: deriveIdentityFromCounts(counts, entries)
  };
};

function App() {
  // Draft state
  const [bluePicks, setBluePicks] = useState([]);
  const [redPicks, setRedPicks] = useState([]);
  const [blueBans, setBlueBans] = useState([]);
  const [redBans, setRedBans] = useState([]);
  const [banMode, setBanMode] = useState(BAN_MODES.PRO);
  const [soloQueueBanTeam, setSoloQueueBanTeam] = useState('blue');
  const [focusTeam, setFocusTeam] = useState('blue');
  const [pickOrder, setPickOrder] = useState(() => createDefaultPickOrder());
  const [lanesAutoSorted, setLanesAutoSorted] = useState(false);
  
  // Recommendations
  const [recommendations, setRecommendations] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [winProjection, setWinProjection] = useState(null);
  const [banRecommendationResponse, setBanRecommendationResponse] = useState(null);
  const [banRecommendationsLoading, setBanRecommendationsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('draft');
  
  // Available champions
  const [championPool, setChampionPool] = useState([]);
  const [championLookup, setChampionLookup] = useState({});

  const canRandomizeDraft = championPool.length >= MIN_UNIQUE_CHAMPIONS_FOR_RANDOM_DRAFT;

  const effectiveBlueBans = useMemo(
    () => blueBans.filter(name => name && name !== SKIP_BAN_SENTINEL),
    [blueBans]
  );
  const effectiveRedBans = useMemo(
    () => redBans.filter(name => name && name !== SKIP_BAN_SENTINEL),
    [redBans]
  );

  const availableChampions = useMemo(() => {
    if (!championPool.length) return [];
    const picked = new Set([
      ...bluePicks.map(p => p.champion),
      ...redPicks.map(p => p.champion)
    ]);
    const banned = new Set([...blueBans, ...redBans]);
    return championPool.filter(({ name }) => !picked.has(name) && !banned.has(name));
  }, [championPool, bluePicks, redPicks, blueBans, redBans]);

  const normalizedChampionIndex = useMemo(() => {
    const lookup = {};
    championPool.forEach(entry => {
      const key = normalizeChampionKey(entry.name);
      if (key && !lookup[key]) {
        lookup[key] = entry;
      }
    });
    return lookup;
  }, [championPool]);
  
  const loadChampions = async () => {
    try {
      // Load from local champion data
      const response = await fetch('/champion_archetypes.json');
      const data = await response.json();
      const assignments = data.assignments || {};
      const entries = Object
        .entries(assignments)
        .map(([name, info]) => buildChampionEntry(name, info))
        .sort((a, b) => a.name.localeCompare(b.name));
      setChampionPool(entries);
      setChampionLookup(Object.fromEntries(entries.map(entry => [entry.name, entry])));
    } catch (error) {
      console.error('Error loading champions:', error);
      // Fallback to a few champions for testing
      const fallbackList = [
        'Aatrox', 'Ahri', 'Akali', 'Alistar', 'Amumu', 'Anivia', 'Annie',
        'Ashe', 'Blitzcrank', 'Brand', 'Braum', 'Caitlyn', 'Cassiopeia',
        'Darius', 'Diana', 'Draven', 'Ekko', 'Ezreal', 'Fiora', 'Garen',
        'Gragas', 'Graves', 'Hecarim', 'Irelia', 'Janna', 'Jarvan IV',
        'Jax', 'Jayce', 'Jhin', 'Jinx', 'Karma', 'Katarina', 'Kayle',
        'LeBlanc', 'Lee Sin', 'Leona', 'Lissandra', 'Lucian', 'Lulu',
        'Lux', 'Malphite', 'Maokai', 'Master Yi', 'Miss Fortune', 'Morgana',
        'Nami', 'Nautilus', 'Nidalee', 'Orianna', 'Pantheon', 'Poppy',
        'Rakan', 'Rammus', 'Renekton', 'Riven', 'Rumble', 'Ryze',
        'Sejuani', 'Shen', 'Shyvana', 'Singed', 'Sona', 'Soraka',
        'Syndra', 'Tahm Kench', 'Talon', 'Thresh', 'Tristana', 'Trundle',
        'Twisted Fate', 'Twitch', 'Urgot', 'Varus', 'Vayne', 'Veigar',
        'Vi', 'Viktor', 'Vladimir', 'Volibear', 'Warwick', 'Wukong',
        'Xayah', 'Xerath', 'Xin Zhao', 'Yasuo', 'Yorick', 'Zac',
        'Zed', 'Ziggs', 'Zilean', 'Zoe', 'Zyra'
      ];
      const fallbackEntries = fallbackList.map(name => ({
        name,
        roles: [],
        archetype: 'Unknown',
        attributes: []
      }));
      setChampionPool(fallbackEntries);
      setChampionLookup(Object.fromEntries(fallbackEntries.map(entry => [entry.name, entry])));
    }
  };
  
  const totalPicks = bluePicks.length + redPicks.length;
  const totalBans = blueBans.length + redBans.length;
  const draftComplete = bluePicks.length === 5 && redPicks.length === 5;

  const soloQueueNeedsBans = blueBans.length < 5 || redBans.length < 5;
  const soloQueueBanSlots = useMemo(() => ({
    blue: Math.max(0, 5 - blueBans.length),
    red: Math.max(0, 5 - redBans.length)
  }), [blueBans, redBans]);

  const currentAction = useMemo(() => {
    if (banMode === BAN_MODES.SOLOQ) {
      if (soloQueueNeedsBans) {
        return 'ban';
      }
      if (totalPicks < PICK_ORDER_TEMPLATE.length) {
        return 'pick';
      }
      return 'complete';
    }

    if (totalBans < OPENING_BAN_COUNT) {
      return 'ban';
    }
    if (totalPicks < OPENING_PICK_COUNT) {
      return 'pick';
    }
    if (totalBans < BAN_TURN_SEQUENCE.length) {
      return 'ban';
    }
    if (totalPicks < PICK_ORDER_TEMPLATE.length) {
      return 'pick';
    }
    return 'complete';
  }, [banMode, soloQueueNeedsBans, totalBans, totalPicks]);

  const nextBanTurn = banMode === BAN_MODES.PRO && totalBans < BAN_TURN_SEQUENCE.length
    ? BAN_TURN_SEQUENCE[totalBans]
    : null;

  const resolvedSoloQueueBanTeam = useMemo(() => {
    if (banMode !== BAN_MODES.SOLOQ || currentAction !== 'ban') {
      return null;
    }
    if (soloQueueBanSlots[soloQueueBanTeam] > 0) {
      return soloQueueBanTeam;
    }
    if (soloQueueBanSlots.blue > 0) {
      return 'blue';
    }
    if (soloQueueBanSlots.red > 0) {
      return 'red';
    }
    return null;
  }, [banMode, currentAction, soloQueueBanSlots, soloQueueBanTeam]);

  const banTeam = currentAction === 'ban'
    ? (banMode === BAN_MODES.PRO ? nextBanTurn?.team || null : resolvedSoloQueueBanTeam)
    : null;

  const nextBanTurnLabel = useMemo(() => {
    if (banMode === BAN_MODES.PRO) {
      return nextBanTurn
        ? `${nextBanTurn.id} • ${nextBanTurn.team.toUpperCase()}`
        : 'All bans complete';
    }
    if (!soloQueueNeedsBans) {
      return 'All bans complete';
    }
    return `SoloQ • BLUE ${soloQueueBanSlots.blue} / RED ${soloQueueBanSlots.red}`;
  }, [banMode, nextBanTurn, soloQueueNeedsBans, soloQueueBanSlots]);

  const nextPickSlot = pickOrder[totalPicks] || null;
  const recommendationTeam = nextPickSlot?.team || focusTeam;
  const draftNextTeam = currentAction === 'pick'
    ? (nextPickSlot?.team || focusTeam)
    : (banTeam || focusTeam);

  const phaseLabel = useMemo(() => {
    if (currentAction === 'pick') {
      return nextPickSlot
        ? `${nextPickSlot.id} • ${nextPickSlot.team.toUpperCase()} • ${nextPickSlot.role || 'FLEX'}`
        : 'All picks complete';
    }
    if (currentAction === 'ban') {
      return nextBanTurnLabel;
    }
    if (currentAction === 'complete') {
      return 'Draft complete';
    }
    return 'Preparing';
  }, [currentAction, nextPickSlot, nextBanTurnLabel]);

  const banQueueHint = useMemo(() => {
    if (banMode !== BAN_MODES.PRO) {
      return '';
    }
    const preview = BAN_TURN_SEQUENCE.slice(totalBans + 1, totalBans + 3);
    if (!preview.length) {
      return '';
    }
    return preview.map(turn => `${turn.id} ${turn.team.toUpperCase()}`).join(' → ');
  }, [banMode, totalBans]);

  useEffect(() => {
    if (banMode !== BAN_MODES.SOLOQ) {
      return;
    }
    if (!soloQueueNeedsBans) {
      return;
    }
    const blueHasRoom = soloQueueBanSlots.blue > 0;
    const redHasRoom = soloQueueBanSlots.red > 0;
    if (blueHasRoom && redHasRoom) {
      return;
    }
    if (blueHasRoom && !redHasRoom && soloQueueBanTeam !== 'blue') {
      setSoloQueueBanTeam('blue');
    } else if (redHasRoom && !blueHasRoom && soloQueueBanTeam !== 'red') {
      setSoloQueueBanTeam('red');
    }
  }, [banMode, soloQueueNeedsBans, soloQueueBanSlots, soloQueueBanTeam]);

  const upcomingSlots = useMemo(() => {
    if (!nextPickSlot) return [];
    const remaining = pickOrder.slice(totalPicks);
    const slots = [];
    for (const slot of remaining) {
      if (slot.team !== recommendationTeam) {
        if (slots.length === 0) {
          continue;
        }
        break;
      }
      slots.push(slot);
      if (slots.length === 2) {
        break;
      }
    }
    return slots;
  }, [pickOrder, totalPicks, recommendationTeam, nextPickSlot]);

  const hasFutureFocusPick = useMemo(() => {
    const remaining = pickOrder.slice(totalPicks);
    return remaining.some(slot => slot.team === focusTeam);
  }, [pickOrder, totalPicks, focusTeam]);

  const waitingForTurn = currentAction === 'pick' && recommendationTeam !== focusTeam && hasFutureFocusPick;
  const teamOrder = focusTeam === 'blue' ? ['blue', 'red'] : ['red', 'blue'];
  const projectionConfidence = typeof winProjection?.confidence === 'number' ? winProjection.confidence : null;
  const favoredSide = winProjection?.favored || null;
  const totalSlots = pickOrder.length || 10;
  const draftProgressRatio = totalSlots ? (totalPicks / totalSlots) : 0;

  const getRecommendations = useCallback(async () => {
    if (currentAction === 'ban') {
      setRecommendations([]);
      setWinProjection(null);
      return;
    }
    if (upcomingSlots.length === 0) {
      setRecommendations([]);
      setWinProjection(null);
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/draft/recommend`, {
        draft_state: {
          blue_picks: bluePicks.map(p => p.champion),
          blue_roles: bluePicks.map(p => p.role),
          blue_bans: effectiveBlueBans,
          red_picks: redPicks.map(p => p.champion),
          red_roles: redPicks.map(p => p.role),
          red_bans: effectiveRedBans,
          next_pick: recommendationTeam
        },
        upcoming_slots: upcomingSlots.map(slot => ({
          slot_id: slot.id,
          team: slot.team,
          role: slot.role || null
        })),
        limit: 5
      });
      setRecommendations(response.data.slots || []);
      setWinProjection(response.data.win_projection || null);
    } catch (error) {
      console.error('Error getting recommendations:', error);
      setRecommendations([]);
      setWinProjection(null);
    } finally {
      setLoading(false);
    }
  }, [
    currentAction,
    bluePicks,
    redPicks,
    effectiveBlueBans,
    effectiveRedBans,
    upcomingSlots,
    recommendationTeam
  ]);

  const getBanRecommendations = useCallback(async () => {
    if (currentAction !== 'ban' || !banTeam) {
      setBanRecommendationResponse(null);
      setBanRecommendationsLoading(false);
      return;
    }

    setBanRecommendationsLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/draft/bans`, {
        mode: banMode,
        team: banTeam,
        draft_state: {
          blue_picks: bluePicks.map(p => p.champion),
          blue_roles: bluePicks.map(p => p.role),
          blue_bans: effectiveBlueBans,
          red_picks: redPicks.map(p => p.champion),
          red_roles: redPicks.map(p => p.role),
          red_bans: effectiveRedBans,
          next_pick: recommendationTeam
        },
        limit: 5
      });
      setBanRecommendationResponse(response.data);
    } catch (error) {
      console.error('Error getting ban recommendations:', error);
      setBanRecommendationResponse(null);
    } finally {
      setBanRecommendationsLoading(false);
    }
  }, [
    currentAction,
    banTeam,
    banMode,
    bluePicks,
    redPicks,
    effectiveBlueBans,
    effectiveRedBans,
    recommendationTeam
  ]);
  
  const getAnalysis = useCallback(async () => {
    if (bluePicks.length !== 5 || redPicks.length !== 5) return;
    try {
      const response = await axios.post(`${API_BASE}/draft/analyze`, {
        blue_team: bluePicks.map(p => p.champion),
        blue_roles: bluePicks.map(p => p.role),
        red_team: redPicks.map(p => p.champion),
        red_roles: redPicks.map(p => p.role)
      });
      setAnalysis(response.data);
    } catch (error) {
      console.error('Error getting analysis:', error);
      setAnalysis(null);
    }
  }, [bluePicks, redPicks]);
  
  // Load champions on mount
  useEffect(() => {
    loadChampions();
  }, []);
  
  // Get recommendations when draft changes
  useEffect(() => {
    getRecommendations();
  }, [getRecommendations]);

  useEffect(() => {
    getBanRecommendations();
  }, [getBanRecommendations]);
  
  // Get analysis when both teams have 5 picks
  useEffect(() => {
    getAnalysis();
  }, [getAnalysis]);
  
  const getDefaultRoleForChampion = useCallback((champion) => {
    return championLookup[champion]?.roles?.[0] || null;
  }, [championLookup]);

  const getNextOpenRole = useCallback((picks) => {
    for (const role of ROLE_ORDER) {
      if (!picks.some(p => p.role === role)) {
        return role;
      }
    }
    return ROLE_ORDER[picks.length % ROLE_ORDER.length];
  }, []);

  const commitPickToSlot = useCallback((slot, champion, suggestedRole = null) => {
    if (!slot) {
      return { success: false, message: 'No pick slot available' };
    }
    const teamPicks = slot.team === 'blue' ? bluePicks : redPicks;
    if (teamPicks.some(p => p.slotId === slot.id)) {
      return { success: false, message: 'Slot already filled' };
    }
    if (teamPicks.length >= 5) {
      return { success: false, message: 'Team already has 5 picks' };
    }
    const preferredRole = suggestedRole || slot.role || getDefaultRoleForChampion(champion);
    const resolvedRole = preferredRole || getNextOpenRole(teamPicks);
    const newPick = {
      slotId: slot.id,
      champion,
      role: resolvedRole
    };
    if (slot.team === 'blue') {
      setBluePicks([...bluePicks, newPick]);
    } else {
      setRedPicks([...redPicks, newPick]);
    }
    return { success: true, champion };
  }, [bluePicks, redPicks, getDefaultRoleForChampion, getNextOpenRole]);

  const handleChampionPick = (champion, suggestedRole = null) => {
    if (currentAction === 'pick') {
      const slot = nextPickSlot;
      if (!slot) return;
      commitPickToSlot(slot, champion, suggestedRole);
    } else if (currentAction === 'ban' && banTeam) {
      const bans = banTeam === 'blue' ? blueBans : redBans;
      if (bans.length >= 5) return;

      if (banTeam === 'blue') {
        setBlueBans([...blueBans, champion || SKIP_BAN_SENTINEL]);
      } else {
        setRedBans([...redBans, champion || SKIP_BAN_SENTINEL]);
      }
    }
  };

  const handleRandomDraft = useCallback(() => {
    if (!canRandomizeDraft) {
      console.warn('Not enough champions available to randomize draft.');
      return;
    }
    const remaining = [...championPool];

    const takeFromPool = (predicate) => {
      const indices = [];
      for (let i = 0; i < remaining.length; i += 1) {
        if (predicate(remaining[i])) {
          indices.push(i);
        }
      }
      if (indices.length === 0) {
        return null;
      }
      const chosenIndex = indices[Math.floor(Math.random() * indices.length)];
      const [chosen] = remaining.splice(chosenIndex, 1);
      return chosen;
    };

    const takeChampion = (role = null) => {
      if (role) {
        const roleMatch = takeFromPool((champ) => champ.roles.includes(role));
        if (roleMatch) {
          return roleMatch;
        }
      }
      return takeFromPool(() => true);
    };

    const generateBans = (count) => {
      const bans = [];
      for (let i = 0; i < count; i += 1) {
        const selection = takeChampion();
        if (!selection) {
          break;
        }
        bans.push(selection.name);
      }
      return bans;
    };

    const newBlueBans = generateBans(5);
    const newRedBans = generateBans(5);
    const newBluePicks = [];
    const newRedPicks = [];
    const orderedSlots = createDefaultPickOrder();
    orderedSlots.forEach((slot) => {
      const selection = takeChampion(slot.role);
      if (!selection) {
        return;
      }
      const pick = {
        slotId: slot.id,
        champion: selection.name,
        role: slot.role
      };
      if (slot.team === 'blue') {
        newBluePicks.push(pick);
      } else {
        newRedPicks.push(pick);
      }
    });

    setBluePicks(newBluePicks);
    setRedPicks(newRedPicks);
    setBlueBans(newBlueBans);
    setRedBans(newRedBans);
    setFocusTeam('blue');
    setSoloQueueBanTeam('blue');
    setRecommendations([]);
    setAnalysis(null);
    setPickOrder(createDefaultPickOrder());
    setLanesAutoSorted(true);
    }, [canRandomizeDraft, championPool]);

  const resolveChampionFromInput = useCallback((value) => {
    if (!value) return null;
    const trimmed = value.trim();
    if (!trimmed) return null;
    const normalized = normalizeChampionKey(trimmed);
    if (normalizedChampionIndex[normalized]) {
      return normalizedChampionIndex[normalized];
    }
    if (!availableChampions.length) {
      return null;
    }
    const exact = availableChampions.find(
      champ => normalizeChampionKey(champ.name) === normalized
    );
    if (exact) return exact;
    const startsWith = availableChampions.find(
      champ => normalizeChampionKey(champ.name).startsWith(normalized)
    );
    if (startsWith) return startsWith;
    return availableChampions.find(champ =>
      champ.name.toLowerCase().includes(trimmed.toLowerCase())
    ) || null;
  }, [availableChampions, normalizedChampionIndex]);

  const handleInlineSlotPick = useCallback((slotId, rawInput) => {
    if (!rawInput || !rawInput.trim()) {
      return { success: false, message: 'Type a champion name' };
    }
    if (currentAction !== 'pick') {
      return { success: false, message: 'Inline entry only during pick phase' };
    }
    const slot = pickOrder.find(entry => entry.id === slotId);
    if (!slot) {
      return { success: false, message: 'Unknown slot' };
    }
    if (!nextPickSlot || slot.id !== nextPickSlot.id) {
      return { success: false, message: 'Waiting for this slot to become active' };
    }
    const candidate = resolveChampionFromInput(rawInput);
    if (!candidate) {
      return { success: false, message: 'Champion not found' };
    }
    const isAvailable = availableChampions.some(champ => champ.name === candidate.name);
    if (!isAvailable) {
      return { success: false, message: 'Champion already drafted or banned' };
    }
    return commitPickToSlot(slot, candidate.name);
  }, [availableChampions, commitPickToSlot, currentAction, nextPickSlot, pickOrder, resolveChampionFromInput]);

  const handleBanModeChange = (mode) => {
    if (mode === banMode) {
      return;
    }
    setBanMode(mode);
    if (mode === BAN_MODES.SOLOQ) {
      if (soloQueueBanSlots[focusTeam] > 0) {
        setSoloQueueBanTeam(focusTeam);
      } else if (soloQueueBanSlots.blue > 0) {
        setSoloQueueBanTeam('blue');
      } else if (soloQueueBanSlots.red > 0) {
        setSoloQueueBanTeam('red');
      }
    }
  };

  const handleSoloQueueTeamSelect = (team) => {
    if (soloQueueBanSlots[team] <= 0) {
      return;
    }
    setSoloQueueBanTeam(team);
  };
  
  const resetDraft = () => {
    setBluePicks([]);
    setRedPicks([]);
    setBlueBans([]);
    setRedBans([]);
    setFocusTeam('blue');
    setSoloQueueBanTeam('blue');
    setRecommendations([]);
    setAnalysis(null);
    setPickOrder(createDefaultPickOrder());
    setLanesAutoSorted(false);
  };

  const handleMoveLane = (slotId, direction) => {
    setPickOrder(prev => {
      const index = prev.findIndex(slot => slot.id === slotId);
      if (index === -1) return prev;
      const slot = prev[index];
      const team = slot.team;
      let targetIndex = index;
      while (true) {
        targetIndex += direction === 'up' ? -1 : 1;
        if (targetIndex < 0 || targetIndex >= prev.length) {
          return prev;
        }
        if (prev[targetIndex].team === team) {
          break;
        }
      }
      const targetSlot = prev[targetIndex];
      const teamPicks = team === 'blue' ? bluePicks : redPicks;
      const slotPick = teamPicks.find(p => p.slotId === slot.id);
      const targetSlotPick = teamPicks.find(p => p.slotId === targetSlot.id);
      if (slotPick || targetSlotPick) {
        return prev;
      }
      const updated = prev.map(item => ({ ...item }));
      const tempRole = updated[index].role;
      updated[index].role = updated[targetIndex].role;
      updated[targetIndex].role = tempRole;
      return updated;
    });
  };

  const resetPickOrderRoles = () => {
    setPickOrder(createDefaultPickOrder());
    setLanesAutoSorted(false);
  };

  const handleBanClick = (team, index) => {
    if (team === 'blue') {
      setBlueBans(prev => {
        if (!prev[index]) return prev;
        const updated = [...prev];
        updated.splice(index, 1);
        return updated;
      });
    } else {
      setRedBans(prev => {
        if (!prev[index]) return prev;
        const updated = [...prev];
        updated.splice(index, 1);
        return updated;
      });
    }
  };
  
  const teamCompositionSummaries = useMemo(() => ({
    blue: summarizeTeamFamilies(bluePicks, championLookup),
    red: summarizeTeamFamilies(redPicks, championLookup)
  }), [bluePicks, redPicks, championLookup]);

  const teamLeanSummaries = useMemo(() => ({
    blue: teamCompositionSummaries.blue.identity,
    red: teamCompositionSummaries.red.identity
  }), [teamCompositionSummaries]);

  const teamCompositionIdentities = useMemo(() => ({
    blue: analysis?.blue_analysis?.composition_type
      ? formatCompositionIdentity(analysis.blue_analysis.composition_type)
      : teamLeanSummaries.blue,
    red: analysis?.red_analysis?.composition_type
      ? formatCompositionIdentity(analysis.red_analysis.composition_type)
      : teamLeanSummaries.red
  }), [analysis, teamLeanSummaries]);

  const enrichedRecommendations = useMemo(() => {
    if (!recommendations || recommendations.length === 0) {
      return recommendations;
    }
    return recommendations.map(slot => {
      const teamPicks = slot.team === 'blue' ? bluePicks : redPicks;
      const teamSummary = summarizeTeamFamilies(teamPicks, championLookup);
      const teamLeanLabel = teamSummary.identity;
      const recs = (slot.recommendations || []).map(rec => {
        const futureSummary = summarizeTeamFamilies(
          [...teamPicks, { champion: rec.champion }],
          championLookup
        );
        return {
          ...rec,
          futureLeanLabel: futureSummary.identity
        };
      });
      return {
        ...slot,
        teamLeanLabel,
        recommendations: recs
      };
    });
  }, [recommendations, bluePicks, redPicks, championLookup]);

  const playmakerHighlight = useMemo(() => {
    const favoredSide = analysis?.matchup_context?.favored;
    const playmaker = analysis?.matchup_context?.favored_playmaker;
    if (!favoredSide || !playmaker?.champion) {
      return null;
    }
    const teamPicks = favoredSide === 'blue' ? bluePicks : redPicks;
    const existsInDraft = teamPicks.some(pick => pick.champion === playmaker.champion);
    if (!existsInDraft) {
      return null;
    }
    return {
      champion: playmaker.champion,
      team: favoredSide,
      impactPct: typeof playmaker.impact_pct === 'number' ? playmaker.impact_pct : null
    };
  }, [analysis, bluePicks, redPicks]);

  useEffect(() => {
    if (draftComplete && !lanesAutoSorted) {
      const freshOrder = createDefaultPickOrder();
      setPickOrder(freshOrder);
      const blueSlots = freshOrder.filter(slot => slot.team === 'blue');
      const redSlots = freshOrder.filter(slot => slot.team === 'red');
      setBluePicks(prev => alignTeamPicksToSlots(prev, blueSlots));
      setRedPicks(prev => alignTeamPicksToSlots(prev, redSlots));
      setLanesAutoSorted(true);
    } else if (!draftComplete && lanesAutoSorted) {
      setLanesAutoSorted(false);
    }
  }, [draftComplete, lanesAutoSorted]);

  const orderedTeams = (teamOrder && teamOrder.length === 2) ? teamOrder : ['blue', 'red'];

  const renderTeamSummary = (team) => (
    <TeamSummary
      key={`team-summary-${team}`}
      label={team === 'blue' ? 'Blue Side' : 'Red Side'}
      team={team}
      picks={team === 'blue' ? bluePicks.length : redPicks.length}
      bans={team === 'blue' ? blueBans.length : redBans.length}
      identity={teamCompositionIdentities[team] || 'Flexible'}
      winRate={typeof winProjection?.[team] === 'number' ? winProjection[team] : null}
      confidence={projectionConfidence}
      favored={favoredSide}
    />
  );
  
  return (
    <div className="App">
      <header className="App-header">
        <h1>⚔️ LoL Draft Analyzer</h1>
        <p className="subtitle">Archetypal Composition Analysis</p>
      </header>

      <div className="tab-switcher">
        <button
          type="button"
          className={activeTab === 'draft' ? 'active' : ''}
          onClick={() => setActiveTab('draft')}
        >
          Draft Room
        </button>
        <button
          type="button"
          className={activeTab === 'coach' ? 'active' : ''}
          onClick={() => setActiveTab('coach')}
        >
          Coach Training
        </button>
        <button
          type="button"
          className={activeTab === 'health' ? 'active' : ''}
          onClick={() => setActiveTab('health')}
        >
          Service Health
        </button>
      </div>

      {activeTab === 'draft' ? (
        <>
          <div className="controls">
            <div className="control-group">
              <label>Focus Team:</label>
              <button
                type="button"
                className={['blue', focusTeam === 'blue' ? 'active' : null].filter(Boolean).join(' ')}
                onClick={() => setFocusTeam('blue')}
              >
                Blue Side
              </button>
              <button
                type="button"
                className={['red', focusTeam === 'red' ? 'active' : null].filter(Boolean).join(' ')}
                onClick={() => setFocusTeam('red')}
              >
                Red Side
              </button>
            </div>

            <div className="control-group">
              <label>Phase:</label>
              <span className={`phase-chip ${currentAction}`}>
                {phaseLabel}
              </span>
            </div>

            <div className="control-group">
              <label>Ban Mode:</label>
              <button
                type="button"
                className={banMode === BAN_MODES.PRO ? 'active' : ''}
                onClick={() => handleBanModeChange(BAN_MODES.PRO)}
              >
                Pro Order
              </button>
              <button
                type="button"
                className={banMode === BAN_MODES.SOLOQ ? 'active' : ''}
                onClick={() => handleBanModeChange(BAN_MODES.SOLOQ)}
              >
                Solo Queue
              </button>
            </div>

            {banMode === BAN_MODES.SOLOQ && currentAction === 'ban' && soloQueueNeedsBans && (
              <div className="control-group">
                <label>Active SoloQ Team:</label>
                <button
                  type="button"
                  className={['blue', banTeam === 'blue' ? 'active' : null].filter(Boolean).join(' ')}
                  disabled={soloQueueBanSlots.blue === 0}
                  onClick={() => handleSoloQueueTeamSelect('blue')}
                >
                  Blue ({soloQueueBanSlots.blue} left)
                </button>
                <button
                  type="button"
                  className={['red', banTeam === 'red' ? 'active' : null].filter(Boolean).join(' ')}
                  disabled={soloQueueBanSlots.red === 0}
                  onClick={() => handleSoloQueueTeamSelect('red')}
                >
                  Red ({soloQueueBanSlots.red} left)
                </button>
              </div>
            )}

            <div className="control-group ban-queue-group">
              <label>Next Ban Turn:</label>
              <div className="ban-turn-chip">{nextBanTurnLabel}</div>
              {banQueueHint && (
                <span className="ban-queue-hint">Queue: {banQueueHint}</span>
              )}
            </div>

            <div className="control-actions">
              <button
                type="button"
                className="random-draft-button"
                onClick={handleRandomDraft}
                disabled={!canRandomizeDraft}
              >
                🎲 Random Draft
              </button>
              <button
                type="button"
                className="reset-button"
                onClick={resetDraft}
              >
                🔄 Reset Draft
              </button>
            </div>
          </div>

          <div className="next-pick-banner">
            {currentAction === 'pick' ? (
              nextPickSlot ? (
                <span>
                  Next Pick: <strong>{nextPickSlot.id}</strong> • {nextPickSlot.team.toUpperCase()} • {nextPickSlot.role || 'FLEX'}
                </span>
              ) : (
                <span>All picks complete</span>
              )
            ) : currentAction === 'ban' ? (
              <span>Ban Turn: <strong>{nextBanTurnLabel}</strong></span>
            ) : (
              <span>Draft complete</span>
            )}
          </div>

          <div className="insights-bar">
            {renderTeamSummary(orderedTeams[0])}
            <div className="draft-progress-card">
              <div className="progress-label">Draft Progress</div>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${Math.min(1, draftProgressRatio) * 100}%` }}
                ></div>
              </div>
              <div className="progress-meta">
                <span>{totalPicks}/10 picks locked</span>
                <span>
                  {currentAction === 'pick'
                    ? `Next: ${nextPickSlot?.id || 'Review'}`
                    : currentAction === 'ban'
                      ? `Ban: ${nextBanTurnLabel}`
                      : 'Draft complete'}
                </span>
              </div>
            </div>
            {renderTeamSummary(orderedTeams[1])}
          </div>

          <div className="main-content">
            <div className="left-panel">
              <DraftBoard
                bluePicks={bluePicks}
                redPicks={redPicks}
                blueBans={blueBans}
                redBans={redBans}
                currentTeam={draftNextTeam}
                currentAction={currentAction}
                activeSlotId={currentAction === 'pick' ? nextPickSlot?.id || null : null}
                pickOrder={pickOrder}
                teamOrder={orderedTeams}
                onMoveLane={handleMoveLane}
                onResetPickOrder={resetPickOrderRoles}
                onBanClick={handleBanClick}
                availableChampions={availableChampions}
                onInlinePick={handleInlineSlotPick}
                championLookup={championLookup}
                playmakerHighlight={playmakerHighlight}
              />
            </div>

            <div className="right-panel">
              {currentAction === 'ban' && banTeam && (
                <BanSelector
                  banTeam={banTeam}
                  banTurnLabel={nextBanTurnLabel}
                  availableChampions={availableChampions}
                  onBanSelect={handleChampionPick}
                  disabled={currentAction !== 'ban'}
                  bansUsed={banTeam === 'blue' ? blueBans.length : redBans.length}
                  maxBans={5}
                  banHistory={{ blue: blueBans, red: redBans }}
                  banRecommendations={banRecommendationResponse?.recommendations || []}
                  banRecommendationsLoading={banRecommendationsLoading}
                  banRecommendationContext={banRecommendationResponse}
                  allowNoneBan={banMode === BAN_MODES.SOLOQ}
                />
              )}
              {analysis && (
                <AnalysisPanel analysis={analysis} />
              )}
              <RecommendationPanel
                slotRecommendations={enrichedRecommendations || []}
                loading={loading}
                currentAction={currentAction}
                recommendationTeam={recommendationTeam}
                userFocusTeam={focusTeam}
                waitingForTurn={waitingForTurn}
                teamLeanSummaries={teamLeanSummaries}
                winProjection={winProjection}
                onSelect={handleChampionPick}
              />
            </div>
          </div>
        </>
      ) : activeTab === 'coach' ? (
        <CoachTraining
          championPool={championPool}
          championLookup={championLookup}
          apiBase={API_BASE}
        />
      ) : (
        <div className="health-tab">
          <HealthDashboard apiBase={API_BASE} />
        </div>
      )}

      <footer className="App-footer">
        <p>Theory over meta • Archetypes over win rates</p>
      </footer>
    </div>
  );
}

export default App;
