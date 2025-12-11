import unittest
import numpy as np
import physics
import benchmark

class TestBenchmarkAndDamping(unittest.TestCase):
    
    def test_benchmark_runs(self):
        """Ensure the benchmark function runs and returns reasonable values."""
        # Run a short benchmark (1000 steps)
        us_per_step, drift = benchmark.benchmark(steps=1000, dt=0.001)
        
        # Check validity
        self.assertGreater(us_per_step, 0)
        self.assertGreaterEqual(drift, 0)
        print(f"\n[Short Bench] {us_per_step:.2f} µs/step, Drift: {drift:.4f}%")

    def test_damping_mechanic(self):
        """Ensure that enabling damping causes energy loss over time."""
        state = np.array([np.radians(90), 0.0, 0.0, 0.0])
        dt = 0.01
        
        # 1. Run WITHOUT damping
        s1 = state.copy()
        for _ in range(100):
            s1 = physics.rk4_step(s1, dt, damping=0.0)
        _, _, e_undamped = physics.compute_energy(s1)
        
        # 2. Run WITH damping
        s2 = state.copy()
        for _ in range(100):
            s2 = physics.rk4_step(s2, dt, damping=0.5)
        _, _, e_damped = physics.compute_energy(s2)
        
        print(f"\n[Damping Test] E_undamped: {e_undamped:.4f}, E_damped: {e_damped:.4f}")
        
        # Energy should be significantly lower with damping
        self.assertLess(e_damped, e_undamped - 0.1, 
                        "Damping did not significantly reduce energy.")

if __name__ == "__main__":
    unittest.main()