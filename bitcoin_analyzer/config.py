import os
from configobj import ConfigObj
import platform
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class BitcoinConfig:
    """Bitcoin node configuration."""
    data_dir: str
    blocks_dir: str
    rpc_host: str = "127.0.0.1"
    rpc_port: int = 8332
    rpc_user: Optional[str] = None
    rpc_password: Optional[str] = None
    cookie_path: Optional[str] = None

def get_default_bitcoin_dir() -> str:
    """Get the default Bitcoin data directory for the current platform."""
    system = platform.system()
    if system == "Darwin":  # macOS
        return os.path.expanduser("~/Library/Application Support/Bitcoin")
    elif system == "Windows":
        return os.path.join(os.environ.get("APPDATA", ""), "Bitcoin")
    else:  # Linux or others
        return os.path.expanduser("~/.bitcoin")

# def parse_bitcoin_conf(conf_path: str) -> Dict[str, str]:
#     """Parse bitcoin.conf file and return settings as a dictionary."""
#     settings = {}
#     with open(conf_path, 'r') as f:
#         for line in f:
#             line = line.strip()
#             if not line or line.startswith("#"):
#                 continue
#             if "=" in line:
#                 key, value = line.split("=", 1)
#                 settings[key.strip()] = value.strip().strip('"')
#     return settings

def load_bitcoin_config(data_dir: Optional[str] = None) -> BitcoinConfig:
    """Load Bitcoin configuration from bitcoin.conf file."""
    if data_dir is None:
        data_dir = get_default_bitcoin_dir()
        
    # Look for bitcoin.conf or bitcoin_rw.conf
    conf_path = None
    for fname in ["bitcoin.conf", "bitcoin_rw.conf"]:
        path = os.path.join(data_dir, fname)
        if os.path.exists(path):
            conf_path = path
            break
            
    if not conf_path:
        raise FileNotFoundError(f"No bitcoin.conf found in {data_dir}")
        
    # Parse config
    # settings = parse_bitcoin_conf(conf_path)
    settings = ConfigObj(conf_path)
    
    # Build config object
    return BitcoinConfig(
        data_dir=data_dir,
        blocks_dir=os.path.expanduser(
            settings.get("blocksdir", os.path.join(data_dir, "blocks"))
        ),
        rpc_host=settings.get("rpcconnect", "127.0.0.1"),
        rpc_port=int(settings.get("rpcport", "8332")),
        rpc_user=settings.get("rpcuser"),
        rpc_password=settings.get("rpcpassword"),
        cookie_path=settings.get("rpccookiefile", os.path.join(data_dir, ".cookie"))
    )