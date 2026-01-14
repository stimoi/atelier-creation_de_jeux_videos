# Caméra
import pygame
from config.constants import *

class Camera:
    """Système de caméra avec effet de suivi fluide"""
    
    def __init__(self):
        self.offset = pygame.Vector2(0, 0)
        self.lag = CAMERA_LAG
    
    def update(self, target_pos):
        """Met à jour la position de la caméra pour suivre une cible"""
        target_x = target_pos.x - SCREEN_WIDTH // 2
        target_y = target_pos.y - SCREEN_HEIGHT // 2
        
        self.offset.x += (target_x - self.offset.x) * self.lag
        self.offset.y += (target_y - self.offset.y) * self.lag
    
    def set_position(self, x, y):
        """Définit directement la position de la caméra"""
        self.offset.x = x
        self.offset.y = y
    
    def world_to_screen(self, world_pos):
        """Convertit les coordonnées du monde en coordonnées d'écran"""
        return pygame.Vector2(world_pos.x - self.offset.x, world_pos.y - self.offset.y)
    
    def screen_to_world(self, screen_pos):
        """Convertit les coordonnées d'écran en coordonnées du monde"""
        return pygame.Vector2(screen_pos[0] + self.offset.x, screen_pos[1] + self.offset.y)
