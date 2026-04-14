from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models import VistaHistorialCompleta
from utils.decorators import require_permission
from sqlalchemy import String, cast, or_
from datetime import datetime
from utils.constants import (
    TABLAS_VISIBLES, CAMPOS_IGNORADOS,
    TABLA_ALIASES, OPERACION_ALIASES,
    TIPO_DE_REGISTRO, OPERACION_MOVIMIENTO
)

historial_bp = Blueprint('historial', __name__)

# ============================================
# Historial de Movimiento
# ============================================

@historial_bp.route('/', methods=['GET'])
@jwt_required()
@require_permission('historial', 'puede_leer')
def get_historial():
    """Obtener historial con filtros avanzados"""
    try:
        # Parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Filtros
        search        = request.args.get('search', '').strip()
        tipo_registro  = request.args.get('tipo_registro', '').strip()
        tipo_movimiento = request.args.get('tipo_movimiento', '').strip()
        usuario_id    = request.args.get('usuario_id')
        fecha_desde   = request.args.get('fecha_desde', '').strip()
        fecha_hasta   = request.args.get('fecha_hasta', '').strip()
        sort_by = request.args.get('sort_by')
        sort_dir = request.args.get('sort_dir', 'asc')

        # Query base — solo tablas visibles
        query = VistaHistorialCompleta.query.filter(
            VistaHistorialCompleta.tabla.in_(TABLAS_VISIBLES)
        )

        # Excluir UPDATEs cuyo único cambio sea un campo ignorado
        # (se hace en Python tras paginación para no complicar el ORM,
        #  pero primero excluimos los casos más comunes a nivel SQL)
        # Nota: si cambios es un JSON como {"ultimo_acceso": {...}},
        # podemos filtrar en SQL con cast + operador JSON
        # Se hace la exclusión post-fetch más abajo.

        # ── Filtros ─────────────────────────────────────────────────────
        if search:
            search_lower = search.lower()

            print(search_lower)

            # Resolver si el término coincide con algún alias
            tabla_buscada     = None
            operacion_buscada = None
            es_catalogo       = False

            for alias, tabla_real in TABLA_ALIASES.items():
                if alias in search_lower:
                    if tabla_real is None:
                        es_catalogo = True
                    else:
                        tabla_buscada = tabla_real
                    break

            for alias, op_real in OPERACION_ALIASES.items():
                if alias in search_lower:
                    operacion_buscada = op_real
                    break

            # Construir condiciones OR
            condiciones = [
                VistaHistorialCompleta.realizado_por.ilike(f'%{search}%'),
                VistaHistorialCompleta.registro_id.ilike(f'%{search}%'),
                VistaHistorialCompleta.tabla.ilike(f'%{search}%'),
                VistaHistorialCompleta.operacion.ilike(f'%{search}%'),
                cast(VistaHistorialCompleta.id_historial, String).ilike(f'%{search}%')
            ]

            if tabla_buscada:
                condiciones.append(VistaHistorialCompleta.tabla == tabla_buscada)

            if es_catalogo:
                condiciones.append(VistaHistorialCompleta.tabla.like('cat_%'))

            if operacion_buscada:
                condiciones.append(VistaHistorialCompleta.operacion == operacion_buscada)

            query = query.filter(or_(*condiciones))

        if usuario_id:
            query = query.filter(VistaHistorialCompleta.usuario_id == usuario_id)

        if tipo_registro:
            tabla_nombre = TIPO_DE_REGISTRO.get(tipo_registro.lower(), tipo_registro)
            query = query.filter(VistaHistorialCompleta.tabla == tabla_nombre)

        if tipo_movimiento:
            operacion_nombre = OPERACION_MOVIMIENTO.get(tipo_movimiento.lower(), tipo_movimiento.upper())
            query = query.filter(VistaHistorialCompleta.operacion == operacion_nombre)

        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
                query = query.filter(VistaHistorialCompleta.fecha >= fecha_desde_dt)
            except ValueError:
                pass

        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(VistaHistorialCompleta.fecha <= fecha_hasta_dt)
            except ValueError:
                pass

        if sort_by:
            column = getattr(VistaHistorialCompleta, sort_by, None)
            if column:
                if sort_dir == 'desc':
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())

        # Ordenar por fecha descendente
        query = query.order_by(VistaHistorialCompleta.id_historial.asc())

        # ── Paginación ──────────────────────────────────────────────────
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        # ── Filtro post-fetch: descartar UPDATEs de solo campos ignorados
        def es_visible(item):
            """Devuelve False si el registro no aporta información útil."""
            if item.operacion != 'UPDATE':
                return True
            if not item.cambios:
                return False  # UPDATE sin cambios registrados → omitir
            campos_cambiados = set(item.cambios.keys())
            # Si todos los campos cambiados son ignorados, omitir
            return not campos_cambiados.issubset(CAMPOS_IGNORADOS)

        # start = (paginated.page - 1) * paginated.per_page + 1

        # items_visibles = [item for item in paginated.items if es_visible(item)]

        # movimientos_filtrados = [
        #     {
        #         **item.to_dict_detallado(),
        #         "index": i
        #     }
        #     for i, item in enumerate(items_visibles, start=start)
        # ]

        movimientos_filtrados = [
            item.to_dict_detallado()
            for item in paginated.items
            if es_visible(item)
        ]

        return jsonify({
            'movimientos':   movimientos_filtrados,
            'total':         paginated.total,
            'pages':         paginated.pages,
            'current_page':  paginated.page,
            'per_page':      per_page,
            'has_next':      paginated.has_next,
            'has_prev':      paginated.has_prev
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@historial_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('historial', 'puede_leer')
def get_historial_detalle(id):
    """Obtener un cambio específico con detalles completos"""
    try:
        cambio = VistaHistorialCompleta.query.get(id)

        if not cambio:
            return jsonify({'error': 'Registro no encontrado'}), 404

        return jsonify(cambio.to_dict_detallado()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@historial_bp.route('/tabla/<string:tabla>', methods=['GET'])
@jwt_required()
@require_permission('historial', 'puede_leer')
def get_historial_por_tabla(tabla):
    """Obtener historial de una tabla específica"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = VistaHistorialCompleta.query.filter_by(tabla=tabla).order_by(
            VistaHistorialCompleta.fecha.desc()
        )

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'movimientos': [item.to_dict_detallado() for item in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': paginated.page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@historial_bp.route('/registro/<string:tabla>/<string:registro_id>', methods=['GET'])
@jwt_required()
@require_permission('historial', 'puede_leer')
def get_historial_por_registro(tabla, registro_id):
    """Obtener historial completo de un registro específico"""
    try:
        historial = VistaHistorialCompleta.query.filter_by(
            tabla=tabla,
            registro_id=registro_id
        ).order_by(VistaHistorialCompleta.fecha.desc()).all()

        return jsonify({
            'movimientos': [item.to_dict_detallado() for item in historial],
            'total': len(historial)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
