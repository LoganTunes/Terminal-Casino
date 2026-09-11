import asyncio
import array
import math
import random
import sys
import pygame

# ============================================================
#       ORIGINAL CASINO MATH ENGINE & GAME LOGIC
# ============================================================

SUITS = ["♥", "♦", "♣", "♠"]

RANKS = [
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
    "A",
]

RANK_VALUES = {rank: i for i, rank in enumerate(RANKS)}

PAYOUTS = [
    ("ROYAL FLUSH", 250),
    ("STRAIGHT FLUSH", 50),
    ("FOUR OF A KIND", 25),
    ("FULL HOUSE", 9),
    ("FLUSH", 6),
    ("STRAIGHT", 4),
    ("THREE OF A KIND", 3),
    ("TWO PAIR", 2),
    ("JACKS OR BETTER", 1),
]


def create_deck():
  deck = []
  for suit in SUITS:
    for rank in RANKS:
      deck.append((rank, suit))
  random.shuffle(deck)
  return deck


def evaluate_poker_hand(hand):
  ranks = [card[0] for card in hand]
  suits = [card[1] for card in hand]

  values = sorted(RANK_VALUES[r] for r in ranks)
  rank_counts = {r: ranks.count(r) for r in ranks}
  counts = sorted(rank_counts.values(), reverse=True)

  is_flush = len(set(suits)) == 1
  is_straight = False

  if len(set(values)) == 5:
    if values[-1] - values[0] == 4:
      is_straight = True
    elif values == [
        RANK_VALUES["A"],
        RANK_VALUES["2"],
        RANK_VALUES["3"],
        RANK_VALUES["4"],
        RANK_VALUES["5"],
    ]:
      is_straight = True

  if is_flush and is_straight:
    if values[0] == RANK_VALUES["10"]:
      return "ROYAL FLUSH"
    return "STRAIGHT FLUSH"

  if counts[0] == 4:
    return "FOUR OF A KIND"

  if counts[0] == 3 and counts[1] == 2:
    return "FULL HOUSE"

  if is_flush:
    return "FLUSH"

  if is_straight:
    return "STRAIGHT"

  if counts[0] == 3:
    return "THREE OF A KIND"

  if counts[0] == 2 and counts[1] == 2:
    return "TWO PAIR"

  if counts[0] == 2:
    for r, count in rank_counts.items():
      if count == 2 and RANK_VALUES[r] >= RANK_VALUES["J"]:
        return "JACKS OR BETTER"

  return "HIGH CARD"


# ============================================================
#              PYGAME VISUAL ENGINE INITIALIZATION
# ============================================================

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

WIDTH, HEIGHT = 950, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vintage Vegas Video Poker - CRT Cabinet")
clock = pygame.time.Clock()
_lobby_hint_font = pygame.font.SysFont(None, 20)
_GAME_TITLE = ("Vintage Vegas Video Poker - CRT Cabinet")


# ============================================================
#               PROCEDURAL AUDIO SYNTH DRIVERS
# ============================================================


def generate_synth_sound(
    freq_list, duration_ms, wave_type="square", volume=0.3
):
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
        val = int(
            32767
            * (
                2.0
                * math.fabs(
                    2.0 * (t * freq - math.floor(t * freq + 0.5))
                )
                - 1.0
            )
        )
      else:
        val = int(32767 * math.sin(2 * math.pi * freq * t))

    buffer[i] = int(val * volume)

  return pygame.mixer.Sound(buffer=buffer)


snd_flip = generate_synth_sound(
    [800, 1200, 600], 40, wave_type="square", volume=0.15
)
snd_hold = generate_synth_sound(
    [523, 659], 60, wave_type="square", volume=0.2
)
snd_unhold = generate_synth_sound(
    [659, 523], 60, wave_type="square", volume=0.2
)
snd_win = generate_synth_sound(
    [523, 659, 783, 1046, 783, 1046], 450, wave_type="square", volume=0.25
)
snd_lose = generate_synth_sound(
    [300, 250, 200, 150], 350, wave_type="triangle", volume=0.3
)
snd_bet = generate_synth_sound(
    [700, 900], 30, wave_type="square", volume=0.15
)


# ============================================================
#                 RETRO CRT COLOR PALETTE
# ============================================================

CRT_BLUE = (0, 0, 170)
CRT_DARK_BLUE = (0, 0, 80)
CRT_YELLOW = (255, 255, 85)
CRT_WHITE = (255, 255, 255)
CRT_RED = (255, 85, 85)
CRT_BLACK = (0, 0, 0)

# Chip-inspired colors for bet buttons
CHIP_WHITE = (240, 240, 240)
CHIP_RED = (200, 40, 40)
CHIP_BLUE = (40, 90, 200)
CHIP_GREEN = (40, 160, 60)
CHIP_BLACK = (30, 30, 30)


# ============================================================
#                            FONTS
# ============================================================

font_options = ["courier", "segoeuiemoji", "arial"]

ui_font = pygame.font.SysFont(font_options, 18, bold=True)
label_font = pygame.font.SysFont(font_options, 14, bold=True)
btn_font = pygame.font.SysFont(font_options, 14, bold=True)
pay_font = pygame.font.SysFont("courier", 15, bold=True)
card_num_font = pygame.font.SysFont("courier", 26, bold=True)


# ============================================================
#     VECTOR SUIT ICON ENGINE (SAME TECHNIQUE AS BLACKJACK)
# Mathematically accurate heart/spade curves and diamond/club
# shapes, drawn at 4x resolution then smoothscaled down, cached
# per (suit, size) so nothing is regenerated every frame.
# ============================================================
SUIT_ICON_CACHE = {}


def create_flat_suit_icon(suit_type, size=32):
  scale = 4
  high_res = size * scale
  surf_high = pygame.Surface((high_res, high_res), pygame.SRCALPHA)
  color = CRT_RED if suit_type in ["♥", "♦"] else CRT_BLACK
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


def get_suit_icon(suit_type, size):
  size = max(4, int(size))
  key = (suit_type, size)
  icon = SUIT_ICON_CACHE.get(key)
  if icon is None:
    icon = create_flat_suit_icon(suit_type, size)
    SUIT_ICON_CACHE[key] = icon
  return icon


def blit_suit_icon(surface, suit_type, center_x, center_y, size):
  icon = get_suit_icon(suit_type, size)
  surface.blit(
      icon,
      (int(center_x - icon.get_width() / 2), int(center_y - icon.get_height() / 2)),
  )


# ============================================================
#                     ANIMATED CARD CLASS
# ============================================================


class AnimatedCard:

  def __init__(self, rect, card):
    self.rect = rect
    self.card = card
    self.progress = 0.0
    self.speed = 0.08
    self.is_animating = True

  def update(self):
    if self.is_animating:
      self.progress += self.speed
      if self.progress >= 1.0:
        self.progress = 1.0
        self.is_animating = False

  def draw(self, surface, is_held=False):
    scale_x = math.fabs(math.cos(self.progress * math.pi))
    scaled_width = max(2, int(self.rect.width * scale_x))
    draw_rect = pygame.Rect(
        self.rect.centerx - scaled_width // 2,
        self.rect.y,
        scaled_width,
        self.rect.height,
    )

    is_front = self.progress >= 0.5

    if is_front:
      pygame.draw.rect(surface, CRT_WHITE, draw_rect, 0, 4)
      pygame.draw.rect(surface, CRT_BLACK, draw_rect, 2, 4)

      if scaled_width > 30:
        rank, suit = self.card
        txt_color = CRT_RED if suit in ["♥", "♦"] else CRT_BLACK

        num_surf = card_num_font.render(rank, True, txt_color)
        surface.blit(num_surf, (draw_rect.x + 6, draw_rect.y + 6))

        blit_suit_icon(surface, suit, draw_rect.centerx, draw_rect.centery, 40)

      if is_held:
        hold_rect = pygame.Rect(
            self.rect.x + 5, self.rect.y - 32, self.rect.width - 10, 26
        )
        pygame.draw.rect(surface, CRT_YELLOW, hold_rect, 0, 2)
        pygame.draw.rect(surface, CRT_BLACK, hold_rect, 1, 2)

        h_txt = label_font.render("HOLD", True, CRT_BLACK)
        surface.blit(
            h_txt,
            (
                hold_rect.centerx - h_txt.get_width() // 2,
                hold_rect.centery - h_txt.get_height() // 2,
            ),
        )
    else:
      pygame.draw.rect(surface, CRT_RED, draw_rect, 0, 4)
      pygame.draw.rect(surface, CRT_WHITE, draw_rect, 2, 4)


# ============================================================
#                         LIVE STATES
# ============================================================


async def run_video_poker(balance):
    global screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(_GAME_TITLE)
    running = True
    current_bet = 5

    win_message = "USE CHIP BUTTONS TO SET WAGER, THEN TAP DEAL."
    game_stage = "BETTING"

    deck = []
    player_hand = []
    animated_cards = []
    held_cards = [False] * 5
    final_hand_rank = ""


    # ============================================================
    #                    LAYOUT CONTROLS
    # ============================================================

    draw_btn_rect = pygame.Rect(750, 535, 155, 75)
    clear_btn_rect = pygame.Rect(750, 620, 155, 35)

    # Bet configurations (value, color, text color)
    bet_configs = [
        (1, CHIP_WHITE, CRT_BLACK),
        (5, CHIP_RED, CRT_WHITE),
        (10, CHIP_BLUE, CRT_WHITE),
        (25, CHIP_GREEN, CRT_WHITE),
        (100, CHIP_BLACK, CRT_YELLOW),
    ]

    card_rects = [
        pygame.Rect(55 + (idx * 165), 325, 110, 165) for idx in range(5)
    ]


    # ============================================================
    #                      RENDERING LOOP
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

          if game_stage == "BETTING":
            # Check minus and plus buttons
            for i, (val, bg_col, txt_col) in enumerate(bet_configs):
              x_pos = 50 + (i * 54)
              minus_rect = pygame.Rect(x_pos, 580, 50, 24)
              plus_rect = pygame.Rect(x_pos, 608, 50, 24)

              if minus_rect.collidepoint(mouse_pos):
                if current_bet - val >= 0:
                  current_bet -= val
                  snd_bet.play()

              if plus_rect.collidepoint(mouse_pos):
                if current_bet + val <= balance:
                  current_bet += val
                  snd_bet.play()

            if clear_btn_rect.collidepoint(mouse_pos):
              current_bet = 0
              snd_bet.play()

            if draw_btn_rect.collidepoint(mouse_pos) and current_bet > 0:
              balance -= current_bet
              deck = create_deck()
              player_hand = [deck.pop() for _ in range(5)]
              animated_cards = [
                  AnimatedCard(card_rects[i], player_hand[i]) for i in range(5)
              ]
              held_cards = [False] * 5
              final_hand_rank = ""
              game_stage = "DRAWING"
              win_message = "SELECT HOLDS AND TAP DRAW"
              snd_flip.play()

          elif game_stage == "DRAWING":
            for idx, rect in enumerate(card_rects):
              if rect.collidepoint(mouse_pos):
                held_cards[idx] = not held_cards[idx]
                if held_cards[idx]:
                  snd_hold.play()
                else:
                  snd_unhold.play()

            if draw_btn_rect.collidepoint(mouse_pos):
              for idx in range(5):
                if not held_cards[idx]:
                  player_hand[idx] = deck.pop()
                  animated_cards[idx] = AnimatedCard(
                      card_rects[idx], player_hand[idx]
                  )

              snd_flip.play()
              final_hand_rank = evaluate_poker_hand(player_hand)

              payout_multiplier = 0
              for name, mult in PAYOUTS:
                if name == final_hand_rank:
                  payout_multiplier = mult
                  break

              if payout_multiplier > 0:
                winnings = current_bet * payout_multiplier
                balance += winnings
                win_message = (
                    f"WINNER! {final_hand_rank} (x{payout_multiplier}) +${winnings}"
                )
                snd_win.play()
              else:
                display_rank = (
                    final_hand_rank
                    if final_hand_rank != "HIGH CARD"
                    else "GAME OVER"
                )
                win_message = f"{display_rank} - NO PAYOUT"
                snd_lose.play()

              game_stage = "RESOLVED"

          elif game_stage == "RESOLVED":
            if draw_btn_rect.collidepoint(mouse_pos):
              player_hand.clear()
              animated_cards.clear()
              if current_bet > balance:
                current_bet = min(5, balance) if balance > 0 else 0
              game_stage = "BETTING"
              win_message = "USE CHIP BUTTONS TO SET WAGER, THEN TAP DEAL."

      # Update Animations
      for card in animated_cards:
        card.update()

      # Main CRT Frame
      screen.fill(CRT_BLACK)
      pygame.draw.rect(
          screen,
          CRT_BLUE,
          (15, 15, WIDTH - 30, HEIGHT - 30),
          0,
          8,
      )
      pygame.draw.rect(
          screen,
          CRT_YELLOW,
          (15, 15, WIDTH - 30, HEIGHT - 30),
          3,
          8,
      )

      # 1. Vintage CRT Paytable Matrix
      pygame.draw.rect(screen, CRT_DARK_BLUE, (45, 35, 860, 205))
      pygame.draw.rect(screen, CRT_YELLOW, (45, 35, 860, 205), 2)

      for i, (name, mult) in enumerate(PAYOUTS):
        col, row = i // 5, i % 5
        tx = 65 if col == 0 else 500
        ty = 48 + (row * 36)

        is_hit_row = game_stage == "RESOLVED" and final_hand_rank == name
        bg_col = CRT_YELLOW if is_hit_row else CRT_DARK_BLUE
        txt_col = CRT_BLACK if is_hit_row else CRT_WHITE

        if is_hit_row:
          pygame.draw.rect(screen, bg_col, (tx - 10, ty - 4, 400, 28))

        name_surf = pay_font.render(name.ljust(18), True, txt_col)
        mult_surf = pay_font.render(f"x{mult}", True, txt_col)

        screen.blit(name_surf, (tx, ty))
        screen.blit(mult_surf, (tx + 300, ty))

      # 2. Animated Active Cards
      for idx, anim_card in enumerate(animated_cards):
        anim_card.draw(screen, is_held=held_cards[idx])

      # 3. Control HUD Panel (Enlarged and neatly spaced vertically)
      pygame.draw.rect(screen, CRT_DARK_BLUE, (45, 525, 335, 140))
      pygame.draw.rect(screen, CRT_YELLOW, (45, 525, 335, 140), 2)

      bal_txt = ui_font.render(f"CREDITS: ${balance}", True, CRT_YELLOW)
      bet_txt = ui_font.render(f"CURRENT BET: ${current_bet}", True, CRT_WHITE)
      screen.blit(bal_txt, (55, 538))
      screen.blit(bet_txt, (55, 560))

      # Render Minus / Plus Increment Buttons (Only active during BETTING)
      if game_stage == "BETTING":
        for i, (val, bg_col, txt_col) in enumerate(bet_configs):
          x_pos = 50 + (i * 54)
          minus_rect = pygame.Rect(x_pos, 588, 50, 24)
          plus_rect = pygame.Rect(x_pos, 614, 50, 24)

          # Minus Button
          pygame.draw.rect(screen, bg_col, minus_rect, 0, 3)
          pygame.draw.rect(screen, CRT_YELLOW, minus_rect, 1, 3)
          m_txt = btn_font.render(f"-{val}", True, txt_col)
          screen.blit(
              m_txt,
              (
                  minus_rect.centerx - m_txt.get_width() // 2,
                  minus_rect.centery - m_txt.get_height() // 2,
              ),
          )

          # Plus Button
          pygame.draw.rect(screen, bg_col, plus_rect, 0, 3)
          pygame.draw.rect(screen, CRT_YELLOW, plus_rect, 1, 3)
          p_txt = btn_font.render(f"+{val}", True, txt_col)
          screen.blit(
              p_txt,
              (
                  plus_rect.centerx - p_txt.get_width() // 2,
                  plus_rect.centery - p_txt.get_height() // 2,
              ),
          )

        # Clear Bet Button
        pygame.draw.rect(screen, CRT_DARK_BLUE, clear_btn_rect, 0, 4)
        pygame.draw.rect(screen, CRT_YELLOW, clear_btn_rect, 2, 4)
        clr_txt = btn_font.render("CLEAR", True, CRT_WHITE)
        screen.blit(
            clr_txt,
            (
                clear_btn_rect.centerx - clr_txt.get_width() // 2,
                clear_btn_rect.centery - clr_txt.get_height() // 2,
            ),
        )

      # 4. Main Deal/Draw Action Button
      lbl_action = (
          "DEAL"
          if game_stage == "BETTING"
          else "DRAW"
          if game_stage == "DRAWING"
          else "AGAIN"
      )

      pygame.draw.rect(screen, CRT_RED, draw_btn_rect, 0, 4)
      pygame.draw.rect(screen, CRT_YELLOW, draw_btn_rect, 2, 4)

      main_btn_txt = btn_font.render(lbl_action, True, CRT_WHITE)
      screen.blit(
          main_btn_txt,
          (
              draw_btn_rect.centerx - main_btn_txt.get_width() // 2,
              draw_btn_rect.centery - main_btn_txt.get_height() // 2,
          ),
      )

      # 5. Message Banner
      pygame.draw.rect(screen, CRT_DARK_BLUE, (45, 675, 860, 30))
      pygame.draw.rect(screen, CRT_YELLOW, (45, 675, 860, 30), 2)

      msg_color = CRT_YELLOW if "WINNER" in win_message else CRT_WHITE
      msg_surf = label_font.render(win_message, True, msg_color)
      screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, 682))

      _hint_surf = _lobby_hint_font.render("ESC: Return to Lobby", True, (230, 200, 140))
      screen.blit(_hint_surf, (10, HEIGHT - 22))
      pygame.display.flip()
      await asyncio.sleep(0)
      clock.tick(60)
    return balance
