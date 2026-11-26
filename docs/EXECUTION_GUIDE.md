# SortLab Execution Guide (macOS, Linux, Windows)

This guide walks through setting up, running, and testing **SortLab** on **macOS**, **Linux**, and **Windows** (`Python >= 3.9` required).

---

## 1. macOS (Terminal / `zsh`)

1. **Clone and enter the repository:**
   ```bash
   git clone https://github.com/bhr007/SortLab.git
   cd SortLab
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install SortLab with visualization and dev dependencies:**
   ```bash
   python -m pip install --upgrade pip
   pip install -e ".[dev,visualization]"
   ```
4. **Run SortLab in your preferred mode:**
   - **Single-window Desktop GUI Studio (no browser):**
     ```bash
     sortlab --gui
     ```
   - **Interactive CLI + Matplotlib visualization:**
     ```bash
     sortlab
     ```
   - **CLI-only (terminal only, no GUI windows):**
     ```bash
     sortlab --mode cli
     ```
   - **Automated CLI input run:**
     ```bash
     sortlab --mode cli < examples/automated_input.txt
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
   git clone https://github.com/bhr007/SortLab.git
   cd SortLab
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
5. **Run SortLab:**
   - **Single-window Desktop GUI Studio:** `sortlab --gui`
   - **Interactive CLI + Matplotlib visualization:** `sortlab`
   - **CLI-only (works over SSH / headless servers):** `sortlab --mode cli`
   - **Automated CLI input run:** `sortlab --mode cli < examples/automated_input.txt`
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
   git clone https://github.com/bhr007/SortLab.git
   cd SortLab
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
5. **Run SortLab:**
   - **Single-window Desktop GUI Studio:**
     ```powershell
     sortlab --gui
     ```
   - **Interactive CLI + Matplotlib visualization:**
     ```powershell
     sortlab
     ```
   - **CLI-only (no GUI windows):**
     ```powershell
     sortlab --mode cli
     ```
   - **Automated CLI input run in PowerShell** *(PowerShell pipes file contents with `Get-Content` instead of `<`)*:
     ```powershell
     Get-Content examples\automated_input.txt | sortlab --mode cli
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
| `sortlab --gui` (or `--mode gui`) | GUI only | Opens the single-window Desktop Studio (Sorting + Graph tabs, presets, live playback). |
| `sortlab` (or `--mode cli-gui`) | CLI + GUI | Interactive terminal menu with automatic Matplotlib visualization launch (option `3` opens the Studio). |
| `sortlab --mode cli` (or `--no-vis`) | CLI only | Terminal-only execution and timing; never opens any GUI window. |
| `sortlab --list` | Info | Lists all 10 sorting and 7 graph algorithms and exits. |
| `sortlab --interval 200` | Timing option | Sets initial animation frame delay in milliseconds. |
| `python -m sortlab.cli ...` | Fallback | Equivalent to `sortlab ...` if the `sortlab` script is not on `PATH`. |
