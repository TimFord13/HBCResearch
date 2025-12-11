import random
from enum import Enum, auto
from typing import Optional, List, Set, Tuple, Any, Dict
import sys

# Increase recursion depth for deep mazes (e.g., Kruskal's find)
sys.setrecursionlimit(20000) 

class CellType(Enum):
    """Represents the state of a single cell in the grid."""
    WALL = auto()
    PASSAGE = auto()

class Grid:
    """
    Represents the maze grid.
    Stores cell types and handles coordinate validation.
    """
    
    def __init__(self, rows: int, cols: int, seed: Optional[Any] = None):
        # Ensure odd dimensions
        self.rows = rows // 2 * 2 + 1
        self.cols = cols // 2 * 2 + 1
        
        self.grid: List[List[CellType]] = [
            [CellType.WALL] * self.cols for _ in range(self.rows)
        ]
        
        # Set start and goal
        self.start = (1, 1)
        self.goal = (self.rows - 2, self.cols - 2)
        
        # Set passage at start
        self.grid[self.start[0]][self.start[1]] = CellType.PASSAGE
        
        # Seeded random number generator for determinism
        self.random = random.Random()
        if seed is not None:
            self.random.seed(seed)
            
    def is_valid(self, r: int, c: int) -> bool:
        """Check if a cell (r, c) is within the grid boundaries."""
        return 0 <= r < self.rows and 0 <= c < self.cols

    def get_neighbors(self, r: int, c: int,
                      step: int = 2,
                      include_walls: bool = False) -> List[Tuple[int, int]]:
        """
        Get valid neighbors for a cell.
        step=1: Adjacent neighbors (for pathfinding)
        step=2: Neighbors 2 cells away (for generation)
        """
        neighbors = []
        for dr, dc in [(-step, 0), (step, 0), (0, -step), (0, step)]:
            nr, nc = r + dr, c + dc
            if self.is_valid(nr, nc):
                if include_walls or self.grid[nr][nc] == CellType.PASSAGE:
                    neighbors.append((nr, nc))
        return neighbors

# ------------------------------------------------------------------
# Union-Find (Disjoint-Set) Structure for Kruskal's
# ------------------------------------------------------------------

class UnionFind:
    """
    A Disjoint-Set data structure with path compression
    and union by size for efficient Kruskal's implementation.
    """
    
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n
        self.num_sets = n

    def find(self, i: int) -> int:
        """Find the root of i with path compression."""
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        """
        Union sets containing i and j.
        Returns True if a union was performed, False if already in same set.
        """
        root_i = self.find(i)
        root_j = self.find(j)
        
        if root_i != root_j:
            # Union by size
            if self.size[root_i] < self.size[root_j]:
                root_i, root_j = root_j, root_i # Ensure root_i is larger
            
            self.parent[root_j] = root_i
            self.size[root_i] += self.size[root_j]
            self.num_sets -= 1
            return True
        return False

# ------------------------------------------------------------------
# Base Generator Class
# ------------------------------------------------------------------

class BaseMazeGenerator:
    """Abstract base class for maze generators."""
    
    def __init__(self, grid: Grid):
        self.grid = grid
        self.random = grid.random
        self.is_done = False
        self.changed_cells: List[Tuple[int, int, CellType]] = []

    def step(self):
        """Perform one step of the generation algorithm."""
        raise NotImplementedError

    def get_state_for_drawing(self) -> Dict[str, Any]:
        """Get the state relevant for visualization."""
        # Pop all changed cells for this frame
        changes = self.changed_cells
        self.changed_cells = []
        return {'changed_cells': changes}

    def _carve(self, r: int, c: int):
        """Set a cell to PASSAGE and log the change."""
        if self.grid.grid[r][c] == CellType.WALL:
            self.grid.grid[r][c] = CellType.PASSAGE
            self.changed_cells.append((r, c, CellType.PASSAGE))

# ------------------------------------------------------------------
# Randomized Prim's Algorithm
# ------------------------------------------------------------------

class PrimGenerator(BaseMazeGenerator):
    """
    Generates a maze using Randomized Prim's algorithm.
    Starts from a cell and grows, adding adjacent walls to a
    frontier and randomly picking one to open up.
    """
    
    def __init__(self, grid: Grid):
        super().__init__(grid)
        self.frontier: Set[Tuple[int, int]] = set()
        
        # Start at the grid's start cell
        start_r, start_c = self.grid.start
        self._add_frontier(start_r, start_c)

    def _add_frontier(self, r: int, c: int):
        """Add valid frontier cells (walls 2 steps away) to the set."""
        for nr, nc in self.grid.get_neighbors(r, c, step=2, include_walls=True):
            if self.grid.grid[nr][nc] == CellType.WALL:
                self.frontier.add((nr, nc))

    def step(self):
        """Perform one step of Prim's algorithm."""
        if not self.frontier:
            self.is_done = True
            return
            
        # 1. Pick a random cell from the frontier
        r, c = self.random.choice(list(self.frontier))
        self.frontier.remove((r, c))

        # 2. Find its "in-maze" neighbors (passages 2 steps away)
        in_maze_neighbors = []
        for nr, nc in self.grid.get_neighbors(r, c, step=2):
            # No include_walls, get_neighbors checks for PASSAGE
            in_maze_neighbors.append((nr, nc))
            
        if not in_maze_neighbors:
            return # Should not happen if start is valid

        # 3. Pick a random in-maze neighbor
        nr, nc = self.random.choice(in_maze_neighbors)
        
        # 4. Carve path: self -> wall -> neighbor
        self._carve(r, c)
        wall_r, wall_c = (r + nr) // 2, (c + nc) // 2
        self._carve(wall_r, wall_c)
        
        # 5. Add new frontiers from the carved cell
        self._add_frontier(r, c)

    def get_state_for_drawing(self) -> Dict[str, Any]:
        """Return changed cells and the current frontier."""
        state = super().get_state_for_drawing()
        state['frontier'] = self.frontier
        return state

# ------------------------------------------------------------------
# Randomized Kruskal's Algorithm
# ------------------------------------------------------------------

class KruskalGenerator(BaseMazeGenerator):
    """
    Generates a maze using Randomized Kruskal's algorithm.
    Treats all cells as separate sets and connects them by
    randomly removing walls, using Union-Find to prevent cycles.
    """
    
    def __init__(self, grid: Grid):
        super().__init__(grid)
        
        self.cell_rows = (self.grid.rows // 2)
        self.cell_cols = (self.grid.cols // 2)
        num_cells = self.cell_rows * self.cell_cols
        
        self.union_find = UnionFind(num_cells)
        self.edges: List[Tuple[int, int, int, int]] = []
        self.current_edge_coords: Optional[Tuple[int, int]] = None
        
        # Kruskal's starts by making *all* cells passages
        for r in range(1, self.grid.rows, 2):
            for c in range(1, self.grid.cols, 2):
                self._carve(r, c)
        
        # Create a list of all walls (edges)
        for r in range(1, self.grid.rows, 2): # For each cell row
            for c in range(1, self.grid.cols, 2): # For each cell
                if r + 2 < self.grid.rows:
                    # (cell1_idx, cell2_idx, wall_r, wall_c)
                    self.edges.append((self._cell_to_index(r, c),
                                       self._cell_to_index(r + 2, c),
                                       r + 1, c))
                if c + 2 < self.grid.cols:
                    self.edges.append((self._cell_to_index(r, c),
                                       self._cell_to_index(r, c + 2),
                                       r, c + 1))
                                       
        # Deterministically shuffle the edges
        self.random.shuffle(self.edges)

    def _cell_to_index(self, r: int, c: int) -> int:
        """Convert a cell's (r, c) to its 0-based index."""
        return (r // 2) * self.cell_cols + (c // 2)
        
    def step(self):
        """Perform one step of Kruskal's algorithm."""
        if not self.edges or self.union_find.num_sets <= 1:
            self.is_done = True
            self.current_edge_coords = None
            return

        # 1. Pop an edge (wall) from the list
        idx1, idx2, wall_r, wall_c = self.edges.pop()
        self.current_edge_coords = (wall_r, wall_c)
        
        # 2. Check if the cells are already connected
        if self.union_find.union(idx1, idx2):
            # 3. If not, union them and carve the wall
            self._carve(wall_r, wall_c)

    def get_state_for_drawing(self) -> Dict[str, Any]:
        """Return changed cells and the wall being tested."""
        state = super().get_state_for_drawing()
        state['current'] = self.current_edge_coords
        return state