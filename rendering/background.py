# Arrière-plan et environnement
import pygame
import math
import random
from config.constants import *
from config.colors import *

class BackgroundSystem:
    """Système de rendu de l'arrière-plan"""
    
    def __init__(self):
        self.clouds = []
        self.init_clouds()
    
    def init_clouds(self):
        """Initialise les nuages"""
        self.clouds = []
        for i in range(12):
            x = random.randint(-200, 3000)
            y = random.randint(50, 300)
            speed = random.uniform(10, 30)
            scale = random.uniform(0.6, 1.4)
            self.clouds.append({"x": x, "y": y, "speed": speed, "scale": scale})
    
    def update_clouds(self, dt, camera_offset):
        """Met à jour les nuages"""
        for c in self.clouds:
            c["x"] += c["speed"] * dt
            if c["x"] - camera_offset.x > 3200:
                c["x"] = camera_offset.x - random.randint(200, 600)
                c["y"] = random.randint(50, 300)
                c["speed"] = random.uniform(10, 30)
    
    def draw_cloud(self, screen, x, y, scale):
        """Dessine un nuage"""
        # Nuage composé de plusieurs ellipses
        color = CLOUD_COLOR
        offsets = [(-40, 10, 90, 50), (0, 0, 120, 60), (60, 15, 80, 45)]
        for ox, oy, w, h in offsets:
            rect = pygame.Rect(int(x + ox*scale), int(y + oy*scale), int(w*scale), int(h*scale))
            pygame.draw.ellipse(screen, color, rect)
    
    def draw_parallax_background(self, screen, camera_offset):
        """Dessine l'arrière-plan complet avec parallax"""
        # Ciel dégradé
        for i in range(SCREEN_HEIGHT):
            color = (
                int(70 + (130 - 70) * i / SCREEN_HEIGHT),
                int(130 + (180 - 130) * i / SCREEN_HEIGHT),
                int(180 + (230 - 180) * i / SCREEN_HEIGHT)
            )
            pygame.draw.line(screen, color, (0, i), (SCREEN_WIDTH, i))

        # Montagnes (3 couches)
        for col, factor, base_y in MOUNTAIN_LAYERS:
            points = []
            start_x = -int(camera_offset.x * factor) - 300
            for x in range(start_x, start_x + SCREEN_WIDTH + 600, 120):
                y = base_y + int(40 * math.sin(x * 0.01))
                points.append((x, y))
            points = [(-1000, SCREEN_HEIGHT), *points, (SCREEN_WIDTH + 1000, SCREEN_HEIGHT)]
            pygame.draw.polygon(screen, col, points)

        # Nuages (parallax léger)
        for c in self.clouds:
            cx = c["x"] - camera_offset.x * 0.2
            cy = c["y"] - camera_offset.y * 0.2
            self.draw_cloud(screen, cx, cy, c["scale"])
    
    def draw_ground(self, screen, camera_offset, ground_y, ground_start_x, ground_end_x):
        """Dessine le sol avec texture"""
        ground_rect = pygame.Rect(
            ground_start_x - camera_offset.x, 
            ground_y - camera_offset.y, 
            ground_end_x - ground_start_x, 
            100
        )
        pygame.draw.rect(screen, GROUND_COLOR, ground_rect)
        pygame.draw.rect(screen, (25, 100, 25), ground_rect, 3)
        
        # Texture du sol
        for i in range(0, 3000, 50):
            pygame.draw.line(screen, (44, 160, 44), 
                            (i - camera_offset.x, ground_y - camera_offset.y),
                            (i - camera_offset.x, ground_y - camera_offset.y + 100), 2)
