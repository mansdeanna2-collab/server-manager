"""WebSocket events for fetch-server (mm.py) script execution with real-time streaming output."""

import threading
import subprocess
import os
import re
import json
import sys
import logging
from flask import request, current_app
from flask_socketio import emit, disconnect, join_room
from config import Config
import jwt

logger = logging.getLogger(__name__)

# Store active fetch-server tasks: {task_id: {output, status, server_info, user_id}}
# Thread-safe access using a lock
fetch_server_tasks = {}
fetch_server_tasks_lock = threading.Lock()

# Track log update interval for database saves (save every N lines to reduce DB load)
LOG_SAVE_INTERVAL = 10

# Regex pattern for printable characters (ASCII printable + CJK characters + fullwidth forms)
# Used to clean corrupted JSON data that may contain unknown/invalid characters
# - \x20-\x7E: ASCII printable characters (space through tilde)
# - \u4e00-\u9fff: CJK Unified Ideographs (Chinese characters)
# - \u3000-\u303f: CJK Symbols and Punctuation
# - \uff00-\uffef: Halfwidth and Fullwidth Forms
PRINTABLE_CHARS_PATTERN = re.compile(r'[^\x20-\x7E\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]')


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


def _save_task_to_db(app, user_id, ip_address, status, log_output=None, servers_added=None):
    """Save task state to database for persistence

    Args:
        app: Flask app instance for context
        user_id: User ID
        ip_address: IP address (task ID)
        status: Task status (running, completed, failed, timeout, error)
        log_output: Current log output
        servers_added: List of added servers
    """
    try:
        with app.app_context():
            from models import db
            from models.user_preference import FetchServerTask
            from utils import china_now

            task = FetchServerTask.query.filter_by(
                user_id=user_id,
                ip_address=ip_address
            ).first()

            if not task:
                task = FetchServerTask(
                    user_id=user_id,
                    ip_address=ip_address
                )
                db.session.add(task)

            task.status = status
            if log_output is not None:
                task.log_output = log_output
            if servers_added is not None:
                task.servers_added = json.dumps(servers_added)
            if status == 'running' and not task.started_at:
                task.started_at = china_now()
            if status in ['completed', 'failed', 'timeout', 'error']:
                task.completed_at = china_now()
            task.updated_at = china_now()

            db.session.commit()
    except Exception as e:
        logger.error(f"Error saving task to database: {str(e)}")


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
            if line and line.startswith('{') and (line.endswith('}') or '}' in line):
                # Handle lines that may have extra content after JSON
                if not line.endswith('}'):
                    # Find the last '}' and extract the JSON part
                    last_brace = line.rfind('}')
                    if last_brace > 0:
                        line = line[:last_brace + 1]

                try:
                    server_data = json.loads(line)
                    # 验证必要字段
                    if 'ips' in server_data and 'password' in server_data:
                        servers.append(server_data)
                except json.JSONDecodeError:
                    # Try to fix common JSON issues (unknown characters)
                    # Replace problematic characters with underscores using pre-compiled pattern
                    cleaned_line = PRINTABLE_CHARS_PATTERN.sub('_', line)
                    try:
                        server_data = json.loads(cleaned_line)
                        if 'ips' in server_data and 'password' in server_data:
                            servers.append(server_data)
                            logger.info("Parsed server data after character cleanup")
                    except json.JSONDecodeError:
                        # Last resort: try to extract key fields using regex
                        server_data = _extract_server_data_regex(line)
                        if server_data:
                            servers.append(server_data)
                            logger.info("Extracted server data using regex fallback")
                        else:
                            logger.warning(f"Failed to parse server JSON: {line[:100]}...")
                            continue

    # Also check for "未知字符数量(未做二次验证)" which indicates incomplete parsing
    # but the data should still be usable
    if not servers and '未知字符数量' in output:
        logger.info("Detected '未知字符数量' marker, attempting alternative extraction")
        # Try to find and extract JSON from the entire output
        json_pattern = r'\{[^{}]*"ips"\s*:\s*\[[^\]]+\][^{}]*"password"\s*:\s*"[^"]+\"[^{}]*\}'
        matches = re.findall(json_pattern, output, re.DOTALL)
        for json_str in matches:
            try:
                server_data = json.loads(json_str)
                if 'ips' in server_data and 'password' in server_data:
                    servers.append(server_data)
                    logger.info("Extracted server data using alternative pattern")
            except json.JSONDecodeError:
                continue

    return servers


def _extract_server_data_regex(line):
    """Extract server data using regex when JSON parsing fails.

    Args:
        line: String containing malformed JSON

    Returns:
        dict: Extracted server data or None if extraction failed
    """
    try:
        # Extract IPs array
        ips_match = re.search(r'"ips"\s*:\s*\[([^\]]+)\]', line)
        if not ips_match:
            return None

        # Extract individual IPs from the array
        ips_str = ips_match.group(1)
        ips = re.findall(r'"([^"]+)"', ips_str)
        if not ips:
            return None

        # Extract password
        password_match = re.search(r'"password"\s*:\s*"([^"]+)"', line)
        if not password_match:
            return None
        password = password_match.group(1)

        # Extract optional fields
        os_id_match = re.search(r'"os_id"\s*:\s*"([^"]+)"', line)
        os_name_match = re.search(r'"os_name"\s*:\s*"([^"]+)"', line)
        instance_id_match = re.search(r'"instance_id"\s*:\s*"([^"]+)"', line)
        name_match = re.search(r'"name"\s*:\s*"([^"]+)"', line)

        return {
            'ips': ips,
            'password': password,
            'os_id': os_id_match.group(1) if os_id_match else '',
            'os_name': os_name_match.group(1) if os_name_match else '',
            'instance_id': instance_id_match.group(1) if instance_id_match else '',
            'name': name_match.group(1) if name_match else ''
        }
    except Exception as e:
        logger.warning(f"Regex extraction failed: {str(e)}")
        return None


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

        # 获取ipid参数（用于更新mm.py中的target_ids）
        ipid = data.get('ipid', '')

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

        # 如果提供了ipid，先更新mm.py中的target_ids
        if ipid:
            try:
                # 验证ipid是否为有效数字
                ipid_int = int(ipid)

                # 读取mm.py文件内容
                with open(mm_py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 使用正则表达式替换target_ids的值，支持任意数组格式（包括多行）
                # 使用 [^\]]* 匹配除右方括号外的任意字符，安全支持多行数组
                new_content = re.sub(
                    r'target_ids\s*=\s*\[[^\]]*\]',
                    f'target_ids = [{ipid_int}]',
                    content
                )

                # 写回文件
                with open(mm_py_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                logger.info(f"Updated mm.py target_ids to [{ipid_int}]")
            except ValueError:
                emit('fetch_server_error', {'message': '无效的ID格式，ID必须是数字'})
                return
            except Exception as e:
                logger.error(f"Error updating mm.py target_ids: {str(e)}")
                emit('fetch_server_error', {'message': f'更新target_ids失败: {str(e)}'})
                return

        # 初始化任务状态
        user_id = user_data.get('user_id')
        with fetch_server_tasks_lock:
            fetch_server_tasks[task_id] = {
                'status': 'running',
                'output': '',
                'servers': [],
                'sid': sid,
                'user_id': user_id,
                'line_count': 0  # Track line count for periodic DB saves
            }

        # 通知客户端任务已开始
        emit('fetch_server_started', {
            'message': '开始运行获取服务器脚本...',
            'task_id': task_id
        })

        # 获取Flask app实例，用于在后台线程中创建应用上下文
        # Get Flask app instance for creating app context in background thread
        app = current_app._get_current_object()

        # Save initial task state to database
        _save_task_to_db(app, user_id, task_id, 'running', '', None)

        # Join a room for this task so multiple clients can receive updates
        join_room(f'task_{task_id}')

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
                line_count = 0

                # 读取输出并实时发送
                try:
                    for line in iter(process.stdout.readline, ''):
                        if line:
                            full_output += line
                            line_count += 1
                            # 更新任务状态（线程安全）
                            with fetch_server_tasks_lock:
                                if task_id in fetch_server_tasks:
                                    fetch_server_tasks[task_id]['output'] = full_output
                                    fetch_server_tasks[task_id]['line_count'] = line_count

                            # 实时发送输出到客户端（发送到任务房间，所有订阅的客户端都能收到）
                            socketio.emit(
                                'fetch_server_output',
                                {'data': line, 'task_id': task_id},
                                namespace='/fetch-server',
                                room=f'task_{task_id}'
                            )

                            # Periodically save to database (every LOG_SAVE_INTERVAL lines)
                            if line_count % LOG_SAVE_INTERVAL == 0:
                                _save_task_to_db(app, user_id, task_id, 'running', full_output, None)
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
                    # Save timeout status to database
                    _save_task_to_db(app, user_id, task_id, 'timeout', full_output, None)
                    socketio.emit(
                        'fetch_server_error',
                        {'message': '脚本执行超时（超过20分钟）', 'task_id': task_id},
                        namespace='/fetch-server',
                        room=f'task_{task_id}'
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

                    password_encryptor = PasswordEncryption(Config.ENCRYPTION_KEY)

                    # 使用之前捕获的app实例创建应用上下文
                    # Use the previously captured app instance to create app context
                    with app.app_context():
                        for server_data in servers:
                            ips = server_data.get('ips', [])
                            password = server_data.get('password', '')

                            if not ips or not password:
                                continue

                            # Ensure ips is a list
                            if not isinstance(ips, list):
                                ips = [str(ips)]

                            port, username = _determine_port_and_username(server_data)

                            # 生成备注：所有IP用/连接
                            notes = '/'.join(ips) if len(ips) > 1 else (server_data.get('name') or server_data.get('instance_id') or '')

                            # 加密密码（所有IP使用相同密码）
                            encrypted_password = password_encryptor.encrypt(password)

                            # 为每个IP创建服务器记录
                            for ip_address in ips:
                                # 检查IP是否已存在
                                existing = Server.query.filter_by(ip_address=ip_address).first()
                                if existing:
                                    logger.info(f"Server {ip_address} already exists, skipping")
                                    continue

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
                final_status = 'completed' if process.returncode == 0 else 'failed'
                with fetch_server_tasks_lock:
                    if task_id in fetch_server_tasks:
                        fetch_server_tasks[task_id]['status'] = final_status
                        fetch_server_tasks[task_id]['servers'] = added_servers
                        fetch_server_tasks[task_id]['output'] = full_output

                # Save final state to database
                _save_task_to_db(app, user_id, task_id, final_status, full_output, added_servers)

                # 发送完成消息到任务房间
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
                    room=f'task_{task_id}'
                )

            except Exception as e:
                logger.error(f"Error running fetch-server script: {str(e)}")
                with fetch_server_tasks_lock:
                    if task_id in fetch_server_tasks:
                        fetch_server_tasks[task_id]['status'] = 'error'
                # Save error state to database
                _save_task_to_db(app, user_id, task_id, 'error', str(e), None)
                socketio.emit(
                    'fetch_server_error',
                    {'message': f'执行失败: {str(e)}', 'task_id': task_id},
                    namespace='/fetch-server',
                    room=f'task_{task_id}'
                )

        # 启动后台线程
        thread = threading.Thread(
            target=run_script,
            daemon=True,
            name=f'fetch-server-{task_id}'
        )
        thread.start()

    @socketio.on('subscribe_task', namespace='/fetch-server')
    def handle_subscribe_task(data):
        """订阅任务更新（用于重新连接到正在运行的任务）

        当用户关闭对话框后重新打开，或者在其他设备打开时，
        可以通过此事件订阅正在运行的任务，接收实时更新。
        """
        # Note: request.sid is available but not needed in this handler

        # 验证token
        token = data.get('token')
        user_data = verify_token(token)
        if not user_data:
            emit('fetch_server_error', {'message': '认证失败，请重新登录'})
            disconnect()
            return

        task_id = data.get('task_id', '')
        if not task_id:
            emit('subscribe_error', {'message': '请提供任务ID'})
            return

        # Join the task room to receive updates
        join_room(f'task_{task_id}')

        # Check if task is still running in memory
        with fetch_server_tasks_lock:
            task = fetch_server_tasks.get(task_id)

        if task:
            # Task is still running, send current state
            emit('task_subscribed', {
                'task_id': task_id,
                'status': task['status'],
                'output': task['output'],
                'servers': task.get('servers', [])
            })
        else:
            # Task not in memory, it might have completed or not started
            emit('task_subscribed', {
                'task_id': task_id,
                'status': 'not_in_memory',
                'message': '任务不在内存中，请从数据库获取状态'
            })

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
                'servers': task.get('servers', [])
            })
        else:
            emit('task_status', {
                'task_id': task_id,
                'status': 'not_found'
            })
