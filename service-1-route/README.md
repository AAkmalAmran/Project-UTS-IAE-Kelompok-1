# Route Service - Layanan Data Rute Transportasi Umum

Service ini mengelola data rute transportasi umum, termasuk informasi jalur yang dilewati dan urutan halte.

## Fitur Utama

- **User Endpoints (Public - GET Only)**: User biasa hanya dapat melihat data rute
- **Admin Endpoints (CRUD)**: Admin dapat mengelola rute secara penuh dengan autentikasi Basic Auth
- **Integrasi dengan Stop Service**: Menggunakan stop_id dari Stop Service
- **Jarak Antar Halte**: Setiap rute menyimpan jarak antar halte (default: 1 km)

## Data yang Dikelola

### Route (Rute)
- **routeId**: ID Rute (Primary Key)
- **name**: Nama Rute (misal: "Rute A", "Koridor 1")
- **description**: Deskripsi Rute
- **origin**: Titik Awal (Origin)
- **destination**: Titik Akhir (Destination)
- **isActive**: Status Aktif/Tidak Aktif

### RouteStop (Halte dalam Rute)
- **routeStopId**: ID RouteStop
- **stopId**: ID Halte (referensi ke Stop Service)
- **stopName**: Nama Halte
- **sequenceOrder**: Urutan halte dalam rute (1, 2, 3, ...)
- **distanceToNext**: Jarak ke halte berikutnya (km)
- **timeToNext**: Estimasi waktu tempuh ke halte berikutnya (menit)

## API Endpoints

### 🔓 User Endpoints (Public - GET Only)

#### 1. GET `/routes`
Mendapatkan daftar semua rute yang tersedia (hanya rute aktif).

**Response:**
```json
{
  "total": 3,
  "routes": [
    {
      "routeId": 1,
      "name": "Rute A",
      "description": "Rute dari Masjid Jami Baitul Huda Baleendah ke Matahari Land",
      "origin": "Masjid Jami Baitul Huda Baleendah",
      "destination": "Matahari Land",
      "isActive": true
    }
  ]
}
```

#### 2. GET `/routes/{routeId}`
Mendapatkan detail rute termasuk daftar halte.

**Response:**
```json
{
  "routeId": 1,
  "name": "Rute A",
  "description": "Rute dari Masjid Jami Baitul Huda Baleendah ke Matahari Land",
  "origin": "Masjid Jami Baitul Huda Baleendah",
  "destination": "Matahari Land",
  "isActive": true,
  "stops": [...],
  "totalStops": 6,
  "totalDistance": 5.0
}
```

#### 3. GET `/routes/{routeId}/stops`
Mendapatkan urutan halte pada rute tertentu.

**Response:**
```json
{
  "routeId": 1,
  "routeName": "Rute A",
  "origin": "Masjid Jami Baitul Huda Baleendah",
  "destination": "Matahari Land",
  "totalStops": 6,
  "totalDistance": 5.0,
  "stops": [
    {
      "routeStopId": 1,
      "stopId": 2,
      "stopName": "Masjid Jami Baitul Huda Baleendah",
      "sequenceOrder": 1,
      "distanceToNext": 1.0,
      "timeToNext": 3
    }
  ]
}
```

#### 4. GET `/routes/nearby?lat=x&lon=y&radius=z`
Mencari rute yang melewati area geografis tertentu.

**Query Parameters:**
- `lat`: Latitude lokasi user (required)
- `lon`: Longitude lokasi user (required)
- `radius`: Radius pencarian dalam km (default: 5)

**Response:**
```json
{
  "userLocation": {
    "latitude": -6.9195,
    "longitude": 107.6105
  },
  "radius": 5,
  "total": 2,
  "routes": [...]
}
```

#### 5. GET `/routes/search?query=nama`
Mencari rute berdasarkan nama atau deskripsi.

**Query Parameters:**
- `query`: Kata kunci pencarian (required)

**Response:**
```json
{
  "query": "Masjid",
  "total": 1,
  "routes": [...]
}
```

---

### 🔐 Admin Endpoints (Requires Authentication)

**Authentication:** Basic Auth
- Username: `admin` (default, dapat diubah via environment variable)
- Password: `admin123` (default, dapat diubah via environment variable)

#### 1. GET `/admin/routes`
Admin dapat melihat semua rute (termasuk yang tidak aktif).

**Headers:**
```
Authorization: Basic YWRtaW46YWRtaW4xMjM=
```

#### 2. POST `/admin/routes/add`
Menambahkan rute baru.

**Request Body:**
```json
{
  "name": "Rute D",
  "description": "Rute baru dari A ke B",
  "origin": "Lokasi A",
  "destination": "Lokasi B",
  "isActive": true,
  "stops": [
    {
      "stopId": 1,
      "stopName": "Halte A",
      "distanceToNext": 1.0,
      "timeToNext": 3
    },
    {
      "stopId": 2,
      "stopName": "Halte B",
      "distanceToNext": null,
      "timeToNext": null
    }
  ]
}
```

#### 3. PUT `/admin/routes/{routeId}`
Mengupdate informasi rute.

**Request Body:**
```json
{
  "name": "Rute A Updated",
  "description": "Deskripsi baru",
  "isActive": false
}
```

#### 4. DELETE `/admin/routes/{routeId}`
Menghapus rute (cascade delete semua route_stops).

#### 5. POST `/admin/routes/{routeId}/stops/add`
Menambahkan halte ke rute.

**Request Body:**
```json
{
  "stopId": 5,
  "stopName": "Museum Kota Bandung",
  "sequenceOrder": 3,
  "distanceToNext": 1.0,
  "timeToNext": 3
}
```

#### 6. PUT `/admin/routes/{routeId}/stops/{routeStopId}`
Mengupdate informasi halte dalam rute.

**Request Body:**
```json
{
  "sequenceOrder": 4,
  "distanceToNext": 1.5,
  "timeToNext": 5
}
```

#### 7. DELETE `/admin/routes/{routeId}/stops/{routeStopId}`
Menghapus halte dari rute.

---

## Setup & Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables
```bash
cp .env.example .env
# Edit .env sesuai kebutuhan
```

### 3. Initialize Database
```bash
flask init-db
```

### 4. Seed Data (Optional)
```bash
flask seed-routes
```

### 5. Run Development Server
```bash
python app.py
```

Server akan berjalan di `http://localhost:5002`

---

## Docker Deployment

### Build Image
```bash
docker build -t route-service .
```

### Run Container
```bash
docker run -p 5002:5002 route-service
```

---

## Data Seeding

Service ini sudah menyediakan 3 rute sample:

1. **Rute A**: Masjid Jami Baitul Huda Baleendah → Matahari Land (6 halte)
2. **Rute B**: BEC → Baleendah (6 halte)
3. **Koridor 1**: Stasiun Bandung → BEC (3 halte)

Setiap rute menggunakan jarak 1 km antar halte dan estimasi waktu tempuh 3 menit.

---

## Integration dengan Stop Service

Route Service menggunakan `stopId` yang mereferensi ke Stop Service. Pastikan Stop Service sudah berjalan dan memiliki data halte yang sesuai.

**Stop IDs yang digunakan:**
- Stop ID 2-10: Halte arah Baleendah → BEC
- Stop ID 11-20: Halte arah BEC → Baleendah

---

## Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "route-service",
  "database": "connected"
}
```

---

## Security Notes

⚠️ **PENTING**: Dalam production:
1. Ganti `ADMIN_USERNAME` dan `ADMIN_PASSWORD` dengan nilai yang aman
2. Gunakan HTTPS untuk semua komunikasi
3. Implementasikan JWT atau OAuth untuk autentikasi yang lebih robust
4. Jangan commit file `.env` ke repository

---

## Port Configuration

- **Development**: Port 5002
- **Production (Docker)**: Port 5002

Pastikan port ini tidak konflik dengan service lain.
