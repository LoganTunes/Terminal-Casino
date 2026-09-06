# The Terminal Casino

All eight of your Pygame table games combined into one app with a single,
shared chip balance.

## Setup

You need Python 3 and Pygame installed locally:

```
pip install pygame
```

## Run it

```
python casino.py
```

## How it works

- `casino.py` is the lobby / launcher. It shows a menu of all 8 games and
  your current bankroll.
- Click any game card to play it. Your original game code runs completely
  unchanged in terms of rules, math, art, and sound.
- Press **ESC** at any point inside a game to cash out back to the lobby.
  Your balance carries over automatically.
- Your bankroll is saved to `chips_save.json` (created next to `casino.py`)
  so it persists between sessions. Use the **RESET BANKROLL** button in the
  lobby to start over with a fresh $1000 if you go broke.
- Each game still opens at its own original window size (they don't all
  match), so the window will resize when you enter/exit a game — that's
  expected.

## Folder structure

```
casino.py              <- run this
games/
  blackjack.py
  craps.py
  keno.py
  mechanical_derby.py
  roulette.py
  slots.py
  ultimate_hold_em.py
  video_poker.py
```

Each file in `games/` is your original script, refactored so that:
- `balance` is now a function parameter/return value instead of a bare
  global, so it can be shared across games.
- The infinite `while True:` game loop became `while running:`, with ESC
  now setting `running = False` to exit back to the lobby.
- A small "ESC: Return to Lobby" hint is drawn in the corner during play.

Nothing about the actual game logic, odds, payouts, art, or sound was
changed.
