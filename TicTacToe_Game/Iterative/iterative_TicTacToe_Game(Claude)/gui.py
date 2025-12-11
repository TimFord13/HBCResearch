"""
================================================================================
TIC-TAC-TOE GUI
================================================================================

Tkinter-based graphical user interface for Tic-Tac-Toe game.

This module provides:
    - TicTacToeGUI class: Complete GUI with menu bar, board, and scoreboard
    - Game mode support: Human vs Human, Human vs AI, AI vs AI
    - Score tracking across multiple games
    - Visual feedback: color-coded marks, winning line highlighting
    - Responsive UI: non-blocking AI moves using tkinter's after()

Features:
    ✓ 3x3 clickable button grid
    ✓ Menu bar (Game: New, Reset Scores, Quit | Mode: 4 modes)
    ✓ Scoreboard showing X wins, O wins, and ties
    ✓ Status display for current player and mode
    ✓ Winning line highlighted in yellow
    ✓ AI moves with 300ms delay for visibility

Usage:
    from gui import main
    main()  # Launches the GUI

Integration:
    Imports TicTacToe and best_move from engine.py
    All game logic is handled by the engine module
    GUI is purely a display and interaction layer

================================================================================
"""

import tkinter as tk
from tkinter import messagebox
from engine import TicTacToe, best_move


class TicTacToeGUI:
    """GUI for Tic-Tac-Toe game."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Tic-Tac-Toe")
        self.root.resizable(False, False)
        
        # Initialize game engine
        self.game = TicTacToe()
        
        # Game mode: 'HvH', 'HvAI', 'AIvAI'
        self.mode = 'HvH'
        
        # Player choice in HvAI mode ('X' or 'O')
        self.human_player = 'X'
        
        # Score tracking
        self.scores = {'X': 0, 'O': 0, 'Tie': 0}
        
        # AI processing flag
        self.ai_thinking = False
        
        # Create GUI elements
        self.create_menu_bar()
        self.create_scoreboard()
        self.create_board()
        self.create_status_label()
        self.create_reset_button()
        
        self.update_display()
    
    def create_menu_bar(self):
        """Create menu bar with Game and Mode options."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Game menu
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="New", command=self.new_game)
        game_menu.add_command(label="Reset Scores", command=self.reset_scores)
        game_menu.add_separator()
        game_menu.add_command(label="Quit", command=self.root.quit)
        
        # Mode menu
        mode_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Mode", menu=mode_menu)
        mode_menu.add_command(label="Human vs Human", command=lambda: self.set_mode('HvH'))
        mode_menu.add_command(label="Human (X) vs AI (O)", command=lambda: self.set_mode('HvAI', 'X'))
        mode_menu.add_command(label="Human (O) vs AI (X)", command=lambda: self.set_mode('HvAI', 'O'))
        mode_menu.add_command(label="AI vs AI", command=lambda: self.set_mode('AIvAI'))
    
    def create_scoreboard(self):
        """Create scoreboard to display wins and ties."""
        scoreboard_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2)
        scoreboard_frame.pack(padx=10, pady=10, fill=tk.X)
        
        tk.Label(
            scoreboard_frame,
            text="SCOREBOARD",
            font=("Arial", 12, "bold")
        ).pack()
        
        self.score_label = tk.Label(
            scoreboard_frame,
            text="",
            font=("Arial", 11),
            pady=5
        )
        self.score_label.pack()
        
        self.update_scoreboard()
    
    def create_board(self):
        """Create the 3x3 grid of buttons."""
        board_frame = tk.Frame(self.root)
        board_frame.pack(padx=10, pady=10)
        
        self.buttons = []
        for row in range(3):
            button_row = []
            for col in range(3):
                button = tk.Button(
                    board_frame,
                    text="",
                    font=("Arial", 32, "bold"),
                    width=5,
                    height=2,
                    command=lambda r=row, c=col: self.on_cell_click(r, c)
                )
                button.grid(row=row, column=col, padx=2, pady=2)
                button_row.append(button)
            self.buttons.append(button_row)
    
    def create_status_label(self):
        """Create status label to show current player and game state."""
        self.status_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 14),
            pady=10
        )
        self.status_label.pack()
    
    def create_reset_button(self):
        """Create reset button."""
        self.reset_button = tk.Button(
            self.root,
            text="New Game",
            font=("Arial", 12),
            command=self.new_game,
            padx=20,
            pady=5
        )
        self.reset_button.pack(pady=10)
    
    def on_cell_click(self, row, col):
        """Handle cell button click."""
        # Don't allow clicks while AI is thinking
        if self.ai_thinking:
            return
        
        # In AI vs AI mode, don't allow human clicks
        if self.mode == 'AIvAI':
            return
        
        # In Human vs AI mode, only allow clicks on human's turn
        if self.mode == 'HvAI' and self.game.current_player != self.human_player:
            return
        
        # Try to make move
        if self.game.make_move(row, col):
            self.update_display()
            
            # Check if game is over
            if self.game.is_game_over:
                self.highlight_winning_line()
                self.handle_game_over()
            else:
                # If Human vs AI mode and AI's turn, make AI move
                if self.mode == 'HvAI' and self.game.current_player != self.human_player:
                    self.ai_thinking = True
                    self.root.after(300, self.make_ai_move)
    
    def make_ai_move(self):
        """Make AI move."""
        if not self.game.is_game_over:
            move = best_move(self.game.get_board(), self.game.current_player)
            if move:
                self.game.make_move(move[0], move[1])
                self.update_display()
                
                if self.game.is_game_over:
                    self.highlight_winning_line()
                    self.handle_game_over()
        
        self.ai_thinking = False
    
    def run_ai_vs_ai_game(self):
        """Run one move in AI vs AI mode."""
        if not self.game.is_game_over:
            move = best_move(self.game.get_board(), self.game.current_player)
            if move:
                self.game.make_move(move[0], move[1])
                self.update_display()
                
                if self.game.is_game_over:
                    self.highlight_winning_line()
                    self.handle_game_over()
                else:
                    # Schedule next move (300ms delay as specified)
                    self.root.after(300, self.run_ai_vs_ai_game)
    
    def update_display(self):
        """Update button text and status label."""
        # Update button text
        board = self.game.get_board()
        for row in range(3):
            for col in range(3):
                cell_value = board[row][col]
                if cell_value:
                    self.buttons[row][col].config(text=cell_value, bg="SystemButtonFace")
                    # Color coding
                    if cell_value == 'X':
                        self.buttons[row][col].config(fg="blue")
                    else:
                        self.buttons[row][col].config(fg="red")
                else:
                    self.buttons[row][col].config(text="", bg="SystemButtonFace")
        
        # Update status label
        if self.game.is_game_over:
            if self.game.winner:
                self.status_label.config(
                    text=f"Game Over! {self.game.winner} Wins!",
                    fg="green"
                )
            else:
                self.status_label.config(
                    text="Game Over! It's a Tie!",
                    fg="orange"
                )
        else:
            mode_text = ""
            if self.mode == 'HvH':
                mode_text = " (Human vs Human)"
            elif self.mode == 'HvAI':
                if self.game.current_player == self.human_player:
                    mode_text = " (Human)"
                else:
                    mode_text = " (AI)"
            else:
                mode_text = " (AI vs AI)"
            
            self.status_label.config(
                text=f"Current Player: {self.game.current_player}{mode_text}",
                fg="black"
            )
    
    def highlight_winning_line(self):
        """Highlight the winning line on the board."""
        if not self.game.winner:
            return
        
        board = self.game.get_board()
        winning_player = self.game.winner
        
        # Check rows
        for row in range(3):
            if all(board[row][col] == winning_player for col in range(3)):
                for col in range(3):
                    self.buttons[row][col].config(bg="yellow")
                return
        
        # Check columns
        for col in range(3):
            if all(board[row][col] == winning_player for row in range(3)):
                for row in range(3):
                    self.buttons[row][col].config(bg="yellow")
                return
        
        # Check diagonal (top-left to bottom-right)
        if all(board[i][i] == winning_player for i in range(3)):
            for i in range(3):
                self.buttons[i][i].config(bg="yellow")
            return
        
        # Check diagonal (top-right to bottom-left)
        if all(board[i][2-i] == winning_player for i in range(3)):
            for i in range(3):
                self.buttons[i][2-i].config(bg="yellow")
            return
    
    def update_scoreboard(self):
        """Update scoreboard display."""
        score_text = f"X Wins: {self.scores['X']}  |  O Wins: {self.scores['O']}  |  Ties: {self.scores['Tie']}"
        self.score_label.config(text=score_text)
    
    def handle_game_over(self):
        """Handle game over - update scores and show message."""
        # Update scores
        if self.game.winner:
            self.scores[self.game.winner] += 1
        else:
            self.scores['Tie'] += 1
        
        self.update_scoreboard()
        self.show_game_over_message()
    
    def show_game_over_message(self):
        """Show game over message box."""
        if self.game.winner:
            message = f"Player {self.game.winner} wins!"
        else:
            message = "It's a tie!"
        
        messagebox.showinfo("Game Over", message)
    
    def new_game(self):
        """Start a new game (reset current game)."""
        self.game.reset()
        self.ai_thinking = False
        self.update_display()
        
        # If AI vs AI mode, start the game
        if self.mode == 'AIvAI':
            self.root.after(300, self.run_ai_vs_ai_game)
        # If Human vs AI and AI goes first
        elif self.mode == 'HvAI' and self.human_player == 'O':
            self.ai_thinking = True
            self.root.after(300, self.make_ai_move)
    
    def reset_scores(self):
        """Reset all scores to zero."""
        self.scores = {'X': 0, 'O': 0, 'Tie': 0}
        self.update_scoreboard()
        messagebox.showinfo("Scores Reset", "All scores have been reset to 0")
    
    def set_mode(self, mode, human_player='X'):
        """Set game mode and start new game."""
        self.mode = mode
        self.human_player = human_player
        self.new_game()
        
        mode_names = {
            'HvH': 'Human vs Human',
            'HvAI': f'Human ({human_player}) vs AI ({("O" if human_player == "X" else "X")})',
            'AIvAI': 'AI vs AI'
        }
        messagebox.showinfo("Mode Changed", f"Mode set to: {mode_names[mode]}")


def main():
    """Run the GUI application."""
    root = tk.Tk()
    app = TicTacToeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()