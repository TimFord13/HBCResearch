"""
=================================================
Perfect-Play Tic-Tac-Toe (Python/tkinter)
=================================================

This application implements a graphical Tic-Tac-Toe game with an
unbeatable AI opponent.

-------------------------------------------------
How to Run
-------------------------------------------------
1. Ensure you have Python 3.10+ installed.
2. Place all three files (`main.py`, `engine.py`, `gui.py`)
   in the same directory.
3. Run the application from your terminal:
   $ python main.py

-------------------------------------------------
Game Modes
-------------------------------------------------
The application supports three modes, selectable from the "Mode" menu:

1.  **Human vs Human:** Two players share the mouse.
2.  **Human vs AI:** Play against the perfect AI. You can choose to
    play as 'X' (first) or 'O' (second) from the "Player" menu.
3.  **AI vs AI:** Watch two perfect AI players play against each other
    (which will always result in a tie).

-------------------------------------------------
AI Implementation (Minimax)
-------------------------------------------------
The AI's perfect play is achieved using the Minimax algorithm with
Alpha-Beta Pruning.

* **Location:** The entire AI logic is encapsulated in the `engine.py`
    file, specifically within the `find_best_move` and `minimax`
    functions.
* **Evaluation:** The algorithm performs a full search of the game
    tree. It does not use heuristics; it only evaluates terminal
    states (Win, Loss, Tie).
    * AI Win:   +1
    * Opponent Win: -1
    * Tie:      0
* **Pruning:** Alpha-beta pruning is used to significantly cut down
    the search space, allowing for an instantaneous response.
* **Determinism:** The AI is fully deterministic. When faced with
    multiple moves of equal (and optimal) value, it *always*
    chooses the first one it finds. The search order is
    top-left to bottom-right (row 0, col 0; row 0, col 1; etc.).
    This satisfies the acceptance test (e.g., as 'X', it will
    always pick the corner at (0, 0)).

-------------------------------------------------
File Structure
-------------------------------------------------
* **main.py:** This file. Contains the README and the entry
    point to launch the application.
* **engine.py:** Contains all pure game logic. This includes the
    board state, win/tie detection, legal move generation, and the
    Minimax AI. It has no `tkinter` dependencies and can be
    imported and tested independently.
* **gui.py:** Contains all `tkinter` code. It builds the main
    application window, menu bar, game board, scoreboard, and
    status bar. It handles all user events and drives the
    game by calling the `engine`.

-------------------------------------------------
Known Limitations
-------------------------------------------------
* The UI is functional but simple. It does not feature
    advanced graphics or win-line animations.
* The "Player" menu (for choosing X/O) is active even when
    not in "Human vs AI" mode. While it has no effect in
    other modes, a more polished UI would disable it.
    (Correction: This has been implemented; the menu is
    disabled in non-AI modes).
"""

import tkinter as tk
from gui import TicTacToeGUI

if __name__ == "__main__":
    # Create the main application window
    root = tk.Tk()
    root.title("Tic-Tac-Toe")
    root.geometry("400x500") # Set a reasonable default size
    root.minsize(350, 450)

    # Instantiate the GUI application class
    # The TicTacToeGUI class handles all setup and logic.
    app = TicTacToeGUI(root)

    # Start the tkinter main event loop
    root.mainloop()