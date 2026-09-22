"""
THE TERMINAL CASINO - Main Lobby / Launcher
=============================================
Ties together twelve table games into a single game with one
shared chip balance. Run this file to play.

    python main.py

Each game lives in games/<name>.py and exposes a run_<name>(balance)
function.
"""

import asyncio
import json
import math
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
JET_BLACK = (18, 18, 18)
CARD_BG = (46, 20, 12)
CARD_BG_HOVER = (66, 30, 16)

# Use same font fallback approach as the games (emoji support + Georgia/Arial)
FONT_OPTIONS = ("segoeuiemoji", "applecoloremoji", "notocoloremoji", "georgia", "arial")
title_font = pygame.font.SysFont(FONT_OPTIONS, 42, bold=True)
subtitle_font = pygame.font.SysFont(FONT_OPTIONS, 15)
bank_font = pygame.font.SysFont(FONT_OPTIONS, 24, bold=True)
card_title_font = pygame.font.SysFont(FONT_OPTIONS, 18, bold=True)
card_sub_font = pygame.font.SysFont(FONT_OPTIONS, 12)
icon_pip_font = pygame.font.SysFont(FONT_OPTIONS, 11, bold=True)
hint_font = pygame.font.SysFont(FONT_OPTIONS, 14)
button_font = pygame.font.SysFont(FONT_OPTIONS, 15, bold=True)

# ----------------------------------------------------------------
# Safe Persistent bankroll (Web Assembly & Desktop compatible)
# ----------------------------------------------------------------

SAVE_FILE = "chips_save.json"
STARTING_BALANCE = 1000

try:
    import js
    HAS_JS = True
except ImportError:
    HAS_JS = False


def load_balance():
    if HAS_JS:
        try:
            saved = js.localStorage.getItem("terminal_casino_bankroll")
            if saved is not None:
                return int(saved)
        except Exception as e:
            print("Could not load from localStorage:", e)
    else:
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, "r") as f:
                    data = json.load(f)
                    return int(data.get("balance", STARTING_BALANCE))
        except Exception as e:
            print("Could not load save file:", e)
    return STARTING_BALANCE


def save_balance(balance):
    if HAS_JS:
        try:
            js.localStorage.setItem("terminal_casino_bankroll", str(balance))
        except Exception as e:
            print("Could not save to localStorage:", e)
    else:
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
    baccarat,
    big_six,
    blackjack,
    craps,
    keno,
    lottery,
    mechanical_derby,
    plinko,
    roulette,
    slots,
    ultimate_hold_em,
    video_poker,
)

screen = pygame.display.set_mode((LOBBY_WIDTH, LOBBY_HEIGHT))
pygame.display.set_caption("The Terminal Casino")

# ----------------------------------------------------------------
# Game catalog (12 Games Total)
# ----------------------------------------------------------------

GAMES = [
    {
        "title": "Baccarat",
        "subtitle": "Punto Banco",
        "run": baccarat.run_baccarat,
        "accent": (180, 50, 80),
    },
    {
        "title": "Big Six Wheel",
        "subtitle": "Money Wheel",
        "run": big_six.run_big_six,
        "accent": (210, 140, 30),
    },
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
        "title": "Lottery",
        "subtitle": "Daily Drawing Machine",
        "run": lottery.run_lottery,
        "accent": (70, 160, 120),
    },
    {
        "title": "Mechanical Derby",
        "subtitle": "Racehorse Wagering",
        "run": mechanical_derby.run_mechanical_derby,
        "accent": (170, 120, 60),
    },
    {
        "title": "Plinko",
        "subtitle": "Peg Drop Board",
        "run": plinko.run_plinko,
        "accent": (210, 80, 180),
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
# Lobby layout: 4 columns x 3 rows of game cards
# ----------------------------------------------------------------

COLS, ROWS = 4, 3
CARD_W, CARD_H = 230, 135
GRID_MARGIN_X, GRID_TOP = 45, 175
GAP_X, GAP_Y = 20, 16

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
    cx, cy = rect.centerx, rect.top + 45

    if index == 0:  # Baccarat - fanned 3-card spread with pips (punto banco hand)
        fan_offsets = [(-16, 2, -12), (0, -4, 0), (16, 2, 12)]
        for dx, dy, _tilt in fan_offsets:
            card_w, card_h = 18, 26
            fx, fy = cx + dx - card_w // 2, cy + dy - card_h // 2
            pygame.draw.rect(surface, CREAM_WHITE, (fx, fy, card_w, card_h), 0, 3)
            pygame.draw.rect(surface, accent, (fx, fy, card_w, card_h), 2, 3)
        # small red pip diamonds on the centre card to read as a hand of cards
        pip_cx, pip_cy = cx, cy - 4
        for pdx, pdy in [(0, -6), (-5, 3), (5, 3)]:
            pygame.draw.polygon(
                surface,
                BRIGHT_RED,
                [
                    (pip_cx + pdx, pip_cy + pdy - 3),
                    (pip_cx + pdx + 3, pip_cy + pdy),
                    (pip_cx + pdx, pip_cy + pdy + 3),
                    (pip_cx + pdx - 3, pip_cy + pdy),
                ],
            )
    elif index == 1:  # Big Six
        pygame.draw.circle(surface, CREAM_WHITE, (cx, cy), 18)
        pygame.draw.circle(surface, accent, (cx, cy), 18, 2)
        for angle_deg in range(0, 360, 45):
            rad = math.radians(angle_deg)
            ex = cx + int(18 * math.cos(rad))
            ey = cy + int(18 * math.sin(rad))
            pygame.draw.line(surface, accent, (cx, cy), (ex, ey), 1)
    elif index == 2:  # Blackjack - Ace + King, "21" pairing
        card_w, card_h = 20, 30
        left = pygame.Rect(cx - 22, cy - 15, card_w, card_h)
        right = pygame.Rect(cx + 2, cy - 15, card_w, card_h)
        pygame.draw.rect(surface, CREAM_WHITE, left, 0, 3)
        pygame.draw.rect(surface, CREAM_WHITE, right, 0, 3)
        pygame.draw.rect(surface, accent, left, 2, 3)
        pygame.draw.rect(surface, accent, right, 2, 3)
        a_txt = icon_pip_font.render("A", True, CHARCOAL)
        k_txt = icon_pip_font.render("K", True, CHARCOAL)
        surface.blit(a_txt, (left.centerx - a_txt.get_width() // 2, left.centery - a_txt.get_height() // 2))
        surface.blit(k_txt, (right.centerx - k_txt.get_width() // 2, right.centery - k_txt.get_height() // 2))
    elif index == 3:  # Craps
        pygame.draw.rect(surface, CREAM_WHITE, (cx - 20, cy - 12, 24, 24), 0, 4)
        pygame.draw.rect(surface, accent, (cx - 20, cy - 12, 24, 24), 2, 4)
        for dx, dy in [(-8, -2), (0, 0), (8, 2)]:
            pygame.draw.circle(surface, CHARCOAL, (cx - 8 + dx, cy + dy), 2)
    elif index == 4:  # Keno
        pygame.draw.circle(surface, CREAM_WHITE, (cx, cy), 16)
        pygame.draw.circle(surface, accent, (cx, cy), 16, 2)
        t = card_sub_font.render("80", True, CHARCOAL)
        surface.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))
    elif index == 5:  # Lottery Ticket Icon
        t_rect = pygame.Rect(cx - 22, cy - 15, 44, 30)
        pygame.draw.rect(surface, CREAM_WHITE, t_rect, 0, 4)
        pygame.draw.rect(surface, accent, t_rect, 2, 4)

        pygame.draw.rect(surface, accent, (cx - 19, cy - 12, 38, 7), 0, 2)

        for gx in (-12, -2, 8):
            for gy in (0, 9):
                pygame.draw.rect(surface, VINTAGE_GOLD, (cx + gx, cy + gy, 6, 6), 1)

        pygame.draw.circle(surface, CARD_BG, (cx - 22, cy), 4)
        pygame.draw.circle(surface, CARD_BG, (cx + 22, cy), 4)
        pygame.draw.circle(surface, accent, (cx - 22, cy), 4, 1)
        pygame.draw.circle(surface, accent, (cx + 22, cy), 4, 1)
    elif index == 6:  # Mechanical Derby - horse head silhouette
        horse_points = [
            (cx - 6, cy + 14),   # chest / bottom
            (cx - 10, cy + 2),   # neck front
            (cx - 6, cy - 10),   # jaw
            (cx - 1, cy - 15),   # nose bridge
            (cx + 6, cy - 16),   # nose tip
            (cx + 5, cy - 11),   # under nose
            (cx + 1, cy - 9),    # mouth
            (cx - 1, cy - 4),    # throat
            (cx + 6, cy - 2),    # mane back edge top
            (cx + 10, cy + 6),   # mane back edge bottom
            (cx + 4, cy + 10),   # back to neck
            (cx + 2, cy + 16),   # bottom right
        ]
        pygame.draw.polygon(surface, CREAM_WHITE, horse_points)
        pygame.draw.polygon(surface, accent, horse_points, 2)
        # ear
        pygame.draw.polygon(
            surface,
            accent,
            [(cx - 2, cy - 12), (cx + 2, cy - 20), (cx + 4, cy - 12)],
            1,
        )
        # eye
        pygame.draw.circle(surface, CHARCOAL, (cx, cy - 6), 1)
    elif index == 7:  # Plinko
        # Inverted peg layout: wide at top, narrowing downward
        for px, py in [(-12, -10), (0, -10), (12, -10), (-6, 0), (6, 0), (0, 10)]:
            pygame.draw.circle(surface, accent, (cx + px, cy + py), 2)
        pygame.draw.circle(surface, CREAM_WHITE, (cx, cy - 14), 4)
    elif index == 8:  # Roulette - wedged wheel with ball
        radius = 18
        wedge_count = 10
        for w in range(wedge_count):
            start_ang = math.radians(w * (360 / wedge_count) - 90)
            end_ang = math.radians((w + 1) * (360 / wedge_count) - 90)
            points = [(cx, cy)]
            steps = 4
            for s in range(steps + 1):
                ang = start_ang + (end_ang - start_ang) * (s / steps)
                points.append(
                    (cx + radius * math.cos(ang), cy + radius * math.sin(ang))
                )
            wedge_color = BRIGHT_RED if w % 2 == 0 else JET_BLACK
            pygame.draw.polygon(surface, wedge_color, points)
        pygame.draw.circle(surface, accent, (cx, cy), radius, 2)
        pygame.draw.circle(surface, VINTAGE_GOLD, (cx, cy), 4)
        # ball sitting on the rim
        ball_ang = math.radians(-40)
        bx = cx + (radius - 3) * math.cos(ball_ang)
        by = cy + (radius - 3) * math.sin(ball_ang)
        pygame.draw.circle(surface, CREAM_WHITE, (int(bx), int(by)), 3)
    elif index == 9:  # Slots
        pygame.draw.rect(surface, CREAM_WHITE, (cx - 22, cy - 12, 44, 24), 0, 4)
        pygame.draw.rect(surface, accent, (cx - 22, cy - 12, 44, 24), 2, 4)
        for lx in (cx - 7, cx + 7):
            pygame.draw.line(surface, accent, (lx, cy - 12), (lx, cy + 12), 1)
    elif index == 10:  # Ultimate Hold 'Em - stacked poker chip tower
        chip_r = 14
        for i, dy in enumerate((10, 2, -6)):
            chip_cy = cy + dy
            pygame.draw.ellipse(
                surface, accent, (cx - chip_r, chip_cy - 5, chip_r * 2, 10)
            )
            pygame.draw.ellipse(
                surface, CREAM_WHITE, (cx - chip_r, chip_cy - 5, chip_r * 2, 10), 2
            )
            for sx in range(-1, 2):
                notch_x = cx + sx * (chip_r - 4)
                pygame.draw.line(
                    surface,
                    CREAM_WHITE,
                    (notch_x, chip_cy - 4),
                    (notch_x, chip_cy - 1),
                    2,
                )
    else:  # Video Poker
        pygame.draw.rect(surface, CHARCOAL, (cx - 22, cy - 14, 44, 28), 0, 4)
        pygame.draw.rect(surface, accent, (cx - 22, cy - 14, 44, 28), 2, 4)
        pygame.draw.rect(surface, accent, (cx - 16, cy - 8, 32, 16), 1, 2)


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
    screen.blit(title_surf, (LOBBY_WIDTH // 2 - title_surf.get_width() // 2, 60))
    sub_surf = subtitle_font.render(
        "Twelve classic casino games in one - Try your luck!",
        True,
        CREAM_WHITE,
    )
    screen.blit(sub_surf, (LOBBY_WIDTH // 2 - sub_surf.get_width() // 2, 112))

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
        accent_rect = pygame.Rect(rect.x + 3, rect.y + 3, rect.width - 6, 5)
        pygame.draw.rect(screen, accent, accent_rect, 0, 3)

        draw_card_icon(screen, rect, i, accent)

        t_surf = card_title_font.render(game["title"], True, CREAM_WHITE)
        screen.blit(
            t_surf, (rect.centerx - t_surf.get_width() // 2, rect.bottom - 32)
        )

    if balance <= 0:
        warn = hint_font.render(
            "You're out of chips! Use RESET BANKROLL to keep playing.",
            True,
            BRIGHT_RED,
        )
        screen.blit(warn, (LOBBY_WIDTH // 2 - warn.get_width() // 2, LOBBY_HEIGHT - 30))
    else:
        hint = hint_font.render(
            "Click a table to play - press ESC inside any game to return here.",
            True,
            (170, 170, 160),
        )
        screen.blit(hint, (LOBBY_WIDTH // 2 - hint.get_width() // 2, LOBBY_HEIGHT - 30))

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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if reset_btn_rect.collidepoint(mouse_pos):
                    balance = STARTING_BALANCE
                    save_balance(balance)
                elif hover_idx is not None:
                    game = GAMES[hover_idx]
                    result = None
                    try:
                        result = game["run"](balance)

                        if asyncio.iscoroutine(result):
                            try:
                                result = await result
                            except SystemExit:
                                traceback.print_exc()
                                result = balance
                    except SystemExit:
                        traceback.print_exc()
                        result = balance
                    except Exception:
                        traceback.print_exc()
                        result = balance

                    if result is None:
                        print(f"Warning: {game['title']} returned None. Preserving bankroll.")
                    else:
                        try:
                            balance = int(result)
                        except Exception:
                            print("Warning: game returned non-numeric balance, preserving previous balance.")

                    save_balance(balance)
                    restore_lobby_window()

        draw_lobby(balance, hover_idx)
        clock.tick(60)

        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
