"""Interactive command-line interface for SortLab."""

from __future__ import annotations

import argparse
import math
import sys
from time import perf_counter
from typing import Callable

from sortlab.core.registry import (
    ALGORITHM_REGISTRY,
    ALGORITHM_SPECS,
    AlgorithmSpec,
    get_algorithm_spec,
    validate_inputs_for_spec,
)

# Preserved for backward compatibility with callers inspecting cli.ALGORITHMS.
ALGORITHMS: dict[str, tuple[str, Callable]] = {
    spec.choice: (spec.name, spec.algorithm) for spec in ALGORITHM_SPECS
}


def show_menu() -> None:
    """Print the algorithm selection menu."""
    print("\n========== SortLab ==========")
    print("Explore. Visualize. Understand Sorting.\n")
    for spec in ALGORITHM_SPECS:
        note = " (integers only)" if spec.integer_only else ""
        print(f"  {spec.choice:>2}. {spec.name}{note}")
    print("   0. Exit")
    print("=============================\n")


def parse_values(raw: str) -> list[float]:
    """Parse a comma- or whitespace-separated list of finite numbers."""
    parts = raw.replace(",", " ").split()
    if not parts:
        raise ValueError("Please enter at least one number.")

    values: list[float] = []
    for part in parts:
        if "." not in part and "e" not in part.lower():
            try:
                values.append(int(part))
                continue
            except ValueError:
                pass
        try:
            number = float(part)
        except ValueError as exc:
            raise ValueError(f"{part!r} is not a valid number.") from exc
        if not math.isfinite(number):
            raise ValueError(f"{part!r} is not a finite number.")
        values.append(int(number) if number.is_integer() else number)
    return values


def run_algorithm(choice: str, values: list[float]) -> list[float]:
    """Validate inputs and dispatch to the selected sorting implementation."""
    spec = get_algorithm_spec(choice)
    validate_inputs_for_spec(spec, values)
    return spec.algorithm(values)


def visualize_algorithm(
    spec: AlgorithmSpec,
    values: list[float],
    *,
    interval: int | None = None,
    max_frames: int | None = 1500,
    show: bool = True,
):
    """Generate events for ``spec`` and launch the Matplotlib animation."""
    from sortlab.visualization.matplotlib import animate_events

    events = spec.event_generator(values)
    return animate_events(
        events,
        interval=interval,
        algorithm_name=spec.name,
        show=show,
        max_frames=max_frames,
    )


def main(argv=None) -> int:
    """Run the interactive SortLab CLI."""
    parser = argparse.ArgumentParser(
        prog="sortlab",
        description="Choose and visualize a sorting algorithm from the SortLab collection.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list all available sorting algorithms and exit",
    )
    parser.add_argument(
        "--no-vis",
        action="store_true",
        help="run sorting without opening the Matplotlib visualization window",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="animation delay between frames in milliseconds",
    )
    args = parser.parse_args(argv)

    if args.list:
        for spec in ALGORITHM_SPECS:
            note = " (integers only)" if spec.integer_only else ""
            print(f"{spec.choice:>2}. {spec.name}{note}")
        return 0

    if args.interval is not None and args.interval < 1:
        parser.error("--interval must be at least 1 ms")

    while True:
        show_menu()
        try:
            choice = input("Choose an algorithm (0-10): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0

        if choice == "0":
            print("Goodbye!")
            return 0
        if choice not in ALGORITHM_REGISTRY:
            print("Invalid choice. Please select a number from 0 to 10.")
            continue

        spec = ALGORITHM_REGISTRY[choice]
        try:
            raw_values = input(
                "\nEnter numbers separated by spaces or commas: "
            )
            values = parse_values(raw_values)
            validate_inputs_for_spec(spec, values)

            # Time only the pure sorting implementation, separate from event
            # generation and Matplotlib visualization overhead.
            start = perf_counter()
            result = spec.algorithm(values)
            elapsed = perf_counter() - start

            print(f"\nAlgorithm: {spec.name}")
            print(f"Original:  {values}")
            print(f"Sorted:    {result}")
            print(f"Sort time: {elapsed:.6f} seconds (algorithm only)\n")

            if not args.no_vis:
                print(
                    f"Opening Matplotlib visualization for {spec.name} "
                    "(close the window to return to the menu)..."
                )
                try:
                    visualize_algorithm(spec, values, interval=args.interval)
                except ImportError as exc:
                    print(f"Visualization unavailable: {exc}\n")
        except (ValueError, TypeError) as exc:
            print(f"Could not sort these values: {exc}\n")
        except (EOFError, KeyboardInterrupt):
            print("\nReturning to the algorithm menu...\n")


if __name__ == "__main__":
    sys.exit(main())
