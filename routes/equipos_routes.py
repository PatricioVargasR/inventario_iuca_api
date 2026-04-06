from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import BloqueoActivo, EquipoComputo, EspecificacionEquipo
from utils.decorators import require_permission
from utils.validators import validate_equipo, ValidationError, handle_db_error
from utils.concurrency import (
    verificar_version,
    liberar_bloqueo
)
from utils.lock_required import lock_required

equipos_bp = Blueprint('equipos', __name__)


@equipos_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('computo', 'puede_leer')
def get_equipo(id):
    """Obtener un equipo por ID con especificaciones y estado de bloqueo"""
    equipo = EquipoComputo.query.get(id)

    if not equipo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    return jsonify(equipo.to_dict(include_specs=True, include_version=True)), 200


@equipos_bp.route('/', methods=['POST'])
@jwt_required()
@require_permission('computo', 'puede_crear')
def create_equipo():
    """Crear nuevo equipo de cómputo"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación de esquema ────────────────────────────────────
    try:
        validate_equipo(data, is_update=False)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    # Verificar número de serie único
    if data.get('numero_serie'):
        existe = EquipoComputo.query.filter_by(numero_serie=data['numero_serie']).first()
        if existe:
            return jsonify({
                'error': 'El número de serie ya está registrado',
                'campos': {'numero_serie': 'Este número de serie ya existe'}
            }), 409

    try:
        equipo = EquipoComputo(
            tipo_activo_id=data['tipo_activo_id'],
            nombre_activo=data['nombre_activo'].strip(),
            marca=data.get('marca', '').strip() or None,
            modelo=data.get('modelo', '').strip() or None,
            numero_serie=data.get('numero_serie', '').strip() or None,
            estado_id=data['estado_id'],
            observaciones=data.get('observaciones', '').strip() or None,
            usuario_asignado_id=data.get('usuario_asignado_id') or None,
            sucursal_nombre=data.get('sucursal_nombre', 'Tulancingo').strip(),
            version=1
        )

        db.session.add(equipo)
        db.session.flush()

        if 'especificaciones' in data and data['especificaciones']:
            for orden, spec in enumerate(data['especificaciones'], start=1):
                especificacion = EspecificacionEquipo(
                    equipo_id=equipo.id_activo,
                    nombre_especificacion=spec['nombre_especificacion'].strip(),
                    valor_especificacion=spec['valor_especificacion'].strip(),
                    orden=orden
                )
                db.session.add(especificacion)

        db.session.commit()

        return jsonify({
            'mensaje': 'Equipo creado exitosamente',
            'equipo': equipo.to_dict(include_specs=True, include_version=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@equipos_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('computo', 'puede_actualizar')
def update_equipo(id):
    """Actualizar equipo de cómputo con control de versiones"""
    user_id = get_jwt_identity()
    equipo = EquipoComputo.query.get(id)

    if not equipo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    # ── Validación de esquema ────────────────────────────────────
    try:
        validate_equipo(data, is_update=True)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    # ── Control de versiones ─────────────────────────────────────
    version_cliente = data.get('version')
    if version_cliente is not None:
        es_valida, version_actual = verificar_version(EquipoComputo, id, version_cliente)
        if not es_valida:
            return jsonify({
                'error': 'conflict',
                'mensaje': 'El registro fue modificado por otro usuario',
                'version_actual': version_actual,
                'datos_actuales': equipo.to_dict(include_specs=True, include_version=True)
            }), 409

    # Verificar número de serie único (si cambió)
    if data.get('numero_serie') and data['numero_serie'] != equipo.numero_serie:
        existe = EquipoComputo.query.filter_by(numero_serie=data['numero_serie']).first()
        if existe:
            return jsonify({
                'error': 'El número de serie ya está registrado',
                'campos': {'numero_serie': 'Este número de serie ya existe'}
            }), 409

    try:
        # Actualizar campos (solo si vienen en el payload)
        campo_map = {
            'tipo_activo_id':    lambda v: setattr(equipo, 'tipo_activo_id', v),
            'nombre_activo':     lambda v: setattr(equipo, 'nombre_activo', v.strip()),
            'marca':             lambda v: setattr(equipo, 'marca', v.strip() or None),
            'modelo':            lambda v: setattr(equipo, 'modelo', v.strip() or None),
            'numero_serie':      lambda v: setattr(equipo, 'numero_serie', v.strip() or None),
            'estado_id':         lambda v: setattr(equipo, 'estado_id', v),
            'observaciones':     lambda v: setattr(equipo, 'observaciones', v.strip() or None),
            'usuario_asignado_id': lambda v: setattr(equipo, 'usuario_asignado_id', v or None),
            'sucursal_nombre':   lambda v: setattr(equipo, 'sucursal_nombre', v.strip()),
        }

        for campo, setter in campo_map.items():
            if campo in data:
                setter(data[campo])

        # Actualizar especificaciones
        if 'especificaciones' in data:
            specs_existentes = EspecificacionEquipo.query.filter_by(equipo_id=id).all()

            specs_nuevas = {
                (spec['nombre_especificacion'].strip(), spec['valor_especificacion'].strip()): spec
                for spec in data['especificaciones']
            }
            specs_actuales = {
                (spec.nombre_especificacion, spec.valor_especificacion): spec
                for spec in specs_existentes
            }

            for key, spec in specs_actuales.items():
                if key not in specs_nuevas:
                    db.session.delete(spec)

            for orden, spec_data in enumerate(data['especificaciones'], start=1):
                key = (spec_data['nombre_especificacion'].strip(), spec_data['valor_especificacion'].strip())
                if key in specs_actuales:
                    spec_existente = specs_actuales[key]
                    if spec_existente.orden != orden:
                        spec_existente.orden = orden
                else:
                    nueva_spec = EspecificacionEquipo(
                        equipo_id=id,
                        nombre_especificacion=spec_data['nombre_especificacion'].strip(),
                        valor_especificacion=spec_data['valor_especificacion'].strip(),
                        orden=orden
                    )
                    db.session.add(nueva_spec)

        db.session.commit()
        liberar_bloqueo('equipos_computo', id, int(user_id))

        return jsonify({
            'mensaje': 'Equipo actualizado exitosamente',
            'equipo': equipo.to_dict(include_specs=True, include_version=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@equipos_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@lock_required('equipos_computo')
def delete_equipo(id, bloqueo):
    """Eliminar equipo con verificación de bloqueo."""

    equipo = EquipoComputo.query.get(id)
    if not equipo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    try:
        db.session.delete(equipo)
        db.session.delete(bloqueo)
        db.session.commit()
        return jsonify({'mensaje': 'Equipo eliminado exitosamente'}), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code