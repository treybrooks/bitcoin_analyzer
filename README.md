# Bitcoin Analyzer (UTXOracle)

A Bitcoin RPC client that analyzes blockchain data to estimate historical Bitcoin prices based on transaction patterns.

## Features

- Connect to local Bitcoin node via RPC
- Analyze transaction outputs to detect round USD amounts
- Estimate daily Bitcoin prices from on-chain data
- Web interface for visualization
- Command-line interface for batch processing

# Install with Poetry
`poetry install`

# Run Base cli command
+ Target Date: -d', '--date', Specify a UTC date to evaluate (YYYY/MM/DD)
+ Config Path: '-p', '--path', help='Specify the data directory for blk files
+ Block Mode: '-rb', '--recent-blocks', action='store_true', Use last 144 recent blocks instead of date mode

Run Example:
`poetry run python .\scripts\cli.py -p ../`

# Inspect Single Block
Paramters:
+ Block: '-b', '--block', Specify Block hieght to evaluate, defaults to most recent block
+ Path: '-p', '--path', Specify the data directory for blk files
+ Display: '-n', '--num_outputs', Number of output displays to print, default 5
+ Debug: '-d', '--debug', Boolean debug flag, default False

Run Example:
`poetry run python .\scripts\inspect_block.py -p ../ -b 898430 -n 10 -d`