"""
================================================================================
TIC-TAC-TOE GAME ENGINE
================================================================================

Core game logic and AI implementation for Tic-Tac-Toe.

This module provides:
    - TicTacToe class: Manages game state, moves, and win detection
    - AI functions: Perfect play using Minimax with alpha-beta pruning
    - Helper functions: Terminal state checking, winner detection, legal moves
    - Comprehensive unit tests

Usage:
    from engine import TicTacToe, best_move
    
    # Create game
    game = TicTacToe()
    
    # Make moves
    game.make_move(0, 0)  # X plays
    game.make_move(1, 1)  # O plays
    
    # Get AI move
    ai_move = best_move(game.get_board(), game.current_player)
    game.make_move(ai_move[0], ai_move[1])

Testing:
    Run this file directly to execute all unit tests:
        python engine.py

================================================================================
"""

from typing import List, Optional, Tuple


class TicTacToe:
    """
    Tic-Tac-Toe game engine.
    Handles game state, move validation, and win detection.
    """
    
    def __init__(self):
        """Initialize a new game with an empty 3x3 board."""
        self.board: List[List[Optional[str]]] = [[None for _ in range(3)] for _ in range(3)]
        self.current_player: str = 'X'  # X always goes first
        self.winner: Optional[str] = None
        self.is_game_over: bool = False
    
    def make_move(self, row: int, col: int) -> bool:
        """
        Attempt to make a move at the specified position.
        
        Args:
            row: Row index (0-2)
            col: Column index (0-2)
        
        Returns:
            True if move was successful, False otherwise
        """
        if not self.is_valid_move(row, col):
            return False
        
        self.board[row][col] = self.current_player
        
        # Check for win or tie
        if self._check_win():
            self.winner = self.current_player
            self.is_game_over = True
        elif self._check_tie():
            self.is_game_over = True
        else:
            # Switch players
            self.current_player = 'O' if self.current_player == 'X' else 'X'
        
        return True
    
    def is_valid_move(self, row: int, col: int) -> bool:
        """
        Check if a move is valid.
        
        Args:
            row: Row index (0-2)
            col: Column index (0-2)
        
        Returns:
            True if the move is legal, False otherwise
        """
        if self.is_game_over:
            return False
        
        if row < 0 or row > 2 or col < 0 or col > 2:
            return False
        
        return self.board[row][col] is None
    
    def _check_win(self) -> bool:
        """
        Check if the current player has won.
        
        Returns:
            True if current player has won, False otherwise
        """
        player = self.current_player
        
        # Check rows
        for row in self.board:
            if all(cell == player for cell in row):
                return True
        
        # Check columns
        for col in range(3):
            if all(self.board[row][col] == player for row in range(3)):
                return True
        
        # Check diagonals
        if all(self.board[i][i] == player for i in range(3)):
            return True
        
        if all(self.board[i][2-i] == player for i in range(3)):
            return True
        
        return False
    
    def _check_tie(self) -> bool:
        """
        Check if the game is a tie (board is full with no winner).
        
        Returns:
            True if game is tied, False otherwise
        """
        return all(self.board[row][col] is not None 
                   for row in range(3) for col in range(3))
    
    def get_board(self) -> List[List[Optional[str]]]:
        """
        Get the current board state.
        
        Returns:
            Copy of the current board
        """
        return [row[:] for row in self.board]
    
    def get_winner(self) -> Optional[str]:
        """
        Get the winner of the game.
        
        Returns:
            'X', 'O', or None
        """
        return self.winner
    
    def reset(self) -> None:
        """Reset the game to initial state."""
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.winner = None
        self.is_game_over = False


def run_tests():
    """Run comprehensive tests on the game engine."""
    print("=" * 50)
    print("STARTING TIC-TAC-TOE ENGINE TESTS")
    print("=" * 50)
    
    # Test 1: Import and Initialization
    print("\n[TEST 1] Import and Initialization")
    game = TicTacToe()
    print(f"Board initialized: {game.board}")
    print(f"Current player: {game.current_player}")
    print(f"✓ PASS" if game.current_player == 'X' else "✗ FAIL")
    
    # Test 2: First Player Check
    print("\n[TEST 2] First Player Check")
    print(f"First player is X: {game.current_player == 'X'}")
    print(f"✓ PASS" if game.current_player == 'X' else "✗ FAIL")
    
    # Test 3: Valid Move Test
    print("\n[TEST 3] Valid Move Test")
    result = game.make_move(0, 0)
    print(f"Move result: {result}")
    print(f"Board[0][0]: {game.board[0][0]}")
    print(f"Current player after move: {game.current_player}")
    print(f"✓ PASS" if result and game.board[0][0] == 'X' and game.current_player == 'O' else "✗ FAIL")
    
    # Test 4: Invalid Move Test (same spot)
    print("\n[TEST 4] Invalid Move Test (same spot)")
    result = game.make_move(0, 0)
    print(f"Attempting same spot - result: {result}")
    print(f"✓ PASS" if not result else "✗ FAIL")
    
    # Test 5: Invalid Move Test (out of bounds)
    print("\n[TEST 5] Invalid Move Test (out of bounds)")
    result = game.make_move(3, 3)
    print(f"Out of bounds move - result: {result}")
    print(f"✓ PASS" if not result else "✗ FAIL")
    
    # Test 6: Win Detection (Horizontal)
    print("\n[TEST 6] Win Detection (Horizontal)")
    game.reset()
    game.make_move(0, 0)  # X
    game.make_move(1, 0)  # O
    game.make_move(0, 1)  # X
    game.make_move(1, 1)  # O
    game.make_move(0, 2)  # X (wins)
    print(f"Winner: {game.winner}")
    print(f"Game over: {game.is_game_over}")
    print(f"Board:\n{game.board[0]}\n{game.board[1]}\n{game.board[2]}")
    print(f"✓ PASS" if game.winner == 'X' and game.is_game_over else "✗ FAIL")
    
    # Test 7: Win Detection (Vertical)
    print("\n[TEST 7] Win Detection (Vertical)")
    game.reset()
    game.make_move(0, 0)  # X
    game.make_move(0, 1)  # O
    game.make_move(1, 0)  # X
    game.make_move(1, 1)  # O
    game.make_move(2, 0)  # X (wins)
    print(f"Winner: {game.winner}")
    print(f"Game over: {game.is_game_over}")
    print(f"Board:\n{game.board[0]}\n{game.board[1]}\n{game.board[2]}")
    print(f"✓ PASS" if game.winner == 'X' and game.is_game_over else "✗ FAIL")
    
    # Test 8: Win Detection (Diagonal top-left to bottom-right)
    print("\n[TEST 8] Win Detection (Diagonal \\)")
    game.reset()
    game.make_move(0, 0)  # X
    game.make_move(0, 1)  # O
    game.make_move(1, 1)  # X
    game.make_move(0, 2)  # O
    game.make_move(2, 2)  # X (wins diagonal)
    print(f"Winner: {game.winner}")
    print(f"Game over: {game.is_game_over}")
    print(f"Board:\n{game.board[0]}\n{game.board[1]}\n{game.board[2]}")
    print(f"✓ PASS" if game.winner == 'X' and game.is_game_over else "✗ FAIL")
    
    # Test 9: Win Detection (Diagonal top-right to bottom-left)
    print("\n[TEST 9] Win Detection (Diagonal /)")
    game.reset()
    game.make_move(0, 2)  # X
    game.make_move(0, 0)  # O
    game.make_move(1, 1)  # X
    game.make_move(1, 0)  # O
    game.make_move(2, 0)  # X (wins diagonal)
    print(f"Winner: {game.winner}")
    print(f"Game over: {game.is_game_over}")
    print(f"Board:\n{game.board[0]}\n{game.board[1]}\n{game.board[2]}")
    print(f"✓ PASS" if game.winner == 'X' and game.is_game_over else "✗ FAIL")
    
    # Test 10: Tie Detection
    print("\n[TEST 10] Tie Detection")
    game.reset()
    # Create a tie: X O X / O X X / O X O
    moves = [(0,0), (0,1), (0,2), (1,1), (1,0), (1,2), (2,1), (2,0), (2,2)]
    for row, col in moves:
        game.make_move(row, col)
    print(f"Winner: {game.winner}")
    print(f"Game over: {game.is_game_over}")
    print(f"Board:\n{game.board[0]}\n{game.board[1]}\n{game.board[2]}")
    print(f"✓ PASS" if game.winner is None and game.is_game_over else "✗ FAIL")
    
    # Test 11: Can't Move After Game Over
    print("\n[TEST 11] Can't Move After Game Over")
    result = game.make_move(1, 1)  # Try to move after game is over
    print(f"Move after game over - result: {result}")
    print(f"✓ PASS" if not result else "✗ FAIL")
    
    # Test 12: Reset Functionality
    print("\n[TEST 12] Reset Functionality")
    game.reset()
    print(f"Current player after reset: {game.current_player}")
    print(f"Game over after reset: {game.is_game_over}")
    print(f"Winner after reset: {game.winner}")
    empty_board = all(game.board[r][c] is None for r in range(3) for c in range(3))
    print(f"Board is empty: {empty_board}")
    print(f"✓ PASS" if game.current_player == 'X' and not game.is_game_over and empty_board else "✗ FAIL")
    
    print("\n" + "=" * 50)
    print("TESTS COMPLETE")
    print("=" * 50)


def is_terminal(board: List[List[Optional[str]]]) -> bool:
    """
    Check if the board is in a terminal state (win or tie).
    
    Args:
        board: Current board state
    
    Returns:
        True if game is over, False otherwise
    """
    return winner(board) is not None or len(legal_moves(board)) == 0


def winner(board: List[List[Optional[str]]]) -> Optional[str]:
    """
    Determine the winner of the game.
    
    Args:
        board: Current board state
    
    Returns:
        'X', 'O', or None if no winner yet
    """
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] and row[0] is not None:
            return row[0]
    
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] is not None:
            return board[0][col]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] is not None:
        return board[0][0]
    
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] is not None:
        return board[0][2]
    
    return None


def legal_moves(board: List[List[Optional[str]]]) -> List[Tuple[int, int]]:
    """
    Get all legal moves on the board.
    
    Args:
        board: Current board state
    
    Returns:
        List of (row, col) tuples representing empty positions
    """
    moves = []
    for row in range(3):
        for col in range(3):
            if board[row][col] is None:
                moves.append((row, col))
    return moves


def minimax(board: List[List[Optional[str]]], player: str, is_maximizing: bool, 
            alpha: float, beta: float) -> int:
    """
    Minimax algorithm with alpha-beta pruning.
    
    Args:
        board: Current board state
        player: The AI player ('X' or 'O')
        is_maximizing: True if maximizing player's turn, False if minimizing
        alpha: Alpha value for pruning (best value for maximizer)
        beta: Beta value for pruning (best value for minimizer)
    
    Returns:
        Score: +1 for AI win, -1 for AI loss, 0 for tie
    """
    # Base case: check if terminal state
    if is_terminal(board):
        win = winner(board)
        if win == player:
            return 1  # AI wins
        elif win is None:
            return 0  # Tie
        else:
            return -1  # AI loses
    
    if is_maximizing:
        # Maximizing player (AI) wants highest score
        max_eval = float('-inf')
        for row, col in legal_moves(board):
            # Make move
            board[row][col] = player
            # Recurse to next depth
            eval_score = minimax(board, player, False, alpha, beta)
            # Undo move
            board[row][col] = None
            
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            
            # Alpha-beta pruning: if beta <= alpha, remaining branches won't affect result
            if beta <= alpha:
                break
        
        return max_eval
    else:
        # Minimizing player (opponent) wants lowest score
        min_eval = float('inf')
        opponent = 'O' if player == 'X' else 'X'
        for row, col in legal_moves(board):
            # Make move
            board[row][col] = opponent
            # Recurse to next depth
            eval_score = minimax(board, player, True, alpha, beta)
            # Undo move
            board[row][col] = None
            
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            
            # Alpha-beta pruning: if beta <= alpha, remaining branches won't affect result
            if beta <= alpha:
                break
        
        return min_eval


def best_move(board: List[List[Optional[str]]], player: str) -> Tuple[int, int]:
    """
    Find the best move using minimax with alpha-beta pruning.
    
    Args:
        board: Current board state
        player: The player to move ('X' or 'O')
    
    Returns:
        (row, col) tuple of the best move
    """
    best_score = float('-inf')
    best_move_coords = None
    
    # Iterate through moves in top-left to bottom-right order for deterministic tie-breaking
    for row, col in legal_moves(board):
        # Make move
        board[row][col] = player
        # Evaluate move using minimax
        score = minimax(board, player, False, float('-inf'), float('inf'))
        # Undo move
        board[row][col] = None
        
        # Choose move with highest score (prefer earlier position on ties for determinism)
        if score > best_score:
            best_score = score
            best_move_coords = (row, col)
    
    return best_move_coords


def run_ai_tests():
    """Test the AI with various game scenarios."""
    print("\n" + "=" * 50)
    print("STARTING AI TESTS (MINIMAX + ALPHA-BETA)")
    print("=" * 50)
    
    # Test 1: AI should block immediate win
    print("\n[AI TEST 1] Block Immediate Win")
    board1 = [
        ['X', 'X', None],
        ['O', None, None],
        [None, None, None]
    ]
    move = best_move(board1, 'O')
    print(f"Board:\n{board1[0]}\n{board1[1]}\n{board1[2]}")
    print(f"AI (O) chose: {move}")
    print(f"✓ PASS" if move == (0, 2) else f"✗ FAIL (expected (0, 2))")
    
    # Test 2: AI should take winning move
    print("\n[AI TEST 2] Take Winning Move")
    board2 = [
        ['O', 'O', None],
        ['X', 'X', None],
        [None, None, None]
    ]
    move = best_move(board2, 'O')
    print(f"Board:\n{board2[0]}\n{board2[1]}\n{board2[2]}")
    print(f"AI (O) chose: {move}")
    print(f"✓ PASS" if move == (0, 2) else f"✗ FAIL (expected (0, 2))")
    
    # Test 3: AI should block fork
    print("\n[AI TEST 3] Block Fork")
    board3 = [
        ['X', None, None],
        [None, 'O', None],
        [None, None, 'X']
    ]
    move = best_move(board3, 'O')
    print(f"Board:\n{board3[0]}\n{board3[1]}\n{board3[2]}")
    print(f"AI (O) chose: {move}")
    # Should block at (0,2) or (2,0) to prevent fork
    print(f"✓ PASS" if move in [(0, 2), (2, 0)] else f"✗ FAIL (expected corner block)")
    
    # Test 4: AI should take center on empty board
    print("\n[AI TEST 4] Take Center on Near-Empty Board")
    board4 = [
        ['X', None, None],
        [None, None, None],
        [None, None, None]
    ]
    move = best_move(board4, 'O')
    print(f"Board:\n{board4[0]}\n{board4[1]}\n{board4[2]}")
    print(f"AI (O) chose: {move}")
    print(f"✓ PASS" if move == (1, 1) else f"✗ FAIL (expected (1, 1) for optimal play)")
    
    # Test 5: AI vs AI should always tie
    print("\n[AI TEST 5] AI vs AI Should Tie")
    game = TicTacToe()
    move_count = 0
    while not game.is_game_over and move_count < 9:
        move = best_move(game.get_board(), game.current_player)
        game.make_move(move[0], move[1])
        move_count += 1
    print(f"Final board:\n{game.board[0]}\n{game.board[1]}\n{game.board[2]}")
    print(f"Winner: {game.winner}")
    print(f"Game over: {game.is_game_over}")
    print(f"✓ PASS" if game.winner is None and game.is_game_over else f"✗ FAIL (should tie)")
    
    # Test 6: AI should never lose
    print("\n[AI TEST 6] AI Should Never Lose (Random vs AI)")
    import random
    for test_num in range(3):
        game = TicTacToe()
        print(f"\n  Test {test_num + 1}:")
        while not game.is_game_over:
            if game.current_player == 'X':
                # Random player
                valid_moves = [(r, c) for r in range(3) for c in range(3) 
                              if game.is_valid_move(r, c)]
                if valid_moves:
                    move = random.choice(valid_moves)
                    game.make_move(move[0], move[1])
            else:
                # AI player
                move = best_move(game.get_board(), 'O')
                game.make_move(move[0], move[1])
        
        print(f"  Winner: {game.winner}")
        ai_won_or_tied = game.winner in [None, 'O']
        print(f"  {'✓ PASS' if ai_won_or_tied else '✗ FAIL (AI should never lose)'}")
    
    print("\n" + "=" * 50)
    print("AI TESTS COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    run_tests()
    run_ai_tests()