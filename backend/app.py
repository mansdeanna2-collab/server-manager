from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from models import db
from models.user import User
from models.server import Server
from routes.auth import auth_bp
from routes.servers import servers_bp
from config import Config
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Configure CORS with specific origins for production
    cors_origins = Config.CORS_ORIGINS.split(',') if Config.CORS_ORIGINS else ['*']
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Configure rate limiting
    if Config.RATELIMIT_ENABLED:
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri=Config.RATELIMIT_STORAGE_URL
        )
        logger.info("Rate limiting enabled")
    else:
        logger.info("Rate limiting disabled")
    
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
            logger.info("Default admin user created: admin/admin123")
    
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Server Manager API',
            'version': '2.0.0',
            'status': 'running',
            'endpoints': {
                'auth': '/api/auth',
                'servers': '/api/servers',
                'health': '/health'
            }
        })
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': str(error)}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'error': 'Rate limit exceeded', 'message': str(e.description)}), 429
    
    return app

if __name__ == '__main__':
    app = create_app()
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting Server Manager API on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
