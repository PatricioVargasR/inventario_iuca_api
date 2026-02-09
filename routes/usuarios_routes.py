from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models import Usuario, Acceso, CatRol
from utils.decorators import require_permission
import bcrypt

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/responsables', methods=['GET'])
@jwt_required()
def get_responsables():
    """Listar usuarios responsables"""
    usuarios = Usuario.query.all()
    return jsonify([u.to_dict() for u in usuarios]), 200


@usuarios_bp.route('/responsables', methods=['POST'])
@jwt_required()
@require_permission('usuarios', 'puede_crear')
def create_responsable():
    """Crear usuario responsable"""
    data = request.get_json()
    
    if not data.get('nombre_usuario'):
        return jsonify({'error': 'Nombre es requerido'}), 400
    
    # Verificar nómina única
    if data.get('numero_nomina'):
        existe = Usuario.query.filter_by(numero_nomina=data['numero_nomina']).first()
        if existe:
            return jsonify({'error': 'Número de nómina ya existe'}), 400
    
    try:
        usuario = Usuario(
            numero_nomina=data.get('numero_nomina'),
            nombre_usuario=data['nombre_usuario'],
            puesto=data.get('puesto'),
            area_id=data.get('area_id')
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Usuario responsable creado',
            'usuario': usuario.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@usuarios_bp.route('/accesos', methods=['GET'])
@jwt_required()
@require_permission('usuarios', 'puede_leer')
def get_accesos():
    """Listar accesos al sistema"""
    accesos = Acceso.query.all()
    return jsonify([a.to_dict() for a in accesos]), 200


@usuarios_bp.route('/accesos', methods=['POST'])
@jwt_required()
@require_permission('usuarios', 'puede_crear')
def create_acceso():
    """Crear acceso al sistema"""
    data = request.get_json()
    
    required = ['nombre_usuario', 'correo_electronico', 'password', 'rol_id']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} es requerido'}), 400
    
    # Verificar correo único
    existe = Acceso.query.filter_by(correo_electronico=data['correo_electronico']).first()
    if existe:
        return jsonify({'error': 'El correo ya está registrado'}), 400
    
    try:
        # Hash de contraseña
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        acceso = Acceso(
            nombre_usuario=data['nombre_usuario'],
            correo_electronico=data['correo_electronico'],
            contrasena_hash=password_hash.decode('utf-8'),
            rol_id=data['rol_id'],
            area_id=data.get('area_id')
        )
        
        db.session.add(acceso)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Acceso creado exitosamente',
            'acceso': acceso.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500