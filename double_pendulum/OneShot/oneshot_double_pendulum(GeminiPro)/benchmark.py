# benchmark.py

import time
import numpy as np
from physics import DoublePendulum

def benchmark(steps=20000, dt=0.001):
    """Runs the integrator without rendering and returns mean step time (µs) and energy drift (%)"""
    
    pendulum = DoublePendulum(L1=1.0, L2=1.0, m1=1.0, m2=1.0)
    pendulum.set_state(np.pi / 2, 0.0, np.pi, 0.0)
    
    initial_energy = pendulum.energy()
    
    start_time = time.perf_counter()
    
    for _ in range(steps):
        pendulum.step(dt)
        
    end_time = time.perf_counter()
    
    final_energy = pendulum.energy()
    
    duration = end_time - start_time
    mean_step_time_us = (duration / steps) * 1e6
    
    energy_drift_percent = abs((final_energy - initial_energy) / initial_energy) * 100
    
    print("--- Benchmark Results ---")
    print(f"  - Total steps:       {steps}")
    print(f"  - dt:                {dt} s")
    print(f"  - Total sim time:    {steps * dt:.2f} s")
    print(f"  - Real time elapsed: {duration:.4f} s")
    print(f"  - Mean step time:    {mean_step_time_us:.2f} µs")
    print(f"  - Initial Energy:    {initial_energy:.4f} J")
    print(f"  - Final Energy:      {final_energy:.4f} J")
    print(f"  - Energy Drift:      {energy_drift_percent:.6f} %")
    
    return mean_step_time_us, energy_drift_percent

if __name__ == '__main__':
    benchmark()