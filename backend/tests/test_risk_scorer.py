import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ml.models.risk_scorer import WalletRiskScorer

@pytest.fixture
def risk_scorer():
    return WalletRiskScorer()

@pytest.fixture
def sample_wallet():
    return {
        'address': '0x1234567890123456789012345678901234567890',
        'first_seen': datetime.now() - timedelta(days=365),
        'last_active': datetime.now(),
        'transactions': [
            {
                'from': '0x1234567890123456789012345678901234567890',
                'to': '0x0987654321098765432109876543210987654321',
                'value': 1.5,
                'contract_interaction': False,
                'token_transfers': 0,
                'timestamp': datetime.now()
            },
            {
                'from': '0x1234567890123456789012345678901234567890',
                'to': '0x1111111111111111111111111111111111111111',
                'value': 2.0,
                'contract_interaction': True,
                'token_transfers': 1,
                'timestamp': datetime.now()
            }
        ]
    }

def test_extract_features(risk_scorer, sample_wallet):
    """Test feature extraction"""
    features = risk_scorer.extract_features(sample_wallet)
    
    assert 'transaction_frequency' in features
    assert 'avg_transaction_value' in features
    assert 'contract_interaction_ratio' in features
    assert 'days_active' in features
    assert features['days_active'] > 0

def test_predict_risk(risk_scorer, sample_wallet):
    """Test risk prediction"""
    result = risk_scorer.predict_risk(sample_wallet)
    
    assert 'score' in result
    assert 'level' in result
    assert 'features' in result
    assert 0 <= result['score'] <= 1
    assert result['level'] in ['low', 'medium', 'high', 'critical']

def test_risk_levels(risk_scorer, sample_wallet):
    """Test risk level classification"""
    result = risk_scorer.predict_risk(sample_wallet)
    
    if result['score'] < 0.4:
        assert result['level'] == 'low'
    elif result['score'] < 0.6:
        assert result['level'] == 'medium'
    elif result['score'] < 0.8:
        assert result['level'] == 'high'
    else:
        assert result['level'] == 'critical'

def test_empty_wallet(risk_scorer):
    """Test with wallet that has no transactions"""
    empty_wallet = {
        'address': '0x0000000000000000000000000000000000000000',
        'first_seen': datetime.now(),
        'last_active': datetime.now(),
        'transactions': []
    }
    
    result = risk_scorer.predict_risk(empty_wallet)
    assert result['score'] >= 0
    assert result['level'] in ['low', 'medium', 'high', 'critical']
