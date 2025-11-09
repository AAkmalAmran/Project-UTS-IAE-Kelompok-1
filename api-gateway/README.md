# 🚪 API Gateway - Transport System

## 📌 Overview

API Gateway adalah **single entry point** untuk semua microservices dalam sistem transportasi. Gateway ini menangani routing, authentication, rate limiting, dan logging untuk semua request.

## 🎯 Fungsi Utama

### 1. **Single Entry Point**
- Client hanya perlu tahu **1 endpoint**: `http://localhost:8080`
- Tidak perlu tahu port masing-masing service (5001-5005)

### 2. **Request Routing**
Mengarahkan request ke service yang tepat:
- `/api/auth/*` → User Service (5001)
- `/api/routes/*` → Route Service (5002)
- `/api/stops/*` → Stop Service (5003)
- `/api/buses/*` → Bus Service (5004)
- `/api/schedules/*` → Schedule Service (5005)

### 3. **Centralized Authentication**
- Validasi JWT token di gateway
- Middleware `authenticateAdmin` untuk endpoint admin
- Token verification via User Service

### 4. **Rate Limiting**
- Maksimal 100 request per 15 menit per IP
- Mencegah abuse dan DDoS attack

### 5. **CORS Handling**
- Configured untuk accept request dari semua origin
- Support untuk mobile/web apps

### 6. **Logging & Monitoring**
- Request logging dengan Morgan
- Error tracking
- Health check endpoint

---

## 🚀 Quick Start

### Development (Local)

1. **Install Dependencies**
```bash
cd api-gateway
npm install
```

2. **Setup Environment**
```bash
# Copy .env.example ke .env
cp .env.example .env

# Edit .env untuk local development
# Gunakan localhost URLs
```

3. **Run Gateway**
```bash
npm start
# atau untuk development dengan auto-reload
npm run dev
```

Gateway akan berjalan di `http://localhost:8080`

### Production (Docker)

```bash
# Build dan run semua services termasuk gateway
docker-compose up --build

# Atau hanya gateway
docker-compose up api-gateway
```

---

## 📡 API Endpoints

### Gateway Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Gateway info |
| `/health` | GET | Health check |
| `/api/docs` | GET | API documentation |

### Service Routes

#### 1. Authentication (`/api/auth/*`)
```bash
POST /api/auth/login
POST /api/auth/register
GET  /api/auth/verify-admin
```

#### 2. Routes (`/api/routes/*`)
```bash
# Public
GET  /api/routes
GET  /api/routes/:id
GET  /api/routes/:id/stops
GET  /api/routes/:id/buses
GET  /api/routes/nearby

# Admin (requires token)
POST   /api/routes/admin/add
PUT    /api/routes/admin/:id
DELETE /api/routes/admin/:id
```

#### 3. Stops (`/api/stops/*`)
```bash
# Public
GET  /api/stops
GET  /api/stops/:id
GET  /api/stops/search

# Admin (requires token)
POST   /api/stops/admin/add
PUT    /api/stops/admin/:id
DELETE /api/stops/admin/:id
```

#### 4. Buses (`/api/buses/*`)
```bash
# Public
GET /api/buses
GET /api/buses/:id
PUT /api/buses/:id/location

# Admin (requires token)
POST /api/buses
PUT  /api/buses/:id/route
PUT  /api/buses/:id/speed
```

#### 5. Schedules & ETA (`/api/schedules/*`)
```bash
# Public
GET /api/schedules/:routeId
GET /api/schedules/eta
GET /api/schedules/stops/:id/arrivals
GET /api/schedules/:routeId/next-departures

# Admin (requires token)
POST   /api/schedules/admin/add
PUT    /api/schedules/admin/:id
DELETE /api/schedules/admin/:id
```

---

## 🧪 Testing Examples

### 1. Health Check
```bash
curl http://localhost:8080/health
```

### 2. Get API Documentation
```bash
curl http://localhost:8080/api/docs
```

### 3. Login (via Gateway)
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### 4. Get All Routes (via Gateway)
```bash
curl http://localhost:8080/api/routes
```

### 5. Get ETA (via Gateway)
```bash
curl "http://localhost:8080/api/schedules/eta?busId=1&stopId=5"
```

### 6. Admin Operation (Add Route)
```bash
# First, login to get token
TOKEN="your-jwt-token-here"

curl -X POST http://localhost:8080/api/routes/admin/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rute Baru",
    "description": "Rute test",
    "origin": "Terminal A",
    "destination": "Terminal B"
  }'
```

---

## 🔧 Configuration

### Environment Variables (`.env`)

```env
# Server
PORT=8080
NODE_ENV=development

# Microservices URLs (Docker)
USER_SERVICE_URL=http://service-user:5001
ROUTE_SERVICE_URL=http://service-1-route:5002
STOP_SERVICE_URL=http://service-2-stop:5003
BUS_SERVICE_URL=http://service-3-bus:5004
SCHEDULE_SERVICE_URL=http://service-4-schedule:5005

# For local development (without Docker)
# USER_SERVICE_URL=http://localhost:5001
# ROUTE_SERVICE_URL=http://localhost:5002
# etc...

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│          Client (Web/Mobile)            │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│          API Gateway :8080              │
│  ┌─────────────────────────────────┐   │
│  │ • Request Routing               │   │
│  │ • Authentication                │   │
│  │ • Rate Limiting                 │   │
│  │ • CORS Handling                 │   │
│  │ • Logging                       │   │
│  └─────────────────────────────────┘   │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┬──────────┐
        │          │          │          │
        ▼          ▼          ▼          ▼
    ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
    │User │   │Route│   │Stop │   │ Bus │
    │5001 │   │5002 │   │5003 │   │5004 │
    └─────┘   └─────┘   └─────┘   └─────┘
                   │
                   ▼
              ┌─────────┐
              │Schedule │
              │  5005   │
              └─────────┘
```

---

## 🔐 Security Features

### 1. **JWT Authentication**
- Token validation via User Service
- Middleware protection untuk admin endpoints

### 2. **Rate Limiting**
- IP-based limiting
- Configurable window & max requests

### 3. **CORS Protection**
- Controlled origin access
- Whitelisted methods & headers

### 4. **Error Handling**
- Graceful error responses
- No sensitive data exposure
- Detailed logging

---

## 📊 Monitoring

### Health Check Response
```json
{
  "status": "healthy",
  "service": "API Gateway",
  "timestamp": "2024-01-09T10:30:00.000Z",
  "services": {
    "USER": "http://service-user:5001",
    "ROUTE": "http://service-1-route:5002",
    "STOP": "http://service-2-stop:5003",
    "BUS": "http://service-3-bus:5004",
    "SCHEDULE": "http://service-4-schedule:5005"
  }
}
```

### Logs
Gateway menggunakan Morgan untuk logging:
```
[PROXY] GET /api/routes -> http://service-1-route:5002/routes
[PROXY] POST /api/auth/login -> http://service-user:5001/login
```

---

## 🐛 Troubleshooting

### Gateway tidak bisa connect ke service

**Problem:** `Service temporarily unavailable`

**Solution:**
1. Pastikan semua services running
2. Check docker network: `docker network inspect project-uts-iae-kelompok-1_my_app_network`
3. Verify service URLs di `.env`

### Authentication gagal

**Problem:** `Authentication failed`

**Solution:**
1. Pastikan User Service running
2. Check token format: `Bearer <token>`
3. Verify token belum expired

### Rate limit exceeded

**Problem:** `Too many requests`

**Solution:**
1. Wait 15 menit
2. Atau adjust `RATE_LIMIT_MAX_REQUESTS` di `.env`

---

## 🚀 Advanced Features

### Custom Middleware

Tambahkan middleware custom di `index.js`:

```javascript
// Request ID untuk tracking
app.use((req, res, next) => {
  req.id = Math.random().toString(36).substr(2, 9);
  console.log(`[${req.id}] ${req.method} ${req.path}`);
  next();
});
```

### Response Caching

Tambahkan caching untuk performance:

```javascript
const cache = require('express-cache-middleware');
app.use('/api/routes', cache({ ttl: 60 })); // Cache 60 detik
```

### Load Balancing

Jika ada multiple instances:

```javascript
const ROUTE_SERVICES = [
  'http://route-1:5002',
  'http://route-2:5002',
  'http://route-3:5002'
];

// Round-robin load balancing
let currentIndex = 0;
const getRouteService = () => {
  const service = ROUTE_SERVICES[currentIndex];
  currentIndex = (currentIndex + 1) % ROUTE_SERVICES.length;
  return service;
};
```

---

## 📦 Dependencies

```json
{
  "express": "^4.18.2",
  "http-proxy-middleware": "^2.0.6",
  "cors": "^2.8.5",
  "express-rate-limit": "^6.7.0",
  "morgan": "^1.10.0",
  "dotenv": "^16.0.3",
  "axios": "^1.4.0"
}
```

---

## 🎓 Benefits

### Untuk Client/Frontend:
✅ Single endpoint untuk semua API  
✅ Simplified authentication  
✅ No CORS issues  
✅ Consistent error handling  

### Untuk Backend:
✅ Centralized security  
✅ Service isolation  
✅ Easy to add new services  
✅ Simplified microservice code  

### Untuk DevOps:
✅ Centralized monitoring  
✅ Easy deployment  
✅ Load balancing ready  
✅ Better logging  

---

## 📞 Support

Untuk pertanyaan atau issues, check:
- Main README: `../readme.md`
- API Documentation: `http://localhost:8080/api/docs`
- Health Check: `http://localhost:8080/health`

---

**Status:** ✅ Production Ready

API Gateway siap digunakan untuk production dengan semua fitur security, monitoring, dan error handling yang diperlukan.
