from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Schedule(db.Model):
    """Model untuk menyimpan jadwal keberangkatan bus pada rute tertentu."""
    __tablename__ = 'schedules'
    
    # ID Schedule (Primary Key)
    id = db.Column(db.Integer, primary_key=True)
    
    # ID Rute (Foreign Key ke Route Service)
    route_id = db.Column(db.Integer, nullable=False)
    
    # Nama Rute (denormalisasi)
    route_name = db.Column(db.String(100), nullable=False)
    
    # ID Bus (Foreign Key ke Bus Service)
    bus_id = db.Column(db.Integer, nullable=False)
    
    # Nomor Polisi Bus (denormalisasi)
    bus_number = db.Column(db.String(20), nullable=False)
    
    # Waktu Keberangkatan (format: HH:MM, misal: "06:00", "07:30")
    departure_time = db.Column(db.String(5), nullable=False)
    
    # Hari operasional (JSON string: ["Monday", "Tuesday", ...] atau "Daily")
    operating_days = db.Column(db.String(200), default='Daily')
    
    # Status jadwal (Active/Inactive)
    is_active = db.Column(db.Boolean, default=True)
    
    # Frekuensi (dalam menit) - untuk jadwal berulang
    # Misal: 15 berarti bus berangkat setiap 15 menit
    frequency_minutes = db.Column(db.Integer, nullable=True)
    
    # Waktu dibuat
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Helper function untuk konversi ke JSON response."""
        return {
            'scheduleId': self.id,
            'routeId': self.route_id,
            'routeName': self.route_name,
            'busId': self.bus_id,
            'busNumber': self.bus_number,
            'departureTime': self.departure_time,
            'operatingDays': self.operating_days,
            'isActive': self.is_active,
            'frequencyMinutes': self.frequency_minutes,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }


class BusArrival(db.Model):
    """
    Model untuk menyimpan prediksi kedatangan bus di halte tertentu.
    Data ini di-generate secara dinamis berdasarkan lokasi real-time bus.
    """
    __tablename__ = 'bus_arrivals'
    
    # ID Arrival (Primary Key)
    id = db.Column(db.Integer, primary_key=True)
    
    # ID Halte (Foreign Key ke Stop Service)
    stop_id = db.Column(db.Integer, nullable=False)
    
    # Nama Halte (denormalisasi)
    stop_name = db.Column(db.String(100), nullable=False)
    
    # ID Bus (Foreign Key ke Bus Service)
    bus_id = db.Column(db.Integer, nullable=False)
    
    # Nomor Polisi Bus
    bus_number = db.Column(db.String(20), nullable=False)
    
    # ID Rute
    route_id = db.Column(db.Integer, nullable=False)
    
    # Nama Rute
    route_name = db.Column(db.String(100), nullable=False)
    
    # Estimasi waktu kedatangan (dalam menit)
    eta_minutes = db.Column(db.Integer, nullable=False)
    
    # Jarak bus ke halte (dalam kilometer)
    distance_km = db.Column(db.Float, nullable=False)
    
    # Waktu prediksi dibuat
    predicted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status (Approaching, Arrived, Departed)
    status = db.Column(db.String(20), default='Approaching')
    
    def to_dict(self):
        """Helper function untuk konversi ke JSON response."""
        return {
            'arrivalId': self.id,
            'stopId': self.stop_id,
            'stopName': self.stop_name,
            'busId': self.bus_id,
            'busNumber': self.bus_number,
            'routeId': self.route_id,
            'routeName': self.route_name,
            'etaMinutes': self.eta_minutes,
            'distanceKm': round(self.distance_km, 2),
            'status': self.status,
            'predictedAt': self.predicted_at.isoformat() if self.predicted_at else None
        }
