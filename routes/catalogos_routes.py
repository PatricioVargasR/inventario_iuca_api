from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models import CatArea, CatTipoActivo, CatEstado, CatTipoMobiliario, CatRol

catalogos_bp = Blueprint('catalogos', __name__)

@catalogos_bp.route('/areas', methods=['GET'])
@jwt_required()
def get_areas():
    """Listar áreas"""
    areas = CatArea.query.all()
    return jsonify([a.to_dict() for a in areas]), 200


@catalogos_bp.route('/tipos-activo', methods=['GET'])
@jwt_required()
def get_tipos_activo():
    """Listar tipos de activo"""
    tipos = CatTipoActivo.query.all()
    return jsonify([t.to_dict() for t in tipos]), 200


@catalogos_bp.route('/estados', methods=['GET'])
@jwt_required()
def get_estados():
    """Listar estados"""
    estados = CatEstado.query.all()
    return jsonify([e.to_dict() for e in estados]), 200


@catalogos_bp.route('/tipos-mobiliario', methods=['GET'])
@jwt_required()
def get_tipos_mobiliario():
    """Listar tipos de mobiliario"""
    tipos = CatTipoMobiliario.query.all()
    return jsonify([t.to_dict() for t in tipos]), 200


@catalogos_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """Listar roles"""
    roles = CatRol.query.all()
    return jsonify([r.to_dict() for r in roles]), 200