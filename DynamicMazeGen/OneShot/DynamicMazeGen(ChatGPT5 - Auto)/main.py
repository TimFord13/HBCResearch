#!/usr/bin/env python3
"""
Dynamic Maze Generation + Pathfinding Race (Python GUI, Real-Time)
==================================================================

How to run
----------
- Requirements: Python 3.10+ (standard library only). tkinter must be available.
- Run: `python main.py`
- This opens a window with a default 41x41 grid. Use the menu bar to generate a maze and start the race.

Menus (Game/Run, Maze, Pathfinding, Speed, View)
------------------------------------------------
Game/Run:
- New Maze: generate a new maze using the selected generator (Prim or Kruskal).
- Start Race: begin interleaved BFS/DFS/Dijkstra/A* exploration (only enabled after a maze exists).
- Pause/Resume: toggle the animation loop.
- Step: advance one multi-algorithm step without running the loop.
- Reset Stats: clear metrics and overlays while keeping the current maze.
- Quit: exit the app.

Maze:
- Algorithm: choose the generator {Prim's, Kruskal's}.
- Grid Size: presets {21x21, 31x31, 41x41, 61x61}. Always odd for wall/cell layout.
- Seed: Set… prompts for an integer; Clear removes deterministic seeding.

Pathfinding (enable/disable):
- Toggle BFS, DFS, Dijkstra, A*. At least one must be enabled for Start Race.

Speed:
- Steps per frame: how many algorithm steps to perform per rendered frame.
- Frame delay (ms): real-time delay between frames. Set to 0 for fastest updates.

View:
- Toggle overlays: frontier, visited, open set/queue/stack, parent pointers.
- Show winning path(s).
- Show weights (if any). We use uniform weights here, so this is informational.

Algorithm Notes
---------------
Maze generation:
- Randomized Prim's: frontier-based expansion from a start cell; uses a seeded RNG when provided.
- Randomized Kruskal's: treat passages as edges between cells; uses union-find to avoid cycles.

Pathfinding:
- BFS: unweighted shortest path (explores in layers). Optimal for uniform cost.
- DFS: depth-first; may return a non-optimal but valid path.
- Dijkstra: optimal shortest path for non-negative weights (uniform here).
- A*: best-first using Manhattan heuristic; optimal with an admissible, consistent heuristic.

Determinism
-----------
- If a seed is set, all random choices draw from a single RNG instance wired through the app. Tie-breaking
  is stable using lexicographic order where priorities are equal. Neighbor order is fixed: up, right, down, left.

Metrics & Correctness
---------------------
- Per algorithm: nodes explored, wall time (ms), path length, frames drawn, average FPS.
- Correctness checks:
  * Valid path: contiguous, in bounds, not through walls.
  * Optimality (Dijkstra/A*): path length equals Dijkstra's ground-truth shortest length.

Export CSV
----------
- Button writes CSV to working directory with columns:
  timestamp, seed, grid_rows, grid_cols, generator, algo, explored, runtime_ms, path_len,
  optimality, frames_drawn, avg_fps

Architecture
------------
- main.py : entry point and app wiring, menu commands
- gui.py  : Tkinter canvas, drawing, control panel, timers, FPS meter
- maze.py : grid representation, Prim's, Kruskal's, union-find, seedable RNG
- search.py: BFS, DFS, Dijkstra, A* sharing a common incremental interface

Quality
-------
- No global singletons for algorithm state; multiple races per session are supported.
- Type hints and docstrings in core structures.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import time
from typing import Optional, Dict, List, Tuple

import maze as mz
import search as sh
import gui as ui


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Dynamic Maze Generation + Pathfinding Race")
        self.state = ui.UIState()  # GUI state flags
        self.rng_seed: Optional[int] = None
        self.rng = mz.SeededRNG(None)

        # Defaults
        self.rows, self.cols = 41, 41
        self.generator_kind = "Prim"  # or "Kruskal"
        self.enabled_algos = {"BFS": True, "DFS": True, "Dijkstra": True, "A*": True}

        # Models
        self.grid = mz.Grid(self.rows, self.cols)
        self.generator: Optional[mz.GeneratorBase] = None
        self.runners: Dict[str, sh.IncrementalSearch] = {}

        # GUI
        self.ui = ui.GUI(self.root, self.rows, self.cols, self.on_export_csv)
        self._build_menu()
        self._bind_keys()
        self._reset_maze_only(draw=True)

        # Animation timers
        self._last_frame_time = time.perf_counter()
        self._frame_counter = 0
        self._fps_samples: List[float] = []

    # ---------- Menu / Controls ----------
    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        game = tk.Menu(menubar, tearoff=0)
        game.add_command(label="New Maze", command=self.menu_new_maze, accelerator="N")
        game.add_command(label="Start Race", command=self.menu_start_race, accelerator="R")
        game.add_command(label="Pause/Resume", command=self.menu_pause_resume, accelerator="P")
        game.add_command(label="Step", command=self.menu_step, accelerator="S")
        game.add_separator()
        game.add_command(label="Reset Stats", command=self.menu_reset_stats)
        game.add_separator()
        game.add_command(label="Quit", command=lambda: self.root.destroy(), accelerator="Esc")
        menubar.add_cascade(label="Game/Run", menu=game)

        m_maze = tk.Menu(menubar, tearoff=0)
        gen = tk.Menu(m_maze, tearoff=0)
        gen.add_radiobutton(label="Prim's", value="Prim", variable=self.state.tk_gen_kind, command=self._on_gen_change)
        gen.add_radiobutton(label="Kruskal's", value="Kruskal", variable=self.state.tk_gen_kind, command=self._on_gen_change)
        m_maze.add_cascade(label="Algorithm", menu=gen)

        size = tk.Menu(m_maze, tearoff=0)
        for r in [21, 31, 41, 61]:
            size.add_radiobutton(label=f"{r}x{r}", value=f"{r}x{r}", variable=self.state.tk_size, command=self._on_size_change)
        m_maze.add_cascade(label="Grid Size presets", menu=size)

        seed = tk.Menu(m_maze, tearoff=0)
        seed.add_command(label="Set…", command=self.menu_seed_set)
        seed.add_command(label="Clear", command=self.menu_seed_clear)
        m_maze.add_cascade(label="Seed", menu=seed)
        menubar.add_cascade(label="Maze", menu=m_maze)

        m_path = tk.Menu(menubar, tearoff=0)
        for name in ["BFS", "DFS", "Dijkstra", "A*"]:
            m_path.add_checkbutton(label=name, onvalue=True, offvalue=False,
                                   variable=self.state.tk_algos[name],
                                   command=self._on_algo_toggle)
        menubar.add_cascade(label="Pathfinding", menu=m_path)

        m_speed = tk.Menu(menubar, tearoff=0)
        self.ui.attach_speed_menu(m_speed)
        menubar.add_cascade(label="Speed", menu=m_speed)

        m_view = tk.Menu(menubar, tearoff=0)
        self.ui.attach_view_menu(m_view)
        menubar.add_cascade(label="View", menu=m_view)

        self.root.config(menu=menubar)

    def _bind_keys(self) -> None:
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("n", lambda e: self.menu_new_maze())
        self.root.bind("N", lambda e: self.menu_new_maze())
        self.root.bind("r", lambda e: self.menu_start_race())
        self.root.bind("R", lambda e: self.menu_start_race())
        self.root.bind("p", lambda e: self.menu_pause_resume())
        self.root.bind("P", lambda e: self.menu_pause_resume())
        self.root.bind("s", lambda e: self.menu_step())
        self.root.bind("S", lambda e: self.menu_step())

    # ---------- Menu callbacks ----------
    def menu_new_maze(self) -> None:
        if self.state.running:
            self._stop_loop()
        self._reset_maze_only(draw=False)
        self._start_generation()
        self._run_loop()  # animate generation

    def menu_start_race(self) -> None:
        if self.grid is None or not self.grid.ready_for_search():
            messagebox.showinfo("Info", "Generate a maze first.")
            return
        if not any(self.state.tk_algos[name].get() for name in ["BFS", "DFS", "Dijkstra", "A*"]):
            messagebox.showinfo("Info", "Enable at least one algorithm in Pathfinding menu.")
            return
        if self.state.running:
            return
        self._start_race()
        self._run_loop()

    def menu_pause_resume(self) -> None:
        if self.state.running:
            self._stop_loop()
        else:
            self._run_loop()

    def menu_step(self) -> None:
        if self.state.running:
            return
        self._tick()

    def menu_reset_stats(self) -> None:
        for r in self.runners.values():
            r.reset_metrics()
        self.ui.reset_metrics_panel()
        self.ui.draw_all(self.grid, self.runners, full=True)

    def menu_seed_set(self) -> None:
        ans = simpledialog.askstring("Set Seed", "Seed (integer):", parent=self.root)
        if ans is None:
            return
        try:
            val = int(ans)
        except ValueError:
            messagebox.showerror("Error", "Seed must be an integer.")
            return
        self.rng_seed = val
        self.rng = mz.SeededRNG(self.rng_seed)
        self.state.status_seed.set(f"Seed: {val}")
        if self.state.running:
            self._stop_loop()

    def menu_seed_clear(self) -> None:
        self.rng_seed = None
        self.rng = mz.SeededRNG(None)
        self.state.status_seed.set("Seed: ∅")

    def _on_gen_change(self) -> None:
        self.generator_kind = self.state.tk_gen_kind.get()

    def _on_size_change(self) -> None:
        s = self.state.tk_size.get()
        r, c = map(int, s.split("x"))
        self.rows, self.cols = r, c
        if self.state.running:
            self._stop_loop()
        self.grid = mz.Grid(self.rows, self.cols)
        self.ui.resize(self.rows, self.cols)
        self.ui.draw_all(self.grid, self.runners, full=True)

    def _on_algo_toggle(self) -> None:
        for name in self.enabled_algos:
            self.enabled_algos[name] = self.state.tk_algos[name].get()

    # ---------- Lifecycle ----------
    def _reset_maze_only(self, draw: bool = True) -> None:
        self.grid = mz.Grid(self.rows, self.cols)
        self.generator = None
        self.runners = {}
        self.ui.reset_metrics_panel()
        if draw:
            self.ui.draw_all(self.grid, self.runners, full=True)
        self.state.status_mode.set(f"Mode: idle | {self.generator_kind} | {self.rows}x{self.cols}")

    def _start_generation(self) -> None:
        if self.generator_kind == "Prim":
            self.generator = mz.PrimGenerator(self.grid, self.rng)
        else:
            self.generator = mz.KruskalGenerator(self.grid, self.rng)
        self.state.status_mode.set(f"Mode: generating ({self.generator_kind})")
        self.state.running = True
        self.ui.set_controls_enabled(False)

    def _start_race(self) -> None:
        start, goal = self.grid.start, self.grid.goal
        enabled = [name for name, on in self.enabled_algos.items() if on]
        self.runners = {}
        for name in enabled:
            if name == "BFS":
                self.runners[name] = sh.BFS(self.grid, start, goal)
            elif name == "DFS":
                self.runners[name] = sh.DFS(self.grid, start, goal)
            elif name == "Dijkstra":
                self.runners[name] = sh.Dijkstra(self.grid, start, goal)
            elif name == "A*":
                self.runners[name] = sh.AStar(self.grid, start, goal)
        self.state.status_mode.set("Mode: race")
        for r in self.runners.values():
            r.begin()
        self.state.running = True
        self.ui.set_controls_enabled(True)

    def _stop_loop(self) -> None:
        self.state.running = False

    def _run_loop(self) -> None:
        if not self.state.running:
            self.state.running = True
        self._last_frame_time = time.perf_counter()
        self._schedule_next()

    def _schedule_next(self) -> None:
        delay = self.ui.frame_delay_ms.get()
        self.root.after(delay, self._on_frame)

    def _on_frame(self) -> None:
        if not self.state.running:
            return
        self._tick()
        self._schedule_next()

    def _tick(self) -> None:
        # Frame timing
        now = time.perf_counter()
        dt = now - self._last_frame_time
        self._last_frame_time = now
        if dt > 0:
            fps = 1.0 / dt
            self._fps_samples.append(fps)
            if len(self._fps_samples) > 60:
                self._fps_samples.pop(0)
            self.state.status_fps.set(f"FPS: {sum(self._fps_samples)/len(self._fps_samples):.1f}")
        self._frame_counter += 1

        steps = self.ui.steps_per_frame.get()

        # Generation phase
        if self.generator is not None:
            done = False
            for _ in range(steps):
                done = self.generator.step()
                if done:
                    break
            self.ui.draw_dirty(self.grid, self.runners, self.generator.consume_dirty())
            if done:
                self.generator = None
                self.grid.finalize_after_generation()
                self.ui.draw_all(self.grid, self.runners, full=False)
                self.state.status_mode.set("Mode: ready")
            return

        # Race phase
        if self.runners:
            # Interleave each runner steps
            all_done = True
            per_frame_dirty = set()
            for _ in range(steps):
                for r in self.runners.values():
                    if not r.is_done():
                        r.step()
                    per_frame_dirty |= r.consume_dirty()
            # Draw
            self.ui.draw_dirty(self.grid, self.runners, per_frame_dirty)

            # Update per algorithm metrics & FPS
            for name, r in self.runners.items():
                r.frames_drawn += 1
                if len(self._fps_samples) >= 1:
                    r.fps_ema.update(self._fps_samples[-1])
                # Update metrics panel line
                m = r.get_metrics()
                self.ui.update_metrics_row(name, m)

            # Check end
            for r in self.runners.values():
                if not r.is_done():
                    all_done = False
            if all_done:
                self._stop_loop()
                # Post-check correctness and optimality
                self._post_check_correctness()
                self.state.status_mode.set("Mode: done")
            return

    # ---------- Correctness & Export ----------
    def _post_check_correctness(self) -> None:
        # Dijkstra ground truth shortest distance if present
        dij = self.runners.get("Dijkstra")
        gt_len = None
        if dij and dij.path:
            gt_len = len(dij.path) - 1

        for name, r in self.runners.items():
            r.correct_path = sh.validate_path(self.grid, r.path)
            if name in ("Dijkstra", "A*") and gt_len is not None and r.path:
                r.optimal = (len(r.path) - 1) == gt_len
            elif name == "BFS" and gt_len is not None and r.path:
                r.optimal = (len(r.path) - 1) == gt_len
            else:
                r.optimal = False if r.path is None else (name in ("Dijkstra", "A*") and gt_len is not None and (len(r.path)-1) == gt_len)
            # Refresh metrics row
            self.ui.update_metrics_row(name, r.get_metrics())

    def on_export_csv(self) -> None:
        # Gather rows from current state
        rows = []
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        seed = self.rng_seed if self.rng_seed is not None else ""
        gen_name = self.generator_kind
        for name, r in self.runners.items():
            m = r.get_metrics()
            row = {
                "timestamp": timestamp,
                "seed": seed,
                "grid_rows": self.grid.rows,
                "grid_cols": self.grid.cols,
                "generator": gen_name,
                "algo": name,
                "explored": m["explored"],
                "runtime_ms": m["runtime_ms"],
                "path_len": m["path_len"],
                "optimality": m["optimal"],
                "frames_drawn": r.frames_drawn,
                "avg_fps": f"{r.fps_ema.value:.2f}" if r.fps_ema.count > 0 else ""
            }
            rows.append(row)

        # Write CSV next to main.py working directory
        headers = ["timestamp","seed","grid_rows","grid_cols","generator","algo","explored","runtime_ms","path_len","optimality","frames_drawn","avg_fps"]
        fname = f"maze_race_metrics_{int(time.time())}.csv"
        try:
            with open(fname, "w", newline="", encoding="utf-8") as f:
                import csv
                w = csv.DictWriter(f, fieldnames=headers)
                w.writeheader()
                for row in rows:
                    w.writerow(row)
            messagebox.showinfo("Export CSV", f"Wrote {fname}")
        except Exception as e:
            messagebox.showerror("Export CSV", f"Failed: {e}")


def main() -> None:
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
