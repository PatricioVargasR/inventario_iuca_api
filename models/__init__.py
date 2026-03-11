from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

# ============================================
# CATÁLOGOS
# ============================================

class CatArea(db.Model):
    __tablename__ = 'cat_areas'

    id_area = db.Column(db.Integer, primary_key=True)
    nombre_area = db.Column(db.String(50), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id_area': self.id_area,
            'nombre_area': self.nombre_area,
            'activo': self.activo,
            'descripcion': self.descripcion
        }


class CatTipoActivo(db.Model):
    __tablename__ = 'cat_tipos_activo'

    id_tipo_activo = db.Column(db.Integer, primary_key=True)
    nombre_tipo = db.Column(db.String(30), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id_tipo_activo': self.id_tipo_activo,
            'nombre_tipo': self.nombre_tipo,
            'activo': self.activo,
            'descripcion': self.descripcion
        }


class CatEstado(db.Model):
    __tablename__ = 'cat_estados'

    id_estado = db.Column(db.Integer, primary_key=True)
    nombre_estado = db.Column(db.String(20), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False)
    descripcion = db.Column(db.Text)
    color_hex = db.Column(db.String(7))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id_estado': self.id_estado,
            'nombre_estado': self.nombre_estado,
            'activo': self.activo,
            'descripcion': self.descripcion,
            'color_hex': self.color_hex
        }


class CatTipoMobiliario(db.Model):
    __tablename__ = 'cat_tipos_mobiliario'

    id_tipo_mobiliario = db.Column(db.Integer, primary_key=True)
    nombre_tipo = db.Column(db.String(30), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id_tipo_mobiliario': self.id_tipo_mobiliario,
            'nombre_tipo': self.nombre_tipo,
            'activo': self.activo,
            'descripcion': self.descripcion
        }

# ============================================
# USUARIOS Y ACCESOS
# ============================================

class Usuario(db.Model):
    __tablename__ = 'usuario'

    id_usuario = db.Column(db.Integer, primary_key=True)
    numero_nomina = db.Column(db.String(10), unique=True)
    nombre_usuario = db.Column(db.String(100), nullable=False)
    puesto = db.Column(db.String(80))
    area_id = db.Column(db.Integer, db.ForeignKey('cat_areas.id_area'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    area = db.relationship('CatArea', backref='usuarios')

    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'numero_nomina': self.numero_nomina,
            'nombre_usuario': self.nombre_usuario,
            'puesto': self.puesto,
            'area_id': self.area_id,
            'area': self.area.nombre_area if self.area else None
        }


class Acceso(db.Model):
    __tablename__ = 'acceso'

    id_acceso = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(100), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('cat_areas.id_area'))
    correo_electronico = db.Column(db.String(100), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(255), nullable=False)
    ultimo_acceso = db.Column(db.DateTime)
    fecha_registro = db.Column(db.Date, default=datetime.utcnow().date)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    area = db.relationship('CatArea', backref='accesos')
    permisos = db.relationship('Permiso', backref='acceso', cascade='all, delete-orphan')

    def to_dict(self, include_password=False):
        data = {
            'id_acceso': self.id_acceso,
            'nombre_usuario': self.nombre_usuario,
            'correo_electronico': self.correo_electronico,
            'area_id': self.area_id,
            'area': self.area.nombre_area if self.area else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }
        if include_password:
            data['contrasena_hash'] = self.contrasena_hash
        return data

    def permisos_dict(self):
        """Devuelve los permisos del usuario indexados por módulo."""
        return {p.modulo: p.to_dict() for p in self.permisos}


class Permiso(db.Model):
    __tablename__ = 'permisos'

    id_permiso = db.Column(db.Integer, primary_key=True)
    acceso_id = db.Column(db.Integer, db.ForeignKey('acceso.id_acceso'), nullable=False)
    modulo = db.Column(db.String(50), nullable=False)
    puede_crear = db.Column(db.Boolean, default=False)
    puede_leer = db.Column(db.Boolean, default=True)
    puede_actualizar = db.Column(db.Boolean, default=False)
    puede_eliminar = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('acceso_id', 'modulo', name='uq_acceso_modulo'),
    )


    def to_dict(self):
        return {
            'id_permiso': self.id_permiso,
            'acceso_id': self.acceso_id,
            'modulo': self.modulo,
            'puede_crear': self.puede_crear,
            'puede_leer': self.puede_leer,
            'puede_actualizar': self.puede_actualizar,
            'puede_eliminar': self.puede_eliminar
        }

# ============================================
# INVENTARIO
# ============================================

class EquipoComputo(db.Model):
    __tablename__ = 'equipos_computo'

    id_activo = db.Column(db.Integer, primary_key=True)
    tipo_activo_id = db.Column(db.Integer, db.ForeignKey('cat_tipos_activo.id_tipo_activo'))
    nombre_activo = db.Column(db.String(50), nullable=False)
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    numero_serie = db.Column(db.String(50), unique=True)
    estado_id = db.Column(db.Integer, db.ForeignKey('cat_estados.id_estado'))
    fecha_registro = db.Column(db.Date, default=datetime.utcnow().date)
    observaciones = db.Column(db.Text)
    usuario_asignado_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))
    sucursal_nombre = db.Column(db.String(50), default='Tulancingo')
    creado_por = db.Column(db.Integer, db.ForeignKey('acceso.id_acceso'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    modificado_por = db.Column(db.Integer, db.ForeignKey('acceso.id_acceso'))
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    tipo_activo = db.relationship('CatTipoActivo')
    estado = db.relationship('CatEstado')
    usuario_asignado = db.relationship('Usuario')
    especificaciones = db.relationship('EspecificacionEquipo', backref='equipo', cascade='all, delete-orphan')

    def to_dict(self, include_specs=False):
        data = {
            'id_activo': self.id_activo,
            'tipo_activo_id': self.tipo_activo_id,
            'tipo_activo': self.tipo_activo.nombre_tipo if self.tipo_activo else None,
            'nombre_activo': self.nombre_activo,
            'marca': self.marca,
            'modelo': self.modelo,
            'numero_serie': self.numero_serie,
            'estado_id': self.estado_id,
            'estado': self.estado.nombre_estado if self.estado else None,
            'color_estado': self.estado.color_hex if self.estado else None,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'observaciones': self.observaciones,
            'usuario_asignado_id': self.usuario_asignado_id,
            'responsable': self.usuario_asignado.nombre_usuario if self.usuario_asignado else None,
            'sucursal_nombre': self.sucursal_nombre,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None
        }
        if include_specs:
            data['especificaciones'] = [spec.to_dict() for spec in self.especificaciones]
        return data


class EspecificacionEquipo(db.Model):
    __tablename__ = 'especificaciones_equipo'

    id_especificacion = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos_computo.id_activo', ondelete='CASCADE'))
    nombre_especificacion = db.Column(db.String(100), nullable=False)
    valor_especificacion = db.Column(db.String(100), nullable=False)
    orden = db.Column(db.Integer, default=1)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id_especificacion': self.id_especificacion,
            'equipo_id': self.equipo_id,
            'nombre_especificacion': self.nombre_especificacion,
            'valor_especificacion': self.valor_especificacion,
            'orden': self.orden
        }


class Mobiliario(db.Model):
    __tablename__ = 'mobiliario'

    id_mueble = db.Column(db.Integer, primary_key=True)
    tipo_mobiliario_id = db.Column(db.Integer, db.ForeignKey('cat_tipos_mobiliario.id_tipo_mobiliario'))
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    color = db.Column(db.String(20))
    caracteristicas = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    estado_id = db.Column(db.Integer, db.ForeignKey('cat_estados.id_estado'))
    usuario_asignado_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))
    fecha_asignacion = db.Column(db.Date)
    sucursal_nombre = db.Column(db.String(50), default='Tulancingo')
    creado_por = db.Column(db.Integer, db.ForeignKey('acceso.id_acceso'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    modificado_por = db.Column(db.Integer, db.ForeignKey('acceso.id_acceso'))
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    tipo_mobiliario = db.relationship('CatTipoMobiliario')
    estado = db.relationship('CatEstado')
    usuario_asignado = db.relationship('Usuario')

    def to_dict(self):
        return {
            'id_mueble': self.id_mueble,
            'tipo_mobiliario_id': self.tipo_mobiliario_id,
            'tipo_mobiliario': self.tipo_mobiliario.nombre_tipo if self.tipo_mobiliario else None,
            'marca': self.marca,
            'modelo': self.modelo,
            'color': self.color,
            'caracteristicas': self.caracteristicas,
            'observaciones': self.observaciones,
            'estado_id': self.estado_id,
            'estado': self.estado.nombre_estado if self.estado else None,
            'color_estado': self.estado.color_hex if self.estado else None,
            'usuario_asignado_id': self.usuario_asignado_id,
            'responsable': self.usuario_asignado.nombre_usuario if self.usuario_asignado else None,
            'fecha_asignacion': self.fecha_asignacion.isoformat() if self.fecha_asignacion else None,
            'sucursal_nombre': self.sucursal_nombre,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None
        }

# ============================================
# VISTAS
# ============================================

class VistaEquiposCompleta(db.Model):
    """
    Vista completa de equipos con información relacionada
    Corresponde a: vista_equipos_completa
    """
    __tablename__ = 'vista_equipos_completa'
    __table_args__ = {'info': {'is_view': True}}

    id_activo = db.Column(db.Integer, primary_key=True)
    nombre_activo = db.Column(db.String(50))
    tipo_activo = db.Column(db.String(30))
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    numero_serie = db.Column(db.String(50))
    estado = db.Column(db.String(20))
    color_estado = db.Column(db.String(7))
    fecha_registro = db.Column(db.Date)
    observaciones = db.Column(db.Text)
    sucursal = db.Column(db.String(50))
    responsable = db.Column(db.String(100))
    numero_nomina = db.Column(db.String(10))
    puesto = db.Column(db.String(80))
    area = db.Column(db.String(50))
    creado_por = db.Column(db.String(100))
    fecha_creacion = db.Column(db.DateTime)
    modificado_por = db.Column(db.String(100))
    fecha_modificacion = db.Column(db.DateTime)
    especificaciones = db.Column(db.Text)

    def to_dict(self):
        return {
            'id_activo': self.id_activo,
            'nombre_activo': self.nombre_activo,
            'tipo_activo': self.tipo_activo,
            'marca': self.marca,
            'modelo': self.modelo,
            'numero_serie': self.numero_serie,
            'estado': self.estado,
            'color_estado': self.color_estado,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'observaciones': self.observaciones,
            'sucursal': self.sucursal,
            'responsable': self.responsable,
            'numero_nomina': self.numero_nomina,
            'puesto': self.puesto,
            'area': self.area,
            'creado_por': self.creado_por,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'modificado_por': self.modificado_por,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None,
            'especificaciones': self.especificaciones
        }


class VistaMobiliarioCompleta(db.Model):
    """
    Vista completa de mobiliario con información relacionada
    Corresponde a: vista_mobiliario_completa
    """
    __tablename__ = 'vista_mobiliario_completa'
    __table_args__ = {'info': {'is_view': True}}

    id_mueble = db.Column(db.Integer, primary_key=True)
    tipo_mobiliario = db.Column(db.String(30))
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    color = db.Column(db.String(20))
    caracteristicas = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    estado = db.Column(db.String(20))
    color_estado = db.Column(db.String(7))
    fecha_asignacion = db.Column(db.Date)
    sucursal = db.Column(db.String(50))
    responsable = db.Column(db.String(100))
    numero_nomina = db.Column(db.String(10))
    puesto = db.Column(db.String(80))
    area = db.Column(db.String(50))
    creado_por = db.Column(db.String(100))
    fecha_creacion = db.Column(db.DateTime)
    modificado_por = db.Column(db.String(100))
    fecha_modificacion = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id_mueble': self.id_mueble,
            'tipo_mobiliario': self.tipo_mobiliario,
            'marca': self.marca,
            'modelo': self.modelo,
            'color': self.color,
            'caracteristicas': self.caracteristicas,
            'observaciones': self.observaciones,
            'estado': self.estado,
            'color_estado': self.color_estado,
            'fecha_asignacion': self.fecha_asignacion.isoformat() if self.fecha_asignacion else None,
            'sucursal': self.sucursal,
            'responsable': self.responsable,
            'numero_nomina': self.numero_nomina,
            'puesto': self.puesto,
            'area': self.area,
            'creado_por': self.creado_por,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'modificado_por': self.modificado_por,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None
        }


class VistaUsuariosCompleta(db.Model):
    """
    Vista de usuarios responsables con conteo de bienes asignados
    Corresponde a: vista_usuarios_completa
    """
    __tablename__ = 'vista_usuarios_completa'
    __table_args__ = {'info': {'is_view': True}}

    id_usuario = db.Column(db.Integer, primary_key=True)
    numero_nomina = db.Column(db.String(10))
    nombre_usuario = db.Column(db.String(100))
    puesto = db.Column(db.String(80))
    area = db.Column(db.String(50))
    fecha_creacion = db.Column(db.DateTime)
    equipos_asignados = db.Column(db.BigInteger)
    mobiliario_asignado = db.Column(db.BigInteger)

    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'numero_nomina': self.numero_nomina,
            'nombre_usuario': self.nombre_usuario,
            'puesto': self.puesto,
            'area': self.area,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'equipos_asignados': self.equipos_asignados,
            'mobiliario_asignado': self.mobiliario_asignado
        }


class VistaAccesosCompleta(db.Model):
    """
    Vista detallada de accesos con módulos y permisos
    Corresponde a: vista_accesos_completa
    """
    __tablename__ = 'vista_accesos_completa'
    __table_args__ = {'info': {'is_view': True}}

    # Datos del usuario
    id_acceso = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(100))
    correo_electronico = db.Column(db.String(100))
    area = db.Column(db.String(50))
    fecha_registro = db.Column(db.Date)
    fecha_creacion = db.Column(db.DateTime)
    ultimo_acceso = db.Column(db.DateTime)

    # Datos del módulo
    permisos = db.Column(JSON)

    def to_dict(self):
        return {
            'id_acceso': self.id_acceso,
            'nombre_usuario': self.nombre_usuario,
            'correo_electronico': self.correo_electronico,
            'area': self.area,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'permisos': self.permisos
        }
class VistaHistorialCompleta(db.Model):
    """
    Vista completa del historial con el nombre del usuario
    """
    __tablename__ = 'vista_historial_completa'
    __table_args__ = {'info': {'is_view': True}}

    id_historial = db.Column(db.Integer, primary_key=True)
    tabla = db.Column(db.Text)
    operacion = db.Column(db.Text)
    registro_id = db.Column(db.Text)
    cambios = db.Column(db.JSON)
    fecha = db.Column(db.DateTime)
    usuario_id = db.Column(db.Integer)
    realizado_por = db.Column(db.String(100))

    def to_dict(self):
        return {
            'id_historial': self.id_historial,
            'tabla': self.tabla,
            'operacion': self.operacion,
            'registro_id': self.registro_id,
            'cambios': self.cambios,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'usuario_id': self.usuario_id,
            'realizado_por': self.realizado_por
        }

    def to_dict_detallado(self):
        """Versión con cambios formateados de manera legible"""
        resultado = self.to_dict()

        if self.cambios:
            resultado['cambios_detallados'] = self._formatear_cambios()

        return resultado

    def _formatear_cambios(self):
        """Convierte los cambios JSON en un formato legible"""
        if not self.cambios:
            return []

        cambios_formateados = []

        for campo, valores in self.cambios.items():
            detalle = {
                'campo': campo,
                'campo_legible': self._nombre_campo_legible(campo)
            }

            if isinstance(valores, dict):
                if 'old' in valores:
                    detalle['valor_anterior'] = self._obtener_valor_legible(campo, valores['old'])
                if 'new' in valores:
                    detalle['valor_nuevo'] = self._obtener_valor_legible(campo, valores['new'])

            cambios_formateados.append(detalle)
        return cambios_formateados

    def _nombre_campo_legible(self, campo):
        """Convierte nombres de campos técnicos a nombres legibles"""
        nombres = {
            'estado_id': 'Estado',
            'usuario_asignado_id': 'Usuario Asignado',
            'tipo_activo_id': 'Tipo de Activo',
            'tipo_mobiliario_id': 'Tipo de Mobiliario',
            'area_id': 'Área',
            'nombre_activo': 'Nombre',
            'marca': 'Marca',
            'modelo': 'Modelo',
            'numero_serie': 'Número de Serie',
            'observaciones': 'Observaciones',
            'caracteristicas': 'Características',
            'color': 'Color',
            'nombre_usuario': 'Nombre',
            'correo_electronico': 'Correo Electrónico',
            'puesto': 'Puesto',
            'numero_nomina': 'Número de Nómina'
        }
        return nombres.get(campo, campo.replace('_', ' ').title())

    def _obtener_valor_legible(self, campo, valor):
        """Convierte IDs en nombres legibles consultando catálogos"""
        if valor is None:
            return None

        try:
            # Estado
            if campo == 'estado_id':
                estado = CatEstado.query.get(int(valor))
                return estado.nombre_estado if estado else valor

            # Usuario asignado
            elif campo == 'usuario_asignado_id':
                usuario = Usuario.query.get(int(valor))
                return usuario.nombre_usuario if usuario else valor

            # Tipo de activo
            elif campo == 'tipo_activo_id':
                tipo = CatTipoActivo.query.get(int(valor))
                return tipo.nombre_tipo if tipo else valor

            # Tipo de mobiliario
            elif campo == 'tipo_mobiliario_id':
                tipo = CatTipoMobiliario.query.get(int(valor))
                return tipo.nombre_tipo if tipo else valor

            # Área
            elif campo == 'area_id':
                area = CatArea.query.get(int(valor))
                return area.nombre_area if area else valor

            # Usuario que modificó/creó
            elif campo in ('creado_por', 'modificado_por'):
                acceso = Acceso.query.get(int(valor))
                return acceso.nombre_usuario if acceso else valor

            else:
                return valor

        except (ValueError, TypeError):
            return valor