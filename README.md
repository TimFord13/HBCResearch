# AI Code Generation Study

This repository contains the code, outputs, and evaluation framework for our **Honors by Contract research project**:  
**"Human-AI Collaboration in Software Development: A Comparative Analysis"**

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

--- 

## Overview
This repository serves as a standardized benchmarking suite for evaluating Large Language Models (LLMs) in software development contexts. It contains the source code, task specifications, and experimental framework used to assess model performance across varying levels of human intervention.

The repository is designed to facilitate the comparative analysis of "Single-Shot" (automated) vs. "Iterative" (collaborative) development workflows. Researchers can use this dataset to:
1.  Analyze the code quality differences between unguided and guided LLM generation.
2.  Replicate the experimental methodology using newer or different models.
3.  Utilize the included tasks as a baseline for future human-AI interaction studies.

## Experimental Design
The repository includes implementations of three distinct programming challenges, selected to test specific capabilities:

* **Double Pendulum:** Tests numerical integration, physics simulation accuracy, and library usage (matplotlib, scipy).
* **Tic-Tac-Toe:** Tests game state management, GUI implementation, and Minimax AI logic.
* **Dynamic Maze Race:** Tests complex pathfinding algorithms (Prim's, A*, Dijkstra) and recursion depth.


--- 

## Installation and Usage

### Prerequisites
The project requires **Python 3.10+** and standard scientific computing libraries.
To install the required dependencies:
```bash
pip install matplotlib numpy scipy
```
*Note: GUI applications utilize `tkinter`. This is included in most standard Python installations but may require a separate package install (e.g., `python3-tk`) on some Linux distributions.*

### Execution Instructions
As this repository contains code generated under different experimental conditions, the entry point and execution method may vary for each specific script. We have standardized the documentation method for every test case.

**Protocol for running the software:**

1.  **Navigate to the specific experiment directory.**

2.  **Locate the Run Instructions.**
    Instructions are always provided in one of two formats:
    * **Local README:** A `README.md` file located within the specific folder will outline the file structure and execution order.
    * **Header Comments:** Detailed instructions on how to run and interact with the program are provided in a comment block at the very top of the main Python file.

3.  **Run the Application.**
    Execute the primary script from the root directory or the experiment folder as specified in the instructions.
    ```bash
    # Example
    python experiments/01_double_pendulum/iterative/main.py
    ```

### Usage Note
The `single_shot` directories contain raw, unrefined model outputs. These scripts are preserved in their original state for data integrity purposes. Users should expect that some of these files may not execute correctly or may contain logical errors. The `iterative` directories contain fully refined, functional applications.

