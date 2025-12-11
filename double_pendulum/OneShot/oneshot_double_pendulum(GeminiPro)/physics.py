# physics.py

import numpy as np

class DoublePendulum:
    """
    Manages the state and physics of a double pendulum.
    Uses RK4 integration to solve the equations of motion.
    """
    def __init__(self, L1=1.0, L2=1.0, m1=1.0, m2=1.0, g=9.81, damping=0.0):
        self.L1, self.L2 = L1, L2
        self.m1, self.m2 = m1, m2
        self.g = g
        self.damping = damping

        # State vector: y = [theta1, omega1, theta2, omega2]
        # omega (w) is angular velocity (theta_dot)
        self.y = np.array([np.pi / 2, 0.0, np.pi, 0.0])
        self.initial_state = self.y.copy()

    def set_state(self, th1, w1, th2, w2):
        """Manually set the pendulum's state."""
        self.y = np.array([th1, w1, th2, w2])

    def reset(self):
        """Reset the pendulum to its initial state."""
        self.y = self.initial_state.copy()

    def equations_of_motion(self, y):
        """
        Calculates the derivatives of the state vector [th1_dot, w1_dot, th2_dot, w2_dot].
        This implements the equations provided in the research prompt.
        """
        th1, w1, th2, w2 = y
        m1, m2 = self.m1, self.m2
        L1, L2 = self.L1, self.L2
        g = self.g

        # Denominator term (Delta in the prompt)
        delta = 2 * m1 + m2 - m2 * np.cos(2 * (th1 - th2))

        # Equation for theta1_ddot (w1_dot)
        th1_ddot_num = -g * (2 * m1 + m2) * np.sin(th1) - m2 * g * np.sin(th1 - 2 * th2) - 2 * np.sin(th1 - th2) * m2 * (w2**2 * L2 + w1**2 * L1 * np.cos(th1 - th2))
        w1_dot = th1_ddot_num / (L1 * delta)

        # Equation for theta2_ddot (w2_dot)
        th2_ddot_num = 2 * np.sin(th1 - th2) * (w1**2 * L1 * (m1 + m2) + g * (m1 + m2) * np.cos(th1) + w2**2 * L2 * m2 * np.cos(th1 - th2))
        w2_dot = th2_ddot_num / (L2 * delta)

        return np.array([w1, w1_dot, w2, w2_dot])

    def step(self, dt):
        """Perform one step of RK4 integration."""
        y = self.y
        
        # RK4 implementation
        k1 = self.equations_of_motion(y)
        k2 = self.equations_of_motion(y + 0.5 * dt * k1)
        k3 = self.equations_of_motion(y + 0.5 * dt * k2)
        k4 = self.equations_of_motion(y + dt * k3)

        self.y += (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        
        # Apply optional velocity damping
        if self.damping > 0:
            self.y[1] *= (1 - self.damping * dt)
            self.y[3] *= (1 - self.damping * dt)

    def energy(self):
        """Calculate the total energy (Kinetic + Potential) of the system."""
        th1, w1, th2, w2 = self.y
        m1, m2, L1, L2, g = self.m1, self.m2, self.L1, self.L2, self.g

        # Potential Energy (U = mgy, pivot at y=0)
        y1 = -L1 * np.cos(th1)
        y2 = y1 - L2 * np.cos(th2)
        U = m1 * g * y1 + m2 * g * y2

        # Kinetic Energy (T = 0.5*m*v^2)
        v1_sq = (L1 * w1)**2
        vx2 = L1 * w1 * np.cos(th1) + L2 * w2 * np.cos(th2)
        vy2 = L1 * w1 * np.sin(th1) + L2 * w2 * np.sin(th2)
        v2_sq = vx2**2 + vy2**2
        T = 0.5 * m1 * v1_sq + 0.5 * m2 * v2_sq

        return T + U

    def positions(self):
        """Calculate the Cartesian coordinates of the bobs."""
        th1, _, th2, _ = self.y
        x1 = self.L1 * np.sin(th1)
        y1 = -self.L1 * np.cos(th1)
        x2 = x1 + self.L2 * np.sin(th2)
        y2 = y1 - self.L2 * np.cos(th2)
        return x1, y1, x2, y2