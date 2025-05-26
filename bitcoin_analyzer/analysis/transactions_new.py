from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class TransactionOutput:
    """Represents a transaction output."""
    value_btc: float
    block_height: int
    timestamp: int
    txid: str
    output_index: int

class TransactionFilter(ABC):
    """Base class for transaction filters."""
    
    @abstractmethod
    def should_include(self, tx: Dict[str, Any], block_height: int, block_time: int) -> bool:
        """Return True if transaction should be included."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return filter name for logging/debugging."""
        pass

class InputCountFilter(TransactionFilter):
    """Filter by number of inputs."""
    
    def __init__(self, max_inputs: int = 5):
        self.max_inputs = max_inputs
    
    def should_include(self, tx: Dict[str, Any], block_height: int, block_time: int) -> bool:
        return len(tx['vin']) <= self.max_inputs
    
    def get_name(self) -> str:
        return f"InputCount<={self.max_inputs}"

class OutputCountFilter(TransactionFilter):
    """Filter by number of outputs."""
    
    def __init__(self, exact_outputs: int = 2):
        self.exact_outputs = exact_outputs
    
    def should_include(self, tx: Dict[str, Any], block_height: int, block_time: int) -> bool:
        return len(tx['vout']) == self.exact_outputs
    
    def get_name(self) -> str:
        return f"OutputCount=={self.exact_outputs}"

class CoinbaseFilter(TransactionFilter):
    """Filter out coinbase transactions."""
    
    def should_include(self, tx: Dict[str, Any], block_height: int, block_time: int) -> bool:
        return 'coinbase' not in tx['vin'][0]
    
    def get_name(self) -> str:
        return "NoCoinbase"

class OpReturnFilter(TransactionFilter):
    """Filter out transactions with OP_RETURN outputs."""
    
    def should_include(self, tx: Dict[str, Any], block_height: int, block_time: int) -> bool:
        for output in tx['vout']:
            script_type = output.get('scriptPubKey', {}).get('type', '')
            asm = output.get('scriptPubKey', {}).get('asm', '')
            if script_type == 'nulldata' or 'OP_RETURN' in asm:
                return False
        return True
    
    def get_name(self) -> str:
        return "NoOpReturn"

class ValueRangeFilter(TransactionFilter):
    """Filter by output value range."""
    
    def __init__(self, min_btc: float = 1e-5, max_btc: float = 1e5):
        self.min_btc = min_btc
        self.max_btc = max_btc
    
    def should_include(self, tx: Dict[str, Any], block_height: int, block_time: int) -> bool:
        for output in tx['vout']:
            value = output['value']
            if not (self.min_btc < value < self.max_btc):
                return False
        return True
    
    def get_name(self) -> str:
        return f"ValueRange({self.min_btc}-{self.max_btc})"

class WitnessDataFilter(TransactionFilter):
    """Filter by witness data size."""
    
    def __init__(self, max_witness_items: int = 100, max_item_size: int = 500):
        self.max_witness_items = max_witness_items
        self.max_item_size = max_item_size
    
    def should_include(self, tx: Dict[str, Any], block_height: int, block_time: int) -> bool:
        for input_data in tx['vin']:
            witness = input_data.get('txinwitness', [])
            if len(witness) > self.max_witness_items:
                return False
            
            total_size = 0
            for item in witness:
                item_size = len(item) // 2  # hex string to bytes
                if item_size > self.max_item_size:
                    return False
                total_size += item_size
                
            if total_size > self.max_item_size:
                return False
        return True
    
    def get_name(self) -> str:
        return f"WitnessData(max_items={self.max_witness_items}, max_size={self.max_item_size})"

class SameDayTransactionFilter(TransactionFilter):
    """Filter out transactions that spend outputs from the same day."""
    
    def __init__(self, rpc_client, known_txids: Set[str]):
        self.rpc_client = rpc_client
        self.known_txids = known_txids
    
    def should_include(self, tx: Dict[str, Any], block_height: int, block_time: int) -> bool:
        for input_data in tx['vin']:
            if 'coinbase' in input_data:
                continue
            
            prev_txid = input_data['txid']
            if prev_txid in self.known_txids:
                return False
                
        return True
    
    def get_name(self) -> str:
        return "NoSameDaySpend"

class CustomFilter(TransactionFilter):
    """Custom filter using a lambda function."""
    
    def __init__(self, filter_func, name: str):
        self.filter_func = filter_func
        self.name = name
    
    def should_include(self, tx: Dict[str, Any], block_height: int, block_time: int) -> bool:
        return self.filter_func(tx, block_height, block_time)
    
    def get_name(self) -> str:
        return self.name

class TransactionParser:
    """Parse and filter Bitcoin transactions using RPC."""
    
    def __init__(self, rpc_client):
        self.rpc_client = rpc_client
        self.filters: List[TransactionFilter] = []
        self.todays_txids: Set[str] = set()
        self.debug = False
        
    def add_filter(self, filter_obj: TransactionFilter) -> 'TransactionParser':
        """Add a filter to the parser. Returns self for chaining."""
        self.filters.append(filter_obj)
        return self
    
    def add_filters(self, *filters: TransactionFilter) -> 'TransactionParser':
        """Add multiple filters. Returns self for chaining."""
        self.filters.extend(filters)
        return self
    
    def clear_filters(self) -> 'TransactionParser':
        """Clear all filters."""
        self.filters.clear()
        return self
    
    def set_debug(self, debug: bool = True) -> 'TransactionParser':
        """Enable/disable debug logging."""
        self.debug = debug
        return self
    
    def parse_block(self, block_hash: str) -> List[TransactionOutput]:
        """Parse a block and return filtered transaction outputs."""
        # Get block with full transaction data (verbosity=2)
        block = self.rpc_client.call("getblock", [block_hash, 2])
        
        outputs = []
        block_height = block['height']
        block_time = block['time']
        
        if self.debug:
            print(f"Processing block {block_height} with {len(block['tx'])} transactions")
        
        for tx in block['tx']:
            # Add txid to known set for same-day filtering
            self.todays_txids.add(tx['txid'])
            
            if self._passes_all_filters(tx, block_height, block_time):
                tx_outputs = self._extract_outputs(tx, block_height, block_time)
                outputs.extend(tx_outputs)
                
                if self.debug:
                    print(f"  ✓ Included tx {tx['txid'][:16]}... ({len(tx_outputs)} outputs)")
            elif self.debug:
                failed_filter = self._get_failed_filter(tx, block_height, block_time)
                print(f"  ✗ Filtered tx {tx['txid'][:16]}... (failed: {failed_filter})")
        
        if self.debug:
            print(f"Block {block_height}: {len(outputs)} outputs after filtering")
            
        return outputs
    
    def _passes_all_filters(self, tx: Dict[str, Any], block_height: int, block_time: int) -> bool:
        """Check if transaction passes all filters."""
        return all(f.should_include(tx, block_height, block_time) for f in self.filters)
    
    def _get_failed_filter(self, tx: Dict[str, Any], block_height: int, block_time: int) -> str:
        """Get name of first failed filter (for debugging)."""
        for f in self.filters:
            if not f.should_include(tx, block_height, block_time):
                return f.get_name()
        return "None"
    
    def _extract_outputs(self, tx: Dict[str, Any], block_height: int, block_time: int) -> List[TransactionOutput]:
        """Extract outputs from a transaction."""
        outputs = []
        
        for i, output in enumerate(tx['vout']):
            outputs.append(TransactionOutput(
                value_btc=output['value'],
                block_height=block_height,
                timestamp=block_time,
                txid=tx['txid'],
                output_index=i
            ))
        
        return outputs
    
    def get_filter_summary(self) -> str:
        """Get a summary of active filters."""
        if not self.filters:
            return "No filters active"
        
        filter_names = [f.get_name() for f in self.filters]
        return f"Active filters: {', '.join(filter_names)}"

# Usage examples and factory functions
def create_default_parser(rpc_client) -> TransactionParser:
    """Create parser with your current filtering logic."""
    return (TransactionParser(rpc_client)
            .add_filters(
                InputCountFilter(max_inputs=5),
                OutputCountFilter(exact_outputs=2),
                CoinbaseFilter(),
                OpReturnFilter(),
                ValueRangeFilter(min_btc=1e-5, max_btc=1e5),
                WitnessDataFilter(max_witness_items=100, max_item_size=500)
            ))

def create_simple_parser(rpc_client) -> TransactionParser:
    """Create parser with basic filters only."""
    return (TransactionParser(rpc_client)
            .add_filters(
                CoinbaseFilter(),
                OpReturnFilter()
            ))

# Example usage:
if __name__ == "__main__":
    # Setup (assuming you have rpc_client)
    import sys
    import os

    # Add the path two folders up to sys.path
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    import argparse
    from bitcoin_analyzer.rpc.client import BitcoinRPCClient
    from bitcoin_analyzer.config import load_bitcoin_config
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path')
    
    args = parser.parse_args()
    
    config = load_bitcoin_config(args.path)
    rpc_client = BitcoinRPCClient(
        host=config.rpc_host,
        port=config.rpc_port,
        user=config.rpc_user,
        password=config.rpc_password,
        cookie_path=config.cookie_path
    )
    
    # Method 1: Use default configuration
    parser = create_default_parser(rpc_client)
    
    # Method 2: Build custom configuration
    parser = (TransactionParser(rpc_client)
              .add_filter(InputCountFilter(max_inputs=3))
              .add_filter(OutputCountFilter(exact_outputs=2))
              .add_filter(CoinbaseFilter())
              .set_debug(True))
    
    # Method 3: Add custom logic
    def large_transaction_filter(tx, block_height, block_time):
        """Custom filter for large transactions."""
        total_value = sum(out['value'] for out in tx['vout'])
        return total_value > 1.0  # Only transactions > 1 BTC
    
    parser.add_filter(CustomFilter(large_transaction_filter, "LargeTransaction>1BTC"))
    
    # Method 4: Add same-day filter dynamically
    parser.add_filter(SameDayTransactionFilter(rpc_client, parser.todays_txids))
    
    # Parse blocks
    print(parser.get_filter_summary())
    
    block_hieght = rpc_client.call("getblockcount")
    block_hash = rpc_client.call("getblockhash", [block_hieght])
    outputs = parser.parse_block(block_hash)
    
    print(f"Found {len(outputs)} matching outputs")
    for output in outputs[:5]:  # Show first 5
        print(f"  {output.value_btc} BTC in tx {output.txid}")