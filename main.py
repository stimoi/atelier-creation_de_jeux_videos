# Importation des bibliothèques nécessaires au jeu
import pygame  # Bibliothèque principale pour le développement de jeux 2D
import random  # Génération de nombres aléatoires pour les spawns et effets
import math  # Fonctions mathématiques pour les calculs de physique et géométrie
import json  # Lecture des fichiers de configuration des niveaux
import os  # Gestion des chemins de fichiers et répertoires
from copy import deepcopy  # Copie profonde d'objets pour éviter les références partagées

# === INITIALISATION DE PYGAME ET DE LA FENÊTRE DE JEU ===
# Initialisation de tous les modules pygame
pygame.init()
# Définition du titre de la fenêtre du jeu
pygame.display.set_caption("Steel Reborn")
# Création de la fenêtre principale avec une résolution de 1366x769 pixels
screen = pygame.display.set_mode((1366, 769))
# Horloge pour contrôler le taux de rafraîchissement (FPS)
clock = pygame.time.Clock()
# Police de caractères pour le texte normal (taille 48)
font = pygame.font.SysFont(None, 48)
# Police de caractères pour le petit texte (taille 32)
small_font = pygame.font.SysFont(None, 32)
# Police de caractères pour les titres (taille 96)
title_font = pygame.font.SysFont(None, 96)
# Police de caractères pour les gros messages (taille 180)
fword_font = pygame.font.SysFont(None, 180)

# === SYSTÈME DE TUTORIEL ET D'AIDE CONTEXTUELLE ===
# Dictionnaire contenant tous les textes du tutoriel organisés par niveau
tutorial_texts = {}
# Liste des textes du tutoriel pour le niveau actuel
current_tutorial_texts = []
# Indique si le tutoriel est actuellement visible à l'écran
tutorial_visible = False
# Index du texte actuel dans la liste des textes du tutoriel
tutorial_index = 0
# Rectangle de la zone cliquable du tutoriel pour la navigation
tutorial_button_rect = None
# Image affichée dans le panneau de tutoriel (photo explicative)
tutorial_image = None
# Cache pour les images redimensionnées du tutoriel (optimisation performance)
tutorial_image_cache = {}

def _wrap_text_lines(text, font, max_width):
    """
    Fonction utilitaire pour découper un long texte en plusieurs lignes
    afin qu'il s'adapte à une largeur maximale spécifiée.
    
    Args:
        text: Le texte à découper (peut contenir des sauts de ligne)
        font: La police de caractères utilisée pour mesurer la largeur du texte
        max_width: Largeur maximale autorisée pour chaque ligne en pixels
    
    Returns:
        list: Liste des lignes de texte découpées
    """
    lines = []  # Liste qui contiendra les lignes finales
    if not text:  # Si le texte est vide, retourner une liste vide
        return lines
    # Traiter chaque paragraphe séparément (séparés par des sauts de ligne)
    for raw_paragraph in text.split("\n"):
        paragraph = raw_paragraph.strip()  # Supprimer les espaces en début/fin
        if not paragraph:  # Si le paragraphe est vide, ajouter une ligne vide
            lines.append("")
            continue
        words = paragraph.split()  # Diviser le paragraphe en mots individuels
        current = words[0]  # Commencer avec le premier mot
        # Traiter les mots restants un par un
        for word in words[1:]:
            potential = f"{current} {word}"  # Ajouter le mot suivant à la ligne actuelle
            # Vérifier si la ligne dépasse la largeur maximale
            if font.size(potential)[0] <= max_width:
                current = potential  # Si ça rentre, continuer sur la même ligne
            else:
                lines.append(current)  # Si ça dépasse, valider la ligne actuelle
                current = word  # Commencer une nouvelle ligne avec le mot actuel
        lines.append(current)  # Ajouter la dernière ligne du paragraphe
    return lines

def _get_tutorial_image(max_width, max_height):
    """
    Récupère une image redimensionnée du tutoriel depuis le cache
    ou la crée si elle n'existe pas encore.
    
    Cette fonction utilise un système de cache pour éviter de redimensionner
    la même image plusieurs fois, ce qui optimise les performances.
    
    Args:
        max_width: Largeur maximale souhaitée pour l'image
        max_height: Hauteur maximale souhaitée pour l'image
    
    Returns:
        Surface pygame: L'image redimensionnée ou None si aucune image n'est disponible
    """
    if tutorial_image is None:  # Si aucune image de tutoriel n'est chargée
        return None
    # Créer une clé unique pour le cache basée sur les dimensions
    key = (max_width, max_height)
    # Vérifier si l'image avec ces dimensions existe déjà dans le cache
    cached = tutorial_image_cache.get(key)
    if cached:  # Si oui, retourner l'image en cache
        return cached
    # Obtenir les dimensions originales de l'image source
    src_w, src_h = tutorial_image.get_size()
    if src_w == 0 or src_h == 0:  # Protection contre les dimensions invalides
        tutorial_image_cache[key] = tutorial_image
        return tutorial_image
    # Calculer le ratio de redimensionnement pour respecter les contraintes
    scale = min(max_width / src_w, max_height / src_h)
    scale = max(scale, 0.01)  # Éviter un ratio trop petit (protection)
    # Calculer les nouvelles dimensions en arrondissant à l'entier supérieur
    new_size = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
    # Redimensionner l'image avec un lissage pour meilleure qualité
    scaled = pygame.transform.smoothscale(tutorial_image, new_size)
    # Stocker dans le cache pour les utilisations futures
    tutorial_image_cache[key] = scaled
    return scaled


def _normalize_key(value):
    """
    Normalise une chaîne de caractères pour l'utiliser comme clé de dictionnaire.
    Convertit en minuscules et ne garde que les caractères alphanumériques.
    
    Args:
        value: La valeur à normaliser (peut être n'importe quel type)
    
    Returns:
        str: La chaîne normalisée contenant uniquement des lettres et chiffres
    """
    return "".join(ch for ch in str(value).lower() if ch.isalnum())

def _extract_text(entry):
    """
    Extrait le texte d'une entrée qui peut être une chaîne ou un dictionnaire.
    Cherche dans plusieurs champs possibles pour trouver le texte pertinent.
    
    Args:
        entry: L'entrée à traiter (chaîne ou dictionnaire)
    
    Returns:
        str or None: Le texte extrait et nettoyé, ou None si aucun texte trouvé
    """
    if isinstance(entry, str):
        # Si c'est une chaîne, la nettoyer et la retourner si non vide
        text = entry.strip()
        return text if text else None
    if isinstance(entry, dict):
        # Si c'est un dictionnaire, chercher dans plusieurs champs possibles
        for field in ("texte", "text", "message", "content"):
            if field in entry and isinstance(entry[field], str):
                text = entry[field].strip()
                if text:  # Retourner le premier texte non vide trouvé
                    return text
    return None  # Aucun texte trouvé

def _coerce_text_list(value):
    """
    Convertit une valeur en liste de textes normalisés.
    Gère différents formats d'entrée: liste, dictionnaire, ou chaîne simple.
    
    Args:
        value: La valeur à convertir (liste, dictionnaire, ou chaîne)
    
    Returns:
        list: Liste des textes extraits et validés
    """
    texts = []  # Liste qui contiendra les textes finaux
    if isinstance(value, list):
        # Si c'est une liste, traiter chaque élément individuellement
        for item in value:
            text = _extract_text(item)  # Extraire le texte de chaque élément
            if text:  # Ajouter uniquement si du texte a été trouvé
                texts.append(text)
    elif isinstance(value, dict):
        # Si c'est un dictionnaire, essayer de trier par clés numériques
        try:
            # Tenter de trier par clés interprétées comme nombres
            items = sorted(value.items(), key=lambda kv: int(kv[0]))
        except Exception:
            # En cas d'erreur, garder l'ordre original
            items = value.items()
        # Traiter chaque paire clé-valeur
        for _, item in items:
            text = _extract_text(item)
            if text:
                texts.append(text)
    else:
        # Si c'est un autre type (chaîne, nombre, etc.), traiter comme élément unique
        text = _extract_text(value)
        if text:
            texts.append(text)
    return texts

def load_tutorial_texts():
    """
    Charge les textes du tutoriel depuis le fichier texte.json.
    Le fichier doit être dans le sous-répertoire 'tutoriel'.
    
    Returns:
        dict: Dictionnaire des textes du tutoriel organisés par niveau
    """
    texts = {}  # Dictionnaire pour stocker les textes chargés
    # Construire le chemin vers le répertoire du tutoriel
    tutoriel_dir = os.path.join(os.path.dirname(__file__), "tutoriel")
    # Construire le chemin vers le fichier de textes
    texte_path = os.path.join(tutoriel_dir, "texte.json")
    # Vérifier si le fichier existe avant de tenter de le lire
    if not os.path.isfile(texte_path):
        return texts  # Retourner un dictionnaire vide si le fichier n'existe pas
    try:
        # Ouvrir et lire le fichier JSON avec encodage UTF-8
        with open(texte_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
    except Exception:
        # En cas d'erreur de lecture, retourner un dictionnaire vide
        return texts

    if isinstance(data, dict):
        # Si les données sont un dictionnaire, traiter chaque entrée
        for key, value in data.items():
            # Extraire et normaliser les textes pour chaque clé
            entries = _coerce_text_list(value)
            if entries:  # Ajouter uniquement si des textes valides sont trouvés
                texts[_normalize_key(key)] = entries
    else:
        # Si les données ne sont pas un dictionnaire, les traiter comme niveau par défaut
        entries = _coerce_text_list(data)
        if entries:
            texts[_normalize_key("niveau1")] = entries
    return texts

def load_tutorial_image():
    """
    Charge l'image du tutoriel depuis le fichier photo.png.
    Si le fichier n'existe pas ou ne peut être chargé, crée une image de remplacement.
    
    Returns:
        Surface pygame: L'image chargée ou une image de remplacement
    """
    # Construire le chemin vers le répertoire du tutoriel
    tutoriel_dir = os.path.join(os.path.dirname(__file__), "tutoriel")
    # Construire le chemin vers le fichier image
    image_path = os.path.join(tutoriel_dir, "photo.png")
    # Vérifier si le fichier existe et tenter de le charger
    if os.path.isfile(image_path):
        try:
            # Charger l'image avec transparence alpha
            return pygame.image.load(image_path).convert_alpha()
        except Exception:
            # En cas d'erreur de chargement, continuer vers l'image de remplacement
            pass
    # Créer une image de remplacement (placeholder) avec une croix
    placeholder = pygame.Surface((200, 200), pygame.SRCALPHA)  # Surface avec transparence
    placeholder.fill((210, 210, 210, 255))  # Fond gris clair
    # Dessiner une bordure arrondie
    pygame.draw.rect(placeholder, (160, 160, 160, 255), placeholder.get_rect(), 6, border_radius=12)
    # Dessiner une croix pour indiquer qu'aucune image n'est disponible
    pygame.draw.line(placeholder, (160, 160, 160, 255), (30, 30), (170, 170), 6)  # Diagonale descendante
    pygame.draw.line(placeholder, (160, 160, 160, 255), (170, 30), (30, 170), 6)  # Diagonale montante
    return placeholder

# Chargement initial des textes et image du tutoriel au démarrage du jeu
tutorial_texts = load_tutorial_texts()  # Charger tous les textes disponibles
tutorial_image = load_tutorial_image()  # Charger l'image illustrative


def select_tutorial_for_level(level):
    """
    Sélectionne les textes du tutoriel appropriés pour un niveau spécifique.
    Cherche d'abord un tutoriel spécifique au niveau, sinon utilise un tutoriel par défaut.
    
    Args:
        level: Dictionnaire contenant les informations du niveau (doit avoir un champ "name")
    """
    global current_tutorial_texts, tutorial_visible, tutorial_index
    if not level:  # Si aucun niveau n'est fourni
        current_tutorial_texts = []  # Vider les textes actuels
        tutorial_visible = False  # Masquer le tutoriel
        tutorial_index = 0  # Réinitialiser l'index
        return
    # Normaliser le nom du niveau pour la recherche
    key = _normalize_key(level.get("name", ""))
    # Chercher les textes spécifiques à ce niveau
    entries = tutorial_texts.get(key)
    if not entries:  # Si aucun texte spécifique n'est trouvé
        # Utiliser le tutoriel par défaut (niveau1)
        fallback_key = _normalize_key("niveau1")
        entries = tutorial_texts.get(fallback_key, [])
    # Préparer les textes pour l'affichage
    current_tutorial_texts = list(entries)  # Copier la liste pour éviter les modifications
    tutorial_index = 0  # Commencer au premier texte
    tutorial_visible = False  # Masquer par défaut (sera affiché plus tard)


def draw_tutorial_overlay():
    """
    Dessine l'interface du tutoriel à l'écran.
    Affiche un panneau semi-transparent avec le texte du tutoriel,
    une image explicative, et des contrôles de navigation.
    """
    global tutorial_button_rect  # Rectangle pour la détection des clics
    # Ne rien afficher si le tutoriel n'est pas visible ou s'il n'y a pas de texte
    if not tutorial_visible or not current_tutorial_texts:
        tutorial_button_rect = None  # Réinitialiser la zone cliquable
        return

    # Dimensions et position du panneau du tutoriel
    panel_margin_x = 50  # Marge horizontale par rapport aux bords de l'écran
    panel_margin_y = 30  # Marge verticale par rapport au bas de l'écran
    panel_width = SCREEN_WIDTH - panel_margin_x * 2  # Largeur du panneau
    panel_height = 200  # Hauteur fixe du panneau
    panel_x = panel_margin_x  # Position X du panneau
    panel_y = SCREEN_HEIGHT - panel_height - panel_margin_y  # Position Y (en bas)
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

    # Définir la zone cliquable pour la navigation dans le tutoriel
    tutorial_button_rect = panel_rect

    # Créer la surface du panneau avec transparence alpha
    panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
    # Fond semi-transparent bleu foncé
    panel_surface.fill((12, 23, 42, 220))
    # Bordure bleue claire avec coins arrondis
    pygame.draw.rect(panel_surface, (56, 130, 203, 220), panel_surface.get_rect(), 3, border_radius=18)

    # Espacement interne pour le contenu
    content_padding = 24
    # Largeur disponible pour le texte (sera réduite si une image est présente)
    text_area_width = panel_rect.width - content_padding * 2
    # Obtenir l'image redimensionnée si disponible
    image_surface = _get_tutorial_image(220, panel_height - content_padding * 2)
    image_width = image_surface.get_width() if image_surface else 0
    if image_surface:  # Réduire la zone de texte si une image est présente
        text_area_width -= image_width + 24  # 24px d'espace entre texte et image

    # Obtenir le texte actuel à afficher (avec protection contre les index hors limites)
    current_text = current_tutorial_texts[min(tutorial_index, len(current_tutorial_texts) - 1)]
    # Découper le texte en lignes pour qu'il s'adapte à la largeur disponible
    wrapped_lines = _wrap_text_lines(current_text, small_font, text_area_width)

    # Position de départ pour le texte
    text_x = content_padding
    text_y = content_padding
    text_color = (235, 245, 255)  # Couleur bleue claire pour le texte
    # Dessiner chaque ligne de texte
    for line in wrapped_lines:
        line_surf = small_font.render(line, True, text_color)
        panel_surface.blit(line_surf, (text_x, text_y))
        text_y += line_surf.get_height() + 6  # Espacement entre les lignes

    # Afficher la progression (ex: "2/5")
    progress_text = f"{tutorial_index + 1}/{len(current_tutorial_texts)}"
    progress_surf = small_font.render(progress_text, True, (180, 210, 255))
    panel_surface.blit(progress_surf, (text_x, panel_rect.height - content_padding - progress_surf.get_height()))

    # Afficher l'indice pour continuer
    hint_text = "Cliquez pour continuer"
    hint_surf = small_font.render(hint_text, True, (120, 180, 255))
    # Positionner l'indice à droite, en tenant compte de l'image si présente
    hint_pos_x = panel_rect.width - content_padding - hint_surf.get_width() - (image_width + 24 if image_surface else 0)
    panel_surface.blit(hint_surf, (max(text_x, hint_pos_x), panel_rect.height - content_padding - hint_surf.get_height()))

    # Dessiner l'image si elle est disponible
    if image_surface:
        # Centrer l'image verticalement à droite du panneau
        img_x = panel_rect.width - content_padding - image_surface.get_width()
        img_y = (panel_rect.height - image_surface.get_height()) // 2
        panel_surface.blit(image_surface, (img_x, img_y))

    # Dessiner le panneau complet à l'écran
    screen.blit(panel_surface, panel_rect.topleft)

def start_tutorial():
    """
    Démarre l'affichage du tutoriel pour le niveau actuel.
    Réinitialise l'index au début et rend le tutoriel visible.
    """
    global tutorial_visible, tutorial_index
    if current_tutorial_texts:  # Vérifier qu'il y a des textes à afficher
        tutorial_index = 0  # Commencer au premier texte
        tutorial_visible = True  # Rendre le tutoriel visible
    else:
        tutorial_visible = False  # Masquer si aucun texte n'est disponible


def hide_tutorial():
    """
    Masque immédiatement l'affichage du tutoriel.
    Utilisé lors des transitions de niveau ou du retour au menu.
    """
    global tutorial_visible
    tutorial_visible = False  # Masquer le panneau du tutoriel


def toggle_tutorial_visibility():
    """
    Bascule l'état de visibilité du tutoriel.
    Si des textes sont disponibles, alterne entre affiché et masqué.
    """
    global tutorial_visible
    if current_tutorial_texts:  # Ne faire quelque chose que si des textes existent
        tutorial_visible = not tutorial_visible  # Inverser l'état actuel


def advance_tutorial_text():
    """
    Passe au texte suivant du tutoriel.
    Si c'était le dernier texte, masque le tutoriel.
    """
    global tutorial_visible, tutorial_index
    # Ne rien faire si le tutoriel n'est pas visible ou s'il n'y a pas de texte
    if not tutorial_visible or not current_tutorial_texts:
        return
    tutorial_index += 1  # Passer au texte suivant
    # Vérifier si on a atteint la fin des textes
    if tutorial_index >= len(current_tutorial_texts):
        tutorial_visible = False  # Masquer le tutoriel à la fin
        tutorial_index = len(current_tutorial_texts) - 1  # Éviter un index hors limites
    # S'assurer que l'index reste valide
    tutorial_index = max(0, tutorial_index)

# === CONSTANTES DU JEU ===
# Dimensions de l'écran obtenues depuis la fenêtre pygame
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
# Position Y du sol (hauteur à laquelle le joueur atterrit)
GROUND_Y = 680
# Position X de début du sol (limite gauche du monde)
GROUND_START_X = 0
# Position X de fin du sol (limite droite du monde)
GROUND_END_X = 3000

# === PHYSIQUE ET MÉCANIQUES DE JEU ===
# Accélération due à la gravité (pixels/secondes²)
GRAVITY = 800
# Force du saut (vitesse verticale initiale, négative = vers le haut)
JUMP_FORCE = -600
# Vitesse de déplacement horizontal du joueur (pixels/secondes)
MOVE_SPEED = 300
# Vitesse des projectiles tirés par le joueur (pixels/secondes)
PROJECTILE_SPEED = 800
# Endurance maximale du joueur
STAMINA_MAX = 100
# Coût en endurance pour un saut normal
STAMINA_JUMP_COST = 10
# Délai avant que la régénération d'endurance ne commence (secondes)
STAMINA_REGEN_DELAY = 4.0
# Intervalle de régénération d'endurance (secondes)
STAMINA_REGEN_INTERVAL = 0.5
# Quantité d'endurance régénérée à chaque intervalle
STAMINA_REGEN_AMOUNT = 5
# Coût en endurance pour un double saut
DOUBLE_JUMP_COST = 15
# Coût en endurance pour un dash (course rapide)
DASH_COST = 10
# Vitesse du dash (pixels/secondes)
DASH_SPEED = 900
# Durée du dash (secondes)
DASH_DURATION = 0.2
# Images par seconde cible pour le jeu
FPS = 60
# Nombre maximum de monstres simultanés dans le niveau
MAX_MONSTERS = 3
# Temps d'attente entre chaque spawn de monstre (secondes)
MONSTER_SPAWN_COOLDOWN = 2.0
# Position Y à laquelle le joueur est considéré comme mort (tombé dans le vide)
DEATH_BELOW_Y = GROUND_Y + 1500

# === SYSTÈME DE CAMÉRA ===
# Position de la caméra dans le monde (décalage par rapport au coin supérieur gauche)
camera_offset = pygame.Vector2(0, 0)
# Facteur de lissage pour les mouvements de caméra (0 = instantané, 1 = très lent)
CAMERA_LAG = 0.05

# === PALETTE DE COULEURS DU JEU ===
# Couleur du ciel (bleu azur)
SKY_COLOR = (70, 130, 180)
# Couleur du sol (vert forêt)
GROUND_COLOR = (34, 139, 34)
# Couleur principale des plateformes (brun foncé)
PLATFORM_COLOR = (101, 67, 33)
# Couleur de surbrillance des plateformes (brun clair)
PLATFORM_HIGHLIGHT = (139, 90, 43)
# Couleur de la porte/objectif (or foncé)
DOOR_COLOR = (184, 134, 11)
# Couleur du cadre de la porte (brun rougeâtre)
DOOR_FRAME = (139, 69, 19)
# Couleur du t-shirt du personnage (bleu moyen)
SHIRT_COLOR = (50, 120, 220)
# Couleur du pantalon du personnage (bleu foncé)
PANTS_COLOR = (30, 50, 90)
# Couleur des chaussures du personnage (gris foncé)
SHOE_COLOR = (40, 40, 40)
# Couleur des mains du personnage (peau claire)
HAND_COLOR = (255, 220, 177)
# Couleur des cheveux du personnage (brun foncé)
HAIR_COLOR = (60, 40, 20)
# Couleur de la peau du personnage (peau claire)
SKIN_COLOR = (255, 220, 177)

# === SYSTÈME DE PARTICULES ===
# Liste contenant toutes les particules actives dans le jeu
particles = []

def create_particles(pos, color, count=8):
    """
    Crée une explosion de particules à une position donnée.
    Utilisé pour les effets visuels (tirs, impacts, morts, etc.).
    
    Args:
        pos: Tuple (x, y) de la position où créer les particules
        color: Couleur des particules au format RGB
        count: Nombre de particules à créer (défaut: 8)
    """
    for _ in range(count):  # Créer le nombre demandé de particules
        # Angle aléatoire pour la direction de la particule (0 à 2π radians)
        angle = random.uniform(0, 2 * math.pi)
        # Vitesse aléatoire pour chaque particule
        speed = random.uniform(50, 150)
        # Ajouter la particule à la liste avec ses propriétés
        particles.append({
            "pos": pygame.Vector2(pos),  # Position initiale
            "vel": pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed),  # Vélocité
            "color": color,  # Couleur de la particule
            "life": 1.0  # Durée de vie (1.0 = pleine vie, 0.0 = morte)
        })

def circle_rect_collision(center, radius, rect):
    """
    Détecte la collision entre un cercle et un rectangle.
    Utilisé pour les collisions joueur-ennemis et projectiles-ennemis.
    
    Args:
        center: Tuple (x, y) du centre du cercle
        radius: Rayon du cercle
        rect: Rectangle pygame (pygame.Rect)
    
    Returns:
        bool: True si collision détectée, False sinon
    """
    cx, cy = center  # Extraire les coordonnées du centre
    # Trouver le point le plus proche du centre sur le rectangle
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    # Calculer la distance au carré entre le centre et ce point
    dx = cx - closest_x
    dy = cy - closest_y
    # Vérifier si la distance est inférieure au rayon (comparaison au carré pour éviter sqrt)
    return dx * dx + dy * dy <= radius * radius

# === SYSTÈME DE PARALLAX ET ARRIÈRE-PLAN ===
# Liste contenant tous les nuages pour l'effet parallax
clouds = []

def init_clouds():
    """
    Initialise les nuages pour l'effet parallax.
    Crée 12 nuages avec des positions, vitesses et tailles aléatoires.
    """
    global clouds
    clouds = []  # Vider la liste existante
    for i in range(12):  # Créer 12 nuages
        # Position X aléatoire sur une large étendue (peut démarrer hors écran à gauche)
        x = random.randint(-200, 3000)
        # Position Y aléatoire dans le ciel (50 à 300 pixels du haut)
        y = random.randint(50, 300)
        # Vitesse de déplacement horizontale (pixels/secondes)
        speed = random.uniform(10, 30)
        # Facteur d'échelle pour la taille du nuage (0.6 = plus petit, 1.4 = plus grand)
        scale = random.uniform(0.6, 1.4)
        clouds.append({"x": x, "y": y, "speed": speed, "scale": scale})

def update_clouds(dt):
    """
    Met à jour la position des nuages pour l'effet parallax.
    Les nuages se déplacent de gauche à droite et réapparaissent à gauche
    lorsqu'ils sortent de l'écran à droite.
    
    Args:
        dt: Temps écoulé depuis la dernière frame (delta time en secondes)
    """
    for c in clouds:  # Mettre à jour chaque nuage
        # Déplacer le nuage vers la droite en fonction de sa vitesse et du temps
        c["x"] += c["speed"] * dt
        # Vérifier si le nuage est sorti de l'écran à droite
        if c["x"] - camera_offset.x > 3200:
            # Réinitialiser le nuage à gauche de l'écran avec de nouvelles propriétés aléatoires
            c["x"] = camera_offset.x - random.randint(200, 600)
            c["y"] = random.randint(50, 300)  # Nouvelle hauteur
            c["speed"] = random.uniform(10, 30)  # Nouvelle vitesse

def draw_cloud(screen, x, y, scale):
    """
    Dessine un nuage composé de plusieurs ellipses superposées.
    Crée un effet de nuage réaliste avec plusieurs cercles de différentes tailles.
    
    Args:
        screen: Surface pygame où dessiner le nuage
        x: Position X du centre du nuage
        y: Position Y du centre du nuage
        scale: Facteur d'échelle pour la taille du nuage
    """
    # Couleur blanche pour les nuages
    color = (255, 255, 255)
    # Définition des ellipses qui composent le nuage (offset_x, offset_y, largeur, hauteur)
    # Chaque ellipse est positionnée relativement au centre du nuage
    offsets = [(-40, 10, 90, 50), (0, 0, 120, 60), (60, 15, 80, 45)]
    for ox, oy, w, h in offsets:
        # Calculer la position et la taille réelles en fonction de l'échelle
        rect = pygame.Rect(int(x + ox*scale), int(y + oy*scale), int(w*scale), int(h*scale))
        # Dessiner l'ellipse (forme ovale)
        pygame.draw.ellipse(screen, color, rect)

def draw_parallax_background():
    """
    Dessine l'arrière-plan complet avec effet parallax.
    Comprend un ciel dégradé, des montagnes en plusieurs couches,
    et des nuages avec effet de profondeur.
    """
    # === CIEL DÉGRADÉ ===
    # Crée un dégradé vertical du bleu foncé (en haut) au bleu clair (en bas)
    for i in range(SCREEN_HEIGHT):
        # Calculer la couleur interpolée pour chaque ligne horizontale
        color = (
            int(70 + (130 - 70) * i / SCREEN_HEIGHT),  # Rouge: 70 → 130
            int(130 + (180 - 130) * i / SCREEN_HEIGHT),  # Vert: 130 → 180
            int(180 + (230 - 180) * i / SCREEN_HEIGHT)   # Bleu: 180 → 230
        )
        # Dessiner une ligne horizontale avec la couleur calculée
        pygame.draw.line(screen, color, (0, i), (SCREEN_WIDTH, i))

    # === MONTAGNES EN 3 COUCHES (PARALLAX) ===
    # Chaque couche a une couleur, un facteur de parallax, et une hauteur de base
    layers = [((90, 110, 140), 0.2, 180), ((80, 100, 130), 0.35, 260), ((70, 90, 120), 0.5, 340)]
    for col, factor, base_y in layers:
        points = []  # Points qui définiront le polygone de la montagne
        # Point de départ bien avant le bord gauche de l'écran
        start_x = -int(camera_offset.x * factor) - 300
        # Générer les points de la crête de la montagne
        for x in range(start_x, start_x + SCREEN_WIDTH + 600, 120):
            # Ajouter une variation sinusoïdale pour un relief naturel
            y = base_y + int(40 * math.sin(x * 0.01))
            points.append((x, y))
        # Fermer le polygone en ajoutant les coins inférieurs
        points = [(-1000, SCREEN_HEIGHT), *points, (SCREEN_WIDTH + 1000, SCREEN_HEIGHT)]
        # Dessiner le polygone rempli
        pygame.draw.polygon(screen, col, points)

    # === NUAGES AVEC EFFET PARALLAX ===
    for c in clouds:
        # Calculer la position du nuage avec effet parallax (déplacement plus lent que la caméra)
        cx = c["x"] - camera_offset.x * 0.2  # 0.2 = facteur de parallax pour les nuages
        cy = c["y"] - camera_offset.y * 0.2  # Effet parallax vertical aussi
        # Dessiner le nuage à sa position calculée
        draw_cloud(screen, cx, cy, c["scale"])

def draw_shadow(center_x, feet_y_world, max_radius):
    """
    Dessine une ombre douce au sol sous un personnage ou objet.
    L'ombre est une ellipse semi-transparente qui donne une impression de profondeur.
    
    Args:
        center_x: Position X mondiale du centre de l'objet
        feet_y_world: Position Y mondiale des pieds de l'objet (au niveau du sol)
        max_radius: Rayon maximal de l'ombre
    """
    # Convertir les coordonnées mondiales en coordonnées d'écran
    shadow_y = int(feet_y_world - camera_offset.y)
    shadow_x = int(center_x - camera_offset.x)
    # Calculer les dimensions de l'ombre (plus large que haute pour un effet réaliste)
    width = int(max_radius * 2.4)  # Largeur = 2.4 × le rayon
    height = max(6, int(max_radius * 0.5))  # Hauteur = 0.5 × le rayon, minimum 6px
    # Créer une surface avec transparence alpha pour l'ombre
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    # Dessiner une ellipse semi-transparente (noir avec alpha = 90/255)
    pygame.draw.ellipse(surf, (0, 0, 0, 90), surf.get_rect())
    # Positionner l'ombre centrée sous l'objet
    screen.blit(surf, (shadow_x - width//2, shadow_y - height//2))

# === VARIABLES DU JOUEUR ===
# Position du joueur dans le monde (coordonnées X, Y)
player_pos = pygame.Vector2(SCREEN_WIDTH / 2, GROUND_Y)
# Dimensions du corps du personnage pour le rendu et les collisions
head_radius = 20  # Rayon de la tête (pixels)
body_height = 40  # Hauteur du torse (pixels)
leg_height = 30  # Hauteur des jambes (pixels)
arm_length = 25  # Longueur des bras (pixels)

# === ÉTAT PHYSIQUE DU JOUEUR ===
player_vel_y = 0  # Vélocité verticale (pixels/secondes, négatif = vers le haut)
direction = 1  # Direction du regard (1 = droite, -1 = gauche)
walk_cycle = 0  # Compteur pour l'animation de marche
blink_timer = 0.0  # Temps avant le prochain clignement d'yeux
blink_close = 0.0  # Durée pendant laquelle les yeux sont fermés
prev_on_ground = True  # État précédent (était-il au sol à la frame précédente ?)
shoot_recoil = 0.0  # Temps de recul après avoir tiré (effet visuel)
stamina = STAMINA_MAX  # Endurance actuelle du joueur
stamina_idle_timer = 0.0  # Temps depuis la dernière action consommant de l'endurance
stamina_regen_timer = 0.0  # Temps écoulé depuis la dernière régénération d'endurance
air_jumps_left = 1  # Nombre de sauts en l'air restants
jump_was_pressed = False  # État précédent de la touche de saut (pour éviter les sauts multiples)
dash_was_pressed = False  # État précédent de la touche de dash
dash_timer = 0.0  # Temps restant pour le dash en cours
dash_direction = 1  # Direction du dash en cours (1 = droite, -1 = gauche)

# Positionner le joueur initialement sur le sol (au-dessus de la ligne de sol)
# La position Y est calculée pour que les pieds touchent le sol
player_pos.y = GROUND_Y - (head_radius + body_height + leg_height)
# Définir le point de spawn (où le joueur réapparaît après une mort)
spawn_point = player_pos

# === SYSTÈME DE PROJECTILES ===
# Liste contenant tous les projectiles actifs tirés par le joueur
projectiles = []
# Rayon des projectiles pour les collisions et le rendu
projectile_radius = 6

# === SYSTÈME D'ENNEMIS ===
# Rayon standard des monstres pour les collisions
monster_radius = 25
# Temps restant avant le prochain spawn de monstre
monster_spawn_timer = 0.0

def spawn_monster():
    """
    Crée un monstre aléatoire avec des propriétés variables.
    Il existe 3 types de monstres: tank (gros/lent), fast (petit/rapide), et flyer (volant).
    
    Returns:
        dict: Dictionnaire contenant toutes les propriétés du monstre créé
    """
    # Position X aléatoire dans la zone de jeu
    x = random.randint(100, 2500)
    
    # Sélection aléatoire du type de monstre
    r = random.random()
    if r < 0.3:  # 30% de chance - Tank (gros, lent, résistant)
        m_type = "tank"
        radius = 32  # Plus grand que la moyenne
        speed = 60   # Plus lent que la moyenne
        hp = 3       # 3 points de vie au lieu de 1
        y = GROUND_Y - radius  # Positionné sur le sol
        extra = {"vel_y": 0.0}  # Vélocité verticale nulle au départ
    elif r < 0.7:  # 40% de chance - Fast (petit, rapide, fragile)
        m_type = "fast"
        radius = 18  # Plus petit que la moyenne
        speed = 140  # Plus rapide que la moyenne
        hp = 1       # 1 point de vie
        y = GROUND_Y - radius  # Positionné sur le sol
        extra = {"vel_y": 0.0}  # Vélocité verticale nulle au départ
    else:  # 30% de chance - Flyer (volant, vitesse moyenne)
        m_type = "flyer"
        radius = 22  # Taille moyenne
        speed = 110  # Vitesse moyenne
        hp = 1       # 1 point de vie
        # Position Y aléatoire dans les airs (entre 280 et 140 pixels au-dessus du sol)
        base_y = random.randint(GROUND_Y - 280, GROUND_Y - 140)
        y = base_y
        # Propriétés spécifiques au vol
        extra = {"fly_phase": random.uniform(0, 6.28), "base_y": base_y}

    # Assembler le dictionnaire du monstre avec toutes ses propriétés
    data = {
        "pos": pygame.Vector2(x, y),  # Position initiale
        "dir": random.choice([-1, 1]),  # Direction de départ (gauche ou droite)
        "type": m_type,  # Type de monstre
        "radius": radius,  # Rayon pour les collisions
        "speed": speed,  # Vitesse de déplacement
        "hp": hp,  # Points de vie
        "anim": 'monster3.png',  # Image d'animation par défaut
        "hit_flash": 0.0,  # Timer pour le flash de dégâts
    }
    # Ajouter les propriétés spécifiques au type
    data.update(extra)
    return data

# === CONFIGURATION PAR DÉFAUT DES TYPES DE MONSTRES ===
# Valeurs par défaut pour chaque type de monstre utilisées lors de la création
# depuis les fichiers de configuration des niveaux
MONSTER_TYPE_DEFAULTS = {
    "tank": {"radius": 32, "speed": 60, "hp": 3, "dir": 1},    # Gros, lent, 3 PV
    "fast": {"radius": 18, "speed": 140, "hp": 1, "dir": 1},   # Petit, rapide, 1 PV
    "flyer": {"radius": 22, "speed": 110, "hp": 1, "dir": 1},  # Volant, vitesse moyenne, 1 PV
    "basic": {"radius": 20, "speed": 100, "hp": 1, "dir": 1},  # Type standard, 1 PV
}

# === SYSTÈME DE GESTION DES ENNEMIS ===
# Liste des configurations d'ennemis pour le niveau actuel (chargées depuis le JSON)
level_enemy_configs = []
# Nombre maximum de monstres autorisés dans le niveau actuel
current_monster_cap = MAX_MONSTERS
# Liste contenant tous les monstres actuellement actifs dans le jeu
monsters = []


def _canonical_monster_type(raw_type):
    """
    Normalise le type de monstre depuis une chaîne de caractères.
    Convertit différents noms possibles en un type standard reconnu.
    
    Args:
        raw_type: Type de monstre brut (peut être None, chaîne vide, ou variante)
    
    Returns:
        str: Type de monstre normalisé ('basic', 'tank', 'fast', ou 'flyer')
    """
    if not raw_type:  # Si aucun type n'est spécifié
        return "basic"  # Utiliser le type de base par défaut
    t = str(raw_type).lower()  # Convertir en minuscules pour la comparaison
    if t in MONSTER_TYPE_DEFAULTS:  # Si le type est déjà reconnu
        return t
    # Gérer les alias ou variations de noms
    if t in ("walker", "ground"):  # Alias pour le type de base
        return "basic"
    return "basic"  # Type par défaut si rien ne correspond


def create_monster_from_config(config, template_id=None):
    """
    Crée un monstre à partir d'une configuration de niveau.
    Utilise les valeurs du fichier JSON ou les valeurs par défaut du type.
    
    Args:
        config: Dictionnaire de configuration du monstre depuis le fichier de niveau
        template_id: ID optionnel pour identifier ce monstre (utile pour le respawn)
    
    Returns:
        dict: Dictionnaire du monstre complètement configuré
    """
    cfg = deepcopy(config)  # Copie profonde pour éviter les modifications de l'original
    # Normaliser le type de monstre et obtenir les valeurs par défaut
    m_type = _canonical_monster_type(cfg.get("type"))
    defaults = MONSTER_TYPE_DEFAULTS[m_type]

    # Extraire et valider la position
    x = float(cfg.get("x", 0))  # Position X (défaut: 0)
    y = float(cfg.get("y", 0))  # Position Y (défaut: 0)
    # Extraire les dimensions si elles sont spécifiées
    width = cfg.get("w") or cfg.get("width")
    height = cfg.get("h") or cfg.get("height")

    # Calculer le rayon (priorité: rayon explicite > dimensions > défaut)
    radius = cfg.get("radius")
    if radius is None:
        if width and height:  # Si dimensions sont spécifiées, utiliser la plus grande
            radius = max(width, height) / 2
        else:
            radius = defaults["radius"]  # Sinon utiliser le rayon par défaut du type

    # Extraire les autres propriétés avec valeurs par défaut
    speed = cfg.get("speed", defaults["speed"])  # Vitesse
    hp = int(cfg.get("hp", defaults["hp"]))  # Points de vie
    dir_val = cfg.get("dir", defaults["dir"])  # Direction
    direction = -1 if float(dir_val) < 0 else 1  # Normaliser la direction (-1 ou 1)

    # Construire le dictionnaire de base du monstre
    monster = {
        "pos": pygame.Vector2(x, y),  # Position
        "dir": direction,  # Direction
        "type": m_type,  # Type normalisé
        "radius": radius,  # Rayon calculé
        "speed": speed,  # Vitesse
        "hp": hp,  # Points de vie
        "hit_flash": 0.0,  # Timer de flash de dégâts
    }

    # Ajouter les propriétés spécifiques au type
    if m_type == "flyer":
        # Pour les monstres volants
        base_y = float(cfg.get("base_y", y))  # Hauteur de vol de base
        monster.update({
            "fly_phase": float(cfg.get("fly_phase", 0.0)),  # Phase de vol initiale
            "base_y": base_y,  # Hauteur de vol
        })
    else:
        # Pour les monstres terrestres
        monster["vel_y"] = float(cfg.get("vel_y", 0.0))  # Vélocité verticale

    # Ajouter l'ID de template si fourni (utile pour le système de respawn)
    if template_id is not None:
        monster["template_id"] = template_id

    return monster


def instantiate_level_enemies():
    """
    Instancie les ennemis pour le niveau actuel.
    Soit utilise les configurations du fichier JSON, soit génère des monstres aléatoires.
    """
    global monsters, current_monster_cap, monster_spawn_timer
    if level_enemy_configs:  # Si des configurations sont définies dans le fichier de niveau
        monsters = []  # Vider la liste actuelle
        # Créer un monstre pour chaque configuration
        for idx, cfg in enumerate(level_enemy_configs):
            monsters.append(create_monster_from_config(cfg, template_id=idx))
        # Limiter le nombre maximum au nombre de configurations
        current_monster_cap = len(level_enemy_configs)
    else:
        # Sinon, générer des monstres aléatoires
        monsters = [spawn_monster() for _ in range(MAX_MONSTERS)]
        current_monster_cap = MAX_MONSTERS
    # Réinitialiser le timer de spawn
    monster_spawn_timer = 0.0

# === SYSTÈME MULTI-NIVEAUX ===
# Chargement des niveaux depuis le fichier levels.json et application des configurations

def _default_level():
    """
    Crée une configuration de niveau par défaut.
    Utilisé si aucun fichier levels.json n'est trouvé ou en cas d'erreur.
    
    Returns:
        dict: Configuration d'un niveau de base avec sol, spawn, objectif et plateformes
    """
    return {
        "name": "Niveau 1",  # Nom du niveau
        "ground": {"y": 0, "start_x": 0, "end_x": 10000},  # Configuration du sol
        "spawn": {"x": 40, "y": -40},  # Point d'apparition du joueur
        "goal": {"x": 1000, "y": -110, "w": 70, "h": 110},  # Porte/objectif
        "platforms": [],  # Liste vide de plateformes
    }

# === CHARGEMENT DES NIVEAUX ===
# Liste qui contiendra tous les niveaux chargés depuis le fichier JSON
levels = []
# Répertoire où se trouve le fichier de niveaux (même répertoire que le script)
levels_dir = os.path.dirname(__file__)
# Noms de fichiers possibles pour la compatibilité (ancien et nouveau format)
level_filenames = ["levels.json"]
# Tenter de charger les niveaux depuis chaque fichier possible
for name in level_filenames:
    level_path = os.path.join(levels_dir, name)  # Construire le chemin complet
    if not os.path.isfile(level_path):  # Si le fichier n'existe pas, passer au suivant
        continue
    try:
        # Ouvrir et lire le fichier JSON
        with open(level_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Vérifier que le fichier a la structure attendue (dictionnaire avec clé "levels")
            if isinstance(data, dict) and isinstance(data.get("levels"), list) and data["levels"]:
                levels = data["levels"]  # Extraire la liste des niveaux
                break  # Sortir de la boucle si le chargement a réussi
    except Exception:
        # En cas d'erreur de lecture, continuer avec le fichier suivant
        continue

# Si aucun niveau n'a été chargé, utiliser le niveau par défaut
if not levels:
    levels = [_default_level()]

# Index du niveau actuellement sélectionné dans le menu
selected_level_idx = 0

# === VARIABLES DU NIVEAU ACTUEL ===
# Liste des plateformes dans le niveau actuel
platforms = []
# Rectangle définissant la porte/objectif à atteindre
goal_rect = pygame.Rect(0, 0, 0, 0)
# Point de spawn du joueur pour le niveau actuel
spawn_point = pygame.Vector2(0, 0)

def load_image(img_name: str):
    """
    Charge une image depuis un fichier avec gestion des erreurs.
    Si l'image ne peut être chargée, affiche un message d'erreur et quitte le jeu.
    
    Args:
        img_name: Nom du fichier image à charger
    
    Returns:
        pygame.Surface: Surface pygame contenant l'image chargée
    """
    try:
        # Charger l'image avec support de la transparence alpha
        loaded_img = pygame.image.load(img_name).convert_alpha()
    except pygame.error as e:
        # En cas d'erreur, afficher le message et quitter
        print(f"Impossible de charger l'image : {e}")
        pygame.quit()
    return loaded_img

def apply_level(level):
    """
    Applique la configuration d'un niveau au jeu.
    Met à jour toutes les variables globales du jeu en fonction des données du niveau.
    
    Args:
        level: Dictionnaire contenant la configuration du niveau
    """
    global GROUND_Y, GROUND_START_X, GROUND_END_X, platforms, goal_rect, spawn_point, level_enemy_configs
    
    # === CONFIGURATION DU SOL ===
    # Extraire les propriétés du sol avec valeurs par défaut si non spécifiées
    GROUND_Y = int(level.get("ground", {}).get("y", GROUND_Y))
    GROUND_START_X = int(level.get("ground", {}).get("start_x", GROUND_START_X))
    GROUND_END_X = int(level.get("ground", {}).get("end_x", GROUND_END_X))
    
    # === CONFIGURATION DES PLATEFORMES ===
    # Créer des rectangles pygame pour chaque plateforme définie dans le niveau
    platforms = [
        pygame.Rect(
            int(p.get("x", 0)),    # Position X avec défaut 0
            int(p.get("y", 0)),    # Position Y avec défaut 0
            int(p.get("w", 0)),    # Largeur avec défaut 0
            int(p.get("h", 0))     # Hauteur avec défaut 0
        )
        for p in level.get("platforms", [])  # Itérer sur la liste des plateformes
    ]
    
    # === CONFIGURATION DE LA PORTE/OBJECTIF ===
    g = level.get("goal", {})  # Obtenir la configuration de l'objectif
    goal_rect.x = int(g.get("x", 2300))      # Position X par défaut: 2300
    goal_rect.y = int(g.get("y", -30))       # Position Y par défaut: -30
    goal_rect.w = int(g.get("w", 70))        # Largeur par défaut: 70
    goal_rect.h = int(g.get("h", 110))       # Hauteur par défaut: 110
    
    # === CONFIGURATION DU POINT DE SPAWN ===
    s = level.get("spawn", {})  # Obtenir la configuration du spawn
    # Mettre à jour le point de spawn avec valeurs par défaut si non spécifiées
    spawn_point.update(
        float(s.get("x", SCREEN_WIDTH / 2)),  # X par défaut: centre de l'écran
        float(s.get("y", GROUND_Y - (head_radius + body_height + leg_height)))  # Y par défaut: sur le sol
    )
    
    # === CONFIGURATION DES ENNEMIS ===
    level_enemy_configs = []  # Vider les configurations existantes
    raw_enemies = level.get("enemies", [])  # Obtenir la liste des ennemis du niveau
    if isinstance(raw_enemies, list):  # Vérifier que c'est bien une liste
        for entry in raw_enemies:
            if isinstance(entry, dict):  # Chaque ennemi doit être un dictionnaire
                level_enemy_configs.append(deepcopy(entry))  # Ajouter une copie profonde
    
    # === SÉLECTION DU TUTORIEL APPROPRIÉ ===
    select_tutorial_for_level(level)  # Choisir les textes de tutoriel pour ce niveau

# === INITIALISATION DU NIVEAU DE DÉPART ===
# Appliquer la configuration du premier niveau sélectionné
apply_level(levels[selected_level_idx])
# Instancier les ennemis pour ce niveau
instantiate_level_enemies()
# Initialiser les nuages pour l'effet parallax
init_clouds()

# === SYSTÈME DE SCORE, VIES ET ÉTAT DE VICTOIRE ===
score = 0  # Score actuel du joueur (augmente en tuant des ennemis)
lives = 3  # Nombre de vies restantes au joueur
invuln_time = 1.5  # Durée de l'invulnérabilité après avoir pris des dégâts (secondes)
invuln_timer = 0.0  # Temps restant d'invulnérabilité
is_invulnerable = False  # État d'invulnérabilité du joueur
victory = False  # Indique si le joueur a gagné le niveau

# === SYSTÈME DE TRANSITION ENTRE NIVEAUX ===
# Durées des transitions en secondes
LEVEL_TRANSITION_FADE_OUT = 0.6  # Durée du fondu au noir
LEVEL_TRANSITION_FADE_IN = 0.6   # Durée du fondu depuis le noir
level_transition_active = False  # Indique si une transition est en cours
level_transition_phase = "fade_out"  # Phase actuelle: "fade_out" ou "fade_in"
level_transition_timer = 0.0  # Temps écoulé dans la transition actuelle
level_transition_next_idx = None  # Index du prochain niveau à charger

# === ÉTAT DU JEU ===
# États possibles: "MENU" (menu principal), "PLAYING" (en jeu), "PAUSED" (en pause)
game_state = "MENU"
fword_timer = 0.0  # Timer pour l'easter egg (gros texte à l'écran)
movement = "perso.png"  # Nom du fichier d'animation actuel du personnage

# === BOUCLE PRINCIPALE DU JEU ===
running = True  # Contrôle la continuation de la boucle de jeu
dt = 0  # Delta time: temps écoulé depuis la dernière frame (en secondes)
cnt = cnt2 = 0  # Compteurs utilisés pour les animations (cycles d'images)
is_played = True  # Indicateur pour la gestion de la musique (boss theme vs main theme)
level_name = ""  # Nom du niveau actuel (utilisé pour la sélection musicale)

# === SYSTÈME AUDIO ===
# Variable pour l'effet sonore du saut
jump = pygame.mixer.Sound('jump.wav')

# Initialisation du mélangeur audio pour la musique et les effets sonores
pygame.mixer.init()

# Chargement et lecture de la musique principale en boucle
pygame.mixer.music.load("themes\\main-theme.mp3")
pygame.mixer.music.play(-1)  # -1 = lecture en boucle infinie

# DÉBUT DE LA BOUCLE PRINCIPALE DU JEU
while running:
    # === MISE À JOUR DES COMPTEURS D'ANIMATION ===
    cnt += 1  # Compteur pour l'animation du personnage
    cnt2 += 1  # Compteur pour l'animation des monstres volants
    
    # === GESTION DYNAMIQUE DE LA MUSIQUE ===
    # Change la musique en fonction du niveau (thème normal vs thème de boss)
    if level_name == "pas de sol" and is_played:
        # Si on est dans le niveau "pas de sol" et que la musique normale joue
        pygame.mixer.music.stop()  # Arrêter la musique actuelle
        pygame.mixer.music.load("themes\\boss-theme.mp3")  # Charger le thème de boss
        pygame.mixer.music.play(-1)  # Jouer en boucle
        is_played = False  # Marquer que le thème de boss est en cours
    elif level_name != "pas de sol" and not is_played:
        # Si on n'est plus dans le niveau "pas de sol" et que le thème de boss joue
        pygame.mixer.music.stop()  # Arrêter le thème de boss
        pygame.mixer.music.load("themes\\main-theme.mp3")  # Recharger le thème normal
        pygame.mixer.music.play(-1)  # Jouer en boucle
        is_played = True  # Marquer que le thème normal est en cours
    # === DÉFINITION DES BOUTONS D'INTERFACE ===
    # Les boutons sont recalculés à chaque frame pour s'adapter aux changements de résolution
    
    # Boutons du menu principal
    play_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 40, 300, 70)  # Bouton "Jouer"
    quit_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 130, 300, 70)   # Bouton "Quitter"
    
    # Boutons du menu pause
    pause_resume_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 20, 300, 70)  # Bouton "Reprendre"
    pause_menu_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 70, 300, 70)   # Bouton "Menu"
    pause_quit_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 160, 300, 70)   # Bouton "Quitter"
    # === TRAITEMENT DES ÉVÉNEMENTS ===
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # L'utilisateur a cliqué sur le bouton de fermeture de la fenêtre
            running = False  # Arrêter la boucle de jeu
            break
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # Gestion de la touche Échap selon l'état actuel du jeu
            if game_state == "MENU":
                # Dans le menu: quitter le jeu
                running = False
                break
            elif game_state == "PLAYING":
                # En jeu: ouvrir le menu pause
                game_state = "PAUSED"
            elif game_state == "PAUSED":
                # En pause: reprendre le jeu
                game_state = "PLAYING"
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_o:
            # Easter egg: afficher un gros texte à l'écran pendant 1.5 secondes
            fword_timer = 1.5
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # === GESTION DES CLICS GAUCHE DE LA SOURIS ===
            
            # D'abord, vérifier si on clique sur le panneau de tutoriel
            if tutorial_visible and tutorial_button_rect and tutorial_button_rect.collidepoint(event.pos):
                advance_tutorial_text()  # Passer au texte suivant du tutoriel
                continue  # Ne pas traiter d'autres clics
            
            if game_state == "MENU":
                # === CLICS DANS LE MENU PRINCIPAL ===
                if play_rect.collidepoint(event.pos):
                    # === DÉMARRAGE D'UNE NOUVELLE PARTIE ===
                    # Réinitialisation complète des variables de jeu
                    score = 0  # Score à zéro
                    lives = 3  # 3 vies au départ
                    invuln_timer = 0.0  # Pas d'invulnérabilité
                    is_invulnerable = False  # Joueur vulnérable
                    victory = False  # Pas encore victoire
                    flip = False  # Direction de départ (non retourné)
                    # Réinitialiser le système de transition
                    level_transition_active = False
                    level_transition_phase = "fade_out"
                    level_transition_timer = 0.0
                    level_transition_next_idx = None
                    # Appliquer la configuration du niveau sélectionné
                    apply_level(levels[selected_level_idx])
                    instantiate_level_enemies()  # Créer les ennemis
                    player_pos = spawn_point  # Positionner le joueur au spawn
                    player_vel_y = 0  # Pas de vélocité verticale
                    projectiles = []  # Vider les projectiles
                    particles = []  # Vider les particules
                    monster_spawn_timer = 0.0  # Réinitialiser le timer de spawn
                    # Réinitialiser le système d'endurance
                    stamina = STAMINA_MAX
                    stamina_idle_timer = 0.0
                    stamina_regen_timer = 0.0
                    air_jumps_left = 1  # Un saut en l'air disponible
                    jump_was_pressed = False
                    dash_was_pressed = False
                    dash_timer = 0.0
                    dash_direction = 1
                    game_state = "PLAYING"  # Passer en mode jeu
                    start_tutorial()  # Afficher le tutoriel du niveau
                    
                elif quit_rect.collidepoint(event.pos):
                    # Quitter le jeu
                    running = False
                    break
            elif game_state == "PAUSED":
                # === CLICS DANS LE MENU PAUSE ===
                if pause_resume_rect.collidepoint(event.pos):
                    # Reprendre le jeu
                    game_state = "PLAYING"
                    start_tutorial()  # Réafficher le tutoriel
                elif pause_menu_rect.collidepoint(event.pos):
                    # Retourner au menu principal
                    game_state = "MENU"
                    hide_tutorial()  # Masquer le tutoriel
                elif pause_quit_rect.collidepoint(event.pos):
                    # Quitter le jeu
                    running = False
                    break
            elif game_state == "PLAYING":
                # === CLICS PENDANT LE JEU (TIR DE PROJECTILE) ===
                # Convertir la position de la souris de l'écran vers les coordonnées du monde
                mouse_world_x = event.pos[0] + camera_offset.x
                mouse_world_y = event.pos[1] + camera_offset.y

                # Calculer la direction du tir (vecteur normalisé)
                dx = mouse_world_x - player_pos.x  # Distance en X
                dy = mouse_world_y - player_pos.y  # Distance en Y
                distance = math.sqrt(dx**2 + dy**2)  # Distance euclidienne

                if distance > 0:  # Éviter la division par zéro
                    # Normaliser le vecteur direction
                    dir_x = dx / distance
                    dir_y = dy / distance

                    # Position de départ du projectile (légèrement décalé du joueur)
                    proj_x = player_pos.x + dir_x * (head_radius + 10)
                    proj_y = player_pos.y + dir_y * (head_radius + 10)

                    # Créer et ajouter le projectile à la liste
                    projectiles.append({
                        "pos": pygame.Vector2(proj_x, proj_y),  # Position initiale
                        "vel": pygame.Vector2(dir_x * PROJECTILE_SPEED, dir_y * PROJECTILE_SPEED)  # Vélocité
                    })
                    # Effets visuels et sonores du tir
                    shoot_recoil = 0.12  # Animation de recul
                    create_particles((proj_x, proj_y), (255, 230, 100), 6)  # Particules jaunes
        elif event.type == pygame.KEYDOWN and game_state == "PAUSED":
            # === CONTRÔLES CLAVIER DU MENU PAUSE ===
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                # Entrée ou Espace: reprendre le jeu
                game_state = "PLAYING"
            elif event.key == pygame.K_m:
                # Touche M: retourner au menu principal
                game_state = "MENU"
                
        elif event.type == pygame.KEYDOWN:
            # === AUTRES CONTRÔLES CLAVIER ===
            if game_state == "MENU" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                # === DÉMARRAGE RAPIDE DEPUIS LE MENU (CLAVIER) ===
                # Lancer le jeu sans utiliser la souris
                score = 0  # Réinitialiser le score
                lives = 3  # Réinitialiser les vies
                invuln_timer = 0.0  # Pas d'invulnérabilité
                is_invulnerable = False  # Joueur vulnérable
                victory = False  # Pas de victoire
                level_transition_active = False  # Pas de transition
                level_transition_phase = "fade_out"
                level_transition_timer = 0.0
                level_transition_next_idx = None
                # Appliquer le niveau sélectionné au démarrage
                apply_level(levels[selected_level_idx])
                instantiate_level_enemies()  # Créer les ennemis
                player_pos = spawn_point  # Positionner le joueur
                player_vel_y = 0  # Pas de vélocité verticale
                game_state = "PLAYING"  # Passer en mode jeu
                projectiles = []  # Vider les projectiles
                particles = []  # Vider les particules
                monster_spawn_timer = 0.0  # Réinitialiser le timer de spawn
                stamina = STAMINA_MAX  # Endurance maximale
                stamina_idle_timer = 0.0
                jump_was_pressed = False
                dash_was_pressed = False
                dash_timer = 0.0
                dash_direction = 1
                game_state = "PLAYING"  # Passer en mode jeu (double assurance)
                start_tutorial()  # Afficher le tutoriel
                
            elif game_state == "MENU" and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                # === NAVIGATION ENTRE LES NIVEAUX DANS LE MENU ===
                if event.key == pygame.K_LEFT:
                    # Flèche gauche: niveau précédent (avec boucle)
                    selected_level_idx = (selected_level_idx - 1) % len(levels)
                else:
                    # Flèche droite: niveau suivant (avec boucle)
                    selected_level_idx = (selected_level_idx + 1) % len(levels)
                # Pré-appliquer le niveau sélectionné pour que les valeurs soient prêtes au lancement
                apply_level(levels[selected_level_idx])

    # === AFFICHAGE DU MENU PRINCIPAL ===
    if game_state == "MENU":
        # === ARRIÈRE-PLAN ANIMÉ ===
        update_clouds(dt)  # Mettre à jour les nuages pour l'effet parallax
        draw_parallax_background()  # Dessiner le fond dégradé avec montagnes

        # === TITRE DU JEU ===
        title_surf = title_font.render("Steel Reborn", True, (255, 255, 255))
        screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, SCREEN_HEIGHT//2 - 140))

        # === FONCTION DE DESSIN DES BOUTONS ===
        mouse_pos = pygame.mouse.get_pos()  # Position actuelle de la souris
        def draw_button(rect, text):
            """
            Dessine un bouton avec effet de survol.
            
            Args:
                rect: Rectangle pygame définissant la position et la taille du bouton
                text: Texte à afficher sur le bouton
            """
            hovered = rect.collidepoint(mouse_pos)  # Vérifier si la souris survole le bouton
            base = (50, 50, 50)    # Couleur de base (gris foncé)
            hover = (80, 80, 80)  # Couleur au survol (gris clair)
            # Dessiner le rectangle avec la couleur appropriée
            pygame.draw.rect(screen, hover if hovered else base, rect, border_radius=10)
            # Dessiner la bordure
            pygame.draw.rect(screen, (200, 200, 200), rect, 3, border_radius=10)
            # Dessiner le texte centré
            txt = font.render(text, True, (255, 255, 255))
            screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

        # === AFFICHAGE DU NOM DU NIVEAU SÉLECTIONNÉ ===
        level_name = levels[selected_level_idx].get("name", f"Niveau {selected_level_idx+1}")
        level_txt = small_font.render(f"Niveau: {level_name}", True, (255, 255, 255))
        screen.blit(level_txt, (SCREEN_WIDTH//2 - level_txt.get_width()//2, SCREEN_HEIGHT//2 - 60))

        # === DESSIN DES BOUTONS ===
        draw_button(play_rect, "Jouer")
        draw_button(quit_rect, "Quitter")

        # === INDICATIONS DE CONTRÔLES ===
        hint = small_font.render("Entrée/Espace pour jouer", True, (230, 230, 230))
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT//2 + 220))

        # === MISE À JOUR DE L'AFFICHAGE ===
        pygame.display.flip()  # Afficher le buffer à l'écran
        dt = clock.tick(FPS) / 1000  # Limiter le FPS et obtenir le delta time
        continue  # Passer à la frame suivante

    # === AFFICHAGE DU MENU PAUSE ===
    if game_state == "PAUSED":
        # === ARRIÈRE-PLAN ASSOMBRIS ===
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Overlay semi-transparent noir
        screen.blit(overlay, (0, 0))

        # === TITRE DU MENU PAUSE ===
        pause_title = title_font.render("Pause", True, (255, 255, 255))
        screen.blit(pause_title, (SCREEN_WIDTH//2 - pause_title.get_width()//2, SCREEN_HEIGHT//2 - 120))

        # === FONCTION DE DESSIN DES BOUTONS (réutilisée du menu principal) ===
        mouse_pos = pygame.mouse.get_pos()
        def draw_button(rect, text):
            """
            Dessine un bouton avec effet de survol (même fonction que dans le menu principal).
            """
            hovered = rect.collidepoint(mouse_pos)
            base = (50, 50, 50)
            hover = (80, 80, 80)
            pygame.draw.rect(screen, hover if hovered else base, rect, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), rect, 3, border_radius=10)
            txt = font.render(text, True, (255, 255, 255))
            screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

        # === DESSIN DES BOUTONS DU MENU PAUSE ===
        draw_button(pause_resume_rect, "Reprendre")
        draw_button(pause_menu_rect, "Menu")
        draw_button(pause_quit_rect, "Quitter")

        # === INDICATIONS DE CONTRÔLES ===
        hint = small_font.render("Echap/Entrée/Espace: Reprendre | M: Menu", True, (230, 230, 230))
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT//2 + 250))

        # === MISE À JOUR DE L'AFFICHAGE ===
        pygame.display.flip()  # Afficher le buffer à l'écran
        dt = clock.tick(FPS) / 1000  # Limiter le FPS et obtenir le delta time
        continue  # Passer à la frame suivante

    # === LOGIQUE PRINCIPALE DU JEU (exécutée uniquement en mode PLAYING) ===

    # === GESTION DE L'ENDURANCE ET DU TEMPS D'INACTIVITÉ ===
    stamina_idle_timer += dt  # Accumuler le temps depuis la dernière action
    keys = pygame.key.get_pressed()  # Obtenir l'état de toutes les touches
    moving = False  # Indicateur de mouvement du joueur
    
    # === MOUVEMENT HORIZONTAL DU JOUEUR ===
    if keys[pygame.K_q] or keys[pygame.K_LEFT]:
        # Déplacement vers la gauche
        player_pos.x -= MOVE_SPEED * dt
        flip = True  # Retourner le sprite du personnage
        direction = -1  # Direction du regard vers la gauche
        moving = True  # Le joueur est en mouvement
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        # Déplacement vers la droite
        player_pos.x += MOVE_SPEED * dt
        flip = False  # Ne pas retourner le sprite
        direction = 1  # Direction du regard vers la droite
        moving = True  # Le joueur est en mouvement
    
    # === GESTION DE L'ANIMATION DE MARCHE ===
    if moving:
        walk_cycle = 10 * dt  # Faire progresser le cycle d'animation
    else:
        walk_cycle = 0  # Réinitialiser le cycle quand le joueur s'arrête

    # === DÉTECTION DE COLLISION AVEC LE SOL ET LES PLATEFORMES ===
    feet_y = player_pos.y + head_radius + body_height + leg_height  # Position Y des pieds
    on_ground = False  # Indicateur: le joueur est-il au sol ?
    
    # Vérifier la collision avec le sol infini (limité en X)
    if feet_y >= GROUND_Y - 0.1 and GROUND_START_X <= player_pos.x <= GROUND_END_X:
        on_ground = True  # Le joueur est sur le sol
    else:
        # Si pas sur le sol, vérifier les plateformes
        for plat in platforms:
            # Vérifier si le joueur est au-dessus d'une plateforme (avec une petite tolérance horizontale)
            if plat.left - 5 < player_pos.x < plat.right + 5 and abs(feet_y - plat.top) <= 6:
                on_ground = True  # Le joueur est sur une plateforme
                # Positionner le joueur précisément sur la plateforme
                player_pos.y = plat.top - (head_radius + body_height + leg_height)
                player_vel_y = 0  # Annuler la vélocité verticale
                break  # Sortir de la boucle (une seule plateforme à la fois)

    # === RÉINITIALISATION DES SAUTS EN L'AIR ===
    if on_ground:
        air_jumps_left = 1  # Le joueur a droit à un saut en l'air quand il touche le sol

    # === GESTION DES SAUTS (NORMAL ET DOUBLE SAUT) ===
    space_pressed = keys[pygame.K_SPACE]  # État actuel de la touche de saut
    if space_pressed and not jump_was_pressed:
        # Détecter l'appui sur la touche (évite les sauts multiples)
        if on_ground and stamina >= STAMINA_JUMP_COST:
            # === SAUT NORMAL (depuis le sol) ===
            player_vel_y = JUMP_FORCE  # Appliquer la force de saut vers le haut
            stamina = max(0, stamina - STAMINA_JUMP_COST)  # Consommer de l'endurance
            stamina_idle_timer = 0.0  # Réinitialiser le timer d'inactivité
            stamina_regen_timer = 0.0  # Réinitialiser le timer de régénération
            air_jumps_left = 1  # Réinitialiser les sauts en l'air disponibles
            jump.play()  # Jouer le son de saut
        elif not on_ground and air_jumps_left > 0 and stamina >= DOUBLE_JUMP_COST:
            # === DOUBLE SAUT (en l'air) ===
            player_vel_y = JUMP_FORCE  # Appliquer la force de saut
            jump.play()  # Jouer le son de saut
            stamina = max(0, stamina - DOUBLE_JUMP_COST)  # Consommer plus d'endurance
            stamina_idle_timer = 0.0  # Réinitialiser le timer d'inactivité
            stamina_regen_timer = 0.0  # Réinitialiser le timer de régénération
            air_jumps_left -= 1  # Consommer un saut en l'air

    # === GESTION DU DASH (COURSE RAPIDE) ===
    dash_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]  # État des touches Shift
    if dash_pressed and not dash_was_pressed and dash_timer <= 0 and stamina >= DASH_COST:
        # Conditions: appui sur Shift + pas de dash en cours + assez d'endurance
        
        # Déterminer la direction du dash
        desired_dir = 0
        if keys[pygame.K_q] or keys[pygame.K_LEFT]:
            desired_dir = -1  # Dash vers la gauche
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            desired_dir = 1   # Dash vers la droite
        else:
            desired_dir = direction  # Dash dans la direction du regard par défaut
        
        if desired_dir != 0:  # Si une direction valide est déterminée
            dash_direction = desired_dir  # Définir la direction du dash
            dash_timer = DASH_DURATION  # Démarrer le timer du dash
            stamina = max(0, stamina - DASH_COST)  # Consommer de l'endurance
            stamina_idle_timer = 0.0  # Réinitialiser le timer d'inactivité
            stamina_regen_timer = 0.0  # Réinitialiser le timer de régénération

    # === MISE À JOUR DES ÉTATS DES TOUCHES (pour éviter les déclenchements multiples) ===
    jump_was_pressed = space_pressed  # Mémoriser l'état précédent de la touche de saut
    dash_was_pressed = dash_pressed  # Mémoriser l'état précédent de la touche de dash

    # === PHYSIQUE: GRAVITÉ ET MISE À JOUR DE POSITION ===
    player_vel_y += GRAVITY * dt  # Appliquer l'accélération due à la gravité
    player_pos.y += player_vel_y * dt  # Mettre à jour la position verticale

    # === CORRECTION DE POSITION AVEC LE SOL (empêcher de traverser le sol) ===
    feet_y = player_pos.y + head_radius + body_height + leg_height  # Recalculer la position des pieds
    if feet_y > GROUND_Y and GROUND_START_X <= player_pos.x <= GROUND_END_X:
        # Si les pieds sont sous le sol, replacer le joueur sur le sol
        player_pos.y = GROUND_Y - (head_radius + body_height + leg_height)
        player_vel_y = 0  # Annuler la vélocité verticale

    # === COLLISIONS AVEC LES PLATEFORMES (atterrissage depuis le haut) ===
    # Créer un rectangle de collision pour le joueur
    player_rect = pygame.Rect(
        int(player_pos.x - head_radius),  # Position X (bord gauche)
        int(player_pos.y - head_radius),  # Position Y (bord supérieur)
        head_radius*2,  # Largeur (diamètre de la tête)
        head_radius*2 + body_height + leg_height  # Hauteur totale
    )
    
    if player_vel_y >= 0:  # Seulement si le joueur descend (évite les collisions par le dessous)
        for plat in platforms:
            if player_rect.colliderect(plat):  # Vérifier la collision rectangle-rectangle
                plat_top = plat.top  # Position Y du haut de la plateforme
                # Vérifier si le joueur était au-dessus de la plateforme avant la collision
                if feet_y - player_vel_y * dt <= plat_top:
                    # Positionner le joueur sur la plateforme
                    player_pos.y = plat_top - (head_radius + body_height + leg_height)
                    player_vel_y = 0  # Annuler la vélocité verticale
                    break  # Sortir de la boucle (une seule plateforme à la fois)

    # === EXÉCUTION DU DASH ===
    if dash_timer > 0:
        # Si un dash est en cours, déplacer le joueur à vitesse élevée
        player_pos.x += dash_direction * DASH_SPEED * dt  # Déplacement horizontal du dash
        dash_timer = max(0.0, dash_timer - dt)  # Réduire le timer du dash

    # === LIMITATION DES BORDS DE L'ÉCRAN (empêcher de sortir par la gauche) ===
    player_pos.x = max(head_radius, player_pos.x)  # Le joueur ne peut pas dépasser le bord gauche

    # === SYSTÈME DE RÉGÉNÉRATION D'ENDURANCE ===
    if stamina_idle_timer >= STAMINA_REGEN_DELAY and stamina < STAMINA_MAX:
        # Si le joueur est inactif depuis assez longtemps ET n'a pas l'endurance maximale
        stamina_regen_timer += dt  # Accumuler le temps pour la régénération
        # Régénérer l'endurance par intervalles
        while stamina_regen_timer >= STAMINA_REGEN_INTERVAL and stamina < STAMINA_MAX:
            stamina = min(STAMINA_MAX, stamina + STAMINA_REGEN_AMOUNT)  # Ajouter de l'endurance sans dépasser le max
            stamina_regen_timer -= STAMINA_REGEN_INTERVAL  # Consommer l'intervalle de temps
        if stamina >= STAMINA_MAX:  # Si l'endurance est pleine
            stamina_regen_timer = 0.0  # Réinitialiser le timer de régénération
    else:
        # Si le joueur n'est pas inactif, réinitialiser le timer de régénération
        stamina_regen_timer = 0.0

    # === EFFETS VISUELS À L'ATTERRISSAGE ===
    if not prev_on_ground and on_ground and player_vel_y == 0:
        # Si le joueur vient d'atterrir (était en l'air, maintenant au sol, vélocité nulle)
        feet_x = player_pos.x  # Position X des pieds (même que le centre X du joueur)
        # Déterminer si l'attérissage se fait sur le sol ou une plateforme
        feet_y = GROUND_Y if feet_y >= GROUND_Y else player_pos.y + head_radius + body_height + leg_height
        # Créer des particules de poussière à l'endroit de l'attérissage
        create_particles((feet_x, feet_y), (180, 180, 180), 10)  # Particules grises
    prev_on_ground = on_ground  # Mémoriser l'état au sol pour la prochaine frame

    # === SYSTÈME DE CLIGNEMENT DES YEUX ===
    blink_timer -= dt  # Réduire le timer avant le prochain clignement
    if blink_timer <= 0 and blink_close <= 0:  # Si le timer est écoulé et les yeux sont ouverts
        blink_close = 0.12  # Durée du clignement (secondes)
        blink_timer = random.uniform(2.0, 5.0)  # Prochain clignement entre 2 et 5 secondes
    if blink_close > 0:  # Si les yeux sont en train de se fermer
        blink_close -= dt  # Réduire la durée du clignement
        
    # === GESTION DE L'ANIMATION DE RECUL APRÈS TIR ===
    if shoot_recoil > 0:  # Si l'animation de recul est active
        shoot_recoil -= dt  # Réduire la durée de l'animation

    # === DÉTECTION DE MORT PAR CHUTE ===
    if player_pos.y > DEATH_BELOW_Y:  # Si le joueur est tombé trop bas
        lives -= 1  # Perte d'une vie
        is_invulnerable = True  # Le joueur devient invulnérable après la mort
        invuln_timer = invuln_time  # Démarrer le timer d'invulnérabilité
        player_pos = spawn_point  # Téléporter le joueur au point de spawn
        player_vel_y = 0  # Annuler la vélocité verticale
        # Créer des particules rouges pour indiquer la mort
        create_particles(player_pos, (255, 100, 100), 15)

    # === SYSTÈME DE CAMÉRA (suivi doux du joueur) ===
    # Calculer la position cible de la caméra (centrée sur le joueur)
    target_x = player_pos.x - SCREEN_WIDTH // 2  # Centrer horizontalement
    target_y = player_pos.y - SCREEN_HEIGHT // 2  # Centrer verticalement
    # Appliquer un lissage pour un mouvement fluide de la caméra
    camera_offset.x += (target_x - camera_offset.x) * CAMERA_LAG
    camera_offset.y += (target_y - camera_offset.y) * CAMERA_LAG

    # === MISE À JOUR DES PROJECTILES ===
    for proj in projectiles[:]:  # Itérer sur une copie pour pouvoir supprimer pendant l'itération
        # Mettre à jour la position du projectile en fonction de sa vélocité
        proj["pos"] += proj["vel"] * dt
        # Vérifier si le projectile est sorti de la zone visible (avec une marge)
        if (proj["pos"].x < camera_offset.x - 200 or proj["pos"].x > camera_offset.x + SCREEN_WIDTH + 200 or
            proj["pos"].y < camera_offset.y - 200 or proj["pos"].y > camera_offset.y + SCREEN_HEIGHT + 200):
            # Supprimer le projectile s'il est trop loin de l'écran
            projectiles.remove(proj)


    # === COLLISIONS PROJECTILE-MONSTRE ===
    for proj in projectiles[:]:  # Itérer sur une copie des projectiles
        for monster in monsters[:]:  # Itérer sur une copie des monstres
            # Vérifier la collision entre le projectile et le monstre (distance entre centres)
            if proj["pos"].distance_to(monster["pos"]) < projectile_radius + monster["radius"]:
                # Collision détectée!
                monster["hp"] -= 1  # Infliger des dégâts au monstre
                monster["hit_flash"] = 0.2  # Démarrer l'animation de flash de dégâts

                if monster["hp"] <= 0:  # Si le monstre n'a plus de points de vie
                    # Le monstre est mort
                    create_particles(monster["pos"], (255, 50, 50), 12)  # Particules rouges d'explosion
                    monsters.remove(monster)  # Supprimer le monstre de la liste
                    # Ajouter des points au score (plus pour les tanks)
                    score += 2 if monster["type"] == "tank" else 1

                # Supprimer le projectile après l'impact
                if proj in projectiles:
                    projectiles.remove(proj)
                break  # Sortir de la boucle des monstres (un projectile ne touche qu'un monstre)

    # === SYSTÈME DE SPAWN DES MONSTRES (avec cooldown) ===
    monster_spawn_timer -= dt  # Réduire le temps avant le prochain spawn
    if monster_spawn_timer <= 0:  # Si le cooldown est terminé
        spawned = False  # Indicateur: un monstre a-t-il été spawné ?
        if level_enemy_configs:
            # === MODE CONFIGURÉ: utiliser les ennemis du fichier de niveau ===
            # Identifier quels ennemis sont déjà actifs
            active_ids = {m.get("template_id") for m in monsters if m.get("template_id") is not None}
            next_id = None  # ID du prochain ennemi à spawn
            # Chercher le premier ennemi non encore actif
            for idx in range(len(level_enemy_configs)):
                if idx not in active_ids:
                    next_id = idx
                    break
            if next_id is not None:  # Si on a trouvé un ennemi à spawn
                monsters.append(create_monster_from_config(level_enemy_configs[next_id], template_id=next_id))
                spawned = True
        else:
            # === MODE ALÉATOIRE: générer des monstres aléatoires ===
            if len(monsters) < MAX_MONSTERS:  # Vérifier qu'on n'a pas atteint la limite
                monsters.append(spawn_monster())  # Ajouter un monstre aléatoire
                spawned = True
        if spawned:  # Si un monstre a été spawné
            monster_spawn_timer = MONSTER_SPAWN_COOLDOWN  # Redémarrer le cooldown

    # === MISE À JOUR DES MONSTRES (mouvement, comportement, animations) ===
    for monster in monsters:
        # === MOUVEMENT HORIZONTAL ===
        monster["pos"].x += monster["dir"] * monster["speed"] * dt  # Déplacer le monstre
        # Gérer les rebonds aux limites du monde
        if monster["pos"].x < 50:  # Limite gauche atteinte
            monster["dir"] = 1  # Changer de direction vers la droite
        if monster["pos"].x > 2500:  # Limite droite atteinte
            monster["dir"] = -1  # Changer de direction vers la gauche

        # === COMPORTEMENT SPÉCIFIQUE AU TYPE DE MONSTRE ===
        if monster.get("type") == "flyer":
            # === MONSTRE VOLANT: mouvement ondulant vertical ===
            monster["fly_phase"] += dt * 2.0  # Faire progresser la phase de vol
            # Calculer la position Y avec une fonction sinusoïdale pour un vol ondulant
            monster["pos"].y = monster["base_y"] + math.sin(monster["fly_phase"]) * 25
        else:
            # === MONSTRE TERRESTRE: gravité et collision avec le sol ===
            # Appliquer la gravité
            monster["vel_y"] += GRAVITY * dt
            monster["pos"].y += monster["vel_y"] * dt

            # Collision avec le sol
            feet_y = monster["pos"].y + monster["radius"]  # Position Y des pieds du monstre
            if feet_y > GROUND_Y:  # Si les pieds sont sous le sol
                monster["pos"].y = GROUND_Y - monster["radius"]  # Replacer sur le sol
                monster["vel_y"] = 0  # Annuler la vélocité verticale

            # === COLLISION AVEC LES PLATEFORMES (atterrissage depuis le haut) ===
            if monster["vel_y"] >= 0:  # Seulement si le monstre descend
                # Créer un rectangle de collision pour le monstre
                monster_rect = pygame.Rect(
                    int(monster["pos"].x - monster["radius"]),  # Position X
                    int(monster["pos"].y - monster["radius"]),  # Position Y
                    monster["radius"]*2,  # Largeur (diamètre)
                    monster["radius"]*2  # Hauteur (diamètre)
                )
                for plat in platforms:
                    if monster_rect.colliderect(plat):  # Vérifier la collision
                        plat_top = plat.top  # Position Y du haut de la plateforme
                        # Vérifier si le monstre était au-dessus avant la collision
                        if feet_y - monster["vel_y"] * dt <= plat_top + 2:
                            # Positionner le monstre sur la plateforme
                            monster["pos"].y = plat_top - monster["radius"]
                            monster["vel_y"] = 0  # Annuler la vélocité verticale
                            break  # Sortir de la boucle des plateformes

        # === ANIMATION DE FLASH DE DÉGÂTS ===
        if monster["hit_flash"] > 0:  # Si le monstre vient de prendre des dégâts
            monster["hit_flash"] -= dt  # Réduire la durée du flash

    # === COLLISIONS JOUEUR-MONSTRE ===
    p_center = (int(player_pos.x), int(player_pos.y))  # Centre du joueur pour la collision
    if not is_invulnerable:  # Ne vérifier les collisions que si le joueur est vulnérable
        for monster in monsters[:]:  # Itérer sur une copie pour pouvoir supprimer
            # Utiliser la fonction de collision cercle-rectangle
            if circle_rect_collision((monster["pos"].x, monster["pos"].y), monster["radius"], player_rect):
                # Collision détectée entre le joueur et un monstre!
                lives -= 1  # Le joueur perd une vie
                is_invulnerable = True  # Le joueur devient invulnérable
                invuln_timer = invuln_time  # Démarrer le timer d'invulnérabilité
                player_pos = spawn_point  # Téléporter le joueur au point de spawn
                player_vel_y = 0  # Annuler la vélocité verticale
                # Créer des particules jaunes pour indiquer la prise de dégâts
                create_particles(player_pos, (255, 255, 100), 15)
                break  # Sortir de la boucle (une seule collision à la fois)

    # === GESTION DE L'INVULNÉRABILITÉ DU JOUEUR ===
    if is_invulnerable:  # Si le joueur est actuellement invulnérable
        invuln_timer -= dt  # Réduire le temps d'invulnérabilité restant
        if invuln_timer <= 0:  # Quand le timer est écoulé
            is_invulnerable = False  # Le joueur redevient vulnérable

    # === MISE À JOUR DES PARTICULES ===
    for part in particles[:]:  # Itérer sur une copie pour pouvoir supprimer pendant l'itération
        # Mettre à jour la position de la particule
        part["pos"] += part["vel"] * dt
        # Appliquer une gravité réduite aux particules (effet plus réaliste)
        part["vel"].y += GRAVITY * 0.5 * dt
        # Réduire la durée de vie de la particule
        part["life"] -= dt * 2  # Les particules disparaissent plus vite qu'elles ne tombent
        if part["life"] <= 0:  # Si la particule est "morte"
            particles.remove(part)  # Supprimer la particule de la liste

    # === DÉTECTION DE VICTOIRE (atteinte de l'objectif) ===
    if (not victory and not level_transition_active and
        # Créer un rectangle pour la tête du joueur et vérifier la collision avec l'objectif
        pygame.Rect(int(player_pos.x - head_radius), int(player_pos.y - head_radius),
                    head_radius*2, head_radius*2).colliderect(goal_rect)):
        # Le joueur a atteint la porte/objectif!
        hide_tutorial()  # Masquer le tutoriel
        if selected_level_idx < len(levels) - 1:  # S'il y a d'autres niveaux
            # Démarrer une transition vers le niveau suivant
            level_transition_active = True
            level_transition_phase = "fade_out"  # Commencer par un fondu au noir
            level_transition_timer = 0.0
            level_transition_next_idx = selected_level_idx + 1  # Index du niveau suivant
        else:
            # C'était le dernier niveau: victoire complète!
            victory = True

    # === SYSTÈME DE RENDU GRAPHIQUE ===
    
    # === ARRIÈRE-PLAN: CIEL DÉGRADÉ ===
    for i in range(SCREEN_HEIGHT):
        # Calculer la couleur interpolée pour chaque ligne horizontale
        color = (
            int(70 + (130 - 70) * i / SCREEN_HEIGHT),  # Rouge: 70 → 130
            int(130 + (180 - 130) * i / SCREEN_HEIGHT),  # Vert: 130 → 180
            int(180 + (230 - 180) * i / SCREEN_HEIGHT)   # Bleu: 180 → 230
        )
        # Dessiner une ligne horizontale avec la couleur calculée
        pygame.draw.line(screen, color, (0, i), (SCREEN_WIDTH, i))

    # === SOL AVEC TEXTURE ===
    ground_rect = pygame.Rect(
        GROUND_START_X - camera_offset.x,  # Position X (décalée par la caméra)
        GROUND_Y - camera_offset.y,        # Position Y (décalée par la caméra)
        GROUND_END_X - GROUND_START_X,   # Largeur totale du sol
        100                             # Hauteur visible du sol
    )
    pygame.draw.rect(screen, GROUND_COLOR, ground_rect)  # Dessiner le rectangle principal du sol
    pygame.draw.rect(screen, (25, 100, 25), ground_rect, 3)  # Bordure verte plus foncée
    
    # === LIGNES DE TEXTURE DU SOL ===
    for i in range(0, 3000, 50):  # Lignes toutes les 50 pixels
        pygame.draw.line(screen, (44, 160, 44),  # Vert plus clair pour les lignes
                        (i - camera_offset.x, GROUND_Y - camera_offset.y),  # Point de départ
                        (i - camera_offset.x, GROUND_Y - camera_offset.y + 100),  # Point d'arrivée
                        2)  # Épaisseur de la ligne

    # === PLATEFORMES AVEC EFFET DE RELIEF ===
    for plat in platforms:
        # Calculer la position de la plateforme à l'écran (décalée par la caméra)
        plat_rect_screen = plat.move(-camera_offset.x, -camera_offset.y)
        # Dessiner le rectangle principal de la plateforme
        pygame.draw.rect(screen, PLATFORM_COLOR, plat_rect_screen)
        # Dessiner la bordure en surbrillance
        pygame.draw.rect(screen, PLATFORM_HIGHLIGHT, plat_rect_screen, 3)
        # Ajouter une ligne horizontale pour un effet de profondeur
        pygame.draw.line(screen, (80, 50, 20),  # Marron foncé pour l'ombre
                        (plat_rect_screen.left, plat_rect_screen.top + 5),  # Point de départ
                        (plat_rect_screen.right, plat_rect_screen.top + 5),  # Point d'arrivée
                        2)  # Épaisseur de la ligne

    # === PORTE/OBJECTIF AVEC DÉTAILS VISUELS ===
    goal_rect_screen = goal_rect.move(-camera_offset.x, -camera_offset.y)  # Position à l'écran
    # Dessiner le rectangle principal de la porte
    pygame.draw.rect(screen, DOOR_COLOR, goal_rect_screen)
    # Dessiner le cadre de la porte
    pygame.draw.rect(screen, DOOR_FRAME, goal_rect_screen, 5)
    # Ajouter une ligne verticale centrale pour simuler les battants de porte
    pygame.draw.line(screen, (100, 70, 20),  # Marron très foncé
                    (goal_rect_screen.centerx, goal_rect_screen.top),    # Point de départ (en haut)
                    (goal_rect_screen.centerx, goal_rect_screen.bottom),  # Point d'arrivée (en bas)
                    3)  # Épaisseur de la ligne
    # Dessiner la poignée de porte
    knob_pos = (goal_rect_screen.right - 12, goal_rect_screen.centery)  # Position de la poignée
    pygame.draw.circle(screen, (30, 30, 30), knob_pos, 6)  # Cercle extérieur (noir)
    pygame.draw.circle(screen, (80, 80, 80), knob_pos, 3)  # Cercle intérieur (gris)

    # === OMBRES AU SOL (commentées pour le moment) ===
    player_feet = player_pos.y + head_radius + body_height + leg_height  # Position Y des pieds du joueur
    # Ombres désactivées (code commenté)
    ## draw_shadow(player_pos.x, player_feet, head_radius + 12)  # Ombre du joueur
    ## for monster in monsters:  # Ombres de tous les monstres
    ##    draw_shadow(monster["pos"].x, monster["pos"].y + monster["radius"], monster["radius"])

    # === RENDU DU JOUEUR ===
    # Calculer la position du joueur à l'écran
    p_center_screen = (int(player_pos.x - camera_offset.x), int(player_pos.y - camera_offset.y))
    # Vérifier si le joueur est en mouvement actuellement
    moving_now = keys[pygame.K_q] or keys[pygame.K_LEFT] or keys[pygame.K_d] or keys[pygame.K_RIGHT]
    # Calculer l'effet de "bobbing" vertical pendant la marche
    bob = math.sin(walk_cycle * 12) * 2 if moving_now else 0
    # Position finale de rendu (avec effet de bobbing)
    render_center = (p_center_screen[0], p_center_screen[1] + int(bob))

    # === GESTION DE L'INVULNÉRABILITÉ VISUELLE (effet de clignotement) ===
    if not is_invulnerable or int(invuln_timer * 10) % 2 == 0:
        # Si le joueur n'est pas invulnérable OU s'il est dans une phase visible du clignotement
        
        # === SÉLECTION DE L'ANIMATION DE MARCHE ===
        if moving:
            # Animation de marche en cycle (4 images)
            if cnt < 5:
                movement = "perso.png"   # Image 1: position debout
            elif cnt < 9:
                movement = "perso2.png"  # Image 2: jambe droite en avant
            elif cnt < 13:
                movement = "perso3.png"  # Image 3: position intermédiaire
            elif cnt < 17:
                movement = "perso4.png"  # Image 4: jambe gauche en avant
            elif cnt > 16:
                cnt = 0  # Réinitialiser le compteur pour boucler
        else:
            movement = "perso.png"  # Position debout quand immobile
            
        # === CHARGEMENT ET RENDU DE L'IMAGE DU PERSONNAGE ===
        # Charger l'image appropriée pour l'animation actuelle
        image = load_image(movement)
        # Redimensionner l'image (taille 2x pour meilleure visibilité)
        image = pygame.transform.scale(image, (image.get_width()*2, image.get_height()*2))
        # Retourner l'image horizontalement si le joueur regarde à gauche
        if direction == -1:
            image = pygame.transform.flip(image, True, False)
        # Calculer le rectangle de positionnement de l'image
        image_rect = pygame.Rect(
            p_center_screen[0]-image.get_width()/2,  # Centrer horizontalement
            p_center_screen[1]+image.get_height()/2,  # Position Y (note: + car l'origine est en haut)
            -40,  # Offset X (ajustement manuel)
            -40   # Offset Y (ajustement manuel)
        )
        # Dessiner l'image du personnage à l'écran
        screen.blit(image, image_rect)

    # === RENDU DES PROJECTILES AVEC EFFET DE TRAÎNÉE ===
    for proj in projectiles:
        # Calculer la position du projectile à l'écran
        proj_screen = (int(proj["pos"].x - camera_offset.x), int(proj["pos"].y - camera_offset.y))
        # Dessiner une couche extérieure plus claire (effet de glow)
        pygame.draw.circle(screen, (150, 255, 150), proj_screen, projectile_radius + 2)
        # Dessiner le cercle principal du projectile (vert vif)
        pygame.draw.circle(screen, (0, 255, 0), proj_screen, projectile_radius)
        # Dessiner le centre blanc pour un effet de brillance
        pygame.draw.circle(screen, (255, 255, 255), proj_screen, projectile_radius - 3)

    # === RENDU DES MONSTRES (avec animations spécifiques par type) ===
    for monster in monsters:
        # Calculer la position du monstre à l'écran
        monster_screen = (
            int(monster["pos"].x - camera_offset.x),  # Position X à l'écran
            int(monster["pos"].y - camera_offset.y)   # Position Y à l'écran
        )
        r = monster["radius"]  # Rayon du monstre

        # === DÉTERMINATION DE LA COULEUR (avec effet de flash de dégâts) ===
        base_colors = {
            "tank": (200, 40, 40),    # Rouge foncé pour les tanks
            "fast": (255, 140, 0),   # Orange pour les rapides
            "flyer": (100, 160, 255), # Bleu clair pour les volants
        }
        # Couleur normale ou blanche si le monstre vient de prendre des dégâts
        monster_color = (255, 220, 220) if monster["hit_flash"] > 0 else base_colors.get(monster["type"], (220, 20, 20))

        # === RENDU SPÉCIFIQUE PAR TYPE DE MONSTRE ===
        if monster["type"] == "tank":
            # === TANK: monstre gros et lent ===
            image = load_image('monster2.webp')  # Charger l'image du tank
            if monster["dir"] == -1:  # Retourner si regarde à gauche
                image = pygame.transform.flip(image, True, False)
            # Redimensionner (taille 3x pour les gros monstres)
            image = pygame.transform.scale(image, (image.get_width()*3, image.get_height()*3))
            # Positionner l'image
            image_rect = pygame.Rect(
                monster_screen[0]-image.get_width()/3,  # Position X (avec ajustement)
                monster_screen[1]-image.get_height()/3,  # Position Y (avec ajustement)
                40,  # Largeur du rectangle de collision
                40   # Hauteur du rectangle de collision
            )
            # Dessiner l'image du tank
            screen.blit(image, image_rect)
            
        elif monster["type"] == "fast":
            # === FAST: monstre petit et rapide ===
            image = load_image('monster1.png')  # Charger l'image du monstre rapide
            if monster["dir"] == -1:  # Retourner si regarde à gauche
                image = pygame.transform.flip(image, True, False)
            # Positionner l'image (sans redimensionnement supplémentaire)
            image_rect = pygame.Rect(
                monster_screen[0]-image.get_width()/3,  # Position X
                monster_screen[1]-image.get_height()/3,  # Position Y
                40,  # Largeur
                40   # Hauteur
            )
            # Dessiner l'image du monstre rapide
            screen.blit(image, image_rect)
            
        else:  # flyer
            # === FLYER: monstre volant avec animation complexe ===
            # Animation de vol en 5 images
            if cnt2 < 5:
                monster["anim"] = 'monsterb1.png'    # Ailes hautes
            elif cnt2 < 9:
                monster["anim"] = 'monsterb2.webp'  # Ailes moyennes-hautes
            elif cnt2 < 13:
                monster["anim"] = 'monsterb3.png'  # Ailes moyennes
            elif cnt2 < 17:
                monster["anim"] = 'monsterb4.webp'  # Ailes moyennes-basses
            elif cnt2 < 21:
                monster["anim"] = 'monsterb5.webp'  # Ailes basses
            elif cnt2 > 20:
                monster["anim"] = 'monsterb1.png'  # Retour au début
                cnt2 = 0  # Réinitialiser le compteur
            # Charger l'image d'animation actuelle
            image = load_image(monster["anim"])
            if monster["dir"] == 1:  # Retourner si regarde à droite (inverse des autres)
                image = pygame.transform.flip(image, True, False)
            # Redimensionner (taille 2x)
            image = pygame.transform.scale(image, (image.get_width()*2, image.get_height()*2))
            # Positionner l'image
            image_rect = pygame.Rect(
                monster_screen[0]-image.get_width()/2,  # Position X
                monster_screen[1]-image.get_height()/2,  # Position Y
                40,  # Largeur
                40   # Hauteur
            )
            # Dessiner l'image du monstre volant
            screen.blit(image, image_rect)

    # === RENDU DES PARTICULES ===
    for part in particles:
        if part["life"] > 0:  # Ne dessiner que les particules "vivantes"
            # Calculer la position de la particule à l'écran
            part_screen = (int(part["pos"].x - camera_offset.x), int(part["pos"].y - camera_offset.y))
            # Calculer la transparence en fonction de la durée de vie
            alpha = int(255 * part["life"])  # Plus la particule est vieille, plus elle est transparente
            # Calculer la couleur avec fade-out en fonction de la durée de vie
            color = tuple(min(255, max(0, int(c * part["life"]))) for c in part["color"])
            # Dessiner la particule comme un petit cercle
            pygame.draw.circle(screen, color, part_screen, 3)

    # === INTERFACE UTILISATEUR (HUD) ===
    # === PANNEAU SEMI-TRANSPARENT ===
    hud_panel = pygame.Surface((300, 210), pygame.SRCALPHA)  # Surface avec transparence
    hud_panel.fill((0, 0, 0, 120))  # Fond noir semi-transparent
    screen.blit(hud_panel, (10, 10))  # Positionner en haut à gauche

    # === AFFICHAGE DU SCORE ===
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (30, 25))

    # === AFFICHAGE DES VIES (avec cœurs) ===
    lives_text = font.render("Vies:", True, (255, 255, 255))
    screen.blit(lives_text, (30, 70))
    # Dessiner un cœur pour chaque vie restante
    for i in range(lives):
        heart_x = 130 + i * 35  # Espacer les cœurs horizontalement
        # Dessiner un cœur avec deux cercles et un triangle
        pygame.draw.circle(screen, (255, 50, 50), (heart_x - 5, 85), 10)  # Cercle gauche
        pygame.draw.circle(screen, (255, 50, 50), (heart_x + 5, 85), 10)  # Cercle droit
        pygame.draw.polygon(screen, (255, 50, 50),  # Triangle inférieur
                           [(heart_x - 15, 85), (heart_x, 100), (heart_x + 15, 85)])

    # === BARRE D'ENDURANCE ===
    stamina_label = small_font.render("Endurance", True, (180, 200, 255))
    screen.blit(stamina_label, (30, 120))
    # Arrière-plan de la barre
    stamina_bar_bg = pygame.Rect(30, 150, 240, 20)
    pygame.draw.rect(screen, (40, 40, 40), stamina_bar_bg, border_radius=6)
    # Calculer le remplissage de la barre
    stamina_ratio = stamina / STAMINA_MAX if STAMINA_MAX else 0  # Ratio d'endurance (0 à 1)
    fill_width = int(stamina_bar_bg.width * max(0, min(1, stamina_ratio)))  # Largeur du remplissage
    if fill_width > 0:  # Ne dessiner que s'il y a de l'endurance
        stamina_bar_fill = pygame.Rect(
            stamina_bar_bg.left, 
            stamina_bar_bg.top, 
            fill_width, 
            stamina_bar_bg.height
        )
        pygame.draw.rect(screen, (70, 170, 255), stamina_bar_fill, border_radius=6)  # Bleu clair
    # Bordure de la barre
    pygame.draw.rect(screen, (120, 180, 255), stamina_bar_bg, 2, border_radius=6)  # Bleu plus clair

    # === INDICATEUR D'INVULNÉRABILITÉ ===
    if is_invulnerable:
        inv_text = small_font.render("⚡ INVULNÉRABLE", True, (255, 255, 0))
        screen.blit(inv_text, (30, 180))

    # === INDICATEUR DE COOLDOWN DE SPAWN DES MONSTRES ===
    if monster_spawn_timer > 0:
        cooldown_text = small_font.render(f"Prochain spawn: {monster_spawn_timer:.1f}s",
                                         True, (200, 200, 200))
        screen.blit(cooldown_text, (SCREEN_WIDTH - 350, 30))  # En haut à droite

    # === SYSTÈME DE TRANSITION ENTRE NIVEAUX ===
    if level_transition_active:
        level_transition_timer += dt  # Faire progresser le timer de transition
        overlay_alpha = 0  # Transparence de l'overlay (0 = transparent, 255 = noir complet)
        
        if level_transition_phase == "fade_out":
            # === PHASE DE FONDU AU NOIR ===
            if LEVEL_TRANSITION_FADE_OUT > 0:
                # Calculer l'alpha en fonction du temps écoulé
                overlay_alpha = min(255, int((level_transition_timer / LEVEL_TRANSITION_FADE_OUT) * 255))
            else:
                overlay_alpha = 255  # Noir complet
            
            # Vérifier si le fondu au noir est terminé
            if level_transition_timer >= LEVEL_TRANSITION_FADE_OUT:
                # === CHARGEMENT DU NOUVEAU NIVEAU ===
                selected_level_idx = level_transition_next_idx  # Changer de niveau
                apply_level(levels[selected_level_idx])  # Appliquer la configuration du nouveau niveau
                instantiate_level_enemies()  # Créer les ennemis du nouveau niveau
                player_pos = spawn_point  # Positionner le joueur au nouveau spawn
                player_vel_y = 0  # Annuler la vélocité verticale
                projectiles = []  # Vider les projectiles
                particles = []  # Vider les particules
                monster_spawn_timer = 0.0  # Réinitialiser le timer de spawn
                # Réinitialiser le système d'endurance
                stamina = STAMINA_MAX
                stamina_idle_timer = 0.0
                stamina_regen_timer = 0.0
                air_jumps_left = 1
                jump_was_pressed = False
                dash_was_pressed = False
                dash_timer = 0.0
                dash_direction = 1
                shoot_recoil = 0.0
                prev_on_ground = True
                is_invulnerable = False
                invuln_timer = 0.0
                # Centrer la caméra sur le joueur
                camera_offset.x = player_pos.x - SCREEN_WIDTH // 2
                camera_offset.y = player_pos.y - SCREEN_HEIGHT // 2
                start_tutorial()  # Afficher le tutoriel du nouveau niveau
                
                # Passer à la phase de fondu depuis le noir
                level_transition_phase = "fade_in"
                level_transition_timer = 0.0
                overlay_alpha = 255  # Commencer avec un écran noir
                
        else:  # level_transition_phase == "fade_in"
            # === PHASE DE FONDU DEPUIS LE NOIR ===
            if LEVEL_TRANSITION_FADE_IN > 0:
                # Calculer l'alpha en fonction du temps écoulé (inverse du fade_out)
                overlay_alpha = max(0, 255 - int((level_transition_timer / LEVEL_TRANSITION_FADE_IN) * 255))
            else:
                overlay_alpha = 0  # Transparent
            
            # Vérifier si le fondu depuis le noir est terminé
            if level_transition_timer >= LEVEL_TRANSITION_FADE_IN:
                level_transition_active = False  # Terminer la transition
                level_transition_next_idx = None  # Réinitialiser l'index du prochain niveau
                level_transition_phase = "fade_out"  # Réinitialiser la phase par défaut
                level_transition_timer = 0.0  # Réinitialiser le timer
                overlay_alpha = 0  # Pas d'overlay
        
        # === DESSIN DE L'OVERLAY DE TRANSITION ===
        if overlay_alpha > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, overlay_alpha))  # Noir avec transparence variable
            screen.blit(overlay, (0, 0))

    # === ÉCRAN DE VICTOIRE ===
    if victory:
        # === ARRIÈRE-PLAN SEMI-TRANSPARENT ===
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Noir avec 70% d'opacité
        screen.blit(overlay, (0, 0))

        # === MESSAGES DE VICTOIRE ===
        # Grand titre "VICTOIRE !"
        big_text = pygame.font.SysFont(None, 120).render("VICTOIRE !", True, (255, 215, 0))  # Or
        # Sous-titre "Félicitations !"
        sub_text = font.render("Félicitations !", True, (255, 255, 255))  # Blanc
        # Score final
        score_final = font.render(f"Score Final: {score}", True, (255, 255, 255))  # Blanc

        # Positionner et dessiner les textes (centrés horizontalement)
        screen.blit(big_text, (SCREEN_WIDTH//2 - big_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
        screen.blit(sub_text, (SCREEN_WIDTH//2 - sub_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
        screen.blit(score_final, (SCREEN_WIDTH//2 - score_final.get_width()//2, SCREEN_HEIGHT//2 + 70))
        
        # Afficher l'écran pendant 1.5 secondes
        pygame.display.flip()
        pygame.time.delay(1500)
        
        # === RETOUR AU MENU PRINCIPAL ===
        game_state = "MENU"
        victory = False  # Réinitialiser l'état de victoire
        level_transition_active = False  # Réinitialiser le système de transition
        level_transition_next_idx = None
        level_transition_phase = "fade_out"
        level_transition_timer = 0.0

    # === ÉCRAN DE GAME OVER ===
    if lives <= 0:
        # === ARRIÈRE-PLAN SEMI-TRANSPARENT ===
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Noir avec 78% d'opacité
        screen.blit(overlay, (0, 0))

        # === MESSAGES DE GAME OVER ===
        # Grand titre "GAME OVER"
        over_text = pygame.font.SysFont(None, 96).render("GAME OVER", True, (255, 50, 50))  # Rouge vif
        # Score obtenu
        score_final = font.render(f"Score: {score}", True, (255, 255, 255))  # Blanc

        # Positionner et dessiner les textes (centrés horizontalement)
        screen.blit(over_text, (SCREEN_WIDTH//2 - over_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
        screen.blit(score_final, (SCREEN_WIDTH//2 - score_final.get_width()//2, SCREEN_HEIGHT//2 + 20))
        
        # Afficher l'écran pendant 1.5 secondes
        pygame.display.flip()
        pygame.time.delay(1500)
        
        # === RETOUR AU MENU PRINCIPAL ===
        game_state = "MENU"
        # === RÉINITIALISATION PARTIELLE DES VARIABLES ===
        # Note: le reset complet se fera quand on clique "Jouer"
        lives = 3  # Réinitialiser les vies
        score = 0  # Réinitialiser le score
        projectiles = []  # Vider les projectiles
        particles = []  # Vider les particules
        level_transition_active = False  # Réinitialiser le système de transition
        level_transition_next_idx = None
        level_transition_phase = "fade_out"
        level_transition_timer = 0.0

    # === AFFICHAGE DU TUTORIEL ===
    draw_tutorial_overlay()  # Dessiner le panneau de tutoriel si visible
    
    # === MISE À JOUR DE L'AFFICHAGE ===
    pygame.display.flip()  # Afficher le buffer à l'écran
    dt = clock.tick(FPS) / 1000  # Limiter le FPS et obtenir le delta time

# === FIN DE LA BOUCLE PRINCIPALE ===
pygame.quit()  # Quitter pygame proprement
