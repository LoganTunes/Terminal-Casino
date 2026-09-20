"""
VEGAS SCRATCH DISPENSER CABINET ENGINE (SYSTEM-ENTROPY HARD RANDOMIZATION)
==========================================================================
- Non-blocking Async Event Loop (`asyncio.sleep(0)`)
- System Entropy Randomization (`secrets.SystemRandom()`)
- Dynamic Dynamic Word Bank Generation with 1:8 Vowel-to-Consonant Odds
"""
import asyncio
import math
import secrets
import sys
import array
import pygame

# Hardware OS-Level True Randomizer
sys_rand = secrets.SystemRandom()

# ============================================================
#                    PALETTE DEFINITIONS
# ============================================================
FELT_GREEN = (12, 75, 38)
FELT_DARK = (8, 50, 25)
MAHOGANY = (48, 14, 8)
WOOD_LIGHT = (78, 26, 16)
CHROME_LIGHT = (230, 230, 230)
CHROME_SHADOW = (100, 100, 100)
VINTAGE_GOLD = (235, 180, 85)
GOLD_SHADOW = (145, 105, 45)
CREAM_WHITE = (250, 248, 235)
CHARCOAL = (20, 20, 20)
CABINET_DARK = (15, 18, 24)
CABINET_ACCENT = (35, 42, 56)
BRIGHT_RED = (210, 30, 30)
BRIGHT_GREEN = (35, 200, 70)
FOIL_GRAY = (165, 170, 175)
FOIL_SHINE = (215, 220, 225)

TIER_PALETTES = {
    1: {"bg": (245, 242, 225), "text": (30, 30, 30), "name": "Quick-Hit Cash"},
    2: {"bg": (180, 25, 25), "text": (235, 180, 85), "name": "Sizzling 7s Multipliers"},
    3: {"bg": (15, 35, 75), "text": (220, 220, 220), "name": "Royal Word Match"},
    4: {"bg": (5, 95, 45), "text": (235, 180, 85), "name": "Emerald Triple Play"},
    5: {"bg": (15, 15, 15), "text": (235, 180, 85), "name": "The Platinum Vault"}
}

CASINO_WORDBANK = [
    "ROYAL", "CASINO", "SLOTS", "CHIP", "VAULT", "LUCKY", "GOLD", "VEGAS",
    "JACKPOT", "WINNER", "POKER", "BONUS", "ACE", "KING", "QUEEN", "JACK",
    "DIAMOND", "RUBY", "SPIN", "ROLL", "DICE", "WHEEL", "CARDS", "DEALER",
    "STACK", "FLUSH", "SUIT", "RISK", "COIN", "CHANCE", "TOKEN", "PAYOUT",
    "REEL", "SEVEN", "FORTUNE", "CHARM", "SHUFFLE", "BET", "HIGH", "WILD"
]
VOWELS = set("AEIOU")

# ============================================================
#              SAFE SYNTH AUDIO GENERATOR
# ============================================================
def generate_synth_sound(freq_list, duration_ms, wave_type="triangle", volume=0.25):
    try:
        if not pygame.mixer.get_init():
            return None
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
    except Exception:
        return None

# ============================================================
#               EFFECTS & PARTICLES
# ============================================================
class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_dust(self, pos, count=5):
        for _ in range(count):
            angle = sys_rand.uniform(0, math.pi * 2)
            speed = sys_rand.uniform(1.0, 3.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = sys_rand.choice([FOIL_SHINE, VINTAGE_GOLD, CREAM_WHITE])
            size = sys_rand.randint(2, 4)
            life = sys_rand.randint(12, 25)
            self.particles.append([list(pos), [vx, vy], color, size, life])

    def update_and_draw(self, surface):
        for p in self.particles[:]:
            p[0][0] += p[1][0]
            p[0][1] += p[1][1]
            p[4] -= 1
            if p[4] <= 0:
                self.particles.remove(p)
            else:
                pygame.draw.circle(surface, p[2], (int(p[0][0]), int(p[0][1])), p[3])

# ============================================================
#                 BANKROLL MANAGEMENT
# ============================================================
class CasinoBankroll:
    def __init__(self, initial_chips=1000):
        self.balance = initial_chips

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False

# ============================================================
#          SYSTEM-ENTROPY CSPRNG DATA GENERATOR
# ============================================================
class TicketPayloadGenerator:
    @classmethod
    def generate_payload(cls, tier, wager):
        win_chance = sys_rand.randrange(100)
        is_winner = win_chance < 38
        multiplier = 0

        if is_winner:
            mult_roll = sys_rand.randrange(100)
            if mult_roll < 60:
                multiplier = 2
            elif mult_roll < 85:
                multiplier = 3
            elif mult_roll < 95:
                multiplier = 5
            else:
                multiplier = 10

        total_payout = wager * multiplier if is_winner else 0

        payload = {
            "tier": tier,
            "wager": wager,
            "payout": total_payout,
            "is_winner": is_winner,
            "multiplier": multiplier,
            "scratch_targets": []
        }

        if tier == 1:
            win_num = sys_rand.randint(10, 30)
            payload["winning_numbers"] = [win_num]
            your_nums = []
            for i in range(4):
                if is_winner and i == 0:
                    your_nums.append((win_num, total_payout))
                else:
                    fake_num = sys_rand.randint(10, 30)
                    while fake_num == win_num or fake_num in [n[0] for n in your_nums]:
                        fake_num = sys_rand.randint(10, 30)
                    your_nums.append((fake_num, 0))
            sys_rand.shuffle(your_nums)
            payload["your_numbers"] = your_nums

        elif tier == 2:
            win_nums = [sys_rand.randint(1, 50), sys_rand.randint(1, 50)]
            while win_nums[0] == win_nums[1]:
                win_nums[1] = sys_rand.randint(1, 50)
            payload["winning_numbers"] = win_nums

            your_spots = []
            winning_slots = [0, 1] if multiplier >= 5 else [0]
            for i in range(8):
                if is_winner and i in winning_slots:
                    target_win = total_payout // len(winning_slots)
                    your_spots.append((sys_rand.choice(win_nums), target_win, f"{multiplier}X" if multiplier > 1 else "1X"))
                else:
                    fake_num = sys_rand.randint(1, 50)
                    while fake_num in win_nums or fake_num in [s[0] for s in your_spots]:
                        fake_num = sys_rand.randint(1, 50)
                    your_spots.append((fake_num, 0, "1X"))
            sys_rand.shuffle(your_spots)
            payload["your_spots"] = your_spots

        elif tier == 3:
            # Fully dynamic target words shuffle per ticket call
            target_words = sys_rand.sample(CASINO_WORDBANK, 8)
            payload["target_words"] = target_words
            per_letter_rate = max(10, wager // 4)
            caller_letters = []

            target_win_count = 1 if is_winner else 0
            alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

            def word_is_complete(word, letter_set):
                return all(c in letter_set for c in word)

            def current_completed_words(letter_set):
                return [w for w in target_words if word_is_complete(w, letter_set)]

            def is_safe_to_add(char):
                if char in caller_letters:
                    return False
                test_set = set(caller_letters + [char])
                completed = current_completed_words(test_set)
                if len(completed) > target_win_count:
                    return False
                return True

            # If winning ticket, force letters for 1 winning word
            if is_winner:
                winning_word = sys_rand.choice(target_words)
                for char in winning_word:
                    if char not in caller_letters:
                        caller_letters.append(char)

            # System Entropy Weighted Letter Picker (Vowels = 1, Consonants = 8)
            while len(caller_letters) < 16:
                candidates = []
                weights = []
                for c in alphabet:
                    if is_safe_to_add(c):
                        candidates.append(c)
                        weights.append(1 if c in VOWELS else 8)

                if not candidates:
                    break

                # Hardware-random weighted sampling
                chosen_char = sys_rand.choices(candidates, weights=weights, k=1)[0]
                caller_letters.append(chosen_char)

            # Extra entropy shuffle on the final sequence
            sys_rand.shuffle(caller_letters)
            payload["caller_letters"] = caller_letters[:16]

            # Recalculate payout from final letter state
            actual_payout = 0
            for w in target_words:
                if word_is_complete(w, set(payload["caller_letters"])):
                    actual_payout += len(w) * per_letter_rate

            payload["payout"] = actual_payout
            payload["is_winner"] = actual_payout > 0

        elif tier == 4:
            payload["game1_num"] = sys_rand.randint(1, 20)
            payload["game1_your"] = [sys_rand.randint(1, 20) for _ in range(3)]
            payload["game2_fast"] = f"${total_payout}" if is_winner else "TRY AGAIN"
            payload["game3_wheel"] = [total_payout if is_winner else 0, 0, 0, 0]
            sys_rand.shuffle(payload["game3_wheel"])

        elif tier == 5:
            player_keys = [sys_rand.randint(1, 9) for _ in range(6)]
            payload["grid_keys"] = player_keys
            safes = []
            for i in range(3):
                if is_winner and i == 0:
                    d1 = sys_rand.choice(player_keys)
                    d2 = sys_rand.choice(player_keys)
                    code = f"{d1}{d2}"
                    payout = total_payout
                else:
                    non_keys = [d for d in range(1, 10) if d not in player_keys]
                    if non_keys:
                        d1 = sys_rand.choice(non_keys)
                        d2 = sys_rand.randint(1, 9)
                    else:
                        d1, d2 = 0, 0
                    code = f"{d1}{d2}"
                    payout = 0
                safes.append({"code": code, "payout": payout})
            sys_rand.shuffle(safes)
            payload["safes"] = safes

        return payload

# ============================================================
#              REALISTIC VENDING MACHINE CABINET
# ============================================================
class VendingMachineCabinet:
    Y_SHIFT = 25

    def __init__(self, fonts, sfx):
        self.inserted_wager = 0
        self.active_tier = None
        self.fonts = fonts
        self.sfx = sfx

        s = self.Y_SHIFT
        self.dispense_rect = pygame.Rect(725, 445 + s, 170, 45)
        self.clear_rect = pygame.Rect(725, 500 + s, 170, 40)

        self.chip_buttons = [
            (10, pygame.Rect(440, 595 + s, 45, 45), (240, 240, 240), (40, 40, 40)),
            (50, pygame.Rect(500, 595 + s, 45, 45), (180, 30, 30), (240, 240, 240)),
            (100, pygame.Rect(560, 595 + s, 45, 45), (30, 80, 180), (240, 240, 240)),
            (250, pygame.Rect(620, 595 + s, 45, 45), (30, 130, 60), (235, 180, 85)),
            (1000, pygame.Rect(680, 595 + s, 45, 45), (30, 30, 30), (235, 180, 85))
        ]

    def update_tier_lock(self):
        w = self.inserted_wager
        if 10 <= w <= 40:
            self.active_tier = 1
        elif 50 <= w <= 90:
            self.active_tier = 2
        elif 100 <= w <= 240:
            self.active_tier = 3
        elif 250 <= w <= 990:
            self.active_tier = 4
        elif 1000 <= w <= 5000:
            self.active_tier = 5
        else:
            self.active_tier = None

    def handle_input(self, mouse_pos, bankroll):
        for val, rect, _, _ in self.chip_buttons:
            if rect.collidepoint(mouse_pos):
                if self.inserted_wager + val <= 5000:
                    if bankroll.withdraw(val):
                        self.inserted_wager += val
                        self.update_tier_lock()
                        if self.sfx["chip"]: self.sfx["chip"].play()
                        return "DEPOSIT"

        if self.clear_rect.collidepoint(mouse_pos) and self.inserted_wager > 0:
            bankroll.deposit(self.inserted_wager)
            self.inserted_wager = 0
            self.active_tier = None
            if self.sfx["chip"]: self.sfx["chip"].play()
            return "CLEAR"

        if self.dispense_rect.collidepoint(mouse_pos) and self.active_tier is not None:
            if self.sfx["dispense"]: self.sfx["dispense"].play()
            return "DISPENSE"

        return None

    def draw(self, surface, frame_counter):
        label_font = self.fonts["label"]
        ui_font = self.fonts["ui"]
        chip_num_font = self.fonts["chip_num"]
        s = self.Y_SHIFT

        cab_rect = pygame.Rect(430, 50 + s, 480, 600)
        pygame.draw.rect(surface, CABINET_DARK, cab_rect, 0, 12)
        pygame.draw.rect(surface, CHROME_SHADOW, cab_rect, 5, 12)
        pygame.draw.rect(surface, CHROME_LIGHT, cab_rect.inflate(-8, -8), 2, 10)

        for rx, ry in [(445, 65 + s), (895, 65 + s), (445, 635 + s), (895, 635 + s)]:
            pygame.draw.circle(surface, CHROME_LIGHT, (rx, ry), 4)
            pygame.draw.circle(surface, CHARCOAL, (rx, ry), 2)

        glass_rect = pygame.Rect(450, 75 + s, 255, 480)
        pygame.draw.rect(surface, (10, 15, 22), glass_rect, 0, 6)
        pygame.draw.rect(surface, CHROME_SHADOW, glass_rect, 2, 6)

        tier_ranges = [
            (1, "$10 - $40", "Quick Cash"),
            (2, "$50 - $90", "Sizzling 7s"),
            (3, "$100 - $240", "Royal Word"),
            (4, "$250 - $990", "Triple Play"),
            (5, "$1000+", "Platinum Vault")
        ]

        for idx, range_lbl, name in tier_ranges:
            ty = 90 + s + ((idx - 1) * 92)
            is_active = (self.active_tier == idx)
            pygame.draw.rect(surface, CHROME_SHADOW, (460, ty + 70, 235, 6))

            card_bg = TIER_PALETTES[idx]["bg"]
            pygame.draw.rect(surface, card_bg, (470, ty, 215, 65), 0, 4)
            pygame.draw.rect(surface, VINTAGE_GOLD if is_active else CHROME_SHADOW, (470, ty, 215, 65), 2, 4)

            t_lbl = label_font.render(f"A{idx} | {range_lbl}", True, TIER_PALETTES[idx]["text"])
            n_lbl = ui_font.render(name, True, TIER_PALETTES[idx]["text"])
            surface.blit(t_lbl, (480, ty + 8))
            surface.blit(n_lbl, (480, ty + 30))

            led_color = BRIGHT_GREEN if is_active else (50, 60, 70)
            pygame.draw.circle(surface, led_color, (665, ty + 32), 7)
            if is_active:
                pygame.draw.circle(surface, CREAM_WHITE, (665, ty + 32), 3)

        pygame.draw.line(surface, (255, 255, 255, 40), (460, 85 + s), (650, 540 + s), 3)
        pygame.draw.line(surface, (255, 255, 255, 20), (480, 85 + s), (670, 540 + s), 2)

        panel_rect = pygame.Rect(715, 75 + s, 180, 480)
        pygame.draw.rect(surface, CABINET_ACCENT, panel_rect, 0, 6)
        pygame.draw.rect(surface, CHROME_SHADOW, panel_rect, 2, 6)

        disp_screen = pygame.Rect(725, 90 + s, 160, 60)
        pygame.draw.rect(surface, CHARCOAL, disp_screen, 0, 4)
        pygame.draw.rect(surface, VINTAGE_GOLD, disp_screen, 2, 4)

        lbl_w = label_font.render("INSERTED CREDIT", True, CHROME_SHADOW)
        val_w = ui_font.render(f"${self.inserted_wager}.00", True, BRIGHT_GREEN)
        surface.blit(lbl_w, (735, 98 + s))
        surface.blit(val_w, (735, 120 + s))

        pygame.draw.rect(surface, CHARCOAL, (755, 170 + s, 100, 35), 0, 4)
        pygame.draw.rect(surface, CHROME_LIGHT, (755, 170 + s, 100, 35), 2, 4)
        pygame.draw.rect(surface, (5, 5, 5), (770, 182 + s, 70, 10), 0, 2)
        c_slot_lbl = label_font.render("INSERT CHIPS", True, CHROME_LIGHT)
        surface.blit(c_slot_lbl, (765, 212 + s))

        dispense_ready = (self.active_tier is not None)
        pygame.draw.rect(surface, BRIGHT_GREEN if dispense_ready else (40, 60, 40), self.dispense_rect, 0, 6)
        pygame.draw.rect(surface, CREAM_WHITE if dispense_ready else CHROME_SHADOW, self.dispense_rect, 2, 6)
        d_txt = label_font.render("PUSH TO DISPENSE", True, CREAM_WHITE if dispense_ready else CHROME_SHADOW)
        surface.blit(d_txt, (self.dispense_rect.centerx - d_txt.get_width() // 2, self.dispense_rect.centery - d_txt.get_height() // 2))

        pygame.draw.rect(surface, BRIGHT_RED if self.inserted_wager > 0 else (60, 40, 40), self.clear_rect, 0, 6)
        pygame.draw.rect(surface, CREAM_WHITE if self.inserted_wager > 0 else CHROME_SHADOW, self.clear_rect, 2, 6)
        c_txt = label_font.render("COIN RETURN", True, CREAM_WHITE if self.inserted_wager > 0 else CHROME_SHADOW)
        surface.blit(c_txt, (self.clear_rect.centerx - c_txt.get_width() // 2, self.clear_rect.centery - c_txt.get_height() // 2))

        chute_rect = pygame.Rect(725, 260 + s, 160, 160)
        pygame.draw.rect(surface, CHARCOAL, chute_rect, 0, 6)
        pygame.draw.rect(surface, CHROME_SHADOW, chute_rect, 3, 6)
        pygame.draw.rect(surface, (10, 10, 10), (735, 275 + s, 140, 130), 0, 4)
        chute_lbl = label_font.render("DISPENSER CHUTE", True, CHROME_SHADOW)
        surface.blit(chute_lbl, (745, 330 + s))

        for val, rect, col_bg, col_str in self.chip_buttons:
            pygame.draw.circle(surface, CHARCOAL, rect.center, 22)
            pygame.draw.circle(surface, col_bg, rect.center, 20)
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                pygame.draw.circle(surface, col_str, (int(rect.centerx + math.cos(rad) * 15), int(rect.centery + math.sin(rad) * 15)), 2)
            pygame.draw.circle(surface, CREAM_WHITE, rect.center, 13)
            display_str = str(val) if val < 1000 else f"{val // 1000}k"
            val_txt = chip_num_font.render(f"${display_str}", True, CHARCOAL)
            surface.blit(val_txt, (rect.centerx - val_txt.get_width() // 2, rect.centery - val_txt.get_height() // 2))

# ============================================================
#                PRE-RENDERED PRIZE CANVAS
# ============================================================
class TicketRenderer:
    @staticmethod
    def render_canvas(payload, fonts):
        ticket_title_font = fonts["ticket_title"]
        ticket_body_font = fonts["ticket_body"]
        prize_font = fonts["prize"]
        word_font = fonts["word"]
        label_font = fonts["label"]

        canvas = pygame.Surface((340, 540))
        tier = payload["tier"]
        palette = TIER_PALETTES[tier]

        canvas.fill(palette["bg"])
        pygame.draw.rect(canvas, VINTAGE_GOLD, (5, 5, 330, 530), 4, 6)
        pygame.draw.rect(canvas, palette["text"], (11, 11, 318, 518), 1, 4)

        title = ticket_title_font.render(palette["name"], True, palette["text"])
        canvas.blit(title, (170 - title.get_width() // 2, 20))

        w_lbl = ticket_body_font.render(f"WAGER: ${payload['wager']} | TIER {tier}", True, palette["text"])
        canvas.blit(w_lbl, (170 - w_lbl.get_width() // 2, 55))

        payload["scratch_targets"] = []

        if tier == 1:
            win_txt = ticket_body_font.render("WINNING NUMBER", True, palette["text"])
            canvas.blit(win_txt, (170 - win_txt.get_width() // 2, 90))
            w_rect = pygame.Rect(140, 115, 60, 50)
            pygame.draw.rect(canvas, palette["text"], w_rect, 2, 4)
            num_surf = prize_font.render(str(payload["winning_numbers"][0]), True, palette["text"])
            canvas.blit(num_surf, (170 - num_surf.get_width() // 2, 130))
            payload["scratch_targets"].append({"id": "w0", "rect": w_rect, "cleared": False})

            your_txt = ticket_body_font.render("YOUR NUMBERS & PRIZES", True, palette["text"])
            canvas.blit(your_txt, (170 - your_txt.get_width() // 2, 195))

            for i, (num, prize) in enumerate(payload["your_numbers"]):
                rx = 40 + (i % 2) * 140
                ry = 230 + (i // 2) * 90
                box_rect = pygame.Rect(rx, ry, 120, 70)
                pygame.draw.rect(canvas, palette["text"], box_rect, 1, 4)
                n_surf = prize_font.render(str(num), True, palette["text"])
                p_str = f"${prize}" if prize > 0 else "TRY AGAIN"
                p_surf = ticket_body_font.render(p_str, True, BRIGHT_GREEN if prize > 0 else palette["text"])
                canvas.blit(n_surf, (box_rect.centerx - n_surf.get_width() // 2, ry + 12))
                canvas.blit(p_surf, (box_rect.centerx - p_surf.get_width() // 2, ry + 42))
                payload["scratch_targets"].append({"id": f"y{i}", "rect": box_rect, "cleared": False})

        elif tier == 2:
            win_txt = ticket_body_font.render("LUCKY NUMBERS", True, palette["text"])
            canvas.blit(win_txt, (170 - win_txt.get_width() // 2, 90))
            for i, win_num in enumerate(payload["winning_numbers"]):
                w_rect = pygame.Rect(95 + (i * 90), 115, 60, 50)
                pygame.draw.rect(canvas, palette["text"], w_rect, 2, 4)
                num_surf = prize_font.render(str(win_num), True, palette["text"])
                canvas.blit(num_surf, (w_rect.centerx - num_surf.get_width() // 2, 130))
                payload["scratch_targets"].append({"id": f"w{i}", "rect": w_rect, "cleared": False})

            your_txt = ticket_body_font.render("THE SIZZLING GRID", True, palette["text"])
            canvas.blit(your_txt, (170 - your_txt.get_width() // 2, 195))

            for i, (num, prize, mult) in enumerate(payload["your_spots"]):
                rx = 40 + (i % 2) * 140
                ry = 225 + (i // 2) * 70
                box_rect = pygame.Rect(rx, ry, 120, 60)
                pygame.draw.rect(canvas, palette["text"], box_rect, 1, 4)
                n_surf = prize_font.render(str(num), True, palette["text"])
                p_str = f"${prize}" if prize > 0 else "LOSE"
                if prize > 0 and mult != "1X":
                    p_str += f" ({mult})"
                p_surf = ticket_body_font.render(p_str, True, GOLD_SHADOW if prize > 0 else palette["text"])
                canvas.blit(n_surf, (box_rect.centerx - n_surf.get_width() // 2, ry + 10))
                canvas.blit(p_surf, (box_rect.centerx - p_surf.get_width() // 2, ry + 34))
                payload["scratch_targets"].append({"id": f"y{i}", "rect": box_rect, "cleared": False})

        elif tier == 3:
            c_lbl = ticket_body_font.render("YOUR CALLER LETTERS", True, palette["text"])
            canvas.blit(c_lbl, (170 - c_lbl.get_width() // 2, 80))

            caller_letters = payload["caller_letters"]
            letters_top = " ".join(caller_letters[:8])
            letters_bot = " ".join(caller_letters[8:])

            bank_rect = pygame.Rect(20, 100, 300, 65)
            pygame.draw.rect(canvas, palette["text"], bank_rect, 2, 4)

            l_surf1 = prize_font.render(letters_top, True, VINTAGE_GOLD)
            l_surf2 = prize_font.render(letters_bot, True, VINTAGE_GOLD)
            canvas.blit(l_surf1, (170 - l_surf1.get_width() // 2, 108))
            canvas.blit(l_surf2, (170 - l_surf2.get_width() // 2, 135))
            payload["scratch_targets"].append({"id": "caller", "rect": bank_rect, "cleared": False})

            w_hdr = ticket_body_font.render("YOUR TARGET WORDS", True, palette["text"])
            canvas.blit(w_hdr, (170 - w_hdr.get_width() // 2, 180))

            target_words = payload["target_words"]
            per_letter_rate = max(10, payload["wager"] // 4)

            for i, word in enumerate(target_words):
                col = i % 2
                row = i // 2
                wx = 30 + (col * 145)
                wy = 205 + (row * 72)
                word_rect = pygame.Rect(wx, wy, 135, 62)
                pygame.draw.rect(canvas, (20, 30, 50), word_rect, 0, 4)
                pygame.draw.rect(canvas, VINTAGE_GOLD, word_rect, 2, 4)

                letter_surfaces = []
                total_width = 0
                for char in word:
                    color = BRIGHT_GREEN if char in caller_letters else CREAM_WHITE
                    ls = word_font.render(char, True, color)
                    letter_surfaces.append(ls)
                    total_width += ls.get_width()

                start_x = word_rect.centerx - (total_width // 2)
                curr_x = start_x
                for ls in letter_surfaces:
                    canvas.blit(ls, (curr_x, wy + 8))
                    curr_x += ls.get_width()

                all_matched = all(char in caller_letters for char in word)
                word_val = len(word) * per_letter_rate
                if all_matched:
                    p_str = f"${word_val}"
                    p_col = BRIGHT_GREEN
                else:
                    p_str = "MATCH LETTERS"
                    p_col = FOIL_GRAY

                p_surf = label_font.render(p_str, True, p_col)
                canvas.blit(p_surf, (word_rect.centerx - p_surf.get_width() // 2, wy + 36))
                payload["scratch_targets"].append({"id": f"word_{i}", "rect": word_rect, "cleared": False})

            rules_txt = label_font.render("MATCH ALL LETTERS IN A WORD TO WIN!", True, VINTAGE_GOLD)
            canvas.blit(rules_txt, (170 - rules_txt.get_width() // 2, 505))

        elif tier == 4:
            g1_rect = pygame.Rect(20, 90, 300, 110)
            pygame.draw.rect(canvas, palette["text"], g1_rect, 2, 4)
            g1_txt = label_font.render("GAME 1: LUCKY MATCH", True, VINTAGE_GOLD)
            canvas.blit(g1_txt, (30, 98))

            nums_str = f"LUCKY: {payload['game1_num']}  |  YOUR: {payload['game1_your']}"
            g1_surf = ticket_body_font.render(nums_str, True, palette["text"])
            canvas.blit(g1_surf, (30, 135))
            payload["scratch_targets"].append({"id": "g1", "rect": g1_rect, "cleared": False})

            g2_rect = pygame.Rect(20, 215, 300, 80)
            pygame.draw.rect(canvas, palette["text"], g2_rect, 2, 4)
            g2_txt = label_font.render("GAME 2: FAST SPOT REVEAL", True, VINTAGE_GOLD)
            canvas.blit(g2_txt, (30, 223))
            g2_surf = prize_font.render(payload["game2_fast"], True, BRIGHT_GREEN if payload["is_winner"] else palette["text"])
            canvas.blit(g2_surf, (170 - g2_surf.get_width() // 2, 250))
            payload["scratch_targets"].append({"id": "g2", "rect": g2_rect, "cleared": False})

            g3_rect = pygame.Rect(20, 310, 300, 180)
            pygame.draw.rect(canvas, palette["text"], g3_rect, 2, 4)
            g3_txt = label_font.render("GAME 3: MINI WHEEL REVEAL", True, VINTAGE_GOLD)
            canvas.blit(g3_txt, (30, 318))
            p_str = f"PRIZE: ${payload['payout']}" if payload['is_winner'] else "TRY AGAIN"
            g3_surf = prize_font.render(p_str, True, BRIGHT_GREEN if payload['is_winner'] else palette["text"])
            canvas.blit(g3_surf, (170 - g3_surf.get_width() // 2, 390))
            payload["scratch_targets"].append({"id": "g3", "rect": g3_rect, "cleared": False})

        elif tier == 5:
            s_lbl = ticket_body_font.render("COMBINATION SAFES", True, VINTAGE_GOLD)
            canvas.blit(s_lbl, (170 - s_lbl.get_width() // 2, 85))

            for i, safe in enumerate(payload["safes"]):
                s_rect = pygame.Rect(20 + (i * 105), 110, 90, 90)
                pygame.draw.rect(canvas, VINTAGE_GOLD, s_rect, 2, 6)
                code_txt = prize_font.render(safe["code"], True, CREAM_WHITE)
                canvas.blit(code_txt, (s_rect.centerx - code_txt.get_width() // 2, 130))
                p_str = f"${safe['payout']}" if safe['payout'] > 0 else "LOCKED"
                p_txt = label_font.render(p_str, True, BRIGHT_GREEN if safe['payout'] > 0 else CHROME_SHADOW)
                canvas.blit(p_txt, (s_rect.centerx - p_txt.get_width() // 2, 160))
                payload["scratch_targets"].append({"id": f"safe_{i}", "rect": s_rect, "cleared": False})

            k_rect = pygame.Rect(20, 220, 300, 280)
            pygame.draw.rect(canvas, VINTAGE_GOLD, k_rect, 2, 6)
            k_title = label_font.render("VAULT KEY CODES", True, VINTAGE_GOLD)
            canvas.blit(k_title, (170 - k_title.get_width() // 2, 235))

            keys_str = " - ".join(map(str, payload["grid_keys"]))
            k_surf = prize_font.render(keys_str, True, CREAM_WHITE)
            canvas.blit(k_surf, (170 - k_surf.get_width() // 2, 340))
            payload["scratch_targets"].append({"id": "keys", "rect": k_rect, "cleared": False})

        return canvas

# ============================================================
#             DYNAMIC ALPHA MASK ERASE ENGINE
# ============================================================
class ScratchCanvas:
    def __init__(self, width=340, height=540):
        self.width = width
        self.height = height
        self.foil_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    def reset_foil_for_targets(self, targets):
        self.foil_surface.fill((0, 0, 0, 0))
        for target in targets:
            rect = target["rect"]
            pygame.draw.rect(self.foil_surface, FOIL_GRAY, rect, 0, 4)
            for i in range(-rect.height, rect.width, 12):
                start = (rect.left + i, rect.top)
                end = (rect.left + i + rect.height, rect.bottom)
                pygame.draw.line(self.foil_surface, FOIL_SHINE, start, end, 2)
            pygame.draw.rect(self.foil_surface, CHARCOAL, rect, 2, 4)

    def scratch_line(self, pos_start, pos_end, radius):
        erase_radius = 18
        pygame.draw.line(self.foil_surface, (0, 0, 0, 0), pos_start, pos_end, erase_radius * 2)
        pygame.draw.circle(self.foil_surface, (0, 0, 0, 0), pos_end, erase_radius)

    def audit_reveal_thresholds(self, targets):
        for target in targets:
            if target["cleared"]:
                continue
            rect = target["rect"]
            check_points = [
                (rect.left + 8, rect.top + 8),
                (rect.right - 8, rect.top + 8),
                (rect.left + 8, rect.bottom - 8),
                (rect.right - 8, rect.bottom - 8),
                (rect.centerx, rect.centery)
            ]

            scratched_count = 0
            for pt_x, pt_y in check_points:
                if 0 <= pt_x < self.width and 0 <= pt_y < self.height:
                    pixel = self.foil_surface.get_at((pt_x, pt_y))
                    if pixel[3] == 0:
                        scratched_count += 1

            if scratched_count >= 3:
                target["cleared"] = True
                pygame.draw.rect(self.foil_surface, (0, 0, 0, 0), rect)

# ============================================================
#                    MAIN ASYNC GAME LOOP
# ============================================================
async def run_lottery(balance=1000):
    pygame.init()
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    except Exception:
        pass

    WIDTH, HEIGHT = 950, 720
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

    pygame.display.set_caption("Vegas Scratch Dispenser Cabinet Engine")
    clock = pygame.time.Clock()

    sfx = {
        "chip": generate_synth_sound([300, 600], 40, "triangle", 0.25),
        "dispense": generate_synth_sound([150, 200, 250, 180], 300, "triangle", 0.2),
        "scrape": generate_synth_sound([100, 80, 110], 15, "square", 0.05)
    }

    FONT_SANS = ("sans-serif", "arial", "helvetica")
    FONT_SERIF = ("serif", "georgia", "times new roman")
    FONT_MONO = ("monospace", "courier new", "courier")

    fonts = {
        "ui": pygame.font.SysFont(FONT_SANS, 18, bold=True),
        "label": pygame.font.SysFont(FONT_SANS, 13, bold=True),
        "ticket_title": pygame.font.SysFont(FONT_SERIF, 22, bold=True),
        "ticket_body": pygame.font.SysFont(FONT_MONO, 13, bold=True),
        "prize": pygame.font.SysFont(FONT_SANS, 18, bold=True),
        "chip_num": pygame.font.SysFont(FONT_SANS, 11, bold=True),
        "word": pygame.font.SysFont(FONT_SANS, 16, bold=True)
    }

    bankroll = CasinoBankroll(balance)
    cabinet = VendingMachineCabinet(fonts, sfx)
    scratch_canvas = ScratchCanvas()
    particle_engine = ParticleSystem()

    current_mode = "VENDING_MODE"
    ticket_payload = None
    pre_rendered_ticket = None
    ticket_pos_x = 305
    ticket_pos_y = 700
    prev_mouse_pos = None
    poker_chip_radius = 22
    frame_counter = 0
    running = True

    while running:
        frame_counter += 1
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return bankroll.balance + cabinet.inserted_wager
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_mode == "VENDING_MODE":
                    action = cabinet.handle_input(mouse_pos, bankroll)
                    if action == "DISPENSE":
                        current_mode = "DISPENSE_ANIMATION"
                        ticket_payload = TicketPayloadGenerator.generate_payload(
                            cabinet.active_tier,
                            cabinet.inserted_wager
                        )
                        pre_rendered_ticket = TicketRenderer.render_canvas(ticket_payload, fonts)
                        scratch_canvas.reset_foil_for_targets(ticket_payload["scratch_targets"])
                        ticket_pos_x = 305
                        ticket_pos_y = 720
                elif current_mode == "SCRATCH_MODE":
                    back_rect = pygame.Rect(725, 600 + cabinet.Y_SHIFT, 180, 45)
                    if back_rect.collidepoint(mouse_pos):
                        bankroll.deposit(ticket_payload["payout"])
                        cabinet.inserted_wager = 0
                        cabinet.active_tier = None
                        ticket_payload = None
                        pre_rendered_ticket = None
                        current_mode = "VENDING_MODE"
                        if sfx["chip"]: sfx["chip"].play()
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                prev_mouse_pos = None

        if not running:
            break

        if current_mode == "DISPENSE_ANIMATION":
            ticket_pos_y -= 22
            if ticket_pos_y <= 90:
                ticket_pos_y = 90
                current_mode = "SCRATCH_MODE"

        elif current_mode == "SCRATCH_MODE":
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0]:
                local_x = mouse_pos[0] - ticket_pos_x
                local_y = mouse_pos[1] - ticket_pos_y
                if 0 <= local_x < 340 and 0 <= local_y < 540:
                    current_local = (local_x, local_y)
                    start_local = prev_mouse_pos if prev_mouse_pos else current_local
                    scratch_canvas.scratch_line(start_local, current_local, poker_chip_radius)
                    prev_mouse_pos = current_local
                    particle_engine.emit_dust(mouse_pos, count=3)
                    if sys_rand.random() < 0.35 and sfx["scrape"]:
                        sfx["scrape"].play()
            else:
                prev_mouse_pos = None

            scratch_canvas.audit_reveal_thresholds(ticket_payload["scratch_targets"])

        screen.fill(MAHOGANY)
        pygame.draw.rect(screen, WOOD_LIGHT, (10, 10, WIDTH - 20, HEIGHT - 20), 10)
        pygame.draw.rect(screen, FELT_GREEN, (20, 20, WIDTH - 40, HEIGHT - 40))

        for y_line in range(25, HEIGHT - 25, 6):
            pygame.draw.line(screen, FELT_DARK, (25, y_line), (WIDTH - 25, y_line), 1)

        pulse_alpha = math.sin(frame_counter * 0.08) * 40 + 215
        marquee_gold = (int(pulse_alpha), 180, 85)

        pygame.draw.rect(screen, CHARCOAL, (45, 20, 860, 45), 0, 4)
        pygame.draw.rect(screen, marquee_gold, (45, 20, 860, 45), 2, 4)

        if current_mode == "VENDING_MODE":
            msg = "INSERT CHIPS INTO SLOT TO LOCK IN TIER SELECTION." if not cabinet.active_tier else "TIER READY! PUSH DISPENSE BUTTON TO CLAIM TICKET."
        elif current_mode == "DISPENSE_ANIMATION":
            msg = "MECHANICAL DISPENSER ACTIVE... DISPENSING TICKET..."
        else:
            revealed_all = all(t["cleared"] for t in ticket_payload["scratch_targets"])
            if revealed_all:
                msg = f"TICKET COMPLETE! PAYOUT: +${ticket_payload['payout']}!"
            else:
                msg = "SCRATCH FOIL PANELS WITH YOUR CHIP TO REVEAL PRIZES."

        msg_color = BRIGHT_GREEN if ("WINNER" in msg or ("COMPLETE" in msg and ticket_payload["payout"] > 0)) else marquee_gold
        screen.blit(fonts["ui"].render(msg, True, msg_color), (65, 32))

        bal_x = 55
        bal_y = 650
        pygame.draw.rect(screen, CHARCOAL, (bal_x, bal_y, 340, 45), 0, 6)
        pygame.draw.rect(screen, VINTAGE_GOLD, (bal_x, bal_y, 340, 45), 2, 6)
        screen.blit(fonts["label"].render("CHIP BANK BALANCE:", True, CHROME_LIGHT), (bal_x + 15, bal_y + 15))
        screen.blit(fonts["ui"].render(f"${bankroll.balance}", True, BRIGHT_GREEN), (bal_x + 165, bal_y + 13))

        if current_mode == "VENDING_MODE":
            s = cabinet.Y_SHIFT
            pygame.draw.rect(screen, CHARCOAL, (45, 80 + s, 360, 560), 0, 8)
            pygame.draw.rect(screen, CHROME_SHADOW, (45, 80 + s, 360, 560), 6, 8)
            pygame.draw.rect(screen, CHARCOAL, (55, 615 + s, 340, 15), 0, 2)
            cabinet.draw(screen, frame_counter)

        elif current_mode in ["DISPENSE_ANIMATION", "SCRATCH_MODE"]:
            pygame.draw.rect(screen, CHARCOAL, (ticket_pos_x + 8, ticket_pos_y + 8, 340, 540), 0, 6)
            screen.blit(pre_rendered_ticket, (ticket_pos_x, ticket_pos_y))
            screen.blit(scratch_canvas.foil_surface, (ticket_pos_x, ticket_pos_y))

            if current_mode == "SCRATCH_MODE":
                back_rect = pygame.Rect(725, 600 + cabinet.Y_SHIFT, 180, 45)
                pygame.draw.rect(screen, BRIGHT_GREEN, back_rect, 0, 5)
                pygame.draw.rect(screen, CREAM_WHITE, back_rect, 1, 5)
                b_txt = fonts["label"].render("COLLECT & EXIT", True, CHARCOAL)
                screen.blit(b_txt, (back_rect.centerx - b_txt.get_width() // 2, back_rect.centery - b_txt.get_height() // 2))

                w = ticket_payload["wager"]
                if w >= 1000:
                    chip_bg, chip_trim = CHARCOAL, VINTAGE_GOLD
                elif w >= 250:
                    chip_bg, chip_trim = (30, 130, 60), VINTAGE_GOLD
                elif w >= 100:
                    chip_bg, chip_trim = (30, 80, 180), CREAM_WHITE
                elif w >= 50:
                    chip_bg, chip_trim = BRIGHT_RED, CREAM_WHITE
                else:
                    chip_bg, chip_trim = CREAM_WHITE, CHARCOAL

                pygame.draw.circle(screen, CHARCOAL, mouse_pos, poker_chip_radius + 2)
                pygame.draw.circle(screen, chip_bg, mouse_pos, poker_chip_radius)
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    pygame.draw.circle(screen, chip_trim, (int(mouse_pos[0] + math.cos(rad) * 16), int(mouse_pos[1] + math.sin(rad) * 16)), 2)
                pygame.draw.circle(screen, CREAM_WHITE, mouse_pos, int(poker_chip_radius * 0.55))

        particle_engine.update_and_draw(screen)
        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(60)

    return bankroll.balance + cabinet.inserted_wager

if __name__ == "__main__":
    asyncio.run(run_lottery(1000))
