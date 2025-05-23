import http.client
import json
import base64
import os
from typing import Any, List, Optional, Tuple
from .exceptions import RPCConnectionError, RPCAuthenticationError

class BitcoinRPCClient:
    """Bitcoin RPC client wrapper for communicating with a Bitcoin node."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8332, 
                 user: Optional[str] = None, password: Optional[str] = None,
                 cookie_path: Optional[str] = None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.cookie_path = cookie_path
        
    def __repr__(self):
        return json.dumps({
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "cookie_path": self.cookie_path
        })
        
    def _get_auth_credentials(self) -> Tuple[str, str]:
        """Get RPC authentication credentials from config or cookie file."""
        if self.user and self.password:
            return self.user, self.password
            
        if self.cookie_path and os.path.exists(self.cookie_path):
            try:
                with open(self.cookie_path, "r") as f:
                    cookie = f.read().strip()
                    return cookie.split(":", 1)
            except Exception as e:
                raise RPCAuthenticationError(f"Error reading .cookie file: {e}")
                
        raise RPCAuthenticationError("No RPC credentials available")
        
    def call(self, method: str, params: List[Any] = None) -> Any:
        """Make an RPC call to the Bitcoin node."""
        if params is None:
            params = []
            
        # Get credentials
        rpc_user, rpc_pass = self._get_auth_credentials()
        
        # Prepare JSON-RPC payload
        payload = json.dumps({
            "jsonrpc": "1.0",
            "id": "bitcoin-analyzer",
            "method": method,
            "params": params
        })
        
        # Basic auth header
        auth_header = base64.b64encode(f"{rpc_user}:{rpc_pass}".encode()).decode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_header}"
        }

        try:
            conn = http.client.HTTPConnection(self.host, self.port)
            conn.request("POST", "/", payload, headers)
            response = conn.getresponse()
            
            if response.status != 200:
                raise RPCConnectionError(f"HTTP error {response.status} {response.reason}")
                
            raw_data = response.read()
            conn.close()
            
            # Parse response
            parsed = json.loads(raw_data)
            if parsed.get("error"):
                raise RPCConnectionError(f"RPC error: {parsed['error']}")
                
            return parsed["result"]
            
        except Exception as e:
            if isinstance(e, (RPCConnectionError, RPCAuthenticationError)):
                raise
            raise RPCConnectionError(f"Connection failed: {e}")
