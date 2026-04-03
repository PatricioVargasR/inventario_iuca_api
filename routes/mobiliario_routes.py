from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import BloqueoActivo, Mobiliario
from utils.concurrency import liberar_bloqueo, verificar_version
from utils.decorators import require_permission
from utils.validators import validate_mobiliario, ValidationError, handle_db_error

mobiliario_bp = Blueprint('mobiliario', __name__)

@mobiliario_bp.route('/', methods=['GET'])
@jwt_required()
@require_permission('mobiliario', 'puede_leer')
def get_mobiliario():
    """Listar todo el mobiliario con filtros"""
    tipo_id = request.args.get('tipo_mobiliario_id', type=int)
    estado_id = request.args.get('estado_id', type=int)
    usuario_id = request.args.get('usuario_id', type=int)
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Mobiliario.query

    if tipo_id:
        query = query.filter_by(tipo_mobiliario_id=tipo_id)
    if estado_id:
        query = query.filter_by(estado_id=estado_id)
    if usuario_id:
        query = query.filter_by(usuario_asignado_id=usuario_id)
    if search:
        query = query.filter(
            db.or_(
                Mobiliario.marca.ilike(f'%{search}%'),
                Mobiliario.modelo.ilike(f'%{search}%')
            )
        )

    query = query.order_by(Mobiliario.id_mueble.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'mobiliario': [m.to_dict() for m in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@mobiliario_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('mobiliario', 'puede_leer')
def get_mobiliario_by_id(id):
    """Obtener mobiliario por ID"""
    mueble = Mobiliario.query.get(id)

    if not mueble:
        return jsonify({'error': 'Mobiliario no encontrado'}), 404

    return jsonify(mueble.to_dict()), 200


@mobiliario_bp.route('/', methods=['POST'])
@jwt_required()
@require_permission('mobiliario', 'puede_crear')
def create_mobiliario():
    """Crear nuevo mobiliario"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación de esquema ────────────────────────────────────
    try:
        validate_mobiliario(data, is_update=False)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    try:
        mueble = Mobiliario(
            tipo_mobiliario_id=data['tipo_mobiliario_id'],
            marca=data.get('marca', '').strip() or None,
            modelo=data.get('modelo', '').strip() or None,
            color=data.get('color', '').strip() or None,
            caracteristicas=data.get('caracteristicas', '').strip() or None,
            observaciones=data.get('observaciones', '').strip() or None,
            estado_id=data['estado_id'],
            usuario_asignado_id=data.get('usuario_asignado_id') or None,
            sucursal_nombre=data.get('sucursal_nombre', 'Tulancingo').strip(),
            creado_por=user_id,
            modificado_por=user_id,
            version=1
        )

        db.session.add(mueble)
        db.session.commit()

        return jsonify({
            'mensaje': 'Mobiliario creado exitosamente',
            'mobiliario': mueble.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@mobiliario_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('mobiliario', 'puede_actualizar')
def update_mobiliario(id):
    """Actualizar mobiliario con control de versiones"""
    user_id = get_jwt_identity()
    mueble = Mobiliario.query.get(id)

    if not mueble:
        return jsonify({'error': 'Mueble no encontrado'}), 404

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación de esquema ────────────────────────────────────
    try:
        validate_mobiliario(data, is_update=True)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    # ── Control de versiones ─────────────────────────────────────
    version_cliente = data.get('version')
    if version_cliente is not None:
        es_valida, version_actual = verificar_version(Mobiliario, id, version_cliente)
        if not es_valida:
            return jsonify({
                'error': 'conflict',
                'mensaje': 'El registro fue modificado por otro usuario',
                'version_actual': version_actual,
                'datos_actuales': mueble.to_dict(include_version=True)
            }), 409

    try:
        campo_map = {
            'tipo_mobiliario_id':  lambda v: setattr(mueble, 'tipo_mobiliario_id', v),
            'marca':               lambda v: setattr(mueble, 'marca', v.strip() or None),
            'modelo':              lambda v: setattr(mueble, 'modelo', v.strip() or None),
            'color':               lambda v: setattr(mueble, 'color', v.strip() or None),
            'caracteristicas':     lambda v: setattr(mueble, 'caracteristicas', v.strip() or None),
            'observaciones':       lambda v: setattr(mueble, 'observaciones', v.strip() or None),
            'estado_id':           lambda v: setattr(mueble, 'estado_id', v),
            'usuario_asignado_id': lambda v: setattr(mueble, 'usuario_asignado_id', v or None),
            'sucursal_nombre':     lambda v: setattr(mueble, 'sucursal_nombre', v.strip()),
        }

        for campo, setter in campo_map.items():
            if campo in data:
                setter(data[campo])

        mueble.modificado_por = user_id

        db.session.commit()

        # Liberar bloqueo
        liberar_bloqueo('mobiliario', id, int(user_id))

        return jsonify({
            'mensaje': 'Mobiliario actualizado exitosamente',
            'mobiliario': mueble.to_dict(include_version=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@mobiliario_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('mobiliario', 'puede_eliminar')
def delete_mobiliario(id):
    """Eliminar mobiliario con verificación de bloqueo"""
    user_id = get_jwt_identity()

    mueble = Mobiliario.query.get(id)
    if not mueble:
        return jsonify({'error': 'Mueble no encontrado'}), 404

    # VERIFICAR BLOQUEO DE ELIMINACIÓN
    bloqueo = BloqueoActivo.query.filter_by(
        tabla='mobiliario',
        registro_id=id,
        usuario_id=user_id,
        tipo_bloqueo='eliminacion'
    ).first()

    if not bloqueo:
        bloqueo_existente = BloqueoActivo.query.filter_by(
            tabla='mobiliario',
            registro_id=id
        ).first()

        if bloqueo_existente:
            accion = 'editando' if bloqueo_existente.tipo_bloqueo == 'edicion' else 'eliminando'
            return jsonify({
                'error': 'locked_by_other',
                'mensaje': f'{bloqueo_existente.nombre_usuario} está {accion} este registro',
                'bloqueo': bloqueo_existente.to_dict()
            }), 409
        else:
            return jsonify({
                'error': 'no_lock',
                'mensaje': 'Debe adquirir bloqueo antes de eliminar'
            }), 403

    try:
        db.session.delete(mueble)
        db.session.delete(bloqueo)
        db.session.commit()

        return jsonify({'mensaje': 'Mobiliario eliminado exitosamente'}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code