from flask import Flask
from app.config import Config
from flask_jwt_extended import JWTManager

jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialiser les extensions
    jwt.init_app(app)
    
    # Enregistrement des blueprints
    from app.routes.main import main_bp
    from app.routes import auth_routes, admin_routes, user_routes, visiteur_routes
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(admin_routes.admin_bp)
    app.register_blueprint(user_routes.user_bp)
    app.register_blueprint(visiteur_routes.visitor_bp)
    
    app.register_blueprint(main_bp)
    # app.register_blueprint(mysql_bp, url_prefix='/mysql')
    # app.register_blueprint(postgres_bp, url_prefix='/postgres')
    
    return app