# physics.py
import numpy as np

# Physical constants
G = 9.81
L1 = 1.0; L2 = 1.0
M1 = 1.0; M2 = 1.0

def get_derivatives(state, damping=0.0):
    """
    Calculates derivatives [theta1_dot, omega1_dot, theta2_dot, omega2_dot].
    Args:
        state: [theta1, omega1, theta2, omega2]
        damping: Viscous damping coefficient (acts against angular velocity)
    """
    theta1, omega1, theta2, omega2 = state
    
    delta_theta = theta1 - theta2
    sin_delta = np.sin(delta_theta)
    cos_delta = np.cos(delta_theta)
    
    den = 2 * M1 + M2 - M2 * np.cos(2 * theta1 - 2 * theta2)
    
    # Omega 1 Acceleration
    num1 = -G * (2 * M1 + M2) * np.sin(theta1)
    num2 = -M2 * G * np.sin(theta1 - 2 * theta2)
    num3 = -2 * sin_delta * M2 * (omega2**2 * L2 + omega1**2 * L1 * cos_delta)
    omega1_dot = (num1 + num2 + num3) / (L1 * den)
    
    # Omega 2 Acceleration
    num4 = 2 * sin_delta
    num5 = omega1**2 * L1 * (M1 + M2)
    num6 = G * (M1 + M2) * np.cos(theta1)
    num7 = omega2**2 * L2 * M2 * cos_delta
    omega2_dot = (num4 * (num5 + num6 + num7)) / (L2 * den)
    
    # Apply damping to accelerations (approximate viscous drag)
    omega1_dot -= damping * omega1
    omega2_dot -= damping * omega2
    
    return np.array([omega1, omega1_dot, omega2, omega2_dot])

def rk4_step(state, dt, damping=0.0):
    """Integrates state forward using RK4 with optional damping."""
    y = np.array(state)
    
    k1 = get_derivatives(y, damping)
    k2 = get_derivatives(y + 0.5 * dt * k1, damping)
    k3 = get_derivatives(y + 0.5 * dt * k2, damping)
    k4 = get_derivatives(y + dt * k3, damping)
    
    new_state = y + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    return new_state

def compute_energy(state):
    theta1, omega1, theta2, omega2 = state
    
    y1 = -L1 * np.cos(theta1)
    y2 = y1 - L2 * np.cos(theta2)
    V = M1 * G * y1 + M2 * G * y2
    
    term1 = 0.5 * M1 * (L1 * omega1)**2
    term2 = 0.5 * M2 * ((L1 * omega1)**2 + (L2 * omega2)**2 + 
                        2 * L1 * L2 * omega1 * omega2 * np.cos(theta1 - theta2))
    T = term1 + term2
    
    return T, V, T + V