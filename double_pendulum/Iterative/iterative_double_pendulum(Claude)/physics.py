# physics.py
import numpy as np

class DoublePendulum:
    def __init__(self, m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81):
        """
        Initialize double pendulum parameters.
        
        Parameters:
        m1, m2: masses of the two bobs (kg)
        L1, L2: lengths of the two rods (m)
        g: gravitational acceleration (m/s^2)
        """
        self.m1 = m1
        self.m2 = m2
        self.L1 = L1
        self.L2 = L2
        self.g = g
    
    def derivatives(self, state):
        """
        Calculate derivatives for the double pendulum system.
        
        Parameters:
        state: [theta1, omega1, theta2, omega2]
        
        Returns:
        [dtheta1/dt, domega1/dt, dtheta2/dt, domega2/dt]
        """
        theta1, omega1, theta2, omega2 = state
        
        delta = theta2 - theta1
        
        # Denominators for angular accelerations
        den1 = (self.m1 + self.m2) * self.L1 - self.m2 * self.L1 * np.cos(delta)**2
        den2 = (self.L2 / self.L1) * den1
        
        # Angular accelerations
        alpha1 = (self.m2 * self.L1 * omega1**2 * np.sin(delta) * np.cos(delta) +
                  self.m2 * self.g * np.sin(theta2) * np.cos(delta) +
                  self.m2 * self.L2 * omega2**2 * np.sin(delta) -
                  (self.m1 + self.m2) * self.g * np.sin(theta1)) / den1
        
        alpha2 = (-self.m2 * self.L2 * omega2**2 * np.sin(delta) * np.cos(delta) +
                  (self.m1 + self.m2) * self.g * np.sin(theta1) * np.cos(delta) -
                  (self.m1 + self.m2) * self.L1 * omega1**2 * np.sin(delta) -
                  (self.m1 + self.m2) * self.g * np.sin(theta2)) / den2
        
        return np.array([omega1, alpha1, omega2, alpha2])
    
    def rk4_step(self, state, dt):
        """
        Perform one Runge-Kutta 4th order integration step.
        
        Parameters:
        state: current state [theta1, omega1, theta2, omega2]
        dt: time step
        
        Returns:
        next state [theta1, omega1, theta2, omega2]
        """
        k1 = self.derivatives(state)
        k2 = self.derivatives(state + 0.5 * dt * k1)
        k3 = self.derivatives(state + 0.5 * dt * k2)
        k4 = self.derivatives(state + dt * k3)
        
        next_state = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        
        return next_state
    
    def compute_energy(self, state):
        """
        Compute kinetic and potential energy of the system.
        
        Parameters:
        state: [theta1, omega1, theta2, omega2]
        
        Returns:
        tuple: (kinetic_energy, potential_energy)
        """
        theta1, omega1, theta2, omega2 = state
        
        # Positions of the bobs
        x1 = self.L1 * np.sin(theta1)
        y1 = -self.L1 * np.cos(theta1)
        
        x2 = x1 + self.L2 * np.sin(theta2)
        y2 = y1 - self.L2 * np.cos(theta2)
        
        # Velocities of the bobs
        vx1 = self.L1 * omega1 * np.cos(theta1)
        vy1 = self.L1 * omega1 * np.sin(theta1)
        
        vx2 = vx1 + self.L2 * omega2 * np.cos(theta2)
        vy2 = vy1 + self.L2 * omega2 * np.sin(theta2)
        
        # Kinetic energy
        KE = 0.5 * self.m1 * (vx1**2 + vy1**2) + 0.5 * self.m2 * (vx2**2 + vy2**2)
        
        # Potential energy (reference at y=0)
        PE = self.m1 * self.g * y1 + self.m2 * self.g * y2
        
        return KE, PE


# Convenience functions for direct use
def create_pendulum(m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81):
    """Create a DoublePendulum instance with given parameters."""
    return DoublePendulum(m1, m2, L1, L2, g)


def rk4_step(pendulum, state, dt):
    """Convenience wrapper for rk4_step."""
    return pendulum.rk4_step(state, dt)


def compute_energy(pendulum, state):
    """Convenience wrapper for compute_energy."""
    return pendulum.compute_energy(state)