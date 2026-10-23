# AI Blockchain Analytics Platform

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![React](https://img.shields.io/badge/React-18.2-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)

AI-powered blockchain analytics platform for wallet risk scoring, anomaly detection, and portfolio insights.

## 🚀 Features

- **AI Risk Scoring**: Machine learning models to assess wallet risk levels
- **Anomaly Detection**: Identify suspicious transactions in real-time
- **Portfolio Insights**: Comprehensive wallet analytics and metrics
- **Multi-chain Support**: Ethereum, Polygon, Arbitrum (expandable)
- **REST API**: Developer-friendly API with rate limiting
- **Smart Contracts**: On-chain risk score registry

## 📋 Requirements

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

## 🛠️ Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/ai-analytics.git
cd ai-analytics

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec api python -m models.database

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
```

### Option 2: Manual Setup

**Backend Setup:**

```bash
# Create virtual environment
cd backend
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb analytics
python src/models/database.py

# Run backend
cd src
uvicorn main:app --reload --port 8000
```

**Frontend Setup:**

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm start
```

**Database Setup:**

```bash
# PostgreSQL
docker run --name analytics-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=analytics \
  -p 5432:5432 -d postgres:15

# Redis
docker run --name analytics-cache -p 6379:6379 -d redis:7-alpine
```

## 📁 Project Structure

```
ai-analytics-platform/
├── backend/                    # Python FastAPI backend
│   ├── src/
│   │   ├── api/routes/        # API endpoints
│   │   ├── models/            # Database models
│   │   ├── services/          # Business logic
│   │   └── main.py            # FastAPI app
│   ├── tests/                 # Unit tests
│   └── requirements.txt       # Python dependencies
├── ml/                        # Machine learning models
│   ├── models/
│   │   ├── risk_scorer.py     # Risk scoring model
│   │   └── anomaly_detector.py # Anomaly detection
│   ├── training/              # Training scripts
│   └── notebooks/             # Jupyter notebooks
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   └── App.js             # Main app
│   └── package.json           # Node dependencies
├── smart-contracts/           # Solidity contracts
│   ├── contracts/             # Contract source
│   ├── scripts/               # Deployment scripts
│   └── hardhat.config.js      # Hardhat config
├── docker-compose.yml         # Docker orchestration
├── Dockerfile                 # Backend container
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/analytics

# Redis
REDIS_URL=redis://localhost:6379

# Blockchain RPC
ETHEREUM_RPC=https://eth.llamarpc.com
POLYGON_RPC=https://polygon-rpc.com

# External APIs (optional)
ALCHEMY_API_KEY=your_key
MORALIS_API_KEY=your_key

# Server
PORT=8000
ENV=development
```

## 📊 API Documentation

### Analyze Wallet

```bash
GET /api/wallets/{address}
```

**Response:**
```json
{
  "address": "0x...",
  "risk_score": 0.35,
  "risk_level": "low",
  "transaction_count": 150,
  "total_value_in": 1500.50,
  "total_value_out": 1200.30,
  "days_active": 365,
  "unique_counterparties": 45,
  "last_analysis": "2025-10-22T10:30:00"
}
```

### Get All Wallets

```bash
GET /api/wallets?skip=0&limit=10&risk_level=high
```

See full API documentation at: `http://localhost:8000/docs`

## 🧪 Testing

```bash
# Run backend tests
cd backend
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Test specific file
pytest tests/test_risk_scorer.py -v
```

## 🚢 Deployment

### Deploy Smart Contracts

```bash
cd smart-contracts
npm install
npx hardhat compile
npx hardhat run scripts/deploy.js --network mumbai
```

### Deploy Backend (Heroku)

```bash
heroku create ai-analytics-api
heroku addons:create heroku-postgresql:standard-0
heroku addons:create heroku-redis:premium-0
git push heroku main
```

### Deploy Frontend (Vercel)

```bash
cd frontend
npm run build
vercel --prod
```

## 📈 Machine Learning Models

### Risk Scoring Model

The risk scorer uses a Random Forest classifier with features including:
- Transaction frequency
- Average transaction value
- Contract interaction ratio
- Unique counterparties
- Balance ratio
- Large transaction ratio

### Anomaly Detection

Uses Isolation Forest to detect:
- Unusual transaction values
- Abnormal time patterns
- High gas prices
- Suspicious contract interactions

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🔗 Links

- [Documentation](./docs/)
- [API Reference](http://localhost:8000/docs)
- [Issue Tracker](https://github.com/yourusername/ai-analytics/issues)

## 👥 Team

Built with ❤️ by the AI Analytics Team

## 📞 Support

For support, email kabirdkng@gmail.com or open an issue.
