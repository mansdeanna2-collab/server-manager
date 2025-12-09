from flask import Blueprint, request, jsonify
from models import db
from models.server import Server
from routes.auth import token_required
from utils.crypto import PasswordEncryption
from utils import china_now
from services.ssh_service import SSHService
from services.check_service import CheckService
from config import Config
import logging

servers_bp = Blueprint('servers', __name__, url_prefix='/api/servers')
logger = logging.getLogger(__name__)
MAX_ERROR_TYPE_LENGTH = 50
MAX_SERVER_FETCH = 1000

# Initialize password encryption
password_encryptor = PasswordEncryption(Config.ENCRYPTION_KEY)


def _normalize_error_type(error_type):
    """Ensure error_type fits database constraints."""
    if not error_type:
        return None
    return str(error_type)[:MAX_ERROR_TYPE_LENGTH]


@servers_bp.route('', methods=['GET'])
@token_required
def get_servers(_current_user):
    """获取所有服务器"""
    servers = (
        Server.query
        .order_by(Server.updated_at.desc())
        .limit(MAX_SERVER_FETCH)
        .all()
    )
    return jsonify([server.to_dict() for server in servers]), 200


@servers_bp.route('', methods=['POST'])
@token_required
def create_server(_current_user):
    """创建新服务器"""
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

    logger.info(f"Server created: {server.ip_address}")
    return jsonify(server.to_dict()), 201


@servers_bp.route('/<int:server_id>', methods=['GET'])
@token_required
def get_server(_current_user, server_id):
    """获取特定服务器"""
    server = Server.query.get(server_id)

    if not server:
        return jsonify({'message': 'Server not found'}), 404

    return jsonify(server.to_dict()), 200


@servers_bp.route('/<int:server_id>', methods=['PUT'])
@token_required
def update_server(_current_user, server_id):
    """更新服务器"""
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

    server.updated_at = china_now()
    db.session.commit()

    logger.info(f"Server updated: {server.ip_address}")
    return jsonify(server.to_dict()), 200


@servers_bp.route('/<int:server_id>', methods=['DELETE'])
@token_required
def delete_server(_current_user, server_id):
    """删除服务器"""
    server = Server.query.get(server_id)

    if not server:
        return jsonify({'message': 'Server not found'}), 404

    ip_address = server.ip_address
    db.session.delete(server)
    db.session.commit()

    logger.info(f"Server deleted: {ip_address}")
    return jsonify({'message': 'Server deleted successfully'}), 200


@servers_bp.route('/<int:server_id>/check', methods=['POST'])
@token_required
def check_server(_current_user, server_id):
    """检查服务器状态"""
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
    server.last_checked = china_now()
    server.check_detail = status_info.get('detail')
    server.error_type = _normalize_error_type(status_info.get('error_type'))
    db.session.commit()

    return jsonify({
        'server_id': server_id,
        'status': status_info,
        'last_checked': server.last_checked.isoformat() if server.last_checked else None,
        'updated_at': server.updated_at.isoformat() if server.updated_at else None,
        'check_detail': server.check_detail,
        'error_type': server.error_type
    }), 200


@servers_bp.route('/check-all', methods=['POST'])
@token_required
def check_all_servers(_current_user):
    """检查所有服务器状态"""
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
        server.last_checked = china_now()
        server.check_detail = status_info.get('detail')
        server.error_type = _normalize_error_type(status_info.get('error_type'))

        results.append({
            'server_id': server.id,
            'ip_address': server.ip_address,
            'status': status_info,
            'last_checked': server.last_checked.isoformat() if server.last_checked else None,
            'updated_at': server.updated_at.isoformat() if server.updated_at else None,
            'check_detail': server.check_detail,
            'error_type': server.error_type
        })

    db.session.commit()

    return jsonify(results), 200


@servers_bp.route('/<int:server_id>/verify-password', methods=['POST'])
@token_required
def verify_password(_current_user, server_id):
    """验证服务器密码"""
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
def check_port(_current_user, server_id):
    """检查服务器端口是否开放"""
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
def get_system_info(_current_user, server_id):
    """获取服务器系统信息"""
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


@servers_bp.route('/ip-region/<ip_address>', methods=['GET'])
@token_required
def get_ip_region(_current_user, ip_address):
    """获取IP地址的地区信息"""
    region_info = CheckService.get_ip_region(ip_address)
    return jsonify(region_info), 200


@servers_bp.route('/port-type/<int:port>', methods=['GET'])
@token_required
def get_port_type(_current_user, port):
    """获取端口类型信息"""
    port_info = CheckService.get_port_type(port)
    return jsonify(port_info), 200
