# Tic-Tac-Toe with Perfect AI

A complete Tic-Tac-Toe implementation featuring a GUI and an unbeatable AI opponent using the Minimax algorithm with alpha-beta pruning.

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)

## 🚀 Quick Start

```bash
python main.py
```

That's it! No installation required beyond Python 3.7+.

## 📋 Requirements

- Python 3.7 or higher
- tkinter (included in standard Python installation)

## 🎮 Game Modes

### 1. Human vs Human
Two players take turns on the same computer.
- X always goes first
- Click any empty cell to play

### 2. Human (X) vs AI (O)
You play as X (blue) against the AI.
- You make the first move
- AI responds automatically after a 300ms delay

### 3. Human (O) vs AI (X)
You play as O (red) against the AI.
- AI makes the first move automatically
- You respond after each AI move

### 4. AI vs AI
Watch two perfect AIs compete (always ends in a tie).
- Moves occur automatically every 300ms
- Great for testing and demonstration

## 🎯 Features

- ✅ **Perfect AI** - Never loses, uses Minimax with alpha-beta pruning
- ✅ **Scoreboard** - Tracks wins and ties across multiple games
- ✅ **Visual Feedback** - Color-coded marks and winning line highlight
- ✅ **Responsive UI** - Non-blocking AI moves using tkinter's `after()`
- ✅ **Multiple Modes** - 4 different play modes via menu
- ✅ **No Dependencies** - Pure Python standard library

## 🎨 User Interface

### Menu Bar

**Game Menu:**
- **New** - Start a new game (resets board, keeps scores)
- **Reset Scores** - Clear all win/tie tallies
- **Quit** - Exit the application

**Mode Menu:**
- Human vs Human
- Human (X) vs AI (O)
- Human (O) vs AI (X)
- AI vs AI

### Visual Elements

- **Blue X** - Player X or first AI
- **Red O** - Player O or second AI
- **Yellow Highlight** - Winning line when game ends
- **Status Display** - Shows current player and mode
- **Scoreboard** - Displays X wins, O wins, and ties

## 🤖 AI Implementation

### Algorithm: Minimax with Alpha-Beta Pruning

The AI uses a recursive game tree search to evaluate all possible future game states:

**Scoring System:**
- `+1` - AI wins
- `-1` - AI loses
- `0` - Tie

**Optimality:**
- The AI explores the complete game tree
- Always chooses the move that maximizes its minimum guaranteed score
- Impossible to beat (you can only tie)

**Alpha-Beta Pruning:**
- Eliminates branches that can't affect the final decision
- Significantly improves performance without sacrificing optimality
- Reduces average time complexity from O(b^d) to O(b^(d/2))

**Deterministic Tie-Breaking:**
- When multiple moves have equal value, the AI chooses the first valid move
- Selection order: top-left to bottom-right (row 0→2, col 0→2)
- Ensures reproducible behavior in identical game states

## 📁 Project Structure

```
tic-tac-toe/
│
├── main.py          # Entry point with documentation
├── engine.py        # Game logic and AI implementation
├── gui.py           # Tkinter GUI interface
└── README.md        # This file
```

### main.py
- Application entry point
- Comprehensive documentation
- Error handling for launch

### engine.py
- `TicTacToe` class - Core game logic
- Board state management
- Move validation
- Win/tie detection
- AI functions:
  - `best_move()` - Find optimal move
  - `minimax()` - Recursive tree search
  - `is_terminal()` - Check game end
  - `winner()` - Determine winner
  - `legal_moves()` - Get valid moves
- Comprehensive unit tests (run with `python engine.py`)

### gui.py
- `TicTacToeGUI` class - User interface
- Menu bar and controls
- Board rendering
- Event handling
- Score tracking
- Mode management

## 🧪 Testing

Run the engine tests:

```bash
python engine.py
```

This executes comprehensive tests including:
- Board initialization
- Move validation
- Win detection (all directions)
- Tie detection
- AI decision quality
- AI vs AI verification
- Random player vs AI (AI never loses)

Expected output: All tests should show `✓ PASS`

## 🎲 Game Rules

1. Board is a 3×3 grid
2. X always makes the first move
3. Players alternate turns
4. First to get 3 marks in a row (horizontal, vertical, or diagonal) wins
5. If all 9 cells are filled with no winner, the game is a tie
6. Illegal moves (occupied cells, out of bounds) are automatically prevented

## ⚠️ Known Limitations

1. **No Difficulty Levels** - AI always plays perfectly (cannot be beaten)
2. **No Save/Load** - Game state is not persisted between sessions
3. **No Customization** - Colors and board size are fixed
4. **No Undo** - Cannot take back moves
5. **No Persistent Scores** - Scoreboard resets when app closes
6. **AI vs AI Always Ties** - Both AIs play perfectly

## 🛠️ Development

### Adding New Features

The modular design makes it easy to extend:

- **New game modes**: Modify `gui.py` mode menu and add handlers
- **Board size**: Update `engine.py` board dimensions and win conditions
- **Difficulty levels**: Add imperfect AI in `engine.py` (e.g., random moves with probability)
- **Save/load**: Add serialization to `engine.py` and file menu to `gui.py`

### Code Quality

- Type hints for key functions
- Comprehensive docstrings
- Separation of concerns (engine/GUI)
- No global state
- Unit tests included

## 📝 License

MIT License - Feel free to use, modify, and distribute.

## 🤝 Contributing

This is an educational project demonstrating clean code architecture and AI implementation. Feel free to fork and extend!

## 📚 Learning Resources

**Topics Demonstrated:**
- Game tree search algorithms (Minimax)
- Alpha-beta pruning optimization
- GUI programming with Tkinter
- Object-oriented design
- Separation of concerns
- Unit testing
- Type hints and documentation

**Suggested Extensions:**
- Implement different board sizes (4×4, 5×5)
- Add network multiplayer
- Create difficulty levels
- Add move history and replay
- Implement other games (Connect Four, Checkers)

---

**Enjoy the game! 🎮** (But remember, you can't beat the AI! 😄)