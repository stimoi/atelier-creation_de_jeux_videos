# Ennemis
import pygame
import math
import random
from copy import deepcopy
from config.constants import *
from config.colors import *

def _canonical_monster_type(raw_type):
    """Normalise le type d'ennemi"""
    if not raw_type:
        return "basic"
    t = str(raw_type).lower()
    if t in MONSTER_TYPE_DEFAULTS:
        return t
    if t in ("walker", "ground"):
        return "basic"
    return "basic"

def create_monster_from_config(config, template_id=None):
    """Crée un ennemi depuis une configuration"""
    cfg = deepcopy(config)
    m_type = _canonical_monster_type(cfg.get("type"))
    defaults = MONSTER_TYPE_DEFAULTS[m_type]

    x = float(cfg.get("x", 0))
    y = float(cfg.get("y", 0))
    width = cfg.get("w") or cfg.get("width")
    height = cfg.get("h") or cfg.get("height")

    radius = cfg.get("radius")
    if radius is None:
        if width and height:
            radius = max(width, height) / 2
        else:
            radius = defaults["radius"]

    speed = cfg.get("speed", defaults["speed"])
    hp = int(cfg.get("hp", defaults["hp"]))
    dir_val = cfg.get("dir", defaults["dir"])
    direction = -1 if float(dir_val) < 0 else 1

    monster = {
        "pos": pygame.Vector2(x, y),
        "dir": direction,
        "type": m_type,
        "radius": radius,
        "speed": speed,
        "hp": hp,
        "hit_flash": 0.0,
    }

    if m_type == "flyer":
        monster["fly_phase"] = float(cfg.get("fly_phase", 0.0))
        monster["base_y"] = float(cfg.get("base_y", y))
    else:
        monster["vel_y"] = float(cfg.get("vel_y", 0.0))

    if template_id is not None:
        monster["template_id"] = template_id

    return monster

def spawn_random_monster():
    """Crée un ennemi aléatoire"""
    x = random.randint(100, 2500)
    
    # Types: tank (gros/lent), fast (petit/rapide), flyer (vole)
    r = random.random()
    if r < 0.3:
        m_type = "tank"
        radius = 32
        speed = 60
        hp = 3
        y = GROUND_Y - radius
        extra = {"vel_y": 0.0}
    elif r < 0.7:
        m_type = "fast"
        radius = 18
        speed = 140
        hp = 1
        y = GROUND_Y - radius
        extra = {"vel_y": 0.0}
    else:
        m_type = "flyer"
        radius = 22
        speed = 110
        hp = 1
        base_y = random.randint(GROUND_Y - 280, GROUND_Y - 140)
        y = base_y
        extra = {"fly_phase": random.uniform(0, 6.28), "base_y": base_y}

    data = {
        "pos": pygame.Vector2(x, y),
        "dir": random.choice([-1, 1]),
        "type": m_type,
        "radius": radius,
        "speed": speed,
        "hp": hp,
        "hit_flash": 0.0,
    }
    data.update(extra)
    return data

class EnemySystem:
    """Système de gestion des ennemis"""
    
    def __init__(self):
        self.monsters = []
        self.level_enemy_configs = []
        self.current_monster_cap = MAX_MONSTERS
        self.monster_spawn_timer = 0.0
    
    def instantiate_level_enemies(self):
        """Instancie les ennemis du niveau"""
        # Spawn automatique désactivé - pas de mobs au démarrage
        self.monsters = []
        self.current_monster_cap = 0
        self.monster_spawn_timer = 0.0
    
    def update(self, dt, platforms, ground_y):
        """Met à jour tous les ennemis"""
        for monster in self.monsters:
            # Mouvement horizontal
            monster["pos"].x += monster["dir"] * monster["speed"] * dt
            if monster["pos"].x < 50:
                monster["dir"] = 1
            if monster["pos"].x > 2500:
                monster["dir"] = -1

            if monster.get("type") == "flyer":
                # Vol stationnaire/ondulant
                monster["fly_phase"] += dt * 2.0
                monster["pos"].y = monster["base_y"] + math.sin(monster["fly_phase"]) * 25
            else:
                # Gravité (marcheurs)
                monster["vel_y"] += GRAVITY * dt
                monster["pos"].y += monster["vel_y"] * dt

                # Collision sol
                feet_y = monster["pos"].y + monster["radius"]
                if feet_y > ground_y:
                    monster["pos"].y = ground_y - monster["radius"]
                    monster["vel_y"] = 0

                # Collision plateformes (atterrir par dessus)
                if monster["vel_y"] >= 0:
                    monster_rect = pygame.Rect(int(monster["pos"].x - monster["radius"]),
                                               int(monster["pos"].y - monster["radius"]),
                                               monster["radius"]*2, monster["radius"]*2)
                    for plat in platforms:
                        if monster_rect.colliderect(plat):
                            plat_top = plat.top
                            if feet_y - monster["vel_y"] * dt <= plat_top + 2:
                                monster["pos"].y = plat_top - monster["radius"]
                                monster["vel_y"] = 0
                            break

            # Flash dégâts
            if monster["hit_flash"] > 0:
                monster["hit_flash"] -= dt
    
    def check_projectile_collision(self, projectiles, particles_system):
        """Vérifie les collisions projectiles-ennemis"""
        score = 0
        for proj in projectiles[:]:
            for monster in self.monsters[:]:
                if proj["pos"].distance_to(monster["pos"]) < projectile_radius + monster["radius"]:
                    monster["hp"] -= 1
                    monster["hit_flash"] = 0.2
                    
                    if monster["hp"] <= 0:
                        particles_system.create_particles(monster["pos"], PARTICLE_COLORS["explosion"], 12)
                        self.monsters.remove(monster)
                        score += 2 if monster["type"] == "tank" else 1
                    
                    if proj in projectiles:
                        projectiles.remove(proj)
                    break
        return score
    
    def check_player_collision(self, player_rect, particles_system):
        """Vérifie les collisions joueur-ennemis"""
        from game.physics import circle_rect_collision
        
        for monster in self.monsters[:]:
            if circle_rect_collision((monster["pos"].x, monster["pos"].y), monster["radius"], player_rect):
                particles_system.create_particles(monster["pos"], PARTICLE_COLORS["damage"], 15)
                return True
        return False
    
    def spawn_from_config(self):
        """Fait spawn les ennemis depuis les configs de niveau"""
        spawned = False
        if self.level_enemy_configs:
            active_ids = {m.get("template_id") for m in self.monsters if m.get("template_id") is not None}
            next_id = None
            for idx in range(len(self.level_enemy_configs)):
                if idx not in active_ids:
                    next_id = idx
                    break
            if next_id is not None:
                self.monsters.append(create_monster_from_config(self.level_enemy_configs[next_id], template_id=next_id))
                spawned = True
        else:
            if len(self.monsters) < self.current_monster_cap:
                self.monsters.append(spawn_random_monster())
                spawned = True
        
        return spawned
    
    def update_spawn_timer(self, dt):
        """Met à jour le timer de spawn"""
        self.monster_spawn_timer -= dt
        if self.monster_spawn_timer <= 0:
            if self.spawn_from_config():
                self.monster_spawn_timer = MONSTER_SPAWN_COOLDOWN
