# utils/responsables.py
"""
Utilidad para sincronizar responsables asignados a un activo.

Calcula el diff entre los IDs actuales y los nuevos, eliminando
los que ya no corresponden e insertando solo los que faltan.
Funciona con cualquier modelo de asignación (EquipoResponsable,
MobiliarioResponsable) gracias a los parámetros campo_entidad
y campo_usuario.
"""

from models import Usuario
from utils.extesions import db


def sync_responsables(
    modelo_asignacion,
    entidad_id: int,
    nuevos_ids: list[int],
    campo_entidad: str,
    campo_usuario: str = 'usuario_id',
) -> None:
    """
    Sincroniza la tabla de asignación de responsables para un activo dado.

    Args:
        modelo_asignacion: Clase SQLAlchemy de la tabla pivote
                           (EquipoResponsable o MobiliarioResponsable).
        entidad_id:        ID del equipo o mueble al que pertenecen
                           las asignaciones.
        nuevos_ids:        Lista (o iterable) de IDs de usuarios que
                           deben quedar asignados tras la operación.
        campo_entidad:     Nombre del atributo FK que apunta al activo
                           en el modelo de asignación
                           (ej: 'equipo_id' o 'mueble_id').
        campo_usuario:     Nombre del atributo FK que apunta al usuario
                           en el modelo de asignación. Por defecto
                           'usuario_id'.

    La función no llama a db.session.commit(); el commit lo realiza
    el endpoint para mantener la operación dentro de la misma transacción.
    """
    nuevos = set(int(i) for i in nuevos_ids)

    actuales = modelo_asignacion.query.filter_by(
        **{campo_entidad: entidad_id}
    ).all()
    actuales_ids = {getattr(r, campo_usuario) for r in actuales}

    # Eliminar asignaciones que ya no están en la lista nueva
    ids_a_eliminar = actuales_ids - nuevos
    for registro in actuales:
        if getattr(registro, campo_usuario) in ids_a_eliminar:
            db.session.delete(registro)

    # Insertar solo las asignaciones que aún no existen
    ids_a_agregar = nuevos - actuales_ids
    for usuario_id in ids_a_agregar:
        if Usuario.query.get(usuario_id):
            db.session.add(
                modelo_asignacion(
                    **{campo_entidad: entidad_id, campo_usuario: usuario_id}
                )
            )