from flask import Blueprint, request, jsonify
from models import db
from models.user_preference import (
    IpCheckStatus, IpIdResult, SegmentNote, SegmentFavorite, ServerFavorite,
    FetchServerTask
)
from models.system_log import SystemLog
from routes.auth import token_required
from services.log_service import log_backup, log_settings_change
from utils import china_now
import logging
import subprocess
import os
import json
import re
import ipaddress

preferences_bp = Blueprint('preferences', __name__, url_prefix='/api/preferences')
logger = logging.getLogger(__name__)

# Regex pattern for backup_id validation: YYYYMMDD_HHMMSS format
BACKUP_ID_PATTERN = re.compile(r'^\d{8}_\d{6}$')

# Backup exclusion patterns
BACKUP_EXCLUDE_DIRS = {'node_modules', '.git', '__pycache__', 'backups', 'venv', '.venv', 'dist'}
BACKUP_EXCLUDE_FILES = {'.DS_Store', 'Thumbs.db'}


def is_valid_ip(ip_str):
    """Validate if a string is a valid IPv4 or IPv6 address"""
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except ValueError:
        return False


# ============ IP Check Status APIs ============

@preferences_bp.route('/ip-check-status', methods=['GET'])
@token_required
def get_all_ip_check_status(current_user):
    """获取当前用户的所有IP检测状态"""
    statuses = IpCheckStatus.query.filter_by(user_id=current_user.id).all()
    result = {}
    for status in statuses:
        result[status.ip_address] = status.to_dict()
    return jsonify(result), 200


@preferences_bp.route('/ip-check-status', methods=['POST'])
@token_required
def save_ip_check_status(current_user):
    """保存IP检测状态"""
    data = request.get_json()

    if not data or not data.get('ip_address'):
        return jsonify({'message': '请提供IP地址'}), 400

    ip_address = data['ip_address']

    try:
        # 查找或创建记录
        status = IpCheckStatus.query.filter_by(
            user_id=current_user.id,
            ip_address=ip_address
        ).first()

        if not status:
            status = IpCheckStatus(
                user_id=current_user.id,
                ip_address=ip_address
            )
            db.session.add(status)

        # 更新状态
        status.port_checked = data.get('port_checked', False)
        status.ping_checked = data.get('ping_checked', False)
        status.ping_online = data.get('ping_online', False)
        status.port_22 = data.get('port_22', False)
        status.port_3389 = data.get('port_3389', False)
        status.last_checked = china_now()
        status.updated_at = china_now()

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving IP check status: {str(e)}")
        return jsonify({'message': '保存失败'}), 500

    return jsonify(status.to_dict()), 200


@preferences_bp.route('/ip-check-status/batch', methods=['POST'])
@token_required
def save_ip_check_status_batch(current_user):
    """批量保存IP检测状态"""
    data = request.get_json()

    if not data or not isinstance(data, list):
        return jsonify({'message': '请提供IP检测状态列表'}), 400

    results = []
    try:
        for item in data:
            ip_address = item.get('ip_address')
            if not ip_address:
                continue

            status = IpCheckStatus.query.filter_by(
                user_id=current_user.id,
                ip_address=ip_address
            ).first()

            if not status:
                status = IpCheckStatus(
                    user_id=current_user.id,
                    ip_address=ip_address
                )
                db.session.add(status)

            status.port_checked = item.get('port_checked', False)
            status.ping_checked = item.get('ping_checked', False)
            status.ping_online = item.get('ping_online', False)
            status.port_22 = item.get('port_22', False)
            status.port_3389 = item.get('port_3389', False)
            status.last_checked = china_now()
            status.updated_at = china_now()

            results.append(status.to_dict())

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving IP check status batch: {str(e)}")
        return jsonify({'message': '保存失败'}), 500

    return jsonify(results), 200


# ============ IP ID Result APIs ============

@preferences_bp.route('/ip-id-results', methods=['GET'])
@token_required
def get_all_ip_id_results(current_user):
    """获取当前用户的所有IP ID查询结果"""
    results = IpIdResult.query.filter_by(user_id=current_user.id).all()
    result_dict = {}
    for result in results:
        result_dict[result.ip_address] = result.to_dict()
    return jsonify(result_dict), 200


@preferences_bp.route('/ip-id-results', methods=['POST'])
@token_required
def save_ip_id_result(current_user):
    """保存IP ID查询结果"""
    data = request.get_json()

    if not data or not data.get('ip_address'):
        return jsonify({'message': '请提供IP地址'}), 400

    ip_address = data['ip_address']

    try:
        # 查找或创建记录
        result = IpIdResult.query.filter_by(
            user_id=current_user.id,
            ip_address=ip_address
        ).first()

        if not result:
            result = IpIdResult(
                user_id=current_user.id,
                ip_address=ip_address
            )
            db.session.add(result)

        # 更新结果
        result.id_result = data.get('id_result')
        result.log_output = data.get('log_output')
        result.last_queried = china_now()
        result.updated_at = china_now()

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving IP ID result: {str(e)}")
        return jsonify({'message': '保存失败'}), 500

    return jsonify(result.to_dict()), 200


# ============ Segment Notes APIs ============

@preferences_bp.route('/segment-notes', methods=['GET'])
@token_required
def get_all_segment_notes(current_user):
    """获取当前用户的所有IP段备注"""
    notes = SegmentNote.query.filter_by(user_id=current_user.id).all()
    result = {}
    for note in notes:
        result[note.segment] = note.note
    return jsonify(result), 200


@preferences_bp.route('/segment-notes', methods=['POST'])
@token_required
def save_segment_note(current_user):
    """保存IP段备注"""
    data = request.get_json()

    if not data or not data.get('segment'):
        return jsonify({'message': '请提供IP段'}), 400

    segment = data['segment']
    note_text = data.get('note', '').strip()

    try:
        # 查找现有记录
        note = SegmentNote.query.filter_by(
            user_id=current_user.id,
            segment=segment
        ).first()

        if not note_text:
            # 如果备注为空，删除记录
            if note:
                db.session.delete(note)
                db.session.commit()
            return jsonify({'message': '备注已删除'}), 200

        if not note:
            note = SegmentNote(
                user_id=current_user.id,
                segment=segment
            )
            db.session.add(note)

        note.note = note_text
        note.updated_at = china_now()

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving segment note: {str(e)}")
        return jsonify({'message': '保存失败'}), 500

    return jsonify(note.to_dict()), 200


# ============ Segment Favorites APIs ============

@preferences_bp.route('/segment-favorites', methods=['GET'])
@token_required
def get_segment_favorites(current_user):
    """获取当前用户收藏的所有IP段"""
    favorites = SegmentFavorite.query.filter_by(user_id=current_user.id).all()
    return jsonify([f.segment for f in favorites]), 200


@preferences_bp.route('/segment-favorites', methods=['POST'])
@token_required
def toggle_segment_favorite(current_user):
    """切换IP段收藏状态"""
    data = request.get_json()

    if not data or not data.get('segment'):
        return jsonify({'message': '请提供IP段'}), 400

    segment = data['segment']

    try:
        # 查找现有收藏
        favorite = SegmentFavorite.query.filter_by(
            user_id=current_user.id,
            segment=segment
        ).first()

        if favorite:
            # 取消收藏
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({'favorited': False, 'segment': segment}), 200
        else:
            # 添加收藏
            favorite = SegmentFavorite(
                user_id=current_user.id,
                segment=segment
            )
            db.session.add(favorite)
            db.session.commit()
            return jsonify({'favorited': True, 'segment': segment}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling segment favorite: {str(e)}")
        return jsonify({'message': '操作失败'}), 500


# ============ Server Favorites APIs ============

@preferences_bp.route('/server-favorites', methods=['GET'])
@token_required
def get_server_favorites(current_user):
    """获取当前用户收藏的所有服务器ID"""
    favorites = ServerFavorite.query.filter_by(user_id=current_user.id).all()
    return jsonify([f.server_id for f in favorites]), 200


@preferences_bp.route('/server-favorites', methods=['POST'])
@token_required
def toggle_server_favorite(current_user):
    """切换服务器收藏状态"""
    data = request.get_json()

    if not data or not data.get('server_id'):
        return jsonify({'message': '请提供服务器ID'}), 400

    server_id = data['server_id']

    try:
        # 查找现有收藏
        favorite = ServerFavorite.query.filter_by(
            user_id=current_user.id,
            server_id=server_id
        ).first()

        if favorite:
            # 取消收藏
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({'favorited': False, 'server_id': server_id}), 200
        else:
            # 添加收藏
            favorite = ServerFavorite(
                user_id=current_user.id,
                server_id=server_id
            )
            db.session.add(favorite)
            db.session.commit()
            return jsonify({'favorited': True, 'server_id': server_id}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling server favorite: {str(e)}")
        return jsonify({'message': '操作失败'}), 500


# ============ Update Cookie API ============

@preferences_bp.route('/update-cookie', methods=['POST'])
@token_required
def update_cookie(_current_user):
    """执行更新Cookie脚本
    
    调用 update_cookie.sh 脚本来:
    1. 发送登录请求到 user.jtti.cc
    2. 从响应中提取 XSRF-TOKEN 和 jtti_session
    3. 更新 mm.py 和 id.py 中的 cookie 值
    
    Returns:
        success: 是否成功
        message: 结果信息
        output: 脚本输出
    """
    # 获取 Python 目录路径（相对于当前文件的路径）
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python_dir = os.path.join(backend_dir, 'Python')
    
    # 验证 Python 目录在 backend 目录下（防止目录遍历）
    python_dir = os.path.realpath(python_dir)
    backend_dir = os.path.realpath(backend_dir)
    if not python_dir.startswith(backend_dir):
        return jsonify({
            'success': False,
            'message': '无效的目录路径'
        }), 400
    
    script_path = os.path.join(python_dir, 'update_cookie.sh')
    
    # 检查脚本是否存在
    if not os.path.exists(script_path):
        return jsonify({
            'success': False,
            'message': 'update_cookie.sh 脚本不存在'
        }), 404
    
    try:
        # 运行脚本
        result = subprocess.run(
            ['bash', script_path],
            capture_output=True,
            text=True,
            timeout=60,  # 60 seconds timeout
            cwd=python_dir
        )
        
        output = result.stdout
        if result.stderr:
            output += '\n' + result.stderr
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Cookie更新成功',
                'output': output
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Cookie更新失败',
                'output': output
            }), 400
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': '脚本执行超时'
        }), 408
    except Exception as e:
        logger.error(f"Error running update_cookie.sh: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'执行失败: {str(e)}'
        }), 500


# ============ Fetch Server Task APIs ============

@preferences_bp.route('/fetch-server-tasks', methods=['GET'])
@token_required
def get_all_fetch_server_tasks(current_user):
    """获取当前用户的所有获取服务器任务状态
    
    Returns a dict mapping IP addresses to task info
    """
    tasks = FetchServerTask.query.filter_by(user_id=current_user.id).all()
    result = {}
    for task in tasks:
        result[task.ip_address] = task.to_dict()
    return jsonify(result), 200


@preferences_bp.route('/fetch-server-tasks/<ip_address>', methods=['GET'])
@token_required
def get_fetch_server_task(current_user, ip_address):
    """获取指定IP的获取服务器任务状态"""
    task = FetchServerTask.query.filter_by(
        user_id=current_user.id,
        ip_address=ip_address
    ).first()
    
    if task:
        return jsonify(task.to_dict()), 200
    else:
        return jsonify({'status': 'not_found'}), 404


@preferences_bp.route('/fetch-server-tasks/running', methods=['GET'])
@token_required
def get_running_fetch_server_tasks(current_user):
    """获取当前用户所有正在运行的获取服务器任务
    
    Returns tasks with status 'running'
    """
    tasks = FetchServerTask.query.filter_by(
        user_id=current_user.id,
        status='running'
    ).all()
    result = {}
    for task in tasks:
        result[task.ip_address] = task.to_dict()
    return jsonify(result), 200


@preferences_bp.route('/fetch-server-tasks', methods=['POST'])
@token_required
def save_fetch_server_task(current_user):
    """保存获取服务器任务状态"""
    data = request.get_json()

    if not data or not data.get('ip_address'):
        return jsonify({'message': '请提供IP地址'}), 400

    ip_address = data['ip_address']

    try:
        # 查找或创建记录
        task = FetchServerTask.query.filter_by(
            user_id=current_user.id,
            ip_address=ip_address
        ).first()

        if not task:
            task = FetchServerTask(
                user_id=current_user.id,
                ip_address=ip_address
            )
            db.session.add(task)

        # 更新状态
        if 'status' in data:
            task.status = data['status']
        if 'log_output' in data:
            task.log_output = data['log_output']
        if 'servers_added' in data:
            try:
                task.servers_added = json.dumps(data['servers_added']) if data['servers_added'] else None
            except (TypeError, ValueError) as e:
                logger.warning(f"Error serializing servers_added: {str(e)}")
                task.servers_added = None
        if data.get('status') == 'running' and not task.started_at:
            task.started_at = china_now()
        if data.get('status') in ['completed', 'failed', 'timeout', 'error']:
            task.completed_at = china_now()
        task.updated_at = china_now()

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving fetch server task: {str(e)}")
        return jsonify({'message': '保存失败'}), 500

    return jsonify(task.to_dict()), 200


@preferences_bp.route('/fetch-server-tasks/<ip_address>', methods=['DELETE'])
@token_required
def delete_fetch_server_task(current_user, ip_address):
    """删除获取服务器任务记录"""
    try:
        task = FetchServerTask.query.filter_by(
            user_id=current_user.id,
            ip_address=ip_address
        ).first()

        if task:
            db.session.delete(task)
            db.session.commit()
            return jsonify({'message': '删除成功'}), 200
        else:
            return jsonify({'message': '任务不存在'}), 404
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting fetch server task: {str(e)}")
        return jsonify({'message': '删除失败'}), 500


# ============ System Backup APIs ============

def format_file_size(size_bytes):
    """格式化文件大小为可读格式"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


@preferences_bp.route('/backup/create', methods=['POST'])
@token_required
def create_system_backup(current_user):
    """创建系统备份
    
    创建一个包含所有文件和数据库的zip备份文件
    备份内容包括:
    - 数据库文件
    - Python脚本目录
    - 服务器文件目录
    - 配置文件
    - 后端源代码
    
    Returns:
        success: 是否成功
        backup_id: 备份文件标识符
        filename: 备份文件名
        size: 备份文件大小（字节）
        size_formatted: 格式化的文件大小
        message: 结果信息
    """
    import zipfile
    from datetime import datetime
    from config import Config
    
    try:
        # 获取当前时间作为备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"system_backup_{timestamp}.zip"
        
        # 获取后端目录路径
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 获取项目根目录（server-manager）
        project_root = os.path.dirname(backend_dir)
        
        # 创建临时目录存放备份文件
        backup_dir = os.path.join(backend_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 创建zip文件
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 备份数据库文件
            db_uri = Config.SQLALCHEMY_DATABASE_URI
            if db_uri.startswith('sqlite:///'):
                # SQLite数据库
                db_filename = db_uri.replace('sqlite:///', '')
                # 处理相对路径
                if not os.path.isabs(db_filename):
                    # 尝试instance目录
                    instance_db = os.path.join(backend_dir, 'instance', db_filename)
                    if os.path.exists(instance_db):
                        db_path = instance_db
                    else:
                        db_path = os.path.join(backend_dir, db_filename)
                else:
                    db_path = db_filename
                    
                if os.path.exists(db_path):
                    zipf.write(db_path, f"database/{os.path.basename(db_path)}")
                    logger.info(f"Added database to backup: {db_path}")
            
            # 备份后端目录（完整备份）
            for root, dirs, files in os.walk(backend_dir):
                # 排除特定目录
                dirs[:] = [d for d in dirs if d not in BACKUP_EXCLUDE_DIRS]
                
                for file in files:
                    if file in BACKUP_EXCLUDE_FILES:
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.join('backend', os.path.relpath(file_path, backend_dir))
                    try:
                        zipf.write(file_path, arcname)
                    except Exception as e:
                        logger.warning(f"Could not add file to backup: {file_path} - {str(e)}")
            logger.info("Added backend directory to backup")
            
            # 备份前端目录
            frontend_dir = os.path.join(project_root, 'frontend')
            if os.path.exists(frontend_dir):
                for root, dirs, files in os.walk(frontend_dir):
                    # 排除特定目录
                    dirs[:] = [d for d in dirs if d not in BACKUP_EXCLUDE_DIRS]
                    
                    for file in files:
                        if file in BACKUP_EXCLUDE_FILES:
                            continue
                        file_path = os.path.join(root, file)
                        arcname = os.path.join('frontend', os.path.relpath(file_path, frontend_dir))
                        try:
                            zipf.write(file_path, arcname)
                        except Exception as e:
                            logger.warning(f"Could not add file to backup: {file_path} - {str(e)}")
                logger.info("Added frontend directory to backup")
            
            # 备份服务器文件目录
            server_files_dir = Config.SERVER_FILES_DIR
            if os.path.exists(server_files_dir):
                for root, dirs, files in os.walk(server_files_dir):
                    dirs[:] = [d for d in dirs if d not in BACKUP_EXCLUDE_DIRS]
                    for file in files:
                        if file in BACKUP_EXCLUDE_FILES:
                            continue
                        file_path = os.path.join(root, file)
                        arcname = os.path.join('server_files', os.path.relpath(file_path, server_files_dir))
                        try:
                            zipf.write(file_path, arcname)
                        except Exception as e:
                            logger.warning(f"Could not add file to backup: {file_path} - {str(e)}")
                logger.info("Added server_files directory to backup")
            
            # 备份根目录下的配置文件
            root_files = ['docker-compose.yml', 'deploy-docker.sh', 'deploy-ubuntu.sh', 
                         'README.md', 'DEPLOYMENT_OPTIONS.md', 'DEPLOYMENT_UBUNTU.md',
                         'DOCUMENTATION_INDEX.md', 'QUICK_REFERENCE.md', '.gitignore']
            for filename in root_files:
                file_path = os.path.join(project_root, filename)
                if os.path.exists(file_path):
                    try:
                        zipf.write(file_path, filename)
                    except Exception as e:
                        logger.warning(f"Could not add file to backup: {file_path} - {str(e)}")
        
        # 获取文件大小
        file_size = os.path.getsize(backup_path)
        
        # 记录备份日志
        log_backup(current_user, backup_filename, success=True)
        
        return jsonify({
            'success': True,
            'backup_id': timestamp,
            'filename': backup_filename,
            'size': file_size,
            'size_formatted': format_file_size(file_size),
            'message': '系统备份创建成功'
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating system backup: {str(e)}")
        log_backup(current_user, backup_filename if 'backup_filename' in locals() else 'unknown', 
                   success=False, error_msg=str(e))
        return jsonify({
            'success': False,
            'message': f'创建备份失败: {str(e)}'
        }), 500


@preferences_bp.route('/backup/download/<backup_id>', methods=['GET'])
@token_required
def download_system_backup(_current_user, backup_id):
    """下载系统备份文件
    
    Args:
        backup_id: 备份文件标识符（时间戳）
        
    Returns:
        备份zip文件流
    """
    from flask import send_file
    
    try:
        # 验证backup_id格式（防止目录遍历攻击）
        if not backup_id or not BACKUP_ID_PATTERN.match(backup_id):
            return jsonify({
                'success': False,
                'message': '无效的备份标识符'
            }), 400
        
        # 获取备份目录路径
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backup_dir = os.path.join(backend_dir, 'backups')
        backup_filename = f"system_backup_{backup_id}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 验证路径安全性（防止目录遍历）
        backup_path = os.path.realpath(backup_path)
        backup_dir = os.path.realpath(backup_dir)
        if not backup_path.startswith(backup_dir):
            return jsonify({
                'success': False,
                'message': '无效的备份路径'
            }), 400
        
        # 检查文件是否存在
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'message': '备份文件不存在'
            }), 404
        
        return send_file(
            backup_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=backup_filename
        )
        
    except Exception as e:
        logger.error(f"Error downloading backup: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'下载备份失败: {str(e)}'
        }), 500


@preferences_bp.route('/backup/list', methods=['GET'])
@token_required
def list_system_backups(_current_user):
    """列出所有可用的系统备份
    
    Returns:
        backups: 备份文件列表，每个包含:
            - backup_id: 备份标识符
            - filename: 文件名
            - size: 文件大小（字节）
            - size_formatted: 格式化的文件大小
            - created_at: 创建时间
    """
    from datetime import datetime
    
    try:
        # 获取备份目录路径
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backup_dir = os.path.join(backend_dir, 'backups')
        
        backups = []
        
        if os.path.exists(backup_dir):
            for filename in os.listdir(backup_dir):
                if filename.startswith('system_backup_') and filename.endswith('.zip'):
                    backup_path = os.path.join(backup_dir, filename)
                    file_size = os.path.getsize(backup_path)
                    
                    # 从文件名提取时间戳
                    try:
                        timestamp_str = filename.replace('system_backup_', '').replace('.zip', '')
                        created_at = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        created_at_str = None
                    
                    backups.append({
                        'backup_id': timestamp_str,
                        'filename': filename,
                        'size': file_size,
                        'size_formatted': format_file_size(file_size),
                        'created_at': created_at_str
                    })
        
        # 按创建时间倒序排列
        backups.sort(key=lambda x: x['backup_id'], reverse=True)
        
        return jsonify({
            'success': True,
            'backups': backups
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取备份列表失败: {str(e)}'
        }), 500


@preferences_bp.route('/backup/delete/<backup_id>', methods=['DELETE'])
@token_required
def delete_system_backup(_current_user, backup_id):
    """删除系统备份文件
    
    Args:
        backup_id: 备份文件标识符（时间戳）
    """
    try:
        # 验证backup_id格式（防止目录遍历攻击）
        if not backup_id or not BACKUP_ID_PATTERN.match(backup_id):
            return jsonify({
                'success': False,
                'message': '无效的备份标识符'
            }), 400
        
        # 获取备份目录路径
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backup_dir = os.path.join(backend_dir, 'backups')
        backup_filename = f"system_backup_{backup_id}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 验证路径安全性（防止目录遍历）
        backup_path = os.path.realpath(backup_path)
        backup_dir = os.path.realpath(backup_dir)
        if not backup_path.startswith(backup_dir):
            return jsonify({
                'success': False,
                'message': '无效的备份路径'
            }), 400
        
        # 检查文件是否存在
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'message': '备份文件不存在'
            }), 404
        
        # 删除文件
        os.remove(backup_path)
        
        return jsonify({
            'success': True,
            'message': '备份文件已删除'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting backup: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除备份失败: {str(e)}'
        }), 500


@preferences_bp.route('/backup/verify/<backup_id>', methods=['GET'])
@token_required
def verify_system_backup(_current_user, backup_id):
    """验证系统备份文件完整性
    
    Args:
        backup_id: 备份文件标识符（时间戳）
        
    Returns:
        success: 是否成功
        valid: 备份文件是否有效
        file_count: 文件数量
        has_database: 是否包含数据库
        has_backend: 是否包含后端代码
        has_frontend: 是否包含前端代码
        errors: 验证错误列表
    """
    import zipfile
    
    try:
        # 验证backup_id格式
        if not backup_id or not BACKUP_ID_PATTERN.match(backup_id):
            return jsonify({
                'success': False,
                'message': '无效的备份标识符'
            }), 400
        
        # 获取备份文件路径
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backup_dir = os.path.join(backend_dir, 'backups')
        backup_filename = f"system_backup_{backup_id}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 验证路径安全性
        backup_path = os.path.realpath(backup_path)
        backup_dir = os.path.realpath(backup_dir)
        if not backup_path.startswith(backup_dir):
            return jsonify({
                'success': False,
                'message': '无效的备份路径'
            }), 400
        
        # 检查文件是否存在
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'message': '备份文件不存在'
            }), 404
        
        errors = []
        file_count = 0
        has_database = False
        has_backend = False
        has_frontend = False
        
        # 验证zip文件完整性
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # 测试zip文件完整性
                bad_files = zipf.testzip()
                if bad_files:
                    errors.append(f'损坏的文件: {bad_files}')
                
                # 获取文件列表
                file_list = zipf.namelist()
                file_count = len(file_list)
                
                # 检查关键目录
                for f in file_list:
                    if f.startswith('database/'):
                        has_database = True
                    elif f.startswith('backend/'):
                        has_backend = True
                    elif f.startswith('frontend/'):
                        has_frontend = True
                        
        except zipfile.BadZipFile:
            errors.append('无效的ZIP文件格式')
        except Exception as e:
            errors.append(f'验证错误: {str(e)}')
        
        # 判断是否有效
        valid = len(errors) == 0 and file_count > 0
        
        return jsonify({
            'success': True,
            'valid': valid,
            'file_count': file_count,
            'has_database': has_database,
            'has_backend': has_backend,
            'has_frontend': has_frontend,
            'errors': errors
        }), 200
        
    except Exception as e:
        logger.error(f"Error verifying backup: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'验证备份失败: {str(e)}'
        }), 500


@preferences_bp.route('/backup/stats', methods=['GET'])
@token_required
def get_backup_stats(_current_user):
    """获取备份统计信息
    
    Returns:
        success: 是否成功
        stats: 统计信息
            - total_count: 备份总数
            - total_size: 总大小（字节）
            - total_size_formatted: 格式化的总大小
            - oldest_backup: 最早的备份时间
            - newest_backup: 最新的备份时间
            - average_size: 平均大小（字节）
            - average_size_formatted: 格式化的平均大小
    """
    from datetime import datetime
    
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backup_dir = os.path.join(backend_dir, 'backups')
        
        total_count = 0
        total_size = 0
        oldest_backup = None
        newest_backup = None
        
        if os.path.exists(backup_dir):
            for filename in os.listdir(backup_dir):
                if filename.startswith('system_backup_') and filename.endswith('.zip'):
                    backup_path = os.path.join(backup_dir, filename)
                    file_size = os.path.getsize(backup_path)
                    total_count += 1
                    total_size += file_size
                    
                    # 提取时间戳
                    try:
                        timestamp_str = filename.replace('system_backup_', '').replace('.zip', '')
                        created_at = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        
                        if oldest_backup is None or created_at < oldest_backup:
                            oldest_backup = created_at
                        if newest_backup is None or created_at > newest_backup:
                            newest_backup = created_at
                    except ValueError:
                        pass
        
        average_size = int(total_size / total_count) if total_count > 0 else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_count': total_count,
                'total_size': total_size,
                'total_size_formatted': format_file_size(total_size),
                'oldest_backup': oldest_backup.strftime('%Y-%m-%d %H:%M:%S') if oldest_backup else None,
                'newest_backup': newest_backup.strftime('%Y-%m-%d %H:%M:%S') if newest_backup else None,
                'average_size': average_size,
                'average_size_formatted': format_file_size(average_size)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting backup stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取备份统计失败: {str(e)}'
        }), 500


# ============ Database Schema APIs ============

@preferences_bp.route('/database/schema', methods=['GET'])
@token_required
def get_database_schema(_current_user):
    """获取数据库结构（所有表和列）
    
    Returns:
        success: 是否成功
        tables: 表列表，每个包含:
            - name: 表名
            - columns: 列列表，每个包含:
                - name: 列名
                - type: 数据类型
                - nullable: 是否可为空
                - primary_key: 是否为主键
    """
    from sqlalchemy import inspect
    
    try:
        inspector = inspect(db.engine)
        tables = []
        
        for table_name in inspector.get_table_names():
            columns = []
            pk_columns = {col for col in inspector.get_pk_constraint(table_name).get('constrained_columns', [])}
            
            for column in inspector.get_columns(table_name):
                columns.append({
                    'name': column['name'],
                    'type': str(column['type']),
                    'nullable': column.get('nullable', True),
                    'primary_key': column['name'] in pk_columns,
                    'default': str(column.get('default')) if column.get('default') else None
                })
            
            tables.append({
                'name': table_name,
                'columns': columns
            })
        
        # Sort tables by name
        tables.sort(key=lambda x: x['name'])
        
        return jsonify({
            'success': True,
            'tables': tables
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting database schema: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取数据库结构失败: {str(e)}'
        }), 500


@preferences_bp.route('/database/data/<table_name>', methods=['GET'])
@token_required
def get_database_table_data(_current_user, table_name):
    """获取数据库表的数据
    
    Args:
        table_name: 表名
        
    Query params:
        page: 页码（默认1）
        per_page: 每页记录数（默认50，最大200）
        
    Returns:
        success: 是否成功
        table_name: 表名
        data: 数据列表
        columns: 列信息
        total: 总记录数
        page: 当前页码
        per_page: 每页记录数
        total_pages: 总页数
    """
    from sqlalchemy import inspect, table, select, func, column as sa_column
    
    try:
        # 验证表名（防止SQL注入）
        inspector = inspect(db.engine)
        valid_tables = inspector.get_table_names()
        
        if table_name not in valid_tables:
            return jsonify({
                'success': False,
                'message': f'表 {table_name} 不存在'
            }), 404
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        page = max(1, page)
        per_page = min(max(1, per_page), 200)
        
        # 获取列信息
        columns = []
        pk_columns = {col for col in inspector.get_pk_constraint(table_name).get('constrained_columns', [])}
        for column in inspector.get_columns(table_name):
            columns.append({
                'name': column['name'],
                'type': str(column['type']),
                'primary_key': column['name'] in pk_columns
            })
        
        # 获取总记录数
        # 使用 SQLAlchemy 的 table() 构造，表名已验证在 valid_tables 列表中
        tbl = table(table_name)
        count_query = select(func.count()).select_from(tbl)
        count_result = db.session.execute(count_query)
        total = count_result.scalar()
        
        # 计算分页
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        offset = (page - 1) * per_page
        
        # 获取数据 - 使用 SQLAlchemy 的 table() 和 select()
        # 显式选择所有已验证的列名，而不是使用 *
        # 注意：table_name 和 column_names 都经过验证
        column_names = [col['name'] for col in columns]
        col_objects = [sa_column(name) for name in column_names]
        data_query = select(*col_objects).select_from(tbl).limit(per_page).offset(offset)
        result = db.session.execute(data_query)
        
        # 转换为字典列表
        data = []
        for row in result:
            row_dict = {}
            for i, col_name in enumerate(column_names):
                value = row[i]
                # 处理日期时间类型
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                # 处理bytes类型
                elif isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8')
                    except Exception:
                        value = '<binary data>'
                row_dict[col_name] = value
            data.append(row_dict)
        
        return jsonify({
            'success': True,
            'table_name': table_name,
            'data': data,
            'columns': columns,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting table data: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取表数据失败: {str(e)}'
        }), 500


# ============ System Settings APIs ============

# System settings file path
SYSTEM_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'system_settings.json')


def load_system_settings():
    """Load system settings from file"""
    default_settings = {
        'login_whitelist': {
            'enabled': False,
            'ip_list': []
        },
        'ssl': {
            'enabled': False,
            'cert_path': '',
            'key_path': ''
        }
    }
    
    if os.path.exists(SYSTEM_SETTINGS_FILE):
        try:
            with open(SYSTEM_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key in default_settings:
                    if key not in settings:
                        settings[key] = default_settings[key]
                return settings
        except Exception as e:
            logger.error(f"Error loading system settings: {str(e)}")
    
    return default_settings


def save_system_settings(settings):
    """Save system settings to file"""
    try:
        with open(SYSTEM_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving system settings: {str(e)}")
        return False


@preferences_bp.route('/system-settings', methods=['GET'])
@token_required
def get_system_settings(_current_user):
    """获取系统设置
    
    Returns:
        success: 是否成功
        settings: 系统设置，包含:
            - login_whitelist: 登录白名单设置
            - ssl: SSL设置
    """
    try:
        settings = load_system_settings()
        return jsonify({
            'success': True,
            'settings': settings
        }), 200
    except Exception as e:
        logger.error(f"Error getting system settings: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取系统设置失败: {str(e)}'
        }), 500


@preferences_bp.route('/system-settings', methods=['POST'])
@token_required
def update_system_settings(_current_user):
    """更新系统设置
    
    Request body:
        settings: 系统设置对象
    """
    data = request.get_json()
    
    if not data or 'settings' not in data:
        return jsonify({
            'success': False,
            'message': '请提供设置数据'
        }), 400
    
    try:
        current_settings = load_system_settings()
        new_settings = data['settings']
        
        # Update login whitelist settings
        if 'login_whitelist' in new_settings:
            whitelist = new_settings['login_whitelist']
            current_settings['login_whitelist']['enabled'] = whitelist.get('enabled', False)
            if 'ip_list' in whitelist:
                # Validate IP addresses
                ip_list = whitelist['ip_list']
                if isinstance(ip_list, list):
                    valid_ips = []
                    invalid_ips = []
                    for ip in ip_list:
                        ip = ip.strip()
                        if ip:
                            if is_valid_ip(ip):
                                valid_ips.append(ip)
                            else:
                                invalid_ips.append(ip)
                    
                    if invalid_ips:
                        return jsonify({
                            'success': False,
                            'message': f'无效的IP地址: {", ".join(invalid_ips)}'
                        }), 400
                    
                    current_settings['login_whitelist']['ip_list'] = valid_ips
        
        # Update SSL settings
        if 'ssl' in new_settings:
            ssl = new_settings['ssl']
            current_settings['ssl']['enabled'] = ssl.get('enabled', False)
            current_settings['ssl']['cert_path'] = ssl.get('cert_path', '')
            current_settings['ssl']['key_path'] = ssl.get('key_path', '')
        
        if save_system_settings(current_settings):
            return jsonify({
                'success': True,
                'message': '系统设置已保存',
                'settings': current_settings
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '保存系统设置失败'
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating system settings: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新系统设置失败: {str(e)}'
        }), 500


# ============ System Logs APIs ============

@preferences_bp.route('/system-logs', methods=['GET'])
@token_required
def get_system_logs(_current_user):
    """获取系统日志（从数据库）
    
    Query params:
        page: 页码（默认1）
        per_page: 每页记录数（默认100，最大500）
        log_type: 日志类型过滤（可选）
        status: 状态过滤（可选）
        
    Returns:
        success: 是否成功
        logs: 日志列表
        total: 总记录数
        page: 当前页码
        per_page: 每页记录数
        total_pages: 总页数
    """
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        log_type = request.args.get('log_type', None, type=str)
        status = request.args.get('status', None, type=str)
        
        page = max(1, page)
        per_page = min(max(1, per_page), 500)
        
        # 构建查询
        query = SystemLog.query
        
        # 应用过滤器
        if log_type:
            query = query.filter(SystemLog.log_type == log_type)
        if status:
            query = query.filter(SystemLog.status == status)
        
        # 按时间倒序排列
        query = query.order_by(SystemLog.created_at.desc())
        
        # 获取总记录数
        total = query.count()
        
        # 分页
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        logs = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in logs],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting system logs: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取系统日志失败: {str(e)}'
        }), 500


@preferences_bp.route('/system-logs/types', methods=['GET'])
@token_required
def get_log_types(_current_user):
    """获取所有日志类型及其描述
    
    Returns:
        success: 是否成功
        types: 日志类型列表
    """
    from models.system_log import (
        LOG_TYPE_LOGIN, LOG_TYPE_LOGOUT, LOG_TYPE_LOGIN_FAILED,
        LOG_TYPE_PASSWORD_CHANGE, LOG_TYPE_SERVER_CONNECT,
        LOG_TYPE_SERVER_CREATE, LOG_TYPE_SERVER_UPDATE,
        LOG_TYPE_SERVER_DELETE, LOG_TYPE_SERVER_CHECK,
        LOG_TYPE_BACKUP, LOG_TYPE_SETTINGS, LOG_TYPE_IMPORT
    )
    
    log_types = [
        {'value': LOG_TYPE_LOGIN, 'label': '登录成功', 'color': 'success'},
        {'value': LOG_TYPE_LOGIN_FAILED, 'label': '登录失败', 'color': 'danger'},
        {'value': LOG_TYPE_LOGOUT, 'label': '用户登出', 'color': 'info'},
        {'value': LOG_TYPE_PASSWORD_CHANGE, 'label': '密码修改', 'color': 'warning'},
        {'value': LOG_TYPE_SERVER_CONNECT, 'label': '服务器连接', 'color': 'primary'},
        {'value': LOG_TYPE_SERVER_CREATE, 'label': '创建服务器', 'color': 'success'},
        {'value': LOG_TYPE_SERVER_UPDATE, 'label': '更新服务器', 'color': 'warning'},
        {'value': LOG_TYPE_SERVER_DELETE, 'label': '删除服务器', 'color': 'danger'},
        {'value': LOG_TYPE_SERVER_CHECK, 'label': '检测服务器', 'color': 'info'},
        {'value': LOG_TYPE_BACKUP, 'label': '系统备份', 'color': 'primary'},
        {'value': LOG_TYPE_SETTINGS, 'label': '设置修改', 'color': 'warning'},
        {'value': LOG_TYPE_IMPORT, 'label': '服务器导入', 'color': 'success'},
    ]
    
    return jsonify({
        'success': True,
        'types': log_types
    }), 200


@preferences_bp.route('/system-logs/stats', methods=['GET'])
@token_required
def get_log_stats(_current_user):
    """获取日志统计信息
    
    Returns:
        success: 是否成功
        stats: 统计信息
    """
    from sqlalchemy import func
    
    try:
        # 按类型统计
        type_stats = db.session.query(
            SystemLog.log_type,
            func.count(SystemLog.id).label('count')
        ).group_by(SystemLog.log_type).all()
        
        # 按状态统计
        status_stats = db.session.query(
            SystemLog.status,
            func.count(SystemLog.id).label('count')
        ).group_by(SystemLog.status).all()
        
        # 总数
        total = SystemLog.query.count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'by_type': {t: c for t, c in type_stats},
                'by_status': {s: c for s, c in status_stats}
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting log stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取日志统计失败: {str(e)}'
        }), 500
