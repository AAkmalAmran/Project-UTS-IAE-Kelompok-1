import os
import requests
import jwt 
from flask import Flask, request, jsonify, Response, send_from_directory, g
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(
    __name__,
    static_folder='frontend',
    static_url_path=''
)
CORS(app) 
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
if not app.config["JWT_SECRET_KEY"]:
    raise ValueError("JWT_SECRET_KEY tidak diatur di environment variables. Tambahkan ke file .env")

PUBLIC_PATHS = [
    '/',                      
    '/index.html',            
    '/admin.html',           
    '/api/user/login',
    '/api/user/register',
    '/api/route/routes',
    '/api/stop/stops',
    '/api/bus/buses',
    '/api/schedule/schedules'
]

SERVICE_URLS = {
    "user": os.environ.get("USER_SERVICE_URL"),      # http://service-user:5001
    "route": os.environ.get("ROUTE_SERVICE_URL"),     # http://service-1-route:5002
    "stop": os.environ.get("STOP_SERVICE_URL"),       # http://service-2-stop:5003
    "bus": os.environ.get("BUS_SERVICE_URL"),         # http://service-3-bus:5004
    "schedule": os.environ.get("SCHEDULE_SERVICE_URL")# http://service-4-schedule:5005
}

# --- Hook Validasi JWT ---
@app.before_request
def require_jwt_authentication():
    """
    Hook ini berjalan sebelum SETIAP request.
    """
    # 1. Cek apakah path request ada di daftar publik
    if request.path in PUBLIC_PATHS:
        return  # Lewati pemeriksaan, lanjutkan ke rute

    # 2. Dapatkan dan validasi token JWT
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Authorization header is missing"}), 401

    try:
        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            raise ValueError("Format header Authorization tidak valid")

        token = parts[1]
        payload = jwt.decode(
            token,
            app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        g.user_payload = payload

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except (jwt.InvalidTokenError, ValueError) as e:
        return jsonify({"error": "Invalid token", "details": str(e)}), 401

    # 3. Validasi Role Admin
    if '/admin' in request.path:
        if request.path == '/admin.html':
            return

        role = g.user_payload.get('role')
        if role != 'admin':
            return jsonify({"error": "Admin access required for this resource"}), 403
    return


# 2. Fungsi forwarder 
def forward_to_service(service_name, path):
    """
    Menerima request dari client dan meneruskannya (forward)
    ke service internal yang sesuai.
    """
    # Dapatkan URL service dari "peta"
    base_url = SERVICE_URLS.get(service_name)
    if not base_url:
        return jsonify({"error": f"Service '{service_name}' not configured"}), 500

    # Gabungkan URL service dengan sisa path dari request
    full_url = f"{base_url}/{path}"

    headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}

    try:
        resp = requests.request(
            method=request.method,       # Teruskan metode (GET, POST, dll)
            url=full_url,                # URL service internal
            headers=headers,             # Teruskan header (termasuk token)
            data=request.get_data(),
            params=request.args,
            allow_redirects=False,
            timeout=10.0               # Batas waktu 10 detik
        )

        # 3. Buat respons baru untuk dikirim kembali ke client
        excluded_headers = ['content-encoding', 'transfer-encoding', 'connection', 'content-length']

        response_headers = [
            (k, v) for k, v in resp.headers.items()
            if k.lower() not in excluded_headers
        ]

        response = Response(resp.content, resp.status_code, response_headers)
        return response

    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Service '{service_name}' is unavailable"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": f"Service '{service_name}' timed out"}), 504

# === Rute Gateway ===

@app.route('/admin.html')
def admin_page():
    """Melayani halaman admin.html"""
    return send_from_directory(app.static_folder, 'admin.html')

@app.route('/')
def index_page():
    """Melayani halaman index.html"""
    return send_from_directory(app.static_folder, 'index.html')

# --- Rute Forwarding ---
@app.route('/api/user/', defaults={'path': ''})
@app.route('/api/user/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def user_service(path):
    return forward_to_service("user", path)

@app.route('/api/route/', defaults={'path': ''})
@app.route('/api/route/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_service(path):
    return forward_to_service("route", path)

@app.route('/api/stop/', defaults={'path': ''})
@app.route('/api/stop/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def stop_service(path):
    return forward_to_service("stop", path)

@app.route('/api/bus/', defaults={'path': ''})
@app.route('/api/bus/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def bus_service(path):
    return forward_to_service("bus", path)

@app.route('/api/schedule/', defaults={'path': ''})
@app.route('/api/schedule/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def schedule_service(path):
    return forward_to_service("schedule", path)

# Menjalankan server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)