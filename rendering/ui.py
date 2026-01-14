# Interface utilisateur (HUD, menus)
import pygame
from config.constants import *
from config.colors import *

class UIManager:
    """Gestionnaire de l'interface utilisateur"""
    
    def __init__(self):
        pass
    
    def draw_hud(self, screen, font, small_font, score, lives, stamina, is_invulnerable):
        """Dessine le HUD (Heads-Up Display)"""
        # Panneau semi-transparent
        hud_panel = pygame.Surface((300, 210), pygame.SRCALPHA)
        hud_panel.fill(UI_COLORS["panel"])
        screen.blit(hud_panel, (10, 10))

        # Score
        score_text = font.render(f"Score: {score}", True, UI_COLORS["text"])
        screen.blit(score_text, (30, 25))
        
        # Vies avec cœurs
        lives_text = font.render("Vies:", True, UI_COLORS["text"])
        screen.blit(lives_text, (30, 70))
        for i in range(lives):
            heart_x = 130 + i * 35
            pygame.draw.circle(screen, HEART_COLOR, (heart_x - 5, 85), 10)
            pygame.draw.circle(screen, HEART_COLOR, (heart_x + 5, 85), 10)
            pygame.draw.polygon(screen, HEART_COLOR, 
                               [(heart_x - 15, 85), (heart_x, 100), (heart_x + 15, 85)])

        # Stamina
        stamina_label = small_font.render("Stamina", True, STAMINA_COLORS["text"])
        screen.blit(stamina_label, (30, 120))
        stamina_bar_bg = pygame.Rect(30, 150, 240, 20)
        pygame.draw.rect(screen, STAMINA_COLORS["background"], stamina_bar_bg, border_radius=6)
        
        stamina_ratio = stamina / STAMINA_MAX if STAMINA_MAX else 0
        fill_width = int(stamina_bar_bg.width * max(0, min(1, stamina_ratio)))
        if fill_width > 0:
            stamina_bar_fill = pygame.Rect(stamina_bar_bg.left, stamina_bar_bg.top, fill_width, stamina_bar_bg.height)
            pygame.draw.rect(screen, STAMINA_COLORS["fill"], stamina_bar_fill, border_radius=6)
        
        pygame.draw.rect(screen, STAMINA_COLORS["border"], stamina_bar_bg, 2, border_radius=6)

        # Statut d'invulnérabilité
        if is_invulnerable:
            inv_text = small_font.render("⚡ INVULNÉRABLE", True, UI_COLORS["invulnerable"])
            screen.blit(inv_text, (30, 180))
    
    def draw_button(self, screen, rect, text, font, mouse_pos):
        """Dessine un bouton interactif"""
        hovered = rect.collidepoint(mouse_pos)
        base = UI_COLORS["background"]
        hover = UI_COLORS["hover"]
        pygame.draw.rect(screen, hover if hovered else base, rect, border_radius=10)
        pygame.draw.rect(screen, UI_COLORS["border"], rect, 3, border_radius=10)
        txt = font.render(text, True, UI_COLORS["text"])
        screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
    
    def draw_menu(self, screen, font, small_font, title_font, selected_level_idx, levels):
        """Dessine le menu principal"""
        # Boutons du menu
        play_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 40, 300, 70)
        quit_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 130, 300, 70)
        
        # Titre
        title_surf = title_font.render("Mon Jeu", True, UI_COLORS["text"])
        screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, SCREEN_HEIGHT//2 - 120))

        # Niveau sélectionné
        level_name = levels[selected_level_idx].get("name", f"Niveau {selected_level_idx+1}")
        level_txt = small_font.render(f"Niveau: {level_name}", True, UI_COLORS["text"])
        screen.blit(level_txt, (SCREEN_WIDTH//2 - level_txt.get_width()//2, SCREEN_HEIGHT//2 - 60))

        # Boutons
        mouse_pos = pygame.mouse.get_pos()
        self.draw_button(screen, play_rect, "Jouer", font, mouse_pos)
        self.draw_button(screen, quit_rect, "Quitter", font, mouse_pos)

        # Instructions
        hint = small_font.render("Entrée/Espace pour jouer", True, UI_COLORS["text_secondary"])
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT//2 + 220))
        
        return play_rect, quit_rect
    
    def draw_pause_menu(self, screen, font, small_font, title_font):
        """Dessine le menu de pause"""
        # Fond atténué
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(UI_COLORS["overlay"])
        screen.blit(overlay, (0, 0))

        # Boutons de pause
        pause_resume_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 20, 300, 70)
        pause_menu_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 70, 300, 70)
        pause_quit_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 160, 300, 70)
        
        # Titre
        pause_title = title_font.render("Pause", True, UI_COLORS["text"])
        screen.blit(pause_title, (SCREEN_WIDTH//2 - pause_title.get_width()//2, SCREEN_HEIGHT//2 - 120))

        # Boutons
        mouse_pos = pygame.mouse.get_pos()
        self.draw_button(screen, pause_resume_rect, "Reprendre", font, mouse_pos)
        self.draw_button(screen, pause_menu_rect, "Menu", font, mouse_pos)
        self.draw_button(screen, pause_quit_rect, "Quitter", font, mouse_pos)

        # Instructions
        hint = small_font.render("Echap/Entrée/Espace: Reprendre | M: Menu", True, UI_COLORS["text_secondary"])
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT//2 + 250))
        
        return pause_resume_rect, pause_menu_rect, pause_quit_rect
    
    def draw_victory_screen(self, screen, font, score):
        """Dessine l'écran de victoire"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(UI_COLORS["overlay"])
        screen.blit(overlay, (0, 0))
        
        big_text = pygame.font.SysFont(None, 120).render("VICTOIRE !", True, UI_COLORS["victory"])
        sub_text = font.render("Félicitations !", True, UI_COLORS["text"])
        score_final = font.render(f"Score Final: {score}", True, UI_COLORS["text"])
        
        screen.blit(big_text, (SCREEN_WIDTH//2 - big_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
        screen.blit(sub_text, (SCREEN_WIDTH//2 - sub_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
        screen.blit(score_final, (SCREEN_WIDTH//2 - score_final.get_width()//2, SCREEN_HEIGHT//2 + 70))
    
    def draw_game_over_screen(self, screen, font, score):
        """Dessine l'écran de game over"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(UI_COLORS["overlay"])
        screen.blit(overlay, (0, 0))
        
        over_text = pygame.font.SysFont(None, 96).render("GAME OVER", True, UI_COLORS["game_over"])
        score_final = font.render(f"Score: {score}", True, UI_COLORS["text"])
        
        screen.blit(over_text, (SCREEN_WIDTH//2 - over_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
        screen.blit(score_final, (SCREEN_WIDTH//2 - score_final.get_width()//2, SCREEN_HEIGHT//2 + 20))
    
    def draw_platforms(self, screen, platforms, platform_colors, platform_types, camera_offset):
        """Dessine les plateformes"""
        for i, plat in enumerate(platforms):
            plat_rect_screen = plat.move(-camera_offset.x, -camera_offset.y)
            col = PLATFORM_COLOR
            if i < len(platform_colors) and platform_colors[i]:
                col = platform_colors[i]
            ptype = 'platform'
            if i < len(platform_types):
                ptype = platform_types[i]

            if ptype == 'platform':
                # Plateforme normale avec highlight
                pygame.draw.rect(screen, col, plat_rect_screen)
                pygame.draw.rect(screen, PLATFORM_HIGHLIGHT, plat_rect_screen, 3)
                pygame.draw.line(screen, (80, 50, 20), 
                                (plat_rect_screen.left, plat_rect_screen.top + 5),
                                (plat_rect_screen.right, plat_rect_screen.top + 5), 2)
            elif ptype == 'block':
                # Bloc solide complet
                pygame.draw.rect(screen, col, plat_rect_screen)
                pygame.draw.rect(screen, (70, 70, 70), plat_rect_screen, 2)
            else:
                # Décor: rectangle semi-transparent
                try:
                    surf = pygame.Surface((plat_rect_screen.width, plat_rect_screen.height), pygame.SRCALPHA)
                    surf.fill((col[0], col[1], col[2], 120))
                    screen.blit(surf, plat_rect_screen.topleft)
                except Exception:
                    pygame.draw.rect(screen, col, plat_rect_screen)
    
    def draw_goal(self, screen, goal_rect, camera_offset):
        """Dessine la porte/objectif"""
        goal_rect_screen = goal_rect.move(-camera_offset.x, -camera_offset.y)
        pygame.draw.rect(screen, DOOR_COLOR, goal_rect_screen)
        pygame.draw.rect(screen, DOOR_FRAME, goal_rect_screen, 5)
        pygame.draw.line(screen, (100, 70, 20), 
                        (goal_rect_screen.centerx, goal_rect_screen.top),
                        (goal_rect_screen.centerx, goal_rect_screen.bottom), 3)
        knob_pos = (goal_rect_screen.right - 12, goal_rect_screen.centery)
        pygame.draw.circle(screen, (30, 30, 30), knob_pos, 6)
        pygame.draw.circle(screen, (80, 80, 80), knob_pos, 3)
    
    def draw_level_transition(self, screen, level_transition_active, level_transition_phase, level_transition_timer):
        """Dessine l'effet de transition entre niveaux"""
        if level_transition_active:
            if level_transition_phase == "fade_out":
                if LEVEL_TRANSITION_FADE_OUT > 0:
                    overlay_alpha = min(255, int((level_transition_timer / LEVEL_TRANSITION_FADE_OUT) * 255))
                else:
                    overlay_alpha = 255
            else:
                if LEVEL_TRANSITION_FADE_IN > 0:
                    overlay_alpha = max(0, 255 - int((level_transition_timer / LEVEL_TRANSITION_FADE_IN) * 255))
                else:
                    overlay_alpha = 0
            
            if overlay_alpha > 0:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, overlay_alpha))
                screen.blit(overlay, (0, 0))
