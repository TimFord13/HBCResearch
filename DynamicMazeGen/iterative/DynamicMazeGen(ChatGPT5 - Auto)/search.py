# search.py
"""
Stepwise search implementations: BFS, DFS, Dijkstra, A*.
Each provides:
    __init__(maze:Maze, start:(r,c), goal:(r,c))
    step() -> "running" or "done"
    is_done() -> bool
    get_path() -> list[(r,c)]
    get_metrics() -> dict with explored, runtime_ms, path_len
All algorithms operate on Maze internal grid coords (0..H-1, 0..W-1).
Tie-breaking neighbor order is fixed: Up, Right, Down, Left.
A* uses Manhattan heuristic. Dijkstra assumes non-negative uniform weights.
"""

import time
import heapq
from collections import deque
from typing import Tuple, List

NEIGHBORS = [(-1,0),(0,1),(1,0),(0,-1)]  # Up, Right, Down, Left for deterministic tie-breaks

def reconstruct_path(came_from, start, goal):
    if start == goal:
        return [start]
    if goal not in came_from:
        return []
    path = [goal]
    cur = goal
    while cur != start:
        cur = came_from.get(cur)
        if cur is None:
            return []
        path.append(cur)
    path.reverse()
    return path

class BaseSearch:
    def __init__(self, maze, start:Tuple[int,int], goal:Tuple[int,int]):
        self.maze = maze
        self.start = start
        self.goal = goal
        self.visited = set()
        self.came_from = {}
        self.done = False
        self.explored_count = 0
        self.runtime_ms = 0.0

    def step(self):
        raise NotImplementedError

    def is_done(self):
        return self.done

    def get_path(self) -> List[Tuple[int,int]]:
        return reconstruct_path(self.came_from, self.start, self.goal)

    def get_metrics(self):
        p = self.get_path()
        return {"explored": self.explored_count, "runtime_ms": self.runtime_ms, "path_len": len(p)}

# BFS
class BFS(BaseSearch):
    def __init__(self, maze, start, goal):
        super().__init__(maze, start, goal)
        self.frontier = deque([start])
        self.visited.add(start)

    def step(self):
        if self.done:
            return "done"
        t0 = time.perf_counter()
        if not self.frontier:
            self.done = True
            self.runtime_ms += (time.perf_counter()-t0)*1000
            return "done"
        cur = self.frontier.popleft()
        self.explored_count += 1
        if cur == self.goal:
            self.done = True
            self.runtime_ms += (time.perf_counter()-t0)*1000
            return "done"
        r,c = cur
        for dr,dc in NEIGHBORS:
            nr, nc = r+dr, c+dc
            if 0 <= nr < self.maze.H and 0 <= nc < self.maze.W and self.maze.is_passage(nr,nc) and (nr,nc) not in self.visited:
                self.visited.add((nr,nc))
                self.came_from[(nr,nc)] = cur
                self.frontier.append((nr,nc))
        self.runtime_ms += (time.perf_counter()-t0)*1000
        return "running"

# DFS
class DFS(BaseSearch):
    def __init__(self, maze, start, goal):
        super().__init__(maze, start, goal)
        self.frontier = [start]
        self.visited.add(start)

    def step(self):
        if self.done:
            return "done"
        t0 = time.perf_counter()
        if not self.frontier:
            self.done = True
            self.runtime_ms += (time.perf_counter()-t0)*1000
            return "done"
        cur = self.frontier.pop()
        self.explored_count += 1
        if cur == self.goal:
            self.done = True
            self.runtime_ms += (time.perf_counter()-t0)*1000
            return "done"
        r,c = cur
        # push neighbors in reverse so stack pops in NEIGHBORS order
        for dr,dc in reversed(NEIGHBORS):
            nr, nc = r+dr, c+dc
            if 0 <= nr < self.maze.H and 0 <= nc < self.maze.W and self.maze.is_passage(nr,nc) and (nr,nc) not in self.visited:
                self.visited.add((nr,nc))
                self.came_from[(nr,nc)] = cur
                self.frontier.append((nr,nc))
        self.runtime_ms += (time.perf_counter()-t0)*1000
        return "running"

# Dijkstra (uniform weights)
class Dijkstra(BaseSearch):
    def __init__(self, maze, start, goal):
        super().__init__(maze, start, goal)
        self.dist = {start:0}
        self.frontier = [(0, start)]
        self.visited = set()

    def step(self):
        if self.done:
            return "done"
        t0 = time.perf_counter()
        while self.frontier:
            d, cur = heapq.heappop(self.frontier)
            if cur in self.visited:
                continue
            self.visited.add(cur)
            self.explored_count += 1
            if cur == self.goal:
                self.done = True
                self.runtime_ms += (time.perf_counter()-t0)*1000
                return "done"
            r,c = cur
            for dr,dc in NEIGHBORS:
                nr, nc = r+dr, c+dc
                if not (0 <= nr < self.maze.H and 0 <= nc < self.maze.W):
                    continue
                if not self.maze.is_passage(nr,nc):
                    continue
                nd = d + 1
                if nd < self.dist.get((nr,nc), float("inf")):
                    self.dist[(nr,nc)] = nd
                    self.came_from[(nr,nc)] = cur
                    heapq.heappush(self.frontier, (nd, (nr,nc)))
            # one expansion per step for visualization purposes — return running here
            self.runtime_ms += (time.perf_counter()-t0)*1000
            return "running"
        self.done = True
        self.runtime_ms += (time.perf_counter()-t0)*1000
        return "done"

# A* with Manhattan heuristic
class AStar(BaseSearch):
    def __init__(self, maze, start, goal):
        super().__init__(maze, start, goal)
        self.g = {start:0}
        self.frontier = []
        h0 = self._heuristic(start)
        heapq.heappush(self.frontier, (h0, 0, start))  # (f, g, node)
        self.visited = set()

    def _heuristic(self, node):
        r,c = node
        gr,gc = self.goal
        return abs(r-gr) + abs(c-gc)

    def step(self):
        if self.done:
            return "done"
        t0 = time.perf_counter()
        while self.frontier:
            f,g,cur = heapq.heappop(self.frontier)
            if cur in self.visited:
                continue
            self.visited.add(cur)
            self.explored_count += 1
            if cur == self.goal:
                self.done = True
                self.runtime_ms += (time.perf_counter()-t0)*1000
                return "done"
            r,c = cur
            for dr,dc in NEIGHBORS:
                nr, nc = r+dr, c+dc
                if not (0 <= nr < self.maze.H and 0 <= nc < self.maze.W):
                    continue
                if not self.maze.is_passage(nr,nc):
                    continue
                newg = g + 1
                if newg < self.g.get((nr,nc), float("inf")):
                    self.g[(nr,nc)] = newg
                    self.came_from[(nr,nc)] = cur
                    f2 = newg + self._heuristic((nr,nc))
                    heapq.heappush(self.frontier, (f2, newg, (nr,nc)))
            # one expansion per step
            self.runtime_ms += (time.perf_counter()-t0)*1000
            return "running"
        self.done = True
        self.runtime_ms += (time.perf_counter()-t0)*1000
        return "done"

# quick test
if __name__ == "__main__":
    from maze import Maze
    m = Maze(20,20, seed=42)
    m.generate_prim()
    s = BFS(m,(1,1),(m.H-2,m.W-2))
    while not s.is_done():
        s.step()
    print("BFS path len", len(s.get_path()))
