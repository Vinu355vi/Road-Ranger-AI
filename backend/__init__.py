from flask import Flask
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)

    # Register Blueprints
    from backend.routes.api_routes import api
    from backend.routes.dashboard_routes import dashboard

    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(dashboard)

    return app
