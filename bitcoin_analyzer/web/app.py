from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
from datetime import datetime

from ..config import load_bitcoin_config
from ..rpc.client import BitcoinRPCClient
from ..analysis.blockchain import BlockchainAnalyzer
from ..analysis.metrics import PriceEstimator
from ..analysis.transactions import TransactionParser

app = FastAPI(title="UTXOracle Local")

# Mount static files
app.mount("/static", StaticFiles(directory="bitcoin_analyzer/web/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="bitcoin_analyzer/web/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/analyze/{date}")
async def analyze_date(date: str):
    """Analyze Bitcoin price for a specific date."""
    # Parse date
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}
    
    # Load config and create RPC client
    config = load_bitcoin_config()
    rpc_client = BitcoinRPCClient(
        host=config.rpc_host,
        port=config.rpc_port,
        user=config.rpc_user,
        password=config.rpc_password,
        cookie_path=config.cookie_path
    )
    
    # Analyze blockchain
    analyzer = BlockchainAnalyzer(rpc_client)
    start_block, end_block, block_nums, block_hashes, block_times = analyzer.find_blocks_by_date(target_date)
    
    # Parse transactions and estimate price
    parser = TransactionParser()
    estimator = PriceEstimator()
    
    for i, block_hash in enumerate(block_hashes):
        block_hex = rpc_client.call("getblock", [block_hash, 0])
        outputs = parser.parse_block(block_hex, block_nums[i], block_times[i])
        
        for output in outputs:
            estimator.add_output(output.value_btc)
    
    # Get price estimate
    final_price, rough_price = estimator.estimate_price()
    
    return {
        "date": date,
        "price": int(final_price),
        "blocks_analyzed": len(block_hashes),
        "start_block": start_block,
        "end_block": end_block
    }

@app.get("/api/recent")
async def analyze_recent():
    """Analyze price from recent blocks."""
    # Similar implementation for recent blocks
    pass
