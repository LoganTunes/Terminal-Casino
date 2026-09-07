import asyncio
import io
import pygame
import random
import sys
import array
import math
import urllib.request

# ============================================================
#        ORIGINAL CASINO MATH ENGINE & GAME LOGIC
# ============================================================

CHERRY = "CHERRY"
BELL = "BELL"
BAR = "BAR"
SEVEN = "7"
LEMON = "LEMON"
GRAPE = "GRAPE"
ORANGE = "ORANGE"

SLOT_SYMBOLS = [CHERRY, BELL, BAR, SEVEN, LEMON, GRAPE, ORANGE]
SLOT_WEIGHTS = [15, 20, 15, 10, 8, 7, 5]

TRIPLE_PAYOUTS = {
    BELL: 10,
    BAR: 20,
    SEVEN: 30,
    LEMON: 40,
    GRAPE: 60,
    ORANGE: 100,
}

CHERRY_PAYOUTS = {
    1: 1,
    2: 2,
    3: 5,
}


def spin_reel():
    return random.choices(SLOT_SYMBOLS, weights=SLOT_WEIGHTS, k=1)[0]


def spin_slots():
    return [spin_reel(), spin_reel(), spin_reel()]


def calculate_winnings(reels, bet):
    cherry_count = reels.count(CHERRY)

    if reels[0] == reels[1] == reels[2] and reels[0] != CHERRY:
        symbol = reels[0]
        return bet * TRIPLE_PAYOUTS[symbol], f"Three {symbol}s!"

    if cherry_count > 0:
        return bet * CHERRY_PAYOUTS[cherry_count], f"{cherry_count} Cherry(s)!"

    return 0, None


# ============================================================
#              PYGAME VISUAL ENGINE INITIALIZATION
# ============================================================

pygame.init()

pygame.mixer.init(
    frequency=22050,
    size=-16,
    channels=1,
)

WIDTH, HEIGHT = 900, 720

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vintage Vegas Slots")

clock = pygame.time.Clock()
_lobby_hint_font = pygame.font.SysFont("sans-serif", 20)
_GAME_TITLE = "Vintage Vegas Slots"


# ============================================================
#                PROCEDURAL AUDIO SYNTH DRIVERS
# ============================================================

def generate_synth_sound(
    freq_list,
    duration_ms,
    wave_type="square",
    volume=0.3,
):
    sample_rate = 22050
    total_samples = int(sample_rate * (duration_ms / 1000.0))

    buffer = array.array("h", [0] * total_samples)
    samples_per_freq = total_samples // len(freq_list)

    for i in range(total_samples):
        freq_idx = min(
            i // samples_per_freq,
            len(freq_list) - 1,
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
                                - math.floor(t * freq + 0.5)
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


snd_lever = generate_synth_sound([120, 80, 50], 120, wave_type="triangle", volume=0.5)
snd_click = generate_synth_sound([800, 0], 15, wave_type="square", volume=0.1)
snd_latch = generate_synth_sound([180, 110], 80, wave_type="triangle", volume=0.4)
snd_winner = generate_synth_sound([440, 554, 659, 880, 1109, 1318], 400, wave_type="square", volume=0.2)
snd_loser = generate_synth_sound([150, 140, 130], 350, wave_type="square", volume=0.3)
snd_coin = generate_synth_sound([987, 1318, 1568, 1046], 70, wave_type="square", volume=0.15)


# ============================================================
#                        COLOR PALETTE
# ============================================================

FELT_GREEN = (10, 68, 33)
MAHOGANY = (56, 18, 11)
WOOD_LIGHT = (84, 30, 20)

CHROME_BASE = (175, 175, 175)
CHROME_LIGHT = (220, 220, 220)
CHROME_SHADOW = (110, 110, 110)

VINTAGE_GOLD = (212, 163, 89)
GOLD_SHADOW = (145, 105, 45)

CREAM_WHITE = (247, 245, 230)
CHARCOAL = (24, 24, 24)

BRIGHT_RED = (210, 25, 25)
RED_SHADOW = (120, 10, 10)

WHITE_GLINT = (255, 255, 255)

TOKEN_EDGE = (90, 95, 100)
TOKEN_BASE = (200, 205, 210)
TOKEN_SHINE = (240, 245, 250)


# ============================================================
#                            FONTS
# ============================================================

ui_font = pygame.font.SysFont("sans-serif", 22, bold=True)
label_font = pygame.font.SysFont("sans-serif", 15, bold=True)


# ============================================================
#            DYNAMIC REAL EMOJI IMAGE LOADER
# ============================================================

EMOJI_UNICODE_MAP = {
    CHERRY: "1f352", # 🍒
    GRAPE: "1f347",  # 🍇
    ORANGE: "1f34a", # 🍊
    LEMON: "1f34b",  # 🍋
    BELL: "1f514",   # 🔔
}

EMOJI_SURFACES = {}

def fetch_emoji_surface(hex_code):
    """Downloads transparent PNG emoji graphic dynamically."""
    url = f"https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/{hex_code}.png"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        image_data = response.read()
    image_file = io.BytesIO(image_data)
    return pygame.image.load(image_file).convert_alpha()

print("Downloading authentic emoji assets...")
for sym, code in EMOJI_UNICODE_MAP.items():
    try:
        EMOJI_SURFACES[sym] = fetch_emoji_surface(code)
    except Exception as e:
        print(f"Could not load emoji image for {sym}: {e}")

# High-Detail Vector fallback renderers for BAR & 7
def draw_custom_seven(surface, cx, cy, scale=1.0):
    pts = [
        (cx - int(22 * scale), cy - int(28 * scale)),
        (cx + int(22 * scale), cy - int(28 * scale)),
        (cx + int(4 * scale), cy + int(28 * scale)),
        (cx - int(8 * scale), cy + int(28 * scale)),
        (cx + int(8 * scale), cy - int(14 * scale)),
        (cx - int(22 * scale), cy - int(14 * scale)),
    ]
    pygame.draw.polygon(surface, GOLD_SHADOW, [(px + int(2 * scale), py + int(2 * scale)) for px, py in pts])
    pygame.draw.polygon(surface, BRIGHT_RED, pts)
    pygame.draw.line(surface, WHITE_GLINT, (cx - int(20 * scale), cy - int(26 * scale)), (cx + int(20 * scale), cy - int(26 * scale)), max(1, int(3 * scale)))

def draw_custom_bar(surface, cx, cy, scale=1.0):
    w, h = int(76 * scale), int(36 * scale)
    bar_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    gold_rect = pygame.Rect(bar_rect.x + 2, bar_rect.y + 2, bar_rect.width - 4, bar_rect.height - 4)
    inner_rect = pygame.Rect(bar_rect.x + 4, bar_rect.y + 4, bar_rect.width - 8, bar_rect.height - 8)
    pygame.draw.rect(surface, CHARCOAL, bar_rect, border_radius=max(1, int(4 * scale)))
    pygame.draw.rect(surface, VINTAGE_GOLD, gold_rect, border_radius=max(1, int(3 * scale)))
    pygame.draw.rect(surface, CHARCOAL, inner_rect, border_radius=max(1, int(2 * scale)))
    bar_font = pygame.font.SysFont("sans-serif", int(15 * scale), bold=True)
    bar_text = bar_font.render("BAR", True, CREAM_WHITE)
    surface.blit(bar_text, bar_text.get_rect(center=(cx, cy)))

def render_symbol(surface, symbol, center_x, center_y, scale=1.0):
    """Direct visual dispatcher rendering high-res emojis or classic badges."""
    if symbol in EMOJI_SURFACES:
        base_img = EMOJI_SURFACES[symbol]
        size = int(60 * scale)
        scaled_img = pygame.transform.smoothscale(base_img, (size, size))
        rect = scaled_img.get_rect(center=(center_x, center_y))
        surface.blit(scaled_img, rect)
    elif symbol == SEVEN:
        draw_custom_seven(surface, center_x, center_y, scale)
    elif symbol == BAR:
        draw_custom_bar(surface, center_x, center_y, scale)


# ============================================================
#                        LIVE STATES
# ============================================================

async def run_slots(balance):
    global screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(_GAME_TITLE)
    running = True
    bet_amount = 10

    win_message = "WELCOME HIGH ROLLER! PULL LEVER TO SPIN."

    win_light_timer = 0
    active_coins = []
    tray_coins = []

    reels_state = [
        [SEVEN, 0, CHERRY, False],
        [SEVEN, 0, BELL, False],
        [SEVEN, 0, BAR, False],
    ]

    final_results = [
        SEVEN,
        SEVEN,
        SEVEN,
    ]

    is_spinning = False
    spin_phase_timer = 0

    lever_state = 0
    lever_offset_y = 0

    lever_knob_rect = pygame.Rect(760, 240, 50, 50)
    dec_bet_rect = pygame.Rect(190, 540, 40, 35)
    inc_bet_rect = pygame.Rect(280, 540, 40, 35)

    def draw_brushed_chrome_rect(surface, rect):
        pygame.draw.rect(surface, CHROME_SHADOW, rect)
        pygame.draw.rect(surface, CHROME_LIGHT, (rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 4))
        pygame.draw.rect(surface, CHROME_BASE, (rect.x + 6, rect.y + 6, rect.width - 12, rect.height - 12))
        pygame.draw.line(surface, CHROME_LIGHT, (rect.x + 10, rect.y + 30), (rect.x + rect.width - 10, rect.y + 30), 2)
        pygame.draw.line(surface, CHROME_SHADOW, (rect.x + 10, rect.y + rect.height - 30), (rect.x + rect.width - 10, rect.y + rect.height - 30), 2)

    def draw_quarter_token(surface, x, y):
        pygame.draw.ellipse(surface, TOKEN_EDGE, (x - 12, y - 7, 24, 14))
        pygame.draw.ellipse(surface, TOKEN_BASE, (x - 11, y - 6, 22, 12))
        pygame.draw.ellipse(surface, TOKEN_EDGE, (x - 8, y - 4, 16, 8), 1)
        pygame.draw.ellipse(surface, TOKEN_SHINE, (x - 6, y - 5, 12, 5))
        pygame.draw.circle(surface, TOKEN_EDGE, (x, y), 1)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                if not is_spinning and lever_state == 0:
                    if lever_knob_rect.collidepoint(mouse_pos):
                        lever_state = 1
                        win_message = ""
                        active_coins.clear()
                        tray_coins.clear()
                        snd_lever.play()

                    elif inc_bet_rect.collidepoint(mouse_pos):
                        if bet_amount + 5 <= balance:
                            bet_amount += 5
                        win_message = ""

                    elif dec_bet_rect.collidepoint(mouse_pos):
                        if bet_amount - 5 >= 5:
                            bet_amount -= 5
                        win_message = ""

        if lever_state == 1:
            lever_offset_y += 15
            if lever_offset_y >= 140:
                lever_state = 2
                if balance >= bet_amount:
                    balance -= bet_amount
                    is_spinning = True
                    spin_phase_timer = 0
                    final_results = spin_slots()
                    for reel in reels_state:
                        reel[3] = True
                else:
                    win_message = "INSUFFICIENT FUNDS! LOWER WAGER TICKER."

        elif lever_state == 2:
            lever_offset_y -= 25
            if lever_offset_y <= 0:
                lever_offset_y = 0
                lever_state = 0

        if is_spinning:
            spin_phase_timer += 1

            if spin_phase_timer % 4 == 0 and any(reel[3] for reel in reels_state):
                snd_click.play()

            stop_times = [45, 85, 125]

            for idx in range(3):
                if reels_state[idx][3]:
                    reels_state[idx][1] += 20
                    if reels_state[idx][1] >= 100:
                        reels_state[idx][1] = 0
                        reels_state[idx][0] = reels_state[idx][2]

                        if spin_phase_timer >= stop_times[idx]:
                            reels_state[idx][0] = final_results[idx]
                            reels_state[idx][3] = False
                            snd_latch.play()
                        else:
                            reels_state[idx][2] = random.choice(SLOT_SYMBOLS)

            if not any(reel[3] for reel in reels_state):
                is_spinning = False
                winnings, description = calculate_winnings(final_results, bet_amount)

                if winnings > 0:
                    balance += winnings
                    win_message = f"WINNER! {description} +${winnings}"
                    win_light_timer = 120

                    coin_count = min(30, max(5, winnings // 2))
                    for c in range(coin_count):
                        active_coins.append({
                            'x': random.randint(340, 460),
                            'y': 590,
                            'vy': random.uniform(-6, -2),
                            'vx': random.uniform(-2, 2),
                            'delay': c * 3,
                        })
                    snd_winner.play()
                else:
                    win_message = "NO MATCH. BETTER LUCK NEXT SPIN!"
                    snd_loser.play()

                if balance <= 0:
                    win_message = "OUT OF CHIPS! RE-RUN GAME TO RESET."

        if win_light_timer > 0:
            win_light_timer -= 1

        for coin in active_coins[:]:
            if coin['delay'] > 0:
                coin['delay'] -= 1
                continue

            coin['x'] += coin['vx']
            coin['y'] += coin['vy']
            coin['vy'] += 0.5

            if coin['vy'] > 0 and 'played' not in coin:
                snd_coin.play()
                coin['played'] = True

            if coin['y'] >= 655:
                tray_coins.append((int(coin['x']), random.randint(650, 665)))
                active_coins.remove(coin)

        if len(tray_coins) > 120:
            tray_coins = tray_coins[-120:]

        screen.fill(MAHOGANY)
        pygame.draw.rect(screen, WOOD_LIGHT, (10, 10, WIDTH - 20, HEIGHT - 20), 10)
        pygame.draw.rect(screen, FELT_GREEN, (20, 20, WIDTH - 40, HEIGHT - 40))

        # Top Winner Dome
        light_center_x, light_y = 400, 35
        if win_light_timer > 0 and (win_light_timer // 10) % 2 == 0:
            dome_color, glow_color = WHITE_GLINT, VINTAGE_GOLD
            pygame.draw.circle(screen, glow_color, (light_center_x, light_y + 10), 40)
        else:
            dome_color, glow_color = BRIGHT_RED, RED_SHADOW

        pygame.draw.rect(screen, CHROME_SHADOW, (light_center_x - 30, light_y + 15, 60, 12))
        pygame.draw.rect(screen, CHROME_LIGHT, (light_center_x - 28, light_y + 15, 56, 6))
        pygame.draw.ellipse(screen, dome_color, (light_center_x - 22, light_y - 15, 44, 32))
        pygame.draw.ellipse(screen, WHITE_GLINT, (light_center_x - 12, light_y - 10, 10, 8))

        # Chrome Cabinet
        draw_brushed_chrome_rect(screen, pygame.Rect(120, 60, 560, 630))

        # Scoring Panel
        pygame.draw.rect(screen, CHARCOAL, (148, 82, 504, 134))
        pygame.draw.rect(screen, GOLD_SHADOW, (150, 80, 500, 130))
        pygame.draw.rect(screen, VINTAGE_GOLD, (152, 82, 496, 126), 2)

        pay_text1 = label_font.render("7-7-7: x30  | BAR-BAR-BAR: x20 | ORANGE x3: x100", True, CHARCOAL)
        pay_text2 = label_font.render("CHERRY x1: x1  | CHERRY x2: x2  | CHERRY x3: x5", True, CREAM_WHITE)
        screen.blit(pay_text1, (170, 110))
        screen.blit(pay_text2, (170, 160))

        # Mini icons on marquee
        draw_custom_seven(screen, 162, 116, scale=0.35)
        draw_custom_bar(screen, 260, 116, scale=0.45)
        render_symbol(screen, ORANGE, 400, 116, scale=0.45)
        render_symbol(screen, CHERRY, 162, 166, scale=0.45)

        # Reel Housing
        pygame.draw.rect(screen, CHARCOAL, (146, 236, 508, 138))
        pygame.draw.rect(screen, CHROME_SHADOW, (150, 240, 500, 130))

        # Render Reels
        for idx in range(3):
            rx, ry = 185 + (idx * 155), 255
            pygame.draw.rect(screen, CHARCOAL, (rx - 2, ry - 2, 119, 104))
            pygame.draw.rect(screen, CREAM_WHITE, (rx, ry, 115, 100))

            reel_clip_rect = pygame.Rect(rx, ry, 115, 100)
            screen.set_clip(reel_clip_rect)

            current_sym = reels_state[idx][0]
            offset_y = reels_state[idx][1]
            incoming_sym = reels_state[idx][2]

            center_x = rx + 57
            current_center_y = ry + 50 + offset_y
            incoming_center_y = ry - 50 + offset_y

            render_symbol(screen, current_sym, center_x, current_center_y)
            if reels_state[idx][3]:
                render_symbol(screen, incoming_sym, center_x, incoming_center_y)

            screen.set_clip(None)

            pygame.draw.rect(screen, (200, 200, 190), (rx, ry, 115, 12))
            pygame.draw.rect(screen, (200, 200, 190), (rx, ry + 88, 115, 12))
            pygame.draw.rect(screen, CHARCOAL, (rx, ry, 115, 100), 2)

        # Data Ticker
        pygame.draw.rect(screen, CHARCOAL, (150, 400, 500, 180))
        pygame.draw.rect(screen, CHROME_SHADOW, (150, 400, 500, 180), 3)

        message_color = VINTAGE_GOLD if ("WINNER" in win_message or "WELCOME" in win_message) else BRIGHT_RED
        msg_surf = ui_font.render(win_message, True, message_color)
        screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2 - 50, 415))

        bal_lbl = label_font.render(f"BANK TOTAL: ${balance}", True, CREAM_WHITE)
        bet_lbl = label_font.render(f"WAGER SELECTION: ${bet_amount}", True, VINTAGE_GOLD)
        screen.blit(bal_lbl, (170, 460))
        screen.blit(bet_lbl, (170, 505))

        # Buttons
        for rect, symbol in [(dec_bet_rect, "-"), (inc_bet_rect, "+")]:
            pygame.draw.rect(screen, RED_SHADOW, rect, 0, 4)
            pygame.draw.rect(screen, BRIGHT_RED, (rect.x, rect.y, rect.width, rect.height - 4), 0, 4)
            pygame.draw.rect(screen, CREAM_WHITE, (rect.x, rect.y, rect.width, rect.height - 4), 1, 4)
            button_text = label_font.render(symbol, True, CREAM_WHITE)
            screen.blit(button_text, (rect.centerx - button_text.get_width() // 2, rect.y + 6))

        # Coin Tray
        tray_rect = pygame.Rect(300, 620, 200, 55)
        pygame.draw.rect(screen, CHROME_SHADOW, tray_rect, border_radius=8)
        pygame.draw.rect(screen, CHARCOAL, (tray_rect.x + 4, tray_rect.y + 4, tray_rect.width - 8, tray_rect.height - 8), border_radius=6)

        for cx, cy in tray_coins:
            draw_quarter_token(screen, cx, cy)

        for coin in active_coins:
            if coin['delay'] <= 0:
                draw_quarter_token(screen, int(coin['x']), int(coin['y']))

        pygame.draw.rect(screen, CHROME_LIGHT, (tray_rect.x, tray_rect.y + 38, tray_rect.width, 17), border_radius=6)
        pygame.draw.rect(screen, CHROME_SHADOW, (tray_rect.x, tray_rect.y + 38, tray_rect.width, 17), 2, border_radius=6)

        # Lever
        lever_knob_rect.y = 240 + lever_offset_y
        pygame.draw.line(screen, CHARCOAL, (684, 314), (789, 264 + lever_offset_y), 14)
        pygame.draw.line(screen, CHROME_LIGHT, (680, 310), (785, 260 + lever_offset_y), 14)
        pygame.draw.line(screen, CHROME_SHADOW, (680, 312), (785, 262 + lever_offset_y), 6)

        pygame.draw.circle(screen, RED_SHADOW, (787, 262 + lever_offset_y), 24)
        pygame.draw.circle(screen, BRIGHT_RED, (785, 260 + lever_offset_y), 24)
        pygame.draw.circle(screen, WHITE_GLINT, (776, 252 + lever_offset_y), 6)

        _hint_surf = _lobby_hint_font.render("ESC: Return to Lobby", True, (230, 200, 140))
        screen.blit(_hint_surf, (10, HEIGHT - 22))
        pygame.display.flip()

        await asyncio.sleep(0)
        clock.tick(60)

    return balance
