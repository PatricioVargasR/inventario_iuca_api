# ============================================
# utils/constants.py — Valores estáticos centralizados
# Sistema de Inventario IUCA
# ============================================


# ── Módulos del sistema ───────────────────────────────────────────────────────

MODULOS_DISPONIBLES = [
    'computo',
    'mobiliario',
    'responsable',
    'catalogos',
    'historial',
    'acceso',
]


# ── Historial: tablas y campos ────────────────────────────────────────────────

TABLAS_VISIBLES = {
    'equipos_computo',
    'mobiliario',
    'usuario',
    'acceso',
    'cat_areas',
    'cat_estados',
    'cat_tipos_activo',
    'cat_tipos_mobiliario',
    'equipos_responsables',      # asignación/desasignación de responsables en equipos
    'mobiliario_responsables',   # asignación/desasignación de responsables en mobiliario
}

CAMPOS_IGNORADOS = {
    'ultimo_acceso',
    'fecha_modificacion',
    'modificado_por',
    'version',
    'token_recuperacion',
    'token_expiracion',
    'intentos_fallidos',
    'bloqueado_hasta',
    # Campos de sesión
    'ip_sesion',
    'ip_ultimo_acceso',
    'user_agent',
    'sesion_activa',
    'refresh_token',
    'ultimo_login',
    'contrasena_hash',
}


# ── Historial: aliases de búsqueda ───────────────────────────────────────────

# Términos que el usuario puede escribir → nombre real de la tabla en BD
# None significa "coincide con todas las cat_*" (catalogo/catálogo)
TABLA_ALIASES: dict[str, str | None] = {
    'computo':                'equipos_computo',
    'cómputo':                'equipos_computo',
    'equipo':                 'equipos_computo',
    'mobiliario':             'mobiliario',
    'mueble':                 'mobiliario',
    'acceso':                 'acceso',
    'usuario':                'usuario',
    'responsable':            'usuario',
    'área':                   'cat_areas',
    'area':                   'cat_areas',
    'estado':                 'cat_estados',
    'tipo de activo':         'cat_tipos_activo',
    'tipos de activo':        'cat_tipos_activo',
    'tipo activo':            'cat_tipos_activo',
    'tipo de mobiliario':     'cat_tipos_mobiliario',
    'tipos de mobiliario':    'cat_tipos_mobiliario',
    'tipo mobiliario':        'cat_tipos_mobiliario',
    'catálogo':               None,
    'catalogo':               None,
    'asignacion':             'equipos_responsables',
    'asignación':             'equipos_responsables',
    'responsable equipo':     'equipos_responsables',
    'responsable mueble':     'mobiliario_responsables',
}

# Términos que el usuario puede escribir → operación real en BD
OPERACION_ALIASES: dict[str, str] = {
    'creacion':    'INSERT',
    'creación':    'INSERT',
    'crear':       'INSERT',
    'nuevo':       'INSERT',
    'insert':      'INSERT',
    'edicion':     'UPDATE',
    'edición':     'UPDATE',
    'editar':      'UPDATE',
    'actualizar':  'UPDATE',
    'update':      'UPDATE',
    'eliminacion': 'DELETE',
    'eliminación': 'DELETE',
    'eliminar':    'DELETE',
    'borrar':      'DELETE',
    'delete':      'DELETE',
}

# Nombres legibles de campos técnicos (usados en historial y modelos)
CAMPOS_LEGIBLES: dict[str, str] = {
    'estado_id':                'Estado',
    'usuario_asignado_id':      'Usuario Asignado',
    'tipo_activo_id':           'Tipo de Activo',
    'tipo_mobiliario_id':       'Tipo de Mobiliario',
    'area_id':                  'Área',
    'nombre_activo':            'Nombre',
    'marca':                    'Marca',
    'modelo':                   'Modelo',
    'numero_serie':             'Número de Serie',
    'observaciones':            'Observaciones',
    'caracteristicas':          'Características',
    'color':                    'Color',
    'nombre_usuario':           'Nombre',
    'correo_electronico':       'Correo Electrónico',
    'puesto':                   'Puesto',
    'numero_nomina':            'Número de Nómina',
    'equipo_id':                'Equipo',
    'mueble_id':                'Mueble',
    'usuario_id':               'Responsable',
    'fecha_asignacion':         'Fecha de asignación',
}


# ── Validators: mensajes de error por FK ─────────────────────────────────────

MENSAJES_FK: dict[str, str] = {
    'usuario':
        'No se puede eliminar este responsable porque tiene equipos o mobiliario asignado.',
    'acceso':
        'No se puede eliminar este acceso porque tiene permisos u otras relaciones activas.',
    'cat_areas':
        'No se puede eliminar esta área porque hay usuarios o accesos asociados a ella.',
    'cat_estados':
        'No se puede eliminar este estado porque hay equipos o mobiliario que lo usan.',
    'cat_tipos_activo':
        'No se puede eliminar este tipo porque hay equipos que lo usan.',
    'cat_tipos_mobiliario':
        'No se puede eliminar este tipo porque hay mobiliario que lo usa.',
}


# ── Catálogos: metadatos de modelos ──────────────────────────────────────────

# Campo que actúa como nombre único por modelo
CATALOGO_CAMPO_NOMBRE: dict[str, str] = {
    'CatArea':           'nombre_area',
    'CatEstado':         'nombre_estado',
    'CatTipoActivo':     'nombre_tipo',
    'CatTipoMobiliario': 'nombre_tipo',
}

# Campos editables en create/update por modelo
CATALOGO_CAMPOS_EDITABLES: dict[str, list[str]] = {
    'CatArea': [
        'nombre_area',
        'descripcion',
        'activo',
    ],
    'CatEstado': [
        'nombre_estado',
        'descripcion',
        'activo',
        'color_hex',
    ],
    'CatTipoActivo': [
        'nombre_tipo',
        'descripcion',
        'activo',
    ],
    'CatTipoMobiliario': [
        'nombre_tipo',
        'descripcion',
        'activo',
    ],
}

# Mapeo de las tablas
TIPO_DE_REGISTRO: dict[str, str] = {
    'computo':                 'equipos_computo',
    'mobiliario':              'mobiliario',
    'acceso':                  'acceso',
    'usuario':                 'usuario',
    'cat_areas':               'cat_areas',
    'cat_estados':             'cat_estados',
    'cat_tipos_activo':        'cat_tipos_activo',
    'cat_tipos_mobiliario':    'cat_tipos_mobiliario',
    'equipos_responsables':    'equipos_responsables',
    'mobiliario_responsables': 'mobiliario_responsables',
}

# Mapeo de los tipos de movimiento
OPERACION_MOVIMIENTO: dict[str, str] = {
    'creacion':    'INSERT',
    'edicion':     'UPDATE',
    'eliminacion': 'DELETE'
}