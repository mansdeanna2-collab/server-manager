"""WebSocket events for query-id script execution with real-time streaming output."""

import threading
import subprocess
import os
import re
import logging
from flask import request
from flask_socketio import emit, disconnect
from config import Config
import jwt

logger = logging.getLogger(__name__)

# Store active query-id tasks: {task_id: {ip, output, status, id_result}}
query_id_tasks = {}


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


def _is_valid_ip(ip_address):
    """验证IP地址格式"""
    if not ip_address or not isinstance(ip_address, str):
        return False
    parts = ip_address.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        try:
            num = int(part)
            if num < 0 or num > 255:
                return False
        except ValueError:
            return False
    return True


def get_task_status(ip_address):
    """获取指定IP的任务状态"""
    return query_id_tasks.get(ip_address)


def register_query_id_events(socketio):
    """注册查询ID的WebSocket事件"""

    @socketio.on('connect', namespace='/query-id')
    def handle_connect():
        """处理WebSocket连接"""
        logger.info(f"Query-ID WebSocket connected: {request.sid}")

    @socketio.on('disconnect', namespace='/query-id')
    def handle_disconnect():
        """处理WebSocket断开"""
        logger.info(f"Query-ID WebSocket disconnected: {request.sid}")

    @socketio.on('start_query_id', namespace='/query-id')
    def handle_start_query_id(data):
        """启动ID查询脚本，实时流式输出"""
        sid = request.sid

        # 验证token
        token = data.get('token')
        user_data = verify_token(token)
        if not user_data:
            emit('query_id_error', {'message': '认证失败，请重新登录'})
            disconnect()
            return

        ip_address = data.get('ip_address', '')
        if not ip_address:
            emit('query_id_error', {'message': '请提供IP地址'})
            return

        if not _is_valid_ip(ip_address):
            emit('query_id_error', {'message': '无效的IP地址格式'})
            return

        # 获取Python目录路径
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        python_dir = os.path.join(backend_dir, 'Python')

        # 验证 Python 目录在 backend 目录下（防止目录遍历）
        python_dir = os.path.realpath(python_dir)
        backend_dir = os.path.realpath(backend_dir)
        if not python_dir.startswith(backend_dir):
            emit('query_id_error', {'message': '无效的目录路径'})
            return

        ip_file = os.path.join(python_dir, 'ip.txt')
        id_py_file = os.path.join(python_dir, 'id.py')

        # 检查id.py脚本文件是否存在
        if not os.path.exists(id_py_file):
            emit('query_id_error', {'message': 'id.py 脚本不存在'})
            return

        # 初始化任务状态
        query_id_tasks[ip_address] = {
            'status': 'running',
            'output': '',
            'id_result': None,
            'sid': sid
        }

        # 通知客户端任务已开始
        emit('query_id_started', {
            'message': f'开始查询 {ip_address} 的ID...',
            'ip_address': ip_address
        })

        # 在后台线程中运行脚本
        def run_script():
            try:
                # 1. 生成对应IP的ip.txt文件（设置受限权限 600）
                with open(ip_file, 'w', encoding='utf-8') as f:
                    f.write(ip_address)
                os.chmod(ip_file, 0o600)

                # 2. 使用Popen实现实时输出流
                process = subprocess.Popen(
                    ['python3', '-u', id_py_file],  # -u for unbuffered output
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
                            # 更新任务状态
                            if ip_address in query_id_tasks:
                                query_id_tasks[ip_address]['output'] = full_output
                            # 实时发送输出到客户端
                            socketio.emit(
                                'query_id_output',
                                {'data': line, 'ip_address': ip_address},
                                namespace='/query-id',
                                room=sid
                            )
                except Exception as e:
                    logger.warning(f"Error reading output: {str(e)}")

                # 等待进程完成（最长5分钟）
                try:
                    process.wait(timeout=300)  # 5 minutes timeout
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    if ip_address in query_id_tasks:
                        query_id_tasks[ip_address]['status'] = 'timeout'
                    socketio.emit(
                        'query_id_error',
                        {'message': '脚本执行超时（超过5分钟）', 'ip_address': ip_address},
                        namespace='/query-id',
                        room=sid
                    )
                    return

                # 从输出中提取ID结果
                id_result = None
                id_match = re.search(r'前\d+个最小的id[:\s]*\[(\d+)\]', full_output)
                if id_match:
                    id_result = id_match.group(1)
                else:
                    id_match = re.search(r'\[(\d+)\]', full_output)
                    if id_match:
                        id_result = id_match.group(1)

                # 更新任务状态
                if ip_address in query_id_tasks:
                    query_id_tasks[ip_address]['status'] = 'completed' if process.returncode == 0 else 'failed'
                    query_id_tasks[ip_address]['id_result'] = id_result
                    query_id_tasks[ip_address]['output'] = full_output

                # 发送完成消息
                socketio.emit(
                    'query_id_completed',
                    {
                        'success': process.returncode == 0,
                        'output': full_output,
                        'id_result': id_result,
                        'ip_address': ip_address,
                        'message': '查询ID完成' if process.returncode == 0 else '脚本执行失败'
                    },
                    namespace='/query-id',
                    room=sid
                )

            except Exception as e:
                logger.error(f"Error running query-id script: {str(e)}")
                if ip_address in query_id_tasks:
                    query_id_tasks[ip_address]['status'] = 'error'
                socketio.emit(
                    'query_id_error',
                    {'message': f'执行失败: {str(e)}', 'ip_address': ip_address},
                    namespace='/query-id',
                    room=sid
                )

        # 启动后台线程
        thread = threading.Thread(
            target=run_script,
            daemon=True,
            name=f'query-id-{ip_address}'
        )
        thread.start()

    @socketio.on('get_task_status', namespace='/query-id')
    def handle_get_task_status(data):
        """获取指定IP的任务状态"""
        ip_address = data.get('ip_address', '')
        task = query_id_tasks.get(ip_address)
        if task:
            emit('task_status', {
                'ip_address': ip_address,
                'status': task['status'],
                'output': task['output'],
                'id_result': task['id_result']
            })
        else:
            emit('task_status', {
                'ip_address': ip_address,
                'status': 'not_found'
            })
