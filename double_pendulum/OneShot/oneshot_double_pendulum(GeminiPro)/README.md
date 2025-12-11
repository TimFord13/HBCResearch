### Double Pendulum Simulation (Python-only)

This project implements a real-time, interactive double pendulum simulation using pure Python with `numpy` and `matplotlib` for visualization. It uses the Runge-Kutta 4th Order (RK4) method for integration and provides real-time energy monitoring and user interaction (pause, reset, and drag).

-----

### 🚀 Getting Started

#### Prerequisites

You must have **Python 3** installed on your system. This project requires two standard scientific computing libraries:

1.  `numpy`
2.  `matplotlib`

#### Installation

You can install the required libraries using `pip`:

```bash
pip install numpy matplotlib
```

-----

### 💻 Files Structure

The project is organized into three Python files to separate physics from visualization and testing:

  * `main.py`: Contains the visualization logic (Matplotlib), the animation loop, and all keyboard/mouse interaction handlers.
  * `physics.py`: Contains the `DoublePendulum` class, the **RK4 integrator**, the **equations of motion**, and the energy calculation functions.
  * `benchmark.py`: Contains the `benchmark()` function for performance testing the integrator.

-----

### ▶️ How to Run

1.  **Save the Code**: Ensure you have saved the contents provided previously into the three files (`main.py`, `physics.py`, `benchmark.py`) in the same directory.

2.  **Run the Simulation**: Execute the `main.py` file from your terminal:

    ```bash
    python main.py
    ```

3.  **Run the Benchmark**: To test the integration performance and energy stability, run `benchmark.py`:

    ```bash
    python benchmark.py
    ```

-----

### 🎮 Controls

The simulation supports real-time interaction via keyboard commands and mouse input:

| Input | Action |
| :--- | :--- |
| **Space** | Toggle **pause/play** |
| **R** | **Reset** to the initial state (default angles are $\pi/3$ and $\pi/4$) |
| **D** | Toggle **velocity damping** (slows the pendulum down over time) |
| **Esc** | **Quit** the application |
| **Mouse Drag** | Click and drag **Bob 2** (the outer mass) to reposition it. The simulation will **auto-pause** during the drag operation. |

-----

### 📊 Visualization Features

The main window displays two subplots:

1.  **Simulation Area**: Shows the pendulum arms and bobs.
2.  **Energy Graph**: Plots the **Total Mechanical Energy (Kinetic + Potential)** over time, allowing for real-time monitoring of integration stability.

Additionally, the simulation provides live status updates in the top-left corner:

  * **FPS**: Frame rate of the visualization.
  * **Energy Drift**: The percentage difference between the current total energy and the initial total energy ($\% \Delta E$).
  * **Damping Status**: Shows whether the damping mechanism is active.