import os
import requests
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# 1. Ambil "peta" alamat service dari .env
# Ini akan cocok dengan yang ada di docker-compose.yml Anda
SERVICE_URLS = {
    "user": os.environ.get("USER_SERVICE_URL"),      # http://service-user:5001
    "route": os.environ.get("ROUTE_SERVICE_URL"),     # http://service-1-route:5002
    "stop": os.environ.get("STOP_SERVICE_URL"),       # http://service-2-stop:5003
    "bus": os.environ.get("BUS_SERVICE_URL"),         # http://service-3-bus:5004
    "schedule": os.environ.get("SCHEDULE_SERVICE_URL")# http://service-4-schedule:5005
}

# 2. Fungsi utama untuk meneruskan request
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
    # Contoh: 'http://service-user:5001' + '/login'
    # Contoh: 'http://service-user:5001' + '/admin/users'
    full_url = f"{base_url}/{path}"
    
    # ----------------------------------------------------
    # INI BAGIAN PENTING UNTUK AUTENTIKASI ANDA:
    # ----------------------------------------------------
    # Salin semua header dari request asli dari client,
    # termasuk 'Authorization', 'Content-Type', dll.
    # Kecualikan header 'Host', karena host-nya sekarang adalah container gateway
    headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}

    try:
        # Panggil service internal menggunakan library 'requests'
        # 'requests' akan bertindak sebagai client di dalam gateway
        resp = requests.request(
            method=request.method,       # Teruskan metode (GET, POST, dll)
            url=full_url,                # URL service internal
            headers=headers,             # Teruskan header (termasuk token)
            data=request.get_data(),     # Teruskan body (JSON, form, dll)
            params=request.args,       # Teruskan query params (misal: ?lat=123)
            allow_redirects=False,     # Gateway tidak boleh auto-redirect
            timeout=10.0               # Batas waktu 10 detik
        )

        # 3. Buat respons baru untuk dikirim kembali ke client
        
        # Hapus header 'hop-by-hop' yang tidak boleh diteruskan
        excluded_headers = ['content-encoding', 'transfer-encoding', 'connection', 'content-length']
        
        # Salin header dari respons service internal
        response_headers = [
            (k, v) for k, v in resp.headers.items()
            if k.lower() not in excluded_headers
        ]
        
        # Buat Flask Response dan kirim kembali ke client asli
        response = Response(resp.content, resp.status_code, response_headers)
        return response

    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Service '{service_name}' is unavailable"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": f"Service '{service_name}' timed out"}), 504

# === Tentukan Rute Gateway ===
# (Ini adalah "papan petunjuk" di lobi resepsionis)

@app.route('/', methods=['GET'])
def gateway_index():
    """Halaman root dari gateway itu sendiri."""
    return jsonify({
        "message": "Welcome to the API Gateway",
        "info": "Requests are routed based on URL prefix.",
        "prefixes": [
            "/api/user/<path>",
            "/api/route/<path>",
            "/api/stop/<path>",
            "/api/bus/<path>",
            "/api/schedule/<path>",
        ]
    })

# Semua request ke /api/user/* akan diteruskan ke SERVICE_USER_URL
# Contoh:
# GET /api/user/health -> service-user:5001/health
# POST /api/user/login -> service-user:5001/login
# GET /api/user/admin/users -> service-user:5001/admin/users
@app.route('/api/user/', defaults={'path': ''}) # Menangani /api/user/
@app.route('/api/user/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def user_service(path):
    return forward_to_service("user", path)

# Semua request ke /api/route/* akan diteruskan ke SERVICE_ROUTE_URL
@app.route('/api/route/', defaults={'path': ''})
@app.route('/api/route/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_service(path):
    return forward_to_service("route", path)

# Semua request ke /api/stop/* akan diteruskan ke SERVICE_STOP_URL
@app.route('/api/stop/', defaults={'path': ''})
@app.route('/api/stop/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def stop_service(path):
    return forward_to_service("stop", path)

# Semua request ke /api/bus/* akan diteruskan ke SERVICE_BUS_URL
@app.route('/api/bus/', defaults={'path': ''})
@app.route('/api/bus/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def bus_service(path):
    return forward_to_service("bus", path)

# Semua request ke /api/schedule/* akan diteruskan ke SERVICE_SCHEDULE_URL
@app.route('/api/schedule/', defaults={'path': ''})
@app.route('/api/schedule/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def schedule_service(path):
    return forward_to_service("schedule", path)

# Menjalankan server
if __name__ == '__main__':
    # Port 5000 adalah port untuk gateway
    app.run(debug=True, host='0.0.0.0', port=5000)