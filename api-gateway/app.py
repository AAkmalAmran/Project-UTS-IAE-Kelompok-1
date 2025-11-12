import os
import requests
import jwt
from flask import Flask, request, jsonify, Response, g
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- 1. Konfigurasi JWT ---
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
if not app.config["JWT_SECRET_KEY"]:
    raise ValueError("JWT_SECRET_KEY tidak diatur di environment variables. Tambahkan ke file .env")

# --- 2. Daftar Rute Publik ---
PUBLIC_PATHS = [
    '/',
    '/api/user/<path:path>',
    '/api/user/login',
    '/api/user/register',
    '/api/route/<path:path>',
    '/api/stop/<path:path>',
    '/api/bus/<path:path>',
    '/api/schedule/<path:path>'

]

SERVICE_URLS = {
    "user": os.environ.get("USER_SERVICE_URL"),      # http://service-user:5001
    "route": os.environ.get("ROUTE_SERVICE_URL"),     # http://service-1-route:5002
    "stop": os.environ.get("STOP_SERVICE_URL"),       # http://service-2-stop:5003
    "bus": os.environ.get("BUS_SERVICE_URL"),         # http://service-3-bus:5004
    "schedule": os.environ.get("SCHEDULE_SERVICE_URL")# http://service-4-schedule:5005
}

# --- 3. Hook Validasi JWT ---
@app.before_request
def require_jwt_authentication():
    # 1. Periksa apakah rute yang diminta ada di daftar publik
    if request.path in PUBLIC_PATHS:
        return

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
    
    # --- 3. Validasi Role Admin (Otorisasi) ---
    if '/admin' in request.path:
        role = g.user_payload.get('role')
        
        if role != 'admin':
            return jsonify({"error": "Admin access required for this resource"}), 403
    return


# --- 4. Fungsi Forwarder ---
def forward_to_service(service_name, path):
    """
    Menerima request dari client dan meneruskannya (forward)
    ke service internal yang sesuai.
    """
    base_url = SERVICE_URLS.get(service_name)
    if not base_url:
        return jsonify({"error": f"Service '{service_name}' not configured"}), 500

    full_url = f"{base_url}/{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}

    try:
        resp = requests.request(
            method=request.method,
            url=full_url,
            headers=headers,
            data=request.get_data(),
            params=request.args,
            allow_redirects=False,
            timeout=10.0
        )

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
@app.route('/', methods=['GET'])
def gateway_index():
    """Halaman root dari gateway itu sendiri."""
    return jsonify({
        "message": "Welcome to the API Gateway",
        "info": "Requests are routed based on URL prefix. Routes containing '/admin' are admin-protected.",
        "prefixes": [
            "/api/user/<path>",
            "/api/route/<path>",
            "/api/stop/<path>",
            "/api/bus/<path>",
            "/api/schedule/<path>",
        ]
    })

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)