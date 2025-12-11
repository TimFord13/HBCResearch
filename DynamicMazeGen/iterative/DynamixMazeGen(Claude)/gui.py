# gui.py
"""
================================================================================
MULTI-ALGORITHM PATHFINDING RACE - MAIN GUI
================================================================================

Chat log:
https://claude.ai/share/764e55ce-d046-4d3b-81e0-d4e3a9ea6008


DETERMINISM & REPRODUCIBILITY:
------------------------------
When a seed is set, all randomness is deterministic and reproducible:

1. MAZE GENERATION:
   - Prim's: Random wall selection uses seeded RNG
   - Kruskal's: Wall list shuffle uses seeded RNG
   - Tie-breaking: Lexicographic order for walls before random selection

2. PATHFINDING ALGORITHMS:
   - Neighbor exploration order: ALWAYS up, right, down, left (deterministic)
   - BFS: Queue order deterministic (FIFO)
   - DFS: Stack order deterministic (LIFO with reversed neighbor addition)
   - Dijkstra: Heap tie-breaking via counter (insertion order)
   - A*: Heap tie-breaking via counter (insertion order)

3. VERIFICATION:
   - Fixed seed → Identical maze generation
   - Fixed seed → Identical exploration patterns
   - Fixed seed → Identical exported CSV metrics

MENU STRUCTURE:
--------------
Game/Run:
  - New Maze (N): Generate new maze with current settings
  - Start Race (R): Begin algorithm race
  - Pause/Resume (P): Toggle race execution
  - Step (S): Execute one step for all algorithms
  - Reset Stats: Clear metrics and redraw maze
  - Export CSV: Save metrics to timestamped CSV file
  - Quit (ESC): Exit application

Maze:
  - Prim's Algorithm: Generate using Prim's
  - Kruskal's Algorithm: Generate using Kruskal's
  - Grid Size: 11×11, 21×21, 31×31, 41×41, 51×51
  - Set Seed: Enter seed for deterministic generation
  - Clear Seed: Return to random generation

Pathfinding:
  - Enable/disable individual algorithms (BFS, DFS, Dijkstra, A*)

View:
  - Toggle Frontier: Show/hide algorithm frontiers
  - Toggle Visited: Show/hide visited cells
  - Toggle Paths: Show/hide solution paths
  - Highlight Winners: Highlight optimal paths after completion

KEYBOARD SHORTCUTS:
------------------
N - New Maze
R - Start/Resume Race
P - Pause
S - Step
ESC - Quit

CSV EXPORT FORMAT:
-----------------
Columns: timestamp, seed, rows, cols, generator, algorithm, nodes_explored,
         runtime_ms, path_len, path_found, path_valid, path_optimal,
         optimal_path_len, steps_executed, frames_drawn, avg_fps

================================================================================
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Optional, Dict, List, Tuple
import time
import csv
from datetime import datetime
from dataclasses import dataclass

from maze import Maze, CellType
from search import BFS, DFS, Dijkstra, AStar, SearchStatus


@dataclass
class AlgorithmMetrics:
    """Comprehensive metrics for a single algorithm run."""
    algorithm: str
    start_time: float
    end_time: Optional[float] = None
    runtime_ms: float = 0.0
    steps_executed: int = 0
    nodes_explored: int = 0
    path_len: int = 0
    path_found: bool = False
    path_valid: bool = False
    path_optimal: bool = False
    optimal_path_len: Optional[int] = None
    
    def update_from_search(self, search):
        """Update metrics from search instance."""
        metrics = search.get_metrics()
        self.nodes_explored = metrics['explored']
        self.runtime_ms = metrics['runtime_ms']
        
        if search.is_done():
            self.end_time = time.perf_counter()
            
            if search.status == SearchStatus.FOUND:
                path = search.get_path()
                self.path_len = len(path)
                self.path_found = True
            else:
                self.path_found = False


class CorrectnessChecker:
    """Verify correctness of pathfinding results."""
    
    @staticmethod
    def verify_path(maze: Maze, path: List[Tuple[int, int]], start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[bool, str]:
        """Verify that a path is valid."""
        if not path:
            return False, "Path is empty"
        
        if path[0] != start:
            return False, f"Path doesn't start at start position"
        
        if path[-1] != goal:
            return False, f"Path doesn't end at goal position"
        
        for i in range(len(path)):
            cell = path[i]
            
            if not (0 <= cell[0] < maze.cell_rows and 0 <= cell[1] < maze.cell_cols):
                return False, f"Cell out of bounds"
            
            grid_r, grid_c = 2 * cell[0] + 1, 2 * cell[1] + 1
            if not maze.is_passage(grid_r, grid_c):
                return False, f"Cell is a wall"
            
            if i < len(path) - 1:
                next_cell = path[i + 1]
                
                dist = abs(cell[0] - next_cell[0]) + abs(cell[1] - next_cell[1])
                if dist != 1:
                    return False, f"Path not contiguous"
                
                wall_r = (2 * cell[0] + 1 + 2 * next_cell[0] + 1) // 2
                wall_c = (2 * cell[1] + 1 + 2 * next_cell[1] + 1) // 2
                
                if not maze.is_passage(wall_r, wall_c):
                    return False, f"Wall between cells"
        
        return True, "Path is valid"
    
    @staticmethod
    def check_optimality(path_len: int, optimal_len: int) -> bool:
        """Check if path length is optimal."""
        return path_len == optimal_len if optimal_len > 0 else False


class MetricsCollector:
    """Collect and manage metrics for all algorithms."""
    
    def __init__(self):
        self.algorithm_metrics: Dict[str, AlgorithmMetrics] = {}
        self.maze_seed: Optional[int] = None
        self.maze_rows: int = 0
        self.maze_cols: int = 0
        self.maze_generator: str = ""
        self.race_start_time: float = 0
        self.frames_drawn: int = 0
        self.frame_times: List[float] = []
        self.optimal_path_length: Optional[int] = None
    
    def start_race(self, algorithms: List[str], maze: Maze, generator: str, seed: Optional[int]):
        """Initialize metrics for a new race."""
        self.race_start_time = time.perf_counter()
        self.frames_drawn = 0
        self.frame_times = []
        self.maze_seed = seed
        self.maze_rows = maze.cell_rows
        self.maze_cols = maze.cell_cols
        self.maze_generator = generator
        self.optimal_path_length = None
        
        current_time = time.perf_counter()
        self.algorithm_metrics = {
            algo: AlgorithmMetrics(algorithm=algo, start_time=current_time)
            for algo in algorithms
        }
    
    def record_frame(self, frame_time: float):
        """Record a frame draw time."""
        self.frames_drawn += 1
        self.frame_times.append(frame_time)
        
        if len(self.frame_times) > 60:
            self.frame_times.pop(0)
    
    def get_fps_stats(self) -> Tuple[float, float]:
        """Get FPS statistics."""
        if not self.frame_times:
            return 0.0, 0.0
        
        instant_fps = 1.0 / self.frame_times[-1] if self.frame_times[-1] > 0 else 0.0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        avg_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
        
        return instant_fps, avg_fps
    
    def update_algorithm(self, algo_name: str, search, maze: Maze):
        """Update metrics for an algorithm."""
        if algo_name not in self.algorithm_metrics:
            return
        
        metrics = self.algorithm_metrics[algo_name]
        metrics.steps_executed += 1
        metrics.update_from_search(search)
        
        if search.is_done() and search.status == SearchStatus.FOUND and not metrics.path_valid:
            path = search.get_path()
            is_valid, _ = CorrectnessChecker.verify_path(maze, path, maze.start, maze.goal)
            metrics.path_valid = is_valid
    
    def check_all_optimality(self):
        """Check optimality for all algorithms after race completes."""
        if self.optimal_path_length is None:
            if 'Dijkstra' in self.algorithm_metrics:
                dijkstra_metrics = self.algorithm_metrics['Dijkstra']
                if dijkstra_metrics.path_found:
                    self.optimal_path_length = dijkstra_metrics.path_len
        
        if self.optimal_path_length:
            for metrics in self.algorithm_metrics.values():
                if metrics.path_found:
                    metrics.optimal_path_len = self.optimal_path_length
                    metrics.path_optimal = CorrectnessChecker.check_optimality(
                        metrics.path_len, self.optimal_path_length
                    )
    
    def export_to_csv(self, filename: str = None):
        """Export metrics to CSV file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.csv"
        
        _, avg_fps = self.get_fps_stats()
        
        headers = [
            'timestamp', 'seed', 'rows', 'cols', 'generator', 'algorithm',
            'nodes_explored', 'runtime_ms', 'path_len', 'path_found',
            'path_valid', 'path_optimal', 'optimal_path_len', 'steps_executed',
            'frames_drawn', 'avg_fps'
        ]
        
        timestamp = datetime.now().isoformat()
        
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for metrics in self.algorithm_metrics.values():
                    row = {
                        'timestamp': timestamp,
                        'seed': self.maze_seed if self.maze_seed is not None else '',
                        'rows': self.maze_rows,
                        'cols': self.maze_cols,
                        'generator': self.maze_generator,
                        'algorithm': metrics.algorithm,
                        'nodes_explored': metrics.nodes_explored,
                        'runtime_ms': f"{metrics.runtime_ms:.2f}",
                        'path_len': metrics.path_len if metrics.path_found else '',
                        'path_found': metrics.path_found,
                        'path_valid': metrics.path_valid if metrics.path_found else '',
                        'path_optimal': metrics.path_optimal if metrics.path_found else '',
                        'optimal_path_len': metrics.optimal_path_len if metrics.optimal_path_len else '',
                        'steps_executed': metrics.steps_executed,
                        'frames_drawn': self.frames_drawn,
                        'avg_fps': f"{avg_fps:.2f}"
                    }
                    writer.writerow(row)
            
            return True, filename
        except Exception as e:
            return False, str(e)


class MultiAlgorithmGUI:
    """GUI for multi-algorithm racing and comparison."""
    
    ALGORITHM_COLORS = {
        'BFS': {'main': '#3498DB', 'light': '#AED6F1', 'path': '#2E86C1'},
        'DFS': {'main': '#E67E22', 'light': '#FADBD8', 'path': '#CA6F1E'},
        'Dijkstra': {'main': '#9B59B6', 'light': '#D7BDE2', 'path': '#7D3C98'},
        'A*': {'main': '#1ABC9C', 'light': '#A3E4D7', 'path': '#148F77'}
    }
    
    BASE_COLORS = {
        'wall': '#2C3E50',
        'passage': '#FFFFFF',
        'start': '#27AE60',
        'goal': '#E74C3C',
        'winner': '#FFD700'
    }
    
    def __init__(self, rows: int = 21, cols: int = 21, cell_size: int = 20):
        """Initialize GUI."""
        self.cell_rows = rows
        self.cell_cols = cols
        self.cell_size = cell_size
        
        self.grid_rows = 2 * rows + 1
        self.grid_cols = 2 * cols + 1
        self.canvas_width = self.grid_cols * cell_size
        self.canvas_height = self.grid_rows * cell_size
        
        self.maze: Optional[Maze] = None
        self.maze_seed: Optional[int] = None
        
        self.algorithms: Dict[str, any] = {}
        self.algorithm_enabled: Dict[str, bool] = {
            'BFS': True, 'DFS': True, 'Dijkstra': True, 'A*': True
        }
        
        self.is_racing = False
        self.is_paused = False
        self.steps_per_frame = 1
        self.frame_delay = 50
        
        # View toggles - will be initialized after root window is created
        self.show_frontier = None
        self.show_visited = None
        self.show_paths = None
        self.highlight_winners = None
        
        self.metrics_collector = MetricsCollector()
        self.last_frame_time = time.perf_counter()
        self.current_generator = 'prim'
        
        self._setup_ui()
        self.root.after(100, self._generate_maze)
    
    def _setup_ui(self):
        """Create and layout UI components."""
        self.root = tk.Tk()
        self.root.title("Multi-Algorithm Pathfinding Race")
        self.root.configure(bg='#F8F9FA')
        
        # Initialize BooleanVar objects AFTER root window is created
        self.show_frontier = tk.BooleanVar(value=True)
        self.show_visited = tk.BooleanVar(value=True)
        self.show_paths = tk.BooleanVar(value=True)
        self.highlight_winners = tk.BooleanVar(value=False)
        
        self._create_menu_bar()
        self._bind_shortcuts()
        
        window_width = 1400
        window_height = 900
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        if window_height > screen_height - 100:
            window_height = screen_height - 100
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)
        
        main_canvas = tk.Canvas(self.root, bg='#F8F9FA', highlightthickness=0)
        main_scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL, command=main_canvas.yview)
        
        scrollable_main = tk.Frame(main_canvas, bg='#F8F9FA')
        
        scrollable_main.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_main, anchor=tk.NW)
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        main = tk.Frame(scrollable_main, bg='#F8F9FA')
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self._create_controls(main)
        self._create_visualization_area(main)
    
    def _create_menu_bar(self):
        """Create menu bar with all options."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game/Run", menu=game_menu)
        game_menu.add_command(label="New Maze (N)", command=self._new_maze, accelerator="N")
        game_menu.add_command(label="Start Race (R)", command=self._start_race, accelerator="R")
        game_menu.add_command(label="Pause/Resume (P)", command=self._pause_race, accelerator="P")
        game_menu.add_command(label="Step (S)", command=self._step_race, accelerator="S")
        game_menu.add_separator()
        game_menu.add_command(label="Reset Stats", command=self._reset_race)
        game_menu.add_command(label="Export CSV", command=self._export_csv)
        game_menu.add_separator()
        game_menu.add_command(label="Quit (ESC)", command=self.root.quit, accelerator="ESC")
        
        maze_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Maze", menu=maze_menu)
        maze_menu.add_command(label="Prim's Algorithm", command=lambda: self._generate_maze('prim'))
        maze_menu.add_command(label="Kruskal's Algorithm", command=lambda: self._generate_maze('kruskal'))
        maze_menu.add_separator()
        
        size_menu = tk.Menu(maze_menu, tearoff=0)
        maze_menu.add_cascade(label="Grid Size", menu=size_menu)
        for size in [11, 21, 31, 41, 51]:
            size_menu.add_command(
                label=f"{size}×{size}",
                command=lambda s=size: self._change_grid_size(s)
            )
        
        maze_menu.add_separator()
        maze_menu.add_command(label="Set Seed...", command=self._set_seed_dialog)
        maze_menu.add_command(label="Clear Seed", command=self._clear_seed)
        
        pathfinding_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Pathfinding", menu=pathfinding_menu)
        
        self.algo_menu_vars = {}
        for algo in ['BFS', 'DFS', 'Dijkstra', 'A*']:
            var = tk.BooleanVar(value=True)
            self.algo_menu_vars[algo] = var
            pathfinding_menu.add_checkbutton(
                label=algo,
                variable=var,
                command=lambda a=algo: self._toggle_algorithm_menu(a)
            )
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(
            label="Show Frontier",
            variable=self.show_frontier,
            command=self._update_visualization
        )
        view_menu.add_checkbutton(
            label="Show Visited",
            variable=self.show_visited,
            command=self._update_visualization
        )
        view_menu.add_checkbutton(
            label="Show Paths",
            variable=self.show_paths,
            command=self._update_visualization
        )
        view_menu.add_separator()
        view_menu.add_checkbutton(
            label="Highlight Winners",
            variable=self.highlight_winners,
            command=self._update_visualization
        )
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.root.bind('<n>', lambda e: self._new_maze())
        self.root.bind('<N>', lambda e: self._new_maze())
        self.root.bind('<r>', lambda e: self._start_race())
        self.root.bind('<R>', lambda e: self._start_race())
        self.root.bind('<p>', lambda e: self._pause_race())
        self.root.bind('<P>', lambda e: self._pause_race())
        self.root.bind('<s>', lambda e: self._step_race())
        self.root.bind('<S>', lambda e: self._step_race())
        self.root.bind('<Escape>', lambda e: self.root.quit())
    
    def _new_maze(self):
        """Generate new maze with current settings."""
        self._generate_maze(self.current_generator)
    
    def _toggle_algorithm_menu(self, algo_name: str):
        """Toggle algorithm from menu."""
        self.algorithm_enabled[algo_name] = self.algo_menu_vars[algo_name].get()
        if hasattr(self, 'algo_checkboxes') and algo_name in self.algo_checkboxes:
            self.algo_checkboxes[algo_name].set(self.algorithm_enabled[algo_name])
        if not self.is_racing:
            self._update_visualization()
    
    def _set_seed_dialog(self):
        """Show dialog to set seed."""
        seed_str = simpledialog.askstring(
            "Set Seed",
            "Enter seed (integer):",
            initialvalue=str(self.maze_seed) if self.maze_seed else ""
        )
        
        if seed_str:
            try:
                self.maze_seed = int(seed_str)
                self.seed_var.set(str(self.maze_seed))
                messagebox.showinfo("Seed Set", f"Seed set to: {self.maze_seed}\n\nMaze generation will now be deterministic.")
                self._generate_maze(self.current_generator)
            except ValueError:
                messagebox.showerror("Invalid Seed", "Seed must be an integer")
    
    def _clear_seed(self):
        """Clear seed and return to random generation."""
        self.maze_seed = None
        self.seed_var.set("")
        messagebox.showinfo("Seed Cleared", "Seed cleared. Maze generation will now be random.")
        self._generate_maze(self.current_generator)
    
    def _change_grid_size(self, size: int):
        """Change grid size."""
        self.cell_rows = size
        self.cell_cols = size
        self.grid_rows = 2 * size + 1
        self.grid_cols = 2 * size + 1
        self.canvas_width = self.grid_cols * self.cell_size
        self.canvas_height = self.grid_rows * self.cell_size
        
        self.canvas.config(width=self.canvas_width, height=self.canvas_height)
        self._generate_maze(self.current_generator)
    
    def _create_controls(self, parent):
        """Create control panel."""
        top_section = tk.Frame(parent, bg='#F8F9FA')
        top_section.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(
            top_section,
            text="🏁 Multi-Algorithm Pathfinding Race",
            bg='#F8F9FA',
            font=('Arial', 18, 'bold'),
            fg='#2C3E50'
        )
        title.pack(pady=(0, 15))
        
        control_panel = tk.Frame(top_section, bg='#FFFFFF', relief=tk.RAISED, bd=2)
        control_panel.pack(fill=tk.X, pady=(0, 10))
        
        ctrl_inner = tk.Frame(control_panel, bg='#FFFFFF')
        ctrl_inner.pack(fill=tk.X, padx=20, pady=15)
        
        # Row 1: Maze Generation
        row1 = tk.Frame(ctrl_inner, bg='#FFFFFF')
        row1.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(
            row1,
            text="MAZE GENERATION",
            bg='#FFFFFF',
            font=('Arial', 10, 'bold'),
            fg='#7F8C8D'
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Button(
            row1,
            text="Generate: Prim's",
            command=lambda: self._generate_maze('prim'),
            bg='#3498DB',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Button(
            row1,
            text="Generate: Kruskal's",
            command=lambda: self._generate_maze('kruskal'),
            bg='#3498DB',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(row1, text="Seed:", bg='#FFFFFF', font=('Arial', 10)).pack(side=tk.LEFT, padx=(0, 8))
        
        self.seed_var = tk.StringVar(value="")
        seed_entry = tk.Entry(row1, textvariable=self.seed_var, width=12, font=('Arial', 10), bd=2, relief=tk.SOLID)
        seed_entry.pack(side=tk.LEFT)
        seed_entry.bind('<Return>', lambda e: self._apply_seed_from_entry())
        
        # Row 2: Race Controls
        row2 = tk.Frame(ctrl_inner, bg='#FFFFFF')
        row2.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(
            row2,
            text="RACE CONTROLS",
            bg='#FFFFFF',
            font=('Arial', 10, 'bold'),
            fg='#7F8C8D'
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        self.start_button = tk.Button(
            row2,
            text="▶ START RACE",
            command=self._start_race,
            bg='#27AE60',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 8))
        
        self.pause_button = tk.Button(
            row2,
            text="⏸ PAUSE",
            command=self._pause_race,
            bg='#F39C12',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10,
            state=tk.DISABLED,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.pause_button.pack(side=tk.LEFT, padx=(0, 8))
        
        self.step_button = tk.Button(
            row2,
            text="⏭ STEP",
            command=self._step_race,
            bg='#95A5A6',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.step_button.pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Button(
            row2,
            text="🔄 RESET",
            command=self._reset_race,
            bg='#E74C3C',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            row2,
            text="📊 Export CSV",
            command=self._export_csv,
            bg='#16A085',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT)
        
        # Row 3: Speed Controls
        row3 = tk.Frame(ctrl_inner, bg='#FFFFFF')
        row3.pack(fill=tk.X)
        
        tk.Label(
            row3,
            text="SPEED SETTINGS",
            bg='#FFFFFF',
            font=('Arial', 10, 'bold'),
            fg='#7F8C8D'
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(row3, text="Steps/Frame:", bg='#FFFFFF', font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.steps_scale = tk.Scale(
            row3,
            from_=1,
            to=20,
            orient=tk.HORIZONTAL,
            bg='#FFFFFF',
            command=self._update_steps,
            length=150,
            width=15,
            highlightthickness=0
        )
        self.steps_scale.set(1)
        self.steps_scale.pack(side=tk.LEFT, padx=(0, 5))
        
        self.steps_label = tk.Label(row3, text="1", bg='#FFFFFF', font=('Arial', 10, 'bold'), width=3)
        self.steps_label.pack(side=tk.LEFT, padx=(0, 30))
        
        tk.Label(row3, text="Delay (ms):", bg='#FFFFFF', font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.delay_scale = tk.Scale(
            row3,
            from_=1,
            to=200,
            orient=tk.HORIZONTAL,
            bg='#FFFFFF',
            command=self._update_delay,
            length=150,
            width=15,
            highlightthickness=0
        )
        self.delay_scale.set(50)
        self.delay_scale.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delay_label = tk.Label(row3, text="50", bg='#FFFFFF', font=('Arial', 10, 'bold'), width=4)
        self.delay_label.pack(side=tk.LEFT)
    
    def _create_visualization_area(self, parent):
        """Create visualization and metrics area."""
        middle_section = tk.Frame(parent, bg='#F8F9FA')
        middle_section.pack(fill=tk.BOTH, expand=True)
        
        # LEFT: Canvas
        left_frame = tk.Frame(middle_section, bg='#F8F9FA')
        left_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(
            left_frame,
            text="Maze Visualization",
            bg='#F8F9FA',
            font=('Arial', 12, 'bold'),
            fg='#34495E'
        ).pack(anchor=tk.W, pady=(0, 8))
        
        canvas_border = tk.Frame(left_frame, bg='#2C3E50', relief=tk.SOLID, bd=3)
        canvas_border.pack()
        
        self.canvas = tk.Canvas(
            canvas_border,
            width=self.canvas_width,
            height=self.canvas_height,
            bg=self.BASE_COLORS['passage'],
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Status bar
        status_bar = tk.Frame(left_frame, bg='#34495E', relief=tk.FLAT, bd=0)
        status_bar.pack(fill=tk.X, pady=(5, 0))
        
        status_inner = tk.Frame(status_bar, bg='#34495E')
        status_inner.pack(fill=tk.X, padx=10, pady=5)
        
        self.fps_label = tk.Label(
            status_inner,
            text="FPS: 0.0 (avg: 0.0) | Frames: 0",
            bg='#34495E',
            fg='#ECF0F1',
            font=('Courier', 9),
            anchor=tk.W
        )
        self.fps_label.pack(side=tk.LEFT)
        
        # RIGHT: Metrics
        right_frame = tk.Frame(middle_section, bg='#F8F9FA')
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            right_frame,
            text="Algorithm Metrics",
            bg='#F8F9FA',
            font=('Arial', 12, 'bold'),
            fg='#34495E'
        ).pack(anchor=tk.W, pady=(0, 8))
        
        metrics_container = tk.Frame(right_frame, bg='#F8F9FA')
        metrics_container.pack(fill=tk.BOTH, expand=True)
        
        canvas_scroll = tk.Canvas(metrics_container, bg='#F8F9FA', highlightthickness=0)
        scrollbar = tk.Scrollbar(metrics_container, orient=tk.VERTICAL, command=canvas_scroll.yview)
        scrollable_frame = tk.Frame(canvas_scroll, bg='#F8F9FA')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        )
        
        canvas_scroll.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        
        canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.algo_frames = {}
        self.algo_checkboxes = {}
        self.algo_metric_labels = {}
        
        for algo_name in ['BFS', 'DFS', 'Dijkstra', 'A*']:
            self._create_algorithm_panel(scrollable_frame, algo_name)
        
        self._create_legend(scrollable_frame)
    
    def _apply_seed_from_entry(self):
        """Apply seed from entry field."""
        seed_text = self.seed_var.get().strip()
        if seed_text:
            try:
                self.maze_seed = int(seed_text)
                self._generate_maze(self.current_generator)
            except ValueError:
                messagebox.showerror("Invalid Seed", "Seed must be an integer")
        else:
            self.maze_seed = None
            self._generate_maze(self.current_generator)
    
    def _create_algorithm_panel(self, parent, algo_name: str):
        """Create a panel for one algorithm."""
        color = self.ALGORITHM_COLORS[algo_name]['main']
        
        outer = tk.Frame(parent, bg=color, relief=tk.SOLID, bd=0)
        outer.pack(fill=tk.X, pady=(0, 15))
        
        frame = tk.Frame(outer, bg='#FFFFFF')
        frame.pack(fill=tk.BOTH, padx=3, pady=3)
        
        self.algo_frames[algo_name] = frame
        
        header = tk.Frame(frame, bg=color)
        header.pack(fill=tk.X)
        
        header_inner = tk.Frame(header, bg=color)
        header_inner.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(
            header_inner,
            text=algo_name,
            bg=color,
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack(side=tk.LEFT)
        
        checkbox_var = tk.BooleanVar(value=True)
        checkbox = tk.Checkbutton(
            header_inner,
            text="Enabled",
            variable=checkbox_var,
            bg=color,
            fg='white',
            selectcolor=color,
            font=('Arial', 9, 'bold'),
            activebackground=color,
            activeforeground='white',
            command=lambda: self._toggle_algorithm(algo_name, checkbox_var.get())
        )
        checkbox.pack(side=tk.RIGHT)
        self.algo_checkboxes[algo_name] = checkbox_var
        
        metrics_area = tk.Frame(frame, bg='#FFFFFF')
        metrics_area.pack(fill=tk.X, padx=15, pady=12)
        
        metrics = [
            ("Status:", "status", "—"),
            ("Explored:", "explored", "0"),
            ("Runtime:", "runtime", "0.0 ms"),
            ("Steps:", "steps", "0"),
            ("Path Found:", "path_found", "—"),
            ("Path Length:", "path_len", "—"),
            ("Path Valid:", "path_valid", "—"),
            ("Optimal:", "optimal", "—")
        ]
        
        self.algo_metric_labels[algo_name] = {}
        
        for label_text, key, default in metrics:
            row = tk.Frame(metrics_area, bg='#FFFFFF')
            row.pack(fill=tk.X, pady=3)
            
            tk.Label(
                row,
                text=label_text,
                bg='#FFFFFF',
                font=('Arial', 10),
                width=12,
                anchor=tk.W,
                fg='#7F8C8D'
            ).pack(side=tk.LEFT)
            
            value_label = tk.Label(
                row,
                text=default,
                bg='#FFFFFF',
                font=('Arial', 10, 'bold'),
                fg='#2C3E50',
                anchor=tk.W
            )
            value_label.pack(side=tk.LEFT, padx=(10, 0))
            
            self.algo_metric_labels[algo_name][key] = value_label
    
    def _create_legend(self, parent):
        """Create color legend."""
        legend_frame = tk.Frame(parent, bg='#FFFFFF', relief=tk.SOLID, bd=2)
        legend_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(
            legend_frame,
            text="Color Legend",
            bg='#FFFFFF',
            font=('Arial', 11, 'bold'),
            fg='#34495E'
        ).pack(pady=(10, 5))
        
        legend_inner = tk.Frame(legend_frame, bg='#FFFFFF')
        legend_inner.pack(pady=(5, 15), padx=15)
        
        for text, color in [("Start", self.BASE_COLORS['start']), ("Goal", self.BASE_COLORS['goal']), ("Winner", self.BASE_COLORS['winner'])]:
            row = tk.Frame(legend_inner, bg='#FFFFFF')
            row.pack(fill=tk.X, pady=3)
            
            box = tk.Canvas(row, width=24, height=24, bg=color, highlightthickness=2, highlightbackground='#2C3E50')
            box.pack(side=tk.LEFT, padx=(0, 10))
            
            tk.Label(row, text=text, bg='#FFFFFF', font=('Arial', 9), fg='#2C3E50').pack(side=tk.LEFT)
        
        for algo_name in ['BFS', 'DFS', 'Dijkstra', 'A*']:
            row = tk.Frame(legend_inner, bg='#FFFFFF')
            row.pack(fill=tk.X, pady=3)
            
            box = tk.Canvas(
                row,
                width=24,
                height=24,
                bg=self.ALGORITHM_COLORS[algo_name]['light'],
                highlightthickness=2,
                highlightbackground=self.ALGORITHM_COLORS[algo_name]['main']
            )
            box.pack(side=tk.LEFT, padx=(0, 10))
            
            tk.Label(row, text=f"{algo_name} Explored", bg='#FFFFFF', font=('Arial', 9), fg='#2C3E50').pack(side=tk.LEFT)
    
    def _toggle_algorithm(self, algo_name: str, enabled: bool):
        """Toggle algorithm on/off."""
        self.algorithm_enabled[algo_name] = enabled
        self.algo_menu_vars[algo_name].set(enabled)
        if not self.is_racing:
            self._update_visualization()
    
    def _cell_to_grid(self, cell_r: int, cell_c: int) -> Tuple[int, int]:
        """Convert cell coordinates to grid coordinates."""
        return (2 * cell_r + 1, 2 * cell_c + 1)
    
    def _draw_cell_base(self, r: int, c: int, color: str):
        """Draw base cell (maze structure)."""
        x1 = c * self.cell_size
        y1 = r * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color, tags='base')
    
    def _draw_cell_overlay(self, r: int, c: int, algo_name: str, layer: str, is_winner: bool = False):
        """Draw algorithm overlay on a cell."""
        x1 = c * self.cell_size
        y1 = r * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        
        colors = self.ALGORITHM_COLORS[algo_name]
        
        if is_winner and self.highlight_winners.get():
            fill_color = self.BASE_COLORS['winner']
        else:
            fill_color = colors['light'] if layer != 'path' else colors['path']
        
        if layer == 'visited':
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=fill_color,
                outline=colors['main'],
                width=1,
                tags=('overlay', f'algo_{algo_name}', f'layer_{layer}')
            )
        elif layer == 'frontier':
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=fill_color,
                outline=colors['main'],
                width=2,
                tags=('overlay', f'algo_{algo_name}', f'layer_{layer}')
            )
        elif layer == 'path':
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=fill_color,
                outline=colors['main'] if not is_winner else '#DAA520',
                width=3 if is_winner else 2,
                tags=('overlay', f'algo_{algo_name}', f'layer_{layer}')
            )
    
    def _draw_maze_base(self):
        """Draw the base maze structure."""
        if not self.maze:
            return
        
        self.canvas.delete('all')
        display_grid = self.maze.to_display_grid()
        
        for r in range(len(display_grid)):
            for c in range(len(display_grid[0])):
                cell_type = display_grid[r][c]
                
                if cell_type == CellType.WALL:
                    color = self.BASE_COLORS['wall']
                elif cell_type == CellType.START:
                    color = self.BASE_COLORS['start']
                elif cell_type == CellType.GOAL:
                    color = self.BASE_COLORS['goal']
                else:
                    color = self.BASE_COLORS['passage']
                
                self._draw_cell_base(r, c, color)
    
    def _update_visualization(self):
        """Update visualization for all algorithms."""
        self.canvas.delete('overlay')
        
        winners = set()
        if self.metrics_collector.optimal_path_length:
            for algo_name, metrics in self.metrics_collector.algorithm_metrics.items():
                if metrics.path_found and metrics.path_optimal:
                    winners.add(algo_name)
        
        for algo_name, search in self.algorithms.items():
            if not self.algorithm_enabled[algo_name] or not search:
                continue
            
            is_winner = algo_name in winners
            
            if self.show_visited.get():
                for cell in search.visited:
                    gr, gc = self._cell_to_grid(*cell)
                    if cell != self.maze.start and cell != self.maze.goal:
                        self._draw_cell_overlay(gr, gc, algo_name, 'visited', is_winner)
            
            if self.show_frontier.get():
                for cell in search.frontier:
                    if cell not in search.visited:
                        gr, gc = self._cell_to_grid(*cell)
                        if cell != self.maze.start and cell != self.maze.goal:
                            self._draw_cell_overlay(gr, gc, algo_name, 'frontier', is_winner)
            
            if self.show_paths.get() and search.status == SearchStatus.FOUND:
                path = search.get_path()
                for cell in path:
                    if cell != self.maze.start and cell != self.maze.goal:
                        gr, gc = self._cell_to_grid(*cell)
                        self._draw_cell_overlay(gr, gc, algo_name, 'path', is_winner)
        
        if self.maze:
            sr, sc = self._cell_to_grid(*self.maze.start)
            self._draw_cell_base(sr, sc, self.BASE_COLORS['start'])
            
            gr, gc = self._cell_to_grid(*self.maze.goal)
            self._draw_cell_base(gr, gc, self.BASE_COLORS['goal'])
    
    def _update_metrics(self):
        """Update metrics display for all algorithms."""
        for algo_name, search in self.algorithms.items():
            if not search:
                continue
            
            self.metrics_collector.update_algorithm(algo_name, search, self.maze)
            
            labels = self.algo_metric_labels[algo_name]
            algo_metrics = self.metrics_collector.algorithm_metrics.get(algo_name)
            
            if algo_metrics:
                labels['status'].config(text=search.status.value.title())
                labels['explored'].config(text=str(algo_metrics.nodes_explored))
                labels['runtime'].config(text=f"{algo_metrics.runtime_ms:.1f} ms")
                labels['steps'].config(text=str(algo_metrics.steps_executed))
                
                if search.status == SearchStatus.FOUND:
                    labels['path_found'].config(text="Yes", fg='#27AE60')
                elif search.status == SearchStatus.NO_PATH:
                    labels['path_found'].config(text="No", fg='#E74C3C')
                else:
                    labels['path_found'].config(text="—", fg='#2C3E50')
                
                if algo_metrics.path_len > 0:
                    labels['path_len'].config(text=str(algo_metrics.path_len))
                else:
                    labels['path_len'].config(text="—")
                
                if algo_metrics.path_found:
                    if algo_metrics.path_valid:
                        labels['path_valid'].config(text="Yes", fg='#27AE60')
                    else:
                        labels['path_valid'].config(text="No", fg='#E74C3C')
                else:
                    labels['path_valid'].config(text="—", fg='#2C3E50')
                
                if algo_metrics.path_found and algo_metrics.optimal_path_len:
                    if algo_metrics.path_optimal:
                        labels['optimal'].config(text="Yes", fg='#27AE60')
                    else:
                        opt_len = algo_metrics.optimal_path_len
                        labels['optimal'].config(text=f"No ({opt_len})", fg='#E67E22')
                else:
                    labels['optimal'].config(text="—", fg='#2C3E50')
        
        instant_fps, avg_fps = self.metrics_collector.get_fps_stats()
        self.fps_label.config(
            text=f"FPS: {instant_fps:.1f} (avg: {avg_fps:.1f}) | Frames: {self.metrics_collector.frames_drawn}"
        )
    
    def _generate_maze(self, algorithm: str = 'prim'):
        """Generate a new maze."""
        self._reset_race()
        
        self.current_generator = algorithm
        
        seed_text = self.seed_var.get().strip()
        if seed_text:
            try:
                self.maze_seed = int(seed_text)
            except ValueError:
                self.maze_seed = None
        else:
            self.maze_seed = None
        
        self.maze = Maze(self.cell_rows, self.cell_cols, seed=self.maze_seed)
        
        if algorithm == 'prim':
            self.maze.generate_prim()
        else:
            self.maze.generate_kruskal()
        
        self._draw_maze_base()
        self._reset_metrics()
    
    def _reset_metrics(self):
        """Reset all metric displays."""
        for algo_name in self.algo_metric_labels:
            labels = self.algo_metric_labels[algo_name]
            labels['status'].config(text="—")
            labels['explored'].config(text="0")
            labels['runtime'].config(text="0.0 ms")
            labels['steps'].config(text="0")
            labels['path_found'].config(text="—", fg='#2C3E50')
            labels['path_len'].config(text="—")
            labels['path_valid'].config(text="—", fg='#2C3E50')
            labels['optimal'].config(text="—", fg='#2C3E50')
        
        self.fps_label.config(text="FPS: 0.0 (avg: 0.0) | Frames: 0")
    
    def _initialize_algorithms(self):
        """Initialize search instances for all enabled algorithms."""
        self.algorithms = {}
        
        if not self.maze:
            return
        
        start = self.maze.start
        goal = self.maze.goal
        
        algo_classes = {
            'BFS': BFS,
            'DFS': DFS,
            'Dijkstra': Dijkstra,
            'A*': AStar
        }
        
        for algo_name, algo_class in algo_classes.items():
            if self.algorithm_enabled[algo_name]:
                self.algorithms[algo_name] = algo_class(self.maze, start, goal)
    
    def _start_race(self):
        """Start the algorithm race."""
        if self.is_racing and not self.is_paused:
            return
        
        if not self.algorithms or all(algo.is_done() for algo in self.algorithms.values()):
            self._draw_maze_base()
            self._initialize_algorithms()
            
            enabled_algos = [name for name, enabled in self.algorithm_enabled.items() if enabled]
            self.metrics_collector.start_race(
                enabled_algos,
                self.maze,
                self.current_generator,
                self.maze_seed
            )
            self.last_frame_time = time.perf_counter()
        
        self.is_racing = True
        self.is_paused = False
        
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL, text="⏸ PAUSE")
        self.step_button.config(state=tk.DISABLED)
        
        self._race_loop()
    
    def _pause_race(self):
        """Pause/resume the race."""
        if not self.is_racing:
            return
        
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_button.config(text="▶ RESUME")
            self.step_button.config(state=tk.NORMAL)
        else:
            self.pause_button.config(text="⏸ PAUSE")
            self.step_button.config(state=tk.DISABLED)
            self._race_loop()
    
    def _step_race(self):
        """Execute one step for all algorithms."""
        if not self.maze:
            return
        
        if not self.algorithms:
            self._draw_maze_base()
            self._initialize_algorithms()
        
        for algo_name, search in self.algorithms.items():
            if not search.is_done():
                search.step()
        
        self._update_visualization()
        self._update_metrics()
        
        if all(algo.is_done() for algo in self.algorithms.values()):
            self._on_race_complete()
    
    def _reset_race(self):
        """Reset the race."""
        self.is_racing = False
        self.is_paused = False
        self.algorithms = {}
        
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="⏸ PAUSE")
        self.step_button.config(state=tk.NORMAL)
        
        if self.maze:
            self._draw_maze_base()
        
        self._reset_metrics()
    
    def _race_loop(self):
        """Main race loop - step all algorithms."""
        if not self.is_racing or self.is_paused:
            return
        
        any_running = any(not algo.is_done() for algo in self.algorithms.values())
        
        if any_running:
            for _ in range(self.steps_per_frame):
                for algo_name, search in self.algorithms.items():
                    if not search.is_done():
                        search.step()
            
            self._update_visualization()
            self._update_metrics()
            
            current_time = time.perf_counter()
            frame_time = current_time - self.last_frame_time
            self.metrics_collector.record_frame(frame_time)
            self.last_frame_time = current_time
            
            if all(algo.is_done() for algo in self.algorithms.values()):
                self._on_race_complete()
            else:
                self.root.after(self.frame_delay, self._race_loop)
        else:
            self._on_race_complete()
    
    def _on_race_complete(self):
        """Handle race completion."""
        self.is_racing = False
        self.is_paused = False
        
        self.metrics_collector.check_all_optimality()
        self._update_visualization()
        self._update_metrics()
        
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="⏸ PAUSE")
        self.step_button.config(state=tk.NORMAL)
    
    def _export_csv(self):
        """Export metrics to CSV file."""
        if not self.metrics_collector.algorithm_metrics:
            messagebox.showwarning("No Data", "No metrics to export. Run a race first.")
            return
        
        success, result = self.metrics_collector.export_to_csv()
        
        if success:
            messagebox.showinfo("Export Successful", f"Metrics exported to:\n{result}")
        else:
            messagebox.showerror("Export Failed", f"Error: {result}")
    
    def _update_steps(self, value):
        """Update steps per frame."""
        self.steps_per_frame = int(float(value))
        self.steps_label.config(text=str(self.steps_per_frame))
    
    def _update_delay(self, value):
        """Update frame delay."""
        self.frame_delay = int(float(value))
        self.delay_label.config(text=str(int(float(value))))
    
    def run(self):
        """Start the GUI event loop."""
        self.root.mainloop()


def demo_race_mode():
    """Demonstrate multi-algorithm race mode."""
    print("="*60)
    print("MULTI-ALGORITHM RACE MODE")
    print("="*60)
    print("\nAlgorithms: BFS, DFS, Dijkstra, A*")
    print("Keyboard Shortcuts: N, R, P, S, ESC")
    print("Starting GUI...")
    print("="*60)
    
    gui = MultiAlgorithmGUI(rows=21, cols=21, cell_size=20)
    gui.run()


def run_headless_test(rows: int = 10, cols: int = 10, seed: int = 42):
    """Run a headless race (no GUI) for testing metrics and correctness."""
    print("="*60)
    print("HEADLESS TEST MODE")
    print("="*60)
    print(f"Maze: {rows}×{cols}, Seed: {seed}")
    print()
    
    maze = Maze(rows, cols, seed=seed)
    maze.generate_prim()
    print("✓ Maze generated")
    
    algorithms = {
        'BFS': BFS(maze, maze.start, maze.goal),
        'DFS': DFS(maze, maze.start, maze.goal),
        'Dijkstra': Dijkstra(maze, maze.start, maze.goal),
        'A*': AStar(maze, maze.start, maze.goal)
    }
    print("✓ Algorithms initialized")
    
    metrics = MetricsCollector()
    metrics.start_race(['BFS', 'DFS', 'Dijkstra', 'A*'], maze, 'prim', seed)
    print("✓ Metrics collection started")
    print()
    
    step_count = 0
    while any(not algo.is_done() for algo in algorithms.values()):
        for algo_name, algo in algorithms.items():
            if not algo.is_done():
                algo.step()
        step_count += 1
        
        for algo_name, algo in algorithms.items():
            metrics.update_algorithm(algo_name, algo, maze)
        
        metrics.record_frame(0.016)
    
    print(f"✓ Race completed in {step_count} steps")
    print()
    
    metrics.check_all_optimality()
    
    print("RESULTS:")
    print("-" * 60)
    print(f"{'Algorithm':<12} {'Explored':<10} {'Path Len':<10} {'Valid':<8} {'Optimal':<8}")
    print("-" * 60)
    
    for algo_name in ['BFS', 'DFS', 'Dijkstra', 'A*']:
        m = metrics.algorithm_metrics[algo_name]
        valid_str = "Yes" if m.path_valid else "No" if m.path_found else "—"
        optimal_str = "Yes" if m.path_optimal else "No" if m.path_found else "—"
        
        print(f"{algo_name:<12} {m.nodes_explored:<10} {m.path_len:<10} {valid_str:<8} {optimal_str:<8}")
    
    print("-" * 60)
    print()
    
    all_valid = True
    all_optimal_correct = True
    
    for algo_name, m in metrics.algorithm_metrics.items():
        if m.path_found:
            if not m.path_valid:
                print(f"✗ FAIL: {algo_name} path is invalid!")
                all_valid = False
            
            if algo_name in ['BFS', 'Dijkstra', 'A*']:
                if not m.path_optimal:
                    print(f"✗ FAIL: {algo_name} should find optimal path!")
                    all_optimal_correct = False
    
    if all_valid:
        print("✓ PASS: All paths are valid")
    
    if all_optimal_correct:
        print("✓ PASS: All optimal algorithms found optimal paths")
    
    print()
    
    success, filename = metrics.export_to_csv("test_metrics.csv")
    if success:
        print(f"✓ Metrics exported to {filename}")
    
    print("="*60)
    
    return metrics


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_headless_test()
    else:
        demo_race_mode()