import asyncio
import pygame
import random
import sys
import array
import math

# ============================================================
#       ORIGINAL CASINO MATH ENGINE & GAME LOGIC
# ============================================================

def calculate_keno_winnings(spots_picked, hits_landed, bet_amount):
    """Processes payouts matching vintage electromechanical lounge matrices."""
    if spots_picked == 0 or hits_landed == 0:
        return 0, "No Matches"

    payout_table = {
        1:  {1: 3},
        2:  {1: 1, 2: 12},
        3:  {2: 2, 3: 42},
        4:  {2: 1, 3: 4, 4: 130},
        5:  {3: 3, 4: 26, 5: 700},
        6:  {3: 1, 4: 7, 5: 70, 6: 1600},
        7:  {4: 3, 5: 21, 6: 300, 7: 5000},
        8:  {5: 12, 6: 90, 7: 1500, 8: 15000},
        9:  {5: 6, 6: 44, 7: 330, 8: 4000, 9: 25000},
        10: {5: 3, 6: 22, 7: 130, 8: 1000, 9: 10000, 10: 50000}
    }

    matrix = payout_table.get(spots_picked, {})
    multiplier = matrix.get(hits_landed, 0)

    if multiplier > 0:
        return (
            bet_amount * multiplier,
            f"Hit {hits_landed} of {spots_picked}!"
        )

    return 0, f"Hit {hits_landed} of {spots_picked}"


# ============================================================
#              PYGAME VISUAL ENGINE INITIALIZATION
# ============================================================

pygame.init()

try:
    pygame.mixer.init(
        frequency=22050,
        size=-16,
        channels=1
    )
    AUDIO_ENABLED = True
except pygame.error:
    AUDIO_ENABLED = False


WIDTH, HEIGHT = 950, 720

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(
    "The Terminal Casino - Lounge Keno Cabinet"
)

clock = pygame.time.Clock()
_lobby_hint_font = pygame.font.SysFont(None, 20)
_GAME_TITLE = ("The Terminal Casino - Lounge Keno Cabinet")


# ============================================================
#               PROCEDURAL AUDIO SYNTH DRIVERS
# ============================================================

def generate_synth_sound(
    freq_list,
    duration_ms,
    wave_type="square",
    volume=0.3
):
    if not AUDIO_ENABLED:
        return None

    sample_rate = 22050

    total_samples = int(
        sample_rate * (duration_ms / 1000.0)
    )

    buffer = array.array("h", [0] * total_samples)

    samples_per_freq = max(
        1,
        total_samples // len(freq_list)
    )

    for i in range(total_samples):
        freq_idx = min(
            i // samples_per_freq,
            len(freq_list) - 1
        )

        freq = freq_list[freq_idx]

        if freq == 0:
            val = 0

        else:
            t = i / sample_rate

            if wave_type == "square":
                val = (
                    32767
                    if math.sin(2 * math.pi * freq * t) >= 0
                    else -32768
                )

            elif wave_type == "triangle":
                val = int(
                    32767
                    * (
                        2.0
                        * math.fabs(
                            2.0
                            * (
                                t * freq
                                - math.floor(
                                    t * freq + 0.5
                                )
                            )
                        )
                        - 1.0
                    )
                )

            else:
                val = int(
                    32767
                    * math.sin(2 * math.pi * freq * t)
                )

        buffer[i] = int(val * volume)

    return pygame.mixer.Sound(buffer=buffer)


def play_sound(sound):
    if AUDIO_ENABLED and sound is not None:
        sound.play()


snd_pop = generate_synth_sound(
    [180, 90],
    50,
    wave_type="triangle",
    volume=0.4
)

snd_hit = generate_synth_sound(
    [660, 880],
    80,
    wave_type="square",
    volume=0.15
)

snd_win = generate_synth_sound(
    [523, 659, 784, 1046],
    500,
    wave_type="square",
    volume=0.15
)

snd_lose = generate_synth_sound(
    [220, 165],
    350,
    wave_type="square",
    volume=0.2
)

snd_chip = generate_synth_sound(
    [440],
    40,
    wave_type="triangle",
    volume=0.25
)


# ============================================================
#                 CLASSIC KENO COLOR PALETTE
# ============================================================

BG_NAVY = (15, 23, 42)
PANEL_BG = (30, 41, 59)
BORDER_COLOR = (71, 85, 105)

ACCENT_AMBER = (245, 158, 11)
AMBER_SHADOW = (180, 83, 9)

TEXT_WHITE = (248, 250, 252)
CHARCOAL = (15, 23, 42)

BRIGHT_RED = (239, 68, 68)
BRIGHT_GREEN = (34, 197, 94)
BTN_BLUE = (37, 99, 235)


# ============================================================
#                           FONTS
# ============================================================

font_options = [
    "segoeuiemoji",
    "applecoloremoji",
    "notocoloremoji",
    "arial"
]

ui_font = pygame.font.SysFont(
    font_options,
    18,
    bold=True
)

label_font = pygame.font.SysFont(
    font_options,
    14,
    bold=True
)

grid_font = pygame.font.SysFont(
    "impact",
    16
)

btn_text_font = pygame.font.SysFont(
    "arial",
    12,
    bold=True
)


# ============================================================
#                         LIVE STATES
# ============================================================


async def run_keno(balance):
    global screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(_GAME_TITLE)
    running = True
    current_bet = 0

    win_message = (
        "TAP UP TO 10 NUMBERS TO CHOOSE SPOTS, "
        "ADJUST BET, THEN DRAW!"
    )

    game_stage = "BETTING"
    # BETTING, DRAWING, RESOLVED

    player_spots = []
    drawn_numbers = []


    # ============================================================
    #                  PNEUMATIC MECHANICAL TIMING
    # ============================================================

    draw_timer = 0
    draw_interval = 22


    # ============================================================
    #                  HARDWARE INTERACTION REGIONS
    # ============================================================

    bet_box_rect = pygame.Rect(
        45,
        420,
        340,
        80
    )

    clear_btn_rect = pygame.Rect(
        720,
        480,
        180,
        45
    )

    draw_btn_rect = pygame.Rect(
        720,
        535,
        180,
        45
    )


    # ============================================================
    #                 10 x 8 KENO NUMBER GRID
    # ============================================================

    grid_rects = {}

    start_grid_x = 440
    start_grid_y = 60

    cell_w = 46
    cell_h = 40

    for num in range(1, 81):

        row = (num - 1) // 10
        col = (num - 1) % 10

        cx = start_grid_x + (col * cell_w)
        cy = start_grid_y + (row * cell_h)

        grid_rects[num] = pygame.Rect(
            cx,
            cy,
            cell_w - 4,
            cell_h - 4
        )


    # ============================================================
    #             VIDEO POKER STYLE BETTING BUTTONS
    # ============================================================

    bet_buttons = []

    # Row 1: Positive modifiers (+1, +5, +10, +25, +100)
    pos_vals = [1, 5, 10, 25, 100]
    btn_w = 62
    btn_h = 32
    spacing = 7
    start_x = 45
    start_y = 515

    for i, val in enumerate(pos_vals):
        bx = start_x + i * (btn_w + spacing)
        rect = pygame.Rect(bx, start_y, btn_w, btn_h)
        bet_buttons.append((f"+{val}", val, rect))

    # Row 2: Negative modifiers (-1, -5, -10, -25, -100)
    neg_vals = [-1, -5, -10, -25, -100]
    start_y_neg = 555

    for i, val in enumerate(neg_vals):
        bx = start_x + i * (btn_w + spacing)
        rect = pygame.Rect(bx, start_y_neg, btn_w, btn_h)
        bet_buttons.append((str(val), val, rect))


    # ============================================================
    #                         MAIN LOOP
    # ============================================================

    while running:

        # =================================================       #                         EVENTS
        # =================================================       
        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):

                mouse_pos = event.pos

                # =================================================
                #                         BETTING
                # =================================================

                if game_stage == "BETTING":

                    # ---------------------------------------------
                    # Video Poker Bet Buttons (+ / -)
                    # ---------------------------------------------
                    for label, amount, rect in bet_buttons:
                        if rect.collidepoint(mouse_pos):
                            if amount > 0:
                                if balance >= amount:
                                    current_bet += amount
                                    balance -= amount
                                    play_sound(snd_chip)
                                    win_message = f"WAGER: ${current_bet}"
                                else:
                                    win_message = "❌ NOT ENOUGH CREDITS!"
                            else:
                                sub_val = abs(amount)
                                if current_bet >= sub_val:
                                    current_bet -= sub_val
                                    balance += sub_val
                                    play_sound(snd_chip)
                                    win_message = f"WAGER: ${current_bet}"
                                else:
                                    current_bet = 0
                                    balance += current_bet
                                    win_message = "WAGER: $0"

                    # ---------------------------------------------
                    # Clear ticket
                    # ---------------------------------------------

                    if clear_btn_rect.collidepoint(mouse_pos):

                        balance += current_bet
                        current_bet = 0

                        player_spots.clear()

                        play_sound(snd_chip)

                        win_message = (
                            "BETTING BOARD CLEARED. "
                            "SELECT NEW SPOTS."
                        )

                    # ---------------------------------------------
                    # Number grid
                    # ---------------------------------------------

                    for num, rect in grid_rects.items():

                        if rect.collidepoint(mouse_pos):

                            if num in player_spots:

                                player_spots.remove(num)
                                play_sound(snd_chip)

                            else:

                                if len(player_spots) < 10:

                                    player_spots.append(num)
                                    play_sound(snd_chip)

                                else:

                                    win_message = (
                                        "❌ KENO RULES: "
                                        "MAX 10 SPOT PICKS "
                                        "ALLOWED!"
                                    )

                    # ---------------------------------------------
                    # Draw balls
                    # ---------------------------------------------

                    if draw_btn_rect.collidepoint(mouse_pos):

                        if (
                            current_bet > 0
                            and len(player_spots) > 0
                        ):

                            game_stage = "DRAWING"

                            drawn_numbers.clear()
                            draw_timer = 0

                            win_message = (
                                "PNEUMATIC BLOWER ACTIVE! "
                                "DRAWING 20 BALLS..."
                            )

                        elif current_bet == 0:

                            win_message = (
                                "❌ MUST PLACE A CREDIT "
                                "WAGER BEFORE DRAWING!"
                            )

                        else:

                            win_message = (
                                "❌ MUST CHOOSE AT LEAST "
                                "1 SPOT NUMBER!"
                            )

                # =================================================
                #                       RESOLVED
                # =================================================

                elif game_stage == "RESOLVED":

                    if (
                        draw_btn_rect.collidepoint(mouse_pos)
                        or clear_btn_rect.collidepoint(mouse_pos)
                        or bet_box_rect.collidepoint(mouse_pos)
                    ):

                        player_spots.clear()
                        drawn_numbers.clear()

                        current_bet = 0

                        game_stage = "BETTING"

                        win_message = (
                            "TICKET WINDOW OPEN. "
                            "CHOOSE NEW SPOTS AND WAGER."
                        )


        # =================================================       #                 PNEUMATIC BALL DRAWING
        # =================================================       
        if game_stage == "DRAWING":

            draw_timer += 1

            if draw_timer >= draw_interval:

                draw_timer = 0

                # Select a unique number from 1-80
                next_ball = random.randint(1, 80)

                while next_ball in drawn_numbers:

                    next_ball = random.randint(1, 80)

                drawn_numbers.append(next_ball)

                # Play hit sound if the number is selected
                if next_ball in player_spots:

                    play_sound(snd_hit)

                else:

                    play_sound(snd_pop)

                # ---------------------------------------------
                # End drawing after 20 balls
                # ---------------------------------------------

                if len(drawn_numbers) >= 20:

                    game_stage = "RESOLVED"

                    # -----------------------------------------
                    # Math Intersection Audit
                    # -----------------------------------------

                    matches = list(
                        set(player_spots)
                        & set(drawn_numbers)
                    )

                    hit_count = len(matches)
                    spots_count = len(player_spots)

                    total_won, summary_desc = (
                        calculate_keno_winnings(
                            spots_count,
                            hit_count,
                            current_bet
                        )
                    )

                    balance += total_won

                    # -----------------------------------------
                    # Win / loss result
                    # -----------------------------------------

                    if total_won > 0:

                        win_message = (
                            f"🎉 WINNER! "
                            f"{summary_desc}. "
                            f"Payout: +${total_won}!"
                        )

                        play_sound(snd_win)

                    else:

                        win_message = (
                            f"😢 NO PAYOUT! "
                            f"{summary_desc}. "
                            f"Ticket cleared."
                        )

                        play_sound(snd_lose)


        # =================================================       #                    BACKGROUND CANVAS
        # =================================================       
        screen.fill(BG_NAVY)

        pygame.draw.rect(
            screen,
            PANEL_BG,
            (10, 10, WIDTH - 20, HEIGHT - 20),
            3
        )

        pygame.draw.rect(
            screen,
            BORDER_COLOR,
            (20, 20, WIDTH - 40, HEIGHT - 40),
            1
        )


        # =================================================       #       1. INTERACTIVE KENO NUMBER BOARD
        # =================================================       
        pygame.draw.rect(
            screen,
            PANEL_BG,
            (
                start_grid_x - 9,
                start_grid_y - 9,
                cell_w * 10 + 14,
                cell_h * 8 + 14
            ),
            0,
            6
        )

        pygame.draw.rect(
            screen,
            ACCENT_AMBER,
            (
                start_grid_x - 5,
                start_grid_y - 5,
                cell_w * 10 + 6,
                cell_h * 8 + 6
            ),
            2,
            4
        )


        # =================================================       #                       GRID CELLS
        # =================================================       
        for num, rect in grid_rects.items():

            is_picked = num in player_spots
            is_drawn = num in drawn_numbers

            box_bg = BG_NAVY
            text_color = ACCENT_AMBER

            # Selected but not drawn
            if is_picked and not is_drawn:

                box_bg = AMBER_SHADOW
                text_color = TEXT_WHITE

            # Drawn but missed
            elif not is_picked and is_drawn:

                box_bg = BRIGHT_RED
                text_color = TEXT_WHITE

            # Selected and hit
            elif is_picked and is_drawn:

                box_bg = BRIGHT_GREEN
                text_color = CHARCOAL


            pygame.draw.rect(
                screen,
                box_bg,
                rect,
                0,
                3
            )

            border_color = (
                BORDER_COLOR
                if not is_picked and not is_drawn
                else TEXT_WHITE
            )

            pygame.draw.rect(
                screen,
                border_color,
                rect,
                1,
                3
            )

            num_surf = grid_font.render(
                str(num),
                True,
                text_color
            )

            screen.blit(
                num_surf,
                (
                    rect.centerx
                    - num_surf.get_width() // 2,

                    rect.centery
                    - num_surf.get_height() // 2
                    - 1
                )
            )


        # =================================================       #       2. REAL VACUUM HOPPER CHAMBER & BALL ANIMATION
        # =================================================       
        hopper_rect = pygame.Rect(45, 60, 340, 330)

        # Outer cabinet frame
        pygame.draw.rect(screen, PANEL_BG, hopper_rect, 0, 6)

        # Inner glass/acrylic chamber background
        glass_rect = hopper_rect.inflate(-8, -8)
        pygame.draw.rect(screen, (10, 15, 25), glass_rect, 0, 4)

        # Metallic hopper chute funnel structure lines
        pygame.draw.line(screen, BORDER_COLOR, (glass_rect.x + 20, glass_rect.y + 15), (glass_rect.right - 20, glass_rect.y + 15), 3)
        pygame.draw.line(screen, BORDER_COLOR, (glass_rect.x + 60, glass_rect.bottom - 15), (glass_rect.right - 60, glass_rect.bottom - 15), 3)
        pygame.draw.line(screen, ACCENT_AMBER, (glass_rect.x + 20, glass_rect.y + 17), (glass_rect.right - 20, glass_rect.y + 17), 1)

        # Frame border
        pygame.draw.rect(screen, ACCENT_AMBER, hopper_rect, 2, 6)

        # Render stored/settled drawn balls
        for i, ball_num in enumerate(drawn_numbers):
            row = i // 5
            col = i % 5

            bx = 81 + (col * 62)
            by = 125 + (row * 52)

            # If it's the very latest ball and we are actively drawing, jitter slightly
            if game_stage == "DRAWING" and i == len(drawn_numbers) - 1:
                bx += random.randint(-4, 4)
                by += random.randint(-4, 4)

            is_match = ball_num in player_spots
            ball_bg = BRIGHT_GREEN if is_match else TEXT_WHITE

            # Drop shadow
            pygame.draw.circle(screen, CHARCOAL, (bx + 2, by + 2), 18)
            # Ball body
            pygame.draw.circle(screen, ball_bg, (bx, by), 18)
            # Ball rim
            pygame.draw.circle(screen, CHARCOAL if is_match else BORDER_COLOR, (bx, by), 15, 1)

            b_txt = grid_font.render(str(ball_num), True, CHARCOAL)
            screen.blit(
                b_txt,
                (
                    bx - b_txt.get_width() // 2,
                    by - b_txt.get_height() // 2 - 1
                )
            )


        # =================================================       #              3. MAIN CREDIT WAGER PANEL
        # =================================================       
        box_bg = (
            PANEL_BG
            if current_bet == 0
            else AMBER_SHADOW
        )

        pygame.draw.rect(
            screen,
            box_bg,
            bet_box_rect,
            0,
            6
        )

        pygame.draw.rect(
            screen,
            ACCENT_AMBER,
            bet_box_rect,
            2,
            6
        )

        box_txt = ui_font.render(
            f"CURRENT BET: ${current_bet}",
            True,
            TEXT_WHITE
        )

        screen.blit(
            box_txt,
            (
                bet_box_rect.centerx
                - box_txt.get_width() // 2,

                bet_box_rect.centery
                - box_txt.get_height() // 2
            )
        )


        # =================================================       #                  4. CONTROL HUD PANEL
        # =================================================       
        pygame.draw.rect(
            screen,
            PANEL_BG,
            (45, 600, 340, 45),
            0,
            6
        )

        pygame.draw.rect(
            screen,
            BORDER_COLOR,
            (45, 600, 340, 45),
            2,
            6
        )

        bal_txt = ui_font.render(
            f"CREDITS: ${balance}",
            True,
            ACCENT_AMBER
        )

        screen.blit(
            bal_txt,
            (65, 613)
        )


        # =================================================       #             VIDEO POKER BET BUTTONS RENDER
        # =================================================       
        for label, amount, rect in bet_buttons:
            if game_stage != "BETTING":
                continue

            btn_bg = BTN_BLUE if amount > 0 else (100, 116, 139)

            pygame.draw.rect(
                screen,
                btn_bg,
                rect,
                0,
                4
            )
            pygame.draw.rect(
                screen,
                TEXT_WHITE,
                rect,
                1,
                4
            )

            b_lbl = btn_text_font.render(
                label,
                True,
                TEXT_WHITE
            )
            screen.blit(
                b_lbl,
                (
                    rect.centerx - b_lbl.get_width() // 2,
                    rect.centery - b_lbl.get_height() // 2
                )
            )


        # =================================================       #                 ACTION DASHBOARD BUTTONS
        # =================================================       
        if game_stage == "BETTING":

            action_label = "DRAW BALLS"

        elif game_stage == "DRAWING":

            action_label = "DRAWING..."

        else:

            action_label = "RESET CONSOLE"


        # DRAW / RESET BUTTON

        if game_stage != "DRAWING":

            pygame.draw.rect(
                screen,
                BRIGHT_RED,
                draw_btn_rect,
                0,
                5
            )

            pygame.draw.rect(
                screen,
                TEXT_WHITE,
                draw_btn_rect,
                1,
                5
            )

            b_txt = label_font.render(
                action_label,
                True,
                TEXT_WHITE
            )

            screen.blit(
                b_txt,
                (
                    draw_btn_rect.centerx
                    - b_txt.get_width() // 2,

                    draw_btn_rect.centery
                    - b_txt.get_height() // 2
                )
            )


        # CLEAR BUTTON ONLY DURING BETTING

        if game_stage == "BETTING":

            pygame.draw.rect(
                screen,
                PANEL_BG,
                clear_btn_rect,
                0,
                5
            )

            pygame.draw.rect(
                screen,
                TEXT_WHITE,
                clear_btn_rect,
                1,
                5
            )

            clear_txt = label_font.render(
                "CLEAR TICKET",
                True,
                TEXT_WHITE
            )

            screen.blit(
                clear_txt,
                (
                    clear_btn_rect.centerx
                    - clear_txt.get_width() // 2,

                    clear_btn_rect.centery
                    - clear_txt.get_height() // 2
                )
            )


        # =================================================       #                  5. BOTTOM TICKER MARQUEE
        # =================================================       
        pygame.draw.rect(
            screen,
            PANEL_BG,
            (45, 660, 855, 45),
            0,
            6
        )

        pygame.draw.rect(
            screen,
            ACCENT_AMBER,
            (45, 660, 855, 45),
            2,
            6
        )

        if (
            "WINNER" in win_message
            or "ADJUST" in win_message
            or "WAGER" in win_message
        ):

            msg_color = ACCENT_AMBER

        elif "❌" in win_message:

            msg_color = BRIGHT_RED

        else:

            msg_color = TEXT_WHITE


        msg_surf = ui_font.render(
            win_message,
            True,
            msg_color
        )

        # Prevent excessively long messages
        if msg_surf.get_width() > 825:

            while (
                msg_surf.get_width() > 825
                and len(win_message) > 10
            ):

                win_message = win_message[:-1]

                msg_surf = ui_font.render(
                    win_message,
                    True,
                    msg_color
                )


        screen.blit(
            msg_surf,
            (
                WIDTH // 2
                - msg_surf.get_width() // 2,

                672
            )
        )


        # =================================================       #                         DISPLAY
        # =================================================       
        _hint_surf = _lobby_hint_font.render("ESC: Return to Lobby", True, (230, 200, 140))
        screen.blit(_hint_surf, (10, HEIGHT - 22))
        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(60)
    return balance
