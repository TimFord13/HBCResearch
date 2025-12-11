import time
import heapq
import math
from collections import deque
from typing import List, Tuple, Dict, Optional, Set, Any
from maze import Maze

# Status Constants
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

class SearchAlgorithm:
    """
    Base class for incremental search algorithms.
    """
    def __init__(self, maze: Maze, start: Tuple[int, int], goal: Tuple[int, int]):
        self.maze = maze
        self.start = start
        self.goal = goal
        
        # Tracking data
        self.came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
        self.cost_so_far: Dict[Tuple[int, int], float] = {start: 0}
        self.visited: Set[Tuple[int, int]] = set() # Closed set (nodes expanded)
        
        # Metrics
        self.start_time = 0.0
        self.accumulated_time = 0.0
        self.steps = 0
        self.path: List[Tuple[int, int]] = []
        
        self.status = STATUS_RUNNING
        self._initialized_timer = False

    def step(self) -> str:
        """
        Executes one atomic step of the algorithm.
        Returns: 'running', 'done', or 'failed'.
        """
        if self.status != STATUS_RUNNING:
            return self.status

        # Timer management
        t0 = time.perf_counter()
        
        try:
            result = self._step_internal()
        except Exception as e:
            print(f"Error during step: {e}")
            self.status = STATUS_FAILED
            return STATUS_FAILED
            
        dt = time.perf_counter() - t0
        self.accumulated_time += dt
        self.steps += 1
        
        if result:
            self.status = result
            if result == STATUS_DONE:
                self._reconstruct_path()
        
        return self.status

    def _step_internal(self) -> Optional[str]:
        raise NotImplementedError

    def is_done(self) -> bool:
        return self.status in [STATUS_DONE, STATUS_FAILED]

    def get_path(self) -> List[Tuple[int, int]]:
        return self.path

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "explored": len(self.visited),
            "steps": self.steps,
            "runtime_ms": self.accumulated_time * 1000.0,
            "path_len": len(self.path) if self.path else 0,
            "status": self.status
        }

    def _reconstruct_path(self):
        current = self.goal
        path = []
        while current is not None:
            path.append(current)
            current = self.came_from.get(current)
        path.reverse()
        self.path = path

    def _get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """
        Returns neighbors in stable order: Up, Right, Down, Left.
        Only returns accessible passages.
        """
        # Direction vectors: Up, Right, Down, Left
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        result = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            # We strictly check is_passage to avoid walls
            if self.maze.is_passage(nr, nc):
                result.append((nr, nc))
        return result


class BFS(SearchAlgorithm):
    def __init__(self, maze: Maze, start: Tuple[int, int], goal: Tuple[int, int]):
        super().__init__(maze, start, goal)
        self.frontier = deque([start])
        # BFS visits nodes when pushed to avoid duplicates in queue
        self.visited_in_frontier = {start} 

    def _step_internal(self) -> Optional[str]:
        if not self.frontier:
            return STATUS_FAILED

        current = self.frontier.popleft()
        self.visited.add(current) # Mark as fully explored

        if current == self.goal:
            return STATUS_DONE

        for next_node in self._get_neighbors(*current):
            if next_node not in self.visited_in_frontier:
                self.frontier.append(next_node)
                self.visited_in_frontier.add(next_node)
                self.came_from[next_node] = current
        
        return None # Continue running


class DFS(SearchAlgorithm):
    def __init__(self, maze: Maze, start: Tuple[int, int], goal: Tuple[int, int]):
        super().__init__(maze, start, goal)
        self.frontier = [start]
        self.seen = {start} # Track seen to avoid cycles/re-adding

    def _step_internal(self) -> Optional[str]:
        if not self.frontier:
            return STATUS_FAILED

        current = self.frontier.pop() # LIFO
        self.visited.add(current)

        if current == self.goal:
            return STATUS_DONE

        # Get neighbors (Up, Right, Down, Left)
        neighbors = self._get_neighbors(*current)
        
        # For DFS to traverse Up first, we must push it LAST if we iterate standard order.
        # Alternatively, iterate in reverse order so Up is at the top of the stack.
        # Requirement: "Tie-breaking of neighbor order must be stable (up,right,down,left)"
        # If we want to *visit* Up first, Up must be at top of stack.
        for next_node in reversed(neighbors):
            if next_node not in self.seen:
                self.frontier.append(next_node)
                self.seen.add(next_node)
                self.came_from[next_node] = current
        
        return None


class PriorityQueueSearch(SearchAlgorithm):
    """Base for Dijkstra and A*"""
    def __init__(self, maze: Maze, start: Tuple[int, int], goal: Tuple[int, int]):
        super().__init__(maze, start, goal)
        # Heap elements: (priority, tie_break_counter, item)
        # tie_break_counter ensures FIFO for equal priority to stabilize behavior
        self.frontier = []
        self.counter = 0 
        heapq.heappush(self.frontier, (0, self.counter, start))
        
        self.cost_so_far[start] = 0

    def heuristic(self, a, b):
        return 0 # Default for Dijkstra

    def _step_internal(self) -> Optional[str]:
        if not self.frontier:
            return STATUS_FAILED

        # Pop lowest priority
        _, _, current = heapq.heappop(self.frontier)
        
        if current in self.visited:
            # Lazy deletion: node might be in heap multiple times with different costs
            return None 

        self.visited.add(current)

        if current == self.goal:
            return STATUS_DONE

        for next_node in self._get_neighbors(*current):
            new_cost = self.cost_so_far[current] + 1 # Uniform weight 1
            
            if next_node not in self.cost_so_far or new_cost < self.cost_so_far[next_node]:
                self.cost_so_far[next_node] = new_cost
                priority = new_cost + self.heuristic(next_node, self.goal)
                self.came_from[next_node] = current
                
                self.counter += 1
                heapq.heappush(self.frontier, (priority, self.counter, next_node))
        
        return None


class Dijkstra(PriorityQueueSearch):
    """Dijkstra is A* with heuristic=0"""
    pass


class AStar(PriorityQueueSearch):
    def heuristic(self, a, b):
        # Manhattan Distance
        (x1, y1) = a
        (x2, y2) = b
        return abs(x1 - x2) + abs(y1 - y2)


# ------------------------------------------------------------------------------
# Unit Tests
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    def run_test(algo_class, maze, name):
        # Determine start/goal (logic specific to the Maze implementation)
        # Using maze._get_cell_coords to find valid walkable spots
        start_grid = maze._get_cell_coords(0, 0)
        goal_grid = maze._get_cell_coords(maze.rows - 1, maze.cols - 1)
        
        print(f"Testing {name} from {start_grid} to {goal_grid}...")
        
        algo = algo_class(maze, start_grid, goal_grid)
        
        while not algo.is_done():
            algo.step()
        
        metrics = algo.get_metrics()
        path = algo.get_path()
        
        print(f"  Status: {metrics['status']}")
        print(f"  Steps: {metrics['steps']}")
        print(f"  Path Len: {metrics['path_len']}")
        
        # Validation
        if metrics['status'] == STATUS_DONE:
            assert len(path) > 0
            assert path[0] == start_grid
            assert path[-1] == goal_grid
            
            # Check continuity
            for i in range(len(path) - 1):
                r1, c1 = path[i]
                r2, c2 = path[i+1]
                assert abs(r1 - r2) + abs(c1 - c2) == 1, "Path not contiguous"
                assert maze.is_passage(r2, c2), "Path goes through wall"
            print("  [PASS] Path valid.")
        else:
            print("  [FAIL] Did not find path.")
        print("-" * 30)

    # Setup Maze
    # Assuming maze.py is in the same directory and functional
    try:
        m = Maze(5, 5, seed=42)
        m.generate_prim()
        
        run_test(BFS, m, "BFS")
        run_test(DFS, m, "DFS")
        run_test(Dijkstra, m, "Dijkstra")
        run_test(AStar, m, "A*")
        
    except ImportError:
        print("maze.py not found. Please ensure maze.py is present to run tests.")