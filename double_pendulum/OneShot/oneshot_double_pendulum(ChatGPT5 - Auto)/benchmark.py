# benchmark.py
# Headless integrator performance + energy drift check
from __future__ import annotations
import time
import numpy as np
from physics import simulate, energy

def benchmark(steps=20000, dt=0.001):
    """
    Runs the integrator without rendering and returns:
        mean_step_us, drift_pct
    """
    params = dict(m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81, damping=0.0)
    y0 = np.array([np.deg2rad(120), np.deg2rad(-10), 0.0, 0.0], dtype=float)

    start = time.perf_counter()
    traj = simulate(y0, dt, steps, params)
    elapsed = time.perf_counter() - start
    mean_step_us = (elapsed / steps) * 1e6

    E0 = energy(traj[0], params)
    E_end = energy(traj[-1], params)
    drift_pct = 100.0 * (E_end - E0) / abs(E0) if abs(E0) > 1e-9 else 0.0
    return mean_step_us, drift_pct

if __name__ == "__main__":
    us, drift = benchmark()
    print(f"Mean step time: {us:.1f} µs  |  Energy drift over run: {drift:+.3f}%")
