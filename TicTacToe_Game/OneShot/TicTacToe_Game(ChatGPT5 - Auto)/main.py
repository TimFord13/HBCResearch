# main.py
"""
README — Perfect-Play Tic-Tac-Toe (tkinter)
===========================================

How to run
----------
Python 3.10+ required. No third-party packages.
Run from a terminal:

    python main.py

You should see a windowed app with a 3×3 board, a menu bar, a status bar, and a scoreboard.

Modes
-----
- Game → New: start a fresh round without closing the app. Scores persist.
- Game → Reset Scores: set X/O/Tie tallies to 0.
- Game → Quit: exit the app.
- Mode → Human vs Human: both players click on the board.
- Mode → Human vs AI: pick whether the human plays X or O. If you pick O, the AI makes the first move.
- Mode → AI vs AI: for demos and testing; it will always result in a tie.

Determinism policy
------------------
The AI uses minimax with alpha-beta pruning and has no randomness. When multiple moves are equally optimal,
the engine uses a stable row-major tie-break rule (top-left to bottom-right), guaranteeing deterministic play.

Implementation overview
-----------------------
- engine.py contains the pure game logic and search:
  - `legal_moves(board)`, `winner(board)`, `is_terminal(board)`
  - `best_move(board, player)` computes the perfect move using `minimax(...)` with alpha-beta pruning.
  - Terminal evaluation only: +1 win, -1 loss, 0 tie, from the root player's perspective.
  - Inline comments document recursion depth handling and pruning conditions.
- gui.py builds the tkinter interface:
  - Menu bar (Game: New, Reset Scores, Quit; Mode: H-H, H-A, A-A)
  - Status bar indicating current player, mode, and results
  - Scoreboard tracking X, O, and ties
  - Non-blocking UI: AI turns are scheduled via `root.after(...)` so the app stays responsive.
- main.py is the entry point and just launches the GUI.

Known limitations
-----------------
- No undo/redo (stretch goal).
- Very small codebase, so there’s no theme customizer or animation. You can add a winning-line highlight as a stretch.

Testing the engine headlessly
-----------------------------
You can import `engine.py` without a display. Example:

    >>> import engine
    >>> b = engine.new_board()
    >>> engine.best_move(b, "X")
    (0, 0)  # or (1,1) depending on row-major tie-breaking; both are optimal.

"""

from gui import launch

if __name__ == "__main__":
    launch()
