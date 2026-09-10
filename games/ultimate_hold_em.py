import asyncio
import pygame
import random
import sys
import array
import math
import itertools

# ============================================================
#        ORIGINAL CASINO MATH ENGINE & GAME LOGIC
# ============================================================

SUITS = ["♥", "♦", "♣", "♠"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {rank: i for i, rank in enumerate(RANKS)}

HAND_RANKS = [
    "ROYAL FLUSH",
    "STRAIGHT FLUSH",
    "FOUR OF A KIND",
    "FULL HOUSE",
    "FLUSH",
    "STRAIGHT",
    "THREE OF A KIND",
    "TWO PAIR",
    "PAIR",
    "HIGH CARD",
]

TRIPS_PAYTABLE = {
    "ROYAL FLUSH": 50,
    "STRAIGHT FLUSH": 40,
    "FOUR OF A KIND": 30,
    "FULL HOUSE": 8,
    "FLUSH": 7,
    "STRAIGHT": 4,
    "THREE OF A KIND": 3,
}

BLIND_PAYTABLE = {
    "ROYAL FLUSH": 500,
    "STRAIGHT FLUSH": 50,
    "FOUR OF A KIND": 10,
    "FULL HOUSE": 3,
    "FLUSH": 1.5,
    "STRAIGHT": 1,
}

def create_deck():
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append((rank, suit))
    random.shuffle(deck)
    return deck

def evaluate_five_card_hand(cards):
    ranks = [rank for rank, _ in cards]
    suits = [suit for _, suit in cards]
    values = sorted([RANK_VALUES[rank] for rank in ranks], reverse=True)
    
    rank_value_counts = {}
    for val in values:
        rank_value_counts[val] = rank_value_counts.get(val, 0) + 1
        
    sorted_counts_groups = sorted(rank_value_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    counts = [item[1] for item in sorted_counts_groups]
    
    is_flush = len(set(suits)) == 1
    unique_values = sorted(set(values))
    is_straight = False
    straight_high = None

    if len(unique_values) == 5:
        if unique_values[-1] - unique_values[0] == 4:
            is_straight = True
            straight_high = unique_values[-1]
        elif unique_values == [RANK_VALUES["2"], RANK_VALUES["3"], RANK_VALUES["4"], RANK_VALUES["5"], RANK_VALUES["A"]]:
            is_straight = True
            straight_high = RANK_VALUES["5"]

    if is_flush and is_straight and straight_high == RANK_VALUES["A"]:
        return (HAND_RANKS.index("ROYAL FLUSH"), "ROYAL FLUSH", [straight_high])
    if is_flush and is_straight:
        return (HAND_RANKS.index("STRAIGHT FLUSH"), "STRAIGHT FLUSH", [straight_high])
    if counts == [4, 1]:
        four_value = sorted_counts_groups[0][0]
        kicker = sorted_counts_groups[1][0]
        return (HAND_RANKS.index("FOUR OF A KIND"), "FOUR OF A KIND", [four_value, kicker])
    if counts == [3, 2]:
        three_value = sorted_counts_groups[0][0]
        pair_value = sorted_counts_groups[1][0]
        return (HAND_RANKS.index("FULL HOUSE"), "FULL HOUSE", [three_value, pair_value])
    if is_flush:
        return (HAND_RANKS.index("FLUSH"), "FLUSH", values)
    if is_straight:
        return (HAND_RANKS.index("STRAIGHT"), "STRAIGHT", [straight_high])
    if counts == [3, 1, 1]:
        three_value = sorted_counts_groups[0][0]
        kickers = sorted([item[0] for item in sorted_counts_groups[1:]], reverse=True)
        return (HAND_RANKS.index("THREE OF A KIND"), "THREE OF A KIND", [three_value] + kickers)
    if counts == [2, 2, 1]:
        pair_values = sorted([item[0] for item in sorted_counts_groups[:2]], reverse=True)
        kicker = sorted_counts_groups[2][0]
        return (HAND_RANKS.index("TWO PAIR"), "TWO PAIR", pair_values + [kicker])
    if counts == [2, 1, 1, 1]:
        pair_value = sorted_counts_groups[0][0]
        kickers = sorted([item[0] for item in sorted_counts_groups[1:]], reverse=True)
        return (HAND_RANKS.index("PAIR"), "PAIR", [pair_value] + kickers)
    return (HAND_RANKS.index("HIGH CARD"), "HIGH CARD", values)

def evaluate_best_5_card_hand(seven_cards):
    best_rank_idx = len(HAND_RANKS)
    best_rank_name = "HIGH CARD"
    best_tie_breaker = []
    for combo in itertools.combinations(seven_cards, 5):
        rank_idx, rank_name, tie_breaker = evaluate_five_card_hand(combo)
        if rank_idx < best_rank_idx:
            best_rank_idx = rank_idx
            best_rank_name = rank_name
            best_tie_breaker = tie_breaker
        elif rank_idx == best_rank_idx:
            if tie_breaker > best_tie_breaker:
                best_tie_breaker = tie_breaker
    return best_rank_idx, best_rank_name, best_tie_breaker

# ============================================================
#       INTEGRATED PRECISION VECTOR RENDERERS
# ============================================================

def draw_diamond(surface, color, x, y, size):
    half_w = int(size * 0.38)
    half_h = int(size * 0.52)
    points = [
        (x, y - half_h),
        (x + half_w, y),
        (x, y + half_h),
        (x - half_w, y)
    ]
    pygame.draw.polygon(surface, color, points)

def draw_heart(surface, color, x, y, size):
    points = []
    steps = 100
    scale = size * 0.44
    for i in range(steps + 1):
        t = math.pi * 2 * i / steps
        dx = 16 * (math.sin(t) ** 3)
        dy = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        px = x + int(dx * scale / 16)
        py = y + int((dy - 1.0) * scale / 16)
        points.append((px, py))
    pygame.draw.polygon(surface, color, points)

def draw_spade(surface, color, x, y, size):
    # Spade Head (Inverted Heart)
    head_points = []
    steps = 80
    scale = size * 0.42
    for i in range(steps + 1):
        t = math.pi * 2 * i / steps
        dx = 16 * (math.sin(t) ** 3)
        dy = (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        px = x + int(dx * scale / 16)
        py = y + int((dy - 3.0) * scale / 16)
        head_points.append((px, py))
    pygame.draw.polygon(surface, color, head_points)
    
    # Flared Pedestal Stem
    stem_w_top = max(1, int(size * 0.04))
    stem_w_bottom = max(2, int(size * 0.28))
    top_y = y + int(size * 0.05)
    bottom_y = y + int(size * 0.48)
    
    stem_points = [
        (x - stem_w_top, top_y),
        (x + stem_w_top, top_y),
        (x + stem_w_bottom, bottom_y),
        (x - stem_w_bottom, bottom_y)
    ]
    pygame.draw.polygon(surface, color, stem_points)

def draw_club(surface, color, x, y, size):
    r = int(size * 0.22)
    dist = int(size * 0.18)
    
    # Center connecting core
    pygame.draw.circle(surface, color, (x, y - dist), r)
    pygame.draw.circle(surface, color, (x - dist, y + int(size * 0.05)), r)
    pygame.draw.circle(surface, color, (x + dist, y + int(size * 0.05)), r)
    
    center_poly = [
        (x, y - dist),
        (x + dist, y + int(size * 0.05)),
        (x, y + int(size * 0.12)),
        (x - dist, y + int(size * 0.05))
    ]
    pygame.draw.polygon(surface, color, center_poly)
    
    # Flared Pedestal Stem
    stem_w_top = max(1, int(size * 0.04))
    stem_w_bottom = max(2, int(size * 0.26))
    top_y = y + int(size * 0.02)
    bottom_y = y + int(size * 0.46)
    
    stem_points = [
        (x - stem_w_top, top_y),
        (x + stem_w_top, top_y),
        (x + stem_w_bottom, bottom_y),
        (x - stem_w_bottom, bottom_y)
    ]
    pygame.draw.polygon(surface, color, stem_points)

def draw_vector_suit(surface, suit_str, x, y, size, color):
    """Dispatcher routing suit strings to precision vector rendering calls."""
    if suit_str == "♦":
        draw_diamond(surface, color, x, y, size)
    elif suit_str == "♥":
        draw_heart(surface, color, x, y, size)
    elif suit_str == "♠":
        draw_spade(surface, color, x, y, size)
    elif suit_str == "♣":
        draw_club(surface, color, x, y, size)

# ============================================================
#        REFACTORED WIDGET ENGINE & STATE DISPATCHER
# ============================================================

class UIWidget:
    def __init__(self, rect, label, bg_color, text_color, callback=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.bg_color = bg_color
        self.text_color = text_color
        self.callback = callback
        self.visible = True

    def draw(self, surface, font):
        if not self.visible:
            return
        pygame.draw.rect(surface, self.bg_color, self.rect, 0, 5)
        pygame.draw.rect(surface, (247, 245, 230), self.rect, 1, 5)
        if self.label:
            b_txt = font.render(self.label, True, self.text_color)
            surface.blit(b_txt, (self.rect.centerx - b_txt.get_width() // 2, self.rect.centery - b_txt.get_height() // 2))

    def handle_event(self, event):
        if self.visible and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                    return True
        return False

# ============================================================
#        CARD DEALING & FLIPPING ANIMATION ENGINE
# ============================================================

class CardAnimation:
    def __init__(self, start_pos, target_rect, card, from_facedown, to_facedown, is_flip_only=False):
        self.start_x, self.start_y = start_pos
        self.target_rect = pygame.Rect(target_rect)
        self.card = card
        self.from_facedown = from_facedown
        self.to_facedown = to_facedown
        self.is_flip_only = is_flip_only
        self.progress = 0.0
        self.speed = 0.12

    def update(self):
        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 1.0
            return True
        return False

    def draw(self, surface):
        if self.is_flip_only:
            scale_x = abs(math.cos(self.progress * math.pi))
            current_facedown = self.from_facedown if self.progress < 0.5 else self.to_facedown
            w = max(2, int(self.target_rect.width * scale_x))
            h = self.target_rect.height
            cx, cy = self.target_rect.centerx, self.target_rect.centery
            scaled_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
            draw_card_scaled(surface, scaled_rect, self.card, facedown=current_facedown)
        else:
            curr_x = self.start_x + (self.target_rect.x - self.start_x) * self.progress
            curr_y = self.start_y + (self.target_rect.y - self.start_y) * self.progress
            sliding_rect = pygame.Rect(int(curr_x), int(curr_y), self.target_rect.width, self.target_rect.height)
            draw_card_scaled(surface, sliding_rect, self.card, facedown=self.from_facedown)

# ============================================================
#            PYGAME VISUAL ENGINE INITIALIZATION
# ============================================================

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

WIDTH, HEIGHT = 950, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vintage Vegas Ultimate Texas Hold 'Em - Refactored Engine")
clock = pygame.time.Clock()
_lobby_hint_font = pygame.font.SysFont(None, 20)
_GAME_TITLE = ("Vintage Vegas Ultimate Texas Hold 'Em - Refactored Engine")

def generate_noise_burst(duration_ms, volume=0.2, filter_low=False):
    sample_rate = 22050
    total_samples = int(sample_rate * (duration_ms / 1000.0))
    buffer = array.array("h", [0] + [0] * (total_samples - 1))
    last_val = 0
    for i in range(total_samples):
        raw = random.randint(-32767, 32767)
        if filter_low:
            last_val = (last_val * 0.85) + (raw * 0.15)
            val = int(last_val)
        else:
            val = raw
        envelope = math.exp(-3.0 * (i / total_samples))
        buffer[i] = int(val * volume * envelope)
    return pygame.mixer.Sound(buffer=buffer)

def generate_harmonic_clink(freqs, duration_ms, volume=0.2):
    sample_rate = 22050
    total_samples = int(sample_rate * (duration_ms / 1000.0))
    buffer = array.array("h", [0] * total_samples)
    for i in range(total_samples):
        t = i / sample_rate
        val = 0
        envelope = math.exp(-4.0 * (i / total_samples))
        for f in freqs:
            val += math.sin(2 * math.pi * f * t)
        val = int((val / len(freqs)) * 32767 * volume * envelope)
        buffer[i] = val
    return pygame.mixer.Sound(buffer=buffer)

snd_slide = generate_noise_burst(70, volume=0.15, filter_low=True)
snd_deal = generate_noise_burst(40, volume=0.2, filter_low=False)
snd_flip = generate_noise_burst(50, volume=0.18, filter_low=True)
snd_chip = generate_harmonic_clink([2400, 3100, 4200], 35, volume=0.25)
snd_win = generate_harmonic_clink([523.25, 659.25, 783.99, 1046.50], 400, volume=0.15)
snd_lose = generate_noise_burst(180, volume=0.25, filter_low=True)

FELT_GREEN = (10, 68, 33)
MAHOGANY = (56, 18, 11)
WOOD_LIGHT = (84, 30, 20)
CHROME_SHADOW = (110, 110, 110)
VINTAGE_GOLD = (212, 163, 89)
GOLD_SHADOW = (145, 105, 45)
CREAM_WHITE = (247, 245, 230)
CHARCOAL = (24, 24, 24)
BRIGHT_RED = (205, 20, 20)

ui_font = pygame.font.SysFont("arial", 18, bold=True)  
label_font = pygame.font.SysFont("arial", 14, bold=True)
card_num_font = pygame.font.SysFont("georgia", 22, bold=True)
chip_num_font = pygame.font.SysFont("arial", 11, bold=True)

def draw_card(surface, rect, card, facedown=False):
    pygame.draw.rect(surface, CHARCOAL, (rect.x + 3, rect.y + 3, rect.width, rect.height), 0, 6)
    if facedown:
        pygame.draw.rect(surface, WOOD_LIGHT, rect, 0, 6)
        pygame.draw.rect(surface, VINTAGE_GOLD, (rect.x + 5, rect.y + 5, rect.width - 10, rect.height - 10), 2, 4)
        pygame.draw.rect(surface, CHARCOAL, (rect.x + 8, rect.y + 8, rect.width - 16, rect.height - 16), 0, 3)
    else:
        rank, suit = card
        pygame.draw.rect(surface, CREAM_WHITE, rect, 0, 6)
        pygame.draw.rect(surface, CHROME_SHADOW, rect, 1, 6)
        txt_color = BRIGHT_RED if suit in ["♥", "♦"] else CHARCOAL
        num_surf = card_num_font.render(rank, True, txt_color)
        surface.blit(num_surf, (rect.x + 6, rect.y + 4))
        
        # Center Vector Suit Render
        draw_vector_suit(surface, suit, rect.centerx, rect.centery + 10, 32, txt_color)
        # Corner Mini-Suit Render
        draw_vector_suit(surface, suit, rect.x + 14 + num_surf.get_width(), rect.y + 14, 14, txt_color)

def draw_card_scaled(surface, rect, card, facedown=False):
    if rect.width < 4:
        return
    pygame.draw.rect(surface, CHARCOAL, (rect.x + 2, rect.y + 2, rect.width, rect.height), 0, 4)
    if facedown:
        pygame.draw.rect(surface, WOOD_LIGHT, rect, 0, 4)
        if rect.width > 20:
            pygame.draw.rect(surface, VINTAGE_GOLD, (rect.x + 3, rect.y + 3, rect.width - 6, rect.height - 6), 1, 2)
    else:
        rank, suit = card
        pygame.draw.rect(surface, CREAM_WHITE, rect, 0, 4)
        pygame.draw.rect(surface, CHROME_SHADOW, rect, 1, 4)
        if rect.width > 35:
            txt_color = BRIGHT_RED if suit in ["♥", "♦"] else CHARCOAL
            num_surf = card_num_font.render(rank, True, txt_color)
            surface.blit(num_surf, (rect.x + 4, rect.y + 2))
            
            # Scaled Center Vector Suit
            suit_size = int(32 * (rect.width / 80.0))
            draw_vector_suit(surface, suit, rect.centerx, rect.centery + 10, suit_size, txt_color)

async def run_ultimate_hold_em(balance):
    global screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(_GAME_TITLE)
    running = True
    active_chip_wager = 10
    win_message = "Place Ante & Blind. Trips optional."
    game_stage = "BETTING"

    deck = []
    player_hole = []
    dealer_hole = []
    community_cards = []
    active_animations = []

    deck_pos = (820, 60)

    bet_ante = 0
    bet_blind = 0
    bet_trips = 0
    bet_play = 0

    player_card_rects = [pygame.Rect(55, 345, 80, 120), pygame.Rect(145, 345, 80, 120)]
    dealer_card_rects = [pygame.Rect(55, 95, 80, 120), pygame.Rect(145, 95, 80, 120)]
    community_rects = [pygame.Rect(260 + (i * 90), 220, 80, 120) for i in range(5)]

    ante_felt_rect = pygame.Rect(440, 100, 110, 80)
    trips_felt_rect = pygame.Rect(565, 100, 110, 80)

    chip_selections = [
        (10, pygame.Rect(55, 595, 45, 45), (240, 240, 240), (40, 40, 40)),
        (50, pygame.Rect(115, 595, 45, 45), (180, 30, 30), (240, 240, 240)),
        (100, pygame.Rect(175, 595, 45, 45), (30, 80, 180), (240, 240, 240)),
        (250, pygame.Rect(235, 595, 45, 45), (30, 130, 60), (212, 163, 89)),
        (1000, pygame.Rect(295, 595, 45, 45), (30, 30, 30), (212, 163, 89)),
    ]

    def can_afford(cost):
        nonlocal balance
        return balance >= cost

    def draw_chip_stack(surface, rect, text_val):
        bg_color, stripe_color = (240, 240, 240), (40, 40, 40)
        for val, _, col_bg, col_str in chip_selections:
            if text_val >= val:
                bg_color, stripe_color = col_bg, col_str
        cx, cy = rect.centerx, rect.centery
        pygame.draw.circle(surface, CHARCOAL, (cx, cy + 2), 14)
        pygame.draw.circle(surface, bg_color, (cx, cy), 14)
        for angle in [0, 90, 180, 270]:
            rad = math.radians(angle)
            pygame.draw.circle(surface, stripe_color, (int(cx + math.cos(rad) * 11), int(cy + math.sin(rad) * 11)), 2)
        pygame.draw.circle(surface, CREAM_WHITE, (cx, cy), 8)
        display_str = str(text_val) if text_val < 1000 else f"{text_val // 1000}k"
        c_txt = chip_num_font.render(display_str, True, CHARCOAL)
        surface.blit(c_txt, (cx - (c_txt.get_width() // 2), cy - (c_txt.get_height() // 2)))

    def evaluate_and_payout():
        nonlocal balance, bet_ante, bet_blind, bet_trips, bet_play, win_message, game_stage, active_animations
        player_cards = player_hole + community_cards
        dealer_cards = dealer_hole + community_cards
        p_idx, p_name, p_tie = evaluate_best_5_card_hand(player_cards)
        d_idx, d_name, d_tie = evaluate_best_5_card_hand(dealer_cards)
        dealer_qualifies = d_idx < HAND_RANKS.index("HIGH CARD")
        payout = 0
        msg = f"You: {p_name} | Dlr: {d_name}."

        for idx, card in enumerate(dealer_hole):
            active_animations.append(CardAnimation(dealer_card_rects[idx].topleft, dealer_card_rects[idx], card, from_facedown=True, to_facedown=False, is_flip_only=True))
        snd_flip.play()

        if bet_trips > 0 and p_name in TRIPS_PAYTABLE:
            trips_win = bet_trips * (TRIPS_PAYTABLE[p_name] + 1)
            payout += trips_win
            msg = f"Trips +${trips_win}!"

        if p_idx < d_idx or (p_idx == d_idx and p_tie > d_tie):
            msg = f"WIN: {p_name} vs {d_name}"
            payout += bet_play * 2
            if dealer_qualifies:
                payout += bet_ante * 2
            else:
                payout += bet_ante
            if p_name in BLIND_PAYTABLE:
                blind_win = bet_blind * (BLIND_PAYTABLE[p_name] + 1)
                payout += blind_win
            else:
                payout += bet_blind
        elif p_idx > d_idx or (p_idx == d_idx and p_tie < d_tie):
            msg = f"LOSS: Dlr {d_name}"
            if not dealer_qualifies:
                payout += bet_ante
        else:
            msg = f"PUSH: Both {p_name}"
            payout += bet_ante + bet_blind + bet_play

        balance += payout
        original_wager = bet_ante + bet_blind + bet_play + bet_trips
        win_message = f"🎉 {msg} (+${payout})" if payout > original_wager else f"❌ {msg}"
        bet_ante, bet_blind, bet_trips, bet_play = 0, 0, 0, 0
        game_stage = "RESOLVED"
        if payout > original_wager:
            snd_win.play()
        else:
            snd_lose.play()

    def cb_clear_chips():
        nonlocal balance, bet_ante, bet_blind, bet_trips
        if game_stage == "BETTING":
            balance += bet_ante + bet_blind + bet_trips
            bet_ante, bet_blind, bet_trips = 0, 0, 0
            snd_chip.play()
        elif game_stage == "RESOLVED":
            cb_next_round()

    def cb_ante_bet():
        nonlocal balance, bet_ante, bet_blind
        if game_stage == "BETTING" and can_afford(active_chip_wager * 2):
            bet_ante += active_chip_wager
            bet_blind += active_chip_wager
            balance -= active_chip_wager * 2
            snd_chip.play()

    def cb_trips_bet():
        nonlocal balance, bet_trips
        if game_stage == "BETTING" and can_afford(active_chip_wager):
            bet_trips += active_chip_wager
            balance -= active_chip_wager
            snd_chip.play()

    def cb_deal_or_check():
        nonlocal game_stage, deck, player_hole, dealer_hole, community_cards, win_message, active_animations
        if game_stage == "BETTING" and bet_ante > 0:
            deck = create_deck()
            player_hole = [deck.pop(), deck.pop()]
            dealer_hole = [deck.pop(), deck.pop()]
            community_cards = [deck.pop() for _ in range(5)]

            for i, card in enumerate(player_hole):
                active_animations.append(CardAnimation(deck_pos, player_card_rects[i], card, from_facedown=False, to_facedown=False))
            for i, card in enumerate(dealer_hole):
                active_animations.append(CardAnimation(deck_pos, dealer_card_rects[i], card, from_facedown=True, to_facedown=True))
            snd_deal.play()

            game_stage = "PRE_FLOP"
            win_message = "Pre-Flop: Raise 4x/3x or Check."
        elif game_stage == "PRE_FLOP":
            game_stage = "FLOP"
            win_message = "Flop: Raise 2x or Check."
            for i in range(3):
                active_animations.append(CardAnimation(deck_pos, community_rects[i], community_cards[i], from_facedown=True, to_facedown=False, is_flip_only=True))
            snd_flip.play()
        elif game_stage == "FLOP":
            game_stage = "RIVER"
            win_message = "River: Raise 1x or Fold."
            for i in range(3, 5):
                active_animations.append(CardAnimation(deck_pos, community_rects[i], community_cards[i], from_facedown=True, to_facedown=False, is_flip_only=True))
            snd_flip.play()

    def cb_action_btn1():
        nonlocal game_stage, bet_play, balance, active_animations
        if game_stage == "PRE_FLOP" and can_afford(bet_ante * 4):
            bet_play = bet_ante * 4
            balance -= bet_play
            game_stage = "RIVER"
            for i in range(5):
                active_animations.append(CardAnimation(deck_pos, community_rects[i], community_cards[i], from_facedown=True, to_facedown=False, is_flip_only=True))
            snd_flip.play()
            evaluate_and_payout()
        elif game_stage == "FLOP" and can_afford(bet_ante * 2):
            bet_play = bet_ante * 2
            balance -= bet_play
            game_stage = "RIVER"
            for i in range(3, 5):
                active_animations.append(CardAnimation(deck_pos, community_rects[i], community_cards[i], from_facedown=True, to_facedown=False, is_flip_only=True))
            snd_flip.play()
            evaluate_and_payout()
        elif game_stage == "RIVER" and can_afford(bet_ante):
            bet_play = bet_ante
            balance -= bet_play
            evaluate_and_payout()

    def cb_action_btn2():
        nonlocal game_stage, bet_play, balance, bet_ante, bet_blind, bet_trips, win_message, active_animations
        if game_stage == "PRE_FLOP" and can_afford(bet_ante * 3):
            bet_play = bet_ante * 3
            balance -= bet_play
            game_stage = "RIVER"
            for i in range(5):
                active_animations.append(CardAnimation(deck_pos, community_rects[i], community_cards[i], from_facedown=True, to_facedown=False, is_flip_only=True))
            snd_flip.play()
            evaluate_and_payout()
        elif game_stage == "RIVER":
            lost_amount = bet_ante + bet_blind + bet_trips
            win_message = f"Hand Folded (-${lost_amount})."
            bet_ante, bet_blind, bet_trips, bet_play = 0, 0, 0, 0
            game_stage = "RESOLVED"
            snd_lose.play()

    def cb_next_round():
        nonlocal game_stage, player_hole, dealer_hole, community_cards, win_message, active_animations
        if game_stage == "RESOLVED":
            player_hole.clear()
            dealer_hole.clear()
            community_cards.clear()
            active_animations.clear()
            game_stage = "BETTING"
            win_message = "Place Ante & Blind. Trips optional."

    btn_1_widget = UIWidget((440, 580, 120, 45), "", BRIGHT_RED, CREAM_WHITE, cb_action_btn1)
    btn_2_widget = UIWidget((570, 580, 120, 45), "", CHARCOAL, CREAM_WHITE, cb_action_btn2)
    clear_widget = UIWidget((720, 520, 180, 45), "CLEAR CHIPS", CHARCOAL, CREAM_WHITE, cb_clear_chips)
    action_widget = UIWidget((720, 580, 180, 45), "DEAL HOLE", BRIGHT_RED, CREAM_WHITE, cb_deal_or_check)

    # ============================================================
    #                        MAIN GAME LOOP
    # ============================================================

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handled = (
                    action_widget.handle_event(event) or
                    clear_widget.handle_event(event) or
                    btn_1_widget.handle_event(event) or
                    btn_2_widget.handle_event(event)
                )

                if not handled:
                    mouse_pos = event.pos
                    if game_stage == "BETTING":
                        for val, rect, _, _ in chip_selections:
                            if rect.collidepoint(mouse_pos):
                                active_chip_wager = val
                                snd_chip.play()
                        if ante_felt_rect.collidepoint(mouse_pos):
                            cb_ante_bet()
                        elif trips_felt_rect.collidepoint(mouse_pos):
                            cb_trips_bet()

        if game_stage == "BETTING":
            action_widget.label = "DEAL HOLE"
            action_widget.callback = cb_deal_or_check
            action_widget.visible = (bet_ante > 0)
            clear_widget.visible = True
            clear_widget.label = "CLEAR CHIPS"
            clear_widget.callback = cb_clear_chips
            btn_1_widget.visible = False
            btn_2_widget.visible = False
        elif game_stage == "PRE_FLOP":
            action_widget.label = "CHECK"
            action_widget.callback = cb_deal_or_check
            action_widget.visible = True
            clear_widget.visible = False
            btn_1_widget.visible = True
            btn_1_widget.label = "BET 4x PLAY"
            btn_1_widget.bg_color = BRIGHT_RED
            btn_1_widget.callback = cb_action_btn1
            btn_2_widget.visible = True
            btn_2_widget.label = "BET 3x PLAY"
            btn_2_widget.bg_color = CHARCOAL
            btn_2_widget.callback = cb_action_btn2
        elif game_stage == "FLOP":
            action_widget.label = "CHECK"
            action_widget.callback = cb_deal_or_check
            action_widget.visible = True
            clear_widget.visible = False
            btn_1_widget.visible = True
            btn_1_widget.label = "BET 2x PLAY"
            btn_1_widget.bg_color = BRIGHT_RED
            btn_1_widget.callback = cb_action_btn1
            btn_2_widget.visible = False
        elif game_stage == "RIVER":
            action_widget.visible = False
            clear_widget.visible = False
            btn_1_widget.visible = True
            btn_1_widget.label = "BET 1x PLAY"
            btn_1_widget.bg_color = BRIGHT_RED
            btn_1_widget.callback = cb_action_btn1
            btn_2_widget.visible = True
            btn_2_widget.label = "FOLD HAND"
            btn_2_widget.bg_color = CHARCOAL
            btn_2_widget.callback = cb_action_btn2
        elif game_stage == "RESOLVED":
            action_widget.visible = True
            action_widget.label = "NEXT ROUND"
            action_widget.callback = cb_next_round
            clear_widget.visible = True
            clear_widget.label = "NEXT ROUND"
            clear_widget.callback = cb_next_round
            btn_1_widget.visible = False
            btn_2_widget.visible = False

        completed_animations = []
        for anim in active_animations:
            if anim.update():
                completed_animations.append(anim)
        for anim in completed_animations:
            active_animations.remove(anim)

        screen.fill(MAHOGANY)
        pygame.draw.rect(screen, WOOD_LIGHT, (10, 10, WIDTH - 20, HEIGHT - 20), 10)
        pygame.draw.rect(screen, FELT_GREEN, (20, 20, WIDTH - 40, HEIGHT - 40))

        pygame.draw.rect(screen, CHARCOAL, (deck_pos[0] + 3, deck_pos[1] + 3, 80, 120), 0, 6)
        pygame.draw.rect(screen, WOOD_LIGHT, (deck_pos[0], deck_pos[1], 80, 120), 0, 6)
        pygame.draw.rect(screen, VINTAGE_GOLD, (deck_pos[0] + 5, deck_pos[1] + 5, 70, 110), 2, 4)

        screen.blit(ui_font.render("DEALER HAND", True, VINTAGE_GOLD), (55, 60))
        if len(dealer_hole) > 0:
            hide_dealer = (game_stage != "RESOLVED")
            for idx, card in enumerate(dealer_hole):
                animating = any(anim.target_rect == dealer_card_rects[idx] for anim in active_animations)
                if not animating:
                    draw_card(screen, dealer_card_rects[idx], card, facedown=hide_dealer)

        screen.blit(ui_font.render("COMMUNITY BOARD", True, VINTAGE_GOLD), (260, 185))
        if game_stage in ["PRE_FLOP", "FLOP", "RIVER", "RESOLVED"]:
            for i in range(5):
                hide_comm = True
                if game_stage == "FLOP" and i < 3:
                    hide_comm = False
                if game_stage in ["RIVER", "RESOLVED"]:
                    hide_comm = False
                if len(community_cards) > 0:
                    animating = any(anim.target_rect == community_rects[i] for anim in active_animations)
                    if not animating:
                        draw_card(screen, community_rects[i], community_cards[i], facedown=hide_comm)

        screen.blit(ui_font.render("YOUR HOLE CARDS", True, VINTAGE_GOLD), (55, 310))
        if len(player_hole) > 0:
            for idx, card in enumerate(player_hole):
                animating = any(anim.target_rect == player_card_rects[idx] for anim in active_animations)
                if not animating:
                    draw_card(screen, player_card_rects[idx], card, facedown=False)

        for anim in active_animations:
            anim.draw(screen)

        if game_stage == "BETTING":
            pygame.draw.rect(screen, (FELT_GREEN if bet_ante == 0 else GOLD_SHADOW), ante_felt_rect, 0, 4)
            pygame.draw.rect(screen, CREAM_WHITE, ante_felt_rect, 2, 4)
            screen.blit(label_font.render("ANTE & BLIND", True, (CREAM_WHITE if bet_ante == 0 else CHARCOAL)), (ante_felt_rect.x + 8, ante_felt_rect.y + 15))
            screen.blit(label_font.render("(AUTO MATCH)", True, (VINTAGE_GOLD if bet_ante == 0 else CHARCOAL)), (ante_felt_rect.x + 8, ante_felt_rect.y + 45))
            if bet_ante > 0:
                draw_chip_stack(screen, ante_felt_rect, bet_ante)

            pygame.draw.rect(screen, (FELT_GREEN if bet_trips == 0 else GOLD_SHADOW), trips_felt_rect, 0, 4)
            pygame.draw.rect(screen, CREAM_WHITE, trips_felt_rect, 2, 4)
            screen.blit(label_font.render("TRIPS BET", True, (CREAM_WHITE if bet_trips == 0 else CHARCOAL)), (trips_felt_rect.x + 18, trips_felt_rect.y + 15))
            screen.blit(label_font.render("(OPTIONAL)", True, (VINTAGE_GOLD if bet_trips == 0 else CHARCOAL)), (trips_felt_rect.x + 18, trips_felt_rect.y + 45))
            if bet_trips > 0:
                draw_chip_stack(screen, trips_felt_rect, bet_trips)

        # Draw Table Bets HUD
        screen.blit(ui_font.render(f"ANTE: ${bet_ante}", True, CREAM_WHITE), (440, 200))
        screen.blit(ui_font.render(f"BLIND: ${bet_blind}", True, CREAM_WHITE), (440, 230))
        screen.blit(ui_font.render(f"TRIPS: ${bet_trips}", True, CREAM_WHITE), (570, 200))
        screen.blit(ui_font.render(f"PLAY: ${bet_play}", True, CREAM_WHITE), (570, 230))

        # Chip Tray Selection HUD
        screen.blit(ui_font.render("CHIP TRAY", True, VINTAGE_GOLD), (55, 560))
        for val, rect, bg_col, str_col in chip_selections:
            is_sel = (val == active_chip_wager)
            cy = rect.centery - (4 if is_sel else 0)
            pygame.draw.circle(screen, CHARCOAL, (rect.centerx, cy + 2), 22)
            pygame.draw.circle(screen, bg_col, (rect.centerx, cy), 22)
            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                pygame.draw.circle(screen, str_col, (int(rect.centerx + math.cos(rad) * 17), int(cy + math.sin(rad) * 17)), 3)
            pygame.draw.circle(screen, CREAM_WHITE, (rect.centerx, cy), 13)
            display_str = str(val) if val < 1000 else f"{val // 1000}k"
            c_txt = chip_num_font.render(display_str, True, CHARCOAL)
            screen.blit(c_txt, (rect.centerx - (c_txt.get_width() // 2), cy - (c_txt.get_height() // 2)))
            if is_sel:
                pygame.draw.circle(screen, VINTAGE_GOLD, (rect.centerx, cy), 23, 2)

        # Dashboard / Balance / Win Message
        balance_txt = ui_font.render(f"BANKROLL: ${balance}", True, VINTAGE_GOLD)
        screen.blit(balance_txt, (55, 20))

        msg_txt = ui_font.render(win_message, True, CREAM_WHITE)
        screen.blit(msg_txt, (WIDTH // 2 - msg_txt.get_width() // 2, 680))

        # Render Active UI Widgets
        action_widget.draw(screen, ui_font)
        clear_widget.draw(screen, ui_font)
        btn_1_widget.draw(screen, ui_font)
        btn_2_widget.draw(screen, ui_font)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    return balance
