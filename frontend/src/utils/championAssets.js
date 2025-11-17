const DDRAGON_VERSION = '14.21.1';
const PUBLIC_ROOT = process.env.PUBLIC_URL || '';
const LOCAL_ICON_BASE = `${PUBLIC_ROOT}/champion-icons`;

const EXCEPTION_MAP = {
  "Cho'Gath": 'Chogath',
  "Kai'Sa": 'Kaisa',
  "Kha'Zix": 'Khazix',
  "LeBlanc": 'Leblanc',
  "Lee Sin": 'LeeSin',
  "Master Yi": 'MasterYi',
  "Miss Fortune": 'MissFortune',
  "Wukong": 'MonkeyKing',
  "Renata Glasc": 'Renata',
  "Jarvan IV": 'JarvanIV',
  "Xin Zhao": 'XinZhao',
  "Aurelion Sol": 'AurelionSol',
  "Tahm Kench": 'TahmKench',
  "Twisted Fate": 'TwistedFate',
  "Vel'Koz": 'Velkoz',
  "Nunu & Willump": 'Nunu',
  "Dr. Mundo": 'DrMundo',
  "Rek'Sai": 'RekSai',
  "Kog'Maw": 'KogMaw',
  "K'Sante": 'KSante',
  "Bel'Veth": 'Belveth'
};

const NORMALIZED_EXCEPTION_MAP = Object.entries(EXCEPTION_MAP).reduce((acc, [key, value]) => {
  const normalizedKey = key.toLowerCase().replace(/[^a-z0-9]/g, '');
  const normalizedValue = value.toLowerCase().replace(/[^a-z0-9]/g, '');
  if (normalizedKey) {
    acc[normalizedKey] = value;
  }
  if (normalizedValue && !acc[normalizedValue]) {
    acc[normalizedValue] = value;
  }
  return acc;
}, {});

const sanitizePart = (value) => value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();

const slugifyChampionName = (name) => {
  if (!name) return '';
  if (EXCEPTION_MAP[name]) {
    return EXCEPTION_MAP[name];
  }
  const normalized = name.toLowerCase().replace(/[^a-z0-9]/g, '');
  if (NORMALIZED_EXCEPTION_MAP[normalized]) {
    return NORMALIZED_EXCEPTION_MAP[normalized];
  }
  const expanded = name
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/[^a-zA-Z0-9\s]/g, ' ');
  return expanded
    .split(/\s+/)
    .filter(Boolean)
    .map(sanitizePart)
    .join('');
};

export const getChampionIconUrl = (name) => {
  const slug = slugifyChampionName(name);
  if (!slug) return '';
  return `${LOCAL_ICON_BASE}/${slug}.png`;
};

export const getChampionIconFallbackUrl = (name) => {
  const slug = slugifyChampionName(name);
  if (!slug) return '';
  return `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/img/champion/${slug}.png`;
};

export const getChampionSplashUrl = (name) => {
  const slug = slugifyChampionName(name);
  if (!slug) return '';
  return `https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${slug}_0.jpg`;
};

export const getChampionTileUrl = (name) => {
  const slug = slugifyChampionName(name);
  if (!slug) return '';
  return `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/img/champion/loading/${slug}_0.jpg`;
};

export const getChampionSlug = slugifyChampionName;
