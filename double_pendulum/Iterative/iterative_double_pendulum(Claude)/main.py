#Claude chat link https://claude.ai/share/327ac52a-b0f3-42fc-b8d7-deef32052bac
# main.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
from physics import DoublePendulum

class DoublePendulumAnimation:
    def __init__(self, pendulum, initial_state, dt=0.01):
        """
        Initialize the animation.
        
        Parameters:
        pendulum: DoublePendulum instance
        initial_state: [theta1, omega1, theta2, omega2]
        dt: time step for integration
        """
        self.pendulum = pendulum
        self.initial_state = np.array(initial_state, dtype=float)
        self.state = np.array(initial_state, dtype=float)
        self.dt = dt
        self.paused = False
        self.damping_enabled = False
        self.damping_coefficient = 0.999  # Velocity multiplier per step
        
        # Mouse interaction
        self.dragging = False
        self.was_paused = False
        
        # Energy tracking
        self.times = []
        self.energies = []
        self.initial_energy = None
        self.last_damping_state = False
        
        # FPS tracking
        self.frame_count = 0
        self.fps_start_time = None
        self.current_fps = 0
        
        # Set up the figure with two subplots
        self.fig = plt.figure(figsize=(12, 6))
        self.ax_pendulum = plt.subplot(1, 2, 1)
        self.ax_energy = plt.subplot(1, 2, 2)
        
        # Pendulum subplot
        self.ax_pendulum.set_xlim(-2.5, 2.5)
        self.ax_pendulum.set_ylim(-2.5, 2.5)
        self.ax_pendulum.set_aspect('equal')
        self.ax_pendulum.grid(True, alpha=0.3)
        self.ax_pendulum.set_xlabel('X (m)')
        self.ax_pendulum.set_ylabel('Y (m)')
        self.ax_pendulum.set_title('Double Pendulum Simulation\n[Space: Pause | R: Reset | D: Damping | Esc: Exit | Drag Bob]')
        
        # Energy subplot
        self.ax_energy.set_xlabel('Time (s)')
        self.ax_energy.set_ylabel('Total Energy (J)')
        self.ax_energy.set_title('Energy vs Time')
        self.ax_energy.grid(True, alpha=0.3)
        self.energy_line, = self.ax_energy.plot([], [], 'b-', lw=1.5)
        
        # Create line for the pendulum arms
        self.line, = self.ax_pendulum.plot([], [], 'o-', lw=2, color='black', markersize=8)
        
        # Create circles for the bobs
        self.bob1 = Circle((0, 0), 0.08, fc='red', ec='darkred', zorder=10)
        self.bob2 = Circle((0, 0), 0.08, fc='blue', ec='darkblue', zorder=10)
        self.ax_pendulum.add_patch(self.bob1)
        self.ax_pendulum.add_patch(self.bob2)
        
        # Add pivot point
        self.pivot = Circle((0, 0), 0.05, fc='black', zorder=10)
        self.ax_pendulum.add_patch(self.pivot)
        
        # Time and energy display on pendulum subplot
        self.time_text = self.ax_pendulum.text(0.02, 0.98, '', transform=self.ax_pendulum.transAxes,
                                      verticalalignment='top', fontfamily='monospace', fontsize=9)
        self.energy_text = self.ax_pendulum.text(0.02, 0.93, '', transform=self.ax_pendulum.transAxes,
                                        verticalalignment='top', fontfamily='monospace', fontsize=9)
        self.status_text = self.ax_pendulum.text(0.02, 0.88, '', transform=self.ax_pendulum.transAxes,
                                        verticalalignment='top', fontfamily='monospace',
                                        color='red', fontsize=10, weight='bold')
        
        # FPS and energy drift display
        self.fps_text = self.ax_pendulum.text(0.02, 0.13, '', transform=self.ax_pendulum.transAxes,
                                      verticalalignment='bottom', fontfamily='monospace', fontsize=9)
        self.drift_text = self.ax_pendulum.text(0.02, 0.08, '', transform=self.ax_pendulum.transAxes,
                                        verticalalignment='bottom', fontfamily='monospace', fontsize=9)
        self.damping_text = self.ax_pendulum.text(0.02, 0.03, '', transform=self.ax_pendulum.transAxes,
                                        verticalalignment='bottom', fontfamily='monospace', fontsize=9)
        
        self.time = 0.0
        
        # Connect events
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_motion)
        
        plt.tight_layout()
        
    def reset_energy_tracking(self):
        """Reset energy tracking to current state."""
        self.times = []
        self.energies = []
        self.initial_energy = None
        
    def on_key_press(self, event):
        """Handle keyboard events."""
        if event.key == ' ':
            # Toggle pause
            self.paused = not self.paused
            self.status_text.set_text('PAUSED' if self.paused else '')
            self.fig.canvas.draw_idle()
        elif event.key == 'd':
            # Toggle damping
            self.damping_enabled = not self.damping_enabled
            self.damping_text.set_text(f'Damping: {"ON" if self.damping_enabled else "OFF"}')
            # Reset energy tracking when damping state changes
            self.reset_energy_tracking()
            self.fig.canvas.draw_idle()
        elif event.key == 'r':
            # Reset to initial conditions
            self.state = np.array(self.initial_state, dtype=float)
            self.time = 0.0
            self.reset_energy_tracking()
            self.frame_count = 0
            self.fps_start_time = None
            self.paused = False
            self.dragging = False
            self.damping_enabled = False
            self.status_text.set_text('')
            self.damping_text.set_text('Damping: OFF')
            self.fig.canvas.draw_idle()
        elif event.key == 'escape':
            # Exit cleanly
            plt.close(self.fig)
    
    def on_mouse_press(self, event):
        """Handle mouse button press."""
        if event.inaxes != self.ax_pendulum:
            return
        
        # Get current bob2 position
        x1, y1, x2, y2 = self.get_positions()
        
        # Check if click is near bob2
        if event.xdata is not None and event.ydata is not None:
            dist = np.sqrt((event.xdata - x2)**2 + (event.ydata - y2)**2)
            if dist < 0.2:  # Click within 0.2m of bob2
                self.dragging = True
                self.was_paused = self.paused
                self.paused = True
                self.status_text.set_text('DRAGGING')
    
    def on_mouse_release(self, event):
        """Handle mouse button release."""
        if self.dragging:
            self.dragging = False
            self.paused = self.was_paused
            self.status_text.set_text('PAUSED' if self.paused else '')
            # Set velocities to zero on release
            self.state[1] = 0.0  # omega1
            self.state[3] = 0.0  # omega2
            # Reset energy tracking after drag
            self.reset_energy_tracking()
    
    def on_mouse_motion(self, event):
        """Handle mouse motion."""
        if not self.dragging or event.inaxes != self.ax_pendulum:
            return
        
        if event.xdata is None or event.ydata is None:
            return
        
        # Target position for bob2
        target_x = event.xdata
        target_y = event.ydata
        
        # Inverse kinematics for double pendulum
        # Current bob1 position
        x1, y1, _, _ = self.get_positions()
        
        # Vector from bob1 to target
        dx = target_x - x1
        dy = target_y - y1
        dist = np.sqrt(dx**2 + dy**2)
        
        # Constrain to L2 length
        if dist > self.pendulum.L2:
            dx = dx * self.pendulum.L2 / dist
            dy = dy * self.pendulum.L2 / dist
        
        # Calculate theta2 from bob1 position to target
        theta2 = np.arctan2(dx, -dy)
        
        # Optionally adjust theta1 to get closer to target
        # Simple approach: keep theta1, only update theta2
        self.state[2] = theta2
        
        # Force redraw
        self.fig.canvas.draw_idle()
        
    def get_positions(self):
        """Calculate the (x, y) positions of both bobs."""
        theta1, _, theta2, _ = self.state
        
        x1 = self.pendulum.L1 * np.sin(theta1)
        y1 = -self.pendulum.L1 * np.cos(theta1)
        
        x2 = x1 + self.pendulum.L2 * np.sin(theta2)
        y2 = y1 - self.pendulum.L2 * np.cos(theta2)
        
        return x1, y1, x2, y2
    
    def init(self):
        """Initialize animation."""
        self.line.set_data([], [])
        self.energy_line.set_data([], [])
        self.damping_text.set_text(f'Damping: {"ON" if self.damping_enabled else "OFF"}')
        return (self.line, self.bob1, self.bob2, self.time_text, self.energy_text, 
                self.status_text, self.energy_line, self.fps_text, self.drift_text, self.damping_text)
    
    def update(self, frame):
        """Update the animation for each frame."""
        # FPS calculation
        import time as time_module
        if self.fps_start_time is None:
            self.fps_start_time = time_module.time()
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            elapsed = time_module.time() - self.fps_start_time
            self.current_fps = 30 / elapsed if elapsed > 0 else 0
            self.fps_start_time = time_module.time()
        
        # Only integrate if not paused and not dragging
        if not self.paused and not self.dragging:
            self.state = self.pendulum.rk4_step(self.state, self.dt)
            self.time += self.dt
            
            # Apply damping if enabled
            if self.damping_enabled:
                self.state[1] *= self.damping_coefficient  # omega1
                self.state[3] *= self.damping_coefficient  # omega2
        
        # Get positions
        x1, y1, x2, y2 = self.get_positions()
        
        # Update line (pivot -> bob1 -> bob2)
        self.line.set_data([0, x1, x2], [0, y1, y2])
        
        # Update bob positions
        self.bob1.center = (x1, y1)
        self.bob2.center = (x2, y2)
        
        # Calculate energy
        KE, PE = self.pendulum.compute_energy(self.state)
        total_energy = KE + PE
        
        # Track energy
        if self.initial_energy is None:
            self.initial_energy = total_energy
        
        if not self.paused and not self.dragging:
            self.times.append(self.time)
            self.energies.append(total_energy)
        
        # Update energy plot
        if len(self.times) > 0:
            self.energy_line.set_data(self.times, self.energies)
            self.ax_energy.relim()
            self.ax_energy.autoscale_view()
        
        # Calculate energy drift (only meaningful when damping is off)
        energy_drift = 0.0
        if self.initial_energy != 0:
            if self.damping_enabled:
                # With damping, show actual energy change (not drift)
                energy_drift = ((total_energy - self.initial_energy) / self.initial_energy) * 100
            else:
                # Without damping, show absolute drift
                energy_drift = abs((total_energy - self.initial_energy) / self.initial_energy) * 100
        
        # Update text displays
        self.time_text.set_text(f'Time: {self.time:.2f} s')
        self.energy_text.set_text(f'Energy: {total_energy:.3f} J')
        self.fps_text.set_text(f'FPS: {self.current_fps:.1f}')
        
        if self.damping_enabled:
            self.drift_text.set_text(f'Energy Change: {energy_drift:.2f}%')
        else:
            self.drift_text.set_text(f'Drift: {energy_drift:.3f}%')
        
        return (self.line, self.bob1, self.bob2, self.time_text, self.energy_text, 
                self.status_text, self.energy_line, self.fps_text, self.drift_text, self.damping_text)
    
    def animate(self):
        """Start the animation."""
        # Calculate interval for ~60 FPS
        interval = self.dt * 1000  # Convert to milliseconds
        
        anim = FuncAnimation(self.fig, self.update, init_func=self.init,
                           interval=interval, blit=True, cache_frame_data=False)
        plt.show()
        return anim


def main():
    # Create pendulum with default parameters
    pendulum = DoublePendulum(m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81)
    
    # Initial conditions: theta1=120°, theta2=-10°, both at rest
    theta1_init = np.radians(120)
    theta2_init = np.radians(-10)
    initial_state = [theta1_init, 0.0, theta2_init, 0.0]
    
    # Create and run animation
    animation = DoublePendulumAnimation(pendulum, initial_state, dt=0.01)
    animation.animate()


if __name__ == "__main__":
    main()