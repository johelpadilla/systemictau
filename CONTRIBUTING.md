# Contributing to Systemic Tau

First off, thank you for considering contributing to `systemictau`! This package bridges the gap between complex systems theory, topology, and real-world time series analysis.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/systemictau.git
   cd systemictau
   ```

2. Install the package in editable mode with development dependencies (pytest, sphinx):
   ```bash
   pip install -e .
   pip install pytest sphinx
   ```

## Running Tests

We use `pytest` for unit testing. Before submitting any pull request, please ensure all tests pass:

```bash
pytest tests/
```

If you are adding a new feature, please add a corresponding test in the `tests/` directory to maintain code coverage.

## Building Documentation

We use Sphinx for documentation. To build the documentation locally:

```bash
cd docs
make html
```

The generated HTML files will be available in `docs/_build/html/`.

## Code of Conduct

By participating in this project, you agree to abide by common open-source standards of respect and collaboration. Our goal is to advance the scientific understanding of temporal discreteness and complex systems.
