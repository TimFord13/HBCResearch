from typing import List, Optional, Tuple

# --- HELPER FUNCTIONS ---

def check_winner(board: List[List[Optional[str]]]) -> Optional[str]:
    """Returns the winner ('X' or 'O') or None."""
    line = get_winning_line(board)
    if line:
        return board[line[0][0]][line[0][1]]
    return None

def get_winning_line(board: List[List[Optional[str]]]) -> Optional[List[Tuple[int, int]]]:
    """Returns the list of coordinates that form a win, or None."""
    # Rows
    for r in range(3):
        if board[r][0] == board[r][1] == board[r][2] and board[r][0] is not None:
            return [(r, 0), (r, 1), (r, 2)]
    # Columns
    for c in range(3):
        if board[0][c] == board[1][c] == board[2][c] and board[0][c] is not None:
            return [(0, c), (1, c), (2, c)]
    # Diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] is not None:
        return [(0, 0), (1, 1), (2, 2)]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] is not None:
        return [(0, 2), (1, 1), (2, 0)]
    
    return None

def is_board_full(board: List[List[Optional[str]]]) -> bool:
    return all(all(cell is not None for cell in row) for row in board)

def get_legal_moves(board: List[List[Optional[str]]]) -> List[Tuple[int, int]]:
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]

# --- AI ENGINE ---

def best_move(board: List[List[Optional[str]]], player: str) -> Tuple[int, int]:
    opponent = 'O' if player == 'X' else 'X'

    def minimax(current_board, depth, is_maximizing, alpha, beta):
        winner = check_winner(current_board)
        if winner == player: return 1
        if winner == opponent: return -1
        if is_board_full(current_board): return 0

        if is_maximizing:
            max_eval = -float('inf')
            for r, c in get_legal_moves(current_board):
                current_board[r][c] = player
                eval = minimax(current_board, depth + 1, False, alpha, beta)
                current_board[r][c] = None
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in get_legal_moves(current_board):
                current_board[r][c] = opponent
                eval = minimax(current_board, depth + 1, True, alpha, beta)
                current_board[r][c] = None
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    best_val = -float('inf')
    best_move_found = None
    
    for r, c in get_legal_moves(board):
        board[r][c] = player
        move_val = minimax(board, 0, False, -float('inf'), float('inf'))
        board[r][c] = None
        if move_val > best_val:
            best_val = move_val
            best_move_found = (r, c)

    return best_move_found

# --- GAME CLASS ---

class TicTacToe:
    def __init__(self):
        self.board: List[List[Optional[str]]] = [[None for _ in range(3)] for _ in range(3)]
        self.current_player: str = 'X'
        self.winner: Optional[str] = None
        self.winning_line: Optional[List[Tuple[int, int]]] = None
        self.is_game_over: bool = False

    def make_move(self, row: int, col: int) -> bool:
        if self.is_game_over or self.board[row][col] is not None:
            return False

        self.board[row][col] = self.current_player
        
        # Check Win/Tie
        line = get_winning_line(self.board)
        if line:
            self.winner = self.current_player
            self.winning_line = line
            self.is_game_over = True
        elif is_board_full(self.board):
            self.winner = None
            self.is_game_over = True
        else:
            self.current_player = 'O' if self.current_player == 'X' else 'X'

        return True

    def reset(self):
        self.__init__()