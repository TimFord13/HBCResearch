import time
import heapq
from collections import deque
from typing import List, Tuple, Dict, Set, Optional, Any

# Import maze/grid definition
try:
    from maze import Grid, CellType
except ImportError:
    print("Error: Could not import maze.py.")
    # Define dummy classes for linting/type hints if maze.py is missing
    class CellType:
        WALL = 1
        PASSAGE = 2
    class Grid:
        def __init__(self, r, c, s):
            self.rows = r
            self.cols = c
            self.grid = []
            self.start = (1,1)
            self.goal = (r-2, c-2)
        def is_valid(self, r, c): return False
        def get_neighbors(self, r, c, step=1): return []


class SearchAlgorithm:
    """
    Abstract base class for pathfinding algorithms.
    Defines the common interface (step, get_path, etc.).
    """
    
    def __init__(self, grid: Grid, start: Tuple[int, int], goal: Tuple[int, int]):
        self.grid = grid
        self.start = start
        self.goal = goal
        
        self.parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
        self.visited: Set[Tuple[int, int]] = set() # For visualization
        
        self.current: Optional[Tuple[int, int]] = None
        self.is_finished = False
        self.path_found = False
        
        self.start_time = 0.0
        self.end_time = 0.0
        self.explored_nodes = 0

    def start_timer(self):
        self.start_time = time.perf_counter()

    def stop_timer(self):
        if self.end_time == 0.0: # Only stop once
            self.end_time = time.perf_counter()

    def step(self):
        """Perform one step of the search (e.g., visit one node)."""
        raise NotImplementedError

    def _get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """
        Get valid, passable neighbors in deterministic order (U, R, D, L).
        """
        neighbors = []
        # (dr, dc)
        # Up, Right, Down, Left
        for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            nr, nc = r + dr, c + dc
            if (self.grid.is_valid(nr, nc) and
                self.grid.grid[nr][nc] != CellType.WALL):
                neighbors.append((nr, nc))
        return neighbors

    def _reconstruct_path(self) -> List[Tuple[int, int]]:
        """Backtrack from goal to start using the parent map."""
        if not self.path_found:
            return []
            
        path = []
        curr = self.goal
        while curr is not None:
            path.append(curr)
            curr = self.parent.get(curr)
            
        return path[::-1] # Reverse to get start -> goal

    def get_path(self) -> List[Tuple[int, int]]:
        """Public method to get the final path."""
        return self._reconstruct_path()

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this algorithm."""
        run_time = (self.end_time if self.is_finished else time.perf_counter())
        return {
            "explored_nodes": self.explored_nodes,
            "runtime_ms": (run_time - self.start_time) * 1000.0,
            "path_found": self.path_found,
        }

    def get_state_overlay(self) -> Dict[str, Any]:
        """Get the current internal state for visualization."""
        # This is overridden by algos that have a frontier
        return {
            'visited': self.visited,
            'frontier': set(),
            'current': self.current
        }

# ------------------------------------------------------------------
# Breadth-First Search (BFS)
# ------------------------------------------------------------------

class BFS(SearchAlgorithm):
    
    def __init__(self, grid: Grid, start: Tuple[int, int], goal: Tuple[int, int]):
        super().__init__(grid, start, goal)
        self.frontier: deque[Tuple[int, int]] = deque([start])
        self.visited.add(start) # For BFS, visited = in_frontier or explored

    def step(self):
        if self.is_finished or not self.frontier:
            self.is_finished = True
            if not self.path_found:
                self.stop_timer() # Stop timer if no path
            return

        # 1. Get next node
        self.current = self.frontier.popleft()
        self.explored_nodes += 1
        
        # 2. Check for goal
        if self.current == self.goal:
            self.is_finished = True
            self.path_found = True
            self.stop_timer()
            return
            
        # 3. Explore neighbors
        for neighbor in self._get_neighbors(*self.current):
            if neighbor not in self.visited:
                self.visited.add(neighbor)
                self.parent[neighbor] = self.current
                self.frontier.append(neighbor)

    def get_state_overlay(self) -> Dict[str, Any]:
        return {
            'visited': self.visited - set(self.frontier),
            'frontier': set(self.frontier),
            'current': self.current
        }

# ------------------------------------------------------------------
# Depth-First Search (DFS)
# ------------------------------------------------------------------

class DFS(SearchAlgorithm):
    
    def __init__(self, grid: Grid, start: Tuple[int, int], goal: Tuple[int, int]):
        super().__init__(grid, start, goal)
        self.frontier: List[Tuple[int, int]] = [start] # Use list as stack
        self.visited.add(start)

    def step(self):
        if self.is_finished or not self.frontier:
            self.is_finished = True
            if not self.path_found:
                self.stop_timer()
            return

        # 1. Get next node
        self.current = self.frontier.pop()
        self.explored_nodes += 1
        
        # 2. Check for goal
        if self.current == self.goal:
            self.is_finished = True
            self.path_found = True
            self.stop_timer()
            return
            
        # 3. Explore neighbors (in U,R,D,L order)
        # Note: We add them, so they will be popped in L,D,R,U order
        for neighbor in self._get_neighbors(*self.current):
            if neighbor not in self.visited:
                self.visited.add(neighbor)
                self.parent[neighbor] = self.current
                self.frontier.append(neighbor)
                
    def get_state_overlay(self) -> Dict[str, Any]:
        return {
            'visited': self.visited - set(self.frontier),
            'frontier': set(self.frontier),
            'current': self.current
        }

# ------------------------------------------------------------------
# Dijkstra's Algorithm
# ------------------------------------------------------------------

class Dijkstra(SearchAlgorithm):
    
    def __init__(self, grid: Grid, start: Tuple[int, int], goal: Tuple[int, int]):
        super().__init__(grid, start, goal)
        
        self.g_score: Dict[Tuple[int, int], float] = {start: 0}
        
        # Priority queue: (g_score, r, c)
        # (r, c) added for deterministic tie-breaking
        self.frontier: List[Tuple[float, int, int]] = [(0, start[0], start[1])]
        self.frontier_nodes: Set[Tuple[int, int]] = {start}

    def step(self):
        if self.is_finished or not self.frontier:
            self.is_finished = True
            if not self.path_found:
                self.stop_timer()
            return

        # 1. Get next node from priority queue
        g, r, c = heapq.heappop(self.frontier)
        self.current = (r, c)
        self.frontier_nodes.remove(self.current)
        
        # Already processed a shorter path
        if g > self.g_score.get(self.current, float('inf')):
            return

        self.visited.add(self.current) # Add to "closed set"
        self.explored_nodes += 1
        
        # 2. Check for goal
        if self.current == self.goal:
            self.is_finished = True
            self.path_found = True
            self.stop_timer()
            return
            
        # 3. Explore neighbors
        for neighbor in self._get_neighbors(*self.current):
            if neighbor in self.visited:
                continue
                
            # Uniform cost grid
            new_g = g + 1
            
            if new_g < self.g_score.get(neighbor, float('inf')):
                self.g_score[neighbor] = new_g
                self.parent[neighbor] = self.current
                
                # Push with (g_score, r, c) for tie-breaking
                heapq.push(self.frontier, (new_g, neighbor[0], neighbor[1]))
                self.frontier_nodes.add(neighbor)

    def get_state_overlay(self) -> Dict[str, Any]:
        return {
            'visited': self.visited,
            'frontier': self.frontier_nodes,
            'current': self.current
        }
        
# ------------------------------------------------------------------
# A* (A-Star) Algorithm
# ------------------------------------------------------------------

class AStar(SearchAlgorithm):
    
    def __init__(self, grid: Grid, start: Tuple[int, int], goal: Tuple[int, int]):
        super().__init__(grid, start, goal)
        
        self.g_score: Dict[Tuple[int, int], float] = {start: 0}
        
        h_start = self._heuristic(start, goal)
        self.f_score: Dict[Tuple[int, int], float] = {start: h_start}
        
        # Priority queue: (f_score, h_score, r, c)
        # h_score is secondary tie-breaker (prefers nodes closer to goal)
        # (r, c) is final tie-breaker
        self.frontier: List[Tuple[float, float, int, int]] = \
            [(h_start, h_start, start[0], start[1])]
        
        # Use a set for quick "is in frontier" checks
        self.frontier_nodes: Set[Tuple[int, int]] = {start}

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Manhattan distance heuristic."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
    def step(self):
        if self.is_finished or not self.frontier:
            self.is_finished = True
            if not self.path_found:
                self.stop_timer()
            return

        # 1. Get next node from priority queue
        f, h, r, c = heapq.heappop(self.frontier)
        self.current = (r, c)
        self.frontier_nodes.remove(self.current)
        
        # Already processed a shorter path
        if f > self.f_score.get(self.current, float('inf')):
            return

        self.visited.add(self.current) # Add to "closed set"
        self.explored_nodes += 1

        # 2. Check for goal
        if self.current == self.goal:
            self.is_finished = True
            self.path_found = True
            self.stop_timer()
            return
            
        # 3. Explore neighbors
        for neighbor in self._get_neighbors(*self.current):
            if neighbor in self.visited:
                continue
                
            # Uniform cost grid
            new_g = self.g_score.get(self.current, float('inf')) + 1
            
            if new_g < self.g_score.get(neighbor, float('inf')):
                self.g_score[neighbor] = new_g
                new_h = self._heuristic(neighbor, self.goal)
                new_f = new_g + new_h
                self.f_score[neighbor] = new_f
                self.parent[neighbor] = self.current
                
                if neighbor not in self.frontier_nodes:
                    # Push with (f, h, r, c) for tie-breaking
                    heapq.push(self.frontier, (new_f, new_h, neighbor[0], neighbor[1]))
                    self.frontier_nodes.add(neighbor)

    def get_state_overlay(self) -> Dict[str, Any]:
        return {
            'visited': self.visited,
            'frontier': self.frontier_nodes,
            'current': self.current
        }