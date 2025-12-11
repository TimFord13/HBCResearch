import math
from typing import List, Tuple, Optional, Literal

# --- Constants ---
PLAYER_X = "X"
PLAYER_O = "O"
EMPTY = " "

# Define type hints for clarity
Board = List[List[str]]
Player = Literal["X", "O"]
Move = Tuple[int, int]

# --- Public AI Function ---

def find_best_move(board: Board, player: Player) -> Move:
    """
    Finds the best possible move for the given player using
    Minimax with Alpha-Beta Pruning.

    Args:
        board: The current 3x3 game board.
        player: The player whose turn it is ("X" or "O").

    Returns:
        A tuple (row, col) for the best move.
    """
    best_val = -math.inf
    best_move = (-1, -1)
    
    # Iterate through all legal moves.
    # This loop provides the deterministic tie-breaking.
    # The first move found with the highest value is chosen.
    for r, c in get_legal_moves(board):
        # Make the move on a copy of the board
        new_board = [row[:] for row in board]
        new_board[r][c] = player
        
        # Call minimax for the *opponent* (minimizing player)
        # The opponent will try to minimize our score.
        move_val = minimax(
            board=new_board,
            depth=0,
            alpha=-math.inf,
            beta=math.inf,
            is_maximizing=False, # It's opponent's turn
            ai_player=player      # The "ai_player" is who we score for
        )
        
        # Update best move if this move is better
        if move_val > best_val:
            best_val = move_val
            best_move = (r, c)
            
    return best_move

# --- Minimax Implementation ---

def minimax(board: Board, depth: int, alpha: float, beta: float, 
            is_maximizing: bool, ai_player: Player) -> int:
    """
    Recursive Minimax function with Alpha-Beta Pruning.

    Args:
        board: The current board state to evaluate.
        depth: The current depth in the search tree.
        alpha: The best value found so far for the maximizer.
        beta: The best value found so far for the minimizer.
        is_maximizing: True if it's the maximizer's turn, False for minimizer.
        ai_player: The player we are calculating the score *for* (+1 for win).

    Returns:
        The static evaluation score for this board state (1, 0, or -1).
    """
    
    # --- Base Case: Check for terminal state ---
    winner = check_winner(board)
    if winner:
        # Return +1 if the AI we're solving for wins
        # Return -1 if the opponent wins
        return 1 if winner == ai_player else -1
    
    if is_board_full(board):
        # It's a tie
        return 0

    # --- Recursive Step ---
    
    if is_maximizing:
        # MAXIMIZER'S TURN (Our AI)
        best_val = -math.inf
        opponent = PLAYER_O if ai_player == PLAYER_X else PLAYER_X
        
        for r, c in get_legal_moves(board):
            # Make the move on a copy
            new_board = [row[:] for row in board]
            new_board[r][c] = ai_player # Maximizer places *its* mark
            
            # Recurse for the *minimizer*
            val = minimax(new_board, depth + 1, alpha, beta, False, ai_player)
            best_val = max(best_val, val)
            alpha = max(alpha, best_val)
            
            # Alpha-Beta Pruning
            if beta <= alpha:
                break # Beta cut-off
                
        return best_val
        
    else:
        # MINIMIZER'S TURN (Opponent)
        best_val = math.inf
        opponent = PLAYER_O if ai_player == PLAYER_X else PLAYER_X

        for r, c in get_legal_moves(board):
            # Make the move on a copy
            new_board = [row[:] for row in board]
            new_board[r][c] = opponent # Minimizer places *its* mark
            
            # Recurse for the *maximizer*
            val = minimax(new_board, depth + 1, alpha, beta, True, ai_player)
            best_val = min(best_val, val)
            beta = min(beta, best_val)
            
            # Alpha-Beta Pruning
            if beta <= alpha:
                break # Alpha cut-off

        return best_val

# --- Game Rules and State Helpers ---

def get_initial_board() -> Board:
    """Returns a new, empty 3x3 board."""
    return [[EMPTY for _ in range(3)] for _ in range(3)]

def get_legal_moves(board: Board) -> List[Move]:
    """Returns a list of (row, col) tuples for all empty cells."""
    moves = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == EMPTY:
                moves.append((r, c))
    return moves

def check_winner(board: Board) -> Optional[Player]:
    """
    Checks for a win condition.

    Returns:
        "X", "O", or None if no winner.
    """
    # Check rows
    for r in range(3):
        if board[r][0] == board[r][1] == board[r][2] != EMPTY:
            return board[r][0]
            
    # Check columns
    for c in range(3):
        if board[c][0] == board[c][1] == board[c][2] != EMPTY:
            return board[c][0]
            
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != EMPTY:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != EMPTY:
        return board[0][2]
        
    return None

def is_board_full(board: Board) -> bool:
    """Returns True if no EMPTY cells are left."""
    for r in range(3):
        for c in range(3):
            if board[r][c] == EMPTY:
                return False
    return True

def is_terminal(board: Board) -> bool:
    """Returns True if the game is over (win or tie)."""
    return check_winner(board) is not None or is_board_full(board)

# --- Engine Class (State Manager) ---

class TicTacToeEngine:
    """
    Manages the state of a single Tic-Tac-Toe game.
    This is used by the GUI to keep track of the current game.
    """
    def __init__(self):
        self.board = get_initial_board()
        self.current_player: Player = PLAYER_X

    def reset_game(self):
        """Resets the board and current player."""
        self.board = get_initial_board()
        self.current_player = PLAYER_X

    def make_move(self, row: int, col: int) -> bool:
        """
        Attempts to make a move on the board.

        Args:
            row: The row (0-2) of the move.
            col: The column (0-2) of the move.

        Returns:
            True if the move was successful, False if illegal
            (cell occupied or game over).
        """
        if self.board[row][col] == EMPTY and not self.is_game_over():
            self.board[row][col] = self.current_player
            self.toggle_player()
            return True
        return False

    def toggle_player(self):
        """Switches the current player from X to O or O to X."""
        self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X

    def get_winner(self) -> Optional[Player]:
        """Checks for a winner."""
        return check_winner(self.board)

    def is_tie(self) -> bool:
        """Checks for a tie (board full, no winner)."""
        return is_board_full(self.board) and not self.get_winner()

    def is_game_over(self) -> bool:
        """Checks if the game is in a terminal state."""
        return self.get_winner() is not None or is_board_full(self.board)