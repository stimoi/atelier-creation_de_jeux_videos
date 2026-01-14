# Rendu des entités (joueur, ennemis, projectiles)
import pygame
import math
from config.constants import *
from config.colors import *

class EntitiesRenderer:
    """Classe responsable du rendu des entités du jeu"""
    
    def draw_player(self, screen, player, camera_offset, keys, is_invulnerable, invuln_timer):
        """Dessine le joueur complet avec toutes ses parties"""
        p_center_screen = (int(player.pos.x - camera_offset.x), int(player.pos.y - camera_offset.y))
        moving_now = keys[pygame.K_q] or keys[pygame.K_LEFT] or keys[pygame.K_d] or keys[pygame.K_RIGHT]
        bob = math.sin(player.walk_cycle * 12) * 2 if moving_now else 0
        render_center = (p_center_screen[0], p_center_screen[1] + int(bob))

        # Effet d'invulnérabilité (clignotement)
        if not is_invulnerable or int(invuln_timer * 10) % 2 == 0:
            self._draw_player_body(screen, render_center, player, moving_now)
            self._draw_player_gun(screen, render_center, player, camera_offset)
    
    def _draw_player_body(self, screen, render_center, player, moving_now):
        """Dessine le corps du joueur"""
        # Tête avec contour
        pygame.draw.circle(screen, skin_color, render_center, head_radius)
        pygame.draw.circle(screen, (0, 0, 0), render_center, head_radius, 3)
        
        # Visage avec yeux
        self._draw_player_face(screen, render_center)
        
        # Cheveux
        self._draw_player_hair(screen, render_center)
        
        # Cou et torse
        self._draw_player_torso(screen, render_center, player, moving_now)
        
        # Bras
        self._draw_player_arms(screen, render_center, player, moving_now)
        
        # Jambes
        self._draw_player_legs(screen, render_center, player.walk_cycle, moving_now)
    
    def _draw_player_face(self, screen, render_center):
        """Dessine le visage du joueur"""
        eye_offset = 7
        left_eye_pos = (render_center[0] - eye_offset, render_center[1] - 5)
        right_eye_pos = (render_center[0] + eye_offset, render_center[1] - 5)
        
        # Clignement des yeux
        blink_close = 0  # Sera géré par le joueur
        
        if blink_close > 0:
            # Yeux fermés (lignes)
            pygame.draw.line(screen, (0, 0, 0), (int(left_eye_pos[0]-3), int(left_eye_pos[1])), (int(left_eye_pos[0]+3), int(left_eye_pos[1])), 2)
            pygame.draw.line(screen, (0, 0, 0), (int(right_eye_pos[0]-3), int(right_eye_pos[1])), (int(right_eye_pos[0]+3), int(right_eye_pos[1])), 2)
        else:
            # Yeux ouverts (cercles)
            pygame.draw.circle(screen, (0, 0, 0), (int(left_eye_pos[0]), int(left_eye_pos[1])), 3)
            pygame.draw.circle(screen, (0, 0, 0), (int(right_eye_pos[0]), int(right_eye_pos[1])), 3)
        
        # Sourire
        pygame.draw.arc(screen, (0, 0, 0), 
                       (render_center[0] - head_radius, render_center[1] - head_radius, 
                        head_radius*2, head_radius*2), 3.8, 5.0, 3)
    
    def _draw_player_hair(self, screen, render_center):
        """Dessine les cheveux du joueur"""
        hair_top = render_center[1] - head_radius - 8
        hair_bottom = render_center[1] - head_radius + 5
        
        # Base de cheveux
        hair_points = [
            (render_center[0] - 16, hair_top + 3),
            (render_center[0] - 13, hair_top),
            (render_center[0] - 8, hair_top + 2),
            (render_center[0] - 3, hair_top),
            (render_center[0], hair_top - 2),
            (render_center[0] + 3, hair_top),
            (render_center[0] + 8, hair_top + 2),
            (render_center[0] + 13, hair_top),
            (render_center[0] + 16, hair_top + 3),
            (render_center[0] + 14, hair_bottom),
            (render_center[0] + 10, hair_bottom + 3),
            (render_center[0] + 6, hair_bottom + 5),
            (render_center[0] + 2, hair_bottom + 7),
            (render_center[0], hair_bottom + 5),
            (render_center[0] - 2, hair_bottom + 7),
            (render_center[0] - 6, hair_bottom + 5),
            (render_center[0] - 10, hair_bottom + 3),
            (render_center[0] - 14, hair_bottom),
        ]
        
        if len(hair_points) >= 3:
            pygame.draw.polygon(screen, HAIR_COLOR, hair_points)
            pygame.draw.polygon(screen, (40, 30, 15), hair_points, 2)
        
        # Mèches individuelles
        pygame.draw.line(screen, HAIR_COLOR, (render_center[0] - 7, hair_bottom + 2), (render_center[0] - 5, hair_bottom + 8), 3)
        pygame.draw.line(screen, HAIR_COLOR, (render_center[0] + 7, hair_bottom + 2), (render_center[0] + 5, hair_bottom + 8), 3)
        pygame.draw.line(screen, HAIR_COLOR, (render_center[0], hair_bottom), (render_center[0], hair_bottom + 6), 3)
    
    def _draw_player_torso(self, screen, render_center, player, moving_now):
        """Dessine le torse du joueur"""
        # Cou
        neck_width = 10
        neck_height = 6
        neck_rect = pygame.Rect(render_center[0] - neck_width//2, render_center[1] + head_radius - 2, neck_width, neck_height)
        pygame.draw.rect(screen, HAND_COLOR, neck_rect, border_radius=3)

        # Torse
        torso_width = 26
        tilt = player.direction * (2 if moving_now else 0)
        torso_rect = pygame.Rect(0, 0, torso_width, body_height)
        torso_rect.centerx = render_center[0] + int(tilt)
        torso_rect.top = render_center[1] + head_radius
        pygame.draw.rect(screen, SHIRT_COLOR, torso_rect, border_radius=6)
        pygame.draw.rect(screen, (0, 0, 0), torso_rect, 2, border_radius=6)
    
    def _draw_player_arms(self, screen, render_center, player, moving_now):
        """Dessine les bras du joueur"""
        shoulder_y = render_center[1] + head_radius + 12
        base_arm_y = render_center[1] + head_radius + 16
        arm_y = base_arm_y - (6 if not player.on_ground else 0)
        arm_angle = math.sin(player.walk_cycle * 10) * 15
        arm_offset = arm_length * math.cos(math.radians(arm_angle))
        
        # Recul du tir
        if player.shoot_recoil > 0:
            recoil_factor = 1.0 - min(1.0, player.shoot_recoil / 0.12) * 0.6
            arm_offset *= recoil_factor
            arm_y -= 2
        if not player.on_ground:
            arm_offset *= 0.6
        
        # Calcul des positions des bras
        left_shoulder = (int(render_center[0] - 8), shoulder_y)
        left_elbow = (int(render_center[0] - 12 - arm_offset//2), arm_y - 5)
        left_hand = (int(render_center[0] - arm_offset), int(arm_y))
        
        right_shoulder = (int(render_center[0] + 8), shoulder_y)
        right_elbow = (int(render_center[0] + 12 + arm_offset//2), arm_y - 5)
        right_hand = (int(render_center[0] + arm_offset), int(arm_y))
        
        # Dessin des bras
        pygame.draw.line(screen, SHIRT_COLOR, left_shoulder, left_elbow, 6)
        pygame.draw.line(screen, SHIRT_COLOR, left_elbow, left_hand, 5)
        pygame.draw.line(screen, SHIRT_COLOR, right_shoulder, right_elbow, 6)
        pygame.draw.line(screen, SHIRT_COLOR, right_elbow, right_hand, 5)
        
        # Mains
        hand_size = 6
        left_hand_rect = pygame.Rect(left_hand[0] - hand_size//2, left_hand[1] - hand_size//2, hand_size, hand_size)
        right_hand_rect = pygame.Rect(right_hand[0] - hand_size//2, right_hand[1] - hand_size//2, hand_size, hand_size)
        
        pygame.draw.rect(screen, HAND_COLOR, left_hand_rect, border_radius=3)
        pygame.draw.rect(screen, (0, 0, 0), left_hand_rect, 1, border_radius=3)
        pygame.draw.rect(screen, HAND_COLOR, right_hand_rect, border_radius=3)
        pygame.draw.rect(screen, (0, 0, 0), right_hand_rect, 1, border_radius=3)
        
        # Articulations
        pygame.draw.circle(screen, SHIRT_COLOR, left_elbow, 3)
        pygame.draw.circle(screen, (0, 0, 0), left_elbow, 3, 1)
        pygame.draw.circle(screen, SHIRT_COLOR, right_elbow, 3)
        pygame.draw.circle(screen, (0, 0, 0), right_elbow, 3, 1)
    
    def _draw_player_legs(self, screen, render_center, walk_cycle, moving_now):
        """Dessine les jambes du joueur"""
        leg_width = 8
        foot_width = 12
        foot_height = 6
        
        # Animation de marche
        walk_offset = 0
        if moving_now:
            walk_offset = math.sin(walk_cycle * 8) * 8
        
        # Positions des jambes
        torso_rect = pygame.Rect(0, 0, 26, body_height)
        torso_rect.centerx = render_center[0]
        torso_rect.top = render_center[1] + head_radius
        
        left_leg_x = torso_rect.centerx - 6
        left_leg_y = torso_rect.bottom
        left_leg_end_y = left_leg_y + leg_height - 5 + walk_offset
        left_foot_y = left_leg_end_y
        
        right_leg_x = torso_rect.centerx + 6
        right_leg_y = torso_rect.bottom
        right_leg_end_y = right_leg_y + leg_height - 5 - walk_offset
        right_foot_y = right_leg_end_y
        
        # Dessin des jambes
        pygame.draw.line(screen, PANTS_COLOR, (left_leg_x, left_leg_y), (left_leg_x, left_leg_end_y), leg_width)
        pygame.draw.line(screen, PANTS_COLOR, (right_leg_x, right_leg_y), (right_leg_x, right_leg_end_y), leg_width)
        
        # Dessin des pieds
        left_foot_rect = pygame.Rect(left_leg_x - foot_width//2, left_foot_y, foot_width, foot_height)
        right_foot_rect = pygame.Rect(right_leg_x - foot_width//2, right_foot_y, foot_width, foot_height)
        
        pygame.draw.rect(screen, SHOE_COLOR, left_foot_rect, border_radius=3)
        pygame.draw.rect(screen, SHOE_COLOR, right_foot_rect, border_radius=3)
        pygame.draw.rect(screen, (0, 0, 0), left_foot_rect, 1, border_radius=3)
        pygame.draw.rect(screen, (0, 0, 0), right_foot_rect, 1, border_radius=3)
    
    def _draw_player_gun(self, screen, render_center, player, camera_offset):
        """Dessine le pistolet dans la main du joueur"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_world = pygame.Vector2(mouse_x + camera_offset.x, mouse_y + camera_offset.y)
        aim_vec = (mouse_world - pygame.Vector2(player.pos.x, player.pos.y))
        
        if aim_vec.length_squared() == 0:
            aim_dir = pygame.Vector2(player.direction, 0)
        else:
            aim_dir = aim_vec.normalize()
        
        # Choisir la main avant selon l'orientation
        front_hand_offset = arm_length * math.cos(math.radians(math.sin(player.walk_cycle * 10) * 15))
        if player.shoot_recoil > 0:
            recoil_factor = 1.0 - min(1.0, player.shoot_recoil / 0.12) * 0.6
            front_hand_offset *= recoil_factor
        
        front_hand_x = render_center[0] + (front_hand_offset if aim_dir.x >= 0 else -front_hand_offset)
        front_hand_y = render_center[1] + head_radius + 16 - (6 if not player.on_ground else 0)
        front_hand = (int(front_hand_x), int(front_hand_y))
        
        # Paramètres du pistolet
        grip_len, body_len, barrel_len = 8, 12, 10
        thickness = 5
        
        # Points du pistolet
        base = pygame.Vector2(front_hand)
        perp = pygame.Vector2(-aim_dir.y, aim_dir.x)
        grip_end = base - perp * 4 + aim_dir * 2
        body_end = base + aim_dir * body_len
        barrel_end = body_end + aim_dir * barrel_len
        
        # Dessin du pistolet
        pygame.draw.line(screen, GUN_COLORS["grip"], base, grip_end, thickness)
        pygame.draw.line(screen, GUN_COLORS["body"], base, body_end, thickness)
        pygame.draw.line(screen, GUN_COLORS["barrel"], body_end, barrel_end, 3)
    
    def draw_enemies(self, screen, enemies, camera_offset):
        """Dessine tous les ennemis"""
        for monster in enemies:
            monster_screen = (int(monster["pos"].x - camera_offset.x), 
                             int(monster["pos"].y - camera_offset.y))
            r = monster["radius"]
            
            # Couleur selon flash
            base_color = MONSTER_COLORS.get(monster["type"], MONSTER_COLORS["basic"])
            monster_color = (255, 220, 220) if monster["hit_flash"] > 0 else base_color
            
            if monster["type"] == "tank":
                self._draw_tank_enemy(screen, monster_screen, r, monster_color)
            elif monster["type"] == "fast":
                self._draw_fast_enemy(screen, monster_screen, r, monster_color, monster["dir"])
            elif monster["type"] == "flyer":
                self._draw_flyer_enemy(screen, monster_screen, r, monster_color)
            else:
                self._draw_basic_enemy(screen, monster_screen, r, monster_color)
    
    def _draw_tank_enemy(self, screen, pos, r, color):
        """Dessine un ennemi tank (gros et lent)"""
        pygame.draw.circle(screen, color, pos, r)
        pygame.draw.circle(screen, (0, 0, 0), pos, r, 3)
        
        # Sac à dos / blindage
        backpack_x = pos[0] - 18
        backpack_y = pos[1]
        backpack_rect = pygame.Rect(backpack_x - 12, backpack_y - 18, 24, 36)
        pygame.draw.rect(screen, (60, 40, 20), backpack_rect)
        pygame.draw.rect(screen, (0, 0, 0), backpack_rect, 2)
        pygame.draw.circle(screen, (100, 80, 50), (backpack_x, backpack_y - 6), 5)
        
        # Yeux
        pygame.draw.circle(screen, (255, 255, 0), (pos[0] - 9, pos[1] - 6), 4)
        pygame.draw.circle(screen, (255, 255, 0), (pos[0] + 9, pos[1] - 6), 4)
        pygame.draw.circle(screen, (0, 0, 0), (pos[0] - 9, pos[1] - 6), 2)
        pygame.draw.circle(screen, (0, 0, 0), (pos[0] + 9, pos[1] - 6), 2)
    
    def _draw_fast_enemy(self, screen, pos, r, color, direction):
        """Dessine un ennemi rapide (petit et vite)"""
        pygame.draw.circle(screen, color, pos, r)
        pygame.draw.circle(screen, (0, 0, 0), pos, r, 3)
        
        # Yeux plus rapprochés
        pygame.draw.circle(screen, (0, 0, 0), (pos[0] - 6, pos[1] - 4), 3)
        pygame.draw.circle(screen, (0, 0, 0), (pos[0] + 6, pos[1] - 4), 3)
        
        # Traînée légère
        pygame.draw.circle(screen, (255, 200, 120), (pos[0] - direction*r, pos[1]), max(1, r//4))
    
    def _draw_flyer_enemy(self, screen, pos, r, color):
        """Dessine un ennemi volant"""
        pygame.draw.circle(screen, color, pos, r)
        pygame.draw.circle(screen, (0, 0, 0), pos, r, 3)
        
        # Ailes
        wing_span = r + 10
        left_wing = [(pos[0] - 2, pos[1]),
                     (pos[0] - wing_span, pos[1] - 6),
                     (pos[0] - wing_span + 6, pos[1] + 6)]
        right_wing = [(pos[0] + 2, pos[1]),
                      (pos[0] + wing_span, pos[1] - 6),
                      (pos[0] + wing_span - 6, pos[1] + 6)]
        
        pygame.draw.polygon(screen, (180, 210, 255), left_wing)
        pygame.draw.polygon(screen, (180, 210, 255), right_wing)
        pygame.draw.polygon(screen, (0, 0, 0), left_wing, 2)
        pygame.draw.polygon(screen, (0, 0, 0), right_wing, 2)
    
    def _draw_basic_enemy(self, screen, pos, r, color):
        """Dessine un ennemi basique"""
        pygame.draw.circle(screen, color, pos, r)
        pygame.draw.circle(screen, (0, 0, 0), pos, r, 3)
        
        # Yeux simples
        pygame.draw.circle(screen, (0, 0, 0), (pos[0] - 7, pos[1] - 5), 3)
        pygame.draw.circle(screen, (0, 0, 0), (pos[0] + 7, pos[1] - 5), 3)
    
    def draw_projectiles(self, screen, projectiles, camera_offset):
        """Dessine tous les projectiles"""
        for proj in projectiles:
            proj_screen = (int(proj["pos"].x - camera_offset.x), int(proj["pos"].y - camera_offset.y))
            pygame.draw.circle(screen, (150, 255, 150), proj_screen, projectile_radius + 2)
            pygame.draw.circle(screen, (0, 255, 0), proj_screen, projectile_radius)
            pygame.draw.circle(screen, (255, 255, 255), proj_screen, projectile_radius - 3)
    
    def draw_particles(self, screen, particles, camera_offset):
        """Dessine toutes les particules"""
        for part in particles:
            if part["life"] > 0:
                part_screen = (int(part["pos"].x - camera_offset.x), int(part["pos"].y - camera_offset.y))
                alpha = int(255 * part["life"])
                color = tuple(min(255, max(0, int(c * part["life"]))) for c in part["color"])
                pygame.draw.circle(screen, color, part_screen, 3)
