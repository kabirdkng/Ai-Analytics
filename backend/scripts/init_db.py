#!/usr/bin/env python3
"""
Initialize the database with schema and sample data
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.database import init_db, SessionLocal, Wallet, Transaction
from datetime import datetime, timedelta
import random

def create_sample_data():
    """Create sample wallet and transaction data for testing"""
    db = SessionLocal()
    
    try:
        print("Creating sample data...")
        
        # Sample wallets
        sample_wallets = [
            {
                'address': '0x742d35cc6634c0532925a3b844bc9e7595f0beb0',
                'risk_level': 'low',
                'risk_score': 0.2
            },
            {
                'address': '0xbe0eb53f46cd790cd13851d5eff43d12404d33e8',
                'risk_level': 'medium',
                'risk_score': 0.5
            },
            {
                'address': '0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503',
                'risk_level': 'high',
                'risk_score': 0.75
            }
        ]
        
        for wallet_data in sample_wallets:
            # Check if wallet exists
            existing = db.query(Wallet).filter(
                Wallet.address == wallet_data['address']
            ).first()
            
            if not existing:
                wallet = Wallet(
                    address=wallet_data['address'],
                    first_seen=datetime.now() - timedelta(days=random.randint(30, 365)),
                    last_active=datetime.now() - timedelta(days=random.randint(1, 30)),
                    transaction_count=random.randint(10, 1000),
                    total_value_in=random.uniform(100, 10000),
                    total_value_out=random.uniform(100, 10000),
                    risk_score=wallet_data['risk_score'],
                    risk_level=wallet_data['risk_level']
                )
                db.add(wallet)
                print(f"Created wallet: {wallet.address} (Risk: {wallet.risk_level})")
                
                # Create sample transactions for each wallet
                for i in range(random.randint(5, 15)):
                    # Random transaction hash
                    tx_hash = '0x' + ''.join(random.choices('0123456789abcdef', k=64))
                    
                    # Randomly decide if this wallet is sender or receiver
                    is_sender = random.choice([True, False])
                    other_address = '0x' + ''.join(random.choices('0123456789abcdef', k=40))
                    
                    transaction = Transaction(
                        hash=tx_hash,
                        from_address=wallet.address if is_sender else other_address,
                        to_address=other_address if is_sender else wallet.address,
                        value=random.uniform(0.1, 100),
                        gas_used=random.randint(21000, 200000),
                        gas_price=random.uniform(10, 50),
                        block_number=random.randint(18000000, 18500000),
                        timestamp=datetime.now() - timedelta(days=random.randint(1, 90)),
                        status='confirmed'
                    )
                    db.add(transaction)
        
        db.commit()
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized!")
    
    # Ask user if they want sample data
    response = input("Create sample data for testing? (y/n): ")
    if response.lower() == 'y':
        create_sample_data()
