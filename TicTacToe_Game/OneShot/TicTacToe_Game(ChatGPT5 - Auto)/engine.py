# engine.py
from __future__ import annotations
from typing import List, Optional, Tuple

Board = List[List[str]]  # 3x3, each cell in {"X","O"," "}

def new_board() -> Board:
    """Return a fresh 3x3 board filled with spaces."""
    return [[" " for _ in range(3)] for _ in range(3)]

def copy_board(board: Board) -> Board:
    return [row[:] for row in board]

def legal_moves(board: Board) -> List[Tuple[int, int]]:
    """Return list of empty positions in deterministic row-major order."""
    moves = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == " ":
                moves.append((r, c))
    return moves

def winner(board: Board) -> Optional[str]:
    """Return 'X' or 'O' if there is a winner, else None."""
    lines = []
    # rows
    for r in range(3):
        lines.append(board[r])
    # cols
    for c in range(3):
        lines.append([board[0][c], board[1][c], board[2][c]])
    # diagonals
    lines.append([board[0][0], board[1][1], board[2][2]])
    lines.append([board[0][2], board[1][1], board[2][0]])
    for line in lines:
        if line[0] != " " and line.count(line[0]) == 3:
            return line[0]
    return None

def is_terminal(board: Board) -> bool:
    """Return True if the game is over (win or full board)."""
    return winner(board) is not None or not any(cell == " " for row in board for cell in row)

def apply_move(board: Board, move: Tuple[int, int], player: str) -> Board:
    r, c = move
    nb = copy_board(board)
    nb[r][c] = player
    return nb

def opponent(player: str) -> str:
    return "O" if player == "X" else "X"

def evaluate_terminal(board: Board, perspective: str) -> int:
    """Score from 'perspective' point of view.
    Returns +1 if perspective has won, -1 if lost, 0 if tie/non-terminal (caller ensures terminal).
    """
    w = winner(board)
    if w is None:
        return 0
    return 1 if w == perspective else -1

def minimax(board: Board, player: str, perspective: str, alpha: int, beta: int, depth: int = 0) -> Tuple[int, Optional[Tuple[int, int]]]:
    """Return (value, move) using minimax with alpha-beta pruning.
    - value is from the perspective player's point of view (the 'perspective' at the root).
    - move is the best move found at this node; None for terminal nodes.
    Tie-breaking: when values are equal, prefer the move with the smallest (row, col) in row-major order.
    Depth increases by 1 each ply; used only for debugging or future enhancements.
    Pruning conditions:
      - Alpha represents the best guaranteed score for the maximizing side encountered so far.
      - Beta represents the best guaranteed score for the minimizing side encountered so far.
      - If alpha >= beta, remaining branches cannot influence the result and are pruned.
    """
    # Terminal node: return the terminal score
    if is_terminal(board):
        return evaluate_terminal(board, perspective), None

    moves = legal_moves(board)  # deterministic order ensures stable tie-breaking

    # Maximize when current player == perspective; otherwise minimize.
    maximizing = (player == perspective)

    best_value = -2 if maximizing else 2  # values are in {-1, 0, 1}
    best_move: Optional[Tuple[int, int]] = None

    for mv in moves:
        child = apply_move(board, mv, player)
        # Recurse for opponent; depth+1 for clarity
        val, _ = minimax(child, opponent(player), perspective, alpha, beta, depth + 1)

        if maximizing:
            if val > best_value or (val == best_value and (best_move is None or mv < best_move)):
                best_value, best_move = val, mv
            # Update alpha for maximizing player and check prune
            alpha = max(alpha, best_value)
            if alpha >= beta:
                # prune remaining siblings
                break
        else:
            if val < best_value or (val == best_value and (best_move is None or mv < best_move)):
                best_value, best_move = val, mv
            # Update beta for minimizing player and check prune
            beta = min(beta, best_value)
            if alpha >= beta:
                # prune remaining siblings
                break

    return best_value, best_move

def best_move(board: Board, player: str) -> Tuple[int, int]:
    """Return the optimal move for 'player' on 'board'.
    Deterministic: no randomness; row-major tie-breaking.
    If no legal moves exist (terminal), returns (-1, -1).
    """
    if is_terminal(board):
        return (-1, -1)
    _, mv = minimax(board, player, perspective=player, alpha=-2, beta=2, depth=0)
    # mv cannot be None because board not terminal, but be safe
    return mv if mv is not None else (-1, -1)
