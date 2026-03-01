
# ============================================
# SISTEMA DE INVENTARIO IUCA - API REST
# Framework: Flask
# Base de Datos: PostgreSQL
# Autor: Janneth y Patricio
# ============================================

# ============================================
# app.py - Aplicación Principal
# ============================================

from flask import Flask
from utils.extesions import db, jwt
from flask_cors import CORS
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensiones
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:8080", "http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Registrar blueprints
    from routes.auth_routes import auth_bp
    from routes.equipos_routes import equipos_bp
    from routes.mobiliario_routes import mobiliario_bp
    from routes.usuarios_routes import usuarios_bp
    from routes.catalogos_routes import catalogos_bp
    from routes.historial_routes import historial_bp
    from routes.vistas_routes import vistas_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(equipos_bp, url_prefix='/api/equipos')
    app.register_blueprint(mobiliario_bp, url_prefix='/api/mobiliario')
    app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
    app.register_blueprint(catalogos_bp, url_prefix='/api/catalogos')
    app.register_blueprint(historial_bp, url_prefix=('/api/historial'))
    app.register_blueprint(vistas_bp, url_prefix=('/api/vistas'))
    
    # Manejador de errores
    from utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
