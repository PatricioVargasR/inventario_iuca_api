from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import bcrypt
from app import db
from models import Acceso, Permiso

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Inicio de sesión"""
    data = request.get_json()
    
    correo = data.get('correo_electronico')
    password = data.get('password')
    
    if not correo or not password:
        return jsonify({'error': 'Correo y contraseña son requeridos'}), 400
    
    # Buscar usuario
    usuario = Acceso.query.filter_by(correo_electronico=correo).first()
    
    if not usuario:
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    # Verificar contraseña
    if not bcrypt.checkpw(password.encode('utf-8'), usuario.contrasena_hash.encode('utf-8')):
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    # Actualizar último acceso
    usuario.ultimo_acceso = datetime.utcnow()
    db.session.commit()
    
    # Obtener permisos
    permisos = Permiso.query.filter_by(rol_id=usuario.rol_id).all()
    permisos_dict = {p.modulo: p.to_dict() for p in permisos}
    
    # Crear token JWT
    access_token = create_access_token(identity=usuario.id_acceso)
    
    return jsonify({
        'token': access_token,
        'usuario': usuario.to_dict(),
        'permisos': permisos_dict
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtener usuario actual"""
    user_id = get_jwt_identity()
    usuario = Acceso.query.get(user_id)
    
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify(usuario.to_dict()), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Cerrar sesión (manejado en frontend)"""
    return jsonify({'mensaje': 'Sesión cerrada exitosamente'}), 200
