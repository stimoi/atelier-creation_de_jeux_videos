# Joueur
import pygame
import math
import random
from config.constants import *
from config.colors import *

class Player:
    """Classe représentant le joueur"""
    
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel_y = 0
        self.direction = 1
        self.walk_cycle = 0
        self.blink_timer = 0.0
        self.blink_close = 0.0
        self.prev_on_ground = True
        self.shoot_recoil = 0.0
        self.stamina = STAMINA_MAX
        self.stamina_idle_timer = 0.0
        self.stamina_regen_timer = 0.0
        self.air_jumps_left = 1
        self.jump_was_pressed = False
        self.dash_was_pressed = False
        self.dash_timer = 0.0
        self.dash_direction = 1
        self.on_ground = False
    
    def update(self, dt, keys, platforms, platform_types, ground_y, ground_start_x, ground_end_x):
        """Met à jour le joueur"""
        # Mouvements horizontaux
        moving = False
        if keys[pygame.K_q] or keys[pygame.K_LEFT]:
            self.pos.x -= MOVE_SPEED * dt
            self.direction = -1
            moving = True
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.pos.x += MOVE_SPEED * dt
            self.direction = 1
            moving = True
        
        if moving:
            self.walk_cycle += 10 * dt
        else:
            self.walk_cycle = 0
        
        # Détection sol/plateforme
        self.on_ground = self._check_ground_collision(platforms, platform_types, ground_y, ground_start_x, ground_end_x)
        
        # Saut
        space_pressed = keys[pygame.K_SPACE]
        if space_pressed and not self.jump_was_pressed:
            if self.on_ground and self.stamina >= STAMINA_JUMP_COST:
                self.vel_y = JUMP_FORCE
                self.stamina = max(0, self.stamina - STAMINA_JUMP_COST)
                self.stamina_idle_timer = 0.0
                self.stamina_regen_timer = 0.0
                self.air_jumps_left = 1
            elif not self.on_ground and self.air_jumps_left > 0 and self.stamina >= DOUBLE_JUMP_COST:
                self.vel_y = JUMP_FORCE
                self.stamina = max(0, self.stamina - DOUBLE_JUMP_COST)
                self.stamina_idle_timer = 0.0
                self.stamina_regen_timer = 0.0
                self.air_jumps_left -= 1
        
        # Dash
        dash_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if dash_pressed and not self.dash_was_pressed and self.dash_timer <= 0 and self.stamina >= DASH_COST:
            desired_dir = 0
            if keys[pygame.K_q] or keys[pygame.K_LEFT]:
                desired_dir = -1
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                desired_dir = 1
            else:
                desired_dir = self.direction
            
            if desired_dir != 0:
                self.dash_direction = desired_dir
                self.dash_timer = DASH_DURATION
                self.stamina = max(0, self.stamina - DASH_COST)
                self.stamina_idle_timer = 0.0
                self.stamina_regen_timer = 0.0
        
        self.jump_was_pressed = space_pressed
        self.dash_was_pressed = dash_pressed
        
        # Gravité
        self.vel_y += GRAVITY * dt
        self.pos.y += self.vel_y * dt
        
        # Collisions avec les plateformes
        self._handle_platform_collisions(platforms, platform_types)
        
        # Limites
        self.pos.x = max(head_radius, self.pos.x)
        
        # Dash
        if self.dash_timer > 0:
            self.pos.x += self.dash_direction * DASH_SPEED * dt
            self.dash_timer = max(0.0, self.dash_timer - dt)
        
        # Régénération stamina
        self.stamina_idle_timer += dt
        if self.stamina_idle_timer >= STAMINA_REGEN_DELAY and self.stamina < STAMINA_MAX:
            self.stamina_regen_timer += dt
            while self.stamina_regen_timer >= STAMINA_REGEN_INTERVAL and self.stamina < STAMINA_MAX:
                self.stamina = min(STAMINA_MAX, self.stamina + STAMINA_REGEN_AMOUNT)
                self.stamina_regen_timer -= STAMINA_REGEN_INTERVAL
            if self.stamina >= STAMINA_MAX:
                self.stamina_regen_timer = 0.0
        else:
            self.stamina_regen_timer = 0.0
        
        # Animations
        self.blink_timer -= dt
        if self.blink_timer <= 0 and self.blink_close <= 0:
            self.blink_close = 0.12
            self.blink_timer = random.uniform(2.0, 5.0)
        if self.blink_close > 0:
            self.blink_close -= dt
        if self.shoot_recoil > 0:
            self.shoot_recoil -= dt
        
        return moving
    
    def _check_ground_collision(self, platforms, platform_types, ground_y, ground_start_x, ground_end_x):
        """Vérifie si le joueur est au sol"""
        feet_y = self.pos.y + head_radius + body_height + leg_height
        
        # Sol infini limité en X
        if feet_y >= ground_y - 0.1 and ground_start_x <= self.pos.x <= ground_end_x:
            if self.on_ground:
                return True
            self.pos.y = ground_y - (head_radius + body_height + leg_height)
            self.vel_y = 0
            return True
        
        # Plateformes
        for i, plat in enumerate(platforms):
            if i < len(platform_types) and platform_types[i] == 'platform':
                if plat.left - 5 < self.pos.x < plat.right + 5 and abs(feet_y - plat.top) <= 6:
                    self.pos.y = plat.top - (head_radius + body_height + leg_height)
                    self.vel_y = 0
                    return True
        
        return False
    
    def _handle_platform_collisions(self, platforms, platform_types):
        """Gère les collisions avec les plateformes"""
        # Créer le rectangle de collision du joueur
        player_rect = pygame.Rect(
            self.pos.x - head_radius,
            self.pos.y - head_radius,
            head_radius * 2,
            head_radius * 2 + body_height + leg_height
        )
        
        # Vérifier les collisions avec les plateformes (atterrissage)
        if self.vel_y >= 0:
            for i, plat in enumerate(platforms):
                if i < len(platform_types) and platform_types[i] == 'platform':
                    if player_rect.colliderect(plat):
                        feet_y = self.pos.y + head_radius + body_height + leg_height
                        plat_top = plat.top
                        if feet_y - self.vel_y * 0.016 <= plat_top:  # dt approximatif
                            self.pos.y = plat_top - (head_radius + body_height + leg_height)
                            self.vel_y = 0
                            break
    
    def get_rect(self):
        """Retourne le rectangle de collision du joueur"""
        return pygame.Rect(
            int(self.pos.x - head_radius),
            int(self.pos.y - head_radius),
            head_radius * 2,
            head_radius * 2 + body_height + leg_height
        )
    
    def get_feet_rect(self):
        """Retourne le rectangle des pieds du joueur"""
        return pygame.Rect(
            int(self.pos.x - head_radius), 
            int(self.pos.y + head_radius + body_height), 
            head_radius*2, 
            leg_height
        )
    
    def shoot(self, mouse_world_pos):
        """Crée un projectile vers la position de la souris"""
        dx = mouse_world_pos.x - self.pos.x
        dy = mouse_world_pos.y - self.pos.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            dir_x = dx / distance
            dir_y = dy / distance
            
            proj_x = self.pos.x + dir_x * (head_radius + 10)
            proj_y = self.pos.y + dir_y * (head_radius + 10)
            
            # Animation de recul
            self.shoot_recoil = 0.12
            
            return {
                "pos": pygame.Vector2(proj_x, proj_y),
                "vel": pygame.Vector2(dir_x * PROJECTILE_SPEED, dir_y * PROJECTILE_SPEED)
            }
        
        return None
    
    def reset(self, spawn_point):
        """Réinitialise le joueur à un point de spawn"""
        self.pos = spawn_point.copy()
        self.vel_y = 0
        self.stamina = STAMINA_MAX
        self.stamina_idle_timer = 0.0
        self.stamina_regen_timer = 0.0
        self.air_jumps_left = 1
        self.jump_was_pressed = False
        self.dash_was_pressed = False
        self.dash_timer = 0.0
        self.dash_direction = 1
        self.shoot_recoil = 0.0
        self.prev_on_ground = True
    
    def is_dead(self, death_below_y):
        """Vérifie si le joueur est mort (tombé trop bas)"""
        return self.pos.y > death_below_y
