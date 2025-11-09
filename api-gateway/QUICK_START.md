# 🚀 Quick Start - API Gateway

## Cara Cepat Menjalankan API Gateway

### Option 1: Dengan Docker (Recommended)

```bash
# 1. Copy environment file
cd api-gateway
cp .env.example .env

# 2. Kembali ke root project
cd ..

# 3. Build dan run semua services
docker-compose up --build

# Gateway akan berjalan di http://localhost:8080
```

### Option 2: Local Development (Tanpa Docker)

```bash
# 1. Install dependencies
cd api-gateway
npm install

# 2. Setup environment untuk local
cp .env.example .env

# 3. Edit .env - gunakan localhost URLs
# USER_SERVICE_URL=http://localhost:5001
# ROUTE_SERVICE_URL=http://localhost:5002
# dst...

# 4. Pastikan semua services sudah running di port masing-masing

# 5. Run gateway
npm start
```

---

## ✅ Testing Gateway

### 1. Check Health
```bash
curl http://localhost:8080/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "API Gateway",
  "timestamp": "2024-01-09T10:30:00.000Z"
}
```

### 2. View Documentation
```bash
curl http://localhost:8080/api/docs
```

### 3. Test Login via Gateway
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 4. Get Routes via Gateway
```bash
curl http://localhost:8080/api/routes
```

### 5. Get Real-time ETA
```bash
curl "http://localhost:8080/api/schedules/eta?busId=1&stopId=5"
```

---

## 🔑 Admin Operations

```bash
# 1. Login dulu
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.token')

# 2. Add new route (admin only)
curl -X POST http://localhost:8080/api/routes/admin/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rute Test",
    "description": "Testing route",
    "origin": "Point A",
    "destination": "Point B"
  }'

# 3. Add new stop (admin only)
curl -X POST http://localhost:8080/api/stops/admin/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Halte Test",
    "address": "Jl. Test No. 1",
    "latitude": -6.9175,
    "longitude": 107.6191
  }'
```

---

## 📊 Monitoring

### View Logs
```bash
# Docker
docker-compose logs -f api-gateway

# Local
# Logs akan muncul di console
```

### Check Service Status
```bash
# Check all containers
docker-compose ps

# Check specific service
docker-compose ps api-gateway
```

---

## 🐛 Common Issues

### Issue: "Service temporarily unavailable"
**Solution:** Pastikan semua microservices running
```bash
docker-compose ps
# Semua services harus status "Up"
```

### Issue: "ECONNREFUSED"
**Solution:** Check service URLs di `.env`
```bash
# Untuk Docker, gunakan service names:
USER_SERVICE_URL=http://service-user:5001

# Untuk local, gunakan localhost:
USER_SERVICE_URL=http://localhost:5001
```

### Issue: Port 8080 already in use
**Solution:** Stop process yang menggunakan port 8080
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8080 | xargs kill -9
```

---

## 🎯 Next Steps

1. ✅ Gateway running
2. ✅ Test basic endpoints
3. ✅ Test authentication
4. 📱 Integrate dengan frontend/mobile app
5. 📊 Setup monitoring dashboard
6. 🚀 Deploy to production

---

## 📚 More Info

- Full Documentation: `README.md`
- API Endpoints: `http://localhost:8080/api/docs`
- Main Project: `../readme.md`
