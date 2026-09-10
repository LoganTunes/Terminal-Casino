import asyncio
import array
import math
import random
import sys
import pygame

# ============================================================
#                 PYGAME & DISPLAY GLOBALS
# ============================================================

WIDTH, HEIGHT = 950, 720

# Audio Globals
snd_card_slide = None
snd_chip = None
snd_win = None
snd_lose = None

# Shared Vector Suit Icon Caches (Lazy loaded inside init_suit_icons)
SUIT_ICONS_32 = {}
SUIT_ICONS_16 = {}

SUITS = ["♥", "♦", "♣", "♠"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

# ============================================================
#                         COLOR PALETTE
# ============================================================

FELT_GREEN = (12, 82, 42)
MAHOGANY = (42, 12, 6)
WOOD_LIGHT = (75, 26, 14)
LEATHER_RAIL = (24, 8, 4)

CHROME_SHADOW = (80, 80, 80)
VINTAGE_GOLD = (212, 163, 89)
GOLD_TEXT = (230, 185, 105)
GOLD_SHADOW = (145, 105, 45)

CREAM_WHITE = (247, 245, 230)
CHARCOAL = (20, 20, 20)
BRIGHT_RED = (190, 25, 25)


# ============================================================
#          MATHEMATICALLY ACCURATE VECTOR SUIT GENERATOR
# ============================================================

def create_flat_suit_icon(suit_type, size=32):
    scale = 4
    high_res = size * scale
    surf_high = pygame.Surface((high_res, high_res), pygame.SRCALPHA)
    color = BRIGHT_RED if suit_type in ["♥", "♦"] else CHARCOAL
    center = high_res / 2

    if suit_type == "♦":
        pts = [
            (center, high_res * 0.05),
            (high_res * 0.88, center),
            (center, high_res * 0.95),
            (high_res * 0.12, center),
        ]
        pygame.draw.polygon(surf_high, color, pts)

    elif suit_type == "♥":
        pts = []
        steps = 120
        for i in range(steps):
            t = (i / steps) * 2 * math.pi
            x = 16 * (math.sin(t) ** 3)
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))

            px = center + (x / 17.5) * (high_res * 0.45)
            py = (center + 2) + (y / 17.5) * (high_res * 0.42)
            pts.append((px, py))
        pygame.draw.polygon(surf_high, color, pts)

    elif suit_type == "♠":
        pts = []
        steps = 120
        for i in range(steps):
            t = (i / steps) * 2 * math.pi
            x = 16 * (math.sin(t) ** 3)
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)

            px = center + (x / 17.5) * (high_res * 0.42)
            py = (center - high_res * 0.08) + (y / 17.5) * (high_res * 0.40)
            pts.append((px, py))
        pygame.draw.polygon(surf_high, color, pts)

        stem = [
            (center - high_res * 0.04, center),
            (center + high_res * 0.04, center),
            (center + high_res * 0.10, high_res * 0.90),
            (center - high_res * 0.10, high_res * 0.90),
        ]
        pygame.draw.polygon(surf_high, color, stem)

    elif suit_type == "♣":
        r = high_res * 0.23
        pygame.draw.circle(surf_high, color, (int(center), int(high_res * 0.32)), int(r))
        pygame.draw.circle(surf_high, color, (int(high_res * 0.30), int(high_res * 0.52)), int(r))
        pygame.draw.circle(surf_high, color, (int(high_res * 0.70), int(high_res * 0.52)), int(r))
        pygame.draw.circle(surf_high, color, (int(center), int(high_res * 0.48)), int(r * 0.8))

        stem = [
            (center - high_res * 0.04, center),
            (center + high_res * 0.04, center),
            (center + high_res * 0.10, high_res * 0.90),
            (center - high_res * 0.10, high_res * 0.90),
        ]
        pygame.draw.polygon(surf_high, color, stem)

    return pygame.transform.smoothscale(surf_high, (size, size))


def init_suit_icons():
    """Deferred suit generator: avoids executing before display surface init."""
    global SUIT_ICONS_32, SUIT_ICONS_16
    if not SUIT_ICONS_32:
        SUIT_ICONS_32 = {s: create_flat_suit_icon(s, 32) for s in SUITS}
        SUIT_ICONS_16 = {s: create_flat_suit_icon(s, 16) for s in SUITS}


# ============================================================
#               REALISTIC CASINO AUDIO SYNTH ENGINE
# ============================================================

class DummySound:
    def play(self):
        pass


def safe_create_sound(func):
    try:
        return func()
    except Exception as e:
        print(f"[Audio Warning] {e}")
        return DummySound()


def create_card_slide_sound():
    sample_rate = 22050
    duration_ms = 70
    total_samples = int(sample_rate * (duration_ms / 1000.0))
    buffer = array.array("h", [0] * total_samples)

    last_val = 0
    for i in range(total_samples):
        env = math.sin(math.pi * (i / total_samples))
        raw = random.randint(-16000, 16000)
        filtered = int((raw + last_val) / 2)
        last_val = filtered
        buffer[i] = int(filtered * env * 0.25)

    return pygame.mixer.Sound(buffer=buffer)


def create_chip_click_sound():
    sample_rate = 22050
    duration_ms = 35
    total_samples = int(sample_rate * (duration_ms / 1000.0))
    buffer = array.array("h", [0] * total_samples)

    for i in range(total_samples):
        t = i / sample_rate
        env = math.exp(-t * 120)
        tone = math.sin(2 * math.pi * 2400 * t) * 0.6
        noise = (random.randint(-32768, 32767) / 32768.0) * 0.4
        val = int((tone + noise) * env * 32767 * 0.3)
        buffer[i] = max(-32768, min(32767, val))

    return pygame.mixer.Sound(buffer=buffer)


def create_win_chime_sound():
    sample_rate = 22050
    duration_ms = 500
    total_samples = int(sample_rate * (duration_ms / 1000.0))
    buffer = array.array("h", [0] * total_samples)

    freqs = [880.0, 1108.73, 1318.51]

    for i in range(total_samples):
        t = i / sample_rate
        env = math.exp(-t * 6.0)
        mixed_wave = 0
        for f in freqs:
            mixed_wave += math.sin(2 * math.pi * f * t)
        val = int((mixed_wave / len(freqs)) * env * 32767 * 0.2)
        buffer[i] = max(-32768, min(32767, val))

    return pygame.mixer.Sound(buffer=buffer)


def create_loss_sound():
    sample_rate = 22050
    duration_ms = 180
    total_samples = int(sample_rate * (duration_ms / 1000.0))
    buffer = array.array("h", [0] * total_samples)

    for i in range(total_samples):
        t = i / sample_rate
        env = math.exp(-t * 20)
        tone = math.sin(2 * math.pi * 90 * t)
        buffer[i] = int(tone * env * 32767 * 0.25)

    return pygame.mixer.Sound(buffer=buffer)


def init_audio():
    global snd_card_slide, snd_chip, snd_win, snd_lose
    if snd_card_slide is None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            snd_card_slide = safe_create_sound(create_card_slide_sound)
            snd_chip = safe_create_sound(create_chip_click_sound)
            snd_win = safe_create_sound(create_win_chime_sound)
            snd_lose = safe_create_sound(create_loss_sound)
        except Exception as err:
            print(f"Audio init bypassed: {err}")
            snd_card_slide = snd_chip = snd_win = snd_lose = DummySound()


# ============================================================
#                      ANIMATED CARD CLASS
# ============================================================

DECK_SHOE_POS = (730, 25)


class AnimatedCard:

    def __init__(self, card_data, target_x, target_y, facedown=False):
        self.card_data = card_data
        self.x = float(DECK_SHOE_POS[0])
        self.y = float(DECK_SHOE_POS[1])
        self.target_x = float(target_x)
        self.target_y = float(target_y)
        self.facedown = facedown
        self.flip_progress = 1.0 if not facedown else 0.0
        self.is_flipping = False
        if snd_card_slide:
            snd_card_slide.play()

    def update(self):
        self.x += (self.target_x - self.x) * 0.2
        self.y += (self.target_y - self.y) * 0.2

        if self.is_flipping:
            self.flip_progress += 0.08
            if self.flip_progress >= 1.0:
                self.flip_progress = 1.0
                self.is_flipping = False
                self.facedown = False

    def trigger_flip(self):
        if self.facedown and not self.is_flipping:
            self.is_flipping = True
            self.flip_progress = 0.0
            if snd_card_slide:
                snd_card_slide.play()


def draw_card_surface(card_data, card_num_font, facedown=False, flip_scale=1.0):
    width = int(75 * abs(flip_scale))
    height = 110
    if width < 1:
        return None

    surf = pygame.Surface((width, height), pygame.SRCALPHA)

    if facedown or flip_scale < 0:
        pygame.draw.rect(surf, WOOD_LIGHT, (0, 0, width, height), 0, 6)
        pygame.draw.rect(surf, VINTAGE_GOLD, (3, 3, max(1, width - 6), height - 6), 2, 4)
        pygame.draw.rect(surf, CHARCOAL, (5, 5, max(1, width - 10), height - 10), 0, 2)
    else:
        rank, suit = card_data
        pygame.draw.rect(surf, CREAM_WHITE, (0, 0, width, height), 0, 6)
        pygame.draw.rect(surf, CHROME_SHADOW, (0, 0, width, height), 1, 6)

        txt_color = BRIGHT_RED if suit in ["♥", "♦"] else CHARCOAL

        if abs(flip_scale) > 0.35:
            num_surf = card_num_font.render(rank, True, txt_color)
            surf.blit(num_surf, (5, 3))

            s_icon_small = SUIT_ICONS_16[suit]
            surf.blit(s_icon_small, (6, 24))

            s_icon = SUIT_ICONS_32[suit]
            surf.blit(s_icon, (width // 2 - 16, height // 2 - 10))

    return surf


def draw_card(surface, card_obj, card_num_font):
    if card_obj.is_flipping:
        scale = math.cos(card_obj.flip_progress * math.pi)
    else:
        scale = -1.0 if card_obj.facedown else 1.0

    c_surf = draw_card_surface(card_obj.card_data, card_num_font, card_obj.facedown, flip_scale=scale)
    if c_surf:
        draw_x = card_obj.x + (75 - c_surf.get_width()) // 2
        pygame.draw.rect(surface, CHARCOAL, (card_obj.x + 2, card_obj.y + 2, 75, 110), 0, 6)
        surface.blit(c_surf, (draw_x, card_obj.y))


# ============================================================
#             BLACKJACK ENGINE & GAME ROUTINE
# ============================================================

def create_blackjack_deck():
    deck = []
    for _ in range(6):
        for suit in SUITS:
            for rank in RANKS:
                deck.append((rank, suit))
    random.shuffle(deck)
    return deck


def calculate_blackjack_hand_value(hand):
    value = 0
    aces = 0
    for card in hand:
        rank = card.card_data[0]
        if rank in ["J", "Q", "K"]:
            value += 10
        elif rank == "A":
            value += 11
            aces += 1
        else:
            value += int(rank)

    while value > 21 and aces > 0:
        value -= 10
        aces -= 1

    return value


async def run_blackjack(balance):
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

    init_suit_icons()
    init_audio()

    clock = pygame.time.Clock()

    ui_font = pygame.font.Font(None, 24)
    label_font = pygame.font.Font(None, 18)
    stencil_large = pygame.font.Font(None, 22)
    stencil_small = pygame.font.Font(None, 16)
    card_num_font = pygame.font.Font(None, 22)
    chip_num_font = pygame.font.Font(None, 14)
    _lobby_hint_font = pygame.font.Font(None, 16)

    pygame.event.clear()

    running = True
    active_chip_wager = 10
    current_bet = 0
    win_message = "SELECT A CHIP VALUE & PLACE A BET!"
    game_stage = "BETTING"

    deck = create_blackjack_deck()
    player_hand = []
    dealer_hand = []

    dealer_timer = 0
    DEALER_DRAW_DELAY = 900

    betting_spots = [
        pygame.Rect(185, 420, 60, 60),
        pygame.Rect(315, 430, 60, 60),
        pygame.Rect(445, 435, 60, 60),
        pygame.Rect(575, 430, 60, 60),
        pygame.Rect(705, 420, 60, 60),
    ]

    deal_box_rect = betting_spots[2]

    hit_btn_rect = pygame.Rect(290, 520, 100, 42)
    stand_btn_rect = pygame.Rect(400, 520, 100, 42)
    double_btn_rect = pygame.Rect(510, 520, 100, 42)

    deal_trigger_rect = pygame.Rect(330, 520, 135, 42)
    clear_btn_rect = pygame.Rect(485, 520, 135, 42)

    chip_selections = [
        (10, pygame.Rect(650, 526, 30, 30), (240, 240, 240), (40, 40, 40)),
        (50, pygame.Rect(688, 526, 30, 30), (180, 30, 30), (240, 240, 240)),
        (100, pygame.Rect(726, 526, 30, 30), (30, 80, 180), (240, 240, 240)),
        (250, pygame.Rect(764, 526, 30, 30), (30, 130, 60), (212, 163, 89)),
        (1000, pygame.Rect(802, 526, 30, 30), (40, 40, 40), (230, 185, 105)),
    ]

    def draw_wood_panel(surface, rect):
        pygame.draw.rect(surface, WOOD_LIGHT, rect, 0, 6)
        pygame.draw.rect(surface, VINTAGE_GOLD, rect, 2, 6)
        pygame.draw.rect(surface, MAHOGANY, (rect.x + 3, rect.y + 3, rect.width - 6, rect.height - 6), 0, 4)

    def draw_chip_stack(surface, rect, text_val):
        bg_color = (240, 240, 240)
        stripe_color = (40, 40, 40)

        for val, _, col_bg, col_str in chip_selections:
            if text_val >= val:
                bg_color = col_bg
                stripe_color = col_str

        cx, cy = rect.centerx, rect.centery
        pygame.draw.circle(surface, CHARCOAL, (cx, cy + 2), 15)
        pygame.draw.circle(surface, bg_color, (cx, cy), 15)

        for angle in [0, 90, 180, 270]:
            rad = math.radians(angle)
            sx = cx + math.cos(rad) * 11
            sy = cy + math.sin(rad) * 11
            pygame.draw.circle(surface, stripe_color, (int(sx), int(sy)), 2)

        pygame.draw.circle(surface, CREAM_WHITE, (cx, cy), 8)
        display_str = str(text_val) if text_val < 1000 else f"{text_val // 1000}k"
        c_txt = chip_num_font.render(display_str, True, CHARCOAL)
        surface.blit(c_txt, (cx - c_txt.get_width() // 2, cy - c_txt.get_height() // 2))

    def draw_table_stencils(surface):
        bj_txt = stencil_large.render("BLACKJACK PAYS 3 TO 2", True, GOLD_TEXT)
        surface.blit(bj_txt, (WIDTH // 2 - bj_txt.get_width() // 2, 190))

        d_rule = stencil_small.render("Dealer must draw to 16 and stand on all 17s", True, GOLD_TEXT)
        surface.blit(d_rule, (WIDTH // 2 - d_rule.get_width() // 2, 215))

        ins_txt = stencil_small.render("INSURANCE PAYS 2 TO 1", True, GOLD_TEXT)
        surface.blit(ins_txt, (WIDTH // 2 - ins_txt.get_width() // 2, 233))

        pygame.draw.arc(surface, GOLD_TEXT, (100, 140, 750, 220), math.radians(195), math.radians(345), 2)

        for i, rect in enumerate(betting_spots):
            color = GOLD_TEXT if i == 2 else GOLD_SHADOW
            pygame.draw.ellipse(surface, color, rect, 2)
            if i != 2:
                lbl = label_font.render("BET", True, GOLD_SHADOW)
                surface.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))

    def draw_dealer_chip_rack(surface):
        rack_rect = pygame.Rect(WIDTH // 2 - 139, 10, 278, 34)
        pygame.draw.rect(surface, WOOD_LIGHT, rack_rect, 0, 4)
        pygame.draw.rect(surface, VINTAGE_GOLD, rack_rect, 2, 4)

        rack_colors = [(240, 240, 240), (180, 30, 30), (30, 80, 180), (30, 130, 60), (40, 40, 40)]

        for i, col in enumerate(rack_colors):
            slot_x = (WIDTH // 2 - 131) + (i * 52)
            pygame.draw.rect(surface, CHARCOAL, (slot_x, 14, 44, 26), 0, 3)
            for c in range(6):
                pygame.draw.ellipse(surface, col, (slot_x + (c * 6), 16, 10, 22))

    def process_dealer_turn(current_time):
        nonlocal dealer_timer, game_stage, win_message, balance, current_bet, deck

        if len(dealer_hand) > 1 and dealer_hand[1].facedown:
            dealer_hand[1].trigger_flip()
            dealer_timer = current_time
            return

        if any(card.is_flipping for card in dealer_hand):
            return

        if current_time - dealer_timer < DEALER_DRAW_DELAY:
            return

        d_val = calculate_blackjack_hand_value(dealer_hand)

        if d_val < 17:
            if len(deck) < 15:
                deck = create_blackjack_deck()
            idx = len(dealer_hand)
            target_x = 350 + (idx * 85)
            dealer_hand.append(AnimatedCard(deck.pop(), target_x, 55))
            dealer_timer = current_time
        else:
            p_val = calculate_blackjack_hand_value(player_hand)
            game_stage = "RESOLVED"

            if d_val > 21:
                win_message = f"DEALER BUSTS WITH {d_val}! YOU WIN +${current_bet * 2}!"
                balance += current_bet * 2
                snd_win.play()
            elif p_val > d_val:
                win_message = f"YOU WIN WITH {p_val} OVER {d_val}! +${current_bet * 2}!"
                balance += current_bet * 2
                snd_win.play()
            elif p_val < d_val:
                win_message = f"DEALER WINS WITH {d_val} OVER {p_val}!"
                snd_lose.play()
            else:
                win_message = f"PUSH! Hand ties at {p_val}. Bet returned."
                balance += current_bet
                snd_chip.play()

            current_bet = 0

    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                if game_stage == "BETTING":
                    for val, rect, c1, c2 in chip_selections:
                        if rect.collidepoint(mouse_pos):
                            active_chip_wager = val
                            snd_chip.play()

                    if clear_btn_rect.collidepoint(mouse_pos):
                        balance += current_bet
                        current_bet = 0
                        snd_chip.play()

                    if deal_box_rect.collidepoint(mouse_pos):
                        if balance >= active_chip_wager:
                            current_bet += active_chip_wager
                            balance -= active_chip_wager
                            snd_chip.play()

                    if deal_trigger_rect.collidepoint(mouse_pos):
                        if current_bet > 0:
                            if len(deck) < 15:
                                deck = create_blackjack_deck()

                            player_hand = [
                                AnimatedCard(deck.pop(), 350, 275),
                                AnimatedCard(deck.pop(), 435, 275),
                            ]
                            dealer_hand = [
                                AnimatedCard(deck.pop(), 350, 55),
                                AnimatedCard(deck.pop(), 435, 55, facedown=True),
                            ]

                            p_val = calculate_blackjack_hand_value(player_hand)

                            if p_val == 21:
                                game_stage = "RESOLVED"
                                bj_payout = int(current_bet * 2.5)
                                balance += bj_payout
                                win_message = f"NATURAL BLACKJACK! Payout: +${bj_payout}!"
                                current_bet = 0
                                dealer_hand[1].trigger_flip()
                                snd_win.play()
                            else:
                                game_stage = "PLAYING"
                                win_message = "HIT, STAND, OR DOUBLE?"
                        else:
                            win_message = "PLACE A CHIP IN THE CENTER BETTING CIRCLE FIRST!"

                elif game_stage == "PLAYING":
                    if hit_btn_rect.collidepoint(mouse_pos):
                        if len(deck) < 15:
                            deck = create_blackjack_deck()
                        idx = len(player_hand)
                        target_x = 350 + (idx * 85)
                        player_hand.append(AnimatedCard(deck.pop(), target_x, 275))

                        p_val = calculate_blackjack_hand_value(player_hand)

                        if p_val > 21:
                            game_stage = "RESOLVED"
                            win_message = f"BUSTED WITH {p_val}! Dealer wins table."
                            current_bet = 0
                            dealer_hand[1].trigger_flip()
                            snd_lose.play()

                    elif stand_btn_rect.collidepoint(mouse_pos):
                        game_stage = "DEALER_TURN"
                        win_message = "DEALER PLAYS..."
                        dealer_timer = current_time

                    elif (
                        double_btn_rect.collidepoint(mouse_pos)
                        and len(player_hand) == 2
                        and balance >= current_bet
                    ):
                        balance -= current_bet
                        current_bet *= 2
                        snd_chip.play()

                        if len(deck) < 15:
                            deck = create_blackjack_deck()

                        idx = len(player_hand)
                        target_x = 350 + (idx * 85)
                        player_hand.append(AnimatedCard(deck.pop(), target_x, 275))

                        p_val = calculate_blackjack_hand_value(player_hand)

                        if p_val > 21:
                            game_stage = "RESOLVED"
                            win_message = f"BUSTED ON DOUBLE WITH {p_val}! Dealer wins."
                            current_bet = 0
                            dealer_hand[1].trigger_flip()
                            snd_lose.play()
                        else:
                            game_stage = "DEALER_TURN"
                            win_message = "DEALER PLAYS..."
                            dealer_timer = current_time

                elif game_stage == "RESOLVED":
                    if (
                        deal_trigger_rect.collidepoint(mouse_pos)
                        or clear_btn_rect.collidepoint(mouse_pos)
                        or deal_box_rect.collidepoint(mouse_pos)
                    ):
                        player_hand.clear()
                        dealer_hand.clear()
                        game_stage = "BETTING"
                        win_message = "PLACE A WAGER TO INITIATE NEW ROUND."

        if game_stage == "DEALER_TURN":
            process_dealer_turn(current_time)

        for card in player_hand + dealer_hand:
            card.update()

        screen.fill(MAHOGANY)

        pygame.draw.ellipse(screen, LEATHER_RAIL, (-60, -180, WIDTH + 120, HEIGHT + 600))
        pygame.draw.ellipse(screen, WOOD_LIGHT, (-45, -165, WIDTH + 90, HEIGHT + 570))
        pygame.draw.ellipse(screen, FELT_GREEN, (-30, -150, WIDTH + 60, HEIGHT + 540))

        draw_table_stencils(screen)
        draw_dealer_chip_rack(screen)

        pygame.draw.rect(screen, CHARCOAL, (DECK_SHOE_POS[0], DECK_SHOE_POS[1], 75, 105), 0, 5)
        pygame.draw.rect(screen, VINTAGE_GOLD, (DECK_SHOE_POS[0] + 4, DECK_SHOE_POS[1] + 4, 67, 97), 2, 4)

        d_lbl = label_font.render("DEALER", True, VINTAGE_GOLD)
        screen.blit(d_lbl, (260, 60))

        if (
            game_stage in ["RESOLVED", "DEALER_TURN"]
            and len(dealer_hand) > 1
            and not dealer_hand[1].facedown
        ):
            d_val_txt = label_font.render(f"Score: {calculate_blackjack_hand_value(dealer_hand)}", True, CREAM_WHITE)
            screen.blit(d_val_txt, (260, 80))

        for card in dealer_hand:
            draw_card(screen, card, card_num_font)

        p_lbl = label_font.render("PLAYER", True, VINTAGE_GOLD)
        screen.blit(p_lbl, (260, 280))

        if len(player_hand) > 0:
            p_val_txt = label_font.render(f"Score: {calculate_blackjack_hand_value(player_hand)}", True, CREAM_WHITE)
            screen.blit(p_val_txt, (260, 300))

        for card in player_hand:
            draw_card(screen, card, card_num_font)

        if game_stage == "BETTING":
            if current_bet == 0:
                b_lbl = label_font.render("BET HERE", True, GOLD_TEXT)
                screen.blit(b_lbl, (deal_box_rect.centerx - b_lbl.get_width() // 2, deal_box_rect.centery - b_lbl.get_height() // 2))
            else:
                draw_chip_stack(screen, deal_box_rect, current_bet)

        bank_rect = pygame.Rect(110, 512, 160, 55)
        draw_wood_panel(screen, bank_rect)

        bal_txt = ui_font.render(f"BANK: ${balance}", True, CREAM_WHITE)
        chip_txt = label_font.render(f"CHIP: ${active_chip_wager}", True, VINTAGE_GOLD)
        screen.blit(bal_txt, (120, 517))
        screen.blit(chip_txt, (120, 540))

        chip_panel_rect = pygame.Rect(638, 512, 205, 55)
        draw_wood_panel(screen, chip_panel_rect)

        for val, rect, col_bg, col_str in chip_selections:
            is_sel_chip = active_chip_wager == val

            if is_sel_chip:
                pygame.draw.circle(screen, VINTAGE_GOLD, rect.center, 17)

            pygame.draw.circle(screen, col_bg, rect.center, 14)

            if val == 1000:
                pygame.draw.circle(screen, VINTAGE_GOLD, rect.center, 14, 2)

            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                sx = rect.centerx + math.cos(rad) * 10
                sy = rect.centery + math.sin(rad) * 10
                pygame.draw.circle(screen, col_str, (int(sx), int(sy)), 2)

            pygame.draw.circle(screen, CREAM_WHITE if val != 1000 else CHARCOAL, rect.center, 8)
            display_str = str(val) if val < 1000 else f"{val // 1000}k"
            val_txt = chip_num_font.render(f"${display_str}", True, CHARCOAL if val != 1000 else VINTAGE_GOLD)
            screen.blit(val_txt, (rect.centerx - val_txt.get_width() // 2, rect.centery - val_txt.get_height() // 2))

        if game_stage == "PLAYING":
            buttons_to_draw = [
                (hit_btn_rect, "HIT", BRIGHT_RED, True),
                (stand_btn_rect, "STAND", WOOD_LIGHT, True),
            ]

            can_double = len(player_hand) == 2 and balance >= current_bet
            buttons_to_draw.append((double_btn_rect, "DOUBLE", GOLD_SHADOW if can_double else MAHOGANY, can_double))

            for btn_rect, label, bg, active in buttons_to_draw:
                pygame.draw.rect(screen, bg, btn_rect, 0, 5)
                pygame.draw.rect(screen, VINTAGE_GOLD if active else CHROME_SHADOW, btn_rect, 2, 5)
                b_txt = label_font.render(label, True, CREAM_WHITE if active else CHROME_SHADOW)
                screen.blit(b_txt, (btn_rect.centerx - b_txt.get_width() // 2, btn_rect.centery - b_txt.get_height() // 2))

        elif game_stage in ["BETTING", "RESOLVED"]:
            lbl_action = "DEAL HAND" if game_stage == "BETTING" else "RESET BOARD"

            for btn_rect, label, bg in [
                (deal_trigger_rect, lbl_action, BRIGHT_RED),
                (clear_btn_rect, "CLEAR CHIPS", WOOD_LIGHT),
            ]:
                pygame.draw.rect(screen, bg, btn_rect, 0, 5)
                pygame.draw.rect(screen, VINTAGE_GOLD, btn_rect, 2, 5)
                b_txt = label_font.render(label, True, CREAM_WHITE)
                screen.blit(b_txt, (btn_rect.centerx - b_txt.get_width() // 2, btn_rect.centery - b_txt.get_height() // 2))

        elif game_stage == "DEALER_TURN":
            for btn_rect, label in [(hit_btn_rect, "HIT"), (stand_btn_rect, "STAND"), (double_btn_rect, "DOUBLE")]:
                pygame.draw.rect(screen, MAHOGANY, btn_rect, 0, 5)
                pygame.draw.rect(screen, CHROME_SHADOW, btn_rect, 1, 5)
                b_txt = label_font.render(label, True, CHROME_SHADOW)
                screen.blit(b_txt, (btn_rect.centerx - b_txt.get_width() // 2, btn_rect.centery - b_txt.get_height() // 2))

        banner_rect = pygame.Rect(60, 585, 830, 45)
        draw_wood_panel(screen, banner_rect)

        msg_color = (
            VINTAGE_GOLD
            if ("WIN" in win_message or "NATURAL" in win_message)
            else BRIGHT_RED
            if ("FIRST" in win_message or "BUSTED" in win_message)
            else CREAM_WHITE
        )
        msg_surf = ui_font.render(win_message, True, msg_color)
        screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, 597))

        _hint_surf = _lobby_hint_font.render("ESC: Return to Lobby", True, (230, 200, 140))
        screen.blit(_hint_surf, (15, HEIGHT - 25))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    return balance


# ============================================================
#       ULTIMATE TEXAS HOLD 'EM ENGINE & HAND EVALUATOR
# ============================================================

RANK_MAP = {r: i for i, r in enumerate(RANKS, start=2)}


def evaluate_7_cards(cards):
    """Evaluates 7 cards and returns a tuple (rank_score, tiebreaker_list, hand_name)."""
    import itertools

    best_val = (-1,)
    best_name = ""

    for combo in itertools.combinations(cards, 5):
        val, name = _eval_5_cards(combo)
        if val > best_val:
            best_val = val
            best_name = name

    return best_val, best_name


def _eval_5_cards(cards):
    ranks = sorted([RANK_MAP[c[0]] for c in cards], reverse=True)
    suits = [c[1] for c in cards]

    is_flush = len(set(suits)) == 1
    is_straight = False
    straight_high = 0

    unique_ranks = sorted(list(set(ranks)), reverse=True)
    if len(unique_ranks) == 5:
        if unique_ranks[0] - unique_ranks[4] == 4:
            is_straight = True
            straight_high = unique_ranks[0]
        elif unique_ranks == [14, 5, 4, 3, 2]:
            is_straight = True
            straight_high = 5

    counts = {r: ranks.count(r) for r in unique_ranks}
    by_count = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)

    if is_straight and is_flush:
        if straight_high == 14:
            return (9, straight_high), "Royal Flush"
        return (8, straight_high), "Straight Flush"

    if by_count[0][1] == 4:
        kicker = by_count[1][0]
        return (7, by_count[0][0], kicker), "Four of a Kind"

    if by_count[0][1] == 3 and by_count[1][1] == 2:
        return (6, by_count[0][0], by_count[1][0]), "Full House"

    if is_flush:
        return (5,) + tuple(ranks), "Flush"

    if is_straight:
        return (4, straight_high), "Straight"

    if by_count[0][1] == 3:
        kickers = tuple([r for r, _ in by_count[1:]])
        return (3, by_count[0][0]) + kickers, "Three of a Kind"

    if by_count[0][1] == 2 and by_count[1][1] == 2:
        kicker = by_count[2][0]
        return (2, max(by_count[0][0], by_count[1][0]), min(by_count[0][0], by_count[1][0]), kicker), "Two Pair"

    if by_count[0][1] == 2:
        kickers = tuple([r for r, _ in by_count[1:]])
        return (1, by_count[0][0]) + kickers, "Pair"

    return (0,) + tuple(ranks), "High Card"


async def run_ultimate_holdem(balance):
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

    init_suit_icons()
    init_audio()

    clock = pygame.time.Clock()

    ui_font = pygame.font.Font(None, 24)
    label_font = pygame.font.Font(None, 18)
    stencil_large = pygame.font.Font(None, 22)
    stencil_small = pygame.font.Font(None, 16)
    card_num_font = pygame.font.Font(None, 22)
    chip_num_font = pygame.font.Font(None, 14)
    _lobby_hint_font = pygame.font.Font(None, 16)

    pygame.event.clear()

    running = True
    active_chip_wager = 10

    ante_bet = 0
    blind_bet = 0
    play_bet = 0
    trips_bet = 0

    win_message = "PLACE ANTE & BLIND BETS (AUTOMATICALLY MATCHED)!"
    game_stage = "BETTING"

    deck = []
    player_hand = []
    dealer_hand = []
    community_cards = []

    dealer_timer = 0
    STAGGER_DELAY = 300

    ante_rect = pygame.Rect(370, 430, 60, 60)
    blind_rect = pygame.Rect(445, 435, 60, 60)
    play_rect = pygame.Rect(520, 430, 60, 60)
    trips_rect = pygame.Rect(445, 365, 60, 60)

    btn_4x_rect = pygame.Rect(200, 520, 90, 42)
    btn_3x_rect = pygame.Rect(300, 520, 90, 42)
    btn_2x_rect = pygame.Rect(400, 520, 90, 42)
    btn_1x_rect = pygame.Rect(500, 520, 90, 42)
    btn_check_rect = pygame.Rect(600, 520, 90, 42)
    btn_fold_rect = pygame.Rect(700, 520, 90, 42)

    deal_trigger_rect = pygame.Rect(330, 520, 135, 42)
    clear_btn_rect = pygame.Rect(485, 520, 135, 42)

    chip_selections = [
        (10, pygame.Rect(650, 526, 30, 30), (240, 240, 240), (40, 40, 40)),
        (50, pygame.Rect(688, 526, 30, 30), (180, 30, 30), (240, 240, 240)),
        (100, pygame.Rect(726, 526, 30, 30), (30, 80, 180), (240, 240, 240)),
        (250, pygame.Rect(764, 526, 30, 30), (30, 130, 60), (212, 163, 89)),
        (1000, pygame.Rect(802, 526, 30, 30), (40, 40, 40), (230, 185, 105)),
    ]

    def draw_wood_panel(surface, rect):
        pygame.draw.rect(surface, WOOD_LIGHT, rect, 0, 6)
        pygame.draw.rect(surface, VINTAGE_GOLD, rect, 2, 6)
        pygame.draw.rect(surface, MAHOGANY, (rect.x + 3, rect.y + 3, rect.width - 6, rect.height - 6), 0, 4)

    def draw_chip_stack(surface, rect, text_val):
        if text_val <= 0:
            return

        bg_color = (240, 240, 240)
        stripe_color = (40, 40, 40)

        for val, _, col_bg, col_str in chip_selections:
            if text_val >= val:
                bg_color = col_bg
                stripe_color = col_str

        cx, cy = rect.centerx, rect.centery
        pygame.draw.circle(surface, CHARCOAL, (cx, cy + 2), 15)
        pygame.draw.circle(surface, bg_color, (cx, cy), 15)

        for angle in [0, 90, 180, 270]:
            rad = math.radians(angle)
            sx = cx + math.cos(rad) * 11
            sy = cy + math.sin(rad) * 11
            pygame.draw.circle(surface, stripe_color, (int(sx), int(sy)), 2)

        pygame.draw.circle(surface, CREAM_WHITE, (cx, cy), 8)
        display_str = str(text_val) if text_val < 1000 else f"{text_val // 1000}k"
        c_txt = chip_num_font.render(display_str, True, CHARCOAL)
        surface.blit(c_txt, (cx - c_txt.get_width() // 2, cy - c_txt.get_height() // 2))

    def draw_table_stencils(surface):
        bj_txt = stencil_large.render("ULTIMATE TEXAS HOLD 'EM", True, GOLD_TEXT)
        surface.blit(bj_txt, (WIDTH // 2 - bj_txt.get_width() // 2, 185))

        d_rule = stencil_small.render("Dealer qualifies with Pair or better", True, GOLD_TEXT)
        surface.blit(d_rule, (WIDTH // 2 - d_rule.get_width() // 2, 208))

        pygame.draw.arc(surface, GOLD_TEXT, (100, 140, 750, 220), math.radians(195), math.radians(345), 2)

        spots = [
            (ante_rect, "ANTE", GOLD_TEXT),
            (blind_rect, "BLIND", GOLD_TEXT),
            (play_rect, "PLAY", GOLD_SHADOW),
            (trips_rect, "TRIPS", GOLD_SHADOW),
        ]

        for rect, lbl, color in spots:
            pygame.draw.ellipse(surface, color, rect, 2)
            lbl_surf = label_font.render(lbl, True, color)
            surface.blit(lbl_surf, (rect.centerx - lbl_surf.get_width() // 2, rect.centery - lbl_surf.get_height() // 2))

    def draw_dealer_chip_rack(surface):
        rack_rect = pygame.Rect(WIDTH // 2 - 139, 10, 278, 34)
        pygame.draw.rect(surface, WOOD_LIGHT, rack_rect, 0, 4)
        pygame.draw.rect(surface, VINTAGE_GOLD, rack_rect, 2, 4)

        rack_colors = [(240, 240, 240), (180, 30, 30), (30, 80, 180), (30, 130, 60), (40, 40, 40)]

        for i, col in enumerate(rack_colors):
            slot_x = (WIDTH // 2 - 131) + (i * 52)
            pygame.draw.rect(surface, CHARCOAL, (slot_x, 14, 44, 26), 0, 3)
            for c in range(6):
                pygame.draw.ellipse(surface, col, (slot_x + (c * 6), 16, 10, 22))

    def resolve_showdown():
        nonlocal game_stage, win_message, balance, ante_bet, blind_bet, play_bet, trips_bet

        for c in dealer_hand:
            if c.facedown:
                c.trigger_flip()

        p_cards = [c.card_data for c in player_hand] + [c.card_data for c in community_cards]
        d_cards = [c.card_data for c in dealer_hand] + [c.card_data for c in community_cards]

        p_val, p_name = evaluate_7_cards(p_cards)
        d_val, d_name = evaluate_7_cards(d_cards)

        dealer_qualifies = d_val[0] >= 1

        total_payout = 0
        details = []

        if trips_bet > 0:
            trips_payout_table = {
                "Royal Flush": 50,
                "Straight Flush": 40,
                "Four of a Kind": 30,
                "Full House": 8,
                "Flush": 7,
                "Straight": 4,
                "Three of a Kind": 3,
            }
            if p_name in trips_payout_table:
                mult = trips_payout_table[p_name]
                trips_win = trips_bet * (mult + 1)
                total_payout += trips_win
                details.append(f"Trips +${trips_win}")
            else:
                details.append("Trips Lost")

        if p_val > d_val:
            play_win = play_bet * 2
            total_payout += play_win

            if dealer_qualifies:
                ante_win = ante_bet * 2
                total_payout += ante_win
                details.append(f"Ante/Play Win (+${play_win + ante_win})")
            else:
                total_payout += ante_bet
                details.append(f"Play Win (+${play_win}), Ante Pushes")

            blind_payout_table = {
                "Royal Flush": 500,
                "Straight Flush": 50,
                "Four of a Kind": 10,
                "Full House": 3,
                "Flush": 1.5,
                "Straight": 1,
            }
            if p_name in blind_payout_table:
                b_mult = blind_payout_table[p_name]
                b_win = int(blind_bet * (b_mult + 1))
                total_payout += b_win
                details.append(f"Blind Bonus (+${b_win})")
            else:
                total_payout += blind_bet
                details.append("Blind Pushes")

            snd_win.play()

        elif p_val < d_val:
            if not dealer_qualifies:
                total_payout += ante_bet
                details.append("Dealer Disqualified (Ante Returned), Play/Blind Lost")
            else:
                details.append("Dealer Wins (Play/Ante/Blind Lost)")

            snd_lose.play()

        else:
            total_payout += play_bet + blind_bet
            if dealer_qualifies:
                total_payout += ante_bet
                details.append("Tie! Ante/Play/Blind Push")
            else:
                total_payout += ante_bet
                details.append("Tie! Ante Push")

            snd_chip.play()

        balance += total_payout
        summary = " | ".join(details)
        win_message = f"SHOWDOWN: You: {p_name} vs Dealer: {d_name}. {summary}"

        ante_bet = 0
        blind_bet = 0
        play_bet = 0
        trips_bet = 0
        game_stage = "RESOLVED"

    def new_deck():
        d = []
        for s in SUITS:
            for r in RANKS:
                d.append((r, s))
        random.shuffle(d)
        return d

    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                if game_stage == "BETTING":
                    for val, rect, c1, c2 in chip_selections:
                        if rect.collidepoint(mouse_pos):
                            active_chip_wager = val
                            snd_chip.play()

                    if clear_btn_rect.collidepoint(mouse_pos):
                        balance += ante_bet + blind_bet + trips_bet
                        ante_bet = 0
                        blind_bet = 0
                        trips_bet = 0
                        snd_chip.play()

                    if ante_rect.collidepoint(mouse_pos) or blind_rect.collidepoint(mouse_pos):
                        needed = active_chip_wager * 2
                        if balance >= needed:
                            ante_bet += active_chip_wager
                            blind_bet += active_chip_wager
                            balance -= needed
                            snd_chip.play()

                    if trips_rect.collidepoint(mouse_pos):
                        if balance >= active_chip_wager:
                            trips_bet += active_chip_wager
                            balance -= active_chip_wager
                            snd_chip.play()

                    if deal_trigger_rect.collidepoint(mouse_pos):
                        if ante_bet > 0:
                            deck = new_deck()
                            player_hand = [
                                AnimatedCard(deck.pop(), 390, 275),
                                AnimatedCard(deck.pop(), 475, 275),
                            ]
                            dealer_hand = [
                                AnimatedCard(deck.pop(), 390, 55, facedown=True),
                                AnimatedCard(deck.pop(), 475, 55, facedown=True),
                            ]
                            community_cards = []

                            game_stage = "PRE_FLOP"
                            win_message = "PRE-FLOP: BET 3X/4X ANTE OR CHECK?"
                        else:
                            win_message = "PLACE ANTE & BLIND BETS FIRST!"

                elif game_stage == "PRE_FLOP":
                    mult = 0
                    if btn_4x_rect.collidepoint(mouse_pos) and balance >= ante_bet * 4:
                        mult = 4
                    elif btn_3x_rect.collidepoint(mouse_pos) and balance >= ante_bet * 3:
                        mult = 3

                    if mult > 0:
                        play_bet = ante_bet * mult
                        balance -= play_bet
                        snd_chip.play()

                        community_cards = [
                            AnimatedCard(deck.pop(), 260, 165),
                            AnimatedCard(deck.pop(), 345, 165),
                            AnimatedCard(deck.pop(), 430, 165),
                            AnimatedCard(deck.pop(), 515, 165),
                            AnimatedCard(deck.pop(), 600, 165),
                        ]
                        resolve_showdown()

                    elif btn_check_rect.collidepoint(mouse_pos):
                        community_cards = [
                            AnimatedCard(deck.pop(), 260, 165),
                            AnimatedCard(deck.pop(), 345, 165),
                            AnimatedCard(deck.pop(), 430, 165),
                        ]
                        game_stage = "FLOP"
                        win_message = "FLOP DEALT: BET 2X ANTE OR CHECK?"

                elif game_stage == "FLOP":
                    if btn_2x_rect.collidepoint(mouse_pos) and balance >= ante_bet * 2:
                        play_bet = ante_bet * 2
                        balance -= play_bet
                        snd_chip.play()

                        community_cards.append(AnimatedCard(deck.pop(), 515, 165))
                        community_cards.append(AnimatedCard(deck.pop(), 600, 165))
                        resolve_showdown()

                    elif btn_check_rect.collidepoint(mouse_pos):
                        community_cards.append(AnimatedCard(deck.pop(), 515, 165))
                        community_cards.append(AnimatedCard(deck.pop(), 600, 165))
                        game_stage = "RIVER"
                        win_message = "RIVER DEALT: BET 1X ANTE OR FOLD?"

                elif game_stage == "RIVER":
                    if btn_1x_rect.collidepoint(mouse_pos) and balance >= ante_bet:
                        play_bet = ante_bet
                        balance -= play_bet
                        snd_chip.play()
                        resolve_showdown()

                    elif btn_fold_rect.collidepoint(mouse_pos):
                        for c in dealer_hand:
                            c.trigger_flip()

                        win_message = "PLAYER FOLDED: Ante & Blind surrendered."
                        if trips_bet > 0:
                            p_cards = [c.card_data for c in player_hand] + [c.card_data for c in community_cards]
                            _, p_name = evaluate_7_cards(p_cards)
                            trips_payout_table = {
                                "Royal Flush": 50,
                                "Straight Flush": 40,
                                "Four of a Kind": 30,
                                "Full House": 8,
                                "Flush": 7,
                                "Straight": 4,
                                "Three of a Kind": 3,
                            }
                            if p_name in trips_payout_table:
                                mult = trips_payout_table[p_name]
                                trips_win = trips_bet * (mult + 1)
                                balance += trips_win
                                win_message += f" (Trips Side Bet Won +${trips_win}!)"

                        ante_bet = 0
                        blind_bet = 0
                        play_bet = 0
                        trips_bet = 0
                        game_stage = "RESOLVED"
                        snd_lose.play()

                elif game_stage == "RESOLVED":
                    if (
                        deal_trigger_rect.collidepoint(mouse_pos)
                        or clear_btn_rect.collidepoint(mouse_pos)
                        or ante_rect.collidepoint(mouse_pos)
                    ):
                        player_hand.clear()
                        dealer_hand.clear()
                        community_cards.clear()
                        game_stage = "BETTING"
                        win_message = "PLACE ANTE & BLIND BETS FOR NEXT HAND."

        for card in player_hand + dealer_hand + community_cards:
            card.update()

        screen.fill(MAHOGANY)

        pygame.draw.ellipse(screen, LEATHER_RAIL, (-60, -180, WIDTH + 120, HEIGHT + 600))
        pygame.draw.ellipse(screen, WOOD_LIGHT, (-45, -165, WIDTH + 90, HEIGHT + 570))
        pygame.draw.ellipse(screen, FELT_GREEN, (-30, -150, WIDTH + 60, HEIGHT + 540))

        draw_table_stencils(screen)
        draw_dealer_chip_rack(screen)

        pygame.draw.rect(screen, CHARCOAL, (DECK_SHOE_POS[0], DECK_SHOE_POS[1], 75, 105), 0, 5)
        pygame.draw.rect(screen, VINTAGE_GOLD, (DECK_SHOE_POS[0] + 4, DECK_SHOE_POS[1] + 4, 67, 97), 2, 4)

        d_lbl = label_font.render("DEALER", True, VINTAGE_GOLD)
        screen.blit(d_lbl, (300, 60))
        for card in dealer_hand:
            draw_card(screen, card, card_num_font)

        b_lbl = label_font.render("COMMUNITY CARDS", True, VINTAGE_GOLD)
        screen.blit(b_lbl, (WIDTH // 2 - b_lbl.get_width() // 2, 145))
        for card in community_cards:
            draw_card(screen, card, card_num_font)

        p_lbl = label_font.render("PLAYER", True, VINTAGE_GOLD)
        screen.blit(p_lbl, (300, 280))
        for card in player_hand:
            draw_card(screen, card, card_num_font)

        draw_chip_stack(screen, ante_rect, ante_bet)
        draw_chip_stack(screen, blind_rect, blind_bet)
        draw_chip_stack(screen, play_rect, play_bet)
        draw_chip_stack(screen, trips_rect, trips_bet)

        bank_rect = pygame.Rect(110, 512, 160, 55)
        draw_wood_panel(screen, bank_rect)

        bal_txt = ui_font.render(f"BANK: ${balance}", True, CREAM_WHITE)
        chip_txt = label_font.render(f"CHIP: ${active_chip_wager}", True, VINTAGE_GOLD)
        screen.blit(bal_txt, (120, 517))
        screen.blit(chip_txt, (120, 540))

        chip_panel_rect = pygame.Rect(638, 512, 205, 55)
        draw_wood_panel(screen, chip_panel_rect)

        for val, rect, col_bg, col_str in chip_selections:
            is_sel_chip = active_chip_wager == val

            if is_sel_chip:
                pygame.draw.circle(screen, VINTAGE_GOLD, rect.center, 17)

            pygame.draw.circle(screen, col_bg, rect.center, 14)

            if val == 1000:
                pygame.draw.circle(screen, VINTAGE_GOLD, rect.center, 14, 2)

            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                sx = rect.centerx + math.cos(rad) * 10
                sy = rect.centery + math.sin(rad) * 10
                pygame.draw.circle(screen, col_str, (int(sx), int(sy)), 2)

            pygame.draw.circle(screen, CREAM_WHITE if val != 1000 else CHARCOAL, rect.center, 8)
            display_str = str(val) if val < 1000 else f"{val // 1000}k"
            val_txt = chip_num_font.render(f"${display_str}", True, CHARCOAL if val != 1000 else VINTAGE_GOLD)
            screen.blit(val_txt, (rect.centerx - val_txt.get_width() // 2, rect.centery - val_txt.get_height() // 2))

        if game_stage == "PRE_FLOP":
            b4_act = balance >= ante_bet * 4
            b3_act = balance >= ante_bet * 3

            for btn_rect, label, active in [
                (btn_4x_rect, "PLAY 4X", b4_act),
                (btn_3x_rect, "PLAY 3X", b3_act),
                (btn_check_rect, "CHECK", True),
            ]:
                pygame.draw.rect(screen, BRIGHT_RED if active else MAHOGANY, btn_rect, 0, 5)
                pygame.draw.rect(screen, VINTAGE_GOLD if active else CHROME_SHADOW, btn_rect, 2, 5)
                b_txt = label_font.render(label, True, CREAM_WHITE if active else CHROME_SHADOW)
                screen.blit(b_txt, (btn_rect.centerx - b_txt.get_width() // 2, btn_rect.centery - b_txt.get_height() // 2))

        elif game_stage == "FLOP":
            b2_act = balance >= ante_bet * 2
            for btn_rect, label, active in [
                (btn_2x_rect, "PLAY 2X", b2_act),
                (btn_check_rect, "CHECK", True),
            ]:
                pygame.draw.rect(screen, BRIGHT_RED if active else MAHOGANY, btn_rect, 0, 5)
                pygame.draw.rect(screen, VINTAGE_GOLD if active else CHROME_SHADOW, btn_rect, 2, 5)
                b_txt = label_font.render(label, True, CREAM_WHITE if active else CHROME_SHADOW)
                screen.blit(b_txt, (btn_rect.centerx - b_txt.get_width() // 2, btn_rect.centery - b_txt.get_height() // 2))

        elif game_stage == "RIVER":
            b1_act = balance >= ante_bet
            for btn_rect, label, active in [
                (btn_1x_rect, "PLAY 1X", b1_act),
                (btn_fold_rect, "FOLD", True),
            ]:
                pygame.draw.rect(screen, BRIGHT_RED if active else MAHOGANY, btn_rect, 0, 5)
                pygame.draw.rect(screen, VINTAGE_GOLD if active else CHROME_SHADOW, btn_rect, 2, 5)
                b_txt = label_font.render(label, True, CREAM_WHITE if active else CHROME_SHADOW)
                screen.blit(b_txt, (btn_rect.centerx - b_txt.get_width() // 2, btn_rect.centery - b_txt.get_height() // 2))

        elif game_stage in ["BETTING", "RESOLVED"]:
            lbl_action = "DEAL HAND" if game_stage == "BETTING" else "RESET BOARD"

            for btn_rect, label, bg in [
                (deal_trigger_rect, lbl_action, BRIGHT_RED),
                (clear_btn_rect, "CLEAR CHIPS", WOOD_LIGHT),
            ]:
                pygame.draw.rect(screen, bg, btn_rect, 0, 5)
                pygame.draw.rect(screen, VINTAGE_GOLD, btn_rect, 2, 5)
                b_txt = label_font.render(label, True, CREAM_WHITE)
                screen.blit(b_txt, (btn_rect.centerx - b_txt.get_width() // 2, btn_rect.centery - b_txt.get_height() // 2))

        banner_rect = pygame.Rect(60, 585, 830, 45)
        draw_wood_panel(screen, banner_rect)

        msg_color = (
            VINTAGE_GOLD
            if ("Win" in win_message or "Bonus" in win_message)
            else BRIGHT_RED
            if ("FIRST" in win_message or "Lost" in win_message or "FOLDED" in win_message)
            else CREAM_WHITE
        )
        msg_surf = ui_font.render(win_message, True, msg_color)
        screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, 597))

        _hint_surf = _lobby_hint_font.render("ESC: Return to Lobby", True, (230, 200, 140))
        screen.blit(_hint_surf, (15, HEIGHT - 25))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    return balance


# ============================================================
#                 MAIN LOBBY ENTRY POINT
# ============================================================

async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("The Terminal Casino")

    screen.fill((12, 82, 42))
    pygame.display.flip()
    await asyncio.sleep(0)

    init_suit_icons()

    bankroll = 1000
    bj_btn_rect = pygame.Rect(220, 280, 220, 140)
    uth_btn_rect = pygame.Rect(510, 280, 220, 140)
    font = pygame.font.Font(None, 24)

    while True:
        screen.fill((12, 82, 42))

        title_font = pygame.font.Font(None, 48)
        title_surf = title_font.render("THE TERMINAL CASINO", True, (212, 163, 89))
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 150))

        # Blackjack Card
        pygame.draw.rect(screen, (42, 12, 6), bj_btn_rect, 0, 8)
        pygame.draw.rect(screen, (212, 163, 89), bj_btn_rect, 2, 8)
        lbl = font.render("Classic Blackjack", True, (247, 245, 230))
        screen.blit(lbl, (bj_btn_rect.centerx - lbl.get_width() // 2, bj_btn_rect.centery - lbl.get_height() // 2))

        # Ultimate Hold'Em Card
        pygame.draw.rect(screen, (42, 12, 6), uth_btn_rect, 0, 8)
        pygame.draw.rect(screen, (212, 163, 89), uth_btn_rect, 2, 8)
        lbl_uth = font.render("Ultimate Hold 'Em", True, (247, 245, 230))
        screen.blit(lbl_uth, (uth_btn_rect.centerx - lbl_uth.get_width() // 2, uth_btn_rect.centery - lbl_uth.get_height() // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if bj_btn_rect.collidepoint(event.pos):
                    pygame.draw.rect(screen, (190, 25, 25), bj_btn_rect, 3, 8)
                    pygame.display.flip()
                    await asyncio.sleep(0.05)
                    bankroll = await run_blackjack(bankroll)

                elif uth_btn_rect.collidepoint(event.pos):
                    pygame.draw.rect(screen, (190, 25, 25), uth_btn_rect, 3, 8)
                    pygame.display.flip()
                    await asyncio.sleep(0.05)
                    bankroll = await run_ultimate_holdem(bankroll)

        pygame.display.flip()
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
