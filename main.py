import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((400, 200))
pygame.display.set_caption("Icon Verification Test")

CARD_BG = (46, 20, 12)
CREAM_WHITE = (247, 245, 230)
VINTAGE_GOLD = (212, 163, 89)

lottery_accent = (70, 160, 120)
plinko_accent = (210, 80, 180)

def draw_lottery_icon(surface, cx, cy):
    # Base Ticket Slip
    t_rect = pygame.Rect(cx - 30, cy - 20, 60, 40)
    pygame.draw.rect(surface, CREAM_WHITE, t_rect, 0, 4)
    pygame.draw.rect(surface, lottery_accent, t_rect, 2, 4)

    # Header Strip
    pygame.draw.rect(surface, lottery_accent, (cx - 26, cy - 16, 52, 10), 0, 2)

    # Scratch Grid
    for gx in (-16, -4, 8):
        for gy in (0, 12):
            pygame.draw.rect(surface, VINTAGE_GOLD, (cx + gx, cy + gy, 8, 8), 1)

    # Side Notches
    pygame.draw.circle(surface, CARD_BG, (cx - 30, cy), 5)
    pygame.draw.circle(surface, CARD_BG, (cx + 30, cy), 5)
    pygame.draw.circle(surface, lottery_accent, (cx - 30, cy), 5, 1)
    pygame.draw.circle(surface, lottery_accent, (cx + 30, cy), 5, 1)

def draw_plinko_icon(surface, cx, cy):
    # Inverted Peg Pyramid (wide on top, narrow on bottom)
    for px, py in [(-18, -12), (0, -12), (18, -12), (-9, 2), (9, 2), (0, 16)]:
        pygame.draw.circle(surface, plinko_accent, (cx + px, cy + py), 3)
    # Chip drop
    pygame.draw.circle(surface, CREAM_WHITE, (cx, cy - 22), 5)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

    screen.fill(CARD_BG)
    
    # Draw test icons
    draw_lottery_icon(screen, 100, 100)
    draw_plinko_icon(screen, 300, 100)

    pygame.display.flip()
