import asyncio
import array
import math
import random
import sys
import pygame

# ============================================================
#           GAME LOGIC & PAYOUT ENGINE
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

CHERRY_PAYOUTS = {1: 1, 2: 2, 3: 5}

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
#                 AUDIO SYNTH DRIVERS
# ============================================================

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

def generate_synth_sound(freq_list, duration_ms, wave_type="square", volume=0.3):
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

snd_lever = generate_synth_sound([120, 80, 50], 120, wave_type="triangle", volume=0.5)
snd_click = generate_synth_sound([800, 0], 15, wave_type="square", volume=0.1)
snd_latch = generate_synth_sound([180, 110], 80, wave_type="triangle", volume=0.4)
snd_winner = generate_synth_sound([440, 554, 659, 880, 1109, 1318], 400, wave_type="square", volume=0.2)
snd_loser = generate_synth_sound([150, 140, 130], 350, wave_type="square", volume=0.3)
snd_coin = generate_synth_sound([987, 1318, 1568, 1046], 70, wave_type="square", volume=0.15)

# ============================================================
#             HIGH-RESOLUTION SURFACE SPRITE GENERATOR
# ============================================================

def create_hd_symbol_sprite(symbol_type, target_w=95, target_h=80):
    """Renders high-res 4x supersampled sprites with drop shadows and beveling."""
    scale = 4
    sw, sh = target_w * scale, target_h * scale
    surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
    cx, cy = sw // 2, sh // 2

    # Drop shadow canvas
    shadow = pygame.Surface((sw, sh), pygame.SRCALPHA)

    if symbol_type == SEVEN:
        # Metallic bevelled Red 7 with Gold outline
        pts = [(cx-60, cy-110), (cx+70, cy-110), (cx+15, cy+110), (cx-35, cy+110), (cx+25, cy-45), (cx-60, cy-45)]
        pygame.draw.polygon(shadow, (0, 0, 0, 120), [(x+12, y+12) for x, y in pts])
        pygame.draw.polygon(surf, (212, 163, 89), pts) # Gold outer
        inner_pts = [(cx-50, cy-100), (cx+58, cy-100), (cx+8, cy+100), (cx-28, cy+100), (cx+28, cy-35), (cx-50, cy-35)]
        pygame.draw.polygon(surf, (220, 20, 30), inner_pts) # Red body
        # Highlight
        pygame.draw.polygon(surf, (255, 140, 140), [(cx-45, cy-95), (cx+50, cy-95), (cx+40, cy-80), (cx-45, cy-80)])

    elif symbol_type == BAR:
        # 3D Inset Badge
        rect = pygame.Rect(cx-140, cy-70, 280, 140)
        pygame.draw.rect(shadow, (0, 0, 0, 140), rect.move(10, 10), border_radius=20)
        pygame.draw.rect(surf, (220, 180, 70), rect, border_radius=20)
        pygame.draw.rect(surf, (20, 20, 25), rect.inflate(-16, -16), border_radius=16)
        
        font = pygame.font.SysFont("impact", 80, bold=True)
        txt = font.render("BAR", True, (245, 245, 240))
        surf.blit(txt, txt.get_rect(center=(cx, cy)))

    elif symbol_type == BELL:
        # 3D Brass Liberty Bell
        pts = [(cx, cy-110), (cx+35, cy-95), (cx+60, cy-30), (cx+105, cy+70), (cx-105, cy+70), (cx-60, cy-30), (cx-35, cy-95)]
        pygame.draw.polygon(shadow, (0, 0, 0, 120), [(x+10, y+10) for x, y in pts])
        pygame.draw.polygon(surf, (230, 160, 20), pts)
        
        # Bell Rim & Clapper
        pygame.draw.circle(surf, (50, 40, 30), (cx, cy+85), 25)
        pygame.draw.ellipse(surf, (255, 210, 60), (cx-115, cy+55, 230, 35))
        pygame.draw.ellipse(surf, (170, 100, 0), (cx-115, cy+55, 230, 35), 6)
        # Glare
        pygame.draw.arc(surf, (255, 245, 180), (cx-80, cy-80, 120, 140), 1.8, 3.2, 14)

    elif symbol_type == CHERRY:
        # Glossy Dual Cherries
        c1, c2 = (cx-45, cy+30), (cx+45, cy+40)
        stem_top = (cx+10, cy-90)
        
        # Stems
        pygame.draw.line(surf, (70, 120, 30), c1, stem_top, 12)
        pygame.draw.line(surf, (90, 150, 40), c2, stem_top, 12)
        # Leaf
        pygame.draw.ellipse(surf, (100, 180, 40), (stem_top[0]-45, stem_top[1]-10, 50, 25))
        
        for center in [c1, c2]:
            pygame.draw.circle(shadow, (0, 0, 0, 100), (center[0]+8, center[1]+8), 48)
            pygame.draw.circle(surf, (150, 10, 30), center, 48)
            pygame.draw.circle(surf, (230, 30, 50), (center[0]-6, center[1]-6), 40)
            pygame.draw.circle(surf, (255, 255, 255), (center[0]-16, center[1]-16), 10)

    elif symbol_type == LEMON:
        # Textured Citrus Oval
        rect = pygame.Rect(cx-110, cy-70, 220, 140)
        pygame.draw.ellipse(shadow, (0, 0, 0, 110), rect.move(8, 10))
        pygame.draw.ellipse(surf, (240, 190, 10), rect)
        pygame.draw.ellipse(surf, (255, 235, 50), rect.inflate(-16, -16))
        pygame.draw.ellipse(surf, (255, 255, 220), (cx-70, cy-45, 90, 45))

    elif symbol_type == GRAPE:
        # Cluster of Grapes
        stem = (cx, cy-80)
        pygame.draw.circle(surf, (100, 160, 30), stem, 12)
        circles = [(0, -40), (-35, -15), (35, -15), (-50, 20), (0, 20), (50, 20), (-25, 55), (25, 55), (0, 85)]
        
        for ox, oy in circles:
            gx, gy = cx + ox, cy + oy
            pygame.draw.circle(shadow, (0, 0, 0, 90), (gx+6, gy+6), 26)
            pygame.draw.circle(surf, (80, 20, 110), (gx, gy), 26)
            pygame.draw.circle(surf, (150, 50, 200), (gx-4, gy-4), 20)
            pygame.draw.circle(surf, (255, 255, 255), (gx-8, gy-8), 5)

    elif symbol_type == ORANGE:
        # Glossy Spherical Orange
        pygame.draw.circle(shadow, (0, 0, 0, 110), (cx+8, cy+8), 85)
        pygame.draw.circle(surf, (210, 90, 10), (cx, cy), 85)
        pygame.draw.circle(surf, (255, 145, 20), (cx-4, cy-4), 78)
        pygame.draw.circle(surf, (255, 190, 90), (cx-20, cy-20), 45)
        pygame.draw.circle(surf, (255, 255, 255), (cx-30, cy-30), 12)

    # Composite Shadow & Sprite, smoothscale down to target size (Anti-Aliased)
    final_hi_res = pygame.Surface((sw, sh), pygame.SRCALPHA)
    final_hi_res.blit(shadow, (0, 0))
    final_hi_res.blit(surf, (0, 0))
    
    return pygame.transform.smoothscale(final_hi_res, (target_w, target_h))

# ============================================================
#               SYSTEM DISPLAY & ASSET CACHE
# ============================================================

WIDTH, HEIGHT = 900, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vintage Vegas Slots - HD Asset Engine")
clock = pygame.time.Clock()

# Pre-render sprite textures
SYMBOL_SPRITES = {sym: create_hd_symbol_sprite(sym, 100, 80) for sym in SLOT_SYMBOLS}

ui_font = pygame.font.SysFont("sans-serif", 22, bold=True)
label_font = pygame.font.SysFont("sans-serif", 14, bold=True)
_lobby_hint_font = pygame.font.SysFont("sans-serif", 18)

# ============================================================
#                         MAIN GAME
# ============================================================

async def run_slots(balance=100):
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

    final_results = [SEVEN, SEVEN, SEVEN]
    is_spinning = False
    spin_phase_timer = 0

    lever_state = 0
    lever_offset_y = 0

    lever_knob_rect = pygame.Rect(760, 240, 50, 50)
    dec_bet_rect = pygame.Rect(190, 540, 40, 35)
    inc_bet_rect = pygame.Rect(280, 540, 40, 35)

    def draw_quarter_token(surface, x, y):
        pygame.draw.ellipse(surface, (90, 95, 100), (x - 12, y - 7, 24, 14))
        pygame.draw.ellipse(surface, (200, 205, 210), (x - 11, y - 6, 22, 12))
        pygame.draw.ellipse(surface, (240, 245, 250), (x - 6, y - 5, 12, 5))

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

        # ============================================================
        #                     RENDERING FRAME
        # ============================================================

        screen.fill((56, 18, 11))
        pygame.draw.rect(screen, (84, 30, 20), (10, 10, WIDTH - 20, HEIGHT - 20), 10)
        pygame.draw.rect(screen, (10, 68, 33), (20, 20, WIDTH - 40, HEIGHT - 40))

        # Top Winner Dome
        light_center_x, light_y = 400, 35
        dome_color = (255, 255, 255) if (win_light_timer > 0 and (win_light_timer // 10) % 2 == 0) else (210, 25, 25)

        pygame.draw.rect(screen, (110, 110, 110), (light_center_x - 30, light_y + 15, 60, 12))
        pygame.draw.ellipse(screen, dome_color, (light_center_x - 22, light_y - 15, 44, 32))

        # Main Cabinet Bezel
        cab_rect = pygame.Rect(120, 60, 560, 630)
        pygame.draw.rect(screen, (110, 110, 110), cab_rect)
        pygame.draw.rect(screen, (220, 220, 220), cab_rect.inflate(-6, -6))
        pygame.draw.rect(screen, (175, 175, 175), cab_rect.inflate(-12, -12))

        # Paytable Marquee Box
        pygame.draw.rect(screen, (145, 105, 45), (150, 80, 500, 130))
        pygame.draw.rect(screen, (212, 163, 89), (152, 82, 496, 126), 2)

        # Restored Clean Multi-Line Text Layout
        p_line1 = label_font.render("7-7-7: x30  |  BAR-BAR-BAR: x20  |  ORANGE x3: x100", True, (24, 24, 24))
        p_line2 = label_font.render("GRAPE x3: x60  |  LEMON x3: x40  |  BELL x3: x10", True, (24, 24, 24))
        p_line3 = label_font.render("CHERRY x1: x1  |  CHERRY x2: x2  |  CHERRY x3: x5", True, (247, 245, 230))
        screen.blit(p_line1, (170, 100))
        screen.blit(p_line2, (170, 132))
        screen.blit(p_line3, (170, 164))

        # Reel Housing Window
        pygame.draw.rect(screen, (24, 24, 24), (146, 236, 508, 138))
        pygame.draw.rect(screen, (110, 110, 110), (150, 240, 500, 130))

        # Render Smooth Blitted Sprite Reels
        for idx in range(3):
            rx, ry = 185 + (idx * 155), 255
            pygame.draw.rect(screen, (247, 245, 230), (rx, ry, 115, 100))

            reel_clip_rect = pygame.Rect(rx, ry, 115, 100)
            screen.set_clip(reel_clip_rect)

            current_sym = reels_state[idx][0]
            offset_y = reels_state[idx][1]
            incoming_sym = reels_state[idx][2]

            # Direct Surface Blits of smooth anti-aliased sprites
            c_sprite = SYMBOL_SPRITES[current_sym]
            screen.blit(c_sprite, c_sprite.get_rect(center=(rx + 57, ry + 50 + offset_y)))

            if reels_state[idx][3]:
                i_sprite = SYMBOL_SPRITES[incoming_sym]
                screen.blit(i_sprite, i_sprite.get_rect(center=(rx + 57, ry - 50 + offset_y)))

            screen.set_clip(None)

            # Inset Reel Bezel Shadows
            pygame.draw.rect(screen, (180, 180, 170), (rx, ry, 115, 10))
            pygame.draw.rect(screen, (180, 180, 170), (rx, ry + 90, 115, 10))
            pygame.draw.rect(screen, (24, 24, 24), (rx, ry, 115, 100), 2)

        # Control Panel
        pygame.draw.rect(screen, (24, 24, 24), (150, 400, 500, 180))

        message_color = (212, 163, 89) if ("WINNER" in win_message or "WELCOME" in win_message) else (210, 25, 25)
        msg_surf = ui_font.render(win_message, True, message_color)
        screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2 - 50, 415))

        bal_lbl = label_font.render(f"BANK TOTAL: ${balance}", True, (247, 245, 230))
        bet_lbl = label_font.render(f"WAGER SELECTION: ${bet_amount}", True, (212, 163, 89))
        screen.blit(bal_lbl, (170, 460))
        screen.blit(bet_lbl, (170, 505))

        # Wager Control Buttons
        for rect, symbol in [(dec_bet_rect, "-"), (inc_bet_rect, "+")]:
            pygame.draw.rect(screen, (120, 10, 10), rect, 0, 4)
            pygame.draw.rect(screen, (210, 25, 25), (rect.x, rect.y, rect.width, rect.height - 4), 0, 4)
            button_text = label_font.render(symbol, True, (247, 245, 230))
            screen.blit(button_text, (rect.centerx - button_text.get_width() // 2, rect.y + 6))

        # Coin Tray
        tray_rect = pygame.Rect(300, 620, 200, 55)
        pygame.draw.rect(screen, (24, 24, 24), tray_rect, border_radius=8)

        for cx, cy in tray_coins:
            draw_quarter_token(screen, cx, cy)

        for coin in active_coins:
            if coin['delay'] <= 0:
                draw_quarter_token(screen, int(coin['x']), int(coin['y']))

        # Side Mechanical Pull Arm
        lever_knob_rect.y = 240 + lever_offset_y
        pygame.draw.line(screen, (220, 220, 220), (680, 310), (785, 260 + lever_offset_y), 14)
        pygame.draw.circle(screen, (210, 25, 25), (785, 260 + lever_offset_y), 24)
        pygame.draw.circle(screen, (255, 255, 255), (776, 252 + lever_offset_y), 6)

        _hint_surf = _lobby_hint_font.render("ESC: Return to Lobby", True, (230, 200, 140))
        screen.blit(_hint_surf, (10, HEIGHT - 22))

        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(60)

    return balance

if __name__ == "__main__":
    asyncio.run(run_slots(100))
