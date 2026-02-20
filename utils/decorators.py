from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from models import Acceso, Permiso

def require_permission(modulo, permiso_tipo):
    """
    Decorador para verificar permisos específicos
    permiso_tipo: 'puede_crear', 'puede_leer', 'puede_actualizar', 'puede_eliminar', 'puede_exportar'
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # Obtener usuario
            usuario = Acceso.query.get(user_id)
            if not usuario:
                return jsonify({'error': 'Usuario no encontrado'}), 404
            
            # Obtener permisos
            permiso = Permiso.query.filter_by(
                rol_id=usuario.rol_id,
                modulo=modulo
            ).first()
            
            if not permiso:
                return jsonify({'error': 'Sin permisos en este módulo'}), 403
            
            # Verificar permiso específico
            if not getattr(permiso, permiso_tipo, False):
                return jsonify({'error': f'Sin permiso para {permiso_tipo.replace("puede_", "")}'}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator