import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, g, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps

# Muat variabel lingkungan dari file .env
load_dotenv()

app = Flask(__name__, instance_relative_config=True)

# Memastikan folder instance ada
os.makedirs(app.instance_path, exist_ok=True)

# === Konfigurasi Aplikasi ===
db_path = os.path.join(app.instance_path, 'user.db')
default_db_uri = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI", default_db_uri)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Konfigurasi JWT
JWT_SECRET = os.environ.get("JWT_SECRET", "default-secret-key")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
TOKEN_TTL_MINUTES = int(os.environ.get("TOKEN_TTL_MINUTES", 30))

app.config['JWT_SECRET'] = JWT_SECRET
app.config['JWT_ALGORITHM'] = JWT_ALGORITHM
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "flask-fallback-key")


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
    return jwt.encode(payload, app.config['JWT_SECRET'], algorithm=app.config['JWT_ALGORITHM'])

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(None, 1)[1]
        else:
            token = request.cookies.get('jwt_token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        if isinstance(token, bytes):
            token = token.decode('utf-8')
        token = token.strip().strip('"').strip("'")
        if token.startswith("b'") and token.endswith("'"):
            token = token[2:-1]
        
        try:
            data = jwt.decode(
                token, 
                app.config['JWT_SECRET'], 
                algorithms=[app.config['JWT_ALGORITHM']]
            )
            
            username = data.get('sub')
            if not username:
                return jsonify({'message': 'Token is invalid!', 'reason': 'Missing subject (sub)'}), 401
                
            current_user = User.query.filter_by(username=username).first()
            if not current_user:
                return jsonify({"error": "User not found"}), 404
            
            g.current_user = current_user
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401

        # Kirim user yang sudah ditemukan ke fungsi aslinya
        return f(current_user, *args, **kwargs)

    return decorated

# Admin role required decorator
def admin_required(f):
    @wraps(f)
    @token_required
    def decorated_function(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'message': 'Permission denied: Requires admin role.'}), 403
        return f(current_user, *args, **kwargs)
    return decorated_function


# === Routes ===

# WEB UI ENDPOINT
@app.route('/')
def index():
    """Serve the web UI"""
    return render_template('index.html')


@app.post("/login")
def login():
    """Autentikasi pengguna dan mengembalikan token."""
    credentials = request.get_json() or {}
    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        return jsonify({"message": "Username dan password wajib diisi"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Kredensial tidak valid"}), 401

    token = generate_token(user.username, user.role)
    return jsonify({
        "token": token,
        "access_token": token, 
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    })

@app.post("/register")
def register():
    """Mendaftarkan pengguna baru."""
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")

    if not username or not password:
        return jsonify({"message": "Username dan password wajib diisi"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username sudah terdaftar"}), 409

    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, password_hash=password_hash, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": f"User {username} berhasil didaftarkan.",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "role": new_user.role
        }
    }), 201


@app.get("/admin/users")
@admin_required
def get_users():
    """Get all users"""
    users = User.query.all()
    return jsonify({
        "users": [{
            "id": user.id,
            "username": user.username,
            "role": user.role
        } for user in users]
    })


@app.delete("/users/<int:user_id>")
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {user.username} deleted successfully"}), 200


@app.get("/health")
def health():
    """Endpoint untuk mengecek kesehatan layanan."""
    return {"status": "auth service healthy"}
    
@app.get("/admin/test")
@admin_required
def admin_test(current_user):
    return jsonify(message=f"Halo admin {current_user.username}! Anda berhasil masuk.")

@app.get("/verify-admin")
@token_required
def verify_admin(current_user):
    """Endpoint untuk memverifikasi apakah token adalah milik admin."""
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied: Requires admin role.'}), 403
    return jsonify({'message': 'Valid admin token', 'username': current_user.username}), 200


# === Perintah CLI untuk Database ===
@app.cli.command("init-db")
def init_db_command():
    """Membuat tabel database."""
    db.create_all()
    db.session.commit()
    print("Database diinisialisasi.")
    
@app.cli.command("seed-admin")
def seed_admin_command():
    """Membuat user admin default untuk tes."""
    username = "admin"
    password = "admin123"
    
    if User.query.filter_by(username=username).first():
        print(f"User {username} sudah ada.")
        return

    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    admin_user = User(username=username, password_hash=password_hash, role='admin')
    db.session.add(admin_user)
    db.session.commit()
    print(f"User admin '{username}' berhasil dibuat dengan password '{password}'.")


# === Main execution ===
if __name__ == "__main__":
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_RUN_PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ['true', '1']
    
    app.run(host=host, port=port, debug=debug)