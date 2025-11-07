import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import requests
from functools import wraps

# Muat variabel lingkungan dari file .env
load_dotenv()

# Inisialisasi Aplikasi Flask
app = Flask(__name__)

# Konfigurasi Database
# Mengambil DATABASE_URL dari file .env
# Sesuai docker-compose, ini akan ada di /app/instance/bus.db
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../instance/bus.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Model Database ---

class Bus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nomor_polisi = db.Column(db.String(20), unique=True, nullable=False)
    kapasitas_penumpang = db.Column(db.Integer, nullable=False)
    status_gps = db.Column(db.String(10), default='Offline') # Online/Offline
    model_kendaraan = db.Column(db.String(50))
    latitude = db.Column(db.Float, default=0.0)
    longitude = db.Column(db.Float, default=0.0)

    # Helper function untuk mengubah data model menjadi dictionary (JSON)
    def to_dict(self):
        return {
            'busId': self.id,
            'nomor_polisi': self.nomor_polisi,
            'kapasitas_penumpang': self.kapasitas_penumpang,
            'status_gps': self.status_gps,
            'model_kendaraan': self.model_kendaraan,
            'lokasi_geografis': {
                'latitude': self.latitude,
                'longitude': self.longitude
            }
        }

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

# --- Endpoint API Sesuai Arsitektur ---

@app.route('/buses', methods=['POST'])
@admin_required
def register_bus():
    """
    POST /buses: Mendaftarkan bus baru ke dalam sistem.
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
        model_kendaraan=data.get('model_kendaraan'), # Ambil jika ada
        status_gps='Offline' # Bus baru default-nya Offline
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
    PUT /buses/{busId}/location: Memperbarui posisi bus secara terus-menerus.
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
    
    # Update status GPS jika ada di data, jika tidak, set ke 'Online'
    bus.status_gps = data.get('status_gps', 'Online') 
    
    db.session.commit()
    
    return jsonify(bus.to_dict()), 200

# --- Perintah CLI untuk setup database ---
@app.cli.command('init-db')
def init_db_command():
    """
    Perintah untuk menginisialisasi database.
    (Opsional: tambahkan data seed di sini jika perlu untuk development)
    """
    db.create_all()
    print('Database telah diinisialisasi.')


# Menjalankan server (sesuai port di docker-compose)
if __name__ == '__main__':
    # Port 5004 agar sesuai dengan docker-compose
    app.run(debug=True, host='0.0.0.0', port=5004)