import pygame
import json
import sys
import tkinter as tk
from tkinter import filedialog

# On initialise tkinter et on cache sa fenêtre principale
root = tk.Tk()
root.withdraw()

HAUTEUR_MENU_HAUT = 50 # Espace réservé en haut pour la barre

# --- CONFIGURATION DE BASE ---
pygame.init()

# On crée l'objet "police" à partir du système de polices de Pygame
police = pygame.font.SysFont("Arial", 18, bold=True)

LARGEUR_FENETRE = 800
HAUTEUR_FENETRE = 600
TAILLE_BLOC = 40

# Création de la fenêtre
ecran = pygame.display.set_mode((LARGEUR_FENETRE, HAUTEUR_FENETRE))
pygame.display.set_caption("Mon Super Mario Maker - Python Édition")

# --- DEFINITION DES BLOCS (Notre Palette) ---
# Chaque bloc a un nom et une couleur (Rouge, Vert, Bleu)
BLOCS = {
    "herbe": {"couleur": (74, 222, 128)},   # Vert clair
    "terre": {"couleur": (139, 90, 43)},    # Marron
    "pierre": {"couleur": (148, 163, 184)}, # Gris
    "brique": {"couleur": (220, 38, 38)},   # Rouge
    "eau": {"couleur": (59, 130, 246)},      # Bleu
    "spawn": {"couleur": (255,255,255)}          # Blanc
}

# Variables de l'éditeur
bloc_actuel = "herbe" # Le bloc sélectionné par défaut
niveau_data = {}      # Dictionnaire qui va stocker nos blocs { "x,y": "type_de_bloc" }

# Variable pour savoir si on travaille déjà sur un fichier
chemin_fichier_actuel = None

# Définition des 3 boutons du haut (X, Y, Largeur, Hauteur)
rect_bouton_save    = pygame.Rect(10, 10, 110, 30)
rect_bouton_save_as = pygame.Rect(130, 10, 170, 30)
rect_bouton_open    = pygame.Rect(310, 10, 110, 30)


# --- FONCTIONS ---

def sauvegarder():
    # Ouvre la fenêtre système "Enregistrer sous"
    chemin_fichier = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("Fichiers JSON", "*.json")]
    )

    if chemin_fichier: # Si l'utilisateur n'a pas fait "Annuler"
        blocs_sauvegardes = []
        for coord, type_b in niveau_data.items():
            x_str, y_str = coord.split(',')
            blocs_sauvegardes.append({
                "x": int(x_str) * TAILLE_BLOC,
                "y": int(y_str) * TAILLE_BLOC,
                "type": type_b
            })

        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump({"blocs": blocs_sauvegardes}, f, indent=4)

def sauvegarder(sous=False):
    global chemin_fichier_actuel

    # Si on fait "Sauvegarder" mais qu'on n'a pas encore de fichier,
    # ou si on force "Enregistrer sous"
    if chemin_fichier_actuel is None or sous:
        chemin = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json")]
        )
        if not chemin: return # L'utilisateur a annulé
        chemin_fichier_actuel = chemin

    # Préparation des données
    blocs_sauvegardes = []
    for coord, type_b in niveau_data.items():
        x_str, y_str = coord.split(',')
        blocs_sauvegardes.append({"x": int(x_str) * TAILLE_BLOC, "y": int(y_str) * TAILLE_BLOC, "type": type_b})

    # Écriture physique sur le disque
    with open(chemin_fichier_actuel, "w", encoding="utf-8") as f:
        json.dump({"blocs": blocs_sauvegardes}, f, indent=4)
    print(f"✅ Enregistré dans : {chemin_fichier_actuel}")

def charger_niveau():
    global chemin_fichier_actuel, niveau_data

    chemin = filedialog.askopenfilename(filetypes=[("Fichiers JSON", "*.json")])
    if chemin:
        with open(chemin, "r", encoding="utf-8") as f:
            donnees = json.load(f)
            # On vide le niveau actuel avant de charger le nouveau
            niveau_data = {}
            for b in donnees["blocs"]:
                gx, gy = b["x"] // TAILLE_BLOC, b["y"] // TAILLE_BLOC
                niveau_data[f"{gx},{gy}"] = b["type"]

        chemin_fichier_actuel = chemin
        print(f"📂 Niveau chargé : {chemin}")

def dessiner_interface():
    """Dessine le fond, la grille, les blocs placés et la barre d'outils."""
    # 1. Fond bleu ciel
    ecran.fill((135, 206, 235))

    # 2. Dessiner la grille (lignes légères)
    for x in range(0, LARGEUR_FENETRE, TAILLE_BLOC):
        pygame.draw.line(ecran, (200, 200, 200), (x, 0), (x, HAUTEUR_FENETRE))
    for y in range(0, HAUTEUR_FENETRE, TAILLE_BLOC):
        pygame.draw.line(ecran, (200, 200, 200), (0, y), (LARGEUR_FENETRE, y))

    # 3. Dessiner les blocs déjà placés
    for coordonnees, type_bloc in niveau_data.items():
        x_str, y_str = coordonnees.split(',')
        x_pixel = int(x_str) * TAILLE_BLOC
        y_pixel = int(y_str) * TAILLE_BLOC
        couleur = BLOCS[type_bloc]["couleur"]

        # On dessine le rectangle du bloc
        rect_bloc = pygame.Rect(x_pixel, y_pixel, TAILLE_BLOC, TAILLE_BLOC)
        pygame.draw.rect(ecran, couleur, rect_bloc)
        pygame.draw.rect(ecran, (0, 0, 0), rect_bloc, 1) # Bordure noire

    # 4. Dessiner la barre d'outils en bas
    barre_rect = pygame.Rect(0, HAUTEUR_FENETRE - 60, LARGEUR_FENETRE, 60)
    pygame.draw.rect(ecran, (30, 41, 59), barre_rect) # Fond gris foncé

    # Dessin de la barre de menu noire en haut
    pygame.draw.rect(ecran, (30, 41, 59), (0, 0, 800, HAUTEUR_MENU_HAUT))

    # Dessiner les choix de blocs dans la barre d'outils
    espacement = 10
    position_x = 10
    for nom_bloc, infos in BLOCS.items():
        rect_choix = pygame.Rect(position_x, HAUTEUR_FENETRE - 50, TAILLE_BLOC, TAILLE_BLOC)
        pygame.draw.rect(ecran, infos["couleur"], rect_choix)

        # Si c'est le bloc sélectionné, on lui met une bordure jaune épaisse
        if nom_bloc == bloc_actuel:
            pygame.draw.rect(ecran, (255, 255, 0), rect_choix, 3)

        position_x += TAILLE_BLOC + espacement

    # Bouton SAUVEGARDER
    pygame.draw.rect(ecran, (34, 197, 94), rect_bouton_save, border_radius=5)
    ecran.blit(police.render("SAUVER", True, (255, 255, 255)), (rect_bouton_save.x + 15, rect_bouton_save.y + 5))

    # Bouton SAUVEGARDER SOUS
    pygame.draw.rect(ecran, (56, 189, 248), rect_bouton_save_as, border_radius=5)
    ecran.blit(police.render("ENREGISTRER SOUS", True, (255, 255, 255)), (rect_bouton_save_as.x + 10, rect_bouton_save_as.y + 5))

    # Bouton OUVRIR
    pygame.draw.rect(ecran, (249, 115, 22), rect_bouton_open, border_radius=5)
    ecran.blit(police.render("OUVRIR", True, (255, 255, 255)), (rect_bouton_open.x + 20, rect_bouton_open.y + 5))


# --- BOUCLE PRINCIPALE (Le Game Loop) ---
# C'est ici que le programme tourne en boucle 60 fois par seconde
en_cours = True
while en_cours:

    # 1. GESTION DES ÉVÉNEMENTS (Clavier, Souris, Fermeture)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            en_cours = False

        # Si on appuie sur une touche du clavier
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s: # Touche 'S' pour Sauvegarder
                sauvegarder()

        # Si on clique avec la souris
        elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEMOTION:
            # On vérifie si un des boutons de la souris est enfoncé
            boutons_souris = pygame.mouse.get_pressed()
            clic_gauche = boutons_souris[0]
            clic_droit = boutons_souris[2]

            if clic_gauche or clic_droit:
                souris_x, souris_y = pygame.mouse.get_pos()
                souris_pos = event.pos

                # Clic dans la barre d'outils ?
                if souris_y > HAUTEUR_FENETRE - 60 and clic_gauche:
                    position_x = 10
                    for nom_bloc in BLOCS.keys():
                        if position_x <= souris_x <= position_x + TAILLE_BLOC:
                            bloc_actuel = nom_bloc
                        position_x += TAILLE_BLOC + 10

                # Clic dans la zone de dessin (la grille)
                elif souris_y <= HAUTEUR_FENETRE - 60:
                    # On calcule la case de la grille correspondante
                    grille_x = souris_x // TAILLE_BLOC
                    grille_y = souris_y // TAILLE_BLOC
                    cle_coordonnees = f"{grille_x},{grille_y}"

                    if clic_gauche:
                        # On place ou remplace le bloc
                        niveau_data[cle_coordonnees] = bloc_actuel
                    elif clic_droit:
                        # On gomme le bloc s'il existe (clic droit)
                        if cle_coordonnees in niveau_data:
                            del niveau_data[cle_coordonnees]

                if rect_bouton_save.collidepoint(souris_pos):
                    sauvegarder(sous=False)

                elif rect_bouton_save_as.collidepoint(souris_pos):
                    sauvegarder(sous=True)

                elif rect_bouton_open.collidepoint(souris_pos):
                    charger_niveau()

    # 2. MISE À JOUR DE L'AFFICHAGE
    dessiner_interface()

    # On actualise l'écran
    pygame.display.flip()

# Quand on sort de la boucle (croix rouge), on ferme proprement
pygame.quit()
sys.exit()