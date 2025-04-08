from flask import Flask

def create_app():
    from .app import create_app as create_flask_app
    app = create_flask_app()
    
    # Initialize database
    from .storage.db import init_app
    init_app(app)
    
    return app 