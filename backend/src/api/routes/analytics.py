from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta

from models.database import get_db, Wallet, Transaction
from services.graph_service import GraphService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize GraphService
graph_service = GraphService()

@router.get("/overview")
async def get_analytics_overview(db: Session = Depends(get_db)):
    """Get platform analytics overview"""
    try:
        # Count total wallets
        total_wallets = db.query(func.count(Wallet.id)).scalar() or 0
        
        # Count total transactions
        total_transactions = db.query(func.count(Transaction.id)).scalar() or 0
        
        # Count high risk wallets
        high_risk_wallets = db.query(func.count(Wallet.id)).filter(
            Wallet.risk_level.in_(['high', 'critical'])
        ).scalar() or 0
        
        # Mock anomalies for now
        anomalies_detected = high_risk_wallets
        
        return {
            "total_wallets_analyzed": total_wallets,
            "total_transactions": total_transactions,
            "high_risk_wallets": high_risk_wallets,
            "anomalies_detected": anomalies_detected
        }
    except Exception as e:
        logger.error(f"Error fetching analytics overview: {str(e)}")
        return {
            "total_wallets_analyzed": 0,
            "total_transactions": 0,
            "high_risk_wallets": 0,
            "anomalies_detected": 0
        }

@router.get("/risk-distribution")
async def get_risk_distribution(db: Session = Depends(get_db)):
    """Get risk level distribution"""
    try:
        risk_counts = db.query(
            Wallet.risk_level,
            func.count(Wallet.id).label('count')
        ).group_by(Wallet.risk_level).all()
        
        distribution = []
        for risk_level, count in risk_counts:
            distribution.append({
                "risk_level": risk_level or "unknown",
                "count": count,
                "percentage": 0  # Will be calculated on frontend
            })
        
        # Calculate percentages
        total = sum(item['count'] for item in distribution)
        if total > 0:
            for item in distribution:
                item['percentage'] = round((item['count'] / total) * 100, 1)
        
        return distribution
        
    except Exception as e:
        logger.error(f"Error fetching risk distribution: {str(e)}")
        return []

@router.get("/trends")
async def get_trends(
    period: str = Query("7d", regex="^(1d|7d|30d|90d)$"),
    db: Session = Depends(get_db)
):
    """Get risk trends over time"""
    try:
        # Calculate date range based on period
        days_map = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(period, 7)
        start_date = datetime.now() - timedelta(days=days)
        
        # Get wallets created in this period
        wallets = db.query(Wallet).filter(
            Wallet.created_at >= start_date
        ).order_by(Wallet.created_at).all()
        
        # Group by date and risk level
        trends = {}
        for wallet in wallets:
            date_key = wallet.created_at.date().isoformat() if wallet.created_at else datetime.now().date().isoformat()
            if date_key not in trends:
                trends[date_key] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            
            risk_level = wallet.risk_level or "low"
            trends[date_key][risk_level] += 1
        
        # Convert to list format
        result = []
        for date_key, counts in sorted(trends.items()):
            result.append({
                "date": date_key,
                "low": counts["low"],
                "medium": counts["medium"], 
                "high": counts["high"],
                "critical": counts["critical"],
                "total": sum(counts.values())
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching trends: {str(e)}")
        return []

@router.get("/defi/{wallet_address}")
async def get_defi_analytics(wallet_address: str):
    """Get DeFi analytics for a specific wallet"""
    try:
        logger.info(f"Getting DeFi analytics for wallet: {wallet_address}")
        analytics = await graph_service.get_defi_analytics(wallet_address)
        return analytics
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
