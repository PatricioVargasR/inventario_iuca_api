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

def get_client_fingerprint():
    """
    Combina IP + User-Agent para identificar de forma más precisa
    al dispositivo que está haciendo la petición.
    """
    ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')
    return ip, user_agent

def _es_mismo_dispositivo(usuario, client_ip, client_ua):
    """
    Determina si la petición viene del mismo dispositivo que tiene
    la sesión activa, comparando IP y User-Agent.
    """
    misma_ip = usuario.ip_sesion == client_ip
    mismo_ua = usuario.user_agent_sesion == client_ua
    return misma_ip and mismo_ua

def _crear_sesion(usuario, client_ip, client_ua):
    """Crea un nuevo token de sesión y actualiza el usuario."""
    access_token = create_access_token(identity=str(usuario.id_acceso))
    usuario.token_sesion_activa = access_token
    usuario.fecha_inicio_sesion = datetime.now()
    usuario.ultimo_acceso = datetime.now()
    usuario.ip_sesion = client_ip
    usuario.user_agent_sesion = client_ua  # <-- campo nuevo
    db.session.commit()
    return access_token


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    correo = data.get('correo_electronico')
    password = data.get('password')

    if not correo or not password:
        return jsonify({'error': 'Correo y contraseña son requeridos'}), 400

    usuario = Acceso.query.filter_by(correo_electronico=correo).first()
    if not usuario:
        return jsonify({'error': 'Correo electrónico no encontrado'}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), usuario.contrasena_hash.encode('utf-8')):
        return jsonify({'error': 'Contraseña incorrecta'}), 401

    client_ip, client_ua = get_client_fingerprint()

    if usuario.token_sesion_activa:
        mismo_dispositivo = _es_mismo_dispositivo(usuario, client_ip, client_ua)

        if mismo_dispositivo:
            # Caso 2: misma computadora → permitir force-login
            return jsonify({
                'error': 'session_active_same_ip',
                'mensaje': 'Ya tienes una sesión abierta en este dispositivo',
                'sesion_info': {
                    'ip': usuario.ip_sesion,
                    'fecha_inicio': usuario.fecha_inicio_sesion.isoformat() if usuario.fecha_inicio_sesion else None
                }
            }), 409
        else:
            # Caso 1 y 3: diferente dispositivo (misma red o diferente red) → bloquear
            return jsonify({
                'error': 'session_active_different_ip',
                'mensaje': 'Ya existe una sesión activa desde otro dispositivo',
                'sesion_info': {
                    'ip': usuario.ip_sesion,
                    'fecha_inicio': usuario.fecha_inicio_sesion.isoformat() if usuario.fecha_inicio_sesion else None
                }
            }), 409

    access_token = _crear_sesion(usuario, client_ip, client_ua)

    return jsonify({
        'token': access_token,
        'usuario': usuario.to_dict(),
        'permisos': usuario.permisos_dict(),
        'sesion_info': {
            'ip': client_ip,
            'fecha_inicio': usuario.fecha_inicio_sesion.isoformat()
        }
    }), 200


@auth_bp.route('/force-login', methods=['POST'])
def force_login():
    """
    Solo se permite cuando es exactamente el mismo dispositivo
    (misma IP + mismo User-Agent).
    """
    data = request.get_json()
    correo = data.get('correo_electronico')
    password = data.get('password')

    if not correo or not password:
        return jsonify({'error': 'Correo y contraseña son requeridos'}), 400

    usuario = Acceso.query.filter_by(correo_electronico=correo).first()
    if not usuario:
        return jsonify({'error': 'Correo electrónico no encontrado'}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), usuario.contrasena_hash.encode('utf-8')):
        return jsonify({'error': 'Contraseña incorrecta'}), 401

    client_ip, client_ua = get_client_fingerprint()

    if usuario.token_sesion_activa:
        mismo_dispositivo = _es_mismo_dispositivo(usuario, client_ip, client_ua)
        if not mismo_dispositivo:
            return jsonify({
                'error': 'session_active_different_ip',
                'mensaje': 'La sesión activa es de otro dispositivo. No puedes forzar el cierre desde aquí.',
                'sesion_info': {
                    'ip': usuario.ip_sesion,
                    'fecha_inicio': usuario.fecha_inicio_sesion.isoformat() if usuario.fecha_inicio_sesion else None
                }
            }), 409

    access_token = _crear_sesion(usuario, client_ip, client_ua)

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

    current_token = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not usuario.token_sesion_activa:
        return jsonify({
            'error': 'session_invalidated',
            'mensaje': 'La sesión ha sido cerrada'
        }), 401

    if usuario.token_sesion_activa != current_token:
        return jsonify({
            'error': 'session_invalidated',
            'mensaje': 'Esta sesión ha sido cerrada desde otro dispositivo'
        }), 401

    return jsonify({
        **usuario.to_dict(),
        'permisos': usuario.permisos_dict()
    }), 200