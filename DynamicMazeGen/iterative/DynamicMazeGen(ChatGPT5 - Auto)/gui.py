# gui.py
"""
Final GUI for Maze Race (optimized for incremental redraw and deterministic step mode).

Full Chat GPT conversation:
---------------------------------------------------------------
https://chatgpt.com/share/693636e5-2fe4-800b-adf8-5a86724e9ae9
---------------------------------------------------------------
Features:
  - Menu (Game/Run, Maze, Pathfinding, View, Speed)
  - Keyboard shortcuts: N (new), R (start/resume), P (pause), S (step), ESC (quit)
  - Seed management (set/clear) and determinism panel
  - Multi-algorithm race (BFS, DFS, Dijkstra, A*) — enable/disable per-alg
  - Tinted overlays for visited cells, thick frontier border, thick path border
  - Incremental redraw: only repaint dirty cells each frame (dirty set)
  - Instrumentation: per-algo metrics, correctness/optimality checks, FPS, CSV export
  - Step mode: deterministic single interleaved step across enabled algorithms
  - Headless test helper: run_headless_race_test()
Usage:
  python gui.py
"""
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import time
import csv
import os
from datetime import datetime
from functools import partial

from maze import Maze
from search import BFS, DFS, Dijkstra, AStar, NEIGHBORS  # NEIGHBORS used for documentation

# Config
CELL = 12
LOGICAL_DEFAULT = 20
FPS_LIMIT_DEFAULT = 60

ALGO_LIST = ["BFS","DFS","Dijkstra","A*"]
TINT_COLORS = {"BFS":"#4C9F70","DFS":"#4C6B9F","Dijkstra":"#C25C2A","A*":"#9F4C8F"}
BORDER_COLORS = TINT_COLORS.copy()
FRONTIER_THICKNESS = 3
WINNER_COLOR = "#FFD700"

# Utility node extraction
def valid_node(item):
    if not isinstance(item, tuple):
        return None
    if len(item) != 2:
        return None
    r,c = item
    if not (isinstance(r,int) and isinstance(c,int)):
        return None
    return (r,c)

def extract_node(item):
    n = valid_node(item)
    if n:
        return n
    if isinstance(item, tuple) and len(item) >= 2:
        last = item[-1]
        return valid_node(last)
    return None

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Maze Race - Final Build")
        # state
        self.logical = LOGICAL_DEFAULT
        self.cell = CELL
        self.fps_limit = FPS_LIMIT_DEFAULT
        self.seed = None
        self.generator = "prim"
        self.steps_per_frame = tk.IntVar(value=2)
        self.frame_delay_ms = tk.IntVar(value=0)
        self.view_frontier = tk.BooleanVar(value=True)
        self.view_visited = tk.BooleanVar(value=True)
        self.view_parents = tk.BooleanVar(value=False)
        self.view_winners = tk.BooleanVar(value=True)
        self.enable_vars = {a:tk.BooleanVar(value=(a=="BFS")) for a in ALGO_LIST}

        # create maze
        self._apply_seed_var(None)
        self.maze = Maze(self.logical, self.logical, seed=self.seed)
        self._gen_maze(self.generator)

        self.H = self.maze.H; self.W = self.maze.W
        self.start = (1,1); self.goal = (self.H-2, self.W-2)

        # canvas & panels
        self.canvas = tk.Canvas(root, width=self.W*self.cell, height=self.H*self.cell, bg="white")
        self.canvas.grid(row=0,column=0,sticky="nw")
        self.panel = ttk.Frame(root); self.panel.grid(row=0,column=1,sticky="ne",padx=6,pady=6)

        # build UI
        self._build_menu()
        self._build_controls()
        self._build_metrics()

        # searches & metrics
        self.searches = {}
        self.algo_metrics = {}
        self.reset_searches()

        # incremental redraw bookkeeping: we track a set of dirty cells to repaint
        self.dirty = set()   # set of (r,c) internal coords that need repainting
        self.running = False
        self.frames_drawn = 0
        self.frame_timestamps = []
        self.instant_fps = 0.0
        self.avg_fps = 0.0
        self._winners = []

        # keyboard shortcuts
        self._bind_shortcuts()

        # initial draw
        self.draw_full()
        self.update_metrics_ui()

    # ---------------- UI builders ----------------
    def _build_menu(self):
        menu = tk.Menu(self.root); self.root.config(menu=menu)
        gm = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Game/Run", menu=gm)
        gm.add_command(label="New Maze (N)", command=self.new_maze, accelerator="N")
        gm.add_command(label="Start Race (R)", command=self.start_race, accelerator="R")
        gm.add_command(label="Pause/Resume (P)", command=self.pause_resume, accelerator="P")
        gm.add_command(label="Step (S)", command=self.step_once, accelerator="S")
        gm.add_separator(); gm.add_command(label="Reset Stats", command=self.reset_searches)
        gm.add_separator(); gm.add_command(label="Quit (Esc)", command=self.root.quit, accelerator="Esc")

        mm = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Maze", menu=mm)
        mm.add_command(label="Prim's", command=lambda: self.set_generator("prim"))
        mm.add_command(label="Kruskal's", command=lambda: self.set_generator("kruskal"))
        mm.add_separator()
        size_sub = tk.Menu(mm, tearoff=0); mm.add_cascade(label="Grid Size Presets", menu=size_sub)
        size_sub.add_command(label="Small (11x11 int)", command=lambda: self.set_grid_preset(5))
        size_sub.add_command(label="Medium (41x41 int)", command=lambda: self.set_grid_preset(20))
        size_sub.add_command(label="Large (81x81 int)", command=lambda: self.set_grid_preset(40))
        mm.add_separator(); mm.add_command(label="Set Seed...", command=self.dialog_set_seed)
        mm.add_command(label="Clear Seed", command=self.clear_seed)

        pm = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Pathfinding", menu=pm)
        for alg in ALGO_LIST:
            pm.add_checkbutton(label=alg, variable=self.enable_vars[alg], command=self.reset_searches)

        vm = tk.Menu(menu, tearoff=0); menu.add_cascade(label="View", menu=vm)
        vm.add_checkbutton(label="Frontier", variable=self.view_frontier, command=self.draw_full)
        vm.add_checkbutton(label="Visited", variable=self.view_visited, command=self.draw_full)
        vm.add_checkbutton(label="Parents", variable=self.view_parents, command=self.draw_full)
        vm.add_checkbutton(label="Winning Paths", variable=self.view_winners, command=self.draw_full)

    def _build_controls(self):
        fr_gen = ttk.LabelFrame(self.panel, text="Generator & Seed"); fr_gen.grid(sticky="ew")
        ttk.Label(fr_gen, text="Generator:").grid(row=0,column=0,sticky="w")
        self.generator_label = ttk.Label(fr_gen, text=self.generator); self.generator_label.grid(row=0,column=1,sticky="w",padx=6)
        ttk.Label(fr_gen, text="Seed:").grid(row=1,column=0,sticky="w")
        self.seed_display = ttk.Label(fr_gen, text=(str(self.seed) if self.seed is not None else "<random>"))
        self.seed_display.grid(row=1,column=1,sticky="w",padx=6)

        fr_speed = ttk.LabelFrame(self.panel, text="Speed"); fr_speed.grid(sticky="ew", pady=(6,0))
        ttk.Label(fr_speed, text="Steps/frame:").grid(row=0,column=0,sticky="w")
        ttk.Scale(fr_speed, from_=1,to=10, orient="horizontal", variable=self.steps_per_frame).grid(row=0,column=1,sticky="ew")
        ttk.Label(fr_speed, text="Frame delay (ms):").grid(row=1,column=0,sticky="w")
        ttk.Scale(fr_speed, from_=0,to=200, orient="horizontal", variable=self.frame_delay_ms).grid(row=1,column=1,sticky="ew")

        fr_view = ttk.LabelFrame(self.panel, text="View"); fr_view.grid(sticky="ew", pady=(6,0))
        ttk.Checkbutton(fr_view, text="Frontier", variable=self.view_frontier, command=self.draw_full).grid(sticky="w")
        ttk.Checkbutton(fr_view, text="Visited", variable=self.view_visited, command=self.draw_full).grid(sticky="w")
        ttk.Checkbutton(fr_view, text="Parents", variable=self.view_parents, command=self.draw_full).grid(sticky="w")
        ttk.Checkbutton(fr_view, text="Highlight winners", variable=self.view_winners, command=self.draw_full).grid(sticky="w")

        fr_act = ttk.Frame(self.panel); fr_act.grid(sticky="ew", pady=(6,0))
        ttk.Button(fr_act, text="New Maze", command=self.new_maze).grid(sticky="ew")
        ttk.Button(fr_act, text="Start Race", command=self.start_race).grid(sticky="ew", pady=(4,0))
        ttk.Button(fr_act, text="Pause/Resume", command=self.pause_resume).grid(sticky="ew", pady=(4,0))
        ttk.Button(fr_act, text="Step", command=self.step_once).grid(sticky="ew", pady=(4,0))
        ttk.Button(fr_act, text="Reset Stats", command=self.reset_searches).grid(sticky="ew", pady=(4,0))
        ttk.Button(fr_act, text="Export CSV", command=self.export_csv).grid(sticky="ew", pady=(6,0))

        # algorithm selection checkboxes
        fr_algos = ttk.LabelFrame(self.panel, text="Algorithms")
        fr_algos.grid(sticky="ew", pady=(4, 4))

        for alg in ALGO_LIST:
            ttk.Checkbutton(
                fr_algos,
                text=alg,
                variable=self.enable_vars[alg],
                command=self.reset_searches
            ).grid(sticky="w")

    def _build_metrics(self):
        fr = ttk.LabelFrame(self.panel, text="Metrics"); fr.grid(sticky="ew", pady=(6,0))
        self.metric_rows = {}
        font = ("Consolas",10)
        labels = ["Alg","Status","Expl","Time(ms)","Path","Len","Opt"]
        widths = [8,10,8,10,6,5,6]
        hdr = ttk.Frame(fr); hdr.grid(row=0,column=0,sticky="ew")
        for i,(t,w) in enumerate(zip(labels,widths)):
            ttk.Label(hdr, text=t, width=w, font=font).grid(row=0,column=i)
        for r,alg in enumerate(ALGO_LIST, start=1):
            rowf = ttk.Frame(fr); rowf.grid(row=r,column=0,sticky="ew")
            ttk.Label(rowf, text=alg, width=8, font=font, foreground=TINT_COLORS[alg]).grid(row=0,column=0)
            s = ttk.Label(rowf, text="idle", width=10, font=font); s.grid(row=0,column=1)
            e = ttk.Label(rowf, text="0", width=8, font=font); e.grid(row=0,column=2)
            t = ttk.Label(rowf, text="0.0", width=10, font=font); t.grid(row=0,column=3)
            p = ttk.Label(rowf, text="no", width=6, font=font); p.grid(row=0,column=4)
            ln = ttk.Label(rowf, text="0", width=5, font=font); ln.grid(row=0,column=5)
            opt = ttk.Label(rowf, text="?", width=6, font=font); opt.grid(row=0,column=6)
            self.metric_rows[alg] = {"status":s,"expl":e,"time":t,"path":p,"len":ln,"opt":opt}
        self.status_label = ttk.Label(self.panel, text="FPS:0 | Frames:0", font=("Consolas",10))
        self.status_label.grid(sticky="ew", pady=(6,0))

    # ---------------- menu actions & helpers ----------------
    def set_generator(self, g):
        self.generator = g
        self.generator_label.config(text=g)
        self.new_maze()

    def set_grid_preset(self, logical):
        self.logical = logical
        self.new_maze()

    def dialog_set_seed(self):
        s = simpledialog.askstring("Set Seed","Enter integer seed (blank => random):",parent=self.root)
        if s is None:
            return
        s = s.strip()
        if s=="":
            self.clear_seed()
            return
        try:
            v = int(s)
        except:
            messagebox.showerror("Seed","Must be integer")
            return
        self.seed = v
        self.seed_display.config(text=str(self.seed))
        self.new_maze()

    def clear_seed(self):
        self.seed = None
        self.seed_display.config(text="<random>")
        self.new_maze()

    def _apply_seed_var(self, val):
        # placeholder if more interactions needed
        pass

    def _gen_maze(self,generator):
        if generator == "kruskal":
            self.maze.generate_kruskal()
        else:
            self.maze.generate_prim()
        if hasattr(self,"seed_display"):
            self.seed_display.config(text=(str(self.seed) if self.seed is not None else "<random>"))

    def new_maze(self):
        # recreate maze instance with current seed and logical
        self.maze = Maze(self.logical, self.logical, seed=self.seed)
        self._gen_maze(self.generator)
        self.H,self.W = self.maze.H,self.maze.W
        self.start=(1,1); self.goal=(self.H-2,self.W-2)
        self.canvas.config(width=self.W*self.cell, height=self.H*self.cell)
        # reset searches and redraw all
        self.reset_searches()
        self.draw_full()
        self.update_metrics_ui()

    # ---------------- searches lifecycle ----------------
    def _create_search(self, alg):
        if alg=="BFS": return BFS(self.maze,self.start,self.goal)
        if alg=="DFS": return DFS(self.maze,self.start,self.goal)
        if alg=="Dijkstra": return Dijkstra(self.maze,self.start,self.goal)
        if alg=="A*": return AStar(self.maze,self.start,self.goal)
        return None

    def reset_searches(self):
        self.searches={}
        self.algo_metrics={}
        for alg in ALGO_LIST:
            if self.enable_vars[alg].get():
                self.searches[alg]=self._create_search(alg)
                self.algo_metrics[alg]={"start_time":None,"end_time":None,"runtime_ms":0.0,
                                       "steps_executed":0,"nodes_explored":0,"path_len":0,"optimal":None}
            else:
                self.searches[alg]=None
                self.algo_metrics[alg]={"start_time":None,"end_time":None,"runtime_ms":0.0,
                                       "steps_executed":0,"nodes_explored":0,"path_len":0,"optimal":None}
        self.running=False
        self.frames_drawn=0
        self.frame_timestamps=[]
        self.instant_fps=0.0
        self.avg_fps=0.0
        self.dirty=set()
        self._winners=[]
        # mark all cells dirty for full redraw
        for r in range(self.H):
            for c in range(self.W):
                self.dirty.add((r,c))

    # ---------------- stepping & frame loop ----------------
    def start_race(self):
        if not any(self.searches.values()):
            self.reset_searches()
        self.running=True
        self._frame_loop_once()

    def pause_resume(self):
        self.running = not self.running
        if self.running:
            self._frame_loop_once()

    def step_once(self):
        # deterministic step mode: one interleaved step of each active algorithm
        for alg in ALGO_LIST:
            s = self.searches.get(alg)
            if s is None:
                continue
            m = self.algo_metrics[alg]
            if m["start_time"] is None:
                m["start_time"]=time.time()
            if not s.is_done():
                try:
                    s.step()
                except Exception as e:
                    print("step error",alg,e); s.done=True
                m["steps_executed"]+=1
                m["nodes_explored"] = getattr(s,"explored_count", len(getattr(s,"visited", set())))
                m["runtime_ms"] = getattr(s,"runtime_ms", m["runtime_ms"])
                if s.is_done():
                    m["end_time"]=time.time()
                    path = s.get_path() or []
                    m["path_len"]=len(path)
                    m["optimal"] = (len(path)==self.compute_ground_truth_dijkstra()) if path else None
        self._compute_winners()
        # mark dirty cells for updates based on visited/frontier/path
        self._mark_all_dynamic_dirty()
        self._repaint_dirty()
        self.update_metrics_ui()

    def _frame_loop_once(self):
        delay = int(self.frame_delay_ms.get())
        # perform steps_per_frame rounds, each round calls step() on each active algorithm once (interleaved)
        steps = max(1, int(self.steps_per_frame.get()))
        for _ in range(steps):
            for alg in ALGO_LIST:
                s = self.searches.get(alg)
                if s is None or s.is_done():
                    continue
                m = self.algo_metrics[alg]
                if m["start_time"] is None:
                    m["start_time"]=time.time()
                try:
                    s.step()
                except Exception as e:
                    print("step error",alg,e); s.done=True
                m["steps_executed"]+=1
                m["nodes_explored"] = getattr(s,"explored_count", len(getattr(s,"visited", set())))
                m["runtime_ms"] = getattr(s,"runtime_ms", m["runtime_ms"])
                if s.is_done():
                    m["end_time"]=time.time()
                    path = s.get_path() or []
                    m["path_len"]=len(path)
                    m["optimal"] = (len(path)==self.compute_ground_truth_dijkstra()) if path else None
        # compute winners (shortest path length)
        self._compute_winners()
        # update dirty based on dynamic sets
        self._mark_all_dynamic_dirty()
        # repaint changed cells only
        self._repaint_dirty()
        self.update_metrics_ui()
        # update fps & schedule next
        now = time.time()
        self.frames_drawn += 1
        self.frame_timestamps.append(now)
        cutoff=now-10.0
        self.frame_timestamps=[t for t in self.frame_timestamps if t>=cutoff]
        if len(self.frame_timestamps)>=2:
            dt=self.frame_timestamps[-1]-self.frame_timestamps[-2]
            self.instant_fps = (1.0/dt) if dt>0 else 0.0
            total = self.frame_timestamps[-1]-self.frame_timestamps[0]
            self.avg_fps = (len(self.frame_timestamps)-1)/total if total>0 else self.instant_fps
        else:
            self.instant_fps = 0.0; self.avg_fps = 0.0
        # schedule next call if running
        if self.running:
            if delay>0:
                self.root.after(delay, self._frame_loop_once)
            else:
                # honor fps cap
                self.root.after(int(1000/max(1,self.fps_limit)), self._frame_loop_once)

    # ---------------- repaint optimization ----------------
    def _mark_all_dynamic_dirty(self):
        # mark all visited/frontier/path cells as dirty
        for alg,s in self.searches.items():
            if s is None: continue
            if self.view_visited.get():
                for node in getattr(s,"visited", set()):
                    n = valid_node(node)
                    if n: self.dirty.add(n)
            if self.view_frontier.get():
                front = getattr(s,"frontier", [])
                try: items = list(front)
                except: items = []
                for item in items:
                    n = extract_node(item)
                    if n: self.dirty.add(n)
            if s.is_done():
                for node in s.get_path():
                    n = valid_node(node)
                    if n: self.dirty.add(n)

    def _repaint_dirty(self):
        if not self.dirty:
            return
        # repaint only dirty cells: first redraw background for each dirty cell, then overlays as needed
        dirty_now = list(self.dirty)
        self.dirty.clear()
        for (r,c) in dirty_now:
            # draw background
            fill = "black" if self.maze._grid[r][c]==1 else "white"
            x1,y1 = c*self.cell, r*self.cell
            x2,y2 = x1+self.cell, y1+self.cell
            # we use a single rectangle per cell with tag cell_r_c to replace previous
            tag = f"cell_{r}_{c}"
            self.canvas.delete(tag)
            self.canvas.create_rectangle(x1,y1,x2,y2, fill=fill, outline="", tags=(tag,))
        # After base background, draw overlays for these cells for each algorithm (so overlays are layered)
        for (r,c) in dirty_now:
            # visited tints
            for alg,s in self.searches.items():
                if s is None: continue
                if self.view_visited.get() and (r,c) in getattr(s,"visited", set()):
                    color = TINT_COLORS.get(alg,"#cccccc")
                    # draw stippled rectangle overlay tagged dyn_cell_r_c_alg to allow deletion
                    tagov = f"ov_{alg}_{r}_{c}"
                    self.canvas.delete(tagov)
                    x1,y1 = c*self.cell, r*self.cell
                    x2,y2 = x1+self.cell, y1+self.cell
                    self.canvas.create_rectangle(x1,y1,x2,y2, fill=color, stipple="gray50", outline="", tags=(tagov,))
            # frontier borders
            for alg,s in self.searches.items():
                if s is None: continue
                if not self.view_frontier.get(): continue
                front = getattr(s,"frontier", [])
                nodes=[]
                try: nodes = [extract_node(it) for it in list(front)]
                except: nodes=[]
                if (r,c) in nodes:
                    col = BORDER_COLORS.get(alg,"#000000")
                    tagb = f"fr_{alg}_{r}_{c}"
                    self.canvas.delete(tagb)
                    x1,y1 = c*self.cell, r*self.cell
                    x2,y2 = x1+self.cell, y1+self.cell
                    self.canvas.create_rectangle(x1,y1,x2,y2, outline=col, width=FRONTIER_THICKNESS, tags=(tagb,))
            # path borders
            for alg,s in self.searches.items():
                if s is None: continue
                if not s.is_done(): continue
                for node in s.get_path():
                    if valid_node(node)==(r,c):
                        # winner highlight overrides if present
                        if self.view_winners.get() and alg in self._winners:
                            col = WINNER_COLOR
                        else:
                            col = BORDER_COLORS.get(alg,"#000000")
                        tagp = f"p_{alg}_{r}_{c}"
                        self.canvas.delete(tagp)
                        inset = max(1,self.cell//6)
                        x1 = c*self.cell+inset; y1 = r*self.cell+inset
                        x2 = (c+1)*self.cell-inset; y2 = (r+1)*self.cell-inset
                        self.canvas.create_rectangle(x1,y1,x2,y2, outline=col, width=3, tags=(tagp,))
        # ensure start/goal on top
        self._draw_start_goal()

    def _draw_start_goal(self):
        # delete existing start/goal tags and redraw
        self.canvas.delete("start")
        self.canvas.delete("goal")
        sr,sc = self.start; gr,gc = self.goal
        x1,y1 = sc*self.cell, sr*self.cell
        x2,y2 = x1+self.cell, y1+self.cell
        self.canvas.create_rectangle(x1,y1,x2,y2, fill="green", outline="", tags=("start",))
        x1,y1 = gc*self.cell, gr*self.cell
        x2,y2 = x1+self.cell, y1+self.cell
        self.canvas.create_rectangle(x1,y1,x2,y2, fill="red", outline="", tags=("goal",))

    # ---------------- drawing full (initial) ----------------
    def draw_full(self):
        self.canvas.delete("all")
        for r in range(self.H):
            for c in range(self.W):
                fill = "black" if self.maze._grid[r][c]==1 else "white"
                x1,y1 = c*self.cell, r*self.cell
                x2,y2 = x1+self.cell, y1+self.cell
                tag = f"cell_{r}_{c}"
                self.canvas.create_rectangle(x1,y1,x2,y2, fill=fill, outline="", tags=(tag,))
        self._draw_start_goal()

    # ---------------- metrics & correctness ----------------
    def update_metrics_ui(self):
        for alg in ALGO_LIST:
            row = self.metric_rows[alg]
            s = self.searches.get(alg)
            if s is None:
                row["status"].config(text="off")
                row["expl"].config(text="-")
                row["time"].config(text="-")
                row["path"].config(text="-")
                row["len"].config(text="-")
                row["opt"].config(text="-")
                continue
            status = "done" if s.is_done() else "run"
            row["status"].config(text=status)
            m = s.get_metrics()
            row["expl"].config(text=str(m["explored"]))
            row["time"].config(text=f"{m['runtime_ms']:.1f}")
            p = s.get_path()
            row["path"].config(text="yes" if p else "no")
            row["len"].config(text=str(len(p)))
            # optimal flag from algo_metrics
            am = self.algo_metrics.get(alg,{})
            opt = am.get("optimal", None)
            if opt is True: txt="yes"
            elif opt is False: txt="no"
            else: txt="?"
            row["opt"].config(text=txt)
        # status label
        self.status_label.config(text=f"FPS: {self.instant_fps:.1f} (avg {self.avg_fps:.1f}) | Frames: {self.frames_drawn}")

    def verify_path(self, path):
        if not path: return False
        prev = path[0]
        if valid_node(prev) is None: return False
        for i,node in enumerate(path):
            v = valid_node(node)
            if v is None: return False
            r,c = v
            if not (0<=r<self.H and 0<=c<self.W): return False
            if self.maze._grid[r][c]==1: return False
            if i>0 and (abs(node[0]-prev[0])+abs(node[1]-prev[1])!=1): return False
            prev=node
        return True

    def compute_ground_truth_dijkstra(self):
        try:
            dj = Dijkstra(self.maze, self.start, self.goal)
            while not dj.is_done():
                dj.step()
            path = dj.get_path()
            return len(path) if path else None
        except Exception as e:
            print("GT Dijkstra error",e); return None

    def _compute_winners(self):
        best=None; wins=[]
        for alg in ALGO_LIST:
            s = self.searches.get(alg)
            if s is None: continue
            p = s.get_path()
            if not p: continue
            ln = len(p)
            if best is None or ln<best:
                best=ln; wins=[alg]
            elif ln==best:
                wins.append(alg)
        self._winners = wins

    # ---------------- CSV export ----------------
    def export_csv(self):
        fname="maze_race_results.csv"
        hdr=["timestamp","seed","rows","cols","generator","algorithm","explored","runtime_ms","path_len","optimality","frames_drawn","avg_fps"]
        ts = datetime.utcnow().isoformat()
        rows=[]
        for alg in ALGO_LIST:
            m = self.algo_metrics.get(alg,{})
            if self.searches.get(alg) is None:
                explored="-" ; runtime="-" ; plen="-" ; opt="-"
            else:
                explored = m.get("nodes_explored",0)
                runtime = m.get("runtime_ms",0.0)
                plen = m.get("path_len",0)
                opt = m.get("optimal","")
            rows.append([ts, str(self.seed) if self.seed is not None else "<random>", str(self.logical), str(self.logical), self.generator, alg, explored, runtime, plen, opt, self.frames_drawn, f"{self.avg_fps:.2f}"])
        write_hdr = not os.path.exists(fname)
        try:
            with open(fname,"a",newline="") as f:
                w=csv.writer(f)
                if write_hdr: w.writerow(hdr)
                for r in rows: w.writerow(r)
            messagebox.showinfo("Export CSV", f"Wrote {fname}")
        except Exception as e:
            messagebox.showerror("Export CSV", f"Failed: {e}")

    # ---------------- menu bindings ----------------
    def _bind_shortcuts(self):
        self.root.bind_all("<Key-n>", lambda e: self.new_maze())
        self.root.bind_all("<Key-N>", lambda e: self.new_maze())
        self.root.bind_all("<Key-r>", lambda e: self.start_race())
        self.root.bind_all("<Key-R>", lambda e: self.start_race())
        self.root.bind_all("<Key-p>", lambda e: self.pause_resume())
        self.root.bind_all("<Key-P>", lambda e: self.pause_resume())
        self.root.bind_all("<Key-s>", lambda e: self.step_once())
        self.root.bind_all("<Key-S>", lambda e: self.step_once())
        self.root.bind_all("<Escape>", lambda e: self.root.quit())

    # ---------------- headless test helper (reused) ----------------
def run_headless_race_test(seed=42, logical=20, enabled_algos=None, max_steps=200000):
    if enabled_algos is None: enabled_algos=ALGO_LIST.copy()
    maze = Maze(logical, logical, seed=seed)
    maze.generate_prim()
    H,W = maze.H, maze.W
    start=(1,1); goal=(H-2,W-2)
    searches={}
    for alg in ALGO_LIST:
        if alg in enabled_algos:
            if alg=="BFS": searches[alg]=BFS(maze,start,goal)
            elif alg=="DFS": searches[alg]=DFS(maze,start,goal)
            elif alg=="Dijkstra": searches[alg]=Dijkstra(maze,start,goal)
            elif alg=="A*": searches[alg]=AStar(maze,start,goal)
        else: searches[alg]=None
    metrics={alg:{"steps":0,"nodes":0,"time":0.0,"path":None} for alg in ALGO_LIST}
    steps=0
    while steps<max_steps:
        all_done=True
        for alg,s in searches.items():
            if s is None: continue
            if not s.is_done():
                all_done=False
                s.step()
                metrics[alg]["steps"]+=1
                metrics[alg]["nodes"]=getattr(s,"explored_count",len(getattr(s,"visited",set())))
                metrics[alg]["time"]=getattr(s,"runtime_ms",metrics[alg]["time"])
            else:
                if metrics[alg]["path"] is None:
                    metrics[alg]["path"]=s.get_path()
        if all_done: break
        steps+=1
    # GT
    dj = Dijkstra(maze,start,goal)
    while not dj.is_done(): dj.step()
    gt = dj.get_path(); gt_len = len(gt) if gt else None
    results={}
    for alg in ALGO_LIST:
        p = metrics[alg]["path"]
        def ok(pth):
            if not pth: return False
            prev=pth[0]
            for i,node in enumerate(pth):
                if valid_node(node) is None: return False
                r,c=node
                if not (0<=r<H and 0<=c<W): return False
                if maze._grid[r][c]==1: return False
                if i>0 and abs(node[0]-prev[0])+abs(node[1]-prev[1])!=1: return False
                prev=node
            return True
        results[alg]={"steps":metrics[alg]["steps"], "nodes":metrics[alg]["nodes"], "time":metrics[alg]["time"], "path_len": len(p) if p else 0, "correct": ok(p), "optimal": (len(p)==gt_len) if (p and gt_len is not None) else None}
    return results

# Entry point
def main():
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
