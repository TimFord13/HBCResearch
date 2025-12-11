"""Tkinter-based GUI for maze visualization and control."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
from datetime import datetime
from typing import List, Dict, Optional
from maze_module import Maze, CellType
from search_module import BFS, DFS, Dijkstra, AStar, verify_optimality


class MazeApp:
    """Main application window with canvas and controls."""
    
    # Color scheme
    COLORS = {
        'wall': '#2c3e50',
        'passage': '#ecf0f1',
        'start': '#27ae60',
        'goal': '#e74c3c',
        'bfs_visited': '#3498db',
        'dfs_visited': '#9b59b6',
        'dijkstra_visited': '#f39c12',
        'astar_visited': '#1abc9c',
        'path': '#e67e22'
    }
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Maze Generation & Pathfinding Race")
        self.root.geometry("1400x900")
        
        # State
        self.maze: Optional[Maze] = None
        self.maze_algorithm = "Prim's"
        self.grid_size = 41
        self.seed: Optional[int] = None
        self.algorithms: List = []
        self.enabled_algos = {'BFS': True, 'DFS': True, 'Dijkstra': True, 'A*': True}
        self.running = False
        self.paused = False
        self.generation_steps = []
        self.generation_index = 0
        self.steps_per_frame = 10
        self.frame_delay = 16  # ~60 FPS
        self.cell_size = 10
        
        # FPS tracking
        self.frame_times = []
        self.last_frame_time = time.time()
        
        # Metrics
        self.metrics_data = []
        
        # Setup UI
        self._create_menu()
        self._create_main_layout()
        self._bind_keys()
        
        # Initialize with default maze
        self.new_maze()
    
    def _create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Game/Run menu
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game/Run", menu=game_menu)
        game_menu.add_command(label="New Maze (N)", command=self.new_maze)
        game_menu.add_command(label="Start Race (R)", command=self.start_race)
        game_menu.add_command(label="Pause/Resume (P)", command=self.toggle_pause)
        game_menu.add_command(label="Step (S)", command=self.step_once)
        game_menu.add_separator()
        game_menu.add_command(label="Reset Stats", command=self.reset_stats)
        game_menu.add_command(label="Quit (ESC)", command=self.root.quit)
        
        # Maze menu
        maze_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Maze", menu=maze_menu)
        
        algo_menu = tk.Menu(maze_menu, tearoff=0)
        maze_menu.add_cascade(label="Algorithm", menu=algo_menu)
        self.maze_algo_var = tk.StringVar(value="Prim's")
        algo_menu.add_radiobutton(label="Prim's", variable=self.maze_algo_var, 
                                   value="Prim's", command=self._update_maze_algo)
        algo_menu.add_radiobutton(label="Kruskal's", variable=self.maze_algo_var,
                                   value="Kruskal's", command=self._update_maze_algo)
        
        size_menu = tk.Menu(maze_menu, tearoff=0)
        maze_menu.add_cascade(label="Grid Size", menu=size_menu)
        self.grid_size_var = tk.IntVar(value=41)
        for size in [21, 31, 41, 61]:
            size_menu.add_radiobutton(label=f"{size}x{size}", variable=self.grid_size_var,
                                      value=size, command=self._update_grid_size)
        
        maze_menu.add_separator()
        maze_menu.add_command(label="Set Seed...", command=self.set_seed)
        maze_menu.add_command(label="Clear Seed", command=self.clear_seed)
        
        # Pathfinding menu
        path_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Pathfinding", menu=path_menu)
        
        self.algo_vars = {}
        for algo in ['BFS', 'DFS', 'Dijkstra', 'A*']:
            var = tk.BooleanVar(value=True)
            self.algo_vars[algo] = var
            path_menu.add_checkbutton(label=f"Enable {algo}", variable=var,
                                      command=lambda a=algo: self._toggle_algo(a))
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Export CSV", command=self.export_csv)
    
    def _create_main_layout(self):
        """Create main application layout."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Canvas
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='white', width=800, height=800)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Right: Control panel
        control_frame = ttk.Frame(main_frame, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        control_frame.pack_propagate(False)
        
        # Speed controls
        speed_frame = ttk.LabelFrame(control_frame, text="Speed Control", padding=10)
        speed_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(speed_frame, text="Steps per Frame:").pack()
        self.steps_scale = ttk.Scale(speed_frame, from_=1, to=100, orient=tk.HORIZONTAL,
                                     command=self._update_steps)
        self.steps_scale.set(10)
        self.steps_scale.pack(fill=tk.X)
        self.steps_label = ttk.Label(speed_frame, text="10")
        self.steps_label.pack()
        
        ttk.Label(speed_frame, text="Frame Delay (ms):").pack(pady=(10, 0))
        self.delay_scale = ttk.Scale(speed_frame, from_=1, to=100, orient=tk.HORIZONTAL,
                                     command=self._update_delay)
        self.delay_scale.set(16)
        self.delay_scale.pack(fill=tk.X)
        self.delay_label = ttk.Label(speed_frame, text="16 ms")
        self.delay_label.pack()
        
        # Metrics display
        metrics_frame = ttk.LabelFrame(control_frame, text="Algorithm Metrics", padding=10)
        metrics_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create text widget for metrics
        self.metrics_text = tk.Text(metrics_frame, height=20, width=35, font=('Courier', 9))
        self.metrics_text.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(metrics_frame, command=self.metrics_text.yview)
        self.metrics_text.config(yscrollcommand=scrollbar.set)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _bind_keys(self):
        """Bind keyboard shortcuts."""
        self.root.bind('<n>', lambda e: self.new_maze())
        self.root.bind('<N>', lambda e: self.new_maze())
        self.root.bind('<r>', lambda e: self.start_race())
        self.root.bind('<R>', lambda e: self.start_race())
        self.root.bind('<p>', lambda e: self.toggle_pause())
        self.root.bind('<P>', lambda e: self.toggle_pause())
        self.root.bind('<s>', lambda e: self.step_once())
        self.root.bind('<S>', lambda e: self.step_once())
        self.root.bind('<Escape>', lambda e: self.root.quit())
    
    def _update_maze_algo(self):
        """Update selected maze algorithm."""
        self.maze_algorithm = self.maze_algo_var.get()
    
    def _update_grid_size(self):
        """Update grid size."""
        self.grid_size = self.grid_size_var.get()
    
    def _toggle_algo(self, algo: str):
        """Toggle algorithm enable state."""
        self.enabled_algos[algo] = self.algo_vars[algo].get()
    
    def _update_steps(self, value):
        """Update steps per frame."""
        self.steps_per_frame = int(float(value))
        self.steps_label.config(text=str(self.steps_per_frame))
    
    def _update_delay(self, value):
        """Update frame delay."""
        self.frame_delay = int(float(value))
        self.delay_label.config(text=f"{self.frame_delay} ms")
    
    def set_seed(self):
        """Prompt user for seed."""
        seed_str = simpledialog.askstring("Set Seed", "Enter numeric seed:")
        if seed_str:
            try:
                self.seed = int(seed_str)
                self.update_status(f"Seed set to {self.seed}")
            except ValueError:
                messagebox.showerror("Error", "Seed must be an integer")
    
    def clear_seed(self):
        """Clear seed for random generation."""
        self.seed = None
        self.update_status("Seed cleared - using random generation")
    
    def new_maze(self):
        """Generate new maze."""
        self.running = False
        self.paused = False
        self.algorithms = []
        self.generation_index = 0
        
        # Create maze
        self.maze = Maze(self.grid_size, self.grid_size, self.seed)
        
        # Calculate cell size to fit canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 100:  # Initial layout
            canvas_width = 800
            canvas_height = 800
        
        self.cell_size = min(canvas_width // self.maze.cols, canvas_height // self.maze.rows)
        
        # Generate maze
        if self.maze_algorithm == "Prim's":
            self.generation_steps = self.maze.generate_prims()
        else:
            self.generation_steps = self.maze.generate_kruskals()
        
        self.update_status(f"Generating maze with {self.maze_algorithm}...")
        self._animate_generation()
    
    def _animate_generation(self):
        """Animate maze generation."""
        if self.generation_index < len(self.generation_steps):
            # Process multiple steps per frame
            for _ in range(self.steps_per_frame):
                if self.generation_index >= len(self.generation_steps):
                    break
                self.generation_index += 1
            
            self.draw_maze()
            self._update_fps()
            self.root.after(self.frame_delay, self._animate_generation)
        else:
            self.draw_maze()
            self.update_status("Maze generated. Ready to start race.")
    
    def start_race(self):
        """Start pathfinding race."""
        if not self.maze or not self.maze.start:
            messagebox.showwarning("Warning", "Generate a maze first")
            return
        
        if self.running:
            self.update_status("Race already running")
            return
        
        # Create enabled algorithms
        self.algorithms = []
        if self.enabled_algos['BFS']:
            self.algorithms.append(BFS(self.maze))
        if self.enabled_algos['DFS']:
            self.algorithms.append(DFS(self.maze))
        if self.enabled_algos['Dijkstra']:
            self.algorithms.append(Dijkstra(self.maze))
        if self.enabled_algos['A*']:
            self.algorithms.append(AStar(self.maze))
        
        if not self.algorithms:
            messagebox.showwarning("Warning", "Enable at least one algorithm")
            return
        
        # Start all algorithms
        for algo in self.algorithms:
            algo.start()
        
        self.running = True
        self.paused = False
        self.update_status("Race started!")
        self._run_race()
    
    def _run_race(self):
        """Run race step-by-step."""
        if not self.running or self.paused:
            return
        
        # Execute steps for all algorithms
        all_done = True
        for _ in range(self.steps_per_frame):
            any_stepped = False
            for algo in self.algorithms:
                if not algo.is_done():
                    algo.step()
                    any_stepped = True
                    all_done = False
            
            if not any_stepped:
                break
        
        # Update display
        self.draw_maze()
        self._update_metrics()
        self._update_fps()
        
        if all_done:
            self.running = False
            self._finish_race()
        else:
            self.root.after(self.frame_delay, self._run_race)
    
    def _finish_race(self):
        """Handle race completion."""
        # Verify paths and optimality
        optimality = verify_optimality(self.algorithms)
        
        # Store metrics
        for algo in self.algorithms:
            metrics = algo.get_metrics()
            metrics['optimal'] = optimality.get(algo.name, False)
            metrics['seed'] = self.seed
            metrics['grid_size'] = self.grid_size
            metrics['generator'] = self.maze_algorithm
            metrics['timestamp'] = datetime.now().isoformat()
            self.metrics_data.append(metrics)
        
        self._update_metrics()
        self.update_status("Race complete!")
        self.draw_maze()
    
    def toggle_pause(self):
        """Toggle pause state."""
        if not self.running:
            return
        self.paused = not self.paused
        self.update_status("Paused" if self.paused else "Running")
        if not self.paused:
            self._run_race()
    
    def step_once(self):
        """Execute one step when paused."""
        if not self.running or not self.paused:
            return
        
        for algo in self.algorithms:
            if not algo.is_done():
                algo.step()
        
        self.draw_maze()
        self._update_metrics()
    
    def reset_stats(self):
        """Reset statistics."""
        self.metrics_data = []
        self._update_metrics()
        self.update_status("Statistics reset")
    
    def draw_maze(self):
        """Draw maze and algorithm states."""
        self.canvas.delete('all')
        
        if not self.maze:
            return
        
        # Draw grid
        for r in range(self.maze.rows):
            for c in range(self.maze.cols):
                x1 = c * self.cell_size
                y1 = r * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                cell_type = self.maze.grid[r][c]
                
                # Base color
                if cell_type == CellType.WALL:
                    color = self.COLORS['wall']
                elif cell_type == CellType.START:
                    color = self.COLORS['start']
                elif cell_type == CellType.GOAL:
                    color = self.COLORS['goal']
                else:
                    color = self.COLORS['passage']
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='gray', width=1)
        
        # Draw algorithm visualizations
        if self.algorithms:
            for algo in self.algorithms:
                self._draw_algorithm_state(algo)
    
    def _draw_algorithm_state(self, algo):
        """Draw algorithm's visited cells and path."""
        # Color mapping
        color_map = {
            'BFS': self.COLORS['bfs_visited'],
            'DFS': self.COLORS['dfs_visited'],
            'Dijkstra': self.COLORS['dijkstra_visited'],
            'A*': self.COLORS['astar_visited']
        }
        
        color = color_map.get(algo.name, 'gray')
        
        # Draw visited cells with semi-transparent overlay
        if hasattr(algo, 'visited'):
            for r, c in algo.visited:
                if (r, c) != self.maze.start and (r, c) != self.maze.goal:
                    x1 = c * self.cell_size + 2
                    y1 = r * self.cell_size + 2
                    x2 = x1 + self.cell_size - 4
                    y2 = y1 + self.cell_size - 4
                    self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline='')
        
        # Draw current cell
        if algo.current and not algo.is_done():
            r, c = algo.current
            x1 = c * self.cell_size
            y1 = r * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3)
        
        # Draw path if found
        if algo.path:
            for i in range(len(algo.path) - 1):
                r1, c1 = algo.path[i]
                r2, c2 = algo.path[i + 1]
                x1 = c1 * self.cell_size + self.cell_size // 2
                y1 = r1 * self.cell_size + self.cell_size // 2
                x2 = c2 * self.cell_size + self.cell_size // 2
                y2 = r2 * self.cell_size + self.cell_size // 2
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
    
    def _update_metrics(self):
        """Update metrics display."""
        self.metrics_text.delete('1.0', tk.END)
        
        if not self.algorithms:
            self.metrics_text.insert('1.0', "No race running")
            return
        
        lines = []
        for algo in self.algorithms:
            metrics = algo.get_metrics()
            status = "DONE" if algo.is_done() else "RUNNING"
            lines.append(f"\n{algo.name} [{status}]")
            lines.append(f"  Explored: {metrics['explored']}")
            lines.append(f"  Time: {metrics['runtime_ms']:.2f} ms")
            lines.append(f"  Path: {metrics['path_length']}")
            if algo.is_done() and metrics['found']:
                lines.append(f"  Found: Yes")
            lines.append("")
        
        self.metrics_text.insert('1.0', '\n'.join(lines))
    
    def _update_fps(self):
        """Update FPS calculation."""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        self.frame_times.append(frame_time)
        if len(self.frame_times) > 30:
            self.frame_times.pop(0)
        
        if self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
            self.update_status(f"FPS: {fps:.1f}")
    
    def update_status(self, message: str):
        """Update status bar."""
        seed_info = f"Seed: {self.seed}" if self.seed else "Random"
        enabled = ', '.join([a for a, v in self.enabled_algos.items() if v])
        status = f"{message} | {seed_info} | Grid: {self.grid_size}x{self.grid_size} | Algos: {enabled}"
        self.status_bar.config(text=status)
    
    def export_csv(self):
        """Export metrics to CSV file."""
        if not self.metrics_data:
            messagebox.showinfo("Info", "No metrics to export")
            return
        
        filename = f"maze_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w') as f:
                # Header
                f.write("timestamp,seed,grid_rows,grid_cols,generator,algo,explored,")
                f.write("runtime_ms,path_len,optimal\n")
                
                # Data
                for m in self.metrics_data:
                    f.write(f"{m['timestamp']},{m['seed']},{m['grid_size']},{m['grid_size']},")
                    f.write(f"{m['generator']},{m['name']},{m['explored']},")
                    f.write(f"{m['runtime_ms']},{m['path_length']},{m['optimal']}\n")
            
            messagebox.showinfo("Success", f"Metrics exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
