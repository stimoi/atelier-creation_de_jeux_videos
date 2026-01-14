# Physique et collisions
import pygame

def circle_rect_collision(center, radius, rect):
    """Vérifie la collision entre un cercle et un rectangle"""
    cx, cy = center
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    dx = cx - closest_x
    dy = cy - closest_y
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
    """Résout la collision avec un bloc"""
    new_pos = player_pos.copy()
    new_vel_y = player_vel_y
    
    # Si le joueur tombe sur un bloc par le dessus
    if player_vel_y > 0 and player_rect.bottom > block_rect.top and player_rect.centery < block_rect.top:
        new_pos.y = block_rect.top - (head_radius + body_height + leg_height)
        new_vel_y = 0
    # Si le joueur saute et touche un bloc par le dessous
    elif player_vel_y < 0 and player_rect.top < block_rect.bottom and player_rect.centery > block_rect.bottom:
        new_pos.y = block_rect.bottom + head_radius + 1
        new_vel_y = 0
    # Si le joueur se déplace horizontalement et touche un bloc
    else:
        if player_rect.right > block_rect.left and player_rect.left < block_rect.left:
            new_pos.x = block_rect.left - head_radius - 1
        elif player_rect.left < block_rect.right and player_rect.right > block_rect.right:
            new_pos.x = block_rect.right + head_radius + 1
    
    return new_pos, new_vel_y
