# Bitcoin Analyzer (UTXOracle)

A Bitcoin RPC client that analyzes blockchain data to estimate historical Bitcoin prices based on transaction patterns.

## Features

- Connect to local Bitcoin node via RPC
- Analyze transaction outputs to detect round USD amounts
- Estimate daily Bitcoin prices from on-chain data
- Web interface for visualization
- Command-line interface for batch processing

# Install with Poetry
poetry install

# Run Base cli command
poetry run python .\scripts\cli.py -p ../