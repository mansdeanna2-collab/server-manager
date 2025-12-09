import socket
import subprocess
import platform
import logging
from config import Config

logger = logging.getLogger(__name__)

# IP段到地区的映射表（基于常见的云服务商IP段）
# 这是一个简化的映射，实际生产环境建议使用GeoIP数据库
IP_REGION_MAP = {
    # 香港 (Hong Kong)
    '103.': 'HK',
    '119.28.': 'HK',
    '119.29.': 'HK',
    '150.109.': 'HK',
    '162.14.': 'HK',
    '175.24.': 'HK',
    '175.45.': 'HK',
    # 新加坡 (Singapore)
    '13.212.': 'SG',
    '13.213.': 'SG',
    '13.214.': 'SG',
    '13.215.': 'SG',
    '18.136.': 'SG',
    '18.137.': 'SG',
    '18.138.': 'SG',
    '18.139.': 'SG',
    '18.140.': 'SG',
    '18.141.': 'SG',
    '52.74.': 'SG',
    '52.76.': 'SG',
    '52.77.': 'SG',
    '54.179.': 'SG',
    '54.251.': 'SG',
    '54.254.': 'SG',
    '54.255.': 'SG',
    # 美国 (United States)
    '3.': 'US',
    '18.': 'US',
    '34.': 'US',
    '35.': 'US',
    '52.': 'US',
    '54.': 'US',
    '104.': 'US',
    '142.': 'US',
    '172.': 'US',
    '198.': 'US',
    '199.': 'US',
    # 日本 (Japan)
    '13.112.': 'JP',
    '13.113.': 'JP',
    '13.114.': 'JP',
    '13.115.': 'JP',
    '18.176.': 'JP',
    '18.177.': 'JP',
    '18.178.': 'JP',
    '18.179.': 'JP',
    '18.180.': 'JP',
    '18.181.': 'JP',
    '18.182.': 'JP',
    '18.183.': 'JP',
    '52.68.': 'JP',
    '52.69.': 'JP',
    '52.192.': 'JP',
    '52.193.': 'JP',
    '52.194.': 'JP',
    '52.195.': 'JP',
    '52.196.': 'JP',
    '52.197.': 'JP',
    '52.198.': 'JP',
    '52.199.': 'JP',
    '54.64.': 'JP',
    '54.65.': 'JP',
    '54.92.': 'JP',
    '54.95.': 'JP',
    '54.168.': 'JP',
    '54.178.': 'JP',
    '54.199.': 'JP',
    '54.238.': 'JP',
    '54.250.': 'JP',
    # 韩国 (South Korea)
    '13.124.': 'KR',
    '13.125.': 'KR',
    '13.209.': 'KR',
    '15.164.': 'KR',
    '15.165.': 'KR',
    '52.78.': 'KR',
    '52.79.': 'KR',
    # 德国 (Germany)
    '3.120.': 'DE',
    '3.121.': 'DE',
    '3.122.': 'DE',
    '3.123.': 'DE',
    '3.124.': 'DE',
    '3.125.': 'DE',
    '3.126.': 'DE',
    '3.127.': 'DE',
    '18.184.': 'DE',
    '18.185.': 'DE',
    '52.28.': 'DE',
    '52.29.': 'DE',
    '52.57.': 'DE',
    '52.58.': 'DE',
    '52.59.': 'DE',
    # 英国 (United Kingdom)
    '3.8.': 'UK',
    '3.9.': 'UK',
    '3.10.': 'UK',
    '3.11.': 'UK',
    '18.130.': 'UK',
    '18.132.': 'UK',
    '18.133.': 'UK',
    '18.134.': 'UK',
    '18.135.': 'UK',
    '35.176.': 'UK',
    '35.177.': 'UK',
    '35.178.': 'UK',
    '35.179.': 'UK',
    # 澳大利亚 (Australia)
    '3.104.': 'AU',
    '3.105.': 'AU',
    '3.106.': 'AU',
    '13.54.': 'AU',
    '13.55.': 'AU',
    '13.210.': 'AU',
    '13.211.': 'AU',
    '52.62.': 'AU',
    '52.63.': 'AU',
    '52.64.': 'AU',
    '52.65.': 'AU',
    '54.66.': 'AU',
    '54.79.': 'AU',
    '54.153.': 'AU',
    '54.206.': 'AU',
    '54.252.': 'AU',
    '54.253.': 'AU',
    # 台湾 (Taiwan)
    '61.216.': 'TW',
    '61.217.': 'TW',
    '61.218.': 'TW',
    '61.219.': 'TW',
    '61.220.': 'TW',
    '61.221.': 'TW',
    '61.222.': 'TW',
    '61.223.': 'TW',
    '114.32.': 'TW',
    '114.33.': 'TW',
    '114.34.': 'TW',
    '114.35.': 'TW',
    '114.36.': 'TW',
    '114.37.': 'TW',
    '114.38.': 'TW',
    '114.39.': 'TW',
    '114.40.': 'TW',
    '114.41.': 'TW',
    '114.42.': 'TW',
    '114.43.': 'TW',
    '114.44.': 'TW',
    '114.45.': 'TW',
    '114.46.': 'TW',
    '114.47.': 'TW',
    # 中国大陆 (China Mainland)
    '1.': 'CN',
    '14.': 'CN',
    '27.': 'CN',
    '36.': 'CN',
    '39.': 'CN',
    '42.': 'CN',
    '49.': 'CN',
    '58.': 'CN',
    '59.': 'CN',
    '60.': 'CN',
    '61.': 'CN',
    '101.': 'CN',
    '106.': 'CN',
    '110.': 'CN',
    '111.': 'CN',
    '112.': 'CN',
    '113.': 'CN',
    '114.': 'CN',
    '115.': 'CN',
    '116.': 'CN',
    '117.': 'CN',
    '118.': 'CN',
    '119.': 'CN',
    '120.': 'CN',
    '121.': 'CN',
    '122.': 'CN',
    '123.': 'CN',
    '124.': 'CN',
    '125.': 'CN',
    '180.': 'CN',
    '182.': 'CN',
    '183.': 'CN',
    '202.': 'CN',
    '218.': 'CN',
    '219.': 'CN',
    '220.': 'CN',
    '221.': 'CN',
    '222.': 'CN',
    '223.': 'CN',
}

# 地区显示信息
REGION_INFO = {
    'HK': {'name': '香港', 'flag': '🇭🇰', 'name_en': 'Hong Kong'},
    'SG': {'name': '新加坡', 'flag': '🇸🇬', 'name_en': 'Singapore'},
    'US': {'name': '美国', 'flag': '🇺🇸', 'name_en': 'United States'},
    'JP': {'name': '日本', 'flag': '🇯🇵', 'name_en': 'Japan'},
    'KR': {'name': '韩国', 'flag': '🇰🇷', 'name_en': 'South Korea'},
    'DE': {'name': '德国', 'flag': '🇩🇪', 'name_en': 'Germany'},
    'UK': {'name': '英国', 'flag': '🇬🇧', 'name_en': 'United Kingdom'},
    'AU': {'name': '澳大利亚', 'flag': '🇦🇺', 'name_en': 'Australia'},
    'TW': {'name': '台湾', 'flag': '🇹🇼', 'name_en': 'Taiwan'},
    'CN': {'name': '中国', 'flag': '🇨🇳', 'name_en': 'China'},
    'UNKNOWN': {'name': '未知', 'flag': '🌐', 'name_en': 'Unknown'},
}


class CheckService:
    """服务器状态检查服务类"""

    @staticmethod
    def get_ip_region(ip_address):
        """根据IP地址获取地区信息"""
        if not ip_address:
            return REGION_INFO['UNKNOWN']

        # 按照前缀长度从长到短排序，优先匹配更精确的
        sorted_prefixes = sorted(IP_REGION_MAP.keys(), key=len, reverse=True)

        for prefix in sorted_prefixes:
            if ip_address.startswith(prefix):
                region_code = IP_REGION_MAP[prefix]
                return {
                    'code': region_code,
                    **REGION_INFO.get(region_code, REGION_INFO['UNKNOWN'])
                }

        return {'code': 'UNKNOWN', **REGION_INFO['UNKNOWN']}

    @staticmethod
    def get_port_type(port):
        """根据端口获取服务类型"""
        port_types = {
            22: {'type': 'SSH', 'os_hint': 'Linux/Unix', 'icon': '🐧'},
            3389: {'type': 'RDP', 'os_hint': 'Windows', 'icon': '🪟'},
            23: {'type': 'Telnet', 'os_hint': 'Network Device', 'icon': '📡'},
            21: {'type': 'FTP', 'os_hint': 'File Server', 'icon': '📁'},
            80: {'type': 'HTTP', 'os_hint': 'Web Server', 'icon': '🌐'},
            443: {'type': 'HTTPS', 'os_hint': 'Web Server', 'icon': '🔒'},
            3306: {'type': 'MySQL', 'os_hint': 'Database', 'icon': '🗄️'},
            5432: {'type': 'PostgreSQL', 'os_hint': 'Database', 'icon': '🗄️'},
            6379: {'type': 'Redis', 'os_hint': 'Cache', 'icon': '⚡'},
            27017: {'type': 'MongoDB', 'os_hint': 'Database', 'icon': '🗄️'},
        }
        return port_types.get(port, {'type': 'Custom', 'os_hint': 'Unknown', 'icon': '🔌'})

    @staticmethod
    def _get_ping_command(host, timeout):
        """获取特定平台的ping命令"""
        system = platform.system().lower()

        if system == 'windows':
            # Windows: ping -n 1 -w <timeout_ms> <host>
            return ['ping', '-n', '1', '-w', str(timeout * 1000), host]
        else:
            # Linux/Unix: ping -c 1 -W <timeout_sec> <host>
            return ['ping', '-c', '1', '-W', str(timeout), host]

    @staticmethod
    def ping_check(host, timeout=None):
        """通过ping检查主机是否可达"""
        timeout = timeout or Config.PING_TIMEOUT
        try:
            command = CheckService._get_ping_command(host, timeout)
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout + 1
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error(f"Ping timeout for {host}")
            return False
        except Exception as e:
            logger.error(f"Ping check failed for {host}: {str(e)}")
            return False

    @staticmethod
    def port_check(host, port, timeout=None):
        """检查特定端口是否开放"""
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
        """综合服务器状态检查"""
        status = {
            'ping': False,
            'port': False,
            'auth': None,
            'overall': 'offline',
            'region': CheckService.get_ip_region(host),
            'port_type': CheckService.get_port_type(port),
            'detail': '',
            'error_type': None
        }

        # Check ping
        status['ping'] = CheckService.ping_check(host)

        # Check port
        status['port'] = CheckService.port_check(host, port)

        # Determine detailed status message
        if not status['ping'] and not status['port']:
            status['detail'] = '主机不可达，端口关闭'
            status['error_type'] = 'unreachable'
        elif status['ping'] and not status['port']:
            status['detail'] = f'主机可达，但端口 {port} 关闭'
            status['error_type'] = 'port_closed'
        elif status['port']:
            status['detail'] = f'端口 {port} ({status["port_type"]["type"]}) 开放'

        # Check authentication if credentials provided
        if username and password and status['port']:
            from services.ssh_service import SSHService
            ssh = SSHService(host, port, username, password)
            auth_result = ssh.verify_credentials_detailed()
            status['auth'] = auth_result.get('success', False)
            if not status['auth']:
                status['error_type'] = auth_result.get('error_type', 'auth_failed')
                status['detail'] = auth_result.get('message', '认证失败')
            else:
                status['detail'] = f'连接成功 ({status["port_type"]["type"]})'

        # Determine overall status
        if status['auth'] is True or status['port'] is True or status['ping'] is True:
            status['overall'] = 'online'
        else:
            status['overall'] = 'offline'

        return status
