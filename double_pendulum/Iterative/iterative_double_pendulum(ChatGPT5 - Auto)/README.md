# Double Pendulum Simulator

An interactive, physics-accurate double pendulum simulation featuring:
- A full nonlinear physics engine using RK4 integration  
- Real-time visualization with Matplotlib  
- Mouse dragging of the second bob  
- Live energy tracking with drift and FPS monitoring  
- Optional damping toggle  
- A benchmarking script for integrator performance

---

## Repository Structure
```
project/
│
├── physics.py # Physics engine, RK4, energy calculations
├── main.py # Visualization, controls, interaction
└── benchmark.py # Headless integrator benchmarking

```
---

## Features

### Physics Engine (`physics.py`)
- Implements standard double-pendulum equations of motion  
- 4th-order Runge–Kutta integration  
- Calculates kinetic, potential, and total energy  
- Configurable masses, lengths, and gravity  

### Real-Time Visualization (`main.py`)
- 60 FPS target update rate  
- Left subplot: animated pendulum  
- Right subplot: total energy vs. simulation time  
- Overlays:
  - FPS (EMA-smoothed)
  - Percent energy drift relative to baseline

### User Interaction
| Control | Function |
|--------|----------|
| **Space** | Pause / resume simulation |
| **R** | Reset to initial conditions |
| **D** | Toggle damping on/off |
| **Esc** | Exit simulation |
| **Click + drag** | Drag the second bob directly; simulation pauses while dragging |

Dragging uses approximate inverse kinematics to maintain rod length and resets velocities to avoid energy injection. The energy baseline also resets after each drag.

### Energy Tracking
- Undamped mode maintains extremely low numerical drift  
- Damping mode recalculates the baseline to ensure meaningful percentages  
- Energy plot autoscaling is rate-limited to preserve frame rate

---

## Benchmarking (`benchmark.py`)

Run via:

python benchmark.py


It reports:
- Mean RK4 step time (microseconds)
- Percent total energy drift over the run

Example output:

Steps: 20000 dt: 0.001
Mean step time: 3.14 µs
Energy drift: -0.0021 %


---

## Installation

### Requirements
- Python 3.9+
- `matplotlib`
- (Optional) `numpy`

Install dependencies:

pip install matplotlib numpy

yaml
Copy code

---

## Running the Simulation

python main.py


---

## Notes on Stability
- Default timestep: `dt = 1/240` with 4 RK4 substeps per frame  
- Stable, low-drift behavior for undamped motion  
- With damping enabled, total mechanical energy exponentially approaches the minimum potential energy configuration  

---

## License
Free for educational and personal use.