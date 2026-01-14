# Constantes du jeu
import pygame

# === Écran ===
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 769

# === Sol et terrain ===
GROUND_Y = 680
GROUND_START_X = 0
GROUND_END_X = 3000

# === Physique ===
GRAVITY = 800
JUMP_FORCE = -600
MOVE_SPEED = 300
PROJECTILE_SPEED = 800

# === Stamina ===
STAMINA_MAX = 100
STAMINA_JUMP_COST = 10
STAMINA_REGEN_DELAY = 4.0
STAMINA_REGEN_INTERVAL = 0.5
STAMINA_REGEN_AMOUNT = 5
DOUBLE_JUMP_COST = 15
DASH_COST = 10
DASH_SPEED = 900
DASH_DURATION = 0.2

# === Jeu ===
FPS = 60
MAX_MONSTERS = 3
MONSTER_SPAWN_COOLDOWN = 2.0
DEATH_BELOW_Y = GROUND_Y + 1500

# === Caméra ===
CAMERA_LAG = 0.05

# === Joueur ===
head_radius = 20
body_height = 40
leg_height = 30
arm_length = 25

# === Projectiles ===
projectile_radius = 6

# === Ennemis ===
monster_radius = 25

# === Transitions de niveaux ===
LEVEL_TRANSITION_FADE_OUT = 0.6
LEVEL_TRANSITION_FADE_IN = 0.6

# === Invulnérabilité ===
invuln_time = 1.5

# === Types d'ennemis par défaut ===
MONSTER_TYPE_DEFAULTS = {
    "tank": {"radius": 32, "speed": 60, "hp": 3, "dir": 1},
    "fast": {"radius": 18, "speed": 140, "hp": 1, "dir": 1},
    "flyer": {"radius": 22, "speed": 110, "hp": 1, "dir": 1},
    "basic": {"radius": 20, "speed": 100, "hp": 1, "dir": 1},
}

# === États du jeu ===
GAME_STATES = {
    "MENU": "MENU",
    "PLAYING": "PLAYING", 
    "PAUSED": "PAUSED"
}

# === Types de plateformes ===
PLATFORM_TYPES = ["platform", "block", "decor"]
