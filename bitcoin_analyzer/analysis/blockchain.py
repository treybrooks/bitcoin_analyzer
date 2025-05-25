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
        
    def get_block_time(self, height: int) -> Tuple[int, str]:
        """Get block timestamp and hash for a given height."""
        print("Block Hieght: ", height)
        block_hash = self.rpc.call("getblockhash", [height])
        block_header = self.rpc.call("getblockheader", [block_hash, True])
        return block_header['time'], block_hash
        
    def find_blocks_by_date(self, target_date: datetime) -> Tuple[int, int, List[int], List[str], List[int]]:
        """Find all blocks mined on a specific date."""
        # Get current block info
        block_count = self.get_block_count()
        block_count_consensus = block_count - 6
        
        # Get target day timestamp
        price_day_seconds = int(target_date.timestamp())
        seconds_in_a_day = 86400
        
        # Get latest block time
        latest_time, _ = self.get_block_time(block_count_consensus)
        
        # Estimate starting block
        seconds_since_price_day = latest_time - price_day_seconds
        blocks_ago_estimate = round(144 * seconds_since_price_day / seconds_in_a_day)
        price_day_block_estimate = block_count_consensus - blocks_ago_estimate
        
        # Binary search for first block of the day
        time_in_seconds, _ = self.get_block_time(price_day_block_estimate)
        seconds_difference = time_in_seconds - price_day_seconds
        block_jump_estimate = round(144 * seconds_difference / seconds_in_a_day)
        
        last_estimate = 0
        last_last_estimate = 0
        
        while block_jump_estimate > 6 and block_jump_estimate != last_last_estimate:
            last_last_estimate = last_estimate
            last_estimate = block_jump_estimate
            price_day_block_estimate = price_day_block_estimate - block_jump_estimate
            time_in_seconds, _ = self.get_block_time(price_day_block_estimate)
            seconds_difference = time_in_seconds - price_day_seconds
            block_jump_estimate = round(144 * seconds_difference / seconds_in_a_day)
        
        # Fine-tune to exact first block
        if time_in_seconds > price_day_seconds:
            while time_in_seconds > price_day_seconds:
                price_day_block_estimate -= 1
                time_in_seconds, _ = self.get_block_time(price_day_block_estimate)
            price_day_block_estimate += 1
        else:
            while time_in_seconds < price_day_seconds:
                price_day_block_estimate += 1
                time_in_seconds, _ = self.get_block_time(price_day_block_estimate)
        
        # Find all blocks on this day
        block_start = price_day_block_estimate
        block_nums = []
        block_hashes = []
        block_times = []
        
        time_in_seconds, hash_val = self.get_block_time(block_start)
        day_start = datetime.fromtimestamp(time_in_seconds, tz=timezone.utc).day
        
        block_num = block_start
        while True:
            time_in_seconds, hash_val = self.get_block_time(block_num)
            current_day = datetime.fromtimestamp(time_in_seconds, tz=timezone.utc).day
            
            if current_day != day_start:
                break
                
            block_nums.append(block_num)
            block_hashes.append(hash_val)
            block_times.append(time_in_seconds)
            block_num += 1
            
        return block_start, block_num, block_nums, block_hashes, block_times
        
    def get_recent_blocks(self, count: int = 144) -> Tuple[int, int, List[int], List[str], List[int]]:
        """Get the most recent N blocks."""
        block_count = self.get_block_count()
        block_finish = block_count
        block_start = block_finish - count
        
        block_nums = []
        block_hashes = []
        block_times = []
        
        for block_num in range(block_start, block_finish):
            time_in_seconds, hash_val = self.get_block_time(block_num)
            block_nums.append(block_num)
            block_hashes.append(hash_val)
            block_times.append(time_in_seconds)
            
        return block_start, block_finish, block_nums, block_hashes, block_times
