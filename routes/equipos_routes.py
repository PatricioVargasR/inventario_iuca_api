from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import BloqueoActivo, EquipoComputo, EspecificacionEquipo, EquipoResponsable, Usuario
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
    """Obtener un equipo por ID con especificaciones, responsables y estado de bloqueo"""
    equipo = EquipoComputo.query.get(id)

    if not equipo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    return jsonify(equipo.to_dict(include_specs=True, include_responsables=True, include_version=True)), 200


@equipos_bp.route('/', methods=['POST'])
@jwt_required()
@require_permission('computo', 'puede_crear')
def create_equipo():
    """Crear nuevo equipo de cómputo con múltiples responsables"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    try:
        validate_equipo(data, is_update=False)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

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
            sucursal_nombre=data.get('sucursal_nombre', 'Tulancingo').strip(),
            version=1
        )

        db.session.add(equipo)
        db.session.flush()

        # Agregar especificaciones
        if 'especificaciones' in data and data['especificaciones']:
            for orden, spec in enumerate(data['especificaciones'], start=1):
                especificacion = EspecificacionEquipo(
                    equipo_id=equipo.id_activo,
                    nombre_especificacion=spec['nombre_especificacion'].strip(),
                    valor_especificacion=spec['valor_especificacion'].strip(),
                    orden=orden
                )
                db.session.add(especificacion)

        # Agregar responsables (lista de IDs)
        responsables_ids = data.get('responsables_ids', [])
        for usuario_id in responsables_ids:
            # Verificar que el usuario existe
            usuario = Usuario.query.get(usuario_id)
            if usuario:
                responsable = EquipoResponsable(
                    equipo_id=equipo.id_activo,
                    usuario_id=usuario_id
                )
                db.session.add(responsable)

        db.session.commit()

        return jsonify({
            'mensaje': 'Equipo creado exitosamente',
            'equipo': equipo.to_dict(include_specs=True, include_responsables=True, include_version=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@equipos_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('computo', 'puede_actualizar')
def update_equipo(id):
    """Actualizar equipo de cómputo con control de versiones y diff de responsables"""
    user_id = get_jwt_identity()
    equipo = EquipoComputo.query.get(id)

    if not equipo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    try:
        validate_equipo(data, is_update=True)
    except ValidationError as e:
        return jsonify({'error': e.message, 'campos': e.fields}), 422

    version_cliente = data.get('version')
    if version_cliente is not None:
        es_valida, version_actual = verificar_version(EquipoComputo, id, version_cliente)
        if not es_valida:
            return jsonify({
                'error': 'conflict',
                'mensaje': 'El registro fue modificado por otro usuario',
                'version_actual': version_actual,
                'datos_actuales': equipo.to_dict(include_specs=True, include_responsables=True, include_version=True)
            }), 409

    if data.get('numero_serie') and data['numero_serie'] != equipo.numero_serie:
        existe = EquipoComputo.query.filter_by(numero_serie=data['numero_serie']).first()
        if existe:
            return jsonify({
                'error': 'El número de serie ya está registrado',
                'campos': {'numero_serie': 'Este número de serie ya existe'}
            }), 409

    try:
        campo_map = {
            'tipo_activo_id':    lambda v: setattr(equipo, 'tipo_activo_id', v),
            'nombre_activo':     lambda v: setattr(equipo, 'nombre_activo', v.strip()),
            'marca':             lambda v: setattr(equipo, 'marca', v.strip() or None),
            'modelo':            lambda v: setattr(equipo, 'modelo', v.strip() or None),
            'numero_serie':      lambda v: setattr(equipo, 'numero_serie', v.strip() or None),
            'estado_id':         lambda v: setattr(equipo, 'estado_id', v),
            'observaciones':     lambda v: setattr(equipo, 'observaciones', v.strip() or None),
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

        # Diff de responsables: solo insertar/eliminar los que cambiaron
        if 'responsables_ids' in data:
            nuevos_ids = set(int(i) for i in data['responsables_ids'])
            responsables_actuales = EquipoResponsable.query.filter_by(equipo_id=id).all()
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
                    nuevo_resp = EquipoResponsable(
                        equipo_id=id,
                        usuario_id=usuario_id
                    )
                    db.session.add(nuevo_resp)

        db.session.commit()
        liberar_bloqueo('equipos_computo', id, int(user_id))

        return jsonify({
            'mensaje': 'Equipo actualizado exitosamente',
            'equipo': equipo.to_dict(include_specs=True, include_responsables=True, include_version=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        message, code = handle_db_error(e)
        return jsonify({'error': message}), code


@equipos_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@lock_required('equipos_computo')
@require_permission('equipos_computo', 'puede_eliminar')
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
        message, code = handle_db_error(e, tabla='equipos_computo')
        return jsonify({'error': message}), code