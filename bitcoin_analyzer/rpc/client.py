import http.client
import json
import asyncio
import aiohttp
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

class AsyncBitcoinRPCClient:
    """Async version of BitcoinRPCClient for concurrent requests."""
    
    def __init__(self, rpc_client, max_concurrent=10):
        self.rpc_client = rpc_client
        self.max_concurrent = max_concurrent
        self._session = None
        
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def call_async(self, method: str, params: List[Any] = None):
        """Make async RPC call."""
        if params is None:
            params = []
            
        payload = {
            "jsonrpc": "1.0",
            "id": "bitcoin-analyzer",
            "method": method,
            "params": params
        }
        
        # Use same auth as sync client
        rpc_user, rpc_pass = self.rpc_client._get_auth_credentials()
        auth = aiohttp.BasicAuth(rpc_user, rpc_pass)
        url = f"http://{self.rpc_client.host}:{self.rpc_client.port}"
        
        async with self._session.post(url, json=payload, auth=auth) as response:
            result = await response.json()
            if 'error' in result and result['error']:
                raise Exception(f"RPC Error: {result['error']}")
            return result['result']
    
    async def parse_blocks_batch(self, block_hashes: List[str], parser):
        """Parse multiple blocks concurrently while preserving order."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def parse_single_block(block_hash: str):
            async with semaphore:
                # Get block data async
                block = await self.call_async("getblock", [block_hash, 2])
                
                # Process block synchronously (reuse existing logic)
                outputs = []
                block_height = block['height']
                block_time = block['time']
                
                for tx in block['tx']:
                    parser.seen_txids.add(tx['txid'])
                    
                    if parser._passes_all_filters(tx, block_height, block_time):
                        tx_outputs = parser._extract_outputs(tx, block_height, block_time)
                        outputs.extend(tx_outputs)
                
                return block_hash, outputs
        
        # Start all tasks
        tasks = [parse_single_block(block_hash) for block_hash in block_hashes]
        results = await asyncio.gather(*tasks)
        
        # Create hash -> outputs mapping to preserve order
        hash_to_outputs = {block_hash: outputs for block_hash, outputs in results}
        
        # Return in original order
        return [hash_to_outputs.get(block_hash, []) for block_hash in block_hashes]