"""WebSocket events for fetch-server (mm.py) script execution with real-time streaming output."""

import threading
import subprocess
import os
import re
import json
import sys
import logging
from flask import request
from flask_socketio import emit, disconnect
from config import Config
import jwt

logger = logging.getLogger(__name__)

# Store active fetch-server tasks: {task_id: {output, status, server_info}}
# Thread-safe access using a lock
fetch_server_tasks = {}
fetch_server_tasks_lock = threading.Lock()


def verify_token(token):
    """验证JWT token并返回用户信息"""
    if not token:
        return None
    try:
        data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return data
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None


def _parse_server_info(output):
    """从脚本输出中解析服务器信息
    
    Args:
        output: 脚本输出文本
    
    Returns:
        list: 解析出的服务器信息列表
    """
    servers = []
    
    # 查找 "===== 完整获取结果（控制台输出） =====" 后面的JSON数据
    # Find JSON data after "===== 完整获取结果（控制台输出） ====="
    pattern = r'=====\s*完整获取结果（控制台输出）\s*=====\s*\n(.+)'
    match = re.search(pattern, output, re.MULTILINE | re.DOTALL)
    
    if match:
        remaining_text = match.group(1)
        # 尝试逐行解析JSON
        for line in remaining_text.split('\n'):
            line = line.strip()
            if line and line.startswith('{') and line.endswith('}'):
                try:
                    server_data = json.loads(line)
                    # 验证必要字段
                    if 'ips' in server_data and 'password' in server_data:
                        servers.append(server_data)
                except json.JSONDecodeError:
                    continue
    
    return servers


def _determine_port_and_username(server_data):
    """根据操作系统类型确定端口和用户名
    
    Args:
        server_data: 服务器信息字典
    
    Returns:
        tuple: (port, username)
    """
    os_name = server_data.get('os_name', '').lower()
    os_id = server_data.get('os_id', '').lower()
    
    # Windows系统使用端口3389和Administrator用户
    if 'windows' in os_name or 'windows' in os_id:
        return 3389, 'Administrator'
    
    # Linux/Ubuntu等系统使用端口22和root用户
    return 22, 'root'


def get_task_status(task_id):
    """获取指定任务的状态"""
    with fetch_server_tasks_lock:
        return fetch_server_tasks.get(task_id)


def register_fetch_server_events(socketio):
    """注册获取服务器的WebSocket事件"""

    @socketio.on('connect', namespace='/fetch-server')
    def handle_connect():
        """处理WebSocket连接"""
        logger.info(f"Fetch-Server WebSocket connected: {request.sid}")

    @socketio.on('disconnect', namespace='/fetch-server')
    def handle_disconnect():
        """处理WebSocket断开"""
        logger.info(f"Fetch-Server WebSocket disconnected: {request.sid}")

    @socketio.on('start_fetch_server', namespace='/fetch-server')
    def handle_start_fetch_server(data):
        """启动获取服务器脚本，实时流式输出"""
        sid = request.sid

        # 验证token
        token = data.get('token')
        user_data = verify_token(token)
        if not user_data:
            emit('fetch_server_error', {'message': '认证失败，请重新登录'})
            disconnect()
            return

        # 获取可选的IP地址（用于标识任务）
        ip_address = data.get('ip_address', '')
        task_id = ip_address or f"task_{sid}"

        # 获取Python目录路径
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        python_dir = os.path.join(backend_dir, 'Python')

        # 验证 Python 目录在 backend 目录下（防止目录遍历）
        python_dir = os.path.realpath(python_dir)
        backend_dir = os.path.realpath(backend_dir)
        if not python_dir.startswith(backend_dir):
            emit('fetch_server_error', {'message': '无效的目录路径'})
            return

        mm_py_file = os.path.join(python_dir, 'mm.py')

        # 检查mm.py脚本文件是否存在
        if not os.path.exists(mm_py_file):
            emit('fetch_server_error', {'message': 'mm.py 脚本不存在'})
            return

        # 初始化任务状态
        with fetch_server_tasks_lock:
            fetch_server_tasks[task_id] = {
                'status': 'running',
                'output': '',
                'servers': [],
                'sid': sid
            }

        # 通知客户端任务已开始
        emit('fetch_server_started', {
            'message': '开始运行获取服务器脚本...',
            'task_id': task_id
        })

        # 在后台线程中运行脚本
        def run_script():
            try:
                # 使用Popen实现实时输出流
                # 使用 sys.executable 确保使用正确的 Python 解释器
                process = subprocess.Popen(
                    [sys.executable, '-u', mm_py_file],  # -u for unbuffered output
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=python_dir,
                    bufsize=1  # Line buffered
                )

                full_output = ''
                
                # 读取输出并实时发送
                try:
                    for line in iter(process.stdout.readline, ''):
                        if line:
                            full_output += line
                            # 更新任务状态（线程安全）
                            with fetch_server_tasks_lock:
                                if task_id in fetch_server_tasks:
                                    fetch_server_tasks[task_id]['output'] = full_output
                            # 实时发送输出到客户端
                            socketio.emit(
                                'fetch_server_output',
                                {'data': line, 'task_id': task_id},
                                namespace='/fetch-server',
                                room=sid
                            )
                except Exception as e:
                    logger.warning(f"Error reading output: {str(e)}")

                # 等待进程完成（最长20分钟，因为脚本需要约15分钟）
                try:
                    process.wait(timeout=1200)  # 20 minutes timeout
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    with fetch_server_tasks_lock:
                        if task_id in fetch_server_tasks:
                            fetch_server_tasks[task_id]['status'] = 'timeout'
                    socketio.emit(
                        'fetch_server_error',
                        {'message': '脚本执行超时（超过20分钟）', 'task_id': task_id},
                        namespace='/fetch-server',
                        room=sid
                    )
                    return

                # 从输出中解析服务器信息
                servers = _parse_server_info(full_output)
                
                # 如果解析到服务器信息，尝试添加到数据库
                added_servers = []
                if servers:
                    from models import db
                    from models.server import Server
                    from utils.crypto import PasswordEncryption
                    from flask import current_app
                    
                    password_encryptor = PasswordEncryption(Config.ENCRYPTION_KEY)
                    
                    with current_app.app_context():
                        for server_data in servers:
                            ips = server_data.get('ips', [])
                            password = server_data.get('password', '')
                            
                            if not ips or not password:
                                continue
                            
                            ip_address = ips[0] if isinstance(ips, list) else str(ips)
                            port, username = _determine_port_and_username(server_data)
                            
                            # 检查IP是否已存在
                            existing = Server.query.filter_by(ip_address=ip_address).first()
                            if existing:
                                logger.info(f"Server {ip_address} already exists, skipping")
                                continue
                            
                            # 加密密码并创建服务器记录
                            encrypted_password = password_encryptor.encrypt(password)
                            notes = server_data.get('name') or server_data.get('instance_id') or ''
                            
                            server = Server(
                                ip_address=ip_address,
                                port=port,
                                username=username,
                                encrypted_password=encrypted_password,
                                notes=notes
                            )
                            db.session.add(server)
                            added_servers.append({
                                'ip': ip_address,
                                'port': port,
                                'username': username,
                                'notes': notes
                            })
                            logger.info(f"Added new server: {ip_address}")
                        
                        if added_servers:
                            db.session.commit()

                # 更新任务状态（线程安全）
                with fetch_server_tasks_lock:
                    if task_id in fetch_server_tasks:
                        fetch_server_tasks[task_id]['status'] = 'completed' if process.returncode == 0 else 'failed'
                        fetch_server_tasks[task_id]['servers'] = added_servers
                        fetch_server_tasks[task_id]['output'] = full_output

                # 发送完成消息
                socketio.emit(
                    'fetch_server_completed',
                    {
                        'success': process.returncode == 0,
                        'output': full_output,
                        'servers': added_servers,
                        'task_id': task_id,
                        'message': f'获取服务器完成，新增 {len(added_servers)} 台服务器' if process.returncode == 0 else '脚本执行失败'
                    },
                    namespace='/fetch-server',
                    room=sid
                )

            except Exception as e:
                logger.error(f"Error running fetch-server script: {str(e)}")
                with fetch_server_tasks_lock:
                    if task_id in fetch_server_tasks:
                        fetch_server_tasks[task_id]['status'] = 'error'
                socketio.emit(
                    'fetch_server_error',
                    {'message': f'执行失败: {str(e)}', 'task_id': task_id},
                    namespace='/fetch-server',
                    room=sid
                )

        # 启动后台线程
        thread = threading.Thread(
            target=run_script,
            daemon=True,
            name=f'fetch-server-{task_id}'
        )
        thread.start()

    @socketio.on('get_task_status', namespace='/fetch-server')
    def handle_get_task_status(data):
        """获取指定任务的状态"""
        task_id = data.get('task_id', '')
        with fetch_server_tasks_lock:
            task = fetch_server_tasks.get(task_id)
        if task:
            emit('task_status', {
                'task_id': task_id,
                'status': task['status'],
                'output': task['output'],
                'servers': task['servers']
            })
        else:
            emit('task_status', {
                'task_id': task_id,
                'status': 'not_found'
            })
