import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_rpc_client():
    """Fixture providing a mock RPC client."""
    mock_client = Mock()
    mock_client.call.return_value = {"result": "test"}
    return mock_client

@pytest.fixture
def sample_transaction():
    """Fixture providing a sample transaction for testing."""
    return {
        "txid": "test_txid_123",
        "vin": [
            {"txid": "prev_tx_1", "vout": 0},
            {"txid": "prev_tx_2", "vout": 1}
        ],
        "vout": [
            {"value": 0.001, "scriptPubKey": {"type": "pubkeyhash"}},
            {"value": 0.002, "scriptPubKey": {"type": "pubkeyhash"}}
        ]
    }

@pytest.fixture
def sample_block():
    """Fixture providing a sample block for testing."""
    return {
        "height": 800000,
        "time": 1609459200,
        "hash": "test_block_hash",
        "tx": []  # Will be populated as needed
    }