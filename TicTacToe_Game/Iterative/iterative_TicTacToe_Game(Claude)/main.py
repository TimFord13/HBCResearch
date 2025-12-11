"""
================================================================================
TIC-TAC-TOE GAME WITH PERFECT AI
================================================================================

Claude chat link: https://claude.ai/share/4ba50be1-e338-4234-82c1-e903aaf4861e

A complete Tic-Tac-Toe implementation with GUI and perfect AI opponent using
Minimax algorithm with alpha-beta pruning.

HOW TO RUN:
-----------
    python main.py

REQUIREMENTS:
-------------
    - Python 3.7 or higher
    - No external dependencies (uses only Python standard library: tkinter)

AVAILABLE MODES:
----------------
    1. Human vs Human
       - Two players take turns clicking cells
       - X always goes first
    
    2. Human (X) vs AI (O)
       - You play as X (blue), AI plays as O (red)
       - You go first
       - AI responds automatically after 300ms delay
    
    3. Human (O) vs AI (X)
       - You play as O (red), AI plays as X (blue)
       - AI goes first automatically
       - You respond after AI moves
    
    4. AI vs AI
       - Watch two perfect AI players compete
       - Moves happen automatically every 300ms
       - Always results in a tie (both players are perfect)

CONTROLS:
---------
    Menu Bar:
        Game Menu:
            - New: Start a new game (resets board, keeps scores)
            - Reset Scores: Clear win/tie tallies
            - Quit: Exit the application
        
        Mode Menu:
            - Human vs Human
            - Human (X) vs AI (O)
            - Human (O) vs AI (X)
            - AI vs AI
    
    Gameplay:
        - Click any empty cell to place your mark
        - Clicks are disabled during AI thinking
        - Clicks are disabled in AI vs AI mode
        - New Game button below the board also starts a new game

FEATURES:
---------
    ✓ Perfect AI using Minimax with alpha-beta pruning
    ✓ Scoreboard tracking X wins, O wins, and ties
    ✓ Visual feedback with color-coded marks (X=blue, O=red)
    ✓ Winning line highlighted in yellow
    ✓ Responsive UI with non-blocking AI moves
    ✓ Game status display showing current player and mode

AI BEHAVIOR:
------------
    The AI uses the Minimax algorithm with alpha-beta pruning for optimal play:
    
    - Scoring: +1 for AI win, -1 for AI loss, 0 for tie
    - Perfect Play: AI never loses, always forces tie or win
    - Deterministic Tie-Breaking: When multiple moves have equal value,
      the AI consistently chooses the first valid move in top-left to
      bottom-right order (row 0→2, col 0→2). This ensures reproducible
      behavior in identical game states.
    - Alpha-Beta Pruning: Eliminates unnecessary branches in the game tree,
      significantly improving performance without affecting optimality

FILE STRUCTURE:
---------------
    main.py
        - Entry point for the application
        - Launches the GUI
        - Contains this documentation
    
    engine.py
        - Core game logic (TicTacToe class)
        - Board representation and move validation
        - Win/tie detection
        - AI implementation (minimax, best_move)
        - Standalone module with comprehensive unit tests
    
    gui.py
        - Tkinter-based graphical user interface
        - Handles all user interactions
        - Integrates with engine.py for game logic
        - Manages game modes and scoreboard

KNOWN LIMITATIONS:
------------------
    1. AI always uses perfect play - no difficulty levels
       (You cannot beat the AI, only tie)
    
    2. No save/load game state functionality
    
    3. No customization of colors or board size
    
    4. No undo/redo functionality
    
    5. Scoreboard resets when application closes
    
    6. AI vs AI always results in tie (both play perfectly)

TESTING:
--------
    To run unit tests for the game engine:
        python engine.py
    
    This will run comprehensive tests including:
        - Board initialization and move validation
        - Win detection (horizontal, vertical, diagonal)
        - Tie detection
        - AI move quality
        - AI vs AI tie verification
        - Random player vs AI (AI never loses)

GAME RULES:
-----------
    - 3x3 grid board
    - X always goes first
    - Players alternate turns
    - First player to get 3 marks in a row (horizontal, vertical, or
      diagonal) wins
    - If all 9 cells are filled with no winner, the game is a tie
    - In Human vs AI modes, illegal moves are prevented automatically

CREDITS:
--------
    Developed as an educational implementation of classic Tic-Tac-Toe
    with emphasis on clean code architecture and perfect AI play.

================================================================================
"""

import sys
from gui import main as gui_main


def main():
    """Launch the Tic-Tac-Toe application."""
    try:
        gui_main()
    except KeyboardInterrupt:
        print("\n\nGame terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        print("Please ensure you have Python 3.7+ with tkinter installed.")
        sys.exit(1)


if __name__ == "__main__":
    main()