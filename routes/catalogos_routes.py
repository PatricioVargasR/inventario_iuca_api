from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app import db
from models import BloqueoActivo, CatArea, CatTipoActivo, CatEstado, CatTipoMobiliario
from utils.concurrency import liberar_bloqueo, verificar_version
from utils.decorators import require_permission
from utils.validators import (
    validate_area,
    validate_estado,
    validate_tipo_activo,
    validate_tipo_mobiliario,
    ValidationError,
    handle_db_error,
)

catalogos_bp = Blueprint('catalogos', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# ÁREAS
# ─────────────────────────────────────────────────────────────────────────────

@catalogos_bp.route('/areas-completo', methods=['GET'])
@jwt_required()
def get_areas_completo():
    """Obtener areas sin paginar"""
    areas = CatArea.query.filter_by(activo=True)
    if not areas:
        return jsonify({'error': 'No se encontraron áreas'}), 404
    return jsonify([a.to_dict() for a in areas]), 200


@catalogos_bp.route('/areas', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_areas():
    search   = request.args.get('search', '').strip()
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = CatArea.query
    if search:
        query = query.filter(
            db.or_(
                CatArea.nombre_area.ilike(f'%{search}%'),
                CatArea.descripcion.ilike(f'%{search}%')
            )
        )
    query = query.order_by(CatArea.id_area.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'areas':        [a.to_dict() for a in paginated.items],
        'total':        paginated.total,
        'pages':        paginated.pages,
        'current_page': paginated.page,
    }), 200


@catalogos_bp.route('/areas/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_area(id):
    area = CatArea.query.get(id)
    if not area:
        return jsonify({'error': 'Área no encontrada'}), 404
    return jsonify(area.to_dict()), 200


@catalogos_bp.route('/areas', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_area():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación ──────────────────────────────────────────────
    try:
        validate_area(data, is_update=False)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    if CatArea.query.filter_by(nombre_area=data['nombre_area']).first():
        return jsonify({
            'error': 'El área ya existe',
            'campos': {'nombre': 'Ya existe un área con este nombre'}
        }), 409

    try:
        area = CatArea(
            nombre_area=data['nombre_area'].strip(),
            descripcion=data.get('descripcion'),
            activo=data.get('activo', True),
            version=1,
            editado_por=user_id
        )
        db.session.add(area)
        db.session.commit()
        return jsonify({'mensaje': 'Área creada', 'area': area.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@catalogos_bp.route('/areas/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puede_actualizar')
def update_area(id):
    user_id = get_jwt_identity()
    area = CatArea.query.get(id)
    if not area:
        return jsonify({'error': 'Área no encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación ──────────────────────────────────────────────
    try:
        validate_area(data, is_update=True)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    # ── Control de versiones ─────────────────────────────────────
    version_cliente = data.get('version')
    if version_cliente is not None:
        es_valida, version_actual = verificar_version(CatArea, id, version_cliente)
        if not es_valida:
            return jsonify({
                'error': 'conflict',
                'mensaje': 'El registro fue modificado por otro usuario',
                'version_actual': version_actual,
                'datos_actuales': area.to_dict(include_version=True)
            }), 409

    try:
        if 'nombre_area' in data:
            area.nombre_area = data['nombre_area'].strip()
        if 'descripcion' in data:
            area.descripcion = data['descripcion']
        if 'activo' in data:
            area.activo = data['activo']

        db.session.commit()
        liberar_bloqueo('cat_areas', id, int(user_id))

        return jsonify({'mensaje': 'Área actualizada', 'area': area.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@catalogos_bp.route('/areas/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
def delete_area(id):
    user_id = get_jwt_identity()
    area = CatArea.query.get(id)
    if not area:
        return jsonify({'error': 'Área no encontrada'}), 404

    bloqueo = BloqueoActivo.query.filter_by(
        tabla='cat_areas', registro_id=id,
        usuario_id=user_id, tipo_bloqueo='eliminacion'
    ).first()

    if not bloqueo:
        bloqueo_existente = BloqueoActivo.query.filter_by(tabla='cat_areas', registro_id=id).first()
        if bloqueo_existente:
            accion = 'editando' if bloqueo_existente.tipo_bloqueo == 'edicion' else 'eliminando'
            return jsonify({
                'error': 'locked_by_other',
                'mensaje': f'{bloqueo_existente.nombre_usuario} está {accion} este registro',
                'bloqueo': bloqueo_existente.to_dict()
            }), 409
        return jsonify({'error': 'no_lock', 'mensaje': 'Debe adquirir bloqueo antes de eliminar'}), 403

    try:
        db.session.delete(area)
        db.session.commit()
        return jsonify({'mensaje': 'Área eliminada'}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE ACTIVO
# ─────────────────────────────────────────────────────────────────────────────

@catalogos_bp.route('/tipos-activo-completo', methods=['GET'])
@jwt_required()
def get_tipos_activos_completo():
    activos = CatTipoActivo.query.filter_by(activo=True)
    if not activos:
        return jsonify({'error': 'No se encontraron tipos de activos'}), 404
    return jsonify([a.to_dict() for a in activos]), 200


@catalogos_bp.route('/tipos-activo', methods=['GET'])
@jwt_required()
def get_tipos_activo():
    search   = request.args.get('search', '').strip()
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = CatTipoActivo.query
    if search:
        query = query.filter(
            db.or_(
                CatTipoActivo.nombre_tipo.ilike(f'%{search}%'),
                CatTipoActivo.descripcion.ilike(f'%{search}%')
            )
        )
    query = query.order_by(CatTipoActivo.id_tipo_activo.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'tipos_activo': [t.to_dict() for t in paginated.items],
        'total':        paginated.total,
        'pages':        paginated.pages,
        'current_page': paginated.page,
    }), 200


@catalogos_bp.route('/activo/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_activo(id):
    activo = CatTipoActivo.query.get(id)
    if not activo:
        return jsonify({'error': 'Tipo de activo no encontrado'}), 404
    return jsonify(activo.to_dict()), 200


@catalogos_bp.route('/tipos-activo', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_tipo_activo():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación ──────────────────────────────────────────────
    try:
        validate_tipo_activo(data, is_update=False)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    if CatTipoActivo.query.filter_by(nombre_tipo=data['nombre_tipo']).first():
        return jsonify({
            'error': 'El tipo ya existe',
            'campos': {'nombre': 'Ya existe un tipo de activo con este nombre'}
        }), 409

    try:
        tipo = CatTipoActivo(
            nombre_tipo=data['nombre_tipo'].strip(),
            descripcion=data.get('descripcion'),
            activo=data.get('activo', True),
            version=1,
            editado_por=user_id
        )
        db.session.add(tipo)
        db.session.commit()
        return jsonify({'mensaje': 'Tipo de activo creado', 'tipo': tipo.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@catalogos_bp.route('/tipos-activo/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puede_actualizar')
def update_tipo_activo(id):
    user_id = get_jwt_identity()
    tipo = CatTipoActivo.query.get(id)
    if not tipo:
        return jsonify({'error': 'Tipo no encontrado'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación ──────────────────────────────────────────────
    try:
        validate_tipo_activo(data, is_update=True)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    # ── Control de versiones ─────────────────────────────────────
    version_cliente = data.get('version')
    if version_cliente is not None:
        es_valida, version_actual = verificar_version(CatTipoActivo, id, version_cliente)
        if not es_valida:
            return jsonify({
                'error': 'conflict',
                'mensaje': 'El registro fue modificado por otro usuario',
                'version_actual': version_actual,
                'datos_actuales': tipo.to_dict(include_version=True)
            }), 409

    try:
        if 'nombre_tipo' in data: tipo.nombre_tipo = data['nombre_tipo'].strip()
        if 'descripcion' in data: tipo.descripcion = data['descripcion']
        if 'activo'      in data: tipo.activo      = data['activo']

        db.session.commit()
        liberar_bloqueo('cat_tipos_activo', id, int(user_id))

        return jsonify({'mensaje': 'Tipo actualizado', 'tipo': tipo.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@catalogos_bp.route('/tipos-activo/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
def delete_tipo_activo(id):
    user_id = get_jwt_identity()
    tipo = CatTipoActivo.query.get(id)
    if not tipo:
        return jsonify({'error': 'Tipo no encontrado'}), 404

    bloqueo = BloqueoActivo.query.filter_by(
        tabla='cat_tipos_activo', registro_id=id,
        usuario_id=user_id, tipo_bloqueo='eliminacion'
    ).first()

    if not bloqueo:
        bloqueo_existente = BloqueoActivo.query.filter_by(tabla='cat_tipos_activo', registro_id=id).first()
        if bloqueo_existente:
            accion = 'editando' if bloqueo_existente.tipo_bloqueo == 'edicion' else 'eliminando'
            return jsonify({
                'error': 'locked_by_other',
                'mensaje': f'{bloqueo_existente.nombre_usuario} está {accion} este registro',
                'bloqueo': bloqueo_existente.to_dict()
            }), 409
        return jsonify({'error': 'no_lock', 'mensaje': 'Debe adquirir bloqueo antes de eliminar'}), 403

    try:
        db.session.delete(tipo)
        db.session.commit()
        return jsonify({'mensaje': 'Tipo eliminado'}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


# ─────────────────────────────────────────────────────────────────────────────
# ESTADOS
# ─────────────────────────────────────────────────────────────────────────────

@catalogos_bp.route('/estados-completo', methods=['GET'])
@jwt_required()
def get_estados_completo():
    estados = CatEstado.query.filter_by(activo=True)
    if not estados:
        return jsonify({'error': 'No se encontraron estados'}), 404
    return jsonify([e.to_dict() for e in estados]), 200


@catalogos_bp.route('/estados', methods=['GET'])
@jwt_required()
def get_estados():
    search   = request.args.get('search', '').strip()
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = CatEstado.query
    if search:
        query = query.filter(
            db.or_(
                CatEstado.nombre_estado.ilike(f'%{search}%'),
                CatEstado.descripcion.ilike(f'%{search}%')
            )
        )
    query = query.order_by(CatEstado.id_estado.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'estados':      [e.to_dict() for e in paginated.items],
        'total':        paginated.total,
        'pages':        paginated.pages,
        'current_page': paginated.page,
    }), 200


@catalogos_bp.route('/estados/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_estado(id):
    estado = CatEstado.query.get(id)
    if not estado:
        return jsonify({'error': 'Estado no encontrado'}), 404
    return jsonify(estado.to_dict()), 200


@catalogos_bp.route('/estados', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_estado():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación ──────────────────────────────────────────────
    try:
        validate_estado(data, is_update=False)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    if CatEstado.query.filter_by(nombre_estado=data['nombre_estado']).first():
        return jsonify({
            'error': 'El estado ya existe',
            'campos': {'nombre': 'Ya existe un estado con este nombre'}
        }), 409

    try:
        estado = CatEstado(
            nombre_estado=data['nombre_estado'].strip(),
            descripcion=data.get('descripcion'),
            activo=data.get('activo', True),
            color_hex=data.get('color_hex'),
            version=1,
            editado_por=user_id
        )
        db.session.add(estado)
        db.session.commit()
        return jsonify({'mensaje': 'Estado creado', 'estado': estado.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@catalogos_bp.route('/estados/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puede_actualizar')
def update_estado(id):
    user_id = get_jwt_identity()
    estado = CatEstado.query.get(id)
    if not estado:
        return jsonify({'error': 'Estado no encontrado'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación ──────────────────────────────────────────────
    try:
        validate_estado(data, is_update=True)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    # ── Control de versiones ─────────────────────────────────────
    version_cliente = data.get('version')
    if version_cliente is not None:
        es_valida, version_actual = verificar_version(CatEstado, id, version_cliente)
        if not es_valida:
            return jsonify({
                'error': 'conflict',
                'mensaje': 'El registro fue modificado por otro usuario',
                'version_actual': version_actual,
                'datos_actuales': estado.to_dict(include_version=True)
            }), 409

    try:
        if 'nombre_estado' in data: estado.nombre_estado = data['nombre_estado'].strip()
        if 'descripcion'   in data: estado.descripcion   = data['descripcion']
        if 'color_hex'     in data: estado.color_hex     = data['color_hex']
        if 'activo'        in data: estado.activo        = data['activo']

        db.session.commit()
        liberar_bloqueo('cat_estados', id, int(user_id))

        return jsonify({'mensaje': 'Estado actualizado', 'estado': estado.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@catalogos_bp.route('/estados/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
def delete_estado(id):
    user_id = get_jwt_identity()
    estado = CatEstado.query.get(id)
    if not estado:
        return jsonify({'error': 'Estado no encontrado'}), 404

    bloqueo = BloqueoActivo.query.filter_by(
        tabla='cat_estados', registro_id=id,
        usuario_id=user_id, tipo_bloqueo='eliminacion'
    ).first()

    if not bloqueo:
        bloqueo_existente = BloqueoActivo.query.filter_by(tabla='cat_estados', registro_id=id).first()
        if bloqueo_existente:
            accion = 'editando' if bloqueo_existente.tipo_bloqueo == 'edicion' else 'eliminando'
            return jsonify({
                'error': 'locked_by_other',
                'mensaje': f'{bloqueo_existente.nombre_usuario} está {accion} este registro',
                'bloqueo': bloqueo_existente.to_dict()
            }), 409
        return jsonify({'error': 'no_lock', 'mensaje': 'Debe adquirir bloqueo antes de eliminar'}), 403

    try:
        db.session.delete(estado)
        db.session.commit()
        return jsonify({'mensaje': 'Estado eliminado'}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE MOBILIARIO
# ─────────────────────────────────────────────────────────────────────────────

@catalogos_bp.route('/tipo-completo', methods=['GET'])
@jwt_required()
def get_mobiliario_completo():
    mobiliarios = CatTipoMobiliario.query.filter_by(activo=True)
    if not mobiliarios:
        return jsonify({'error': 'No se encontraron tipos de mobiliarios'}), 404
    return jsonify([m.to_dict() for m in mobiliarios]), 200


@catalogos_bp.route('/tipos-mobiliario', methods=['GET'])
@jwt_required()
def get_tipos_mobiliario():
    search   = request.args.get('search', '').strip()
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = CatTipoMobiliario.query
    if search:
        query = query.filter(
            db.or_(
                CatTipoMobiliario.nombre_tipo.ilike(f'%{search}%'),
                CatTipoMobiliario.descripcion.ilike(f'%{search}%')
            )
        )
    query = query.order_by(CatTipoMobiliario.id_tipo_mobiliario.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'tipos_mobiliario': [t.to_dict() for t in paginated.items],
        'total':            paginated.total,
        'pages':            paginated.pages,
        'current_page':     paginated.page,
    }), 200


@catalogos_bp.route('/mobiliario/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_catalogo(id):
    catalogo = CatTipoMobiliario.query.get(id)
    if not catalogo:
        return jsonify({'error': 'Catálogo no encontrado'}), 404
    return jsonify(catalogo.to_dict()), 200


@catalogos_bp.route('/tipos-mobiliario', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_tipo_mobiliario():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación ──────────────────────────────────────────────
    try:
        validate_tipo_mobiliario(data, is_update=False)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    if CatTipoMobiliario.query.filter_by(nombre_tipo=data['nombre_tipo']).first():
        return jsonify({
            'error': 'El tipo ya existe',
            'campos': {'nombre': 'Ya existe un tipo de mobiliario con este nombre'}
        }), 409

    try:
        tipo = CatTipoMobiliario(
            nombre_tipo=data['nombre_tipo'].strip(),
            descripcion=data.get('descripcion'),
            activo=data.get('activo', True),
            version=1,
            editado_por=user_id
        )
        db.session.add(tipo)
        db.session.commit()
        return jsonify({'mensaje': 'Tipo de mobiliario creado', 'tipo': tipo.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@catalogos_bp.route('/tipos-mobiliario/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puede_actualizar')
def update_tipo_mobiliario(id):
    user_id = get_jwt_identity()
    tipo = CatTipoMobiliario.query.get(id)
    if not tipo:
        return jsonify({'error': 'Tipo no encontrado'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación ──────────────────────────────────────────────
    try:
        validate_tipo_mobiliario(data, is_update=True)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    # ── Control de versiones ─────────────────────────────────────
    version_cliente = data.get('version')
    if version_cliente is not None:
        es_valida, version_actual = verificar_version(CatTipoMobiliario, id, version_cliente)
        if not es_valida:
            return jsonify({
                'error': 'conflict',
                'mensaje': 'El registro fue modificado por otro usuario',
                'version_actual': version_actual,
                'datos_actuales': tipo.to_dict(include_version=True)
            }), 409

    try:
        if 'nombre_tipo' in data: tipo.nombre_tipo = data['nombre_tipo'].strip()
        if 'descripcion' in data: tipo.descripcion = data['descripcion']
        if 'activo'      in data: tipo.activo      = data['activo']

        db.session.commit()
        liberar_bloqueo('cat_tipos_mobiliario', id, int(user_id))

        return jsonify({'mensaje': 'Tipo actualizado', 'tipo': tipo.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@catalogos_bp.route('/tipos-mobiliario/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
def delete_tipo_mobiliario(id):
    user_id = get_jwt_identity()
    tipo = CatTipoMobiliario.query.get(id)
    if not tipo:
        return jsonify({'error': 'Tipo no encontrado'}), 404

    bloqueo = BloqueoActivo.query.filter_by(
        tabla='cat_tipos_mobiliario', registro_id=id,
        usuario_id=user_id, tipo_bloqueo='eliminacion'
    ).first()

    if not bloqueo:
        bloqueo_existente = BloqueoActivo.query.filter_by(tabla='cat_tipos_mobiliario', registro_id=id).first()
        if bloqueo_existente:
            accion = 'editando' if bloqueo_existente.tipo_bloqueo == 'edicion' else 'eliminando'
            return jsonify({
                'error': 'locked_by_other',
                'mensaje': f'{bloqueo_existente.nombre_usuario} está {accion} este registro',
                'bloqueo': bloqueo_existente.to_dict()
            }), 409
        return jsonify({'error': 'no_lock', 'mensaje': 'Debe adquirir bloqueo antes de eliminar'}), 403

    try:
        db.session.delete(tipo)
        db.session.commit()
        return jsonify({'mensaje': 'Tipo eliminado'}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code