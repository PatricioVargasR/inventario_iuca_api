from sqlalchemy.ext.declarative import declared_attr
from utils.extesions import db

class VersionMixin:
    """
        Mixin que agrega control de versiones y auditoría de edición
        a cualquier modelo SQLAlchemy.

        Requisito: el modelo que lo use debe declarar la relación 'editor'
        apuntando al modelo Acceso con el FK editado_por.
    """
    version = db.Column(db.Integer, default=1, nullable=False)
    editado_por = db.Column(db.Integer, db.ForeignKey('acceso.id_acceso'))
    editado_desde = db.Column(db.DateTime)

    @declared_attr
    def editor(cls):
        # Mantenemos la definición de la relación
        return db.relationship('Acceso', foreign_keys=[cls.editado_por], lazy='joined')

    def version_dict(self):
        """Retorna el bloque de auditoría listo para incluir en to_dict()."""

        # IMPORTANTE: Accedemos a la relación a través de la instancia
        # Usamos getattr por seguridad si la relación aún no se ha inicializado
        editor_obj = getattr(self, 'editor', None)

        return {
            'version': self.version,
            'editado_por': self.editado_por,
            'editado_desde': self.editado_desde.isoformat() if self.editado_desde else None,
            'nombre_editor': editor_obj.nombre_usuario if editor_obj else None,
        }