# physics.py
# Pure-python double pendulum dynamics + RK4 integrator and energy helpers
# Only depends on numpy for convenience.

from __future__ import annotations
import numpy as np

# State vector y = [theta1, theta2, omega1, omega2]
# Params: dict with keys: m1, m2, L1, L2, g, damping
# Damping is linear viscous damping applied to angular velocities.

def deriv(y: np.ndarray, params: dict) -> np.ndarray:
    """
    Return time derivative dy/dt for the double pendulum.
    y = [theta1, theta2, omega1, omega2]
    """
    t1, t2, w1, w2 = y
    m1 = params.get("m1", 1.0)
    m2 = params.get("m2", 1.0)
    L1 = params.get("L1", 1.0)
    L2 = params.get("L2", 1.0)
    g  = params.get("g", 9.81)
    b  = params.get("damping", 0.0)  # viscous coefficient in s^-1

    delta = t1 - t2
    s, c = np.sin(delta), np.cos(delta)

    den1 = (m1 + m2) * L1 - m2 * L1 * c * c
    den2 = (L2 / L1) * den1

    # Equations from standard formulation
    a1 = (m2 * L1 * w1**2 * s * c +
          m2 * g * np.sin(t2) * c +
          m2 * L2 * w2**2 * s -
          (m1 + m2) * g * np.sin(t1)) / den1

    a2 = (-m2 * L2 * w2**2 * s * c +
          (m1 + m2) * (g * np.sin(t1) * c - L1 * w1**2 * s - g * np.sin(t2))) / den2

    # Add simple viscous damping torques proportional to angular velocity
    a1 -= b * w1
    a2 -= b * w2

    return np.array([w1, w2, a1, a2], dtype=float)


def rk4_step(y: np.ndarray, dt: float, params: dict) -> np.ndarray:
    """One RK4 step for state y over dt."""
    k1 = deriv(y, params)
    k2 = deriv(y + 0.5 * dt * k1, params)
    k3 = deriv(y + 0.5 * dt * k2, params)
    k4 = deriv(y + dt * k3, params)
    return y + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)


def energy(y: np.ndarray, params: dict) -> float:
    """Total mechanical energy (kinetic + potential). Zero potential at pivot height 0."""
    t1, t2, w1, w2 = y
    m1 = params.get("m1", 1.0)
    m2 = params.get("m2", 1.0)
    L1 = params.get("L1", 1.0)
    L2 = params.get("L2", 1.0)
    g  = params.get("g", 9.81)

    # Positions
    x1 = L1 * np.sin(t1)
    y1 = -L1 * np.cos(t1)
    x2 = x1 + L2 * np.sin(t2)
    y2 = y1 - L2 * np.cos(t2)

    # Velocities via Jacobian
    vx1 = L1 * w1 * np.cos(t1)
    vy1 = L1 * w1 * np.sin(t1)
    vx2 = vx1 + L2 * w2 * np.cos(t2)
    vy2 = vy1 + L2 * w2 * np.sin(t2)

    T = 0.5 * m1 * (vx1**2 + vy1**2) + 0.5 * m2 * (vx2**2 + vy2**2)
    V = m1 * g * (y1) + m2 * g * (y2)
    return float(T + V)


def simulate(y0: np.ndarray, dt: float, steps: int, params: dict) -> np.ndarray:
    """Run the integrator without rendering. Returns array of states shape (steps+1, 4)."""
    out = np.zeros((steps + 1, 4), dtype=float)
    out[0] = y0
    y = y0.copy()
    for i in range(1, steps + 1):
        y = rk4_step(y, dt, params)
        out[i] = y
    return out
