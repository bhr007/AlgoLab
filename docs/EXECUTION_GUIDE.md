# AlgoLab Execution Guide (macOS, Linux, Windows)

This guide walks through setting up, running, and testing **AlgoLab** on **macOS**, **Linux**, and **Windows** (`Python >= 3.9` required).

> Both `algolab` and the legacy `sortlab` CLI alias (as well as `python -m sortlab.cli`) invoke the same entrypoint.

---

## 1. macOS (Terminal / `zsh`)

1. **Clone and enter the repository:**
   ```bash
   git clone https://github.com/bhr007/AlgoLab.git
   cd AlgoLab
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install AlgoLab with visualization and dev dependencies:**
   ```bash
   python -m pip install --upgrade pip
   pip install -e ".[dev,visualization]"
   ```
4. **Run AlgoLab in your preferred mode:**
   - **Single-window Desktop GUI Studio (no browser):**
     ```bash
     algolab --gui
     ```
   - **Interactive CLI + Matplotlib visualization:**
     ```bash
     algolab
     ```
   - **CLI-only (terminal only, no GUI windows):**
     ```bash
     algolab --mode cli
     ```
   - **Automated CLI input run:**
     ```bash
     algolab --mode cli < examples/automated_input.txt
     ```
5. **Run examples and tests:**
   ```bash
   python examples/visualize_bubble_sort.py
   python examples/benchmark_algorithms.py
   pytest -v
   ```

---

## 2. Linux (`bash` / `zsh`)

1. **Ensure Python venv and a GUI backend (`TkAgg`) are installed** *(skip `python3-tk` if you only need headless CLI mode `--mode cli`)*:
   - **Debian / Ubuntu:**
     ```bash
     sudo apt-get update && sudo apt-get install -y python3-venv python3-tk
     ```
   - **Fedora:**
     ```bash
     sudo dnf install -y python3-tkinter
     ```
   - **Arch Linux:**
     ```bash
     sudo pacman -S tk
     ```
2. **Clone and enter the repository:**
   ```bash
   git clone https://github.com/bhr007/AlgoLab.git
   cd AlgoLab
   ```
3. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
4. **Install dependencies:**
   ```bash
   python -m pip install --upgrade pip
   pip install -e ".[dev,visualization]"
   ```
5. **Run AlgoLab:**
   - **Single-window Desktop GUI Studio:** `algolab --gui`
   - **Interactive CLI + Matplotlib visualization:** `algolab`
   - **CLI-only (works over SSH / headless servers):** `algolab --mode cli`
   - **Automated CLI input run:** `algolab --mode cli < examples/automated_input.txt`
6. **Run examples and tests:**
   ```bash
   python examples/visualize_bubble_sort.py
   python examples/benchmark_algorithms.py
   pytest -v
   ```

---

## 3. Windows (PowerShell)

1. **Install Python 3.9+ from [python.org](https://www.python.org/downloads/)** (standard installer includes `tkinter` for Matplotlib's `TkAgg` GUI backend; check **"Add python.exe to PATH"**).
2. **Clone and enter the repository:**
   ```powershell
   git clone https://github.com/bhr007/AlgoLab.git
   cd AlgoLab
   ```
3. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   *(If PowerShell blocks script activation, allow local scripts once: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.)*
4. **Install dependencies:**
   ```powershell
   python -m pip install --upgrade pip
   pip install -e ".[dev,visualization]"
   ```
5. **Run AlgoLab:**
   - **Single-window Desktop GUI Studio:**
     ```powershell
     algolab --gui
     ```
   - **Interactive CLI + Matplotlib visualization:**
     ```powershell
     algolab
     ```
   - **CLI-only (no GUI windows):**
     ```powershell
     algolab --mode cli
     ```
   - **Automated CLI input run in PowerShell** *(PowerShell pipes file contents with `Get-Content` instead of `<`)*:
     ```powershell
     Get-Content examples\automated_input.txt | algolab --mode cli
     ```
6. **Run examples and tests:**
   ```powershell
   python examples\visualize_bubble_sort.py
   python examples\benchmark_algorithms.py
   pytest -v
   ```

---

## Quick Mode & Flag Reference (All OS)

| Command | Mode | Description |
|---|---|---|
| `algolab --gui` (or `--mode gui`) | GUI only | Opens the single-window Desktop Studio (Sorting + Graph tabs, presets, live playback). |
| `algolab` (or `--mode cli-gui`) | CLI + GUI | Interactive terminal menu with automatic Matplotlib visualization launch (option `3` opens the Studio). |
| `algolab --mode cli` (or `--no-vis`) | CLI only | Terminal-only execution and timing; never opens any GUI window. |
| `algolab --list` | Info | Lists all 10 sorting and 7 graph algorithms and exits. |
| `algolab --interval 200` | Timing option | Sets initial animation frame delay in milliseconds. |
| `sortlab ...` / `python -m sortlab.cli ...` | Compatibility | Legacy CLI alias and module invocation (kept for backward compatibility). |
