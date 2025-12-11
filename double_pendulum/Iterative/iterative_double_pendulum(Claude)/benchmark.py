# benchmark.py
import numpy as np
import time
from physics import DoublePendulum

def benchmark(steps=20000, dt=0.001):
    """
    Runs the integrator without rendering and returns mean step time (µs) and energy drift (%).
    
    Parameters:
    steps: number of integration steps
    dt: time step size
    
    Returns:
    tuple: (mean_step_time_us, energy_drift_percent)
    """
    # Create pendulum
    pendulum = DoublePendulum(m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81)
    
    # Initial conditions
    state = np.array([np.radians(120), 0.0, np.radians(-10), 0.0])
    
    # Calculate initial energy
    KE_init, PE_init = pendulum.compute_energy(state)
    initial_energy = KE_init + PE_init
    
    # Benchmark integration
    start_time = time.perf_counter()
    
    for _ in range(steps):
        state = pendulum.rk4_step(state, dt)
    
    end_time = time.perf_counter()
    
    # Calculate final energy
    KE_final, PE_final = pendulum.compute_energy(state)
    final_energy = KE_final + PE_final
    
    # Calculate metrics
    elapsed_time = end_time - start_time
    mean_step_time_us = (elapsed_time / steps) * 1e6
    
    energy_drift_percent = abs((final_energy - initial_energy) / initial_energy) * 100
    
    return mean_step_time_us, energy_drift_percent


def main():
    print("Running benchmark...")
    print("-" * 50)
    
    mean_time, drift = benchmark(steps=20000, dt=0.001)
    
    print(f"Steps: 20000")
    print(f"dt: 0.001 s")
    print(f"Mean step time: {mean_time:.2f} µs")
    print(f"Energy drift: {drift:.4f}%")
    print("-" * 50)
    
    # Additional benchmark with different parameters
    print("\nRunning extended benchmark...")
    print("-" * 50)
    
    mean_time2, drift2 = benchmark(steps=50000, dt=0.0005)
    
    print(f"Steps: 50000")
    print(f"dt: 0.0005 s")
    print(f"Mean step time: {mean_time2:.2f} µs")
    print(f"Energy drift: {drift2:.4f}%")
    print("-" * 50)


if __name__ == "__main__":
    main()