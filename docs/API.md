# API Reference

Base URL: `http://localhost:8000/api`

## Authentication

Currently no authentication required for MVP. API keys coming in v2.0.

---

## Endpoints

### Wallets

#### GET /wallets/{address}
Analyze a specific wallet address.

**Parameters:**
- `address` (path): Ethereum wallet address (0x...)

**Response:**
```json
{
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb0",
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

**Example:**
```bash
curl http://localhost:8000/api/wallets/0x742d35cc6634c0532925a3b844bc9e7595f0beb0
```

---

#### GET /wallets
Get list of analyzed wallets with filtering.

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 10, max: 100)
- `risk_level` (optional): Filter by risk level (low, medium, high, critical)

**Response:**
```json
[
  {
    "address": "0x...",
    "risk_score": 0.35,
    "risk_level": "low",
    ...
  }
]
```

**Example:**
```bash
curl "http://localhost:8000/api/wallets?limit=5&risk_level=high"
```

---

#### POST /wallets/watchlist
Add wallet to watchlist (coming soon).

**Request Body:**
```json
{
  "address": "0x...",
  "name": "My Wallet"
}
```

---

### Transactions

#### GET /transactions
Get recent transactions (coming soon).

#### GET /transactions/{tx_hash}
Get transaction details (coming soon).

---

### Analytics

#### GET /analytics/overview
Get platform analytics overview.

**Response:**
```json
{
  "total_wallets_analyzed": 1250,
  "total_transactions": 45000,
  "high_risk_wallets": 23,
  "anomalies_detected": 12
}
```

**Example:**
```bash
curl http://localhost:8000/api/analytics/overview
```

---

#### GET /analytics/trends
Get risk trends over time (coming soon).

---

### Authentication

#### POST /auth/register
Register new user (coming soon).

#### POST /auth/api-key
Create new API key (coming soon).

**Request Body:**
```json
{
  "email": "user@example.com",
  "tier": "free"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid wallet address format"
}
```

### 404 Not Found
```json
{
  "detail": "Wallet not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Current limits (MVP):
- Free tier: 100 requests/hour
- No authentication required yet

Future tiers:
- Free: 100 req/hour
- Pro: 10,000 req/hour
- Enterprise: Unlimited

---

## Data Models

### Wallet
```typescript
{
  address: string;           // Ethereum address
  risk_score: number;        // 0.0 - 1.0
  risk_level: string;        // low, medium, high, critical
  transaction_count: number;
  total_value_in: number;
  total_value_out: number;
  days_active: number;
  unique_counterparties: number;
  last_analysis: string;     // ISO 8601 datetime
}
```

### Risk Levels
- **Low** (0.0 - 0.4): Normal activity
- **Medium** (0.4 - 0.6): Slightly elevated risk
- **High** (0.6 - 0.8): Concerning patterns
- **Critical** (0.8 - 1.0): High risk, investigate

---

## WebSocket (Coming Soon)

Real-time updates for wallet monitoring.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New alert:', data);
};
```

---

## SDK Examples

### Python
```python
import requests

response = requests.get(
    'http://localhost:8000/api/wallets/0x...'
)
data = response.json()
print(f"Risk Level: {data['risk_level']}")
```

### JavaScript
```javascript
const response = await fetch(
    'http://localhost:8000/api/wallets/0x...'
);
const data = await response.json();
console.log(`Risk Level: ${data.risk_level}`);
```

### cURL
```bash
curl -X GET \
  'http://localhost:8000/api/wallets/0x...' \
  -H 'Content-Type: application/json'
```

---

## Interactive Documentation

Visit http://localhost:8000/docs for interactive Swagger UI documentation where you can:
- Test endpoints directly
- View request/response schemas
- See example values
- Download OpenAPI spec

Alternative ReDoc UI: http://localhost:8000/redoc

---

## Support

For API support or bug reports:
- GitHub Issues: https://github.com/yourusername/ai-analytics/issues
- Email: api@aianalytics.io
