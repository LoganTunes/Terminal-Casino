import asyncio
import pygame
import random
import sys
import array
import math

# ============================================================
#       CLASSIC VEGAS CASINO MATH & GAME LOGIC
# ============================================================

def evaluate_craps_wagers(die1, die2, point, active_bets, come_points, come_points_r, dont_come_points, dont_come_points_r):
    total_dice = die1 + die2
    is_hard = (die1 == die2)
    payout = 0
    new_point = point
    messages = []
    round_resolved = False

    # 1. Pass Line (combines left/right bets)
    pass_amt = active_bets.get("PASS", 0) + active_bets.get("PASS_R", 0)
    if pass_amt > 0:
        if point == 0:
            if total_dice in (7, 11):
                payout += pass_amt * 2
                messages.append(f"Pass Line Win! (+${pass_amt * 2})")
                active_bets["PASS"] = 0
                active_bets["PASS_R"] = 0
                round_resolved = True
            elif total_dice in (2, 3, 12):
                messages.append(f"Pass Line Craps Out! (-${pass_amt})")
                active_bets["PASS"] = 0
                active_bets["PASS_R"] = 0
                round_resolved = True
            else:
                new_point = total_dice
                messages.append(f"Point set to {new_point}.")
        else:
            if total_dice == point:
                payout += pass_amt * 2
                messages.append(f"Pass Line Hit Point {point}! (+${pass_amt * 2})")
                active_bets["PASS"] = 0
                active_bets["PASS_R"] = 0
                new_point = 0
                round_resolved = True
            elif total_dice == 7:
                messages.append(f"Pass Line Seven-Out! (-${pass_amt})")
                active_bets["PASS"] = 0
                active_bets["PASS_R"] = 0
                new_point = 0
                round_resolved = True
    else:
        # No pass-line money riding, but the point still needs to be
        # established/resolved for the puck and for every other bet type.
        if point == 0:
            if total_dice not in (2, 3, 7, 11, 12):
                new_point = total_dice
        else:
            if total_dice == point or total_dice == 7:
                new_point = 0

    # 2. Come Bets (each is its own "mini pass line" that starts on the roll it's placed)
    for come_key, points_dict in (("COME", come_points), ("COME_R", come_points_r)):
        fresh_amt = active_bets.get(come_key, 0)
        if fresh_amt > 0:
            if total_dice in (7, 11):
                payout += fresh_amt * 2
                messages.append(f"Come Win! (+${fresh_amt * 2})")
                active_bets[come_key] = 0
            elif total_dice in (2, 3, 12):
                messages.append(f"Come Craps Out! (-${fresh_amt})")
                active_bets[come_key] = 0
            else:
                points_dict[total_dice] = points_dict.get(total_dice, 0) + fresh_amt
                messages.append(f"Come bet moves to {total_dice}.")
                active_bets[come_key] = 0

        # Resolve come bets that already moved to a number in a prior roll
        if total_dice == 7:
            for num, amt in points_dict.items():
                messages.append(f"Come {num} Seven-Out! (-${amt})")
            points_dict.clear()
        elif total_dice in points_dict:
            amt = points_dict.pop(total_dice)
            payout += amt * 2
            messages.append(f"Come {total_dice} Hit! (+${amt * 2})")

    # 3. Don't Come Bets (mirror of Come, using Don't Pass style win/lose rules)
    for dc_key, dc_points_dict in (("DONT_COME", dont_come_points), ("DONT_COME_R", dont_come_points_r)):
        fresh_dc_amt = active_bets.get(dc_key, 0)
        if fresh_dc_amt > 0:
            if total_dice in (2, 3):
                payout += fresh_dc_amt * 2
                messages.append(f"Don't Come Win! (+${fresh_dc_amt * 2})")
                active_bets[dc_key] = 0
            elif total_dice == 12:
                payout += fresh_dc_amt
                messages.append("Don't Come Push (Bar 12)!")
                active_bets[dc_key] = 0
            elif total_dice in (7, 11):
                messages.append(f"Don't Come Loss! (-${fresh_dc_amt})")
                active_bets[dc_key] = 0
            else:
                dc_points_dict[total_dice] = dc_points_dict.get(total_dice, 0) + fresh_dc_amt
                messages.append(f"Don't Come bet moves to {total_dice}.")
                active_bets[dc_key] = 0

        # Resolve don't come bets that already moved to a number
        if total_dice == 7:
            for num, amt in dc_points_dict.items():
                payout += amt * 2
                messages.append(f"Don't Come {num} Win on 7! (+${amt * 2})")
            dc_points_dict.clear()
        elif total_dice in dc_points_dict:
            amt = dc_points_dict.pop(total_dice)
            messages.append(f"Don't Come {total_dice} Loss! (-${amt})")

    # 4. Don't Pass
    dp_amt = active_bets.get("DONT_PASS", 0) + active_bets.get("DONT_PASS_R", 0)
    if dp_amt > 0:
        if point == 0:
            if total_dice in (2, 3):
                payout += dp_amt * 2
                messages.append(f"Don't Pass Win! (+${dp_amt * 2})")
                active_bets["DONT_PASS"] = 0
                active_bets["DONT_PASS_R"] = 0
            elif total_dice == 12:
                payout += dp_amt
                messages.append("Don't Pass Push (Bar 12)!")
                active_bets["DONT_PASS"] = 0
                active_bets["DONT_PASS_R"] = 0
            elif total_dice in (7, 11):
                messages.append(f"Don't Pass Loss! (-${dp_amt})")
                active_bets["DONT_PASS"] = 0
                active_bets["DONT_PASS_R"] = 0
        else:
            if total_dice == 7:
                payout += dp_amt * 2
                messages.append(f"Don't Pass Win on 7! (+${dp_amt * 2})")
                active_bets["DONT_PASS"] = 0
                active_bets["DONT_PASS_R"] = 0
            elif total_dice == point:
                messages.append(f"Don't Pass Loss! (-${dp_amt})")
                active_bets["DONT_PASS"] = 0
                active_bets["DONT_PASS_R"] = 0

    # 5. Place Bets
    place_odds = {4: (9, 5), 5: (7, 5), 6: (7, 6), 8: (7, 6), 9: (7, 5), 10: (9, 5)}
    for num, (num_pay, num_bet) in place_odds.items():
        p_amt = active_bets.get(f"PLACE_{num}", 0) + active_bets.get(f"PLACE_{num}_R", 0)
        if p_amt > 0:
            if total_dice == num:
                win_val = p_amt + int(p_amt * (num_pay / num_bet))
                payout += win_val
                messages.append(f"Place {num} Hit! (+${win_val})")
                active_bets[f"PLACE_{num}"] = 0
                active_bets[f"PLACE_{num}_R"] = 0
            elif total_dice == 7:
                messages.append(f"Place {num} Lost. (-${p_amt})")
                active_bets[f"PLACE_{num}"] = 0
                active_bets[f"PLACE_{num}_R"] = 0

    # 6. Field Bet
    field_amt = active_bets.get("FIELD", 0) + active_bets.get("FIELD_R", 0)
    if field_amt > 0:
        if total_dice in (3, 4, 9, 10, 11):
            payout += field_amt * 2
            messages.append(f"Field Win! (+${field_amt * 2})")
        elif total_dice == 2:
            payout += field_amt * 3
            messages.append(f"Field Double Win! (+${field_amt * 3})")
        elif total_dice == 12:
            payout += field_amt * 4
            messages.append(f"Field Triple Win! (+${field_amt * 4})")
        else:
            messages.append(f"Field Loss. (-${field_amt})")
        active_bets["FIELD"] = 0
        active_bets["FIELD_R"] = 0

    # 7. Big 6 & Big 8
    for b_num in [6, 8]:
        b_amt = active_bets.get(f"BIG_{b_num}", 0) + active_bets.get(f"BIG_{b_num}_R", 0)
        if b_amt > 0:
            if total_dice == b_num:
                payout += b_amt * 2
                messages.append(f"Big {b_num} Hit! (+${b_amt * 2})")
                active_bets[f"BIG_{b_num}"] = 0
                active_bets[f"BIG_{b_num}_R"] = 0
            elif total_dice == 7:
                messages.append(f"Big {b_num} Lost. (-${b_amt})")
                active_bets[f"BIG_{b_num}"] = 0
                active_bets[f"BIG_{b_num}_R"] = 0

    # 8. Center Proposition Bets
    prop_specs = {
        "SEVEN": ([7], 5),
        "HARD_8": ([8], 10, True),
        "HARD_6": ([6], 10, True),
        "HARD_4": ([4], 8, True),
        "HARD_10": ([10], 8, True),
        "CRAPS": ([2, 3, 12], 8)
    }
    for prop_key, spec in prop_specs.items():
        pr_amt = active_bets.get(prop_key, 0)
        if pr_amt > 0:
            targets = spec[0]
            mult = spec[1]
            needs_hard = spec[2] if len(spec) > 2 else False

            if total_dice in targets and (not needs_hard or is_hard):
                win_val = pr_amt * mult
                payout += win_val
                messages.append(f"{prop_key.replace('_', ' ')} Win! (+${win_val})")
                active_bets[prop_key] = 0
            elif total_dice == 7 or (needs_hard and total_dice in targets and not is_hard):
                messages.append(f"{prop_key.replace('_', ' ')} Loss. (-${pr_amt})")
                active_bets[prop_key] = 0

    msg_str = ", ".join(messages) if messages else f"Rolled {total_dice}."
    return payout, new_point, msg_str, round_resolved


# ============================================================
#              PYGAME INITIALIZATION & SOUNDS
# ============================================================

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

WIDTH, HEIGHT = 1200, 780
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Double-Sided Classic Vegas Felt Craps")
clock = pygame.time.Clock()
_lobby_hint_font = pygame.font.SysFont(None, 20)
_GAME_TITLE = ("Double-Sided Classic Vegas Felt Craps")

def generate_synth_sound(freq_list, duration_ms, wave_type="triangle", volume=0.3):
    sample_rate = 22050
    total_samples = int(sample_rate * (duration_ms / 1000.0))
    buffer = array.array("h", [0] * total_samples)
    samples_per_freq = total_samples // len(freq_list)

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

snd_wall_thud = generate_synth_sound([160, 90], 50, wave_type="triangle", volume=0.4)
snd_dice_bounce = generate_synth_sound([220, 140], 30, wave_type="triangle", volume=0.2)
snd_win = generate_synth_sound([440, 554, 659, 880], 300, wave_type="square", volume=0.15)
snd_lose = generate_synth_sound([220, 180], 250, wave_type="triangle", volume=0.2)
snd_chip = generate_synth_sound([600, 900], 30, wave_type="triangle", volume=0.2)


# ============================================================
#                      COLOR PALETTE
# ============================================================

CASINO_GREEN = (18, 120, 60)
MAHOGANY = (30, 10, 5)
WOOD_RAIL = (50, 20, 10)
CREAM_WHITE = (245, 242, 225)
BRIGHT_YELLOW = (255, 215, 0)
CHARCOAL = (20, 20, 20)
BRIGHT_RED = (210, 30, 30)


# ============================================================
#                            FONTS
# ============================================================

font_options = ["georgia", "timesnewroman", "arial"]
ui_font = pygame.font.SysFont(font_options, 19, bold=True)
label_font = pygame.font.SysFont(font_options, 11, bold=True)
felt_font = pygame.font.SysFont("georgia", 14, bold=True)
felt_large = pygame.font.SysFont("georgia", 20, bold=True)
big_num_font = pygame.font.SysFont("georgia", 24, bold=True)
chip_num_font = pygame.font.SysFont("arial", 11, bold=True)


# ============================================================
#                         LIVE STATES
# ============================================================


async def run_craps(balance):
    global screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(_GAME_TITLE)
    running = True
    active_chip_wager = 10
    current_point = 0
    come_points = {}
    come_points_r = {}
    dont_come_points = {}
    dont_come_points_r = {}
    win_message = "PLACE YOUR BETS AND CLICK SHOOT DICE"

    ALL_BET_KEYS = [
        "PASS", "DONT_PASS", "COME", "DONT_COME", "FIELD",
        "PLACE_4", "PLACE_5", "PLACE_6", "PLACE_8", "PLACE_9", "PLACE_10",
        "BIG_6", "BIG_8",
        "PASS_R", "DONT_PASS_R", "COME_R", "DONT_COME_R", "FIELD_R",
        "PLACE_4_R", "PLACE_5_R", "PLACE_6_R", "PLACE_8_R", "PLACE_9_R", "PLACE_10_R",
        "BIG_6_R", "BIG_8_R",
        "SEVEN", "HARD_8", "HARD_6", "HARD_4", "HARD_10", "CRAPS"
    ]
    player_bets = {k: 0 for k in ALL_BET_KEYS}

    is_rolling = False
    roll_timer = 0
    dice_size = 28

    TABLE_RECT = pygame.Rect(45, 75, 1110, 510)

    dice_state = [
        [70, 388, 0, 0.0, 0.0, 0.0, 6, 0, 0, 0, False],
        [70, 438, 0, 0.0, 0.0, 0.0, 6, 0, 0, 0, False]
    ]


    # ============================================================
    #           AUTHENTIC DOUBLE-SIDED FELT BET ZONES
    # ============================================================

    # --- LEFT SIDE TABLE ---
    place_w_l = 48
    place_h_l = 75
    p_start_x_l = 175
    p_start_y_l = 163

    bet_zones = {
        "PLACE_10": (pygame.Rect(p_start_x_l, p_start_y_l, place_w_l, place_h_l), "10"),
        "PLACE_9":  (pygame.Rect(p_start_x_l + place_w_l, p_start_y_l, place_w_l, place_h_l), "NINE"),
        "PLACE_8":  (pygame.Rect(p_start_x_l + place_w_l*2, p_start_y_l, place_w_l, place_h_l), "8"),
        "PLACE_6":  (pygame.Rect(p_start_x_l + place_w_l*3, p_start_y_l, place_w_l, place_h_l), "SIX"),
        "PLACE_5":  (pygame.Rect(p_start_x_l + place_w_l*4, p_start_y_l, place_w_l, place_h_l), "5"),
        "PLACE_4":  (pygame.Rect(p_start_x_l + place_w_l*5, p_start_y_l, place_w_l, place_h_l), "4"),

        "COME":      (pygame.Rect(175, 238, 288, 80), "C O M E"),
        "DONT_COME": (pygame.Rect(125, 163, 50, 200), "Don't come bar"),
        "FIELD":     (pygame.Rect(175, 318, 288, 90), "FIELD"),
        "DONT_PASS": (pygame.Rect(175, 408, 288, 45), "Don't pass bar"),

        "BIG_6": (pygame.Rect(125, 408, 50, 45), "6"),
        "BIG_8": (pygame.Rect(125, 363, 50, 45), "8"),

        # --- CENTER PROPOSITION BOX (CENTERED) ---
        "SEVEN":   (pygame.Rect(495, 173, 210, 45), "5 for 1  SEVEN"),
        "HARD_8":  (pygame.Rect(495, 223, 210, 38), "HARD 8 (10 for 1)"),
        "HARD_6":  (pygame.Rect(495, 266, 210, 38), "HARD 6 (10 for 1)"),
        "HARD_4":  (pygame.Rect(495, 309, 210, 38), "HARD 4 (8 for 1)"),
        "HARD_10": (pygame.Rect(495, 352, 210, 38), "HARD 10 (8 for 1)"),
        "CRAPS":   (pygame.Rect(495, 395, 210, 45), "CRAPS  8 for 1"),

        # --- RIGHT SIDE TABLE ---
        "PLACE_4_R":  (pygame.Rect(737, p_start_y_l, place_w_l, place_h_l), "4"),
        "PLACE_5_R":  (pygame.Rect(737 + place_w_l, p_start_y_l, place_w_l, place_h_l), "5"),
        "PLACE_6_R":  (pygame.Rect(737 + place_w_l*2, p_start_y_l, place_w_l, place_h_l), "SIX"),
        "PLACE_8_R":  (pygame.Rect(737 + place_w_l*3, p_start_y_l, place_w_l, place_h_l), "8"),
        "PLACE_9_R":  (pygame.Rect(737 + place_w_l*4, p_start_y_l, place_w_l, place_h_l), "NINE"),
        "PLACE_10_R": (pygame.Rect(737 + place_w_l*5, p_start_y_l, place_w_l, place_h_l), "10"),

        "COME_R":      (pygame.Rect(737, 238, 288, 80), "C O M E"),
        "DONT_COME_R": (pygame.Rect(1025, 163, 50, 200), "Don't come bar"),
        "FIELD_R":     (pygame.Rect(737, 318, 288, 90), "FIELD"),
        "DONT_PASS_R": (pygame.Rect(737, 408, 288, 45), "Don't pass bar"),

        "BIG_6_R": (pygame.Rect(1025, 408, 50, 45), "6"),
        "BIG_8_R": (pygame.Rect(1025, 363, 50, 45), "8")
    }

    throw_btn_rect = pygame.Rect(920, 620, 180, 52)
    clear_btn_rect = pygame.Rect(720, 620, 180, 52)

    chip_selections = [
        (10, pygame.Rect(370, 625, 48, 48), (240, 240, 240), (40, 40, 40)),
        (50, pygame.Rect(430, 625, 48, 48), (180, 30, 30), (240, 240, 240)),
        (100, pygame.Rect(490, 625, 48, 48), (30, 80, 180), (240, 240, 240)),
        (250, pygame.Rect(550, 625, 48, 48), (30, 130, 60), (230, 190, 90)),
        (1000, pygame.Rect(610, 625, 48, 48), (30, 30, 30), (230, 190, 90))
    ]


    # ============================================================
    #                      DRAWING HELPERS
    # ============================================================

    def draw_chip_stack(surface, rect, text_val):
        bg_color = (240, 240, 240)
        stripe_color = (40, 40, 40)
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


    def draw_clean_die(surface, x, y, z, val, angle, size=28):
        dx, dy = int(x), int(y - z)

        shadow_surf = pygame.Surface((size + 4, size // 2 + 2), pygame.SRCALPHA)
        shadow_alpha = max(20, 100 - int(z * 2.5))
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha), (0, 0, size + 4, size // 2 + 2))
        surface.blit(shadow_surf, (dx - 2, int(y) + size - 6))

        die_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(die_surf, CREAM_WHITE, (0, 0, size, size), 0, 4)
        pygame.draw.rect(die_surf, CHARCOAL, (0, 0, size, size), 1, 4)

        p_rad = 3
        mid = size // 2
        l, r = int(size * 0.28), int(size * 0.72)
        t, b = int(size * 0.28), int(size * 0.72)

        pips_map = {
            1: [(mid, mid)],
            2: [(l, t), (r, b)],
            3: [(l, t), (mid, mid), (r, b)],
            4: [(l, t), (r, t), (l, b), (r, b)],
            5: [(l, t), (r, t), (mid, mid), (l, b), (r, b)],
            6: [(l, t), (r, t), (l, mid), (r, mid), (l, b), (r, b)]
        }

        for px, py in pips_map.get(val, []):
            pygame.draw.circle(die_surf, BRIGHT_RED if val == 1 else CHARCOAL, (px, py), p_rad)

        rotated_surf = pygame.transform.rotate(die_surf, angle)
        rot_rect = rotated_surf.get_rect(center=(dx + mid, dy + mid))
        surface.blit(rotated_surf, rot_rect.topleft)


    # ============================================================
    #                      MAIN GAME LOOP
    # ============================================================

    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                if not is_rolling:
                    for val, rect, c1, c2 in chip_selections:
                        if rect.collidepoint(mouse_pos):
                            active_chip_wager = val
                            snd_chip.play()

                    if clear_btn_rect.collidepoint(mouse_pos):
                        balance += (sum(player_bets.values()) + sum(come_points.values()) + sum(come_points_r.values())
                                    + sum(dont_come_points.values()) + sum(dont_come_points_r.values()))
                        player_bets = {k: 0 for k in ALL_BET_KEYS}
                        come_points.clear()
                        come_points_r.clear()
                        dont_come_points.clear()
                        dont_come_points_r.clear()
                        snd_chip.play()

                    # Left Pass Line Region
                    pass_l_rect = pygame.Rect(75, 163, 50, 290)
                    pass_b_rect = pygame.Rect(75, 453, 388, 45)
                    # Right Pass Line Region
                    pass_r_l_rect = pygame.Rect(1075, 163, 50, 290)
                    pass_r_b_rect = pygame.Rect(737, 453, 388, 45)

                    if pass_l_rect.collidepoint(mouse_pos) or pass_b_rect.collidepoint(mouse_pos):
                        if balance >= active_chip_wager:
                            player_bets["PASS"] += active_chip_wager
                            balance -= active_chip_wager
                            snd_chip.play()

                    elif pass_r_l_rect.collidepoint(mouse_pos) or pass_r_b_rect.collidepoint(mouse_pos):
                        if balance >= active_chip_wager:
                            player_bets["PASS_R"] += active_chip_wager
                            balance -= active_chip_wager
                            snd_chip.play()

                    else:
                        for key, (rect, label) in bet_zones.items():
                            if rect.collidepoint(mouse_pos):
                                if key in ("COME", "COME_R", "DONT_COME", "DONT_COME_R") and current_point == 0:
                                    win_message = "❌ Come/Don't Come only allowed once the point is ON!"
                                elif balance >= active_chip_wager:
                                    player_bets[key] += active_chip_wager
                                    balance -= active_chip_wager
                                    snd_chip.play()

                    if throw_btn_rect.collidepoint(mouse_pos):
                        if sum(player_bets.values()) > 0:
                            is_rolling = True
                            roll_timer = 0
                            win_message = "Shooter throws toward the back wall!"

                            dice_state[0] = [
                                70, 388, 25,
                                random.uniform(22.0, 26.0),
                                random.uniform(-1.5, 1.5),
                                random.uniform(6.0, 9.0),
                                random.randint(1, 6),
                                0,
                                random.uniform(20.0, 35.0),
                                0,
                                False
                            ]
                            dice_state[1] = [
                                70, 438, 25,
                                random.uniform(20.0, 24.0),
                                random.uniform(-1.0, 2.0),
                                random.uniform(6.0, 9.0),
                                random.randint(1, 6),
                                0,
                                random.uniform(20.0, 35.0),
                                0,
                                False
                            ]
                        else:
                            win_message = "❌ PLACE A BET ON THE FELT FIRST!"

        # --- REALISTIC CASINO WALL-BOUNCE PHYSICS ---
        if is_rolling:
            roll_timer += 1
            gravity = 0.75

            for d in dice_state:
                d[0] += d[3]
                d[1] += d[4]
                d[2] += d[5]
                d[5] -= gravity

                d[3] *= 0.985
                d[4] *= 0.985

                d[7] = (d[7] + d[8]) % 360

                if d[9] > 0:
                    d[9] -= 1

                if (abs(d[3]) + abs(d[4]) + abs(d[5])) > 0.8 and roll_timer % 2 == 0:
                    d[6] = random.randint(1, 6)

                right_wall = TABLE_RECT.right - dice_size - 20
                if d[0] >= right_wall and not d[10]:
                    d[0] = right_wall
                    d[3] = -d[3] * random.uniform(0.35, 0.50)
                    d[4] += random.uniform(-4.0, 4.0)
                    d[8] = random.uniform(15.0, 30.0)
                    d[10] = True
                    snd_wall_thud.play()

                if d[2] <= 0:
                    d[2] = 0
                    if abs(d[5]) > 1.2:
                        d[5] = -d[5] * 0.4
                        d[3] *= 0.75
                        d[4] *= 0.75
                        d[8] *= 0.6
                        if d[9] == 0:
                            snd_dice_bounce.play()
                            d[9] = 6
                    else:
                        d[5] = 0
                        d[3] *= 0.85
                        d[4] *= 0.85
                        d[8] *= 0.7

                if d[1] <= TABLE_RECT.top + 20 or d[1] >= TABLE_RECT.bottom - dice_size - 20:
                    d[4] = -d[4] * 0.5
                    d[1] = max(TABLE_RECT.top + 20, min(d[1], TABLE_RECT.bottom - dice_size - 20))

            speed1 = math.hypot(dice_state[0][3], dice_state[0][4]) + abs(dice_state[0][5])
            speed2 = math.hypot(dice_state[1][3], dice_state[1][4]) + abs(dice_state[1][5])

            if (speed1 < 0.25 and speed2 < 0.25 and dice_state[0][2] == 0 and dice_state[1][2] == 0) or roll_timer > 90:
                is_rolling = False
                for d in dice_state:
                    d[2] = 0; d[3] = 0; d[4] = 0; d[5] = 0; d[7] = 0; d[8] = 0

                v1, v2 = dice_state[0][6], dice_state[1][6]
                total_won, current_point, outcome_text, round_resolved = evaluate_craps_wagers(v1, v2, current_point, player_bets, come_points, come_points_r, dont_come_points, dont_come_points_r)
                balance += total_won

                if total_won > 0:
                    win_message = f"Result: {v1}+{v2}={v1+v2}. {outcome_text}"
                    snd_win.play()
                else:
                    win_message = f"Result: {v1}+{v2}={v1+v2}. {outcome_text}"
                    if any(w in outcome_text for w in ["Loss", "Seven-Out", "Craps Out", "Lost"]):
                        snd_lose.play()

        # --- RENDERING CLASSIC FELT LAYOUT ---
        screen.fill(MAHOGANY)

        # Leather Outer Rail
        pygame.draw.rect(screen, WOOD_RAIL, (20, 15, WIDTH - 40, HEIGHT - 30), 0, 22)
        pygame.draw.rect(screen, CHARCOAL, (20, 15, WIDTH - 40, HEIGHT - 30), 4, 22)

        # Deep Green Felt Container
        pygame.draw.rect(screen, CASINO_GREEN, TABLE_RECT, 0, 14)

        # --- DRAW LEFT SIDE GRID ---
        pygame.draw.rect(screen, CREAM_WHITE, pygame.Rect(175, 163, 288, 290), 2)
        dc_rect_l = pygame.Rect(125, 163, 50, 200)
        pygame.draw.rect(screen, CREAM_WHITE, dc_rect_l, 2)
        dc_txt_l = label_font.render("Don't come bar", True, BRIGHT_RED)
        dc_txt_l = pygame.transform.rotate(dc_txt_l, 90)
        screen.blit(dc_txt_l, (dc_rect_l.centerx - dc_txt_l.get_width() // 2, dc_rect_l.centery - dc_txt_l.get_height() // 2))

        # --- DRAW RIGHT SIDE GRID ---
        pygame.draw.rect(screen, CREAM_WHITE, pygame.Rect(737, 163, 288, 290), 2)
        dc_rect_r = pygame.Rect(1025, 163, 50, 200)
        pygame.draw.rect(screen, CREAM_WHITE, dc_rect_r, 2)
        dc_txt_r = label_font.render("Don't come bar", True, BRIGHT_RED)
        dc_txt_r = pygame.transform.rotate(dc_txt_r, 270)
        screen.blit(dc_txt_r, (dc_rect_r.centerx - dc_txt_r.get_width() // 2, dc_rect_r.centery - dc_txt_r.get_height() // 2))

        # Place, Come, Field, Don't Pass, Big 6/8 Rendering
        for key, (rect, label) in bet_zones.items():
            if key in ("DONT_COME", "DONT_COME_R"):
                continue  # border + rotated label already drawn in the side-grid section above

            if "PLACE" in key:
                pygame.draw.rect(screen, CREAM_WHITE, rect, 2)
                lbl_surf = big_num_font.render(label, True, CREAM_WHITE) if label.isdigit() else felt_font.render(label, True, CREAM_WHITE)
                if label in ["SIX", "NINE"]:
                    lbl_surf = pygame.transform.rotate(lbl_surf, 90)
                screen.blit(lbl_surf, (rect.centerx - lbl_surf.get_width() // 2, rect.centery - lbl_surf.get_height() // 2))

            elif "COME" in key:
                pygame.draw.rect(screen, CREAM_WHITE, rect, 2)
                c_txt = felt_large.render("COME", True, BRIGHT_YELLOW)
                screen.blit(c_txt, (rect.centerx - c_txt.get_width() // 2, rect.centery - c_txt.get_height() // 2))

            elif "FIELD" in key:
                pygame.draw.rect(screen, CREAM_WHITE, rect, 2)
                f_txt = felt_large.render("FIELD", True, BRIGHT_YELLOW)
                screen.blit(f_txt, (rect.centerx - f_txt.get_width() // 2, rect.bottom - 26))
                f_nums = label_font.render("3   4   9   10   11", True, CREAM_WHITE)
                screen.blit(f_nums, (rect.centerx - f_nums.get_width() // 2, rect.y + 10))

                for cx, val_str in [(rect.x + 38, "2"), (rect.right - 38, "12")]:
                    pygame.draw.circle(screen, BRIGHT_YELLOW, (cx, rect.y + 38), 16)
                    v_txt = label_font.render(val_str, True, CHARCOAL)
                    screen.blit(v_txt, (cx - v_txt.get_width() // 2, rect.y + 38 - v_txt.get_height() // 2))

            elif "DONT_PASS" in key:
                pygame.draw.rect(screen, CREAM_WHITE, rect, 2)
                dp_txt = felt_font.render("Don't pass bar", True, BRIGHT_RED)
                screen.blit(dp_txt, (rect.centerx - dp_txt.get_width() // 2, rect.centery - dp_txt.get_height() // 2))

            elif "BIG_" in key:
                col = BRIGHT_RED if "6" in key else BRIGHT_YELLOW
                pygame.draw.rect(screen, CREAM_WHITE, rect, 2)
                b_surf = big_num_font.render(label, True, col)
                screen.blit(b_surf, (rect.centerx - b_surf.get_width() // 2, rect.centery - b_surf.get_height() // 2))

        # --- LEFT L-SHAPED PASS LINE ---
        pass_pts_l = [(75, 163), (125, 163), (125, 453), (463, 453), (463, 498), (75, 498)]
        pygame.draw.polygon(screen, CREAM_WHITE, pass_pts_l, 2)
        pass_v_l = felt_large.render("PASS LINE", True, CREAM_WHITE)
        pass_v_l = pygame.transform.rotate(pass_v_l, 90)
        screen.blit(pass_v_l, (90, 248))
        pass_h_l = felt_large.render("PASS LINE", True, CREAM_WHITE)
        screen.blit(pass_h_l, (230, 464))

        # --- RIGHT L-SHAPED PASS LINE ---
        pass_pts_r = [(1075, 163), (1125, 163), (1125, 498), (737, 498), (737, 453), (1075, 453)]
        pygame.draw.polygon(screen, CREAM_WHITE, pass_pts_r, 2)
        pass_v_r = felt_large.render("PASS LINE", True, CREAM_WHITE)
        pass_v_r = pygame.transform.rotate(pass_v_r, 270)
        screen.blit(pass_v_r, (1090, 248))
        pass_h_r = felt_large.render("PASS LINE", True, CREAM_WHITE)
        screen.blit(pass_h_r, (880, 464))

        # --- CENTER PROPOSITION BOX (ROUNDED CAPSULE) ---
        prop_box = pygame.Rect(485, 153, 230, 300)
        pygame.draw.rect(screen, CREAM_WHITE, prop_box, 2, border_radius=18)

        for key in ["SEVEN", "HARD_8", "HARD_6", "HARD_4", "HARD_10", "CRAPS"]:
            rect, label = bet_zones[key]
            pygame.draw.rect(screen, CREAM_WHITE, rect, 1)
            col = BRIGHT_YELLOW if key in ["SEVEN", "CRAPS"] else CREAM_WHITE
            pr_txt = label_font.render(label, True, col)
            screen.blit(pr_txt, (rect.centerx - pr_txt.get_width() // 2, rect.centery - pr_txt.get_height() // 2))

        # Render Active Bets
        for key, (rect, label) in bet_zones.items():
            wager_amt = player_bets.get(key, 0)
            if wager_amt > 0:
                draw_chip_stack(screen, rect, wager_amt)

        if player_bets["PASS"] > 0:
            draw_chip_stack(screen, pygame.Rect(75, 453, 388, 45), player_bets["PASS"])
        if player_bets["PASS_R"] > 0:
            draw_chip_stack(screen, pygame.Rect(737, 453, 388, 45), player_bets["PASS_R"])

        # Come bet markers (chips that traveled from the COME box to a point number)
        for num, amt in come_points.items():
            rect = bet_zones[f"PLACE_{num}"][0]
            come_rect = pygame.Rect(rect.x, rect.bottom - 24, rect.width, 24)
            draw_chip_stack(screen, come_rect, amt)
            c_lbl = label_font.render("C", True, BRIGHT_YELLOW)
            screen.blit(c_lbl, (come_rect.x + 2, come_rect.centery - c_lbl.get_height() // 2))
        for num, amt in come_points_r.items():
            rect = bet_zones[f"PLACE_{num}_R"][0]
            come_rect = pygame.Rect(rect.x, rect.bottom - 24, rect.width, 24)
            draw_chip_stack(screen, come_rect, amt)
            c_lbl = label_font.render("C", True, BRIGHT_YELLOW)
            screen.blit(c_lbl, (come_rect.x + 2, come_rect.centery - c_lbl.get_height() // 2))

        # Don't Come point markers (chips that traveled from the DONT_COME box to a number)
        for num, amt in dont_come_points.items():
            rect = bet_zones[f"PLACE_{num}"][0]
            dc_pt_rect = pygame.Rect(rect.x, rect.y, rect.width, 24)
            draw_chip_stack(screen, dc_pt_rect, amt)
            d_lbl = label_font.render("D", True, BRIGHT_RED)
            screen.blit(d_lbl, (dc_pt_rect.x + 2, dc_pt_rect.centery - d_lbl.get_height() // 2))
        for num, amt in dont_come_points_r.items():
            rect = bet_zones[f"PLACE_{num}_R"][0]
            dc_pt_rect = pygame.Rect(rect.x, rect.y, rect.width, 24)
            draw_chip_stack(screen, dc_pt_rect, amt)
            d_lbl = label_font.render("D", True, BRIGHT_RED)
            screen.blit(d_lbl, (dc_pt_rect.x + 2, dc_pt_rect.centery - d_lbl.get_height() // 2))

        # ON/OFF Puck
        puck_radius = 18
        if current_point == 0:
            puck_cx, puck_cy = 100, 193
            puck_color = CHARCOAL
            puck_label = "OFF"
        else:
            point_key = f"PLACE_{current_point}"
            puck_rect = bet_zones[point_key][0]
            puck_cx, puck_cy = puck_rect.centerx, puck_rect.top - 12
            puck_color = BRIGHT_RED
            puck_label = "ON"

        pygame.draw.circle(screen, puck_color, (puck_cx, puck_cy), puck_radius)
        pygame.draw.circle(screen, CREAM_WHITE, (puck_cx, puck_cy), puck_radius, width=2)
        p_txt = label_font.render(puck_label, True, CREAM_WHITE)
        screen.blit(p_txt, (puck_cx - p_txt.get_width() // 2, puck_cy - p_txt.get_height() // 2))

        # Render Dice
        for d in dice_state:
            draw_clean_die(screen, d[0], d[1], d[2], d[6], d[7], size=dice_size)

        # HUD Control Bar
        pygame.draw.rect(screen, CHARCOAL, (50, 605, 290, 80), 0, 8)
        pygame.draw.rect(screen, BRIGHT_YELLOW, (50, 605, 290, 80), 2, 8)
        bal_txt = ui_font.render(f"BANKROLL: ${balance}", True, CREAM_WHITE)
        chip_txt = label_font.render(f"ACTIVE CHIP: ${active_chip_wager}", True, BRIGHT_YELLOW)
        screen.blit(bal_txt, (65, 620))
        screen.blit(chip_txt, (65, 655))

        # Chip Selection Rack
        for val, rect, col_bg, col_str in chip_selections:
            is_sel = (active_chip_wager == val)
            pygame.draw.circle(screen, BRIGHT_YELLOW if is_sel else CHARCOAL, rect.center, 25)
            pygame.draw.circle(screen, col_bg, rect.center, 22)
            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                sx = rect.centerx + math.cos(rad) * 17
                sy = rect.centery + math.sin(rad) * 17
                pygame.draw.circle(screen, col_str, (int(sx), int(sy)), 3)
            pygame.draw.circle(screen, CREAM_WHITE, rect.center, 15)
            display_str = str(val) if val < 1000 else f"{val // 1000}k"
            val_txt = chip_num_font.render(f"${display_str}", True, CHARCOAL)
            screen.blit(val_txt, (rect.centerx - val_txt.get_width() // 2, rect.centery - val_txt.get_height() // 2))

        # Action Buttons
        for btn_rect, label, bg in [(throw_btn_rect, "SHOOT DICE", BRIGHT_RED), (clear_btn_rect, "CLEAR CHIPS", CHARCOAL)]:
            pygame.draw.rect(screen, bg, btn_rect, 0, 8)
            pygame.draw.rect(screen, CREAM_WHITE, btn_rect, 1, 8)
            b_txt = ui_font.render(label, True, CREAM_WHITE)
            screen.blit(b_txt, (btn_rect.centerx - b_txt.get_width() // 2, btn_rect.centery - b_txt.get_height() // 2))

        # Bottom Status Banner
        pygame.draw.rect(screen, CHARCOAL, (50, 705, 1050, 42), 0, 6)
        pygame.draw.rect(screen, BRIGHT_YELLOW, (50, 705, 1050, 42), 2, 6)
        msg_color = BRIGHT_YELLOW if "Win" in win_message or "Hit" in win_message else BRIGHT_RED if "❌" in win_message or "Loss" in win_message or "Lost" in win_message else CREAM_WHITE
        msg_surf = ui_font.render(win_message, True, msg_color)
        screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, 715))

        _hint_surf = _lobby_hint_font.render("ESC: Return to Lobby", True, (230, 200, 140))
        screen.blit(_hint_surf, (10, HEIGHT - 22))
        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(60)
    return balance
