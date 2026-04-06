from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from models import BloqueoActivo


def lock_required(tabla: str):
    """
    Decorador que verifica que el usuario autenticado posea un bloqueo
    de tipo 'eliminacion' sobre el registro antes de proceder con el DELETE.

    Uso:
        @equipos_bp.route('/<int:id>', methods=['DELETE'])
        @jwt_required()
        @lock_required('equipos_computo')
        def delete_equipo(id):
            ...

    El decorador espera que la función reciba `id` como argumento posicional
    o keyword argument (el ID del registro a eliminar).
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            registro_id = kwargs.get('id')

            # ¿El usuario tiene el bloqueo de eliminación?
            bloqueo_propio = BloqueoActivo.query.filter_by(
                tabla=tabla,
                registro_id=registro_id,
                usuario_id=user_id,
                tipo_bloqueo='eliminacion'
            ).first()

            if not bloqueo_propio:
                # ¿Existe algún bloqueo de otro usuario?
                bloqueo_ajeno = BloqueoActivo.query.filter_by(
                    tabla=tabla,
                    registro_id=registro_id
                ).first()

                if bloqueo_ajeno:
                    accion = 'editando' if bloqueo_ajeno.tipo_bloqueo == 'edicion' else 'eliminando'
                    return jsonify({
                        'error': 'locked_by_other',
                        'mensaje': f'{bloqueo_ajeno.nombre_usuario} está {accion} este registro',
                        'bloqueo': bloqueo_ajeno.to_dict()
                    }), 409

                return jsonify({
                    'error': 'no_lock',
                    'mensaje': 'Debe adquirir bloqueo antes de eliminar'
                }), 403

            # Inyectar el bloqueo en kwargs para que el endpoint pueda eliminarlo
            kwargs['bloqueo'] = bloqueo_propio
            return fn(*args, **kwargs)

        return wrapper
    return decorator