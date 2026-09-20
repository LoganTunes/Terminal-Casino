import array
import asyncio
import math
import random
import sys
import pygame

# ============================================================
#           CASINO MATH ENGINE & GAME LOGIC
# ============================================================

SUITS = ["♥", "♦", "♣", "♠"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]


def create_deck():
    deck = [(rank, suit) for suit in SUITS for rank in RANKS]
    random.shuffle(deck)
    return deck


def get_card_value(card):
    rank, _ = card
    if rank in ["10", "J", "Q", "K"]:
        return 0
    elif rank == "A":
        return 1
    return int(rank)


def calculate_baccarat_score(hand):
    return sum(get_card_value(c) for c in hand) % 10


def process_baccarat_tableau(deck):
    """Executes official Punto Banco 3rd-card drawing matrix rules."""
    p_hand = [deck.pop(), deck.pop()]
    b_hand = [deck.pop(), deck.pop()]

    p_score = calculate_baccarat_score(p_hand)
    b_score = calculate_baccarat_score(b_hand)

    # 1. Natural Check: 8 or 9 stands immediately
    if p_score >= 8 or b_score >= 8:
        return p_hand, b_hand

    # 2. Player Rule: Draw on 0-5, Stand on 6-7
    p_third_card = None
    if p_score <= 5:
        p_third_card = deck.pop()
        p_hand.append(p_third_card)

    # 3. Banker Rule
    if p_third_card is None:
        # Player stood: Banker draws on 0-5, stands on 6-7
        if b_score <= 5:
            b_hand.append(deck.pop())
    else:
        # Player drew: Banker draws based on fixed tableau matrix
        p_third_val = get_card_value(p_third_card)
        draw_banker = False

        if b_score <= 2:
            draw_banker = True
        elif b_score == 3 and p_third_val != 8:
            draw_banker = True
        elif b_score == 4 and p_third_val in [2, 3, 4, 5, 6, 7]:
            draw_banker = True
        elif b_score == 5 and p_third_val in [4, 5, 6, 7]:
            draw_banker = True
        elif b_score == 6 and p_third_val in [6, 7]:
            draw_banker = True

        if draw_banker:
            b_hand.append(deck.pop())

    return p_hand, b_hand


def evaluate_baccarat_payout(p_score, b_score, active_bets):
    """Calculates payouts using standard casino odds."""
    payout = 0
    breakdown = ""

    if p_score > b_score:
        winning_outcome = "PLAYER"
    elif b_score > p_score:
        winning_outcome = "BANKER"
    else:
        winning_outcome = "TIE"

    for bet_type, bet_amount in active_bets.items():
        if bet_amount <= 0:
            continue

        if bet_type == winning_outcome:
            if bet_type == "PLAYER":
                win_amt = bet_amount * 2  # 1:1 payout + original wager returned
                payout += win_amt
                breakdown += f"Player Win (+${win_amt}) "
            elif bet_type == "BANKER":
                win_amt = bet_amount + int(
                    bet_amount * 0.95
                )  # 0.95:1 payout + original wager
                payout += win_amt
                breakdown += f"Banker Win [5% Comm] (+${win_amt}) "
            elif bet_type == "TIE":
                win_amt = bet_amount * 9  # 8:1 payout + original wager
                payout += win_amt
                breakdown += f"Tie Hit (8:1) (+${win_amt}) "
        elif winning_outcome == "TIE" and bet_type in ["PLAYER", "BANKER"]:
            # Main bets push when a Tie hits
            payout += bet_amount
            breakdown += f"{bet_type} Push Returned (+${bet_amount}) "

    return payout, winning_outcome, breakdown


# ============================================================
#               PYGAME VISUAL ENGINE INITIALIZATION
# ============================================================

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

WIDTH, HEIGHT = 950, 720
# NOTE: display is (re)configured inside run_*() below, not at import time.
# Calling set_mode() here too caused repeated canvas resizes on startup
# (once per game module imported by main.py), which breaks rendering
# under pygbag/WebAssembly.
clock = pygame.time.Clock()
_lobby_hint_font = pygame.font.SysFont(None, 20)

# ============================================================
#               PROCEDURAL AUDIO SYNTH DRIVERS
# ============================================================


def generate_synth_sound(freq_list, duration_ms, wave_type="triangle", volume=0.25):
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
                val = (
                    32767 if math.sin(2 * math.pi * freq * t) >= 0 else -32768
                )
            elif wave_type == "triangle":
                val = int(
                    32767
                    * (
                        2.0
                        * math.fabs(2.0 * (t * freq - math.floor(t * freq + 0.5)))
                        - 1.0
                    )
                )
            else:
                val = int(32767 * math.sin(2 * math.pi * freq * t))

        scaled_val = int(val * volume)
        buffer[i] = max(-32768, min(32767, scaled_val))

    return pygame.mixer.Sound(buffer=buffer)


snd_card_slide = generate_synth_sound([400, 300], 80, "triangle", 0.2)
snd_win = generate_synth_sound([523, 659, 783, 1046], 400, "square", 0.15)
snd_lose = generate_synth_sound([330, 293, 220], 350, "square", 0.2)
snd_chip = generate_synth_sound([1200], 40, "triangle", 0.25)

# ============================================================
#                       COLOR PALETTE
# ============================================================

FELT_GREEN = (10, 68, 33)
MAHOGANY = (56, 18, 11)
WOOD_LIGHT = (84, 30, 20)
LEATHER_RAIL = (24, 8, 4)
CHROME_SHADOW = (110, 110, 110)
VINTAGE_GOLD = (212, 163, 89)
GOLD_TEXT = (230, 185, 105)
GOLD_SHADOW = (145, 105, 45)
CREAM_WHITE = (247, 245, 230)
CHARCOAL = (24, 24, 24)
BRIGHT_RED = (190, 25, 25)

font_options = ["segoeuiemoji", "applecoloremoji", "notocoloremoji", "arial"]
ui_font = pygame.font.SysFont(font_options, 20, bold=True)
label_font = pygame.font.SysFont(font_options, 14, bold=True)
stencil_font = pygame.font.SysFont(font_options, 15, bold=True)
card_num_font = pygame.font.SysFont("georgia", 22, bold=True)
chip_num_font = pygame.font.SysFont("arial", 11, bold=True)

# ============================================================
#               VECTOR SUIT ICON ENGINE
# ============================================================
SUIT_ICON_CACHE = {}


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
            y = -(
                13 * math.cos(t)
                - 5 * math.cos(2 * t)
                - 2 * math.cos(3 * t)
                - math.cos(4 * t)
            )
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
            y = (
                13 * math.cos(t)
                - 5 * math.cos(2 * t)
                - 2 * math.cos(3 * t)
                - math.cos(4 * t)
            )
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
        pygame.draw.circle(
            surf_high, color, (int(center), int(high_res * 0.32)), int(r)
        )
        pygame.draw.circle(
            surf_high, color, (int(high_res * 0.30), int(high_res * 0.52)), int(r)
        )
        pygame.draw.circle(
            surf_high, color, (int(high_res * 0.70), int(high_res * 0.52)), int(r)
        )
        pygame.draw.circle(
            surf_high, color, (int(center), int(high_res * 0.48)), int(r * 0.8)
        )

        stem = [
            (center - high_res * 0.04, center),
            (center + high_res * 0.04, center),
            (center + high_res * 0.10, high_res * 0.90),
            (center - high_res * 0.10, high_res * 0.90),
        ]
        pygame.draw.polygon(surf_high, color, stem)

    return pygame.transform.smoothscale(surf_high, (size, size))


def get_suit_icon(suit_type, size):
    size = max(4, int(size))
    key = (suit_type, size)
    icon = SUIT_ICON_CACHE.get(key)
    if icon is None:
        icon = create_flat_suit_icon(suit_type, size)
        SUIT_ICON_CACHE[key] = icon
    return icon


# ============================================================
#                 ANIMATED CARD CLASS
# ============================================================
CARD_W, CARD_H = 80, 115
DECK_SHOE_POS = (820, 25)


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


def draw_card_surface(card_data, facedown=False, flip_scale=1.0):
    width = int(CARD_W * abs(flip_scale))
    height = CARD_H
    if width < 1:
        return None

    surf = pygame.Surface((width, height), pygame.SRCALPHA)

    if facedown or flip_scale < 0:
        pygame.draw.rect(surf, WOOD_LIGHT, (0, 0, width, height), 0, 6)
        pygame.draw.rect(
            surf, VINTAGE_GOLD, (3, 3, max(1, width - 6), height - 6), 2, 4
        )
        pygame.draw.rect(
            surf, CHARCOAL, (5, 5, max(1, width - 10), height - 10), 0, 2
        )
    else:
        rank, suit = card_data
        pygame.draw.rect(surf, CREAM_WHITE, (0, 0, width, height), 0, 6)
        pygame.draw.rect(surf, CHROME_SHADOW, (0, 0, width, height), 1, 6)

        txt_color = BRIGHT_RED if suit in ["♥", "♦"] else CHARCOAL

        if abs(flip_scale) > 0.35:
            num_surf = card_num_font.render(rank, True, txt_color)
            surf.blit(num_surf, (5, 3))

            s_icon_small = get_suit_icon(suit, 16)
            surf.blit(s_icon_small, (6, 24))

            s_icon = get_suit_icon(suit, 34)
            surf.blit(s_icon, (width // 2 - 17, height // 2 - 12))

    return surf


def draw_animated_card(surface, card_obj):
    if card_obj.is_flipping:
        scale = math.cos(card_obj.flip_progress * math.pi)
    else:
        scale = -1.0 if card_obj.facedown else 1.0

    c_surf = draw_card_surface(
        card_obj.card_data, card_obj.facedown, flip_scale=scale
    )
    if c_surf:
        draw_x = card_obj.x + (CARD_W - c_surf.get_width()) // 2
        pygame.draw.rect(
            surface, CHARCOAL, (card_obj.x + 2, card_obj.y + 2, CARD_W, CARD_H), 0, 6
        )
        surface.blit(c_surf, (draw_x, card_obj.y))


# STATE MANAGEMENT
balance = 500
active_chip_wager = 10
win_message = "STACK CHIPS ON PLAYER, BANKER, OR TIE, THEN DEAL!"

game_stage = "BETTING"  # BETTING, DEALING, RESOLVED
player_anim = []
banker_anim = []

deal_order = []
deal_index = 0
deal_timer = 0
DEAL_STEP_DELAY = 450

player_bets = {"PLAYER": 0, "BANKER": 0, "TIE": 0}

# Side-by-side card layouts: Banker (Left), Player (Right)
b_card_rects = [
    pygame.Rect(180 + (i * 90), 80, CARD_W, CARD_H) for i in range(3)
]
p_card_rects = [
    pygame.Rect(510 + (i * 90), 80, CARD_W, CARD_H) for i in range(3)
]

# Betting Zones
bet_zones = {
    "PLAYER": (pygame.Rect(65, 475, 260, 50), "PLAYER (PUNTO)"),
    "BANKER": (pygame.Rect(345, 475, 260, 50), "BANKER (BANCO)"),
    "TIE": (pygame.Rect(625, 475, 260, 50), "TIE"),
}

# UI elements
deal_btn_rect = pygame.Rect(330, 550, 135, 42)
clear_btn_rect = pygame.Rect(485, 550, 135, 42)
bank_rect = pygame.Rect(110, 543, 160, 55)
chip_panel_rect = pygame.Rect(638, 543, 205, 55)
banner_rect = pygame.Rect(60, 610, 830, 45)

chip_selections = [
    (10, pygame.Rect(650, 556, 30, 30), (240, 240, 240), (40, 40, 40)),
    (50, pygame.Rect(688, 556, 30, 30), (180, 30, 30), (240, 240, 240)),
    (100, pygame.Rect(726, 556, 30, 30), (30, 80, 180), (240, 240, 240)),
    (250, pygame.Rect(764, 556, 30, 30), (30, 130, 60), (212, 163, 89)),
    (1000, pygame.Rect(802, 556, 30, 30), (40, 40, 40), (230, 185, 105)),
]


def draw_wood_panel(surface, rect):
    pygame.draw.rect(surface, WOOD_LIGHT, rect, 0, 6)
    pygame.draw.rect(surface, VINTAGE_GOLD, rect, 2, 6)
    pygame.draw.rect(
        surface,
        MAHOGANY,
        (rect.x + 3, rect.y + 3, rect.width - 6, rect.height - 6),
        0,
        4,
    )


def draw_chip_stack(surface, rect, text_val):
    bg_color, stripe_color = (240, 240, 240), (40, 40, 40)
    for val, _, col_bg, col_str in chip_selections:
        if text_val >= val:
            bg_color, stripe_color = col_bg, col_str

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
    surface.blit(
        c_txt, (cx - (c_txt.get_width() // 2), cy - c_txt.get_height() // 2)
    )


def draw_table_stencils(surface):
    pay_txt = stencil_font.render(
        "PLAYER PAYS 1:1  •  BANKER PAYS 0.95:1  •  TIE PAYS 8:1",
        True,
        GOLD_TEXT,
    )
    surface.blit(pay_txt, (WIDTH // 2 - pay_txt.get_width() // 2, 280))

    comm_txt = label_font.render(
        "Banker wins carry a 5% house commission", True, GOLD_TEXT
    )
    surface.blit(comm_txt, (WIDTH // 2 - comm_txt.get_width() // 2, 305))

    pygame.draw.arc(
        surface,
        GOLD_TEXT,
        (80, 260, 790, 210),
        math.radians(195),
        math.radians(345),
        2,
    )

    pygame.draw.arc(
        surface,
        GOLD_SHADOW,
        (130, 290, 690, 170),
        math.radians(195),
        math.radians(345),
        1,
    )

    pygame.draw.line(surface, GOLD_SHADOW, (240, 360), (170, 460), 1)
    pygame.draw.line(surface, GOLD_SHADOW, (710, 360), (780, 460), 1)


def draw_dealer_chip_rack(surface):
    rack_rect = pygame.Rect(WIDTH // 2 - 139, 10, 278, 34)
    pygame.draw.rect(surface, WOOD_LIGHT, rack_rect, 0, 4)
    pygame.draw.rect(surface, VINTAGE_GOLD, rack_rect, 2, 4)

    rack_colors = [
        (240, 240, 240),
        (180, 30, 30),
        (30, 80, 180),
        (30, 130, 60),
        (40, 40, 40),
    ]

    for i, col in enumerate(rack_colors):
        slot_x = (WIDTH // 2 - 131) + (i * 52)
        pygame.draw.rect(surface, CHARCOAL, (slot_x, 14, 44, 26), 0, 3)
        for c in range(6):
            pygame.draw.ellipse(surface, col, (slot_x + (c * 6), 16, 10, 22))


def build_deal_order(p_cards, b_cards):
    order = []
    for i in range(2):
        order.append(("player", p_cards[i]))
        order.append(("banker", b_cards[i]))
    if len(p_cards) == 3:
        order.append(("player", p_cards[2]))
    if len(b_cards) == 3:
        order.append(("banker", b_cards[2]))
    return order


def finalize_round():
    global game_stage, win_message, balance, player_bets
    p_score = calculate_baccarat_score([c.card_data for c in player_anim])
    b_score = calculate_baccarat_score([c.card_data for c in banker_anim])
    total_won, winner, details = evaluate_baccarat_payout(
        p_score, b_score, player_bets
    )
    balance += total_won
    win_message = (
        f"Result: Player {p_score} vs Banker {b_score}. Winner: {winner}! {details}"
    )
    game_stage = "RESOLVED"
    if total_won > 0:
        snd_win.play()
    else:
        snd_lose.play()


def process_deal_sequence(current_time):
    global deal_timer, deal_index

    if deal_index > 0:
        prev_hand_key = deal_order[deal_index - 1][0]
        prev_list = player_anim if prev_hand_key == "player" else banker_anim
        last_card = prev_list[-1]
        if last_card.facedown and not last_card.is_flipping:
            last_card.trigger_flip()
            deal_timer = current_time
            return
        if last_card.is_flipping:
            return

    if current_time - deal_timer < DEAL_STEP_DELAY:
        return

    if deal_index < len(deal_order):
        hand_key, card = deal_order[deal_index]
        count_in_hand = sum(
            1 for h, _ in deal_order[:deal_index] if h == hand_key
        )
        rect = (
            p_card_rects[count_in_hand]
            if hand_key == "player"
            else b_card_rects[count_in_hand]
        )
        new_card = AnimatedCard(card, rect.x, rect.y, facedown=True)
        (player_anim if hand_key == "player" else banker_anim).append(new_card)
        deal_index += 1
        deal_timer = current_time
    else:
        finalize_round()


# ============================================================
#                       ASYNC MAIN LOOP
# ============================================================
async def run_baccarat(starting_balance):
    global balance, active_chip_wager, win_message, game_stage, screen
    global player_anim, banker_anim, deal_order, deal_index, deal_timer, player_bets

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Vintage Vegas Baccarat - Punto Banco Table")

    balance = starting_balance
    active_chip_wager = 10
    win_message = "STACK CHIPS ON PLAYER, BANKER, OR TIE, THEN DEAL!"
    game_stage = "BETTING"
    player_anim = []
    banker_anim = []
    deal_order = []
    deal_index = 0
    deal_timer = 0
    player_bets = {"PLAYER": 0, "BANKER": 0, "TIE": 0}

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
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
                        balance += sum(player_bets.values())
                        player_bets = {"PLAYER": 0, "BANKER": 0, "TIE": 0}
                        snd_chip.play()

                    for sector_key, (rect, label) in bet_zones.items():
                        if rect.collidepoint(mouse_pos):
                            if balance >= active_chip_wager:
                                player_bets[sector_key] += active_chip_wager
                                balance -= active_chip_wager
                                snd_chip.play()

                    if deal_btn_rect.collidepoint(mouse_pos):
                        if any(v > 0 for v in player_bets.values()):
                            deck = create_deck()
                            p_cards, b_cards = process_baccarat_tableau(deck)
                            deal_order = build_deal_order(p_cards, b_cards)
                            player_anim = []
                            banker_anim = []
                            deal_index = 0
                            deal_timer = current_time
                            game_stage = "DEALING"
                            win_message = "Dealing the tableau..."
                            snd_chip.play()
                        else:
                            win_message = (
                                "❌ MUST PLACE CHIPS ON PLAYER, BANKER, OR TIE BEFORE DEALING!"
                            )

                elif game_stage == "RESOLVED":
                    if deal_btn_rect.collidepoint(
                        mouse_pos
                    ) or clear_btn_rect.collidepoint(mouse_pos):
                        player_anim = []
                        banker_anim = []
                        deal_order = []
                        deal_index = 0
                        player_bets = {"PLAYER": 0, "BANKER": 0, "TIE": 0}
                        game_stage = "BETTING"
                        win_message = (
                            "CHOOSE CHIP VALUE, PLACE SECTOR CHIPS, THEN DEAL NEW ROUND."
                        )
                        snd_chip.play()

        if game_stage == "DEALING":
            process_deal_sequence(current_time)

        for card in player_anim + banker_anim:
            card.update()

        # BACKGROUND FELT TABLE
        screen.fill(MAHOGANY)
        pygame.draw.ellipse(
            screen, LEATHER_RAIL, (-60, -180, WIDTH + 120, HEIGHT + 600)
        )
        pygame.draw.ellipse(
            screen, WOOD_LIGHT, (-45, -165, WIDTH + 90, HEIGHT + 570)
        )
        pygame.draw.ellipse(
            screen, FELT_GREEN, (-30, -150, WIDTH + 60, HEIGHT + 540)
        )

        draw_table_stencils(screen)
        draw_dealer_chip_rack(screen)

        # Deck shoe
        pygame.draw.rect(
            screen, CHARCOAL, (DECK_SHOE_POS[0], DECK_SHOE_POS[1], CARD_W, CARD_H - 5), 0, 5
        )
        pygame.draw.rect(
            screen,
            VINTAGE_GOLD,
            (DECK_SHOE_POS[0] + 4, DECK_SHOE_POS[1] + 4, CARD_W - 8, CARD_H - 13),
            2,
            4,
        )

        # HAND LABELS & SCORES
        screen.blit(ui_font.render("BANKER (BANCO)", True, VINTAGE_GOLD), (180, 52))
        if len(banker_anim) > 0 and game_stage != "DEALING":
            b_score_txt = label_font.render(
                f"Score: {calculate_baccarat_score([c.card_data for c in banker_anim])}",
                True,
                CREAM_WHITE,
            )
            screen.blit(b_score_txt, (180, 205))

        screen.blit(
            ui_font.render("PLAYER (PUNTO)", True, VINTAGE_GOLD), (510, 52)
        )
        if len(player_anim) > 0 and game_stage != "DEALING":
            p_score_txt = label_font.render(
                f"Score: {calculate_baccarat_score([c.card_data for c in player_anim])}",
                True,
                CREAM_WHITE,
            )
            screen.blit(p_score_txt, (510, 205))

        # DRAW CARDS
        for card in banker_anim:
            draw_animated_card(screen, card)
        for card in player_anim:
            draw_animated_card(screen, card)

        # BETTING SECTORS
        if game_stage in ("BETTING", "RESOLVED"):
            for key, (rect, label) in bet_zones.items():
                wager_amt = player_bets[key]
                box_bg = FELT_GREEN if wager_amt == 0 else GOLD_SHADOW
                pygame.draw.rect(screen, box_bg, rect, 0, 6)
                pygame.draw.rect(
                    screen,
                    CREAM_WHITE if wager_amt == 0 else VINTAGE_GOLD,
                    rect,
                    2,
                    6,
                )
                lbl_txt = label_font.render(
                    label, True, CREAM_WHITE if wager_amt == 0 else CHARCOAL
                )
                screen.blit(
                    lbl_txt, (rect.centerx - lbl_txt.get_width() // 2, rect.y + 6)
                )
                if wager_amt > 0:
                    draw_chip_stack(screen, rect, wager_amt)

        # BANKROLL & CHIPS
        draw_wood_panel(screen, bank_rect)
        bal_txt = ui_font.render(f"BANK: ${balance}", True, CREAM_WHITE)
        chip_txt = label_font.render(
            f"CHIP: ${active_chip_wager}", True, VINTAGE_GOLD
        )
        screen.blit(bal_txt, (120, 548))
        screen.blit(chip_txt, (120, 571))

        draw_wood_panel(screen, chip_panel_rect)
        for val, rect, col_bg, col_str in chip_selections:
            if active_chip_wager == val:
                pygame.draw.circle(screen, VINTAGE_GOLD, rect.center, 17)
            pygame.draw.circle(screen, col_bg, rect.center, 14)
            if val == 1000:
                pygame.draw.circle(screen, VINTAGE_GOLD, rect.center, 14, 2)
            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                sx = rect.centerx + math.cos(rad) * 10
                sy = rect.centery + math.sin(rad) * 10
                pygame.draw.circle(screen, col_str, (int(sx), int(sy)), 2)
            pygame.draw.circle(
                screen, CREAM_WHITE if val != 1000 else CHARCOAL, rect.center, 8
            )
            display_str = str(val) if val < 1000 else f"{val // 1000}k"
            val_txt = chip_num_font.render(
                f"${display_str}",
                True,
                CHARCOAL if val != 1000 else VINTAGE_GOLD,
            )
            screen.blit(
                val_txt,
                (
                    rect.centerx - val_txt.get_width() // 2,
                    rect.centery - val_txt.get_height() // 2,
                ),
            )

        # ACTION BUTTONS
        if game_stage == "BETTING":
            for btn_rect, label, bg in [
                (deal_btn_rect, "DEAL HAND", BRIGHT_RED),
                (clear_btn_rect, "CLEAR CHIPS", WOOD_LIGHT),
            ]:
                pygame.draw.rect(screen, bg, btn_rect, 0, 5)
                pygame.draw.rect(screen, VINTAGE_GOLD, btn_rect, 2, 5)
                b_txt = label_font.render(label, True, CREAM_WHITE)
                screen.blit(
                    b_txt,
                    (
                        btn_rect.centerx - b_txt.get_width() // 2,
                        btn_rect.centery - b_txt.get_height() // 2,
                    ),
                )
        elif game_stage == "RESOLVED":
            pygame.draw.rect(screen, BRIGHT_RED, deal_btn_rect, 0, 5)
            pygame.draw.rect(screen, VINTAGE_GOLD, deal_btn_rect, 2, 5)
            b_txt = label_font.render("NEW ROUND", True, CREAM_WHITE)
            screen.blit(
                b_txt,
                (
                    deal_btn_rect.centerx - b_txt.get_width() // 2,
                    deal_btn_rect.centery - b_txt.get_height() // 2,
                ),
            )
        else:
            for btn_rect, label in [
                (deal_btn_rect, "DEALING"),
                (clear_btn_rect, "…"),
            ]:
                pygame.draw.rect(screen, MAHOGANY, btn_rect, 0, 5)
                pygame.draw.rect(screen, CHROME_SHADOW, btn_rect, 1, 5)
                b_txt = label_font.render(label, True, CHROME_SHADOW)
                screen.blit(
                    b_txt,
                    (
                        btn_rect.centerx - b_txt.get_width() // 2,
                        btn_rect.centery - b_txt.get_height() // 2,
                    ),
                )

        # MESSAGE BANNER
        draw_wood_panel(screen, banner_rect)

        msg_color = (
            BRIGHT_RED
            if "❌" in win_message
            else VINTAGE_GOLD
            if "Winner" in win_message
            else CREAM_WHITE
        )
        msg_surf = ui_font.render(win_message, True, msg_color)
        if msg_surf.get_width() > banner_rect.width - 20:
            msg_surf = label_font.render(win_message, True, msg_color)
        screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, 622))

        _hint_surf = _lobby_hint_font.render("ESC: Return to Lobby", True, (230, 200, 140))
        screen.blit(_hint_surf, (15, HEIGHT - 25))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    return balance
