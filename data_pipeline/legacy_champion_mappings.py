"""
Manual mappings for legacy champions with non-standard spell naming.

These are older champions that use different naming conventions in their .bin files.
"""

LEGACY_SPELL_MAPPINGS = {
    'Alistar': {
        'Q': 'Pulverize',
        'W': 'Headbutt',
        'E': 'AlistarE',
        'R': 'FerociousHowl'
    },
    'Anivia': {
        'Q': 'FlashFrost',
        'W': 'Crystallize',
        'E': 'Frostbite',
        'R': 'GlacialStorm'
    },
    'Blitzcrank': {
        'Q': 'RocketGrab',
        'W': 'Overdrive',
        'E': 'PowerFist',
        'R': 'StaticField'
    },
    'Chogath': {
        'Q': 'Rupture',
        'W': 'FeralScream',
        'E': 'VorpalSpikes',
        'R': 'Feast'
    },
    'Corki': {
        'Q': 'PhosphorusBomb',
        'W': 'CarpetBomb',
        'E': 'GatlingGun',
        'R': 'MissileBarrage'
    },
    'Darius': {
        'Q': 'DariusCleave',
        'W': 'DariusNoxianTacticsONH',
        'E': 'DariusAxeGrabCone',
        'R': 'DariusExecute'
    },
    'Draven': {
        'Q': 'DravenSpinning',
        'W': 'DravenFury',
        'E': 'DravenDoubleShot',
        'R': 'DravenRCast'
    },
    'Fiddlesticks': {
        'Q': 'FiddleSticksQ',
        'W': 'FiddleSticksW',
        'E': 'FiddleSticksE',
        'R': 'FiddleSticksR'
    },
    'Graves': {
        'Q': 'GravesClusterShot',
        'W': 'GravesSmokeGrenade',
        'E': 'GravesMove',
        'R': 'GravesChargeShot'
    },
    'Janna': {
        'Q': 'HowlingGale',
        'W': 'Zephyr',
        'E': 'EyeOfTheStorm',
        'R': 'ReapTheWhirlwind'
    },
    'JarvanIV': {
        'Q': 'JarvanIVDragonStrike',
        'W': 'JarvanIVGoldenAegis',
        'E': 'JarvanIVDemacianStandard',
        'R': 'JarvanIVCataclysm'
    },
    'Jayce': {
        'Q': 'JayceToTheSkies',  # Hammer Q
        'W': 'JayceStaticField',  # Hammer W
        'E': 'JayceThunderingBlow',  # Hammer E
        'R': 'JayceStanceHtG'  # Transform
    },
    'Karthus': {
        'Q': 'KarthusLayWasteA1',
        'W': 'WallOfPain',
        'E': 'Defile',
        'R': 'KarthusFallenOne'
    },
    'Kassadin': {
        'Q': 'NullLance',
        'W': 'NetherBlade',
        'E': 'ForcePulse',
        'R': 'RiftWalk'
    },
    'Kennen': {
        'Q': 'KennenShurikens',
        'W': 'KennenBringTheLight',
        'E': 'KennenLightningRush',
        'R': 'KennenShurikenStorm'
    },
    'Leona': {
        'Q': 'LeonaShieldOfDaybreak',
        'W': 'LeonaSolarBarrier',
        'E': 'LeonaZenithBlade',
        'R': 'LeonaSolarFlare'
    },
    'Malphite': {
        'Q': 'SeismicShard',
        'W': 'Obduracy',
        'E': 'Landslide',
        'R': 'UFSlash'
    },
    'MasterYi': {
        'Q': 'AlphaStrike',
        'W': 'Meditate',
        'E': 'WujuStyle',
        'R': 'Highlander'
    },
    'MissFortune': {
        'Q': 'MissFortuneRicochetShot',
        'W': 'MissFortuneViciousStrikes',
        'E': 'MissFortuneScattershot',
        'R': 'MissFortuneBulletTime'
    },
    'MonkeyKing': {  # Wukong
        'Q': 'MonkeyKingQAttack',
        'W': 'MonkeyKingDecoy',
        'E': 'MonkeyKingNimbus',
        'R': 'MonkeyKingSpinToWin'
    },
    'Nautilus': {
        'Q': 'NautilusAnchorDrag',
        'W': 'NautilusPiercingGaze',
        'E': 'NautilusSplashZone',
        'R': 'NautilusGrandLine'
    },
    'Nidalee': {
        'Q': 'JavelinToss',  # Human Q
        'W': 'Bushwhack',  # Human W
        'E': 'PrimalSurge',  # Human E
        'R': 'AspectOfTheCougar'
    },
    'Olaf': {
        'Q': 'OlafAxeThrow',
        'W': 'OlafFrenziedStrikes',
        'E': 'OlafRecklessStrike',
        'R': 'OlafRagnarok'
    },
    'Orianna': {
        'Q': 'OrianaIzunaCommand',
        'W': 'OrianaDissonanceCommand',
        'E': 'OrianaRedactCommand',
        'R': 'OrianaDetonateCommand'
    },
    'Renekton': {
        'Q': 'RenektonCleave',
        'W': 'RenektonPreExecute',
        'E': 'RenektonSliceAndDice',
        'R': 'RenektonReignOfTheTyrant'
    },
    'Riven': {
        'Q': 'RivenTriCleave',
        'W': 'RivenMartyr',
        'E': 'RivenFeint',
        'R': 'RivenFengShuiEngine'
    },
    'Rumble': {
        'Q': 'RumbleFlameThrower',
        'W': 'RumbleShield',
        'E': 'RumbleGrenade',
        'R': 'RumbleCarpetBomb'
    },
    'Shaco': {
        'Q': 'Deceive',
        'W': 'JackInTheBox',
        'E': 'TwoShivPoison',
        'R': 'HallucinateFull'
    },
    'Shyvana': {
        'Q': 'ShyvanaDoubleAttack',
        'W': 'ShyvanaImmolation',
        'E': 'ShyvanaFireball',
        'R': 'ShyvanaTransformCast'
    },
    'Singed': {
        'Q': 'PoisonTrail',
        'W': 'MegaAdhesive',
        'E': 'Fling',
        'R': 'InsanityPotion'
    },
    'Trundle': {
        'Q': 'TrundleTrollSmash',
        'W': 'TrundleDesecrate',
        'E': 'TrundleCircle',
        'R': 'TrundlePain'
    },
    'TwistedFate': {
        'Q': 'WildCards',
        'W': 'PickACard',
        'E': 'CardmasterStack',
        'R': 'Destiny'
    },
    'Twitch': {
        'Q': 'HideInShadows',
        'W': 'TwitchVenomCask',
        'E': 'TwitchExpunge',
        'R': 'TwitchFullAutomatic'
    },
    'Vayne': {
        'Q': 'VayneTumble',
        'W': 'VayneSilveredBolts',
        'E': 'VayneCondemn',
        'R': 'VayneInquisition'
    },
    'Xerath': {
        'Q': 'XerathArcanopulseChargeUp',
        'W': 'XerathArcaneBarrage2',
        'E': 'XerathMageSpear',
        'R': 'XerathLocusPulse'
    },
    'Zilean': {
        'Q': 'ZileanQ',
        'W': 'ZileanW',
        'E': 'ZileanE',
        'R': 'ZileanR'
    }
}


def get_spell_paths(champion_name: str, spell_key: str) -> list[str]:
    """
    Get all possible spell paths for a champion's spell.
    
    Returns a list of paths to try, in order of preference.
    """
    paths = []
    
    # Check if champion has legacy mapping
    if champion_name in LEGACY_SPELL_MAPPINGS:
        spell_name = LEGACY_SPELL_MAPPINGS[champion_name].get(spell_key)
        if spell_name:
            # Legacy champions have multiple possible patterns
            paths.extend([
                f"Characters/{champion_name}/Spells/{spell_name}Ability/{spell_name}",
                f"Characters/{champion_name}/Spells/{spell_name}Ability",
                f"Characters/{champion_name}/Spells/{spell_name}",
            ])
    
    # Standard patterns (for all champions, try these too)
    paths.extend([
        f"Characters/{champion_name}/Spells/{champion_name}{spell_key}Ability/{champion_name}{spell_key}",
        f"Characters/{champion_name}/Spells/{champion_name}{spell_key}Ability",
        f"Characters/{champion_name}/Spells/{champion_name}{spell_key}",
    ])
    
    return paths
