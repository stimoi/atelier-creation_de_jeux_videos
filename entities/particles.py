# Particules
import pygame
import math
import random
from config.constants import *
from config.colors import *

class ParticleSystem:
    """Système de gestion des particules"""
    
    def __init__(self):
        self.particles = []
    
    def create_particles(self, pos, color, count=8):
        """Crée des particules d'explosion"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            self.particles.append({
                "pos": pygame.Vector2(pos),
                "vel": pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed),
                "color": color,
                "life": 1.0
            })
    
    def update(self, dt):
        """Met à jour toutes les particules"""
        for part in self.particles[:]:
            part["pos"] += part["vel"] * dt
            part["vel"].y += GRAVITY * 0.5 * dt
            part["life"] -= dt * 2
            if part["life"] <= 0:
                self.particles.remove(part)
    
    def clear(self):
        """Supprime toutes les particules"""
        self.particles = []
    
    def get_count(self):
        """Retourne le nombre de particules"""
        return len(self.particles)
