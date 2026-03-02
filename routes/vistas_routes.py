from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import or_, and_, func
from utils.extesions import db
from utils.decorators import require_permission
from models import (
    VistaEquiposCompleta,
    VistaMobiliarioCompleta,
    VistaUsuariosCompleta,
    VistaAccesosCompleta,
    VistaPermisosDetalle,
    VistaHistorialCompleta
)

# TODO: Fix ID's search

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
                # VistaEquiposCompleta.id_activo.ilike(f'%{search}%')
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
                # VistaMobiliarioCompleta.id_mueble.ilike(f'%{search}%')
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

@vistas_bp.route('/usuarios-completo/', methods=['GET'])
@jwt_required()
@require_permission('responsable', 'puede_leer')
def get_vista_usuarios_completa():
    """Obtener vista de usuarios responsables con conteo de bienes asignados"""
    search = request.args.get('search', '')
    area = request.args.get('area')
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
                VistaUsuariosCompleta.numero_nomina.ilike(f'%{search}%'),
                VistaUsuariosCompleta.puesto.ilike(f'%{search}%')
            )
        )

    # Ordenar alfabéticamente por nombre
    query = query.order_by(VistaUsuariosCompleta.nombre_usuario.asc())

    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'usuarios': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@vistas_bp.route('/usuario-completo/<int:id>', methods=['GET'])
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
    # modulo = request.args.get('modulo_id')
    # tipo = request.args.get('tipo_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)


    # Query base usando el modelo
    query = VistaAccesosCompleta.query

    # Aplicar filtros
    if area:
        query = query.filter(VistaAccesosCompleta.area == area)

    if search:
        query = query.filter(
            or_(
                VistaAccesosCompleta.nombre_usuario.ilike(f'%{search}%'),
                VistaAccesosCompleta.correo_electronico.ilike(f'%{search}%'),
                VistaAccesosCompleta.area.ilike(f'%{search}%')
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


# ============================================
# VISTA DETALLADA DE PERMISOS
# ============================================

@vistas_bp.route('/permisos-detalle', methods=['GET'])
@jwt_required()
@require_permission('acceso', 'puede_leer')
def get_vista_permisos_detalle():
    """Obtener vista detallada de permisos por usuario y módulo"""
    usuario = request.args.get('usuario')
    modulo = request.args.get('modulo')
    area = request.args.get('area')

    # Query base usando el modelo
    query = VistaPermisosDetalle.query

    # Aplicar filtros
    if usuario:
        query = query.filter(VistaPermisosDetalle.nombre_usuario.ilike(f'%{usuario}%'))

    if modulo:
        query = query.filter(VistaPermisosDetalle.modulo == modulo)

    if area:
        query = query.filter(VistaPermisosDetalle.area == area)

    # Ordenar por usuario y módulo
    query = query.order_by(
        VistaPermisosDetalle.nombre_usuario.asc(),
        VistaPermisosDetalle.modulo.asc()
    )

    # Ejecutar query
    permisos = query.all()

    return jsonify({
        'permisos': [p.to_dict() for p in permisos],
        'total': len(permisos)
    }), 200


# ============================================
# VISTA DE HISTORIAL DE MOVIMIENTOS
# ============================================

@vistas_bp.route('/historial-completa', methods=['GET'])
@jwt_required()
@require_permission('historial', 'puede_leer')
def get_vista_historial_completa():
    """Obtener vista completa del historial de movimientos"""
    tipo_registro = request.args.get('tipo_registro')  # 'computo' o 'mobiliario'
    id_registro = request.args.get('id_registro', type=int)
    tipo_movimiento = request.args.get('tipo_movimiento')
    realizado_por = request.args.get('realizado_por')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Query base usando el modelo
    query = VistaHistorialCompleta.query

    # Aplicar filtros
    if tipo_registro:
        query = query.filter(VistaHistorialCompleta.tipo_registro == tipo_registro)

    if id_registro:
        query = query.filter(VistaHistorialCompleta.id_registro == id_registro)

    if tipo_movimiento:
        query = query.filter(VistaHistorialCompleta.tipo_movimiento == tipo_movimiento)

    if realizado_por:
        query = query.filter(VistaHistorialCompleta.realizado_por.ilike(f'%{realizado_por}%'))

    if fecha_desde:
        query = query.filter(VistaHistorialCompleta.fecha_movimiento >= fecha_desde)

    if fecha_hasta:
        query = query.filter(VistaHistorialCompleta.fecha_movimiento <= fecha_hasta)

    # Ordenar por fecha descendente (más recientes primero)
    query = query.order_by(VistaHistorialCompleta.fecha_movimiento.desc())

    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'movimientos': [m.to_dict() for m in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


# ============================================
# ENDPOINT PARA ESTADÍSTICAS GENERALES
# ============================================

@vistas_bp.route('/estadisticas', methods=['GET'])
@jwt_required()
def get_estadisticas():
    """Obtener estadísticas generales del sistema"""

    # Estadísticas de equipos usando el modelo
    total_equipos = VistaEquiposCompleta.query.count()
    funcionales = VistaEquiposCompleta.query.filter(
        VistaEquiposCompleta.estado == 'Funcional'
    ).count()
    en_reparacion = VistaEquiposCompleta.query.filter(
        VistaEquiposCompleta.estado == 'En reparación'
    ).count()
    danados = VistaEquiposCompleta.query.filter(
        VistaEquiposCompleta.estado == 'Dañado'
    ).count()
    equipos_asignados = VistaEquiposCompleta.query.filter(
        VistaEquiposCompleta.responsable.isnot(None)
    ).count()

    # Estadísticas de mobiliario usando el modelo
    total_mobiliario = VistaMobiliarioCompleta.query.count()
    buenos = VistaMobiliarioCompleta.query.filter(
        VistaMobiliarioCompleta.estado == 'Bueno'
    ).count()
    regulares = VistaMobiliarioCompleta.query.filter(
        VistaMobiliarioCompleta.estado == 'Regular'
    ).count()
    malos = VistaMobiliarioCompleta.query.filter(
        VistaMobiliarioCompleta.estado == 'Malo'
    ).count()
    mobiliario_asignado = VistaMobiliarioCompleta.query.filter(
        VistaMobiliarioCompleta.responsable.isnot(None)
    ).count()

    # Estadísticas de usuarios usando agregación
    total_responsables = VistaUsuariosCompleta.query.count()

    # Suma total de equipos asignados
    sum_equipos = db.session.query(
        func.sum(VistaUsuariosCompleta.equipos_asignados)
    ).scalar() or 0

    # Suma total de mobiliario asignado
    sum_mobiliario = db.session.query(
        func.sum(VistaUsuariosCompleta.mobiliario_asignado)
    ).scalar() or 0

    # Estadísticas de accesos
    total_accesos = VistaAccesosCompleta.query.count()

    return jsonify({
        'equipos': {
            'total': total_equipos,
            'funcionales': funcionales,
            'en_reparacion': en_reparacion,
            'danados': danados,
            'asignados': equipos_asignados
        },
        'mobiliario': {
            'total': total_mobiliario,
            'buenos': buenos,
            'regulares': regulares,
            'malos': malos,
            'asignados': mobiliario_asignado
        },
        'usuarios': {
            'total_responsables': total_responsables,
            'total_equipos_asignados': int(sum_equipos),
            'total_mobiliario_asignado': int(sum_mobiliario)
        },
        'accesos': {
            'total_accesos': total_accesos
        }
    }), 200