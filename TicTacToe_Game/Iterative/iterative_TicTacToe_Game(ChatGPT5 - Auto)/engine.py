"""
engine.py

Core Tic-Tac-Toe game logic + perfect AI (Minimax with alpha-beta pruning).

Features:
- 3x3 board (list of lists)
- Legal move checking
- Win / tie / terminal detection
- Turn order enforcement (X always first, alternates correctly)
- Standalone AI helpers:
    - best_move(board, player)
    - is_terminal_board(board)
    - winner_board(board)
    - legal_moves_board(board)
- Simple self-test suite that runs when executed directly.
"""

from typing import List, Optional, Literal, Tuple

Player = Literal["X", "O"]
Board = List[List[Optional[Player]]]
Move = Tuple[int, int]


class TicTacToeEngine:
    """
    Core Tic-Tac-Toe engine (no GUI).
    """

    def __init__(self) -> None:
        """Initialize a new empty game with X to move first."""
        self.board: Board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player: Player = "X"
        self.winner: Optional[Player] = None
        self.tie: bool = False

    def reset(self) -> None:
        """
        Reset the game to an empty board with X to move first.
        """
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.winner = None
        self.tie = False

    def get_board(self) -> Board:
        """
        Return a copy of the current board.

        Returns:
            A 3x3 list of lists containing 'X', 'O', or None.
        """
        return [[cell for cell in row] for row in self.board]

    def get_current_player(self) -> Player:
        """
        Get the player whose turn it is.

        Returns:
            'X' or 'O'.
        """
        return self.current_player

    def get_winner(self) -> Optional[Player]:
        """
        Get the winner of the game.

        Returns:
            'X', 'O', or None if there is no winner yet.
        """
        return self.winner

    def is_tie(self) -> bool:
        """
        Check if the game ended in a tie.

        Returns:
            True if the board is full and there is no winner, False otherwise.
        """
        return self.tie

    def is_terminal(self) -> bool:
        """
        Check if the game is in a terminal state (win or tie).

        Returns:
            True if the game is over, False otherwise.
        """
        return self.winner is not None or self.tie

    def get_legal_moves(self) -> List[Move]:
        """
        Get a list of all legal moves.

        Returns:
            A list of (row, col) pairs where the board cell is empty.
            If the game is over, this list is empty.
        """
        if self.is_terminal():
            return []

        moves: List[Move] = []
        for r in range(3):
            for c in range(3):
                if self.board[r][c] is None:
                    moves.append((r, c))
        return moves

    def is_legal_move(self, row: int, col: int) -> bool:
        """
        Check whether a move is legal.

        Args:
            row: Row index (0-2).
            col: Column index (0-2).

        Returns:
            True if the move is within bounds, the cell is empty,
            and the game is not already over.
        """
        if self.is_terminal():
            return False
        if not (0 <= row < 3 and 0 <= col < 3):
            return False
        return self.board[row][col] is None

    def play_move(self, row: int, col: int) -> bool:
        """
        Attempt to play a move for the current player.

        Args:
            row: Row index (0-2).
            col: Column index (0-2).

        Returns:
            True if the move was applied successfully, False otherwise.
        """
        if not self.is_legal_move(row, col):
            return False

        self.board[row][col] = self.current_player
        self.winner = self._check_winner()

        if self.winner is None and self._is_board_full():
            self.tie = True

        if not self.is_terminal():
            self.current_player = "O" if self.current_player == "X" else "X"

        return True

    def _is_board_full(self) -> bool:
        """
        Check whether the board is full.

        Returns:
            True if all cells are occupied, False otherwise.
        """
        for row in self.board:
            for cell in row:
                if cell is None:
                    return False
        return True

    def _check_winner(self) -> Optional[Player]:
        """
        Check the board for a winner.

        Returns:
            'X', 'O', or None if there is no winner.
        """
        lines = []

        # Rows
        lines.extend(self.board)

        # Columns
        for c in range(3):
            lines.append([self.board[r][c] for r in range(3)])

        # Diagonals
        lines.append([self.board[i][i] for i in range(3)])
        lines.append([self.board[i][2 - i] for i in range(3)])

        for line in lines:
            if line[0] is not None and line[0] == line[1] == line[2]:
                return line[0]

        return None


# ----------------------------------------------------------------------
# AI helper functions operating on raw board data
# ----------------------------------------------------------------------


def clone_board(board: List[List[Optional[str]]]) -> List[List[Optional[str]]]:
    """
    Return a shallow copy of a 3x3 board.
    Cells may be 'X', 'O', or None / other falsy value for empty.
    """
    return [[cell for cell in row] for row in board]


def winner_board(board: List[List[Optional[str]]]) -> Optional[str]:
    """
    Pure function version of winner detection for a given board.

    Returns:
        'X', 'O', or None.
    """
    lines: List[List[Optional[str]]] = []

    # Rows
    lines.extend(board)

    # Columns
    for c in range(3):
        lines.append([board[r][c] for r in range(3)])

    # Diagonals
    lines.append([board[i][i] for i in range(3)])
    lines.append([board[i][2 - i] for i in range(3)])

    for line in lines:
        if line[0] in ("X", "O") and line[0] == line[1] == line[2]:
            return line[0]  # type: ignore[return-value]
    return None


def board_full(board: List[List[Optional[str]]]) -> bool:
    """
    Check if all cells are occupied by 'X' or 'O'.
    """
    for row in board:
        for cell in row:
            if cell not in ("X", "O"):
                return False
    return True


def is_terminal_board(board: List[List[Optional[str]]]) -> bool:
    """
    Check if the given board is in a terminal state (win or tie).
    """
    return winner_board(board) is not None or board_full(board)


def legal_moves_board(board: List[List[Optional[str]]]) -> List[Move]:
    """
    Return all legal moves (row, col) for the given board.
    Uses row-major order so Minimax tie-breaking is deterministic.
    """
    if is_terminal_board(board):
        return []

    moves: List[Move] = []
    for r in range(3):
        for c in range(3):
            if board[r][c] not in ("X", "O"):
                moves.append((r, c))
    return moves


def best_move(board: List[List[Optional[str]]], player: str) -> Move:
    """
    Compute the best move for `player` ('X' or 'O') using Minimax + alpha-beta.

    Args:
        board: 3x3 board as list of lists. Cells: 'X', 'O', or None/empty.
        player: 'X' or 'O'.

    Returns:
        (row, col) of chosen move.

    Scoring:
        +1 : win for `player`
        -1 : loss for `player`
         0 : tie

    Deterministic tie-breaking: moves are considered in row-major order.
    """
    if player not in ("X", "O"):
        raise ValueError("player must be 'X' or 'O'")

    # Make a working copy so we don't mutate the caller's board
    work_board = clone_board(board)
    maximizing_player = player

    def minimax(
        b: List[List[Optional[str]]],
        current: str,
        alpha: int,
        beta: int,
        depth: int,
    ) -> int:
        """
        Recursive Minimax with alpha-beta pruning.

        depth: number of plies from the root. In Tic-Tac-Toe, max depth is 9.
        """
        # Base case: terminal node
        if is_terminal_board(b):
            w = winner_board(b)
            if w == maximizing_player:
                return 1
            if w is None:  # tie
                return 0
            return -1  # opponent win

        if current == maximizing_player:
            # Maximizing branch
            value = -2  # less than minimum possible score
            for (r, c) in legal_moves_board(b):
                # Try move
                b[r][c] = current
                # Recursive call goes one ply deeper
                score = minimax(b, "O" if current == "X" else "X", alpha, beta, depth + 1)
                # Undo move
                b[r][c] = None

                if score > value:
                    value = score

                # Update alpha (best already found for maximizer)
                if value > alpha:
                    alpha = value

                if alpha >= beta:
                    # Prune: remaining children cannot affect parent
                    break

            return value
        else:
            # Minimizing branch
            value = 2  # greater than maximum possible score
            for (r, c) in legal_moves_board(b):
                b[r][c] = current
                score = minimax(b, "O" if current == "X" else "X", alpha, beta, depth + 1)
                b[r][c] = None

                if score < value:
                    value = score

                # Update beta (best already found for minimizer)
                if value < beta:
                    beta = value

                if alpha >= beta:
                    # Prune: remaining children cannot affect parent
                    break

            return value

    best_score = -2
    best_move_choice: Optional[Move] = None

    for (r, c) in legal_moves_board(work_board):
        work_board[r][c] = player
        # Root depth is 1 for the first child
        score = minimax(work_board, "O" if player == "X" else "X", -2, 2, 1)
        work_board[r][c] = None

        # Maximize score; row-major order gives deterministic tie-breaking
        if best_move_choice is None or score > best_score:
            best_score = score
            best_move_choice = (r, c)

    if best_move_choice is None:
        raise ValueError("No legal moves available for best_move")

    return best_move_choice


# ----------------------------------------------------------------------
# Simple self-test suite (runs when engine.py is executed directly)
# ----------------------------------------------------------------------


def _expect(condition: bool, message: str, results: List[str]) -> None:
    """Record a test result based on condition."""
    if condition:
        results.append(f"PASS: {message}")
    else:
        results.append(f"FAIL: {message}")


def _run_tests() -> None:
    results: List[str] = []

    # ---- Engine tests (same behavior as before) ----
    game = TicTacToeEngine()
    _expect(game.get_current_player() == "X", "Initial player is X", results)
    _expect(game.get_winner() is None, "No winner at start", results)
    _expect(not game.is_tie(), "Not a tie at start", results)
    _expect(not game.is_terminal(), "Not terminal at start", results)
    empty_cells = sum(1 for row in game.get_board() for cell in row if cell is None)
    _expect(empty_cells == 9, "Board has 9 empty cells at start", results)

    game.reset()
    move1 = game.play_move(0, 0)
    _expect(move1, "First move (0,0) is legal", results)
    _expect(game.get_board()[0][0] == "X", "X placed at (0,0)", results)
    _expect(game.get_current_player() == "O", "Player alternates to O", results)

    move2 = game.play_move(0, 1)
    _expect(move2, "Second move (0,1) is legal", results)
    _expect(game.get_board()[0][1] == "O", "O placed at (0,1)", results)
    _expect(game.get_current_player() == "X", "Player alternates back to X", results)

    repeat_move = game.play_move(0, 0)
    _expect(not repeat_move, "Cannot play on occupied cell (0,0)", results)

    oob_move_1 = game.play_move(3, 3)
    oob_move_2 = game.play_move(-1, 0)
    _expect(not oob_move_1 and not oob_move_2, "Out-of-bounds moves are illegal", results)

    game.reset()
    # X: (0,0), O: (1,0), X: (0,1), O: (1,1), X: (0,2)
    game.play_move(0, 0)
    game.play_move(1, 0)
    game.play_move(0, 1)
    game.play_move(1, 1)
    game.play_move(0, 2)
    _expect(game.get_winner() == "X", "Row win detected for X", results)
    _expect(game.is_terminal(), "Game is terminal after win", results)
    _expect(game.get_legal_moves() == [], "No legal moves after terminal state", results)
    post_win_move = game.play_move(2, 2)
    _expect(not post_win_move, "Cannot move after game is terminal", results)

    game.reset()
    # Tie sequence:
    # X O X
    # O O X
    # X O X
    tie_moves = [
        (0, 0),  # X
        (1, 1),  # O
        (0, 1),  # X
        (0, 2),  # O
        (2, 0),  # X
        (1, 0),  # O
        (1, 2),  # X
        (2, 1),  # O
        (2, 2),  # X
    ]
    for r, c in tie_moves:
        ok = game.play_move(r, c)
        if not ok:
            _expect(False, f"Move {(r, c)} should be legal during tie sequence", results)
            break

    _expect(game.get_winner() is None, "No winner in tie game", results)
    _expect(game.is_tie(), "Tie is detected", results)
    _expect(game.is_terminal(), "Tie game is terminal", results)
    _expect(game.get_legal_moves() == [], "No legal moves after tie", results)

    game.reset()
    _expect(not game.is_terminal(), "Game not terminal after reset", results)
    _expect(game.get_winner() is None, "No winner after reset", results)
    _expect(not game.is_tie(), "Not a tie after reset", results)
    _expect(game.get_current_player() == "X", "X to move after reset", results)

    # ---- AI tests ----

    # 1) Immediate winning move for X
    board1: List[List[Optional[str]]] = [
        ["X", "X", None],
        ["O", "O", None],
        [None, None, None],
    ]
    bm1 = best_move(board1, "X")
    _expect(bm1 == (0, 2), f"AI (X) takes immediate win at (0,2), got {bm1}", results)

    # 2) Must block O's winning move
    board2: List[List[Optional[str]]] = [
        ["O", "O", None],
        ["X", "X", None],
        [None, None, None],
    ]
    bm2 = best_move(board2, "X")
    _expect(bm2 == (0, 2), f"AI (X) blocks O at (0,2), got {bm2}", results)

    # 3) Perfect play from start: best move is a corner or center
    empty_board: List[List[Optional[str]]] = [
        [None, None, None],
        [None, None, None],
        [None, None, None],
    ]
    bm3 = best_move(empty_board, "X")
    _expect(
        bm3 in [(0, 0), (0, 2), (2, 0), (2, 2), (1, 1)],
        f"AI (X) chooses strong opening, got {bm3}",
        results,
    )

    # 4) Terminal board: best_move should error (no legal moves)
    full_board: List[List[Optional[str]]] = [
        ["X", "O", "X"],
        ["O", "O", "X"],
        ["X", "X", "O"],
    ]
    try:
        _ = best_move(full_board, "X")
        _expect(False, "best_move should fail on full/terminal board", results)
    except ValueError:
        _expect(True, "best_move raises on terminal board", results)

    # Print summary
    total = len(results)
    failures = sum(1 for r in results if r.startswith("FAIL"))
    passes = total - failures

    print("=== TicTacToeEngine + AI self-test ===")
    for line in results:
        print(line)
    print("---------------------------------")
    print(f"Total tests:   {total}")
    print(f"Passed:        {passes}")
    print(f"Failed:        {failures}")
    print("=================================")


if __name__ == "__main__":
    _run_tests()
