import asyncio
import array
import math
import random
import sys
import pygame

# ============================================================
#             CASINO MATH ENGINE & GAME LOGIC
# ============================================================

SUITS = ["♥", "♦", "♣", "♠"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}


def create_deck():
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append((rank, suit))
    random.shuffle(deck)
    return deck


def evaluate_5card_hand(cards):
    """Returns a tuple (hand_rank_score, tiebreaker_values) for comparing 5-card hands."""
    values = sorted([RANK_VALUES[c[0]] for c in cards], reverse=True)
    counts = {v: values.count(v) for v in set(values)}

    # Check Flush
    suits = [c[1] for c in cards]
    is_flush = len(set(suits)) == 1

    # Check Straight
    unique_vals = sorted(list(set(values)), reverse=True)
    is_straight = False
    straight_high = 0

    if len(unique_vals) == 5:
        if unique_vals[0] - unique_vals[4] == 4:
            is_straight = True
            straight_high = unique_vals[0]
        elif unique_vals == [14, 5, 4, 3, 2]:  # A-5 Straight
            is_straight = True
            straight_high = 5

    # Group counts: (count, val) sorted descending
    by_count = sorted([(count, val) for val, count in counts.items()], reverse=True)

    if is_straight and is_flush:
        return (8, straight_high)
    if by_count[0][0] == 4:
        kicker = [v for v in values if v != by_count[0][1]][0]
        return (7, by_count[0][1], kicker)
    if by_count[0][0] == 3 and by_count[1][0] == 2:
        return (6, by_count[0][1], by_count[1][1])
    if is_flush:
        return (5, values)
    if is_straight:
        return (4, straight_high)
    if by_count[0][0] == 3:
        kickers = sorted([v for v in values if v != by_count[0][1]], reverse=True)
        return (3, by_count[0][1], kickers)
    if by_count[0][0] == 2 and by_count[1][0] == 2:
        kicker = [v for v in values if v not in (by_count[0][1], by_count[1][1])][0]
        return (2, max(by_count[0][1], by_count[1][1]), min(by_count[0][1], by_count[1][1]), kicker)
    if by_count[0][0] == 2:
        kickers = sorted([v for v in values if v != by_count[0][1]], reverse=True)
        return (1, by_count[0][1], kickers)

    return (0, values)


def best_hand_of_7(cards):
    """Evaluates all 21 combinations of 5 cards out of 7."""
    from itertools import combinations
    best_score = None
    for combo in combinations(cards, 5):
        score = evaluate_5card_hand(combo)
        if best_score is None or score > best_score:
            best_score = score
    return best_score


HAND_NAMES = {
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "Pair",
    0: "High Card"
}


# ============================================================
#                 PYGAME & DISPLAY GLOBALS
# ============================================================

WIDTH, HEIGHT = 950, 720

# Audio Globals
snd_card_slide = None
snd_chip = None
snd_win = None
snd_lose = None

# Shared Vector Suit Icon Caches
SUIT_ICONS_32 = {}
SUIT_ICONS_16 = {}


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
#                      ANIMATED CARD CLASS
# ============================================================

DECK_SHOE_POS = (780, 25)


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
    width = int(70 * abs(flip_scale))
    height = 100
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
            surf.blit(s_icon_small, (6, 22))

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
        draw_x = card_obj.x + (70 - c_surf.get_width()) // 2
        pygame.draw.rect(surface, CHARCOAL, (card_obj.x + 2, card_obj.y + 2, 70, 100), 0, 6)
        surface.blit(c_surf, (draw_x, card_obj.y))


# ============================================================
#                 ULTIMATE HOLD 'EM GAME ROUTINE
# ============================================================

async def run_ultimate_holdem(balance):
    global snd_card_slide, snd_chip, snd_win, snd_lose

    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

    screen.fill(MAHOGANY)
    pygame.display.flip()
    await asyncio.sleep(0)

    init_suit_icons()

    clock = pygame.time.Clock()

    ui_font = pygame.font.Font(None, 24)
    label_font = pygame.font.Font(None, 18)
    stencil_large = pygame.font.Font(None, 22)
    stencil_small = pygame.font.Font(None, 16)
    card_num_font = pygame.font.Font(None, 22)
    chip_num_font = pygame.font.Font(None, 14)
    hint_font = pygame.font.Font(None, 16)

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

    pygame.event.clear()

    running = True
    active_chip_wager = 10
    
    ante_bet = 0
    blind_bet = 0
    play_bet = 0
    trips_bet = 0

    win_message = "SELECT CHIPS AND PLACE ANTE / TRIPS BETS!"
    game_stage = "BETTING"  # Stages: BETTING, PRE_FLOP, FLOP, RIVER, RESOLVED

    deck = create_deck()
    player_hand = []
    dealer_hand = []
    community_cards = []

    # Betting spot layout
    ante_rect = pygame.Rect(320, 410, 65, 65)
    blind_rect = pygame.Rect(400, 410, 65, 65)
    play_rect = pygame.Rect(480, 410, 65, 65)
    trips_rect = pygame.Rect(560, 410, 65, 65)

    # Action UI Buttons
    check_btn = pygame.Rect(290, 520, 100, 42)
    bet_3x_4x_btn = pygame.Rect(400, 520, 100, 42)
    bet_2x_btn = pygame.Rect(400, 520, 100, 42)
    bet_1x_btn = pygame.Rect(400, 520, 100, 42)
    fold_btn = pygame.Rect(510, 520, 100, 42)

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
        title_txt = stencil_large.render("ULTIMATE TEXAS HOLD 'EM", True, GOLD_TEXT)
        surface.blit(title_txt, (WIDTH // 2 - title_txt.get_width() // 2, 185))

        d_rule = stencil_small.render("Dealer qualifies with Pair or better", True, GOLD_TEXT)
        surface.blit(d_rule, (WIDTH // 2 - d_rule.get_width() // 2, 208))

        spots = [
            (ante_rect, "ANTE"),
            (blind_rect, "BLIND"),
            (play_rect, "PLAY"),
            (trips_rect, "TRIPS"),
        ]
        for rect, name in spots:
            color = GOLD_TEXT if name in ["ANTE", "BLIND"] else GOLD_SHADOW
            pygame.draw.ellipse(surface, color, rect, 2)
            lbl = label_font.render(name, True, color)
            surface.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))

    def resolve_showdown():
        nonlocal balance, win_message, game_stage

        # Reveal dealer cards
        for card in dealer_hand:
            card.trigger_flip()

        p_cards = [c.card_data for c in player_hand] + [c.card_data for c in community_cards]
        d_cards = [c.card_data for c in dealer_hand] + [c.card_data for c in community_cards]

        p_score = best_hand_of_7(p_cards)
        d_score = best_hand_of_7(d_cards)

        p_rank_name = HAND_NAMES[p_score[0]]
        d_rank_name = HAND_NAMES[d_score[0]]

        dealer_qualifies = d_score[0] >= 1  # Pair or better

        payout = 0
        summary = []

        # 1. Evaluate Play Bet vs Dealer
        if play_bet > 0:
            if p_score > d_score:
                payout += play_bet * 2
                summary.append("Play Wins")
            elif p_score < d_score:
                summary.append("Play Loses")
            else:
                payout += play_bet
                summary.append("Play Pushes")

        # 2. Evaluate Ante Bet
        if dealer_qualifies:
            if p_score > d_score:
                payout += ante_bet * 2
                summary.append("Ante Wins")
            elif p_score < d_score:
                summary.append("Ante Loses")
            else:
                payout += ante_bet
                summary.append("Ante Pushes")
        else:
            payout += ante_bet  # Ante pushes if dealer doesn't qualify
            summary.append("Ante Pushes (Dealer DNQ)")

        # 3. Evaluate Blind Bet
        if p_score > d_score:
            # Blind pays according to hand rank scale if beat dealer
            rank_val = p_score[0]
            if rank_val == 8:    # Straight Flush
                payout += blind_bet + (blind_bet * 500)
            elif rank_val == 7:  # Quads
                payout += blind_bet + (blind_bet * 50)
            elif rank_val == 6:  # Full House
                payout += blind_bet + (blind_bet * 3)
            elif rank_val == 5:  # Flush
                payout += blind_bet + (blind_bet * 1.5)
            elif rank_val == 4:  # Straight
                payout += blind_bet + (blind_bet * 1)
            else:
                payout += blind_bet  # Push for lower winning hands
            summary.append("Blind Wins")
        elif p_score < d_score:
            summary.append("Blind Loses")
        else:
            payout += blind_bet
            summary.append("Blind Pushes")

        # 4. Evaluate Trips Bonus Bet (independent of dealer hand)
        if trips_bet > 0:
            rank_val = p_score[0]
            trips_payouts = {8: 50, 7: 30, 6: 8, 5: 7, 4: 4, 3: 3}
            if rank_val in trips_payouts:
                mult = trips_payouts[rank_val]
                payout += trips_bet + (trips_bet * mult)
                summary.append(f"Trips (+${trips_bet * mult})")
            else:
                summary.append("Trips Loses")

        balance += int(payout)
        total_staked = ante_bet + blind_bet + play_bet + trips_bet
        net = payout - total_staked

        if net > 0:
            win_message = f"YOU WIN +${net}! Player: {p_rank_name} vs Dealer: {d_rank_name}"
            snd_win.play()
        elif net == 0:
            win_message = f"PUSH! Net $0. Player: {p_rank_name} vs Dealer: {d_rank_name}"
            snd_chip.play()
        else:
            win_message = f"DEALER WINS! Player: {p_rank_name} vs Dealer: {d_rank_name}"
            snd_lose.play()

        game_stage = "RESOLVED"

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

                    if ante_rect.collidepoint(mouse_pos):
                        if balance >= active_chip_wager * 2:  # Ante + matching Blind
                            ante_bet += active_chip_wager
                            blind_bet += active_chip_wager
                            balance -= active_chip_wager * 2
                            snd_chip.play()

                    if trips_rect.collidepoint(mouse_pos):
                        if balance >= active_chip_wager:
                            trips_bet += active_chip_wager
                            balance -= active_chip_wager
                            snd_chip.play()

                    if clear_btn_rect.collidepoint(mouse_pos):
                        balance += ante_bet + blind_bet + trips_bet
                        ante_bet = blind_bet = trips_bet = 0
                        snd_chip.play()

                    if deal_trigger_rect.collidepoint(mouse_pos):
                        if ante_bet > 0:
                            if len(deck) < 20:
                                deck = create_deck()

                            # Deal 2 to Player, 2 to Dealer (facedown), 5 Community
                            player_hand = [
                                AnimatedCard(deck.pop(), 390, 275),
                                AnimatedCard(deck.pop(), 470, 275),
                            ]
                            dealer_hand = [
                                AnimatedCard(deck.pop(), 390, 55, facedown=True),
                                AnimatedCard(deck.pop(), 470, 55, facedown=True),
                            ]
                            community_cards = [
                                AnimatedCard(deck.pop(), 270 + (i * 80), 165, facedown=True) for i in range(5)
                            ]

                            game_stage = "PRE_FLOP"
                            win_message = "PRE-FLOP: CHECK OR BET 3X / 4X ANTE"
                        else:
                            win_message = "PLACE AN ANTE BET TO START (MATCHING BLIND AUTOMATICALLY ADDED)"

                elif game_stage == "PRE_FLOP":
                    if check_btn.collidepoint(mouse_pos):
                        # Reveal Flop (first 3 community cards)
                        for c in community_cards[:3]:
                            c.trigger_flip()
                        game_stage = "FLOP"
                        win_message = "FLOP: CHECK OR BET 2X ANTE"

                    elif bet_3x_4x_btn.collidepoint(mouse_pos):
                        wager = ante_bet * 4 if balance >= ante_bet * 4 else ante_bet * 3
                        if balance >= wager:
                            balance -= wager
                            play_bet = wager
                            snd_chip.play()
                            # Reveal all community cards & resolve
                            for c in community_cards:
                                c.trigger_flip()
                            resolve_showdown()

                elif game_stage == "FLOP":
                    if check_btn.collidepoint(mouse_pos):
                        # Reveal Turn + River
                        for c in community_cards[3:]:
                            c.trigger_flip()
                        game_stage = "RIVER"
                        win_message = "RIVER: FOLD OR BET 1X ANTE"

                    elif bet_2x_btn.collidepoint(mouse_pos):
                        wager = ante_bet * 2
                        if balance >= wager:
                            balance -= wager
                            play_bet = wager
                            snd_chip.play()
                            for c in community_cards[3:]:
                                c.trigger_flip()
                            resolve_showdown()

                elif game_stage == "RIVER":
                    if fold_btn.collidepoint(mouse_pos):
                        # Player folds - loses Ante & Blind
                        game_stage = "RESOLVED"
                        # Reveal dealer cards
                        for card in dealer_hand:
                            card.trigger_flip()
                        
                        # Handle Trips if active
                        p_cards = [c.card_data for c in player_hand] + [c.card_data for c in community_cards]
                        p_score = best_hand_of_7(p_cards)

                        if trips_bet > 0 and p_score[0] >= 3:
                            trips_payouts = {8: 50, 7: 30, 6: 8, 5: 7, 4: 4, 3: 3}
                            mult = trips_payouts[p_score[0]]
                            payout = trips_bet + (trips_bet * mult)
                            balance += payout
                            win_message = f"FOLDED HAND. TRIPS BONUS PAYS +${trips_bet * mult}!"
                            snd_win.play()
                        else:
                            win_message = "HAND FOLDED. ANTE & BLIND FORFEITED."
                            snd_lose.play()

                    elif bet_1x_btn.collidepoint(mouse_pos):
                        wager = ante_bet * 1
                        if balance >= wager:
                            balance -= wager
                            play_bet = wager
                            snd_chip.play()
                            resolve_showdown()

                elif game_stage == "RESOLVED":
                    if (
                        deal_trigger_rect.collidepoint(mouse_pos)
                        or clear_btn_rect.collidepoint(mouse_pos)
                        or ante_rect.collidepoint(mouse_pos)
                    ):
                        player_hand.clear()
                        dealer_hand.clear()
                        community_cards.clear()
                        ante_bet = blind_bet = play_bet = trips_bet = 0
                        game_stage = "BETTING"
                        win_message = "PLACE ANTE / TRIPS BETS FOR NEW ROUND."

        # Card position updates
        for card in player_hand + dealer_hand + community_cards:
            card.update()

        # Render Background & Rail
        screen.fill(MAHOGANY)
        pygame.draw.ellipse(screen, LEATHER_RAIL, (-60, -180, WIDTH + 120, HEIGHT + 600))
        pygame.draw.ellipse(screen, WOOD_LIGHT, (-45, -165, WIDTH + 90, HEIGHT + 570))
        pygame.draw.ellipse(screen, FELT_GREEN, (-30, -150, WIDTH + 60, HEIGHT + 540))

        draw_table_stencils(screen)

        # Deck Shoe
        pygame.draw.rect(screen, CHARCOAL, (DECK_SHOE_POS[0], DECK_SHOE_POS[1], 75, 105), 0, 5)
        pygame.draw.rect(screen, VINTAGE_GOLD, (DECK_SHOE_POS[0] + 4, DECK_SHOE_POS[1] + 4, 67, 97), 2, 4)

        # Draw Labels
        d_lbl = label_font.render("DEALER", True, VINTAGE_GOLD)
        screen.blit(d_lbl, (300, 60))

        p_lbl = label_font.render("PLAYER", True, VINTAGE_GOLD)
        screen.blit(p_lbl, (300, 280))

        c_lbl = label_font.render("COMMUNITY CARDS", True, VINTAGE_GOLD)
        screen.blit(c_lbl, (WIDTH // 2 - c_lbl.get_width() // 2, 145))

        # Render Cards
        for card in dealer_hand + community_cards + player_hand:
            draw_card(screen, card, card_num_font)

        # Render Bet Stacks
        if ante_bet > 0:
            draw_chip_stack(screen, ante_rect, ante_bet)
        if blind_bet > 0:
            draw_chip_stack(screen, blind_rect, blind_bet)
        if play_bet > 0:
            draw_chip_stack(screen, play_rect, play_bet)
        if trips_bet > 0:
            draw_chip_stack(screen, trips_rect, trips_bet)

        # Bankroll Panel
        bank_rect = pygame.Rect(110, 512, 160, 55)
        draw_wood_panel(screen, bank_rect)

        bal_txt = ui_font.render(f"BANK: ${balance}", True, CREAM_WHITE)
        chip_txt = label_font.render(f"CHIP: ${active_chip_wager}", True, VINTAGE_GOLD)
        screen.blit(bal_txt, (120, 517))
        screen.blit(chip_txt, (120, 540))

        # Chip Tray Selection
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

        # Action Buttons State Machine
        if game_stage == "PRE_FLOP":
            for btn_rect, label, bg in [
                (check_btn, "CHECK", WOOD_LIGHT),
                (bet_3x_4x_btn, "BET 4X", BRIGHT_RED),
            ]:
                pygame.draw.rect(screen, bg, btn_rect, 0, 5)
                pygame.draw.rect(screen, VINTAGE_GOLD, btn_rect, 2, 5)
                b_txt = label_font.render(label, True, CREAM_WHITE)
                screen.blit(b_txt, (btn_rect.centerx - b_txt.get_width() // 2, btn_rect.centery - b_txt.get_height() // 2))

        elif game_stage == "FLOP":
            for btn_rect, label, bg in [
                (check_btn, "CHECK", WOOD_LIGHT),
                (bet_2x_btn, "BET 2X", BRIGHT_RED),
            ]:
                pygame.draw.rect(screen, bg, btn_rect, 0, 5)
                pygame.draw.rect(screen, VINTAGE_GOLD, btn_rect, 2, 5)
                b_txt = label_font.render(label, True, CREAM_WHITE)
                screen.blit(b_txt, (btn_rect.centerx - b_txt.get_width() // 2, btn_rect.centery - b_txt.get_height() // 2))

        elif game_stage == "RIVER":
            for btn_rect, label, bg in [
                (bet_1x_btn, "BET 1X", BRIGHT_RED),
                (fold_btn, "FOLD", MAHOGANY),
            ]:
                pygame.draw.rect(screen, bg, btn_rect, 0, 5)
                pygame.draw.rect(screen, VINTAGE_GOLD, btn_rect, 2, 5)
                b_txt = label_font.render(label, True, CREAM_WHITE)
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

        # Bottom Announcement Banner
        banner_rect = pygame.Rect(60, 585, 830, 45)
        draw_wood_panel(screen, banner_rect)

        msg_color = (
            VINTAGE_GOLD
            if ("WIN" in win_message or "NATURAL" in win_message)
            else BRIGHT_RED
            if ("PLACE" in win_message or "FOLDED" in win_message or "DEALER WINS" in win_message)
            else CREAM_WHITE
        )
        msg_surf = ui_font.render(win_message, True, msg_color)
        screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, 597))

        hint_surf = hint_font.render("ESC: Return to Lobby", True, (230, 200, 140))
        screen.blit(hint_surf, (15, HEIGHT - 25))

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
    holdem_btn_rect = pygame.Rect(40, 140, 200, 150)
    font = pygame.font.Font(None, 24)

    while True:
        screen.fill((12, 82, 42))

        pygame.draw.rect(screen, (42, 12, 6), holdem_btn_rect, 0, 8)
        pygame.draw.rect(screen, (212, 163, 89), holdem_btn_rect, 2, 8)
        lbl = font.render("Ultimate Hold 'Em", True, (247, 245, 230))
        screen.blit(lbl, (holdem_btn_rect.centerx - lbl.get_width() // 2, holdem_btn_rect.centery - lbl.get_height() // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if holdem_btn_rect.collidepoint(event.pos):
                    pygame.draw.rect(screen, (190, 25, 25), holdem_btn_rect, 3, 8)
                    pygame.display.flip()
                    await asyncio.sleep(0.05)
                    bankroll = await run_ultimate_holdem(bankroll)

        pygame.display.flip()
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
