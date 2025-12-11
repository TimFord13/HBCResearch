import tkinter as tk
from tkinter import Frame, Button, Label, Menu, StringVar, Toplevel
from tkinter.constants import SUNKEN, W, E, NORMAL, DISABLED
from typing import Optional

# Import the game engine and AI functions
import engine

# Define constants from the engine for GUI use
PLAYER_X = engine.PLAYER_X
PLAYER_O = engine.PLAYER_O
EMPTY = engine.EMPTY

class TicTacToeGUI:
    """
    The main graphical user interface class for the Tic-Tac-Toe game.
    It handles window creation, widgets, event binding, and game flow.
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.root.quit)

        # Initialize the game engine
        self.game_engine = engine.TicTacToeEngine()

        # --- Game State Variables ---
        self.scores = {"X": 0, "O": 0, "Ties": 0}
        self.mode_var = StringVar(value="Human vs Human")
        self.human_player_var = StringVar(value=PLAYER_X)
        self.human_player_var.trace_add("write", self._on_player_change)
        
        # --- Build UI Components ---
        self._create_menu()
        self._create_scoreboard()
        self._create_board_frame()
        self._create_status_bar()

        # Start the first game
        self.new_game()

    # --- UI Creation Methods ---

    def _create_menu(self):
        """Creates the main application menu bar."""
        self.menu_bar = Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # --- Game Menu ---
        game_menu = Menu(self.menu_bar, tearoff=0)
        game_menu.add_command(label="New Game", command=self.new_game)
        game_menu.add_command(label="Reset Scores", command=self.reset_scores)
        game_menu.add_separator()
        game_menu.add_command(label="Quit", command=self.root.quit)
        self.menu_bar.add_cascade(label="Game", menu=game_menu)

        # --- Mode Menu ---
        mode_menu = Menu(self.menu_bar, tearoff=0)
        mode_menu.add_radiobutton(
            label="Human vs Human", 
            variable=self.mode_var, 
            value="Human vs Human", 
            command=self._on_mode_change
        )
        mode_menu.add_radiobutton(
            label="Human vs AI", 
            variable=self.mode_var, 
            value="Human vs AI", 
            command=self._on_mode_change
        )
        mode_menu.add_radiobutton(
            label="AI vs AI", 
            variable=self.mode_var, 
            value="AI vs AI", 
            command=self._on_mode_change
        )
        self.menu_bar.add_cascade(label="Mode", menu=mode_menu)

        # --- Player Menu (for Human vs AI) ---
        self.player_menu = Menu(self.menu_bar, tearoff=0)
        self.player_menu.add_radiobutton(
            label="Play as X", 
            variable=self.human_player_var, 
            value=PLAYER_X
        )
        self.player_menu.add_radiobutton(
            label="Play as O", 
            variable=self.human_player_var, 
            value=PLAYER_O
        )
        self.menu_bar.add_cascade(label="Player", menu=self.player_menu)

    def _create_scoreboard(self):
        """Creates the frame for displaying X, O, and Tie scores."""
        score_frame = Frame(self.root)
        score_frame.pack(pady=10)

        self.score_label_x = Label(score_frame, text="X Wins: 0", 
                                   font=("Arial", 14), padx=10)
        self.score_label_ties = Label(score_frame, text="Ties: 0", 
                                      font=("Arial", 14), padx=10)
        self.score_label_o = Label(score_frame, text="O Wins: 0", 
                                   font=("Arial", 14), padx=10)
        
        self.score_label_x.pack(side=tk.LEFT)
        self.score_label_ties.pack(side=tk.LEFT)
        self.score_label_o.pack(side=tk.LEFT)

    def _create_board_frame(self):
        """Creates the 3x3 grid of buttons for the game board."""
        board_frame = Frame(self.root)
        board_frame.pack(pady=10, expand=True)
        
        self.board_buttons: List[List[Button]] = []
        for r in range(3):
            row_list = []
            for c in range(3):
                button = Button(
                    board_frame,
                    text=EMPTY,
                    font=("Helvetica", 32, "bold"),
                    width=5,
                    height=2,
                    relief=SUNKEN,
                    bd=1,
                    command=lambda r=r, c=c: self._on_cell_click(r, c)
                )
                button.grid(row=r, column=c, padx=2, pady=2)
                row_list.append(button)
            self.board_buttons.append(row_list)

    def _create_status_bar(self):
        """Creates the label at the bottom for game status."""
        status_frame = Frame(self.root, relief=SUNKEN, bd=1)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = Label(status_frame, text="", anchor=W, padx=5, pady=2)
        self.status_label.pack(fill=tk.X)

    # --- Game Flow Methods ---

    def new_game(self):
        """Starts a new round of Tic-Tac-Toe."""
        self.game_engine.reset_game()
        self._update_board_buttons()
        self._enable_all_buttons()
        self._update_player_menu_state()
        self._update_status_bar()
        
        # Check if AI should make the first move
        self._check_for_ai_turn()

    def reset_scores(self):
        """Resets all scores to 0."""
        self.scores = {"X": 0, "O": 0, "Ties": 0}
        self._update_scoreboard()
        self._update_status_bar()

    def _on_cell_click(self, row: int, col: int):
        """Handles a human player clicking on a board cell."""
        
        # 1. Check if the game is already over
        if self.game_engine.is_game_over():
            return

        # 2. Determine if it's a human's turn
        is_human_turn = False
        current_mode = self.mode_var.get()
        human_player = self.human_player_var.get()
        
        if current_mode == "Human vs Human":
            is_human_turn = True
        elif current_mode == "Human vs AI":
            is_human_turn = (self.game_engine.current_player == human_player)
        # If "AI vs AI", is_human_turn remains False
        
        if not is_human_turn:
            return # Not user's turn, do nothing

        # 3. Try to make the move
        success = self.game_engine.make_move(row, col)
        
        if success:
            # 4. Update the board
            self._update_board_buttons()
            
            # 5. Check for game end
            if self._check_for_game_end():
                return # Game over, stop here
            
            # 6. Update status (e.g., "O's turn")
            self._update_status_bar()
            
            # 7. If game is not over, check if it's now an AI's turn
            self._check_for_ai_turn()

    def _check_for_ai_turn(self):
        """
        Checks if the current player is an AI, and if so,
        triggers the AI's move.
        """
        if self.game_engine.is_game_over():
            return
            
        current_mode = self.mode_var.get()
        human_player = self.human_player_var.get()
        current_player = self.game_engine.current_player
        
        is_ai_turn = False
        if current_mode == "AI vs AI":
            is_ai_turn = True
        elif current_mode == "Human vs AI" and current_player != human_player:
            is_ai_turn = True
            
        if is_ai_turn:
            # Disable board during AI 'thinking' (even if instant)
            self._disable_all_buttons()
            
            # Use root.after to make the AI move non-blocking
            # This allows the UI to update (e.g., button disable)
            # before the AI calculation (which is fast, but good practice).
            self.root.after(100, self._make_ai_move)

    def _make_ai_move(self):
        """Finds and executes the AI's best move."""
        if self.game_engine.is_game_over():
            return
            
        # Get best move from the engine
        board_state = self.game_engine.board
        player = self.game_engine.current_player
        row, col = engine.find_best_move(board_state, player)
        
        # Make the move
        self.game_engine.make_move(row, col)
        
        # Update UI
        self._update_board_buttons()
        
        # Check for game end
        if self._check_for_game_end():
            return
            
        # Re-enable board if it's now a human's turn
        if self.mode_var.get() == "Human vs AI":
            self._enable_all_buttons()
        
        self._update_status_bar()
        
        # Check for *another* AI turn (for AI vs AI mode)
        self._check_for_ai_turn()

    def _check_for_game_end(self) -> bool:
        """
        Checks if the game is over, updates scores, and disables
        the board.
        
        Returns:
            True if the game ended, False otherwise.
        """
        winner = self.game_engine.get_winner()
        is_tie = self.game_engine.is_tie()
        
        if winner:
            self.scores[winner] += 1
            self._disable_all_buttons()
        elif is_tie:
            self.scores["Ties"] += 1
            self._disable_all_buttons()
            
        if winner or is_tie:
            self._update_scoreboard()
            self._update_status_bar()
            return True
            
        return False

    # --- Event Handlers (Menu) ---

    def _on_mode_change(self):
        """Called when a Mode menu radio button is clicked."""
        self.new_game() # Start a new game whenever mode changes

    def _on_player_change(self, *args):
        """
        Called when the Player menu (X/O) is changed.
        The *args is required by the trace_add callback.
        """
        # Only start a new game if the mode is relevant
        if self.mode_var.get() == "Human vs AI":
            self.new_game()

    # --- UI Update (Helper) Methods ---

    def _update_board_buttons(self):
        """Syncs the text of the 3x3 buttons with the engine's board."""
        for r in range(3):
            for c in range(3):
                text = self.game_engine.board[r][c]
                self.board_buttons[r][c].config(text=text)

    def _update_scoreboard(self):
        """Updates the X Wins, O Wins, and Ties labels."""
        self.score_label_x.config(text=f"X Wins: {self.scores['X']}")
        self.score_label_o.config(text=f"O Wins: {self.scores['O']}")
        self.score_label_ties.config(text=f"Ties: {self.scores['Ties']}")

    def _update_status_bar(self):
        """Updates the text in the bottom status label."""
        winner = self.game_engine.get_winner()
        is_tie = self.game_engine.is_tie()
        
        if winner:
            message = f"Game Over: Player {winner} wins!"
        elif is_tie:
            message = "Game Over: It's a tie!"
        else:
            mode = self.mode_var.get()
            player = self.game_engine.current_player
            message = f"Mode: {mode}  |  Current Player: {player}"
        
        self.status_label.config(text=message)

    def _disable_all_buttons(self):
        """Disables all 9 board buttons."""
        for r in range(3):
            for c in range(3):
                self.board_buttons[r][c].config(state=DISABLED)

    def _enable_all_buttons(self):
        """Enables all 9 board buttons."""
        # Note: We could be smarter and only enable *empty* ones,
        # but clicking an occupied one does nothing anyway.
        # This is simpler.
        for r in range(3):
            for c in range(3):
                self.board_buttons[r][c].config(state=NORMAL)
                
    def _update_player_menu_state(self):
        """Enables/Disables the 'Player' menu based on game mode."""
        if self.mode_var.get() == "Human vs AI":
            self.player_menu.entryconfig("Play as X", state=NORMAL)
            self.player_menu.entryconfig("Play as O", state=NORMAL)
        else:
            self.player_menu.entryconfig("Play as X", state=DISABLED)
            self.player_menu.entryconfig("Play as O", state=DISABLED)