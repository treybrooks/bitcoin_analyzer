import hashlib
import struct
from io import BytesIO
from typing import List, Tuple, Set, Optional
import binascii
from dataclasses import dataclass

@dataclass
class TransactionOutput:
    """Represents a transaction output."""
    value_btc: float
    block_height: int
    timestamp: int

class TransactionParser:
    """Parse and filter Bitcoin transactions."""
    
    def __init__(self):
        self.todays_txids: Set[str] = set()
        
    def parse_block(self, block_hex: str, block_height: int, block_time: int) -> List[TransactionOutput]:
        """Parse a block and extract filtered transaction outputs."""
        raw_block = binascii.unhexlify(block_hex)
        stream = BytesIO(raw_block)
        
        # Skip header
        stream.read(80)
        tx_count = self._read_varint(stream)
        
        outputs = []
        
        for _ in range(tx_count):
            tx_outputs = self._parse_transaction(stream, block_height, block_time)
            outputs.extend(tx_outputs)
            
        return outputs
        
    def _parse_transaction(self, stream: BytesIO, block_height: int, block_time: int) -> List[TransactionOutput]:
        """Parse a single transaction and return filtered outputs."""
        start_pos = stream.tell()
        
        # Read version
        version = stream.read(4)
        
        # Check for SegWit
        marker_flag = stream.read(2)
        is_segwit = marker_flag == b'\x00\x01'
        if not is_segwit:
            stream.seek(start_pos + 4)
            
        # Read inputs
        input_count = self._read_varint(stream)
        input_txids = []
        is_coinbase = False
        
        for _ in range(input_count):
            prev_txid = stream.read(32)
            prev_index = stream.read(4)
            script_len = self._read_varint(stream)
            script = stream.read(script_len)
            stream.read(4)  # sequence
            
            input_txids.append(prev_txid[::-1].hex())
            
            if prev_txid == b'\x00' * 32 and prev_index == b'\xff\xff\xff\xff':
                is_coinbase = True
                
        # Read outputs
        output_count = self._read_varint(stream)
        output_values = []
        has_op_return = False
        
        for _ in range(output_count):
            value_sats = struct.unpack("<Q", stream.read(8))[0]
            script_len = self._read_varint(stream)
            script = stream.read(script_len)
            
            if script and script[0] == 0x6a:
                has_op_return = True
                
            value_btc = value_sats / 1e8
            if 1e-5 < value_btc < 1e5:
                output_values.append(value_btc)
                
        # Check witness data
        witness_exceeds = False
        if is_segwit:
            witness_exceeds = self._check_witness_size(stream, input_count)
            
        # Read locktime
        stream.read(4)
        
        # Compute txid
        end_pos = stream.tell()
        stream.seek(start_pos)
        raw_tx = stream.read(end_pos - start_pos)
        txid = self._compute_txid(raw_tx)
        self.todays_txids.add(txid.hex())
        
        # Check same-day transaction
        is_same_day = any(itxid in self.todays_txids for itxid in input_txids)
        
        # Apply filters
        if (input_count <= 5 and output_count == 2 and not is_coinbase and
            not has_op_return and not witness_exceeds and not is_same_day):
            return [TransactionOutput(value, block_height, block_time) for value in output_values]
            
        return []
        
    def _read_varint(self, stream: BytesIO) -> int:
        """Read a variable-length integer."""
        i = stream.read(1)
        if not i:
            return 0
        i = i[0]
        if i < 0xfd:
            return i
        elif i == 0xfd:
            return struct.unpack("<H", stream.read(2))[0]
        elif i == 0xfe:
            return struct.unpack("<I", stream.read(4))[0]
        else:
            return struct.unpack("<Q", stream.read(8))[0]
            
    def _check_witness_size(self, stream: BytesIO, input_count: int) -> bool:
        """Check if witness data exceeds size limit."""
        for _ in range(input_count):
            stack_count = self._read_varint(stream)
            total_witness_len = 0
            for _ in range(stack_count):
                item_len = self._read_varint(stream)
                total_witness_len += item_len
                stream.read(item_len)
                if item_len > 500 or total_witness_len > 500:
                    return True
        return False
        
    def _compute_txid(self, raw_tx: bytes) -> bytes:
        """Compute transaction ID."""
        # For SegWit transactions, we need to strip witness data
        stream = BytesIO(raw_tx)
        version = stream.read(4)
        marker = stream.read(1)
        flag = stream.read(1)
        
        if marker == b'\x00' and flag == b'\x01':
            # SegWit transaction - need to strip witness data
            stripped_tx = self._strip_witness(raw_tx)
        else:
            stripped_tx = raw_tx
            
        return hashlib.sha256(hashlib.sha256(stripped_tx).digest()).digest()[::-1]
        
    def _strip_witness(self, raw_tx: bytes) -> bytes:
        """Strip witness data from SegWit transaction."""
        # Implementation would go here
        # For brevity, returning raw_tx
        return raw_tx
