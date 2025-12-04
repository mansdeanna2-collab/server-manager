from flask import Flask
from flask_cors import CORS
from models import db
from models.user import User
from models.server import Server
from routes.auth import auth_bp
from routes.servers import servers_bp
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(servers_bp)
    
    # Create tables and default admin user
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin/admin123")
    
    @app.route('/')
    def index():
        return {
            'message': 'Server Manager API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'servers': '/api/servers'
            }
        }
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
