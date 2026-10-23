from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, TIMESTAMP, Text, DECIMAL, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/analytics")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(42), unique=True, nullable=False, index=True)
    first_seen = Column(TIMESTAMP, default=datetime.now)
    last_active = Column(TIMESTAMP)
    transaction_count = Column(Integer, default=0)
    total_value_in = Column(DECIMAL(30, 18))  # Increased precision for ETH values
    total_value_out = Column(DECIMAL(30, 18))  # Increased precision for ETH values
    total_fees_paid = Column(DECIMAL(30, 18), default=0)  # Total transaction fees paid
    days_active = Column(Integer, default=1)  # Number of days between first and last transaction
    risk_score = Column(Float)
    risk_level = Column(String(20))
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    # Note: Transactions relationship removed due to foreign key constraint removal
    risk_events = relationship("RiskEvent", back_populates="wallet")
    
    def should_update(self, max_age_hours=1):
        """Check if wallet data needs updating"""
        if not self.updated_at:
            return True
        age = datetime.now() - self.updated_at
        return age.total_seconds() > max_age_hours * 3600

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    from_address = Column(String(42), index=True)  # Removed foreign key constraint
    to_address = Column(String(42), index=True)    # Removed foreign key constraint
    value = Column(DECIMAL(30, 18))  # Increased precision for ETH values
    gas_price = Column(DECIMAL(30, 18))  # Increased precision for gas prices
    gas_used = Column(Integer, default=0)  # Gas units used
    transaction_fee = Column(DECIMAL(30, 18), default=0)  # Total transaction fee in ETH
    timestamp = Column(TIMESTAMP)
    block_number = Column(Integer)
    is_anomalous = Column(Boolean, default=False)
    anomaly_score = Column(Float)
    token_transfers = Column(Integer, default=0)
    contract_interaction = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

class RiskEvent(Base):
    __tablename__ = "risk_events"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), ForeignKey("wallets.address"))
    event_type = Column(String(50))
    severity = Column(String(20))
    description = Column(Text)
    evidence = Column(JSONB)
    timestamp = Column(TIMESTAMP, default=datetime.now)
    
    wallet = relationship("Wallet", back_populates="risk_events")

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(64), unique=True, nullable=False)
    user_id = Column(Integer)
    tier = Column(String(20), default="free")
    rate_limit = Column(Integer, default=100)
    created_at = Column(TIMESTAMP, default=datetime.now)
    last_used = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)

class Watchlist(Base):
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    wallet_address = Column(String(42), ForeignKey("wallets.address"))
    name = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.now)

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
