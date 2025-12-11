# Interactive Double Pendulum Simulation

A real-time double pendulum simulation in pure Python with interactive controls and energy visualization.

## Requirements

- Python 3.7+
- numpy
- matplotlib

Install dependencies:
```bash
pip install numpy matplotlib
```

## Quick Start

Run the simulation:
```bash
python main.py
```

Run performance benchmarks:
```bash
python benchmark.py
```

Run automated tests:
```bash
python test_simulation.py
```

Generate analysis examples:
```bash
python examples.py
```

## Features

### Physics Simulation
- **RK4 Integration**: 4th-order Runge-Kutta integrator for accurate motion
- **Energy Conservation**: < 1% energy drift over 30 seconds (no damping)
- **Optional Damping**: Toggle velocity damping with 'D' key
- **Chaotic Dynamics**: Demonstrates sensitive dependence on initial conditions

### Interactive Controls

| Key/Action | Function |
|------------|----------|
| **Space** | Toggle pause/play |
| **R** | Reset to initial state |
| **D** | Toggle velocity damping on/off |
| **Esc** | Quit simulation |
| **Mouse Drag** | Click and drag the second bob to reposition it (auto-pauses) |

### Visualization
- Real-time pendulum motion with trace trail
- Live energy vs. time graph
- FPS counter and energy drift percentage
- Status display with current simulation state

## File Structure

```
.
├── main.py              # Main simulation with visualization and controls
├── physics.py           # Physics engine (equations, RK4 integrator, energy)
├── benchmark.py         # Performance testing suite
├── test_simulation.py   # Automated test suite
├── examples.py          # Example analyses and demonstrations
└── README.md            # This file
```

## Physics Implementation

The simulation uses the standard double pendulum equations of motion:

```
Δ = 2m₁ + m₂ - m₂cos(2(θ₁ - θ₂))

θ̈₁ = [complex equation for angular acceleration of first pendulum]
θ̈₂ = [complex equation for angular acceleration of second pendulum]
```

State vector: `[θ₁, ω₁, θ₂, ω₂]` where θ is angle and ω is angular velocity.

## Benchmark Results

Typical performance on modern hardware:
- **Step time**: ~15-30 µs per integration step
- **Energy drift**: < 0.01% over 20 seconds
- **Real-time factor**: 100-200x (simulation runs faster than real-time)

Run `python benchmark.py` for detailed performance metrics on your system.

## Customization

Edit `main.py` to change initial conditions:

```python
# In DoublePendulumSimulation.__init__():
self.initial_state = np.array([np.pi/2, 0.0, np.pi/2, 0.0])
```

Edit `physics.py` to change physical parameters:

```python
# In DoublePendulumSimulation.__init__():
self.pendulum = DoublePendulum(
    m1=1.0,      # Mass of first bob
    m2=1.0,      # Mass of second bob
    L1=1.0,      # Length of first rod
    L2=1.0,      # Length of second rod
    g=9.81,      # Gravitational acceleration
    damping=0.0  # Velocity damping coefficient
)
```

## Tips

- **Chaos Exploration**: Reset (R) multiple times to see how tiny differences create vastly different trajectories
- **Energy Conservation**: Watch the energy graph - with damping off, it should remain nearly constant
- **Interactive Mode**: Drag the second bob to create custom starting configurations
- **Performance**: The simulation uses substeps internally for stability at 60 FPS

## Advanced Usage

### Running Tests
```bash
python test_simulation.py
```
Runs automated tests for:
- Energy conservation (< 1% drift)
- Damping functionality
- Inverse kinematics accuracy
- Numerical stability
- RK4 integrator accuracy

### Generating Analysis Plots
```bash
python examples.py
```
Creates visualizations:
- `chaos_demonstration.png` - Sensitive dependence on initial conditions
- `energy_analysis.png` - Energy components and drift over time
- `phase_space.png` - Phase space portraits
- `damping_comparison.png` - Effect of damping on energy

### Programmatic Usage
```python
from physics import DoublePendulum
import numpy as np

# Create pendulum
pendulum = DoublePendulum(m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81)

# Initial state: [theta1, omega1, theta2, omega2]
state = np.array([np.pi/4, 0.0, np.pi/4, 0.0])

# Integrate
dt = 0.001
for _ in range(1000):
    state = pendulum.rk4_step(state, dt)

# Get positions
(x1, y1), (x2, y2) = pendulum.cartesian_positions(state)

# Calculate energy
energy = pendulum.total_energy(state)
```

## License

Free to use and modify for educational and research purposes.
