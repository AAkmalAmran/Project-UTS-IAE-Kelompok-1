# 🚌 Project Summary - Sistem Transportasi Umum Terintegrasi

## 📌 Overview

Sistem microservices lengkap untuk manajemen transportasi umum dengan fitur:
- ✅ Manajemen Rute & Halte
- ✅ Tracking Bus Real-time
- ✅ Jadwal Keberangkatan
- ✅ **ETA (Estimated Time of Arrival) Real-time**
- ✅ Autentikasi & Autorisasi
- ✅ CRUD Operations untuk Admin
- ✅ Public API untuk User

---

## 🏗️ Arsitektur Microservices

```
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Optional)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┬──────────────┐
        │                  │                  │              │
        ▼                  ▼                  ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ USER SERVICE │  │ROUTE SERVICE │  │ STOP SERVICE │  │  BUS SERVICE │
│   :5001      │  │   :5002      │  │   :5003      │  │   :5004      │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       │                 └─────────┬───────┴─────────────────┘
       │                           │
       │                           ▼
       │                  ┌──────────────────┐
       └─────────────────►│ SCHEDULE SERVICE │
                          │      :5005       │
                          └──────────────────┘
```

---

## 📦 Services yang Telah Dibuat

### 1. **User Service** (Port 5001)
**Status:** ✅ Existing (sudah ada sebelumnya)

**Fungsi:**
- Autentikasi user (login/register)
- JWT token generation
- Admin verification untuk CRUD operations

**Endpoints:**
- `POST /login` - Login user
- `POST /register` - Register user baru
- `GET /verify-admin` - Verify admin token

---

### 2. **Route Service** (Port 5002)
**Status:** ✅ **BARU DIBUAT**

**Fungsi:**
- Manajemen rute transportasi
- Urutan halte dalam rute
- Jarak antar halte (1 km default)
- Integrasi dengan Bus & Stop Service

**Files Created:**
- ✅ `models.py` - Route & RouteStop models
- ✅ `app.py` - Flask app dengan CRUD endpoints
- ✅ `requirements.txt`
- ✅ `.env.example`
- ✅ `dockerfile`
- ✅ `README.md` - Dokumentasi lengkap

**Key Features:**
- User endpoints (GET only): `/routes`, `/routes/{id}`, `/routes/{id}/stops`, `/routes/nearby`
- Admin endpoints (CRUD): `/admin/routes/add`, `/admin/routes/{id}` (PUT/DELETE)
- Integrasi dengan Bus Service: `/routes/{id}/buses`
- Sample data: 3 rute (Rute A, Rute B, Koridor 1)

---

### 3. **Stop Service** (Port 5003)
**Status:** ✅ **UPDATED** (ditambahkan CRUD admin)

**Fungsi:**
- Manajemen halte/stasiun
- Informasi fasilitas halte
- Koordinat GPS halte

**Updates:**
- ✅ Added admin authentication middleware
- ✅ Added admin CRUD endpoints
- ✅ Added `GET /stops` untuk list semua halte
- ✅ Updated requirements.txt (tambah requests)

**New Admin Endpoints:**
- `GET /admin/stops` - List semua halte
- `POST /admin/stops/add` - Tambah halte baru
- `PUT /admin/stops/{id}` - Update halte
- `DELETE /admin/stops/{id}` - Hapus halte

**Sample Data:**
- 20 halte (10 arah Baleendah→BEC, 10 arah BEC→Baleendah)

---

### 4. **Bus Service** (Port 5004)
**Status:** ✅ **UPDATED** (ditambahkan integrasi & speed tracking)

**Fungsi:**
- Manajemen bus
- Real-time GPS tracking
- Speed tracking (current & average)
- Assignment bus ke rute
- Status operasional

**Files Created/Updated:**
- ✅ `models.py` - **BARU** (Bus model dengan route & speed fields)
- ✅ `app.py` - **UPDATED** (integrasi route, speed tracking)
- ✅ `README.md` - **BARU** (dokumentasi lengkap)

**New Features:**
- **Speed Tracking:**
  - `average_speed` (km/jam) - untuk estimasi ETA
  - `current_speed` (km/jam) - dari GPS real-time
- **Route Integration:**
  - `route_id` & `route_name` fields
  - Validasi ke Route Service saat assign
- **Operational Status:**
  - Available, In Service, Maintenance, Out of Service

**New Endpoints:**
- `GET /buses?route_id={id}` - Filter bus by route
- `PUT /buses/{id}/route` - Assign bus ke rute
- `DELETE /buses/{id}/route` - Unassign bus
- `PUT /buses/{id}/speed` - Update average speed
- `PUT /buses/{id}/status` - Update operational status
- `GET /routes/{id}/buses` - Get buses on route

**Sample Data:**
- 6 bus dengan berbagai status dan assignment

---

### 5. **Schedule Service** (Port 5005)
**Status:** ✅ **BARU DIBUAT** (Service Integrator)

**Fungsi:**
- Jadwal keberangkatan static
- **ETA calculation real-time** ⭐
- Prediksi kedatangan bus di halte
- Integrasi dengan semua service

**Files Created:**
- ✅ `models.py` - Schedule & BusArrival models
- ✅ `app.py` - Flask app dengan ETA calculation
- ✅ `requirements.txt`
- ✅ `.env.example`
- ✅ `dockerfile`
- ✅ `README.md` - Dokumentasi lengkap

**Key Features:**

**A. Jadwal Keberangkatan**
- Static schedules per route
- Departure time & frequency
- Operating days

**B. ETA Real-time** ⭐ **FUNGSI KUNCI**
```python
GET /eta?busId=1&stopId=5

# Workflow:
1. Get bus location dari Bus Service
2. Get stop location dari Stop Service
3. Calculate distance (Haversine formula)
4. Calculate ETA = (distance / speed) * 60
5. Return prediction
```

**C. Arrivals per Stop**
```python
GET /stops/{stopId}/arrivals

# Return: List bus yang akan tiba, sorted by ETA
```

**D. Next Departures**
```python
GET /routes/{routeId}/next-departures

# Return: Jadwal keberangkatan berikutnya
```

**Integration:**
- Route Service: Get route info
- Stop Service: Get stop coordinates
- Bus Service: Get bus location & speed
- User Service: Admin authentication

**Sample Data:**
- 4 jadwal untuk berbagai rute

---

## 🔗 Integrasi Antar Service

### Service Dependencies

```
User Service (5001)
    ↓ (verify-admin)
    ├─→ Route Service (5002)
    ├─→ Stop Service (5003)
    ├─→ Bus Service (5004)
    └─→ Schedule Service (5005)

Route Service (5002)
    ↔ Stop Service (5003) - validate stop_id
    ↔ Bus Service (5004) - get buses on route

Bus Service (5004)
    → Route Service (5002) - validate route_id

Schedule Service (5005) - INTEGRATOR
    → Route Service (5002) - get route info
    → Stop Service (5003) - get stop location
    → Bus Service (5004) - get bus location & speed
```

### Key Integration Points

1. **Admin Authentication** (All Services → User Service)
   - Semua admin endpoint verify token ke User Service
   - Header: `Authorization: Bearer <token>`

2. **Bus-Route Assignment** (Bus ↔ Route)
   - Bus Service validate route_id ke Route Service
   - Route Service query buses dari Bus Service

3. **ETA Calculation** (Schedule → Bus + Stop)
   - Get bus GPS coordinates
   - Get stop GPS coordinates
   - Calculate distance & ETA

---

## 📊 Database Schema

### Route Service
```sql
routes: id, name, description, origin, destination, is_active
route_stops: id, route_id, stop_id, stop_name, sequence_order, 
             distance_to_next, time_to_next
```

### Stop Service
```sql
stops: id, name, address, latitude, longitude,
       shelter, seating, lighting, wheelchair_access,
       guiding_block, digital_eta_display, charging_port
```

### Bus Service
```sql
buses: id, nomor_polisi, kapasitas_penumpang, model_kendaraan,
       status_gps, latitude, longitude,
       route_id, route_name,
       average_speed, current_speed, operational_status
```

### Schedule Service
```sql
schedules: id, route_id, route_name, bus_id, bus_number,
           departure_time, operating_days, frequency_minutes, is_active

bus_arrivals: id, stop_id, stop_name, bus_id, bus_number,
              route_id, route_name, eta_minutes, distance_km,
              status, predicted_at
```

---

## 🚀 Quick Start Guide

### 1. Setup Environment

```bash
# Clone repository
cd Project-UTS-IAE-Kelompok-1

# Install dependencies untuk setiap service
cd service-1-route && pip install -r requirements.txt && cd ..
cd service-2-stop && pip install -r requirements.txt && cd ..
cd service-3-bus && pip install -r requirements.txt && cd ..
cd service-4-schedule && pip install -r requirements.txt && cd ..
```

### 2. Initialize Databases

```bash
# Route Service
cd service-1-route
flask init-db
flask seed-routes

# Stop Service
cd ../service-2-stop
flask init-db
flask seed-stops

# Bus Service
cd ../service-3-bus
flask init-db
flask seed-buses

# Schedule Service
cd ../service-4-schedule
flask init-db
flask seed-schedules
```

### 3. Run All Services

```bash
# Terminal 1 - User Service
cd service-user
python app.py  # Port 5001

# Terminal 2 - Route Service
cd service-1-route
python app.py  # Port 5002

# Terminal 3 - Stop Service
cd service-2-stop
python app.py  # Port 5003

# Terminal 4 - Bus Service
cd service-3-bus
python app.py  # Port 5004

# Terminal 5 - Schedule Service
cd service-4-schedule
python app.py  # Port 5005
```

### 4. Test Integration

```bash
# 1. Login admin
curl -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Save token dari response

# 2. Assign bus ke rute
curl -X PUT http://localhost:5004/buses/1/route \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"route_id": 1}'

# 3. Update lokasi bus (simulate GPS)
curl -X PUT http://localhost:5004/buses/1/location \
  -H "Content-Type: application/json" \
  -d '{"latitude": -6.9195, "longitude": 107.6105, "current_speed": 42}'

# 4. Calculate ETA
curl "http://localhost:5005/eta?busId=1&stopId=5"

# 5. Check arrivals at stop
curl "http://localhost:5005/stops/5/arrivals"
```

---

## 📝 API Endpoints Summary

### Public Endpoints (No Auth)

| Service | Endpoint | Method | Description |
|---------|----------|--------|-------------|
| Route | `/routes` | GET | List semua rute |
| Route | `/routes/{id}` | GET | Detail rute |
| Route | `/routes/{id}/stops` | GET | Halte dalam rute |
| Route | `/routes/{id}/buses` | GET | Bus di rute |
| Stop | `/stops` | GET | List semua halte |
| Stop | `/stops/{id}` | GET | Detail halte |
| Stop | `/stops/search` | GET | Cari halte |
| Bus | `/buses` | GET | List semua bus |
| Bus | `/buses/{id}` | GET | Detail bus |
| Bus | `/buses/{id}/location` | PUT | Update GPS |
| Schedule | `/schedules/{routeId}` | GET | Jadwal rute |
| **Schedule** | **`/eta`** | **GET** | **ETA real-time** ⭐ |
| Schedule | `/stops/{id}/arrivals` | GET | Bus yang akan tiba |

### Admin Endpoints (Auth Required)

| Service | Endpoint | Method | Description |
|---------|----------|--------|-------------|
| Route | `/admin/routes/add` | POST | Tambah rute |
| Route | `/admin/routes/{id}` | PUT/DELETE | Edit/Hapus rute |
| Stop | `/admin/stops/add` | POST | Tambah halte |
| Stop | `/admin/stops/{id}` | PUT/DELETE | Edit/Hapus halte |
| Bus | `/buses` | POST | Daftar bus |
| Bus | `/buses/{id}/route` | PUT/DELETE | Assign/Unassign |
| Bus | `/buses/{id}/speed` | PUT | Update speed |
| Schedule | `/admin/schedules/add` | POST | Tambah jadwal |
| Schedule | `/admin/schedules/{id}` | PUT/DELETE | Edit/Hapus jadwal |

---

## 🎯 Key Achievements

### ✅ Completed Features

1. **Full Microservices Architecture**
   - 5 independent services
   - Each with own database
   - RESTful API design

2. **Authentication & Authorization**
   - JWT-based authentication
   - Role-based access (Admin/User)
   - Admin verification across services

3. **Route Management**
   - CRUD operations
   - Stop sequences with distances
   - Integration with Bus Service

4. **Stop Management**
   - CRUD operations
   - Facility information
   - GPS coordinates

5. **Bus Management**
   - CRUD operations
   - Real-time GPS tracking
   - Speed tracking (current & average)
   - Route assignment
   - Operational status

6. **Schedule & ETA**
   - Static schedules
   - **Real-time ETA calculation** ⭐
   - Haversine distance formula
   - Arrivals prediction per stop
   - Integration with all services

7. **Data Seeding**
   - 3 routes with stops
   - 20 stops (bidirectional)
   - 6 buses with assignments
   - 4 schedules

8. **Documentation**
   - README for each service
   - Integration guide
   - API documentation
   - Setup instructions

---

## 📂 Project Structure

```
Project-UTS-IAE-Kelompok-1/
├── service-user/              # User Service (existing)
│   ├── app.py
│   └── ...
│
├── service-1-route/           # Route Service (NEW)
│   ├── models.py             ✅ NEW
│   ├── app.py                ✅ NEW
│   ├── requirements.txt      ✅ NEW
│   ├── .env.example          ✅ NEW
│   ├── dockerfile            ✅ NEW
│   └── README.md             ✅ NEW
│
├── service-2-stop/            # Stop Service (UPDATED)
│   ├── models.py
│   ├── app.py                ✅ UPDATED (admin CRUD)
│   ├── requirements.txt      ✅ UPDATED (requests)
│   └── ...
│
├── service-3-bus/             # Bus Service (UPDATED)
│   ├── models.py             ✅ NEW
│   ├── app.py                ✅ UPDATED (integration)
│   ├── README.md             ✅ NEW
│   └── ...
│
├── service-4-schedule/        # Schedule Service (NEW)
│   ├── models.py             ✅ NEW
│   ├── app.py                ✅ NEW
│   ├── requirements.txt      ✅ NEW
│   ├── .env.example          ✅ NEW
│   ├── dockerfile            ✅ NEW
│   └── README.md             ✅ NEW
│
├── INTEGRATION_GUIDE.md       ✅ NEW - Panduan integrasi lengkap
├── PROJECT_SUMMARY.md         ✅ NEW - Summary ini
└── docker-compose.yml
```

---

## 🔧 Technologies Used

- **Backend:** Flask (Python)
- **Database:** SQLite (SQLAlchemy ORM)
- **Authentication:** JWT
- **Inter-service Communication:** HTTP/REST (requests library)
- **Geospatial:** Haversine formula
- **Containerization:** Docker
- **Documentation:** Markdown

---

## 📈 Sample Data Overview

### Routes
1. **Rute A**: Masjid → Matahari Land (6 halte, 5 km)
2. **Rute B**: BEC → Baleendah (6 halte, 5 km)
3. **Koridor 1**: Stasiun Bandung → BEC (3 halte, 2 km)

### Stops
- 20 halte total (bidirectional)
- Koordinat GPS real
- Fasilitas lengkap

### Buses
1. B 1234 ABC - Mercedes (Rute A, 45 km/h)
2. B 5678 DEF - Hino (Rute A, 42 km/h)
3. B 9012 GHI - Scania (Rute B, 48 km/h)
4. B 3456 JKL - Isuzu (Koridor 1, 40 km/h)
5. B 7890 MNO - Mercedes (Available, 44 km/h)
6. B 1122 PQR - Hino (Maintenance, 43 km/h)

### Schedules
- 4 jadwal dengan frekuensi berbeda
- Operating hours: 06:00 - 22:00
- Frequency: 15-30 menit

---

## 🎓 Learning Outcomes

1. **Microservices Architecture**
   - Service decomposition
   - Inter-service communication
   - Data consistency

2. **RESTful API Design**
   - Resource-based endpoints
   - HTTP methods
   - Status codes

3. **Authentication & Authorization**
   - JWT implementation
   - Role-based access control
   - Token verification

4. **Database Design**
   - Normalization
   - Foreign keys
   - Denormalization for performance

5. **Geospatial Calculations**
   - Haversine formula
   - Distance calculation
   - ETA prediction

6. **Integration Patterns**
   - Service discovery
   - API composition
   - Error handling

---

## 🚀 Next Steps (Future Enhancements)

- [ ] API Gateway implementation
- [ ] WebSocket for real-time updates
- [ ] Mobile app integration
- [ ] Machine learning for ETA accuracy
- [ ] Traffic prediction
- [ ] Push notifications
- [ ] Payment integration
- [ ] Route optimization
- [ ] Analytics dashboard
- [ ] Load balancing
- [ ] Service mesh (Istio)

---

## 📞 Documentation Links

- **Integration Guide:** `INTEGRATION_GUIDE.md`
- **Route Service:** `service-1-route/README.md`
- **Bus Service:** `service-3-bus/README.md`
- **Schedule Service:** `service-4-schedule/README.md`

---

## ✨ Highlights

### 🌟 **ETA Real-time Calculation**
Fitur unggulan yang menghitung waktu kedatangan bus secara real-time menggunakan:
- GPS location dari bus
- Koordinat halte
- Haversine distance formula
- Kecepatan rata-rata bus

### 🔄 **Full Integration**
Semua 5 services terintegrasi dengan baik:
- User → All (authentication)
- Route ↔ Stop (validation)
- Route ↔ Bus (assignment)
- Schedule → All (aggregation)

### 📱 **User-Friendly API**
- Public endpoints untuk user
- Admin endpoints dengan authentication
- Clear error messages
- Comprehensive documentation

---

**Project Status:** ✅ **COMPLETED**

Semua requirement telah terpenuhi:
- ✅ Route Service dengan CRUD
- ✅ Stop Service dengan CRUD admin
- ✅ Bus Service dengan speed & route integration
- ✅ Schedule Service dengan ETA real-time
- ✅ Full integration antar semua service
- ✅ Documentation lengkap
