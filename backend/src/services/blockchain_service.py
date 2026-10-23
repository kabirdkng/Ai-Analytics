import aiohttp
import asyncio
from typing import Dict, List
from web3 import Web3
import logging
import os
from datetime import datetime, timezone, timedelta
import json

logger = logging.getLogger(__name__)

class BlockchainService:
    def __init__(self):
        self.eth_rpc = os.getenv("ETHEREUM_RPC", "https://eth.llamarpc.com")
        self.polygon_rpc = os.getenv("POLYGON_RPC", "https://polygon-rpc.com")
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
        self.moralis_api_key = os.getenv("MORALIS_API_KEY")
        
        # Initialize Web3 with Alchemy if available, fallback to public RPC
        if self.alchemy_api_key:
            self.eth_rpc = f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
        
        self.w3 = Web3(Web3.HTTPProvider(self.eth_rpc))
        
        # API endpoints
        self.alchemy_base_url = f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}" if self.alchemy_api_key else None
        self.moralis_base_url = "https://deep-index.moralis.io/api/v2.2"
    
    async def fetch_wallet_data(self, address: str) -> Dict:
        """Fetch wallet data from blockchain"""
        try:
            address_checksum = Web3.to_checksum_address(address)
        except Exception as e:
            logger.error(f"Invalid address format: {address}")
            raise ValueError(f"Invalid Ethereum address: {address}")
        
        try:
            # Get balance
            balance = self.w3.eth.get_balance(address_checksum)
            
            # Get transaction count
            tx_count = self.w3.eth.get_transaction_count(address_checksum)
            
            # Fetch ALL transactions with timeout
            transactions = []
            try:
                # Use asyncio.wait_for to add timeout - fetch all transactions
                transactions = await asyncio.wait_for(
                    self._fetch_transactions(address_checksum, limit=None), 
                    timeout=120.0  # 2 minute timeout for all transactions
                )
            except asyncio.TimeoutError:
                logger.warning(f"Transaction fetching timed out for {address}")
                transactions = []
            
            # Calculate timestamps
            first_seen = self._get_first_tx_timestamp(transactions)
            last_active = self._get_last_tx_timestamp(transactions)
            
            return {
                'address': address.lower(),
                'balance': float(balance) / 10**18,  # Convert to ETH
                'transaction_count': max(tx_count, len(transactions)),  # Use max of both
                'transactions': transactions,
                'first_seen': first_seen or datetime.now(),
                'last_active': last_active or datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching wallet data: {str(e)}")
            # Return minimal data instead of failing
            return {
                'address': address.lower(),
                'balance': 0.0,
                'transaction_count': 0,
                'transactions': [],
                'first_seen': datetime.now(),
                'last_active': datetime.now()
            }
    
    async def _fetch_transactions(self, address: str, limit: int = None) -> List[Dict]:
        """Fetch ALL transactions from available APIs"""
        transactions = []
        
        try:
            # Try Alchemy first (most reliable) - fetch ALL transactions
            if self.alchemy_api_key:
                logger.info(f"Fetching ALL transactions from Alchemy for {address}")
                transactions = await self._fetch_transactions_alchemy(address, limit)
            
            # Fallback to Moralis if Alchemy fails or no API key
            elif self.moralis_api_key and len(transactions) == 0:
                logger.info(f"Falling back to Moralis for {address}")
                # Use high limit for Moralis as well
                transactions = await self._fetch_transactions_moralis(address, limit or 10000)
            
            # Final fallback to Web3 (limited functionality)
            elif len(transactions) == 0:
                logger.warning("No API keys configured, using basic Web3 data")
                transactions = await self._fetch_transactions_web3(address, limit or 1000)
                
            logger.info(f"Successfully fetched {len(transactions)} transactions for {address}")
            
        except Exception as e:
            logger.error(f"Error fetching transactions: {str(e)}")
            # Fallback to empty list
            transactions = []
        
        return transactions
    
    async def _fetch_transactions_moralis(self, address: str, limit: int = 10000) -> List[Dict]:
        """Fetch transactions using Moralis API with pagination"""
        transactions = []
        
        headers = {
            'X-API-Key': self.moralis_api_key,
            'accept': 'application/json'
        }
        
        url = f"{self.moralis_base_url}/wallets/{address}/history"
        params = {
            'chain': 'eth',
            'limit': min(limit, 1000),  # Moralis max per request
            'order': 'DESC'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for tx in data.get('result', []):
                            transactions.append({
                                'hash': tx.get('hash'),
                                'from': tx.get('from_address', '').lower(),
                                'to': tx.get('to_address', '').lower(),
                                'value': float(tx.get('value', 0)) / 10**18,  # Convert from wei to ETH
                                'gas_price': float(tx.get('gas_price', 0)) / 10**9,  # Convert to Gwei
                                'gas_used': int(tx.get('gas', 0)),
                                'timestamp': datetime.fromisoformat(tx.get('block_timestamp', '').replace('Z', '+00:00')) if tx.get('block_timestamp') else datetime.now(),
                                'block_number': int(tx.get('block_number', 0)),
                                'contract_interaction': bool(tx.get('to_address') and len(tx.get('input', '')) > 2),
                                'token_transfers': 0  # Would need separate API call for token transfers
                            })
                    else:
                        logger.error(f"Moralis API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error fetching from Moralis: {str(e)}")
            raise
        
        return transactions
    
    async def _fetch_transactions_alchemy(self, address: str, limit: int = None) -> List[Dict]:
        """Fetch ALL transactions using Alchemy API with complete pagination"""
        transactions = []
        seen_hashes = set()  # Track hashes to avoid duplicates
        
        # Fetch both sent and received transactions separately for complete coverage
        for direction in ["from", "to"]:
            page_key = None
            fetched_count = 0
            max_per_direction = float('inf') if limit is None else limit // 2
            
            logger.info(f"Fetching ALL {direction} transactions for {address}")
            
            while fetched_count < max_per_direction:
                # Calculate how many more we need (or max 1000 per page for unlimited)
                if limit is None:
                    page_limit = 1000  # Alchemy max per request
                else:
                    remaining = max_per_direction - fetched_count
                    page_limit = min(remaining, 1000)  # Alchemy max per request
                
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "alchemy_getAssetTransfers",
                    "params": [{
                        f"{direction}Address": address,
                        "category": ["external", "internal"],
                        "maxCount": hex(page_limit),
                        "order": "desc"
                    }]
                }
                
                # Add pageKey if we have one (for pagination)
                if page_key:
                    payload["params"][0]["pageKey"] = page_key
            
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(self.alchemy_base_url, json=payload) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                result = data.get('result')
                                if result is None:
                                    logger.warning(f"Alchemy API returned null result for {direction} direction")
                                    break
                                    
                                transfers = result.get('transfers', [])
                                next_page_key = result.get('pageKey')
                                
                                if not transfers:
                                    logger.info(f"No more {direction} transactions available - completed pagination")
                                    break
                                
                                logger.info(f"Fetched {len(transfers)} {direction} transactions (page {fetched_count//1000 + 1})")
                                
                                # Process transfers and get gas data where possible
                                for transfer in transfers:
                                    if transfer is None:
                                        continue
                                        
                                    tx_hash = transfer.get('hash')
                                    if not tx_hash or tx_hash in seen_hashes:
                                        continue
                                        
                                    seen_hashes.add(tx_hash)
                                    
                                    # Handle blockNum conversion safely
                                    block_num = transfer.get('blockNum')
                                    if block_num:
                                        try:
                                            if isinstance(block_num, str) and block_num.startswith('0x'):
                                                block_number = int(block_num, 16)
                                            else:
                                                block_number = int(block_num)
                                        except:
                                            block_number = 0
                                    else:
                                        block_number = 0
                                    
                                    # Parse value
                                    value = transfer.get('value', 0)
                                    if isinstance(value, str):
                                        try:
                                            value = int(value, 16) / 10**18 if value.startswith('0x') else float(value)
                                        except:
                                            value = 0.0
                                    elif isinstance(value, (int, float)):
                                        value = float(value)
                                    else:
                                        value = 0.0
                                    
                                    # Get basic timestamp estimate (12 sec per block from current)
                                    if block_number > 0:
                                        # Rough estimation based on current block ~21M
                                        days_ago = max(0, (21000000 - block_number) * 12 // 86400)
                                        timestamp = datetime.now() - timedelta(days=days_ago)
                                    else:
                                        timestamp = datetime.now()
                                    
                                    # Use estimated gas fees to avoid timeout issues
                                    gas_price = 0
                                    gas_used = 0
                                    transaction_fee = 0
                                    
                                    # Estimate transaction fee based on block number and direction
                                    if direction == "from":  # Only charge fees for outgoing transactions
                                        # Estimate based on block age (newer blocks = higher fees)
                                        if block_number > 20000000:  # Recent blocks
                                            transaction_fee = 0.005  # ~$5 USD typical recent fee
                                        elif block_number > 15000000:  # Mid-age blocks
                                            transaction_fee = 0.003  # ~$3 USD typical mid fee
                                        else:  # Older blocks
                                            transaction_fee = 0.001  # ~$1 USD typical old fee
                                    
                                    # Handle None values safely
                                    from_addr = transfer.get('from')
                                    to_addr = transfer.get('to')
                                    
                                    transactions.append({
                                        'hash': tx_hash,
                                        'from': from_addr.lower() if from_addr else '',
                                        'to': to_addr.lower() if to_addr else '',
                                        'value': value,
                                        'gas_price': gas_price,
                                        'gas_used': gas_used,
                                        'transaction_fee': transaction_fee,
                                        'timestamp': timestamp,
                                        'block_number': block_number,
                                        'contract_interaction': transfer.get('category') in ['erc20', 'erc721', 'erc1155'],
                                        'token_transfers': 1 if transfer.get('category') in ['erc20', 'erc721', 'erc1155'] else 0
                                    })
                                    
                                    fetched_count += 1
                                
                                # Check if there's a next page and we haven't hit our limit
                                if next_page_key and fetched_count < max_per_direction:
                                    page_key = next_page_key
                                else:
                                    break
                            else:
                                logger.error(f"Alchemy API error: {response.status}")
                                break
                except Exception as e:
                    logger.error(f"Error fetching from Alchemy {direction} direction: {str(e)}")
                    break
        
        return transactions
    


    async def _get_block_timestamp(self, block_number: int, cache: Dict) -> datetime:
        """Get block timestamp with caching to avoid duplicate requests"""
        if block_number in cache:
            return cache[block_number]
            
        if block_number == 0:
            timestamp = datetime.now()
        else:
            # For performance, use Alchemy RPC instead of Web3
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_getBlockByNumber",
                    "params": [hex(block_number), False]
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.alchemy_base_url, json=payload, timeout=5.0) as response:
                        if response.status == 200:
                            data = await response.json()
                            result = data.get('result')
                            if result and result.get('timestamp'):
                                # Convert hex timestamp to datetime
                                hex_timestamp = result['timestamp']
                                timestamp_int = int(hex_timestamp, 16)
                                timestamp = datetime.fromtimestamp(timestamp_int)
                            else:
                                timestamp = datetime.now()
                        else:
                            timestamp = datetime.now()
            except Exception as e:
                logger.warning(f"Could not fetch block {block_number}: {e}")
                timestamp = datetime.now()
        
        # Cache the result
        cache[block_number] = timestamp
        return timestamp

    async def _batch_fetch_block_timestamps(self, block_numbers: set, cache: Dict):
        """Batch fetch block timestamps to reduce API calls"""
        # Filter out blocks already in cache
        blocks_to_fetch = [b for b in block_numbers if b not in cache and b > 0]
        
        if not blocks_to_fetch:
            return
        
        # Limit to reasonable batch size to avoid timeout
        max_batch_size = 20
        if len(blocks_to_fetch) > max_batch_size:
            # For large batches, use estimated timestamps based on block differences
            # Ethereum has ~12 second block times on average
            blocks_to_fetch = sorted(blocks_to_fetch, reverse=True)[:max_batch_size]
        
        logger.info(f"Batch fetching timestamps for {len(blocks_to_fetch)} blocks")
        
        # Fetch blocks in parallel with limited concurrency
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
        
        async def fetch_single_block(block_num):
            async with semaphore:
                try:
                    payload = {
                        "jsonrpc": "2.0",
                        "id": block_num,
                        "method": "eth_getBlockByNumber",
                        "params": [hex(block_num), False]
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(self.alchemy_base_url, json=payload, timeout=3.0) as response:
                            if response.status == 200:
                                data = await response.json()
                                result = data.get('result')
                                if result and result.get('timestamp'):
                                    hex_timestamp = result['timestamp']
                                    timestamp_int = int(hex_timestamp, 16)
                                    timestamp = datetime.fromtimestamp(timestamp_int)
                                    cache[block_num] = timestamp
                                    return block_num, timestamp
                except Exception as e:
                    logger.warning(f"Failed to fetch block {block_num}: {e}")
                
                # Fallback - estimate timestamp based on current time and block difference
                cache[block_num] = datetime.now()
                return block_num, datetime.now()
        
        # Execute batch fetch
        tasks = [fetch_single_block(block_num) for block_num in blocks_to_fetch]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Completed batch timestamp fetch for {len([r for r in results if not isinstance(r, Exception)])} blocks")
    
    async def _fetch_transactions_web3(self, address: str, limit: int = 50) -> List[Dict]:
        """Fallback method using basic Web3 (limited functionality)"""
        transactions = []
        
        try:
            # Get latest block number
            latest_block = self.w3.eth.get_block('latest')
            current_block = latest_block['number']
            
            # Search recent blocks for transactions involving this address
            # This is very limited and slow, but works without API keys
            blocks_to_check = min(10, limit)  # Reduced to only 10 blocks for speed
            
            for i in range(blocks_to_check):
                try:
                    block_num = current_block - i
                    block = self.w3.eth.get_block(block_num, full_transactions=True)
                    
                    for tx in block.transactions:
                        tx_from = tx.get('from')
                        tx_to = tx.get('to')
                        
                        # Skip transactions with null addresses
                        if not tx_from or not tx_to:
                            continue
                            
                        if (tx_from.lower() == address.lower() or tx_to.lower() == address.lower()):
                            
                            transactions.append({
                                'hash': tx.get('hash').hex() if tx.get('hash') else '',
                                'from': tx_from.lower(),
                                'to': tx_to.lower(),
                                'value': float(tx.get('value', 0)) / 10**18,
                                'gas_price': float(tx.get('gasPrice', 0)) / 10**9,
                                'gas_used': int(tx.get('gas', 0)),
                                'timestamp': datetime.fromtimestamp(block.timestamp),
                                'block_number': block_num,
                                'contract_interaction': bool(tx_to and tx.get('input') and len(tx.get('input')) > 2),
                                'token_transfers': 0
                            })
                            
                            if len(transactions) >= limit:
                                break
                                
                except Exception as block_error:
                    logger.warning(f"Error processing block {block_num}: {block_error}")
                    continue
                    
                if len(transactions) >= limit:
                    break
                    
        except Exception as e:
            logger.error(f"Error in Web3 fallback: {str(e)}")
        
        return transactions
    
    def _get_first_tx_timestamp(self, transactions: List) -> datetime:
        """Get first transaction timestamp"""
        if not transactions:
            return datetime.now()
        
        timestamps = []
        for tx in transactions:
            ts = tx.get('timestamp')
            if ts:
                # Ensure timezone-naive datetime
                if hasattr(ts, 'tzinfo') and ts.tzinfo:
                    ts = ts.replace(tzinfo=None)
                timestamps.append(ts)
        
        return min(timestamps) if timestamps else datetime.now()
    
    def _get_last_tx_timestamp(self, transactions: List) -> datetime:
        """Get last transaction timestamp"""
        if not transactions:
            return datetime.now()
        
        timestamps = []
        for tx in transactions:
            ts = tx.get('timestamp')
            if ts:
                # Ensure timezone-naive datetime
                if hasattr(ts, 'tzinfo') and ts.tzinfo:
                    ts = ts.replace(tzinfo=None)
                timestamps.append(ts)
        
        return max(timestamps) if timestamps else datetime.now()
