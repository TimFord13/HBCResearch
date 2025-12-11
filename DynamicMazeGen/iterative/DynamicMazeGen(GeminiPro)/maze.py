import random
from typing import Optional, List, Tuple, Set

class UnionFind:
    """
    A simple Union-Find (Disjoint Set) data structure for Kruskal's algorithm.
    """
    def __init__(self, size: int):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, i: int) -> int:
        """Find the representative of the set containing i with path compression."""
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        """
        Union the sets containing i and j.
        Returns True if a merge happened (sets were different), False otherwise.
        """
        root_i = self.find(i)
        root_j = self.find(j)

        if root_i != root_j:
            # Union by rank
            if self.rank[root_i] < self.rank[root_j]:
                root_i, root_j = root_j, root_i
            self.parent[root_j] = root_i
            if self.rank[root_i] == self.rank[root_j]:
                self.rank[root_i] += 1
            return True
        return False


class Maze:
    """
    Maze generator supporting Randomized Prim's and Randomized Kruskal's algorithms.
    
    The grid uses an internal representation where:
    - 0 represents a WALL
    - 1 represents a PASSAGE
    
    Dimensions are (2*rows + 1) x (2*cols + 1) to accommodate walls between cells.
    """
    
    # Internal integer constants
    _WALL_INT = 0
    _PASSAGE_INT = 1
    
    # Display constants
    WALL_CHAR = '#'
    PASSAGE_CHAR = ' '
    START_CHAR = 'S'
    GOAL_CHAR = 'G'

    def __init__(self, rows: int, cols: int, seed: Optional[int] = None):
        """
        Initialize the maze grid.
        
        Args:
            rows: Number of usable cells vertically.
            cols: Number of usable cells horizontally.
            seed: Seed for the random number generator.
        """
        self.rows = rows
        self.cols = cols
        self.height = 2 * rows + 1
        self.width = 2 * cols + 1
        self.rng = random.Random(seed)
        
        # Grid initialization (0 = Wall, 1 = Passage)
        self.grid = [[self._WALL_INT for _ in range(self.width)] for _ in range(self.height)]
        
        self.start_cell = (0, 0)
        self.goal_cell = (rows - 1, cols - 1)

    def _reset_grid(self):
        """Resets the grid to all walls."""
        self.grid = [[self._WALL_INT for _ in range(self.width)] for _ in range(self.height)]

    def _get_cell_coords(self, r: int, c: int) -> Tuple[int, int]:
        """Convert logical cell coordinates (0..rows-1) to grid coordinates."""
        return 1 + 2 * r, 1 + 2 * c

    def is_passage(self, r: int, c: int) -> bool:
        """Check if grid coordinate (r, c) is a passage."""
        if 0 <= r < self.height and 0 <= c < self.width:
            return self.grid[r][c] == self._PASSAGE_INT
        return False

    def neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """
        Return list of grid coordinates for orthogonal neighbors 
        that are within bounds.
        """
        candidates = [
            (r - 1, c), (r + 1, c),
            (r, c - 1), (r, c + 1)
        ]
        result = []
        for nr, nc in candidates:
            if 0 <= nr < self.height and 0 <= nc < self.width:
                result.append((nr, nc))
        return result

    def generate_prim(self):
        """
        Generates a maze using Randomized Prim's algorithm.
        1. Start with a grid full of walls.
        2. Pick a cell, mark it as part of the maze. Add walls of the cell to the wall list.
        3. While there are walls in the list:
           - Pick a random wall from the list.
           - If only one of the two cells that the wall divides is visited:
             - Make the wall a passage.
             - Mark the unvisited cell as part of the maze.
             - Add the neighboring walls of the cell to the wall list.
        """
        self._reset_grid()
        
        # Start at logical (0,0)
        start_r, start_c = 0, 0
        gr, gc = self._get_cell_coords(start_r, start_c)
        self.grid[gr][gc] = self._PASSAGE_INT
        
        # Frontier walls: store (wall_grid_r, wall_grid_c, dest_logical_r, dest_logical_c)
        # We store destination logical coords to easily check visitation and add new walls.
        walls = []
        
        def add_walls(r: int, c: int):
            # r, c are logical coordinates
            # Up
            if r > 0: walls.append((2*r, 2*c + 1, r - 1, c))
            # Down
            if r < self.rows - 1: walls.append((2*r + 2, 2*c + 1, r + 1, c))
            # Left
            if c > 0: walls.append((2*r + 1, 2*c, r, c - 1))
            # Right
            if c < self.cols - 1: walls.append((2*r + 1, 2*c + 2, r, c + 1))

        add_walls(start_r, start_c)
        
        visited = set()
        visited.add((start_r, start_c))
        
        while walls:
            # Deterministic tie-break via seeded choice (pop random index)
            idx = self.rng.randint(0, len(walls) - 1)
            wr, wc, next_r, next_c = walls.pop(idx)
            
            if (next_r, next_c) not in visited:
                # Carve the wall
                self.grid[wr][wc] = self._PASSAGE_INT
                
                # Carve the cell
                ngr, ngc = self._get_cell_coords(next_r, next_c)
                self.grid[ngr][ngc] = self._PASSAGE_INT
                
                visited.add((next_r, next_c))
                add_walls(next_r, next_c)

    def generate_kruskal(self):
        """
        Generates a maze using Randomized Kruskal's algorithm.
        1. Create a list of all walls (edges) connecting distinct cells.
        2. Create a set for each cell (using Union-Find).
        3. For each wall, in random order:
           - If the cells divided by this wall belong to distinct sets:
             - Remove the wall (create passage).
             - Join the sets of the two cells.
        """
        self._reset_grid()
        
        # Initialize Union-Find
        uf = UnionFind(self.rows * self.cols)
        
        # List all internal edges.
        # Format: (wall_grid_r, wall_grid_c, cell1_idx, cell2_idx)
        edges = []
        
        # Horizontal edges (walls between columns)
        for r in range(self.rows):
            for c in range(self.cols - 1):
                idx1 = r * self.cols + c
                idx2 = r * self.cols + (c + 1)
                # Wall is at (2r+1, 2c+2)
                edges.append((2*r + 1, 2*c + 2, idx1, idx2))
                
        # Vertical edges (walls between rows)
        for r in range(self.rows - 1):
            for c in range(self.cols):
                idx1 = r * self.cols + c
                idx2 = (r + 1) * self.cols + c
                # Wall is at (2r+2, 2c+1)
                edges.append((2*r + 2, 2*c + 1, idx1, idx2))
        
        # Shuffle edges
        self.rng.shuffle(edges)
        
        # Process edges
        for wr, wc, u, v in edges:
            if uf.union(u, v):
                # Carve wall
                self.grid[wr][wc] = self._PASSAGE_INT
                # Carve the two cells connected (ensure they are open)
                # Calculate logical coordinates from index to grid coordinates
                r1, c1 = divmod(u, self.cols)
                gr1, gc1 = self._get_cell_coords(r1, c1)
                self.grid[gr1][gc1] = self._PASSAGE_INT
                
                r2, c2 = divmod(v, self.cols)
                gr2, gc2 = self._get_cell_coords(r2, c2)
                self.grid[gr2][gc2] = self._PASSAGE_INT

    def to_display_grid(self) -> List[str]:
        """
        Convert internal representation to a simple 2D array of strings.
        Returns a list of strings for easy printing.
        """
        display_grid = []
        for r in range(self.height):
            row_chars = []
            for c in range(self.width):
                if self.grid[r][c] == self._WALL_INT:
                    row_chars.append(self.WALL_CHAR)
                else:
                    row_chars.append(self.PASSAGE_CHAR)
            display_grid.append(row_chars)
        
        # Mark Start (0,0) and Goal (rows-1, cols-1)
        sr, sc = self._get_cell_coords(self.start_cell[0], self.start_cell[1])
        er, ec = self._get_cell_coords(self.goal_cell[0], self.goal_cell[1])
        
        display_grid[sr][sc] = self.START_CHAR
        display_grid[er][ec] = self.GOAL_CHAR
        
        return ["".join(row) for row in display_grid]

# ------------------------------------------------------------------------------
# Example Usage & Tests
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    def print_maze(m, title):
        print(f"\n--- {title} ---")
        grid = m.to_display_grid()
        for line in grid:
            print(line)

    SEED = 42
    ROWS, COLS = 5, 5

    # Test Prim's
    maze_prim = Maze(ROWS, COLS, seed=SEED)
    maze_prim.generate_prim()
    print_maze(maze_prim, "Randomized Prim's (Seed 42)")

    # Test Kruskal's
    maze_kruskal = Maze(ROWS, COLS, seed=SEED)
    maze_kruskal.generate_kruskal()
    print_maze(maze_kruskal, "Randomized Kruskal's (Seed 42)")

    # Test Reproducibility
    maze_prim_2 = Maze(ROWS, COLS, seed=SEED)
    maze_prim_2.generate_prim()
    
    assert maze_prim.to_display_grid() == maze_prim_2.to_display_grid()
    print("\n[SUCCESS] Deterministic behavior verified (Prim's generated identical mazes with same seed).")