from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models import HistorialMovimiento
from utils.decorators import require_permission

historial_bp = Blueprint('historial', __name__)

# ============================================
# Historial de Movimiento
# ============================================

@historial_bp.route('/movimientos', methods=['GET'])
@jwt_required()
def get_movimientos():
    """Listar todos los movimientos disponibles"""
    movimientos = HistorialMovimiento.query.all()
    return jsonify([m.to_dict() for m in movimientos]), 200

@historial_bp.route('/movimiento/<int:id>', methods=['GET'])
@jwt_required()
def get_movimiento(id):
    """Obtener movimiento por ID"""
    movimiento = HistorialMovimiento.query.get(id)

    if not movimiento:
        return jsonify({
            'error': 'Movimiento no encontrado'
        }), 404

    return jsonify(movimiento.to_dict()), 200