"""
Dynamic Maze Generation + Pathfinding Race
==========================================

A Python desktop application for visualizing maze generation and pathfinding algorithms.

RUNNING:
    python main.py

FEATURES:
- Maze Generation: Randomized Prim's Algorithm, Randomized Kruskal's Algorithm
- Pathfinding: BFS, DFS, Dijkstra, A* (Manhattan heuristic)
- Real-time visualization with step-by-step animation
- Performance metrics: runtime, nodes explored, FPS, path optimality
- Deterministic generation with seeds

MENU GUIDE:
    Game/Run:
        - New Maze: Generate a new maze with selected algorithm
        - Start Race: Begin pathfinding race with enabled algorithms
        - Pause/Resume: Toggle animation
        - Step: Advance one step when paused
        - Reset Stats: Clear metrics
        - Quit: Exit application
    
    Maze:
        - Algorithm: Choose Prim's or Kruskal's
        - Grid Size: 21x21, 31x31, 41x41, 61x61
        - Set Seed: Enter numeric seed for reproducibility
        - Clear Seed: Use random generation
    
    Pathfinding:
        - Enable/Disable: BFS, DFS, Dijkstra, A*
    
    Speed:
        - Steps per Frame: 1-100
        - Frame Delay: 1-100ms
    
    View:
        - Toggle various overlays
        - Export CSV: Save metrics to file

ALGORITHMS:
    Prim's: Frontier-based maze generation starting from random cell
    Kruskal's: Union-find based generation treating cells as disjoint sets
    BFS: Breadth-first search, guarantees shortest path
    DFS: Depth-first search, may find non-optimal paths
    Dijkstra: Optimal pathfinding with uniform weights
    A*: Optimal pathfinding with Manhattan distance heuristic

METRICS:
    - Explored Nodes: Number of cells examined
    - Runtime (ms): Wall-clock time for algorithm
    - Path Length: Number of steps in solution
    - Optimality: Whether path length equals Dijkstra's result

DETERMINISM:
    When a seed is set, all random choices use the seeded RNG.
    Tie-breaking order: up, right, down, left for neighbors.
    Equal priority in Dijkstra/A* broken by (row, col) order.

KEYBOARD SHORTCUTS:
    N: New Maze
    R: Start/Resume Race
    P: Pause
    S: Step
    ESC: Quit
"""

from gui_module import MazeApp
import tkinter as tk


def main():
    root = tk.Tk()
    app = MazeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
