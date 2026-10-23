# Deployment Guide

## Local Development

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ai-analytics.git
cd ai-analytics
```

### 2. Start Services
```bash
docker-compose up -d
```

### 3. Run Migrations
```bash
docker-compose exec api python src/models/database.py
```

### 4. Access Dashboard
- Frontend: http://localhost:3000
- API: http://localhost:8000/docs
- Database: localhost:5432

---

## Production Deployment

### Option 1: Cloud Providers (AWS/GCP/Azure)

#### AWS EC2 Deployment

**1. Launch EC2 Instance**
```bash
# Ubuntu 22.04 LTS
# Instance Type: t3.medium or larger
# Security Group: Open ports 22, 80, 443, 8000, 3000
```

**2. Install Docker**
```bash
ssh ubuntu@your-ec2-ip

curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**3. Clone and Deploy**
```bash
git clone <repo>
cd ai-analytics

# Create .env file
cp .env.example .env
nano .env  # Edit with production values

# Start services
docker-compose up -d

# Initialize database
docker-compose exec api python src/models/database.py
```

**4. Set Up Nginx Reverse Proxy**
```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/ai-analytics
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ai-analytics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**5. SSL with Let's Encrypt**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

### Option 2: Heroku

**1. Deploy Backend**
```bash
heroku login
heroku create ai-analytics-api

# Add PostgreSQL
heroku addons:create heroku-postgresql:standard-0

# Add Redis
heroku addons:create heroku-redis:premium-0

# Set environment variables
heroku config:set ETHEREUM_RPC=https://eth.llamarpc.com
heroku config:set ENV=production

# Deploy
git push heroku main

# Initialize database
heroku run python src/models/database.py
```

**2. Deploy Frontend (Vercel)**
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod

# Set environment variable
# REACT_APP_API_URL=https://ai-analytics-api.herokuapp.com
```

---

### Option 3: DigitalOcean App Platform

**1. Create App**
- Go to DigitalOcean App Platform
- Connect GitHub repository
- Add three components:
  - Backend (Python/Docker)
  - Frontend (Node.js)
  - Database (PostgreSQL)

**2. Configure Backend**
```yaml
name: api
dockerfile_path: Dockerfile
http_port: 8000
envs:
  - key: DATABASE_URL
    scope: RUN_AND_BUILD_TIME
  - key: REDIS_URL
    scope: RUN_AND_BUILD_TIME
```

**3. Configure Frontend**
```yaml
name: frontend
build_command: npm run build
run_command: npm start
envs:
  - key: REACT_APP_API_URL
    value: ${api.PUBLIC_URL}
```

---

## Deploy Smart Contracts

### Polygon Mumbai Testnet

```bash
cd smart-contracts
npm install

# Add to .env
echo "PRIVATE_KEY=your_private_key" >> .env
echo "POLYGON_MUMBAI_RPC=https://rpc-mumbai.maticvigil.com" >> .env

# Deploy
npx hardhat run scripts/deploy.js --network mumbai

# Verify on PolygonScan
npx hardhat verify --network mumbai DEPLOYED_CONTRACT_ADDRESS
```

### Mainnet Deployment

```bash
# Add to .env
echo "POLYGON_RPC=https://polygon-rpc.com" >> .env

# Deploy to mainnet
npx hardhat run scripts/deploy.js --network polygon

# Verify
npx hardhat verify --network polygon DEPLOYED_CONTRACT_ADDRESS
```

---

## Monitoring & Logging

### 1. Application Monitoring (Datadog)

```bash
# Install Datadog agent
DD_API_KEY=<your_api_key> bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script.sh)"

# Configure Python APM
pip install ddtrace

# Run with tracing
ddtrace-run uvicorn src.main:app
```

### 2. Error Tracking (Sentry)

```bash
pip install sentry-sdk

# Add to main.py
import sentry_sdk
sentry_sdk.init(
    dsn="your_sentry_dsn",
    traces_sample_rate=1.0
)
```

### 3. Log Aggregation (ELK Stack)

```yaml
# docker-compose.yml
elasticsearch:
  image: elasticsearch:8.11.0
  environment:
    - discovery.type=single-node
  ports:
    - "9200:9200"

kibana:
  image: kibana:8.11.0
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch
```

---

## Database Management

### Backups

```bash
# Automated daily backups
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * docker-compose exec -T db pg_dump -U user analytics > /backups/analytics_$(date +\%Y\%m\%d).sql
```

### Migrations

```bash
# Install Alembic
pip install alembic

# Initialize
alembic init migrations

# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

---

## Performance Optimization

### 1. Database Indexing

```sql
CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_transactions_hash ON transactions(tx_hash);
CREATE INDEX idx_transactions_from ON transactions(from_address);
CREATE INDEX idx_transactions_to ON transactions(to_address);
CREATE INDEX idx_risk_events_wallet ON risk_events(wallet_address);
```

### 2. Redis Caching

```python
# Already implemented in backend/src/services/cache_service.py
# Caches wallet analysis for 1 hour
```

### 3. CDN for Frontend

```bash
# CloudFront (AWS)
# or Cloudflare
# Point to frontend static files
```

---

## Health Checks & Monitoring

### Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| API Response Time | <500ms | >1000ms |
| Database Query Time | <100ms | >500ms |
| Cache Hit Rate | >80% | <60% |
| Error Rate | <0.1% | >1% |
| CPU Usage | <70% | >85% |
| Memory Usage | <80% | >90% |

### Monitoring Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Database check
docker-compose exec db pg_isready

# Redis check
docker-compose exec redis redis-cli ping
```

---

## Scaling Strategies

### Horizontal Scaling

```bash
# Use Docker Swarm or Kubernetes
docker swarm init
docker stack deploy -c docker-compose.yml ai-analytics

# Or with Kubernetes
kubectl apply -f k8s/
```

### Database Scaling

```bash
# Read replicas
# Connection pooling (already using SQLAlchemy)
# Partitioning by date for transactions table
```

---

## Security Checklist

- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Implement API authentication
- [ ] Regular security updates
- [ ] Database encryption at rest
- [ ] Backup encryption
- [ ] CORS configuration
- [ ] Input validation

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check database is running
docker-compose ps db

# Check connection
docker-compose exec db psql -U user -d analytics
```

**2. Redis Connection Failed**
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
```

**3. Frontend Can't Connect to API**
```bash
# Check CORS settings in backend/src/main.py
# Verify REACT_APP_API_URL in frontend/.env
```

---

## Support & Maintenance

### Daily Tasks
- Monitor error logs
- Check performance metrics
- Review API usage

### Weekly Tasks
- Database backups verification
- Security updates
- Performance optimization

### Monthly Tasks
- Cost optimization review
- Capacity planning
- Model retraining
- Security audit

---

## Rollback Procedure

```bash
# Rollback Docker containers
docker-compose down
git checkout previous-stable-tag
docker-compose up -d

# Rollback database
psql -U user analytics < /backups/analytics_YYYYMMDD.sql

# Rollback smart contract (if needed)
# Deploy previous contract version
```

---

## Contact

For deployment support: devops@aianalytics.io
