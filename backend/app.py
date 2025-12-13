from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import SocketIO
from sqlalchemy import inspect, text
from models import db
from models.user import User
from models.user_preference import (
    IpCheckStatus, IpIdResult, SegmentNote, SegmentFavorite, ServerFavorite
)
from routes.auth import auth_bp
from routes.servers import servers_bp
from routes.preferences import preferences_bp
from extensions import limiter
from config import Config
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize SocketIO globally
socketio = SocketIO()


def _migrate_add_missing_columns(db_engine):
    """Add missing columns to the servers table if they don't exist.
    
    This handles the case where the database was created with an older schema
    and new columns (check_detail, error_type) were added to the model.
    """
    inspector = inspect(db_engine)
    
    # Skip if the servers table doesn't exist yet (fresh database)
    if 'servers' not in inspector.get_table_names():
        return
    
    columns = {col['name'] for col in inspector.get_columns('servers')}
    
    with db_engine.connect() as conn:
        if 'check_detail' not in columns:
            conn.execute(text('ALTER TABLE servers ADD COLUMN check_detail TEXT'))
            logger.info("Added 'check_detail' column to servers table")
        if 'error_type' not in columns:
            conn.execute(text('ALTER TABLE servers ADD COLUMN error_type VARCHAR(50)'))
            logger.info("Added 'error_type' column to servers table")
        conn.commit()


def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

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

    # Initialize SocketIO with CORS settings
    # Use threading mode for better compatibility
    socketio.init_app(
        app,
        cors_allowed_origins=cors_origins if cors_origins != ['*'] else "*",
        async_mode='threading'
    )

    # Configure rate limiting
    if Config.RATELIMIT_ENABLED:
        limiter.init_app(app)
        # Set default limits
        app.config['RATELIMIT_DEFAULT'] = "200 per day, 50 per hour"
        logger.info("Rate limiting enabled")
    else:
        logger.info("Rate limiting disabled")

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(servers_bp)
    app.register_blueprint(preferences_bp)

    # Register terminal WebSocket events
    from routes.terminal import register_terminal_events
    register_terminal_events(socketio)

    # Register query-id WebSocket events
    from routes.query_id import register_query_id_events
    register_query_id_events(socketio)

    # Create tables and default admin user
    with app.app_context():
        db.create_all()
        
        # Migrate schema: add any missing columns to existing tables
        _migrate_add_missing_columns(db.engine)

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
            'version': '2.1.0',
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
    # allow_unsafe_werkzeug is needed when running with Werkzeug development server
    # Only enable in debug mode for development; production should use a proper WSGI server
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=debug)
