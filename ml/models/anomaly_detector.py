import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

class AnomalyDetector:
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.scaler = StandardScaler()
    
    def extract_transaction_features(self, transaction, wallet_history):
        """Extract features from a transaction for anomaly detection"""
        features = {}
        
        # Transaction value
        features['value'] = transaction.get('value', 0)
        
        # Historical comparison
        historical_values = [tx.get('value', 0) for tx in wallet_history]
        if historical_values:
            mean_val = np.mean(historical_values)
            std_val = max(np.std(historical_values), 1)
            features['value_zscore'] = (transaction.get('value', 0) - mean_val) / std_val
        else:
            features['value_zscore'] = 0
        
        # Time pattern
        if transaction.get('timestamp'):
            hour_of_day = transaction['timestamp'].hour
            features['unusual_hour'] = 1 if hour_of_day < 6 else 0
        else:
            features['unusual_hour'] = 0
        
        # Gas price anomaly
        features['gas_price'] = transaction.get('gas_price', 0)
        
        # Contract interaction flag
        features['contract_interaction'] = 1 if transaction.get('contract_interaction') else 0
        
        # Token transfer flag
        features['token_transfer'] = 1 if transaction.get('token_transfers', 0) > 0 else 0
        
        return features
    
    def predict_anomaly(self, transaction, wallet_history):
        """Predict if transaction is anomalous"""
        features = self.extract_transaction_features(transaction, wallet_history)
        feature_array = np.array(list(features.values())).reshape(1, -1)
        
        # Check if model is trained
        if not hasattr(self.model, 'offset_'):
            # Use rule-based detection for untrained model
            is_anomalous, anomaly_score = self._rule_based_anomaly(features, wallet_history)
        else:
            feature_scaled = self.scaler.transform(feature_array)
            anomaly_prediction = self.model.predict(feature_scaled)[0]
            anomaly_score = -self.model.score_samples(feature_scaled)[0]
            is_anomalous = anomaly_prediction == -1
        
        return {
            'is_anomalous': is_anomalous,
            'anomaly_score': float(anomaly_score),
            'features': features
        }
    
    def _rule_based_anomaly(self, features, wallet_history):
        """Simple rule-based anomaly detection"""
        anomaly_score = 0.0
        
        # High value z-score
        if abs(features['value_zscore']) > 3:
            anomaly_score += 0.4
        
        # Unusual hour
        if features['unusual_hour'] == 1:
            anomaly_score += 0.2
        
        # High gas price
        historical_gas = [tx.get('gas_price', 0) for tx in wallet_history]
        if historical_gas and features['gas_price'] > np.mean(historical_gas) * 2:
            anomaly_score += 0.2
        
        # Contract interaction
        if features['contract_interaction'] == 1:
            anomaly_score += 0.1
        
        # Token transfer
        if features['token_transfer'] == 1:
            anomaly_score += 0.1
        
        is_anomalous = anomaly_score > 0.5
        return is_anomalous, anomaly_score
    
    def train(self, transactions_data):
        """Train anomaly detection model"""
        X = np.array([list(self.extract_transaction_features(tx, []).values()) 
                     for tx in transactions_data])
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.save()
    
    def save(self, path='ml/models'):
        """Save model and scaler"""
        os.makedirs(path, exist_ok=True)
        joblib.dump(self.model, f'{path}/anomaly_detector.pkl')
        joblib.dump(self.scaler, f'{path}/anomaly_scaler.pkl')
    
    def load(self, path='ml/models'):
        """Load model and scaler"""
        self.model = joblib.load(f'{path}/anomaly_detector.pkl')
        self.scaler = joblib.load(f'{path}/anomaly_scaler.pkl')
