from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# Inicialización de extensiones
db = SQLAlchemy()
jwt = JWTManager()