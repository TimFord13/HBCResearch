"""
TIC-TAC-TOE (UNBEATABLE AI)
===========================

Gemini chat link: https://gemini.google.com/share/b5b1a63f1fd1

How to Run:
-----------
1. Ensure 'engine.py', 'gui.py', and 'main.py' are in the same directory.
2. Run the command:
   $ python main.py

Modes & Controls:
-----------------
* Game Menu:
  - New Game: Resets the board (keeps scores).
  - Reset Scores: Resets the scoreboard (keeps game state).
  - Quit: Exits the application.

* Mode Menu:
  - Human vs. Human: Traditional hot-seat multiplayer.
  - Human vs. AI: Play against the engine.
    - Side Selection: Choose to play as X (First) or O (Second) via the 'Side' menu.
  - AI vs. AI: Watch the computer play against itself (Always results in a Tie).

* Gameplay:
  - Click any empty cell to make a move.
  - Winning lines are highlighted in green.
  - Visual status updates occur at the bottom of the window.

AI Behavior (Determinism):
--------------------------
The AI uses the Minimax algorithm with Alpha-Beta pruning.
- Scoring: +1 (Win), -1 (Loss), 0 (Tie).
- Tie-Breaking: The AI is deterministic. If multiple moves have the same 
  optimal score, it selects the first one found scanning from Top-Left (0,0) 
  to Bottom-Right (2,2).
- Recursion: Searches the full game tree depth-first.

File Structure:
---------------
1. engine.py: Core logic, board state, validation, and Minimax AI.
2. gui.py:    Tkinter visualization, event handling, and window management.
3. main.py:   Entry point and documentation.

Limitations:
------------
- The window size is locked to preserve the aspect ratio.
- The AI has no difficulty setting; it is always perfect.
- The AI move is calculated on the main thread (blocking), though 
  imperceptible for the 3x3 search space.
"""

import tkinter as tk
from gui import TicTacToeGUI

def main():
    """Initializes the Tkinter root and starts the application."""
    root = tk.Tk()
    
    # Instantiate the GUI logic
    app = TicTacToeGUI(root)
    
    # Start the event loop
    root.mainloop()

if __name__ == "__main__":
    main()