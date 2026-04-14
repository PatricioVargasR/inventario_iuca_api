"""
Utilidades para manejo de concurrencia y bloqueos optimistas
Sistema de Inventario IUCA
"""

from datetime import datetime, timedelta
from flask import request
from sqlalchemy.exc import IntegrityError
from models import BloqueoActivo
from utils.extesions import db


def get_client_ip():
    """Obtiene la IP real del cliente."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr


def limpiar_bloqueos_expirados():
    """
    Elimina bloqueos que ya expiraron.

    Solo se llama desde crear_bloqueo para no añadir un DELETE
    extra a cada operación de lectura/verificación de bloqueos.
    """
    try:
        BloqueoActivo.query.filter(
            BloqueoActivo.expira_en < datetime.now()
        ).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error limpiando bloqueos: {e}")


def obtener_bloqueo(tabla, registro_id):
    """
    Obtiene el bloqueo activo de un registro.
    Retorna None si no hay bloqueo. No dispara limpieza —
    los registros expirados se filtran por fecha en la consulta.
    """
    return BloqueoActivo.query.filter(
        BloqueoActivo.tabla == tabla,
        BloqueoActivo.registro_id == registro_id,
        BloqueoActivo.expira_en > datetime.now(),
    ).first()


def crear_bloqueo(tabla, registro_id, usuario_id, nombre_usuario,
                  duracion_minutos=10, tipo_bloqueo='edicion'):
    """
    Intenta crear un bloqueo para un registro.
    Limpia bloqueos expirados antes de operar para evitar
    conflictos de unicidad con registros fantasma.

    Args:
        tipo_bloqueo: 'edicion' o 'eliminacion'

    Returns:
        tuple: (success: bool, data: dict)
    """
    # La limpieza ocurre solo aquí: punto donde se escribe y donde
    # los registros expirados podrían causar colisiones de unicidad.
    limpiar_bloqueos_expirados()

    bloqueo_existente = BloqueoActivo.query.filter_by(
        tabla=tabla,
        registro_id=registro_id
    ).first()

    if bloqueo_existente:
        # Mismo usuario, mismo tipo → renovar expiración
        if bloqueo_existente.usuario_id == usuario_id \
                and bloqueo_existente.tipo_bloqueo == tipo_bloqueo:
            bloqueo_existente.expira_en = datetime.now() + timedelta(minutes=duracion_minutos)
            db.session.commit()
            return True, bloqueo_existente.to_dict()

        # Mismo usuario, tipo distinto → actualizar tipo y renovar
        if bloqueo_existente.usuario_id == usuario_id \
                and bloqueo_existente.tipo_bloqueo != tipo_bloqueo:
            bloqueo_existente.tipo_bloqueo = tipo_bloqueo
            bloqueo_existente.expira_en = datetime.now() + timedelta(minutes=duracion_minutos)
            db.session.commit()
            return True, bloqueo_existente.to_dict()

        # Otro usuario → bloqueo activo
        accion = 'editando' if bloqueo_existente.tipo_bloqueo == 'edicion' else 'eliminando'
        return False, {
            'error': 'locked_by_other',
            'mensaje': f'{bloqueo_existente.nombre_usuario} está {accion} este registro',
            'bloqueo': bloqueo_existente.to_dict()
        }

    try:
        nuevo_bloqueo = BloqueoActivo(
            tabla=tabla,
            registro_id=registro_id,
            usuario_id=usuario_id,
            nombre_usuario=nombre_usuario,
            tipo_bloqueo=tipo_bloqueo,
            expira_en=datetime.now() + timedelta(minutes=duracion_minutos)
        )
        db.session.add(nuevo_bloqueo)
        db.session.commit()
        return True, nuevo_bloqueo.to_dict()

    except IntegrityError:
        # Race condition: otro proceso ganó la escritura simultánea
        db.session.rollback()
        bloqueo_existente = BloqueoActivo.query.filter_by(
            tabla=tabla,
            registro_id=registro_id
        ).first()

        if bloqueo_existente and bloqueo_existente.usuario_id == usuario_id:
            return True, bloqueo_existente.to_dict()

        accion = 'editando' if bloqueo_existente.tipo_bloqueo == 'edicion' else 'eliminando'
        return False, {
            'error': 'locked_by_other',
            'mensaje': f'{bloqueo_existente.nombre_usuario} está {accion} este registro',
            'bloqueo': bloqueo_existente.to_dict()
        }


def liberar_bloqueo(tabla, registro_id, usuario_id):
    """
    Libera el bloqueo de un registro.
    Solo el usuario que lo creó puede liberarlo.
    """
    try:
        bloqueo = BloqueoActivo.query.filter_by(
            tabla=tabla,
            registro_id=registro_id,
            usuario_id=usuario_id
        ).first()

        if bloqueo:
            db.session.delete(bloqueo)
            db.session.commit()
            return True

        return False

    except Exception as e:
        db.session.rollback()
        print(f"Error liberando bloqueo: {e}")
        return False


def liberar_todos_bloqueos_usuario(usuario_id):
    """Libera todos los bloqueos de un usuario. Útil al cerrar sesión."""
    try:
        BloqueoActivo.query.filter_by(usuario_id=usuario_id).delete()
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error liberando bloqueos del usuario: {e}")
        return False


def verificar_version(modelo, registro_id, version_esperada):
    """
    Verifica que la versión del registro coincida con la esperada.
    Retorna (es_valida: bool, version_actual: int).
    """
    registro = modelo.query.get(registro_id)
    if not registro:
        return False, None
    version_actual = getattr(registro, 'version')
    return version_actual == version_esperada, version_actual


def marcar_en_edicion(modelo, registro_id, usuario_id):
    """Marca un registro como 'en edición' por un usuario."""
    try:
        registro = modelo.query.get(registro_id)
        if registro:
            registro.editado_por = usuario_id
            registro.editado_desde = datetime.now()
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error marcando en edición: {e}")
        return False


def limpiar_marca_edicion(modelo, registro_id):
    """Limpia la marca de 'en edición' de un registro."""
    try:
        registro = modelo.query.get(registro_id)
        if registro:
            registro.editado_por = None
            registro.editado_desde = None
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error limpiando marca de edición: {e}")
        return False