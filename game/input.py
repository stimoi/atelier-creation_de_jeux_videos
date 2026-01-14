# Gestion des entrées (clavier, souris)
import pygame
from config.constants import *

class InputManager:
    """Gestionnaire des entrées utilisateur"""
    
    def __init__(self):
        self.keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_pressed = pygame.mouse.get_pressed()
    
    def update(self):
        """Met à jour l'état des entrées"""
        self.keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_pressed = pygame.mouse.get_pressed()
    
    def is_key_pressed(self, key):
        """Vérifie si une touche est pressée"""
        return self.keys[key]
    
    def is_mouse_pressed(self, button=1):
        """Vérifie si un bouton de la souris est pressé"""
        return self.mouse_pressed[button]
    
    def get_mouse_pos(self):
        """Retourne la position de la souris"""
        return self.mouse_pos
    
    def is_moving_left(self):
        """Vérifie si le joueur veut aller à gauche"""
        return self.keys[pygame.K_q] or self.keys[pygame.K_LEFT]
    
    def is_moving_right(self):
        """Vérifie si le joueur veut aller à droite"""
        return self.keys[pygame.K_d] or self.keys[pygame.K_RIGHT]
    
    def is_jumping(self):
        """Vérifie si le joueur veut sauter"""
        return self.keys[pygame.K_SPACE]
    
    def is_dashing(self):
        """Vérifie si le joueur veut dasher"""
        return self.keys[pygame.K_LSHIFT] or self.keys[pygame.K_RSHIFT]
    
    def is_shooting(self):
        """Vérifie si le joueur veut tirer"""
        return self.mouse_pressed[1]  # Clic gauche
    
    def get_movement_direction(self):
        """Retourne la direction de mouvement horizontale"""
        if self.is_moving_left():
            return -1
        elif self.is_moving_right():
            return 1
        return 0
    
    def get_aim_direction(self, player_pos, camera):
        """Retourne la direction de visée"""
        mouse_world = camera.screen_to_world(self.mouse_pos)
        aim_vec = mouse_world - pygame.Vector2(player_pos)
        
        if aim_vec.length_squared() == 0:
            return pygame.Vector2(1, 0)  # Direction par défaut
        
        return aim_vec.normalize()
