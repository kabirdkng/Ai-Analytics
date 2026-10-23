# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Docker & Docker Compose installed
- Git

### Steps

1. **Clone & Setup**
```bash
git clone https://github.com/yourusername/ai-analytics.git
cd ai-analytics
cp .env.example .env
```

2. **Start Services**
```bash
sudo docker-compose up -d
```

3. **Wait for Services to be Ready**
```bash
# Check service status
sudo docker-compose ps
# Wait for all services to be healthy
sudo docker-compose logs -f
```

4. **Initialize Database**
```bash
sudo docker-compose exec api python scripts/init_db.py
```

5. **Verify Services**
```bash
# Test API
curl http://localhost:8000/docs
# Check frontend is accessible
curl http://localhost:3000
```

6. **Access Application**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### ✅ Verify Everything Works

Test the API:
```bash
# Test API documentation
curl http://localhost:8000/docs

# Test wallets endpoint
curl http://localhost:8000/api/wallets/
```

Test the Frontend:
```bash
# Check if frontend is accessible
curl http://localhost:3000
```

### Try It Out

1. Open http://localhost:3000
2. Enter any Ethereum wallet address (e.g., `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`)
3. Click "Analyze"
4. View **LIVE BLOCKCHAIN DATA** - real-time balance, transaction count, and risk assessment!

**🔴 Live Data Features:**
- Real-time wallet balance from Ethereum network
- Live transaction count (not cached)
- Fresh risk analysis based on current blockchain state
- All data fetched directly from Alchemy/Moralis APIs

**Real Blockchain Integration:**
- ✅ Uses Alchemy & Moralis APIs for live blockchain data
- ✅ Real wallet balance and transaction history  
- ✅ AI-powered risk scoring with ML models
- ✅ Interactive charts showing transaction patterns
- ✅ Accurate total value in/out calculations in ETH
- ✅ Intelligent caching for fast responses (<200ms)
- ✅ Fallback to public RPC if API keys unavailable

**Test with Real Wallets:**
- Vitalik's Address: `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
- Any valid Ethereum address works!

---

## 📋 Development Workflow

### Running Locally (Without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd src
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

**Database:**
```bash
# PostgreSQL
createdb analytics

# Initialize
python backend/scripts/init_db.py
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests (if added)
cd frontend
npm test
```

---

## 📚 API Examples

### Analyze Wallet
```bash
curl http://localhost:8000/api/wallets/0x742d35cc6634c0532925a3b844bc9e7595f0beb0
```

### Get All Wallets
```bash
curl http://localhost:8000/api/wallets?limit=10
```

### Analytics Overview
```bash
curl http://localhost:8000/api/analytics/overview
```

---

## 🔧 Common Commands

```bash
# Stop services
docker-compose down

# View logs
docker-compose logs -f api

# Restart service
docker-compose restart api

# Run database backup
docker-compose exec db pg_dump -U user analytics > backup.sql

# Access database
docker-compose exec db psql -U user analytics
```

---

## 🐛 Troubleshooting

**Issue: Port already in use**
```bash
# Change ports in docker-compose.yml
# Or stop conflicting services
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8000
```

**Issue: Database connection error**
```bash
# Wait for database to be ready
sudo docker-compose logs db
# Check if database is initialized
sudo docker-compose exec db psql -U user -d analytics -c "\dt"
```

**Issue: Frontend can't reach API**
```bash
# Check CORS settings
# Verify proxy in frontend/package.json
sudo docker-compose logs api
sudo docker-compose logs frontend
```

**Issue: Frontend dependencies missing**
```bash
# Restart frontend service to install dependencies
sudo docker-compose restart frontend
sudo docker-compose logs frontend
```

**Issue: API import errors**
```bash
# Rebuild and restart API service
sudo docker-compose build api
sudo docker-compose restart api
sudo docker-compose logs api
```

**Issue: Services not starting**
```bash
# Check all service status
sudo docker-compose ps
# Restart all services
sudo docker-compose down
sudo docker-compose up -d
# Check logs
sudo docker-compose logs -f
```

---

## 📖 Next Steps

1. Read full [README.md](../README.md)
2. Check [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
3. Explore API documentation at http://localhost:8000/docs
4. Customize ML models in `ml/models/`
5. Add your blockchain RPC endpoints in `.env`

---

## 💡 Tips

- Use sample wallet addresses from init_db.py for testing
- Check logs with `docker-compose logs -f`
- API documentation is interactive - try it at /docs
- Frontend uses Tailwind CSS for styling
- ML models use rule-based scoring initially (train for better results)

---

## 🆘 Need Help?

- Check the logs: `docker-compose logs -f`
- Review error messages in browser console (F12)
- Ensure all services are running: `docker-compose ps`
- Read the full documentation in `/docs`

Happy Coding! 🎉
