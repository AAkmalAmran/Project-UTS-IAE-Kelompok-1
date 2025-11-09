from flask import Flask
from src.routes.route import route_bp
from src.routes.stop import stop_bp
from src.routes.bus import bus_bp
from src.routes.schedule import schedule_bp
from src.routes.user import user_bp
from src.config import Config


def create_app():
    app = Flask(__name__)
    # load minimal config
    app.config['DEBUG'] = Config.DEBUG
    app.config['TESTING'] = Config.TESTING
    app.config['SERVICE_URLS'] = Config.SERVICE_URLS

    # Register blueprints for each service under a base prefix
    API_PREFIX = app.config.get('API_PREFIX', '/api')
    app.register_blueprint(route_bp, url_prefix=f"{API_PREFIX}/routes")
    app.register_blueprint(stop_bp, url_prefix=f"{API_PREFIX}/stops")
    app.register_blueprint(bus_bp, url_prefix=f"{API_PREFIX}/buses")
    app.register_blueprint(schedule_bp, url_prefix=f"{API_PREFIX}/schedules")
    app.register_blueprint(user_bp, url_prefix=f"{API_PREFIX}/users")

    return app


app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)