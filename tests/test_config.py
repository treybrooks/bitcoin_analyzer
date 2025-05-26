import pytest
from unittest.mock import patch, mock_open
from bitcoin_analyzer.config import load_bitcoin_config, get_default_bitcoin_dir

class TestConfig:
    @patch('platform.system')
    def test_get_default_bitcoin_dir_macos(self, mock_system):
        mock_system.return_value = "Darwin"
        result = get_default_bitcoin_dir()
        assert "Library/Application Support/Bitcoin" in result

    @patch('platform.system')
    def test_get_default_bitcoin_dir_windows(self, mock_system):
        mock_system.return_value = "Windows"
        with patch.dict('os.environ', {'APPDATA': 'C:\\Users\\Test\\AppData\\Roaming'}):
            result = get_default_bitcoin_dir()
            assert "Bitcoin" in result

    @patch('os.path.exists')
    @patch('bitcoin_analyzer.config.ConfigObj')
    def test_load_bitcoin_config(self, mock_configobj, mock_exists):
        mock_exists.return_value = True
        mock_config = {
            'rpcuser': 'testuser',
            'rpcpassword': 'testpass',
            'rpcport': '8332'
        }
        mock_configobj.return_value = mock_config
        
        config = load_bitcoin_config("/test/path")
        
        assert config.rpc_user == 'testuser'
        assert config.rpc_password == 'testpass'
        assert config.rpc_port == 8332