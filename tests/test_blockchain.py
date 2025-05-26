import pytest
from unittest.mock import Mock
from datetime import datetime, timezone
from bitcoin_analyzer.analysis.blockchain import BlockchainAnalyzer

class TestBlockchainAnalyzer:
    def test_init(self):
        mock_rpc = Mock()
        analyzer = BlockchainAnalyzer(mock_rpc)
        assert analyzer.rpc == mock_rpc

    def test_get_block_count(self):
        mock_rpc = Mock()
        mock_rpc.call.return_value = 800000
        
        analyzer = BlockchainAnalyzer(mock_rpc)
        result = analyzer.get_block_count()
        
        assert result == 800000
        mock_rpc.call.assert_called_once_with("getblockcount")

    def test_get_block_timehash(self):
        mock_rpc = Mock()
        mock_rpc.call.side_effect = [
            "block_hash_123",  # getblockhash result
            {"time": 1609459200, "hash": "block_hash_123"}  # getblockheader result
        ]
        
        analyzer = BlockchainAnalyzer(mock_rpc)
        time, hash_val = analyzer.get_block_timehash(123)
        
        assert time == 1609459200
        assert hash_val == "block_hash_123"