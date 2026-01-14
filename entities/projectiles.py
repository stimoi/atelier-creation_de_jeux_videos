# Projectiles
import pygame
from config.constants import *

class ProjectileSystem:
    """Système de gestion des projectiles"""
    
    def __init__(self):
        self.projectiles = []
    
    def add_projectile(self, projectile_data):
        """Ajoute un projectile"""
        if projectile_data:
            self.projectiles.append(projectile_data)
    
    def update(self, dt, camera_offset):
        """Met à jour tous les projectiles"""
        for proj in self.projectiles[:]:
            proj["pos"] += proj["vel"] * dt
            
            # Supprime les projectiles trop éloignés de l'écran
            if (proj["pos"].x < camera_offset.x - 200 or 
                proj["pos"].x > camera_offset.x + SCREEN_WIDTH + 200 or
                proj["pos"].y < camera_offset.y - 200 or 
                proj["pos"].y > camera_offset.y + SCREEN_HEIGHT + 200):
                self.projectiles.remove(proj)
    
    def clear(self):
        """Supprime tous les projectiles"""
        self.projectiles = []
    
    def get_count(self):
        """Retourne le nombre de projectiles"""
        return len(self.projectiles)
