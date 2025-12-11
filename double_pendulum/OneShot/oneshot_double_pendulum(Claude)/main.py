import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
import time
from physics import DoublePendulum

class DoublePendulumSimulation:
    def __init__(self):
        # Physical parameters
        self.pendulum = DoublePendulum(m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81, damping=0.0)
        
        # Initial state: [theta1, omega1, theta2, omega2]
        self.initial_state = np.array([np.pi/2, 0.0, np.pi/2, 0.0])
        self.state = self.initial_state.copy()
        
        # Simulation parameters
        self.dt = 0.01
        self.time = 0.0
        
        # Energy tracking
        self.initial_energy = self.pendulum.total_energy(self.state)
        self.energy_history = []
        self.time_history = []
        
        # Control flags
        self.paused = False
        self.dragging = False
        self.drag_start = None
        
        # Performance tracking
        self.fps_history = []
        self.last_time = time.time()
        
        # Setup plot
        self.setup_plot()
        
    def setup_plot(self):
        """Initialize the matplotlib figure and axes."""
        self.fig = plt.figure(figsize=(12, 6))
        
        # Pendulum visualization
        self.ax_pend = plt.subplot(1, 2, 1)
        self.ax_pend.set_xlim(-2.5, 2.5)
        self.ax_pend.set_ylim(-2.5, 2.5)
        self.ax_pend.set_aspect('equal')
        self.ax_pend.grid(True, alpha=0.3)
        self.ax_pend.set_title('Double Pendulum')
        
        # Draw pendulum elements
        self.line1, = self.ax_pend.plot([], [], 'o-', lw=2, color='blue', markersize=8)
        self.line2, = self.ax_pend.plot([], [], 'o-', lw=2, color='red', markersize=8)
        
        # Trace for second bob
        self.trace, = self.ax_pend.plot([], [], '-', lw=0.5, color='red', alpha=0.3)
        self.trace_x = []
        self.trace_y = []
        self.max_trace = 500
        
        # Status text
        self.status_text = self.ax_pend.text(0.02, 0.98, '', transform=self.ax_pend.transAxes,
                                             verticalalignment='top', fontfamily='monospace',
                                             fontsize=8, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Energy plot
        self.ax_energy = plt.subplot(1, 2, 2)
        self.ax_energy.set_xlabel('Time (s)')
        self.ax_energy.set_ylabel('Total Energy (J)')
        self.ax_energy.set_title('Energy Conservation')
        self.ax_energy.grid(True, alpha=0.3)
        
        self.energy_line, = self.ax_energy.plot([], [], 'b-', lw=1)
        self.energy_ref, = self.ax_energy.plot([], [], 'r--', lw=1, label='Initial Energy')
        self.ax_energy.legend()
        
        plt.tight_layout()
        
        # Connect event handlers
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        
    def on_click(self, event):
        """Handle mouse click."""
        if event.inaxes != self.ax_pend:
            return
        
        # Check if click is near second bob
        (x1, y1), (x2, y2) = self.pendulum.cartesian_positions(self.state)
        
        dist = np.sqrt((event.xdata - x2)**2 + (event.ydata - y2)**2)
        if dist < 0.3:  # Click threshold
            self.dragging = True
            self.paused = True
            self.drag_start = (event.xdata, event.ydata)
    
    def on_release(self, event):
        """Handle mouse release."""
        if self.dragging:
            self.dragging = False
            # Don't unpause automatically
    
    def on_motion(self, event):
        """Handle mouse motion (dragging)."""
        if self.dragging and event.inaxes == self.ax_pend:
            # Update pendulum position to follow mouse
            self.state = self.pendulum.set_position_from_cartesian(
                event.xdata, event.ydata, self.state
            )
    
    def on_key(self, event):
        """Handle keyboard input."""
        if event.key == ' ':
            self.paused = not self.paused
        elif event.key == 'r':
            self.reset()
        elif event.key == 'd':
            self.toggle_damping()
        elif event.key == 'escape':
            plt.close(self.fig)
    
    def reset(self):
        """Reset simulation to initial conditions."""
        self.state = self.initial_state.copy()
        self.time = 0.0
        self.initial_energy = self.pendulum.total_energy(self.state)
        self.energy_history = []
        self.time_history = []
        self.trace_x = []
        self.trace_y = []
        self.paused = False
        self.dragging = False
    
    def toggle_damping(self):
        """Toggle damping on/off."""
        if self.pendulum.damping == 0.0:
            self.pendulum.damping = 0.001
        else:
            self.pendulum.damping = 0.0
    
    def update(self, frame):
        """Animation update function."""
        current_time = time.time()
        
        # Update physics if not paused
        if not self.paused:
            # Multiple substeps for stability
            substeps = 2
            sub_dt = self.dt / substeps
            for _ in range(substeps):
                self.state = self.pendulum.rk4_step(self.state, sub_dt)
            self.time += self.dt
            
            # Track energy
            current_energy = self.pendulum.total_energy(self.state)
            self.energy_history.append(current_energy)
            self.time_history.append(self.time)
            
            # Limit history length
            if len(self.energy_history) > 2000:
                self.energy_history = self.energy_history[-2000:]
                self.time_history = self.time_history[-2000:]
        
        # Get positions
        (x1, y1), (x2, y2) = self.pendulum.cartesian_positions(self.state)
        
        # Update trace
        self.trace_x.append(x2)
        self.trace_y.append(y2)
        if len(self.trace_x) > self.max_trace:
            self.trace_x = self.trace_x[-self.max_trace:]
            self.trace_y = self.trace_y[-self.max_trace:]
        
        # Update pendulum visualization
        self.line1.set_data([0, x1], [0, y1])
        self.line2.set_data([x1, x2], [y1, y2])
        self.trace.set_data(self.trace_x, self.trace_y)
        
        # Update energy plot
        if len(self.energy_history) > 0:
            self.energy_line.set_data(self.time_history, self.energy_history)
            self.energy_ref.set_data([self.time_history[0], self.time_history[-1]], 
                                     [self.initial_energy, self.initial_energy])
            
            self.ax_energy.relim()
            self.ax_energy.autoscale_view()
        
        # Calculate FPS
        fps = 1.0 / (current_time - self.last_time) if (current_time - self.last_time) > 0 else 0
        self.last_time = current_time
        self.fps_history.append(fps)
        if len(self.fps_history) > 30:
            self.fps_history = self.fps_history[-30:]
        avg_fps = np.mean(self.fps_history)
        
        # Calculate energy drift
        if len(self.energy_history) > 0:
            current_energy = self.energy_history[-1]
            energy_drift = abs((current_energy - self.initial_energy) / self.initial_energy * 100)
        else:
            energy_drift = 0.0
        
        # Update status text
        status = f"Time: {self.time:.2f}s\n"
        status += f"FPS: {avg_fps:.1f}\n"
        status += f"Energy Drift: {energy_drift:.3f}%\n"
        status += f"Damping: {'ON' if self.pendulum.damping > 0 else 'OFF'}\n"
        status += f"Status: {'PAUSED' if self.paused else 'RUNNING'}\n"
        status += "\nControls:\n"
        status += "Space: Pause/Play\n"
        status += "R: Reset\n"
        status += "D: Toggle Damping\n"
        status += "Drag Bob: Reposition\n"
        status += "Esc: Quit"
        
        self.status_text.set_text(status)
        
        return self.line1, self.line2, self.trace, self.energy_line, self.energy_ref, self.status_text
    
    def run(self):
        """Start the animation."""
        anim = FuncAnimation(self.fig, self.update, interval=20, blit=True, cache_frame_data=False)
        plt.show()

if __name__ == '__main__':
    sim = DoublePendulumSimulation()
    sim.run()