from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Stop(db.Model):
    # ID Halte (StopId)
    id = db.Column(db.Integer, primary_key=True)
    # Nama Halte
    name = db.Column(db.String(100), nullable=False)
    # Alamat (Opsional, untuk detail)
    address = db.Column(db.String(255))
    
    # Koordinat Geografis
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    # === Fasilitas Halte (Boolean) ===
    shelter = db.Column(db.Boolean, default=False)
    seating = db.Column(db.Boolean, default=False)
    lighting = db.Column(db.Boolean, default=False)
    
    # Aksesibilitas
    wheelchair_access = db.Column(db.Boolean, default=False) # Akses Kursi Roda
    guiding_block = db.Column(db.Boolean, default=False)     # Guiding Block
    
    # Fasilitas Teknologi
    digital_eta_display = db.Column(db.Boolean, default=False)
    charging_port = db.Column(db.Boolean, default=False)

    def to_dict(self):
        """Helper function untuk konversi ke JSON response."""
        return {
            'stopId': self.id,
            'name': self.name,
            'address': self.address,
            'coordinates': {
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            'facilities': {
                'shelter': self.shelter,
                'seating': self.seating,
                'lighting': self.lighting,
                'wheelchair_access': self.wheelchair_access,
                'guiding_block': self.guiding_block,
                'digital_eta_display': self.digital_eta_display,
                'charging_port': self.charging_port
            }
        }