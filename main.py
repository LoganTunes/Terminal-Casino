"""
THE TERMINAL CASINO - Main Lobby / Launcher
=============================================
Ties together all eight table games into a single game with one
shared chip balance. Run this file to play.

    python main.py

Each game lives in games/<name>.py and exposes a run_<name>(balance)
function.
"""

import asyncio
import json
import os
import sys
import traceback

import pygame

pygame.init()

# ----------------------------------------------------------------
# Window / lobby setup
# ----------------------------------------------------------------

LOBBY_WIDTH, LOBBY_HEIGHT = 1080, 720
screen = pygame.display.set_mode((LOBBY_WIDTH, LOBBY_HEIGHT))
pygame.display.set_caption("The Terminal Casino")
clock = pygame.time.Clock()

# ----------------------------------------------------------------
# Palette (matches the felt / mahogany / gold look of the games)
# ----------------------------------------------------------------

FELT_GREEN = (12, 82, 42)
MAHOGANY = (32, 14, 8)
WOOD_LIGHT = (75, 26, 14)
LEATHER_RAIL = (24, 8, 4)
VINTAGE_GOLD = (212, 163, 89)
GOLD_TEXT = (230, 195, 130)
GOLD_SHADOW = (145, 105, 45)
CREAM_WHITE = (247, 245, 230)
CHARCOAL = (20, 20, 20)
BRIGHT_RED = (190, 25, 25)
CARD_BG = (46, 20, 12)
CARD_BG_HOVER = (66, 30, 16)

FONT_OPTIONS = ["georgia", "arial"]
title_font = pygame.font.SysFont(FONT_OPTIONS, 46, bold=True)
subtitle_font = pygame.font.SysFont(FONT_OPTIONS, 16)
bank_font = pygame.font.SysFont(FONT_OPTIONS, 24, bold=True)
card_title_font = pygame.font.SysFont(FONT_OPTIONS, 22, bold=True)
card_sub_font = pygame.font.SysFont(FONT_OPTIONS, 13)
hint_font = pygame.font.SysFont(FONT_OPTIONS, 15)
button_font = pygame.font.SysFont(FONT_OPTIONS, 15, bold=True)

# ----------------------------------------------------------------
# Safe Persistent bankroll (Web Assembly & Desktop compatible)
# ----------------------------------------------------------------

SAVE_FILE = "chips_save.json"
STARTING_BALANCE = 1000


def load_balance():
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                return int(data.get("balance", STARTING_BALANCE))
    except Exception as e:
        print("Could not load save file:", e)
    return STARTING_BALANCE


def save_balance(balance):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump({"balance": balance}, f)
    except Exception as e:
        print("Could not save balance:", e)


# ----------------------------------------------------------------
# Loading screen
# ----------------------------------------------------------------

def draw_loading_screen(message):
    screen.fill(MAHOGANY)
    msg_surf = bank_font.render(message, True, GOLD_TEXT)
    screen.blit(
        msg_surf,
        (LOBBY_WIDTH // 2 - msg_surf.get_width() // 2, LOBBY_HEIGHT // 2 - 10),
    )
    pygame.display.flip()


draw_loading_screen("Loading the casino floor...")

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

screen = pygame.display.set_mode((LOBBY_WIDTH, LOBBY_HEIGHT))
pygame.display.set_caption("The Terminal Casino")

# ----------------------------------------------------------------
# Game catalog
# ----------------------------------------------------------------

GAMES = [
    {
        "title": "Blackjack",
        "subtitle": "5-Spot Vegas Table",
        "run": blackjack.run_blackjack,
        "accent": BRIGHT_RED,
    },
    {
        "title": "Craps",
        "subtitle": "Double-Sided Felt Table",
        "run": craps.run_craps,
        "accent": (60, 130, 90),
    },
    {
        "title": "Keno",
        "subtitle": "Lounge Keno Cabinet",
        "run": keno.run_keno,
        "accent": (90, 140, 200),
    },
    {
        "title": "Mechanical Derby",
        "subtitle": "Racehorse Wagering",
        "run": mechanical_derby.run_mechanical_derby,
        "accent": (170, 120, 60),
    },
    {
        "title": "Roulette",
        "subtitle": "Perfect-Layout Wheel",
        "run": roulette.run_roulette,
        "accent": (150, 40, 40),
    },
    {
        "title": "Slots",
        "subtitle": "Mechanical Reel Machine",
        "run": slots.run_slots,
        "accent": (200, 170, 60),
    },
    {
        "title": "Ultimate Hold 'Em",
        "subtitle": "Vegas Poker Table",
        "run": ultimate_hold_em.run_ultimate_hold_em,
        "accent": (100, 60, 140),
    },
    {
        "title": "Video Poker",
        "subtitle": "CRT Cabinet",
        "run": video_poker.run_video_poker,
        "accent": (60, 170, 170),
    },
]

# ----------------------------------------------------------------
# Lobby layout: 4 columns x 2 rows of game cards
# ----------------------------------------------------------------

COLS, ROWS = 4, 2
CARD_W, CARD_H = 230, 190
GRID_MARGIN_X, GRID_TOP = 45, 195
GAP_X, GAP_Y = 20, 22

card_rects = []
for i, game in enumerate(GAMES):
    col = i % COLS
    row = i // COLS
    x = GRID_MARGIN_X + col * (CARD_W + GAP_X)
    y = GRID_TOP + row * (CARD_H + GAP_Y)
    card_rects.append(pygame.Rect(x, y, CARD_W, CARD_H))

reset_btn_rect = pygame.Rect(LOBBY_WIDTH - 205, 18, 165, 40)


def draw_wood_panel(surface, rect):
    pygame.draw.rect(surface, WOOD_LIGHT, rect, 0, 8)
    pygame.draw.rect(surface, VINTAGE_GOLD, rect, 2, 8)


def draw_card_icon(surface, rect, index, accent):
    cx, cy = rect.centerx, rect.top + 58
    if index == 0:
        pygame.draw.rect(surface, CREAM_WHITE, (cx - 26, cy - 18, 24, 36), 0, 3)
        pygame.draw.rect(surface, CREAM_WHITE, (cx + 2, cy - 18, 24, 36), 0, 3)
        pygame.draw.rect(surface, accent, (cx - 26, cy - 18, 24, 36), 2, 3)
        pygame.draw.rect(surface, accent, (cx + 2, cy - 18, 24, 36), 2, 3)
    elif index == 1:
        pygame.draw.rect(surface, CREAM_WHITE, (cx - 24, cy - 16, 30, 30), 0, 5)
        pygame.draw.rect(surface, accent, (cx - 24, cy - 16, 30, 30), 2, 5)
        for dx, dy in [(-12, -2), (0, 0), (12, 2)]:
            pygame.draw.circle(surface, CHARCOAL, (cx - 9 + dx, cy - 1 + dy), 2)
    elif index == 2:
        pygame.draw.circle(surface, CREAM_WHITE, (cx, cy), 20)
        pygame.draw.circle(surface, accent, (cx, cy), 20, 2)
        t = card_sub_font.render("18", True, CHARCOAL)
        surface.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))
    elif index == 3:
        pygame.draw.rect(surface, CREAM_WHITE, (cx - 30, cy - 8, 60, 16), 0, 3)
        pygame.draw.rect(surface, accent, (cx - 30, cy - 8, 60, 16), 2, 3)
        pygame.draw.polygon(
            surface, accent, [(cx + 18, cy), (cx + 8, cy - 6), (cx + 8, cy + 6)]
        )
    elif index == 4:
        pygame.draw.circle(surface, CREAM_WHITE, (cx, cy), 22)
        pygame.draw.circle(surface, accent, (cx, cy), 22, 2)
        pygame.draw.circle(surface, accent, (cx, cy), 6)
    elif index == 5:
        pygame.draw.rect(surface, CREAM_WHITE, (cx - 28, cy - 16, 56, 32), 0, 4)
        pygame.draw.rect(surface, accent, (cx - 28, cy - 16, 56, 32), 2, 4)
        for lx in (cx - 9, cx + 9):
            pygame.draw.line(surface, accent, (lx, cy - 16), (lx, cy + 16), 1)
    elif index == 6:
        pygame.draw.circle(surface, accent, (cx - 14, cy), 14, 3)
        pygame.draw.circle(surface, accent, (cx + 14, cy), 14, 3)
        pygame.draw.circle(surface, CREAM_WHITE, (cx, cy), 14, 3)
    else:
        pygame.draw.rect(surface, CHARCOAL, (cx - 28, cy - 18, 56, 36), 0, 4)
        pygame.draw.rect(surface, accent, (cx - 28, cy - 18, 56, 36), 2, 4)
        pygame.draw.rect(surface, accent, (cx - 20, cy - 10, 40, 20), 1, 2)


def draw_lobby(balance, hover_idx):
    screen.fill(MAHOGANY)
    pygame.draw.ellipse(
        screen, LEATHER_RAIL, (-150, -260, LOBBY_WIDTH + 300, LOBBY_HEIGHT + 700)
    )
    pygame.draw.ellipse(
        screen, WOOD_LIGHT, (-130, -240, LOBBY_WIDTH + 260, LOBBY_HEIGHT + 660)
    )
    pygame.draw.ellipse(
        screen, FELT_GREEN, (-110, -220, LOBBY_WIDTH + 220, LOBBY_HEIGHT + 620)
    )

    title_surf = title_font.render("THE TERMINAL CASINO", True, GOLD_TEXT)
    screen.blit(title_surf, (LOBBY_WIDTH // 2 - title_surf.get_width() // 2, 68))
    sub_surf = subtitle_font.render(
        "Choose a table to play - your bankroll follows you everywhere",
        True,
        CREAM_WHITE,
    )
    screen.blit(sub_surf, (LOBBY_WIDTH // 2 - sub_surf.get_width() // 2, 122))

    bank_rect = pygame.Rect(30, 18, 260, 40)
    draw_wood_panel(screen, bank_rect)
    bal_txt = bank_font.render(f"BANKROLL: ${balance}", True, CREAM_WHITE)
    screen.blit(bal_txt, (bank_rect.x + 16, bank_rect.y + 8))

    draw_wood_panel(screen, reset_btn_rect)
    reset_txt = button_font.render("RESET BANKROLL", True, GOLD_TEXT)
    screen.blit(
        reset_txt,
        (
            reset_btn_rect.centerx - reset_txt.get_width() // 2,
            reset_btn_rect.centery - reset_txt.get_height() // 2,
        ),
    )

    for i, (game, rect) in enumerate(zip(GAMES, card_rects)):
        hovered = i == hover_idx
        bg = CARD_BG_HOVER if hovered else CARD_BG
        pygame.draw.rect(screen, bg, rect, 0, 10)
        pygame.draw.rect(
            screen, VINTAGE_GOLD if hovered else GOLD_SHADOW, rect, 2, 10
        )

        accent = game["accent"]
        accent_rect = pygame.Rect(rect.x + 3, rect.y + 3, rect.w - 6, 6)
        pygame.draw.rect(screen, accent, accent_rect, 0, 3)

        draw_card_icon(screen, rect, i, accent)

        t_surf = card_title_font.render(game["title"], True, CREAM_WHITE)
        screen.blit(
            t_surf, (rect.centerx - t_surf.get_width() // 2, rect.bottom - 44)
        )

    if balance <= 0:
        warn = hint_font.render(
            "You're out of chips! Use RESET BANKROLL to keep playing.",
            True,
            BRIGHT_RED,
        )
        screen.blit(warn, (LOBBY_WIDTH // 2 - warn.get_width() // 2, LOBBY_HEIGHT - 34))
    else:
        hint = hint_font.render(
            "Click a table to play - press ESC inside any game to return here.",
            True,
            (170, 170, 160),
        )
        screen.blit(hint, (LOBBY_WIDTH // 2 - hint.get_width() // 2, LOBBY_HEIGHT - 34))

    pygame.display.flip()


def restore_lobby_window():
    global screen
    screen = pygame.display.set_mode((LOBBY_WIDTH, LOBBY_HEIGHT))
    pygame.display.set_caption("The Terminal Casino")


async def main():
    balance = load_balance()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()
        hover_idx = None
        for i, rect in enumerate(card_rects):
            if rect.collidepoint(mouse_pos):
                hover_idx = i
                break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_balance(balance)
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                save_balance(balance)
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if reset_btn_rect.collidepoint(mouse_pos):
                    balance = STARTING_BALANCE
                    save_balance(balance)
                elif hover_idx is not None:
                    game = GAMES[hover_idx]
                    try:
                        balance = game["run"](balance)
                    except Exception:
                        traceback.print_exc()
                    if balance is None:
                        balance = 0
                    balance = max(0, balance)
                    save_balance(balance)
                    restore_lobby_window()

        draw_lobby(balance, hover_idx)
        clock.tick(60)

        # Essential for WebAssembly execution context
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
