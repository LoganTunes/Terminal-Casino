import asyncio
import math
import random
import secrets
import struct
import sys
import pygame

# ==========================================
# CONSTANTS & SETUP
# ==========================================
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60

# Palette
COLOR_BG = (18, 18, 24)
COLOR_CABINET = (35, 40, 55)
COLOR_CABINET_BORDER = (60, 70, 95)
COLOR_GOLD = (245, 190, 40)
COLOR_WHITE = (245, 245, 245)
COLOR_BLACK = (15, 15, 15)
COLOR_RED = (220, 50, 50)
COLOR_GREEN = (40, 200, 100)
COLOR_SILVER = (190, 195, 205)
COLOR_DARK_SILVER = (120, 125, 135)

# Game States
STATE_VENDING = 0
STATE_DISPENSING = 1
STATE_SCRATCHING = 2

# Tier Configurations
TIER_CONFIGS = {
    1: {"name": "LUCKY SEVENS", "cost": 5, "color": (210, 40, 40)},
    2: {"name": "HIGH ROLLER MATCH", "cost": 10, "color": (40, 120, 220)},
    3: {"name": "WORD SEARCH BINGO", "cost": 25, "color": (40, 180, 90)},
    4: {"name": "TREASURE HUNT", "cost": 50, "color": (160, 50, 210)},
    5: {"name": "GOLDEN JACKPOT", "cost": 100, "color": (230, 170, 30)},
}

# ==========================================
# PROCEDURAL SOUND ENGINE
# ==========================================
class SoundSynth:
    @staticmethod
    def create_sound(samples, sample_rate=22050):
        buf = bytearray()
        for sample in samples:
            val = max(-32768, min(32767, int(sample * 32767)))
            buf.extend(struct.pack("<h", val))
        return pygame.mixer.Sound(buffer=bytes(buf))

    @classmethod
    def gen_scratch(cls):
        sr = 22050
        duration = 0.08
        n_samples = int(sr * duration)
        samples = [(random.random() * 2.0 - 1.0) * (1.0 - (i / n_samples)) * 0.3 for i in range(n_samples)]
        return cls.create_sound(samples, sr)

    @classmethod
    def gen_coin(cls):
        sr = 22050
        duration = 0.25
        n_samples = int(sr * duration)
        freq1, freq2 = 987.77, 1318.51
        samples = []
        for i in range(n_samples):
            t = i / sr
            f = freq1 if t < 0.1 else freq2
            amp = max(0.0, 1.0 - (t / duration))
            samples.append(math.sin(2 * math.pi * f * t) * amp * 0.4)
        return cls.create_sound(samples, sr)

    @classmethod
    def gen_win(cls):
        sr = 22050
        duration = 0.5
        n_samples = int(sr * duration)
        notes = [523.25, 659.25, 783.99, 1046.50]
        samples = []
        for i in range(n_samples):
            t = i / sr
            note_idx = min(int(t / 0.125), len(notes) - 1)
            f = notes[note_idx]
            amp = max(0.0, 1.0 - ((t % 0.125) / 0.125))
            samples.append(math.sin(2 * math.pi * f * t) * amp * 0.3)
        return cls.create_sound(samples, sr)

# ==========================================
# PAYLOAD GENERATOR (REBALANCED MATH)
# ==========================================
class TicketPayloadGenerator:
    WORD_LIST = ["CASINO", "LUCKY", "BONUS", "CHIPS", "WINNER", "SEVEN", "JACKPOT", "GOLD", "STACKS", "COIN"]

    @classmethod
    def generate_payload(cls, tier, wager):
        # 1. Base Hit Rate reduced to 25% for healthy house edge
        win_chance = secrets.randbelow(100)
        is_winner = win_chance < 25

        multiplier = 0
        if is_winner:
            # 2. Multiplier distribution with 1x (Break-Even) tier
            mult_roll = secrets.randbelow(100)
            if mult_roll < 50:
                multiplier = 1     # 50% chance: Money back (1x)
            elif mult_roll < 80:
                multiplier = 2     # 30% chance: 2x
            elif mult_roll < 93:
                multiplier = 3     # 13% chance: 3x
            elif mult_roll < 98:
                multiplier = 5     # 5% chance:  5x
            else:
                multiplier = 10    # 2% chance:  10x Jackpot

        target_payout = wager * multiplier if is_winner else 0

        payload = {
            "tier": tier,
            "wager": wager,
            "is_winner": is_winner,
            "multiplier": multiplier,
            "payout": target_payout,
            "grid": [],
            "target_words": [],
            "caller_letters": []
        }

        if tier == 3:
            # Word Match Tier normalized to payload target_payout
            target_words = random.sample(cls.WORD_LIST, 3)
            payload["target_words"] = target_words
            
            letters_needed = set("".join(target_words))
            caller_letters = set()

            if is_winner:
                # Guaranteed letters for target_words based on multiplier
                if multiplier >= 5:
                    completed_words = target_words[:2]
                else:
                    completed_words = target_words[:1]
                
                for word in completed_words:
                    for char in word:
                        caller_letters.add(char)

            # Fill remaining caller letters safely without completing non-winning words
            all_letters = [chr(c) for c in range(65, 91)]
            random.shuffle(all_letters)
            
            for letter in all_letters:
                if len(caller_letters) >= 12:
                    break
                # Check if adding letter accidentally completes an unearned word
                temp_set = caller_letters | {letter}
                valid = True
                if not is_winner:
                    for tw in target_words:
                        if all(c in temp_set for c in tw):
                            valid = False
                            break
                if valid:
                    caller_letters.add(letter)

            payload["caller_letters"] = list(caller_letters)
        else:
            # Grid-based matching (3x3 grid)
            base_val = wager // 2
            vals = [base_val, wager, wager * 2, wager * 5, wager * 10]
            
            if is_winner:
                winning_val = target_payout if target_payout in vals else wager
                grid_vals = [winning_val] * 3
                while len(grid_vals) < 9:
                    v = random.choice(vals)
                    if grid_vals.count(v) < 2:
                        grid_vals.append(v)
            else:
                grid_vals = []
                while len(grid_vals) < 9:
                    v = random.choice(vals)
                    if grid_vals.count(v) < 2:
                        grid_vals.append(v)

            random.shuffle(grid_vals)
            payload["grid"] = grid_vals

        return payload

# ==========================================
# RENDERERS & CANVAS MECHANICS
# ==========================================
class TicketRenderer:
    @staticmethod
    def render_ticket(payload, width, height, font_main, font_small):
        surface = pygame.Surface((width, height))
        cfg = TIER_CONFIGS[payload["tier"]]
        
        surface.fill((240, 235, 220))
        pygame.draw.rect(surface, cfg["color"], (0, 0, width, 45))
        pygame.draw.rect(surface, COLOR_GOLD, (0, 0, width, height), 4)

        title = font_main.render(cfg["name"], True, COLOR_WHITE)
        surface.blit(title, title.get_rect(center=(width // 2, 22)))

        info = font_small.render(f"COST: ${payload['wager']}  |  MAX WIN: ${payload['wager'] * 10}", True, COLOR_BLACK)
        surface.blit(info, info.get_rect(center=(width // 2, 65)))

        # Sub-render content
        if payload["tier"] == 3:
            # Render Word Match Layout
            words_str = "  ".join(payload["target_words"])
            tw_txt = font_small.render(f"TARGETS: {words_str}", True, COLOR_BLACK)
            surface.blit(tw_txt, tw_txt.get_rect(center=(width // 2, 110)))

            callers = " ".join(payload["caller_letters"])
            cl_txt = font_main.render(f"CALLERS: {callers[:18]}", True, cfg["color"])
            surface.blit(cl_txt, cl_txt.get_rect(center=(width // 2, 160)))
            if len(callers) > 18:
                cl_txt2 = font_main.render(callers[18:], True, cfg["color"])
                surface.blit(cl_txt2, cl_txt2.get_rect(center=(width // 2, 195)))
        else:
            # Render Grid Layout
            grid = payload["grid"]
            for i in range(9):
                row, col = i // 3, i % 3
                x = 40 + col * 100
                y = 90 + row * 55
                pygame.draw.rect(surface, COLOR_WHITE, (x, y, 90, 48), border_radius=6)
                pygame.draw.rect(surface, COLOR_SILVER, (x, y, 90, 48), 2, border_radius=6)
                
                txt = font_main.render(f"${grid[i]}", True, COLOR_BLACK)
                surface.blit(txt, txt.get_rect(center=(x + 45, y + 24)))

        return surface

class ScratchCanvas:
    def __init__(self, width, height, font):
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.reset()
        self.font = font
        self.scratched_pixels = 0
        self.total_pixels = width * height

    def reset(self):
        self.surface.fill((160, 165, 175, 255))
        # Draw metallic foil texture grid lines
        for x in range(0, self.width, 20):
            pygame.draw.line(self.surface, (140, 145, 155, 255), (x, 0), (x, self.height), 2)
        for y in range(0, self.height, 20):
            pygame.draw.line(self.surface, (140, 145, 155, 255), (0, y), (self.width, y), 2)

    def scratch(self, pos, radius=22):
        x, y = pos
        pygame.draw.circle(self.surface, (0, 0, 0, 0), (x, y), radius)

    def get_scratched_ratio(self):
        # Sample alpha channel on 10x10 grid for performance
        transparent_count = 0
        samples = 0
        for x in range(10, self.width, 25):
            for y in range(10, self.height, 25):
                samples += 1
                if self.surface.get_at((x, y))[3] == 0:
                    transparent_count += 1
        return transparent_count / max(1, samples)

    def reveal_all(self):
        self.surface.fill((0, 0, 0, 0))

# ==========================================
# VENDING CABINET & ENGINE
# ==========================================
class VendingMachineCabinet:
    def __init__(self):
        self.credits = 100
        self.selected_tier = 1

    def draw(self, surface, font_large, font_small):
        # Cabinet outer frame
        pygame.draw.rect(surface, COLOR_CABINET, (20, 20, 300, 660), border_radius=12)
        pygame.draw.rect(surface, COLOR_CABINET_BORDER, (20, 20, 300, 660), 4, border_radius=12)

        # Credit Display Screen
        pygame.draw.rect(surface, COLOR_BLACK, (40, 40, 260, 60), border_radius=6)
        pygame.draw.rect(surface, COLOR_GOLD, (40, 40, 260, 60), 2, border_radius=6)
        
        cred_txt = font_large.render(f"CREDITS: ${self.credits}", True, COLOR_GOLD)
        surface.blit(cred_txt, cred_txt.get_rect(center=(170, 70)))

        # Tier Selection Buttons
        for tier, data in TIER_CONFIGS.items():
            y = 120 + (tier - 1) * 95
            is_sel = self.selected_tier == tier
            
            btn_color = data["color"] if is_sel else (50, 55, 70)
            border_c = COLOR_GOLD if is_sel else COLOR_SILVER
            
            pygame.draw.rect(surface, btn_color, (40, y, 260, 80), border_radius=8)
            pygame.draw.rect(surface, border_c, (40, y, 260, 80), 3 if is_sel else 1, border_radius=8)

            t_name = font_small.render(data["name"], True, COLOR_WHITE)
            t_cost = font_large.render(f"${data['cost']}", True, COLOR_GOLD if not is_sel else COLOR_WHITE)
            
            surface.blit(t_name, (52, y + 15))
            surface.blit(t_cost, (52, y + 40))

# ==========================================
# MAIN GAME LOOP
# ==========================================
async def main():
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=1)
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Casino Scratch-Off Terminal")
    clock = pygame.time.Clock()

    # Fonts
    font_large = pygame.font.SysFont("arial", 22, bold=True)
    font_main = pygame.font.SysFont("arial", 18, bold=True)
    font_small = pygame.font.SysFont("arial", 14, bold=True)

    # Audio Effects
    sfx_scratch = SoundSynth.gen_scratch()
    sfx_coin = SoundSynth.gen_coin()
    sfx_win = SoundSynth.gen_win()

    cabinet = VendingMachineCabinet()
    state = STATE_VENDING
    
    active_payload = None
    ticket_surface = None
    scratch_canvas = None
    dispense_y = -300
    payout_processed = False

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == STATE_VENDING:
                    # Select Tiers
                    for tier in TIER_CONFIGS:
                        y = 120 + (tier - 1) * 95
                        if 40 <= mouse_pos[0] <= 300 and y <= mouse_pos[1] <= y + 80:
                            cabinet.selected_tier = tier
                            sfx_coin.play()
                            break
                    
                    # Buy Ticket Button Slot
                    cost = TIER_CONFIGS[cabinet.selected_tier]["cost"]
                    if cabinet.credits >= cost:
                        # Dispense sequence init
                        cabinet.credits -= cost
                        active_payload = TicketPayloadGenerator.generate_payload(cabinet.selected_tier, cost)
                        ticket_surface = TicketRenderer.render_ticket(active_payload, 450, 280, font_main, font_small)
                        scratch_canvas = ScratchCanvas(450, 280, font_small)
                        
                        dispense_y = -300
                        payout_processed = False
                        state = STATE_DISPENSING
                        sfx_coin.play()

        # Update Mechanics
        if state == STATE_DISPENSING:
            dispense_y += 600 * dt
            if dispense_y >= 200:
                dispense_y = 200
                state = STATE_SCRATCHING

        elif state == STATE_SCRATCHING:
            ticket_rect = pygame.Rect(380, int(dispense_y), 450, 280)
            if mouse_pressed and ticket_rect.collidepoint(mouse_pos):
                local_x = mouse_pos[0] - ticket_rect.x
                local_y = mouse_pos[1] - ticket_rect.y
                scratch_canvas.scratch((local_x, local_y))
                if random.random() < 0.3:
                    sfx_scratch.play()

            # Auto Reveal & Payout processing
            if scratch_canvas.get_scratched_ratio() > 0.65:
                scratch_canvas.reveal_all()

            if scratch_canvas.get_scratched_ratio() > 0.85 and not payout_processed:
                payout_processed = True
                payout = active_payload["payout"]
                if payout > 0:
                    cabinet.credits += payout
                    sfx_win.play()

        # Render Core Stage
        screen.fill(COLOR_BG)
        cabinet.draw(screen, font_large, font_small)

        # Render Active Ticket & Scratch Layer
        if state in (STATE_DISPENSING, STATE_SCRATCHING):
            t_x, t_y = 380, int(dispense_y)
            screen.blit(ticket_surface, (t_x, t_y))
            screen.blit(scratch_canvas.surface, (t_x, t_y))

            # Display Status Banner
            if payout_processed:
                win_amt = active_payload["payout"]
                res_txt = f"WINNER! +${win_amt}" if win_amt > 0 else "TRY AGAIN!"
                color = COLOR_GREEN if win_amt > 0 else COLOR_RED
                lbl = font_large.render(res_txt, True, color)
                screen.blit(lbl, lbl.get_rect(center=(605, 520)))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
