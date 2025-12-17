from flask import Blueprint, request, jsonify
from models import db
from models.user_preference import (
    IpCheckStatus, IpIdResult, SegmentNote, SegmentFavorite, ServerFavorite,
    FetchServerTask
)
from routes.auth import token_required
from utils import china_now
import logging
import subprocess
import os
import json

preferences_bp = Blueprint('preferences', __name__, url_prefix='/api/preferences')
logger = logging.getLogger(__name__)


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
def create_system_backup(_current_user):
    """创建系统备份
    
    创建一个包含所有文件和数据库的zip备份文件
    
    Returns:
        success: 是否成功
        backup_id: 备份文件标识符
        filename: 备份文件名
        size: 备份文件大小（字节）
        size_formatted: 格式化的文件大小
        message: 结果信息
    """
    import zipfile
    import tempfile
    import shutil
    from datetime import datetime
    from config import Config
    
    try:
        # 获取当前时间作为备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"system_backup_{timestamp}.zip"
        
        # 获取后端目录路径
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
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
            
            # 备份Python脚本目录
            python_dir = os.path.join(backend_dir, 'Python')
            if os.path.exists(python_dir):
                for root, _dirs, files in os.walk(python_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join('Python', os.path.relpath(file_path, python_dir))
                        zipf.write(file_path, arcname)
                logger.info(f"Added Python directory to backup")
            
            # 备份服务器文件目录
            server_files_dir = Config.SERVER_FILES_DIR
            if os.path.exists(server_files_dir):
                for root, _dirs, files in os.walk(server_files_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join('server_files', os.path.relpath(file_path, server_files_dir))
                        zipf.write(file_path, arcname)
                logger.info(f"Added server_files directory to backup")
        
        # 获取文件大小
        file_size = os.path.getsize(backup_path)
        
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
        if not backup_id or not backup_id.replace('_', '').isdigit():
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
        if not backup_id or not backup_id.replace('_', '').isdigit():
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
