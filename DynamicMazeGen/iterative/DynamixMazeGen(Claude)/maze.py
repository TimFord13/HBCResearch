# maze.py
"""
Core Grid & Maze Generation Engine

Provides a Maze class with two perfect maze generation algorithms:
- Randomized Prim's Algorithm
- Randomized Kruskal's Algorithm

Both algorithms use a seeded RNG for reproducible maze generation.
"""

import random
from typing import Optional, List, Tuple, Set
from enum import IntEnum


class CellType(IntEnum):
    """Cell types for display grid"""
    WALL = 0
    PASSAGE = 1
    START = 2
    GOAL = 3


class UnionFind:
    """
    Union-Find (Disjoint Set Union) data structure with path compression
    and union by rank for Kruskal's algorithm.
    """
    
    def __init__(self, size: int):
        """
        Initialize Union-Find structure.
        
        Args:
            size: Number of elements (0 to size-1)
        """
        self.parent = list(range(size))
        self.rank = [0] * size
    
    def find(self, x: int) -> int:
        """
        Find the root of element x with path compression.
        
        Args:
            x: Element to find root for
            
        Returns:
            Root of the set containing x
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """
        Union the sets containing x and y.
        
        Args:
            x: First element
            y: Second element
            
        Returns:
            True if union was performed, False if already in same set
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True
    
    def connected(self, x: int, y: int) -> bool:
        """
        Check if x and y are in the same set.
        
        Args:
            x: First element
            y: Second element
            
        Returns:
            True if x and y are in the same set
        """
        return self.find(x) == self.find(y)


class Maze:
    """
    Grid-based maze with perfect maze generation algorithms.
    
    Internal representation uses odd dimensions where:
    - Odd indices (1, 3, 5, ...) represent cells
    - Even indices (0, 2, 4, ...) represent walls between cells
    
    For a maze with m×n cells, internal grid is (2m+1)×(2n+1).
    """
    
    def __init__(self, rows: int, cols: int, seed: Optional[int] = None):
        """
        Initialize maze grid.
        
        Args:
            rows: Number of cell rows (not including walls)
            cols: Number of cell columns (not including walls)
            seed: Random seed for reproducible generation
        """
        self.cell_rows = rows
        self.cell_cols = cols
        self.seed = seed
        
        # Internal grid dimensions (cells + walls)
        self.grid_rows = 2 * rows + 1
        self.grid_cols = 2 * cols + 1
        
        # Initialize grid: 0 = wall, 1 = passage
        self.grid = [[0 for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
        
        # Initialize all cells as passages
        for r in range(1, self.grid_rows, 2):
            for c in range(1, self.grid_cols, 2):
                self.grid[r][c] = 1
        
        # Seeded random number generator
        self.rng = random.Random(seed)
        
        # Start and goal positions (in cell coordinates, not grid coordinates)
        self.start = (0, 0)
        self.goal = (rows - 1, cols - 1)
    
    def _cell_to_grid(self, cell_r: int, cell_c: int) -> Tuple[int, int]:
        """Convert cell coordinates to grid coordinates."""
        return (2 * cell_r + 1, 2 * cell_c + 1)
    
    def _grid_to_cell(self, grid_r: int, grid_c: int) -> Tuple[int, int]:
        """Convert grid coordinates to cell coordinates."""
        return ((grid_r - 1) // 2, (grid_c - 1) // 2)
    
    def is_passage(self, r: int, c: int) -> bool:
        """
        Check if a grid position is a passage.
        
        Args:
            r: Grid row
            c: Grid column
            
        Returns:
            True if position is a passage, False if wall or out of bounds
        """
        if 0 <= r < self.grid_rows and 0 <= c < self.grid_cols:
            return self.grid[r][c] == 1
        return False
    
    def neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """
        Get valid neighboring cells (in cell coordinates).
        
        Args:
            r: Cell row
            c: Cell column
            
        Returns:
            List of (row, col) tuples for valid neighbors in lexicographic order
        """
        result = []
        directions = [(-1, 0), (0, -1), (0, 1), (1, 0)]  # Lexicographic: up, left, right, down
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.cell_rows and 0 <= nc < self.cell_cols:
                result.append((nr, nc))
        
        return result
    
    def _remove_wall(self, cell1: Tuple[int, int], cell2: Tuple[int, int]):
        """Remove wall between two adjacent cells."""
        r1, c1 = self._cell_to_grid(*cell1)
        r2, c2 = self._cell_to_grid(*cell2)
        
        # Wall is at midpoint
        wall_r = (r1 + r2) // 2
        wall_c = (c1 + c2) // 2
        self.grid[wall_r][wall_c] = 1
    
    def generate_prim(self):
        """
        Generate perfect maze using Randomized Prim's algorithm.
        
        Algorithm:
        1. Start with a random cell, mark it as part of maze
        2. Add all walls of this cell to a wall list
        3. While wall list is not empty:
           - Pick a random wall from the list
           - If the cell on the opposite side isn't in the maze:
             - Make the wall a passage and mark the cell as part of maze
             - Add neighboring walls to the wall list
           - Remove the wall from the list
        """
        # Reset grid to all walls except cells
        self.grid = [[0 for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
        for r in range(1, self.grid_rows, 2):
            for c in range(1, self.grid_cols, 2):
                self.grid[r][c] = 1
        
        visited = set()
        walls = []
        
        # Start with cell (0, 0)
        start_cell = (0, 0)
        visited.add(start_cell)
        
        # Add walls of starting cell
        for neighbor in self.neighbors(*start_cell):
            if neighbor not in visited:
                walls.append((start_cell, neighbor))
        
        while walls:
            # Sort for deterministic tie-breaking, then pick random
            walls.sort()  # Lexicographic order
            wall_idx = self.rng.randint(0, len(walls) - 1)
            cell1, cell2 = walls.pop(wall_idx)
            
            # If cell2 hasn't been visited, add it to maze
            if cell2 not in visited:
                visited.add(cell2)
                self._remove_wall(cell1, cell2)
                
                # Add walls of newly visited cell
                for neighbor in self.neighbors(*cell2):
                    if neighbor not in visited:
                        walls.append((cell2, neighbor))
    
    def generate_kruskal(self):
        """
        Generate perfect maze using Randomized Kruskal's algorithm.
        
        Algorithm:
        1. Create a list of all walls
        2. Create a set for each cell
        3. For each wall (in random order):
           - If the cells divided by this wall are in different sets:
             - Remove the wall
             - Join the sets of the formerly divided cells
        """
        # Reset grid to all walls except cells
        self.grid = [[0 for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
        for r in range(1, self.grid_rows, 2):
            for c in range(1, self.grid_cols, 2):
                self.grid[r][c] = 1
        
        # Create cell index mapping
        def cell_index(r: int, c: int) -> int:
            return r * self.cell_cols + c
        
        # Initialize Union-Find
        num_cells = self.cell_rows * self.cell_cols
        uf = UnionFind(num_cells)
        
        # Create list of all possible walls (between adjacent cells)
        walls = []
        for r in range(self.cell_rows):
            for c in range(self.cell_cols):
                # Right neighbor
                if c + 1 < self.cell_cols:
                    walls.append(((r, c), (r, c + 1)))
                # Bottom neighbor
                if r + 1 < self.cell_rows:
                    walls.append(((r, c), (r + 1, c)))
        
        # Shuffle walls (with deterministic tie-break via sort first)
        walls.sort()  # Lexicographic order for determinism
        self.rng.shuffle(walls)
        
        # Process walls
        for cell1, cell2 in walls:
            idx1 = cell_index(*cell1)
            idx2 = cell_index(*cell2)
            
            # If cells are in different sets, remove wall and union sets
            if not uf.connected(idx1, idx2):
                uf.union(idx1, idx2)
                self._remove_wall(cell1, cell2)
    
    def to_display_grid(self) -> List[List[int]]:
        """
        Convert internal grid to display grid.
        
        Returns:
            2D list with CellType values:
            - WALL (0): Wall
            - PASSAGE (1): Passage
            - START (2): Start position
            - GOAL (3): Goal position
        """
        display = [row[:] for row in self.grid]
        
        # Mark start and goal
        start_r, start_c = self._cell_to_grid(*self.start)
        goal_r, goal_c = self._cell_to_grid(*self.goal)
        
        display[start_r][start_c] = CellType.START
        display[goal_r][goal_c] = CellType.GOAL
        
        return display
    
    def print_maze(self):
        """Print maze to console using ASCII characters."""
        display = self.to_display_grid()
        symbols = {
            CellType.WALL: '█',
            CellType.PASSAGE: ' ',
            CellType.START: 'S',
            CellType.GOAL: 'G'
        }
        
        for row in display:
            print(''.join(symbols[cell] for cell in row))


# ============================================================================
# TESTS AND EXAMPLE USAGE
# ============================================================================

def test_deterministic_generation():
    """Test that fixed seed produces identical mazes."""
    print("Testing deterministic generation...\n")
    
    # Test Prim's algorithm
    print("Prim's Algorithm - Seed 42:")
    maze1 = Maze(5, 5, seed=42)
    maze1.generate_prim()
    grid1 = maze1.to_display_grid()
    
    maze2 = Maze(5, 5, seed=42)
    maze2.generate_prim()
    grid2 = maze2.to_display_grid()
    
    assert grid1 == grid2, "Prim's algorithm not deterministic!"
    print("✓ Same seed produces identical maze")
    maze1.print_maze()
    
    # Test Kruskal's algorithm
    print("\nKruskal's Algorithm - Seed 42:")
    maze3 = Maze(5, 5, seed=42)
    maze3.generate_kruskal()
    grid3 = maze3.to_display_grid()
    
    maze4 = Maze(5, 5, seed=42)
    maze4.generate_kruskal()
    grid4 = maze4.to_display_grid()
    
    assert grid3 == grid4, "Kruskal's algorithm not deterministic!"
    print("✓ Same seed produces identical maze")
    maze3.print_maze()
    
    # Test different seeds produce different mazes
    maze5 = Maze(5, 5, seed=123)
    maze5.generate_prim()
    grid5 = maze5.to_display_grid()
    
    assert grid1 != grid5, "Different seeds should produce different mazes!"
    print("\n✓ Different seeds produce different mazes")


def test_union_find():
    """Test UnionFind data structure."""
    print("\nTesting UnionFind...\n")
    
    uf = UnionFind(5)
    
    # Initially all separate
    assert not uf.connected(0, 1)
    assert not uf.connected(2, 3)
    print("✓ Initially all elements separate")
    
    # Union some elements
    uf.union(0, 1)
    assert uf.connected(0, 1)
    assert not uf.connected(0, 2)
    print("✓ Union connects elements")
    
    uf.union(2, 3)
    uf.union(1, 2)
    assert uf.connected(0, 3)
    print("✓ Transitive connections work")


def example_usage():
    """Demonstrate basic usage."""
    print("\n" + "="*50)
    print("EXAMPLE USAGE")
    print("="*50 + "\n")
    
    # Create and generate maze with Prim's
    print("10×10 Maze - Prim's Algorithm (seed=999):")
    maze = Maze(10, 10, seed=999)
    maze.generate_prim()
    maze.print_maze()
    
    print("\n10×10 Maze - Kruskal's Algorithm (seed=999):")
    maze2 = Maze(10, 10, seed=999)
    maze2.generate_kruskal()
    maze2.print_maze()
    
    # Test helper methods
    print("\n\nHelper Methods Test:")
    print(f"Start position (cell coords): {maze.start}")
    print(f"Goal position (cell coords): {maze.goal}")
    print(f"Start is passage: {maze.is_passage(*maze._cell_to_grid(*maze.start))}")
    print(f"Neighbors of (0,0): {maze.neighbors(0, 0)}")


if __name__ == "__main__":
    test_union_find()
    test_deterministic_generation()
    example_usage()