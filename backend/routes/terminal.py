import threading
import logging
from flask import request
from flask_socketio import emit, disconnect
from models.server import Server
from models.user import User
from utils.crypto import PasswordEncryption
from services.terminal_service import TerminalService
from services.log_service import log_server_connect
from config import Config
import jwt

logger = logging.getLogger(__name__)

# Store active terminal sessions
terminal_sessions = {}

# Initialize password encryption
password_encryptor = PasswordEncryption(Config.ENCRYPTION_KEY)


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


def register_terminal_events(socketio):
    """注册终端WebSocket事件"""

    @socketio.on('connect', namespace='/terminal')
    def handle_connect():
        """处理WebSocket连接"""
        logger.info(f"Terminal WebSocket connected: {request.sid}")

    @socketio.on('disconnect', namespace='/terminal')
    def handle_disconnect():
        """处理WebSocket断开"""
        sid = request.sid
        if sid in terminal_sessions:
            terminal = terminal_sessions[sid]
            terminal.disconnect()
            del terminal_sessions[sid]
        logger.info(f"Terminal WebSocket disconnected: {sid}")

    @socketio.on('start_terminal', namespace='/terminal')
    def handle_start_terminal(data):
        """启动终端连接"""
        sid = request.sid

        # 验证token
        token = data.get('token')
        user_data = verify_token(token)
        if not user_data:
            emit('terminal_error', {'message': '认证失败，请重新登录'})
            disconnect()
            return

        server_id = data.get('server_id')
        if not server_id:
            emit('terminal_error', {'message': '缺少服务器ID'})
            return

        # 获取服务器信息
        server = Server.query.get(server_id)
        if not server:
            emit('terminal_error', {'message': '服务器不存在'})
            return

        # 解密密码
        try:
            password = password_encryptor.decrypt(server.encrypted_password)
        except Exception as e:
            logger.error(f"Failed to decrypt password: {str(e)}")
            emit('terminal_error', {'message': '密码解密失败'})
            return

        # 创建终端服务
        terminal = TerminalService(
            server.ip_address,
            server.port,
            server.username,
            password
        )

        # 连接服务器
        connect_result = terminal.connect()
        if not connect_result.get('success'):
            error_msg = connect_result.get('message', '无法连接到服务器')
            emit('terminal_error', {'message': error_msg})
            # 记录连接失败日志
            user = User.query.get(user_data.get('user_id'))
            log_server_connect(user, server.ip_address, success=False, error_msg=error_msg)
            return

        # 存储会话
        terminal_sessions[sid] = terminal

        # 记录连接成功日志
        user = User.query.get(user_data.get('user_id'))
        log_server_connect(user, server.ip_address, success=True)

        # 通知客户端连接成功
        emit('terminal_connected', {
            'message': f'已连接到 {server.ip_address}'
        })

        # 启动输出读取线程
        def output_callback(output_data):
            # Check if session still exists before emitting
            if sid in terminal_sessions:
                socketio.emit(
                    'terminal_output',
                    {'data': output_data},
                    namespace='/terminal',
                    room=sid
                )

        output_thread = threading.Thread(
            target=terminal.read_output,
            args=(output_callback,),
            daemon=True,
            name=f'terminal-output-{sid[:8]}'
        )
        output_thread.start()

    @socketio.on('terminal_input', namespace='/terminal')
    def handle_terminal_input(data):
        """处理终端输入"""
        sid = request.sid
        if sid not in terminal_sessions:
            emit('terminal_error', {'message': '终端会话不存在'})
            return

        terminal = terminal_sessions[sid]
        input_data = data.get('data', '')
        if input_data:
            terminal.send_input(input_data)

    @socketio.on('terminal_resize', namespace='/terminal')
    def handle_terminal_resize(data):
        """处理终端大小调整"""
        sid = request.sid
        if sid not in terminal_sessions:
            return

        terminal = terminal_sessions[sid]
        cols = data.get('cols', 80)
        rows = data.get('rows', 24)
        terminal.resize(cols, rows)

    @socketio.on('stop_terminal', namespace='/terminal')
    def handle_stop_terminal():
        """停止终端连接"""
        sid = request.sid
        if sid in terminal_sessions:
            terminal = terminal_sessions[sid]
            terminal.disconnect()
            del terminal_sessions[sid]
            emit('terminal_disconnected', {'message': '终端已断开'})
