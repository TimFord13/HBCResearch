# physics.py
"""
Double pendulum physics engine with RK4 integration.

State format: [theta1, omega1, theta2, omega2]
Angles in radians, angular velocities in radians/second.
"""

import math

# Default physical parameters (can be overridden via set_params)
m1 = 1.0  # Mass of first bob
m2 = 1.0  # Mass of second bob
L1 = 1.0  # Length of first rod
L2 = 1.0  # Length of second rod
g = 9.81  # Gravitational acceleration


def set_params(m1_val, m2_val, L1_val, L2_val, g_val=9.81):
    """
    Set global physical parameters for the double pendulum.

    This affects all subsequent calls to rk4_step and compute_energy.
    """
    global m1, m2, L1, L2, g
    m1 = float(m1_val)
    m2 = float(m2_val)
    L1 = float(L1_val)
    L2 = float(L2_val)
    g = float(g_val)


def get_params():
    """
    Return current physical parameters as a dict.
    """
    return {
        "m1": m1,
        "m2": m2,
        "L1": L1,
        "L2": L2,
        "g": g,
    }


def _derivatives(state):
    """
    Compute time derivatives for the double pendulum state.

    state = [theta1, omega1, theta2, omega2]
    returns [dtheta1/dt, domega1/dt, dtheta2/dt, domega2/dt]
    """
    theta1, omega1, theta2, omega2 = state

    delta = theta2 - theta1
    sin_delta = math.sin(delta)
    cos_delta = math.cos(delta)

    # Denominators for the coupled equations
    den1 = (m1 + m2) * L1 - m2 * L1 * cos_delta * cos_delta
    den2 = (L2 / L1) * den1

    # Angular accelerations (standard double pendulum equations)
    # These are the general-mass, general-length forms.
    num1 = (
        m2 * L1 * omega1 * omega1 * sin_delta * cos_delta
        + m2 * g * math.sin(theta2) * cos_delta
        + m2 * L2 * omega2 * omega2 * sin_delta
        - (m1 + m2) * g * math.sin(theta1)
    )
    alpha1 = num1 / den1

    num2 = (
        -m2 * L2 * omega2 * omega2 * sin_delta * cos_delta
        + (m1 + m2)
        * (
            g * math.sin(theta1) * cos_delta
            - L1 * omega1 * omega1 * sin_delta
            - g * math.sin(theta2)
        )
    )
    alpha2 = num2 / den2

    return [omega1, alpha1, omega2, alpha2]


def _add_scaled(state, deriv, scale):
    """
    Helper: state + scale * deriv for RK4.
    """
    return [s + scale * d for s, d in zip(state, deriv)]


def rk4_step(state, dt):
    """
    Perform a single RK4 step for the double pendulum.

    Parameters:
        state: [theta1, omega1, theta2, omega2]
        dt: timestep (seconds)

    Returns:
        new_state: [theta1, omega1, theta2, omega2] at t + dt
    """
    k1 = _derivatives(state)
    k2 = _derivatives(_add_scaled(state, k1, dt * 0.5))
    k3 = _derivatives(_add_scaled(state, k2, dt * 0.5))
    k4 = _derivatives(_add_scaled(state, k3, dt))

    new_state = [
        s + (dt / 6.0) * (k1_i + 2.0 * k2_i + 2.0 * k3_i + k4_i)
        for s, k1_i, k2_i, k3_i, k4_i in zip(state, k1, k2, k3, k4)
    ]

    return new_state


def compute_energy(state):
    """
    Compute kinetic and potential energy of the double pendulum.

    Parameters:
        state: [theta1, omega1, theta2, omega2]

    Returns:
        (T, V):
            T = total kinetic energy
            V = total potential energy (relative, up to a constant offset)
    """
    theta1, omega1, theta2, omega2 = state

    # Positions of the masses
    x1 = L1 * math.sin(theta1)
    y1 = -L1 * math.cos(theta1)

    x2 = x1 + L2 * math.sin(theta2)
    y2 = y1 - L2 * math.cos(theta2)

    # Velocities (via time derivatives)
    v1x = L1 * omega1 * math.cos(theta1)
    v1y = L1 * omega1 * math.sin(theta1)

    v2x = v1x + L2 * omega2 * math.cos(theta2)
    v2y = v1y + L2 * omega2 * math.sin(theta2)

    # Kinetic energy
    T1 = 0.5 * m1 * (v1x * v1x + v1y * v1y)
    T2 = 0.5 * m2 * (v2x * v2x + v2y * v2y)
    T = T1 + T2

    # Potential energy (zero level arbitrary)
    V1 = m1 * g * y1
    V2 = m2 * g * y2
    V = V1 + V2

    return T, V
