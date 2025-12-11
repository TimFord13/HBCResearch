from physics import rk4_step, compute_energy

state = [0.5, 0.0, 1.0, 0.0]
dt = 0.001
steps = 5000

T0, V0 = compute_energy(state)
E0 = T0 + V0

for _ in range(steps):
    state = rk4_step(state, dt)

T1, V1 = compute_energy(state)
E1 = T1 + V1
print("E0:", E0, "E1:", E1, "ΔE:", E1 - E0)
