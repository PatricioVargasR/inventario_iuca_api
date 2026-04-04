from flask import jsonify

def register_error_handlers(app):

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad Request', 'mensaje': str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Unauthorized', 'mensaje': str(e)}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden', 'mensaje': str(e)}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not Found', 'mensaje': str(e)}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal Server Error', 'mensaje': str(e)}), 500