# Physique et collisions
import pygame

def circle_rect_collision(center, radius, rect):
    """Vérifie la collision entre un cercle et un rectangle
    
    Algorithme: Trouve le point le plus proche du centre du cercle sur le rectangle,
    puis vérifie si la distance entre ce point et le centre est inférieure au rayon.
    
    Args:
        center: tuple (x, y) - centre du cercle
        radius: int - rayon du cercle
        rect: pygame.Rect - rectangle
    
    Returns:
        bool: True si collision, False sinon
    """
    cx, cy = center
    # Clamp les coordonnées du centre aux bornes du rectangle
    # Cela trouve le point du rectangle le plus proche du centre du cercle
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    
    # Calcule la distance au carré entre le centre et le point le plus proche
    dx = cx - closest_x
    dy = cy - closest_y
    
    # Compare avec le rayon au carré (évite sqrt pour la performance)
    return dx * dx + dy * dy <= radius * radius

def check_block_collision(rect, platforms, platform_types):
    """Vérifie les collisions avec les plateformes de type 'block' (rectangles pleins)"""
    try:
        for i, plat in enumerate(platforms):
            if i < len(platform_types) and platform_types[i] == 'block':
                block_rect = plat
                if rect.colliderect(block_rect):
                    return block_rect
    except Exception:
        pass
    return None

def resolve_block_collision(player_rect, player_pos, player_vel_y, block_rect, head_radius, body_height, leg_height):
    """Résout la collision avec un bloc en déterminant la direction de l'impact
    
    Stratégie de résolution:
    1. Priorité aux collisions verticales (atterrissage/plafond)
    2. Ensuite gère les collisions horizontales (murs)
    3. Ajuste position et vélocité selon le type de collision
    
    Args:
        player_rect: pygame.Rect - rectangle de collision du joueur
        player_pos: pygame.Vector2 - position actuelle du joueur
        player_vel_y: float - vélocité verticale du joueur
        block_rect: pygame.Rect - rectangle du bloc
        head_radius, body_height, leg_height: dimensions du joueur
    
    Returns:
        tuple: (nouvelle_position, nouvelle_velocite_y)
    """
    new_pos = player_pos.copy()
    new_vel_y = player_vel_y
    
    # Collision verticale prioritaire: joueur tombe sur le bloc
    # Vérifie si le joueur descend (vel_y > 0) et que son bas dépasse le haut du bloc
    # mais que son centre est encore au-dessus (évite les collisions latérales)
    if player_vel_y > 0 and player_rect.bottom > block_rect.top and player_rect.centery < block_rect.top:
        # Positionne le joueur exactement sur le bloc
        new_pos.y = block_rect.top - (head_radius + body_height + leg_height)
        new_vel_y = 0  # Arrête la chute
    
    # Collision avec le plafond: joueur saute et touche le dessous d'un bloc
    elif player_vel_y < 0 and player_rect.top < block_rect.bottom and player_rect.centery > block_rect.bottom:
        # Positionne le joueur juste sous le bloc avec une marge de 1px
        new_pos.y = block_rect.bottom + head_radius + 1
        new_vel_y = 0  # Arrête la montée
        # TODO: ajouter une fonction qui permet de remettre le jump a 0
    
    # Collisions horizontales (murs gauche/droite)
    else:
        # Collision avec le mur gauche: joueur arrive de la gauche
        if player_rect.right > block_rect.left and player_rect.left < block_rect.left:
            # Positionne le joueur juste à gauche du bloc avec une marge de 1px
            new_pos.x = block_rect.left - head_radius - 1
        # Collision avec le mur droit: joueur arrive de la droite
        elif player_rect.left < block_rect.right and player_rect.right > block_rect.right:
            # Positionne le joueur juste à droite du bloc avec une marge de 1px
            new_pos.x = block_rect.right + head_radius + 1
    
    return new_pos, new_vel_y
