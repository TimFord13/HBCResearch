"""
Perfect-Play Tic-Tac-Toe with Minimax AI

HOW TO RUN:
    python main.py

MODES:
    - Human vs Human: Two players take turns
    - Human vs AI: Play against perfect AI (choose X or O)
    - AI vs AI: Watch two AIs play (always ties)

DETERMINISM:
    AI uses Minimax with alpha-beta pruning. No randomness.
    Tie-breaking: always picks top-left to bottom-right (row-major order).

IMPLEMENTATION:
    - Engine class: game logic, Minimax with alpha-beta pruning
    - TicTacToeGUI class: tkinter interface with menu bar
    - Perfect play guaranteed via exhaustive search with pruning

LIMITATIONS:
    - 3x3 board only (standard Tic-Tac-Toe)
    - X always moves first
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Optional, Tuple, List
from enum import Enum


class GameMode(Enum):
    """Game mode enumeration"""
    HUMAN_VS_HUMAN = "Human vs Human"
    HUMAN_VS_AI = "Human vs AI"
    AI_VS_AI = "AI vs AI"


class Engine:
    """
    Pure game logic engine with Minimax AI.
    Fully testable without GUI.
    """
    
    EMPTY = " "
    X = "X"
    O = "O"
    
    def __init__(self):
        """Initialize empty 3x3 board"""
        self.board: List[List[str]] = [[self.EMPTY] * 3 for _ in range(3)]
    
    def reset(self) -> None:
        """Clear the board"""
        self.board = [[self.EMPTY] * 3 for _ in range(3)]
    
    def make_move(self, row: int, col: int, player: str) -> bool:
        """
        Place a move if legal.
        Returns True if successful, False otherwise.
        """
        if not (0 <= row < 3 and 0 <= col < 3):
            return False
        if self.board[row][col] != self.EMPTY:
            return False
        self.board[row][col] = player
        return True
    
    def legal_moves(self) -> List[Tuple[int, int]]:
        """Return list of (row, col) for empty cells"""
        moves = []
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == self.EMPTY:
                    moves.append((r, c))
        return moves
    
    def is_terminal(self) -> bool:
        """Check if game is over (win or tie)"""
        return self.winner() is not None or len(self.legal_moves()) == 0
    
    def winner(self) -> Optional[str]:
        """
        Return winning player (X or O) or None.
        Checks rows, columns, and diagonals.
        """
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != self.EMPTY:
                return row[0]
        
        # Check columns
        for c in range(3):
            if self.board[0][c] == self.board[1][c] == self.board[2][c] != self.EMPTY:
                return self.board[0][c]
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != self.EMPTY:
            return self.board[1][1]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != self.EMPTY:
            return self.board[1][1]
        
        return None
    
    def best_move(self, player: str) -> Tuple[int, int]:
        """
        Find best move using Minimax with alpha-beta pruning.
        Returns (row, col) tuple.
        Deterministic: breaks ties by selecting top-left to bottom-right.
        """
        best_score = float('-inf')
        best_move_coords = None
        
        # Try moves in row-major order for deterministic tie-breaking
        for move in self.legal_moves():
            row, col = move
            # Simulate move
            self.board[row][col] = player
            # Minimax with alpha-beta
            score = self._minimax(False, player, float('-inf'), float('inf'))
            # Undo move
            self.board[row][col] = self.EMPTY
            
            # Update best move (first encountered due to row-major order)
            if score > best_score:
                best_score = score
                best_move_coords = move
        
        return best_move_coords
    
    def _minimax(self, is_maximizing: bool, ai_player: str, 
                 alpha: float, beta: float) -> float:
        """
        Minimax algorithm with alpha-beta pruning.
        
        Args:
            is_maximizing: True if maximizing player's turn
            ai_player: The AI player (X or O)
            alpha: Best score maximizer can guarantee
            beta: Best score minimizer can guarantee
        
        Returns:
            Best score for current player
        """
        # Terminal state evaluation
        winner = self.winner()
        if winner == ai_player:
            return 1  # AI wins
        elif winner is not None:
            return -1  # AI loses
        elif len(self.legal_moves()) == 0:
            return 0  # Tie
        
        opponent = self.O if ai_player == self.X else self.X
        
        if is_maximizing:
            # AI's turn: maximize score
            max_score = float('-inf')
            for row, col in self.legal_moves():
                self.board[row][col] = ai_player
                score = self._minimax(False, ai_player, alpha, beta)
                self.board[row][col] = self.EMPTY
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break  # Beta cutoff: opponent won't allow this path
            return max_score
        else:
            # Opponent's turn: minimize score
            min_score = float('inf')
            for row, col in self.legal_moves():
                self.board[row][col] = opponent
                score = self._minimax(True, ai_player, alpha, beta)
                self.board[row][col] = self.EMPTY
                min_score = min(min_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break  # Alpha cutoff: AI won't allow this path
            return min_score


class TicTacToeGUI:
    """Tkinter GUI for Tic-Tac-Toe with menu bar and scoreboard"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Perfect-Play Tic-Tac-Toe")
        self.root.resizable(False, False)
        
        # Game state
        self.engine = Engine()
        self.current_player = Engine.X
        self.mode = GameMode.HUMAN_VS_HUMAN
        self.human_player = Engine.X  # For Human vs AI mode
        
        # Scoreboard
        self.scores = {Engine.X: 0, Engine.O: 0, "Tie": 0}
        
        # GUI components
        self.buttons: List[List[tk.Button]] = []
        self._create_menu()
        self._create_status_bar()
        self._create_board()
        self._create_scoreboard()
        
        self._update_status()
    
    def _create_menu(self) -> None:
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Game menu
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="New", command=self._new_game)
        game_menu.add_command(label="Reset Scores", command=self._reset_scores)
        game_menu.add_separator()
        game_menu.add_command(label="Quit", command=self.root.quit)
        
        # Mode menu
        mode_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Mode", menu=mode_menu)
        mode_menu.add_command(label="Human vs Human", 
                             command=lambda: self._set_mode(GameMode.HUMAN_VS_HUMAN))
        mode_menu.add_command(label="Human vs AI", 
                             command=lambda: self._set_mode(GameMode.HUMAN_VS_AI))
        mode_menu.add_command(label="AI vs AI", 
                             command=lambda: self._set_mode(GameMode.AI_VS_AI))
    
    def _create_status_bar(self) -> None:
        """Create status label"""
        self.status_label = tk.Label(self.root, text="", font=("Arial", 12), 
                                     pady=10, relief=tk.SUNKEN, bd=1)
        self.status_label.pack(fill=tk.X)
    
    def _create_board(self) -> None:
        """Create 3x3 grid of buttons"""
        board_frame = tk.Frame(self.root)
        board_frame.pack(pady=10)
        
        for r in range(3):
            row_buttons = []
            for c in range(3):
                btn = tk.Button(board_frame, text=" ", font=("Arial", 24), 
                               width=5, height=2,
                               command=lambda row=r, col=c: self._on_click(row, col))
                btn.grid(row=r, column=c, padx=2, pady=2)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)
    
    def _create_scoreboard(self) -> None:
        """Create scoreboard display"""
        score_frame = tk.Frame(self.root)
        score_frame.pack(pady=10)
        
        self.score_label = tk.Label(score_frame, text="", font=("Arial", 11))
        self.score_label.pack()
        self._update_scoreboard()
    
    def _update_scoreboard(self) -> None:
        """Update scoreboard text"""
        text = f"X Wins: {self.scores[Engine.X]}  |  " \
               f"O Wins: {self.scores[Engine.O]}  |  " \
               f"Ties: {self.scores['Tie']}"
        self.score_label.config(text=text)
    
    def _update_status(self) -> None:
        """Update status bar with current game state"""
        if self.engine.is_terminal():
            winner = self.engine.winner()
            if winner:
                self.status_label.config(text=f"Game Over - {winner} wins!")
            else:
                self.status_label.config(text="Game Over - Tie!")
        else:
            mode_str = self.mode.value
            if self.mode == GameMode.HUMAN_VS_AI:
                mode_str += f" (You are {self.human_player})"
            self.status_label.config(
                text=f"Mode: {mode_str} | Current Player: {self.current_player}"
            )
    
    def _update_board_display(self) -> None:
        """Sync button display with engine state"""
        for r in range(3):
            for c in range(3):
                self.buttons[r][c].config(text=self.engine.board[r][c])
    
    def _on_click(self, row: int, col: int) -> None:
        """Handle board button click"""
        # Ignore if game over
        if self.engine.is_terminal():
            return
        
        # Ignore if not human's turn
        if self.mode == GameMode.HUMAN_VS_AI:
            if self.current_player != self.human_player:
                return
        elif self.mode == GameMode.AI_VS_AI:
            return  # No human clicks in AI vs AI
        
        # Try to make move
        if self.engine.make_move(row, col, self.current_player):
            self._update_board_display()
            
            if self.engine.is_terminal():
                self._handle_game_over()
            else:
                self._switch_player()
                self._update_status()
                
                # Trigger AI move if needed
                if self.mode == GameMode.HUMAN_VS_AI and \
                   self.current_player != self.human_player:
                    self.root.after(100, self._ai_move)
    
    def _ai_move(self) -> None:
        """Execute AI move (non-blocking)"""
        if self.engine.is_terminal():
            return
        
        move = self.engine.best_move(self.current_player)
        if move:
            row, col = move
            self.engine.make_move(row, col, self.current_player)
            self._update_board_display()
            
            if self.engine.is_terminal():
                self._handle_game_over()
            else:
                self._switch_player()
                self._update_status()
                
                # Continue AI vs AI
                if self.mode == GameMode.AI_VS_AI:
                    self.root.after(500, self._ai_move)
    
    def _switch_player(self) -> None:
        """Toggle current player"""
        self.current_player = Engine.O if self.current_player == Engine.X else Engine.X
    
    def _handle_game_over(self) -> None:
        """Handle end of game"""
        winner = self.engine.winner()
        if winner:
            self.scores[winner] += 1
        else:
            self.scores["Tie"] += 1
        
        self._update_scoreboard()
        self._update_status()
    
    def _new_game(self) -> None:
        """Start new game (preserve scores)"""
        self.engine.reset()
        self.current_player = Engine.X
        self._update_board_display()
        self._update_status()
        
        # If AI is X in Human vs AI, make first move
        if self.mode == GameMode.HUMAN_VS_AI and self.human_player == Engine.O:
            self.root.after(100, self._ai_move)
        elif self.mode == GameMode.AI_VS_AI:
            self.root.after(500, self._ai_move)
    
    def _reset_scores(self) -> None:
        """Reset all scores to zero"""
        self.scores = {Engine.X: 0, Engine.O: 0, "Tie": 0}
        self._update_scoreboard()
    
    def _set_mode(self, mode: GameMode) -> None:
        """Change game mode"""
        self.mode = mode
        
        # For Human vs AI, ask which side to play
        if mode == GameMode.HUMAN_VS_AI:
            choice = messagebox.askyesno(
                "Choose Side",
                "Do you want to play as X?\n(X moves first)\n\nYes = X, No = O"
            )
            self.human_player = Engine.X if choice else Engine.O
        
        self._new_game()


def main():
    """Entry point"""
    root = tk.Tk()
    app = TicTacToeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
