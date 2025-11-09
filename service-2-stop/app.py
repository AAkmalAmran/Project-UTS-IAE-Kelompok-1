import os
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import or_
from functools import wraps
import requests

# Menggunakan relative import untuk models (memastikan models.py ada di folder yang sama)
from models import db, Stop 

# Muat variabel lingkungan
load_dotenv()

app = Flask(__name__, instance_relative_config=True)

# Memastikan folder instance ada (untuk SQLite)
os.makedirs(app.instance_path, exist_ok=True)

# Konfigurasi Database
db_path = os.path.join(app.instance_path, 'stop.db')
# Mengambil DATABASE_URL dari .env, fallback ke SQLite di instance path
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inisialisasi Database
db.init_app(app)

# --- Middleware untuk Autentikasi Admin ---
def admin_required(f):
    """Decorator untuk memvalidasi admin credentials."""
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
                headers={'Authorization': token}
            )
            
            if response.status_code != 200:
                return jsonify({'error': 'Unauthorized - Admin role required'}), 403
                
        except requests.exceptions.RequestException:
            return jsonify({'error': 'Gagal terhubung ke service autentikasi'}), 500
            
        return f(*args, **kwargs)
    return decorated_function

# --- Definisi Data Seeding Dua Arah (Total 20 Halte) ---

# === Arah Baleendah → BEC (10 Halte) ===
RUTE_BALEENDAH_TO_BEC = [
    # Halte 1
    {'name': 'Baleendah', 'latitude': -7.0305, 'longitude': 107.6327, 'shelter': True, 'lighting': True, 'digital_eta_display': True, 'address': 'Halte Awal Arah Pergi'},
    # Halte 2
    {'name': 'Masjid Jami Baitul Huda Baleendah', 'latitude': -7.0310, 'longitude': 107.6330, 'shelter': False, 'address': 'Halte 2'},
    # Halte 3
    {'name': 'Griya Bandung Asri (GBA)', 'latitude': -7.0000, 'longitude': 107.6500, 'shelter': True, 'address': 'Halte 3'},
    # Halte 4
    {'name': 'Sekolah Moh Toha', 'latitude': -6.9500, 'longitude': 107.6200, 'shelter': True, 'address': 'Halte 4'},
    # Halte 5
    {'name': 'Museum Kota Bandung', 'latitude': -6.9200, 'longitude': 107.6100, 'shelter': True, 'address': 'Halte 5'},
    # Halte 6
    {'name': 'Merdeka', 'latitude': -6.9195, 'longitude': 107.6105, 'shelter': False, 'address': 'Halte 6'},
    # Halte 7
    {'name': 'Alun-alun Bandung', 'latitude': -6.9217, 'longitude': 107.6074, 'shelter': True, 'wheelchair_access': True, 'address': 'Halte 7'},
    # Halte 8
    {'name': 'Simpang Ijan', 'latitude': -6.9185, 'longitude': 107.6050, 'shelter': True, 'address': 'Halte 8'},
    # Halte 9
    {'name': 'Stasiun Bandung', 'latitude': -6.9147, 'longitude': 107.6015, 'shelter': True, 'digital_eta_display': True, 'address': 'Halte 9'},
    # Halte 10
    {'name': 'Bandung Electronic Centre (BEC)', 'latitude': -6.9130, 'longitude': 107.6067, 'shelter': True, 'digital_eta_display': True, 'charging_port': True, 'address': 'Halte Akhir Arah Pergi'}
]

# === Arah BEC → Baleendah (10 Halte) ===
RUTE_BEC_TO_BALEENDAH = [
    # Halte 11 (Awal Arah Balik)
    {'name': 'Bandung Electronic Centre (BEC) B', 'latitude': -6.9135, 'longitude': 107.6070, 'shelter': True, 'digital_eta_display': True, 'address': 'Halte Awal Arah Balik'},
    # Halte 12
    {'name': 'Stasiun Bandung B', 'latitude': -6.9150, 'longitude': 107.6020, 'shelter': True, 'address': 'Halte 12'},
    # Halte 13
    {'name': 'SMAN 6 Bandung', 'latitude': -6.9190, 'longitude': 107.6045, 'shelter': True, 'address': 'Halte 13'},
    # Halte 14
    {'name': 'Simpang Ijan B', 'latitude': -6.9180, 'longitude': 107.6055, 'shelter': True, 'address': 'Halte 14'},
    # Halte 15
    {'name': 'Alun-alun Bandung B', 'latitude': -6.9220, 'longitude': 107.6078, 'shelter': True, 'wheelchair_access': True, 'address': 'Halte 15'},
    # Halte 16
    {'name': 'Kepatihan B', 'latitude': -6.9205, 'longitude': 107.6090, 'shelter': False, 'address': 'Halte 16'},
    # Halte 17
    {'name': 'RS Bersalin B', 'latitude': -6.9550, 'longitude': 107.6250, 'shelter': True, 'address': 'Halte 17'},
    # Halte 18
    {'name': 'Podomoro B', 'latitude': -7.0050, 'longitude': 107.6450, 'shelter': True, 'address': 'Halte 18'},
    # Halte 19
    {'name': 'Transmart Buah Batu B', 'latitude': -7.0200, 'longitude': 107.6350, 'shelter': True, 'address': 'Halte 19'},
    # Halte 20 (Akhir Arah Balik)
    {'name': 'Baleendah B', 'latitude': -7.0300, 'longitude': 107.6320, 'shelter': True, 'digital_eta_display': True, 'address': 'Halte Akhir Arah Balik'}
]

# Gabungkan kedua arah menjadi satu daftar untuk seeding
ALL_STOPS_DATA = RUTE_BALEENDAH_TO_BEC + RUTE_BEC_TO_BALEENDAH


# ========================================
# WEB UI ENDPOINT
# ========================================

@app.route('/')
def index():
    """Serve the web UI"""
    return render_template('index.html')


# ========================================
# ENDPOINTS UNTUK USER (PUBLIC - GET ONLY)
# ========================================

@app.route('/stops', methods=['GET'])
def get_all_stops():
    """
    GET /stops: Mendapatkan daftar semua halte.
    """
    stops = Stop.query.all()
    
    return jsonify({
        'total': len(stops),
        'stops': [stop.to_dict() for stop in stops]
    }), 200


@app.route('/stops/<int:stopId>', methods=['GET'])
def get_stop_detail(stopId):
    """
    GET /stops/{stopId}: Mendapatkan detail informasi suatu halte.
    """
    stop = db.session.get(Stop, stopId)
    if not stop:
        return jsonify({'error': 'Halte tidak ditemukan.'}), 404
        
    return jsonify(stop.to_dict()), 200

@app.route('/stops/search', methods=['GET'])
def search_stops():
    """
    GET /stops/search?query=nama: Mencari halte berdasarkan nama.
    """
    query_name = request.args.get('query')
    if not query_name:
        return jsonify({'error': 'Parameter query wajib diisi.'}), 400
        
    # Mencari halte yang namanya mengandung query_name (case-insensitive)
    stops = Stop.query.filter(
        Stop.name.ilike(f'%{query_name}%')
    ).all()
    
    return jsonify([stop.to_dict() for stop in stops]), 200

@app.route('/stops/nearby', methods=['GET'])
def nearby_stops():
    """
    GET /stops/nearby?lat=x&lon=y: Mencari halte-halte terdekat dari lokasi pengguna.
    (Placeholder untuk implementasi perhitungan Haversine)
    """
    try:
        # Panggil parameter lat dan lon, konversi ke float
        user_lat = float(request.args.get('lat'))
        user_lon = float(request.args.get('lon'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Parameter lat dan lon harus berupa angka.'}), 400

    # Untuk demo, kita ambil semua halte yang ada di database
    all_stops = Stop.query.all()
    
    # Catatan: Di sini, Anda akan melakukan filter dan sorting menggunakan rumus Haversine 
    # atau ekstensi database seperti PostGIS. Untuk saat ini, kita kembalikan semua data.
    return jsonify([stop.to_dict() for stop in all_stops]), 200

# ========================================
# ENDPOINTS UNTUK ADMIN (CRUD)
# ========================================

@app.route('/admin/stops', methods=['GET'])
@admin_required
def admin_get_all_stops():
    """
    GET /admin/stops: Admin dapat melihat semua halte.
    """
    stops = Stop.query.all()
    
    return jsonify({
        'total': len(stops),
        'stops': [stop.to_dict() for stop in stops]
    }), 200


@app.route('/admin/stops/add', methods=['POST'])
@admin_required
def admin_add_stop():
    """
    POST /admin/stops/add: Menambahkan halte baru.
    Body JSON:
    {
        "name": "Halte Baru",
        "latitude": -6.9195,
        "longitude": 107.6105,
        "address": "Jl. Contoh No. 123",
        "shelter": true,
        "seating": true,
        "lighting": true,
        "wheelchair_access": true,
        "guiding_block": false,
        "digital_eta_display": true,
        "charging_port": false
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body harus berupa JSON.'}), 400
    
    # Validasi field wajib
    required_fields = ['name', 'latitude', 'longitude']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Field {field} wajib diisi.'}), 400
    
    # Buat halte baru
    new_stop = Stop(
        name=data['name'],
        latitude=data['latitude'],
        longitude=data['longitude'],
        address=data.get('address'),
        shelter=data.get('shelter', False),
        seating=data.get('seating', False),
        lighting=data.get('lighting', False),
        wheelchair_access=data.get('wheelchair_access', False),
        guiding_block=data.get('guiding_block', False),
        digital_eta_display=data.get('digital_eta_display', False),
        charging_port=data.get('charging_port', False)
    )
    
    db.session.add(new_stop)
    db.session.commit()
    
    return jsonify({
        'message': 'Halte berhasil ditambahkan.',
        'stop': new_stop.to_dict()
    }), 201


@app.route('/admin/stops/<int:stopId>', methods=['PUT'])
@admin_required
def admin_update_stop(stopId):
    """
    PUT /admin/stops/{stopId}: Mengupdate informasi halte.
    """
    stop = db.session.get(Stop, stopId)
    if not stop:
        return jsonify({'error': 'Halte tidak ditemukan.'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body harus berupa JSON.'}), 400
    
    # Update field yang diberikan
    if 'name' in data:
        stop.name = data['name']
    if 'latitude' in data:
        stop.latitude = data['latitude']
    if 'longitude' in data:
        stop.longitude = data['longitude']
    if 'address' in data:
        stop.address = data['address']
    if 'shelter' in data:
        stop.shelter = data['shelter']
    if 'seating' in data:
        stop.seating = data['seating']
    if 'lighting' in data:
        stop.lighting = data['lighting']
    if 'wheelchair_access' in data:
        stop.wheelchair_access = data['wheelchair_access']
    if 'guiding_block' in data:
        stop.guiding_block = data['guiding_block']
    if 'digital_eta_display' in data:
        stop.digital_eta_display = data['digital_eta_display']
    if 'charging_port' in data:
        stop.charging_port = data['charging_port']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Halte berhasil diupdate.',
        'stop': stop.to_dict()
    }), 200


@app.route('/admin/stops/<int:stopId>', methods=['DELETE'])
@admin_required
def admin_delete_stop(stopId):
    """
    DELETE /admin/stops/{stopId}: Menghapus halte.
    """
    stop = db.session.get(Stop, stopId)
    if not stop:
        return jsonify({'error': 'Halte tidak ditemukan.'}), 404
    
    stop_name = stop.name
    db.session.delete(stop)
    db.session.commit()
    
    return jsonify({
        'message': f'Halte {stop_name} berhasil dihapus.'
    }), 200


# --- Perintah CLI untuk setup database & Seeding ---

@app.cli.command('init-db')
def init_db_command():
    """Perintah untuk menginisialisasi database."""
    with app.app_context():
        # Membuat semua tabel berdasarkan models.py
        db.create_all()
        print('Database Halte telah diinisialisasi.')

@app.cli.command('seed-stops')
def seed_stops_command():
    """Menambahkan data halte (stops) awal untuk Rute 3 (20 Halte Dua Arah)."""
    with app.app_context():
        # Perintah penting: Hapus SEMUA data lama sebelum memasukkan yang baru (Reset)
        Stop.query.delete() 
        
        # Tambahkan data baru (20 Halte)
        for data in ALL_STOPS_DATA:
            new_stop = Stop(
                name=data['name'],
                latitude=data['latitude'],
                longitude=data['longitude'],
                address=data.get('address'),
                shelter=data.get('shelter', False),
                seating=data.get('seating', False),
                lighting=data.get('lighting', False),
                wheelchair_access=data.get('wheelchair_access', False),
                guiding_block=data.get('guiding_block', False),
                digital_eta_display=data.get('digital_eta_display', False),
                charging_port=data.get('charging_port', False),
            )
            db.session.add(new_stop)
        
        db.session.commit()
        print(f'{len(ALL_STOPS_DATA)} Halte (Dua Arah) untuk Rute 3 berhasil ditambahkan.')
        
# Health check
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'stop-service',
        'database': 'connected' 
    })


if __name__ == '__main__':
    # Pastikan app_context digunakan saat run lokal untuk membuat DB
    with app.app_context():
        db.create_all() 
    # Port 5003 agar sesuai dengan docker-compose
    app.run(debug=True, host='0.0.0.0', port=5003)