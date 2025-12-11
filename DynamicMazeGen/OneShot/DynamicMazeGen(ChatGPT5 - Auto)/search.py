from __future__ import annotations
from typing import Optional, Tuple, List, Dict, Set
import heapq
import time
from dataclasses import dataclass

Coord = Tuple[int, int]


class EMA:
    """Simple exponentially-weighted moving average for FPS display."""
    def __init__(self, alpha: float = 0.2) -> None:
        self.alpha = alpha
        self.value = 0.0
        self.count = 0

    def update(self, x: float) -> None:
        if self.count == 0:
            self.value = x
        else:
            self.value = self.alpha * x + (1 - self.alpha) * self.value
        self.count += 1


def manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def validate_path(grid, path: Optional[List[Coord]]) -> bool:
    if not path:
        return False
    for i in range(len(path)-1):
        a, b = path[i], path[i+1]
        if b not in grid.passable_neighbors(a):
            return False
    return True


class IncrementalSearch:
    """Base class for BFS/DFS/Dijkstra/A* with incremental step() and metrics."""
    def __init__(self, grid, start: Coord, goal: Coord) -> None:
        self.grid = grid
        self.start = start
        self.goal = goal
        self._done = False
        self.explored = 0
        self._t0 = 0.0
        self._t1 = 0.0
        self.path: Optional[List[Coord]] = None
        self.frames_drawn = 0
        self.fps_ema = EMA()
        self.correct_path = False
        self.optimal = False
        self._dirty: Set[Coord] = set()

    def begin(self) -> None:
        self._t0 = time.perf_counter()

    def is_done(self) -> bool:
        return self._done

    def step(self) -> None:
        raise NotImplementedError

    def get_metrics(self) -> Dict:
        runtime_ms = int((self._t1 - self._t0) * 1000) if self._t1 > 0 else int((time.perf_counter() - self._t0) * 1000)
        return {
            "explored": self.explored,
            "runtime_ms": runtime_ms,
            "path_len": len(self.path)-1 if self.path else "",
            "optimal": self.optimal and self.correct_path,
            "valid": self.correct_path
        }

    def consume_dirty(self) -> Set[Coord]:
        out = self._dirty
        self._dirty = set()
        return out

    def reset_metrics(self) -> None:
        self.explored = 0
        self._t0 = time.perf_counter()
        self._t1 = 0.0
        self.path = None
        self.frames_drawn = 0
        self.fps_ema = EMA()
        self.correct_path = False
        self.optimal = False


class BFS(IncrementalSearch):
    def __init__(self, grid, start: Coord, goal: Coord) -> None:
        super().__init__(grid, start, goal)
        self.queue: List[Coord] = [start]
        self.parent: Dict[Coord, Coord] = {}
        self.seen: Set[Coord] = {start}

    def step(self) -> None:
        if self._done or not self.queue:
            self._done = True
            if self._t1 == 0.0:
                self._t1 = time.perf_counter()
            return
        rc = self.queue.pop(0)
        self.explored += 1
        self._dirty.add(rc)

        if rc == self.goal:
            self._done = True
            self.path = self._reconstruct(rc)
            self._t1 = time.perf_counter()
            return

        for nr in self._neighbors(rc):
            if nr not in self.seen:
                self.seen.add(nr)
                self.parent[nr] = rc
                self.queue.append(nr)

    def _neighbors(self, rc: Coord) -> List[Coord]:
        # stable order: up, right, down, left
        r, c = rc
        cand = [(r-1, c), (r, c+1), (r+1, c), (r, c-1)]
        return [p for p in cand if self.grid.in_bounds(*p) and not self.grid.is_wall(p)]

    def _reconstruct(self, end: Coord) -> List[Coord]:
        path = [end]
        while path[-1] != self.start:
            path.append(self.parent[path[-1]])
        path.reverse()
        return path


class DFS(IncrementalSearch):
    def __init__(self, grid, start: Coord, goal: Coord) -> None:
        super().__init__(grid, start, goal)
        self.stack: List[Coord] = [start]
        self.parent: Dict[Coord, Coord] = {}
        self.seen: Set[Coord] = {start}

    def step(self) -> None:
        if self._done or not self.stack:
            self._done = True
            if self._t1 == 0.0:
                self._t1 = time.perf_counter()
            return
        rc = self.stack.pop()
        self.explored += 1
        self._dirty.add(rc)

        if rc == self.goal:
            self._done = True
            self.path = self._reconstruct(rc)
            self._t1 = time.perf_counter()
            return

        for nr in reversed(self._neighbors(rc)):  # stack LIFO with up,right,down,left means push reversed to pop in order
            if nr not in self.seen:
                self.seen.add(nr)
                self.parent[nr] = rc
                self.stack.append(nr)

    def _neighbors(self, rc: Coord) -> List[Coord]:
        r, c = rc
        cand = [(r-1, c), (r, c+1), (r+1, c), (r, c-1)]
        return [p for p in cand if self.grid.in_bounds(*p) and not self.grid.is_wall(p)]

    def _reconstruct(self, end: Coord) -> List[Coord]:
        path = [end]
        while path[-1] != self.start:
            path.append(self.parent[path[-1]])
        path.reverse()
        return path


class Dijkstra(IncrementalSearch):
    def __init__(self, grid, start: Coord, goal: Coord) -> None:
        super().__init__(grid, start, goal)
        self.dist: Dict[Coord, int] = {start: 0}
        self.parent: Dict[Coord, Coord] = {}
        self.pq: List[Tuple[int, int, Coord]] = []  # (priority, tie, node)
        self._tie = 0
        heapq.heappush(self.pq, (0, self._tie, start))

    def step(self) -> None:
        if self._done or not self.pq:
            self._done = True
            if self._t1 == 0.0:
                self._t1 = time.perf_counter()
            return
        d, _, rc = heapq.heappop(self.pq)
        if d != self.dist.get(rc, float("inf")):
            return
        self.explored += 1
        self._dirty.add(rc)

        if rc == self.goal:
            self._done = True
            self.path = self._reconstruct(rc)
            self._t1 = time.perf_counter()
            return

        for nr in self._neighbors(rc):
            nd = d + 1  # uniform cost
            if nd < self.dist.get(nr, float("inf")):
                self.dist[nr] = nd
                self.parent[nr] = rc
                self._tie += 1
                heapq.heappush(self.pq, (nd, self._tie, nr))

    def _neighbors(self, rc: Coord) -> List[Coord]:
        r, c = rc
        cand = [(r-1, c), (r, c+1), (r+1, c), (r, c-1)]  # stable order
        return [p for p in cand if self.grid.in_bounds(*p) and not self.grid.is_wall(p)]

    def _reconstruct(self, end: Coord) -> List[Coord]:
        path = [end]
        while path[-1] != self.start:
            path.append(self.parent[path[-1]])
        path.reverse()
        return path


class AStar(IncrementalSearch):
    def __init__(self, grid, start: Coord, goal: Coord) -> None:
        super().__init__(grid, start, goal)
        self.g: Dict[Coord, int] = {start: 0}
        self.parent: Dict[Coord, Coord] = {}
        self.pq: List[Tuple[int, int, Coord]] = []  # (f, tie, node)
        self._tie = 0
        heapq.heappush(self.pq, (manhattan(start, goal), self._tie, start))

    def step(self) -> None:
        if self._done or not self.pq:
            self._done = True
            if self._t1 == 0.0:
                self._t1 = time.perf_counter()
            return
        f, _, rc = heapq.heappop(self.pq)
        if f != self._f(rc):
            return
        self.explored += 1
        self._dirty.add(rc)

        if rc == self.goal:
            self._done = True
            self.path = self._reconstruct(rc)
            self._t1 = time.perf_counter()
            return

        for nr in self._neighbors(rc):
            ng = self.g[rc] + 1
            if ng < self.g.get(nr, float("inf")):
                self.g[nr] = ng
                self.parent[nr] = rc
                self._tie += 1
                heapq.heappush(self.pq, (self._f(nr), self._tie, nr))

    def _neighbors(self, rc: Coord) -> List[Coord]:
        r, c = rc
        cand = [(r-1, c), (r, c+1), (r+1, c), (r, c-1)]
        return [p for p in cand if self.grid.in_bounds(*p) and not self.grid.is_wall(p)]

    def _f(self, rc: Coord) -> int:
        return self.g.get(rc, float("inf")) + manhattan(rc, self.goal)

    def _reconstruct(self, end: Coord) -> List[Coord]:
        path = [end]
        while path[-1] != self.start:
            path.append(self.parent[path[-1]])
        path.reverse()
        return path
