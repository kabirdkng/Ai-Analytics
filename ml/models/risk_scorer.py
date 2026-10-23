import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime, timedelta
import os

class WalletRiskScorer:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.risk_thresholds = {
            'critical': 0.8,
            'high': 0.6,
            'medium': 0.4,
            'low': 0.0
        }
    
    def extract_features(self, wallet_data):
        """Extract features from wallet transaction history"""
        features = {}
        
        # Transaction patterns
        days_active = max((datetime.now() - wallet_data['first_seen']).days, 1) if wallet_data.get('first_seen') else 1
        features['transaction_frequency'] = len(wallet_data.get('transactions', [])) / days_active
        
        transaction_values = [tx.get('value', 0) for tx in wallet_data.get('transactions', [])]
        features['avg_transaction_value'] = np.mean(transaction_values) if transaction_values else 0
        features['transaction_std'] = np.std(transaction_values) if transaction_values else 0
        
        # Behavioral patterns
        counterparties = set()
        for tx in wallet_data.get('transactions', []):
            if tx.get('to') != wallet_data.get('address'):
                counterparties.add(tx.get('to'))
            if tx.get('from') != wallet_data.get('address'):
                counterparties.add(tx.get('from'))
        features['unique_counterparties'] = len(counterparties)
        
        # Contract interactions
        contract_interactions = [tx for tx in wallet_data.get('transactions', []) 
                               if tx.get('contract_interaction', False)]
        total_txs = max(len(wallet_data.get('transactions', [])), 1)
        features['contract_interaction_ratio'] = len(contract_interactions) / total_txs
        
        # Time-based patterns
        features['days_active'] = days_active
        if wallet_data.get('last_active'):
            features['activity_recency'] = (datetime.now() - wallet_data['last_active']).days
        else:
            features['activity_recency'] = 0
        
        # Large transaction patterns
        avg_val = features['avg_transaction_value']
        large_txs = [tx for tx in wallet_data.get('transactions', []) 
                    if tx.get('value', 0) > avg_val * 3]
        features['large_tx_ratio'] = len(large_txs) / total_txs
        
        # Balance changes
        total_in = sum([tx.get('value', 0) for tx in wallet_data.get('transactions', []) 
                       if tx.get('to') == wallet_data.get('address')])
        total_out = sum([tx.get('value', 0) for tx in wallet_data.get('transactions', []) 
                        if tx.get('from') == wallet_data.get('address')])
        features['total_in'] = total_in
        features['total_out'] = total_out
        features['balance_ratio'] = total_in / max(total_out, 0.001)
        
        return features
    
    def predict_risk(self, wallet_data):
        """Predict risk score (0-1) for a wallet"""
        features = self.extract_features(wallet_data)
        feature_array = np.array(list(features.values())).reshape(1, -1)
        
        # Check if model is trained
        if not hasattr(self.model, 'classes_'):
            # Use rule-based scoring for untrained model
            risk_score = self._rule_based_score(features)
        else:
            feature_scaled = self.scaler.transform(feature_array)
            risk_score = self.model.predict_proba(feature_scaled)[0][1]
        
        # Determine risk level
        risk_level = 'low'
        for level in ['critical', 'high', 'medium', 'low']:
            if risk_score >= self.risk_thresholds[level]:
                risk_level = level
                break
        
        return {
            'score': float(risk_score),
            'level': risk_level,
            'features': features
        }
    
    def _rule_based_score(self, features):
        """Simple rule-based scoring when ML model isn't trained"""
        score = 0.0
        
        # High transaction frequency
        if features['transaction_frequency'] > 10:
            score += 0.2
        
        # High value volatility
        if features['transaction_std'] > features['avg_transaction_value'] * 2:
            score += 0.2
        
        # Many unique counterparties
        if features['unique_counterparties'] > 100:
            score += 0.15
        
        # High contract interaction
        if features['contract_interaction_ratio'] > 0.7:
            score += 0.15
        
        # Unusual balance ratio
        if features['balance_ratio'] < 0.1 or features['balance_ratio'] > 10:
            score += 0.2
        
        # Large transaction ratio
        if features['large_tx_ratio'] > 0.3:
            score += 0.1
        
        return min(score, 1.0)
    
    def train(self, training_data, labels):
        """Train the risk model"""
        X = np.array([list(self.extract_features(wallet).values()) for wallet in training_data])
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, labels)
        self.save()
    
    def save(self, path='ml/models'):
        """Save model and scaler"""
        os.makedirs(path, exist_ok=True)
        joblib.dump(self.model, f'{path}/risk_scorer.pkl')
        joblib.dump(self.scaler, f'{path}/scaler.pkl')
    
    def load(self, path='ml/models'):
        """Load model and scaler"""
        self.model = joblib.load(f'{path}/risk_scorer.pkl')
        self.scaler = joblib.load(f'{path}/scaler.pkl')
