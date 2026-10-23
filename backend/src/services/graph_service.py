import aiohttp
import asyncio
from typing import Dict, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

class GraphService:
    def __init__(self):
        self.api_key = os.getenv("THE_GRAPH_API_KEY")
        self.base_url = "https://gateway.thegraph.com/api"
        
                # Subgraph deployment IDs - verified working endpoints
        self.subgraphs = {
            "uniswap_v3": "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV",  # Working ✅
            "aave_v3": "JCNWRypm7FYwV8fx5HhzZPSFaMxgkPuw4TnR3Gpi81zk",     # Aave V3 
            "compound_v3": "AwoxEZbiWLvv6e3QdvdMZw4WDURdGbvPfHmZRc8Dpfz9"  # Compound V3
        }
    
    def _get_subgraph_url(self, subgraph_name: str) -> str:
        """Get the full URL for a subgraph"""
        if not self.api_key or self.api_key == "your_key" or self.api_key == "your_key_here":
            logger.warning(f"The Graph API key not configured. Current key: {self.api_key}")
            raise ValueError("The Graph API key not configured")
        
        # All subgraphs use The Graph Network decentralized endpoints
            
        subgraph_id = self.subgraphs.get(subgraph_name)
        if not subgraph_id:
            raise ValueError(f"Unknown subgraph: {subgraph_name}")
            
        return f"{self.base_url}/{self.api_key}/subgraphs/id/{subgraph_id}"
    
    async def query_subgraph(self, subgraph_name: str, query: str) -> Dict:
        """Execute a GraphQL query against a subgraph"""
        try:
            url = self._get_subgraph_url(subgraph_name)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={"query": query},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Graph API error: {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Error querying The Graph: {str(e)}")
            return {}
    
    async def get_wallet_defi_positions(self, wallet_address: str) -> List[Dict]:
        """Get DeFi positions for a wallet across multiple protocols"""
        positions = []
        
        # Check if API key is configured
        if not self.api_key or self.api_key in ["your_key", "your_key_here"]:
            logger.warning(f"The Graph API key not configured. Returning empty positions.")
            return []
        
        # Query Uniswap V3 positions
        uniswap_query = f"""
        {{
          positions(where: {{owner: "{wallet_address.lower()}"}}, first: 50) {{
            id
            liquidity
            depositedToken0
            depositedToken1
            withdrawnToken0
            withdrawnToken1
            collectedFeesToken0
            collectedFeesToken1
            pool {{
              token0 {{
                symbol
                name
                decimals
              }}
              token1 {{
                symbol
                name
                decimals
              }}
              feeTier
              sqrtPrice
              totalValueLockedUSD
            }}
            tickLower {{
              tickIdx
            }}
            tickUpper {{
              tickIdx
            }}
          }}
        }}
        """
        
        try:
            logger.info(f"Querying Uniswap V3 for wallet {wallet_address}")
            uniswap_data = await self.query_subgraph("uniswap_v3", uniswap_query)
            logger.info(f"Uniswap V3 response: {uniswap_data}")
            if uniswap_data and uniswap_data.get("data", {}).get("positions"):
                for position in uniswap_data["data"]["positions"]:
                    liquidity = float(position.get("liquidity", 0))
                    
                    # Calculate meaningful amounts - use deposited amounts, fees, or withdrawals to determine activity
                    deposited0 = float(position.get("depositedToken0", 0))
                    deposited1 = float(position.get("depositedToken1", 0))
                    fees0 = float(position.get("collectedFeesToken0", 0))
                    fees1 = float(position.get("collectedFeesToken1", 0))
                    withdrawn0 = float(position.get("withdrawnToken0", 0))
                    withdrawn1 = float(position.get("withdrawnToken1", 0))
                    
                    # Normalize by decimals
                    decimals0 = int(position["pool"]["token0"]["decimals"])
                    decimals1 = int(position["pool"]["token1"]["decimals"])
                    
                    deposited0_norm = deposited0 / (10 ** decimals0)
                    deposited1_norm = deposited1 / (10 ** decimals1)
                    fees0_norm = fees0 / (10 ** decimals0)
                    fees1_norm = fees1 / (10 ** decimals1)
                    withdrawn0_norm = withdrawn0 / (10 ** decimals0)
                    withdrawn1_norm = withdrawn1 / (10 ** decimals1)
                    
                    # Consider a position meaningful if it has significant activity (deposits, fees, or current liquidity)
                    total_activity0 = deposited0_norm + fees0_norm + withdrawn0_norm
                    total_activity1 = deposited1_norm + fees1_norm + withdrawn1_norm
                    
                    logger.info(f"Position {position['id']}: liquidity={liquidity}, total_activity0={total_activity0:.2f}, total_activity1={total_activity1:.2f}")
                    
                    # Include if active liquidity OR significant historical activity (>$1 equivalent to avoid micro-dust)
                    if (liquidity > 0 or total_activity0 > 1.0 or total_activity1 > 0.001):
                        token0 = position["pool"]["token0"]
                        token1 = position["pool"]["token1"]
                        
                        positions.append({
                            "protocol": "Uniswap V3",
                            "type": "liquidity_pool",
                            "position_id": position["id"],
                            "liquidity": liquidity,
                            "tokens": [token0["symbol"], token1["symbol"]],
                            "token_names": [token0.get("name", token0["symbol"]), token1.get("name", token1["symbol"])],
                            "fee_tier": position["pool"]["feeTier"],
                            "deposited_token0": deposited0_norm,
                            "deposited_token1": deposited1_norm,
                            "withdrawn_token0": float(position.get("withdrawnToken0", 0)) / (10 ** int(token0["decimals"])),
                            "withdrawn_token1": float(position.get("withdrawnToken1", 0)) / (10 ** int(token1["decimals"])),
                            "fees_token0": float(position.get("collectedFeesToken0", 0)) / (10 ** int(token0["decimals"])),
                            "fees_token1": float(position.get("collectedFeesToken1", 0)) / (10 ** int(token1["decimals"])),
                            "tick_lower": position.get("tickLower", {}).get("tickIdx"),
                            "tick_upper": position.get("tickUpper", {}).get("tickIdx"),
                            "pool_tvl_usd": float(position["pool"].get("totalValueLockedUSD", 0)),
                            "active": liquidity > 0
                        })
        except Exception as e:
            logger.warning(f"Failed to query Uniswap V3 data: {str(e)}")
        
        # Query Aave V3 positions - try different schema options
        aave_query = f"""
        {{
          accounts(where: {{id: "{wallet_address.lower()}"}}) {{
            id
            positions {{
              balance
              asset {{
                symbol
                name
                decimals
              }}
              side
            }}
          }}
        }}
        """
        
        # Query Aave V3 positions
        try:
            logger.info(f"Querying Aave V3 for wallet {wallet_address}")
            aave_data = await self.query_subgraph("aave_v3", aave_query)
            logger.info(f"Aave V3 response: {aave_data}")
            
            if aave_data and aave_data.get("data", {}).get("accounts"):
                accounts = aave_data["data"]["accounts"]
                if accounts and len(accounts) > 0:
                    positions_data = accounts[0].get("positions", [])
                    logger.info(f"Found {len(positions_data)} Aave positions")
                    for position in positions_data:
                        balance = float(position.get("balance", 0))
                        if balance > 0:  # Only include positions with balance
                            asset = position["asset"]
                            decimals = int(asset["decimals"])
                            side = position.get("side", "").lower()
                            
                            # Determine if it's supplied or borrowed
                            supplied = balance / (10 ** decimals) if side == "lender" else 0
                            borrowed = balance / (10 ** decimals) if side == "borrower" else 0
                            
                            if supplied > 0 or borrowed > 0:
                                positions.append({
                                    "protocol": "Aave V3",
                                    "type": "lending",
                                    "token": asset["symbol"],
                                    "token_name": asset["name"],
                                    "supplied": supplied,
                                    "borrowed": borrowed
                                })
        except Exception as e:
            logger.warning(f"Failed to query Aave V3 data: {str(e)}")
            
        # Uniswap V2 removed per user request
            
        # Query Compound V3 positions
        try:
            logger.info(f"Querying Compound V3 for wallet {wallet_address}")
            compound_v3_query = f"""
            {{
              accounts(where: {{id: "{wallet_address.lower()}"}}) {{
                id
                positions {{
                  balance
                  market {{
                    inputToken {{
                      symbol
                      name
                      decimals
                    }}
                  }}
                }}
              }}
            }}
            """
            
            compound_data = await self.query_subgraph("compound_v3", compound_v3_query)
            logger.info(f"Compound V3 response: {compound_data}")
            
            if compound_data and compound_data.get("data"):
                data = compound_data["data"]
                if data.get("accounts"):
                    logger.info(f"Found {len(data['accounts'])} Compound accounts")
                    for account in data["accounts"]:
                        for position in account.get("positions", []):
                            balance = float(position.get("balance", 0))
                            
                            if balance != 0:  # Can be positive (supplied) or negative (borrowed)
                                market = position["market"]
                                input_token = market["inputToken"]
                                decimals = int(input_token["decimals"])
                                
                                # Positive balance = supplied, negative = borrowed
                                supplied = max(0, balance / (10 ** decimals))
                                borrowed = max(0, -balance / (10 ** decimals))
                                
                                if supplied > 0 or borrowed > 0:
                                    positions.append({
                                        "protocol": "Compound V3",
                                        "type": "lending",
                                        "token": input_token["symbol"],
                                        "token_name": input_token["name"],
                                        "supplied": supplied,
                                        "borrowed": borrowed
                                    })
                else:
                    logger.info(f"Compound V3 data structure: {list(data.keys()) if data else 'empty'}")
        except Exception as e:
            logger.warning(f"Failed to query Compound V3 data: {str(e)}")
        
        logger.info("Queried Uniswap V3, Aave V3, and Compound V3 protocols")
            
        # Filter out positions with values below dust threshold
        dust_threshold = 0.00001
        meaningful_positions = []
        
        for pos in positions:
            if pos["protocol"] == "Uniswap V3":
                # For LP positions, check if there's meaningful liquidity (using correct field names)
                deposited_token0 = pos.get("deposited_token0", 0)
                deposited_token1 = pos.get("deposited_token1", 0)
                fees_token0 = pos.get("fees_token0", 0)
                fees_token1 = pos.get("fees_token1", 0)
                
                # Consider position meaningful if there's significant activity
                total_value0 = deposited_token0 + fees_token0
                total_value1 = deposited_token1 + fees_token1
                
                if total_value0 > dust_threshold or total_value1 > dust_threshold or pos.get("liquidity", 0) > 0:
                    meaningful_positions.append(pos)
            else:
                # For lending positions
                supplied = pos.get("supplied", 0)
                borrowed = pos.get("borrowed", 0) + pos.get("borrowed_stable", 0) + pos.get("borrowed_variable", 0)
                
                if supplied > dust_threshold or borrowed > dust_threshold:
                    meaningful_positions.append(pos)
        
        positions = meaningful_positions
        logger.info(f"Found {len(positions)} meaningful positions after dust filtering")
        
        logger.info(f"Total DeFi positions found: {len(positions)} across {len(set(p['protocol'] for p in positions))} protocols")
        
        return positions
    
    async def get_token_transfers(self, wallet_address: str, limit: int = 100) -> List[Dict]:
        """Get token transfer history for a wallet"""
        # This would require a custom subgraph or token-specific subgraphs
        # For now, return empty list
        return []
    
    async def get_defi_analytics(self, wallet_address: str) -> Dict:
        """Get comprehensive DeFi analytics for a wallet"""
        try:
            logger.info(f"Getting DeFi analytics for wallet: {wallet_address}")
            logger.info(f"Graph API key status: {'CONFIGURED' if self.api_key and self.api_key not in ['your_key', 'your_key_here'] else 'NOT CONFIGURED'}")
            
            positions = await self.get_wallet_defi_positions(wallet_address)
            
            # Calculate totals properly
            total_liquidity = 0
            total_supplied = 0
            total_borrowed = 0
            
            for p in positions:
                if p["type"] == "liquidity_pool":
                    # For liquidity pools, count deposited amounts as supplied liquidity
                    total_liquidity += p.get("liquidity", 0)
                    total_supplied += p.get("deposited_token0", 0) + p.get("deposited_token1", 0)
                elif p["type"] == "lending":
                    # For lending protocols
                    total_supplied += p.get("supplied", 0)
                    total_borrowed += p.get("borrowed_stable", 0) + p.get("borrowed_variable", 0)
                    total_borrowed += p.get("borrowed", 0)  # Compound style
            
            protocols_used = list(set(p["protocol"] for p in positions))
            
            # Calculate additional metrics
            active_positions = [p for p in positions if p.get("active", True) or p.get("liquidity", 0) > 0]
            protocol_diversification = len(protocols_used)
            
            # Risk factors
            defi_risk_factors = []
            if total_borrowed > 0:
                if (total_supplied / total_borrowed) < 1.5:
                    defi_risk_factors.append("Low collateral ratio")
            if len(positions) > 10:
                defi_risk_factors.append("High position count")
            if protocol_diversification == 1:
                defi_risk_factors.append("Single protocol exposure")
                
            leverage_ratio = (total_borrowed / total_supplied) if total_supplied > 0 else 0
            
            return {
                "total_positions": len(positions),
                "protocols_used": protocols_used,
                "total_liquidity_provided": total_liquidity,
                "total_supplied": total_supplied,
                "total_borrowed": total_borrowed,
                "health_factor": (total_supplied / total_borrowed) if total_borrowed > 0 else 999.99,
                "leverage_ratio": leverage_ratio,
                "protocol_diversification": protocol_diversification,
                "defi_risk_factors": defi_risk_factors,
                "positions": positions
            }
            
        except Exception as e:
            logger.error(f"Error getting DeFi analytics: {str(e)}")
            return {
                "total_positions": 0,
                "protocols_used": [],
                "total_liquidity_provided": 0.0,
                "total_supplied": 0.0,
                "total_borrowed": 0.0,
                "health_factor": 999.99,
                "leverage_ratio": 0.0,
                "protocol_diversification": 0,
                "defi_risk_factors": [],
                "positions": []
            }