from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import BloqueoActivo, Usuario, Acceso, Permiso
from utils.concurrency import liberar_bloqueo, verificar_version
from utils.decorators import require_permission
from utils.validators import validate_responsable, validate_acceso, ValidationError, handle_db_error
import bcrypt
from utils.lock_required import lock_required

usuarios_bp = Blueprint('usuarios', __name__)

MODULOS_DISPONIBLES = ['computo', 'mobiliario', 'responsable', 'catalogos', 'historial', 'acceso']

# ============================================
# RESPONSABLES (personas con bienes asignados)
# ============================================

@usuarios_bp.route('/responsables', methods=['GET'])
@jwt_required()
@require_permission('responsable', 'puede_leer')
def get_responsables():
    """Listar usuarios responsables"""
    usuarios = Usuario.query.all()
    return jsonify([u.to_dict() for u in usuarios]), 200


@usuarios_bp.route('/responsable/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('responsable', 'puede_leer')
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
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación de esquema ────────────────────────────────────
    try:
        validate_responsable(data, is_update=False)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    # Verificar nómina única
    if data.get('numero_nomina'):
        existe = Usuario.query.filter_by(numero_nomina=data['numero_nomina']).first()
        if existe:
            return jsonify({
                'error': 'El número de nómina ya está registrado',
                'campos': {'numero_nomina': 'Este número de nómina ya existe'}
            }), 409

    try:
        usuario = Usuario(
            numero_nomina=data.get('numero_nomina') or None,
            nombre_usuario=data['nombre_usuario'].strip(),
            puesto=data.get('puesto', '').strip() or None,
            area_id=data.get('area_id') or None,
            version=1,
            editado_por=user_id
        )

        db.session.add(usuario)
        db.session.commit()

        return jsonify({
            'mensaje': 'Responsable creado exitosamente',
            'usuario': usuario.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@usuarios_bp.route('/responsables/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('responsable', 'puede_actualizar')
def update_responsable(id):
    """Actualizar usuario responsable"""
    user_id = get_jwt_identity()
    usuario = Usuario.query.get(id)

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación de esquema ────────────────────────────────────
    try:
        validate_responsable(data, is_update=True)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    # ── Control de versiones ─────────────────────────────────────
    version_cliente = data.get('version')
    if version_cliente is not None:
        es_valida, version_actual = verificar_version(Usuario, id, version_cliente)
        if not es_valida:
            return jsonify({
                'error': 'conflict',
                'mensaje': 'El registro fue modificado por otro usuario',
                'version_actual': version_actual,
                'datos_actuales': usuario.to_dict(include_version=True)
            }), 409

    # Verificar nómina única si cambió
    if data.get('numero_nomina') and data['numero_nomina'] != usuario.numero_nomina:
        existe = Usuario.query.filter_by(numero_nomina=data['numero_nomina']).first()
        if existe:
            return jsonify({
                'error': 'El número de nómina ya está registrado',
                'campos': {'numero_nomina': 'Este número de nómina ya existe'}
            }), 409

    try:
        campo_map = {
            'nombre_usuario': lambda v: setattr(usuario, 'nombre_usuario', v.strip()),
            'numero_nomina':  lambda v: setattr(usuario, 'numero_nomina', v or None),
            'puesto':         lambda v: setattr(usuario, 'puesto', v.strip() or None),
            'area_id':        lambda v: setattr(usuario, 'area_id', v or None),
        }

        for campo, setter in campo_map.items():
            if campo in data:
                setter(data[campo])

        db.session.commit()

        # Liberar bloqueo
        liberar_bloqueo('usuario', id, int(user_id))

        return jsonify({
            'mensaje': 'Responsable actualizado exitosamente',
            'usuario': usuario.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@usuarios_bp.route('/responsables/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('responsable', 'puede_eliminar')
@lock_required('usuario')
def delete_responsable(id, bloqueo):
    """Eliminar el usuario responsable"""

    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    try:
        db.session.delete(usuario)
        db.session.delete(bloqueo)
        db.session.commit()

        return jsonify({'mensaje': 'Responsable eliminado exitosamente'}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e, tabla='usuario')
        return jsonify({'error': message}), code


# ============================================
# ACCESOS (cuentas del sistema con permisos)
# ============================================

@usuarios_bp.route('/accesos-filtro', methods=['GET'])
@jwt_required()
def get_accesos_filtro():
    """Lista los accesos para funcionar como filtros"""
    accesos = Acceso.query.order_by(Acceso.nombre_usuario)
    return jsonify([u.to_dict() for u in accesos]), 200

@usuarios_bp.route('/accesos', methods=['GET'])
@jwt_required()
@require_permission('acceso', 'puede_leer')
def get_accesos():
    """Listar cuentas de acceso con sus permisos"""
    accesos = Acceso.query.all()
    resultado = []

    for a in accesos:
        datos = a.to_dict()
        datos['permisos'] = a.permisos_dict()
        resultado.append(datos)

    return jsonify(resultado), 200

@usuarios_bp.route('/accesos/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('acceso', 'puede_leer')
def get_acceso(id):
    """Obtener un acceso mediante su ID"""
    acceso = Acceso.query.get(id)

    if not acceso:
        return jsonify({'error': 'Acceso no encontrado'}), 404

    datos = acceso.to_dict()
    datos['permisos'] = acceso.permisos_dict()

    return jsonify(datos), 200


@usuarios_bp.route('/accesos', methods=['POST'])
@jwt_required()
@require_permission('acceso', 'puede_crear')
def create_acceso():
    """Crear acceso al sistema"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación de esquema ────────────────────────────────────
    try:
        validate_acceso(data, is_update=False)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    # Verificar correo único
    existe = Acceso.query.filter_by(correo_electronico=data['correo_electronico']).first()
    if existe:
        return jsonify({
            'error': 'El correo ya está registrado',
            'campos': {'correo_electronico': 'Este correo ya existe'}
        }), 409

    try:
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

        acceso = Acceso(
            nombre_usuario=data['nombre_usuario'].strip(),
            correo_electronico=data['correo_electronico'].strip(),
            contrasena_hash=password_hash.decode('utf-8'),
            area_id=data.get('area_id'),
            version=1,
            editado_por=user_id
        )

        db.session.add(acceso)
        db.session.flush()

        permisos_data = data.get('permisos', {})

        for indice, modulo in enumerate(MODULOS_DISPONIBLES):
            p_modulo = permisos_data[indice]
            permiso = Permiso(
                acceso_id=acceso.id_acceso,
                modulo=modulo,
                puede_leer=p_modulo.get('puede_leer', False),
                puede_crear=p_modulo.get('puede_crear', False),
                puede_actualizar=p_modulo.get('puede_actualizar', False),
                puede_eliminar=p_modulo.get('puede_eliminar', False),
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
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code

@usuarios_bp.route('/accesos/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('acceso', 'puede_actualizar')
def update_acceso(id):
    """Actualizar cuenta de acceso y/o sus permisos"""
    user_id = get_jwt_identity()
    acceso = Acceso.query.get(id)

    if not acceso:
        return jsonify({'error': 'Acceso no encontrado'}), 404

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación de esquema ────────────────────────────────────
    try:
        validate_acceso(data, is_update=True)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    # ── Control de versiones ─────────────────────────────────────
    version_cliente = data.get('version')
    if version_cliente is not None:
        es_valida, version_actual = verificar_version(Acceso, id, version_cliente)
        if not es_valida:
            return jsonify({
                'error': 'conflict',
                'mensaje': 'El registro fue modificado por otro usuario',
                'version_actual': version_actual,
                'datos_actuales': acceso.to_dict(include_version=True)
            }), 409

    try:
        for campo in ['nombre_usuario', 'area_id']:
            if campo in data:
                setattr(acceso, campo, data[campo])

        if 'correo_electronico' in data and data['correo_electronico'] != acceso.correo_electronico:
            if Acceso.query.filter_by(correo_electronico=data['correo_electronico']).first():
                return jsonify({
                    'error': 'El correo ya está registrado',
                    'campos': {'correo_electronico': 'Este correo ya existe'}
                }), 409
            acceso.correo_electronico = data['correo_electronico']

        if 'password' in data and data['password']:
            acceso.contrasena_hash = bcrypt.hashpw(
                data['password'].encode('utf-8'), bcrypt.gensalt()
            ).decode('utf-8')

        if 'permisos' in data:
            permisos_data = data['permisos']
            for modulo in MODULOS_DISPONIBLES:
                p_modulo = permisos_data.get(modulo, {})
                permiso = Permiso.query.filter_by(acceso_id=id, modulo=modulo).first()

                if permiso:
                    permiso.puede_leer = p_modulo.get('puede_leer', permiso.puede_leer)
                    permiso.puede_crear = p_modulo.get('puede_crear', permiso.puede_crear)
                    permiso.puede_actualizar = p_modulo.get('puede_actualizar', permiso.puede_actualizar)
                    permiso.puede_eliminar = p_modulo.get('puede_eliminar', permiso.puede_eliminar)
                elif p_modulo:
                    nuevo = Permiso(
                        acceso_id=id,
                        modulo=modulo,
                        puede_leer=p_modulo.get('puede_leer', False),
                        puede_crear=p_modulo.get('puede_crear', False),
                        puede_actualizar=p_modulo.get('puede_actualizar', False),
                        puede_eliminar=p_modulo.get('puede_eliminar', False)
                    )
                    db.session.add(nuevo)

        db.session.commit()

        resultado = acceso.to_dict()
        resultado['permisos'] = acceso.permisos_dict()

        # Liberar bloqueo
        liberar_bloqueo('acceso', id, int(user_id))

        return jsonify({
            'mensaje': 'Acceso actualizado exitosamente',
            'acceso': resultado
        }), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@usuarios_bp.route('/accesos/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('acceso', 'puede_eliminar')
@lock_required('acceso')
def delete_acceso(id, bloqueo):
    """Eliminar cuenta de acceso (elimina permisos en cascada)"""
    user_id = get_jwt_identity()

    if int(user_id) == id:
        return jsonify({'error': 'No puedes eliminar tu propio acceso'}), 400

    acceso = Acceso.query.get(id)
    if not acceso:
        return jsonify({'error': 'Acceso no encontrado'}), 404

    try:
        db.session.delete(acceso)
        db.session.delete(bloqueo)
        db.session.commit()

        return jsonify({'mensaje': 'Acceso eliminado exitosamente'}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e, tabla='acceso')
        return jsonify({'error': message}), code