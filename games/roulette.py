import asyncio
import pygame
import random
import sys
import array
import math

# ============================================================
#       ORIGINAL CASINO MATH ENGINE & GAME LOGIC
# ============================================================

ROULETTE_NUMBERS = [
    (0, "GREEN"), (32, "RED"), (15, "BLACK"), (19, "RED"), (4, "BLACK"),
    (21, "RED"), (2, "BLACK"), (25, "RED"), (17, "BLACK"), (34, "RED"),
    (6, "BLACK"), (27, "RED"), (13, "BLACK"), (36, "RED"), (11, "BLACK"),
    (30, "RED"), (8, "BLACK"), (23, "RED"), (10, "BLACK"), (5, "RED"),
    (24, "BLACK"), (16, "RED"), (33, "BLACK"), (1, "RED"), (20, "BLACK"),
    (14, "RED"), (31, "BLACK"), (9, "RED"), (22, "BLACK"), (18, "RED"),
    (29, "BLACK"), (7, "RED"), (28, "BLACK"), (12, "RED"), (35, "BLACK"),
    (3, "RED"), (26, "BLACK")
]

NUMBER_COLORS = {num: color for num, color in ROULETTE_NUMBERS}


def evaluate_all_wagers(winning_num, winning_color, active_bets):
    """Evaluates all placed stacked wagers simultaneously with accurate casino math."""
    total_payout = 0
    breakdown_messages = []

    for bet_key, bet_amount in active_bets.items():
        if bet_amount <= 0:
            continue

        bet_type, bet_value = bet_key.split(":")

        # COLOR BETS (1-to-1 Payout)
        if bet_type == "COLOR" and bet_value == winning_color:
            total_payout += bet_amount * 2
            breakdown_messages.append(f"Color {bet_value} (+${bet_amount * 2})")

        # EVEN / ODD (1-to-1 Payout, Zero loses)
        elif bet_type == "EVEN_ODD" and winning_num != 0:
            if bet_value == "EVEN" and winning_num % 2 == 0:
                total_payout += bet_amount * 2
                breakdown_messages.append(f"Even (+${bet_amount * 2})")
            elif bet_value == "ODD" and winning_num % 2 != 0:
                total_payout += bet_amount * 2
                breakdown_messages.append(f"Odd (+${bet_amount * 2})")

        # HIGH / LOW (1-to-1 Payout)
        elif bet_type == "HI_LOW" and winning_num != 0:
            if bet_value == "LOW" and 1 <= winning_num <= 18:
                total_payout += bet_amount * 2
                breakdown_messages.append(f"1-18 Low (+${bet_amount * 2})")
            elif bet_value == "HIGH" and 19 <= winning_num <= 36:
                total_payout += bet_amount * 2
                breakdown_messages.append(f"19-36 High (+${bet_amount * 2})")

        # DOZENS (2-to-1 Payout)
        elif bet_type == "DOZEN" and winning_num != 0:
            if bet_value == "1ST" and 1 <= winning_num <= 12:
                total_payout += bet_amount * 3
                breakdown_messages.append(f"1st 12 (+${bet_amount * 3})")
            elif bet_value == "2ND" and 13 <= winning_num <= 24:
                total_payout += bet_amount * 3
                breakdown_messages.append(f"2nd 12 (+${bet_amount * 3})")
            elif bet_value == "3RD" and 25 <= winning_num <= 36:
                total_payout += bet_amount * 3
                breakdown_messages.append(f"3rd 12 (+${bet_amount * 3})")

        # STRAIGHT UP NUMBER (35-to-1 Payout -> Pays 36x stake total)
        elif bet_type == "NUMBER" and int(bet_value) == winning_num:
            total_payout += bet_amount * 36
            breakdown_messages.append(f"Single #{bet_value} Hit! (+${bet_amount * 36})")

    return total_payout, ", ".join(breakdown_messages)


# ============================================================
#              PYGAME VISUAL ENGINE INITIALIZATION
# ============================================================

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

WIDTH, HEIGHT = 980, 640

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vintage Vegas Roulette - Perfect Layout")

clock = pygame.time.Clock()
_lobby_hint_font = pygame.font.SysFont(None, 20)
_GAME_TITLE = ("Vintage Vegas Roulette - Perfect Layout")


# ============================================================
#               PROCEDURAL AUDIO SYNTH DRIVERS
# ============================================================

def generate_synth_sound(freq_list, duration_ms, wave_type="square", volume=0.3):
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


snd_ball_click = generate_synth_sound([1600, 1200], 12, wave_type="square", volume=0.1)
snd_win = generate_synth_sound([523, 659, 784, 1046], 400, wave_type="square", volume=0.15)
snd_lose = generate_synth_sound([220, 147], 300, wave_type="square", volume=0.2)
snd_chip = generate_synth_sound([400, 600], 40, wave_type="triangle", volume=0.25)


# ============================================================
#                       COLOR PALETTE
# ============================================================

FELT_GREEN = (10, 68, 33)
MAHOGANY = (56, 18, 11)
WOOD_LIGHT = (84, 30, 20)
CHROME_SHADOW = (110, 110, 110)
VINTAGE_GOLD = (212, 163, 89)
GOLD_SHADOW = (145, 105, 45)
CREAM_WHITE = (247, 245, 230)
CHARCOAL = (24, 24, 24)
BRIGHT_RED = (190, 25, 25)
WHITE_GLINT = (255, 255, 255)


# ============================================================
#                            FONTS
# ============================================================

font_options = ["segoeuiemoji", "applecoloremoji", "notocoloremoji", "arial"]

ui_font = pygame.font.SysFont(font_options, 15, bold=True)
label_font = pygame.font.SysFont(font_options, 13, bold=True)
grid_font = pygame.font.SysFont("georgia", 14, bold=True)
wheel_font = pygame.font.SysFont("arial", 10, bold=True)
chip_num_font = pygame.font.SysFont("arial", 11, bold=True)


# ============================================================
#                         LIVE STATES
# ============================================================


async def run_roulette(balance):
    global screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(_GAME_TITLE)
    running = True
    active_chip_wager = 10
    win_message = "CHOOSE CHIP VALUE, PLACE MULTIPLE BETS, THEN SPIN!"
    player_bets = {}


    # ============================================================
    #                   PHYSICS ENGINE VARIABLES
    # ============================================================

    is_spinning = False
    wheel_angle = 0.0
    ball_angle = 270.0
    wheel_speed = 0.0
    ball_speed = 0.0
    spin_timer = 0
    ball_settled = False


    # ============================================================
    #     ADJUSTED LAYOUT: SLIGHTLY LARGER WHEEL & SHIFTED UI
    # ============================================================

    # Shifted 30px right to leave space for slightly bigger wheel
    start_grid_x = 430
    start_grid_y = 120
    grid_w = 40
    grid_h = 42

    number_rects = {}
    for num in range(1, 37):
        row = (num - 1) % 3
        col = (num - 1) // 3
        nx = start_grid_x + (col * grid_w)
        ny = start_grid_y + (2 - row) * grid_h
        number_rects[num] = (pygame.Rect(nx, ny, grid_w, grid_h), f"NUMBER:{num}")

    grid_total_width = grid_w * 12
    dozen_w = grid_total_width // 3
    outside_w = grid_total_width // 6

    dozens_y = start_grid_y + (grid_h * 3)
    outside_y = dozens_y + grid_h

    zero_rect = pygame.Rect(start_grid_x - 45, start_grid_y, 45, grid_h * 5)

    outside_bet_rects = {
        "1st 12": (pygame.Rect(start_grid_x, dozens_y, dozen_w, grid_h), "DOZEN:1ST"),
        "2nd 12": (pygame.Rect(start_grid_x + dozen_w, dozens_y, dozen_w, grid_h), "DOZEN:2ND"),
        "3rd 12": (pygame.Rect(start_grid_x + (dozen_w * 2), dozens_y, dozen_w, grid_h), "DOZEN:3RD"),
        "1-18": (pygame.Rect(start_grid_x, outside_y, outside_w, grid_h), "HI_LOW:LOW"),
        "EVEN": (pygame.Rect(start_grid_x + outside_w, outside_y, outside_w, grid_h), "EVEN_ODD:EVEN"),
        "RED": (pygame.Rect(start_grid_x + (outside_w * 2), outside_y, outside_w, grid_h), "COLOR:RED"),
        "BLACK": (pygame.Rect(start_grid_x + (outside_w * 3), outside_y, outside_w, grid_h), "COLOR:BLACK"),
        "ODD": (pygame.Rect(start_grid_x + (outside_w * 4), outside_y, outside_w, grid_h), "EVEN_ODD:ODD"),
        "19-36": (pygame.Rect(start_grid_x + (outside_w * 5), outside_y, outside_w, grid_h), "HI_LOW:HIGH")
    }

    # Chips Row Positioned Relative to Shifted Grid
    chips_y = outside_y + grid_h + 24
    chip_start_x = start_grid_x - 30
    chip_spacing = 96

    chip_selections = [
        (10, pygame.Rect(chip_start_x, chips_y, 42, 42), (240, 240, 240), (40, 40, 40)),
        (50, pygame.Rect(chip_start_x + chip_spacing, chips_y, 42, 42), (180, 30, 30), (240, 240, 240)),
        (100, pygame.Rect(chip_start_x + (chip_spacing * 2), chips_y, 42, 42), (30, 80, 180), (240, 240, 240)),
        (250, pygame.Rect(chip_start_x + (chip_spacing * 3), chips_y, 42, 42), (30, 130, 60), (212, 163, 89)),
        (1000, pygame.Rect(chip_start_x + (chip_spacing * 4), chips_y, 42, 42), (30, 30, 30), (212, 163, 89))
    ]

    # Action Controls Aligned Under Shifted Grid
    controls_y = chips_y + 55

    bankroll_rect = pygame.Rect(start_grid_x - 30, controls_y, 200, 44)
    clear_btn_rect = pygame.Rect(start_grid_x + 185, controls_y, 110, 44)
    spin_btn_rect = pygame.Rect(start_grid_x + 310, controls_y, 170, 44)


    # ============================================================
    #                       CHIP DRAWING
    # ============================================================

    def draw_chip_stack(surface, center_rect, text_val):
        bg_color = (240, 240, 240)
        stripe_color = (40, 40, 40)

        for val, _, col_bg, col_str in chip_selections:
            if text_val >= val:
                bg_color = col_bg
                stripe_color = col_str

        cx = center_rect.centerx
        cy = center_rect.centery

        pygame.draw.circle(surface, CHARCOAL, (cx, cy + 2), 13)
        pygame.draw.circle(surface, bg_color, (cx, cy), 13)

        for angle in [0, 90, 180, 270]:
            rad = math.radians(angle)
            sx = cx + math.cos(rad) * 10
            sy = cy + math.sin(rad) * 10
            pygame.draw.circle(surface, stripe_color, (int(sx), int(sy)), 2)

        pygame.draw.circle(surface, CREAM_WHITE, (cx, cy), 7)

        display_str = str(text_val) if text_val < 1000 else f"{text_val // 1000}k"
        c_txt = chip_num_font.render(display_str, True, CHARCOAL)
        surface.blit(c_txt, (cx - c_txt.get_width() // 2, cy - c_txt.get_height() // 2))


    # ============================================================
    #                      RENDERING LOOP
    # ============================================================

    while running:
        dt = clock.tick(60) / 1000.0 * 60.0

        # ========================================================
        #                       EVENT HANDLING
        # ========================================================

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                if not is_spinning:
                    # Chip Selection
                    for val, rect, c1, c2 in chip_selections:
                        if rect.collidepoint(mouse_pos):
                            active_chip_wager = val
                            snd_chip.play()

                    # Clear Bets
                    if clear_btn_rect.collidepoint(mouse_pos):
                        total_refund = sum(player_bets.values())
                        balance += total_refund
                        player_bets.clear()
                        snd_chip.play()

                    # Outside Bets
                    for label, (rect, bet_key) in outside_bet_rects.items():
                        if rect.collidepoint(mouse_pos):
                            if balance >= active_chip_wager:
                                player_bets[bet_key] = player_bets.get(bet_key, 0) + active_chip_wager
                                balance -= active_chip_wager
                                snd_chip.play()

                    # Zero Bet
                    if zero_rect.collidepoint(mouse_pos):
                        if balance >= active_chip_wager:
                            player_bets["NUMBER:0"] = player_bets.get("NUMBER:0", 0) + active_chip_wager
                            balance -= active_chip_wager
                            snd_chip.play()

                    # Number Bets
                    for num, (rect, bet_key) in number_rects.items():
                        if rect.collidepoint(mouse_pos):
                            if balance >= active_chip_wager:
                                player_bets[bet_key] = player_bets.get(bet_key, 0) + active_chip_wager
                                balance -= active_chip_wager
                                snd_chip.play()

                    # Spin Button
                    if spin_btn_rect.collidepoint(mouse_pos):
                        if any(v > 0 for v in player_bets.values()):
                            is_spinning = True
                            ball_settled = False
                            spin_timer = 0
                            wheel_speed = random.uniform(8.0, 11.0)
                            ball_speed = random.uniform(-22.0, -26.0)
                            win_message = "Rien ne va plus! No more bets..."
                        else:
                            win_message = "❌ PLACE AT LEAST ONE CHIP ON FELT BEFORE SPINNING!"

        # ============================================================
        #                MECHANICAL WHEEL PHYSICS ENGINE
        # ============================================================

        if is_spinning:
            spin_timer += 1

            wheel_speed *= math.pow(0.982, dt)
            ball_speed *= math.pow(0.983, dt)

            wheel_angle += wheel_speed * dt
            ball_angle += ball_speed * dt

            if (
                not ball_settled
                and spin_timer % max(2, int(abs(ball_speed // 1.2))) == 0
                and abs(ball_speed) > 1.0
            ):
                snd_ball_click.play()

            if not ball_settled and abs(ball_speed) < (wheel_speed + 0.3):
                ball_settled = True
                ball_relative_offset = (ball_angle - wheel_angle) % 360

            if ball_settled:
                ball_angle = wheel_angle + ball_relative_offset
                ball_speed = wheel_speed

            if wheel_speed < 0.01:
                is_spinning = False
                wheel_speed = 0
                ball_speed = 0

                seg_arc = 360.0 / len(ROULETTE_NUMBERS)
                final_ball_deg = ball_angle % 360
                final_wheel_deg = wheel_angle % 360

                offset_from_zero = (final_ball_deg - final_wheel_deg) % 360
                ball_relative_index = int((offset_from_zero / seg_arc) + 0.5) % len(ROULETTE_NUMBERS)
                resolved_index = ball_relative_index

                winning_num, winning_color = ROULETTE_NUMBERS[resolved_index]
                total_won, details = evaluate_all_wagers(winning_num, winning_color, player_bets)

                balance += total_won
                player_bets.clear()

                if total_won > 0:
                    win_message = f"🎉 WIN! Result: {winning_num} {winning_color}. Matches: {details} +${total_won}"
                    snd_win.play()
                else:
                    win_message = f"😢 Result: {winning_num} {winning_color}. No matched chips. Table cleared."
                    snd_lose.play()

        # ============================================================
        #                    TABLE BACKGROUND
        # ============================================================

        screen.fill(MAHOGANY)
        pygame.draw.rect(screen, WOOD_LIGHT, (10, 10, WIDTH - 20, HEIGHT - 20), 10)
        pygame.draw.rect(screen, FELT_GREEN, (20, 20, WIDTH - 40, HEIGHT - 40))

        # ========================================================
        #   1. RENDER GRAPHICAL REVOLVING WHEEL (SLIGHTLY LARGER)
        # ========================================================

        w_cx, w_cy = 205, 255
        w_rad = 160  # Increased from 145px to 160px for a bolder look

        pygame.draw.circle(screen, CHARCOAL, (w_cx, w_cy), w_rad + 4)
        pygame.draw.circle(screen, WOOD_LIGHT, (w_cx, w_cy), w_rad)
        pygame.draw.circle(screen, CHARCOAL, (w_cx, w_cy), w_rad - 2)

        seg_arc = 360.0 / len(ROULETTE_NUMBERS)

        for idx, (num, color) in enumerate(ROULETTE_NUMBERS):
            current_deg = idx * seg_arc + wheel_angle
            start_rad = math.radians(current_deg - seg_arc / 2)
            end_rad = math.radians(current_deg + seg_arc / 2)

            px1 = w_cx + math.cos(start_rad) * w_rad
            py1 = w_cy + math.sin(start_rad) * w_rad
            px2 = w_cx + math.cos(end_rad) * w_rad
            py2 = w_cy + math.sin(end_rad) * w_rad

            px3 = w_cx + math.cos(end_rad) * (w_rad - 22)
            py3 = w_cy + math.sin(end_rad) * (w_rad - 22)
            px4 = w_cx + math.cos(start_rad) * (w_rad - 22)
            py4 = w_cy + math.sin(start_rad) * (w_rad - 22)

            poly_color = BRIGHT_RED if color == "RED" else CHARCOAL if color == "BLACK" else FELT_GREEN

            pygame.draw.polygon(screen, poly_color, [(px1, py1), (px2, py2), (px3, py3), (px4, py4)])
            pygame.draw.polygon(screen, GOLD_SHADOW, [(px1, py1), (px2, py2), (px3, py3), (px4, py4)], 1)

            text_deg = current_deg % 360
            text_rad = math.radians(text_deg)
            tx = w_cx + math.cos(text_rad) * (w_rad - 11)
            ty = w_cy + math.sin(text_rad) * (w_rad - 11)

            n_surf = wheel_font.render(str(num), True, CREAM_WHITE)
            n_surf = pygame.transform.rotate(n_surf, -text_deg - 90)
            screen.blit(n_surf, (tx - n_surf.get_width() // 2, ty - n_surf.get_height() // 2))

        pygame.draw.circle(screen, CHARCOAL, (w_cx, w_cy), w_rad - 22)
        pygame.draw.circle(screen, WOOD_LIGHT, (w_cx, w_cy), w_rad - 24)
        pygame.draw.circle(screen, CHARCOAL, (w_cx, w_cy), w_rad - 40, 2)

        pygame.draw.circle(screen, GOLD_SHADOW, (w_cx, w_cy), 28)
        pygame.draw.circle(screen, VINTAGE_GOLD, (w_cx, w_cy), 24)
        pygame.draw.circle(screen, CHARCOAL, (w_cx, w_cy), 8)

        ball_orbit = w_rad - 10 if is_spinning and not ball_settled else w_rad - 31
        bx = w_cx + math.cos(math.radians(ball_angle)) * ball_orbit
        by = w_cy + math.sin(math.radians(ball_angle)) * ball_orbit

        pygame.draw.circle(screen, WHITE_GLINT, (int(bx), int(by)), 6)
        pygame.draw.circle(screen, CHROME_SHADOW, (int(bx), int(by)), 6, 1)

        pygame.draw.polygon(
            screen,
            VINTAGE_GOLD,
            [(w_cx, w_cy - w_rad), (w_cx - 7, w_cy - w_rad - 11), (w_cx + 7, w_cy - w_rad - 11)]
        )

        # ========================================================
        #          2. RENDER THE INTEGRATED BETTING FELT
        # ========================================================

        # Zero Box
        z_rect = zero_rect
        z_val = player_bets.get("NUMBER:0", 0)

        pygame.draw.rect(screen, FELT_GREEN, z_rect)
        pygame.draw.rect(screen, CREAM_WHITE, z_rect, 1)
        z_txt = grid_font.render("0", True, CREAM_WHITE)
        screen.blit(z_txt, (z_rect.centerx - z_txt.get_width() // 2, z_rect.centery - z_txt.get_height() // 2))

        if z_val > 0:
            draw_chip_stack(screen, z_rect, z_val)

        # Numbers
        for num, (rect, bet_key) in number_rects.items():
            n_val = player_bets.get(bet_key, 0)
            box_color = BRIGHT_RED if NUMBER_COLORS[num] == "RED" else CHARCOAL

            pygame.draw.rect(screen, box_color, rect)
            pygame.draw.rect(screen, CREAM_WHITE, rect, 1)

            n_txt = grid_font.render(str(num), True, CREAM_WHITE)
            screen.blit(n_txt, (rect.centerx - n_txt.get_width() // 2, rect.centery - n_txt.get_height() // 2))

            if n_val > 0:
                draw_chip_stack(screen, rect, n_val)

        # Outside & Dozens Bets
        for label, (rect, bet_key) in outside_bet_rects.items():
            out_val = player_bets.get(bet_key, 0)
            box_color = BRIGHT_RED if label == "RED" else CHARCOAL if label == "BLACK" else FELT_GREEN

            pygame.draw.rect(screen, box_color, rect)
            pygame.draw.rect(screen, CREAM_WHITE, rect, 1)

            o_txt = ui_font.render(label, True, CREAM_WHITE)
            screen.blit(o_txt, (rect.centerx - o_txt.get_width() // 2, rect.centery - o_txt.get_height() // 2))

            if out_val > 0:
                draw_chip_stack(screen, rect, out_val)

        # Outer felt outline border
        felt_outline = pygame.Rect(start_grid_x - 45, start_grid_y, grid_total_width + 45, grid_h * 5)
        pygame.draw.rect(screen, CREAM_WHITE, felt_outline, 2)

        # ========================================================
        #          3. RENDER EXPANDED CHIP RACK & CONTROLS
        # ========================================================

        # Chip Selector Panel
        for val, rect, col_bg, col_str in chip_selections:
            is_sel_chip = active_chip_wager == val
            pygame.draw.circle(screen, VINTAGE_GOLD if is_sel_chip else CHARCOAL, rect.center, 22)
            pygame.draw.circle(screen, col_bg, rect.center, 19)

            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                sx = rect.centerx + math.cos(rad) * 14
                sy = rect.centery + math.sin(rad) * 14
                pygame.draw.circle(screen, col_str, (int(sx), int(sy)), 2)

            pygame.draw.circle(screen, CREAM_WHITE, rect.center, 12)

            display_str = str(val) if val < 1000 else f"{val // 1000}k"
            val_txt = chip_num_font.render(f"${display_str}", True, CHARCOAL)
            screen.blit(val_txt, (rect.centerx - val_txt.get_width() // 2, rect.centery - val_txt.get_height() // 2))

        # Bankroll HUD Box
        pygame.draw.rect(screen, CHARCOAL, bankroll_rect, 0, 4)
        pygame.draw.rect(screen, VINTAGE_GOLD, bankroll_rect, 1, 4)

        bal_txt = label_font.render(f"BANKROLL: ${balance}", True, CREAM_WHITE)
        chip_txt = label_font.render(f"ACTIVE CHIP: ${active_chip_wager}", True, VINTAGE_GOLD)

        screen.blit(bal_txt, (bankroll_rect.x + 10, bankroll_rect.y + 6))
        screen.blit(chip_txt, (bankroll_rect.x + 10, bankroll_rect.y + 24))

        # Action Buttons
        for btn_rect, label, bg in [(clear_btn_rect, "CLEAR", CHARCOAL), (spin_btn_rect, "SPIN WHEEL", BRIGHT_RED)]:
            pygame.draw.rect(screen, bg, btn_rect, 0, 4)
            pygame.draw.rect(screen, CREAM_WHITE, btn_rect, 1, 4)

            b_txt = label_font.render(label, True, CREAM_WHITE)
            screen.blit(b_txt, (btn_rect.centerx - b_txt.get_width() // 2, btn_rect.centery - b_txt.get_height() // 2))

        # ========================================================
        #                  BOTTOM MESSAGE BANNER
        # ========================================================

        pygame.draw.rect(screen, CHARCOAL, (40, 560, WIDTH - 80, 40), 0, 4)
        pygame.draw.rect(screen, VINTAGE_GOLD, (40, 560, WIDTH - 80, 40), 1, 4)

        msg_color = (
            VINTAGE_GOLD if ("WIN" in win_message or "CHOOSE" in win_message)
            else BRIGHT_RED if "❌" in win_message
            else CREAM_WHITE
        )

        msg_surf = ui_font.render(win_message, True, msg_color)
        screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, 570))

        _hint_surf = _lobby_hint_font.render("ESC: Return to Lobby", True, (230, 200, 140))
        screen.blit(_hint_surf, (10, HEIGHT - 22))
        pygame.display.flip()
    return balance
