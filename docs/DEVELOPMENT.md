<!-- generated-by: gsd-doc-writer -->
# Development

## Local Setup
To set up the project for development:
1. Ensure Python 3.8+ is installed.
2. Clone the repository.
3. Create a virtual environment (`python -m venv .venv`).
4. Activate the environment and install dependencies (`pip install pandas numpy mplfinance tvDatafeed pyarrow`).

## Build Commands
This project consists of Python scripts and does not have a formal build step or `package.json`. 

| Command | Description |
|---|---|
| `python main.py` | Runs the main data fetcher and structure analysis script, outputting PNG charts. |
| `python test_fetch.py` | Runs the test fetching script to verify API connectivity. |

## Code Style
There are currently no enforced linters or formatters (like `black` or `flake8`) configured in the repository. Standard PEP-8 conventions are recommended.

## Branch Conventions
No convention documented.

## PR Process
1. Fork the repository and create your branch from `main`.
2. Ensure your code does not break the logic in `market_structure.py`.
3. Test your changes by running `python main.py` and reviewing the output charts.
4. Open a pull request describing your changes.
