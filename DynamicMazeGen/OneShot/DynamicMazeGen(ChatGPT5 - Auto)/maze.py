from __future__ import annotations
from typing import List, Tuple, Optional, Set, Dict
import random

Coord = Tuple[int, int]


class SeededRNG:
    """Shared RNG wrapper for determinism across modules."""
    def __init__(self, seed: Optional[int]) -> None:
        self.seed = seed
        self._rng = random.Random(seed)

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def choice(self, seq):
        return self._rng.choice(seq)

    def shuffle(self, seq) -> None:
        self._rng.shuffle(seq)

    def random(self) -> float:
        return self._rng.random()


class Grid:
    """Odd-dimension maze grid: walls on even indices, cells on odd indices."""
    def __init__(self, rows: int, cols: int) -> None:
        assert rows % 2 == 1 and cols % 2 == 1, "Use odd dimensions like 41x41"
        self.rows, self.cols = rows, cols
        self.wall = 1
        self.free = 0
        self.grid: List[List[int]] = [[self.wall for _ in range(cols)] for _ in range(rows)]
        # Start/goal in first and last cell positions
        self.start: Coord = (1, 1)
        self.goal: Coord = (rows-2, cols-2)
        self._dirty: Set[Coord] = set()

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_wall(self, rc: Coord) -> bool:
        r, c = rc
        return self.grid[r][c] == self.wall

    def set_free(self, rc: Coord) -> None:
        r, c = rc
        if self.grid[r][c] != self.free:
            self.grid[r][c] = self.free
            self._dirty.add(rc)

    def set_wall(self, rc: Coord) -> None:
        r, c = rc
        if self.grid[r][c] != self.wall:
            self.grid[r][c] = self.wall
            self._dirty.add(rc)

    def consume_dirty(self) -> Set[Coord]:
        out = self._dirty
        self._dirty = set()
        return out

    def carve_cell(self, r: int, c: int) -> None:
        self.set_free((r, c))

    def carve_passage(self, a: Coord, b: Coord) -> None:
        """Carve cell a and b and the wall between them."""
        ar, ac = a
        br, bc = b
        self.set_free(a)
        self.set_free(b)
        wr, wc = (ar + br)//2, (ac + bc)//2
        self.set_free((wr, wc))

    def ready_for_search(self) -> bool:
        return not self.is_wall(self.start) and not self.is_wall(self.goal)

    def neighbors_cells(self, rc: Coord) -> List[Coord]:
        r, c = rc
        out: List[Coord] = []
        for dr, dc in [(-2, 0), (0, 2), (2, 0), (0, -2)]:  # up, right, down, left (cell-to-cell)
            rr, cc = r + dr, c + dc
            if self.in_bounds(rr, cc):
                out.append((rr, cc))
        return out

    def passable_neighbors(self, rc: Coord) -> List[Coord]:
        """Neighbors at distance 1 (including walls between cells already carved)."""
        r, c = rc
        out: List[Coord] = []
        for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:  # up, right, down, left
            rr, cc = r + dr, c + dc
            if self.in_bounds(rr, cc) and not self.is_wall((rr, cc)):
                out.append((rr, cc))
        return out

    def finalize_after_generation(self) -> None:
        # Ensure start and goal are free
        self.set_free(self.start)
        self.set_free(self.goal)


# ---------- Generators ----------
class GeneratorBase:
    def __init__(self, grid: Grid, rng: SeededRNG) -> None:
        self.grid = grid
        self.rng = rng

    def step(self) -> bool:
        raise NotImplementedError

    def consume_dirty(self) -> Set[Coord]:
        return self.grid.consume_dirty()


class PrimGenerator(GeneratorBase):
    """Randomized Prim's with frontier set. Incremental step expands one cell."""
    def __init__(self, grid: Grid, rng: SeededRNG) -> None:
        super().__init__(grid, rng)
        self.frontier: Set[Coord] = set()
        # Start at (1,1)
        start = grid.start
        self.grid.carve_cell(*start)
        for n in self.grid.neighbors_cells(start):
            self.frontier.add(n)

    def step(self) -> bool:
        if not self.frontier:
            return True
        # Stable choice: sort frontier lexicographically, but mix with RNG via a single random index window
        sorted_front = sorted(self.frontier)  # stable order
        idx = self.rng.randint(0, min(7, len(sorted_front)-1))
        rc = sorted_front[idx]
        self.frontier.remove(rc)

        # Connect rc to any carved neighbor (choose stable-then-random)
        carved_neighbors = [n for n in self.grid.neighbors_cells(rc) if not self.grid.is_wall(n)]
        if not carved_neighbors:
            # Re-add other frontier cells for continuity
            for n in self.grid.neighbors_cells(rc):
                if self.grid.in_bounds(*n):
                    self.frontier.add(n)
            return False

        carved_neighbors.sort()
        neighbor = carved_neighbors[self.rng.randint(0, len(carved_neighbors)-1)]
        self.grid.carve_passage(rc, neighbor)

        # Add new frontier cells
        for n in self.grid.neighbors_cells(rc):
            if self.grid.in_bounds(*n) and self.grid.is_wall(n):
                self.frontier.add(n)

        return False


class KruskalGenerator(GeneratorBase):
    """Randomized Kruskal's using union-find over cell coordinates."""
    def __init__(self, grid: Grid, rng: SeededRNG) -> None:
        super().__init__(grid, rng)
        # Make all cells free initially to mark them as sets, then walls will be carved by edges
        for r in range(1, grid.rows, 2):
            for c in range(1, grid.cols, 2):
                grid.carve_cell(r, c)

        # Build edges between adjacent cells (distance 2)
        edges: List[Tuple[Coord, Coord]] = []
        for r in range(1, grid.rows, 2):
            for c in range(1, grid.cols, 2):
                for dr, dc in [(0, 2), (2, 0)]:  # right and down to avoid duplicates
                    rr, cc = r+dr, c+dc
                    if grid.in_bounds(rr, cc):
                        edges.append(((r, c), (rr, cc)))
        # Shuffle edges deterministically
        self.edges = edges
        rng.shuffle(self.edges)
        # Stable ordering inside small groups for determinism
        self.edges = sorted(self.edges, key=lambda e: (e[0], e[1]))

        self.uf = UnionFind()
        for r in range(1, grid.rows, 2):
            for c in range(1, grid.cols, 2):
                self.uf.add((r, c))

        # Initially set walls everywhere, we will carve when we accept an edge
        for r in range(grid.rows):
            for c in range(grid.cols):
                grid.set_wall((r, c))
        for r in range(1, grid.rows, 2):
            for c in range(1, grid.cols, 2):
                grid.carve_cell(r, c)
        self.i = 0

    def step(self) -> bool:
        if self.i >= len(self.edges):
            return True
        # Take a batch per step for visual speed
        batch = 8
        end = min(self.i + batch, len(self.edges))
        for k in range(self.i, end):
            a, b = self.edges[k]
            if self.uf.find(a) != self.uf.find(b):
                self.uf.union(a, b)
                self.grid.carve_passage(a, b)
        self.i = end
        return self.i >= len(self.edges)


class UnionFind:
    def __init__(self) -> None:
        self.parent: Dict[Coord, Coord] = {}
        self.rank: Dict[Coord, int] = {}

    def add(self, x: Coord) -> None:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x: Coord) -> Coord:
        # Path compression
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: Coord, b: Coord) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1
