from app import db
from datetime import datetime

# ============================================
# CATÁLOGOS
# ============================================

class CatArea(db.Model):
    __tablename__ = 'cat_areas'
    
    id_area = db.Column(db.Integer, primary_key=True)
    nombre_area = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id_area': self.id_area,
            'nombre_area': self.nombre_area,
            'descripcion': self.descripcion
        }


class CatTipoActivo(db.Model):
    __tablename__ = 'cat_tipos_activo'
    
    id_tipo_activo = db.Column(db.Integer, primary_key=True)
    nombre_tipo = db.Column(db.String(30), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id_tipo_activo': self.id_tipo_activo,
            'nombre_tipo': self.nombre_tipo,
            'descripcion': self.descripcion
        }


class CatEstado(db.Model):
    __tablename__ = 'cat_estados'
    
    id_estado = db.Column(db.Integer, primary_key=True)
    nombre_estado = db.Column(db.String(20), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    color_hex = db.Column(db.String(7))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id_estado': self.id_estado,
            'nombre_estado': self.nombre_estado,
            'descripcion': self.descripcion,
            'color_hex': self.color_hex
        }


class CatTipoMobiliario(db.Model):
    __tablename__ = 'cat_tipos_mobiliario'
    
    id_tipo_mobiliario = db.Column(db.Integer, primary_key=True)
    nombre_tipo = db.Column(db.String(30), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id_tipo_mobiliario': self.id_tipo_mobiliario,
            'nombre_tipo': self.nombre_tipo,
            'descripcion': self.descripcion
        }


class CatRol(db.Model):
    __tablename__ = 'cat_roles'
    
    id_rol = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(30), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    nivel_acceso = db.Column(db.Integer)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id_rol': self.id_rol,
            'nombre_rol': self.nombre_rol,
            'descripcion': self.descripcion,
            'nivel_acceso': self.nivel_acceso
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
    rol_id = db.Column(db.Integer, db.ForeignKey('cat_roles.id_rol'))
    ultimo_acceso = db.Column(db.DateTime)
    fecha_registro = db.Column(db.Date, default=datetime.utcnow().date)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    rol = db.relationship('CatRol', backref='accesos')
    area = db.relationship('CatArea', backref='accesos')
    
    def to_dict(self, include_password=False):
        data = {
            'id_acceso': self.id_acceso,
            'nombre_usuario': self.nombre_usuario,
            'correo_electronico': self.correo_electronico,
            'area_id': self.area_id,
            'area': self.area.nombre_area if self.area else None,
            'rol_id': self.rol_id,
            'rol': self.rol.nombre_rol if self.rol else None,
            'nivel_acceso': self.rol.nivel_acceso if self.rol else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }
        if include_password:
            data['contrasena_hash'] = self.contrasena_hash
        return data


class Permiso(db.Model):
    __tablename__ = 'permisos'
    
    id_permiso = db.Column(db.Integer, primary_key=True)
    rol_id = db.Column(db.Integer, db.ForeignKey('cat_roles.id_rol'))
    modulo = db.Column(db.String(50), nullable=False)
    puede_crear = db.Column(db.Boolean, default=False)
    puede_leer = db.Column(db.Boolean, default=True)
    puede_actualizar = db.Column(db.Boolean, default=False)
    puede_eliminar = db.Column(db.Boolean, default=False)
    puede_exportar = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    rol = db.relationship('CatRol', backref='permisos')
    
    def to_dict(self):
        return {
            'id_permiso': self.id_permiso,
            'rol_id': self.rol_id,
            'modulo': self.modulo,
            'puede_crear': self.puede_crear,
            'puede_leer': self.puede_leer,
            'puede_actualizar': self.puede_actualizar,
            'puede_eliminar': self.puede_eliminar,
            'puede_exportar': self.puede_exportar
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


class HistorialMovimiento(db.Model):
    __tablename__ = 'historial_movimientos'
    
    id_movimiento = db.Column(db.Integer, primary_key=True)
    tipo_registro = db.Column(db.String(20), nullable=False)
    id_registro = db.Column(db.Integer, nullable=False)
    tipo_movimiento = db.Column(db.String(50), nullable=False)
    usuario_anterior_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))
    usuario_nuevo_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))
    estado_anterior_id = db.Column(db.Integer, db.ForeignKey('cat_estados.id_estado'))
    estado_nuevo_id = db.Column(db.Integer, db.ForeignKey('cat_estados.id_estado'))
    campo_modificado = db.Column(db.String(100))
    valor_anterior = db.Column(db.Text)
    valor_nuevo = db.Column(db.Text)
    realizado_por = db.Column(db.Integer, db.ForeignKey('acceso.id_acceso'))
    fecha_movimiento = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id_movimiento': self.id_movimiento,
            'tipo_registro': self.tipo_registro,
            'id_registro': self.id_registro,
            'tipo_movimiento': self.tipo_movimiento,
            'usuario_anterior_id': self.usuario_anterior_id,
            'usuario_nuevo_id': self.usuario_nuevo_id,
            'estado_anterior_id': self.estado_anterior_id,
            'estado_nuevo_id': self.estado_nuevo_id,
            'campo_modificado': self.campo_modificado,
            'valor_anterior': self.valor_anterior,
            'valor_nuevo': self.valor_nuevo,
            'realizado_por': self.realizado_por,
            'fecha_movimiento': self.fecha_movimiento.isoformat() if self.fecha_movimiento else None,
            'observaciones': self.observaciones
        }