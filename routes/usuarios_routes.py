from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models import Usuario, Acceso, Permiso
from utils.decorators import require_permission
import bcrypt

usuarios_bp = Blueprint('usuarios', __name__)

MODULOS_DISPONIBLES = ['computo', 'mobiliario', 'responsable', 'catalogos', 'historial', 'acceso']

# ============================================
# RESPONSABLES (personas con bienes asignados)
# ============================================

@usuarios_bp.route('/responsables', methods=['GET'])
@jwt_required()
def get_responsables():
    """Listar usuarios responsables"""
    usuarios = Usuario.query.all()
    return jsonify([u.to_dict() for u in usuarios]), 200


@usuarios_bp.route('/responsable/<int:id>', methods=['GET'])
@jwt_required
def get_responsable(id):
    """Obtener usuario responsable por ID"""
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    return jsonify(usuario.to_dict()), 200

@usuarios_bp.route('/responsables', methods=['POST'])
@jwt_required()
@require_permission('responsable', 'puede_crear')
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

@usuarios_bp.route('/responsables/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('responsable', 'puede_actualizar')
def update_responsable(id):
    """Actualizar uaurio responsable"""
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    data = request.get_json()

    if data.get('numero_nomina') and data['numero_nomina'] != usuario.numero_nomina:
        if Usuario.query.filter_by(numero_nomina=data['numero_nomina']).first():
            return jsonify({
                'error': 'Número de nómina ya existe'
            }), 400

    try:
        for campo in ['numero_nomina','nombre_usuario', 'puesto', 'area_id']:
            if campo in data:
                setattr(usuario, campo, data[campo])
            db.session.commit()

            return jsonify({
                'mensaje': 'usuario actualizado',
                'usuario': usuario.to_dict()
            }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500


@usuarios_bp.route('/responsables/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('responsable', 'puede_eliminar')
def delete_responsable(id):
    """ELiminar el usuario responsable"""
    usuario = Usuario.query.get(id)

    if not usuario:
        return jsonify({
            'error': 'Usuario no encontrado'
        }), 404

    try:
        db.session.delete(usuario)
        db.session.commit()

        return jsonify({
            'mensaje': 'Usuario eliminado'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

# ============================================
# ACCESOS (cuentas del sistema con permisos)
# ============================================

@usuarios_bp.route('/accesos', methods=['GET'])
@jwt_required()
@require_permission('acceso', 'puede_leer')
def get_accesos():
    """Listar cuentas de acceso con sus permisos """
    accesos = Acceso.query.all()
    resultado = []

    for a in accesos:
        datos = a.to_dict()
        datos['permisos'] = a.permisos_dict()
        resultado.append(datos)

    return jsonify(resultado), 200


@usuarios_bp.route('/accesos', methods=['POST'])
@jwt_required()
@require_permission('acceso', 'puede_crear')
def create_acceso():
    """Crear acceso al sistema"""
    data = request.get_json()

    required = ['nombre_usuario', 'correo_electronico', 'password']
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
            area_id=data.get('area_id')
        )

        db.session.add(acceso)
        db.session.flush()

        # Crear permisos directamente por módulo
        permisos_data = data.get('permisos', {})

        for modulo in MODULOS_DISPONIBLES:
            p_modulo = permisos_data.get(modulo, {})
            permiso = Permiso(
                acceso_id = acceso.id_acceso,
                modulo = modulo,
                puede_leer = p_modulo.get('puede_leer', False),
                puede_crear = p_modulo.get('puede_crear', False),
                puede_actualizar = p_modulo.get('puede_actualizar', False),
                puede_eliminar = p_modulo.get('puede_eliminar', False),
            )
            db.session.add(permiso)

        db.session.commit()

        resultado = acceso.to_dict()
        resultado['permisos'] = acceso.permisos_dict()

        return jsonify({
            'mensaje': 'Acceso creado exitosamente',
            'acceso': resultado
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

@usuarios_bp.route('/accesos/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('acceso', 'puede_actualizar')
def update_acceso(id):
    """Actualizar cuenta de acceso y/o sus permisos"""
    acceso = Acceso.query.get(id)

    if not acceso:
        return jsonify({
            'error': 'Acceso no encontrado'
        }), 404

    data = request.get_json()

    try:
        # Actualiar datos básicos
        for campo in ['nombre_usuario', 'area_id']:
            if campo in data:
                setattr(acceso, campo, data[campo])

        if 'correo_electronico' in data and data['correo_electronico'] != acceso.correo_electronico:
            if Acceso.query.filter_by(correo_electronico=data['correo_electronico']).first():
                return jsonify({
                    'error': 'El correo ya está registrado'
                }), 400

            acceso.correo_electronico = data['correo_electronico']

            if 'password' in data and data['password']:
                acceso.contrasena_hash = bcrypt.hashpw(
                    data['password'].encode('utf-8'), bcrypt.gensalt()
                ).decode('utf-8')

        # Actualizar permisos si se enviaron
        if 'permisos' in data:
            permisos_data = data['permisos']
            for modulo in MODULOS_DISPONIBLES:
                p_modulo = permisos_data.get(modulo, {})
                permiso: Permiso = Permiso.query.filter_by(acceso_id=id, modulo=modulo).first()

                if permiso:
                    # Actualizar existente
                    permiso.puede_leer = p_modulo.get('puede_leer', permiso.puede_leer)
                    permiso.puede_crear = p_modulo.get('puede_crear', permiso.puede_crear)
                    permiso.puede_actualizar = p_modulo.get('puede_actualizar', permiso.puede_actualizar)
                    permiso.puede_eliminar = p_modulo.get('puede_elmininar', permiso.puede_leer)
                elif p_modulo:
                    # Crear si no existía y se enviaron datos
                    nuevo = Permiso(
                        acceso_id = id,
                        modulo=modulo,
                        puede_leer = p_modulo.get('puede_leer', False),
                        puede_crear = p_modulo.get('puede_crear', False),
                        puede_actualizar = p_modulo.get('puede_actualizar', False),
                        puede_eliminar = p_modulo.get('puede_eliminar', False),
                        puede_exportar = p_modulo.get('puede_exportar', False)
                    )
                    db.session.add(nuevo)

        db.session.commit()
        resultado = acceso.to_dict()
        resultado['permisos'] = acceso.permisos_dict()

        return jsonify({
            'mensaje': 'Acceso actualizado',
            'acceso': resultado
        }),200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

@usuarios_bp.route('/accesos/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('acceso', 'puede_eliminar')
def delete_acceso(id):
    """Eliminar cuenta de acceso (elimina permisos en cascada)"""
    acceso = Acceso.query.get(id)

    if not acceso:
        return jsonify({
            'error': 'Acceso no encontrado'
        }), 404

    try:
        db.session.delete(acceso)
        db.session.commit()
        return jsonify({
            'mensaje': 'Acceso eliminado'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500
