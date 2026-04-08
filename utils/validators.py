"""
utils/validators.py — Validaciones centralizadas para la API

Uso en una ruta:
    from utils.validators import validate_equipo, validate_mobiliario, ValidationError

    @equipos_bp.route('/', methods=['POST'])
    def create_equipo():
        data = request.get_json()
        try:
            validated = validate_equipo(data)
        except ValidationError as e:
            return jsonify({'error': e.message, 'campos': e.fields}), 422
        ...
"""

import re

class ValidationError(Exception):
    """Error de validación con mensaje legible y campos afectados."""
    def __init__(self, message: str, fields: dict = None):
        super().__init__(message)
        self.message = message
        self.fields = fields or {}  # { nombre_campo: "mensaje del campo" }


# ── Helpers ─────────────────────────────────────────────────────────────────

def _require(data: dict, field: str, label: str) -> any:
    """Verifica que un campo exista y no sea None ni cadena vacía."""
    value = data.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(
            f'El campo "{label}" es obligatorio',
            {field: f'"{label}" es requerido'}
        )
    return value


def _max_len(value: str, length: int, field: str, label: str) -> str:
    if value and len(str(value)) > length:
        raise ValidationError(
            f'"{label}" no puede superar {length} caracteres',
            {field: f'Máximo {length} caracteres'}
        )
    return value


def _valid_hex_color(value: str, field: str = 'color_hex') -> str:
    """Valida que sea un color HEX válido (#RRGGBB)."""
    if value and not re.match(r'^#[0-9A-Fa-f]{6}$', value):
        raise ValidationError(
            'El color debe tener formato HEX válido (Ej: #FF5733)',
            {field: 'Formato HEX inválido'}
        )
    return value


def _positive_int(value, field: str, label: str) -> int:
    """Verifica que sea entero positivo."""
    try:
        v = int(value)
        if v <= 0:
            raise ValueError
        return v
    except (TypeError, ValueError):
        raise ValidationError(
            f'"{label}" debe ser un número válido',
            {field: 'Debe ser un número entero positivo'}
        )


# ── Validadores por módulo ───────────────────────────────────────────────────

def validate_equipo(data: dict, is_update: bool = False) -> dict:
    """
    Valida los datos de un equipo de cómputo.
    Retorna el diccionario limpio y validado.
    """
    errors = {}

    # Campos obligatorios (solo en creación)
    if not is_update:
        for field, label in [
            ('nombre_activo', 'Nombre del activo'),
            ('tipo_activo_id', 'Tipo de activo'),
            ('estado_id', 'Estado'),
        ]:
            if not data.get(field):
                errors[field] = f'"{label}" es obligatorio'

    if errors:
        raise ValidationError('Hay campos obligatorios sin completar', errors)

    # Longitudes máximas
    string_limits = {
        'nombre_activo':  ('Nombre del activo',  50),
        'marca':          ('Marca',               50),
        'modelo':         ('Modelo',              50),
        'numero_serie':   ('Número de serie',     50),
        'sucursal_nombre':('Sucursal',            50),
        'observaciones':  ('Observaciones',       500),
    }

    for field, (label, max_length) in string_limits.items():
        val = data.get(field)
        if val:
            try:
                _max_len(str(val), max_length, field, label)
            except ValidationError as e:
                errors.update(e.fields)

    if errors:
        raise ValidationError('Algunos campos superan la longitud permitida', errors)

    # IDs deben ser enteros positivos si se envían
    for field, label in [('tipo_activo_id', 'Tipo de activo'), ('estado_id', 'Estado'), ('usuario_asignado_id', 'Responsable')]:
        val = data.get(field)
        if val is not None and val != '':
            try:
                _positive_int(val, field, label)
            except ValidationError as e:
                errors.update(e.fields)

    if errors:
        raise ValidationError('Hay datos inválidos en el formulario', errors)

    # Especificaciones
    specs = data.get('especificaciones', [])
    if specs and not isinstance(specs, list):
        raise ValidationError('Las especificaciones deben ser una lista', {'especificaciones': 'Formato inválido'})

    for i, spec in enumerate(specs or []):
        if not spec.get('nombre_especificacion') or not str(spec['nombre_especificacion']).strip():
            errors[f'especificaciones[{i}].nombre'] = 'El nombre de la especificación es obligatorio'
        if not spec.get('valor_especificacion') or not str(spec['valor_especificacion']).strip():
            errors[f'especificaciones[{i}].valor'] = 'El valor de la especificación es obligatorio'

    if errors:
        raise ValidationError('Revisa las especificaciones del equipo', errors)

    return data


def validate_mobiliario(data: dict, is_update: bool = False) -> dict:
    errors = {}

    if not is_update:
        for field, label in [
            ('tipo_mobiliario_id', 'Tipo de mobiliario'),
            ('estado_id', 'Estado'),
        ]:
            if not data.get(field):
                errors[field] = f'"{label}" es obligatorio'

    if errors:
        raise ValidationError('Hay campos obligatorios sin completar', errors)

    string_limits = {
        'marca':          ('Marca',          50),
        'modelo':         ('Modelo',         50),
        'color':          ('Color',          20),
        'caracteristicas':('Características', 500),
        'observaciones':  ('Observaciones',  500),
        'sucursal_nombre':('Sucursal',       50),
    }

    for field, (label, max_length) in string_limits.items():
        val = data.get(field)
        if val:
            try:
                _max_len(str(val), max_length, field, label)
            except ValidationError as e:
                errors.update(e.fields)

    if errors:
        raise ValidationError('Algunos campos superan la longitud permitida', errors)

    return data


def validate_responsable(data: dict, is_update: bool = False) -> dict:
    errors = {}

    if not is_update and not data.get('nombre_usuario'):
        errors['nombre_usuario'] = '"Nombre" es obligatorio'

    if errors:
        raise ValidationError('Hay campos obligatorios sin completar', errors)

    string_limits = {
        'nombre_usuario': ('Nombre completo', 100),
        'numero_nomina':  ('Número de nómina', 10),
        'puesto':         ('Puesto',           80),
    }

    for field, (label, max_length) in string_limits.items():
        val = data.get(field)
        if val:
            try:
                _max_len(str(val), max_length, field, label)
            except ValidationError as e:
                errors.update(e.fields)

    if errors:
        raise ValidationError('Algunos campos superan la longitud permitida', errors)

    # Número de nómina: solo dígitos si se provee
    nomina = data.get('numero_nomina')
    if nomina and not str(nomina).isdigit():
        raise ValidationError(
            'El número de nómina solo puede contener dígitos',
            {'numero_nomina': 'Solo se permiten números'}
        )

    return data


def validate_acceso(data: dict, is_update: bool = False) -> dict:
    errors = {}

    if not is_update:
        for field, label in [
            ('nombre_usuario', 'Nombre completo'),
            ('correo_electronico', 'Correo electrónico'),
            ('password', 'Contraseña'),
        ]:
            if not data.get(field):
                errors[field] = f'"{label}" es obligatorio'

    if errors:
        raise ValidationError('Hay campos obligatorios sin completar', errors)

    # Validar formato de correo
    correo = data.get('correo_electronico')
    if correo and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', correo):
        raise ValidationError(
            'El correo electrónico no tiene un formato válido',
            {'correo_electronico': 'Formato de correo inválido'}
        )

    # Contraseña: longitud exacta de 10
    password = data.get('password')
    if password and len(password) != 10:
        raise ValidationError(
            'La contraseña debe tener exactamente 10 caracteres',
            {'password': 'Debe tener 10 caracteres'}
        )

    string_limits = {
        'nombre_usuario': ('Nombre completo', 100),
    }

    for field, (label, max_length) in string_limits.items():
        val = data.get(field)
        if val:
            try:
                _max_len(str(val), max_length, field, label)
            except ValidationError as e:
                errors.update(e.fields)

    if errors:
        raise ValidationError('Algunos campos superan la longitud permitida', errors)

    return data


def validate_area(data: dict, is_update: bool = False) -> dict:
    errors = {}

    if not is_update and not data.get('nombre_area'):
        errors['nombre_area'] = '"Nombre del área" es obligatorio'

    if errors:
        raise ValidationError('Hay campos obligatorios sin completar', errors)

    val = data.get('nombre_area')
    if val:
        _max_len(str(val), 50, 'nombre_area', 'Nombre del área')

    return data


def validate_estado(data: dict, is_update: bool = False) -> dict:
    errors = {}

    if not is_update and not data.get('nombre_estado'):
        errors['nombre_estado'] = '"Nombre del estado" es obligatorio'

    if errors:
        raise ValidationError('Hay campos obligatorios sin completar', errors)

    val = data.get('nombre_estado')
    if val:
        _max_len(str(val), 20, 'nombre_estado', 'Nombre del estado')

    color = data.get('color_hex')
    if color:
        _valid_hex_color(color)

    return data


def validate_tipo(data: dict, is_update: bool = False) -> dict:
    errors = {}

    if not is_update and not data.get('nombre_tipo'):
        errors['nombre_tipo'] = '"Nombre del tipo" es obligatorio'

    if errors:
        raise ValidationError('Hay campos obligatorios sin completar', errors)

    val = data.get('nombre_tipo')
    if val:
        _max_len(str(val), 30, 'nombre_tipo', 'Nombre del tipo')

    return data

# ── Error handler de SQLAlchemy ──────────────────────────────────────────────

def handle_db_error(e: Exception, tabla: str = None) -> tuple:
    """
    Convierte excepciones de SQLAlchemy/psycopg2 en respuestas JSON legibles.
    Retorna (mensaje, código_http).

    Uso:
        except Exception as e:
            message, code = handle_db_error(e)
            return jsonify({'error': message}), code
    """

    # Intentar obtener código SQLSTATE
    error_code = getattr(getattr(e, 'orig', None), 'pgcode', None)

    print(type(error_code))

    # FALLBACK (por si no es IntegrityError)
    error_str = str(e).lower()

    if  error_code == '23505':
        # Intentar extraer el campo duplicado
        match = re.search(r'key \((.+?)\)', str(e))
        if match:
            campo = match.group(1).replace('_', ' ')
            return f'Ya existe un registro con ese {campo}', 409
        return 'Ya existe un registro con esos datos', 409

    if error_code == '23502':
        match = re.search(r'column "(.+?)"', str(e))
        if match:
            campo = match.group(1).replace('_', ' ')
            return f'El campo "{campo}" es obligatorio', 422
        return 'Hay campos obligatorios sin completar', 422

    if error_code == '23503':
        MENSAJES_FK = {
            'usuario':     'No se puede eliminar este responsable porque tiene equipos o mobiliario asignado.',
            'acceso':      'No se puede eliminar este acceso porque tiene permisos u otras relaciones activas.',
            'cat_areas':   'No se puede eliminar esta área porque hay usuarios o accesos asociados a ella.',
            'cat_estados': 'No se puede eliminar este estado porque hay equipos o mobiliario que lo usan.',
            'cat_tipos_activo':     'No se puede eliminar este tipo porque hay equipos que lo usan.',
            'cat_tipos_mobiliario': 'No se puede eliminar este tipo porque hay mobiliario que lo usa.',
        }
        mensaje = MENSAJES_FK.get(tabla, 'Este registro está relacionado con otros datos y no puede eliminarse.')
        return mensaje, 409

    if error_code == '23514':
        return 'Los datos no cumplen con las reglas de validación del sistema', 422

    if 'connection' in error_str or 'operational' in error_str:
        return 'Error de conexión con la base de datos. Intenta de nuevo.', 503

    # Fallback: no exponer detalles internos
    return 'Error interno del servidor. Intenta de nuevo.', 500