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
        """Met à jour l'état du joueur à chaque frame
        
        Gère tous les aspects du joueur:
        - Mouvements horizontaux (Q/D, flèches)
        - Sauts simples et doubles avec gestion de la stamina
        - Dash avec cooldown et consommation de stamina
        - Gravité et collisions
        - Régénération de stamina avec délais
        - Animations (cycle de marche, clignements, recul de tir)
        
        Args:
            dt: float - delta time en secondes
            keys: pygame.key.get_pressed() - états des touches
            platforms: list - liste des plateformes
            platform_types: list - types des plateformes
            ground_y, ground_start_x, ground_end_x: paramètres du sol
        
        Returns:
            bool: True si le joueur est en mouvement, False sinon
        """
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
            if self.on_ground and self.stamina >= 0:
                self.vel_y = JUMP_FORCE
                self.stamina = max(0, self.stamina - 0)
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
        
        # Gestion de la stamina avec système de régénération par paliers
        # La stamina ne se régénère qu'après un délai d'inactivité (STAMINA_REGEN_DELAY)
        self.stamina_idle_timer += dt
        if self.stamina_idle_timer >= STAMINA_REGEN_DELAY and self.stamina < STAMINA_MAX:
            # Accumulateur pour la régénération (permet un contrôle fin du timing)
            self.stamina_regen_timer += dt
            # Boucle while pour gérer les régénérations multiples si dt est grand
            while self.stamina_regen_timer >= STAMINA_REGEN_INTERVAL and self.stamina < STAMINA_MAX:
                self.stamina = min(STAMINA_MAX, self.stamina + STAMINA_REGEN_AMOUNT)
                self.stamina_regen_timer -= STAMINA_REGEN_INTERVAL
            # Réinitialise le timer une fois la stamina pleine
            if self.stamina >= STAMINA_MAX:
                self.stamina_regen_timer = 0.0
        else:
            # Réinitialise si le joueur n'est pas inactif
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
        """Vérifie si le joueur est au sol et gère l'atterrissage
        
        Logique complexe de détection du sol:
        1. Vérifie d'abord le sol infini (limité en X)
        2. Ensuite vérifie les plateformes semi-solides
        3. Ajuste la position et la vélocité si atterrissage
        
        Args:
            platforms: list - rectangles des plateformes
            platform_types: list - types des plateformes
            ground_y, ground_start_x, ground_end_x: paramètres du sol
        
        Returns:
            bool: True si le joueur est au sol, False sinon
        """
        # Position des pieds du joueur (bas du personnage)
        feet_y = self.pos.y + head_radius + body_height + leg_height
        
        # Sol infini mais limité horizontalement (crée un sol continu)
        # La marge de 0.1 évite les problèmes de précision flottante
        if feet_y >= ground_y - 0.1 and ground_start_x <= self.pos.x <= ground_end_x:
            if self.on_ground:
                return True  # Déjà au sol, pas d'ajustement
            # Premier contact avec le sol: ajuste position et arrête la chute
            self.pos.y = ground_y - (head_radius + body_height + leg_height)
            self.vel_y = 0
            return True
        
        # Vérification des plateformes (seulement celles de type 'platform')
        # Les plateformes ont une zone de détection élargie de 5px pour faciliter l'atterrissage
        for i, plat in enumerate(platforms):
            if i < len(platform_types) and platform_types[i] == 'platform':
                # Vérifie si le joueur est dans la zone X de la plateforme et proche verticalement
                if plat.left - 5 < self.pos.x < plat.right + 5 and abs(feet_y - plat.top) <= 6:
                    # Ajuste la position pour que les pieds touchent exactement le haut de la plateforme
                    self.pos.y = plat.top - (head_radius + body_height + leg_height)
                    self.vel_y = 0
                    return True
        
        return False
    
    def _handle_platform_collisions(self, platforms, platform_types):
        """Gère les collisions avec les plateformes pendant la chute
        
        Cette méthode est différente de _check_ground_collision:
        - Elle ne gère que l'atterrissage sur les plateformes (pas le sol)
        - Elle utilise une prédiction pour éviter les "téléportations"
        - Elle ne s'active que si le joueur descend (vel_y >= 0)
        
        Args:
            platforms: list - rectangles des plateformes
            platform_types: list - types des plateformes
        """
        # Crée le rectangle de collision complet du joueur
        # Utilise la tête comme base et ajoute le corps et les jambes
        player_rect = pygame.Rect(
            self.pos.x - head_radius,
            self.pos.y - head_radius,
            head_radius * 2,
            head_radius * 2 + body_height + leg_height
        )
        
        # Ne vérifie les collisions que si le joueur descend ou est stationnaire
        # Évite les collisions lorsqu'on saute à travers une plateforme
        if self.vel_y >= 0:
            for i, plat in enumerate(platforms):
                if i < len(platform_types) and platform_types[i] == 'platform':
                    if player_rect.colliderect(plat):
                        # Calcul de la position des pieds et du haut de la plateforme
                        feet_y = self.pos.y + head_radius + body_height + leg_height
                        plat_top = plat.top
                        
                        # Vérification critique: prédit où étaient les pieds à la frame précédente
                        # Utilise dt approximatif (0.016s = 60 FPS) pour la prédiction
                        # Évite que le joueur ne "téléporte" à travers une plateforme
                        if feet_y - self.vel_y * 0.016 <= plat_top:
                            # Atterrissage validé: ajuste position et arrête la chute
                            self.pos.y = plat_top - (head_radius + body_height + leg_height)
                            self.vel_y = 0
                            break  # Une seule plateforme à la fois
    
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
        """Crée un projectile vers la position de la souris
        
        Calcul vectoriel pour déterminer la direction du tir:
        1. Calcule le vecteur direction (mouse - player)
        2. Normalise ce vecteur pour obtenir une direction unitaire
        3. Positionne le projectile juste devant le joueur
        4. Applique la vélocité dans la direction calculée
        
        Args:
            mouse_world_pos: pygame.Vector2 - position de la souris dans le monde
        
        Returns:
            dict or None: dictionnaire du projectile {pos, vel} ou None si impossible
        """
        # Vecteur du joueur vers la souris
        dx = mouse_world_pos.x - self.pos.x
        dy = mouse_world_pos.y - self.pos.y
        
        # Distance euclidienne (évite division par zéro)
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            # Normalisation: vecteur direction de longueur 1
            dir_x = dx / distance
            dir_y = dy / distance
            
            # Position de départ du projectile: légèrement devant le joueur
            # Évite que le projectile ne collisionne immédiatement avec le joueur
            proj_x = self.pos.x + dir_x * (head_radius + 10)
            proj_y = self.pos.y + dir_y * (head_radius + 10)
            
            # Animation de recul visuel (très courte durée)
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
