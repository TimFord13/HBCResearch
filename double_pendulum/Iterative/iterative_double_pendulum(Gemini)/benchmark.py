# benchmark.py
import time
import numpy as np
import physics

def benchmark(steps=20000, dt=0.001):
    """
    Runs the integrator without rendering and returns performance stats.
    
    Args:
        steps (int): Number of integration steps to run.
        dt (float): Time step size.
        
    Returns:
        tuple: (mean_step_time_us, drift_percent)
    """
    # Initial state: theta1=120 deg, theta2=-10 deg
    state = np.array([np.radians(120), 0.0, np.radians(-10), 0.0])
    
    _, _, start_energy = physics.compute_energy(state)
    
    print(f"Starting Benchmark: {steps} steps, dt={dt}s ...")
    
    # Timing Start
    t0 = time.perf_counter()
    
    for _ in range(steps):
        state = physics.rk4_step(state, dt, damping=0.0)
        
    # Timing End
    t1 = time.perf_counter()
    
    total_time = t1 - t0
    mean_step_time_us = (total_time / steps) * 1_000_000
    
    _, _, end_energy = physics.compute_energy(state)
    drift_percent = abs((end_energy - start_energy) / start_energy) * 100
    
    print(f"Done.")
    print(f"Total Time: {total_time:.4f} s")
    print(f"Mean Step Time: {mean_step_time_us:.3f} µs")
    print(f"Energy Drift: {drift_percent:.4f}%")
    
    return mean_step_time_us, drift_percent

if __name__ == "__main__":
    benchmark()