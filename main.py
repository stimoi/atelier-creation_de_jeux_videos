# Point d'entrée principal du jeu
import pygame # truc de base
import sys
import os

# Import des modules de configuration
from config.constants import *
from config.colors import *

# Import des modules core
from core.chargeur_niveau import load_levels, apply_level
from core.tutoriel import TutorialSystem

# Import des entités
from entities.player import Player
from entities.enemies import EnemySystem
from entities.projectiles import ProjectileSystem
from entities.particles import ParticleSystem

# Import des systèmes de rendu
from rendering.background import BackgroundSystem
from rendering.entities_renderer import EntitiesRenderer
from rendering.ui import UIManager

# Import des systèmes de jeu
from game.physics import check_block_collision, resolve_block_collision, circle_rect_collision
from game.camera import Camera
from game.input import InputManager
from game.game_state import GameState

class Game:
    """Classe principale du jeu"""
    
    def __init__(self):
        pygame.init()
        
        # Initialisation de l'écran
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mon Jeu")
        
        # Horloge et polices
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 32)
        self.title_font = pygame.font.SysFont(None, 96)
        self.fword_font = pygame.font.SysFont(None, 180)
        
        # Systèmes du jeu
        self.input_manager = InputManager()
        self.game_state = GameState()
        self.camera = Camera()
        self.ui_manager = UIManager()
        self.background_system = BackgroundSystem()
        self.entities_renderer = EntitiesRenderer()
        self.tutorial_system = TutorialSystem()
        
        # Systèmes d'entités
        self.particle_system = ParticleSystem()
        self.projectile_system = ProjectileSystem()
        self.enemy_system = EnemySystem()
        
        # Niveaux
        self.levels = load_levels()
        self.selected_level_idx = 0
        
        # État du jeu
        self.player = None
        self.platforms = []
        self.platform_colors = []
        self.platform_types = []
        self.goal_rect = pygame.Rect(0, 0, 0, 0)
        self.spawn_point = pygame.Vector2(0, 0)
        self.ground_y = GROUND_Y
        self.ground_start_x = GROUND_START_X
        self.ground_end_x = GROUND_END_X
        
        # Appliquer le premier niveau
        self._apply_current_level()
        
        # Variables de contrôle
        self.running = True
        self.dt = 0
    
    def _apply_current_level(self):
        """Applique le niveau actuel"""
        level = self.levels[self.selected_level_idx]
        
        # Met à jour les données du niveau
        game_state_data = {
            "GROUND_Y": self.ground_y,
            "GROUND_START_X": self.ground_start_x,
            "GROUND_END_X": self.ground_end_x,
            "platforms": self.platforms,
            "platform_colors": self.platform_colors,
            "platform_types": self.platform_types,
            "goal_rect": self.goal_rect,
            "spawn_point": self.spawn_point,
            "level_enemy_configs": []
        }
        
        game_state_data = apply_level(level, game_state_data)
        
        # Mettre à jour les variables locales
        self.ground_y = game_state_data["GROUND_Y"]
        self.ground_start_x = game_state_data["GROUND_START_X"]
        self.ground_end_x = game_state_data["GROUND_END_X"]
        self.platforms = game_state_data["platforms"]
        self.platform_colors = game_state_data["platform_colors"]
        self.platform_types = game_state_data["platform_types"]
        self.goal_rect = game_state_data["goal_rect"]
        self.spawn_point = game_state_data["spawn_point"]
        self.enemy_system.level_enemy_configs = game_state_data["level_enemy_configs"]
        
        # Créer le joueur
        if self.player is None:
            self.player = Player(self.spawn_point.x, self.spawn_point.y)
        
        # Configurer le tutoriel
        self.tutorial_system.select_tutorial_for_level(level)
    
    def _handle_events(self):
        """Gère les événements"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state.is_menu():
                        self.running = False
                    elif self.game_state.is_playing():
                        self.game_state.set_state(GAME_STATES["PAUSED"])
                    elif self.game_state.is_paused():
                        self.game_state.set_state(GAME_STATES["PLAYING"])
                
                elif event.key == pygame.K_o:
                    # Easter egg
                    self.game_state.fword_timer = 1.5
                
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.game_state.is_menu():
                        self._start_new_game()
                    elif self.game_state.is_paused():
                        self.game_state.set_state(GAME_STATES["PLAYING"])
                        self.tutorial_system.start_display()
                
                elif event.key == pygame.K_m and self.game_state.is_paused():
                    self.game_state.set_state(GAME_STATES["MENU"])
                    self.tutorial_system.hide_display()
                
                elif self.game_state.is_menu():
                    if event.key == pygame.K_LEFT:
                        self.selected_level_idx = (self.selected_level_idx - 1) % len(self.levels)
                        self._apply_current_level()
                    elif event.key == pygame.K_RIGHT:
                        self.selected_level_idx = (self.selected_level_idx + 1) % len(self.levels)
                        self._apply_current_level()
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                # Tutoriel
                if self.tutorial_system.visible and self.tutorial_system.button_rect and self.tutorial_system.button_rect.collidepoint(mouse_pos):
                    self.tutorial_system.advance_text()
                    continue
                
                if self.game_state.is_menu():
                    play_rect, quit_rect = self.ui_manager.draw_menu(self.screen, self.font, self.small_font, self.title_font, self.selected_level_idx, self.levels)
                    if play_rect.collidepoint(mouse_pos):
                        self._start_new_game()
                    elif quit_rect.collidepoint(mouse_pos):
                        self.running = False
                
                elif self.game_state.is_paused():
                    pause_resume_rect, pause_menu_rect, pause_quit_rect = self.ui_manager.draw_pause_menu(self.screen, self.font, self.small_font, self.title_font)
                    if pause_resume_rect.collidepoint(mouse_pos):
                        self.game_state.set_state(GAME_STATES["PLAYING"])
                        self.tutorial_system.start_display()
                    elif pause_menu_rect.collidepoint(mouse_pos):
                        self.game_state.set_state(GAME_STATES["MENU"])
                        self.tutorial_system.hide_display()
                    elif pause_quit_rect.collidepoint(mouse_pos):
                        self.running = False
                
                elif self.game_state.is_playing():
                    # Tir
                    mouse_world = self.camera.screen_to_world(mouse_pos)
                    projectile = self.player.shoot(mouse_world)
                    if projectile:
                        self.projectile_system.add_projectile(projectile)
                        self.particle_system.create_particles(projectile["pos"], PARTICLE_COLORS["impact"], 6)
    
    def _start_new_game(self):
        """Démarre une nouvelle partie"""
        self.game_state.start_new_game()
        self._apply_current_level()
        self.player.reset(self.spawn_point)
        self.projectile_system.clear()
        self.particle_system.clear()
        self.enemy_system.instantiate_level_enemies()
        self.game_state.set_state(GAME_STATES["PLAYING"])
        self.tutorial_system.start_display()
    
    def _update(self):
        """Met à jour la logique du jeu"""
        if self.game_state.is_menu():
            self.background_system.update_clouds(self.dt, self.camera.offset)
            return
        
        if self.game_state.is_paused():
            return
        
        # Mise à jour des entrées
        self.input_manager.update()
        
        # Mise à jour du joueur
        moving = self.player.update(
            self.dt, 
            self.input_manager.keys,
            self.platforms,
            self.platform_types,
            self.ground_y,
            self.ground_start_x,
            self.ground_end_x
        )
        
        # Collisions avec les blocs
        player_rect = self.player.get_rect()
        block_collision = check_block_collision(player_rect, self.platforms, self.platform_types)
        if block_collision:
            self.player.pos, self.player.vel_y = resolve_block_collision(
                player_rect, self.player.pos, self.player.vel_y, block_collision,
                head_radius, body_height, leg_height
            )
        
        # Vérifier si le joueur est mort
        if self.player.is_dead(DEATH_BELOW_Y):
            self.game_state.player_hit()
            self.player.reset(self.spawn_point)
            self.particle_system.create_particles(self.player.pos, PARTICLE_COLORS["damage"], 15)
        
        # Collision avec la porte/objectif
        if self.player.get_feet_rect().colliderect(self.goal_rect) and not self.game_state.level_transition_active:
            next_idx = (self.selected_level_idx + 1) % len(self.levels)
            self.game_state.start_level_transition(next_idx)
        
        # Gestion de la transition de niveau
        should_change_level = self.game_state.update_level_transition(self.dt)
        if should_change_level:
            self.selected_level_idx = self.game_state.level_transition_next_idx
            self._apply_current_level()
            self.player.reset(self.spawn_point)
            self.projectile_system.clear()
            self.particle_system.clear()
            self.enemy_system.instantiate_level_enemies()
            self.camera.set_position(self.player.pos.x - SCREEN_WIDTH // 2, self.player.pos.y - SCREEN_HEIGHT // 2)
            self.game_state.complete_level_transition()
            self.tutorial_system.start_display()
        
        # Mise à jour de la caméra
        self.camera.update(self.player.pos)
        
        # Mise à jour des projectiles
        self.projectile_system.update(self.dt, self.camera.offset)
        
        # Mise à jour des ennemis
        self.enemy_system.update(self.dt, self.platforms, self.ground_y)
        
        # Collisions projectiles-ennemis
        score_gained = self.enemy_system.check_projectile_collision(self.projectile_system.projectiles, self.particle_system)
        self.game_state.score += score_gained
        
        # Collisions joueur-ennemis
        if not self.game_state.is_invulnerable:
            if self.enemy_system.check_player_collision(self.player.get_rect(), self.particle_system):
                self.game_state.player_hit()
                self.player.reset(self.spawn_point)
        
        # Mise à jour de l'invulnérabilité
        self.game_state.update_invulnerability(self.dt)
        
        # Mise à jour des particules
        self.particle_system.update(self.dt)
        
        # Effet de particules quand on atterrit
        if not self.player.prev_on_ground and self.player.on_ground and self.player.vel_y == 0:
            feet_x = self.player.pos.x
            feet_y = self.ground_y if self.player.pos.y + head_radius + body_height + leg_height >= self.ground_y else self.player.pos.y + head_radius + body_height + leg_height
            self.particle_system.create_particles((feet_x, feet_y), PARTICLE_COLORS["landing"], 10)
        
        self.player.prev_on_ground = self.player.on_ground
        
        # Mise à jour des timers
        self.game_state.update_fword_timer(self.dt)
        
        # Mise à jour des nuages
        self.background_system.update_clouds(self.dt, self.camera.offset)
    
    def _render(self):
        """Rendu graphique"""
        # Effacer l'écran
        self.screen.fill((0, 0, 0))
        
        if self.game_state.is_menu():
            # Menu principal
            self.background_system.draw_parallax_background(self.screen, self.camera.offset)
            self.ui_manager.draw_menu(self.screen, self.font, self.small_font, self.title_font, self.selected_level_idx, self.levels)
        
        elif self.game_state.is_paused():
            # Menu pause
            self._render_game()
            self.ui_manager.draw_pause_menu(self.screen, self.font, self.small_font, self.title_font)
        
        else:
            # Jeu
            self._render_game()
            
            # Écrans de fin
            if self.game_state.victory:
                self.ui_manager.draw_victory_screen(self.screen, self.font, self.game_state.score)
                pygame.display.flip()
                pygame.time.delay(1500)
                self.game_state.set_state(GAME_STATES["MENU"])
                self.game_state.victory = False
                self.game_state.level_transition_active = False
            
            elif self.game_state.is_game_over():
                self.ui_manager.draw_game_over_screen(self.screen, self.font, self.game_state.score)
                pygame.display.flip()
                pygame.time.delay(1500)
                self.game_state.set_state(GAME_STATES["MENU"])
                self.game_state.lives = 3
                self.game_state.score = 0
                self.projectile_system.clear()
                self.particle_system.clear()
                self.game_state.level_transition_active = False
        
        # Easter egg
        if self.game_state.fword_timer > 0:
            fword_surf = self.fword_font.render("BRAVO!", True, (255, 0, 0))
            self.screen.blit(fword_surf, (SCREEN_WIDTH//2 - fword_surf.get_width()//2, SCREEN_HEIGHT//2 - fword_surf.get_height()//2))
        
        # Tutoriel
        self.tutorial_system.draw(self.screen, self.small_font, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        pygame.display.flip()
    
    def _render_game(self):
        """Rendu du jeu"""
        # Arrière-plan
        self.background_system.draw_parallax_background(self.screen, self.camera.offset)
        
        # Sol
        self.background_system.draw_ground(self.screen, self.camera.offset, self.ground_y, self.ground_start_x, self.ground_end_x)
        
        # Plateformes
        self.ui_manager.draw_platforms(self.screen, self.platforms, self.platform_colors, self.platform_types, self.camera.offset)
        
        # Porte/objectif
        self.ui_manager.draw_goal(self.screen, self.goal_rect, self.camera.offset)
        
        # Entités
        self.entities_renderer.draw_enemies(self.screen, self.enemy_system.monsters, self.camera.offset)
        self.entities_renderer.draw_player(self.screen, self.player, self.camera.offset, self.input_manager.keys, self.game_state.is_invulnerable, self.game_state.invuln_timer)
        self.entities_renderer.draw_projectiles(self.screen, self.projectile_system.projectiles, self.camera.offset)
        self.entities_renderer.draw_particles(self.screen, self.particle_system.particles, self.camera.offset)
        
        # HUD
        self.ui_manager.draw_hud(self.screen, self.font, self.small_font, self.game_state.score, self.game_state.lives, self.player.stamina, self.game_state.is_invulnerable)
        
        # Transition de niveau
        self.ui_manager.draw_level_transition(self.screen, self.game_state.level_transition_active, self.game_state.level_transition_phase, self.game_state.level_transition_timer)
    
    def run(self):
        """Boucle principale du jeu"""
        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.dt = self.clock.tick(FPS) / 1000
        
        pygame.quit()
        sys.exit()

def main():
    """Point d'entrée"""
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
