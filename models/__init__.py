from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from models.mixins import VersionMixin
from utils.constants import CAMPOS_LEGIBLES

# ============================================
# CATÁLOGOS
# ============================================

class CatArea(db.Model, VersionMixin):
    __tablename__ = 'cat_areas'

    id_area = db.Column(db.Integer, primary_key=True)
    nombre_area = db.Column(db.String(50), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self, include_version=True):
        data = {
            'id_area': self.id_area,
            'nombre_area': self.nombre_area,
            'activo': self.activo,
            'descripcion': self.descripcion,
            'fecha_creacion': self.fecha_creacion
        }
        if include_version:
            data.update(self.version_dict())
        return data


class CatTipoActivo(db.Model, VersionMixin):
    __tablename__ = 'cat_tipos_activo'

    id_tipo_activo = db.Column(db.Integer, primary_key=True)
    nombre_tipo = db.Column(db.String(30), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self, include_version=True):
        data = {
            'id_tipo_activo': self.id_tipo_activo,
            'nombre_tipo': self.nombre_tipo,
            'activo': self.activo,
            'descripcion': self.descripcion,
            'fecha_creacion': self.fecha_creacion
        }
        if include_version:
            data.update(self.version_dict())
        return data


class CatEstado(db.Model, VersionMixin):
    __tablename__ = 'cat_estados'

    id_estado = db.Column(db.Integer, primary_key=True)
    nombre_estado = db.Column(db.String(20), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False)
    descripcion = db.Column(db.Text)
    color_hex = db.Column(db.String(7))
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self, include_version=True):
        data = {
            'id_estado': self.id_estado,
            'nombre_estado': self.nombre_estado,
            'activo': self.activo,
            'descripcion': self.descripcion,
            'color_hex': self.color_hex,
            'fecha_creacion': self.fecha_creacion
        }
        if include_version:
            data.update(self.version_dict())
        return data

class CatTipoMobiliario(db.Model, VersionMixin):
    __tablename__ = 'cat_tipos_mobiliario'

    id_tipo_mobiliario = db.Column(db.Integer, primary_key=True)
    nombre_tipo = db.Column(db.String(30), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self, include_version=True):
        data = {
            'id_tipo_mobiliario': self.id_tipo_mobiliario,
            'nombre_tipo': self.nombre_tipo,
            'activo': self.activo,
            'descripcion': self.descripcion,
            'fecha_creacion': self.fecha_creacion
        }
        if include_version:
            data.update(self.version_dict())
        return data

# ============================================
# USUARIOS Y ACCESOS
# ============================================

class Usuario(db.Model, VersionMixin):
    __tablename__ = 'usuario'

    id_usuario = db.Column(db.Integer, primary_key=True)
    numero_nomina = db.Column(db.String(10), unique=True)
    nombre_usuario = db.Column(db.String(100), nullable=False)
    puesto = db.Column(db.String(80))
    area_id = db.Column(db.Integer, db.ForeignKey('cat_areas.id_area'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

    area = db.relationship(
        'CatArea',
        backref=db.backref('usuarios', passive_deletes=True)
    )

    def to_dict(self, include_version=True):
        data = {
            'id_usuario': self.id_usuario,
            'numero_nomina': self.numero_nomina,
            'nombre_usuario': self.nombre_usuario,
            'puesto': self.puesto,
            'area_id': self.area_id,
            'area': self.area.nombre_area if self.area else None,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
        if include_version:
            data.update(self.version_dict())
        return data

class Acceso(db.Model, VersionMixin):
    __tablename__ = 'acceso'

    id_acceso = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(100), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('cat_areas.id_area'))
    correo_electronico = db.Column(db.String(100), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(255), nullable=False)
    ultimo_acceso = db.Column(db.DateTime)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

    token_sesion_activa = db.Column(db.String(500))
    fecha_inicio_sesion = db.Column(db.DateTime)
    ip_sesion = db.Column(db.String(45))
    user_agent_sesion = db.Column(db.String(500))

    area = db.relationship(
        'CatArea',
        foreign_keys=[area_id],
        backref=db.backref('accesos', passive_deletes=True)
    )

    permisos = db.relationship('Permiso', backref='acceso', cascade='all, delete-orphan')

    def to_dict(self, include_password=False, include_version=True):
        data = {
            'id_acceso': self.id_acceso,
            'nombre_usuario': self.nombre_usuario,
            'correo_electronico': self.correo_electronico,
            'area_id': self.area_id,
            'area': self.area.nombre_area if self.area else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
        if include_password:
            data['contrasena_hash'] = self.contrasena_hash
        if include_version:
            data.update(self.version_dict())
        return data

    def permisos_dict(self):
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
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

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

class EquipoComputo(db.Model, VersionMixin):
    __tablename__ = 'equipos_computo'

    id_activo = db.Column(db.Integer, primary_key=True)
    tipo_activo_id = db.Column(db.Integer, db.ForeignKey('cat_tipos_activo.id_tipo_activo'))
    nombre_activo = db.Column(db.String(50), nullable=False)
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    numero_serie = db.Column(db.String(50), unique=True)
    estado_id = db.Column(db.Integer, db.ForeignKey('cat_estados.id_estado'))
    observaciones = db.Column(db.Text)
    sucursal_nombre = db.Column(db.String(50), default='Tulancingo')
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.now)

    tipo_activo = db.relationship('CatTipoActivo')
    estado = db.relationship('CatEstado')
    especificaciones = db.relationship('EspecificacionEquipo', backref='equipo', cascade='all, delete-orphan')
    responsables = db.relationship('EquipoResponsable', backref='equipo', cascade='all, delete-orphan')

    def to_dict(self, include_specs=False, include_responsables=True, include_version=True):
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
            'observaciones': self.observaciones,
            'sucursal_nombre': self.sucursal_nombre,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None
        }
        if include_version:
            data.update(self.version_dict())
        if include_specs:
            data['especificaciones'] = [spec.to_dict() for spec in self.especificaciones]
        if include_responsables:
            data['responsables'] = [resp.to_dict() for resp in self.responsables]
            data['responsables_ids'] = [resp.usuario_id for resp in self.responsables]
        return data


class EspecificacionEquipo(db.Model):
    __tablename__ = 'especificaciones_equipo'

    id_especificacion = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos_computo.id_activo', ondelete='CASCADE'))
    nombre_especificacion = db.Column(db.String(100), nullable=False)
    valor_especificacion = db.Column(db.String(100), nullable=False)
    orden = db.Column(db.Integer, default=1)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id_especificacion': self.id_especificacion,
            'equipo_id': self.equipo_id,
            'nombre_especificacion': self.nombre_especificacion,
            'valor_especificacion': self.valor_especificacion,
            'orden': self.orden
        }


class EquipoResponsable(db.Model):
    __tablename__ = 'equipos_responsables'

    id_equipo_responsable = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos_computo.id_activo', ondelete='CASCADE'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario', ondelete='CASCADE'), nullable=False)
    fecha_asignacion = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('equipo_id', 'usuario_id', name='uq_equipo_usuario'),
    )

    usuario = db.relationship('Usuario')

    def to_dict(self):
        return {
            'id_equipo_responsable': self.id_equipo_responsable,
            'equipo_id': self.equipo_id,
            'usuario_id': self.usuario_id,
            'nombre_usuario': self.usuario.nombre_usuario if self.usuario else None,
            'fecha_asignacion': self.fecha_asignacion.isoformat() if self.fecha_asignacion else None
        }


class Mobiliario(db.Model, VersionMixin):
    __tablename__ = 'mobiliario'

    id_mueble = db.Column(db.Integer, primary_key=True)
    tipo_mobiliario_id = db.Column(db.Integer, db.ForeignKey('cat_tipos_mobiliario.id_tipo_mobiliario'))
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    color = db.Column(db.String(20))
    caracteristicas = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    estado_id = db.Column(db.Integer, db.ForeignKey('cat_estados.id_estado'))
    sucursal_nombre = db.Column(db.String(50), default='Tulancingo')
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.now)

    tipo_mobiliario = db.relationship('CatTipoMobiliario')
    estado = db.relationship('CatEstado')
    responsables = db.relationship('MobiliarioResponsable', backref='mobiliario', cascade='all, delete-orphan')

    def to_dict(self, include_responsables=True, include_version=True):
        data = {
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
            'sucursal_nombre': self.sucursal_nombre,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None
        }
        if include_version:
            data.update(self.version_dict())
        if include_responsables:
            data['responsables'] = [resp.to_dict() for resp in self.responsables]
            data['responsables_ids'] = [resp.usuario_id for resp in self.responsables]
        return data


class MobiliarioResponsable(db.Model):
    __tablename__ = 'mobiliario_responsables'

    id_mueble_responsable = db.Column(db.Integer, primary_key=True)
    mueble_id = db.Column(db.Integer, db.ForeignKey('mobiliario.id_mueble', ondelete='CASCADE'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario', ondelete='CASCADE'), nullable=False)
    fecha_asignacion = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('mueble_id', 'usuario_id', name='uq_mueble_usuario'),
    )

    usuario = db.relationship('Usuario')

    def to_dict(self):
        return {
            'id_mueble_responsable': self.id_mueble_responsable,
            'mueble_id': self.mueble_id,
            'usuario_id': self.usuario_id,
            'nombre_usuario': self.usuario.nombre_usuario if self.usuario else None,
            'fecha_asignacion': self.fecha_asignacion.isoformat() if self.fecha_asignacion else None
        }


# ============================================
# VISTAS
# ============================================

class VistaEquiposCompleta(db.Model):
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
    observaciones = db.Column(db.Text)
    sucursal = db.Column(db.String(50))
    fecha_creacion = db.Column(db.DateTime)
    fecha_modificacion = db.Column(db.DateTime)
    especificaciones = db.Column(db.Text)
    # La vista ahora devuelve el JSON array de responsables
    responsables = db.Column(JSON)
    editado_por = db.Column(db.Integer)
    version = db.Column(db.Integer)

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
            'observaciones': self.observaciones,
            'sucursal': self.sucursal,
            # Compatibilidad: primer responsable como string
            'responsable': self.responsables[0]['nombre_usuario'] if self.responsables else None,
            # Lista completa de responsables
            'responsables': self.responsables or [],
            'responsables_ids': [r['id_usuario'] for r in (self.responsables or [])],
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None,
            'especificaciones': self.especificaciones,
            'editado_por': self.editado_por,
            'version': self.version,
        }


class VistaMobiliarioCompleta(db.Model):
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
    sucursal = db.Column(db.String(50))
    fecha_creacion = db.Column(db.DateTime)
    fecha_modificacion = db.Column(db.DateTime)
    responsables = db.Column(JSON)
    editado_por = db.Column(db.Integer)
    version = db.Column(db.Integer)

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
            'sucursal': self.sucursal,
            'responsable': self.responsables[0]['nombre_usuario'] if self.responsables else None,
            'responsables': self.responsables or [],
            'responsables_ids': [r['id_usuario'] for r in (self.responsables or [])],
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None,
            'editado_por': self.editado_por,
            'version': self.version,
        }


class VistaUsuariosCompleta(db.Model):
    __tablename__ = 'vista_usuarios_completa'
    __table_args__ = {'info': {'is_view': True}}

    id_usuario = db.Column(db.Integer, primary_key=True)
    numero_nomina = db.Column(db.String(10))
    nombre_usuario = db.Column(db.String(100))
    puesto = db.Column(db.String(80))
    area = db.Column(db.String(50))
    fecha_creacion = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'numero_nomina': self.numero_nomina,
            'nombre_usuario': self.nombre_usuario,
            'puesto': self.puesto,
            'area': self.area,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }


class VistaAccesosCompleta(db.Model):
    __tablename__ = 'vista_accesos_completa'
    __table_args__ = {'info': {'is_view': True}}

    id_acceso = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(100))
    correo_electronico = db.Column(db.String(100))
    area = db.Column(db.String(50))
    fecha_creacion = db.Column(db.DateTime)
    ultimo_acceso = db.Column(db.DateTime)
    permisos = db.Column(JSON)

    def to_dict(self):
        return {
            'id_acceso': self.id_acceso,
            'nombre_usuario': self.nombre_usuario,
            'correo_electronico': self.correo_electronico,
            'area': self.area,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'permisos': self.permisos
        }


class VistaHistorialCompleta(db.Model):
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
        resultado = self.to_dict()
        if self.cambios:
            resultado['cambios_detallados'] = self._formatear_cambios()
        return resultado

    def _formatear_cambios(self):
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
        return CAMPOS_LEGIBLES.get(campo, campo.replace('_', ' ').title())

    def _obtener_valor_legible(self, campo, valor):
        if valor is None:
            return None
        try:
            if campo == 'estado_id':
                estado = CatEstado.query.get(int(valor))
                return estado.nombre_estado if estado else valor
            elif campo == 'tipo_activo_id':
                tipo = CatTipoActivo.query.get(int(valor))
                return tipo.nombre_tipo if tipo else valor
            elif campo == 'tipo_mobiliario_id':
                tipo = CatTipoMobiliario.query.get(int(valor))
                return tipo.nombre_tipo if tipo else valor
            elif campo == 'area_id':
                area = CatArea.query.get(int(valor))
                return area.nombre_area if area else valor
            elif campo in ('creado_por', 'modificado_por'):
                acceso = Acceso.query.get(int(valor))
                return acceso.nombre_usuario if acceso else valor
            else:
                return valor
        except (ValueError, TypeError):
            return valor


class BloqueoActivo(db.Model):
    __tablename__ = 'bloqueos_activos'

    id_bloqueo = db.Column(db.Integer, primary_key=True)
    tabla = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('acceso.id_acceso', ondelete='CASCADE'), nullable=False)
    nombre_usuario = db.Column(db.String(100), nullable=False)
    tipo_bloqueo = db.Column(db.String(20), default='edicion', nullable=False)
    fecha_bloqueo = db.Column(db.DateTime, default=datetime.now)
    expira_en = db.Column(db.DateTime, nullable=False)
    ip_usuario = db.Column(db.String(45))

    __table_args__ = (
        db.UniqueConstraint('tabla', 'registro_id', name='uq_tabla_registro'),
        db.CheckConstraint("tipo_bloqueo IN ('edicion', 'eliminacion')", name='check_tipo_bloqueo')
    )

    def to_dict(self):
        return {
            'id_bloqueo': self.id_bloqueo,
            'tabla': self.tabla,
            'registro_id': self.registro_id,
            'usuario_id': self.usuario_id,
            'nombre_usuario': self.nombre_usuario,
            'tipo_bloqueo': self.tipo_bloqueo,
            'fecha_bloqueo': self.fecha_bloqueo.isoformat() if self.fecha_bloqueo else None,
            'expira_en': self.expira_en.isoformat() if self.expira_en else None,
            'ip_usuario': self.ip_usuario
        }