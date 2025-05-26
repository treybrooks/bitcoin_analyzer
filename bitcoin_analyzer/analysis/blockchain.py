from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional
import json
from ..rpc.client import BitcoinRPCClient

class BlockchainAnalyzer:
    """Analyze blockchain data from a Bitcoin node."""
    
    def __init__(self, rpc_client: BitcoinRPCClient):
        self.rpc = rpc_client
        
    def get_block_count(self) -> int:
        """Get the current block height."""
        return self.rpc.call("getblockcount")
        
    def get_block_timehash(self, height: int) -> Tuple[int, str]:
        """Get block timestamp and hash for a given height."""
        block_hash = self.rpc.call("getblockhash", [height])
        block_header = self.rpc.call("getblockheader", [block_hash, True])
        return block_header['time'], block_hash
    
    def get_first_block_of_day(self, target_date):
        """
        Find the first block mined on a specific date using binary search
        """
        day_start = int(target_date.timestamp())
        day_end = int((target_date.timestamp() + 86400))  # +24 hours
        
        # Binary search for the last block of the day
        left, right = 0, self.rpc.call("getblockcount")
        first_block_of_day = None
        
        while left <= right:
            mid = (left + right) // 2
            block = mid
            block_time, _ = self.get_block_timehash(block)
            
            if day_start <= block_time < day_end:
                # Block is within our target day
                first_block_of_day = block
                right = mid - 1  # Look for earlier blocks in the same day
            elif block_time < day_start:
                left = mid + 1
            else:
                right = mid - 1
                
        return first_block_of_day

    def find_blocks_by_date(self, target_date: datetime):
        """
        Find last block in day, retrieve data until day changes
        """
        block_num = self.get_first_block_of_day(target_date)
        oldest_time_allowed = int(target_date.timestamp() + 24*60*60)  # +24 hours
        
        # compare block time to oldest allowable utc timestamp
        block_data = [tuple([block_num, *self.get_block_timehash(block_num)])]
        while block_data[-1][1] <= oldest_time_allowed:
            block_num += 1
            block_data.append(tuple([block_num, *self.get_block_timehash(block_num)]))

        return block_data
        
    def get_recent_blocks(self, count: int = 144):
        """Get the most recent N blocks."""
        block_count = self.get_block_count()
        block_data = []
        for block_num in range(block_count - count, block_count):
            block_data.append(tuple([block_num, *self.get_block_timehash(block_num)]))
        return block_data
        

