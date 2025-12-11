# gui.py
# Tkinter Tic-Tac-Toe GUI with menu, modes, side selection, AI integration, scoreboard,
# delayed AI turns (watchable), winning-line highlight, and responsive layout (flex on resize).
# Place this next to engine.py and run:  python gui.py

import tkinter as tk
from typing import List, Optional, Tuple
from engine import TicTacToeEngine, Board, best_move

Mode = str  # "HvH" | "HvAI_X" | "HvAI_O" | "AIvAI"


class TicTacToeGUI:
    AI_DELAY_MS = 300  # visual cadence between AI moves

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Tic-Tac-Toe")
        # Give the window a reasonable minimum and allow flex growth
        self.root.minsize(420, 520)

        # Game + state
        self.game = TicTacToeEngine()
        self.mode: Mode = "HvH"  # default: Human vs Human
        self.scores = {"X": 0, "O": 0, "T": 0}  # ties under "T"
        self.ai_busy: bool = False  # block clicks while AI is "thinking"
        self.winning_cells: List[Tuple[int, int]] = []

        # Menu bar
        self._build_menubar()

        # ----- Layout: top-level vertical stack that flexes -----
        self.root_frame = tk.Frame(self.root)
        self.root_frame.pack(fill="both", expand=True)

        # Board grid (flexes to absorb extra space)
        board_wrapper = tk.Frame(self.root_frame, padx=10, pady=10)
        board_wrapper.pack(side="top", fill="both", expand=True)

        self.buttons: List[List[tk.Button]] = []
        self._default_bg: Optional[str] = None

        for r in range(3):
            row_btns: List[tk.Button] = []
            for c in range(3):
                btn = tk.Button(
                    board_wrapper,
                    text="",
                    width=5,
                    height=2,
                    font=("Segoe UI", 24, "bold"),
                    command=lambda rr=r, cc=c: self.on_cell_click(rr, cc),
                )
                # Make each button expand to fill its cell
                btn.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
                if self._default_bg is None:
                    self._default_bg = btn.cget("bg")
                row_btns.append(btn)
            self.buttons.append(row_btns)

        # Make the 3x3 grid flex evenly and stay square-ish
        for i in range(3):
            board_wrapper.grid_rowconfigure(i, weight=1, uniform="board")
            board_wrapper.grid_columnconfigure(i, weight=1, uniform="board")

        # Status + controls (fixed height)
        bottom = tk.Frame(self.root_frame, padx=10, pady=6)
        bottom.pack(side="top", fill="x")

        self.status_var = tk.StringVar(value="X to move")
        self.status_label = tk.Label(bottom, textvariable=self.status_var, font=("Segoe UI", 12))
        self.status_label.pack(side="left")

        self.new_btn = tk.Button(bottom, text="New", command=self.new_game)
        self.new_btn.pack(side="right")

        # Scoreboard (fixed height)
        score_frame = tk.Frame(self.root_frame, padx=10, pady=6)
        score_frame.pack(side="top", fill="x")
        self.score_var = tk.StringVar()
        self._update_score_label()
        self.score_label = tk.Label(score_frame, textvariable=self.score_var, font=("Segoe UI", 11))
        self.score_label.pack(side="left")

        self.refresh()
        self._maybe_trigger_ai()  # if mode starts with AI turn

    # --------------------- Menu ---------------------

    def _build_menubar(self) -> None:
        menubar = tk.Menu(self.root)

        game_menu = tk.Menu(menubar, tearoff=0)
        game_menu.add_command(label="New", command=self.new_game)
        game_menu.add_command(label="Reset Scores", command=self.reset_scores)
        game_menu.add_separator()
        game_menu.add_command(label="Quit", command=self.root.quit)
        menubar.add_cascade(label="Game", menu=game_menu)

        mode_menu = tk.Menu(menubar, tearoff=0)
        mode_menu.add_command(label="Human vs Human", command=lambda: self.set_mode("HvH"))
        # Side selection for Human vs AI
        mode_menu.add_command(label="Human (X) vs AI (O)", command=lambda: self.set_mode("HvAI_X"))
        mode_menu.add_command(label="Human (O) vs AI (X)", command=lambda: self.set_mode("HvAI_O"))
        mode_menu.add_separator()
        mode_menu.add_command(label="AI vs AI", command=lambda: self.set_mode("AIvAI"))
        menubar.add_cascade(label="Mode", menu=mode_menu)

        self.root.config(menu=menubar)

    # --------------------- Core UI actions ---------------------

    def on_cell_click(self, r: int, c: int) -> None:
        # Disable clicks when it's not human turn or AI is thinking
        if self.ai_busy or not self._is_human_turn():
            return

        if self.game.is_terminal():
            self.blink_status("Cell filled or game over.", error=True)
            return

        if not self.game.is_legal_move(r, c):
            self.blink_status("Cell filled or game over.", error=True)
            return

        if self.game.play_move(r, c):
            self.refresh()
            if self.game.is_terminal():
                self._finish_round()
            else:
                self._maybe_trigger_ai()

    def refresh(self) -> None:
        board: Board = self.game.get_board()

        # Update button text and color
        for r in range(3):
            for c in range(3):
                val: Optional[str] = board[r][c]
                btn = self.buttons[r][c]
                btn["text"] = val if val is not None else ""

                # Reset background, then apply highlight if part of winning line
                if self._default_bg is not None:
                    btn.configure(bg=self._default_bg)
                if (r, c) in self.winning_cells:
                    btn.configure(bg="#c7f7c4")  # gentle green highlight

        # Status text
        winner = self.game.get_winner()
        if winner is not None:
            self.status_var.set(f"{winner} wins!")
        elif self.game.is_tie():
            self.status_var.set("Tie game.")
        else:
            turn = self.game.get_current_player()
            if self._is_human_turn():
                self.status_var.set(f"{turn} to move")
            else:
                self.status_var.set(f"{turn} to move (AI{' thinking...' if self.ai_busy else ''})")

        # Enable/disable interactability
        self._update_interactivity()

    def _update_interactivity(self) -> None:
        # In non-human modes (AIvAI) or AI turns, disable clicking
        allow_clicks = (not self.game.is_terminal()) and self._is_human_turn() and (not self.ai_busy)
        for r in range(3):
            for c in range(3):
                cell = self.game.get_board()[r][c]
                enabled = allow_clicks and (cell is None)
                self.buttons[r][c]["state"] = tk.NORMAL if enabled else tk.DISABLED

    def new_game(self) -> None:
        self.game.reset()
        self.ai_busy = False
        self.winning_cells = []
        self.refresh()
        self._maybe_trigger_ai()

    def reset_scores(self) -> None:
        self.scores = {"X": 0, "O": 0, "T": 0}
        self._update_score_label()

    def set_mode(self, mode: Mode) -> None:
        self.mode = mode
        self.new_game()  # start fresh in the new mode

    def blink_status(self, msg: str, error: bool = False) -> None:
        prev = self.status_var.get()
        self.status_var.set(msg)
        self.status_label.config(fg=("red" if error else "black"))
        self.root.after(900, lambda: (self.status_var.set(prev), self.status_label.config(fg="black")))

    # --------------------- AI plumbing ---------------------

    def _is_human_turn(self) -> bool:
        """
        HvH: always human turn.
        HvAI_X: human is X; human turn iff current == 'X'.
        HvAI_O: human is O; human turn iff current == 'O'.
        AIvAI: never human turn.
        """
        if self.mode == "HvH":
            return True
        if self.mode == "HvAI_X":
            return self.game.get_current_player() == "X"
        if self.mode == "HvAI_O":
            return self.game.get_current_player() == "O"
        return False  # AIvAI

    def _ai_turn(self) -> bool:
        if self.mode == "HvAI_X":
            return self.game.get_current_player() == "O"
        if self.mode == "HvAI_O":
            return self.game.get_current_player() == "X"
        if self.mode == "AIvAI":
            return not self.game.is_terminal()
        return False

    def _maybe_trigger_ai(self) -> None:
        """Schedule AI move when appropriate; never blocks. Adds a small delay for watchability."""
        if self.game.is_terminal():
            return
        if not self._ai_turn():
            return

        # Mark busy, update UI, then schedule compute with a small delay
        self.ai_busy = True
        self.refresh()
        self.root.after(self.AI_DELAY_MS, self._ai_move_once)

    def _ai_move_once(self) -> None:
        # If something changed while waiting, bail cleanly
        if self.game.is_terminal():
            self.ai_busy = False
            self.refresh()
            return
        if not self._ai_turn():
            self.ai_busy = False
            self.refresh()
            return

        current = self.game.get_current_player()
        board_copy = self.game.get_board()

        try:
            r, c = best_move(board_copy, current)
        except ValueError:
            # No legal moves (terminal); clean up.
            self.ai_busy = False
            self.refresh()
            return

        # Apply AI move
        self.game.play_move(r, c)
        self.ai_busy = False

        # If game ended, mark winners before refreshing
        if self.game.is_terminal():
            self._finish_round()
        else:
            self.refresh()
            # Chain next AI move with the same gentle delay
            if self._ai_turn():
                self._maybe_trigger_ai()

    # --------------------- Round/score + polish ---------------------

    def _finish_round(self) -> None:
        # Determine winning cells for highlight (if any)
        self.winning_cells = self._find_winning_line()
        winner = self.game.get_winner()
        if winner == "X":
            self.scores["X"] += 1
        elif winner == "O":
            self.scores["O"] += 1
        else:
            self.scores["T"] += 1
        self._update_score_label()
        self.refresh()  # apply highlight + final status
        self._update_interactivity()

    def _update_score_label(self) -> None:
        self.score_var.set(f"Score — X: {self.scores['X']}   O: {self.scores['O']}   Ties: {self.scores['T']}")

    def _find_winning_line(self) -> List[Tuple[int, int]]:
        """
        Return list of (r,c) cells forming the winning line, or [] if none.
        """
        w = self.game.get_winner()
        if w is None:
            return []

        b = self.game.get_board()

        # Rows
        for r in range(3):
            if b[r][0] == b[r][1] == b[r][2] == w:
                return [(r, 0), (r, 1), (r, 2)]

        # Columns
        for c in range(3):
            if b[0][c] == b[1][c] == b[2][c] == w:
                return [(0, c), (1, c), (2, c)]

        # Diagonals
        if b[0][0] == b[1][1] == b[2][2] == w:
            return [(0, 0), (1, 1), (2, 2)]
        if b[0][2] == b[1][1] == b[2][0] == w:
            return [(0, 2), (1, 1), (2, 0)]

        return []


def main() -> None:
    root = tk.Tk()
    TicTacToeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
