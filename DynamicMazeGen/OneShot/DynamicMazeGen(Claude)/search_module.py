"""Pathfinding algorithms with incremental stepping support."""

import time
from typing import List, Tuple, Optional, Dict, Set
from collections import deque
import heapq
from abc import ABC, abstractmethod


class SearchAlgorithm(ABC):
    """Base class for pathfinding algorithms."""
    
    def __init__(self, maze, name: str):
        self.maze = maze
        self.name = name
        self.start_time = None
        self.end_time = None
        self.explored_count = 0
        self.current = None
        self.path = None
        self.done = False
        
    @abstractmethod
    def init_search(self):
        """Initialize search state."""
        pass
    
    @abstractmethod
    def step(self) -> bool:
        """Execute one search step. Returns True if search continues."""
        pass
    
    def is_done(self) -> bool:
        """Check if search is complete."""
        return self.done
    
    def get_path(self) -> Optional[List[Tuple[int, int]]]:
        """Return found path or None."""
        return self.path
    
    def get_metrics(self) -> Dict:
        """Return algorithm metrics."""
        runtime = 0
        if self.start_time and self.end_time:
            runtime = (self.end_time - self.start_time) * 1000  # Convert to ms
        
        return {
            'name': self.name,
            'explored': self.explored_count,
            'runtime_ms': round(runtime, 2),
            'path_length': len(self.path) if self.path else 0,
            'found': self.path is not None
        }
    
    def start(self):
        """Start timing."""
        self.start_time = time.time()
        self.init_search()
    
    def finish(self):
        """Stop timing."""
        if not self.end_time:
            self.end_time = time.time()
        self.done = True


class BFS(SearchAlgorithm):
    """Breadth-First Search - guarantees shortest path."""
    
    def __init__(self, maze):
        super().__init__(maze, "BFS")
        self.queue = deque()
        self.visited = set()
        self.parent = {}
        
    def init_search(self):
        """Initialize BFS."""
        self.queue = deque([self.maze.start])
        self.visited = {self.maze.start}
        self.parent = {self.maze.start: None}
        self.explored_count = 0
        
    def step(self) -> bool:
        """Execute one BFS step."""
        if not self.queue or self.done:
            if not self.done:
                self.finish()
            return False
        
        self.current = self.queue.popleft()
        self.explored_count += 1
        
        # Check if goal reached
        if self.current == self.maze.goal:
            self.path = self._reconstruct_path()
            self.finish()
            return False
        
        # Explore neighbors in order: up, right, down, left
        for neighbor in self.maze.get_passable_neighbors(*self.current):
            if neighbor not in self.visited:
                self.visited.add(neighbor)
                self.parent[neighbor] = self.current
                self.queue.append(neighbor)
        
        return True
    
    def _reconstruct_path(self) -> List[Tuple[int, int]]:
        """Reconstruct path from start to goal."""
        path = []
        current = self.maze.goal
        while current is not None:
            path.append(current)
            current = self.parent.get(current)
        return path[::-1]


class DFS(SearchAlgorithm):
    """Depth-First Search - may find non-optimal path."""
    
    def __init__(self, maze):
        super().__init__(maze, "DFS")
        self.stack = []
        self.visited = set()
        self.parent = {}
        
    def init_search(self):
        """Initialize DFS."""
        self.stack = [self.maze.start]
        self.visited = {self.maze.start}
        self.parent = {self.maze.start: None}
        self.explored_count = 0
        
    def step(self) -> bool:
        """Execute one DFS step."""
        if not self.stack or self.done:
            if not self.done:
                self.finish()
            return False
        
        self.current = self.stack.pop()
        self.explored_count += 1
        
        # Check if goal reached
        if self.current == self.maze.goal:
            self.path = self._reconstruct_path()
            self.finish()
            return False
        
        # Explore neighbors in reverse order for consistent left-to-right DFS
        # Order: up, right, down, left -> push in reverse: left, down, right, up
        neighbors = self.maze.get_passable_neighbors(*self.current)
        for neighbor in reversed(neighbors):
            if neighbor not in self.visited:
                self.visited.add(neighbor)
                self.parent[neighbor] = self.current
                self.stack.append(neighbor)
        
        return True
    
    def _reconstruct_path(self) -> List[Tuple[int, int]]:
        """Reconstruct path from start to goal."""
        path = []
        current = self.maze.goal
        while current is not None:
            path.append(current)
            current = self.parent.get(current)
        return path[::-1]


class Dijkstra(SearchAlgorithm):
    """Dijkstra's algorithm - optimal pathfinding with uniform costs."""
    
    def __init__(self, maze):
        super().__init__(maze, "Dijkstra")
        self.open_set = []
        self.distances = {}
        self.parent = {}
        self.visited = set()
        
    def init_search(self):
        """Initialize Dijkstra."""
        self.open_set = [(0, 0, self.maze.start)]  # (distance, tie_breaker, node)
        self.distances = {self.maze.start: 0}
        self.parent = {self.maze.start: None}
        self.visited = set()
        self.explored_count = 0
        self.counter = 0
        
    def step(self) -> bool:
        """Execute one Dijkstra step."""
        if not self.open_set or self.done:
            if not self.done:
                self.finish()
            return False
        
        dist, _, self.current = heapq.heappop(self.open_set)
        
        if self.current in self.visited:
            return True
        
        self.visited.add(self.current)
        self.explored_count += 1
        
        # Check if goal reached
        if self.current == self.maze.goal:
            self.path = self._reconstruct_path()
            self.finish()
            return False
        
        # Explore neighbors
        for neighbor in self.maze.get_passable_neighbors(*self.current):
            if neighbor not in self.visited:
                new_dist = dist + 1  # Uniform cost
                
                if neighbor not in self.distances or new_dist < self.distances[neighbor]:
                    self.distances[neighbor] = new_dist
                    self.parent[neighbor] = self.current
                    self.counter += 1
                    # Tie-break by row, then col for determinism
                    heapq.heappush(self.open_set, (new_dist, (neighbor[0], neighbor[1]), neighbor))
        
        return True
    
    def _reconstruct_path(self) -> List[Tuple[int, int]]:
        """Reconstruct path from start to goal."""
        path = []
        current = self.maze.goal
        while current is not None:
            path.append(current)
            current = self.parent.get(current)
        return path[::-1]


class AStar(SearchAlgorithm):
    """A* algorithm - optimal pathfinding with Manhattan heuristic."""
    
    def __init__(self, maze):
        super().__init__(maze, "A*")
        self.open_set = []
        self.g_scores = {}
        self.parent = {}
        self.visited = set()
        
    def init_search(self):
        """Initialize A*."""
        h = self._heuristic(self.maze.start)
        self.open_set = [(h, 0, 0, self.maze.start)]  # (f, g, tie_breaker, node)
        self.g_scores = {self.maze.start: 0}
        self.parent = {self.maze.start: None}
        self.visited = set()
        self.explored_count = 0
        self.counter = 0
        
    def _heuristic(self, node: Tuple[int, int]) -> int:
        """Manhattan distance heuristic."""
        return abs(node[0] - self.maze.goal[0]) + abs(node[1] - self.maze.goal[1])
    
    def step(self) -> bool:
        """Execute one A* step."""
        if not self.open_set or self.done:
            if not self.done:
                self.finish()
            return False
        
        f, g, _, self.current = heapq.heappop(self.open_set)
        
        if self.current in self.visited:
            return True
        
        self.visited.add(self.current)
        self.explored_count += 1
        
        # Check if goal reached
        if self.current == self.maze.goal:
            self.path = self._reconstruct_path()
            self.finish()
            return False
        
        # Explore neighbors
        for neighbor in self.maze.get_passable_neighbors(*self.current):
            if neighbor not in self.visited:
                new_g = g + 1  # Uniform cost
                
                if neighbor not in self.g_scores or new_g < self.g_scores[neighbor]:
                    self.g_scores[neighbor] = new_g
                    self.parent[neighbor] = self.current
                    new_f = new_g + self._heuristic(neighbor)
                    self.counter += 1
                    # Tie-break by row, then col for determinism
                    heapq.heappush(self.open_set, (new_f, new_g, (neighbor[0], neighbor[1]), neighbor))
        
        return True
    
    def _reconstruct_path(self) -> List[Tuple[int, int]]:
        """Reconstruct path from start to goal."""
        path = []
        current = self.maze.goal
        while current is not None:
            path.append(current)
            current = self.parent.get(current)
        return path[::-1]


def verify_optimality(algorithms: List[SearchAlgorithm]) -> Dict[str, bool]:
    """
    Verify path optimality against Dijkstra's result.
    Returns dict of algorithm name to optimality status.
    """
    # Find Dijkstra's path length as ground truth
    dijkstra_length = None
    for algo in algorithms:
        if algo.name == "Dijkstra" and algo.path:
            dijkstra_length = len(algo.path)
            break
    
    if dijkstra_length is None:
        return {algo.name: False for algo in algorithms}
    
    # Compare each algorithm's path length
    results = {}
    for algo in algorithms:
        if algo.path:
            results[algo.name] = len(algo.path) == dijkstra_length
        else:
            results[algo.name] = False
    
    return results
