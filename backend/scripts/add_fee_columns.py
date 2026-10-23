import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.src.models.database import engine, Base
from sqlalchemy import text

def add_fee_columns():
    """Add transaction fee columns to existing tables"""
    try:
        with engine.begin() as conn:
            # Add total_fees_paid to wallets table if it doesn't exist
            conn.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='wallets' AND column_name='total_fees_paid'
                    ) THEN
                        ALTER TABLE wallets ADD COLUMN total_fees_paid DECIMAL(30,18) DEFAULT 0;
                    END IF;
                END $$;
            """))
            
            # Add gas_used to transactions table if it doesn't exist
            conn.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='transactions' AND column_name='gas_used'
                    ) THEN
                        ALTER TABLE transactions ADD COLUMN gas_used INTEGER DEFAULT 0;
                    END IF;
                END $$;
            """))
            
            # Add transaction_fee to transactions table if it doesn't exist
            conn.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='transactions' AND column_name='transaction_fee'
                    ) THEN
                        ALTER TABLE transactions ADD COLUMN transaction_fee DECIMAL(30,18) DEFAULT 0;
                    END IF;
                END $$;
            """))
            
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise

if __name__ == "__main__":
    add_fee_columns()
