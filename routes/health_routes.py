from flask import Blueprint

health_bp = Blueprint("check", __name__)

@health_bp.get("/")
def health():
    return {"status": "ok"}, 200
