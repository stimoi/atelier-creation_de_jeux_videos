# États du jeu
import pygame
from config.constants import *

class GameState:
    """Gestionnaire des états du jeu"""
    
    def __init__(self):
        self.state = GAME_STATES["MENU"]
        self.score = 0
        self.lives = 3
        self.victory = False
        self.is_invulnerable = False
        self.invuln_timer = 0.0
        
        # Transition de niveaux
        self.level_transition_active = False
        self.level_transition_phase = "fade_out"
        self.level_transition_timer = 0.0
        self.level_transition_next_idx = None
        
        # Easter egg
        self.fword_timer = 0.0
    
    def set_state(self, new_state):
        """Change l'état du jeu"""
        self.state = new_state
    
    def is_menu(self):
        """Vérifie si on est dans le menu"""
        return self.state == GAME_STATES["MENU"]
    
    def is_playing(self):
        """Vérifie si on est en jeu"""
        return self.state == GAME_STATES["PLAYING"]
    
    def is_paused(self):
        """Vérifie si le jeu est en pause"""
        return self.state == GAME_STATES["PAUSED"]
    
    def start_new_game(self):
        """Initialise une nouvelle partie"""
        self.score = 0
        self.lives = 3
        self.victory = False
        self.is_invulnerable = False
        self.invuln_timer = 0.0
        self.level_transition_active = False
        self.level_transition_phase = "fade_out"
        self.level_transition_timer = 0.0
        self.level_transition_next_idx = None
        self.fword_timer = 0.0
    
    def player_hit(self):
        """Gère quand le joueur se fait toucher"""
        self.lives -= 1
        self.is_invulnerable = True
        self.invuln_timer = invuln_time
    
    def update_invulnerability(self, dt):
        """Met à jour l'état d'invulnérabilité"""
        if self.is_invulnerable:
            self.invuln_timer -= dt
            if self.invuln_timer <= 0:
                self.is_invulnerable = False
    
    def start_level_transition(self, next_level_idx):
        """Commence la transition vers le niveau suivant"""
        self.level_transition_active = True
        self.level_transition_phase = "fade_out"
        self.level_transition_timer = 0.0
        self.level_transition_next_idx = next_level_idx
        self.victory = True
    
    def update_level_transition(self, dt):
        """Met à jour la transition de niveau"""
        if not self.level_transition_active:
            return False
        
        self.level_transition_timer += dt
        
        if self.level_transition_phase == "fade_out":
            if LEVEL_TRANSITION_FADE_OUT <= 0 or self.level_transition_timer >= LEVEL_TRANSITION_FADE_OUT:
                return True  # Signal pour changer de niveau
        elif self.level_transition_phase == "fade_in":
            if LEVEL_TRANSITION_FADE_IN <= 0 or self.level_transition_timer >= LEVEL_TRANSITION_FADE_IN:
                self.level_transition_active = False
                self.level_transition_next_idx = None
                self.level_transition_phase = "fade_out"
                self.level_transition_timer = 0.0
                self.victory = False
        
        return False
    
    def complete_level_transition(self):
        """Passe à la phase de fade_in"""
        self.level_transition_phase = "fade_in"
        self.level_transition_timer = 0.0
    
    def is_game_over(self):
        """Vérifie si le jeu est terminé"""
        return self.lives <= 0
    
    def update_fword_timer(self, dt):
        """Met à jour le timer de l'easter egg"""
        if self.fword_timer > 0:
            self.fword_timer -= dt
