# Contributing to SortLab

Thanks for considering a contribution! SortLab aims to be a welcoming, beginner-friendly reference.

## Ways to contribute

- Add or improve an algorithm implementation.
- Add tests for edge cases.
- Improve explanations, examples, or complexity notes.
- Add or improve a visualization.
- Improve benchmarks or developer tooling.

## Development setup

```bash
git clone https://github.com/bhr007/sortlab.git
cd sortlab
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,visualization]"
pytest
```

## Algorithm contribution checklist

Every algorithm contribution should:

1. Use a descriptive filename and function name.
2. Include a docstring explaining the algorithm and its complexity.
3. Avoid modifying the caller's input unless the function explicitly documents in-place behavior.
4. Handle empty and single-element inputs.
5. Include tests for duplicates, negative values where supported, sorted input, reverse-sorted input, and randomized input.
6. Be added to the relevant package `__init__.py`.
7. Include a visualization event stream if the algorithm is intended to support step-by-step visualization.

## Code style

- Prefer readable, beginner-friendly Python.
- Add type hints.
- Keep dependencies optional where possible.
- Run `ruff check .` and `pytest` before submitting.
- Explain non-obvious implementation choices in comments.

## Pull requests

Keep pull requests focused. Describe what changed, why it is useful, and how it was tested. For new algorithms, include authoritative references when practical.

## Code of conduct

Be respectful, constructive, and welcoming. Critique code and ideas, not people.
