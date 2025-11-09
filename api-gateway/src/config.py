from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    TESTING = os.getenv('TESTING', 'False') == 'True'
    SERVICE_URLS = {
        'user_service': os.getenv('USER_SERVICE_URL', 'http://localhost:5001'),
        'route_service': os.getenv('ROUTE_SERVICE_URL', 'http://localhost:5002'),
        'stop_service': os.getenv('STOP_SERVICE_URL', 'http://localhost:5003'),
        'bus_service': os.getenv('BUS_SERVICE_URL', 'http://localhost:5004'),
        'schedule_service': os.getenv('SCHEDULE_SERVICE_URL', 'http://localhost:5005'),
    }

# convenience top-level names for older imports
SERVICE_URLS = Config.SERVICE_URLS
USER_SERVICE_URL = SERVICE_URLS.get('user_service')
ROUTE_SERVICE_URL = SERVICE_URLS.get('route_service')
STOP_SERVICE_URL = SERVICE_URLS.get('stop_service')
BUS_SERVICE_URL = SERVICE_URLS.get('bus_service')
SCHEDULE_SERVICE_URL = SERVICE_URLS.get('schedule_service')