#!/usr/bin/env python3
"""Command-line interface for UTXOracle."""

import argparse
import sys
from datetime import datetime, timedelta
import webbrowser
import os

from bitcoin_analyzer.config import load_bitcoin_config
from bitcoin_analyzer.rpc.client import BitcoinRPCClient
from bitcoin_analyzer.analysis.transactions_new import *

def main():
    parser = argparse.ArgumentParser(description='Inspect single block')
    parser.add_argument('-b', '--block', help='Specify Block hieght to evaluate', type=int)
    parser.add_argument('-p', '--path', help='Specify the data directory for blk files')
    parser.add_argument('-n', '--num_outputs', help='Number of output displays to print', type=int)
    parser.add_argument('-d', '--debug', help='Debug flag', nargs='?', type=bool, const=1)
    
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
    
    newest_block = rpc_client.call('getblockcount')
    print(f"Most Recent Block Height: {newest_block}")
        
    parser = TransactionParser(rpc_client).add_filters(
                InputCountFilter(max_inputs=5),
                OutputCountFilter(min_outputs=2, max_outputs=2),
                CoinbaseFilter(),
                OpReturnFilter(),
                ValueRangeFilter(min_btc=1e-5, max_btc=1e5),
                WitnessDataFilter(max_witness_items=100, max_item_size=500),
                InputReuseFilter()
            )
    
    # parser = create_default_parser(rpc_client)
    print(parser.get_filter_summary())
    if args.debug:
        parser.set_debug(True)
        
    block = newest_block
    if args.block:
        block = int(args.block)
    print(f"Inspecting block: {block}")
    block_hash = rpc_client.call("getblockhash", [block])
       
    outputs = parser.parse_block(block_hash)
    
    num_outputs = 5
    if args.num_outputs:
        num_outputs = args.num_outputs
        
    print(f"Found {len(outputs)} matching outputs")
    for output in outputs[:num_outputs]:  # Show first num_outputs
        print(f"  {output.value_btc} BTC in tx {output.txid} at {datetime.fromtimestamp(output.timestamp)}")
        
if __name__ == "__main__":
   main()