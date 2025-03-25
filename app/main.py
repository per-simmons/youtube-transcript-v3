from flask import Flask, send_from_directory, request
from .api.routes import api
import os

def create_app():
    app = Flask(__name__, static_folder='static')
    
    # Register blueprints
    app.register_blueprint(api)
    
    # Serve static files
    @app.route('/')
    def serve_static():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static_files(path):
        if path.startswith('api/'):
            return api.handle_request(path)
        
        # Handle static files
        if os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')
    
    return app 