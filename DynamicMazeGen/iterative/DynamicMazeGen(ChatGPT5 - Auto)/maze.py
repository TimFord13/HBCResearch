# maze.py
"""
Maze generation module — seedable, internal odd-sized grid, Randomized Prim's and Kruskal's.
Public API:
    class Maze(rows:int, cols:int, seed:Optional[int]=None)
        - generate_prim()
        - generate_kruskal()
        - is_passage(r,c)
        - neighbors(r,c)  # 4-way neighbors in internal coords
        - to_display_grid(mark_start_goal=True)
Notes:
- Internal grid size = (rows*2 + 1) x (cols*2 + 1)
- Cells are on odd indices (1,3,5,...). Walls are 1s, passages 0s.
- Uses local rng = random.Random(seed) when seed is provided.
"""

from typing import Optional, List, Tuple
import random
import sys

WALL = 1
PASSAGE = 0

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0]*n

    def find(self, a):
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a, b):
        ra = self.find(a); rb = self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        else:
            self.parent[rb] = ra
            if self.rank[ra] == self.rank[rb]:
                self.rank[ra] += 1
        return True

class Maze:
    def __init__(self, rows:int, cols:int, seed:Optional[int]=None):
        """
        rows, cols = logical cell counts (not internal grid size).
        seed: Optional int to create deterministic rng.
        """
        if rows < 1 or cols < 1:
            raise ValueError("rows and cols must be >= 1")
        self.rows = rows
        self.cols = cols
        self.H = rows*2 + 1
        self.W = cols*2 + 1
        self.seed = seed
        self.rng = random.Random(seed) if seed is not None else random.Random()
        # grid: 2D list of ints; 1 = wall, 0 = passage
        self._grid = [[WALL for _ in range(self.W)] for _ in range(self.H)]
        # initialize all cell centers as passages (odd indices)
        for r in range(1, self.H, 2):
            for c in range(1, self.W, 2):
                self._grid[r][c] = PASSAGE

    def is_passage(self, r:int, c:int) -> bool:
        if r<0 or c<0 or r>=self.H or c>=self.W:
            return False
        return self._grid[r][c] == PASSAGE

    def neighbors(self, r:int, c:int) -> List[Tuple[int,int]]:
        """Return 4-neighbors in internal grid coordinates (not logical cell coords)."""
        nbrs = []
        for dr,dc in [(-1,0),(0,1),(1,0),(0,-1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < self.H and 0 <= nc < self.W:
                nbrs.append((nr,nc))
        return nbrs

    # ---------------- Prim's Algorithm ----------------
    def generate_prim(self):
        """
        Correct, fully functional Randomized Prim's algorithm.
        Produces a perfect maze: exactly one connected component, no cycles.
        Uses self.rng for deterministic behavior.
        """

        # Start with all walls
        for r in range(self.H):
            for c in range(self.W):
                self._grid[r][c] = WALL

        # Random starting cell (odd, odd)
        sr = self.rng.randrange(self.rows) * 2 + 1
        sc = self.rng.randrange(self.cols) * 2 + 1
        self._grid[sr][sc] = PASSAGE

        walls = []

        def add_walls_of(r, c):
            """Add walls adjacent to cell (must be odd,odd)."""
            for dr, dc in [(-2,0), (0,2), (2,0), (0,-2)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr < self.H-1 and 1 <= nc < self.W-1:
                    wr, wc = r + dr//2, c + dc//2
                    if self._grid[wr][wc] == WALL:
                        walls.append((wr, wc, nr, nc))

        add_walls_of(sr, sc)

        while walls:
            idx = self.rng.randrange(len(walls))
            wr, wc, nr, nc = walls.pop(idx)

            # If the far cell is still a wall cell center → carve path
            if self._grid[nr][nc] == WALL:
                # Carve wall + far cell
                self._grid[wr][wc] = PASSAGE
                self._grid[nr][nc] = PASSAGE
                add_walls_of(nr, nc)

    # ---------------- Kruskal's Algorithm ----------------
    def generate_kruskal(self):
        """Randomized Kruskal's algorithm with union-find on logical cells."""
        # label logical cells 0..(rows*cols-1)
        n_cells = self.rows * self.cols
        uf = UnionFind(n_cells)
        # Initially, clear all walls between cells to passages only at centers and between them randomly decide to open
        # Build list of potential walls between adjacent logical cells (vertical and horizontal)
        walls = []
        for r in range(self.rows):
            for c in range(self.cols):
                id1 = r*self.cols + c
                # right neighbor
                if c+1 < self.cols:
                    id2 = r*self.cols + (c+1)
                    # wall position in internal coords:
                    wr = r*2+1
                    wc = c*2+2
                    walls.append((id1,id2,wr,wc))
                # down neighbor
                if r+1 < self.rows:
                    id2 = (r+1)*self.cols + c
                    wr = r*2+2
                    wc = c*2+1
                    walls.append((id1,id2,wr,wc))
        # shuffle walls deterministically
        self.rng.shuffle(walls)
        # Start with all internal walls present; we will remove wall (wr,wc) when we union sets
        # (centers already passages)
        for id1,id2,wr,wc in walls:
            if uf.find(id1) != uf.find(id2):
                uf.union(id1,id2)
                # remove wall
                self._grid[wr][wc] = PASSAGE
        # done
        return

    # Utility: convert internal grid to display tokens
    def to_display_grid(self, mark_start_goal:bool=True):
        """
        Return a copy of the internal grid as 2D list with ints (1=wall,0=passage).
        If mark_start_goal True, places special tokens START/GOAL as 2/3 (not used elsewhere).
        """
        out = [row[:] for row in self._grid]
        if mark_start_goal:
            sr,sc = 1,1
            gr,gc = self.H-2, self.W-2
            if out[sr][sc] == PASSAGE:
                out[sr][sc] = 2
            if out[gr][gc] == PASSAGE:
                out[gr][gc] = 3
        return out

# quick smoke test when run directly
if __name__ == "__main__":
    m = Maze(20,20, seed=42)
    m.generate_prim()
    dg = m.to_display_grid()
    print("Maze HxW:", m.H, m.W)
    # print small representation
    for r in range(m.H):
        row = "".join('#' if dg[r][c]==1 else '.' if dg[r][c] in (0,2,3) else '?' for c in range(m.W))
        print(row)
