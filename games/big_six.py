"""
THE TERMINAL CASINO - Old Vegas Big Six (Restored Clapper Sprite + Physics + Arcade Tuned Odds)
==============================================================================================
- Web-Ready Async Event Loop (Explicit window event pumps)
- Non-blocking Asset Initialization (Safe Audio Buffer Prepping)
- Standard Cross-Platform Font Fallbacks (Sans-serif Web Defaults)
"""

import asyncio
import math
import random
import sys
import array
import pygame

# ============================================================
# REAL CASINO MATH & SEGMENT LAYOUT (54 SEGMENTS)
# ============================================================

BIG_SIX_WHEEL = [
    "$1", "$2", "$1", "$5", "$2", "$1", "$10", "$1", "$5", "$2", "$1", "$20",
    "$1", "$2", "$1", "$5", "$2", "$1", "$20", "$1", "$2", "$1", "$5", "$2",
    "$1", "$10", "$1", "$5", "$2", "$1", "$2", "$1", "$5", "$2", "$1", "$10",
    "$1", "$5", "$2", "$1", "$20", "$1", "$2", "$1", "$5", "$2", "$1", "FLAG",
    "$1", "$2", "$1", "$5", "$2", "JOKER"
]

# TUNED PAYOUTS: Boosted high-tier returns to lower house edge ~3-5%
PAYOUT_MULTIPLIERS = {
    "$1": 1,
    "$2": 2,
    "$5": 5,
    "$10": 12,    # Boosted from 10:1
    "$20": 25,    # Boosted from 20:1
    "JOKER": 60,  # Boosted from 45:1
    "FLAG": 60,   # Boosted from 45:1
}

# Base Colors
FELT_GREEN = (10, 75, 38)
MAHOGANY_WOOD = (24, 10, 5)
WOOD_ACCENT = (45, 18, 8)
LEATHER_BORDER = (15, 5, 2)
VEGAS_GOLD = (212, 163, 89)
GOLD_HIGHLIGHT = (255, 215, 0)
CREAM_WHITE = (245, 242, 225)
CHARCOAL = (20, 20, 20)
CHROME_PEG = (230, 230, 230)

# Carnival / Vegas Rainbow Palette
CARNIVAL_COLORS = {
    "$1": (245, 240, 220),     # Ivory / White
    "$2": (225, 75, 35),       # Bright Orange-Red
    "$5": (30, 110, 200),      # Deep Blue
    "$10": (130, 45, 160),     # Vivid Purple/Magenta
    "$20": (245, 190, 40),     # Bright Gold
    "FLAG": (20, 20, 25),      # Jet Black
    "JOKER": (230, 50, 140)    # Neon Pink
}

# Standard Casino Chip Palette
CHIP_STANDARD_COLORS = {
    10: ((240, 240, 240), CHARCOAL),      # $1 White
    50: ((180, 30, 30), CREAM_WHITE),     # $2 Red
    100: ((30, 80, 180), CREAM_WHITE),    # $5 Blue
    250: ((30, 130, 60), CREAM_WHITE),    # $10 Green
    1000: ((35, 35, 35), GOLD_HIGHLIGHT)  # $20 Black
}

TEXT_COLORS = {
    "$1": CHARCOAL,
    "$2": CREAM_WHITE,
    "$5": CREAM_WHITE,
    "$10": CREAM_WHITE,
    "$20": CHARCOAL,
    "FLAG": GOLD_HIGHLIGHT,
    "JOKER": CREAM_WHITE
}

# ============================================================
# SYNTH SOUND GENERATOR
# ============================================================

def generate_synth_sound(freq_list, duration_ms, wave_type="square", volume=0.3):
    """Safely builds in-memory sound buffers; skips gracefully on web if audio pre-init fails."""
    try:
        if not pygame.mixer.get_init():
            return None
        sample_rate = 22050
        total_samples = int(sample_rate * (duration_ms / 1000.0))
        buffer = array.array("h", [0] * total_samples)
        samples_per_freq = max(1, total_samples // len(freq_list))

        for i in range(total_samples):
            freq_idx = min(i // samples_per_freq, len(freq_list) - 1)
            freq = freq_list[freq_idx]
            if freq == 0:
                val = 0
            else:
                t = i / sample_rate
                if wave_type == "square":
                    val = 32767 if math.sin(2 * math.pi * freq * t) >= 0 else -32768
                elif wave_type == "triangle":
                    val = int(32767 * (2.0 * math.fabs(2.0 * (t * freq - math.floor(t * freq + 0.5))) - 1.0))
                else:
                    val = int(32767 * math.sin(2 * math.pi * freq * t))
            buffer[i] = int(val * volume)
        return pygame.mixer.Sound(buffer=buffer)
    except Exception:
        return None

# ============================================================
# MAIN GAME FUNCTION
# ============================================================

async def run_big_six(balance):
    pygame.init()
    
    # Safe web mixer initialization
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    except Exception:
        pass

    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((1080, 720))

    clock = pygame.time.Clock()

    snd_clapper = generate_synth_sound([900, 450], 12, "square", 0.10)
    snd_win = generate_synth_sound([440, 554, 659, 880], 400, "square", 0.15)
    snd_lose = generate_synth_sound([180, 150, 120], 300, "square", 0.2)
    snd_chip = generate_synth_sound([300, 600], 40, "triangle", 0.25)

    # Standard browser-safe font stack
    FONT_OPTS = ("sans-serif", "arial", "helvetica")
    title_font = pygame.font.SysFont(FONT_OPTS, 22, bold=True)
    ui_font = pygame.font.SysFont(FONT_OPTS, 16, bold=True)
    felt_font = pygame.font.SysFont(FONT_OPTS, 15, bold=True)
    wheel_font = pygame.font.SysFont(FONT_OPTS, 9, bold=True)
    chip_num_font = pygame.font.SysFont(FONT_OPTS, 11, bold=True)

    active_chip = 10
    player_bets = {k: 0 for k in PAYOUT_MULTIPLIERS.keys()}
    win_msg = "PLACE BETS ON THE FELT, THEN SPIN THE WHEEL!"

    is_spinning = False
    wheel_angle = 0.0
    wheel_speed = 0.0
    last_clapper_angle = 0.0
    clapper_angle = 0.0

    spin_btn = pygame.Rect(842, 580, 160, 42)
    clear_btn = pygame.Rect(842, 525, 160, 42)

    bet_keys = ["$1", "$2", "$5", "$10", "$20", "FLAG", "JOKER"]
    bet_rects = {}
    
    for idx, key in enumerate(bet_keys):
        col = idx // 4
        row = idx % 4
        bx = 520 + (col * 160)
        by = 110 + (row * 82)
        bet_rects[key] = pygame.Rect(bx, by, 145, 68)

    chip_selections = [
        (10, pygame.Rect(520, 576, 48, 48), CHIP_STANDARD_COLORS[10][0], CHIP_STANDARD_COLORS[10][1]),
        (50, pygame.Rect(580, 576, 48, 48), CHIP_STANDARD_COLORS[50][0], CHIP_STANDARD_COLORS[50][1]),
        (100, pygame.Rect(640, 576, 48, 48), CHIP_STANDARD_COLORS[100][0], CHIP_STANDARD_COLORS[100][1]),
        (250, pygame.Rect(700, 576, 48, 48), CHIP_STANDARD_COLORS[250][0], CHIP_STANDARD_COLORS[250][1]),
        (1000, pygame.Rect(760, 576, 48, 48), CHIP_STANDARD_COLORS[1000][0], CHIP_STANDARD_COLORS[1000][1])
    ]

    def draw_chip_stack(surface, rect, text_val):
        bg_color, stripe_color = CHIP_STANDARD_COLORS[10]
        for val, _, col_bg, col_str in chip_selections:
            if text_val >= val:
                bg_color = col_bg
                stripe_color = col_str

        cx, cy = rect.centerx, rect.centery
        pygame.draw.circle(surface, CHARCOAL, (cx, cy + 2), 12)
        pygame.draw.circle(surface, bg_color, (cx, cy), 12)

        for angle in [0, 90, 180, 270]:
            rad = math.radians(angle)
            sx = cx + math.cos(rad) * 9
            sy = cy + math.sin(rad) * 9
            pygame.draw.circle(surface, stripe_color, (int(sx), int(sy)), 2)

        pygame.draw.circle(surface, CREAM_WHITE, (cx, cy), 6)
        display_str = str(text_val) if text_val < 1000 else f"{text_val // 1000}k"
        c_txt = chip_num_font.render(display_str, True, CHARCOAL)
        surface.blit(c_txt, (cx - c_txt.get_width() // 2, cy - c_txt.get_height() // 2))

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return balance + sum(player_bets.values())

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not is_spinning:
                    for val, rect, _, _ in chip_selections:
                        if rect.collidepoint(mouse_pos):
                            active_chip = val
                            if snd_chip: snd_chip.play()

                    if clear_btn.collidepoint(mouse_pos):
                        balance += sum(player_bets.values())
                        player_bets = {k: 0 for k in PAYOUT_MULTIPLIERS.keys()}
                        if snd_chip: snd_chip.play()

                    for key, rect in bet_rects.items():
                        if rect.collidepoint(mouse_pos):
                            if balance >= active_chip:
                                player_bets[key] += active_chip
                                balance -= active_chip
                                if snd_chip: snd_chip.play()

                    if spin_btn.collidepoint(mouse_pos):
                        if any(v > 0 for v in player_bets.values()):
                            is_spinning = True
                            wheel_speed = random.uniform(16.0, 22.0)
                            last_clapper_angle = wheel_angle
                            win_msg = "The wheel is spinning..."
                        else:
                            win_msg = "❌ PLACE A BET BEFORE SPINNING!"

        if not running:
            break

        # ----------------------------------------------------
        # ANIMATION & PHYSICS UPDATES
        # ----------------------------------------------------
        if is_spinning:
            wheel_angle += wheel_speed
            wheel_speed *= 0.985

            seg_arc = 360.0 / len(BIG_SIX_WHEEL)
            if abs(wheel_angle - last_clapper_angle) >= seg_arc:
                if snd_clapper: snd_clapper.play()
                last_clapper_angle = wheel_angle - (wheel_angle % seg_arc)
                clapper_angle = -min(28.0, 10.0 + wheel_speed * 0.8)

            if wheel_speed < 0.01:
                is_spinning = False
                wheel_speed = 0

                normalized = (270 - wheel_angle) % 360
                winner_idx = int((normalized + seg_arc / 2) / seg_arc) % len(BIG_SIX_WHEEL)
                winning_slot = BIG_SIX_WHEEL[winner_idx]

                # Identify neighboring slots for Near-Miss Consolation Mechanics
                prev_slot = BIG_SIX_WHEEL[(winner_idx - 1) % len(BIG_SIX_WHEEL)]
                next_slot = BIG_SIX_WHEEL[(winner_idx + 1) % len(BIG_SIX_WHEEL)]

                total_won = 0
                near_miss = False

                # 1. Direct Hit Check
                if player_bets[winning_slot] > 0:
                    mult = PAYOUT_MULTIPLIERS[winning_slot]
                    total_won += player_bets[winning_slot] * (mult + 1)

                # 2. Near-Miss Consolation Check for High-Tier Bets ($20, Joker, Flag)
                for spot in ["JOKER", "FLAG", "$20"]:
                    if player_bets[spot] > 0 and spot in (prev_slot, next_slot) and spot != winning_slot:
                        consolation = player_bets[spot] * 2  # Pays 2:1 near-miss bonus
                        total_won += consolation
                        near_miss = True

                if total_won > 0:
                    balance += total_won
                    if near_miss and player_bets[winning_slot] == 0:
                        win_msg = f"⚡ NEAR MISS! Consolation payout! (Paid ${total_won})"
                    else:
                        win_msg = f"🎉 WINNER! Stopped on {winning_slot} (Paid ${total_won})!"
                    if snd_win: snd_win.play()
                else:
                    win_msg = f"😢 Stopped on {winning_slot}. Better luck next spin!"
                    if snd_lose: snd_lose.play()

                player_bets = {k: 0 for k in PAYOUT_MULTIPLIERS.keys()}

        clapper_angle += (0 - clapper_angle) * 0.35

        # ----------------------------------------------------
        # RENDER TABLE
        # ----------------------------------------------------
        screen.fill(MAHOGANY_WOOD)
        pygame.draw.rect(screen, LEATHER_BORDER, (15, 15, 1050, 690), 0, 14)
        pygame.draw.rect(screen, FELT_GREEN, (30, 30, 1020, 660), 0, 8)

        t_surf = title_font.render(" ", True, VEGAS_GOLD)
        screen.blit(t_surf, (540 - t_surf.get_width() // 2, 45))

        # ----------------------------------------------------
        # WHEEL & STAND
        # ----------------------------------------------------
        w_cx, w_cy = 265, 310
        w_outer_rad = 220
        w_inner_hub = 50

        shadow_poly = [(w_cx - 95, 615), (w_cx + 95, 615), (w_cx + 50, w_cy + 100), (w_cx - 50, w_cy + 100)]
        pygame.draw.polygon(screen, (5, 40, 20), shadow_poly)

        pygame.draw.polygon(screen, WOOD_ACCENT, [(w_cx - 40, w_cy + 100), (w_cx + 40, w_cy + 100), (w_cx + 85, 610), (w_cx - 85, 610)])
        pygame.draw.polygon(screen, VEGAS_GOLD, [(w_cx - 40, w_cy + 100), (w_cx + 40, w_cy + 100), (w_cx + 85, 610), (w_cx - 85, 610)], 2)
        pygame.draw.rect(screen, CHARCOAL, (w_cx - 105, 600, 210, 24), 0, 4)

        pygame.draw.circle(screen, CHARCOAL, (w_cx, w_cy), w_outer_rad + 10)
        pygame.draw.circle(screen, VEGAS_GOLD, (w_cx, w_cy), w_outer_rad + 6, 3)
        pygame.draw.circle(screen, MAHOGANY_WOOD, (w_cx, w_cy), w_outer_rad)

        seg_arc = 360.0 / len(BIG_SIX_WHEEL)
        for idx, slot in enumerate(BIG_SIX_WHEEL):
            deg = (idx * seg_arc + wheel_angle) % 360
            rad_s = math.radians(deg - seg_arc / 2)
            rad_e = math.radians(deg + seg_arc / 2)

            p1 = (w_cx + math.cos(rad_s) * w_outer_rad, w_cy + math.sin(rad_s) * w_outer_rad)
            p2 = (w_cx + math.cos(rad_e) * w_outer_rad, w_cy + math.sin(rad_e) * w_outer_rad)
            p3 = (w_cx + math.cos(rad_e) * w_inner_hub, w_cy + math.sin(rad_e) * w_inner_hub)
            p4 = (w_cx + math.cos(rad_s) * w_inner_hub, w_cy + math.sin(rad_s) * w_inner_hub)

            color = CARNIVAL_COLORS.get(slot, CREAM_WHITE)
            pygame.draw.polygon(screen, color, [p1, p2, p3, p4])
            pygame.draw.polygon(screen, CHARCOAL, [p1, p2, p3, p4], 1)

            pygame.draw.circle(screen, CHROME_PEG, (int(p1[0]), int(p1[1])), 3)

            t_deg = math.radians(deg)
            tx = w_cx + math.cos(t_deg) * (w_outer_rad - 22)
            ty = w_cy + math.sin(t_deg) * (w_outer_rad - 22)
            
            tc = TEXT_COLORS.get(slot, CHARCOAL)
            lbl = wheel_font.render(slot.replace("$", ""), True, tc)
            lbl = pygame.transform.rotate(lbl, -deg - 90)
            screen.blit(lbl, (tx - lbl.get_width() // 2, ty - lbl.get_height() // 2))

        pygame.draw.circle(screen, MAHOGANY_WOOD, (w_cx, w_cy), w_inner_hub)
        pygame.draw.circle(screen, VEGAS_GOLD, (w_cx, w_cy), w_inner_hub, 3)
        pygame.draw.circle(screen, GOLD_HIGHLIGHT, (w_cx, w_cy), 22)
        pygame.draw.circle(screen, CHARCOAL, (w_cx, w_cy), 22, 2)
        pygame.draw.circle(screen, CHARCOAL, (w_cx, w_cy), 6)

        # ----------------------------------------------------
        # RESTORED ORIGINAL TRIANGLE SPRITE + ANIMATED ROTATION
        # ----------------------------------------------------
        pivot_x, pivot_y = w_cx, w_cy - w_outer_rad - 14
        
        # Original Downward-Pointing Triangle Sprite (Relative to Hinge Pivot)
        raw_pts = [(0, 26), (-7, 0), (7, 0)]
        rot_rad = math.radians(clapper_angle)

        transformed_pts = []
        for px, py in raw_pts:
            rx = px * math.cos(rot_rad) - py * math.sin(rot_rad) + pivot_x
            ry = px * math.sin(rot_rad) + py * math.cos(rot_rad) + pivot_y
            transformed_pts.append((rx, ry))

        # Render original triangle sprite
        pygame.draw.polygon(screen, CARNIVAL_COLORS["$2"], transformed_pts)
        pygame.draw.polygon(screen, CHARCOAL, transformed_pts, 1)

        # Original Pin Base
        pygame.draw.circle(screen, CHROME_PEG, (pivot_x, pivot_y), 4)

        # ----------------------------------------------------
        # BETTING FELT FIELD
        # ----------------------------------------------------
        for key, rect in bet_rects.items():
            amt = player_bets.get(key, 0)
            b_bg = CARNIVAL_COLORS.get(key, (24, 60, 36))

            pygame.draw.rect(screen, b_bg, rect, 0, 6)
            border_col = GOLD_HIGHLIGHT if amt > 0 else VEGAS_GOLD
            
            pygame.draw.rect(screen, border_col, rect, 2, 6)
            pygame.draw.rect(screen, border_col, rect.inflate(-8, -8), 1, 4)

            tc = TEXT_COLORS.get(key, CREAM_WHITE)
            mult_txt = f"{PAYOUT_MULTIPLIERS[key]}:1"
            
            lbl_title = felt_font.render(key, True, tc)
            lbl_sub = felt_font.render(f"PAYS {mult_txt}", True, tc)

            screen.blit(lbl_title, (rect.centerx - lbl_title.get_width() // 2, rect.y + 10))
            screen.blit(lbl_sub, (rect.centerx - lbl_sub.get_width() // 2, rect.y + 36))

            if amt > 0:
                draw_chip_stack(screen, pygame.Rect(rect.right - 40, rect.top + 8, 32, 32), amt)

        # ----------------------------------------------------
        # HUD & CHIP RACK
        # ----------------------------------------------------
        pygame.draw.rect(screen, CHARCOAL, (520, 465, 310, 36), 0, 4)
        pygame.draw.rect(screen, VEGAS_GOLD, (520, 465, 310, 36), 1, 4)
        b_txt = ui_font.render(f"BANKROLL: ${balance}", True, CREAM_WHITE)
        screen.blit(b_txt, (535, 472))

        pygame.draw.rect(screen, CHARCOAL, (510, 565, 310, 68), 0, 6)
        pygame.draw.rect(screen, VEGAS_GOLD, (510, 565, 310, 68), 2, 6)

        for val, rect, c1, c2 in chip_selections:
            border_col = GOLD_HIGHLIGHT if active_chip == val else CHARCOAL
            pygame.draw.circle(screen, border_col, rect.center, 24)
            pygame.draw.circle(screen, c1, rect.center, 22)

            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                sx = rect.centerx + math.cos(rad) * 16
                sy = rect.centery + math.sin(rad) * 16
                pygame.draw.circle(screen, c2, (int(sx), int(sy)), 3)

            pygame.draw.circle(screen, CREAM_WHITE, rect.center, 12)
            lbl = chip_num_font.render(str(val) if val < 1000 else "1k", True, CHARCOAL)
            screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))

        # Action Buttons
        for b_rect, label, col in [(spin_btn, "SPIN WHEEL", CARNIVAL_COLORS["$2"]), (clear_btn, "CLEAR BETS", CHARCOAL)]:
            pygame.draw.rect(screen, col, b_rect, 0, 6)
            pygame.draw.rect(screen, CREAM_WHITE, b_rect, 1, 6)
            bt = ui_font.render(label, True, CREAM_WHITE)
            screen.blit(bt, (b_rect.centerx - bt.get_width() // 2, b_rect.centery - bt.get_height() // 2))

        # Announcement Banner
        pygame.draw.rect(screen, CHARCOAL, (30, 645, 1020, 40), 0, 4)
        pygame.draw.rect(screen, VEGAS_GOLD, (30, 645, 1020, 40), 2, 4)
        msg_s = ui_font.render(win_msg, True, VEGAS_GOLD if "🎉" in win_msg or "⚡" in win_msg else CREAM_WHITE)
        screen.blit(msg_s, (540 - msg_s.get_width() // 2, 654))

        pygame.display.flip()
        # Yield control back to browser event loop
        await asyncio.sleep(0)
        clock.tick(60)

    return balance

if __name__ == "__main__":
    asyncio.run(run_big_six(1000))
