import socket
import subprocess
import platform
import logging
from config import Config

logger = logging.getLogger(__name__)

# IP段到地区的映射表（基于常见的云服务商IP段）
# 这是一个简化的映射，实际生产环境建议使用GeoIP数据库
IP_REGION_MAP = {
    # 香港 (Hong Kong) - 腾讯云香港
    '38.47.': 'HK',
    '103.10.': 'HK',
    '103.11.': 'HK',
    '103.12.': 'HK',
    '103.13.': 'HK',
    '103.14.': 'HK',
    '103.15.': 'HK',
    '103.16.': 'HK',
    '103.17.': 'HK',
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
    # 美国 (United States) - AWS US regions
    '3.80.': 'US',
    '3.81.': 'US',
    '3.82.': 'US',
    '3.83.': 'US',
    '3.84.': 'US',
    '3.85.': 'US',
    '3.86.': 'US',
    '3.87.': 'US',
    '3.88.': 'US',
    '3.89.': 'US',
    '3.90.': 'US',
    '3.91.': 'US',
    '3.92.': 'US',
    '3.93.': 'US',
    '3.94.': 'US',
    '3.95.': 'US',
    '3.208.': 'US',
    '3.209.': 'US',
    '3.210.': 'US',
    '3.211.': 'US',
    '3.212.': 'US',
    '3.213.': 'US',
    '3.214.': 'US',
    '3.215.': 'US',
    '3.216.': 'US',
    '3.217.': 'US',
    '3.218.': 'US',
    '3.219.': 'US',
    '3.220.': 'US',
    '3.221.': 'US',
    '3.222.': 'US',
    '3.223.': 'US',
    '3.224.': 'US',
    '3.225.': 'US',
    '3.226.': 'US',
    '3.227.': 'US',
    '3.228.': 'US',
    '3.229.': 'US',
    '3.230.': 'US',
    '3.231.': 'US',
    '3.232.': 'US',
    '3.233.': 'US',
    '3.234.': 'US',
    '3.235.': 'US',
    '3.236.': 'US',
    '34.192.': 'US',
    '34.193.': 'US',
    '34.194.': 'US',
    '34.195.': 'US',
    '34.196.': 'US',
    '34.197.': 'US',
    '34.198.': 'US',
    '34.199.': 'US',
    '34.200.': 'US',
    '34.201.': 'US',
    '34.202.': 'US',
    '34.203.': 'US',
    '34.204.': 'US',
    '34.205.': 'US',
    '34.206.': 'US',
    '34.207.': 'US',
    '34.208.': 'US',
    '34.209.': 'US',
    '34.210.': 'US',
    '34.211.': 'US',
    '34.212.': 'US',
    '34.213.': 'US',
    '34.214.': 'US',
    '34.215.': 'US',
    '34.216.': 'US',
    '34.217.': 'US',
    '34.218.': 'US',
    '34.219.': 'US',
    '34.220.': 'US',
    '34.221.': 'US',
    '34.222.': 'US',
    '34.223.': 'US',
    '52.0.': 'US',
    '52.1.': 'US',
    '52.2.': 'US',
    '52.3.': 'US',
    '52.4.': 'US',
    '52.5.': 'US',
    '52.6.': 'US',
    '52.7.': 'US',
    '52.20.': 'US',
    '52.21.': 'US',
    '52.22.': 'US',
    '52.23.': 'US',
    '52.24.': 'US',
    '52.25.': 'US',
    '52.26.': 'US',
    '52.27.': 'US',
    '54.80.': 'US',
    '54.81.': 'US',
    '54.82.': 'US',
    '54.83.': 'US',
    '54.84.': 'US',
    '54.85.': 'US',
    '54.86.': 'US',
    '54.87.': 'US',
    '54.88.': 'US',
    '54.89.': 'US',
    '54.90.': 'US',
    '54.91.': 'US',
    '54.92.': 'US',
    '54.93.': 'US',
    '54.144.': 'US',
    '54.145.': 'US',
    '54.146.': 'US',
    '54.147.': 'US',
    '54.148.': 'US',
    '54.149.': 'US',
    '54.152.': 'US',
    '54.153.': 'US',
    '54.156.': 'US',
    '54.157.': 'US',
    '54.158.': 'US',
    '54.159.': 'US',
    '54.160.': 'US',
    '54.161.': 'US',
    '54.162.': 'US',
    '54.163.': 'US',
    '54.164.': 'US',
    '54.165.': 'US',
    '54.166.': 'US',
    '54.167.': 'US',
    '54.168.': 'US',
    '54.169.': 'US',
    '104.196.': 'US',
    '104.197.': 'US',
    '104.198.': 'US',
    '104.199.': 'US',
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
    '54.95.': 'JP',
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
    # 中国大陆 (China Mainland) - 主要运营商IP段
    # 中国电信
    '1.192.': 'CN',
    '1.193.': 'CN',
    '1.194.': 'CN',
    '1.195.': 'CN',
    '1.196.': 'CN',
    '1.197.': 'CN',
    '1.198.': 'CN',
    '1.199.': 'CN',
    '14.16.': 'CN',
    '14.17.': 'CN',
    '14.18.': 'CN',
    '14.19.': 'CN',
    '14.20.': 'CN',
    '14.21.': 'CN',
    '14.22.': 'CN',
    '14.23.': 'CN',
    '27.16.': 'CN',
    '27.17.': 'CN',
    '27.18.': 'CN',
    '27.19.': 'CN',
    '36.96.': 'CN',
    '36.97.': 'CN',
    '36.98.': 'CN',
    '36.99.': 'CN',
    '36.100.': 'CN',
    '36.101.': 'CN',
    '36.102.': 'CN',
    '36.103.': 'CN',
    '39.128.': 'CN',
    '39.129.': 'CN',
    '39.130.': 'CN',
    '39.131.': 'CN',
    '42.80.': 'CN',
    '42.81.': 'CN',
    '42.82.': 'CN',
    '42.83.': 'CN',
    '58.32.': 'CN',
    '58.33.': 'CN',
    '58.34.': 'CN',
    '58.35.': 'CN',
    '59.32.': 'CN',
    '59.33.': 'CN',
    '59.34.': 'CN',
    '59.35.': 'CN',
    '60.0.': 'CN',
    '60.1.': 'CN',
    '60.2.': 'CN',
    '60.3.': 'CN',
    # 中国联通
    '101.16.': 'CN',
    '101.17.': 'CN',
    '101.18.': 'CN',
    '101.19.': 'CN',
    '106.32.': 'CN',
    '106.33.': 'CN',
    '106.34.': 'CN',
    '106.35.': 'CN',
    '110.80.': 'CN',
    '110.81.': 'CN',
    '110.82.': 'CN',
    '110.83.': 'CN',
    '111.0.': 'CN',
    '111.1.': 'CN',
    '111.2.': 'CN',
    '111.3.': 'CN',
    '112.64.': 'CN',
    '112.65.': 'CN',
    '112.66.': 'CN',
    '112.67.': 'CN',
    '113.96.': 'CN',
    '113.97.': 'CN',
    '113.98.': 'CN',
    '113.99.': 'CN',
    # 中国移动
    '117.128.': 'CN',
    '117.129.': 'CN',
    '117.130.': 'CN',
    '117.131.': 'CN',
    '120.192.': 'CN',
    '120.193.': 'CN',
    '120.194.': 'CN',
    '120.195.': 'CN',
    '183.192.': 'CN',
    '183.193.': 'CN',
    '183.194.': 'CN',
    '183.195.': 'CN',
    # 阿里云
    '47.92.': 'CN',
    '47.93.': 'CN',
    '47.94.': 'CN',
    '47.95.': 'CN',
    '47.96.': 'CN',
    '47.97.': 'CN',
    '47.98.': 'CN',
    '47.99.': 'CN',
    '47.100.': 'CN',
    '47.101.': 'CN',
    '47.102.': 'CN',
    '47.103.': 'CN',
    '47.104.': 'CN',
    '47.105.': 'CN',
    '47.106.': 'CN',
    '47.107.': 'CN',
    '47.108.': 'CN',
    '47.109.': 'CN',
    '47.110.': 'CN',
    '47.111.': 'CN',
    '120.76.': 'CN',
    '120.77.': 'CN',
    '120.78.': 'CN',
    '120.79.': 'CN',
    # 腾讯云
    '129.204.': 'CN',
    '129.205.': 'CN',
    '129.206.': 'CN',
    '129.207.': 'CN',
    '119.27.': 'CN',
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
        # Only attempt SSH authentication for SSH port (not RDP/3389, Telnet/23, etc.)
        # Other protocols use different authentication mechanisms
        ssh_port = 22
        if username and password and status['port'] and port == ssh_port:
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
