# Système de tutoriel
import json
import os
import pygame

def _normalize_key(value):
    """Normalise une clé pour le tutoriel"""
    return "".join(ch for ch in str(value).lower() if ch.isalnum())

def _extract_text(entry):
    """Extrait le texte d'une entrée de tutoriel"""
    if isinstance(entry, str):
        text = entry.strip()
        return text if text else None
    if isinstance(entry, dict):
        for field in ("texte", "text", "message", "content"):
            if field in entry and isinstance(entry[field], str):
                text = entry[field].strip()
                if text:
                    return text
    return None

def _coerce_text_list(value):
    """Convertit une valeur en liste de textes"""
    texts = []
    if isinstance(value, list):
        for item in value:
            text = _extract_text(item)
            if text:
                texts.append(text)
    elif isinstance(value, dict):
        try:
            items = sorted(value.items(), key=lambda kv: int(kv[0]))
        except Exception:
            items = value.items()
        for _, item in items:
            text = _extract_text(item)
            if text:
                texts.append(text)
    else:
        text = _extract_text(value)
        if text:
            texts.append(text)
    return texts

def load_tutorial_texts():
    """Charge les textes du tutoriel depuis le fichier JSON"""
    texts = {}
    tutoriel_dir = os.path.join(os.path.dirname(__file__), "..", "tutoriel")
    texte_path = os.path.join(tutoriel_dir, "texte.json")
    
    if not os.path.isfile(texte_path):
        return texts
    
    try:
        with open(texte_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
    except Exception:
        return texts

    if isinstance(data, dict):
        for key, value in data.items():
            entries = _coerce_text_list(value)
            if entries:
                texts[_normalize_key(key)] = entries
    else:
        entries = _coerce_text_list(data)
        if entries:
            texts[_normalize_key("niveau1")] = entries
    
    return texts

def load_tutorial_image():
    """Charge l'image du tutoriel"""
    tutoriel_dir = os.path.join(os.path.dirname(__file__), "..", "tutoriel")
    image_path = os.path.join(tutoriel_dir, "photo.png")
    
    if os.path.isfile(image_path):
        try:
            return pygame.image.load(image_path).convert_alpha()
        except Exception:
            pass
    
    # Crée un placeholder si l'image n'existe pas
    placeholder = pygame.Surface((200, 200), pygame.SRCALPHA)
    placeholder.fill((210, 210, 210, 255))
    pygame.draw.rect(placeholder, (160, 160, 160, 255), placeholder.get_rect(), 6, border_radius=12)
    pygame.draw.line(placeholder, (160, 160, 160, 255), (30, 30), (170, 170), 6)
    pygame.draw.line(placeholder, (160, 160, 160, 255), (170, 30), (30, 170), 6)
    return placeholder

class TutorialSystem:
    """Système de tutoriel complet"""
    
    def __init__(self):
        self.texts = load_tutorial_texts()
        self.image = load_tutorial_image()
        self.current_texts = []
        self.visible = False
        self.index = 0
        self.button_rect = None
        self.image_cache = {}
    
    def select_tutorial_for_level(self, level):
        """Sélectionne le tutoriel approprié pour le niveau"""
        if not level:
            self.current_texts = []
            self.visible = False
            self.index = 0
            return
        
        # Uniquement pour le niveau 1
        if _normalize_key(level.get("name", "")) != "niveau1":
            self.current_texts = []
            self.visible = False
            self.index = 0
            return
        
        key = _normalize_key(level.get("name", ""))
        entries = self.texts.get(key)
        if not entries:
            fallback_key = _normalize_key("niveau1")
            entries = self.texts.get(fallback_key, [])
        
        self.current_texts = list(entries)
        self.index = 0
        self.visible = False
    
    def start_display(self):
        """Commence l'affichage du tutoriel"""
        if self.current_texts:
            self.index = 0
            self.visible = True
        else:
            self.visible = False
    
    def hide_display(self):
        """Cache l'affichage du tutoriel"""
        self.visible = False
    
    def toggle_visibility(self):
        """Bascule la visibilité du tutoriel"""
        if self.current_texts:
            self.visible = not self.visible
    
    def advance_text(self):
        """Passe au texte suivant du tutoriel"""
        if not self.visible or not self.current_texts:
            return
        
        self.index += 1
        if self.index >= len(self.current_texts):
            self.visible = False
            self.index = len(self.current_texts) - 1
        
        self.index = max(0, self.index)
    
    def _wrap_text_lines(self, text, font, max_width):
        """Divise le texte en lignes selon la largeur maximale"""
        lines = []
        if not text:
            return lines
        
        for raw_paragraph in text.split("\n"):
            paragraph = raw_paragraph.strip()
            if not paragraph:
                lines.append("")
                continue
            
            words = paragraph.split()
            current = words[0]
            for word in words[1:]:
                potential = f"{current} {word}"
                if font.size(potential)[0] <= max_width:
                    current = potential
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        
        return lines
    
    def _get_tutorial_image(self, max_width, max_height):
        """Obtient l'image du tutoriel redimensionnée"""
        if self.image is None:
            return None
        
        key = (max_width, max_height)
        cached = self.image_cache.get(key)
        if cached:
            return cached
        
        src_w, src_h = self.image.get_size()
        if src_w == 0 or src_h == 0:
            self.image_cache[key] = self.image
            return self.image
        
        scale = min(max_width / src_w, max_height / src_h)
        scale = max(scale, 0.01)
        new_size = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
        scaled = pygame.transform.smoothscale(self.image, new_size)
        self.image_cache[key] = scaled
        return scaled
    
    def draw(self, screen, small_font, screen_width, screen_height):
        """Dessine l'overlay du tutoriel"""
        if not self.visible or not self.current_texts:
            self.button_rect = None
            return
        
        panel_margin_x = 50
        panel_margin_y = 30
        panel_width = screen_width - panel_margin_x * 2
        panel_height = 200
        panel_x = panel_margin_x
        panel_y = screen_height - panel_height - panel_margin_y
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        self.button_rect = panel_rect.copy()
        
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((12, 23, 42, 220))
        pygame.draw.rect(panel_surface, (56, 130, 203, 220), panel_surface.get_rect(), 3, border_radius=18)
        
        content_padding = 24
        text_area_width = panel_rect.width - content_padding * 2
        image_surface = self._get_tutorial_image(220, panel_height - content_padding * 2)
        image_width = image_surface.get_width() if image_surface else 0
        
        if image_surface:
            text_area_width -= image_width + 24
        
        current_text = self.current_texts[min(self.index, len(self.current_texts) - 1)]
        wrapped_lines = self._wrap_text_lines(current_text, small_font, text_area_width)
        
        text_x = content_padding
        text_y = content_padding
        text_color = (235, 245, 255)
        
        for line in wrapped_lines:
            line_surf = small_font.render(line, True, text_color)
            panel_surface.blit(line_surf, (text_x, text_y))
            text_y += line_surf.get_height() + 6
        
        progress_text = f"{self.index + 1}/{len(self.current_texts)}"
        progress_surf = small_font.render(progress_text, True, (180, 210, 255))
        panel_surface.blit(progress_surf, (text_x, panel_rect.height - content_padding - progress_surf.get_height()))
        
        hint_text = "Cliquez pour continuer"
        hint_surf = small_font.render(hint_text, True, (120, 180, 255))
        hint_pos_x = panel_rect.width - content_padding - hint_surf.get_width() - (image_width + 24 if image_surface else 0)
        panel_surface.blit(hint_surf, (max(text_x, hint_pos_x), panel_rect.height - content_padding - hint_surf.get_height()))
        
        if image_surface:
            img_x = panel_rect.width - content_padding - image_surface.get_width()
            img_y = (panel_rect.height - image_surface.get_height()) // 2
            panel_surface.blit(image_surface, (img_x, img_y))
        
        screen.blit(panel_surface, panel_rect.topleft)
