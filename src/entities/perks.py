"""
Perks and upgrades definitions for Recoil Wing.
Handles perk data, random pool sampling, and card descriptions.
"""
import random


class PerkID:
    SHOTGUN = "shotgun"
    SHIELD = "shield"
    BOUNCY = "bouncy"
    EXPANDED_MAG = "expanded_mag"
    PIERCER = "piercer"


PERK_REGISTRY = {
    PerkID.SHOTGUN: {
        "id": PerkID.SHOTGUN,
        "name": "SCATTER CANNON",
        "category": "WEAPON",
        "description": "Fires 3 spread pellets with massive upward recoil impulse.",
        "badge": "SHOTGUN",
        "color": (244, 63, 94),     # Rose red
    },
    PerkID.SHIELD: {
        "id": PerkID.SHIELD,
        "name": "ENERGY SHIELD",
        "category": "DEFENSE",
        "description": "Deploys a kinetic barrier that absorbs 1 fatal collision.",
        "badge": "SHIELD +1",
        "color": (56, 189, 248),    # Cyan blue
    },
    PerkID.BOUNCY: {
        "id": PerkID.BOUNCY,
        "name": "RICOCHET ROUNDS",
        "category": "AMMO",
        "description": "Bullets bounce off pipes and ground up to 2 times.",
        "badge": "RICOCHET",
        "color": (234, 179, 8),     # Amber gold
    },
    PerkID.EXPANDED_MAG: {
        "id": PerkID.EXPANDED_MAG,
        "name": "OVERCLOCKED CELL",
        "category": "UTILITY",
        "description": "Max Ammo increased to 6 + 35% faster reload rate.",
        "badge": "MAX AMMO 6",
        "color": (34, 197, 94),     # Emerald green
    },
    PerkID.PIERCER: {
        "id": PerkID.PIERCER,
        "name": "HYPER PIERCER",
        "category": "WEAPON",
        "description": "Bullets pass through all obstacles in a straight laser line.",
        "badge": "PIERCER",
        "color": (168, 85, 247),    # Purple
    },
}


def get_random_perk_choices(active_perk_ids, count=3):
    """
    Returns a sample of perk choices excluding mutually exclusive or maxed-out perks.
    """
    available_ids = list(PERK_REGISTRY.keys())
    # If already has shotgun or piercer, don't show the exact same weapon
    if PerkID.SHOTGUN in active_perk_ids and PerkID.SHOTGUN in available_ids:
        available_ids.remove(PerkID.SHOTGUN)
    if PerkID.PIERCER in active_perk_ids and PerkID.PIERCER in available_ids:
        available_ids.remove(PerkID.PIERCER)
    if PerkID.EXPANDED_MAG in active_perk_ids and PerkID.EXPANDED_MAG in available_ids:
        available_ids.remove(PerkID.EXPANDED_MAG)
    if PerkID.BOUNCY in active_perk_ids and PerkID.BOUNCY in available_ids:
        available_ids.remove(PerkID.BOUNCY)

    # Fallback to all if pool gets too small
    if len(available_ids) < count:
        available_ids = list(PERK_REGISTRY.keys())

    chosen_ids = random.sample(available_ids, min(count, len(available_ids)))
    return [PERK_REGISTRY[pid] for pid in chosen_ids]
