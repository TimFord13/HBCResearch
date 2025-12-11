import numpy as np
import time
from physics import DoublePendulum

def benchmark(steps=20000, dt=0.001):
    """
    Runs the integrator without rendering and returns performance metrics.
    
    Args:
        steps: number of integration steps to perform
        dt: time step size
    
    Returns:
        dict with keys:
            - mean_step_time_us: mean time per step in microseconds
            - total_time_s: total elapsed time in seconds
            - energy_drift_percent: percentage energy drift
            - final_time: simulated time reached
    """
    # Initialize pendulum with no damping for energy conservation test
    pendulum = DoublePendulum(m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81, damping=0.0)
    
    # Initial state: [theta1, omega1, theta2, omega2]
    state = np.array([np.pi/2, 0.0, np.pi/2, 0.0])
    
    # Record initial energy
    initial_energy = pendulum.total_energy(state)
    
    # Run integration
    start_time = time.perf_counter()
    
    for i in range(steps):
        state = pendulum.rk4_step(state, dt)
    
    end_time = time.perf_counter()
    
    # Calculate final energy and drift
    final_energy = pendulum.total_energy(state)
    energy_drift = abs((final_energy - initial_energy) / initial_energy * 100)
    
    # Calculate timing
    total_time = end_time - start_time
    mean_step_time_us = (total_time / steps) * 1e6
    final_sim_time = steps * dt
    
    return {
        'mean_step_time_us': mean_step_time_us,
        'total_time_s': total_time,
        'energy_drift_percent': energy_drift,
        'final_time': final_sim_time,
        'steps': steps,
        'dt': dt
    }

def run_benchmark_suite():
    """Run a suite of benchmarks with different parameters."""
    print("=" * 70)
    print("DOUBLE PENDULUM BENCHMARK SUITE")
    print("=" * 70)
    
    # Test 1: Standard benchmark
    print("\nTest 1: Standard Benchmark (20000 steps, dt=0.001)")
    print("-" * 70)
    result = benchmark(steps=20000, dt=0.001)
    print(f"Mean step time:    {result['mean_step_time_us']:.2f} µs")
    print(f"Total time:        {result['total_time_s']:.3f} s")
    print(f"Energy drift:      {result['energy_drift_percent']:.6f} %")
    print(f"Simulated time:    {result['final_time']:.2f} s")
    print(f"Real-time factor:  {result['final_time']/result['total_time_s']:.1f}x")
    
    # Test 2: Long simulation
    print("\nTest 2: Long Simulation (30000 steps, dt=0.001)")
    print("-" * 70)
    result = benchmark(steps=30000, dt=0.001)
    print(f"Mean step time:    {result['mean_step_time_us']:.2f} µs")
    print(f"Total time:        {result['total_time_s']:.3f} s")
    print(f"Energy drift:      {result['energy_drift_percent']:.6f} %")
    print(f"Simulated time:    {result['final_time']:.2f} s")
    
    # Test 3: Smaller time step
    print("\nTest 3: High Precision (10000 steps, dt=0.0005)")
    print("-" * 70)
    result = benchmark(steps=10000, dt=0.0005)
    print(f"Mean step time:    {result['mean_step_time_us']:.2f} µs")
    print(f"Total time:        {result['total_time_s']:.3f} s")
    print(f"Energy drift:      {result['energy_drift_percent']:.6f} %")
    print(f"Simulated time:    {result['final_time']:.2f} s")
    
    # Test 4: Larger time step (stability test)
    print("\nTest 4: Stability Test (10000 steps, dt=0.002)")
    print("-" * 70)
    result = benchmark(steps=10000, dt=0.002)
    print(f"Mean step time:    {result['mean_step_time_us']:.2f} µs")
    print(f"Total time:        {result['total_time_s']:.3f} s")
    print(f"Energy drift:      {result['energy_drift_percent']:.6f} %")
    print(f"Simulated time:    {result['final_time']:.2f} s")
    
    # Test 5: Different initial conditions
    print("\nTest 5: Chaotic Initial Conditions")
    print("-" * 70)
    pendulum = DoublePendulum(m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81, damping=0.0)
    state = np.array([np.pi/4, 1.0, 3*np.pi/4, -0.5])
    initial_energy = pendulum.total_energy(state)
    
    steps = 20000
    dt = 0.001
    start_time = time.perf_counter()
    
    for i in range(steps):
        state = pendulum.rk4_step(state, dt)
    
    end_time = time.perf_counter()
    final_energy = pendulum.total_energy(state)
    energy_drift = abs((final_energy - initial_energy) / initial_energy * 100)
    
    print(f"Mean step time:    {((end_time - start_time) / steps) * 1e6:.2f} µs")
    print(f"Total time:        {end_time - start_time:.3f} s")
    print(f"Energy drift:      {energy_drift:.6f} %")
    print(f"Simulated time:    {steps * dt:.2f} s")
    
    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    run_benchmark_suite()