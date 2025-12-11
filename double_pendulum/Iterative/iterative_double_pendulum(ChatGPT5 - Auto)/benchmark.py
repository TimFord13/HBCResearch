# benchmark.py
import math
import time
from physics import rk4_step, compute_energy, set_params

def benchmark(steps=20000, dt=0.001):
    """
    Runs the integrator without rendering and returns:
      (mean_step_time_us, energy_drift_percent)

    - Uses time.perf_counter() for timing.
    - Starts from a standard initial condition.
    """
    # Parameters and initial state
    set_params(1.0, 1.0, 1.0, 1.0, 9.81)
    state = [math.radians(120.0), 0.0, math.radians(-10.0), 0.0]

    # Baseline energy
    T0, V0 = compute_energy(state)
    E0 = T0 + V0

    # Warm-up few steps (JIT-nope, but CPU caches like treats)
    for _ in range(100):
        state = rk4_step(state, dt)

    # Timed run
    start = time.perf_counter()
    for _ in range(steps):
        state = rk4_step(state, dt)
    end = time.perf_counter()

    # Energy drift
    T1, V1 = compute_energy(state)
    E1 = T1 + V1
    drift_pct = 100.0 * (E1 - E0) / (abs(E0) + 1e-12)

    mean_step_time_us = (end - start) / steps * 1e6

    print(f"Steps: {steps}  dt: {dt}")
    print(f"Mean step time: {mean_step_time_us:.2f} µs")
    print(f"Energy drift: {drift_pct:+.6f} %")

    return mean_step_time_us, drift_pct

if __name__ == "__main__":
    benchmark()
