from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db
from models.server import Server
from routes.auth import token_required
from utils.crypto import PasswordEncryption
from services.ssh_service import SSHService
from services.check_service import CheckService
from config import Config

servers_bp = Blueprint('servers', __name__, url_prefix='/api/servers')

# Initialize password encryption
password_encryptor = PasswordEncryption(Config.ENCRYPTION_KEY)

@servers_bp.route('', methods=['GET'])
@token_required
def get_servers(current_user):
    """Get all servers"""
    servers = Server.query.all()
    return jsonify([server.to_dict() for server in servers]), 200

@servers_bp.route('', methods=['POST'])
@token_required
def create_server(current_user):
    """Create a new server"""
    data = request.get_json()
    
    if not data.get('ip_address') or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'IP address, username, and password are required'}), 400
    
    # Encrypt password before storing
    encrypted_password = password_encryptor.encrypt(data['password'])
    
    server = Server(
        ip_address=data['ip_address'],
        port=data.get('port', 22),
        username=data['username'],
        encrypted_password=encrypted_password,
        notes=data.get('notes', '')
    )
    
    db.session.add(server)
    db.session.commit()
    
    return jsonify(server.to_dict()), 201

@servers_bp.route('/<int:server_id>', methods=['GET'])
@token_required
def get_server(current_user, server_id):
    """Get a specific server"""
    server = Server.query.get(server_id)
    
    if not server:
        return jsonify({'message': 'Server not found'}), 404
    
    return jsonify(server.to_dict()), 200

@servers_bp.route('/<int:server_id>', methods=['PUT'])
@token_required
def update_server(current_user, server_id):
    """Update a server"""
    server = Server.query.get(server_id)
    
    if not server:
        return jsonify({'message': 'Server not found'}), 404
    
    data = request.get_json()
    
    if 'ip_address' in data:
        server.ip_address = data['ip_address']
    if 'port' in data:
        server.port = data['port']
    if 'username' in data:
        server.username = data['username']
    if 'password' in data:
        server.encrypted_password = password_encryptor.encrypt(data['password'])
    if 'notes' in data:
        server.notes = data['notes']
    
    server.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(server.to_dict()), 200

@servers_bp.route('/<int:server_id>', methods=['DELETE'])
@token_required
def delete_server(current_user, server_id):
    """Delete a server"""
    server = Server.query.get(server_id)
    
    if not server:
        return jsonify({'message': 'Server not found'}), 404
    
    db.session.delete(server)
    db.session.commit()
    
    return jsonify({'message': 'Server deleted successfully'}), 200

@servers_bp.route('/<int:server_id>/check', methods=['POST'])
@token_required
def check_server(current_user, server_id):
    """Check server status"""
    server = Server.query.get(server_id)
    
    if not server:
        return jsonify({'message': 'Server not found'}), 404
    
    # Decrypt password
    password = password_encryptor.decrypt(server.encrypted_password)
    
    # Check status
    status_info = CheckService.check_server_status(
        server.ip_address,
        server.port,
        server.username,
        password
    )
    
    # Update server status
    server.status = status_info['overall']
    server.last_checked = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'server_id': server_id,
        'status': status_info
    }), 200

@servers_bp.route('/check-all', methods=['POST'])
@token_required
def check_all_servers(current_user):
    """Check status of all servers"""
    servers = Server.query.all()
    results = []
    
    for server in servers:
        password = password_encryptor.decrypt(server.encrypted_password)
        status_info = CheckService.check_server_status(
            server.ip_address,
            server.port,
            server.username,
            password
        )
        
        server.status = status_info['overall']
        server.last_checked = datetime.utcnow()
        
        results.append({
            'server_id': server.id,
            'ip_address': server.ip_address,
            'status': status_info
        })
    
    db.session.commit()
    
    return jsonify(results), 200

@servers_bp.route('/<int:server_id>/verify-password', methods=['POST'])
@token_required
def verify_password(current_user, server_id):
    """Verify server password"""
    server = Server.query.get(server_id)
    
    if not server:
        return jsonify({'message': 'Server not found'}), 404
    
    password = password_encryptor.decrypt(server.encrypted_password)
    ssh = SSHService(server.ip_address, server.port, server.username, password)
    
    is_valid = ssh.verify_credentials()
    
    return jsonify({
        'server_id': server_id,
        'password_valid': is_valid
    }), 200

@servers_bp.route('/<int:server_id>/check-port', methods=['POST'])
@token_required
def check_port(current_user, server_id):
    """Check if server port is open"""
    server = Server.query.get(server_id)
    
    if not server:
        return jsonify({'message': 'Server not found'}), 404
    
    is_open = CheckService.port_check(server.ip_address, server.port)
    
    return jsonify({
        'server_id': server_id,
        'port': server.port,
        'is_open': is_open
    }), 200

@servers_bp.route('/<int:server_id>/system-info', methods=['GET'])
@token_required
def get_system_info(current_user, server_id):
    """Get system information from server"""
    server = Server.query.get(server_id)
    
    if not server:
        return jsonify({'message': 'Server not found'}), 404
    
    password = password_encryptor.decrypt(server.encrypted_password)
    ssh = SSHService(server.ip_address, server.port, server.username, password)
    
    system_info = ssh.get_system_info()
    
    if system_info:
        # Update server with system info
        server.os_info = system_info.get('os')
        server.cpu_info = system_info.get('cpu')
        server.memory_info = system_info.get('memory')
        server.disk_info = system_info.get('disk')
        server.uptime = system_info.get('uptime')
        db.session.commit()
        
        return jsonify(system_info), 200
    else:
        return jsonify({'message': 'Failed to get system information'}), 500
