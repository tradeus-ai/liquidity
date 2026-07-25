<!-- generated-by: gsd-doc-writer -->
# Testing

## Test Framework and Setup
This project currently does not use a formal testing framework (such as `pytest` or `unittest`). 

Testing is done manually or via specific test scripts provided in the repository.

## Running Tests
To verify that the TradingView API data fetching logic works, run the `test_fetch.py` script:

```bash
python test_fetch.py
```

This will attempt to fetch data for the configured symbol to verify connectivity and caching logic without invoking the visualization suite.

## Coverage Requirements
No coverage threshold configured.

## CI Integration
There are no Continuous Integration (CI) workflows currently configured for this repository.
