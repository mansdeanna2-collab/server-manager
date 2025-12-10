from flask import Blueprint, request, jsonify
from models import db
from models.server import Server
from routes.auth import token_required
from utils.crypto import PasswordEncryption
from utils import china_now
from services.ssh_service import SSHService
from services.check_service import CheckService
from extensions import limiter
from config import Config
import logging
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

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

    # Check for duplicate IP address
    existing_server = Server.query.filter_by(ip_address=data['ip_address']).first()
    if existing_server:
        return jsonify({'message': f'服务器IP {data["ip_address"]} 已存在'}), 400

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

    # Check for duplicate IP address when updating IP
    if 'ip_address' in data and data['ip_address'] != server.ip_address:
        existing_server = Server.query.filter_by(ip_address=data['ip_address']).first()
        if existing_server:
            return jsonify({'message': f'服务器IP {data["ip_address"]} 已存在'}), 400
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


def _check_single_server(server_data):
    """Check a single server status (for use in thread pool).
    
    Args:
        server_data: tuple of (server_id, ip_address, port, username, encrypted_password)
    
    Returns:
        dict with server check results
    """
    server_id, ip_address, port, username, encrypted_password = server_data
    
    try:
        password = password_encryptor.decrypt(encrypted_password)
        status_info = CheckService.check_server_status(
            ip_address,
            port,
            username,
            password
        )
        
        return {
            'server_id': server_id,
            'ip_address': ip_address,
            'status_info': status_info,
            'success': True
        }
    except Exception as e:
        logger.error(f"Error checking server {ip_address}: {str(e)}")
        return {
            'server_id': server_id,
            'ip_address': ip_address,
            'status_info': {
                'overall': 'offline',
                'detail': f'检测出错: {str(e)}',
                'error_type': 'check_error'
            },
            'success': False
        }


@servers_bp.route('/check-all', methods=['POST'])
@limiter.exempt
@token_required
def check_all_servers(_current_user):
    """检查所有服务器状态（并发执行）
    
    This endpoint is exempt from rate limiting because:
    1. It checks all servers in a single request (batched operation)
    2. The actual network checks are done concurrently using ThreadPoolExecutor
    3. Users should be able to check all their servers without rate limit concerns
    """
    servers = Server.query.all()
    results = []
    
    if not servers:
        return jsonify(results), 200
    
    # Prepare server data for concurrent checking
    server_data_list = [
        (server.id, server.ip_address, server.port, server.username, server.encrypted_password)
        for server in servers
    ]
    
    # Create a mapping for quick lookup
    server_map = {server.id: server for server in servers}
    
    # Use ThreadPoolExecutor for concurrent checking
    max_workers = min(Config.CHECK_MAX_WORKERS, len(servers))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_server = {
            executor.submit(_check_single_server, data): data[0]
            for data in server_data_list
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_server):
            result = future.result()
            server_id = result['server_id']
            server = server_map.get(server_id)
            
            if server:
                status_info = result['status_info']
                server.status = status_info['overall']
                server.last_checked = china_now()
                server.check_detail = status_info.get('detail')
                server.error_type = _normalize_error_type(status_info.get('error_type'))
                
                results.append({
                    'server_id': server_id,
                    'ip_address': result['ip_address'],
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


def _is_valid_ip(ip):
    """Validate IP address format."""
    if not ip or not isinstance(ip, str):
        return False
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        num = int(part)
        if num < 0 or num > 255:
            return False
    return True


@servers_bp.route('/import-from-files', methods=['POST'])
@token_required
def import_servers_from_files(_current_user):
    """从服务器文件目录导入服务器"""
    server_files_dir = Config.SERVER_FILES_DIR
    if not os.path.exists(server_files_dir):
        return jsonify({'message': f'目录不存在: {server_files_dir}'}), 404

    if not os.path.isdir(server_files_dir):
        return jsonify({'message': f'路径不是目录: {server_files_dir}'}), 400

    imported = []
    skipped = []
    errors = []

    try:
        files = os.listdir(server_files_dir)
    except PermissionError:
        return jsonify({'message': f'无权限访问目录: {server_files_dir}'}), 403
    except OSError as e:
        return jsonify({'message': f'读取目录失败: {str(e)}'}), 500

    txt_files = [f for f in files if f.endswith('.txt')]

    try:
        for filename in txt_files:
            filepath = os.path.join(server_files_dir, filename)
            # Get notes from filename without .txt extension
            notes = filename[:-4]  # Remove .txt

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if not content:
                    errors.append({'file': filename, 'error': '文件为空'})
                    continue

                data = json.loads(content)

                # Extract IP from ips array
                ips = data.get('ips', [])
                if not ips or not isinstance(ips, list):
                    errors.append({'file': filename, 'error': '缺少有效的ips字段'})
                    continue
                ip_address = ips[0]

                # Validate IP address
                if not _is_valid_ip(ip_address):
                    errors.append({'file': filename, 'error': f'无效的IP地址: {ip_address}'})
                    continue

                # Extract password
                password = data.get('password', '')
                if not password:
                    errors.append({'file': filename, 'error': '缺少password字段'})
                    continue

                # Determine OS type and set port/username accordingly
                os_name = data.get('os_name', '').lower()
                os_id = data.get('os_id', '').lower()

                if 'windows' in os_name or 'windows' in os_id:
                    port = 3389
                    username = 'Administrator'
                else:
                    # Default to Linux/CentOS - SSH
                    port = 22
                    username = 'root'

                # Check if server with same IP already exists
                existing = Server.query.filter_by(ip_address=ip_address).first()
                if existing:
                    skipped.append({
                        'file': filename,
                        'ip': ip_address,
                        'reason': '服务器已存在'
                    })
                    continue

                # Encrypt password and create server
                encrypted_password = password_encryptor.encrypt(password)
                server = Server(
                    ip_address=ip_address,
                    port=port,
                    username=username,
                    encrypted_password=encrypted_password,
                    notes=notes
                )
                db.session.add(server)
                imported.append({
                    'file': filename,
                    'ip': ip_address,
                    'port': port,
                    'username': username,
                    'notes': notes
                })
                logger.info(f"Imported server from file: {filename} -> {ip_address}")

            except json.JSONDecodeError as e:
                errors.append({'file': filename, 'error': f'JSON解析失败: {str(e)}'})
            except PermissionError:
                errors.append({'file': filename, 'error': '无权限读取文件'})
            except OSError as e:
                errors.append({'file': filename, 'error': f'读取文件失败: {str(e)}'})

        if imported:
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Import failed: {str(e)}")
        return jsonify({'message': f'导入失败: {str(e)}'}), 500

    return jsonify({
        'imported': imported,
        'skipped': skipped,
        'errors': errors,
        'summary': {
            'total_files': len(txt_files),
            'imported_count': len(imported),
            'skipped_count': len(skipped),
            'error_count': len(errors)
        }
    }), 200


@servers_bp.route('/<int:server_id>/read-file', methods=['POST'])
@token_required
def read_server_file(_current_user, server_id):
    """通过SSH读取远程服务器上的文件内容"""
    server = Server.query.get(server_id)

    if not server:
        return jsonify({'message': 'Server not found'}), 404

    data = request.get_json()
    file_path = data.get('file_path', '') if data else ''

    if not file_path:
        return jsonify({'message': '请提供文件路径'}), 400

    # 检查端口是否为SSH端口
    if server.port == 3389:
        return jsonify({'message': 'Windows远程桌面服务不支持读取文件'}), 400

    # Decrypt password
    password = password_encryptor.decrypt(server.encrypted_password)

    # Create SSH connection and read file
    ssh = SSHService(server.ip_address, server.port, server.username, password)
    result = ssh.read_remote_file(file_path)

    if result['success']:
        return jsonify({
            'filename': file_path.split('/')[-1],
            'file_path': result['file_path'],
            'content': result['content']
        }), 200
    else:
        return jsonify({
            'message': result['message'],
            'error_type': result.get('error_type')
        }), 400
