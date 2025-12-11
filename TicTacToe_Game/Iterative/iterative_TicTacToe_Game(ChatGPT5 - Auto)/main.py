"""
main.py — Tic-Tac-Toe (Tkinter + perfect AI)

ChatGPT-5 converstaion link: https://chatgpt.com/share/6929e7fe-d57c-800e-9e83-7cd8e2717fb1

How to run
----------
    python main.py
Requires only the Python standard library (tkinter). No third-party packages.

Available modes & controls
--------------------------
Menu → Game
  • New: start a fresh round (keeps the scoreboard)
  • Reset Scores: clear X/O/Ties tallies
  • Quit: exit the app

Menu → Mode
  • Human vs Human
  • Human (X) vs AI (O)
  • Human (O) vs AI (X)
  • AI vs AI

In-window controls
  • 3×3 grid of buttons for moves
  • Status bar shows the current side, AI thinking state, and results
  • Winning line is highlighted when a game ends

AI determinism & tie-breaking
-----------------------------
The AI uses Minimax with alpha-beta pruning and terminal-state scoring only:
  +1 (win), 0 (tie), −1 (loss), evaluated from the perspective of the side to move.
Move ordering is row-major (top-left to bottom-right), which provides deterministic
tie-breaking. Given a fixed position, the AI will always choose the same move.

File structure
--------------
  • engine.py
      - Core game logic (board state, legal moves, win/tie detection)
      - Perfect AI utilities: best_move(board, player)
      - Built-in self-tests (run `python engine.py` to see PASS/FAIL)
  • gui.py
      - Tkinter UI, menu, scoreboard, modes, AI integration, visual polish
      - Non-blocking AI turns using `after(...)` with a short delay (watchable)
  • main.py (this file)
      - Entry point that launches the GUI

Known limitations
-----------------
  • Board size fixed at 3×3.
  • No move history/undo.
  • Single-threaded UI; long-running work would need backgrounding, but the AI here
    is tiny and runs instantly. Turn cadence is intentionally paced via `after(...)`.
  • Appearance varies slightly by OS/theme due to native Tk styling.

Acceptance checklist (met)
--------------------------
  ✓ Runs with standard library only
  ✓ Human vs Human, Human vs AI (choose side), AI vs AI
  ✓ Prevents illegal/post-game moves and disables clicks during AI turns
  ✓ Deterministic, perfect AI that never loses and always blocks
  ✓ Status updates every move; AI turns are visually paced; UI stays responsive
  ✓ Winning line highlight; scoreboard persists across rounds until reset

Quick smoke tests
-----------------
  1) Start in Human vs Human. Play a quick X win; verify highlight and X score +1.
  2) Switch to Human (O) vs AI (X). AI should move first automatically.
  3) Switch to AI vs AI. Board should fill with ~300 ms cadence until tie or win.
  4) Game → New resets the board but keeps scores. Game → Reset Scores zeros them.
"""

import tkinter as tk
from gui import TicTacToeGUI


def main() -> None:
    root = tk.Tk()
    TicTacToeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
