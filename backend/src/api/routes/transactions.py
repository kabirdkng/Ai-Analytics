from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from models.database import get_db, Transaction, Wallet

logger = logging.getLogger(__name__)
router = APIRouter()

class TransactionResponse(BaseModel):
    hash: str
    from_address: str
    to_address: str
    value: float
    gas_used: Optional[int] = None
    gas_price: Optional[float] = None
    block_number: Optional[int] = None
    timestamp: int
    status: str = "confirmed"
    
    class Config:
        from_attributes = True

@router.get("/wallet/{address}")
async def get_wallet_transactions(
    address: str,
    limit: int = Query(50, le=2000),
    db: Session = Depends(get_db)
):
    """Get transactions for a specific wallet"""
    try:
        address = address.lower()
        
        # Get transactions where wallet is either sender or receiver
        transactions = db.query(Transaction).filter(
            (Transaction.from_address == address) | (Transaction.to_address == address)
        ).order_by(Transaction.timestamp.desc()).limit(limit).all()
        
        results = []
        for tx in transactions:
            results.append(TransactionResponse(
                hash=tx.tx_hash,
                from_address=tx.from_address or "",
                to_address=tx.to_address or "",
                value=float(tx.value or 0),
                gas_used=getattr(tx, 'gas_used', None),
                gas_price=float(tx.gas_price or 0) if tx.gas_price else None,
                block_number=tx.block_number,
                timestamp=int(tx.timestamp.timestamp()) if tx.timestamp else int(datetime.now().timestamp()),
                status="confirmed"  # Default status
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error fetching transactions for wallet {address}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")

@router.get("/")
async def get_recent_transactions(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """Get recent transactions"""
    try:
        transactions = db.query(Transaction).order_by(
            Transaction.timestamp.desc()
        ).limit(limit).all()
        
        results = []
        for tx in transactions:
            results.append(TransactionResponse(
                hash=tx.tx_hash,
                from_address=tx.from_address or "",
                to_address=tx.to_address or "",
                value=float(tx.value or 0),
                gas_used=getattr(tx, 'gas_used', None),
                gas_price=float(tx.gas_price or 0) if tx.gas_price else None,
                block_number=tx.block_number,
                timestamp=int(tx.timestamp.timestamp()) if tx.timestamp else int(datetime.now().timestamp()),
                status="confirmed"
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error fetching recent transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")

@router.get("/{tx_hash}")
async def get_transaction(tx_hash: str, db: Session = Depends(get_db)):
    """Get transaction details"""
    try:
        transaction = db.query(Transaction).filter(Transaction.tx_hash == tx_hash).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return TransactionResponse(
            hash=transaction.tx_hash,
            from_address=transaction.from_address or "",
            to_address=transaction.to_address or "",
            value=float(transaction.value or 0),
            gas_used=getattr(transaction, 'gas_used', None),
            gas_price=float(transaction.gas_price or 0) if transaction.gas_price else None,
            block_number=transaction.block_number,
            timestamp=int(transaction.timestamp.timestamp()) if transaction.timestamp else int(datetime.now().timestamp()),
            status="confirmed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transaction {tx_hash}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching transaction: {str(e)}")
