import socket
import subprocess
import platform
import logging
from config import Config

logger = logging.getLogger(__name__)

class CheckService:
    @staticmethod
    def _get_ping_command(host, timeout):
        """Get platform-specific ping command"""
        system = platform.system().lower()
        
        if system == 'windows':
            # Windows: ping -n 1 -w <timeout_ms> <host>
            return ['ping', '-n', '1', '-w', str(timeout * 1000), host]
        else:
            # Linux/Unix: ping -c 1 -W <timeout_sec> <host>
            return ['ping', '-c', '1', '-W', str(timeout), host]
    
    @staticmethod
    def ping_check(host, timeout=None):
        """Check if host is reachable via ping"""
        timeout = timeout or Config.PING_TIMEOUT
        try:
            command = CheckService._get_ping_command(host, timeout)
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout + 1)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error(f"Ping timeout for {host}")
            return False
        except Exception as e:
            logger.error(f"Ping check failed for {host}: {str(e)}")
            return False
    
    @staticmethod
    def port_check(host, port, timeout=None):
        """Check if a specific port is open"""
        timeout = timeout or Config.PORT_TIMEOUT
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except socket.timeout:
            logger.error(f"Port check timeout for {host}:{port}")
            return False
        except Exception as e:
            logger.error(f"Port check failed for {host}:{port} - {str(e)}")
            return False
    
    @staticmethod
    def check_server_status(host, port, username=None, password=None):
        """Comprehensive server status check"""
        status = {
            'ping': False,
            'port': False,
            'auth': None,
            'overall': 'offline'
        }
        
        # Check ping
        status['ping'] = CheckService.ping_check(host)
        
        # Check port
        status['port'] = CheckService.port_check(host, port)
        
        # Check authentication if credentials provided
        if username and password and status['port']:
            from services.ssh_service import SSHService
            ssh = SSHService(host, port, username, password)
            status['auth'] = ssh.verify_credentials()
        
        # Determine overall status
        if status['ping'] and status['port']:
            status['overall'] = 'online'
        else:
            status['overall'] = 'offline'
        
        return status
