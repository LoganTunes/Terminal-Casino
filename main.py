"""
THE TERMINAL CASINO - MAIN LOBBY & ENGINE LAUNCHER
==================================================
Global Resolution Target: 950x720 (Native to all games)
"""

import asyncio
import sys
import pygame

# Import game modules from games package
from games import (
    blackjack,
    craps,
    keno,
    mechanical_derby,
    roulette,
    slots,
    ultimate_hold_em,
    video_poker,
)

# Initialize Pygame Display
pygame.init()
if not pygame.mixer.get_init():
    pygame.mixer.init(frequency=22050, size=-16, channels=1)

# FIXED NATIVE RESOLUTION FOR ALL GAMES AND LOBBY
WIDTH, HEIGHT = 950, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Terminal Casino - Main Lobby")
clock = pygame.time.Clock()

# Color Palette
MAHOGANY = (56, 18, 11)
WOOD_LIGHT = (84, 30, 20)
FELT_GREEN = (10, 68, 33)
VINTAGE_GOLD = (212, 163, 89)
CREAM_WHITE = (247, 245, 230)
CHARCOAL = (24, 24, 24)
BRIGHT_RED = (190, 25, 25)

# Fonts
title_font = pygame.font.SysFont("georgia", 36, bold=True)
subtitle_font = pygame.font.SysFont("georgia", 18, italic=True)
card_font = pygame.font.SysFont("arial", 16, bold=True)
hud_font = pygame.font.SysFont("arial", 20, bold=True)


class MenuButton:
    def __init__(self, rect, title, game_key, callback):
        self.rect = pygame.Rect(rect)
        self.title = title
        self.game_key = game_key
        self.callback = callback
        self.hovered = False

    def draw(self, surface):
        bg_col = BRIGHT_RED if self.hovered else CHARCOAL
        border_col = VINTAGE_GOLD if self.hovered else CREAM_WHITE

        # Outer Card Body
        pygame.draw.rect(surface, bg_col, self.rect, 0, 8)
        pygame.draw.rect(surface, border_col, self.rect, 2, 8)

        # Title Label
        txt = card_font.render(self.title, True, CREAM_WHITE)
        surface.blit(
            txt,
            (
                self.rect.centerx - txt.get_width() // 2,
                self.rect.centery - txt.get_height() // 2,
            ),
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self.game_key
        return None


async def main():
    global screen
    player_balance = 1000

    # Game Launcher Registry
    game_launchers = {
        "blackjack": blackjack.run_blackjack,
        "craps": craps.run_craps,
        "keno": keno.run_keno,
        "mechanical_derby": mechanical_derby.run_derby,
        "roulette": roulette.run_roulette,
        "slots": slots.run_slots,
        "ultimate_hold_em": ultimate_hold_em.run_ultimate_hold_em,
        "video_poker": video_poker.run_video_poker,
    }

    # 2x4 Layout Grid Scaled to Fit 950x720 Cleanly
    # Card size: 180x100 | Spacing: 25px horizontal, 25px vertical
    start_x, start_y = 75, 220
    card_w, card_h = 180, 100
    gap_x, gap_y = 25, 25

    buttons = [
        # Row 1
        MenuButton((start_x + 0 * (card_w + gap_x), start_y + 0 * (card_h + gap_y), card_w, card_h), "BLACKJACK", "blackjack", None),
        MenuButton((start_x + 1 * (card_w + gap_x), start_y + 0 * (card_h + gap_y), card_w, card_h), "CRAPS", "craps", None),
        MenuButton((start_x + 2 * (card_w + gap_x), start_y + 0 * (card_h + gap_y), card_w, card_h), "KENO", "keno", None),
        MenuButton((start_x + 3 * (card_w + gap_x), start_y + 0 * (card_h + gap_y), card_w, card_h), "HORSE DERBY", "mechanical_derby", None),
        # Row 2
        MenuButton((start_x + 0 * (card_w + gap_x), start_y + 1 * (card_h + gap_y), card_w, card_h), "ROULETTE", "roulette", None),
        MenuButton((start_x + 1 * (card_w + gap_x), start_y + 1 * (card_h + gap_y), card_w, card_h), "SLOTS", "slots", None),
        MenuButton((start_x + 2 * (card_w + gap_x), start_y + 1 * (card_h + gap_y), card_w, card_h), "HOLD 'EM", "ultimate_hold_em", None),
        MenuButton((start_x + 3 * (card_w + gap_x), start_y + 1 * (card_h + gap_y), card_w, card_h), "VIDEO POKER", "video_poker", None),
    ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            for btn in buttons:
                launched_game = btn.handle_event(event)
                if launched_game and launched_game in game_launchers:
                    # Launch target game and retrieve balance upon returning
                    player_balance = await game_launchers[launched_game](player_balance)
                    
                    # Force screen re-bind back to 950x720 upon returning to main menu
                    screen = pygame.display.set_mode((WIDTH, HEIGHT))
                    pygame.display.set_caption("The Terminal Casino - Main Lobby")

        # Render Main Lobby Scene
        screen.fill(MAHOGANY)
        pygame.draw.rect(screen, WOOD_LIGHT, (10, 10, WIDTH - 20, HEIGHT - 20), 10)
        pygame.draw.rect(screen, FELT_GREEN, (20, 20, WIDTH - 40, HEIGHT - 40))

        # Title & Banner
        title_surf = title_font.render("THE TERMINAL CASINO", True, VINTAGE_GOLD)
        subtitle_surf = subtitle_font.render("Select a table to begin playing", True, CREAM_WHITE)
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 45))
        screen.blit(subtitle_surf, (WIDTH // 2 - subtitle_surf.get_width() // 2, 95))

        # HUD Panel (Bankroll)
        hud_rect = pygame.Rect(WIDTH // 2 - 150, 140, 300, 45)
        pygame.draw.rect(screen, CHARCOAL, hud_rect, 0, 6)
        pygame.draw.rect(screen, VINTAGE_GOLD, hud_rect, 2, 6)
        bal_txt = hud_font.render(f"BANKROLL: ${player_balance}", True, CREAM_WHITE)
        screen.blit(bal_txt, (hud_rect.centerx - bal_txt.get_width() // 2, hud_rect.centery - bal_txt.get_height() // 2))

        # Menu Buttons
        for btn in buttons:
            btn.draw(screen)

        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(60)


if __name__ == "__main__":
    asyncio.run(main())
