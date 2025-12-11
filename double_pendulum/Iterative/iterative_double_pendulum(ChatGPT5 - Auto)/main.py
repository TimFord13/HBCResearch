# main.py
# ChatGPT5 conversation link - https://chatgpt.com/share/691b51ab-bf1c-800e-8952-65eab2a362ff
import math
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
from collections import deque

from physics import rk4_step, set_params, get_params, compute_energy

def main():
    # Physical parameters
    set_params(m1_val=1.0, m2_val=1.0, L1_val=1.0, L2_val=1.0, g_val=9.81)
    params = get_params()
    L1, L2 = params["L1"], params["L2"]
    m1, m2, g = params["m1"], params["m2"], params["g"]

    # Initial conditions and state
    initial_state = [math.radians(120.0), 0.0, math.radians(-10.0), 0.0]
    state = initial_state[:]  # [theta1, omega1, theta2, omega2]

    # Timing: ~60 FPS; integrate with fixed dt
    fps_target = 60
    interval_ms = 1000 / fps_target
    dt = 1.0 / 240.0
    steps_per_frame = 4  # physics: 4 * (1/240) = 1/60 s per visual frame
    sim_time = 0.0

    # Damping toggle
    damping_enabled = False
    damping_gamma = 0.02  # 1/s; effective velocity decay rate
    damp_factor_dt = lambda h: math.exp(-damping_gamma * h)

    # Figure and axes: left = pendulum, right = energy plot
    fig, (ax_sim, ax_energy) = plt.subplots(1, 2, figsize=(10, 5))
    try:
        fig.canvas.manager.set_window_title("Double Pendulum — [Space] Pause/Play  [R] Reset  [D] Damping  [Esc] Exit")
    except Exception:
        pass

    # Simulation view
    ax_sim.set_aspect("equal", adjustable="box")
    reach = L1 + L2
    margin = 0.1 * reach
    ax_sim.set_xlim(-reach - margin, reach + margin)
    ax_sim.set_ylim(-reach - margin, reach + margin)
    ax_sim.set_xlabel("x")
    ax_sim.set_ylabel("y")
    ax_sim.set_title("Double Pendulum (RK4, fixed dt)")

    line = Line2D([0, 0, 0], [0, 0, 0], lw=2)
    ax_sim.add_line(line)
    bob_radius = 0.05 * max(L1, L2)
    bob1 = Circle((0, 0), bob_radius, fill=True)
    bob2 = Circle((0, 0), bob_radius, fill=True)
    ax_sim.add_patch(bob1)
    ax_sim.add_patch(bob2)

    # Energy plot
    ax_energy.set_title("Total Energy over Time")
    ax_energy.set_xlabel("time (s)")
    ax_energy.set_ylabel("E = T + V")
    energy_line, = ax_energy.plot([], [], lw=1.5)

    # Rolling buffers (show last ~60 s)
    window_seconds = 60.0
    max_points = int(window_seconds * fps_target) + 10
    t_buf = deque(maxlen=max_points)
    e_buf = deque(maxlen=max_points)

    # Baseline energy for drift (%)
    T0, V0 = compute_energy(state)
    E0 = T0 + V0

    # Characteristic energy scale, used as a safe denominator fallback if |E0| is tiny
    # Rough potential span from hanging down: ~ g * (m1*L1 + m2*(L1+L2))
    E_scale = g * (m1 * L1 + m2 * (L1 + L2))

    # Overlay text for FPS and drift
    overlay_text = ax_sim.text(
        0.02, 0.98, "",
        transform=ax_sim.transAxes,
        ha="left", va="top",
        fontsize=10,
        bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=2.0),
    )

    # Control and interaction state
    paused = False
    dragging = False
    was_running_before_drag = False  # remember pre-drag run state
    hit_tolerance = bob_radius * 1.5  # click radius around bob2
    last_wall = time.perf_counter()
    fps_ema = float(fps_target)
    alpha = 0.1  # EMA smoothing

    # Reduce plot churn to help FPS
    autoscale_every = 20
    setdata_every = 2
    frame_counter = 0

    def state_to_xy(s):
        theta1, _, theta2, _ = s
        x1 = L1 * math.sin(theta1)
        y1 = -L1 * math.cos(theta1)
        x2 = x1 + L2 * math.sin(theta2)
        y2 = y1 - L2 * math.cos(theta2)
        return x1, y1, x2, y2

    def draw_from_state(s):
        x1, y1, x2, y2 = state_to_xy(s)
        line.set_data([0, x1, x2], [0, y1, y2])
        bob1.center = (x1, y1)
        bob2.center = (x2, y2)

    def init():
        draw_from_state(state)
        energy_line.set_data([], [])
        ax_energy.relim()
        ax_energy.autoscale_view()
        overlay_text.set_text("")
        return line, bob1, bob2, energy_line, overlay_text

    def update(frame_idx):
        nonlocal state, sim_time, last_wall, fps_ema, frame_counter, E0
        frame_counter += 1

        # Only integrate when running and not dragging
        if not paused and not dragging:
            for _ in range(steps_per_frame):
                state = rk4_step(state, dt)
                if damping_enabled:
                    theta1, w1, theta2, w2 = state
                    f = damp_factor_dt(dt)
                    state = [theta1, w1 * f, theta2, w2 * f]
            sim_time += steps_per_frame * dt

            # Energy tracking buffers
            T, V = compute_energy(state)
            E = T + V
            t_buf.append(sim_time)
            e_buf.append(E)

        # Update pendulum drawing either way
        draw_from_state(state)

        # Update energy plot with decimation
        if len(t_buf) >= 2 and frame_counter % setdata_every == 0:
            energy_line.set_data(t_buf, e_buf)
            if frame_counter % autoscale_every == 0:
                ax_energy.set_xlim(t_buf[0], max(t_buf[-1], t_buf[0] + 1e-6))
                emin = min(e_buf)
                emax = max(e_buf)
                pad = 0.02 * max(1.0, abs(emax - emin))
                ax_energy.set_ylim(emin - pad, emax + pad)

        # Update FPS and drift overlay
        now = time.perf_counter()
        dt_wall = max(1e-9, now - last_wall)
        last_wall = now
        inst_fps = 1.0 / dt_wall
        fps_ema = (1 - alpha) * fps_ema + alpha * inst_fps

        T_cur, V_cur = compute_energy(state)
        E_cur = T_cur + V_cur
        # Use a safe denominator so percentage can't explode when |E0| ~ 0
        denom = max(abs(E0), 0.25 * E_scale, 1e-9)
        drift_pct = 100.0 * (E_cur - E0) / denom
        tags = []
        if dragging:
            tags.append("drag")
        if damping_enabled:
            tags.append("damp")
        tag_str = f" ({', '.join(tags)})" if tags else ""
        overlay_text.set_text(f"FPS: {fps_ema:5.1f}\nEnergy drift: {drift_pct:+.3f}%{tag_str}")

        return line, bob1, bob2, energy_line, overlay_text

    # -------------------------
    # Mouse interaction handlers
    # -------------------------

    def on_press(event):
        nonlocal paused, dragging, was_running_before_drag
        if event.inaxes != ax_sim:
            return
        x1, y1, x2, y2 = state_to_xy(state)
        if event.xdata is None or event.ydata is None:
            return
        dx = event.xdata - x2
        dy = event.ydata - y2
        if math.hypot(dx, dy) <= hit_tolerance:
            dragging = True
            was_running_before_drag = not paused
            paused = True  # pause simulation while dragging

    def on_motion(event):
        nonlocal state
        if not dragging:
            return
        if event.inaxes != ax_sim or event.xdata is None or event.ydata is None:
            return

        theta1, _, _, _ = state
        x1 = L1 * math.sin(theta1)
        y1 = -L1 * math.cos(theta1)

        dx = event.xdata - x1
        dy = event.ydata - y1
        r = math.hypot(dx, dy)
        if r < 1e-12:
            return
        scale = L2 / r
        px = x1 + dx * scale
        py = y1 + dy * scale

        relx = max(-L2, min(L2, px - x1))
        rely = max(-L2, min(L2, py - y1))
        theta2_new = math.atan2(relx / L2, -rely / L2)

        state = [theta1, 0.0, theta2_new, 0.0]
        draw_from_state(state)
        fig.canvas.draw_idle()

    def on_release(event):
        nonlocal dragging, paused, E0
        if not dragging:
            return
        dragging = False
        # Re-baseline energy after user intervention
        T_now, V_now = compute_energy(state)
        E0 = T_now + V_now
        paused = not was_running_before_drag

    # Keyboard controls
    def on_key(event):
        nonlocal paused, state, sim_time, fps_ema, last_wall, t_buf, e_buf, E0, damping_enabled
        if event.key == " ":
            paused = not paused
            last_wall = time.perf_counter()
        elif event.key in ("r", "R"):
            state = initial_state[:]
            sim_time = 0.0
            t_buf.clear()
            e_buf.clear()
            T_base, V_base = compute_energy(state)
            E0 = T_base + V_base
            draw_from_state(state)
            fig.canvas.draw_idle()
        elif event.key in ("d", "D"):
            # Toggle damping and re-baseline to avoid percent blowups
            damping_enabled = not damping_enabled
            T_now, V_now = compute_energy(state)
            E0 = T_now + V_now
            print("E0 at damping toggle:", E0)
        elif event.key == "escape":
            try:
                anim.event_source.stop()
            except Exception:
                pass
            plt.close(fig)

    cid_key = fig.canvas.mpl_connect("key_press_event", on_key)
    cid_press = fig.canvas.mpl_connect("button_press_event", on_press)
    cid_motion = fig.canvas.mpl_connect("motion_notify_event", on_motion)
    cid_release = fig.canvas.mpl_connect("button_release_event", on_release)

    anim = FuncAnimation(
        fig,
        update,
        init_func=init,
        interval=interval_ms,
        blit=False
    )

    plt.tight_layout()
    plt.show()

    # Clean up
    try:
        fig.canvas.mpl_disconnect(cid_key)
        fig.canvas.mpl_disconnect(cid_press)
        fig.canvas.mpl_disconnect(cid_motion)
        fig.canvas.mpl_disconnect(cid_release)
    except Exception:
        pass

if __name__ == "__main__":
    main()
