import pytest
from unittest.mock import Mock
from bitcoin_analyzer.analysis.transactions import *

class TestTransactionFilters:
    def test_input_count_filter(self):
        filter_obj = InputCountFilter(max_inputs=2)
        
        tx_pass = {"vin": [{"txid": "abc"}, {"txid": "def"}]}
        tx_fail = {"vin": [{"txid": "abc"}, {"txid": "def"}, {"txid": "ghi"}]}
        
        assert filter_obj.should_include(tx_pass, 100, 1000) == True
        assert filter_obj.should_include(tx_fail, 100, 1000) == False

    def test_coinbase_filter(self):
        filter_obj = CoinbaseFilter()
        
        tx_coinbase = {"vin": [{"coinbase": "01000000010000000000000000"}]}
        tx_normal = {"vin": [{"txid": "abc", "vout": 0}]}
        
        assert filter_obj.should_include(tx_coinbase, 100, 1000) == False
        assert filter_obj.should_include(tx_normal, 100, 1000) == True

    def test_op_return_filter(self):
        filter_obj = OpReturnFilter()
        
        tx_op_return = {
            "vout": [{
                "scriptPubKey": {"type": "nulldata", "asm": "OP_RETURN 48656c6c6f"}
            }]
        }
        tx_normal = {
            "vout": [{
                "scriptPubKey": {"type": "pubkeyhash", "asm": "OP_DUP OP_HASH160..."}
            }]
        }
        
        assert filter_obj.should_include(tx_op_return, 100, 1000) == False
        assert filter_obj.should_include(tx_normal, 100, 1000) == True


class TestTransactionParser:
    def test_filter_chaining(self):
        mock_rpc = Mock()
        parser = TransactionParser(mock_rpc)
        
        parser.add_filter(InputCountFilter(5)).add_filter(CoinbaseFilter())
        
        assert len(parser.filters) == 2
        assert isinstance(parser.filters[0], InputCountFilter)
        assert isinstance(parser.filters[1], CoinbaseFilter)

    def test_filter_summary(self):
        mock_rpc = Mock()
        parser = TransactionParser(mock_rpc)
        
        parser.add_filters(InputCountFilter(3), CoinbaseFilter())
        summary = parser.get_filter_summary()
        
        assert "InputCount<=3" in summary
        assert "NoCoinbase" in summary