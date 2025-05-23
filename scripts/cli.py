#!/usr/bin/env python3
"""Command-line interface for UTXOracle."""

import argparse
import sys
from datetime import datetime, timedelta
import webbrowser
import os

from bitcoin_analyzer.config import load_bitcoin_config
from bitcoin_analyzer.rpc.client import BitcoinRPCClient
from bitcoin_analyzer.analysis.blockchain import BlockchainAnalyzer
from bitcoin_analyzer.analysis.metrics import PriceEstimator
from bitcoin_analyzer.analysis.transactions import TransactionParser
from bitcoin_analyzer.web.chart_generator import ChartGenerator

def main():
    parser = argparse.ArgumentParser(description='UTXOracle - Bitcoin price oracle')
    parser.add_argument('-d', '--date', help='Specify a UTC date to evaluate (YYYY/MM/DD)')
    parser.add_argument('-p', '--path', help='Specify the data directory for blk files')
    parser.add_argument('-rb', '--recent-blocks', action='store_true', 
                       help='Use last 144 recent blocks instead of date mode')
    
    args = parser.parse_args()
    
    # Load config
    config = load_bitcoin_config(args.path)
    
    # Create RPC client
    rpc_client = BitcoinRPCClient(
        host=config.rpc_host,
        port=config.rpc_port,
        user=config.rpc_user,
        password=config.rpc_password,
        cookie_path=config.cookie_path
    )
    
    # Run analysis
    analyzer = BlockchainAnalyzer(rpc_client)
    parser = TransactionParser()
    estimator = PriceEstimator()
    
    if args.recent_blocks:
        # Analyze recent blocks
        print("Analyzing recent 144 blocks...")
        start, end, nums, hashes, times = analyzer.get_recent_blocks(144)
    else:
       # Analyze specific date
       if args.date:
           target_date = datetime.strptime(args.date, "%Y/%m/%d")
       else:
           # Use yesterday as default
           target_date = datetime.now() - timedelta(days=1)
           target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
       
       print(f"Analyzing blocks for {target_date.strftime('%Y-%m-%d')}...")
       start, end, nums, hashes, times = analyzer.find_blocks_by_date(target_date)
   
   # Parse transactions
    print("Parsing transactions...")
    for i, block_hash in enumerate(hashes):
       if i % 10 == 0:
           print(f"Progress: {i}/{len(hashes)} blocks")
       
       block_hex = rpc_client.call("getblock", [block_hash, 0])
       outputs = parser.parse_block(block_hex, nums[i], times[i])
       
       for output in outputs:
           estimator.add_output(output.value_btc)
   
   # Get price estimate
    final_price, rough_price = estimator.estimate_price()
    print(f"\nEstimated price: ${int(final_price):,}")
   
    # Generate and display chart
    generator = ChartGenerator()
    html_path = generator.generate_chart(
       estimator, nums, times, final_price,
       is_date_mode=not args.recent_blocks,
       target_date=target_date if not args.recent_blocks else None
    )
   
    webbrowser.open(f'file://{os.path.abspath(html_path)}')

if __name__ == "__main__":
   main()