import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

# Muat variabel lingkungan dari file .env
load_dotenv()

app = Flask(__name__)

# === Konfigurasi Aplikasi ===
# Memuat konfigurasi dari variabel lingkungan (.env)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///./instance/user.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
JWT_SECRET = os.environ.get("JWT_SECRET", "default-secret-key") # Default value untuk keamanan
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
TOKEN_TTL_MINUTES = int(os.environ.get("TOKEN_TTL_MINUTES", 30))

# Memastikan folder 'instance' ada
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# === Inisialisasi Database ===
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# === Model Database ===
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Menyimpan hash, bukan password asli
    role = db.Column(db.String(80), nullable=False, default='user')

    def __repr__(self):
        return f'<User {self.username}>'


# === Fungsi Helper ===
def generate_token(username: str, role: str) -> str:
    """Membuat JWT token baru."""
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MINUTES),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# === Routes ===
@app.post("/login")
def login():
    """Autentikasi pengguna dan mengembalikan token."""
    credentials = request.get_json() or {}
    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        return jsonify({"message": "Username dan password wajib diisi"}), 400

    # Mengambil user dari database
    user = User.query.filter_by(username=username).first()

    # Memvalidasi user dan mengecek hash password
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Kredensial tidak valid"}), 401

    # Jika valid, buat token
    token = generate_token(user.username, user.role)
    return jsonify({"access_token": token})

@app.post("/register")
def register():
    """Mendaftarkan pengguna baru."""
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")

    if not username or not password:
        return jsonify({"message": "Username dan password wajib diisi"}), 400

    # Cek apakah username sudah ada
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username sudah terdaftar"}), 409

    # Hash password sebelum disimpan
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, password_hash=password_hash, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": f"User {username} berhasil didaftarkan."}), 201


@app.get("/health")
def health():
    """Endpoint untuk mengecek kesehatan layanan."""
    return {"status": "auth service healthy"}


# === Perintah CLI untuk Database ===
@app.cli.command("init-db")
def init_db_command():
    """Membuat tabel database."""
    db.create_all()

    db.session.commit()
    print("Database diinisialisasi.")


# === Main execution ===
if __name__ == "__main__":
    # Mengambil host, port, dan debug dari .env
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_RUN_PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ['true', '1']
    
    app.run(host=host, port=port, debug=debug)