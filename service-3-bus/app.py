import os
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import requests
from functools import wraps

# Import models
from models import db, Bus

# Muat variabel lingkungan dari file .env
load_dotenv()

# Inisialisasi Aplikasi Flask
app = Flask(__name__, instance_relative_config=True)

# Memastikan folder instance ada (untuk SQLite)
os.makedirs(app.instance_path, exist_ok=True)

# Konfigurasi Database
db_path = os.path.join(app.instance_path, 'bus.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# URL Route Service (untuk integrasi)
ROUTE_SERVICE_URL = os.environ.get('ROUTE_SERVICE_URL', 'http://localhost:5002')

# Inisialisasi Database
db.init_app(app)

# --- Middleware untuk Verifikasi Token JWT ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Dapatkan token dari header
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token tidak ditemukan'}), 401

        try:
            # Verifikasi token admin ke service-user
            response = requests.get(
                'http://service-user:5001/verify-admin',
                headers={'Authorization': token}  # Kirim token yang sama
            )
            
            if response.status_code != 200:
                return jsonify({'error': 'Unauthorized - Admin role required'}), 403
                
        except requests.exceptions.RequestException:
            return jsonify({'error': 'Gagal terhubung ke service autentikasi'}), 500
            
        return f(*args, **kwargs)
    return decorated_function

# ========================================
# WEB UI ENDPOINT
# ========================================

@app.route('/')
def index():
    """Serve the web UI"""
    return render_template('index.html')


# ========================================
# ENDPOINTS UNTUK PUBLIC
# ========================================

@app.route('/buses', methods=['GET'])
def get_all_buses():
    """
    GET /buses: Mendapatkan daftar semua bus.
    Query params: route_id (optional) untuk filter bus berdasarkan rute
    """
    route_id = request.args.get('route_id', type=int)
    
    if route_id:
        buses = Bus.query.filter_by(route_id=route_id).all()
    else:
        buses = Bus.query.all()
    
    return jsonify({
        'total': len(buses),
        'buses': [bus.to_dict(include_route=True) for bus in buses]
    }), 200


@app.route('/admin/buses/add', methods=['POST'])
@admin_required
def register_bus():
    """
    POST /admin/buses/add: Mendaftarkan bus baru ke dalam sistem.
    """
    data = request.json
    
    # Validasi input
    if not data or 'nomor_polisi' not in data or 'kapasitas_penumpang' not in data:
        return jsonify({'error': 'Data tidak lengkap. Butuh nomor_polisi dan kapasitas_penumpang.'}), 400

    # Cek jika nomor polisi sudah ada
    if Bus.query.filter_by(nomor_polisi=data['nomor_polisi']).first():
         return jsonify({'error': 'Nomor polisi sudah terdaftar.'}), 409 # 409 Conflict

    new_bus = Bus(
        nomor_polisi=data['nomor_polisi'],
        kapasitas_penumpang=data['kapasitas_penumpang'],
        model_kendaraan=data.get('model_kendaraan'),
        average_speed=data.get('average_speed', 40.0),  # Default 40 km/jam
        operational_status='Available',
        status_gps='Offline'
    )
    
    db.session.add(new_bus)
    db.session.commit()
    
    return jsonify(new_bus.to_dict()), 201 # 201 Created

@app.route('/buses/<int:busId>', methods=['GET'])
def get_bus_detail(busId):
    """
    GET /buses/{busId}: Mendapatkan detail dan lokasi bus tertentu.
    """
    bus = db.session.get(Bus, busId)
    if not bus:
        return jsonify({'error': 'Bus tidak ditemukan.'}), 404
        
    return jsonify(bus.to_dict()), 200

@app.route('/buses/<int:busId>/location', methods=['PUT'])
def update_bus_location(busId):
    """
    PUT /buses/{busId}/location: Memperbarui posisi dan kecepatan bus secara real-time.
    """
    bus = db.session.get(Bus, busId)
    if not bus:
        return jsonify({'error': 'Bus tidak ditemukan.'}), 404
        
    data = request.json
    
    # Validasi input lokasi
    if not data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Data lokasi tidak lengkap. Butuh latitude dan longitude.'}), 400

    # Update lokasi
    bus.latitude = data['latitude']
    bus.longitude = data['longitude']
    
    # Update kecepatan saat ini (dari GPS)
    if 'current_speed' in data:
        bus.current_speed = data['current_speed']
    
    # Update status GPS jika ada di data, jika tidak, set ke 'Online'
    bus.status_gps = data.get('status_gps', 'Online') 
    
    db.session.commit()
    
    return jsonify(bus.to_dict(include_route=True)), 200


@app.route('/admin/buses/<int:busId>/route/assign', methods=['PUT'])
@admin_required
def assign_bus_to_route(busId):
    """
    PUT /buses/{busId}/route: Assign bus ke rute tertentu.
    Body: {"route_id": 1, "route_name": "Rute A"}
    """
    bus = db.session.get(Bus, busId)
    if not bus:
        return jsonify({'error': 'Bus tidak ditemukan.'}), 404
    
    data = request.json
    if not data or 'route_id' not in data:
        return jsonify({'error': 'route_id wajib diisi.'}), 400
    
    # Validasi route_id dengan Route Service
    try:
        route_response = requests.get(f'{ROUTE_SERVICE_URL}/routes/{data["route_id"]}')
        if route_response.status_code != 200:
            return jsonify({'error': 'Route tidak ditemukan di Route Service.'}), 404
        
        route_data = route_response.json()
        
        # Assign bus ke route
        bus.route_id = data['route_id']
        bus.route_name = route_data.get('name', data.get('route_name', ''))
        bus.operational_status = 'In Service'
        
        db.session.commit()
        
        return jsonify({
            'message': f'Bus {bus.nomor_polisi} berhasil di-assign ke {bus.route_name}',
            'bus': bus.to_dict(include_route=True)
        }), 200
        
    except requests.exceptions.RequestException:
        # Jika Route Service tidak tersedia, tetap assign tapi dengan warning
        bus.route_id = data['route_id']
        bus.route_name = data.get('route_name', f'Route {data["route_id"]}')
        bus.operational_status = 'In Service'
        
        db.session.commit()
        
        return jsonify({
            'message': f'Bus {bus.nomor_polisi} di-assign ke route (Route Service unavailable)',
            'warning': 'Tidak dapat memvalidasi route_id',
            'bus': bus.to_dict(include_route=True)
        }), 200


@app.route('/admin/buses/<int:busId>/route/unassign', methods=['DELETE'])
@admin_required
def unassign_bus_from_route(busId):
    """
    DELETE /buses/{busId}/route: Unassign bus dari rute.
    """
    bus = db.session.get(Bus, busId)
    if not bus:
        return jsonify({'error': 'Bus tidak ditemukan.'}), 404
    
    if not bus.route_id:
        return jsonify({'error': 'Bus tidak sedang di-assign ke rute manapun.'}), 400
    
    old_route = bus.route_name
    bus.route_id = None
    bus.route_name = None
    bus.operational_status = 'Available'
    
    db.session.commit()
    
    return jsonify({
        'message': f'Bus {bus.nomor_polisi} berhasil di-unassign dari {old_route}',
        'bus': bus.to_dict()
    }), 200


@app.route('/admin/buses/<int:busId>/speed', methods=['PUT'])
@admin_required
def update_bus_speed(busId):
    """
    PUT /admin/buses/{busId}/speed: Update kecepatan rata-rata bus.
    Body: {"average_speed": 45.0}
    """
    bus = db.session.get(Bus, busId)
    if not bus:
        return jsonify({'error': 'Bus tidak ditemukan.'}), 404
    
    data = request.json
    if not data or 'average_speed' not in data:
        return jsonify({'error': 'average_speed wajib diisi.'}), 400
    
    bus.average_speed = data['average_speed']
    db.session.commit()
    
    return jsonify({
        'message': f'Kecepatan rata-rata bus {bus.nomor_polisi} berhasil diupdate',
        'bus': bus.to_dict(include_route=True)
    }), 200


@app.route('/admin/buses/<int:busId>/status', methods=['PUT'])
@admin_required
def update_bus_status(busId):
    """
    PUT /admin/buses/{busId}/status: Update status operasional bus.
    Body: {"operational_status": "Maintenance"}
    Status: Available, In Service, Maintenance, Out of Service
    """
    bus = db.session.get(Bus, busId)
    if not bus:
        return jsonify({'error': 'Bus tidak ditemukan.'}), 404
    
    data = request.json
    if not data or 'operational_status' not in data:
        return jsonify({'error': 'operational_status wajib diisi.'}), 400
    
    valid_statuses = ['Available', 'In Service', 'Maintenance', 'Out of Service']
    if data['operational_status'] not in valid_statuses:
        return jsonify({'error': f'Status harus salah satu dari: {valid_statuses}'}), 400
    
    bus.operational_status = data['operational_status']
    db.session.commit()
    
    return jsonify({
        'message': f'Status bus {bus.nomor_polisi} berhasil diupdate',
        'bus': bus.to_dict(include_route=True)
    }), 200


@app.route('/routes/<int:routeId>/buses', methods=['GET'])
def get_buses_by_route(routeId):
    """
    GET /routes/{routeId}/buses: Mendapatkan semua bus yang melayani rute tertentu.
    """
    buses = Bus.query.filter_by(route_id=routeId).all()
    
    return jsonify({
        'routeId': routeId,
        'total': len(buses),
        'buses': [bus.to_dict(include_route=True) for bus in buses]
    }), 200

# --- Perintah CLI untuk setup database ---
@app.cli.command('init-db')
def init_db_command():
    """
    Perintah untuk menginisialisasi database.
    """
    with app.app_context():
        db.create_all()
        print('Database Bus telah diinisialisasi.')


@app.cli.command('seed-buses')
def seed_buses_command():
    """
    Menambahkan data bus sample untuk testing.
    """
    with app.app_context():
        # Hapus data lama
        Bus.query.delete()
        
        # Data bus sample
        buses_data = [
            {
                'nomor_polisi': 'B 1234 ABC',
                'kapasitas_penumpang': 50,
                'model_kendaraan': 'Mercedes-Benz OH 1526',
                'average_speed': 45.0,
                'route_id': 1,
                'route_name': 'Rute A',
                'operational_status': 'In Service'
            },
            {
                'nomor_polisi': 'B 5678 DEF',
                'kapasitas_penumpang': 45,
                'model_kendaraan': 'Hino RK8',
                'average_speed': 42.0,
                'route_id': 1,
                'route_name': 'Rute A',
                'operational_status': 'In Service'
            },
            {
                'nomor_polisi': 'B 9012 GHI',
                'kapasitas_penumpang': 50,
                'model_kendaraan': 'Scania K310',
                'average_speed': 48.0,
                'route_id': 2,
                'route_name': 'Rute B',
                'operational_status': 'In Service'
            },
            {
                'nomor_polisi': 'B 3456 JKL',
                'kapasitas_penumpang': 40,
                'model_kendaraan': 'Isuzu NQR',
                'average_speed': 40.0,
                'route_id': 3,
                'route_name': 'Koridor 1',
                'operational_status': 'In Service'
            },
            {
                'nomor_polisi': 'B 7890 MNO',
                'kapasitas_penumpang': 50,
                'model_kendaraan': 'Mercedes-Benz OH 1526',
                'average_speed': 44.0,
                'operational_status': 'Available'
            },
            {
                'nomor_polisi': 'B 1122 PQR',
                'kapasitas_penumpang': 45,
                'model_kendaraan': 'Hino RK8',
                'average_speed': 43.0,
                'operational_status': 'Maintenance'
            }
        ]
        
        for bus_data in buses_data:
            bus = Bus(
                nomor_polisi=bus_data['nomor_polisi'],
                kapasitas_penumpang=bus_data['kapasitas_penumpang'],
                model_kendaraan=bus_data['model_kendaraan'],
                average_speed=bus_data['average_speed'],
                route_id=bus_data.get('route_id'),
                route_name=bus_data.get('route_name'),
                operational_status=bus_data['operational_status'],
                status_gps='Offline',
                current_speed=0.0
            )
            db.session.add(bus)
        
        db.session.commit()
        print(f'{len(buses_data)} Bus berhasil ditambahkan.')


# Health check
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'bus-service',
        'database': 'connected'
    })

# Menjalankan server (sesuai port di docker-compose)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Port 5004 agar sesuai dengan docker-compose
    app.run(debug=True, host='0.0.0.0', port=5004)