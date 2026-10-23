from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import logging
from datetime import datetime

from services.wallet_service import WalletService
from services.blockchain_service import BlockchainService
from services.cache_service import cache
from models.database import get_db, Wallet

logger = logging.getLogger(__name__)
router = APIRouter()

class WalletAnalysisResponse(BaseModel):
    address: str
    risk_score: float
    risk_level: str
    transaction_count: int
    total_value_in: float
    total_value_out: float
    total_fees_paid: Optional[float] = 0.0
    current_balance: Optional[float] = 0.0
    days_active: int
    unique_counterparties: int
    last_analysis: str
    blockchain_fetched: Optional[bool] = False
    
    class Config:
        from_attributes = True

class WalletWatchRequest(BaseModel):
    address: str
    name: Optional[str] = None

wallet_service = WalletService()
blockchain_service = BlockchainService()

@router.get("/{address}", response_model=WalletAnalysisResponse)
async def analyze_wallet(
    address: str,
    db: Session = Depends(get_db)
):
    """Get comprehensive wallet analysis"""
    try:
        address = address.lower()
        
        # Always fetch fresh blockchain data for real-time analysis
        logger.info(f"Fetching fresh blockchain data for wallet: {address}")
        
        # Fetch real-time data from blockchain
        wallet_data = await blockchain_service.fetch_wallet_data(address)
        
        # Log raw blockchain data for debugging
        logger.info(f"Raw blockchain data for {address}:")
        logger.info(f"  Balance: {wallet_data.get('balance', 0)} ETH")
        logger.info(f"  Transaction count: {wallet_data.get('transaction_count', 0)}")
        logger.info(f"  Fetched transactions: {len(wallet_data.get('transactions', []))}")
        
        if wallet_data.get('transactions'):
            sample_txs = wallet_data['transactions'][:3]
            for i, tx in enumerate(sample_txs):
                logger.info(f"  Sample TX {i+1}: {tx.get('hash', 'No hash')} | Value: {tx.get('value', 0)} ETH | From: {tx.get('from', 'Unknown')[:10]}... | To: {tx.get('to', 'Unknown')[:10]}...")
        
        # Check if wallet exists in DB for historical tracking
        wallet = db.query(Wallet).filter(Wallet.address == address).first()
        
        if not wallet:
            # Create new wallet entry
            wallet = await wallet_service.create_wallet(wallet_data, db)
        else:
            # Always update with fresh blockchain data
            wallet = await wallet_service.update_wallet(wallet, wallet_data, db)
        
        # Calculate unique counterparties from fresh blockchain data
        transactions = wallet_data.get('transactions', [])
        unique_addresses = set()
        
        for tx in transactions:
            if tx.get('from') and tx.get('from').lower() != address:
                unique_addresses.add(tx.get('from').lower())
            if tx.get('to') and tx.get('to').lower() != address:
                unique_addresses.add(tx.get('to').lower())
        
        unique_counterparties = len(unique_addresses)
        
        # Use wallet database values as single source of truth
        response_data = {
            "address": address,
            "risk_score": wallet.risk_score or 0.0,
            "risk_level": wallet.risk_level or 'low',
            "transaction_count": wallet.transaction_count or 0,
            "total_value_in": float(wallet.total_value_in or 0),
            "total_value_out": float(wallet.total_value_out or 0),
            "total_fees_paid": float(wallet.total_fees_paid or 0),
            "current_balance": float(wallet_data.get('balance', 0)),
            "days_active": wallet.days_active or 1,
            "unique_counterparties": unique_counterparties,
            "last_analysis": datetime.now().isoformat(),
            "blockchain_fetched": True
        }
        
        return WalletAnalysisResponse(**response_data)
    except Exception as e:
        logger.error(f"Error analyzing wallet {address}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing wallet: {str(e)}")

@router.post("/watchlist")
async def add_to_watchlist(
    request: WalletWatchRequest,
    db: Session = Depends(get_db)
):
    """Add wallet to user watchlist"""
    # TODO: Implement with authentication
    return {"message": "Watchlist feature coming soon", "address": request.address}

@router.get("/")
async def get_wallets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get wallets with pagination and filtering"""
    query = db.query(Wallet)
    
    if risk_level:
        query = query.filter(Wallet.risk_level == risk_level)
    
    wallets = query.offset(skip).limit(limit).all()
    
    results = []
    for w in wallets:
        unique_counterparties = len(set([
            tx.to_address if tx.from_address == w.address else tx.from_address
            for tx in w.transactions
            if tx.to_address and tx.from_address
        ]))
        results.append(WalletAnalysisResponse(
            address=w.address,
            risk_score=w.risk_score or 0.0,
            risk_level=w.risk_level or 'low',
            transaction_count=w.transaction_count or 0,
            total_value_in=float(w.total_value_in or 0),
            total_value_out=float(w.total_value_out or 0),
            total_fees_paid=float(w.total_fees_paid or 0),
            days_active=w.days_active or 1,
            unique_counterparties=unique_counterparties,
            last_analysis=w.updated_at.isoformat() if w.updated_at else datetime.now().isoformat()
        ))
    
    return results

class DeFiAnalyticsResponse(BaseModel):
    address: str
    total_positions: int
    protocols_used: list[str]
    total_liquidity_provided: float
    total_supplied: float
    total_borrowed: float
    health_factor: float
    leverage_ratio: float
    protocol_diversification: int
    defi_risk_factors: list[str]
    positions: list[dict]
    
@router.get("/{address}/defi", response_model=DeFiAnalyticsResponse)
async def get_defi_analytics(address: str):
    """Get DeFi analytics for a wallet using The Graph Protocol"""
    try:
        address = address.lower()
        
        # Check cache first
        cache_key = f"defi_analytics:{address}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached DeFi data for {address}")
            return DeFiAnalyticsResponse(address=address, **cached_data)
        
        # Fetch fresh DeFi data
        logger.info(f"Fetching DeFi analytics for wallet: {address}")
        defi_data = await wallet_service.get_defi_analytics(address)
        
        # Cache for 5 minutes
        cache.set(cache_key, defi_data, ttl=300)
        
        response_data = DeFiAnalyticsResponse(
            address=address,
            **defi_data
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error getting DeFi analytics for {address}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get DeFi analytics: {str(e)}"
        )
