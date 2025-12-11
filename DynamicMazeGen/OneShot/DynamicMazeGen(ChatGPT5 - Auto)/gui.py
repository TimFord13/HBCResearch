from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Dict, Set, Tuple, Optional
from dataclasses import dataclass, field

Coord = Tuple[int, int]


@dataclass
class UIState:
    running: bool = False
    tk_gen_kind: tk.StringVar = field(default_factory=lambda: tk.StringVar(value="Prim"))
    tk_size: tk.StringVar = field(default_factory=lambda: tk.StringVar(value="41x41"))
    tk_algos: Dict[str, tk.BooleanVar] = field(default_factory=lambda: {
        "BFS": tk.BooleanVar(value=True),
        "DFS": tk.BooleanVar(value=True),
        "Dijkstra": tk.BooleanVar(value=True),
        "A*": tk.BooleanVar(value=True),
    })
    steps_per_frame: tk.IntVar = field(default_factory=lambda: tk.IntVar(value=5))
    frame_delay_ms: tk.IntVar = field(default_factory=lambda: tk.IntVar(value=10))

    show_frontier: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    show_visited: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    show_structs: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=False))
    show_parents: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=False))
    show_path: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    show_weights: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=False))

    status_mode: tk.StringVar = field(default_factory=lambda: tk.StringVar(value="Mode: idle"))
    status_fps: tk.StringVar = field(default_factory=lambda: tk.StringVar(value="FPS: —"))
    status_seed: tk.StringVar = field(default_factory=lambda: tk.StringVar(value="Seed: ∅"))


ALGO_STYLE = {
    "BFS": {"fill": "", "outline": "blue", "dash": (2, 2)},
    "DFS": {"fill": "", "outline": "purple", "dash": (4, 2)},
    "Dijkstra": {"fill": "", "outline": "green", "dash": (1, 1)},
    "A*": {"fill": "", "outline": "red", "dash": (3, 1)},
}
PATH_COLOR = {
    "BFS": "blue",
    "DFS": "purple",
    "Dijkstra": "green",
    "A*": "red",
}


class GUI:
    def __init__(self, root: tk.Tk, rows: int, cols: int, on_export_csv) -> None:
        self.root = root
        self.state = UIState()
        self.rows, self.cols = rows, cols
        self.cell = 14  # pixels per grid square
        self.pad = 8

        # Canvas
        w = self.cols * self.cell + self.pad * 2
        h = self.rows * self.cell + self.pad * 2
        self.canvas = tk.Canvas(root, width=w, height=h, bg="white")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Right panel with controls and metrics
        self.side = ttk.Frame(root)
        self.side.grid(row=0, column=1, sticky="ns")
        ttk.Label(self.side, text="Pathfinding Race", font=("TkDefaultFont", 12, "bold")).pack(pady=4)
        self.metrics = ttk.Treeview(self.side, columns=("status","explored","runtime","path","optimal","avgfps"), show="headings", height=8)
        for i, name in enumerate(["Algo","Explored","Time (ms)","Path","Optimal","Avg FPS"], start=1):
            self.metrics.heading(self.metrics["columns"][i-1], text=name)
            self.metrics.column(self.metrics["columns"][i-1], width=84, anchor="center")
        self.metrics.pack(padx=6, pady=6, fill="x")
        for a in ["BFS","DFS","Dijkstra","A*"]:
            self.metrics.insert("", "end", iid=a, values=(a, "-", "-", "-", "-", "-"))

        btns = ttk.Frame(self.side)
        btns.pack(pady=4)
        ttk.Button(btns, text="Export CSV", command=on_export_csv).grid(row=0, column=0, padx=4)
        ttk.Label(self.side, textvariable=self.state.status_mode).pack(anchor="w", padx=6)
        ttk.Label(self.side, textvariable=self.state.status_fps).pack(anchor="w", padx=6)
        ttk.Label(self.side, textvariable=self.state.status_seed).pack(anchor="w", padx=6)

        # Status bar at bottom
        self.status = ttk.Frame(root)
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Label(self.status, text="Steps/frame").pack(side="left")
        self.steps_scale = ttk.Scale(self.status, from_=1, to=50, orient="horizontal", variable=self.state.steps_per_frame)
        self.steps_scale.pack(side="left", padx=4)
        ttk.Label(self.status, text="Frame delay (ms)").pack(side="left")
        self.delay_scale = ttk.Scale(self.status, from_=0, to=100, orient="horizontal", variable=self.state.frame_delay_ms)
        self.delay_scale.pack(side="left", padx=4)

        self._dirty_cache: Set[Coord] = set()

    # ---------- Menus ----------
    def attach_speed_menu(self, menu: tk.Menu) -> None:
        menu.add_command(label="Steps per frame: use bottom slider")
        menu.add_command(label="Frame delay: use bottom slider")

    def attach_view_menu(self, menu: tk.Menu) -> None:
        menu.add_checkbutton(label="Frontier", variable=self.state.show_frontier)
        menu.add_checkbutton(label="Visited", variable=self.state.show_visited)
        menu.add_checkbutton(label="Open/Queue/Stack", variable=self.state.show_structs)
        menu.add_checkbutton(label="Parent pointers", variable=self.state.show_parents)
        menu.add_checkbutton(label="Winning path(s)", variable=self.state.show_path)
        menu.add_checkbutton(label="Weights", variable=self.state.show_weights)

    def set_controls_enabled(self, enabled: bool) -> None:
        self.steps_scale.configure(state="normal" if enabled else "disabled")
        self.delay_scale.configure(state="normal" if enabled else "disabled")

    # ---------- Drawing ----------
    def resize(self, rows: int, cols: int) -> None:
        self.rows, self.cols = rows, cols
        w = self.cols * self.cell + self.pad * 2
        h = self.rows * self.cell + self.pad * 2
        self.canvas.config(width=w, height=h)
        self.canvas.delete("all")

    def _xy(self, r: int, c: int) -> Tuple[int, int, int, int]:
        x0 = self.pad + c * self.cell
        y0 = self.pad + r * self.cell
        x1 = x0 + self.cell
        y1 = y0 + self.cell
        return x0, y0, x1, y1

    def draw_all(self, grid, runners, full: bool = True) -> None:
        if full:
            self.canvas.delete("all")
            # base cells
            for r in range(grid.rows):
                for c in range(grid.cols):
                    x0,y0,x1,y1 = self._xy(r,c)
                    if grid.grid[r][c] == grid.wall:
                        self.canvas.create_rectangle(x0,y0,x1,y1, fill="black", outline="")
                    else:
                        self.canvas.create_rectangle(x0,y0,x1,y1, fill="white", outline="")
        self._draw_special(grid)
        self._draw_runners(runners)

    def draw_dirty(self, grid, runners, dirty: Set[Coord]) -> None:
        # Only redraw dirty cells to keep FPS high
        for r, c in dirty:
            x0,y0,x1,y1 = self._xy(r,c)
            if grid.grid[r][c] == grid.wall:
                self.canvas.create_rectangle(x0,y0,x1,y1, fill="black", outline="")
            else:
                self.canvas.create_rectangle(x0,y0,x1,y1, fill="white", outline="")
        if dirty:
            self._draw_special(grid)
            self._draw_runners(runners)

    def _draw_special(self, grid) -> None:
        # start & goal
        for rc, color in [(grid.start, "#e0ffe0"), (grid.goal, "#ffe0e0")]:
            x0,y0,x1,y1 = self._xy(*rc)
            self.canvas.create_rectangle(x0,y0,x1,y1, fill=color, outline="")

    def _draw_runners(self, runners) -> None:
        # overlays
        for name, r in runners.items():
            style = ALGO_STYLE.get(name, {"outline":"gray"})
            # visited/explored
            # We approximate visited by using each algorithm's own seen structures when available
            visited = getattr(r, "seen", None)
            if visited:
                for rc in visited:
                    x0,y0,x1,y1 = self._xy(*rc)
                    self.canvas.create_rectangle(x0+2,y0+2,x1-2,y1-2, outline=style["outline"], dash=style.get("dash", None))
            # path
            if r.path:
                for rc in r.path:
                    x0,y0,x1,y1 = self._xy(*rc)
                    self.canvas.create_rectangle(x0+4,y0+4,x1-4,y1-4, outline=PATH_COLOR.get(name, "gray"))

    # ---------- Metrics panel ----------
    def reset_metrics_panel(self) -> None:
        for a in ["BFS","DFS","Dijkstra","A*"]:
            if self.metrics.exists(a):
                self.metrics.item(a, values=(a, "-", "-", "-", "-", "-"))

    def update_metrics_row(self, name: str, m: Dict) -> None:
        if not self.metrics.exists(name):
            self.metrics.insert("", "end", iid=name, values=(name, "-", "-", "-", "-", "-"))
        vals = (name, str(m["explored"]), str(m["runtime_ms"]), str(m["path_len"]), "✔" if m["optimal"] else "✖", "")
        self.metrics.item(name, values=vals)
