from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models import CatArea, CatTipoActivo, CatEstado, CatTipoMobiliario
from utils.decorators import require_permission

catalogos_bp = Blueprint('catalogos', __name__)

# ---- Áreas ----
@catalogos_bp.route('/areas_sin_paginacion', methods=['GET'])
@jwt_required()
def get_areas_sin_paginar():
    """Obtener areas sin paginar"""
    areas = CatArea.query.all()

    if not areas:
        return jsonify({'error': 'No se econtraron áreas'}), 404

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
    query = query.order_by(CatArea.nombre_area.asc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'areas':   [a.to_dict() for a in paginated.items],
        'total':   paginated.total,
        'pages':   paginated.pages,
        'current_page': paginated.page,
    }), 200


@catalogos_bp.route('/areas/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_area(id):
    """Obtener un área con base a su ID"""
    area = CatArea.query.get(id)

    if not area:
        return jsonify({
            'error': 'Área no encontrada'
        }), 500

    return jsonify(area.to_dict()), 200

@catalogos_bp.route('/areas', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_area():
    """Crear una nueva área"""
    data = request.get_json()

    if not data.get('nombre'):
        return jsonify({
            'error': 'El nombre del área es requerido'
        }), 400

    if CatArea.query.filter_by(nombre_area=data['nombre_area']).first():
        return jsonify({
            'error': 'El área ya existe'
        }), 400

    try:
        area = CatArea(
            nombre_area=data['hombre_area'],
            descripcion=data.get('descripcion'),
            activo=data.get('activo')
        )
        db.session.add(area)
        db.session.commit()

        return jsonify({
            'mensaje': 'Área creada',
            'area': area.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

@catalogos_bp.route('/areas/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puede_actualizar')
def update_area(id):
    """Actualizar un área en particular"""
    area = CatArea.query.get(id)

    if not area:
        return jsonify({
            'error': 'Área no encontrada'
        }), 404

    data = request.get_json()

    try:
        if 'nombre_area' in data:
            area.nombre_area = data['nombre_area']

        if 'descripcion' in data:
            area.descripcion = data['descripcion']

        if 'activo' in data:
            area.activo = data['activo']

        db.session.commit()
        return jsonify({
            'mensaje': 'Área actualizada',
            'area': area.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

@catalogos_bp.route('/areas/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
def delete_area(id):
    """Eliminar un área en especifico"""
    area = CatArea.query.get(id)

    if not area:
        return jsonify({
            'error': 'Área no encontrada'
        }), 404

    try:
        db.session.delete(area)
        db.session.commit()

        return jsonify({
            'mensaje': 'Área eliminada'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

# ---- Tipos de Activo ----

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
    query = query.order_by(CatTipoActivo.nombre_tipo.asc())
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
    """Obtener un activo mediante su ID"""
    activo = CatTipoActivo.query.get(id)

    if not activo:
        return jsonify({
            'error': 'Tipo de activo no encontrado'
        }), 404

    return jsonify(activo.to_dict()), 200

@catalogos_bp.route('/tipos-activo', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_tipo_activo():
    """Crear un tipo de activo"""
    data = request.get_json()

    if not data.get('nombre_tipo'):
        return jsonify({
            'error': 'El nombre del tipo es requerido'
        }), 200

    if CatTipoActivo.query.filter_by(nombre_tipo=data['nombre_tipo']).first():
        return jsonify({
            'error': 'El tipo ya existe'
        }), 400

    try:
        tipo = CatTipoActivo(
            nombre_tipo=data['nombre_tipo'],
            descripcion=data.get('descripcion'),
            activo=data.get('activo')
        )
        db.session.add(tipo)
        db.session.commit()

        return jsonify({
            'mensaje': 'Tipo de activo creado',
            'tipo': tipo.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

@catalogos_bp.route('/tipos-activo/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puede_actualizar')
def update_tipo_activo(id):
    """Actualizar tipo de activo"""
    tipo = CatTipoActivo.query.get(id)

    if not tipo:
        return jsonify({
            'error': 'Tipo no encontrado'
        }), 404

    data = request.get_json()

    try:
        if 'nombre_tipo' in data: tipo.nombre_tipo = data['nombre_tipo']
        if 'descripcion' in data: tipo.descripcion = data['descripcion']
        if 'activo' in data: tipo.activo = data['activo']

        db.session.commit()
        return jsonify({
            'mensaje': 'tipo actualizado',
            'tipo': tipo.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

@catalogos_bp.route('/tipos-activo/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
def delete_tipo_activo(id):
    """Eliminar un tipo de activo"""
    tipo = CatTipoActivo.query.get(id)

    if not tipo:
        return jsonify({
            'error': 'Tipo no encontrado'
        }), 404

    try:
        db.session.delete(tipo)
        db.session.commit()

        return jsonify({
            'mensaje': 'Tipo elminado'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

# ---- Estados ----

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
    query = query.order_by(CatEstado.nombre_estado.asc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'estados': [e.to_dict() for e in paginated.items],
        'total':   paginated.total,
        'pages':   paginated.pages,
        'current_page': paginated.page,
    }), 200


@catalogos_bp.route('/estados/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('catalogos','puede_leer')
def get_estado(id):
    """Obtener un estado mediante su ID"""
    estado = CatEstado.query.get(id)

    if not estado:
        return jsonify({
            'error': 'Estado no encontrado'
        }), 404

    return jsonify(estado.to_dict()), 200

@catalogos_bp.route('/estados', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_estado():
    """Crear un nuevo estado"""
    data = request.get_json()

    if not data.get('nombre_estado'):
        return jsonify({
            'error': 'El nombre del estado es requerido'
        }), 400

    if CatEstado.query.filter_by(nombre_estado=data['nombre_estado']).first():
        return jsonify({
            'error': 'El estado ya existe'
        }), 400

    try:
        estado = CatEstado(
            nombre_estado=data['nombre_estado'],
            descripcion=data.get('descripcion'),
            activo=data.get('activo'),
            color_hex=data.get('color_hex')
        )

        db.session.add(estado)
        db.session.commit()

        return jsonify({
            'mensaje': 'Estado creado',
            'estado': estado.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

@catalogos_bp.route('/estados/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puede_actualizar')
def update_estado(id):
    """Actualizar un estado"""
    estado = CatEstado.query.get(id)

    if not estado:
        return jsonify({
            'error': 'Estado no encontrado'
        }), 404

    data = request.get_json()

    try:
        if 'nombre_estado' in data: estado.nombre_estado = data['nombre_estado']
        if 'descripcion' in data: estado.descripcion = data['descripcion']
        if 'color_hex' in data: estado.color_hex = data['color_hex']
        if 'activo' in data: estado.activo = data['activo']

        db.session.commit()
        return jsonify({
            'mensaje': 'Esatdo actualizado',
            'estado': estado.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

@catalogos_bp.route('/estados/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
def delete_estado(id):
    """Eliminar un estado"""
    estado = CatEstado.query.get(id)

    if not estado:
        return jsonify({
            'error': 'Estado no encontrado'
        }), 404

    try:
        db.session.delete(estado)
        db.session.commit()

        return jsonify({
            'mensaje': 'Estado elminado'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

# ----- Tipos de Mobiliario ----

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
    query = query.order_by(CatTipoMobiliario.nombre_tipo.asc())
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
    """Obtener un mobiliario mediante su ID"""
    catalogo = CatTipoMobiliario.query.get(id)

    if not catalogo:
        return jsonify({
            'error': 'Catálogo no encontrado'
        }), 404

    return jsonify(catalogo.to_dict()), 200

@catalogos_bp.route('/tipos-mobiliario', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_tipo_mobiliario():
    """Crear un nuevo tipo de mobiliario"""
    data = request.get_json()

    if not data.get('nombre_tipo'):
        return jsonify({
            'error': 'El nombre del tipo es requerido'
        }), 400

    if CatTipoMobiliario.query.filter_by(nombre_tipo=data['nombre_tipo']).first():
        return jsonify({
            'error': 'El tipo ya existe'
        }), 400

    try:
        tipo = CatTipoMobiliario(
            nombre_activo=data['nombre_tipo'],
            descripcion=data.get('descripcion'),
            activo=data.get('activo')
        )
        db.session.add(tipo)
        db.session.commit()

        return jsonify({
            'mensaje': 'Tipo de mobiliario creado'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

@catalogos_bp.route('/tipos-mobiliario/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puedo_actualizar')
def update_tipo_mobiliario(id):
    """Actualizar un tipo de mobiliario"""
    tipo = CatTipoMobiliario.query.get(id)

    if not tipo:
        return jsonify({
            'error': 'Tipo no encontrado'
        }), 404

    data = request.get_json()

    try:
        if 'nombre_tipo' in data: tipo.nombre_tipo = data['nombre_tipo']
        if 'descripcion' in data: tipo.descripcion = data['descripcion']
        if 'activo' in data: tipo.activo = data['activo']

        db.session.commit()

        return jsonify({
            'mensaje': 'tipo actualizado',
            'tipo': tipo.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

@catalogos_bp.route('/tipos-mobiliario/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
def delete_tipo_mobiliario(id):
    """Eliminar un tipo de mobiliario"""
    tipo = CatTipoMobiliario.query.get(id)

    if not tipo:
        return jsonify({
            'error': 'Tipo no encontrado'
        }), 404

    try:
        db.session.delete(tipo)
        db.session.commit()

        return jsonify({
            'mensaje': 'Tipo eliminado'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500