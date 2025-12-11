# search.py
"""
Stepwise Search API

Provides incremental pathfinding algorithms with uniform interface:
- BFS (Breadth-First Search)
- DFS (Depth-First Search)
- Dijkstra's Algorithm
- A* Search

All algorithms support step-by-step execution for visualization.
"""

import time
from typing import Tuple, List, Dict, Optional, Set
from collections import deque
import heapq
from enum import Enum
from maze import Maze, CellType


class SearchStatus(Enum):
    """Status of search algorithm execution."""
    RUNNING = "running"
    FOUND = "found"
    NO_PATH = "no_path"


class SearchAlgorithm:
    """Base class for search algorithms with uniform interface."""
    
    def __init__(self, maze: Maze, start: Tuple[int, int], goal: Tuple[int, int]):
        """
        Initialize search algorithm.
        
        Args:
            maze: Maze object to search
            start: Start cell (row, col) in cell coordinates
            goal: Goal cell (row, col) in cell coordinates
        """
        self.maze = maze
        self.start = start
        self.goal = goal
        
        # Status tracking
        self.status = SearchStatus.RUNNING
        self.path: List[Tuple[int, int]] = []
        
        # Metrics
        self.explored_count = 0
        self.start_time = time.perf_counter()
        self.end_time: Optional[float] = None
        
        # Internal structures (to be set by subclasses)
        self.frontier: Set[Tuple[int, int]] = set()
        self.visited: Set[Tuple[int, int]] = set()
        self.parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {}
    
    def _cell_to_grid(self, cell_r: int, cell_c: int) -> Tuple[int, int]:
        """Convert cell coordinates to grid coordinates."""
        return (2 * cell_r + 1, 2 * cell_c + 1)
    
    def _get_neighbors(self, cell: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get valid neighbors of a cell in stable order (up, right, down, left).
        
        Args:
            cell: Cell position (row, col)
            
        Returns:
            List of neighboring cells that are reachable
        """
        r, c = cell
        neighbors = []
        
        # Stable order: up, right, down, left
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            
            # Check bounds
            if 0 <= nr < self.maze.cell_rows and 0 <= nc < self.maze.cell_cols:
                # Check if there's a passage (wall removed) between cells
                cell_grid = self._cell_to_grid(r, c)
                neighbor_grid = self._cell_to_grid(nr, nc)
                wall_r = (cell_grid[0] + neighbor_grid[0]) // 2
                wall_c = (cell_grid[1] + neighbor_grid[1]) // 2
                
                if self.maze.is_passage(wall_r, wall_c):
                    neighbors.append((nr, nc))
        
        return neighbors
    
    def _reconstruct_path(self) -> List[Tuple[int, int]]:
        """
        Reconstruct path from start to goal using parent pointers.
        
        Returns:
            List of cells from start to goal
        """
        if self.goal not in self.parent:
            return []
        
        path = []
        current = self.goal
        
        while current is not None:
            path.append(current)
            current = self.parent[current]
        
        path.reverse()
        return path
    
    def step(self) -> SearchStatus:
        """
        Advance algorithm by one exploration step.
        
        Returns:
            Current status of the search
        """
        raise NotImplementedError("Subclasses must implement step()")
    
    def is_done(self) -> bool:
        """
        Check if search is complete.
        
        Returns:
            True if search has finished (found or no path)
        """
        return self.status != SearchStatus.RUNNING
    
    def get_path(self) -> List[Tuple[int, int]]:
        """
        Get the path from start to goal.
        
        Returns:
            List of cells from start to goal, empty if no path found
        """
        return self.path
    
    def get_metrics(self) -> Dict[str, any]:
        """
        Get search metrics.
        
        Returns:
            Dictionary with:
            - explored: number of cells explored
            - runtime_ms: runtime in milliseconds
            - path_len: length of path (0 if no path)
        """
        if self.end_time is None:
            runtime = (time.perf_counter() - self.start_time) * 1000
        else:
            runtime = (self.end_time - self.start_time) * 1000
        
        return {
            'explored': self.explored_count,
            'runtime_ms': runtime,
            'path_len': len(self.path)
        }


class BFS(SearchAlgorithm):
    """Breadth-First Search - uniform cost, explores by distance from start."""
    
    def __init__(self, maze: Maze, start: Tuple[int, int], goal: Tuple[int, int]):
        super().__init__(maze, start, goal)
        
        # BFS uses a queue for frontier
        self.queue = deque([start])
        self.frontier = {start}
        self.visited = set()
        self.parent = {start: None}
    
    def step(self) -> SearchStatus:
        """Advance BFS by one step."""
        if self.status != SearchStatus.RUNNING:
            return self.status
        
        if not self.queue:
            self.status = SearchStatus.NO_PATH
            self.end_time = time.perf_counter()
            return self.status
        
        # Dequeue next cell
        current = self.queue.popleft()
        self.frontier.discard(current)
        
        # Mark as visited
        if current in self.visited:
            return self.status
        
        self.visited.add(current)
        self.explored_count += 1
        
        # Check if goal reached
        if current == self.goal:
            self.status = SearchStatus.FOUND
            self.path = self._reconstruct_path()
            self.end_time = time.perf_counter()
            return self.status
        
        # Add neighbors to queue
        for neighbor in self._get_neighbors(current):
            if neighbor not in self.visited and neighbor not in self.frontier:
                self.queue.append(neighbor)
                self.frontier.add(neighbor)
                self.parent[neighbor] = current
        
        return self.status


class DFS(SearchAlgorithm):
    """Depth-First Search - explores deeply before backtracking."""
    
    def __init__(self, maze: Maze, start: Tuple[int, int], goal: Tuple[int, int]):
        super().__init__(maze, start, goal)
        
        # DFS uses a stack for frontier
        self.stack = [start]
        self.frontier = {start}
        self.visited = set()
        self.parent = {start: None}
    
    def step(self) -> SearchStatus:
        """Advance DFS by one step."""
        if self.status != SearchStatus.RUNNING:
            return self.status
        
        if not self.stack:
            self.status = SearchStatus.NO_PATH
            self.end_time = time.perf_counter()
            return self.status
        
        # Pop next cell
        current = self.stack.pop()
        self.frontier.discard(current)
        
        # Mark as visited
        if current in self.visited:
            return self.status
        
        self.visited.add(current)
        self.explored_count += 1
        
        # Check if goal reached
        if current == self.goal:
            self.status = SearchStatus.FOUND
            self.path = self._reconstruct_path()
            self.end_time = time.perf_counter()
            return self.status
        
        # Add neighbors to stack (reverse order for stable exploration)
        neighbors = self._get_neighbors(current)
        for neighbor in reversed(neighbors):  # Reverse so first neighbor is processed first
            if neighbor not in self.visited and neighbor not in self.frontier:
                self.stack.append(neighbor)
                self.frontier.add(neighbor)
                self.parent[neighbor] = current
        
        return self.status


class Dijkstra(SearchAlgorithm):
    """Dijkstra's Algorithm - finds shortest path with non-negative edge weights."""
    
    def __init__(self, maze: Maze, start: Tuple[int, int], goal: Tuple[int, int]):
        super().__init__(maze, start, goal)
        
        # Priority queue: (cost, counter, cell)
        # Counter for stable tie-breaking
        self.heap = [(0, 0, start)]
        self.counter = 1
        self.frontier = {start}
        self.visited = set()
        self.parent = {start: None}
        self.g_score = {start: 0}  # Cost from start to cell
    
    def step(self) -> SearchStatus:
        """Advance Dijkstra by one step."""
        if self.status != SearchStatus.RUNNING:
            return self.status
        
        if not self.heap:
            self.status = SearchStatus.NO_PATH
            self.end_time = time.perf_counter()
            return self.status
        
        # Pop cell with lowest cost
        cost, _, current = heapq.heappop(self.heap)
        self.frontier.discard(current)
        
        # Skip if already visited
        if current in self.visited:
            return self.status
        
        self.visited.add(current)
        self.explored_count += 1
        
        # Check if goal reached
        if current == self.goal:
            self.status = SearchStatus.FOUND
            self.path = self._reconstruct_path()
            self.end_time = time.perf_counter()
            return self.status
        
        # Process neighbors
        for neighbor in self._get_neighbors(current):
            if neighbor in self.visited:
                continue
            
            # Uniform cost of 1 for each move
            tentative_g = self.g_score[current] + 1
            
            if neighbor not in self.g_score or tentative_g < self.g_score[neighbor]:
                self.g_score[neighbor] = tentative_g
                self.parent[neighbor] = current
                heapq.heappush(self.heap, (tentative_g, self.counter, neighbor))
                self.counter += 1
                self.frontier.add(neighbor)
        
        return self.status


class AStar(SearchAlgorithm):
    """A* Search - uses heuristic (Manhattan distance) for efficient pathfinding."""
    
    def __init__(self, maze: Maze, start: Tuple[int, int], goal: Tuple[int, int]):
        super().__init__(maze, start, goal)
        
        # Priority queue: (f_score, counter, cell)
        # f_score = g_score + h_score
        self.heap = [(self._heuristic(start), 0, start)]
        self.counter = 1
        self.frontier = {start}
        self.visited = set()
        self.parent = {start: None}
        self.g_score = {start: 0}  # Cost from start
        self.f_score = {start: self._heuristic(start)}  # Estimated total cost
    
    def _heuristic(self, cell: Tuple[int, int]) -> int:
        """
        Manhattan distance heuristic.
        
        Args:
            cell: Cell position
            
        Returns:
            Manhattan distance to goal
        """
        return abs(cell[0] - self.goal[0]) + abs(cell[1] - self.goal[1])
    
    def step(self) -> SearchStatus:
        """Advance A* by one step."""
        if self.status != SearchStatus.RUNNING:
            return self.status
        
        if not self.heap:
            self.status = SearchStatus.NO_PATH
            self.end_time = time.perf_counter()
            return self.status
        
        # Pop cell with lowest f_score
        _, _, current = heapq.heappop(self.heap)
        self.frontier.discard(current)
        
        # Skip if already visited
        if current in self.visited:
            return self.status
        
        self.visited.add(current)
        self.explored_count += 1
        
        # Check if goal reached
        if current == self.goal:
            self.status = SearchStatus.FOUND
            self.path = self._reconstruct_path()
            self.end_time = time.perf_counter()
            return self.status
        
        # Process neighbors
        for neighbor in self._get_neighbors(current):
            if neighbor in self.visited:
                continue
            
            # Uniform cost of 1 for each move
            tentative_g = self.g_score[current] + 1
            
            if neighbor not in self.g_score or tentative_g < self.g_score[neighbor]:
                self.g_score[neighbor] = tentative_g
                h = self._heuristic(neighbor)
                f = tentative_g + h
                self.f_score[neighbor] = f
                self.parent[neighbor] = current
                heapq.heappush(self.heap, (f, self.counter, neighbor))
                self.counter += 1
                self.frontier.add(neighbor)
        
        return self.status


# ============================================================================
# TESTS
# ============================================================================

def test_path_validity(algorithm_class, name: str):
    """Test that path is contiguous and within bounds."""
    print(f"\nTesting {name}...")
    
    # Create simple maze
    maze = Maze(5, 5, seed=42)
    maze.generate_prim()
    
    start = (0, 0)
    goal = (4, 4)
    
    # Run algorithm to completion
    algo = algorithm_class(maze, start, goal)
    steps = 0
    max_steps = 1000  # Prevent infinite loops
    
    while not algo.is_done() and steps < max_steps:
        algo.step()
        steps += 1
    
    path = algo.get_path()
    metrics = algo.get_metrics()
    
    print(f"  Status: {algo.status.value}")
    print(f"  Steps: {steps}")
    print(f"  Explored: {metrics['explored']}")
    print(f"  Path length: {metrics['path_len']}")
    print(f"  Runtime: {metrics['runtime_ms']:.3f}ms")
    
    if algo.status == SearchStatus.FOUND:
        # Validate path
        assert len(path) > 0, f"{name}: Path is empty"
        assert path[0] == start, f"{name}: Path doesn't start at start"
        assert path[-1] == goal, f"{name}: Path doesn't end at goal"
        
        # Check path is contiguous
        for i in range(len(path) - 1):
            curr = path[i]
            next_cell = path[i + 1]
            
            # Check bounds
            assert 0 <= curr[0] < maze.cell_rows, f"{name}: Path cell out of bounds"
            assert 0 <= curr[1] < maze.cell_cols, f"{name}: Path cell out of bounds"
            
            # Check adjacent
            dist = abs(curr[0] - next_cell[0]) + abs(curr[1] - next_cell[1])
            assert dist == 1, f"{name}: Path not contiguous at {curr} -> {next_cell}"
            
            # Verify cells are neighbors (passage exists)
            neighbors = algo._get_neighbors(curr)
            assert next_cell in neighbors, f"{name}: No passage from {curr} to {next_cell}"
        
        print(f"  ✓ Path is valid and contiguous")
    else:
        print(f"  ✓ No path found (as expected for disconnected regions)")


def test_all_algorithms():
    """Test all search algorithms."""
    print("="*60)
    print("SEARCH ALGORITHM TESTS")
    print("="*60)
    
    algorithms = [
        (BFS, "BFS"),
        (DFS, "DFS"),
        (Dijkstra, "Dijkstra"),
        (AStar, "A*")
    ]
    
    for algo_class, name in algorithms:
        test_path_validity(algo_class, name)
    
    print("\n" + "="*60)
    print("All tests passed!")
    print("="*60)


def compare_algorithms():
    """Compare performance of all algorithms on same maze."""
    print("\n" + "="*60)
    print("ALGORITHM COMPARISON")
    print("="*60 + "\n")
    
    # Create maze
    maze = Maze(10, 10, seed=123)
    maze.generate_kruskal()
    
    print("Maze generated (10×10 with Kruskal's):")
    maze.print_maze()
    
    start = (0, 0)
    goal = (9, 9)
    
    algorithms = [
        (BFS, "BFS"),
        (DFS, "DFS"),
        (Dijkstra, "Dijkstra"),
        (AStar, "A*")
    ]
    
    print(f"\nSearching from {start} to {goal}:\n")
    print(f"{'Algorithm':<12} {'Explored':<10} {'Path Len':<10} {'Runtime (ms)':<15}")
    print("-" * 50)
    
    for algo_class, name in algorithms:
        algo = algo_class(maze, start, goal)
        
        # Run to completion
        while not algo.is_done():
            algo.step()
        
        metrics = algo.get_metrics()
        
        print(f"{name:<12} {metrics['explored']:<10} {metrics['path_len']:<10} {metrics['runtime_ms']:<15.3f}")


def test_step_by_step():
    """Demonstrate step-by-step execution."""
    print("\n" + "="*60)
    print("STEP-BY-STEP EXECUTION DEMO (BFS)")
    print("="*60 + "\n")
    
    maze = Maze(3, 3, seed=1)
    maze.generate_prim()
    
    print("Maze:")
    maze.print_maze()
    
    start = (0, 0)
    goal = (2, 2)
    
    bfs = BFS(maze, start, goal)
    
    step_num = 0
    print(f"\n{'Step':<6} {'Current':<12} {'Frontier Size':<15} {'Visited Size':<15} {'Status'}")
    print("-" * 65)
    
    while not bfs.is_done():
        frontier_size = len(bfs.frontier)
        visited_size = len(bfs.visited)
        status = bfs.status.value
        
        if bfs.queue:
            current = bfs.queue[0]
        else:
            current = "None"
        
        print(f"{step_num:<6} {str(current):<12} {frontier_size:<15} {visited_size:<15} {status}")
        
        bfs.step()
        step_num += 1
    
    print(f"{step_num:<6} {'Done':<12} {len(bfs.frontier):<15} {len(bfs.visited):<15} {bfs.status.value}")
    
    print(f"\nFinal path: {bfs.get_path()}")
    print(f"Metrics: {bfs.get_metrics()}")


if __name__ == "__main__":
    test_all_algorithms()
    compare_algorithms()
    test_step_by_step()