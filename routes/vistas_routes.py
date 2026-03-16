from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import String, or_, func, cast
from utils.extesions import db
from utils.decorators import require_permission
from models import (
    VistaEquiposCompleta,
    VistaMobiliarioCompleta,
    VistaUsuariosCompleta,
    VistaAccesosCompleta,
)

vistas_bp = Blueprint('vistas', __name__)

# ============================================
# VISTA COMPLETA DE EQUIPOS
# ============================================

@vistas_bp.route('/equipos-completo/', methods=['GET'])
@jwt_required()
@require_permission('computo', 'puede_leer')
def get_vista_equipos_completa():
    """Obtener vista completa de equipos con toda la información relacionada"""
    # Parámetros de filtro
    tipo_activo = request.args.get('tipo_activo_id')
    estado = request.args.get('estado_id')
    area = request.args.get('area')
    responsable = request.args.get('usuario_id')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Query base usando el modelo
    query = VistaEquiposCompleta.query


    # Aplicar filtros
    if tipo_activo:
        query = query.filter(VistaEquiposCompleta.tipo_activo == tipo_activo)

    if estado:
        query = query.filter(VistaEquiposCompleta.estado == estado)

    if area:
        query = query.filter(VistaEquiposCompleta.area == area)

    if responsable:
        query = query.filter(VistaEquiposCompleta.responsable.ilike(f'%{responsable}%'))

    if search:
        query = query.filter(
            or_(
                VistaEquiposCompleta.nombre_activo.ilike(f'%{search}%'),
                VistaEquiposCompleta.marca.ilike(f'%{search}%'),
                VistaEquiposCompleta.modelo.ilike(f'%{search}%'),
                VistaEquiposCompleta.numero_serie.ilike(f'%{search}%'),
                VistaEquiposCompleta.responsable.ilike(f'%{search}%'),
                cast(VistaEquiposCompleta.id_activo, String).ilike(f'%{search}%')
            )
        )

    # Ordenar por ID descendente
    query = query.order_by(VistaEquiposCompleta.id_activo.desc())

    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'equipos': [equipo.to_dict() for equipo in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@vistas_bp.route('/equipo-completo/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('computo', 'puede_leer')
def get_equipo_completo(id):
    """Obtener un equipo por ID con especificaciones"""
    equipo = VistaEquiposCompleta.query.get(id)

    if not equipo:
        return jsonify({
            'error': 'Equipo no encontrado'
        }), 404

    return jsonify(equipo.to_dict()), 200


# ============================================
# VISTA COMPLETA DE MOBILIARIO
# ============================================

@vistas_bp.route('/mobiliarios-completo/', methods=['GET'])
@jwt_required()
@require_permission('mobiliario', 'puede_leer')
def get_vista_mobiliario_completa():
    """Obtener vista completa de mobiliario con toda la información relacionada"""
    # Parámetros de filtro
    tipo_mobiliario = request.args.get('tipo_mobiliario_id')
    estado = request.args.get('estado_id')
    area = request.args.get('area')
    responsable = request.args.get('usuario_id')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Query base usando el modelo
    query = VistaMobiliarioCompleta.query

    # Aplicar filtros
    if tipo_mobiliario:
        query = query.filter(VistaMobiliarioCompleta.tipo_mobiliario == tipo_mobiliario)

    if estado:
        query = query.filter(VistaMobiliarioCompleta.estado == estado)

    if area:
        query = query.filter(VistaMobiliarioCompleta.area == area)

    if responsable:
        query = query.filter(VistaMobiliarioCompleta.responsable.ilike(f'%{responsable}%'))

    if search:
        query = query.filter(
            or_(
                VistaMobiliarioCompleta.marca.ilike(f'%{search}%'),
                VistaMobiliarioCompleta.modelo.ilike(f'%{search}%'),
                VistaMobiliarioCompleta.color.ilike(f'%{search}%'),
                VistaMobiliarioCompleta.responsable.ilike(f'%{search}%'),
                VistaMobiliarioCompleta.tipo_mobiliario.ilike(f'%{search}%'),
                cast(VistaMobiliarioCompleta.id_mueble, String).ilike(f'%{search}%')

            )
        )

    # Ordenar por ID descendente
    query = query.order_by(VistaMobiliarioCompleta.id_mueble.desc())

    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'mobiliario': [m.to_dict() for m in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@vistas_bp.route('/mobiliario-completo/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('mobiliario', 'puede_leer')
def get_mobiliario_completo(id):
    """Obtener un mobiliario mediante su ID"""
    mobiliario = VistaMobiliarioCompleta.query.get(id)

    if not mobiliario:
        return jsonify({
            'error': 'Mobiliario no encontrado'
        }), 404

    return jsonify(mobiliario.to_dict()), 200

# ============================================
# VISTA DE USUARIOS CON CONTEO DE BIENES
# ============================================

@vistas_bp.route('/responsables-completo/', methods=['GET'])
@jwt_required()
@require_permission('responsable', 'puede_leer')
def get_vista_responsables_completa():
    """Obtener vista de usuarios responsables con conteo de bienes asignados"""
    search = request.args.get('search', '')
    area = request.args.get('area_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Query base usando el modelo
    query = VistaUsuariosCompleta.query

    # Aplicar filtros
    if area:
        query = query.filter(VistaUsuariosCompleta.area == area)

    if search:
        query = query.filter(
            or_(
                VistaUsuariosCompleta.nombre_usuario.ilike(f'%{search}%'),
                VistaUsuariosCompleta.puesto.ilike(f'%{search}%'),
                cast(VistaUsuariosCompleta.id_usuario, String).ilike(f'%{search}%')
            )
        )

    # Ordenar alfabéticamente por nombre
    query = query.order_by(VistaUsuariosCompleta.nombre_usuario.asc())

    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'responsables': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@vistas_bp.route('/responsable-completo/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('responsable', 'puede_leer')
def get_usuario_complet(id):
    """Obtener un usuario mediante su ID"""
    usuario = VistaUsuariosCompleta.query.get(id)

    if not usuario:
        return jsonify({
            'error': 'Usuario no encontrado'
        }), 404

    return jsonify(usuario.to_dict()), 200


# ============================================
# VISTA DE ACCESOS CON RESUMEN DE PERMISOS
# ============================================

@vistas_bp.route('/accesos-completo/', methods=['GET'])
@jwt_required()
@require_permission('acceso', 'puede_leer')
def get_vista_accesos_completa():
    """Obtener vista de accesos al sistema con resumen de permisos"""
    search = request.args.get('search', '')
    area = request.args.get('area_id')
    modulo = request.args.get('modulo')  # Módulo seleccionado
    permisos = request.args.getlist('permisos[]')  # Lista de permisos a filtrar
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)


    # Query base usando el modelo
    query = VistaAccesosCompleta.query

    # Aplicar filtros
    if area:
        query = query.filter(VistaAccesosCompleta.area == area)

    # Filtro por módulo y permisos específicos
    if modulo and permisos:
        # Filtrar accesos que tengan al menos uno de los permisos seleccionados en el módulo
        for permiso in permisos:
            # Construir la condición JSON para verificar el permiso
            json_path = f"$.{modulo}.{permiso}"
            query = query.filter(
                func.jsonb_path_exists(
                    VistaAccesosCompleta.permisos,
                    json_path
                )
            ).filter(
                func.jsonb_extract_path_text(
                    VistaAccesosCompleta.permisos,
                    modulo,
                    permiso
                ).cast(db.Boolean) == True
            )

    if search:
        query = query.filter(
            or_(
                VistaAccesosCompleta.nombre_usuario.ilike(f'%{search}%'),
                VistaAccesosCompleta.correo_electronico.ilike(f'%{search}%'),
                VistaAccesosCompleta.area.ilike(f'%{search}%'),
                cast(VistaAccesosCompleta.id_acceso, String).ilike(f'%{search}%')
            )
        )

    # Ordenar alfabéticamente por nombre
    query = query.order_by(VistaAccesosCompleta.nombre_usuario.asc())

    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'accesos': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@vistas_bp.route('/acceso-completo/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('acceso', 'puede_leer')
def get_acceso_completo(id):
    """Obtener un acceso mediante su ID"""
    acceso = VistaAccesosCompleta.query.get(id)

    if not acceso:
        return jsonify({
            'mensaje': 'Acceso no encontrado'
        }), 404

    return jsonify(acceso.to_dict()), 200

