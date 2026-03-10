"""
Utilidad para establecer el usuario actual en los triggers de historial
Sistema de Inventario IUCA
"""

from functools import wraps
from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from utils.extesions import db
from sqlalchemy import text

def set_current_user_for_triggers():
    try:
        verify_jwt_in_request(optional=True)

        user_id = get_jwt_identity()

        if not user_id:
            return

        db.session.execute(
            text("SET LOCAL app.current_user_id = :user_id"),
            {"user_id": str(user_id)}
        )

    except Exception as e:
        print("Error setting trigger user:", e)
        db.session.rollback()
