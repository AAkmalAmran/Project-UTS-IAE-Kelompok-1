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

# === URL SERVICE LAIN ===
BUS_SERVICE_URL = os.environ.get('BUS_SERVICE_URL', 'http://localhost:5004')
STOP_SERVICE_URL = os.environ.get('STOP_SERVICE_URL', 'http://service-2-stop:5003') 
USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://service-user:5001') 

# Inisialisasi Database
db.init_app(app)


# --- Middleware untuk Autentikasi Admin ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token tidak ditemukan'}), 401

        try:
            verify_url = f"{USER_SERVICE_URL}/verify-admin"
            response = requests.get(
                verify_url,
                headers={'Authorization': token}, # Kirim token yang sama
                timeout=5 # Batas waktu 5 detik
            )
            
            if response.status_code != 200:
                return jsonify({'error': 'Unauthorized - Admin role required', 'detail': response.json()}), 403
                
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Gagal terhubung ke service autentikasi: {e}")
            return jsonify({'error': 'Gagal terhubung ke service autentikasi'}), 500
            
        return f(*args, **kwargs)
    return decorated_function


# --- Helper Function: Haversine Distance ---
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
    r = 6371 # Radius bumi dalam kilometer
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
    """
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
    route = db.session.get(Route, routeId)
    if not route:
        return jsonify({'error': 'Rute tidak ditemukan.'}), 404
    
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
    query_text = request.args.get('query')
    if not query_text:
        return jsonify({'error': 'Parameter query wajib diisi.'}), 400
    
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

# ---ENDPOINT (MEMANGGIL SERVICE-2-STOP)---
@app.route('/admin/routes/find-stop', methods=['GET'])
@admin_required
def admin_find_stop_proxy():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Parameter query wajib diisi.'}), 400
        
    try:
        search_url = f"{STOP_SERVICE_URL}/stops/search"
        params = {'query': query}
        
        # Ambil token dari request asli untuk diteruskan (jika service stop juga butuh)
        auth_header = request.headers.get('Authorization')
        headers = {'Authorization': auth_header} if auth_header else {}
        
        response = requests.get(search_url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        # Kembalikan respons dari service-2-stop apa adanya
        return jsonify(response.json()), response.status_code

    except requests.exceptions.HTTPError as e:
        app.logger.error(f"Error dari service-2-stop (search): {e.response.text}")
        return jsonify({'error': 'Gagal mengambil data pencarian halte.', 'detail': str(e)}), 502
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Gagal terhubung ke service-2-stop (search): {e}")
        return jsonify({'error': 'Gagal terhubung ke service halte.'}), 503


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
    
    # Ambil header otentikasi untuk diteruskan ke service lain
    auth_header = request.headers.get('Authorization')
    validation_headers = {'Authorization': auth_header} if auth_header else {}

    try:
        # Buat rute baru (tapi jangan commit dulu)
        new_route = Route(
            name=data['name'],
            description=data.get('description'),
            origin=data['origin'],
            destination=data['destination'],
            is_active=data.get('isActive', True)
        )
        
        db.session.add(new_route)
        db.session.flush()  # Untuk mendapatkan route.id
        
        stops_to_add = [] # List sementara untuk menampung stops
        
        # Tambahkan stops jika ada
        if 'stops' in data and isinstance(data['stops'], list):
            for idx, stop_data in enumerate(data['stops'], start=1):
                
                provided_name = stop_data.get('stopName')

                # Validasi payload dari admin
                if not provided_name:
                    db.session.rollback()
                    return jsonify({'error': f'Stop ke-{idx} kekurangan stopName.'}), 400
                if 'sequenceOrder' not in stop_data:
                    db.session.rollback()
                    return jsonify({'error': f'Stop ke-{idx} kekurangan sequenceOrder.'}), 400

                # 1. Panggil service-2-stop untuk mencari halte berdasarkan nama
                search_url = f"{STOP_SERVICE_URL}/stops/search"
                params = {'query': provided_name}
                
                try:
                    resp = requests.get(search_url, headers=validation_headers, params=params, timeout=5)
                    resp.raise_for_status() # Cek error 4xx/5xx
                    
                    search_results = resp.json()
                    found_stop = None
                    results_list = search_results.get('stops', search_results if isinstance(search_results, list) else [])
                    
                    exact_matches = []
                    for stop in results_list:
                        actual_name = stop.get('stopName') or stop.get('name') or stop.get('nama_halte')
                        if actual_name and actual_name.lower() == provided_name.lower():
                            exact_matches.append(stop)

                    # 3. Validasi hasil pencarian
                    if len(exact_matches) == 0:
                        db.session.rollback()
                        return jsonify({'error': f"Validasi gagal: stopName '{provided_name}' tidak ditemukan di service-2-stop."}), 400
                    
                    if len(exact_matches) > 1:
                        db.session.rollback()
                        return jsonify({'error': f"Validasi gagal: stopName '{provided_name}' ambigu, ditemukan {len(exact_matches)} hasil."}), 400
                    
                    # Sukses, kita temukan satu halte
                    found_stop = exact_matches[0]
                    
                    # 4. Ambil stopId dari hasil pencarian
                    found_stop_id = found_stop.get('stopId') or found_stop.get('id')
                    if not found_stop_id:
                         db.session.rollback()
                         return jsonify({'error': f"Validasi sukses, tapi service-2-stop tidak mengembalikan ID untuk '{provided_name}'."}), 500

                except requests.exceptions.HTTPError as e:
                    db.session.rollback()
                    return jsonify({'error': 'Error saat validasi halte via search.', 'detail': str(e), 'status_code': e.response.status_code}), 502
                except requests.exceptions.RequestException as e:
                    db.session.rollback()
                    return jsonify({'error': 'Gagal terhubung ke service-2-stop untuk validasi search.', 'detail': str(e)}), 503

                route_stop = RouteStop(
                    route_id=new_route.id,
                    stop_id=found_stop_id,            # <- ID dari hasil search
                    stop_name=provided_name,          # <- Nama dari admin (sudah divalidasi)
                    sequence_order=stop_data['sequenceOrder'],
                    distance_to_next=stop_data.get('distanceToNext'),
                    time_to_next=stop_data.get('timeToNext')
                )
                stops_to_add.append(route_stop)
        
        db.session.add_all(stops_to_add)
        db.session.commit()
        
        return jsonify({
            'message': 'Rute berhasil ditambahkan.',
            'route': new_route.to_dict(include_stops=True)
        }), 201

    except Exception as e:
        # Catch-all jika terjadi error tak terduga
        db.session.rollback()
        app.logger.error(f"Error tak terduga di admin_add_route: {e}")
        return jsonify({'error': 'Terjadi kesalahan internal.', 'detail': str(e)}), 500


@app.route('/admin/routes/<int:routeId>', methods=['PUT'])
@admin_required
def admin_update_route(routeId):
    route = db.session.get(Route, routeId)
    if not route:
        return jsonify({'error': 'Rute tidak ditemukan.'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body harus berupa JSON.'}), 400
    
    if 'name' in data:
        existing = Route.query.filter(Route.name == data['name'], Route.id != routeId).first()
        if existing:
            return jsonify({'error': f'Rute dengan nama {data["name"]} sudah ada.'}), 400
        route.name = data['name']
    
    if 'description' in data: route.description = data['description']
    if 'origin' in data: route.origin = data['origin']
    if 'destination' in data: route.destination = data['destination']
    if 'isActive' in data: route.is_active = data['isActive']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Rute berhasil diupdate.',
        'route': route.to_dict(include_stops=True)
    }), 200


@app.route('/admin/routes/<int:routeId>', methods=['DELETE'])
@admin_required
def admin_delete_route(routeId):
    route = db.session.get(Route, routeId)
    if not route:
        return jsonify({'error': 'Rute tidak ditemukan.'}), 404
    
    route_name = route.name
    db.session.delete(route)
    db.session.commit()
    
    return jsonify({'message': f'Rute {route_name} berhasil dihapus.'}), 200


@app.route('/admin/routes/<int:routeId>/stops/add', methods=['POST'])
@admin_required
def admin_add_stop_to_route(routeId):
    route = db.session.get(Route, routeId)
    if not route:
        return jsonify({'error': 'Rute tidak ditemukan.'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body harus berupa JSON.'}), 400

    required_fields = ['stopName', 'sequenceOrder']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Field {field} wajib diisi.'}), 400
    
    provided_name = data['stopName']
    sequence_order = data['sequenceOrder']

    existing_seq = RouteStop.query.filter_by(
        route_id=routeId,
        sequence_order=sequence_order
    ).first()
    if existing_seq:
        return jsonify({'error': f'Sequence order {sequence_order} sudah ada di rute ini.'}), 400
    
    # Ambil header auth untuk validasi
    auth_header = request.headers.get('Authorization')
    validation_headers = {'Authorization': auth_header} if auth_header else {}
    found_stop_id = None
    try:
        search_url = f"{STOP_SERVICE_URL}/stops/search"
        params = {'query': provided_name}
        
        resp = requests.get(search_url, headers=validation_headers, params=params, timeout=5)
        resp.raise_for_status() # Cek error 4xx/5xx
        
        search_results = resp.json()
        
        # 2. Cari satu hasil yang sama persis (case-insensitive)
        results_list = search_results.get('stops', search_results if isinstance(search_results, list) else [])
        
        exact_matches = []
        for stop in results_list:
            actual_name = stop.get('stopName') or stop.get('name') or stop.get('nama_halte')
            if actual_name and actual_name.lower() == provided_name.lower():
                exact_matches.append(stop)

        # 3. Validasi hasil pencarian
        if len(exact_matches) == 0:
            return jsonify({'error': f"Validasi gagal: stopName '{provided_name}' tidak ditemukan di service-2-stop."}), 400
        
        if len(exact_matches) > 1:
            return jsonify({'error': f"Validasi gagal: stopName '{provided_name}' ambigu, ditemukan {len(exact_matches)} hasil."}), 400
        
        # Sukses, kita temukan satu halte
        found_stop = exact_matches[0]
        
        # 4. Ambil stopId dari hasil pencarian
        found_stop_id = found_stop.get('stopId') or found_stop.get('id')
        if not found_stop_id:
             return jsonify({'error': f"Validasi sukses, tapi service-2-stop tidak mengembalikan ID untuk '{provided_name}'."}), 500

    except requests.exceptions.HTTPError as e:
        return jsonify({'error': 'Error saat validasi halte via search.', 'detail': str(e), 'status_code': e.response.status_code}), 502
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Gagal terhubung ke service-2-stop untuk validasi search.', 'detail': str(e)}), 503

    if found_stop_id:
        existing_stop = RouteStop.query.filter_by(
            route_id=routeId,
            stop_id=found_stop_id
        ).first()
        if existing_stop:
            return jsonify({'error': f'Stop ID {found_stop_id} ({provided_name}) sudah ada di rute ini.'}), 400

    route_stop = RouteStop(
        route_id=routeId,
        stop_id=found_stop_id,        # <- ID dari hasil search
        stop_name=provided_name,      # <- Nama dari input admin
        sequence_order=sequence_order,
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
    route_stop = RouteStop.query.filter_by(id=routeStopId, route_id=routeId).first()
    if not route_stop:
        return jsonify({'error': 'Route stop tidak ditemukan.'}), 404
    
    stop_name = route_stop.stop_name
    db.session.delete(route_stop)
    db.session.commit()
    
    return jsonify({'message': f'Halte {stop_name} berhasil dihapus dari rute.'}), 200


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
    (Data ini mengasumsikan stop_id sudah ada di service-2-stop)
    """
    with app.app_context():
        # Hapus data lama
        RouteStop.query.delete()
        Route.query.delete()
        db.session.commit()
        
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
        
        stops_route_a = [
            {'stopId': 2, 'stopName': 'Masjid Jami Baitul Huda Baleendah', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 3, 'stopName': 'Griya Bandung Asri (GBA)', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 4, 'stopName': 'Sekolah Moh Toha', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 5, 'stopName': 'Museum Kota Bandung', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 6, 'stopName': 'Merdeka', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 7, 'stopName': 'Alun-alun Bandung', 'distanceToNext': None, 'timeToNext': None}
        ]
        
        for idx, stop_data in enumerate(stops_route_a, start=1):
            route_stop = RouteStop(route_id=route_a.id, sequence_order=idx, **stop_data)
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
        
        stops_route_b = [
            {'stopId': 11, 'stopName': 'Bandung Electronic Centre (BEC) B', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 12, 'stopName': 'Stasiun Bandung B', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 13, 'stopName': 'SMAN 6 Bandung', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 14, 'stopName': 'Simpang Ijan B', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 15, 'stopName': 'Alun-alun Bandung B', 'distanceToNext': 1.0, 'timeToNext': 3},
            {'stopId': 20, 'stopName': 'Baleendah B', 'distanceToNext': None, 'timeToNext': None}
        ]
        
        for idx, stop_data in enumerate(stops_route_b, start=1):
            route_stop = RouteStop(route_id=route_b.id, sequence_order=idx, **stop_data)
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
            route_stop = RouteStop(route_id=route_c.id, sequence_order=idx, **stop_data)
            db.session.add(route_stop)
        
        db.session.commit()
        print('3 Rute berhasil ditambahkan dengan total halte dan jarak 1 km antar halte.')

# Health check
@app.route('/health')
def health_check():
    # Coba koneksi database
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'disconnected: {e}'

    return jsonify({
        'status': 'healthy',
        'service': 'route-service',
        'database': db_status
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Port 5002 untuk route service
    app.run(debug=True, host='0.0.0.0', port=5002)