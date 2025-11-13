import os
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from functools import wraps
from math import radians, cos, sin, asin, sqrt
import requests

# Import models
from models import db, Route, RouteStop

# Muat variabel lingkungan
load_dotenv()

app = Flask(__name__, instance_relative_config=True)

# Memastikan folder instance ada (untuk SQLite)
os.makedirs(app.instance_path, exist_ok=True)

# Konfigurasi Database
db_path = os.path.join(app.instance_path, 'route.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Admin credentials (dalam production, gunakan JWT atau OAuth)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# URL Bus Service (untuk integrasi)
BUS_SERVICE_URL = os.environ.get('BUS_SERVICE_URL', 'http://localhost:5004')

# Inisialisasi Database
db.init_app(app)


# --- Middleware untuk Autentikasi Admin ---
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


# --- Helper Function: Haversine Distance ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Menghitung jarak antara dua koordinat geografis menggunakan formula Haversine.
    Return: jarak dalam kilometer
    """
    # Konversi derajat ke radian
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Formula Haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius bumi dalam kilometer
    r = 6371
    
    return c * r


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

@app.route('/routes', methods=['GET'])
def get_all_routes():
    """
    GET /routes: Mendapatkan daftar semua rute yang tersedia.
    User biasa hanya bisa melihat rute yang aktif.
    """
    # Filter hanya rute yang aktif
    routes = Route.query.filter_by(is_active=True).all()
    
    return jsonify({
        'total': len(routes),
        'routes': [route.to_dict() for route in routes]
    }), 200


@app.route('/routes/<int:routeId>', methods=['GET'])
def get_route_detail(routeId):
    """
    GET /routes/{routeId}: Mendapatkan detail rute termasuk daftar halte.
    """
    route = db.session.get(Route, routeId)
    if not route:
        return jsonify({'error': 'Rute tidak ditemukan.'}), 404
    
    return jsonify(route.to_dict(include_stops=True)), 200


@app.route('/routes/<int:routeId>/stops', methods=['GET'])
def get_route_stops(routeId):
    """
    GET /routes/{routeId}/stops: Mendapatkan urutan halte pada rute tertentu.
    """
    route = db.session.get(Route, routeId)
    if not route:
        return jsonify({'error': 'Rute tidak ditemukan.'}), 404
    
    # Ambil semua route_stops yang sudah terurut
    stops = route.route_stops
    
    return jsonify({
        'routeId': route.id,
        'routeName': route.name,
        'origin': route.origin,
        'destination': route.destination,
        'totalStops': len(stops),
        'totalDistance': sum(rs.distance_to_next for rs in stops if rs.distance_to_next),
        'stops': [stop.to_dict() for stop in stops]
    }), 200

@app.route('/routes/search', methods=['GET'])
def search_routes():
    """
    GET /routes/search?query=nama: Mencari rute berdasarkan nama atau deskripsi.
    """
    query_text = request.args.get('query')
    if not query_text:
        return jsonify({'error': 'Parameter query wajib diisi.'}), 400
    
    # Mencari rute yang namanya atau deskripsinya mengandung query_text
    routes = Route.query.filter(
        db.or_(
            Route.name.ilike(f'%{query_text}%'),
            Route.description.ilike(f'%{query_text}%')
        ),
        Route.is_active == True
    ).all()
    
    return jsonify({
        'query': query_text,
        'total': len(routes),
        'routes': [route.to_dict() for route in routes]
    }), 200

# ========================================
# ENDPOINTS UNTUK ADMIN (CRUD)
# ========================================

@app.route('/admin/routes', methods=['GET'])
@admin_required
def admin_get_all_routes():
    """
    GET /admin/routes: Admin dapat melihat semua rute (termasuk yang tidak aktif).
    """
    routes = Route.query.all()
    
    return jsonify({
        'total': len(routes),
        'routes': [route.to_dict(include_stops=True) for route in routes]
    }), 200


@app.route('/admin/routes/add', methods=['POST'])
@admin_required
def admin_add_route():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body harus berupa JSON.'}), 400
    
    # Validasi field wajib
    required_fields = ['name', 'origin', 'destination']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Field {field} wajib diisi.'}), 400
    
    # Cek apakah nama rute sudah ada
    existing_route = Route.query.filter_by(name=data['name']).first()
    if existing_route:
        return jsonify({'error': f'Rute dengan nama {data["name"]} sudah ada.'}), 400
    
    # Buat rute baru
    new_route = Route(
        name=data['name'],
        description=data.get('description'),
        origin=data['origin'],
        destination=data['destination'],
        is_active=data.get('isActive', True)
    )
    
    db.session.add(new_route)
    db.session.flush()  # Untuk mendapatkan route.id
    
    # Tambahkan stops jika ada
    if 'stops' in data and isinstance(data['stops'], list):
        for idx, stop_data in enumerate(data['stops'], start=1):
            route_stop = RouteStop(
                route_id=new_route.id,
                stop_id=stop_data['stopId'],
                stop_name=stop_data['stopName'],
                sequence_order=idx,
                distance_to_next=stop_data.get('distanceToNext'),
                time_to_next=stop_data.get('timeToNext')
            )
            db.session.add(route_stop)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Rute berhasil ditambahkan.',
        'route': new_route.to_dict(include_stops=True)
    }), 201


@app.route('/admin/routes/<int:routeId>', methods=['PUT'])
@admin_required
def admin_update_route(routeId):
    """
    PUT /admin/routes/{routeId}: Mengupdate informasi rute.
    Body JSON dapat berisi: name, description, origin, destination, isActive
    """
    route = db.session.get(Route, routeId)
    if not route:
        return jsonify({'error': 'Rute tidak ditemukan.'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body harus berupa JSON.'}), 400
    
    # Update field yang diberikan
    if 'name' in data:
        # Cek duplikasi nama
        existing = Route.query.filter(Route.name == data['name'], Route.id != routeId).first()
        if existing:
            return jsonify({'error': f'Rute dengan nama {data["name"]} sudah ada.'}), 400
        route.name = data['name']
    
    if 'description' in data:
        route.description = data['description']
    
    if 'origin' in data:
        route.origin = data['origin']
    
    if 'destination' in data:
        route.destination = data['destination']
    
    if 'isActive' in data:
        route.is_active = data['isActive']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Rute berhasil diupdate.',
        'route': route.to_dict(include_stops=True)
    }), 200


@app.route('/admin/routes/<int:routeId>', methods=['DELETE'])
@admin_required
def admin_delete_route(routeId):
    """
    DELETE /admin/routes/{routeId}: Menghapus rute.
    """
    route = db.session.get(Route, routeId)
    if not route:
        return jsonify({'error': 'Rute tidak ditemukan.'}), 404
    
    route_name = route.name
    db.session.delete(route)
    db.session.commit()
    
    return jsonify({
        'message': f'Rute {route_name} berhasil dihapus.'
    }), 200


@app.route('/admin/routes/<int:routeId>/stops/add', methods=['POST'])
@admin_required
def admin_add_stop_to_route(routeId):
    """
    POST /admin/routes/{routeId}/stops/add: Menambahkan halte ke rute.
    Body JSON:
    {
        "stopId": 5,
        "stopName": "Museum Kota Bandung",
        "sequenceOrder": 3,
        "distanceToNext": 1.0,
        "timeToNext": 3
    }
    """
    route = db.session.get(Route, routeId)
    if not route:
        return jsonify({'error': 'Rute tidak ditemukan.'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body harus berupa JSON.'}), 400
    
    required_fields = ['stopId', 'stopName', 'sequenceOrder']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Field {field} wajib diisi.'}), 400
    
    # Cek apakah sequence order sudah ada
    existing = RouteStop.query.filter_by(
        route_id=routeId,
        sequence_order=data['sequenceOrder']
    ).first()
    
    if existing:
        return jsonify({'error': f'Sequence order {data["sequenceOrder"]} sudah ada di rute ini.'}), 400
    
    # Tambahkan route stop
    route_stop = RouteStop(
        route_id=routeId,
        stop_id=data['stopId'],
        stop_name=data['stopName'],
        sequence_order=data['sequenceOrder'],
        distance_to_next=data.get('distanceToNext'),
        time_to_next=data.get('timeToNext')
    )
    
    db.session.add(route_stop)
    db.session.commit()
    
    return jsonify({
        'message': 'Halte berhasil ditambahkan ke rute.',
        'routeStop': route_stop.to_dict()
    }), 201

@app.route('/admin/routes/<int:routeId>/stops/<int:routeStopId>', methods=['DELETE'])
@admin_required
def admin_delete_route_stop(routeId, routeStopId):
    """
    DELETE /admin/routes/{routeId}/stops/{routeStopId}: Menghapus halte dari rute.
    """
    route_stop = RouteStop.query.filter_by(id=routeStopId, route_id=routeId).first()
    if not route_stop:
        return jsonify({'error': 'Route stop tidak ditemukan.'}), 404
    
    stop_name = route_stop.stop_name
    db.session.delete(route_stop)
    db.session.commit()
    
    return jsonify({
        'message': f'Halte {stop_name} berhasil dihapus dari rute.'
    }), 200


# ========================================
# CLI COMMANDS
# ========================================

@app.cli.command('init-db')
def init_db_command():
    """Perintah untuk menginisialisasi database."""
    with app.app_context():
        db.create_all()
        print('Database Route telah diinisialisasi.')


@app.cli.command('seed-routes')
def seed_routes_command():
    """
    Menambahkan data rute awal.
    Rute A: Masjid Jami Baitul Huda Baleendah → Matahari Land (via beberapa halte)
    """
    with app.app_context():
        # Hapus data lama
        RouteStop.query.delete()
        Route.query.delete()
        
        # Rute A: Masjid ke Matahari Land
        route_a = Route(
            name='Rute A',
            description='Rute dari Masjid Jami Baitul Huda Baleendah ke Matahari Land',
            origin='Masjid Jami Baitul Huda Baleendah',
            destination='Matahari Land',
            is_active=True
        )
        db.session.add(route_a)
        db.session.flush()
        
        # Halte-halte untuk Rute A (menggunakan stop_id dari Stop Service)
        # Jarak antar halte: 1 km, estimasi waktu: 3 menit
        stops_route_a = [
            {'stopId': 2, 'stopName': 'Masjid Jami Baitul Huda Baleendah', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 3, 'stopName': 'Griya Bandung Asri (GBA)', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 4, 'stopName': 'Sekolah Moh Toha', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 5, 'stopName': 'Museum Kota Bandung', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 6, 'stopName': 'Merdeka', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 7, 'stopName': 'Alun-alun Bandung', 'distanceToNext': None, 'timeToNext': None}  # Halte terakhir
        ]
        
        for idx, stop_data in enumerate(stops_route_a, start=1):
            route_stop = RouteStop(
                route_id=route_a.id,
                stop_id=stop_data['stopId'],
                stop_name=stop_data['stopName'],
                sequence_order=idx,
                distance_to_next=stop_data['distanceToNext'],
                time_to_next=stop_data['timeToNext']
            )
            db.session.add(route_stop)
        
        # Rute B: BEC ke Baleendah (rute balik)
        route_b = Route(
            name='Rute B',
            description='Rute dari Bandung Electronic Centre (BEC) ke Baleendah',
            origin='Bandung Electronic Centre (BEC)',
            destination='Baleendah',
            is_active=True
        )
        db.session.add(route_b)
        db.session.flush()
        
        # Halte-halte untuk Rute B
        stops_route_b = [
            {'stopId': 11, 'stopName': 'Bandung Electronic Centre (BEC) B', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 12, 'stopName': 'Stasiun Bandung B', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 13, 'stopName': 'SMAN 6 Bandung', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 14, 'stopName': 'Simpang Ijan B', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 15, 'stopName': 'Alun-alun Bandung B', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 20, 'stopName': 'Baleendah B', 'distanceToNext': None, 'timeToNext': None}
        ]
        
        for idx, stop_data in enumerate(stops_route_b, start=1):
            route_stop = RouteStop(
                route_id=route_b.id,
                stop_id=stop_data['stopId'],
                stop_name=stop_data['stopName'],
                sequence_order=idx,
                distance_to_next=stop_data['distanceToNext'],
                time_to_next=stop_data['timeToNext']
            )
            db.session.add(route_stop)
        
        # Rute C: Koridor 1 (rute tambahan)
        route_c = Route(
            name='Koridor 1',
            description='Koridor utama menghubungkan Stasiun Bandung dengan BEC',
            origin='Stasiun Bandung',
            destination='Bandung Electronic Centre (BEC)',
            is_active=True
        )
        db.session.add(route_c)
        db.session.flush()
        
        stops_route_c = [
            {'stopId': 9, 'stopName': 'Stasiun Bandung', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 8, 'stopName': 'Simpang Ijan', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 10, 'stopName': 'Bandung Electronic Centre (BEC)', 'distanceToNext': None, 'timeToNext': None}
        ]
        
        for idx, stop_data in enumerate(stops_route_c, start=1):
            route_stop = RouteStop(
                route_id=route_c.id,
                stop_id=stop_data['stopId'],
                stop_name=stop_data['stopName'],
                sequence_order=idx,
                distance_to_next=stop_data['distanceToNext'],
                time_to_next=stop_data['timeToNext']
            )
            db.session.add(route_stop)
        
        db.session.commit()
        print('3 Rute berhasil ditambahkan dengan total halte dan jarak 1 km antar halte.')

# Health check
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'route-service',
        'database': 'connected'
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Port 5002 untuk route service
    app.run(debug=True, host='0.0.0.0', port=5002)
