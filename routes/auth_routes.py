from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import bcrypt
from app import db
from models import Acceso

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Inicio de sesión"""
    data = request.get_json()
    correo = data.get('correo_electronico')
    password = data.get('password')

    if not correo or not password:
        return jsonify({'error': 'Correo y contraseña son requeridos'}), 400

    usuario: Acceso = Acceso.query.filter_by(correo_electronico=correo).first()
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), usuario.contrasena_hash.encode('utf-8')):
        return jsonify({'error': 'Contraseña errónea'}), 401

    usuario.ultimo_acceso = datetime.utcnow()
    db.session.commit()

    # Los permisos se leen directamente del usuario — sin intermediar roles
    access_token = create_access_token(identity=str(usuario.id_acceso))

    return jsonify({
        'token': access_token,
        'usuario': usuario.to_dict(),
        'permisos': usuario.permisos_dict()   # { modulo: { puede_leer, puede_crear, ... } }
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtener usuario actual con sus permisos"""
    user_id = get_jwt_identity()
    usuario = Acceso.query.get(user_id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    return jsonify({
        **usuario.to_dict(),
        'permisos': usuario.permisos_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Cerrar sesión (token invalidado en el frontend)"""
    return jsonify({'mensaje': 'Sesión cerrada exitosamente'}), 200