#Gemini chat link https://gemini.google.com/share/fa913d7ba55a

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import physics

# Simulation Parameters
DT = 0.01
FPS = 60
INTERVAL = 1000 / FPS
DAMPING_FACTOR = 0.5

# Initial Conditions
initial_theta1 = np.radians(120)
initial_theta2 = np.radians(-10)
initial_omega1 = 0.0
initial_omega2 = 0.0

# Global State
state = np.array([initial_theta1, initial_omega1, initial_theta2, initial_omega2])
is_paused = False
is_dragging = False
use_damping = False

# Data Logging
time_history = []; energy_history = []
sim_time = 0.0; initial_energy = 0.0
last_real_time = time.time(); fps_display = 0.0

def get_coords(state):
    theta1, _, theta2, _ = state
    x1 = physics.L1 * np.sin(theta1)
    y1 = -physics.L1 * np.cos(theta1)
    x2 = x1 + physics.L2 * np.sin(theta2)
    y2 = y1 - physics.L2 * np.cos(theta2)
    return (0, 0), (x1, y1), (x2, y2)

def calculate_ik(target_x, target_y):
    max_reach = physics.L1 + physics.L2 - 0.001
    dist = np.hypot(target_x, target_y)
    if dist > max_reach:
        scale = max_reach / dist
        target_x *= scale; target_y *= scale
        dist = max_reach

    base_angle = np.arctan2(target_x, -target_y)
    cos_alpha = (physics.L1**2 + dist**2 - physics.L2**2) / (2 * physics.L1 * dist)
    alpha = np.arccos(np.clip(cos_alpha, -1.0, 1.0))

    theta1 = base_angle - alpha
    elbow_x = physics.L1 * np.sin(theta1)
    elbow_y = -physics.L1 * np.cos(theta1)
    theta2 = np.arctan2(target_x - elbow_x, -(target_y - elbow_y))
    return theta1, theta2

# Setup Figure
fig, (ax_sim, ax_energy) = plt.subplots(1, 2, figsize=(12, 6))
plt.subplots_adjust(bottom=0.2)

# Sim Plot
limit = physics.L1 + physics.L2 + 0.2
ax_sim.set_aspect('equal'); ax_sim.set_xlim(-limit, limit); ax_sim.set_ylim(-limit, limit)
ax_sim.grid(True, alpha=0.3)
ax_sim.set_title("Space: Pause | R: Reset | D: Damping | Drag: Move")
rods, = ax_sim.plot([], [], 'o-', lw=2, color='black')
trace, = ax_sim.plot([], [], '-', lw=1, color='red', alpha=0.5)
trace_x, trace_y = [], []
stats_text = ax_sim.text(0.05, 0.95, '', transform=ax_sim.transAxes, va='top', 
                         bbox=dict(facecolor='white', alpha=0.7))

# Energy Plot
ax_energy.set_title("Total Energy vs Time")
ax_energy.set_xlabel("Time (s)"); ax_energy.set_ylabel("Energy (J)")
ax_energy.grid(True, alpha=0.3)
energy_line, = ax_energy.plot([], [], lw=1.5, color='blue')

def reset_simulation():
    global state, trace_x, trace_y, time_history, energy_history, sim_time, initial_energy
    state = np.array([initial_theta1, initial_omega1, initial_theta2, initial_omega2])
    trace_x.clear(); trace_y.clear()
    time_history.clear(); energy_history.clear()
    sim_time = 0.0
    _, _, initial_energy = physics.compute_energy(state)
    time_history.append(0); energy_history.append(initial_energy)

def on_key(event):
    global is_paused, use_damping
    if event.key == ' ': is_paused = not is_paused
    elif event.key == 'r': reset_simulation()
    elif event.key == 'd': use_damping = not use_damping
    elif event.key == 'escape': plt.close(fig)

def on_click(event):
    global is_dragging
    if event.inaxes == ax_sim and event.button == 1:
        _, _, p2 = get_coords(state)
        if np.hypot(event.xdata - p2[0], event.ydata - p2[1]) < 0.3:
            is_dragging = True

def on_release(event):
    global is_dragging, state
    if event.button == 1 and is_dragging:
        is_dragging = False
        state[1] = 0.0; state[3] = 0.0
        reset_simulation_keep_pos()

def on_move(event):
    if is_dragging and event.inaxes == ax_sim:
        t1, t2 = calculate_ik(event.xdata, event.ydata)
        state[0] = t1; state[2] = t2; state[1] = 0.0; state[3] = 0.0

def reset_simulation_keep_pos():
    global time_history, energy_history, sim_time, initial_energy
    time_history.clear(); energy_history.clear(); sim_time = 0.0
    _, _, initial_energy = physics.compute_energy(state)
    time_history.append(0); energy_history.append(initial_energy)

def init():
    reset_simulation()
    rods.set_data([], []); trace.set_data([], []); energy_line.set_data([], [])
    stats_text.set_text('')
    return rods, trace, energy_line, stats_text

def animate(i):
    global state, sim_time, last_real_time, fps_display
    
    curr = time.time()
    dt_real = curr - last_real_time
    last_real_time = curr
    if dt_real > 0: fps_display = 0.9 * fps_display + 0.1 * (1.0 / dt_real)

    if not is_paused and not is_dragging:
        d_val = DAMPING_FACTOR if use_damping else 0.0
        state = physics.rk4_step(state, DT, damping=d_val)
        sim_time += DT
        
        _, _, total_E = physics.compute_energy(state)
        time_history.append(sim_time); energy_history.append(total_E)
        if len(time_history) > 1000: time_history.pop(0); energy_history.pop(0)
        
        _, _, p2 = get_coords(state)
        trace_x.append(p2[0]); trace_y.append(p2[1])
        if len(trace_x) > 50: trace_x.pop(0); trace_y.pop(0)

    p0, p1, p2 = get_coords(state)
    rods.set_data([p0[0], p1[0], p2[0]], [p0[1], p1[1], p2[1]])
    trace.set_data(trace_x, trace_y)

    if len(energy_history) > 0:
        energy_line.set_data(time_history, energy_history)
        if len(time_history) > 1:
            ax_energy.set_xlim(min(time_history), max(time_history) + 0.5)
            e_vals = energy_history
            pad = (max(e_vals) - min(e_vals)) * 0.1 if max(e_vals) != min(e_vals) else 0.1
            ax_energy.set_ylim(min(e_vals) - pad, max(e_vals) + pad)
            
            # --- UPDATED TEXT LOGIC ---
            curr_E = e_vals[-1]
            if use_damping:
                # Show raw energy when damping is on (Drift is meaningless here)
                metric_str = f"Energy: {curr_E:.2f} J"
                damp_txt = "ON"
            else:
                # Show drift when damping is off (Checking numerical stability)
                drift = 100 * abs(curr_E - initial_energy) / abs(initial_energy) if initial_energy != 0 else 0
                metric_str = f"Drift: {drift:.3f}%"
                damp_txt = "OFF"
                
            stats_text.set_text(f'FPS: {fps_display:.1f}\n{metric_str}\nDamping: {damp_txt}\nTime: {sim_time:.1f}s')

    return rods, trace, energy_line, stats_text

fig.canvas.mpl_connect('key_press_event', on_key)
fig.canvas.mpl_connect('button_press_event', on_click)
fig.canvas.mpl_connect('button_release_event', on_release)
fig.canvas.mpl_connect('motion_notify_event', on_move)

ani = animation.FuncAnimation(fig, animate, init_func=init, interval=INTERVAL, blit=True)

if __name__ == "__main__":
    plt.show()