from flask import jsonify

def register_error_handlers(app):

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad Request', 'mensaje': str(e)}), 400

    @app.errorhandler(401)
    def bad_request(e):
        return jsonify({'error': 'Bad Request', 'mensaje': str(e)}), 401

    @app.errorhandler(403)
    def bad_request(e):
        return jsonify({'error': 'Bad Request', 'mensaje': str(e)}), 403

    @app.errorhandler(404)
    def bad_request(e):
        return jsonify({'error': 'Bad Request', 'mensaje': str(e)}), 404

    @app.errorhandler(404)
    def bad_request(e):
        return jsonify({'error': 'Bad Request', 'mensaje': str(e)}), 404