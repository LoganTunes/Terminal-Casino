import pygame
import sys
import math

# --- PRECISION VECTOR GENERATORS ---

def draw_diamond(surface, color, x, y, size):
    """Draws a tall, narrow diamond matching the exact traditional proportions."""
    # Traditional diamonds are taller than they are wide (approx 1 : 1.35 ratio)
    half_w = int(size * 0.38)
    half_h = int(size * 0.52)
    points = [
        (x, y - half_h),  # Top
        (x + half_w, y),  # Right
        (x, y + half_h),  # Bottom
        (x - half_w, y)   # Left
    ]
    pygame.draw.polygon(surface, color, points)

def draw_heart(surface, color, x, y, size):
    """Draws a smooth heart with deep curves using a parametric equation path."""
    points = []
    # Steps through a parametric card-heart curve for flawless smoothness
    steps = 100
    scale = size * 0.44
    for i in range(steps + 1):
        t = math.pi * 2 * i / steps
        # Classic algebraic heart curve formula modified for exact shape matching
        dx = 16 * (math.sin(t) ** 3)
        dy = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        
        # Center adjustments to align perfectly with the bounding box
        px = x + int(dx * scale / 16)
        py = y + int((dy - 1.5) * scale / 16)
        points.append((px, py))
        
    pygame.draw.polygon(surface, color, points)

def draw_spade(surface, color, x, y, size):
    """Draws an authentic spade with an inverted heart blade and a flared stem."""
    points = []
    steps = 80
    scale = size * 0.41
    
    # 1. Generate the main spade blade (inverted mathematical heart)
    for i in range(steps + 1):
        t = math.pi * 2 * i / steps
        dx = 16 * (math.sin(t) ** 3)
        dy = (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        px = x + int(dx * scale / 16)
        py = y + int((dy - 2.5) * scale / 16)
        points.append((px, py))
        
    pygame.draw.polygon(surface, color, points)
    
    # 2. Draw the flared elegant stem (curves out fluidly to a flat base)
    stem_points = []
    stem_height = int(size * 0.35)
    stem_top_y = y + int(size * 0.05)
    stem_bottom_y = stem_top_y + stem_height
    
    # Curve down left side of the stem
    for i in range(11):
        pct = i / 10.0
        curr_y = stem_top_y + (stem_height * pct)
        # Quadratic flair curve
        curr_x = x - int((size * 0.03) + (size * 0.15) * (pct ** 2.5))
        stem_points.append((curr_x, curr_y))
        
    # Curve up right side of the stem
    for i in range(11):
        pct = (10 - i) / 10.0
        curr_y = stem_top_y + (stem_height * pct)
        curr_x = x + int((size * 0.03) + (size * 0.15) * (pct ** 2.5))
        stem_points.append((curr_x, curr_y))
        
    pygame.draw.polygon(surface, color, stem_points)

def draw_club(surface, color, x, y, size):
    """Draws a traditional club using geometric spacing and a flared stem."""
    # Proportions mathematically balanced to match the target asset
    r = int(size * 0.23)
    dist = int(size * 0.21)
    
    # Top lobe
    pygame.draw.circle(surface, color, (x, y - dist), r)
    # Left lobe
    pygame.draw.circle(surface, color, (x - dist, y + int(size * 0.06)), r)
    # Right lobe
    pygame.draw.circle(surface, color, (x + dist, y + int(size * 0.06)), r)
    
    # Solid geometric center block to seamlessly fuse the lobes together
    center_poly = [
        (x, y - dist),
        (x + dist, y + int(size * 0.06)),
        (x, y + int(size * 0.15)),
        (x - dist, y + int(size * 0.06))
    ]
    pygame.draw.polygon(surface, color, center_poly)
    
    # Flared stem matching the spade profile
    stem_points = []
    stem_height = int(size * 0.32)
    stem_top_y = y + int(size * 0.08)
    stem_bottom_y = stem_top_y + stem_height
    
    for i in range(11):
        pct = i / 10.0
        curr_y = stem_top_y + (stem_height * pct)
        curr_x = x - int((size * 0.02) + (size * 0.14) * (pct ** 2.5))
        stem_points.append((curr_x, curr_y))
        
    for i in range(11):
        pct = (10 - i) / 10.0
        curr_y = stem_top_y + (stem_height * pct)
        curr_x = x + int((size * 0.02) + (size * 0.14) * (pct ** 2.5))
        stem_points.append((curr_x, curr_y))
        
    pygame.draw.polygon(surface, color, stem_points)


# --- APPLICATION RUNNER ---

def main():
    pygame.init()
    
    screen_width = 900
    screen_height = 400
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Exact Card Suit Vector Matcher")
    
    # Colors matched to traditional casino layouts
    bg_color = (245, 246, 248)    # Clean off-white canvas
    red_suit = (255, 0, 0)        # Pure vibrant casino red
    black_suit = (20, 20, 20)     # Clean solid ink black
    
    suit_size = 150               # Increased size to view curve fidelity clearly
    y_center = screen_height // 2
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        screen.fill(bg_color)
        
        # Render sequence matching your target image layout: Spade -> Heart -> Club -> Diamond
        draw_spade(screen, black_suit, 180, y_center + 10, suit_size)
        draw_heart(screen, red_suit, 360, y_center, suit_size)
        draw_club(screen, black_suit, 540, y_center, suit_size)
        draw_diamond(screen, red_suit, 720, y_center, suit_size)
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
