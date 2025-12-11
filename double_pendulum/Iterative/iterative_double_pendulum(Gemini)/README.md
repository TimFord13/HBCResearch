Here is the comprehensive `README.md` for your repository. It documents the project setup, controls, physics implementation, and testing procedures.

### **Next Step:**

I have also included a **master test script** (`test_all.py`) at the bottom. You can simply run `python test_all.py` to execute every verification test we've written so far in one go.

-----

# Interactive Double Pendulum

[Image of double pendulum physics diagram]

A real-time, interactive physics simulation of a double pendulum using Python. It features a custom **Runge-Kutta 4 (RK4)** integrator, live energy tracking, chaotic motion visualization, and interactive mouse controls (Inverse Kinematics).

## 🚀 Features

  * **Physics Engine:** Custom implementation of double pendulum equations of motion using RK4 integration for high stability.
  * **Interactive Controls:** Click and drag the pendulum bob to set new initial conditions using Inverse Kinematics.
  * **Live Analysis:** Real-time plotting of total energy to monitor drift and conservation.
  * **Damping:** Toggle viscous damping to observe energy dissipation.
  * **Benchmarking:** Built-in tool to measure integration performance ($\mu s$/step).

## 📦 Requirements

  * Python 3.7+
  * `numpy`
  * `matplotlib`

## 🛠️ Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/yourusername/double-pendulum.git
    cd double-pendulum
    ```

2.  Install dependencies:

    ```bash
    pip install numpy matplotlib
    ```

## 🎮 Usage

### Running the Simulation

Execute the main script to start the visual simulation:

```bash
python main.py
```

### Controls

| Input | Action |
| :--- | :--- |
| **Space** | Pause / Resume simulation |
| **R** | Reset to initial conditions |
| **D** | Toggle Damping (Friction) On/Off |
| **Esc** | Exit the application |
| **Mouse Drag** | Click and drag the bottom bob to interact |

### Benchmarking

To test the speed and accuracy of the physics engine without the GUI overhead:

```bash
python benchmark.py
```

  * **Steps:** 20,000 integration steps.
  * **Output:** Mean calculation time per step and total energy drift %.

## 📂 File Structure

  * `main.py`: The entry point. Handles the Matplotlib GUI, animation loop, and user input.
  * `physics.py`: The core physics engine. Contains the Lagrangian derivatives, RK4 integrator, and energy calculations.
  * `benchmark.py`: A headless performance test for the integrator.
  * `test_*.py`: Unit tests for verification (see below).

## 🧪 Testing

This project includes a suite of tests to verify the physics, energy conservation, and math logic.

You can run the master test script to check everything at once:

```bash
python test_all.py
```

Or run individual tests:

  * `test_physics.py`: Basic derivative and shape checks.
  * `test_physics_extended.py`: Long-duration stability checks (30s run).
  * `test_ik_logic.py`: Verifies the Inverse Kinematics math for mouse interaction.

-----

