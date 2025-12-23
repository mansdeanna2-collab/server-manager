"""SSL Certificate Generation Service

This module provides functionality for:
1. Detecting whether an address is an IP or domain
2. Generating self-signed SSL certificates
3. Managing SSL configuration
"""

import os
import re
import shutil
import socket
import ipaddress
import subprocess
import logging
import urllib.request
import urllib.error
from datetime import datetime

logger = logging.getLogger(__name__)

# Default SSL certificate directory (used when /etc/ssl is writable, e.g., in Docker)
DEFAULT_SSL_DIR = '/etc/ssl/server-manager'
# Fallback to local directory if /etc/ssl is not writable
LOCAL_SSL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ssl')
# Project root ssl directory - preferred for Docker deployments as it can be mounted
PROJECT_SSL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'ssl')


def is_valid_ip(address):
    """Check if the address is a valid IPv4 or IPv6 address"""
    try:
        ipaddress.ip_address(address.strip())
        return True
    except ValueError:
        return False


def is_valid_domain(address):
    """Check if the address is a valid domain name"""
    # Domain name regex pattern
    domain_pattern = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    )
    return bool(domain_pattern.match(address.strip()))


def detect_address_type(address):
    """Detect whether the address is an IP or domain

    Returns:
        dict: {
            'type': 'ip' | 'domain' | 'unknown',
            'address': the cleaned address,
            'is_valid': whether the address is valid,
            'message': description message
        }
    """
    address = address.strip()

    if not address:
        return {
            'type': 'unknown',
            'address': '',
            'is_valid': False,
            'message': '请输入地址'
        }

    # Check if it's an IP address
    if is_valid_ip(address):
        return {
            'type': 'ip',
            'address': address,
            'is_valid': True,
            'message': f'检测到IP地址: {address}'
        }

    # Check if it's a domain
    if is_valid_domain(address):
        return {
            'type': 'domain',
            'address': address,
            'is_valid': True,
            'message': f'检测到域名: {address}'
        }

    return {
        'type': 'unknown',
        'address': address,
        'is_valid': False,
        'message': f'无法识别的地址格式: {address}'
    }


def get_ssl_directory():
    """Get the SSL directory, creating it if necessary

    For Docker deployments, prioritizes directories that can be mounted between containers.

    Priority order:
    1. /etc/ssl/server-manager (Docker volume mount point)
    2. Project root ssl directory (can be mounted in docker-compose)
    3. Backend local ssl directory (fallback)

    Returns:
        str: Path to SSL directory
    """
    # Try the Docker/system directory first (used when mounted via docker-compose)
    if os.path.exists('/etc/ssl/server-manager') or (os.path.exists('/etc/ssl') and os.access('/etc/ssl', os.W_OK)):
        ssl_dir = DEFAULT_SSL_DIR
        try:
            if not os.path.exists(ssl_dir):
                os.makedirs(ssl_dir, mode=0o755)
                logger.info(f"Created SSL directory: {ssl_dir}")
            return ssl_dir
        except PermissionError:
            pass  # Fall through to next option

    # Try project root ssl directory (for Docker deployments)
    try:
        if not os.path.exists(PROJECT_SSL_DIR):
            os.makedirs(PROJECT_SSL_DIR, mode=0o755)
            logger.info(f"Created project SSL directory: {PROJECT_SSL_DIR}")
        return PROJECT_SSL_DIR
    except (PermissionError, OSError):
        pass  # Fall through to local directory

    # Fall back to backend local directory
    ssl_dir = LOCAL_SSL_DIR
    if not os.path.exists(ssl_dir):
        os.makedirs(ssl_dir, mode=0o755)
        logger.info(f"Created local SSL directory: {ssl_dir}")

    return ssl_dir


def generate_self_signed_certificate(address, address_type='ip'):
    """Generate a self-signed SSL certificate

    Args:
        address: IP address or domain name
        address_type: 'ip' or 'domain'

    Returns:
        dict: {
            'success': bool,
            'cert_path': path to certificate file,
            'key_path': path to private key file,
            'message': result message
        }
    """
    ssl_dir = get_ssl_directory()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # File names - use fixed names that nginx expects
    # This makes it easier for Docker to mount and use the certificates
    key_file = os.path.join(ssl_dir, 'server.key')
    cert_file = os.path.join(ssl_dir, 'server.crt')

    # Also create timestamped backup copies
    key_file_backup = os.path.join(ssl_dir, f'server_{timestamp}.key')
    cert_file_backup = os.path.join(ssl_dir, f'server_{timestamp}.crt')

    # Build Subject Alternative Name (SAN) based on address type
    if address_type == 'ip':
        cn = address
        alt_names_section = f"IP.1 = {address}"
    else:
        cn = address
        alt_names_section = f"DNS.1 = {address}"

    # OpenSSL config for SAN
    openssl_config = f'''[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
CN = {cn}
O = Server Manager
OU = Auto Generated
C = CN

[v3_req]
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[v3_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, keyEncipherment, keyCertSign
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
{alt_names_section}
'''

    # Write temporary config file
    config_file = os.path.join(ssl_dir, f'openssl_{timestamp}.cnf')
    try:
        with open(config_file, 'w') as f:
            f.write(openssl_config)

        # Generate private key and certificate
        cmd = [
            'openssl', 'req', '-x509',
            '-newkey', 'rsa:2048',
            '-keyout', key_file,
            '-out', cert_file,
            '-sha256',
            '-days', '3650',  # 10 years validity
            '-nodes',  # No password
            '-config', config_file
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(f"OpenSSL error: {result.stderr}")
            return {
                'success': False,
                'cert_path': '',
                'key_path': '',
                'message': f'生成证书失败: {result.stderr}'
            }

        # Set proper permissions
        os.chmod(key_file, 0o600)  # Private key: owner read only
        os.chmod(cert_file, 0o644)  # Certificate: readable by all

        # Create backup copies with timestamps
        shutil.copy2(key_file, key_file_backup)
        shutil.copy2(cert_file, cert_file_backup)
        os.chmod(key_file_backup, 0o600)

        logger.info(f"Generated SSL certificate: {cert_file}")
        logger.info(f"Backup certificate created: {cert_file_backup}")
        return {
            'success': True,
            'cert_path': cert_file,
            'key_path': key_file,
            'message': 'SSL证书已生成（自签名，有效期10年）'
        }

    except subprocess.TimeoutExpired:
        logger.error("OpenSSL command timed out")
        return {
            'success': False,
            'cert_path': '',
            'key_path': '',
            'message': '生成证书超时'
        }
    except Exception as e:
        logger.error(f"Error generating certificate: {str(e)}")
        return {
            'success': False,
            'cert_path': '',
            'key_path': '',
            'message': f'生成证书失败: {str(e)}'
        }
    finally:
        # Clean up config file
        if os.path.exists(config_file):
            try:
                os.remove(config_file)
            except Exception:
                pass


def verify_certificate(cert_path, key_path):
    """Verify that certificate and key files exist and are valid

    Args:
        cert_path: Path to certificate file
        key_path: Path to private key file

    Returns:
        dict: {
            'valid': bool,
            'message': result message,
            'details': additional details
        }
    """
    details = {}

    # Check file existence
    if not os.path.exists(cert_path):
        return {
            'valid': False,
            'message': f'证书文件不存在: {cert_path}',
            'details': {}
        }

    if not os.path.exists(key_path):
        return {
            'valid': False,
            'message': f'私钥文件不存在: {key_path}',
            'details': {}
        }

    try:
        # Verify certificate with openssl
        result = subprocess.run(
            ['openssl', 'x509', '-in', cert_path, '-text', '-noout'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return {
                'valid': False,
                'message': f'无效的证书文件: {result.stderr}',
                'details': {}
            }

        # Parse certificate details
        output = result.stdout
        if 'Subject:' in output:
            subject_line = [line for line in output.split('\n') if 'Subject:' in line]
            if subject_line:
                details['subject'] = subject_line[0].strip()

        if 'Not After' in output:
            expiry_line = [line for line in output.split('\n') if 'Not After' in line]
            if expiry_line:
                details['expires'] = expiry_line[0].strip()

        # Verify key matches certificate using public key comparison (works for all key types)
        key_pubkey = subprocess.run(
            ['openssl', 'pkey', '-in', key_path, '-pubout', '-outform', 'PEM'],
            capture_output=True,
            text=True,
            timeout=30
        )

        cert_pubkey = subprocess.run(
            ['openssl', 'x509', '-in', cert_path, '-pubkey', '-noout'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if key_pubkey.returncode != 0 or cert_pubkey.returncode != 0:
            # Provide detailed error message
            error_detail = key_pubkey.stderr.strip() if key_pubkey.returncode != 0 else cert_pubkey.stderr.strip()
            if not error_detail:
                error_detail = '未知错误'
            return {
                'valid': False,
                'message': f'无法验证证书和私钥的匹配性: {error_detail}',
                'details': details
            }

        # Compare public keys extracted from certificate and private key
        if key_pubkey.stdout.strip() != cert_pubkey.stdout.strip():
            return {
                'valid': False,
                'message': '证书和私钥不匹配',
                'details': details
            }

        return {
            'valid': True,
            'message': '证书验证通过',
            'details': details
        }

    except subprocess.TimeoutExpired:
        return {
            'valid': False,
            'message': '证书验证超时',
            'details': {}
        }
    except Exception as e:
        return {
            'valid': False,
            'message': f'证书验证失败: {str(e)}',
            'details': {}
        }


def _is_private_ip(ip_str):
    """Check if an IP address is in a private/reserved range.

    Private IP ranges include:
    - 10.0.0.0/8 (Class A private)
    - 172.16.0.0/12 (Class B private, includes 172.16.x.x to 172.31.x.x)
    - 192.168.0.0/16 (Class C private)
    - 169.254.0.0/16 (link-local)
    - 127.0.0.0/8 (loopback)

    Args:
        ip_str: IP address string

    Returns:
        bool: True if the IP is private/reserved, False otherwise
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def _get_external_ip():
    """Try to get the external/public IP address using external services.

    This is useful for Docker environments where the container's internal IP
    differs from the host's external IP that users actually use to access the service.

    Returns:
        str or None: External IP address if successful, None otherwise
    """
    # List of services that return the public IP in plain text
    ip_services = [
        'https://api.ipify.org',
        'https://ifconfig.me/ip',
        'https://icanhazip.com',
        'https://ipinfo.io/ip',
    ]

    for service_url in ip_services:
        try:
            # Use a short timeout to avoid long waits
            req = urllib.request.Request(
                service_url,
                headers={'User-Agent': 'curl/7.68.0'}  # Some services require User-Agent
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                ip = response.read().decode('utf-8').strip()
                # Validate the response is a valid IP
                if ip and is_valid_ip(ip):
                    logger.info(f"Detected external IP from {service_url}: {ip}")
                    return ip
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as e:
            logger.debug(f"Failed to get IP from {service_url}: {str(e)}")
            continue

    return None


def get_server_address():
    """Try to detect the server's IP address

    This function attempts to detect the server's IP address through multiple methods:
    1. Try to get external/public IP using external services (useful for Docker)
    2. Get hostname and resolve it
    3. Get outbound IP by checking network routing
    4. Fall back to localhost if all else fails

    Returns:
        dict: {
            'address': detected IP address,
            'type': 'ip' (always returns IP type),
            'message': result message
        }
    """
    # First, try to get the external/public IP address
    # This is especially important for Docker environments where internal IPs
    # differ from the external IP users use to access the service
    external_ip = _get_external_ip()
    if external_ip:
        return {
            'address': external_ip,
            'type': 'ip',
            'message': f'检测到服务器外部IP: {external_ip}'
        }

    # Try to get hostname and resolve it to IP
    try:
        hostname = socket.gethostname()
        try:
            ip = socket.gethostbyname(hostname)
            # Check if this is not a Docker/container internal IP
            if not _is_private_ip(ip):
                return {
                    'address': ip,
                    'type': 'ip',
                    'message': f'检测到服务器IP: {ip}'
                }
        except socket.gaierror:
            pass
    except Exception:
        pass

    # Try to get outbound IP by checking network routing
    # This creates a UDP socket and connects to check the local interface
    # No actual data is sent; it just determines which local IP would be used
    # Multiple DNS servers are tried as fallbacks
    dns_servers = ['8.8.8.8', '1.1.1.1', '114.114.114.114']
    for dns_ip in dns_servers:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.connect((dns_ip, 53))
            ip = s.getsockname()[0]
            s.close()
            # Check if this is not a Docker/container internal IP
            if not _is_private_ip(ip):
                return {
                    'address': ip,
                    'type': 'ip',
                    'message': f'检测到服务器IP: {ip}'
                }
        except Exception:
            pass

    # Fall back to localhost
    return {
        'address': '127.0.0.1',
        'type': 'ip',
        'message': '无法检测服务器地址，使用localhost'
    }
