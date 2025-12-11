# gui.py
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Optional, Tuple
import engine

MODE_HH = "Human vs Human"
MODE_HA = "Human vs AI"
MODE_AA = "AI vs AI"

class TicTacToeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Tic-Tac-Toe — Perfect Play")
        self.root.resizable(False, False)

        # Game state
        self.board = engine.new_board()
        self.current_player = "X"
        self.mode = MODE_HH
        self.human_side = "X"  # relevant only in HA mode
        self.scores = {"X": 0, "O": 0, "Tie": 0}
        self.game_over = False
        self.ai_thinking = False

        # UI
        self._build_menu()
        self._build_main()
        self._update_status()
        # Start if AI must move first
        self._maybe_ai_turn()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        game_menu = tk.Menu(menubar, tearoff=0)
        game_menu.add_command(label="New", command=self.menu_new_game, accelerator="Ctrl+N")
        game_menu.add_command(label="Reset Scores", command=self.menu_reset_scores)
        game_menu.add_separator()
        game_menu.add_command(label="Quit", command=self.root.quit, accelerator="Ctrl+Q")

        mode_menu = tk.Menu(menubar, tearoff=0)
        mode_menu.add_command(label=MODE_HH, command=lambda: self.set_mode(MODE_HH))
        mode_menu.add_command(label=MODE_HA, command=lambda: self.set_mode(MODE_HA))
        mode_menu.add_command(label=MODE_AA, command=lambda: self.set_mode(MODE_AA))

        menubar.add_cascade(label="Game", menu=game_menu)
        menubar.add_cascade(label="Mode", menu=mode_menu)
        self.root.config(menu=menubar)

        # Keyboard shortcuts (optional polish)
        self.root.bind_all("<Control-n>", lambda e: self.menu_new_game())
        self.root.bind_all("<Control-q>", lambda e: self.root.quit())

    def _build_main(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.grid(row=0, column=0)

        # Scoreboard
        self.score_var = tk.StringVar()
        score_label = ttk.Label(outer, textvariable=self.score_var, font=("TkDefaultFont", 10, "bold"))
        score_label.grid(row=0, column=0, columnspan=3, pady=(0, 8))

        # Board grid
        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        for r in range(3):
            for c in range(3):
                btn = ttk.Button(outer, text=" ", width=5, command=lambda rr=r, cc=c: self.on_cell_click(rr, cc))
                btn.grid(row=r+1, column=c, padx=2, pady=2, ipadx=6, ipady=6)
                self.buttons[r][c] = btn

        # Status bar
        self.status_var = tk.StringVar()
        status_label = ttk.Label(outer, textvariable=self.status_var, anchor="w")
        status_label.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        self._refresh_board()
        self._update_scoreboard()

    def set_mode(self, new_mode: str) -> None:
        """Switch modes mid-app and update status appropriately."""
        self.mode = new_mode
        if self.mode == MODE_HA:
            # Choose human side
            self._prompt_human_side()
        self._update_status()
        self._maybe_ai_turn()

    def _prompt_human_side(self) -> None:
        choice = self._ask_human_side_dialog()
        if choice in ("X", "O"):
            self.human_side = choice
            # If the human chose O and the game is fresh and X to play, AI should move
            self._maybe_ai_turn()

    def _ask_human_side_dialog(self) -> Optional[str]:
        # Small simple dialog using simpledialog
        while True:
            ans = simpledialog.askstring(
                "Human Side",
                "Play as X or O? (X moves first)",
                parent=self.root,
            )
            if ans is None:
                # user canceled; keep previous side
                return None
            ans = ans.strip().upper()
            if ans in ("X", "O"):
                return ans
            messagebox.showinfo("Invalid choice", "Please enter X or O.")

    def on_cell_click(self, r: int, c: int) -> None:
        """Handle user clicks. Ignore when not allowed or cell filled or game over."""
        if self.game_over or self.ai_thinking:
            return

        if self.mode == MODE_HA and self.current_player != self.human_side:
            return  # disable clicks when it isn’t the human’s turn

        if self.board[r][c] != " ":
            # Clicking a filled cell should do nothing
            return

        # Make human move
        self.board[r][c] = self.current_player
        self._post_move()

    def _post_move(self) -> None:
        self._refresh_board()
        w = engine.winner(self.board)
        if w is not None:
            self.game_over = True
            self.scores[w] += 1
            self._update_scoreboard()
            self._update_status(f"{w} wins")
            return
        if all(cell != " " for row in self.board for cell in row):
            self.game_over = True
            self.scores["Tie"] += 1
            self._update_scoreboard()
            self._update_status("Tie")
            return

        # Switch player and maybe trigger AI
        self.current_player = "O" if self.current_player == "X" else "X"
        self._update_status()
        self._maybe_ai_turn()

    def _maybe_ai_turn(self) -> None:
        """If current turn belongs to AI (in HA or AA), schedule AI to move via after()."""
        if self.game_over:
            return
        if self.mode == MODE_HH:
            return
        if self.mode == MODE_HA and self.current_player != self.human_side:
            self.ai_thinking = True
            # Non-blocking: compute shortly after so UI stays responsive
            self.root.after(10, self._ai_move_once)
        elif self.mode == MODE_AA:
            self.ai_thinking = True
            self.root.after(10, self._ai_move_once)

    def _ai_move_once(self) -> None:
        """Make exactly one AI move (for current_player), then post-move. For AA, this will chain."""
        if self.game_over:
            self.ai_thinking = False
            return

        # Compute best move deterministically
        move = engine.best_move(self.board, self.current_player)
        if move == (-1, -1):
            # Terminal safeguard
            self.ai_thinking = False
            return
        r, c = move
        self.board[r][c] = self.current_player
        self.ai_thinking = False
        self._post_move()

        # If still AI's turn in AA mode, schedule next step
        if not self.game_over and self.mode == MODE_AA:
            self._maybe_ai_turn()

    def _refresh_board(self) -> None:
        for r in range(3):
            for c in range(3):
                self.buttons[r][c]["text"] = self.board[r][c]

        # Disable all buttons when terminal or when AI's turn in HA/AA
        disable_all = self.game_over or (self.mode != MODE_HH and (self.mode == MODE_AA or self.current_player != self.human_side))
        for r in range(3):
            for c in range(3):
                state = tk.DISABLED if disable_all or self.board[r][c] != " " else tk.NORMAL
                self.buttons[r][c]["state"] = state

    def _update_status(self, result: Optional[str] = None) -> None:
        if result:
            status = f"Result: {result} | Mode: {self.mode} | Scores X:{self.scores['X']} O:{self.scores['O']} Ties:{self.scores['Tie']}"
        else:
            status = f"Turn: {self.current_player} | Mode: {self.mode} | Human: {self.human_side if self.mode==MODE_HA else '-'}"
        self.status_var.set(status)

    def _update_scoreboard(self) -> None:
        self.score_var.set(f"Scoreboard — X: {self.scores['X']}   O: {self.scores['O']}   Ties: {self.scores['Tie']}")

    # Menu commands
    def menu_new_game(self) -> None:
        """Start a new round, preserve scores."""
        self.board = engine.new_board()
        self.current_player = "X"
        self.game_over = False
        self._refresh_board()
        self._update_status()
        self._maybe_ai_turn()

    def menu_reset_scores(self) -> None:
        self.scores = {"X": 0, "O": 0, "Tie": 0}
        self._update_scoreboard()
        self._update_status()

def launch() -> None:
    root = tk.Tk()
    # Use themed widgets for consistent sizing
    try:
        from tkinter import ttk  # noqa: F401
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = TicTacToeApp(root)
    root.mainloop()
