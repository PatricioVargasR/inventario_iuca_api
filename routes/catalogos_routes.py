from flask import Blueprint
from flask_jwt_extended import jwt_required
from models import CatArea, CatTipoActivo, CatEstado, CatTipoMobiliario
from utils.crud_catalogo import crud_catalogo
from utils.lock_required import lock_required
from utils.decorators import require_permission
from utils.validators import (
    validate_area,
    validate_estado,
    validate_tipo,
)

catalogos_bp = Blueprint('catalogos', __name__)

# ── Generar funciones CRUD para cada catálogo ─────────────────────────────────

_area   = crud_catalogo(CatArea,           validate_area,            'Área',               'cat_areas',
                        campo_busqueda='nombre_area',   clave_respuesta='areas',            campo_id='id_area',            campo_orden=CatArea.id_area)

_estado = crud_catalogo(CatEstado,         validate_estado,          'Estado',             'cat_estados',
                        campo_busqueda='nombre_estado', clave_respuesta='estados',          campo_id='id_estado',          campo_orden=CatEstado.id_estado)

_t_activo = crud_catalogo(CatTipoActivo,   validate_tipo,     'Tipo de activo',     'cat_tipos_activo',
                        campo_busqueda='nombre_tipo',   clave_respuesta='tipos_activo',     campo_id='id_tipo_activo',     campo_orden=CatTipoActivo.id_tipo_activo)

_t_mob  = crud_catalogo(CatTipoMobiliario, validate_tipo, 'Tipo de mobiliario', 'cat_tipos_mobiliario',
                        campo_busqueda='nombre_tipo',   clave_respuesta='tipos_mobiliario', campo_id='id_tipo_mobiliario', campo_orden=CatTipoMobiliario.id_tipo_mobiliario)

# Desempaquetar — ahora son 6 funciones
(get_areas_completo_fn,   get_areas_fn,    get_area_fn,  create_area_fn,    update_area_fn,    delete_area_fn)    = _area
(get_estados_completo_fn, get_estados_fn,  get_estado_fn, create_estado_fn, update_estado_fn,  delete_estado_fn)  = _estado
(get_t_activo_completo_fn,get_t_activo_fn, get_activo_fn, create_t_activo_fn,update_t_activo_fn,delete_t_activo_fn)= _t_activo
(get_t_mob_completo_fn,   get_t_mob_fn,   get_mob_fn,   create_t_mob_fn,   update_t_mob_fn,   delete_t_mob_fn)   = _t_mob

# ── ÁREAS ─────────────────────────────────────────────────────────────────────

@catalogos_bp.route('/areas-completo', methods=['GET'])
@jwt_required()
def get_areas_completo():
    return get_areas_completo_fn()

@catalogos_bp.route('/areas', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_areas():
    return get_areas_fn()

@catalogos_bp.route('/areas/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_area(id):
    return get_area_fn(id)

@catalogos_bp.route('/areas', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_area():
    return create_area_fn()

@catalogos_bp.route('/areas/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puede_actualizar')
def update_area(id):
    return update_area_fn(id)

@catalogos_bp.route('/areas/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
@lock_required('cat_areas')
def delete_area(id, bloqueo):
    return delete_area_fn(id, bloqueo)


# ── ESTADOS ───────────────────────────────────────────────────────────────────

@catalogos_bp.route('/estados-completo', methods=['GET'])
@jwt_required()
def get_estados_completo():
    return get_estados_completo_fn()

@catalogos_bp.route('/estados', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_estados():
    return get_estados_fn()

@catalogos_bp.route('/estados/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_estado(id):
    return get_estado_fn(id)


@catalogos_bp.route('/estados', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_estado():
    return create_estado_fn()


@catalogos_bp.route('/estados/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puede_actualizar')
def update_estado(id):
    return update_estado_fn(id)


@catalogos_bp.route('/estados/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
@lock_required('cat_estados')
def delete_estado(id, bloqueo):
    return delete_estado_fn(id, bloqueo)


# ── TIPOS DE ACTIVO ───────────────────────────────────────────────────────────

@catalogos_bp.route('/tipos-activo-completo', methods=['GET'])
@jwt_required()
def get_tipos_activos_completo():
    return get_t_activo_completo_fn()

@catalogos_bp.route('/tipos-activo', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_activos():
    return get_t_activo_fn()

@catalogos_bp.route('/activo/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_activo(id):
    return get_activo_fn(id)

@catalogos_bp.route('/tipos-activo', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_tipo_activo():
    return create_t_activo_fn()

@catalogos_bp.route('/tipos-activo/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puede_actualizar')
def update_tipo_activo(id):
    return update_t_activo_fn(id)

@catalogos_bp.route('/tipos-activo/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
@lock_required('cat_tipos_activo')
def delete_tipo_activo(id, bloqueo):
    return delete_t_activo_fn(id, bloqueo)


# ── TIPOS DE MOBILIARIO ───────────────────────────────────────────────────────

@catalogos_bp.route('/tipo-completo', methods=['GET'])
@jwt_required()
def get_mobiliario_completo():
    return get_t_mob_completo_fn()

@catalogos_bp.route('/tipos-mobiliario', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_mobiliarios():
    return get_t_mob_fn()

@catalogos_bp.route('/mobiliario/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('catalogos', 'puede_leer')
def get_catalogo(id):
    return get_mob_fn(id)


@catalogos_bp.route('/tipos-mobiliario', methods=['POST'])
@jwt_required()
@require_permission('catalogos', 'puede_crear')
def create_tipo_mobiliario():
    return create_t_mob_fn()


@catalogos_bp.route('/tipos-mobiliario/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('catalogos', 'puede_actualizar')
def update_tipo_mobiliario(id):
    return update_t_mob_fn(id)


@catalogos_bp.route('/tipos-mobiliario/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('catalogos', 'puede_eliminar')
@lock_required('cat_tipos_mobiliario')
def delete_tipo_mobiliario(id, bloqueo):
    return delete_t_mob_fn(id, bloqueo)