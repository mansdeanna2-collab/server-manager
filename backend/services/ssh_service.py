import paramiko
import socket
import logging
import os
from config import Config

logger = logging.getLogger(__name__)


def _validate_remote_path(path, path_type='file'):
    """验证远程路径的安全性

    Args:
        path: 要验证的路径
        path_type: 路径类型 ('file' 或 'directory')，用于错误消息

    Returns:
        dict: 包含验证结果，成功时返回 {'valid': True}，
              失败时返回 {'valid': False, 'message': str, 'error_type': str}
    """
    type_name = '文件' if path_type == 'file' else '目录'

    if not path or not path.startswith('/'):
        return {
            'valid': False,
            'message': f'{type_name}路径必须以 / 开头',
            'error_type': 'invalid_path'
        }

    # 规范化路径并检查是否尝试通过 .. 逃逸
    # 使用 os.path.normpath 处理 .. 和 . 序列
    normalized = os.path.normpath(path)

    # 检查规范化后的路径是否仍然以 / 开头
    # 并且不包含 .. 在路径开始（表示尝试逃逸根目录）
    if not normalized.startswith('/'):
        return {
            'valid': False,
            'message': f'{type_name}路径无效',
            'error_type': 'invalid_path'
        }

    # 检查危险的 shell 特殊字符（不包括 ..，因为已经通过 normpath 处理）
    dangerous_patterns = [';', '|', '&', '$', '`', '\n', '\r']
    for pattern in dangerous_patterns:
        if pattern in path:
            return {
                'valid': False,
                'message': f'{type_name}路径包含不允许的字符',
                'error_type': 'invalid_path'
            }

    return {'valid': True}


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

    def verify_credentials_detailed(self):
        """验证凭据并返回详细信息"""
        try:
            self.client = paramiko.SSHClient()
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
            self.disconnect()
            return {
                'success': True,
                'message': '认证成功',
                'error_type': None
            }
        except paramiko.AuthenticationException:
            logger.error(f"Authentication failed for {self.host}:{self.port}")
            return {
                'success': False,
                'message': '密码错误或用户名不存在',
                'error_type': 'auth_failed'
            }
        except paramiko.SSHException as e:
            logger.error(f"SSH connection failed to {self.host}:{self.port} - {str(e)}")
            error_msg = str(e).lower()
            if 'no existing session' in error_msg:
                return {
                    'success': False,
                    'message': 'SSH协议错误',
                    'error_type': 'ssh_error'
                }
            return {
                'success': False,
                'message': f'SSH连接失败: {str(e)}',
                'error_type': 'ssh_error'
            }
        except socket.timeout:
            logger.error(f"Connection timeout to {self.host}:{self.port}")
            return {
                'success': False,
                'message': '连接超时',
                'error_type': 'timeout'
            }
        except Exception as e:
            logger.error(
                f"Unexpected error connecting to {self.host}:{self.port} - {str(e)}"
            )
            return {
                'success': False,
                'message': f'连接错误: {str(e)}',
                'error_type': 'connection_error'
            }

    def read_remote_file(self, file_path):
        """读取远程服务器上的文件内容

        Args:
            file_path: 远程服务器上的文件路径

        Returns:
            dict: 包含文件内容或错误信息的字典
        """
        # 验证文件路径安全性
        validation = _validate_remote_path(file_path, 'file')
        if not validation['valid']:
            return {
                'success': False,
                'message': validation['message'],
                'error_type': validation['error_type']
            }

        if not self.connect():
            return {
                'success': False,
                'message': '无法连接到服务器',
                'error_type': 'connection_error'
            }

        try:
            # 使用 shlex.quote 进行 shell 转义以防止命令注入
            import shlex
            safe_path = shlex.quote(file_path)

            # 先检查文件是否存在
            file_exists = self.execute_command(f'test -f {safe_path} && echo "exists"')
            if file_exists != 'exists':
                return {
                    'success': False,
                    'message': f'文件不存在: {file_path}',
                    'error_type': 'file_not_found'
                }

            # 使用 cat 命令读取文件内容
            content = self.execute_command(f'cat {safe_path}')

            if content is None:
                return {
                    'success': False,
                    'message': f'无法读取文件: {file_path}',
                    'error_type': 'read_error'
                }

            return {
                'success': True,
                'content': content,
                'file_path': file_path
            }
        except Exception as e:
            logger.error(f"Failed to read file {file_path} from {self.host}: {str(e)}")
            return {
                'success': False,
                'message': f'读取文件失败: {str(e)}',
                'error_type': 'read_error'
            }
        finally:
            self.disconnect()

    def list_directory(self, dir_path):
        """列出远程服务器上的目录内容

        Args:
            dir_path: 远程服务器上的目录路径

        Returns:
            dict: 包含目录文件列表或错误信息的字典
        """
        # 验证目录路径安全性
        validation = _validate_remote_path(dir_path, 'directory')
        if not validation['valid']:
            return {
                'success': False,
                'message': validation['message'],
                'error_type': validation['error_type']
            }

        if not self.connect():
            return {
                'success': False,
                'message': '无法连接到服务器',
                'error_type': 'connection_error'
            }

        try:
            import shlex
            safe_path = shlex.quote(dir_path)

            # 检查目录是否存在
            dir_exists = self.execute_command(f'test -d {safe_path} && echo "exists"')
            if dir_exists != 'exists':
                return {
                    'success': False,
                    'message': f'目录不存在: {dir_path}',
                    'error_type': 'dir_not_found'
                }

            # 使用 ls -la 命令获取目录内容，格式化输出
            # 输出格式: type|permissions|size|name
            # type: d=目录, -=文件, l=链接
            ls_output = self.execute_command(
                f'ls -la {safe_path} | tail -n +2'
            )

            if ls_output is None:
                return {
                    'success': False,
                    'message': f'无法读取目录: {dir_path}',
                    'error_type': 'read_error'
                }

            files = []
            for line in ls_output.split('\n'):
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) < 9:
                    continue

                permissions = parts[0]
                size = parts[4]
                name = ' '.join(parts[8:])  # 文件名可能包含空格

                # 跳过 . 和 .. 目录
                if name in ['.', '..']:
                    continue

                file_type = 'directory' if permissions.startswith('d') else 'file'
                if permissions.startswith('l'):
                    file_type = 'link'

                files.append({
                    'name': name,
                    'type': file_type,
                    'size': size,
                    'permissions': permissions
                })

            # 按类型和名称排序：目录在前，文件在后
            files.sort(key=lambda x: (0 if x['type'] == 'directory' else 1, x['name'].lower()))

            return {
                'success': True,
                'path': dir_path,
                'files': files
            }
        except Exception as e:
            logger.error(f"Failed to list directory {dir_path} from {self.host}: {str(e)}")
            return {
                'success': False,
                'message': f'读取目录失败: {str(e)}',
                'error_type': 'read_error'
            }
        finally:
            self.disconnect()

    def write_remote_file(self, file_path, content):
        """写入内容到远程服务器上的文件

        Args:
            file_path: 远程服务器上的文件路径
            content: 要写入的内容

        Returns:
            dict: 包含操作结果或错误信息的字典
        """
        # 验证文件路径安全性
        validation = _validate_remote_path(file_path, 'file')
        if not validation['valid']:
            return {
                'success': False,
                'message': validation['message'],
                'error_type': validation['error_type']
            }

        if not self.connect():
            return {
                'success': False,
                'message': '无法连接到服务器',
                'error_type': 'connection_error'
            }

        try:
            # 使用 SFTP 写入文件
            sftp = self.client.open_sftp()
            try:
                with sftp.file(file_path, 'w') as f:
                    f.write(content)

                return {
                    'success': True,
                    'message': '文件保存成功',
                    'file_path': file_path
                }
            finally:
                sftp.close()
        except PermissionError:
            logger.error(f"Permission denied writing to {file_path} on {self.host}")
            return {
                'success': False,
                'message': f'没有权限写入文件: {file_path}',
                'error_type': 'permission_denied'
            }
        except Exception as e:
            logger.error(f"Failed to write file {file_path} to {self.host}: {str(e)}")
            return {
                'success': False,
                'message': f'写入文件失败: {str(e)}',
                'error_type': 'write_error'
            }
        finally:
            self.disconnect()
