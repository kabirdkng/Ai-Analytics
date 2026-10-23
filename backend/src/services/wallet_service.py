from sqlalchemy.orm import Session
from models.database import Wallet, Transaction
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from ml.models.risk_scorer import WalletRiskScorer
from services.graph_service import GraphService
import logging

logger = logging.getLogger(__name__)

class WalletService:
    def __init__(self):
        self.risk_scorer = WalletRiskScorer()
        self.graph_service = GraphService()
        # Try to load existing model
        try:
            self.risk_scorer.load()
            logger.info("Loaded pre-trained risk scoring model")
        except Exception as e:
            logger.warning(f"No pre-trained model found, using rule-based scoring: {e}")
    
    async def create_wallet(self, wallet_data: dict, db: Session) -> Wallet:
        """Create new wallet entry in database"""
        try:
            # Calculate risk score
            risk_analysis = self.risk_scorer.predict_risk(wallet_data)
            
            # Calculate transaction totals
            transactions = wallet_data.get('transactions', [])
            address = wallet_data['address'].lower()
            
            # Debug logging
            logger.info(f"Calculating totals for {len(transactions)} transactions")
            if transactions:
                sample_tx = transactions[0]
                logger.info(f"Sample transaction: {sample_tx}")
            
            total_value_in = 0
            total_value_out = 0
            total_fees_paid = 0
            
            # Ensure address is lowercase for comparison
            address_lower = address.lower()
            
            for tx in transactions:
                tx_value = float(tx.get('value', 0))
                tx_from = tx.get('from', '').lower() if tx.get('from') else ''
                tx_to = tx.get('to', '').lower() if tx.get('to') else ''
                tx_fee = float(tx.get('transaction_fee', 0))
                
                # Incoming: receiving ETH (to_address matches wallet)
                if tx_to == address_lower and tx_value > 0:
                    total_value_in += tx_value
                
                # Outgoing: sending ETH (from_address matches wallet)
                if tx_from == address_lower and tx_value > 0:
                    total_value_out += tx_value
                    # Add transaction fees for outgoing transactions only
                    total_fees_paid += tx_fee
            
            logger.info(f"Calculated totals - In: {total_value_in}, Out: {total_value_out}, Fees: {total_fees_paid}")
            logger.info(f"Address: {address_lower}, Transaction count: {len(transactions)}")
            
            # Handle timezone-aware datetimes
            first_seen = wallet_data.get('first_seen', datetime.now())
            if hasattr(first_seen, 'tzinfo') and first_seen.tzinfo:
                first_seen = first_seen.replace(tzinfo=None)
                
            last_active = wallet_data.get('last_active', datetime.now())  
            if hasattr(last_active, 'tzinfo') and last_active.tzinfo:
                last_active = last_active.replace(tzinfo=None)
            
            # Create wallet
            wallet = Wallet(
                address=wallet_data['address'],
                first_seen=first_seen,
                last_active=last_active,
                transaction_count=wallet_data.get('transaction_count', 0),
                total_value_in=total_value_in,
                total_value_out=total_value_out,
                total_fees_paid=total_fees_paid,
                risk_score=risk_analysis['score'],
                risk_level=risk_analysis['level'],
                updated_at=datetime.now()
            )
            
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
            
            # Add transactions individually to avoid duplicates
            transactions_added = 0
            oldest_timestamp = datetime.now()
            newest_timestamp = datetime.min
            
            for tx_data in wallet_data.get('transactions', []):
                tx_hash = tx_data.get('hash')
                if not tx_hash:
                    continue
                    
                # Check if transaction already exists
                existing_tx = db.query(Transaction).filter(
                    Transaction.tx_hash == tx_hash
                ).first()
                
                if not existing_tx:
                    timestamp = tx_data.get('timestamp', datetime.now())
                    if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo:
                        timestamp = timestamp.replace(tzinfo=None)
                    
                    # Track oldest and newest timestamps for days_active calculation
                    if timestamp < oldest_timestamp:
                        oldest_timestamp = timestamp
                    if timestamp > newest_timestamp:
                        newest_timestamp = timestamp
                    
                    tx = Transaction(
                        tx_hash=tx_hash,
                        from_address=tx_data.get('from'),
                        to_address=tx_data.get('to'),
                        value=tx_data.get('value', 0),
                        gas_price=tx_data.get('gas_price', 0),
                        gas_used=tx_data.get('gas_used', 0),
                        transaction_fee=tx_data.get('transaction_fee', 0),
                        timestamp=timestamp,
                        block_number=tx_data.get('block_number', 0)
                    )
                    db.add(tx)
                    transactions_added += 1
                    
                    # Commit in batches to avoid memory issues
                    if transactions_added % 100 == 0:
                        db.commit()
            
            # Update transaction_count and days_active
            wallet.transaction_count = transactions_added
            
            # Calculate days_active from transaction timestamps
            if oldest_timestamp != datetime.now() and newest_timestamp != datetime.min:
                days_active = (newest_timestamp - oldest_timestamp).days + 1
                wallet.days_active = max(1, days_active)  # At least 1 day
            else:
                wallet.days_active = 1
            
            db.commit()
            logger.info(f"Added {transactions_added} new transactions, days_active: {wallet.days_active}")
            logger.info(f"Created wallet {wallet.address} with risk level {wallet.risk_level}")
            
            return wallet
            
        except Exception as e:
            logger.error(f"Error creating wallet: {str(e)}")
            db.rollback()
            raise
    
    async def update_wallet(self, wallet: Wallet, wallet_data: dict, db: Session) -> Wallet:
        """Update existing wallet with new data"""
        try:
            # Calculate new risk score
            risk_analysis = self.risk_scorer.predict_risk(wallet_data)
            
            # Update wallet
            last_active = wallet_data.get('last_active', datetime.now())
            if hasattr(last_active, 'tzinfo') and last_active.tzinfo:
                last_active = last_active.replace(tzinfo=None)
            wallet.last_active = last_active
            wallet.transaction_count = wallet_data.get('transaction_count', 0)
            
            # Calculate transaction totals properly (same logic as create_wallet)
            transactions = wallet_data.get('transactions', [])
            address_lower = wallet_data['address'].lower()
            
            total_value_in = 0
            total_value_out = 0
            total_fees_paid = 0
            
            for tx in transactions:
                tx_value = float(tx.get('value', 0))
                tx_from = tx.get('from', '').lower() if tx.get('from') else ''
                tx_to = tx.get('to', '').lower() if tx.get('to') else ''
                tx_fee = float(tx.get('transaction_fee', 0))
                
                # Incoming: receiving ETH (to_address matches wallet)
                if tx_to == address_lower and tx_value > 0:
                    total_value_in += tx_value
                
                # Outgoing: sending ETH (from_address matches wallet)
                if tx_from == address_lower and tx_value > 0:
                    total_value_out += tx_value
                    total_fees_paid += tx_fee
            
            wallet.total_value_in = total_value_in
            wallet.total_value_out = total_value_out
            wallet.total_fees_paid = total_fees_paid
            wallet.risk_score = risk_analysis['score']
            wallet.risk_level = risk_analysis['level']
            wallet.updated_at = datetime.now()
            
            # Add new transactions and calculate days_active
            transactions_added = 0
            oldest_timestamp = datetime.now()
            newest_timestamp = datetime.min
            
            for tx_data in wallet_data.get('transactions', []):
                tx_hash = tx_data.get('hash')
                if not tx_hash:
                    continue
                    
                # Check if transaction already exists
                existing_tx = db.query(Transaction).filter(
                    Transaction.tx_hash == tx_hash
                ).first()
                
                if not existing_tx:
                    timestamp = tx_data.get('timestamp', datetime.now())
                    if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo:
                        timestamp = timestamp.replace(tzinfo=None)
                    
                    # Track oldest and newest timestamps
                    if timestamp < oldest_timestamp:
                        oldest_timestamp = timestamp
                    if timestamp > newest_timestamp:
                        newest_timestamp = timestamp
                    
                    tx = Transaction(
                        tx_hash=tx_hash,
                        from_address=tx_data.get('from'),
                        to_address=tx_data.get('to'),
                        value=tx_data.get('value', 0),
                        gas_price=tx_data.get('gas_price', 0),
                        gas_used=tx_data.get('gas_used', 0),
                        transaction_fee=tx_data.get('transaction_fee', 0),
                        timestamp=timestamp,
                        block_number=tx_data.get('block_number', 0)
                    )
                    db.add(tx)
                    transactions_added += 1
                    
                    # Commit in batches
                    if transactions_added % 100 == 0:
                        db.commit()
                else:
                    # Still track timestamps for days_active calculation
                    timestamp = existing_tx.timestamp
                    if timestamp < oldest_timestamp:
                        oldest_timestamp = timestamp
                    if timestamp > newest_timestamp:
                        newest_timestamp = timestamp
            
            # Update transaction_count with total from database
            total_txs = db.query(Transaction).filter(
                (Transaction.from_address == address_lower) | (Transaction.to_address == address_lower)
            ).count()
            wallet.transaction_count = total_txs
            
            # Calculate days_active from all transaction timestamps
            if oldest_timestamp != datetime.now() and newest_timestamp != datetime.min:
                days_active = (newest_timestamp - oldest_timestamp).days + 1
                wallet.days_active = max(1, days_active)
            else:
                wallet.days_active = 1
            
            db.commit()
            db.refresh(wallet)
            
            logger.info(f"Updated wallet {wallet.address} with risk level {wallet.risk_level}, added {transactions_added} new transactions, days_active: {wallet.days_active}")
            
            return wallet
            
        except Exception as e:
            logger.error(f"Error updating wallet: {str(e)}")
            db.rollback()
    
    async def get_defi_analytics(self, wallet_address: str) -> dict:
        """Get comprehensive DeFi analytics using The Graph Protocol"""
        try:
            # Get DeFi positions from The Graph
            defi_data = await self.graph_service.get_defi_analytics(wallet_address)
            
            # Enhanced analytics with risk assessment
            enhanced_data = {
                **defi_data,
                "defi_risk_factors": self._assess_defi_risks(defi_data),
                "protocol_diversification": len(defi_data.get("protocols_used", [])),
                "leverage_ratio": self._calculate_leverage(defi_data)
            }
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error getting DeFi analytics: {str(e)}")
            return {
                "total_positions": 0,
                "protocols_used": [],
                "total_liquidity_provided": 0,
                "total_supplied": 0,
                "total_borrowed": 0,
                "health_factor": 999.99,
                "positions": [],
                "defi_risk_factors": [],
                "protocol_diversification": 0,
                "leverage_ratio": 0
            }
    
    def _assess_defi_risks(self, defi_data: dict) -> list:
        """Assess DeFi-specific risk factors"""
        risks = []
        
        health_factor = defi_data.get("health_factor", float("inf"))
        if health_factor < 1.5:
            risks.append("LOW_HEALTH_FACTOR")
        
        if defi_data.get("total_borrowed", 0) > defi_data.get("total_supplied", 0) * 0.8:
            risks.append("HIGH_LEVERAGE")
        
        if len(defi_data.get("protocols_used", [])) == 1:
            risks.append("PROTOCOL_CONCENTRATION")
        
        if defi_data.get("total_liquidity_provided", 0) > defi_data.get("total_supplied", 0) * 2:
            risks.append("IMPERMANENT_LOSS_EXPOSURE")
        
        return risks
    
    def _calculate_leverage(self, defi_data: dict) -> float:
        """Calculate effective leverage ratio"""
        supplied = defi_data.get("total_supplied", 0)
        borrowed = defi_data.get("total_borrowed", 0)
        
        if supplied == 0:
            return 0
        
        return (supplied + borrowed) / supplied
