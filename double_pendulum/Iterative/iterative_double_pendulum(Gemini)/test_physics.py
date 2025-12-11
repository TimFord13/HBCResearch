import unittest
import numpy as np
import physics

class TestPhysicsExtended(unittest.TestCase):
    
    def setUp(self):
        # Initial conditions from the main simulation
        # Theta1 = 120 deg, Theta2 = -10 deg
        self.initial_state = np.array([np.radians(120), 0, np.radians(-10), 0])
        self.dt = 0.01
        self.duration = 30.0 # seconds
        self.steps = int(self.duration / self.dt)

    def test_energy_drift_30s(self):
        """
        Requirement Check: Energy drift must be below 1% over 30 seconds.
        """
        state = self.initial_state.copy()
        
        # Calculate initial total energy
        _, _, start_energy = physics.compute_energy(state)
        
        # Run simulation for 30 seconds
        for _ in range(self.steps):
            state = physics.rk4_step(state, self.dt)
            
        # Calculate final energy
        _, _, end_energy = physics.compute_energy(state)
        
        # Calculate percentage drift
        # Avoid division by zero if energy is exactly 0 (unlikely here)
        drift_percent = abs((end_energy - start_energy) / start_energy) * 100
        
        print(f"\n[30s Run] Start E: {start_energy:.4f}J, End E: {end_energy:.4f}J")
        print(f"Drift: {drift_percent:.4f}% (Limit: 1.0%)")
        
        self.assertLess(drift_percent, 1.0, 
                        f"Energy drift {drift_percent:.4f}% exceeded 1% limit over 30s.")

    def test_stable_equilibrium(self):
        """
        Sanity Check: If the pendulum hangs straight down (0,0), 
        it should not move and energy should remain constant.
        """
        # Both straight down, no velocity
        state = np.array([0.0, 0.0, 0.0, 0.0])
        
        # Step forward
        next_state = physics.rk4_step(state, self.dt)
        
        # Check that state hasn't changed (velocities still 0, angles still 0)
        np.testing.assert_array_almost_equal(state, next_state, decimal=6,
                                             err_msg="Pendulum moved from dead stop at equilibrium.")

if __name__ == '__main__':
    unittest.main()