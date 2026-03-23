from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import bcrypt
from app import db
from models import Acceso

auth_bp = Blueprint('auth', __name__)


def get_client_ip():
    """Obtiene la IP real del cliente considerando proxies"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr


@auth_bp.route('/login', methods=['POST'])
def login():
    """Inicio de sesión con control de sesión única basado en IP"""
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

    # Obtener IP del cliente actual
    client_ip = get_client_ip()

    # VERIFICAR SI YA HAY UNA SESIÓN ACTIVA
    if usuario.token_sesion_activa:
        # Caso 1: Misma IP → Cerrar sesión anterior automáticamente
        if usuario.ip_sesion == client_ip:
            # Limpiar sesión anterior (mismo dispositivo/red)
            usuario.token_sesion_activa = None
            usuario.fecha_inicio_sesion = None
            usuario.ip_sesion = None
            db.session.commit()

            # Continuar con el login normal (se creará nueva sesión abajo)

        # Caso 2: IP diferente → Solo avisar, NO permitir login
        else:
            return jsonify({
                'error': 'session_active_different_ip',
                'mensaje': 'Ya existe una sesión activa desde otra ubicación',
                'sesion_info': {
                    'ip': usuario.ip_sesion,
                    'fecha_inicio': usuario.fecha_inicio_sesion.isoformat() if usuario.fecha_inicio_sesion else None
                }
            }), 409  # 409 Conflict

    # CREAR NUEVO TOKEN Y REGISTRAR SESIÓN
    access_token = create_access_token(identity=str(usuario.id_acceso))

    # Actualizar información de sesión
    usuario.token_sesion_activa = access_token
    usuario.fecha_inicio_sesion = datetime.now()
    usuario.ultimo_acceso = datetime.now()
    usuario.ip_sesion = client_ip

    db.session.commit()

    return jsonify({
        'token': access_token,
        'usuario': usuario.to_dict(),
        'permisos': usuario.permisos_dict(),
        'sesion_info': {
            'ip': client_ip,
            'fecha_inicio': usuario.fecha_inicio_sesion.isoformat()
        }
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Cerrar sesión y limpiar token activo"""
    user_id = get_jwt_identity()
    usuario = Acceso.query.get(user_id)

    if usuario:
        # Limpiar información de sesión completamente
        usuario.token_sesion_activa = None
        usuario.fecha_inicio_sesion = None
        usuario.ip_sesion = None
        db.session.commit()

    return jsonify({'mensaje': 'Sesión cerrada exitosamente'}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtener usuario actual y verificar validez de sesión"""
    user_id = get_jwt_identity()
    usuario = Acceso.query.get(user_id)

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    # VERIFICAR QUE EL TOKEN SEA EL ACTIVO
    current_token = request.headers.get('Authorization', '').replace('Bearer ', '')

    # Si no hay token activo registrado, la sesión es inválida
    if not usuario.token_sesion_activa:
        return jsonify({
            'error': 'session_invalidated',
            'mensaje': 'La sesión ha sido cerrada'
        }), 401

    # Si el token no coincide, fue invalidado por otro login
    if usuario.token_sesion_activa != current_token:
        return jsonify({
            'error': 'session_invalidated',
            'mensaje': 'Esta sesión ha sido cerrada desde otro dispositivo'
        }), 401

    return jsonify({
        **usuario.to_dict(),
        'permisos': usuario.permisos_dict()
    }), 200
