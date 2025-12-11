"""
=====================================================================
Dynamic Maze Generation & Pathfinding Race
=====================================================================

This application generates random mazes and visualizes a real-time
"race" between four pathfinding algorithms: Breadth-First Search (BFS),
Depth-First Search (DFS), Dijkstra's Algorithm, and A* (A-Star).

---------------------------------------------------------------------
How to Run
---------------------------------------------------------------------
1. Ensure you have Python 3.10+ installed.
2. Save all four files (main.py, gui.py, maze.py, search.py) in
   the same directory.
3. Run the application from your terminal:
   $ python main.py

---------------------------------------------------------------------
Menu Guide
---------------------------------------------------------------------
[Game]
- New Maze: Generates a new maze with the current settings.
- Start Race: Begins the pathfinding race from the start to goal.
- Pause/Resume: Pauses or resumes the current generation/race.
- Step: (When paused) Advances the simulation by one step.
- Reset Stats: Clears the metrics from the last race.
- Export CSV: Saves the metrics from the last completed race to
  a CSV file in the working directory.
- Quit: Exits the application.

[Maze]
- Algorithm:
  - Prim's: Randomized Prim's algorithm. Tends to have many
    short branching paths.
  - Kruskal's: Randomized Kruskal's algorithm. Tends to have
    longer, more winding paths.
- Grid Size: Select from preset grid dimensions (e.g., 21x21).
- Seed:
  - Set...: Enter a specific seed for reproducible maze
    generation.
  - Clear: Uses a random (time-based) seed.

[Pathfinding]
- Enable/Disable {BFS, DFS, Dijkstra, A*}: Toggles which
  algorithms participate in the race.

[Speed]
- Steps per Frame: Slider controlling how many logical steps
  (e.g., visiting one node) are processed per visual frame.
- Frame Delay (ms): Slider controlling the millisecond delay
  between each visual frame, slowing down the animation.

[View]
- Show Overlays For...: Selects which algorithm's internal
  state (frontier, visited) to visualize during the race.
- Show Winning Path(s): Toggles the display of the final
  found paths after the race is complete.

---------------------------------------------------------------------
Algorithm Notes
---------------------------------------------------------------------
[Maze Generation]
- Randomized Prim's: Starts from a cell and grows the maze
  like a tree, adding random adjacent "frontier" cells.
- Randomized Kruskal's: Starts with a grid of isolated cells
  and randomly connects them by breaking down walls, using a
  Disjoint-Set (Union-Find) data structure to prevent cycles.

[Pathfinding]
- BFS: Explores layer by layer. Guarantees the shortest path
  (by number of steps) on unweighted grids.
- DFS: Explores as deeply as possible down one path before
  backtracking. Does not guarantee an optimal path.
- Dijkstra: Explores based on the lowest cumulative cost from
  the start. GuaranteES the shortest path. For this
  uniform-cost grid, it behaves similarly to BFS.
- A*: A "smarter" version of Dijkstra. It uses a heuristic
  (Manhattan distance) to guess the distance to the goal,
  prioritizing nodes that are both cheap to get to and
  appear close to the end. It guarantees the shortest path
  and explores fewer or equal nodes than Dijkstra.

---------------------------------------------------------------------
Metrics & Determinism
---------------------------------------------------------------------
- Runtime (ms): Wall-clock time from when an algorithm
  starts to when it finds the goal or exhausts its search.
- Explored Nodes: The number of unique nodes popped from the
  frontier (e.g., visited/expanded).
- Path Length: The number of cells in the final path,
  including start and goal.
- Optimality: Compares an algorithm's path length to
  Dijkstra's path length (which is the ground truth).
- Determinism: When a "Seed" is set, the maze generation
  (Prim's/Kruskal's) is 100% reproducible. Pathfinding tie-
  breaking (neighbor order, priority queue) is also
  deterministic, ensuring identical metrics for the same
  maze across runs.

"""

import gui
import sys

if __name__ == "__main__":
    if sys.version_info < (3, 10):
        print("Error: This application requires Python 3.10 or newer.")
        sys.exit(1)
        
    try:
        app = gui.MazeApp()
        app.mainloop()
    except ImportError as e:
        print(f"Error: Failed to import a required module.")
        print(f"Please ensure main.py, gui.py, maze.py, and search.py are all in the same directory.")
        print(f"Details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")