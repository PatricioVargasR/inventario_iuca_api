from flask import Blueprint, request, jsonify
import json
from flask_jwt_extended import jwt_required
from sqlalchemy import String, and_, or_, func, cast, text
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
    tipo_activo = request.args.get('tipo_activo_id')
    estado = request.args.get('estado_id')
    # Soporta múltiples responsables: ?usuario_id=1&usuario_id=2 o ?usuario_id=1,2
    responsables_raw = request.args.getlist('usuario_id')
    sort_by = request.args.get('sort_by')
    sort_dir = request.args.get('sort_dir')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Normalizar lista de IDs (puede venir como "1,2,3" o múltiples parámetros)
    responsables_ids = _parse_ids_list(responsables_raw)

    query = VistaEquiposCompleta.query

    if tipo_activo:
        query = query.filter(VistaEquiposCompleta.tipo_activo == tipo_activo)

    if estado:
        query = query.filter(VistaEquiposCompleta.estado == estado)

    # Filtro por múltiples responsables usando subquery sobre equipos_responsables
    if responsables_ids:
        from models import EquipoResponsable
        # Equipos que tienen AL MENOS UNO de los responsables seleccionados
        subq = db.session.query(EquipoResponsable.equipo_id).filter(
            EquipoResponsable.usuario_id.in_(responsables_ids)
        ).subquery()
        query = query.filter(VistaEquiposCompleta.id_activo.in_(subq))

    if sort_by:
        column = getattr(VistaEquiposCompleta, sort_by, None)
        if column:
            if sort_dir == 'desc':
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

    if search:
        query = query.filter(
            or_(
                VistaEquiposCompleta.nombre_activo.ilike(f'%{search}%'),
                VistaEquiposCompleta.marca.ilike(f'%{search}%'),
                VistaEquiposCompleta.modelo.ilike(f'%{search}%'),
                VistaEquiposCompleta.numero_serie.ilike(f'%{search}%'),
                cast(VistaEquiposCompleta.id_activo, String).ilike(f'%{search}%')
            )
        )

    query = query.order_by(VistaEquiposCompleta.id_activo.asc())
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
    tipo_mobiliario = request.args.get('tipo_mobiliario_id')
    estado = request.args.get('estado_id')
    area = request.args.get('area')
    responsables_raw = request.args.getlist('usuario_id')
    sort_by = request.args.get('sort_by')
    sort_dir = request.args.get('sort_dir', 'asc')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    responsables_ids = _parse_ids_list(responsables_raw)

    query = VistaMobiliarioCompleta.query

    if tipo_mobiliario:
        query = query.filter(VistaMobiliarioCompleta.tipo_mobiliario == tipo_mobiliario)

    if estado:
        query = query.filter(VistaMobiliarioCompleta.estado == estado)

    if area:
        query = query.filter(VistaMobiliarioCompleta.area == area)

    # Filtro por múltiples responsables
    if responsables_ids:
        from models import MobiliarioResponsable
        subq = db.session.query(MobiliarioResponsable.mueble_id).filter(
            MobiliarioResponsable.usuario_id.in_(responsables_ids)
        ).subquery()
        query = query.filter(VistaMobiliarioCompleta.id_mueble.in_(subq))

    if sort_by:
        column = getattr(VistaMobiliarioCompleta, sort_by, None)
        if column:
            if sort_dir == 'desc':
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

    if search:
        query = query.filter(
            or_(
                VistaMobiliarioCompleta.marca.ilike(f'%{search}%'),
                VistaMobiliarioCompleta.modelo.ilike(f'%{search}%'),
                VistaMobiliarioCompleta.color.ilike(f'%{search}%'),
                VistaMobiliarioCompleta.tipo_mobiliario.ilike(f'%{search}%'),
                cast(VistaMobiliarioCompleta.id_mueble, String).ilike(f'%{search}%')
            )
        )

    query = query.order_by(VistaMobiliarioCompleta.id_mueble.asc())
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
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by')
    sort_dir = request.args.get('sort_dir', 'asc')
    area = request.args.get('area_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = VistaUsuariosCompleta.query

    if area:
        query = query.filter(VistaUsuariosCompleta.area == area)

    if search:
        query = query.filter(
            or_(
                VistaUsuariosCompleta.nombre_usuario.ilike(f'%{search}%'),
                VistaUsuariosCompleta.puesto.ilike(f'%{search}%'),
                cast(VistaUsuariosCompleta.id_usuario, String).ilike(f'%{search}%'),
                cast(VistaUsuariosCompleta.numero_nomina, String).ilike(f'%{search}%')
            )
        )

    if sort_by:
        column = getattr(VistaUsuariosCompleta, sort_by, None)
        if column:
            if sort_dir == 'desc':
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

    query = query.order_by(VistaUsuariosCompleta.id_usuario.asc())
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
    sort_by = request.args.get('sort_by')
    sort_dir = request.args.get('sort_dir', 'asc')
    permisos_param = request.args.get('permisos')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = VistaAccesosCompleta.query

    if area:
        query = query.filter(VistaAccesosCompleta.area == area)

    if sort_by:
        column = getattr(VistaAccesosCompleta, sort_by, None)
        if column:
            if sort_dir == 'desc':
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

    if permisos_param:
        try:
            permisos_filtro = json.loads(permisos_param)

            mapeo_permisos = {
                'puede_leer': 'leer',
                'puede_crear': 'crear',
                'puede_actualizar': 'actualizar',
                'puede_eliminar': 'eliminar'
            }

            condiciones_modulos = []

            for modulo, permisos_requeridos in permisos_filtro.items():
                condiciones_permisos = []

                for permiso_frontend in permisos_requeridos:
                    permiso_db = mapeo_permisos.get(permiso_frontend, permiso_frontend)

                    condicion_sql = text("""
                        EXISTS (
                            SELECT 1
                            FROM json_array_elements(permisos) AS p
                            WHERE p->>'modulo' = :modulo
                            AND (p->>'""" + permiso_db + """')::boolean = true
                        )
                    """).bindparams(modulo=modulo)

                    condiciones_permisos.append(condicion_sql)

                if condiciones_permisos:
                    condiciones_modulos.append(and_(*condiciones_permisos))

            if condiciones_modulos:
                query = query.filter(and_(*condiciones_modulos))

        except (json.JSONDecodeError, ValueError):
            pass

    if search:
        query = query.filter(
            or_(
                VistaAccesosCompleta.nombre_usuario.ilike(f'%{search}%'),
                VistaAccesosCompleta.correo_electronico.ilike(f'%{search}%'),
                VistaAccesosCompleta.area.ilike(f'%{search}%'),
                cast(VistaAccesosCompleta.id_acceso, String).ilike(f'%{search}%')
            )
        )

    query = query.order_by(VistaAccesosCompleta.id_acceso.asc())
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
# HELPER
# ============================================

def _parse_ids_list(raw_list):
    """
    Normaliza una lista de IDs que puede venir como:
    - Múltiples params: ?usuario_id=1&usuario_id=2
    - Valores con coma: ?usuario_id=1,2,3
    - Mezcla de ambos
    Retorna un set de enteros o None si está vacío.
    """
    ids = set()
    for item in raw_list:
        for part in str(item).split(','):
            part = part.strip()
            if part.isdigit():
                ids.add(int(part))
    return ids if ids else None