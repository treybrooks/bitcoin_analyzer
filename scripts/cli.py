#!/usr/bin/env python3
"""Command-line interface for UTXOracle."""

import argparse
import asyncio
from datetime import datetime, timedelta
import webbrowser
import os

from bitcoin_analyzer.config import load_bitcoin_config
from bitcoin_analyzer.rpc.client import BitcoinRPCClient, AsyncBitcoinRPCClient
from bitcoin_analyzer.analysis.blockchain import BlockchainAnalyzer
from bitcoin_analyzer.analysis.metrics import PriceEstimator
from bitcoin_analyzer.analysis.transactions import create_default_parser
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
    
    print(f"Most Recent Block Height: {rpc_client.call('getblockcount')}")
    
    # Run analysis
    analyzer = BlockchainAnalyzer(rpc_client)
    # parser = TransactionParser()
    parser = create_default_parser(rpc_client)
    estimator = PriceEstimator() # from Metrics
    
    if args.recent_blocks:
        # Analyze recent blocks
        print("Analyzing recent 144 blocks...")
        block_data = analyzer.get_recent_blocks(144)
    else:
       # Analyze specific date
       if args.date:
           target_date = datetime.strptime(args.date, "%Y/%m/%d")
       else:
           # Use yesterday as default
           target_date = datetime.now() - timedelta(days=1)
           target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
       
       print(f"Analyzing blocks for {target_date.strftime('%Y-%m-%d')}...")
       block_data = analyzer.find_blocks_by_date(target_date)
   

    for i, data in enumerate(block_data):
        block, time, hash = data
        if i % 10 == 0:
            print(f"Progress: {i}/{len(block_data)} blocks")
            
        outputs = parser.parse_block(hash)
       
        for output in outputs:
           estimator.add_output(output.value_btc)

   # Get price estimate
    rough_price = estimator.estimate_price()
    print(f"\nEstimated Rough price: ${int(rough_price):,}")
   
    # # Generate and display chart
    # generator = ChartGenerator()
    # html_path = generator.generate_chart(
    #    estimator, nums, times, rough_price,
    #    is_date_mode=not args.recent_blocks,
    #    target_date=target_date if not args.recent_blocks else None
    # )
   
    # webbrowser.open(f'file://{os.path.abspath(html_path)}')

async def async_main():
    parser = argparse.ArgumentParser(description='UTXOracle - Bitcoin price oracle')
    parser.add_argument('-d', '--date', help='Specify a UTC date to evaluate (YYYY/MM/DD)')
    parser.add_argument('-p', '--path', help='Specify the data directory for blk files')
    parser.add_argument('-rb', '--recent-blocks', action='store_true', 
                       help='Use last 144 recent blocks instead of date mode')
    parser.add_argument('--max-concurrent', type=int, default=10,
                       help='Maximum concurrent RPC calls (default: 10)')
    
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
    
    print(f"Most Recent Block Height: {rpc_client.call('getblockcount')}")
    
    # Run analysis
    analyzer = BlockchainAnalyzer(rpc_client)
    parser_obj = create_default_parser(rpc_client)
    estimator = PriceEstimator()
    
    if args.recent_blocks:
        print("Analyzing recent 144 blocks...")
        block_data = analyzer.get_recent_blocks(144)
    else:
        if args.date:
            target_date = datetime.strptime(args.date, "%Y/%m/%d")
        else:
            target_date = datetime.now() - timedelta(days=1)
            target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        print(f"Analyzing blocks for {target_date.strftime('%Y-%m-%d')}...")
        block_data = analyzer.find_blocks_by_date(target_date)
    
    # Extract block hashes
    block_hashes = [data[2] for data in block_data]
    
    print(f"Processing {len(block_hashes)} blocks async with max {args.max_concurrent} concurrent requests...")
    
    # Process blocks async
    async with AsyncBitcoinRPCClient(rpc_client, max_concurrent=args.max_concurrent) as async_client:
        all_outputs_lists = await async_client.parse_blocks_batch(block_hashes, parser_obj)
        
        # Add all outputs to estimator
        for outputs_list in all_outputs_lists:
            for output in outputs_list:
                estimator.add_output(output.value_btc)
    
    # Get price estimate
    rough_price = estimator.estimate_price()
    print(f"\nEstimated Rough price: ${int(rough_price):,}")
    
def main():
    asyncio.run(async_main())

if __name__ == "__main__":
   main()