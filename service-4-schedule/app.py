# type: ignore
import os
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timedelta
from typing import Any, List, Optional, Dict
from math import radians, cos, sin, asin, sqrt
import requests

# Import models
from models import db, Schedule, BusArrival

# Muat variabel lingkungan
load_dotenv()

app = Flask(__name__, instance_relative_config=True)

# Memastikan folder instance ada (untuk SQLite)
os.makedirs(app.instance_path, exist_ok=True)

# Konfigurasi Database
db_path = os.path.join(app.instance_path, 'schedule.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# URLs untuk integrasi dengan service lain
ROUTE_SERVICE_URL = os.environ.get('ROUTE_SERVICE_URL', 'http://localhost:5002')
STOP_SERVICE_URL = os.environ.get('STOP_SERVICE_URL', 'http://localhost:5003')
BUS_SERVICE_URL = os.environ.get('BUS_SERVICE_URL', 'http://localhost:5004')

# Timeout untuk request eksternal (dalam detik)
REQUEST_TIMEOUT = 5
# Radius maksimal untuk pencarian bus di halte (dalam km)
MAX_SEARCH_RADIUS_KM = 10.0

# Inisialisasi Database
db.init_app(app)


# --- Middleware untuk Autentikasi Admin ---
def admin_required(f):
    """Decorator untuk memvalidasi admin credentials."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token tidak ditemukan'}), 401

        try:
            response = requests.get(
                'http://service-user:5001/verify-admin',
                headers={'Authorization': token}
            )
            
            if response.status_code != 200:
                return jsonify({'error': 'Unauthorized - Admin role required'}), 403
                
        except requests.exceptions.RequestException:
            return jsonify({'error': 'Gagal terhubung ke service autentikasi'}), 500
            
        return f(*args, **kwargs)
    return decorated_function


# --- Helper Functions ---

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Menghitung jarak antara dua koordinat geografis menggunakan formula Haversine.
    Return: jarak dalam kilometer
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    r = 6371  # Radius bumi dalam kilometer
    
    return c * r


def calculate_eta(distance_km, average_speed_kmh):
    """
    Menghitung ETA berdasarkan jarak dan kecepatan rata-rata.
    Return: waktu dalam menit
    """
    if average_speed_kmh == 0:
        return 999  # Jika bus tidak bergerak
    
    hours = distance_km / average_speed_kmh
    minutes = hours * 60
    
    return int(minutes)


def get_bus_location(bus_id):
    """
    Mengambil lokasi real-time bus dari Bus Service.
    """
    try:
        response = requests.get(f'{BUS_SERVICE_URL}/buses/{bus_id}', timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f'Warning: Gagal mengambil lokasi bus {bus_id}: {str(e)}')
        return None


def get_stop_location(stop_id):
    """
    Mengambil lokasi halte dari Stop Service.
    """
    try:
        response = requests.get(f'{STOP_SERVICE_URL}/stops/{stop_id}', timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f'Warning: Gagal mengambil lokasi halte {stop_id}: {str(e)}')
        return None


def get_route_info(route_id):
    """
    Mengambil informasi rute dari Route Service.
    """
    try:
        response = requests.get(f'{ROUTE_SERVICE_URL}/routes/{route_id}', timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f'Warning: Gagal mengambil info rute {route_id}: {str(e)}')
        return None


# ========================================
# WEB UI ENDPOINT
# ========================================

@app.route('/')
def index():
    """Serve the web UI"""
    return render_template('index.html')


# ========================================
# ENDPOINTS UNTUK USER (PUBLIC)
# ========================================

@app.route('/schedules', methods=['GET'])
def get_all_schedules():
    """
    GET /schedules[?routeId=x]: Jika `routeId` diberikan, kembalikan hanya jadwal
    untuk rute tersebut. Jika tidak, kembalikan semua jadwal aktif.
    """
    # Normalize parameter names: accept routeId, route_id, routeid, and similarly for busId
    def _get_int_param(variants):
        # Try query params first
        for name in variants:
            val = request.args.get(name)
            if val is not None:
                try:
                    return int(val)
                except (TypeError, ValueError):
                    return None

        # Fallback: try JSON body (some clients send body with GET)
        data = request.get_json(silent=True) or {}
        for name in variants:
            if name in data:
                try:
                    return int(data.get(name))
                except (TypeError, ValueError):
                    return None

        return None

    route_id_param = _get_int_param(['routeId', 'route_id', 'routeid'])
    bus_id_param = _get_int_param(['busId', 'bus_id', 'busid'])

    # Jika kedua parameter diberikan, pastikan kedua cocok (AND)
    if route_id_param is not None and bus_id_param is not None:
        route_id = route_id_param
        bus_id = bus_id_param

        schedules: List[Any] = Schedule.query.filter_by(route_id=route_id, bus_id=bus_id, is_active=True).all()
        if not schedules:
            return jsonify({
                'routeId': route_id,
                'busId': bus_id,
                'total': 0,
                'schedules': [],
                'message': 'Tidak ada jadwal yang cocok untuk kombinasi routeId dan busId ini.'
            }), 200

        route_info = get_route_info(route_id)
        return jsonify({
            'routeId': route_id,
            'busId': bus_id,
            'routeName': route_info.get('name') if route_info else schedules[0].route_name,
            'total': len(schedules),
            'schedules': [schedule.to_dict() for schedule in schedules]
        }), 200

    # Jika hanya routeId diberikan
    if route_id_param is not None:
        route_id = route_id_param
        schedules: List[Any] = Schedule.query.filter_by(route_id=route_id, is_active=True).all()

        if not schedules:
            return jsonify({
                'routeId': route_id,
                'total': 0,
                'schedules': [],
                'message': 'Tidak ada jadwal untuk rute ini.'
            }), 200

        route_info = get_route_info(route_id)
        return jsonify({
            'routeId': route_id,
            'routeName': route_info.get('name') if route_info else schedules[0].route_name,
            'total': len(schedules),
            'schedules': [schedule.to_dict() for schedule in schedules]
        }), 200

    # Jika hanya busId diberikan
    if bus_id_param is not None:
        bus_id = bus_id_param
        schedules: List[Any] = Schedule.query.filter_by(bus_id=bus_id, is_active=True).all()

        if not schedules:
            return jsonify({
                'busId': bus_id,
                'total': 0,
                'schedules': [],
                'message': 'Tidak ada jadwal untuk bus ini.'
            }), 200

        return jsonify({
            'busId': bus_id,
            'total': len(schedules),
            'schedules': [schedule.to_dict() for schedule in schedules]
        }), 200

    # Default: kembalikan semua jadwal aktif
    schedules: List[Any] = Schedule.query.filter_by(is_active=True).all()

    return jsonify({
        'total': len(schedules),
        'schedules': [schedule.to_dict() for schedule in schedules]
    }), 200

@app.route('/schedules/<int:routeId>', methods=['GET'])
def get_route_schedules(routeId):
    """
    GET /schedules/{routeId}: Mendapatkan jadwal keberangkatan bus untuk rute tertentu.
    """
    # Ambil semua jadwal aktif untuk rute ini
    schedules = Schedule.query.filter_by(route_id=routeId, is_active=True).all()
    
    if not schedules:
        return jsonify({
            'routeId': routeId,
            'total': 0,
            'schedules': [],
            'message': 'Tidak ada jadwal untuk rute ini.'
        }), 200
    
    # Ambil info rute dari Route Service
    route_info = get_route_info(routeId)
    
    return jsonify({
        'routeId': routeId,
        'routeName': route_info.get('name') if route_info else schedules[0].route_name,
        'total': len(schedules),
        'schedules': [schedule.to_dict() for schedule in schedules]
    }), 200


@app.route('/schedule/<int:scheduleId>', methods=['GET'])
def get_schedule_by_id(scheduleId):
    """
    GET /schedule/{scheduleId}: Mengembalikan satu jadwal berdasarkan ID jadwal.
    """
    schedule = db.session.get(Schedule, scheduleId)
    if not schedule:
        return jsonify({'error': 'Jadwal tidak ditemukan.'}), 404

    return jsonify({'schedule': schedule.to_dict()}), 200


@app.route('/buses/<int:busId>/schedules', methods=['GET'])
def get_schedules_by_bus(busId):
    """
    GET /buses/{busId}/schedules: Mengembalikan daftar jadwal untuk bus tertentu.
    """
    # optional route filter to disambiguate schedules for same bus on multiple routes
    route_filter = request.args.get('routeId', type=int) or request.args.get('route_id', type=int) or request.args.get('routeid', type=int)

    if route_filter is not None:
        schedules: List[Any] = Schedule.query.filter_by(bus_id=busId, route_id=route_filter, is_active=True).all()
    else:
        schedules: List[Any] = Schedule.query.filter_by(bus_id=busId, is_active=True).all()
    if not schedules:
        return jsonify({'busId': busId, 'total': 0, 'schedules': [], 'message': 'Tidak ada jadwal untuk bus ini.'}), 200

    return jsonify({'busId': busId, 'total': len(schedules), 'schedules': [s.to_dict() for s in schedules]}), 200


@app.route('/eta', methods=['GET'])
def calculate_bus_eta():
    """
    GET /eta?busId=x&stopId=y: Memprediksi berapa menit lagi bus X akan tiba di Halte Y.
    Ini adalah fungsi kunci yang memanggil data lokasi real-time dari BusService.
    """
    bus_id = request.args.get('busId', type=int)
    stop_id = request.args.get('stopId', type=int)

    if bus_id is None or stop_id is None:
        return jsonify({'error': 'Parameter busId dan stopId harus diberikan dan berupa angka.'}), 400
    
    # Ambil lokasi bus real-time
    bus_data = get_bus_location(bus_id)
    if not bus_data:
        return jsonify({'error': 'Bus tidak ditemukan atau Bus Service tidak tersedia.'}), 404
    
    # Ambil lokasi halte
    stop_data = get_stop_location(stop_id)
    if not stop_data:
        return jsonify({'error': 'Halte tidak ditemukan atau Stop Service tidak tersedia.'}), 404
    
    # Ekstrak koordinat
    bus_lat = bus_data['lokasi_geografis']['latitude']
    bus_lon = bus_data['lokasi_geografis']['longitude']
    stop_lat = stop_data['coordinates']['latitude']
    stop_lon = stop_data['coordinates']['longitude']
    
    # Hitung jarak menggunakan Haversine
    distance = haversine_distance(bus_lat, bus_lon, stop_lat, stop_lon)
    
    # Ambil kecepatan rata-rata bus
    average_speed = bus_data.get('speed', {}).get('average', 40.0)
    
    # Hitung ETA
    eta = calculate_eta(distance, average_speed)
    
    # Simpan prediksi ke database (optional, untuk tracking)
    arrival = BusArrival(
        stop_id=stop_id,
        stop_name=stop_data['name'],
        bus_id=bus_id,
        bus_number=bus_data['nomor_polisi'],
        route_id=bus_data.get('route', {}).get('routeId', 0) if 'route' in bus_data else 0,
        route_name=bus_data.get('route', {}).get('routeName', 'Unknown') if 'route' in bus_data else 'Unknown',
        eta_minutes=eta,
        distance_km=distance,
        status='Approaching' if eta > 0 else 'Arrived'
    )
    
    db.session.add(arrival)
    db.session.commit()
    
    return jsonify({
        'busId': bus_id,
        'busNumber': bus_data['nomor_polisi'],
        'stopId': stop_id,
        'stopName': stop_data['name'],
        'distance': round(distance, 2),
        'distanceUnit': 'km',
        'eta': eta,
        'etaUnit': 'minutes',
        'averageSpeed': average_speed,
        'speedUnit': 'km/h',
        'busLocation': {
            'latitude': bus_lat,
            'longitude': bus_lon
        },
        'stopLocation': {
            'latitude': stop_lat,
            'longitude': stop_lon
        },
        'status': 'Approaching' if eta > 0 else 'Arrived'
    }), 200


@app.route('/stops/<int:stopId>/arrivals', methods=['GET'])
def get_stop_arrivals(stopId):
    """
    GET /stops/{stopId}/arrivals: Mendapatkan daftar bus dan waktu kedatangan terdekat di halte tertentu.
    """
    # Ambil info halte
    stop_data = get_stop_location(stopId)
    if not stop_data:
        return jsonify({'error': 'Halte tidak ditemukan.'}), 404
    
    stop_lat = stop_data['coordinates']['latitude']
    stop_lon = stop_data['coordinates']['longitude']
    
    # Ambil optional filter dari query params (routeId / busId)
    filter_route_id = request.args.get('routeId', type=int)
    filter_bus_id = request.args.get('busId', type=int)

    # Ambil semua bus yang sedang beroperasi
    try:
        buses_response = requests.get(f'{BUS_SERVICE_URL}/buses', timeout=REQUEST_TIMEOUT)
        if buses_response.status_code != 200:
            return jsonify({'error': 'Tidak dapat mengambil data bus.'}), 500
        
        buses_data = buses_response.json()
        buses = buses_data.get('buses', [])
        
    except requests.exceptions.RequestException:
        return jsonify({'error': 'Bus Service tidak tersedia.'}), 500
    
    # Hitung ETA untuk setiap bus yang sedang In Service
    arrivals = []
    
    for bus in buses:
        # Skip bus yang tidak sedang beroperasi
        if bus.get('operational_status') != 'In Service':
            continue
        
        # Skip bus yang tidak punya route
        if not bus.get('route'):
            continue

        # Jika filter routeId diberikan, skip bus yang tidak cocok
        if filter_route_id is not None:
            bus_route = bus.get('route', {})
            if bus_route.get('routeId') != filter_route_id:
                continue

        # Jika filter busId diberikan, skip bus yang tidak cocok
        if filter_bus_id is not None:
            if bus.get('busId') != filter_bus_id:
                continue
        
        bus_lat = bus['lokasi_geografis']['latitude']
        bus_lon = bus['lokasi_geografis']['longitude']
        
        # Skip bus yang masih di posisi default (0, 0)
        if bus_lat == 0.0 and bus_lon == 0.0:
            continue
        
        # Hitung jarak dan ETA
        distance = haversine_distance(bus_lat, bus_lon, stop_lat, stop_lon)
        average_speed = bus.get('speed', {}).get('average', 40.0)
        eta = calculate_eta(distance, average_speed)
        
        # Hanya tampilkan bus yang dalam radius maksimal
        if distance <= MAX_SEARCH_RADIUS_KM:
            arrivals.append({
                'busId': bus['busId'],
                'busNumber': bus['nomor_polisi'],
                'routeId': bus['route']['routeId'],
                'routeName': bus['route']['routeName'],
                'eta': eta,
                'etaUnit': 'minutes',
                'distance': round(distance, 2),
                'distanceUnit': 'km',
                'status': 'Approaching' if eta > 2 else 'Arriving Soon'
            })
    
    # Sort berdasarkan ETA (terdekat dulu)
    arrivals.sort(key=lambda x: x['eta'])
    
    return jsonify({
        'stopId': stopId,
        'stopName': stop_data['name'],
        'totalArrivals': len(arrivals),
        'arrivals': arrivals[:10]  # Batasi 10 bus terdekat
    }), 200


@app.route('/routes/<int:routeId>/next-departures', methods=['GET'])
def get_next_departures(routeId):
    """
    GET /routes/{routeId}/next-departures: Mendapatkan jadwal keberangkatan berikutnya untuk rute tertentu.
    """
    # Ambil waktu sekarang
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    
    # Ambil semua jadwal aktif untuk rute ini
    schedules = Schedule.query.filter_by(route_id=routeId, is_active=True).all()
    
    if not schedules:
        return jsonify({
            'routeId': routeId,
            'message': 'Tidak ada jadwal untuk rute ini.'
        }), 404
    
    # Filter jadwal yang belum lewat hari ini
    next_departures = []
    
    for schedule in schedules:
        departure_time = schedule.departure_time
        
        # Bandingkan waktu
        if departure_time >= current_time:
            next_departures.append(schedule.to_dict())
    
    # Sort berdasarkan waktu keberangkatan
    next_departures.sort(key=lambda x: x['departureTime'])
    
    return jsonify({
        'routeId': routeId,
        'currentTime': current_time,
        'totalDepartures': len(next_departures),
        'nextDepartures': next_departures[:5]  # Batasi 5 keberangkatan berikutnya
    }), 200


# ========================================
# ENDPOINTS UNTUK ADMIN (CRUD)
# ========================================

@app.route('/admin/schedules', methods=['GET'])
@admin_required
def admin_get_all_schedules():
    """
    GET /admin/schedules: Admin dapat melihat semua jadwal.
    """
    schedules = Schedule.query.all()
    
    return jsonify({
        'total': len(schedules),
        'schedules': [schedule.to_dict() for schedule in schedules]
    }), 200


@app.route('/admin/schedules/add', methods=['POST'])
@admin_required
def admin_add_schedule():
    """
    POST /admin/schedules/add: Menambahkan jadwal baru.
    Body JSON:
    {
        "route_id": 1,
        "route_name": "Rute A",
        "bus_id": 1,
        "bus_number": "B 1234 ABC",
        "departure_time": "06:00",
        "operating_days": "Daily",
        "frequency_minutes": 15
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body harus berupa JSON.'}), 400
    
    # Validasi field wajib
    required_fields = ['route_id', 'bus_id', 'departure_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Field {field} wajib diisi.'}), 400
    
    # Validasi format waktu (HH:MM)
    try:
        datetime.strptime(data['departure_time'], '%H:%M')
    except ValueError:
        return jsonify({'error': 'Format departure_time harus HH:MM (misal: 06:00)'}), 400
    # Validasi frequency_minutes jika diberikan
    freq_value = data.get('frequency_minutes')
    if freq_value is not None:
        try:
            freq_value = int(freq_value)
        except (TypeError, ValueError):
            return jsonify({'error': 'frequency_minutes harus berupa angka bulat.'}), 400

        if freq_value < 0:
            return jsonify({'error': 'frequency_minutes tidak boleh negatif.'}), 400

    # Buat jadwal baru
    new_schedule = Schedule(
        route_id=data['route_id'],
        route_name=data.get('route_name', f'Route {data["route_id"]}'),
        bus_id=data['bus_id'],
        bus_number=data.get('bus_number', f'Bus {data["bus_id"]}'),
        departure_time=data['departure_time'],
        operating_days=data.get('operating_days', 'Daily'),
        frequency_minutes=freq_value,
        is_active=data.get('is_active', True)
    )
    
    db.session.add(new_schedule)
    db.session.commit()
    
    return jsonify({
        'message': 'Jadwal berhasil ditambahkan.',
        'schedule': new_schedule.to_dict()
    }), 201


@app.route('/admin/schedules/<int:scheduleId>', methods=['PUT'])
@admin_required
def admin_update_schedule(scheduleId):
    """
    PUT /admin/schedules/{scheduleId}: Mengupdate jadwal.
    """
    schedule = db.session.get(Schedule, scheduleId)
    if not schedule:
        return jsonify({'error': 'Jadwal tidak ditemukan.'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body harus berupa JSON.'}), 400
    
    # Update field yang diberikan
    if 'departure_time' in data:
        try:
            datetime.strptime(data['departure_time'], '%H:%M')
            schedule.departure_time = data['departure_time']
        except ValueError:
            return jsonify({'error': 'Format departure_time harus HH:MM'}), 400
    
    if 'operating_days' in data:
        schedule.operating_days = data['operating_days']
    
    if 'frequency_minutes' in data:
        # Validate frequency_minutes is integer >= 0
        try:
            freq = int(data['frequency_minutes'])
        except (TypeError, ValueError):
            return jsonify({'error': 'frequency_minutes harus berupa angka bulat.'}), 400

        if freq < 0:
            return jsonify({'error': 'frequency_minutes tidak boleh negatif.'}), 400

        schedule.frequency_minutes = freq
    
    if 'is_active' in data:
        schedule.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Jadwal berhasil diupdate.',
        'schedule': schedule.to_dict()
    }), 200


@app.route('/admin/schedules/<int:scheduleId>', methods=['DELETE'])
@admin_required
def admin_delete_schedule(scheduleId):
    """
    DELETE /admin/schedules/{scheduleId}: Menghapus jadwal.
    """
    schedule = db.session.get(Schedule, scheduleId)
    if not schedule:
        return jsonify({'error': 'Jadwal tidak ditemukan.'}), 404
    
    db.session.delete(schedule)
    db.session.commit()
    
    return jsonify({
        'message': f'Jadwal untuk {schedule.route_name} berhasil dihapus.'
    }), 200


# --- CLI Commands ---

@app.cli.command('init-db')
def init_db_command():
    """Perintah untuk menginisialisasi database."""
    with app.app_context():
        db.create_all()
        print('Database Schedule telah diinisialisasi.')


@app.cli.command('seed-schedules')
def seed_schedules_command():
    """Menambahkan data jadwal sample."""
    with app.app_context():
        # Hapus data lama
        BusArrival.query.delete()
        Schedule.query.delete()
        
        # Data jadwal sample
        schedules_data = [
            # Rute A - Bus 1
            {'route_id': 1, 'route_name': 'Rute A', 'bus_id': 1, 'bus_number': 'B 1234 ABC', 'departure_time': '06:00', 'frequency_minutes': 15},
            {'route_id': 1, 'route_name': 'Rute A', 'bus_id': 2, 'bus_number': 'B 5678 DEF', 'departure_time': '06:15', 'frequency_minutes': 15},
            
            # Rute B - Bus 3
            {'route_id': 2, 'route_name': 'Rute B', 'bus_id': 3, 'bus_number': 'B 9012 GHI', 'departure_time': '06:30', 'frequency_minutes': 20},
            
            # Koridor 1 - Bus 4
            {'route_id': 3, 'route_name': 'Koridor 1', 'bus_id': 4, 'bus_number': 'B 3456 JKL', 'departure_time': '07:00', 'frequency_minutes': 30},
        ]
        
        for schedule_data in schedules_data:
            schedule = Schedule(
                route_id=schedule_data['route_id'],
                route_name=schedule_data['route_name'],
                bus_id=schedule_data['bus_id'],
                bus_number=schedule_data['bus_number'],
                departure_time=schedule_data['departure_time'],
                operating_days='Daily',
                frequency_minutes=schedule_data['frequency_minutes'],
                is_active=True
            )
            db.session.add(schedule)
        
        db.session.commit()
        print(f'{len(schedules_data)} Jadwal berhasil ditambahkan.')


# Health check
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'schedule-service',
        'database': 'connected'
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Port 5005 untuk schedule service
    app.run(debug=True, host='0.0.0.0', port=5005)
