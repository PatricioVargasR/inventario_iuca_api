from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models import VistaHistorialCompleta
from utils.decorators import require_permission
from sqlalchemy import or_
from datetime import datetime

historial_bp = Blueprint('historial', __name__)

# ============================================
# Historial de Movimiento
# ============================================

historial_bp = Blueprint('historial', __name__, url_prefix='/api/historial')

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
        search = request.args.get('search', '').strip()
        tipo_registro = request.args.get('tipo_registro', '').strip()
        tipo_movimiento = request.args.get('tipo_movimiento', '').strip()
        fecha_desde = request.args.get('fecha_desde', '').strip()
        fecha_hasta = request.args.get('fecha_hasta', '').strip()

        # Query base
        query = VistaHistorialCompleta.query

        # Filtro de búsqueda rápida (en tabla, operación, realizado_por, registro_id)
        if search:
            query = query.filter(
                or_(
                    VistaHistorialCompleta.tabla.ilike(f'%{search}%'),
                    VistaHistorialCompleta.operacion.ilike(f'%{search}%'),
                    VistaHistorialCompleta.realizado_por.ilike(f'%{search}%'),
                    VistaHistorialCompleta.registro_id.ilike(f'%{search}%')
                )
            )

        # Filtro por tipo de registro
        if tipo_registro:
            # Mapear nombres amigables a nombres de tabla
            tabla_map = {
                'computo': 'equipos_computo',
                'mobiliario': 'mobiliario',
                'acceso': 'acceso',
                'usuario': 'usuario'
            }
            tabla_nombre = tabla_map.get(tipo_registro.lower(), tipo_registro)
            query = query.filter(VistaHistorialCompleta.tabla == tabla_nombre)

        # Filtro por tipo de movimiento
        if tipo_movimiento:
            # Mapear nombres amigables a operaciones
            operacion_map = {
                'creacion': 'INSERT',
                'edicion': 'UPDATE',
                'eliminacion': 'DELETE'
            }
            operacion_nombre = operacion_map.get(tipo_movimiento.lower(), tipo_movimiento.upper())
            query = query.filter(VistaHistorialCompleta.operacion == operacion_nombre)

        # Filtro por rango de fechas
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
                query = query.filter(VistaHistorialCompleta.fecha >= fecha_desde_dt)
            except ValueError:
                pass

        if fecha_hasta:
            try:
                # Incluir todo el día hasta las 23:59:59
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(VistaHistorialCompleta.fecha <= fecha_hasta_dt)
            except ValueError:
                pass

        # Ordenar por fecha descendente
        query = query.order_by(VistaHistorialCompleta.fecha.desc())

        # Paginación
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'movimientos': [item.to_dict_detallado() for item in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': paginated.page,
            'per_page': per_page,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
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
