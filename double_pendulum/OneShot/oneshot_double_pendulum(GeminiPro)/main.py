# main.py

import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
from physics import DoublePendulum

# --- Simulation Parameters ---
DT = 0.005  # Physics time step (s)
L1, L2 = 1.0, 1.0
m1, m2 = 1.0, 1.0
DAMPING = 0.05
MAX_TRAIL_POINTS = 300
TIME_HISTORY_S = 20

# --- Setup ---
pendulum = DoublePendulum(L1=L1, L2=L2, m1=m1, m2=m2)
# A chaotic initial state
pendulum.set_state(th1=np.pi * 0.75, w1=0.0, th2=np.pi * 0.75, w2=0.0)
pendulum.initial_state = pendulum.y.copy()
initial_energy = pendulum.energy()

# --- Global State for Interaction ---
is_paused = False
is_dragging = False
damping_enabled = False

# --- Data for Plotting ---
time_data = deque(maxlen=int(TIME_HISTORY_S / DT))
energy_data = deque(maxlen=int(TIME_HISTORY_S / DT))
trail_x = deque(maxlen=MAX_TRAIL_POINTS)
trail_y = deque(maxlen=MAX_TRAIL_POINTS)

# --- Matplotlib Figure Setup ---
fig = plt.figure(figsize=(12, 8), facecolor='whitesmoke')
gs = fig.add_gridspec(2, 2)
ax_pendulum = fig.add_subplot(gs[:, 0], facecolor='#f0f0f0')
ax_energy = fig.add_subplot(gs[0, 1], facecolor='#f0f0f0')

# Pendulum subplot
ax_pendulum.set_title("Double Pendulum")
extents = L1 + L2
ax_pendulum.set_xlim(-extents * 1.1, extents * 1.1)
ax_pendulum.set_ylim(-extents * 1.1, extents * 1.1)
ax_pendulum.set_aspect('equal')
ax_pendulum.axis('off')

# Energy subplot
ax_energy.set_title("Total Energy")
ax_energy.set_xlabel("Time (s)")
ax_energy.set_ylabel("Energy (J)")
ax_energy.grid(True, linestyle=':')

# --- Artists to be animated ---
pivot, = ax_pendulum.plot([0], [0], 'ko', markersize=5)
line1, = ax_pendulum.plot([], [], 'k-', lw=2)
bob1, = ax_pendulum.plot([], [], 'o', markersize=10, color='royalblue', zorder=10)
line2, = ax_pendulum.plot([], [], 'k-', lw=2)
bob2, = ax_pendulum.plot([], [], 'o', markersize=10, color='crimson', zorder=10)
trail, = ax_pendulum.plot([], [], '-', color='gray', alpha=0.7, lw=1)
energy_line, = ax_energy.plot([], [], '-', lw=2, color='darkorange')
energy_ref_line = ax_energy.axhline(initial_energy, color='r', linestyle='--', lw=1, label=f'Initial E = {initial_energy:.2f} J')
ax_energy.legend(loc='upper right')
status_text = ax_pendulum.text(0.02, 0.98, '', transform=ax_pendulum.transAxes, va='top', fontsize=10)
controls_text = fig.text(0.01, 0.01, "Controls: [Space]=Pause, [R]=Reset, [D]=Damping, [Esc]=Quit, Drag Bob 2", fontsize=8)

# --- Frame timing ---
frame_times = deque(maxlen=60)
t_start = time.perf_counter()

def init():
    """Initialize animation artists."""
    return line1, bob1, line2, bob2, trail, energy_line, status_text

def update(frame):
    """Main animation loop."""
    global is_paused, t_start, initial_energy

    t_frame_start = time.perf_counter()
    if not is_paused and not is_dragging:
        elapsed = t_frame_start - t_start
        num_steps = max(1, int(elapsed / DT))
        for _ in range(num_steps):
            pendulum.step(DT)
    t_start = time.perf_counter()

    x1, y1, x2, y2 = pendulum.positions()
    current_energy = pendulum.energy()
    energy_drift = ((current_energy - initial_energy) / initial_energy) * 100 if initial_energy != 0 else 0
    
    trail_x.append(x2)
    trail_y.append(y2)
    
    if not is_paused:
        current_time = len(time_data) * DT
        time_data.append(current_time)
        energy_data.append(current_energy)

    line1.set_data([0, x1], [0, y1])
    bob1.set_data([x1], [y1])
    line2.set_data([x1, x2], [y1, y2])
    bob2.set_data([x2], [y2])
    trail.set_data(trail_x, trail_y)
    energy_line.set_data(time_data, energy_data)

    if time_data:
        ax_energy.set_xlim(max(0, time_data[-1] - TIME_HISTORY_S), time_data[-1] + 1)
        energy_range = max(np.ptp(energy_data), abs(initial_energy) * 0.1)
        ax_energy.set_ylim(np.mean(energy_data) - energy_range, np.mean(energy_data) + energy_range)

    frame_times.append(time.perf_counter())
    fps = len(frame_times) / (frame_times[-1] - frame_times[0]) if len(frame_times) > 1 else 0
    
    status_str = f"FPS: {fps:.1f}\nEnergy Drift: {energy_drift:.4f} %\nDamping: {'ON' if damping_enabled else 'OFF'}"
    if is_paused: status_str += "\nPAUSED"
    status_text.set_text(status_str)

    return line1, bob1, line2, bob2, trail, energy_line, status_text

def reset_simulation():
    """Helper function to reset the simulation state and plots."""
    global initial_energy
    pendulum.reset()
    initial_energy = pendulum.energy()
    energy_ref_line.set_ydata([initial_energy, initial_energy])
    energy_ref_line.set_label(f'Initial E = {initial_energy:.2f} J')
    ax_energy.legend(loc='upper right')
    time_data.clear(); energy_data.clear(); trail_x.clear(); trail_y.clear()

def on_key_press(event):
    global is_paused, damping_enabled
    if event.key == ' ': is_paused = not is_paused
    elif event.key == 'r': reset_simulation()
    elif event.key == 'd':
        damping_enabled = not damping_enabled
        pendulum.damping = DAMPING if damping_enabled else 0.0
    elif event.key == 'escape': plt.close(fig)

def on_mouse_press(event):
    global is_dragging
    if event.inaxes != ax_pendulum or event.button != 1: return
    x_mouse, y_mouse = event.xdata, event.ydata
    _, _, x2, y2 = pendulum.positions()
    if np.sqrt((x_mouse - x2)**2 + (y_mouse - y2)**2) < 0.2:
        is_dragging = True

def on_mouse_move(event):
    if not is_dragging or event.inaxes != ax_pendulum: return
    x, y = event.xdata, event.ydata
    d = np.sqrt(x**2 + y**2)
    d = np.clip(d, abs(L1 - L2), L1 + L2)

    alpha = np.arccos(np.clip((d**2 + L1**2 - L2**2) / (2 * d * L1), -1, 1))
    beta = np.arctan2(x, -y)
    th1 = beta - alpha
    
    gamma = np.arccos(np.clip((L1**2 + L2**2 - d**2) / (2 * L1 * L2), -1, 1))
    th2 = th1 + np.pi - gamma

    pendulum.set_state(th1, 0, th2, 0)
    _, _, x2_new, y2_new = pendulum.positions()
    trail_x.append(x2_new); trail_y.append(y2_new)

def on_mouse_release(event):
    global is_dragging, initial_energy
    if is_dragging and event.button == 1:
        is_dragging = False
        initial_energy = pendulum.energy()
        energy_ref_line.set_ydata([initial_energy, initial_energy])
        energy_ref_line.set_label(f'Initial E = {initial_energy:.2f} J')
        ax_energy.legend(loc='upper right')
        time_data.clear(); energy_data.clear()

# --- Connect events and start animation ---
fig.canvas.mpl_connect('key_press_event', on_key_press)
fig.canvas.mpl_connect('button_press_event', on_mouse_press)
fig.canvas.mpl_connect('motion_notify_event', on_mouse_move)
fig.canvas.mpl_connect('button_release_event', on_mouse_release)

ani = animation.FuncAnimation(fig, update, frames=None, init_func=init, blit=True, interval=16, save_count=50) # interval=16ms ~ 60FPS

plt.tight_layout()
plt.show()