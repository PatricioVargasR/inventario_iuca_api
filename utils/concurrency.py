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
    """Obtiene la IP real del cliente"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr


def limpiar_bloqueos_expirados():
    """Elimina bloqueos que ya expiraron"""
    try:
        BloqueoActivo.query.filter(
            BloqueoActivo.expira_en < datetime.utcnow()
        ).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error limpiando bloqueos: {e}")


def obtener_bloqueo(tabla, registro_id):
    """
    Obtiene el bloqueo activo de un registro
    Retorna None si no hay bloqueo o si ya expiró
    """
    limpiar_bloqueos_expirados()

    bloqueo = BloqueoActivo.query.filter_by(
        tabla=tabla,
        registro_id=registro_id
    ).first()

    return bloqueo


def crear_bloqueo(tabla, registro_id, usuario_id, nombre_usuario, duracion_minutos=10):
    """
    Crea un bloqueo de edición para un registro
    Retorna (success: bool, bloqueo_o_error: dict)
    """
    limpiar_bloqueos_expirados()

    # Verificar si ya existe un bloqueo
    bloqueo_existente = BloqueoActivo.query.filter_by(
        tabla=tabla,
        registro_id=registro_id
    ).first()

    if bloqueo_existente:
        # Si el bloqueo es del mismo usuario, extender el tiempo
        if bloqueo_existente.usuario_id == usuario_id:
            bloqueo_existente.expira_en = datetime.utcnow() + timedelta(minutes=duracion_minutos)
            db.session.commit()
            return True, bloqueo_existente.to_dict()
        else:
            # Hay otro usuario editando
            return False, {
                'error': 'locked_by_other',
                'mensaje': f'{bloqueo_existente.nombre_usuario} está editando este registro',
                'bloqueo': bloqueo_existente.to_dict()
            }

    # Crear nuevo bloqueo
    try:
        nuevo_bloqueo = BloqueoActivo(
            tabla=tabla,
            registro_id=registro_id,
            usuario_id=usuario_id,
            nombre_usuario=nombre_usuario,
            expira_en=datetime.utcnow() + timedelta(minutes=duracion_minutos),
            ip_usuario=get_client_ip()
        )

        db.session.add(nuevo_bloqueo)
        db.session.commit()

        return True, nuevo_bloqueo.to_dict()

    except IntegrityError:
        db.session.rollback()
        # Race condition: otro usuario bloqueó entre la verificación y la creación
        bloqueo_existente = obtener_bloqueo(tabla, registro_id)
        if bloqueo_existente:
            return False, {
                'error': 'locked_by_other',
                'mensaje': f'{bloqueo_existente.nombre_usuario} está editando este registro',
                'bloqueo': bloqueo_existente.to_dict()
            }
        else:
            return False, {'error': 'Error al crear bloqueo'}


def liberar_bloqueo(tabla, registro_id, usuario_id):
    """
    Libera un bloqueo de edición
    Solo el usuario que lo creó puede liberarlo
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
    """
    Libera todos los bloqueos de un usuario
    Útil al cerrar sesión
    """
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
    Verifica que la versión del registro coincida con la esperada
    Retorna (es_valida: bool, version_actual: int)
    """
    registro = modelo.query.get(registro_id)

    if not registro:
        return False, None

    version_actual = registro.version
    es_valida = (version_actual == version_esperada)

    return es_valida, version_actual


def marcar_en_edicion(modelo, registro_id, usuario_id):
    """
    Marca un registro como 'en edición' por un usuario
    """
    try:
        registro = modelo.query.get(registro_id)
        if registro:
            registro.editado_por = usuario_id
            registro.editado_desde = datetime.utcnow()
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error marcando en edición: {e}")
        return False


def limpiar_marca_edicion(modelo, registro_id):
    """
    Limpia la marca de 'en edición' de un registro
    """
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