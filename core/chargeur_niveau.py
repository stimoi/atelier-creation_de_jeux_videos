# Chargeur de niveaux
import json
import os
from copy import deepcopy
import pygame
from config.constants import *

def _default_level():
    """Crée un niveau par défaut"""
    return {
        "name": "Niveau 1",
        "ground": {"y": 0, "start_x": 0, "end_x": 10000},
        "spawn": {"x": 40, "y": -40},
        "goal": {"x": 1000, "y": -110, "w": 70, "h": 110},
        "platforms": [],
    }

def _parse_color(val):
    """Accept hex string '#rrggbb' or short '#rgb', or list/tuple of ints, return (r,g,b)."""
    fallback = (100, 100, 100)
    if val is None:
        return fallback
    if isinstance(val, (list, tuple)) and len(val) >= 3:
        try:
            return (int(val[0]), int(val[1]), int(val[2]))
        except Exception:
            return fallback
    if isinstance(val, str):
        s = val.strip()
        if s.startswith('#'):
            s = s[1:]
            if len(s) == 3:
                s = ''.join(ch*2 for ch in s)
            if len(s) >= 6:
                try:
                    r = int(s[0:2], 16)
                    g = int(s[2:4], 16)
                    b = int(s[4:6], 16)
                    return (r, g, b)
                except Exception:
                    return fallback
    return fallback

def load_levels():
    """Charge tous les niveaux depuis les fichiers JSON"""
    levels = []
    levels_dir = os.path.dirname(__file__)
    level_filenames = ["level.json", "levels.json"]  # support ancien et nouveau nommage
    
    for name in level_filenames:
        level_path = os.path.join(levels_dir, "..", name)
        if not os.path.isfile(level_path):
            continue
        try:
            with open(level_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and isinstance(data.get("levels"), list) and data["levels"]:
                    levels = data["levels"]
                    break
        except Exception:
            continue

    if not levels:
        levels = [_default_level()]
    
    return levels

def apply_level(level, game_state):
    """Applique un niveau à l'état du jeu"""
    # Sol
    game_state["GROUND_Y"] = int(level.get("ground", {}).get("y", GROUND_Y))
    game_state["GROUND_START_X"] = int(level.get("ground", {}).get("start_x", GROUND_START_X))
    game_state["GROUND_END_X"] = int(level.get("ground", {}).get("end_x", GROUND_END_X))
    
    # Plateformes
    platforms = []
    platform_colors = []
    platform_types = []
    
    for p in level.get("platforms", []):
        try:
            rx = int(p.get("x", 0))
            ry = int(p.get("y", 0))
            rw = int(p.get("w") or p.get("width") or 0)
            rh = int(p.get("h") or p.get("height") or 0)
        except Exception:
            rx = int(p.get("x", 0))
            ry = int(p.get("y", 0))
            rw = int(p.get("w", 0))
            rh = int(p.get("h", 0))
        
        platforms.append(pygame.Rect(rx, ry, rw, rh))
        platform_colors.append(_parse_color(p.get("color")))
        
        t = str(p.get("type", "platform") or "platform").lower()
        if t not in PLATFORM_TYPES:
            t = "platform"
        platform_types.append(t)
    
    game_state["platforms"] = platforms
    game_state["platform_colors"] = platform_colors
    game_state["platform_types"] = platform_types
    
    # Porte/objectif
    g = level.get("goal", {})
    goal_rect = pygame.Rect(
        int(g.get("x", 2300)),
        int(g.get("y", -30)),
        int(g.get("w", 70)),
        int(g.get("h", 110))
    )
    game_state["goal_rect"] = goal_rect
    
    # Spawn
    s = level.get("spawn", {})
    spawn_point = pygame.Vector2(
        float(s.get("x", SCREEN_WIDTH / 2)),
        float(s.get("y", GROUND_Y - (head_radius + body_height + leg_height)))
    )
    game_state["spawn_point"] = spawn_point
    
    # Ennemis
    level_enemy_configs = []
    raw_enemies = level.get("enemies", [])
    if isinstance(raw_enemies, list):
        for entry in raw_enemies:
            if isinstance(entry, dict):
                level_enemy_configs.append(deepcopy(entry))
    game_state["level_enemy_configs"] = level_enemy_configs
    
    return game_state
