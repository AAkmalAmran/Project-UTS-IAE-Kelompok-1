from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Route(db.Model):
    """Model untuk menyimpan informasi rute transportasi umum."""
    __tablename__ = 'routes'
    
    # ID Rute (Primary Key)
    id = db.Column(db.Integer, primary_key=True)
    
    # Nama Rute (misal: "Rute A", "Koridor 1")
    name = db.Column(db.String(100), nullable=False, unique=True)
    
    # Deskripsi Rute
    description = db.Column(db.String(255))
    
    # Titik Awal (Origin)
    origin = db.Column(db.String(100), nullable=False)
    
    # Titik Akhir (Destination)
    destination = db.Column(db.String(100), nullable=False)
    
    # Status Aktif/Tidak Aktif
    is_active = db.Column(db.Boolean, default=True)
    
    # Relasi dengan RouteStop (one-to-many)
    route_stops = db.relationship('RouteStop', backref='route', lazy=True, cascade='all, delete-orphan', order_by='RouteStop.sequence_order')
    
    def to_dict(self, include_stops=False):
        """Helper function untuk konversi ke JSON response."""
        result = {
            'routeId': self.id,
            'name': self.name,
            'description': self.description,
            'origin': self.origin,
            'destination': self.destination,
            'isActive': self.is_active
        }
        
        if include_stops:
            result['stops'] = [rs.to_dict() for rs in self.route_stops]
            result['totalStops'] = len(self.route_stops)
            result['totalDistance'] = sum(rs.distance_to_next for rs in self.route_stops if rs.distance_to_next)
        
        return result


class RouteStop(db.Model):
    """Model untuk menyimpan urutan halte pada setiap rute beserta jarak antar halte."""
    __tablename__ = 'route_stops'
    
    # ID RouteStop (Primary Key)
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key ke Route
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    
    # ID Halte (referensi ke Stop Service)
    stop_id = db.Column(db.Integer, nullable=False)
    
    # Nama Halte (denormalisasi untuk performa, bisa di-sync dari Stop Service)
    stop_name = db.Column(db.String(100), nullable=False)
    
    # Urutan halte dalam rute (1, 2, 3, dst.)
    sequence_order = db.Column(db.Integer, nullable=False)
    
    # Jarak ke halte berikutnya dalam kilometer (null jika halte terakhir)
    distance_to_next = db.Column(db.Float, nullable=True)
    
    # Estimasi waktu tempuh ke halte berikutnya dalam menit (opsional)
    time_to_next = db.Column(db.Integer, nullable=True)
    
    # Unique constraint: satu rute tidak boleh punya stop_id yang sama di sequence yang sama
    __table_args__ = (
        db.UniqueConstraint('route_id', 'sequence_order', name='unique_route_sequence'),
    )
    
    def to_dict(self):
        """Helper function untuk konversi ke JSON response."""
        return {
            'routeStopId': self.id,
            'stopId': self.stop_id,
            'stopName': self.stop_name,
            'sequenceOrder': self.sequence_order,
            'distanceToNext': self.distance_to_next,
            'timeToNext': self.time_to_next
        }
