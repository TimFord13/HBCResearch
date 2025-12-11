"""Maze generation algorithms with deterministic RNG support."""

import random
from typing import List, Tuple, Set, Optional
from enum import Enum


class CellType(Enum):
    """Cell types in the maze grid."""
    WALL = 0
    PASSAGE = 1
    START = 2
    GOAL = 3


class UnionFind:
    """Disjoint set data structure for Kruskal's algorithm."""
    
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x: int) -> int:
        """Find root with path compression."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """Unite two sets. Returns True if they were separate."""
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True


class Maze:
    """Maze grid with generation algorithms."""
    
    def __init__(self, rows: int, cols: int, seed: Optional[int] = None):
        """
        Initialize maze grid.
        
        Args:
            rows: Number of rows (should be odd)
            cols: Number of columns (should be odd)
            seed: Random seed for deterministic generation
        """
        self.rows = rows if rows % 2 == 1 else rows + 1
        self.cols = cols if cols % 2 == 1 else cols + 1
        self.grid = [[CellType.WALL for _ in range(self.cols)] for _ in range(self.rows)]
        self.seed = seed
        self.rng = random.Random(seed)
        self.start: Optional[Tuple[int, int]] = None
        self.goal: Optional[Tuple[int, int]] = None
        
    def reset(self):
        """Reset grid to all walls."""
        self.grid = [[CellType.WALL for _ in range(self.cols)] for _ in range(self.rows)]
        self.start = None
        self.goal = None
        if self.seed is not None:
            self.rng = random.Random(self.seed)
    
    def is_valid_cell(self, r: int, c: int) -> bool:
        """Check if coordinates are valid passage cells (odd indices)."""
        return 1 <= r < self.rows - 1 and 1 <= c < self.cols - 1 and r % 2 == 1 and c % 2 == 1
    
    def get_cell_coords(self) -> List[Tuple[int, int]]:
        """Get all valid cell coordinates (odd row and col indices)."""
        return [(r, c) for r in range(1, self.rows, 2) for c in range(1, self.cols, 2)]
    
    def get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Get neighboring cells (2 steps away in cardinal directions)."""
        neighbors = []
        for dr, dc in [(-2, 0), (0, 2), (2, 0), (0, -2)]:  # up, right, down, left
            nr, nc = r + dr, c + dc
            if self.is_valid_cell(nr, nc):
                neighbors.append((nr, nc))
        return neighbors
    
    def carve_passage(self, r1: int, c1: int, r2: int, c2: int):
        """Carve passage between two cells by removing wall between them."""
        self.grid[r1][c1] = CellType.PASSAGE
        self.grid[r2][c2] = CellType.PASSAGE
        # Remove wall between cells
        wall_r, wall_c = (r1 + r2) // 2, (c1 + c2) // 2
        self.grid[wall_r][wall_c] = CellType.PASSAGE
    
    def generate_prims(self) -> List[Tuple[str, any]]:
        """
        Generate maze using Randomized Prim's algorithm.
        Returns list of steps for visualization: (action, data)
        """
        self.reset()
        steps = []
        
        # Start from a random cell
        cells = self.get_cell_coords()
        start_cell = self.rng.choice(cells)
        self.grid[start_cell[0]][start_cell[1]] = CellType.PASSAGE
        
        # Initialize frontier with neighbors of start cell
        frontier = set()
        for neighbor in self.get_neighbors(*start_cell):
            frontier.add(neighbor)
        
        steps.append(('init', start_cell))
        
        while frontier:
            # Choose random frontier cell (deterministic with seed)
            frontier_list = sorted(list(frontier))  # Sort for determinism
            current = self.rng.choice(frontier_list)
            frontier.remove(current)
            
            # Find all adjacent passages
            adjacent_passages = []
            for neighbor in self.get_neighbors(*current):
                if self.grid[neighbor[0]][neighbor[1]] == CellType.PASSAGE:
                    adjacent_passages.append(neighbor)
            
            if adjacent_passages:
                # Connect to a random adjacent passage
                connect_to = self.rng.choice(sorted(adjacent_passages))
                self.carve_passage(current[0], current[1], connect_to[0], connect_to[1])
                steps.append(('carve', (current, connect_to)))
                
                # Add new frontier cells
                for neighbor in self.get_neighbors(*current):
                    if self.grid[neighbor[0]][neighbor[1]] == CellType.WALL:
                        if self.is_valid_cell(neighbor[0], neighbor[1]):
                            frontier.add(neighbor)
            
            steps.append(('frontier', list(frontier)))
        
        self._set_start_goal()
        return steps
    
    def generate_kruskals(self) -> List[Tuple[str, any]]:
        """
        Generate maze using Randomized Kruskal's algorithm.
        Returns list of steps for visualization: (action, data)
        """
        self.reset()
        steps = []
        
        # Get all cells and create edges between adjacent cells
        cells = self.get_cell_coords()
        cell_to_id = {cell: i for i, cell in enumerate(cells)}
        
        # Create all possible edges
        edges = []
        for r, c in cells:
            for nr, nc in self.get_neighbors(r, c):
                if (r, c) < (nr, nc):  # Avoid duplicate edges
                    edges.append(((r, c), (nr, nc)))
        
        # Shuffle edges deterministically
        self.rng.shuffle(edges)
        
        # Initialize union-find
        uf = UnionFind(len(cells))
        
        steps.append(('init', cells))
        
        # Process edges
        for cell1, cell2 in edges:
            id1, id2 = cell_to_id[cell1], cell_to_id[cell2]
            
            # If cells are in different sets, unite them
            if uf.find(id1) != uf.find(id2):
                uf.union(id1, id2)
                self.carve_passage(cell1[0], cell1[1], cell2[0], cell2[1])
                steps.append(('carve', (cell1, cell2)))
        
        self._set_start_goal()
        return steps
    
    def _set_start_goal(self):
        """Set start and goal positions at opposite corners."""
        # Start at top-left valid cell
        self.start = (1, 1)
        self.grid[1][1] = CellType.START
        
        # Goal at bottom-right valid cell
        self.goal = (self.rows - 2, self.cols - 2)
        self.grid[self.rows - 2][self.cols - 2] = CellType.GOAL
    
    def get_passable_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Get passable neighbors for pathfinding (1 step away)."""
        neighbors = []
        for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:  # up, right, down, left
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] != CellType.WALL:
                    neighbors.append((nr, nc))
        return neighbors
    
    def is_valid_path(self, path: List[Tuple[int, int]]) -> bool:
        """Verify path is contiguous and contains no walls."""
        if not path:
            return False
        if path[0] != self.start or path[-1] != self.goal:
            return False
        
        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i + 1]
            # Check cells are adjacent
            if abs(r1 - r2) + abs(c1 - c2) != 1:
                return False
            # Check no walls
            if self.grid[r1][c1] == CellType.WALL or self.grid[r2][c2] == CellType.WALL:
                return False
        
        return True
