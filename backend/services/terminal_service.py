import paramiko
import logging
import threading
import time

logger = logging.getLogger(__name__)


class TerminalService:
    """WebSocket SSH终端服务类"""

    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.channel = None
        self._stop_event = threading.Event()

    def connect(self):
        """建立SSH连接并获取PTY通道"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=15,
                banner_timeout=30,
                auth_timeout=30
            )

            # 获取交互式shell通道
            self.channel = self.client.invoke_shell(term='xterm-256color')
            self.channel.settimeout(0.0)

            logger.info(f"Terminal connected to {self.host}:{self.port}")
            return True
        except paramiko.AuthenticationException:
            logger.error(f"Terminal auth failed for {self.host}:{self.port}")
            return False
        except Exception as e:
            logger.error(f"Terminal connection failed to {self.host}:{self.port} - {str(e)}")
            return False

    def send_input(self, data):
        """发送输入数据到终端"""
        if self.channel:
            try:
                self.channel.send(data)
            except Exception as e:
                logger.error(f"Failed to send input: {str(e)}")

    def resize(self, cols, rows):
        """调整终端大小"""
        if self.channel:
            try:
                self.channel.resize_pty(width=cols, height=rows)
            except Exception as e:
                logger.error(f"Failed to resize terminal: {str(e)}")

    def read_output(self, callback, check_interval=0.01):
        """读取终端输出并通过回调发送"""
        while not self._stop_event.is_set():
            try:
                if self.channel and self.channel.recv_ready():
                    data = self.channel.recv(4096)
                    if data:
                        callback(data.decode('utf-8', errors='replace'))
                else:
                    time.sleep(check_interval)
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"Error reading output: {str(e)}")
                break

    def disconnect(self):
        """关闭连接"""
        self._stop_event.set()
        if self.channel:
            try:
                self.channel.close()
            except Exception:
                pass
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        logger.info(f"Terminal disconnected from {self.host}:{self.port}")

    def is_connected(self):
        """检查连接状态"""
        return (
            self.client is not None and
            self.channel is not None and
            not self.channel.closed
        )
