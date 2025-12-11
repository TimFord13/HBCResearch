# Double Pendulum Simulator

A real-time interactive physics simulation of a double pendulum system with energy tracking, mouse interaction, and optional damping.

![Double Pendulum](https://via.placeholder.com/800x400.png?text=Double+Pendulum+Simulation)

## Features

- **Real-time Physics Simulation**: Accurate double pendulum dynamics using RK4 integration
- **Interactive Controls**: Keyboard shortcuts for pause, reset, and damping
- **Mouse Interaction**: Click and drag the second bob to set custom initial conditions
- **Energy Tracking**: Live visualization of total energy over time with drift calculation
- **Performance Monitoring**: Real-time FPS display
- **Damping Mode**: Optional velocity damping to observe energy dissipation
- **Benchmarking Tool**: Test integration performance without rendering overhead

## Requirements

- Python 3.7+
- NumPy
- Matplotlib

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd double-pendulum
```

2. Install dependencies:
```bash
pip install numpy matplotlib
```

## Usage

### Running the Simulation
```bash
python main.py
```

### Keyboard Controls

| Key | Action |
|-----|--------|
| `Space` | Pause/Resume simulation |
| `R` | Reset to initial conditions |
| `D` | Toggle velocity damping on/off |
| `Esc` | Exit application |

### Mouse Controls

- **Click and Drag**: Click on the blue bob (second pendulum) and drag to set a new position
- The simulation automatically pauses while dragging
- Release to resume with zero initial velocity

## File Structure
```
double-pendulum/
├── physics.py      # Physics engine and RK4 integrator
├── main.py         # Main visualization and animation
├── benchmark.py    # Performance benchmarking tool
└── README.md       # This file
```

## Physics Implementation

### Equations of Motion

The double pendulum system is governed by the following coupled differential equations:

**Angular accelerations:**
- θ₁̈ = [m₂L₁ω₁² sin(Δ)cos(Δ) + m₂g sin(θ₂)cos(Δ) + m₂L₂ω₂² sin(Δ) - (m₁+m₂)g sin(θ₁)] / den₁
- θ₂̈ = [-m₂L₂ω₂² sin(Δ)cos(Δ) + (m₁+m₂)g sin(θ₁)cos(Δ) - (m₁+m₂)L₁ω₁² sin(Δ) - (m₁+m₂)g sin(θ₂)] / den₂

Where:
- Δ = θ₂ - θ₁
- den₁ = (m₁ + m₂)L₁ - m₂L₁cos²(Δ)
- den₂ = (L₂/L₁) × den₁

### Integration Method

The simulation uses the 4th-order Runge-Kutta (RK4) method for numerical integration, providing excellent accuracy with minimal energy drift (<1% over 30 seconds with dt=0.01).

### Parameters

Default system parameters:
- m₁ = 1.0 kg (mass of first bob)
- m₂ = 1.0 kg (mass of second bob)
- L₁ = 1.0 m (length of first rod)
- L₂ = 1.0 m (length of second rod)
- g = 9.81 m/s² (gravitational acceleration)
- dt = 0.01 s (integration time step)

## Benchmarking

Run the benchmark to test integration performance:
```bash
python benchmark.py
```

Expected output:
```
Running benchmark...
--------------------------------------------------
Steps: 20000
dt: 0.001 s
Mean step time: ~XX.XX µs
Energy drift: <0.1%
--------------------------------------------------
```

## Energy Conservation

The simulation tracks total energy (kinetic + potential) and displays:
- **Drift** (damping off): Numerical error in energy conservation, should remain <1%
- **Energy Change** (damping on): Expected energy decrease due to damping

## Customization

### Changing Initial Conditions

Edit `main.py`:
```python
# Initial angles in degrees
theta1_init = np.radians(120)  # First pendulum angle
theta2_init = np.radians(-10)  # Second pendulum angle
initial_state = [theta1_init, 0.0, theta2_init, 0.0]
```

### Adjusting System Parameters

Edit the pendulum creation in `main.py`:
```python
pendulum = DoublePendulum(
    m1=1.0,   # First bob mass
    m2=1.0,   # Second bob mass
    L1=1.0,   # First rod length
    L2=1.0,   # Second rod length
    g=9.81    # Gravity
)
```

### Modifying Damping Coefficient

Edit `main.py` in the `DoublePendulumAnimation.__init__()` method:
```python
self.damping_coefficient = 0.999  # Reduce for stronger damping (e.g., 0.99)
```

### Changing Time Step

Edit `main.py`:
```python
animation = DoublePendulumAnimation(pendulum, initial_state, dt=0.01)
```

Smaller dt = better accuracy but slower performance
Larger dt = faster but may have energy drift

## Technical Details

### Performance

- Target: 60 FPS
- Typical step time: 20-50 µs (depends on hardware)
- Energy drift: <1% over 30 seconds (no damping)

### Visualization

- **Left Panel**: Real-time pendulum animation
  - Red bob: First pendulum
  - Blue bob: Second pendulum
  - Black line: Connecting rods
  
- **Right Panel**: Energy vs. time graph
  - Blue line shows total energy evolution
  - Auto-scales to fit data

### Mouse Interaction Details

The mouse dragging uses inverse kinematics to compute the second pendulum angle (θ₂) based on cursor position. The first pendulum remains fixed during dragging. Energy tracking resets upon release to provide accurate drift measurements from the new state.

## Known Limitations

- Mouse dragging only affects the second bob
- Very high energy initial conditions may cause numerical instability
- Energy drift increases with larger time steps (dt)

## Troubleshooting

**Animation is slow/choppy:**
- Increase `dt` in main.py (e.g., dt=0.02)
- Close other applications
- Reduce window size

**Energy drift is too high:**
- Decrease `dt` for better accuracy (e.g., dt=0.005)
- Check that initial conditions aren't too extreme

**Window doesn't respond:**
- Make sure the plot window has focus
- Try clicking on the window before using keyboard shortcuts

## License

MIT License - feel free to use and modify for educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## References

- [Double Pendulum Mathematics](https://www.myphysicslab.com/pendulum/double-pendulum-en.html)
- [Runge-Kutta Methods](https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_methods)
- [Chaos Theory and the Double Pendulum](https://www.youtube.com/watch?v=d0Z8wLLPNE0)

## Acknowledgments

Built as a demonstration of:
- Classical mechanics simulation
- Numerical integration techniques
- Real-time interactive visualization
- Chaotic systems behavior

---

**Enjoy exploring the beautiful chaos of the double pendulum!** 🎭