# Interactive Double Pendulum (Python-only)

Real-time double pendulum written in pure Python with `matplotlib` animation and `numpy`. No HTML, no servers. Run it, watch chaos, press keys, drag the bob.

## Features
- RK4 integration with optional viscous damping
- Live energy plot and drift percentage
- Pause/play, reset, damping toggle
- Click-and-drag the end bob; simulation auto-pauses while dragging
- Benchmark function to measure integrator speed and energy drift

## Quickstart
```bash
pip install numpy matplotlib
python main.py
```

## Controls
| Key        | Action                         |
|------------|--------------------------------|
| Space      | Toggle pause/play              |
| R          | Reset initial state            |
| D          | Toggle damping (0 or 0.03 s^-1)|
| Esc        | Quit                           |
| Mouse drag | Drag bob 2 (auto-pause on drag)|

## Benchmark
```bash
python benchmark.py
```
Outputs mean step time (microseconds) and energy drift percentage for a headless run.

## Acceptance Notes
- Default dt = 1/240 s with 4 substeps per animation frame targets ~60 FPS on typical machines.
- Energy drift with RK4 at small dt should be well under 1% over 30 s with damping = 0. Exact drift depends on machine precision and initial conditions.
- Modify parameters in `main.py` or `physics.py` as needed:
  - `params = dict(m1, m2, L1, L2, g, damping)`
  - `y0 = [theta1, theta2, omega1, omega2]` in radians
  - `dt` and `substeps_per_frame` for stability/perf trade-offs.
```

# Tips
- If the cursor goes outside the reachable workspace while dragging, the IK gently clamps to the nearest feasible point to avoid numerical sadness.
- For stricter energy conservation, you can lower `dt` further or remove damping.
```