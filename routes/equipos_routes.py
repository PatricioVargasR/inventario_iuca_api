from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import EquipoComputo, EspecificacionEquipo
from utils.decorators import require_permission

equipos_bp = Blueprint('equipos', __name__)

@equipos_bp.route('/', methods=['GET'])
@jwt_required()
@require_permission('computo', 'puede_leer')
def get_equipos():
    """Listar todos los equipos con filtros opcionales"""
    # Parámetros de filtro
    tipo_activo_id = request.args.get('tipo_activo_id', type=int)
    estado_id = request.args.get('estado_id', type=int)
    usuario_id = request.args.get('usuario_id', type=int)
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Query base
    query = EquipoComputo.query
    
    # Aplicar filtros
    if tipo_activo_id:
        query = query.filter_by(tipo_activo_id=tipo_activo_id)
    if estado_id:
        query = query.filter_by(estado_id=estado_id)
    if usuario_id:
        query = query.filter_by(usuario_asignado_id=usuario_id)
    if search:
        query = query.filter(
            db.or_(
                EquipoComputo.nombre_activo.ilike(f'%{search}%'),
                EquipoComputo.marca.ilike(f'%{search}%'),
                EquipoComputo.numero_serie.ilike(f'%{search}%')
            )
        )
    
    # Ordenar por ID descendente
    query = query.order_by(EquipoComputo.id_activo.desc())
    
    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'equipos': [equipo.to_dict() for equipo in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@equipos_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('computo', 'puede_leer')
def get_equipo(id):
    """Obtener un equipo por ID con especificaciones"""
    equipo = EquipoComputo.query.get(id)
    
    if not equipo:
        return jsonify({'error': 'Equipo no encontrado'}), 404
    
    return jsonify(equipo.to_dict(include_specs=True)), 200


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
            usuario_asignado_id=data.get('usuario_asignado_id'),
            sucursal_nombre=data.get('sucursal_nombre', 'Tulancingo'),
            creado_por=user_id,
            modificado_por=user_id
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
            'equipo': equipo.to_dict(include_specs=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@equipos_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('computo', 'puede_actualizar')
def update_equipo(id):
    """Actualizar equipo de cómputo"""
    user_id = get_jwt_identity()
    equipo = EquipoComputo.query.get(id)
    
    if not equipo:
        return jsonify({'error': 'Equipo no encontrado'}), 404
    
    data = request.get_json()
    
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
            equipo.usuario_asignado_id = data['usuario_asignado_id']
        
        equipo.modificado_por = user_id
        
        # Actualizar especificaciones si se enviaron
        if 'especificaciones' in data:
            # Eliminar especificaciones anteriores
            EspecificacionEquipo.query.filter_by(equipo_id=id).delete()
            
            # Agregar nuevas
            for orden, spec in enumerate(data['especificaciones'], start=1):
                especificacion = EspecificacionEquipo(
                    equipo_id=id,
                    nombre_especificacion=spec['nombre_especificacion'],
                    valor_especificacion=spec['valor_especificacion'],
                    orden=orden
                )
                db.session.add(especificacion)
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Equipo actualizado exitosamente',
            'equipo': equipo.to_dict(include_specs=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@equipos_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('computo', 'puede_eliminar')
def delete_equipo(id):
    """Eliminar equipo de cómputo"""
    equipo = EquipoComputo.query.get(id)
    
    if not equipo:
        return jsonify({'error': 'Equipo no encontrado'}), 404
    
    try:
        db.session.delete(equipo)  # CASCADE eliminará especificaciones
        db.session.commit()
        
        return jsonify({'mensaje': 'Equipo eliminado exitosamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500