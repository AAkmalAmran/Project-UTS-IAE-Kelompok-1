from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Bus(db.Model):
    """Model untuk menyimpan informasi bus dalam sistem transportasi."""
    __tablename__ = 'buses'
    
    # ID Bus (Primary Key)
    id = db.Column(db.Integer, primary_key=True)
    
    # Nomor Polisi (Unique)
    nomor_polisi = db.Column(db.String(20), unique=True, nullable=False)
    
    # Kapasitas Penumpang
    kapasitas_penumpang = db.Column(db.Integer, nullable=False)
    
    # Model Kendaraan
    model_kendaraan = db.Column(db.String(50))
    
    # Status GPS (Online/Offline)
    status_gps = db.Column(db.String(10), default='Offline')
    
    # Lokasi Geografis Real-time
    latitude = db.Column(db.Float, default=0.0)
    longitude = db.Column(db.Float, default=0.0)
    
    # === INTEGRASI DENGAN ROUTE SERVICE ===
    # ID Rute yang sedang dilayani bus ini (Foreign Key ke Route Service)
    route_id = db.Column(db.Integer, nullable=True)  # Null jika bus belum assigned
    
    # Nama Rute (denormalisasi untuk performa)
    route_name = db.Column(db.String(100), nullable=True)
    
    # === KECEPATAN BUS ===
    # Kecepatan rata-rata bus dalam km/jam
    average_speed = db.Column(db.Float, default=40.0)  # Default 40 km/jam
    
    # Kecepatan saat ini dalam km/jam (real-time dari GPS)
    current_speed = db.Column(db.Float, default=0.0)
    
    # Status operasional bus
    operational_status = db.Column(db.String(20), default='Available')  # Available, In Service, Maintenance, Out of Service
    
    def to_dict(self, include_route=False):
        """Helper function untuk konversi ke JSON response."""
        result = {
            'busId': self.id,
            'nomor_polisi': self.nomor_polisi,
            'kapasitas_penumpang': self.kapasitas_penumpang,
            'status_gps': self.status_gps,
            'model_kendaraan': self.model_kendaraan,
            'lokasi_geografis': {
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            'speed': {
                'current': self.current_speed,
                'average': self.average_speed
            },
            'operational_status': self.operational_status
        }
        
        if include_route and self.route_id:
            result['route'] = {
                'routeId': self.route_id,
                'routeName': self.route_name
            }
        
        return result
