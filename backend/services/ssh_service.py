import paramiko
import socket
import logging
from config import Config

logger = logging.getLogger(__name__)


class SSHService:
    """SSH连接服务类，用于远程服务器管理"""

    def __init__(self, host, port, username, password, timeout=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout or Config.SSH_TIMEOUT
        self.client = None

    def connect(self):
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            # SECURITY NOTE: AutoAddPolicy accepts all host keys automatically
            # In production, consider using WarningPolicy or loading known_hosts
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            logger.warning(
                f"Connecting to {self.host}:{self.port} with AutoAddPolicy "
                "(accepts any host key)"
            )

            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                banner_timeout=30,
                auth_timeout=30
            )
            logger.info(f"Successfully connected to {self.host}:{self.port}")
            return True
        except paramiko.AuthenticationException:
            logger.error(f"Authentication failed for {self.host}:{self.port}")
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH connection failed to {self.host}:{self.port} - {str(e)}")
            return False
        except socket.timeout:
            logger.error(f"Connection timeout to {self.host}:{self.port}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error connecting to {self.host}:{self.port} - {str(e)}"
            )
            return False

    def disconnect(self):
        """关闭SSH连接"""
        if self.client:
            self.client.close()

    def execute_command(self, command):
        """在远程服务器上执行命令"""
        if not self.client:
            return None

        try:
            _stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if error:
                logger.warning(f"Command error on {self.host}: {error}")

            return output
        except Exception as e:
            logger.error(f"Command execution failed on {self.host}: {str(e)}")
            return None

    def get_system_info(self):
        """获取系统信息"""
        if not self.connect():
            return None

        try:
            info = {}

            # OS Information
            os_info = self.execute_command(
                'cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d \'"\''
            )
            if not os_info:
                os_info = self.execute_command('uname -s')
            info['os'] = os_info or 'Unknown'

            # CPU Information
            cpu_count = self.execute_command('nproc')
            cpu_usage = self.execute_command(
                "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
            )
            if cpu_usage and cpu_count:
                info['cpu'] = f"{cpu_usage}% ({cpu_count} cores)"
            else:
                info['cpu'] = 'Unknown'

            # Memory Information
            mem_info = self.execute_command("free -h | awk 'NR==2{print $2,$3,$4}'")
            if mem_info:
                parts = mem_info.split()
                if len(parts) >= 3:
                    info['memory'] = f"Total: {parts[0]}, Used: {parts[1]}, Free: {parts[2]}"
                else:
                    info['memory'] = mem_info
            else:
                info['memory'] = 'Unknown'

            # Disk Information
            disk_info = self.execute_command("df -h / | awk 'NR==2{print $2,$3,$4,$5}'")
            if disk_info:
                parts = disk_info.split()
                if len(parts) >= 4:
                    info['disk'] = (
                        f"Total: {parts[0]}, Used: {parts[1]} ({parts[3]}), "
                        f"Free: {parts[2]}"
                    )
                else:
                    info['disk'] = disk_info
            else:
                info['disk'] = 'Unknown'

            # Uptime
            uptime = self.execute_command("uptime -p")
            if not uptime:
                uptime = self.execute_command("uptime | awk '{print $3,$4}'")
            info['uptime'] = uptime or 'Unknown'

            return info
        except Exception as e:
            logger.error(f"Failed to get system info from {self.host}: {str(e)}")
            return None
        finally:
            self.disconnect()

    def verify_credentials(self):
        """验证凭据是否正确"""
        result = self.connect()
        if result:
            self.disconnect()
        return result
