# main.py
# Real-time double pendulum using matplotlib animation. Pure Python.
# Controls:
#   Space: pause/play
#   R: reset
#   D: toggle damping
#   Esc: quit
#   Drag bob2 with mouse: simulation auto-pauses; angles follow cursor using IK.

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from time import perf_counter
from physics import rk4_step, energy

# --------------------- Simulation Params ---------------------
params = dict(m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81, damping=0.0)
dt = 1/240.0               # integrator timestep (seconds)
substeps_per_frame = 4     # 4 * 1/240 = 1/60 sec per animation frame
assert abs(substeps_per_frame*dt - 1/60.0) < 1e-6

# Initial state (radians and rad/s)
y0 = np.array([np.deg2rad(120), np.deg2rad(-10), 0.0, 0.0], dtype=float)
y  = y0.copy()

# Energy tracking
E0 = energy(y, params)
times, energies = [0.0], [E0]

# Runtime state
paused = False
dragging = False
last_frame_time = perf_counter()
fps = 0.0

# --------------------- Matplotlib Setup ---------------------
plt.rcParams["toolbar"] = "None"
fig = plt.figure(figsize=(8, 6), layout="constrained")
gs = fig.add_gridspec(2, 2, height_ratios=[3, 1])

ax = fig.add_subplot(gs[0, :])
ax.set_aspect("equal")
ax.set_xlim(-2.2, 2.2)
ax.set_ylim(-2.2, 1.2)
ax.set_title("Double Pendulum (Space: play/pause, R: reset, D: damping, drag bob2)")

# Energy subplot
axE = fig.add_subplot(gs[1, :])
lineE, = axE.plot([], [], lw=1)
axE.set_xlabel("Time (s)")
axE.set_ylabel("Energy")
axE.grid(True, alpha=0.3)

# Pendulum artists
origin = np.array([0.0, 0.0])
rod1, = ax.plot([], [], lw=2)
rod2, = ax.plot([], [], lw=2)
bob1, = ax.plot([], [], "o", ms=10)
bob2, = ax.plot([], [], "o", ms=10)

status = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top", ha="left",
                 bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.8))

def state_to_xy(y):
    t1, t2, w1, w2 = y
    x1 = params["L1"] * np.sin(t1)
    y1 = -params["L1"] * np.cos(t1)
    x2 = x1 + params["L2"] * np.sin(t2)
    y2 = y1 - params["L2"] * np.cos(t2)
    return (x1, y1, x2, y2)

def update_artists(y, t):
    x1, y1, x2, y2 = state_to_xy(y)
    rod1.set_data([origin[0], x1], [origin[1], y1])
    rod2.set_data([x1, x2], [y1, y2])
    bob1.set_data([x1], [y1])
    bob2.set_data([x2], [y2])

    # Update energy plot
    lineE.set_data(times, energies)
    axE.relim()
    axE.autoscale_view()

    drift_pct = 100.0 * (energies[-1] - E0) / abs(E0) if abs(E0) > 1e-9 else 0.0
    damp = params["damping"]
    status.set_text(f"t = {t:5.2f}s   FPS ≈ {fps:4.0f}   Energy drift = {drift_pct:+.3f}%   damping={damp:.3f}")

def reset_state():
    global y, times, energies, E0
    y[:] = y0
    times = [0.0]
    energies = [energy(y, params)]
    E0 = energies[0]

def near_bob2(event, thresh=0.1):
    x1,y1,x2,y2 = state_to_xy(y)
    if event.xdata is None or event.ydata is None:
        return False
    dx = event.xdata - x2
    dy = event.ydata - y2
    return (dx*dx + dy*dy) ** 0.5 < thresh

def ik_set_angles_from_xy(x, y):
    """Set y[0], y[1] so that bob2 end-effector is at (x,y). Clamp if outside reach.
    Uses 2-link planar IK (elbow-down)."""
    L1, L2 = params["L1"], params["L2"]
    r2 = x*x + y*y
    r = np.sqrt(r2)
    # Clamp to reachable annulus [|L1-L2|, L1+L2]
    r = np.clip(r, abs(L1 - L2) + 1e-9, L1 + L2 - 1e-9)
    cos_t2 = (r2 - L1*L1 - L2*L2) / (2*L1*L2)
    cos_t2 = np.clip(cos_t2, -1.0, 1.0)
    t2 = np.arccos(cos_t2)  # elbow-down
    t1 = np.arctan2(y, x) - np.arctan2(L2*np.sin(t2), L1 + L2*np.cos(t2))
    # Set angles; zero velocities when dragging
    y_state = y
    y_state[0] = t1
    y_state[1] = t2
    y_state[2] = 0.0
    y_state[3] = 0.0
    return y_state

def on_key(event):
    global paused
    key = (event.key or "").lower()
    if key == " ":
        paused = not paused
    elif key == "r":
        reset_state()
    elif key == "d":
        params["damping"] = 0.03 if params["damping"] == 0.0 else 0.0
    elif key == "escape":
        plt.close(fig)

def on_press(event):
    global paused, dragging
    if near_bob2(event):
        dragging = True
        paused = True

def on_release(event):
    global dragging
    dragging = False

def on_move(event):
    if dragging and event.xdata is not None and event.ydata is not None:
        ik_set_angles_from_xy(event.xdata, event.ydata)

fig.canvas.mpl_connect("key_press_event", on_key)
fig.canvas.mpl_connect("button_press_event", on_press)
fig.canvas.mpl_connect("button_release_event", on_release)
fig.canvas.mpl_connect("motion_notify_event", on_move)

def step(frame):
    global y, fps, last_frame_time
    t_prev = times[-1]
    if not paused and not dragging:
        for _ in range(substeps_per_frame):
            y = rk4_step(y, dt, params)
            t = times[-1] + dt
            times.append(t)
            energies.append(energy(y, params))
    else:
        # even when paused, keep time axis continuous for plotting
        times.append(times[-1] if times else 0.0)
        energies.append(energies[-1] if energies else energy(y, params))

    # FPS estimate
    now = perf_counter()
    dt_frame = now - last_frame_time
    last_frame_time = now
    if dt_frame > 0:
        fps = 1.0 / dt_frame

    update_artists(y, times[-1])
    return rod1, rod2, bob1, bob2, lineE, status

reset_state()
ani = FuncAnimation(fig, step, interval=1000/60, blit=True)
plt.show()
