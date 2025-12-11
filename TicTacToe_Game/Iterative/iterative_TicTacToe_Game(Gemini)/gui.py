import tkinter as tk
from tkinter import font
from engine import TicTacToe, best_move

class TicTacToeGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Tic-Tac-Toe")
        
        # 1. Lock Window Size & Center it
        self.root.resizable(False, False)
        
        # Game State
        self.game = TicTacToe()
        self.scores = {'X': 0, 'O': 0, 'Tie': 0}
        self.mode = "HvH" 
        self.human_side = "X" 
        
        # UI Config
        self.btn_font = font.Font(family="Helvetica", size=24, weight="bold")
        self.default_bg = "SystemButtonFace"
        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        
        self._create_menu()
        self._create_scoreboard()
        self._create_board()
        self._create_status()
        
        # Center window after widgets are packed
        self._center_window()
        
        self._update_status("Player X's Turn")

    def _center_window(self):
        """Updates geometry to center the window on the screen."""
        self.root.update_idletasks() # Ensure widgets are calculated
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        
        # Game Menu
        game_menu = tk.Menu(menubar, tearoff=0)
        game_menu.add_command(label="New Game", command=self.reset_game)
        game_menu.add_command(label="Reset Scores", command=self.reset_scores)
        game_menu.add_separator()
        game_menu.add_command(label="Quit", command=self.root.quit)
        menubar.add_cascade(label="Game", menu=game_menu)
        
        # Mode Menu
        mode_menu = tk.Menu(menubar, tearoff=0)
        mode_menu.add_radiobutton(label="Human vs Human", command=lambda: self.set_mode("HvH"))
        mode_menu.add_separator()
        mode_menu.add_radiobutton(label="Human vs AI", command=lambda: self.set_mode("HvAI"))
        mode_menu.add_radiobutton(label="AI vs AI", command=lambda: self.set_mode("AIvAI"))
        menubar.add_cascade(label="Mode", menu=mode_menu)

        # Side Menu
        side_menu = tk.Menu(menubar, tearoff=0)
        side_menu.add_radiobutton(label="Play as X (First)", command=lambda: self.set_side("X"))
        side_menu.add_radiobutton(label="Play as O (Second)", command=lambda: self.set_side("O"))
        menubar.add_cascade(label="Side", menu=side_menu)
        
        self.root.config(menu=menubar)

    def _create_scoreboard(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        self.score_labels = {}
        for key in ['X', 'O', 'Tie']:
            lbl = tk.Label(frame, text=f"{key}: 0", font=("Arial", 12), width=8)
            lbl.pack(side=tk.LEFT, padx=5)
            self.score_labels[key] = lbl

    def _create_board(self):
        grid_frame = tk.Frame(self.root)
        grid_frame.pack(pady=10)
        for r in range(3):
            for c in range(3):
                btn = tk.Button(
                    grid_frame, text="", width=6, height=3, font=self.btn_font,
                    command=lambda row=r, col=c: self.handle_human_click(row, col)
                )
                btn.grid(row=r, column=c, padx=5, pady=5)
                self.buttons[r][c] = btn

    def _create_status(self):
        self.status_label = tk.Label(self.root, text="Welcome", font=("Arial", 14))
        self.status_label.pack(pady=10)

    # --- Logic ---

    def set_mode(self, mode):
        self.mode = mode
        self.reset_game()

    def set_side(self, side):
        self.human_side = side
        self.reset_game()

    def handle_human_click(self, row, col):
        if self.game.is_game_over: return
        if self.mode == "AIvAI": return
        if self.mode == "HvAI" and self.game.current_player != self.human_side: return

        self.execute_move(row, col)
        
        if not self.game.is_game_over and self.mode == "HvAI":
            self.root.after(500, self.computer_move)

    def computer_move(self):
        if self.game.is_game_over: return

        move = best_move(self.game.board, self.game.current_player)
        if move:
            self.execute_move(move[0], move[1])
            
        if not self.game.is_game_over and self.mode == "AIvAI":
            self.root.after(500, self.computer_move)
        elif not self.game.is_game_over and self.mode == "HvAI" and self.game.current_player != self.human_side:
             pass

    def execute_move(self, row, col):
        if self.game.make_move(row, col):
            player = self.game.board[row][col]
            color = "black" if player == "X" else "red"
            self.buttons[row][col].config(text=player, state="disabled", disabledforeground=color)
            
            if self.game.is_game_over:
                self.handle_game_over()
            else:
                self._update_status(f"Player {self.game.current_player}'s Turn")

    def handle_game_over(self):
        if self.game.winner:
            self.scores[self.game.winner] += 1
            self._update_status(f"Winner: {self.game.winner}!")
            self.highlight_win()
        else:
            self.scores['Tie'] += 1
            self._update_status("It's a Tie!")
        self._update_scoreboard()

    def highlight_win(self):
        if self.game.winning_line:
            for r, c in self.game.winning_line:
                self.buttons[r][c].config(bg="#90EE90")

    def reset_game(self):
        self.game.reset()
        for r in range(3):
            for c in range(3):
                self.buttons[r][c].config(text="", state="normal", bg=self.default_bg)
        
        self._update_status("Player X's Turn")
        
        if self.mode == "AIvAI":
            self.root.after(500, self.computer_move)
        elif self.mode == "HvAI" and self.human_side == "O":
            self.root.after(500, self.computer_move)

    def reset_scores(self):
        self.scores = {'X': 0, 'O': 0, 'Tie': 0}
        self._update_scoreboard()

    def _update_scoreboard(self):
        for key in self.scores:
            self.score_labels[key].config(text=f"{key}: {self.scores[key]}")

    def _update_status(self, text):
        self.status_label.config(text=text)

if __name__ == "__main__":
    root = tk.Tk()
    app = TicTacToeGUI(root)
    root.mainloop()