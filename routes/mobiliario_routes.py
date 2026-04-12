from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import BloqueoActivo, Mobiliario, MobiliarioResponsable, Usuario
from utils.concurrency import liberar_bloqueo, verificar_version
from utils.decorators import require_permission
from utils.validators import validate_mobiliario, ValidationError, handle_db_error
from utils.lock_required import lock_required

mobiliario_bp = Blueprint('mobiliario', __name__)

@mobiliario_bp.route('/', methods=['GET'])
@jwt_required()
@require_permission('mobiliario', 'puede_leer')
def get_mobiliario():
    """Listar todo el mobiliario con filtros"""
    tipo_id = request.args.get('tipo_mobiliario_id', type=int)
    estado_id = request.args.get('estado_id', type=int)
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Mobiliario.query

    if tipo_id:
        query = query.filter_by(tipo_mobiliario_id=tipo_id)
    if estado_id:
        query = query.filter_by(estado_id=estado_id)
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
        'mobiliario': [m.to_dict(include_responsables=True) for m in pagination.items],
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

    return jsonify(mueble.to_dict(include_responsables=True)), 200


@mobiliario_bp.route('/', methods=['POST'])
@jwt_required()
@require_permission('mobiliario', 'puede_crear')
def create_mobiliario():
    """Crear nuevo mobiliario con múltiples responsables"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

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
            sucursal_nombre=data.get('sucursal_nombre', 'Tulancingo').strip(),
            version=1
        )

        db.session.add(mueble)
        db.session.flush()

        # Agregar responsables (lista de IDs)
        responsables_ids = data.get('responsables_ids', [])
        for usuario_id in responsables_ids:
            usuario = Usuario.query.get(usuario_id)
            if usuario:
                responsable = MobiliarioResponsable(
                    mueble_id=mueble.id_mueble,
                    usuario_id=usuario_id
                )
                db.session.add(responsable)

        db.session.commit()

        return jsonify({
            'mensaje': 'Mobiliario creado exitosamente',
            'mobiliario': mueble.to_dict(include_responsables=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@mobiliario_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('mobiliario', 'puede_actualizar')
def update_mobiliario(id):
    """Actualizar mobiliario con control de versiones y diff de responsables"""
    user_id = get_jwt_identity()
    mueble = Mobiliario.query.get(id)

    if not mueble:
        return jsonify({'error': 'Mueble no encontrado'}), 404

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    try:
        validate_mobiliario(data, is_update=True)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    version_cliente = data.get('version')
    if version_cliente is not None:
        es_valida, version_actual = verificar_version(Mobiliario, id, version_cliente)
        if not es_valida:
            return jsonify({
                'error': 'conflict',
                'mensaje': 'El registro fue modificado por otro usuario',
                'version_actual': version_actual,
                'datos_actuales': mueble.to_dict(include_version=True, include_responsables=True)
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
            'sucursal_nombre':     lambda v: setattr(mueble, 'sucursal_nombre', v.strip()),
        }

        for campo, setter in campo_map.items():
            if campo in data:
                setter(data[campo])

        # Diff de responsables: solo insertar/eliminar los que cambiaron
        if 'responsables_ids' in data:
            nuevos_ids = set(int(i) for i in data['responsables_ids'])
            responsables_actuales = MobiliarioResponsable.query.filter_by(mueble_id=id).all()
            actuales_ids = set(r.usuario_id for r in responsables_actuales)

            # Eliminar los que ya no están
            ids_a_eliminar = actuales_ids - nuevos_ids
            for resp in responsables_actuales:
                if resp.usuario_id in ids_a_eliminar:
                    db.session.delete(resp)

            # Agregar solo los nuevos
            ids_a_agregar = nuevos_ids - actuales_ids
            for usuario_id in ids_a_agregar:
                usuario = Usuario.query.get(usuario_id)
                if usuario:
                    nuevo_resp = MobiliarioResponsable(
                        mueble_id=id,
                        usuario_id=usuario_id
                    )
                    db.session.add(nuevo_resp)

        db.session.commit()

        liberar_bloqueo('mobiliario', id, int(user_id))

        return jsonify({
            'mensaje': 'Mobiliario actualizado exitosamente',
            'mobiliario': mueble.to_dict(include_version=True, include_responsables=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@mobiliario_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('mobiliario', 'puede_eliminar')
@lock_required('mobiliario')
def delete_mobiliario(id, bloqueo):
    """Eliminar mobiliario con verificación de bloqueo"""

    mueble = Mobiliario.query.get(id)
    if not mueble:
        return jsonify({'error': 'Mueble no encontrado'}), 404

    try:
        db.session.delete(mueble)
        db.session.delete(bloqueo)
        db.session.commit()

        return jsonify({'mensaje': 'Mobiliario eliminado exitosamente'}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e, tabla='mobiliario')
        return jsonify({'error': message}), code