import os
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from api.auth import auth_bp
from api.files import files_bp

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    # Load config
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret'),
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads'),
    )
    
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        pass
    
    # Initialize extensions
    CORS(app)
    jwt = JWTManager(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)
    
    @app.route('/ping')
    def ping():
        return {'message': 'pong'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000) 