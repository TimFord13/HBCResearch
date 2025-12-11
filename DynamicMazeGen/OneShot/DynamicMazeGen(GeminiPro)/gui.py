import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import time
import random
import csv
import datetime
from typing import Optional, Dict, List, Any, Tuple

# Import logic from other files
try:
    import maze
    import search
except ImportError:
    print("Error: Could not import maze.py or search.py.")
    print("Please ensure all files (main.py, gui.py, maze.py, search.py) are in the same directory.")
    # We don't exit, as main.py will catch this if run from there
    # This just prevents crashes in linters/IDEs.
    pass


# --- Constants ---

CELL_SIZE_PX = 10  # Default cell size, will be auto-adjusted
MIN_CELL_SIZE = 2
MAX_CANVAS_WIDTH = 1200
MAX_CANVAS_HEIGHT = 800

# --- Color and Style Definitions ---

COLOR_WALL = "#1a1a1a"
COLOR_PASSAGE = "#f0f0f0"
COLOR_START = "#00c7e0"
COLOR_GOAL = "#ff4136"
COLOR_PATH_FINAL = "yellow"
COLOR_CURRENT = "red"
COLOR_BG = "#333333"

# Per-algorithm styling for overlays and final paths
ALGO_STYLES: Dict[str, Dict[str, str]] = {
    'BFS': {
        'frontier': '#0074D9',  # Blue
        'visited': '#7FDBFF',   # Light Blue
        'path': '#0074D9',
    },
    'DFS': {
        'frontier': '#2ECC40',  # Green
        'visited': '#98FB98',   # Pale Green
        'path': '#2ECC40',
    },
    'Dijkstra': {
        'frontier': '#FF851B',  # Orange
        'visited': '#FFDC00',   # Yellow (using a different yellow)
        'path': '#FF851B',
    },
    'AStar': {
        'frontier': '#B10DC9',  # Purple
        'visited': '#F012BE',   # Pink
        'path': '#B10DC9',
    }
}


class MazeApp(tk.Tk):
    """
    Main application class for the Maze Generator and Pathfinding Visualizer.
    Manages the GUI, application state, and main update loop.
    """
    
    def __init__(self):
        super().__init__()
        self.title("Maze Generation & Pathfinding Race")
        self.geometry("1024x768")
        self.configure(bg=COLOR_BG)

        # --- Core App State ---
        self.grid_obj: Optional[maze.Grid] = None
        self.generator: Optional[maze.BaseMazeGenerator] = None
        self.search_algos: Dict[str, search.SearchAlgorithm] = {}
        self.search_results: List[Dict[str, Any]] = []

        self.app_mode = "IDLE"  # IDLE, GENERATING, RACING, DONE
        self.is_paused = False
        self.current_seed: Optional[int] = None
        self.last_run_metrics: List[Dict[str, Any]] = []

        # --- UI Variables ---
        self.grid_size_var = tk.StringVar(self, "41x41")
        self.maze_algo_var = tk.StringVar(self, "Prim")
        self.path_algos_enabled_var = {
            name: tk.BooleanVar(self, value=True)
            for name in ['BFS', 'DFS', 'Dijkstra', 'AStar']
        }
        self.view_overlay_var = tk.StringVar(self, "BFS")
        self.view_show_paths_var = tk.BooleanVar(self, value=True)
        self.steps_per_frame_var = tk.IntVar(self, value=1)
        self.frame_delay_var = tk.IntVar(self, value=10)

        # --- FPS Counter ---
        self.frame_times: List[float] = []
        self.avg_fps = 0.0
        self.last_frame_time = time.perf_counter()

        # --- Canvas Drawing State ---
        self.canvas: Optional[tk.Canvas] = None
        self.canvas_rects: List[List[Optional[int]]] = []
        self.cell_width = CELL_SIZE_PX
        self.cell_height = CELL_SIZE_PX
        self.path_vis_items: List[int] = [] # Store final path line IDs

        # --- Build UI ---
        self._setup_ui()
        self._bind_keys()
        
        # Start with a default maze
        self.create_new_maze()
        
        # Start the main update loop
        self.update_loop()

    # ------------------------------------------------------------------
    # UI Setup Methods
    # ------------------------------------------------------------------

    def _setup_ui(self):
        """Initializes all GUI components."""
        
        # --- Create main window layout ---
        # Top: Control Panel
        # Middle: Canvas
        # Bottom: Status Bar
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # --- 1. Menu Bar ---
        self._setup_menus()

        # --- 2. Control Panel (Top) ---
        control_frame = tk.Frame(self, bg=COLOR_BG)
        control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self._setup_controls(control_frame)

        # --- 3. Main Content (Middle) ---
        main_frame = tk.Frame(self, bg=COLOR_BG)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=3) # Canvas takes 3/4
        main_frame.grid_columnconfigure(1, weight=1) # Stats take 1/4

        # --- 3a. Canvas ---
        self.canvas_frame = tk.Frame(main_frame, bg=COLOR_BG)
        self.canvas_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.canvas = tk.Canvas(self.canvas_frame, bg=COLOR_WALL,
                                highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        # Handle canvas resizing
        self.canvas_frame.bind("<Configure>", self._on_canvas_resize)

        # --- 3b. Stats Panel (Right) ---
        self.stats_frame = tk.Frame(main_frame, bg=COLOR_BG, width=250)
        self.stats_frame.grid(row=0, column=1, sticky="ns", padx=(5, 0))
        self.stats_frame.grid_propagate(False) # Fix width
        self._setup_stats_panel()

        # --- 4. Status Bar (Bottom) ---
        self.status_bar = tk.Label(
            self, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W,
            fg="white", bg="#222222"
        )
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

    def _setup_menus(self):
        """Creates the top menu bar."""
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        # --- Game Menu ---
        game_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="New Maze (N)", command=self.create_new_maze)
        game_menu.add_command(label="Start Race (R)", command=self.start_race)
        game_menu.add_separator()
        game_menu.add_command(label="Pause/Resume (P)", command=self._on_toggle_pause)
        game_menu.add_command(label="Step (S)", command=self._on_step)
        game_menu.add_separator()
        game_menu.add_command(label="Reset Stats", command=self._reset_stats)
        game_menu.add_command(label="Export CSV", command=self.export_csv)
        game_menu.add_separator()
        game_menu.add_command(label="Quit (Esc)", command=self.quit)

        # --- Maze Menu ---
        maze_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Maze", menu=maze_menu)
        
        algo_menu = tk.Menu(maze_menu, tearoff=0)
        maze_menu.add_cascade(label="Algorithm", menu=algo_menu)
        algo_menu.add_radiobutton(label="Prim's", variable=self.maze_algo_var,
                                  value="Prim", command=self.create_new_maze)
        algo_menu.add_radiobutton(label="Kruskal's", variable=self.maze_algo_var,
                                  value="Kruskal", command=self.create_new_maze)
        
        size_menu = tk.Menu(maze_menu, tearoff=0)
        maze_menu.add_cascade(label="Grid Size", menu=size_menu)
        for size in ["21x21", "31x31", "41x41", "61x61"]:
            size_menu.add_radiobutton(label=size, variable=self.grid_size_var,
                                      value=size, command=self.create_new_maze)
        
        seed_menu = tk.Menu(maze_menu, tearoff=0)
        maze_menu.add_cascade(label="Seed", menu=seed_menu)
        seed_menu.add_command(label="Set Seed...", command=self._on_set_seed)
        seed_menu.add_command(label="Clear Seed", command=self._on_clear_seed)

        # --- Pathfinding Menu ---
        path_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Pathfinding", menu=path_menu)
        for name, var in self.path_algos_enabled_var.items():
            path_menu.add_checkbutton(label=f"Enable {name}", variable=var)

        # --- View Menu ---
        view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="View", menu=view_menu)
        
        overlay_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Show Overlays For...", menu=overlay_menu)
        for name in self.path_algos_enabled_var.keys():
            overlay_menu.add_radiobutton(label=name, variable=self.view_overlay_var,
                                        value=name)
        
        view_menu.add_checkbutton(label="Show Winning Path(s)",
                                  variable=self.view_show_paths_var)

    def _setup_controls(self, parent: tk.Frame):
        """Creates the buttons and sliders in the top control panel."""
        parent.columnconfigure(6, weight=1) # Make sliders expand
        
        def add_button(text, command, col):
            btn = ttk.Button(parent, text=text, command=command)
            btn.grid(row=0, column=col, padx=3, pady=5)
            
        add_button("New Maze (N)", self.create_new_maze, 0)
        add_button("Start Race (R)", self.start_race, 1)
        self.pause_btn = ttk.Button(parent, text="Pause (P)",
                                    command=self._on_toggle_pause)
        self.pause_btn.grid(row=0, column=2, padx=3)
        add_button("Step (S)", self._on_step, 3)
        
        # --- Sliders ---
        def add_slider(text, var, from_, to, col):
            ttk.Label(parent, text=text, foreground="white", background=COLOR_BG
                      ).grid(row=0, column=col, padx=(10, 2), sticky="e")
            slider = ttk.Scale(parent, variable=var, from_=from_, to=to,
                               orient=tk.HORIZONTAL)
            slider.grid(row=0, column=col+1, padx=3, sticky="we")
            
        add_slider("Steps/Frame:", self.steps_per_frame_var, 1, 100, 4)
        add_slider("Frame Delay (ms):", self.frame_delay_var, 0, 200, 6)

    def _setup_stats_panel(self):
        """Creates the dynamic statistics display on the right."""
        
        ttk.Label(self.stats_frame, text="Algorithm Race Stats",
                  font=("Arial", 14, "bold"), anchor="center",
                  foreground="white", background=COLOR_BG
                  ).pack(fill="x", pady=10)
        
        self.stats_widgets: Dict[str, Dict[str, tk.Label]] = {}
        
        header_frame = tk.Frame(self.stats_frame, bg=COLOR_BG)
        header_frame.pack(fill="x", padx=5)
        headers = ["Algo", "Status", "Explored", "Time(ms)", "Path"]
        weights = [2, 2, 3, 3, 2]
        
        for i, (text, w) in enumerate(zip(headers, weights)):
            header_frame.columnconfigure(i, weight=w)
            ttk.Label(header_frame, text=text, font=("Arial", 10, "bold"),
                      foreground="#aaa", background=COLOR_BG, anchor="w"
                      ).grid(row=0, column=i, sticky="w")

        ttk.Separator(self.stats_frame, orient=tk.HORIZONTAL).pack(fill="x", pady=5, padx=5)

        for name in self.path_algos_enabled_var.keys():
            row_frame = tk.Frame(self.stats_frame, bg=COLOR_BG)
            row_frame.pack(fill="x", padx=5, pady=2)
            self.stats_widgets[name] = {}
            
            for i, (key, w) in enumerate(zip(headers, weights)):
                row_frame.columnconfigure(i, weight=w)
                if key == "Algo":
                    text = name
                    color = ALGO_STYLES[name]['path']
                else:
                    text = "---"
                    color = "white"

                lbl = tk.Label(row_frame, text=text, fg=color, bg=COLOR_BG,
                               anchor="w", font=("Consolas", 10))
                lbl.grid(row=0, column=i, sticky="w")
                if key != "Algo":
                    self.stats_widgets[name][key.lower()] = lbl

    def _bind_keys(self):
        """Binds keyboard shortcuts."""
        self.bind("<n>", lambda e: self.create_new_maze())
        self.bind("<r>", lambda e: self.start_race())
        self.bind("<p>", lambda e: self._on_toggle_pause())
        self.bind("<s>", lambda e: self._on_step())
        self.bind("<Escape>", lambda e: self.quit())

    # ------------------------------------------------------------------
    # Core Application Logic & State Management
    # ------------------------------------------------------------------

    def create_new_maze(self):
        """
        Generates a new maze based on current UI settings.
        Resets the application to a pre-race state.
        """
        self.app_mode = "GENERATING"
        self.is_paused = False
        self._reset_stats()
        
        try:
            rows, cols = map(int, self.grid_size_var.get().split('x'))
        except ValueError:
            rows, cols = 41, 41
            self.grid_size_var.set("41x41")

        # Ensure odd dimensions
        rows = rows // 2 * 2 + 1
        cols = cols // 2 * 2 + 1
            
        self.grid_obj = maze.Grid(rows, cols, self.current_seed)
        
        algo_name = self.maze_algo_var.get()
        if algo_name == "Kruskal":
            self.generator = maze.KruskalGenerator(self.grid_obj)
        else:
            self.generator = maze.PrimGenerator(self.grid_obj)
            
        self._init_canvas()
        self.draw_grid()

    def start_race(self):
        """Initializes and starts the pathfinding race."""
        if self.app_mode == "GENERATING":
            messagebox.showwarning("Wait", "Please wait for maze generation to finish.")
            return
        if self.app_mode == "RACING":
            return # Already racing

        if not self.grid_obj:
            self.create_new_maze()

        self._reset_stats()
        self.search_algos = {}
        self.last_run_metrics = []
        
        enabled_algos = [
            name for name, var in self.path_algos_enabled_var.items()
            if var.get()
        ]
        
        if not enabled_algos:
            messagebox.showinfo("No Algorithms", "Please enable at least one pathfinding algorithm from the 'Pathfinding' menu.")
            return

        start = (1, 1)
        goal = (self.grid_obj.rows - 2, self.grid_obj.cols - 2)
        
        for name in enabled_algos:
            if name == 'BFS':
                self.search_algos[name] = search.BFS(self.grid_obj, start, goal)
            elif name == 'DFS':
                self.search_algos[name] = search.DFS(self.grid_obj, start, goal)
            elif name == 'Dijkstra':
                self.search_algos[name] = search.Dijkstra(self.grid_obj, start, goal)
            elif name == 'AStar':
                self.search_algos[name] = search.AStar(self.grid_obj, start, goal)
        
        for algo in self.search_algos.values():
            algo.start_timer()

        self.app_mode = "RACING"
        self.is_paused = False

    def update_loop(self):
        """
        The main non-blocking update loop, driven by `self.after()`.
        """
        # --- 1. Calculate FPS ---
        now = time.perf_counter()
        delta = now - self.last_frame_time
        self.last_frame_time = now
        
        if delta > 0:
            self.frame_times.append(1.0 / delta)
            if len(self.frame_times) > 100:
                self.frame_times.pop(0)
            self.avg_fps = sum(self.frame_times) / len(self.frame_times)

        # --- 2. Update Status Bar ---
        self._update_status_bar()

        # --- 3. Main Logic Step ---
        if not self.is_paused:
            steps = self.steps_per_frame_var.get()
            
            if self.app_mode == "GENERATING":
                self._step_generation(steps)
                
            elif self.app_mode == "RACING":
                self._step_race(steps)

        # --- 4. Drawing ---
        if self.app_mode == "GENERATING":
            self.draw_generation_state()
        elif self.app_mode in ["RACING", "DONE"]:
            self.draw_search_state()
            
        # --- 5. Stats ---
        if self.app_mode in ["RACING", "DONE"]:
            self._update_stats_panel()

        # --- 6. Schedule next frame ---
        delay = self.frame_delay_var.get()
        self.after(delay, self.update_loop)

    def _step_generation(self, steps: int):
        """Advances the maze generation simulation."""
        if not self.generator:
            return
            
        for _ in range(steps):
            if not self.generator.is_done:
                self.generator.step()
            else:
                self.app_mode = "IDLE"
                self.draw_grid() # Final draw
                break

    def _step_race(self, steps: int):
        """Advances the pathfinding race simulation."""
        all_done = True
        
        for algo in self.search_algos.values():
            if not algo.is_finished:
                all_done = False
                for _ in range(steps):
                    if not algo.is_finished:
                        algo.step()
                    else:
                        break # Done with this algo's steps for this frame
        
        if all_done:
            self.app_mode = "DONE"
            self._run_correctness_checks()

    def _run_correctness_checks(self):
        """Compares algorithm results for validity and optimality."""
        self.last_run_metrics = []
        dijkstra_result = self.search_algos.get('Dijkstra')
        optimal_len = -1
        
        if dijkstra_result and dijkstra_result.path_found:
            optimal_len = len(dijkstra_result.get_path())

        for name, algo in self.search_algos.items():
            path = algo.get_path()
            path_len = len(path) if algo.path_found else 0
            
            # 1. Correctness (is path valid?)
            is_valid = self._validate_path(path) if algo.path_found else (not algo.path_found)

            # 2. Optimality
            is_optimal = False
            if algo.path_found:
                if name in ['BFS', 'Dijkstra', 'AStar']:
                    is_optimal = (path_len == optimal_len)
                else: # DFS
                    is_optimal = (path_len == optimal_len) # Mark as optimal if it happens to be
            
            metrics = algo.get_metrics()
            metrics['name'] = name
            metrics['is_valid'] = is_valid
            metrics['is_optimal'] = is_optimal
            metrics['path_len'] = path_len
            
            # Update stats panel with final check
            if not is_valid:
                self.stats_widgets[name]['status'].config(text="INVALID", fg="red")
            elif name in ['BFS', 'Dijkstra', 'AStar'] and not is_optimal:
                self.stats_widgets[name]['status'].config(text="NON-OPTIMAL", fg="red")

            self.last_run_metrics.append(metrics)

    def _validate_path(self, path: List[Tuple[int, int]]) -> bool:
        """Checks if a path is contiguous and follows maze rules."""
        if not path:
            return False
        if not self.grid_obj:
            return False
            
        # Check start and goal
        if path[0] != self.grid_obj.start or path[-1] != self.grid_obj.goal:
            return False
            
        for i in range(len(path)):
            r, c = path[i]
            # Check bounds and walls
            if not self.grid_obj.is_valid(r, c) or self.grid_obj.grid[r][c] == maze.CellType.WALL:
                return False
            # Check contiguity
            if i > 0:
                pr, pc = path[i-1]
                if abs(r - pr) + abs(c - pc) != 1:
                    return False # Not contiguous
        return True

    # ------------------------------------------------------------------
    # Drawing and Visualization
    # ------------------------------------------------------------------

    def _init_canvas(self):
        """Clears and re-initializes the canvas for a new grid."""
        self.canvas.delete("all")
        if not self.grid_obj:
            return

        rows, cols = self.grid_obj.rows, self.grid_obj.cols
        
        # Calculate cell size based on container
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # Add a 1px border/padding
        cell_w = (canvas_w - 1) / cols
        cell_h = (canvas_h - 1) / cols 
        self.cell_width = max(MIN_CELL_SIZE, int(min(cell_w, cell_h)))
        self.cell_height = self.cell_width
        
        # Center the grid
        self.canvas.config(width=cols * self.cell_width,
                           height=rows * self.cell_height)

        self.canvas_rects = [[None] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                x1 = c * self.cell_width
                y1 = r * self.cell_height
                x2 = x1 + self.cell_width
                y2 = y1 + self.cell_height
                self.canvas_rects[r][c] = self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=COLOR_WALL, outline=""
                )

    def _on_canvas_resize(self, event):
        """Handles window resize to redraw the maze."""
        # Only resize if not generating/racing (too slow)
        if self.app_mode in ["IDLE", "DONE"]:
            self._init_canvas()
            self.draw_grid()
            if self.app_mode == "DONE":
                self.draw_search_state() # Redraw paths etc.

    def _update_cell_color(self, r: int, c: int, color: str):
        """Optimized cell color update."""
        rect_id = self.canvas_rects[r][c]
        if rect_id:
            self.canvas.itemconfig(rect_id, fill=color, outline="")

    def draw_grid(self):
        """Draws the entire base maze (walls, passages, start, goal)."""
        if not self.grid_obj or not self.canvas_rects:
            return
            
        for r in range(self.grid_obj.rows):
            for c in range(self.grid_obj.cols):
                cell = self.grid_obj.grid[r][c]
                color = COLOR_WALL if cell == maze.CellType.WALL else COLOR_PASSAGE
                self._update_cell_color(r, c, color)
        
        # Draw start and goal
        self._update_cell_color(self.grid_obj.start[0], self.grid_obj.start[1], COLOR_START)
        self._update_cell_color(self.grid_obj.goal[0], self.grid_obj.goal[1], COLOR_GOAL)

    def draw_generation_state(self):
        """Visualizes the maze *during* generation."""
        if not self.generator or not self.grid_obj:
            return
            
        state = self.generator.get_state_for_drawing()
        
        # Draw changed cells
        for r, c, cell_type in state['changed_cells']:
            color = COLOR_WALL if cell_type == maze.CellType.WALL else COLOR_PASSAGE
            self._update_cell_color(r, c, color)
        
        # Draw frontier
        frontier_color = ALGO_STYLES['BFS']['frontier'] # Just borrow a color
        for r, c in state.get('frontier', []):
            self._update_cell_color(r, c, frontier_color)

        # Draw current (Kruskal's edge)
        current = state.get('current')
        if current:
            r, c = current
            self._update_cell_color(r, c, COLOR_CURRENT)

    def draw_search_state(self):
        """Visualizes the pathfinding race."""
        if not self.grid_obj:
            return
            
        # 1. Redraw base grid first to clear old overlays
        self.draw_grid()
        
        # 2. Clear old path lines
        for item in self.path_vis_items:
            self.canvas.delete(item)
        self.path_vis_items.clear()

        # 3. Draw overlays (Visited/Frontier) for the *selected* algo
        algo_to_view = self.view_overlay_var.get()
        if algo_to_view in self.search_algos and self.app_mode == "RACING":
            algo = self.search_algos[algo_to_view]
            styles = ALGO_STYLES[algo_to_view]
            
            overlay_state = algo.get_state_overlay()
            
            # Draw Visited
            for r, c in overlay_state['visited']:
                if (r,c) != self.grid_obj.start and (r,c) != self.grid_obj.goal:
                    self._update_cell_color(r, c, styles['visited'])

            # Draw Frontier
            for r, c in overlay_state['frontier']:
                if (r,c) != self.grid_obj.start and (r,c) != self.grid_obj.goal:
                    self._update_cell_color(r, c, styles['frontier'])

        # 4. Draw all "current" nodes
        if self.app_mode == "RACING":
            for algo in self.search_algos.values():
                curr = algo.current
                if curr and curr != self.grid_obj.goal:
                    self._update_cell_color(curr[0], curr[1], COLOR_CURRENT)

        # 5. Draw final paths if "DONE"
        if self.app_mode == "DONE" and self.view_show_paths_var.get():
            self._draw_final_paths()

    def _draw_final_paths(self):
        """Draws the final path(s) on the canvas using lines."""
        
        for name, algo in self.search_algos.items():
            if not algo.path_found:
                continue
                
            path = algo.get_path()
            if not path:
                continue

            color = ALGO_STYLES[name]['path']
            width = 3 if name == self.view_overlay_var.get() else 2
            
            # Create a list of pixel coordinates
            coords = []
            for r, c in path:
                x = (c + 0.5) * self.cell_width
                y = (r + 0.5) * self.cell_height
                coords.append(x)
                coords.append(y)
                
            line_id = self.canvas.create_line(
                *coords, fill=color, width=width,
                capstyle=tk.ROUND, joinstyle=tk.ROUND
            )
            self.path_vis_items.append(line_id)

    # ------------------------------------------------------------------
    # UI Updates & Event Handlers
    # ------------------------------------------------------------------

    def _update_status_bar(self):
        """Updates the bottom status bar text."""
        mode_text = self.app_mode.capitalize()
        if self.is_paused:
            mode_text += " (Paused)"
        
        grid_text = f"Grid: {self.grid_size_var.get()}"
        maze_text = f"Maze: {self.maze_algo_var.get()}"
        seed_text = f"Seed: {self.current_seed if self.current_seed else 'None'}"
        fps_text = f"FPS: {self.avg_fps:.1f}"
        
        self.status_bar.config(
            text=f" {mode_text} | {grid_text} | {maze_text} | {seed_text} | {fps_text} "
        )

    def _update_stats_panel(self):
        """Updates the live metrics in the right-hand panel."""
        
        for name, algo in self.search_algos.items():
            widgets = self.stats_widgets.get(name)
            if not widgets:
                continue
            
            metrics = algo.get_metrics()
            
            if algo.is_finished:
                status = "DONE" if algo.path_found else "NO PATH"
                color = "white" if algo.path_found else "orange"
            else:
                status = "Running"
                color = "white"
            
            widgets['status'].config(text=status, fg=color)
            widgets['explored'].config(text=f"{metrics['explored_nodes']}")
            widgets['time(ms)'].config(text=f"{metrics['runtime_ms']:.1f}")
            
            if algo.path_found:
                widgets['path'].config(text=f"{len(algo.get_path())}")
            elif algo.is_finished:
                 widgets['path'].config(text="N/A")

    def _reset_stats(self):
        """Clears the stats panel and internal algorithm states."""
        self.search_algos.clear()
        self.last_run_metrics.clear()
        
        for name, widgets in self.stats_widgets.items():
            widgets['status'].config(text="---", fg="white")
            widgets['explored'].config(text="---")
            widgets['time(ms)'].config(text="---")
            widgets['path'].config(text="---")
            
        # Clear path drawings
        for item in self.path_vis_items:
            self.canvas.delete(item)
        self.path_vis_items.clear()
        
        if self.app_mode == "DONE":
            self.app_mode = "IDLE"
            self.draw_grid() # Redraw to clear overlays

    def _on_toggle_pause(self):
        """Event handler for the Pause/Resume button."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.config(text="Resume (P)")
        else:
            self.pause_btn.config(text="Pause (P)")

    def _on_step(self):
        """Event handler for the Step button."""
        if not self.is_paused:
            self._on_toggle_pause() # Pause first
        
        # Manually advance logic by 1 step
        if self.app_mode == "GENERATING":
            self._step_generation(1)
            self.draw_generation_state()
            
        elif self.app_mode == "RACING":
            self._step_race(1)
            self.draw_search_state()
            self._update_stats_panel()

    def _on_set_seed(self):
        """Opens a dialog to set a deterministic seed."""
        seed_str = simpledialog.askstring("Set Seed",
                                          "Enter seed (integer or text):",
                                          parent=self)
        if seed_str:
            try:
                # Allow text seeds, Python's hash() is stable
                # within a session, but random.seed() can take
                # strings directly.
                self.current_seed = seed_str
            except ValueError:
                messagebox.showerror("Invalid Seed", "Could not use seed.")
                self.current_seed = None
            
            self.create_new_maze() # Regenerate with new seed

    def _on_clear_seed(self):
        """Clears the seed, reverting to random generation."""
        self.current_seed = None
        self.create_new_maze()

    # ------------------------------------------------------------------
    # Data Export
    # ------------------------------------------------------------------

    def export_csv(self):
        """Exports the last run's metrics to a CSV file."""
        if not self.last_run_metrics:
            messagebox.showinfo("No Data", "No race data to export. "
                                "Please run a race to completion first.")
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"maze_race_stats_{timestamp}.csv"
        
        # Prepare common data
        grid_rows, grid_cols = map(int, self.grid_size_var.get().split('x'))
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                header = [
                    "timestamp", "seed", "grid_rows", "grid_cols",
                    "generator", "algo", "explored_nodes", "runtime_ms",
                    "path_len", "path_found", "is_valid", "is_optimal",
                    "avg_fps_during_run" # Note: This is tricky, using overall avg
                ]
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writeheader()
                
                for metrics in self.last_run_metrics:
                    row = {
                        "timestamp": timestamp,
                        "seed": self.current_seed if self.current_seed else "None",
                        "grid_rows": grid_rows,
                        "grid_cols": grid_cols,
                        "generator": self.maze_algo_var.get(),
                        "algo": metrics['name'],
                        "explored_nodes": metrics['explored_nodes'],
                        "runtime_ms": metrics['runtime_ms'],
                        "path_len": metrics['path_len'],
                        "path_found": metrics['path_found'],
                        "is_valid": metrics['is_valid'],
                        "is_optimal": metrics['is_optimal'],
                        "avg_fps_during_run": self.avg_fps
                    }
                    writer.writerow(row)
            
            messagebox.showinfo("Export Successful",
                                f"Successfully exported stats to:\n{filename}")
        
        except IOError as e:
            messagebox.showerror("Export Failed",
                                 f"Could not write to file:\n{e}")
        except Exception as e:
            messagebox.showerror("Export Error", f"An unexpected error occurred: {e}")