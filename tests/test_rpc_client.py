import pytest
from unittest.mock import Mock, patch
from bitcoin_analyzer.rpc.client import BitcoinRPCClient
from bitcoin_analyzer.rpc.exceptions import RPCConnectionError, RPCAuthenticationError

class TestBitcoinRPCClient:
    def test_init(self):
        client = BitcoinRPCClient("localhost", 8332, "user", "pass")
        assert client.host == "localhost"
        assert client.port == 8332
        assert client.user == "user"
        assert client.password == "pass"

    @patch('bitcoin_analyzer.rpc.client.http.client.HTTPConnection')
    def test_successful_call(self, mock_conn_class):
        # Mock the HTTP connection
        mock_conn = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"result": 12345, "error": null}'
        mock_conn.getresponse.return_value = mock_response
        mock_conn_class.return_value = mock_conn
        
        client = BitcoinRPCClient(user="test", password="test")
        result = client.call("getblockcount")
        
        assert result == 12345

    def test_auth_credentials_user_pass(self):
        client = BitcoinRPCClient(user="testuser", password="testpass")
        user, password = client._get_auth_credentials()
        assert user == "testuser"
        assert password == "testpass"

    @patch('builtins.open')
    @patch('os.path.exists')
    def test_auth_credentials_cookie(self, mock_exists, mock_open):
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "cookieuser:cookiepass"
        
        client = BitcoinRPCClient(cookie_path="/path/to/.cookie")
        user, password = client._get_auth_credentials()
        
        assert user == "cookieuser"
        assert password == "cookiepass"