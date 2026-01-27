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
    """Parse une valeur de couleur depuis différents formats
    
    Formats supportés:
    - Chaîne hexadécimale: '#rrggbb' ou '#rgb' (ex: '#ff0000', '#f00')
    - Liste/tuple: [r, g, b] ou (r, g, b)
    - None ou invalide: retourne la couleur par défaut
    
    Args:
        val: valeur à parser (str, list, tuple, ou None)
    
    Returns:
        tuple: (r, g, b) avec des valeurs 0-255
    """
    fallback = (100, 100, 100)  # Gris par défaut
    
    # Cas 1: Liste ou tuple d'au moins 3 éléments
    if isinstance(val, (list, tuple)) and len(val) >= 3:
        try:
            return (int(val[0]), int(val[1]), int(val[2]))
        except Exception:
            return fallback
    
    # Cas 2: Chaîne de caractères
    if isinstance(val, str):
        s = val.strip()
        if s.startswith('#'):
            s = s[1:]  # Retire le '#'
            
            # Format court '#rgb' -> étend à '#rrggbb'
            if len(s) == 3:
                s = ''.join(ch*2 for ch in s)  # 'f00' -> 'ff0000'
            
            # Format long '#rrggbb'
            if len(s) >= 6:
                try:
                    r = int(s[0:2], 16)  # Conversion hexadécimale
                    g = int(s[2:4], 16)
                    b = int(s[4:6], 16)
                    return (r, g, b)
                except Exception:
                    return fallback
    
    return fallback

def load_levels():
    """Charge tous les niveaux depuis les fichiers JSON
    
    Stratégie de chargement:
    1. Cherche 'level.json' et 'levels.json' (support ancien/nouveau format)
    2. Parse le JSON et extrait la liste 'levels'
    3. Si aucun fichier trouvé ou invalide, utilise un niveau par défaut
    
    Returns:
        list: liste des dictionnaires de niveaux
    """
    levels = []
    levels_dir = os.path.dirname(__file__)
    level_filenames = ["levels (1).json", "level.json", "levels.json"]  # Prioritize levels (1).json for music support
    
    for name in level_filenames:
        level_path = os.path.join(levels_dir, "..", name)
        if not os.path.isfile(level_path):
            continue  # Fichier n'existe pas, passe au suivant
        
        try:
            with open(level_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Vérifie la structure: dict avec clé 'levels' contenant une liste non vide
                if isinstance(data, dict) and isinstance(data.get("levels"), list) and data["levels"]:
                    levels = data["levels"]
                    break  # Arrête après le premier fichier valide trouvé
        except Exception:
            continue  # Erreur de parsing, passe au fichier suivant

    # Si aucun niveau trouvé, crée un niveau par défaut
    if not levels:
        levels = [_default_level()]
    
    return levels

def apply_level(level, game_state):
    """Applique les données d'un niveau à l'état du jeu
    
    Convertit les données JSON en structures de jeu utilisables:
    - Paramètres du sol (position, limites)
    - Plateformes avec types et couleurs
    - Objectif (porte/zone de fin)
    - Point de spawn du joueur
    - Configurations des ennemis
    
    Args:
        level: dict - données du niveau depuis le JSON
        game_state: dict - état du jeu à modifier
    
    Returns:
        dict: l'état du jeu modifié
    """
    # Extraction et conversion des paramètres du sol
    game_state["GROUND_Y"] = int(level.get("ground", {}).get("y", GROUND_Y))
    game_state["GROUND_START_X"] = int(level.get("ground", {}).get("start_x", GROUND_START_X))
    game_state["GROUND_END_X"] = int(level.get("ground", {}).get("end_x", GROUND_END_X))
    
    # Traitement des plateformes
    platforms = []
    platform_colors = []
    platform_types = []
    
    for p in level.get("platforms", []):
        try:
            # Essaie de récupérer les dimensions avec différents noms de clés
            # Supporte 'w'/'width' et 'h'/'height' pour la flexibilité
            rx = int(p.get("x", 0))
            ry = int(p.get("y", 0))
            rw = int(p.get("w") or p.get("width") or 0)
            rh = int(p.get("h") or p.get("height") or 0)
        except Exception:
            # Fallback en cas d'erreur de conversion
            rx = int(p.get("x", 0))
            ry = int(p.get("y", 0))
            rw = int(p.get("w", 0))
            rh = int(p.get("h", 0))
        
        # Crée le rectangle pygame pour la collision
        platforms.append(pygame.Rect(rx, ry, rw, rh))
        # Parse la couleur avec gestion d'erreur
        platform_colors.append(_parse_color(p.get("color")))
        
        # Normalise le type de plateforme avec validation
        t = str(p.get("type", "platform") or "platform").lower()
        if t not in PLATFORM_TYPES:
            t = "platform"  # Type par défaut si invalide
        platform_types.append(t)
    
    game_state["platforms"] = platforms
    game_state["platform_colors"] = platform_colors
    game_state["platform_types"] = platform_types
    
    # Configuration de l'objectif (porte/zone de fin)
    g = level.get("goal", {})
    goal_rect = pygame.Rect(
        int(g.get("x", 2300)),      # Position X par défaut
        int(g.get("y", -30)),       # Position Y par défaut
        int(g.get("w", 70)),        # Largeur par défaut
        int(g.get("h", 110))        # Hauteur par défaut
    )
    game_state["goal_rect"] = goal_rect
    
    # Configuration du point de spawn
    s = level.get("spawn", {})
    spawn_point = pygame.Vector2(
        float(s.get("x", SCREEN_WIDTH / 2)),  # Centre de l'écran par défaut
        float(s.get("y", GROUND_Y - (head_radius + body_height + leg_height)))  # Au sol par défaut
    )
    game_state["spawn_point"] = spawn_point
    
    # Configuration des ennemis avec deepcopy pour éviter les références partagées
    level_enemy_configs = []
    raw_enemies = level.get("enemies", [])
    if isinstance(raw_enemies, list):
        for entry in raw_enemies:
            if isinstance(entry, dict):
                # deepcopy crée une copie indépendante de chaque configuration
                level_enemy_configs.append(deepcopy(entry))
    game_state["level_enemy_configs"] = level_enemy_configs
    
    # Configuration de la musique
    level_music = []
    raw_music = level.get("music", [])
    if isinstance(raw_music, list):
        for entry in raw_music:
            if isinstance(entry, dict):
                # Extrait les informations de musique (nom, type, données base64)
                music_info = {
                    "name": entry.get("name", ""),
                    "type": entry.get("type", ""),
                    "data": entry.get("data", "")
                }
                level_music.append(music_info)
    game_state["level_music"] = level_music
    
    return game_state
