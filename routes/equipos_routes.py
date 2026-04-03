from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import BloqueoActivo, EquipoComputo, EspecificacionEquipo
from utils.decorators import require_permission
from utils.concurrency import (
    verificar_version,
    liberar_bloqueo
)

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

    # Validar campos obligatorios
    required_fields = ['nombre_activo', 'tipo_activo_id', 'estado_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es requerido'}), 400

    # Verificar número de serie único
    if data.get('numero_serie'):
        existe = EquipoComputo.query.filter_by(numero_serie=data['numero_serie']).first()
        if existe:
            return jsonify({'error': 'El número de serie ya existe'}), 400

    try:
        # Crear equipo
        equipo = EquipoComputo(
            tipo_activo_id=data['tipo_activo_id'],
            nombre_activo=data['nombre_activo'],
            marca=data.get('marca'),
            modelo=data.get('modelo'),
            numero_serie=data.get('numero_serie'),
            estado_id=data['estado_id'],
            observaciones=data.get('observaciones'),
            usuario_asignado_id=data.get('usuario_asignado_id') or None,
            sucursal_nombre=data.get('sucursal_nombre', 'Tulancingo'),
            creado_por=user_id,
            modificado_por=user_id,
            version=1  # Inicializar versión
        )

        db.session.add(equipo)
        db.session.flush()  # Para obtener el ID

        # Agregar especificaciones
        if 'especificaciones' in data and data['especificaciones']:
            for orden, spec in enumerate(data['especificaciones'], start=1):
                especificacion = EspecificacionEquipo(
                    equipo_id=equipo.id_activo,
                    nombre_especificacion=spec['nombre_especificacion'],
                    valor_especificacion=spec['valor_especificacion'],
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
        return jsonify({'error': str(e)}), 500


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
    version_cliente = data.get('version')

    # VERIFICACIÓN DE VERSIÓN (Control Optimista)
    if version_cliente is not None:
        es_valida, version_actual = verificar_version(EquipoComputo, id, version_cliente)

        if not es_valida:
            return jsonify({
                'error': 'conflict',
                'mensaje': 'El registro fue modificado por otro usuario',
                'version_actual': version_actual,
                'datos_actuales': equipo.to_dict(include_specs=True, include_version=True)
            }), 409  # 409 Conflict

    # Verificar número de serie único (si cambió)
    if data.get('numero_serie') and data['numero_serie'] != equipo.numero_serie:
        existe = EquipoComputo.query.filter_by(numero_serie=data['numero_serie']).first()
        if existe:
            return jsonify({'error': 'El número de serie ya existe'}), 400

    try:
        # Actualizar campos
        if 'tipo_activo_id' in data:
            equipo.tipo_activo_id = data['tipo_activo_id']
        if 'nombre_activo' in data:
            equipo.nombre_activo = data['nombre_activo']
        if 'marca' in data:
            equipo.marca = data['marca']
        if 'modelo' in data:
            equipo.modelo = data['modelo']
        if 'numero_serie' in data:
            equipo.numero_serie = data['numero_serie']
        if 'estado_id' in data:
            equipo.estado_id = data['estado_id']
        if 'observaciones' in data:
            equipo.observaciones = data['observaciones']
        if 'usuario_asignado_id' in data:
            equipo.usuario_asignado_id = data['usuario_asignado_id'] or None
        if 'sucursal_nombre' in data:
            equipo.sucursal_nombre = data['sucursal_nombre']

        equipo.modificado_por = user_id

        # Actualizar especificaciones si se enviaron
        if 'especificaciones' in data:
            specs_existentes = EspecificacionEquipo.query.filter_by(equipo_id=id).all()

            specs_nuevas = {
                (spec['nombre_especificacion'], spec['valor_especificacion']): spec
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
                key = (spec_data['nombre_especificacion'], spec_data['valor_especificacion'])

                if key in specs_actuales:
                    spec_existente = specs_actuales[key]
                    if spec_existente.orden != orden:
                        spec_existente.orden = orden
                else:
                    nueva_spec = EspecificacionEquipo(
                        equipo_id=id,
                        nombre_especificacion=spec_data['nombre_especificacion'],
                        valor_especificacion=spec_data['valor_especificacion'],
                        orden=orden
                    )
                    db.session.add(nueva_spec)

        db.session.commit()

        # Liberar bloqueo si existe
        liberar_bloqueo('equipos_computo', id, int(user_id))

        return jsonify({
            'mensaje': 'Equipo actualizado exitosamente',
            'equipo': equipo.to_dict(include_specs=True, include_version=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@equipos_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_equipo(id):
    """Eliminar equipo con verificación de bloqueo."""
    user_id = get_jwt_identity()

    equipo = EquipoComputo.query.get(id)
    if not equipo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    # VERIFICAR QUE EXISTE BLOQUEO DE ELIMINACIÓN DEL USUARIO
    bloqueo = BloqueoActivo.query.filter_by(
        tabla='equipos_computo',
        registro_id=id,
        usuario_id=user_id,
        tipo_bloqueo='eliminacion'
    ).first()

    if not bloqueo:
        # No hay bloqueo o es de otro usuario/tipo
        bloqueo_existente = BloqueoActivo.query.filter_by(
            tabla='equipos_computo',
            registro_id=id
        ).first()

        if bloqueo_existente:
            accion = 'editando' if bloqueo_existente.tipo_bloqueo == 'edicion' else 'eliminando'
            return jsonify({
                'error': 'locked_by_other',
                'mensaje': f'{bloqueo_existente.nombre_usuario} está {accion} este registro',
                'bloqueo': bloqueo_existente.to_dict()
            }), 409
        else:
            return jsonify({
                'error': 'no_lock',
                'mensaje': 'Debe adquirir bloqueo antes de eliminar'
            }), 403

    # Proceder con la eliminación
    try:
        db.session.delete(equipo)
        db.session.delete(bloqueo)  # Eliminar bloqueo también
        db.session.commit()

        return jsonify({'mensaje': 'Equipo eliminado exitosamente'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500