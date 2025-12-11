import numpy as np

class DoublePendulum:
    def __init__(self, m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81, damping=0.0):
        """
        Initialize double pendulum parameters.
        
        Args:
            m1, m2: masses of bobs
            L1, L2: lengths of rods
            g: gravitational acceleration
            damping: velocity damping coefficient
        """
        self.m1 = m1
        self.m2 = m2
        self.L1 = L1
        self.L2 = L2
        self.g = g
        self.damping = damping
        
    def derivatives(self, state):
        """
        Compute derivatives for the double pendulum system.
        
        Args:
            state: [theta1, omega1, theta2, omega2]
        
        Returns:
            [dtheta1, domega1, dtheta2, domega2]
        """
        theta1, omega1, theta2, omega2 = state
        
        delta = theta1 - theta2
        den1 = (self.m1 + self.m2) * self.L1 - self.m2 * self.L1 * np.cos(delta) * np.cos(delta)
        den2 = (self.L2 / self.L1) * den1
        
        # Apply damping to velocities
        omega1_damped = omega1 * (1 - self.damping)
        omega2_damped = omega2 * (1 - self.damping)
        
        # Acceleration of theta1
        domega1 = (self.m2 * self.L1 * omega1_damped * omega1_damped * np.sin(delta) * np.cos(delta) +
                   self.m2 * self.g * np.sin(theta2) * np.cos(delta) +
                   self.m2 * self.L2 * omega2_damped * omega2_damped * np.sin(delta) -
                   (self.m1 + self.m2) * self.g * np.sin(theta1)) / den1
        
        # Acceleration of theta2
        domega2 = (-self.m2 * self.L2 * omega2_damped * omega2_damped * np.sin(delta) * np.cos(delta) +
                   (self.m1 + self.m2) * self.g * np.sin(theta1) * np.cos(delta) -
                   (self.m1 + self.m2) * self.L1 * omega1_damped * omega1_damped * np.sin(delta) -
                   (self.m1 + self.m2) * self.g * np.sin(theta2)) / den2
        
        return np.array([omega1, domega1, omega2, domega2])
    
    def rk4_step(self, state, dt):
        """
        Perform one Runge-Kutta 4th order integration step.
        
        Args:
            state: current state [theta1, omega1, theta2, omega2]
            dt: time step
        
        Returns:
            new state after dt
        """
        k1 = self.derivatives(state)
        k2 = self.derivatives(state + 0.5 * dt * k1)
        k3 = self.derivatives(state + 0.5 * dt * k2)
        k4 = self.derivatives(state + dt * k3)
        
        return state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    
    def kinetic_energy(self, state):
        """Calculate kinetic energy of the system."""
        theta1, omega1, theta2, omega2 = state
        
        v1_sq = (self.L1 * omega1)**2
        v2_sq = (self.L1 * omega1)**2 + (self.L2 * omega2)**2 + \
                2 * self.L1 * self.L2 * omega1 * omega2 * np.cos(theta1 - theta2)
        
        return 0.5 * self.m1 * v1_sq + 0.5 * self.m2 * v2_sq
    
    def potential_energy(self, state):
        """Calculate potential energy of the system."""
        theta1, _, theta2, _ = state
        
        y1 = -self.L1 * np.cos(theta1)
        y2 = y1 - self.L2 * np.cos(theta2)
        
        return self.m1 * self.g * y1 + self.m2 * self.g * y2
    
    def total_energy(self, state):
        """Calculate total energy of the system."""
        return self.kinetic_energy(state) + self.potential_energy(state)
    
    def cartesian_positions(self, state):
        """
        Convert angles to Cartesian positions of the bobs.
        
        Returns:
            (x1, y1), (x2, y2)
        """
        theta1, _, theta2, _ = state
        
        x1 = self.L1 * np.sin(theta1)
        y1 = -self.L1 * np.cos(theta1)
        
        x2 = x1 + self.L2 * np.sin(theta2)
        y2 = y1 - self.L2 * np.cos(theta2)
        
        return (x1, y1), (x2, y2)
    
    def set_position_from_cartesian(self, x2, y2, state):
        """
        Inverse kinematics: set angles from desired (x2, y2) position.
        Keeps first bob fixed, adjusts both angles to reach target.
        
        Args:
            x2, y2: desired position of second bob
            state: current state
        
        Returns:
            new state with updated angles (velocities set to 0)
        """
        # Distance from origin
        r = np.sqrt(x2**2 + y2**2)
        
        # Clamp to valid range
        max_reach = self.L1 + self.L2
        min_reach = abs(self.L1 - self.L2)
        r = np.clip(r, min_reach + 0.01, max_reach - 0.01)
        
        # Rescale target if needed
        if np.sqrt(x2**2 + y2**2) > 0:
            scale = r / np.sqrt(x2**2 + y2**2)
            x2 *= scale
            y2 *= scale
        
        # Use law of cosines to find angles
        cos_angle = (self.L1**2 + self.L2**2 - r**2) / (2 * self.L1 * self.L2)
        cos_angle = np.clip(cos_angle, -1, 1)
        
        # Angle between the two rods
        elbow_angle = np.arccos(cos_angle)
        
        # Angle of line from origin to target
        target_angle = np.arctan2(x2, -y2)
        
        # Angle for first rod
        beta = np.arcsin(self.L2 * np.sin(elbow_angle) / r)
        theta1 = target_angle - beta
        
        # Angle for second rod
        theta2 = theta1 + elbow_angle
        
        return np.array([theta1, 0, theta2, 0])