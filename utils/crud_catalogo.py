# utils/crud_catalogo.py

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.extesions import db
from utils.concurrency import liberar_bloqueo, verificar_version
from utils.validators import ValidationError, handle_db_error
from sqlalchemy import String, cast

def crud_catalogo(modelo, validador, nombre: str, tabla: str,
                  campo_busqueda: str,
                  clave_respuesta: str,
                  campo_id: str,
                  campo_orden):
    """
    Genera las 5 funciones CRUD para un catálogo genérico.

    Args:
        modelo:     Clase SQLAlchemy (ej: CatArea)
        validador:  Función de validación (ej: validate_area)
        nombre:     Nombre legible para mensajes (ej: 'Área')
        tabla:      Nombre de la tabla en BD para bloqueos (ej: 'cat_areas')

    Uso:
        get_one, create, update, delete, get_completo = crud_catalogo(
            CatArea, validate_area, 'Área', 'cat_areas'
        )
    """


    # ── GET PAGINADO ──────────────────────────────────────────────────────

    def get_paginado():
        search   = request.args.get('search', '').strip()
        page     = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        query = modelo.query
        if search:
            query = query.filter(
                db.or_(
                    getattr(modelo, campo_busqueda).ilike(f'%{search}%'),
                    cast(getattr(modelo, campo_id), String).ilike(f'%{search}%'),
                    modelo.descripcion.ilike(f'%{search}%')
                )
            )
        paginated = query.order_by(campo_orden.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return jsonify({
            clave_respuesta: [i.to_dict() for i in paginated.items],
            'total':         paginated.total,
            'pages':         paginated.pages,
            'current_page':  paginated.page,
        }), 200


    # ── GET COMPLETO (sin paginar, solo activos) ──────────────────────────

    def get_completo():
        items = modelo.query.filter_by(activo=True).order_by(campo_busqueda).all()
        return jsonify([i.to_dict() for i in items]), 200


    # ── GET ONE ───────────────────────────────────────────────────────────

    def get_one(id):
        item = modelo.query.get(id)
        if not item:
            return jsonify({'error': f'{nombre} no encontrado/a'}), 404
        return jsonify(item.to_dict()), 200


    # ── CREATE ────────────────────────────────────────────────────────────

    def create():
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400

        try:
            validador(data, is_update=False)
        except ValidationError as e:
            return jsonify({'error': e.message, 'campos': e.fields}), 422

        # Verificar nombre único — todos los catálogos tienen nombre único
        campo_nombre = _campo_nombre(modelo)
        if modelo.query.filter_by(**{campo_nombre: data[campo_nombre]}).first():
            return jsonify({
                'error': f'{nombre} ya existe',
                'campos': {campo_nombre: f'Ya existe un/a {nombre.lower()} con este nombre'}
            }), 409

        try:
            item = modelo(
                **_build_fields(modelo, data),
                version=1,
                editado_por=user_id
            )
            db.session.add(item)
            db.session.commit()
            return jsonify({
                'mensaje': f'{nombre} creado/a',
                nombre.lower().replace(' ', '_'): item.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            message, code = handle_db_error(e)
            return jsonify({'error': message}), code


    # ── UPDATE ────────────────────────────────────────────────────────────

    def update(id):
        user_id = get_jwt_identity()
        item = modelo.query.get(id)
        if not item:
            return jsonify({'error': f'{nombre} no encontrado/a'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400

        try:
            validador(data, is_update=True)
        except ValidationError as e:
            return jsonify({'error': e.message, 'campos': e.fields}), 422

        version_cliente = data.get('version')
        if version_cliente is not None:
            es_valida, version_actual = verificar_version(modelo, id, version_cliente)
            if not es_valida:
                return jsonify({
                    'error': 'conflict',
                    'mensaje': 'El registro fue modificado por otro usuario',
                    'version_actual': version_actual,
                    'datos_actuales': item.to_dict(include_version=True)
                }), 409

        try:
            for campo, valor in _build_fields(modelo, data).items():
                setattr(item, campo, valor)

            db.session.commit()
            liberar_bloqueo(tabla, id, int(user_id))

            return jsonify({
                'mensaje': f'{nombre} actualizado/a',
                nombre.lower().replace(' ', '_'): item.to_dict()
            }), 200

        except Exception as e:
            db.session.rollback()
            message, code = handle_db_error(e)
            return jsonify({'error': message}), code


    # ── DELETE ────────────────────────────────────────────────────────────

    def delete(id, bloqueo):
        item = modelo.query.get(id)
        if not item:
            return jsonify({'error': f'{nombre} no encontrado/a'}), 404

        try:
            db.session.delete(item)
            db.session.delete(bloqueo)
            db.session.commit()
            return jsonify({'mensaje': f'{nombre} eliminado/a'}), 200

        except Exception as e:
            db.session.rollback()
            message, code = handle_db_error(e)
            return jsonify({'error': message}), code


    return get_completo,get_paginado,  get_one, create, update, delete


# ── Helpers internos ──────────────────────────────────────────────────────────

# Mapeo: modelo → campo que actúa como nombre único
_NOMBRE_CAMPO = {
    'CatArea':            'nombre_area',
    'CatEstado':          'nombre_estado',
    'CatTipoActivo':      'nombre_tipo',
    'CatTipoMobiliario':  'nombre_tipo',
}

# Campos editables por modelo (los que se asignan en create/update)
_CAMPOS_EDITABLES = {
    'CatArea': [
        'nombre_area', 'descripcion', 'activo'
    ],
    'CatEstado': [
        'nombre_estado', 'descripcion', 'activo', 'color_hex'
    ],
    'CatTipoActivo': [
        'nombre_tipo', 'descripcion', 'activo'
    ],
    'CatTipoMobiliario': [
        'nombre_tipo', 'descripcion', 'activo'
    ],
}


def _campo_nombre(modelo) -> str:
    return _NOMBRE_CAMPO[modelo.__name__]


def _build_fields(modelo, data: dict) -> dict:
    """
    Devuelve solo los campos editables del modelo que estén presentes en data.
    Aplica .strip() a strings automáticamente.
    """
    resultado = {}
    for campo in _CAMPOS_EDITABLES.get(modelo.__name__, []):
        if campo not in data:
            continue
        valor = data[campo]
        if isinstance(valor, str):
            valor = valor.strip() or None
        resultado[campo] = valor
    return resultado