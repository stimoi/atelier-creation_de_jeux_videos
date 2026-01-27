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
from core.music_system import MusicSystem

# Import des entités
from entities.player import Player
from entities.enemies import EnemySystem
from entities.projectiles import ProjectileSystem
from entities.particles import ParticleSystem

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
        self.music_system = MusicSystem()
        
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
        
        # Menu GUI state
        self.menu_gui_open = False
        self.input_active = False
        self.input_text = ""
        self.power_buttons = []
        self.power_images = {}
        self._setup_menu_gui()
    
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
        
        # Fix ground if it has no width (end_x <= start_x)
        if self.ground_end_x <= self.ground_start_x:
            self.ground_end_x = 10000  # Give it a reasonable width
        self.platforms = game_state_data["platforms"]
        self.platform_colors = game_state_data["platform_colors"]
        self.platform_types = game_state_data["platform_types"]
        self.goal_rect = game_state_data["goal_rect"]
        self.spawn_point = game_state_data["spawn_point"]
        self.enemy_system.level_enemy_configs = game_state_data["level_enemy_configs"]
        
        # Charger et jouer la musique du niveau
        level_music = game_state_data.get("level_music", [])
        if level_music:
            # Joue la première piste musicale trouvée
            if self.music_system.load_music_from_data(level_music[0]):
                self.music_system.play(loops=-1)
                print(f"Musique chargée: {level_music[0].get('name', 'Inconnue')}")
        else:
            self.music_system.stop()
        
        # Créer le joueur
        if self.player is None:
            self.player = Player(self.spawn_point.x, self.spawn_point.y)
        
        # Configurer le tutoriel
        self.tutorial_system.select_tutorial_for_level(level)
    
    def _handle_events(self):
        """Gère tous les événements pygame (clavier, souris, fenêtre)
        
        Logique complexe de gestion d'états:
        - Menu principal: navigation entre niveaux, démarrage jeu
        - Jeu en cours: tir, pause, interactions
        - Menu pause: reprise, retour menu, quitter
        - Easter eggs et fonctionnalités spéciales
        
        Les événements sont routés selon l'état actuel du jeu
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Logique de navigation entre états avec ESC
                    if self.game_state.is_menu():
                        self.running = False  # Menu -> Quitter
                    elif self.game_state.is_playing():
                        self.game_state.set_state(GAME_STATES["PAUSED"])  # Jeu -> Pause
                    elif self.game_state.is_paused():
                        self.game_state.set_state(GAME_STATES["PLAYING"])  # Pause -> Jeu
                
                elif event.key == pygame.K_TAB:
                    # Toggle menu GUI
                    self.menu_gui_open = not self.menu_gui_open
                    if self.menu_gui_open:
                        self.input_active = False
                
                elif self.menu_gui_open and self.input_active:
                    # Handle text input for the pseudo field
                    if event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.input_active = False
                    else:
                        self.input_text += event.unicode
                
                elif event.key == pygame.K_o:
                    # Easter egg: affiche "BRAVO!" pendant 1.5 secondes
                    self.game_state.fword_timer = 1.5
                
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Validation/Action dans les menus
                    if self.game_state.is_menu():
                        self._start_new_game()  # Menu -> Nouveau jeu
                    elif self.game_state.is_paused():
                        self.game_state.set_state(GAME_STATES["PLAYING"])  # Pause -> Jeu
                        self.tutorial_system.start_display()  # Réaffiche le tutoriel
                
                elif event.key == pygame.K_m and self.game_state.is_paused():
                    # Retour au menu depuis la pause
                    self.game_state.set_state(GAME_STATES["MENU"])
                    self.tutorial_system.hide_display()  # Cache le tutoriel
                    self.music_system.stop()  # Arrête la musique au menu
                
                elif self.game_state.is_menu():
                    # Navigation entre niveaux dans le menu
                    if event.key == pygame.K_LEFT:
                        self.selected_level_idx = (self.selected_level_idx - 1) % len(self.levels)
                        self._apply_current_level()  # Recharge le niveau sélectionné
                    elif event.key == pygame.K_RIGHT:
                        self.selected_level_idx = (self.selected_level_idx + 1) % len(self.levels)
                        self._apply_current_level()  # Recharge le niveau sélectionné
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                # Gestion du menu GUI
                if self.menu_gui_open:
                    self._handle_menu_gui_click(mouse_pos)
                    return
                
                # Gestion des clics sur le tutoriel (bouton "Suivant")
                if self.tutorial_system.visible and self.tutorial_system.button_rect and self.tutorial_system.button_rect.collidepoint(mouse_pos):
                    self.tutorial_system.advance_text()
                    continue  # Évite les autres traitements de clic
                
                if self.game_state.is_menu():
                    # Clics sur les boutons du menu principal
                    play_rect, quit_rect = self.ui_manager.draw_menu(self.screen, self.font, self.small_font, self.title_font, self.selected_level_idx, self.levels)
                    if play_rect.collidepoint(mouse_pos):
                        self._start_new_game()
                    elif quit_rect.collidepoint(mouse_pos):
                        self.running = False
                
                elif self.game_state.is_paused():
                    # Clics sur les boutons du menu pause
                    pause_resume_rect, pause_menu_rect, pause_quit_rect = self.ui_manager.draw_pause_menu(self.screen, self.font, self.small_font, self.title_font)
                    if pause_resume_rect.collidepoint(mouse_pos):
                        self.game_state.set_state(GAME_STATES["PLAYING"])
                        self.tutorial_system.start_display()
                    elif pause_menu_rect.collidepoint(mouse_pos):
                        self.game_state.set_state(GAME_STATES["MENU"])
                        self.tutorial_system.hide_display()
                        self.music_system.stop()  # Arrête la musique au menu
                    elif pause_quit_rect.collidepoint(mouse_pos):
                        self.running = False
                
                elif self.game_state.is_playing():
                    # Tir: convertit la position souris écran -> monde et crée un projectile
                    mouse_world = self.camera.screen_to_world(mouse_pos)
                    projectile = self.player.shoot(mouse_world)
                    if projectile:
                        self.projectile_system.add_projectile(projectile)
                        # Crée des particules d'impact à la position de tir
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
            old_vel_y = self.player.vel_y
            self.player.pos, self.player.vel_y = resolve_block_collision(
                player_rect, self.player.pos, self.player.vel_y, block_collision,
                head_radius, body_height, leg_height
            )
            # Reset jumps when landing on a block (falling and velocity stopped)
            if old_vel_y > 0 and self.player.vel_y == 0:
                self.player.air_jumps_left = 1
        
        # Vérifier si le joueur est mort
        if self.player.is_dead(DEATH_BELOW_Y):
            self.game_state.player_hit()
            self.player.reset(self.spawn_point)
            self.particle_system.create_particles(self.player.pos, PARTICLE_COLORS["damage"], 15)
        
        # Collision avec la porte/objectif
        if self.player.get_feet_rect().colliderect(self.goal_rect) and not self.game_state.level_transition_active:
            next_idx = (self.selected_level_idx + 1) % len(self.levels)
            self.game_state.start_level_transition(next_idx)
        
        # Gestion complexe de la transition entre niveaux
        # Système à plusieurs phases pour une transition fluide
        should_change_level = self.game_state.update_level_transition(self.dt)
        if should_change_level:
            # Phase 1: Préparation du changement de niveau
            self.selected_level_idx = self.game_state.level_transition_next_idx
            self._apply_current_level()  # Charge les nouvelles données de niveau
            
            # Phase 2: Réinitialisation complète des entités
            self.player.reset(self.spawn_point)  # Replace le joueur au spawn
            self.projectile_system.clear()  # Nettoie tous les projectiles
            self.particle_system.clear()  # Nettoie toutes les particules
            self.enemy_system.instantiate_level_enemies()  # Crée les ennemis du nouveau niveau
            
            # Phase 3: Ajustement de la caméra pour éviter un saut visuel
            self.camera.set_position(self.player.pos.x - SCREEN_WIDTH // 2, self.player.pos.y - SCREEN_HEIGHT // 2)
            
            # Phase 4: Finalisation et réinitialisation du tutoriel
            self.game_state.complete_level_transition()
            self.tutorial_system.start_display()  # Affiche le tutoriel du nouveau niveau
        
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
        
        # Effet de particules lors de l'atterrissage pour le feedback visuel
        # Détecte le moment exact où le joueur touche le sol après être en l'air
        if not self.player.prev_on_ground and self.player.on_ground and self.player.vel_y == 0:
            # Position des particules: pieds du joueur
            feet_x = self.player.pos.x
            # Détermine si on atterrit sur le sol ou une plateforme
            feet_y = self.ground_y if self.player.pos.y + head_radius + body_height + leg_height >= self.ground_y else self.player.pos.y + head_radius + body_height + leg_height
            # Crée un petit nuage de particules à l'impact
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
                self.music_system.stop()  # Arrête la musique au menu
            
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
                self.music_system.stop()  # Arrête la musique au menu
        
        # Easter egg
        if self.game_state.fword_timer > 0:
            fword_surf = self.fword_font.render("BRAVO!", True, (255, 0, 0))
            self.screen.blit(fword_surf, (SCREEN_WIDTH//2 - fword_surf.get_width()//2, SCREEN_HEIGHT//2 - fword_surf.get_height()//2))
        
        # Menu GUI
        if self.menu_gui_open:
            self._draw_menu_gui()
        
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
    
    def _setup_menu_gui(self):
        """Setup the menu GUI components"""
        # Menu dimensions
        self.menu_width = 800
        self.menu_height = 600
        self.menu_x = (SCREEN_WIDTH - self.menu_width) // 2
        self.menu_y = (SCREEN_HEIGHT - self.menu_height) // 2
        
        # Input field
        self.input_rect = pygame.Rect(self.menu_x + 250, self.menu_y + 200, 300, 40)
        
        # Setup power buttons
        self._setup_power_buttons()
        self._load_power_images()
    
    def _setup_power_buttons(self):
        """Setup the 5 power buttons in a row"""
        button_radius = 50
        button_spacing = 120
        start_x = self.menu_x + (self.menu_width - (5 * button_spacing)) // 2 + button_radius // 2
        button_y = self.menu_y + 350
        
        self.power_buttons = []
        for i in range(5):
            x = start_x + i * button_spacing
            button_rect = pygame.Rect(x - button_radius, button_y - button_radius, 
                                     button_radius * 2, button_radius * 2)
            self.power_buttons.append({
                'rect': button_rect,
                'label': f'POUWOR {i + 1}',
                'image_key': f'pouvoir{i + 1}'
            })
    
    def _load_power_images(self):
        """Load power images if they exist"""
        for i in range(1, 6):
            image_path = f'GUI/IMG/pouvoir{i}.png'
            if os.path.exists(image_path):
                try:
                    image = pygame.image.load(image_path)
                    image = pygame.transform.scale(image, (80, 80))
                    self.power_images[f'pouvoir{i}'] = image
                except pygame.error:
                    print(f"Could not load image: {image_path}")
    
    def _handle_menu_gui_click(self, mouse_pos):
        """Handle clicks in the menu GUI"""
        # Check if input field was clicked
        if self.input_rect.collidepoint(mouse_pos):
            self.input_active = True
        else:
            self.input_active = False
        
        # Check if power buttons were clicked
        for button in self.power_buttons:
            if button['rect'].collidepoint(mouse_pos):
                print(f"Clicked: {button['label']}")
    
    def _draw_menu_gui(self):
        """Draw the menu GUI"""
        # Menu GUI colors
        WHITE = (255, 255, 255)
        BLACK = (0, 0, 0)
        GRAY = (200, 200, 200)
        DARK_GRAY = (100, 100, 100)
        BLUE = (100, 149, 237)
        LIGHT_BLUE = (173, 216, 230)
        
        # Draw menu background
        menu_surface = pygame.Surface((self.menu_width, self.menu_height))
        menu_surface.fill(WHITE)
        menu_surface.set_alpha(240)
        self.screen.blit(menu_surface, (self.menu_x, self.menu_y))
        
        # Draw menu border
        pygame.draw.rect(self.screen, BLACK, 
                        (self.menu_x, self.menu_y, self.menu_width, self.menu_height), 3)
        
        # Draw title
        font_title = pygame.font.Font(None, 36)
        title_text = font_title.render("INFORMATIONS SUR LE JOUEUR", True, BLACK)
        title_rect = title_text.get_rect(center=(self.menu_x + self.menu_width // 2, self.menu_y + 60))
        self.screen.blit(title_text, title_rect)
        
        # Draw avatar placeholder
        avatar_rect = pygame.Rect(self.menu_x + 100, self.menu_y + 120, 120, 120)
        pygame.draw.rect(self.screen, GRAY, avatar_rect)
        pygame.draw.rect(self.screen, BLACK, avatar_rect, 2)
        font_label = pygame.font.Font(None, 24)
        avatar_text = font_label.render("Avatar", True, DARK_GRAY)
        avatar_text_rect = avatar_text.get_rect(center=avatar_rect.center)
        self.screen.blit(avatar_text, avatar_text_rect)
        
        # Draw pseudo label
        pseudo_label = font_label.render("Pseudo:", True, BLACK)
        self.screen.blit(pseudo_label, (self.menu_x + 100, self.menu_y + 90))
        
        # Draw input field
        color = BLUE if self.input_active else BLACK
        pygame.draw.rect(self.screen, color, self.input_rect, 2)
        text_surface = font_label.render(self.input_text, True, BLACK)
        self.screen.blit(text_surface, (self.input_rect.x + 5, self.input_rect.y + 8))
        
        # Draw power buttons
        for button in self.power_buttons:
            self._draw_power_button(button, WHITE, BLACK, GRAY, DARK_GRAY, BLUE, LIGHT_BLUE)
    
    def _draw_power_button(self, button, WHITE, BLACK, GRAY, DARK_GRAY, BLUE, LIGHT_BLUE):
        """Draw a single power button"""
        center = button['rect'].center
        font_button = pygame.font.Font(None, 20)
        
        # Check if image exists
        if button['image_key'] in self.power_images:
            # Draw circular background
            pygame.draw.circle(self.screen, LIGHT_BLUE, center, 45)
            pygame.draw.circle(self.screen, BLACK, center, 45, 2)
            
            # Draw image
            image = self.power_images[button['image_key']]
            image_rect = image.get_rect(center=center)
            self.screen.blit(image, image_rect)
        else:
            # Draw circular button with text
            pygame.draw.circle(self.screen, LIGHT_BLUE, center, 45)
            pygame.draw.circle(self.screen, BLACK, center, 45, 2)
            
            # Draw text
            text = font_button.render(button['label'], True, BLACK)
            text_rect = text.get_rect(center=center)
            self.screen.blit(text, text_rect)

def main():
    """Point d'entrée"""
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
