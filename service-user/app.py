from auth.routes import auth_bp
from profile.routes import profile_bp
import os
import jwt
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # enable CORS untuk semua endpoint
app.config['JWT_SECRET'] = os.getenv('JWT_SECRET')

# NOTE: Untuk menambah role baru, tambahkan di sini
# Contoh role yang bisa ditambahkan:
# - SUPER_ADMIN: Akses penuh ke semua fitur
# - OPERATOR: Bisa mengakses dashboard dan mengelola data
# - USER: Hanya bisa mengakses fitur dasar
# Implementasi: Tambahkan decorator baru seperti operator_required()


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')

        if auth_header:
            # Handle both "Bearer token" and just "token"
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
            elif len(parts) == 1:
                token = parts[0]

        if not token:
            return jsonify({'error': 'token tidak ditemukan'}), 401

        try:
            # verif token
            data = jwt.decode(
                token, app.config['JWT_SECRET'], algorithms=['HS256'])
            # simpen data user dari token ke req, biar bisa diakses di endpoint
            request.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'token sudah kadaluarsa'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'token tidak valid'}), 401

        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # cek dulu apakah ada token (pakai jwt_required logic)
        token = None
        auth_header = request.headers.get('Authorization', '')

        if auth_header:
            # Handle both "Bearer token" and just "token"
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
            elif len(parts) == 1:
                token = parts[0]

        if not token:
            return jsonify({'error': 'token tidak ditemukan'}), 401

        try:
            data = jwt.decode(
                token, app.config['JWT_SECRET'], algorithms=['HS256'])
            request.user = data

            # cek apakah role admin
            if data.get('role') != 'admin':
                return jsonify({'error': 'akses ditolak, butuh role admin'}), 403

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'token sudah kadaluarsa'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'token tidak valid'}), 401

        return f(*args, **kwargs)
    return decorated


app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)

# protect update_profile endpoint dengan jwt
app.view_functions['profile_bp.update_profile'] = jwt_required(
    app.view_functions['profile_bp.update_profile'])

# protect admin endpoints - hanya admin yang bisa akses
app.view_functions['auth_bp.get_all_users'] = admin_required(
    app.view_functions['auth_bp.get_all_users'])
app.view_functions['auth_bp.delete_user'] = admin_required(
    app.view_functions['auth_bp.delete_user'])


@app.route("/")
def index():
    return "<h1>User Service API</h1>"


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
