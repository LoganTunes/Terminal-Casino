import array
import asyncio
import math
import random
import secrets
import sys
import pygame

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

snd_peg = None
snd_win = None
snd_lose = None
snd_chip = None

def init_sounds():
    global snd_peg, snd_win, snd_lose, snd_chip
    if snd_peg is None:
        try:
            snd_peg = generate_synth_sound([900, 1300], 12, wave_type="square", volume=0.08)
            snd_win = generate_synth_sound([523, 659, 784, 1046], 400, wave_type="square", volume=0.15)
            snd_lose = generate_synth_sound([220, 196, 165], 350, wave_type="square", volume=0.2)
            snd_chip = generate_synth_sound([440, 554], 40, wave_type="triangle", volume=0.25)
        except Exception:
            pass

# ============================================================
#                       COLOR PALETTE
# ============================================================

MAHOGANY = (38, 12, 8)
FELT_DARK = (15, 45, 25)
WOOD_LIGHT = (75, 25, 15)
CHROME_LIGHT = (230, 230, 230)
CHROME_SHADOW = (100, 100, 100)
VINTAGE_GOLD = (235, 180, 70)
GOLD_SHADOW = (150, 100, 30)
CREAM_WHITE = (248, 244, 220)
CHARCOAL = (18, 18, 18)

COLOR_RED = (190, 25, 35)
COLOR_DUSTY = (130, 55, 60)
COLOR_CYAN = (0, 175, 215)
COLOR_PURPLE = (140, 30, 110)
COLOR_GOLD = (230, 170, 30)
COLOR_GREEN = (30, 150, 80)
COLOR_TRAP = (40, 10, 10)

# ============================================================
#              CASINO PLINKO BOARD GEOMETRY (1080x720)
# ============================================================

WIDTH, HEIGHT = 1080, 720

BOARD_LEFT = 35
BOARD_RIGHT = 545
BOARD_WIDTH = BOARD_RIGHT - BOARD_LEFT
BOARD_CENTER_X = (BOARD_LEFT + BOARD_RIGHT) / 2
BOARD_TOP = 85
BOARD_BOTTOM = 635

NUM_ROWS = 12

pegs = []
start_y = BOARD_TOP + 55
row_height = 32
cols_spacing = 32

for row in range(NUM_ROWS):
    y = start_y + (row * row_height)
    num_pegs_in_row = 3 + row
    row_w = (num_pegs_in_row - 1) * cols_spacing
    row_start_x = BOARD_CENTER_X - (row_w / 2)

    for col in range(num_pegs_in_row):
        x = row_start_x + (col * cols_spacing)
        pegs.append((x, y))

chute_w = 110
single_drop_chute = pygame.Rect(BOARD_CENTER_X - (chute_w / 2), BOARD_TOP + 8, chute_w, 30)

SLOT_DATA = [
    (100.0, COLOR_GOLD,   "100x"),
    (25.0,  COLOR_PURPLE, "25x"),
    (8.0,   COLOR_CYAN,   "8x"),
    (2.5,   COLOR_GREEN,  "2.5x"),
    (0.6,   COLOR_RED,    "0.6x"),
    (0.2,   COLOR_DUSTY,  "0.2x"),
    (0.0,   COLOR_TRAP,   "0x"),
    (0.2,   COLOR_DUSTY,  "0.2x"),
    (0.6,   COLOR_RED,    "0.6x"),
    (2.5,   COLOR_GREEN,  "2.5x"),
    (8.0,   COLOR_CYAN,   "8x"),
    (25.0,  COLOR_PURPLE, "25x"),
    (100.0, COLOR_GOLD,   "100x"),
]

slot_rects = []
slot_w = BOARD_WIDTH / len(SLOT_DATA)
slot_y = start_y + (NUM_ROWS * row_height) + 8

for i in range(len(SLOT_DATA)):
    sx = BOARD_LEFT + (i * slot_w)
    slot_rects.append(pygame.Rect(sx + 1, slot_y, slot_w - 2, 55))

# ============================================================
#      OUTCOME LAYER: RNG DECIDES FIRST, ANIMATION DRAWS IT
# ============================================================

def calculate_binomial_probabilities(n, p=0.5):
    probs = []
    for k in range(n + 1):
        comb = math.comb(n, k)
        probs.append(comb * (p ** k) * ((1 - p) ** (n - k)))
    return probs

binomial_probs = calculate_binomial_probabilities(NUM_ROWS, 0.5)

def roll_csprng_slot():
    r = secrets.SystemRandom().random()
    cumulative = 0.0
    for i, prob in enumerate(binomial_probs):
        cumulative += prob
        if r <= cumulative:
            return i
    return len(binomial_probs) - 1

def generate_discrete_path(target_slot, total_rows=NUM_ROWS):
    moves = [1] * target_slot + [0] * (total_rows - target_slot)
    random.shuffle(moves)

    path_x = []
    lane = 0
    for row in range(total_rows):
        lane += moves[row]
        num_pegs = 3 + row
        row_w = (num_pegs - 1) * cols_spacing
        row_start_x = BOARD_CENTER_X - (row_w / 2)
        x = row_start_x + (lane + 0.5) * cols_spacing
        path_x.append(x)

    return path_x

def triangle_half_width_at_y(y):
    row_idx = (y - start_y) / row_height
    row_idx = max(0.0, min(NUM_ROWS - 1, row_idx))
    width = (2.0 + row_idx) * cols_spacing
    return width / 2.0

def clamp_to_triangle(x, y):
    last_peg_row_y = start_y + (NUM_ROWS - 1) * row_height
    if y > last_peg_row_y + row_height * 0.5:
        return x
    half_w = triangle_half_width_at_y(y)
    return max(BOARD_CENTER_X - half_w, min(BOARD_CENTER_X + half_w, x))

def build_waypoints(target_slot_idx, start_x):
    path = generate_discrete_path(target_slot_idx)
    target_slot = slot_rects[target_slot_idx]

    ys = [single_drop_chute.bottom + 5]
    xs = [start_x]

    for i, px in enumerate(path):
        ys.append(start_y + i * row_height)
        xs.append(px)

    ys.append(slot_y)
    xs.append(float(target_slot.centerx))

    wobble = []
    for i in range(len(xs)):
        if i < 3:
            wobble.append(0.0)
        else:
            wobble.append(random.uniform(-1.0, 1.0) * max(0.0, 1.0 - (i / len(xs))) * 5.0)

    return ys, xs, wobble

DROP_GRAVITY = 900.0
BASE_RESTITUTION = 0.55
V0_START = 50.0
V_FLOOR = 40.0
V_CAP = 1200.0

def build_segment_plan(ys):
    v0 = V0_START
    plan = []
    for i in range(len(ys) - 1):
        d = max(1.0, ys[i + 1] - ys[i])
        g = DROP_GRAVITY
        disc = v0 * v0 + 2 * g * d
        t = (-v0 + math.sqrt(disc)) / g
        v_exit = v0 + g * t
        plan.append((t, v0, g))
        r = BASE_RESTITUTION * random.uniform(0.82, 1.18)
        v0 = min(V_CAP, max(V_FLOOR, v_exit * r + random.uniform(-15.0, 15.0)))
    return plan

def eval_drop(elapsed, ys, xs, wobble, seg_plan):
    t = elapsed
    for i, (seg_dur, v0, g) in enumerate(seg_plan):
        if t <= seg_dur or i == len(seg_plan) - 1:
            local_t = max(0.0, min(1.0, t / max(1e-6, seg_dur)))
            sub_t = local_t * seg_dur
            y = ys[i] + v0 * sub_t + 0.5 * g * sub_t * sub_t

            x0, x1 = xs[i], xs[i + 1]
            base_x = x0 + (x1 - x0) * local_t
            w = wobble[i] * math.sin(math.pi * local_t) if i < len(wobble) else 0.0
            x = clamp_to_triangle(base_x + w, y)
            return y, x, i
        t -= seg_dur
    return ys[-1], xs[-1], len(seg_plan) - 1

# ============================================================
#                      UI CHIP SELECTIONS
# ============================================================

clear_btn_rect = pygame.Rect(585, 590, 460, 38)

chip_selections = [
    (10, pygame.Rect(585, 520, 48, 48), (240, 240, 240), (40, 40, 40)),
    (50, pygame.Rect(685, 520, 48, 48), (180, 30, 30), (240, 240, 240)),
    (100, pygame.Rect(785, 520, 48, 48), (30, 80, 180), (240, 240, 240)),
    (250, pygame.Rect(885, 520, 48, 48), (30, 130, 60), (212, 163, 89)),
    (1000, pygame.Rect(985, 520, 48, 48), (30, 30, 30), (212, 163, 89)),
]

prebuilt_chip_surfaces = []

def init_chip_surfaces(chip_num_font):
    global prebuilt_chip_surfaces
    if prebuilt_chip_surfaces:
        return
    for val, _, col_bg, col_str in chip_selections:
        radius = 12
        size = radius * 2 + 8
        base_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)

        pygame.draw.circle(base_surf, col_bg, center, radius)

        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            sx = center[0] + math.cos(rad) * (radius - 3)
            sy = center[1] + math.sin(rad) * (radius - 3)
            pygame.draw.circle(base_surf, col_str, (int(sx), int(sy)), 2)

        pygame.draw.circle(base_surf, CREAM_WHITE, center, radius - 5)

        display_str = str(val) if val < 1000 else f"{val // 1000}k"
        c_txt = chip_num_font.render(display_str, True, CHARCOAL)
        base_surf.blit(c_txt, (center[0] - c_txt.get_width() // 2, center[1] - c_txt.get_height() // 2))
        prebuilt_chip_surfaces.append(base_surf)

def draw_chip_stack(surface, cx, cy, chip_model_idx, rotation=0.0):
    base_surf = prebuilt_chip_surfaces[chip_model_idx]
    rotated_surf = pygame.transform.rotate(base_surf, rotation)
    new_rect = rotated_surf.get_rect(center=(int(cx), int(cy)))
    pygame.draw.circle(surface, CHARCOAL, (int(cx), int(cy + 2)), 12)
    surface.blit(rotated_surf, new_rect.topleft)

# ============================================================
#                   MAIN ENTRY POINT FUNCTION
# ============================================================

BUMP_FLASH_SECONDS = 0.1

async def run_plinko(balance):
    init_sounds()
    clock = pygame.time.Clock()
    _lobby_hint_font = pygame.font.SysFont("arial", 18, bold=True)

    font_options = ["segoeuiemoji", "applecoloremoji", "notocoloremoji", "arial"]
    ui_font = pygame.font.SysFont(font_options, 18, bold=True)
    label_font = pygame.font.SysFont(font_options, 11, bold=True)
    header_font = pygame.font.SysFont("impact", 32)
    slot_font = pygame.font.SysFont("impact", 12)
    chip_num_font = pygame.font.SysFont("arial", 9, bold=True)

    init_chip_surfaces(chip_num_font)

    active_chip_wager = 100
    win_message = "PRESS 'DROP' TO RELEASE CHIP. PRESS ESC TO EXIT."

    token = {
        "active": False,
        "landed": False,
        "x": 0.0,
        "y": 0.0,
        "render_y": 0.0,
        "elapsed": 0.0,
        "angle": 0.0,
        "spin": 0.0,
        "wager": 0,
        "model_idx": 2,
        "target_slot": 0,
        "waypoint_ys": [],
        "waypoint_xs": [],
        "waypoint_wobble": [],
        "seg_plan": [],
        "seg_idx": 0,
        "bump_flash_timer": 0.0,
    }

    running = True
    _lobby_btn_label = "ESC: Return to Lobby"
    _lobby_btn_text_surf = _lobby_hint_font.render(_lobby_btn_label, True, (230, 200, 140))
    _lobby_btn_rect = pygame.Rect(10 - 8, (HEIGHT - 22) - 6, _lobby_btn_text_surf.get_width() + 16, _lobby_btn_text_surf.get_height() + 12)
    while running:
        screen = pygame.display.get_surface()
        if screen is None:
            return balance

        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            # Treat window close (QUIT) identically to ESC return to prevent display context corruption
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return balance

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and _lobby_btn_rect.collidepoint(pygame.mouse.get_pos()):
                return balance

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                for val, rect, c1, c2 in chip_selections:
                    if rect.collidepoint(mouse_pos):
                        active_chip_wager = val
                        if snd_chip: snd_chip.play()

                if clear_btn_rect.collidepoint(mouse_pos):
                    win_message = "Board reset. Ready to drop."
                    token["active"] = False
                    token["landed"] = False
                    if snd_chip: snd_chip.play()

                if not token["active"]:
                    if single_drop_chute.collidepoint(mouse_pos):
                        if balance >= active_chip_wager:
                            balance -= active_chip_wager
                            if snd_chip: snd_chip.play()

                            target_slot_idx = roll_csprng_slot()

                            model_idx = 0
                            for idx, sel in enumerate(chip_selections):
                                if sel[0] == active_chip_wager:
                                    model_idx = idx

                            start_x = BOARD_CENTER_X + random.uniform(-3.0, 3.0)
                            ys, xs, wobble = build_waypoints(target_slot_idx, start_x)
                            seg_plan = build_segment_plan(ys)

                            token["active"] = True
                            token["landed"] = False
                            token["x"] = start_x
                            token["y"] = ys[0]
                            token["render_y"] = ys[0]
                            token["elapsed"] = 0.0
                            token["angle"] = 0.0
                            token["spin"] = random.choice([-300.0, 300.0])
                            token["wager"] = active_chip_wager
                            token["model_idx"] = model_idx
                            token["target_slot"] = target_slot_idx
                            token["waypoint_ys"] = ys
                            token["waypoint_xs"] = xs
                            token["waypoint_wobble"] = wobble
                            token["seg_plan"] = seg_plan
                            token["seg_idx"] = 0
                            token["bump_flash_timer"] = 0.0

                            win_message = f"Dropping ${active_chip_wager} chip..."
                        else:
                            win_message = "❌ INSUFFICIENT FUNDS! LOWER YOUR CHIP WAGER."

        if token["active"] and not token["landed"]:
            ys = token["waypoint_ys"]
            xs = token["waypoint_xs"]
            wobble = token["waypoint_wobble"]
            seg_plan = token["seg_plan"]

            token["elapsed"] += dt
            y, x, seg_idx = eval_drop(token["elapsed"], ys, xs, wobble, seg_plan)
            token["angle"] = (token["angle"] + token["spin"] * dt) % 360.0

            if seg_idx > token["seg_idx"]:
                token["seg_idx"] = seg_idx
                token["spin"] = random.choice([-450.0, 450.0])
                token["bump_flash_timer"] = BUMP_FLASH_SECONDS
                if snd_peg: snd_peg.play()

            token["y"] = y
            token["x"] = x

            if token["bump_flash_timer"] > 0.0:
                token["bump_flash_timer"] = max(0.0, token["bump_flash_timer"] - dt)
                dip_frac = token["bump_flash_timer"] / BUMP_FLASH_SECONDS
                token["render_y"] = token["y"] - (3.0 * dip_frac)
            else:
                token["render_y"] = token["y"]

            total_seg_time = sum(t for t, _, _ in seg_plan)
            if token["elapsed"] >= total_seg_time:
                token["landed"] = True
                token["active"] = False

                slot_idx = token["target_slot"]
                target_slot = slot_rects[slot_idx]

                token["x"] = float(target_slot.centerx)
                token["y"] = float(target_slot.bottom - 12)
                token["render_y"] = token["y"]

                multiplier, _, label_str = SLOT_DATA[slot_idx]
                wager = token["wager"]
                payout_amount = int(wager * multiplier)

                if multiplier >= 1.0:
                    balance += payout_amount
                    win_message = f"🎉 BIG WIN! Landed in {label_str} (+${payout_amount})!"
                    if snd_win: snd_win.play()
                elif multiplier > 0.0:
                    balance += payout_amount
                    win_message = f"🪙 PARTIAL RETURN: Landed in {label_str} (+${payout_amount})."
                    if snd_lose: snd_lose.play()
                else:
                    win_message = f"💀 CENTER TRAP! Hit {label_str} ($0 Payout)."
                    if snd_lose: snd_lose.play()

        # Render step
        screen.fill(MAHOGANY)
        pygame.draw.rect(screen, WOOD_LIGHT, (10, 10, WIDTH - 20, HEIGHT - 20), 8)
        pygame.draw.rect(screen, FELT_DARK, (18, 18, WIDTH - 36, HEIGHT - 36))

        board_rect = pygame.Rect(BOARD_LEFT - 10, BOARD_TOP - 40, BOARD_WIDTH + 20, BOARD_BOTTOM - BOARD_TOP + 45)
        pygame.draw.rect(screen, CHARCOAL, board_rect)
        pygame.draw.rect(screen, VINTAGE_GOLD, board_rect.inflate(6, 6), 3)

        title_surf = header_font.render("PLINKO", True, COLOR_CYAN)
        title_rect = title_surf.get_rect(center=(BOARD_CENTER_X, BOARD_TOP - 18))
        screen.blit(title_surf, title_rect)

        is_hover = single_drop_chute.collidepoint(pygame.mouse.get_pos()) and not token["active"]
        chute_bg = VINTAGE_GOLD if is_hover else CHARCOAL
        pygame.draw.rect(screen, chute_bg, single_drop_chute, 0, 4)
        pygame.draw.rect(screen, CREAM_WHITE, single_drop_chute, 2, 4)

        c_txt = ui_font.render("▼ DROP ▼", True, CHARCOAL if is_hover else VINTAGE_GOLD)
        screen.blit(c_txt, (single_drop_chute.centerx - c_txt.get_width() // 2, single_drop_chute.centery - c_txt.get_height() // 2))

        for px, py in pegs:
            pygame.draw.circle(screen, GOLD_SHADOW, (px, py + 1), 4)
            pygame.draw.circle(screen, CREAM_WHITE, (px, py), 3)

        for i, rect in enumerate(slot_rects):
            mult, s_color, label_str = SLOT_DATA[i]

            pygame.draw.rect(screen, s_color, rect, 0, 3)
            pygame.draw.rect(screen, CREAM_WHITE if mult > 0 else COLOR_RED, rect, 1, 3)

            txt_surf = slot_font.render(label_str, True, CREAM_WHITE if mult > 0 else COLOR_RED)
            txt_surf = pygame.transform.rotate(txt_surf, 90)

            screen.blit(txt_surf, (rect.centerx - txt_surf.get_width() // 2, rect.centery - txt_surf.get_height() // 2))

        if token["active"] or token["landed"]:
            draw_y = token["render_y"] if token["active"] else token["y"]
            draw_chip_stack(screen, token["x"], draw_y, token["model_idx"], rotation=token["angle"])

        panel_x = BOARD_RIGHT + 25
        panel_w = WIDTH - panel_x - 25

        pygame.draw.rect(screen, CHARCOAL, (panel_x, BOARD_TOP - 40, panel_w, 260))
        pygame.draw.rect(screen, GOLD_SHADOW, (panel_x, BOARD_TOP - 40, panel_w, 260), 2)
        screen.blit(ui_font.render("PAYTABLE", True, VINTAGE_GOLD), (panel_x + 15, BOARD_TOP - 25))

        pay_lines = [
            "100x GOLD      -> OUTMOST EDGES",
            "25x PURPLE     -> OUTER FLANKS",
            "8x CYAN        -> MID EDGES",
            "2.5x GREEN     -> INNER FLANKS",
            "0.6x RED       -> NEAR CENTER",
            "0.2x DUSTY     -> CLOSE CALL",
            "0x CHARCOAL    -> DEAD CENTER",
        ]
        for idx, line in enumerate(pay_lines):
            p_txt = label_font.render(line, True, CREAM_WHITE)
            screen.blit(p_txt, (panel_x + 15, BOARD_TOP + 10 + (idx * 28)))

        bank_panel_y = 320
        pygame.draw.rect(screen, CHARCOAL, (panel_x, bank_panel_y, panel_w, 80))
        pygame.draw.rect(screen, CHROME_SHADOW, (panel_x, bank_panel_y, panel_w, 80), 2)
        screen.blit(ui_font.render(f"BANKROLL: ${balance}", True, CREAM_WHITE), (panel_x + 15, bank_panel_y + 12))
        screen.blit(label_font.render(f"SELECTED CHIP: ${active_chip_wager}", True, VINTAGE_GOLD), (panel_x + 15, bank_panel_y + 45))

        for val, rect, col_bg, col_str in chip_selections:
            is_sel = active_chip_wager == val
            pygame.draw.circle(screen, VINTAGE_GOLD if is_sel else CHARCOAL, rect.center, 24)
            pygame.draw.circle(screen, col_bg, rect.center, 21)

            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                sx = int(rect.centerx + math.cos(rad) * 16)
                sy = int(rect.centery + math.sin(rad) * 16)
                pygame.draw.circle(screen, col_str, (sx, sy), 2)

            pygame.draw.circle(screen, CREAM_WHITE, rect.center, 13)
            display_str = str(val) if val < 1000 else f"{val // 1000}k"
            val_txt = chip_num_font.render(f"${display_str}", True, CHARCOAL)
            screen.blit(val_txt, (rect.centerx - val_txt.get_width() // 2, rect.centery - val_txt.get_height() // 2))

        pygame.draw.rect(screen, CHARCOAL, clear_btn_rect, 0, 4)
        pygame.draw.rect(screen, CREAM_WHITE, clear_btn_rect, 1, 4)
        b_txt = label_font.render("RESET MESSAGES", True, CREAM_WHITE)
        screen.blit(b_txt, (clear_btn_rect.centerx - b_txt.get_width() // 2, clear_btn_rect.centery - b_txt.get_height() // 2))

        pygame.draw.rect(screen, CHARCOAL, (25, 645, WIDTH - 50, 40))
        pygame.draw.rect(screen, VINTAGE_GOLD, (25, 645, WIDTH - 50, 40), 2)
        msg_color = VINTAGE_GOLD if ("WINNER" in win_message or "BIG WIN" in win_message or "READY" in win_message or "DROP" in win_message) else COLOR_RED if ("❌" in win_message or "TRAP" in win_message) else CREAM_WHITE
        msg_surf = ui_font.render(win_message, True, msg_color)
        screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, 655))

        _lobby_btn_hover = _lobby_btn_rect.collidepoint(pygame.mouse.get_pos())
        _lobby_btn_bg = (70, 45, 25) if _lobby_btn_hover else (40, 25, 15)
        pygame.draw.rect(screen, _lobby_btn_bg, _lobby_btn_rect, 0, 6)
        pygame.draw.rect(screen, (200, 160, 90) if _lobby_btn_hover else (150, 110, 60), _lobby_btn_rect, 1, 6)
        screen.blit(_lobby_btn_text_surf, (10, HEIGHT - 22))

        pygame.display.flip()
        await asyncio.sleep(0)

    return balance
