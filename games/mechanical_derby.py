import asyncio
import pygame
import random
import sys
import array
import math

# ============================================================
#       ORIGINAL CASINO MATH ENGINE & GAME LOGIC
# ============================================================

HORSE_NAMES = {
    1: "Thunder",
    2: "Lightning",
    3: "Midnight",
    4: "Silver",
    5: "Cyclone"
}


def calculate_racing_winnings(chosen_horse, winning_horse, bet_amount):
    """Processes straight-up single horse win payouts at 4-to-1 odds."""

    if chosen_horse == winning_horse:
        # 4:1 profit + original wager returned
        return bet_amount * 5, f"{HORSE_NAMES[winning_horse]} Won the Race!"

    return 0, None


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
except pygame.error:
    print("Warning: Audio could not be initialized.")


WIDTH, HEIGHT = 1150, 780

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "The Terminal Casino - Mechanical Derby"
)

clock = pygame.time.Clock()
_lobby_hint_font = pygame.font.SysFont(None, 20)
_GAME_TITLE = ("The Terminal Casino - Mechanical Derby")


# ============================================================
#               PROCEDURAL AUDIO SYNTH DRIVERS
# ============================================================

def generate_synth_sound(
    freq_list,
    duration_ms,
    wave_type="square",
    volume=0.3
):
    sample_rate = 22050

    total_samples = int(
        sample_rate * (duration_ms / 1000.0)
    )

    buffer = array.array(
        "h",
        [0] * total_samples
    )

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
                    if math.sin(
                        2 * math.pi * freq * t
                    ) >= 0
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
                    * math.sin(
                        2 * math.pi * freq * t
                    )
                )

        buffer[i] = int(
            val * volume
        )

    return pygame.mixer.Sound(
        buffer=buffer
    )


# ============================================================
#                       SOUND EFFECTS
# ============================================================

try:

    snd_gallop = generate_synth_sound(
        [180, 120, 0, 180, 120],
        45,
        wave_type="triangle",
        volume=0.15
    )

    snd_horn = generate_synth_sound(
        [330, 330, 440, 330, 554],
        300,
        wave_type="square",
        volume=0.12
    )

    snd_win = generate_synth_sound(
        [523, 659, 784, 1046],
        400,
        wave_type="square",
        volume=0.15
    )

    snd_lose = generate_synth_sound(
        [220, 196, 165, 147],
        350,
        wave_type="square",
        volume=0.20
    )

    snd_chip = generate_synth_sound(
        [880, 1200],
        40,
        wave_type="triangle",
        volume=0.25
    )

except pygame.error:

    snd_gallop = None
    snd_horn = None
    snd_win = None
    snd_lose = None
    snd_chip = None


def play_sound(sound):
    """Safely play a sound if audio is available."""

    if sound is not None:
        sound.play()


# ============================================================
#                       COLOR PALETTE
# ============================================================

FELT_GREEN = (10, 68, 33)
MAHOGANY = (56, 18, 11)
WOOD_LIGHT = (84, 30, 20)

CHROME_LIGHT = (220, 220, 220)
CHROME_SHADOW = (110, 110, 110)

VINTAGE_GOLD = (255, 215, 0)
GOLD_SHADOW = (145, 105, 45)

CREAM_WHITE = (247, 245, 230)
CHARCOAL = (24, 24, 24)

BRIGHT_RED = (190, 25, 25)


# ============================================================
#                       HORSE COLORS
# ============================================================

HORSE_COLORS = {
    1: (210, 40, 40),    # Thunder (Red)
    2: (40, 80, 210),    # Lightning (Blue)
    3: (240, 140, 40),   # Midnight (Orange)
    4: (40, 160, 60),    # Silver (Green)
    5: (140, 60, 180)    # Cyclone (Purple)
}


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
    20,
    bold=True
)

label_font = pygame.font.SysFont(
    font_options,
    14,
    bold=True
)

track_font = pygame.font.SysFont(
    "impact",
    18
)

# Tuscan / classic decorative serif font for header text in black legible letters
tuscan_font_options = [
    "georgia",
    "timesnewroman",
    "times",
    "serif"
]

header_text_font = pygame.font.SysFont(
    tuscan_font_options,
    22,
    bold=True
)

chip_num_font = pygame.font.SysFont(
    "arial",
    11,
    bold=True
)

felt_font = pygame.font.SysFont(
    "courier",
    16,
    bold=True
)


# ============================================================
#                         LIVE STATES
# ============================================================


async def run_mechanical_derby(balance):
    global screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(_GAME_TITLE)
    running = True

    active_chip_wager = 10

    win_message = (
        "CHOOSE CHIP VALUE, DROP TOKENS ON YOUR TARGET HORSE, "
        "THEN START!"
    )

    game_stage = "BETTING"
    # BETTING, RACING, RESOLVED

    selected_horse = 0

    player_bets = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0
    }


    # ============================================================
    #                  TRACK STATE VARIABLES
    # ============================================================

    horses_state = [
        [30, 0]
        for _ in range(5)
    ]

    race_rankings = []


    # ============================================================
    #                  HARDWARE INTERACTION REGIONS
    # ============================================================

    clear_btn_rect = pygame.Rect(
        920,
        630,
        190,
        45
    )

    race_btn_rect = pygame.Rect(
        920,
        685,
        190,
        45
    )


    # ============================================================
    #             STRAIGHT-UP HORSE BETTING CELLS
    # ============================================================

    bet_rects = {}

    for idx in range(1, 6):
        col_idx = 0 if idx <= 3 else 1
        row_idx = (idx - 1) if col_idx == 0 else (idx - 4)

        x_pos = 40 + (col_idx * 270)
        y_pos = 430 + (row_idx * 60)

        bet_rects[idx] = pygame.Rect(
            x_pos,
            y_pos,
            250,
            50
        )


    # ============================================================
    #                       CHIP SELECTIONS
    # ============================================================

    chip_selections = [

        (
            10,
            pygame.Rect(620, 520, 45, 45),
            (240, 240, 240),
            (40, 40, 40)
        ),

        (
            50,
            pygame.Rect(680, 520, 45, 45),
            (180, 30, 30),
            (240, 240, 240)
        ),

        (
            100,
            pygame.Rect(740, 520, 45, 45),
            (30, 80, 180),
            (240, 240, 240)
        ),

        (
            250,
            pygame.Rect(800, 520, 45, 45),
            (30, 130, 60),
            (212, 163, 89)
        ),

        (
            1000,
            pygame.Rect(860, 520, 45, 45),
            (30, 30, 30),
            (212, 163, 89)
        )
    ]


    # ============================================================
    #                    CHIP DRAWING FUNCTION
    # ============================================================

    def draw_chip_stack(surface, rect, text_val):

        bg_color = (240, 240, 240)
        stripe_color = (40, 40, 40)

        for val, _, col_bg, col_str in chip_selections:

            if text_val >= val:

                bg_color = col_bg
                stripe_color = col_str

        cx = rect.x + rect.width - 25
        cy = rect.centery

        # Drop shadow
        pygame.draw.circle(
            surface,
            CHARCOAL,
            (cx, cy + 1),
            11
        )

        # Chip body
        pygame.draw.circle(
            surface,
            bg_color,
            (cx, cy),
            11
        )

        # Chip edge markings
        for angle in range(0, 360, 45):

            rad = math.radians(angle)

            pygame.draw.circle(
                surface,
                stripe_color,
                (
                    int(
                        cx + math.cos(rad) * 9
                    ),
                    int(
                        cy + math.sin(rad) * 9
                    )
                ),
                1
            )

        # Center
        pygame.draw.circle(
            surface,
            CREAM_WHITE,
            (cx, cy),
            6
        )

        display_str = (
            str(text_val)
            if text_val < 1000
            else f"{text_val // 1000}k"
        )

        c_txt = chip_num_font.render(
            display_str,
            True,
            CHARCOAL
        )

        surface.blit(
            c_txt,
            (
                cx - c_txt.get_width() // 2,
                cy - c_txt.get_height() // 2
            )
        )


    # ============================================================
    #         SIGMA DERBY STYLE MECHANICAL HORSE & ROD ART
    # ============================================================

    def draw_sigma_derby_horse(surface, x, y, h_color, stride_timer):
        """Renders an authentic Sigma Derby mechanical horse deeply embedded into the slot trench."""

        # 1. Internal recessed slot rod and anchor block emerging from the core mechanism
        rod_rect = pygame.Rect(x + 16, y, 4, 32)
        pygame.draw.rect(surface, (10, 8, 5), rod_rect)
        pygame.draw.rect(surface, CHROME_SHADOW, (x + 16, y + 4, 2, 28))
        pygame.draw.rect(surface, CHROME_LIGHT, (x + 18, y + 4, 1, 28))

        # Recessed mechanical base block anchoring inside the slot
        base_block = pygame.Rect(x + 12, y + 22, 12, 7)
        pygame.draw.rect(surface, CHARCOAL, base_block, 0, 2)
        pygame.draw.rect(surface, VINTAGE_GOLD, base_block, 1, 2)

        # 2. Main Horse Torso (Horizontal profile pointing forward left-to-right)
        body_rect = pygame.Rect(x + 2, y + 6, 28, 12)
        pygame.draw.rect(surface, h_color, body_rect, 0, 4)
        pygame.draw.rect(surface, CHARCOAL, body_rect, 1, 4)

        # 3. Head and Neck (Extending forward, level and charging)
        neck_pts = [(x + 22, y + 8), (x + 32, y + 2), (x + 38, y + 4), (x + 26, y + 10)]
        pygame.draw.polygon(surface, h_color, neck_pts)
        pygame.draw.polygon(surface, CHARCOAL, neck_pts, 1)

        # Forward-facing snout / head
        head_rect = pygame.Rect(x + 34, y + 3, 7, 5)
        pygame.draw.rect(surface, h_color, head_rect, 0, 2)
        pygame.draw.rect(surface, CHARCOAL, head_rect, 1, 2)

        # Mane along the neck top
        pygame.draw.line(surface, CHARCOAL, (x + 24, y + 5), (x + 30, y + 1), 2)
        pygame.draw.line(surface, CHARCOAL, (x + 20, y + 7), (x + 26, y + 3), 2)

        # Tail sweeping back
        tail_pts = [(x + 2, y + 8), (x - 4, y + 12), (x - 2, y + 16)]
        pygame.draw.polygon(surface, CHARCOAL, tail_pts)

        # 4. Animated mechanical articulated legs
        leg_offset = int(math.sin(stride_timer * 0.9) * 4)

        # Front mechanical legs
        pygame.draw.line(surface, CHARCOAL, (x + 26, y + 16), (x + 24 + leg_offset, y + 29), 2)
        pygame.draw.line(surface, CHARCOAL, (x + 30, y + 16), (x + 32 - leg_offset, y + 29), 2)

        # Back mechanical legs
        pygame.draw.line(surface, CHARCOAL, (x + 6, y + 16), (x + 4 - leg_offset, y + 29), 2)
        pygame.draw.line(surface, CHARCOAL, (x + 10, y + 16), (x + 12 + leg_offset, y + 29), 2)


    # ============================================================
    #                         MAIN LOOP
    # ============================================================

    while running:

        # ========================================================
        #                       EVENT HANDLING
        # ========================================================

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
                    # CHIP SELECTION
                    # ---------------------------------------------

                    for val, rect, c1, c2 in chip_selections:

                        if rect.collidepoint(mouse_pos):

                            active_chip_wager = val

                            play_sound(
                                snd_chip
                            )

                    # ---------------------------------------------
                    # CLEAR CHIPS
                    # ---------------------------------------------

                    if clear_btn_rect.collidepoint(mouse_pos):

                        balance += sum(
                            player_bets.values()
                        )

                        player_bets = {
                            1: 0,
                            2: 0,
                            3: 0,
                            4: 0,
                            5: 0
                        }

                        selected_horse = 0

                        win_message = (
                            "BETTING BOARD CLEARED. "
                            "SELECT A HORSE."
                        )

                        play_sound(
                            snd_chip
                        )

                    # ---------------------------------------------
                    # PLACE BET ON HORSE
                    # ---------------------------------------------

                    for horse_id, rect in bet_rects.items():

                        if rect.collidepoint(mouse_pos):

                            if (
                                selected_horse == 0
                                or selected_horse == horse_id
                            ):

                                if balance >= active_chip_wager:

                                    player_bets[
                                        horse_id
                                    ] += active_chip_wager

                                    balance -= active_chip_wager

                                    selected_horse = horse_id

                                    win_message = (
                                        f"BET PLACED: {HORSE_NAMES[horse_id]} "
                                        f"(#{horse_id}) — "
                                        f"${player_bets[horse_id]} "
                                        f"TOTAL"
                                    )

                                    play_sound(
                                        snd_chip
                                    )

                                else:

                                    win_message = (
                                        "❌ NOT ENOUGH MACHINE "
                                        "CREDITS FOR THAT CHIP!"
                                    )

                            else:

                                win_message = (
                                    "❌ STRAIGHT-UP BETS ONLY! "
                                    "CLEAR THE BOARD TO "
                                    "CHOOSE A DIFFERENT HORSE."
                                )

                    # ---------------------------------------------
                    # START RACE
                    # ---------------------------------------------

                    if race_btn_rect.collidepoint(mouse_pos):

                        if (
                            selected_horse > 0
                            and player_bets[selected_horse] > 0
                        ):

                            game_stage = "RACING"

                            win_message = (
                                "THE GATES DROP! "
                                "THEY ARE CHARGING DOWN "
                                "THE STRAIGHTAWAY!"
                            )

                            play_sound(
                                snd_horn
                            )

                            horses_state = [
                                [30, 0]
                                for _ in range(5)
                            ]

                            race_rankings.clear()

                        else:

                            win_message = (
                                "❌ DROP TOKENS ON A HORSE "
                                "CELL BEFORE CALLING "
                                "THE GATES!"
                            )

                # =================================================
                #                       RESOLVED
                # =================================================

                elif game_stage == "RESOLVED":

                    if (
                        race_btn_rect.collidepoint(mouse_pos)
                        or clear_btn_rect.collidepoint(mouse_pos)
                    ):

                        player_bets = {
                            1: 0,
                            2: 0,
                            3: 0,
                            4: 0,
                            5: 0
                        }

                        selected_horse = 0

                        game_stage = "BETTING"

                        horses_state = [
                            [30, 0]
                            for _ in range(5)
                        ]

                        race_rankings.clear()

                        win_message = (
                            "TRACK CLEARED. PLACE A "
                            "STRAIGHT WIN BET ON YOUR "
                            "RUNNER TO START."
                        )


        # ========================================================
        #                  TRACK PHYSICS LOOP
        # ========================================================

        if game_stage == "RACING":

            if random.random() < 0.35:

                play_sound(
                    snd_gallop
                )

            finish_line_x = 1030

            for idx in range(5):

                if horses_state[idx][0] < finish_line_x:

                    horses_state[idx][1] += 1

                    stride_interval = random.randint(
                        3,
                        7
                    )

                    if (
                        horses_state[idx][1]
                        % stride_interval
                        == 0
                    ):

                        stride_burst = random.choice(
                            [5, 8, 12, 16]
                        )

                        horses_state[idx][0] += (
                            stride_burst
                        )

                    if horses_state[idx][0] >= finish_line_x:

                        horses_state[idx][0] = (
                            finish_line_x
                        )

                        race_rankings.append(
                            idx + 1
                        )

            # =====================================================
            #                   RACE RESOLUTION
            # =====================================================

            if len(race_rankings) >= 5:

                game_stage = "RESOLVED"

                winner = race_rankings[0]

                wagered_cash = player_bets.get(
                    selected_horse,
                    0
                )

                total_won, outcome_desc = (
                    calculate_racing_winnings(
                        selected_horse,
                        winner,
                        wagered_cash
                    )
                )

                balance += total_won

                if total_won > 0:

                    win_message = (
                        f"🎉 WINNER! "
                        f"{outcome_desc} "
                        f"PAYOUT (4-1 ODDS): "
                        f"+${total_won}!"
                    )

                    play_sound(
                        snd_win
                    )

                else:

                    win_message = (
                        f"😢 RACE OVER! "
                        f"{HORSE_NAMES[winner]} "
                        f"hit the wire first. "
                        f"Your bet on {HORSE_NAMES[selected_horse]} lost."
                    )

                    play_sound(
                        snd_lose
                    )


        # ========================================================
        #                  BACKGROUND VELVET
        # ========================================================

        screen.fill(
            MAHOGANY
        )

        pygame.draw.rect(
            screen,
            WOOD_LIGHT,
            (
                10,
                10,
                WIDTH - 20,
                HEIGHT - 20
            ),
            10
        )

        pygame.draw.rect(
            screen,
            FELT_GREEN,
            (
                20,
                20,
                WIDTH - 40,
                HEIGHT - 40
            )
        )


        # ========================================================
        #       1. FULL-SCREEN WIDTH RACE TRACK
        # ========================================================

        track_x = 35
        track_y = 45
        track_w = WIDTH - 70
        track_h = 360

        pygame.draw.rect(
            screen,
            CHARCOAL,
            (
                track_x - 4,
                track_y - 4,
                track_w + 8,
                track_h + 8
            )
        )

        pygame.draw.rect(
            screen,
            CHROME_LIGHT,
            (
                track_x,
                track_y,
                track_w,
                track_h
            )
        )

        pygame.draw.rect(
            screen,
            CHROME_SHADOW,
            (
                track_x,
                track_y,
                track_w,
                track_h
            ),
            5
        )

        lane_h = track_h // 5

        for idx in range(5):

            ly = track_y + (
                idx * lane_h
            )

            pygame.draw.rect(
                screen,
                (75, 60, 45),
                (
                    track_x + 10,
                    ly,
                    track_w - 20,
                    lane_h - 4
                )
            )

            # 3D Beveled mechanical slot trench recessed into the track surface
            slot_y = ly + lane_h // 2
            pygame.draw.line(
                screen,
                (8, 6, 3),
                (track_x + 10, slot_y - 1),
                (track_x + track_w - 10, slot_y - 1),
                1
            )
            pygame.draw.line(
                screen,
                (20, 15, 10),
                (track_x + 10, slot_y),
                (track_x + track_w - 10, slot_y),
                4
            )
            pygame.draw.line(
                screen,
                (110, 100, 90),
                (track_x + 10, slot_y + 3),
                (track_x + track_w - 10, slot_y + 3),
                1
            )

            pygame.draw.rect(
                screen,
                CHARCOAL,
                (
                    track_x + 10,
                    ly,
                    track_w - 20,
                    lane_h - 4
                ),
                2
            )

            if idx < 4:

                pygame.draw.line(
                    screen,
                    CHROME_SHADOW,
                    (
                        track_x + 10,
                        ly + lane_h - 2
                    ),
                    (
                        track_x + track_w - 10,
                        ly + lane_h - 2
                    ),
                    1
                )

            finish_line_x = track_x + track_w - 70

            for dash_y in range(
                ly + 4,
                ly + lane_h - 8,
                9
            ):

                pygame.draw.line(
                    screen,
                    BRIGHT_RED,
                    (
                        finish_line_x,
                        dash_y
                    ),
                    (
                        finish_line_x,
                        dash_y + 5
                    ),
                    2
                )

            hx = horses_state[idx][0]
            h_color = HORSE_COLORS.get(idx + 1, CREAM_WHITE)
            stride_val = horses_state[idx][1]

            # Draw the Sigma Derby horse with its rod receding into the 3D slot trench
            draw_sigma_derby_horse(screen, hx, ly + (lane_h // 2) - 14, h_color, stride_val)

            # Horse Name Tag plate above the horse
            name_txt = track_font.render(
                HORSE_NAMES[idx + 1],
                True,
                CREAM_WHITE
            )
            screen.blit(
                name_txt,
                (
                    hx + 18 - name_txt.get_width() // 2,
                    ly + 4
                )
            )

            if idx + 1 in race_rankings:

                place = (
                    race_rankings.index(
                        idx + 1
                    ) + 1
                )

                place_txt = label_font.render(
                    f"{place}",
                    True,
                    VINTAGE_GOLD
                )

                screen.blit(
                    place_txt,
                    (
                        finish_line_x - 30,
                        ly + (lane_h // 2) - 8
                    )
                )


        # ========================================================
        #          2. SPORTSBOOK WIN WAGER HEADER (TUSCAN FONT)
        # ========================================================

        header_rect = pygame.Rect(
            740,
            420,
            370,
            75
        )

        pygame.draw.rect(
            screen,
            CHARCOAL,
            header_rect,
            0,
            6
        )

        pygame.draw.rect(
            screen,
            GOLD_SHADOW,
            header_rect.inflate(-4, -4),
            0,
            4
        )

        pygame.draw.rect(
            screen,
            VINTAGE_GOLD,
            header_rect.inflate(-8, -8),
            2,
            4
        )

        # Legible black Tuscan-style serif text rendered directly on the gold panel without a background box
        header_txt_surf = header_text_font.render("MECHANICAL DERBY", True, CHARCOAL)
        screen.blit(
            header_txt_surf,
            (
                header_rect.centerx - header_txt_surf.get_width() // 2,
                header_rect.y + 14
            )
        )

        sub_txt = label_font.render(
            "★ PAYS 4-1 ODDS ★",
            True,
            CREAM_WHITE
        )
        screen.blit(
            sub_txt,
            (
                header_rect.centerx - sub_txt.get_width() // 2,
                header_rect.y + 45
            )
        )


        # ========================================================
        #                3. HORSE BETTING FIELDS
        # ========================================================

        for horse_id, rect in bet_rects.items():

            wager_amount = player_bets.get(
                horse_id,
                0
            )

            box_bg = (
                CHARCOAL
                if wager_amount == 0
                else GOLD_SHADOW
            )

            box_border = (
                VINTAGE_GOLD
                if wager_amount == 0
                else CHARCOAL
            )

            pygame.draw.rect(
                screen,
                box_bg,
                rect,
                0,
                4
            )

            pygame.draw.rect(
                screen,
                box_border,
                rect,
                1,
                4
            )

            pygame.draw.circle(
                screen,
                HORSE_COLORS[horse_id],
                (
                    rect.x + 22,
                    rect.centery
                ),
                10
            )

            lbl_color = (
                VINTAGE_GOLD
                if wager_amount == 0
                else CHARCOAL
            )

            lbl_txt = felt_font.render(
                f"{HORSE_NAMES[horse_id]} (#{horse_id})",
                True,
                lbl_color
            )

            screen.blit(
                lbl_txt,
                (
                    rect.x + 48,
                    rect.y + 14
                )
            )

            if wager_amount > 0:

                draw_chip_stack(
                    screen,
                    rect,
                    wager_amount
                )


        # ========================================================
        #                   CONTROL HUD PANEL
        # ========================================================

        pygame.draw.rect(
            screen,
            CHARCOAL,
            (
                40,
                630,
                330,
                100
            )
        )

        pygame.draw.rect(
            screen,
            CHROME_SHADOW,
            (
                40,
                630,
                330,
                100
            ),
            2
        )

        bal_txt = ui_font.render(
            f"TOTAL HAND BALANCE: ${balance}",
            True,
            CREAM_WHITE
        )

        screen.blit(
            bal_txt,
            (
                55,
                645
            )
        )

        chip_txt = label_font.render(
            f"ACTIVE CHIP SELECTION: ${active_chip_wager}",
            True,
            VINTAGE_GOLD
        )

        screen.blit(
            chip_txt,
            (
                55,
                685
            )
        )


        # ========================================================
        #                    CHIP SELECTION ROW
        # ========================================================

        for val, rect, col_bg, col_str in chip_selections:

            if game_stage != "BETTING":
                continue

            is_selected = (
                active_chip_wager == val
            )

            pygame.draw.circle(
                screen,
                VINTAGE_GOLD
                if is_selected
                else CHARCOAL,
                rect.center,
                24
            )

            pygame.draw.circle(
                screen,
                col_bg,
                rect.center,
                21
            )

            for angle in range(
                0,
                360,
                45
            ):

                rad = math.radians(
                    angle
                )

                pygame.draw.circle(
                    screen,
                    col_str,
                    (
                        int(
                            rect.centerx
                            + math.cos(rad) * 16
                        ),
                        int(
                            rect.centery
                            + math.sin(rad) * 16
                        )
                    ),
                    3
                )

            pygame.draw.circle(
                screen,
                CREAM_WHITE,
                rect.center,
                14
            )

            display_str = (
                str(val)
                if val < 1000
                else f"{val // 1000}k"
            )

            val_txt = chip_num_font.render(
                f"${display_str}",
                True,
                CHARCOAL
            )

            screen.blit(
                val_txt,
                (
                    rect.centerx
                    - val_txt.get_width() // 2,
                    rect.centery
                    - val_txt.get_height() // 2
                )
            )


        # ========================================================
        #                    ACTION DASHBOARD
        # ========================================================

        if game_stage == "BETTING":

            action_label = "START RACE"

        elif game_stage == "RACING":

            action_label = "RACING..."

        else:

            action_label = "RESET TRACK"


        buttons = [
            (
                race_btn_rect,
                action_label,
                BRIGHT_RED
            ),
            (
                clear_btn_rect,
                "CLEAR CHIPS",
                CHARCOAL
            )
        ]


        for btn_rect, label, bg in buttons:

            if game_stage == "RACING":
                continue

            if (
                game_stage != "BETTING"
                and btn_rect == clear_btn_rect
            ):
                continue

            pygame.draw.rect(
                screen,
                bg,
                btn_rect,
                0,
                5
            )

            pygame.draw.rect(
                screen,
                CREAM_WHITE,
                btn_rect,
                1,
                5
            )

            b_txt = label_font.render(
                label,
                True,
                CREAM_WHITE
            )

            screen.blit(
                b_txt,
                (
                    btn_rect.centerx
                    - b_txt.get_width() // 2,
                    btn_rect.centery
                    - b_txt.get_height() // 2
                )
            )


        # ========================================================
        #                LOWER ALERT BANNER / TICKER
        # ========================================================

        pygame.draw.rect(
            screen,
            CHARCOAL,
            (
                390,
                630,
                510,
                100
            )
        )

        pygame.draw.rect(
            screen,
            VINTAGE_GOLD,
            (
                390,
                630,
                510,
                100
            ),
            2
        )

        if (
            "WINNER" in win_message
            or "CHOOSE" in win_message
        ):

            msg_color = VINTAGE_GOLD

        elif "❌" in win_message:

            msg_color = BRIGHT_RED

        else:

            msg_color = CREAM_WHITE


        msg_surf = ui_font.render(
            win_message,
            True,
            msg_color
        )

        if msg_surf.get_width() > 480:

            msg_surf = pygame.transform.smoothscale(
                msg_surf,
                (
                    480,
                    msg_surf.get_height()
                )
            )

        screen.blit(
            msg_surf,
            (
                645
                - msg_surf.get_width() // 2,
                672
            )
        )


        # ========================================================
        #                     DISPLAY UPDATE
        # ========================================================

        _hint_surf = _lobby_hint_font.render("ESC: Return to Lobby", True, (230, 200, 140))
        screen.blit(_hint_surf, (10, HEIGHT - 22))
        pygame.display.flip()

        await asyncio.sleep(0)

        clock.tick(60)
    return balance
