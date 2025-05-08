from flask import Flask
from app.config import Config
from flask_jwt_extended import JWTManager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enregistrement des blueprints
    from app.routes.main import main_bp
    from app.routes import auth_routes, admin_routes, user_routes, visiteur_routes
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(user_routes.bp)
    app.register_blueprint(visiteur_routes.bp)
    
    app.register_blueprint(main_bp)
    # app.register_blueprint(mysql_bp, url_prefix='/mysql')
    # app.register_blueprint(postgres_bp, url_prefix='/postgres')
    
    return app