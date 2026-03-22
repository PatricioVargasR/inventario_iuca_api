"""
Rutas para manejo de bloqueos y concurrencia
Sistema de Inventario IUCA
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.concurrency import (
    crear_bloqueo,
    liberar_bloqueo,
    obtener_bloqueo,
    limpiar_bloqueos_expirados
)
from models import Acceso, BloqueoActivo
from utils.decorators import require_permission

concurrency_bp = Blueprint('concurrency', __name__)

@concurrency_bp.route('/lock', methods=['POST'])
@jwt_required()
def adquirir_bloqueo():
    """
    Adquiere un bloqueo de edición para un registro
    Body: { tabla: str, registro_id: int, duracion_minutos: int (opcional) }
    """
    user_id = int(get_jwt_identity())
    usuario = Acceso.query.get(user_id)

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    data = request.get_json()
    tabla = data.get('tabla')
    registro_id = data.get('registro_id')
    duracion = data.get('duracion_minutos', 10)

    if not tabla or not registro_id:
        return jsonify({'error': 'Tabla y registro_id son requeridos'}), 400

    success, resultado = crear_bloqueo(
        tabla=tabla,
        registro_id=registro_id,
        usuario_id=user_id,
        nombre_usuario=usuario.nombre_usuario,
        duracion_minutos=duracion
    )

    if success:
        return jsonify({
            'mensaje': 'Bloqueo adquirido exitosamente',
            'bloqueo': resultado
        }), 200
    else:
        return jsonify(resultado), 409  # 409 Conflict


@concurrency_bp.route('/unlock', methods=['POST'])
@jwt_required()
def liberar_bloqueo_endpoint():
    """
    Libera un bloqueo de edición
    Body: { tabla: str, registro_id: int }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()

    tabla = data.get('tabla')
    registro_id = data.get('registro_id')

    if not tabla or not registro_id:
        return jsonify({'error': 'Tabla y registro_id son requeridos'}), 400

    success = liberar_bloqueo(tabla, registro_id, user_id)

    if success:
        return jsonify({'mensaje': 'Bloqueo liberado exitosamente'}), 200
    else:
        return jsonify({'error': 'No se pudo liberar el bloqueo'}), 400


@concurrency_bp.route('/check-lock', methods=['GET'])
@jwt_required()
def verificar_bloqueo():
    """
    Verifica si un registro está bloqueado
    Query params: tabla, registro_id
    """
    tabla = request.args.get('tabla')
    registro_id = request.args.get('registro_id', type=int)

    if not tabla or not registro_id:
        return jsonify({'error': 'Tabla y registro_id son requeridos'}), 400

    bloqueo = obtener_bloqueo(tabla, registro_id)

    if bloqueo:
        return jsonify({
            'bloqueado': True,
            'bloqueo': bloqueo.to_dict()
        }), 200
    else:
        return jsonify({
            'bloqueado': False,
            'bloqueo': None
        }), 200

@concurrency_bp.route('/active-locks', methods=['GET'])
@jwt_required()
@require_permission('acceso', 'puede_leer')
def obtener_bloqueos_activos():
    """
    Obtiene todos los bloqueos activos del sistema
    """
    limpiar_bloqueos_expirados()

    bloqueos = BloqueoActivo.query.all()

    return jsonify({
        'bloqueos': [b.to_dict() for b in bloqueos],
        'total': len(bloqueos)
    }), 200


@concurrency_bp.route('/my-locks', methods=['GET'])
@jwt_required()
def obtener_mis_bloqueos():
    """
    Obtiene los bloqueos activos del usuario actual
    """
    user_id = int(get_jwt_identity())

    bloqueos = BloqueoActivo.query.filter_by(usuario_id=user_id).all()

    return jsonify({
        'bloqueos': [b.to_dict() for b in bloqueos],
        'total': len(bloqueos)
    }), 200