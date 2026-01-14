import pygame
import sys
import os

pygame.init()

SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 769
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Menu GUI")

# Constants
MENU_WIDTH = 800
MENU_HEIGHT = 600
FPS = 120

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BLUE = (100, 149, 237)
LIGHT_BLUE = (173, 216, 230)

# Fonts
font_title = pygame.font.Font(None, 36)
font_label = pygame.font.Font(None, 24)
font_button = pygame.font.Font(None, 20)

# Menu state
menu_open = False
running = True

# Menu position (centered)
menu_x = (SCREEN_WIDTH - MENU_WIDTH) // 2
menu_y = (SCREEN_HEIGHT - MENU_HEIGHT) // 2

# Input field
input_active = False
input_text = ""
input_rect = pygame.Rect(menu_x + 250, menu_y + 200, 300, 40)

# Power buttons
power_buttons = []
power_images = {}

def setup_power_buttons():
    """Setup the 5 power buttons in a row"""
    global power_buttons
    button_radius = 50
    button_spacing = 120
    start_x = menu_x + (MENU_WIDTH - (5 * button_spacing)) // 2 + button_radius // 2
    button_y = menu_y + 350
    
    for i in range(5):
        x = start_x + i * button_spacing
        button_rect = pygame.Rect(x - button_radius, button_y - button_radius, 
                                 button_radius * 2, button_radius * 2)
        power_buttons.append({
            'rect': button_rect,
            'label': f'POUWOR {i + 1}',
            'image_key': f'pouvoir{i + 1}'
        })

def load_power_images():
    """Load power images if they exist"""
    global power_images
    for i in range(1, 6):
        image_path = f'GUI/IMG/pouvoir{i}.png'
        if os.path.exists(image_path):
            try:
                image = pygame.image.load(image_path)
                image = pygame.transform.scale(image, (80, 80))
                power_images[f'pouvoir{i}'] = image
            except pygame.error:
                print(f"Could not load image: {image_path}")

def draw_menu():
    """Draw the menu GUI"""
    if not menu_open:
        return
    
    # Draw menu background
    menu_surface = pygame.Surface((MENU_WIDTH, MENU_HEIGHT))
    menu_surface.fill(WHITE)
    menu_surface.set_alpha(240)
    screen.blit(menu_surface, (menu_x, menu_y))
    
    # Draw menu border
    pygame.draw.rect(screen, BLACK, 
                    (menu_x, menu_y, MENU_WIDTH, MENU_HEIGHT), 3)
    
    # Draw title
    title_text = font_title.render("INFORMATIONS SUR LE JOUEUR", True, BLACK)
    title_rect = title_text.get_rect(center=(menu_x + MENU_WIDTH // 2, menu_y + 60))
    screen.blit(title_text, title_rect)
    
    # Draw avatar placeholder
    avatar_rect = pygame.Rect(menu_x + 100, menu_y + 120, 120, 120)
    pygame.draw.rect(screen, GRAY, avatar_rect)
    pygame.draw.rect(screen, BLACK, avatar_rect, 2)
    avatar_text = font_label.render("Avatar", True, DARK_GRAY)
    avatar_text_rect = avatar_text.get_rect(center=avatar_rect.center)
    screen.blit(avatar_text, avatar_text_rect)
    
    # Draw pseudo label
    pseudo_label = font_label.render("Pseudo:", True, BLACK)
    screen.blit(pseudo_label, (menu_x + 100, menu_y + 90))
    
    # Draw input field
    color = BLUE if input_active else BLACK
    pygame.draw.rect(screen, color, input_rect, 2)
    text_surface = font_label.render(input_text, True, BLACK)
    screen.blit(text_surface, (input_rect.x + 5, input_rect.y + 8))
    
    # Draw power buttons
    for button in power_buttons:
        draw_power_button(button)

def draw_power_button(button):
    """Draw a single power button"""
    center = button['rect'].center
    
    # Check if image exists
    if button['image_key'] in power_images:
        # Draw circular background
        pygame.draw.circle(screen, LIGHT_BLUE, center, 45)
        pygame.draw.circle(screen, BLACK, center, 45, 2)
        
        # Draw image
        image = power_images[button['image_key']]
        image_rect = image.get_rect(center=center)
        screen.blit(image, image_rect)
    else:
        # Draw circular button with text
        pygame.draw.circle(screen, LIGHT_BLUE, center, 45)
        pygame.draw.circle(screen, BLACK, center, 45, 2)
        
        # Draw text
        text = font_button.render(button['label'], True, BLACK)
        text_rect = text.get_rect(center=center)
        screen.blit(text, text_rect)

def handle_events():
    """Handle pygame events"""
    global menu_open, running, input_active, input_text
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                menu_open = not menu_open
            
            elif input_active and menu_open:
                if event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_RETURN:
                    input_active = False
                else:
                    input_text += event.unicode
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if menu_open:
                # Check if input field was clicked
                if input_rect.collidepoint(event.pos):
                    input_active = True
                else:
                    input_active = False
                
                # Check if power buttons were clicked
                for button in power_buttons:
                    if button['rect'].collidepoint(event.pos):
                        print(f"Clicked: {button['label']}")

# Initialize
setup_power_buttons()
load_power_images()

# Main game loop
clock = pygame.time.Clock()
while running:
    handle_events()
    
    # Clear screen
    screen.fill(GRAY)
    
    # Draw menu
    draw_menu()
    
    # Draw instructions
    if not menu_open:
        instruction_text = font_label.render("Press TAB to open menu", True, BLACK)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(instruction_text, instruction_rect)
    
    # Update display
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
