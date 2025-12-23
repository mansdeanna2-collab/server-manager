"""SSL Certificate Generation Service

This module provides functionality for:
1. Detecting whether an address is an IP or domain
2. Generating self-signed SSL certificates
3. Managing SSL configuration
"""

import os
import re
import socket
import ipaddress
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Default SSL certificate directory
DEFAULT_SSL_DIR = '/etc/ssl/server-manager'
# Fallback to local directory if /etc/ssl is not writable
LOCAL_SSL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ssl')


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
    
    Returns:
        str: Path to SSL directory
    """
    # Try system directory first
    if os.path.exists('/etc/ssl') and os.access('/etc/ssl', os.W_OK):
        ssl_dir = DEFAULT_SSL_DIR
    else:
        # Fall back to local directory
        ssl_dir = LOCAL_SSL_DIR
    
    # Create directory if it doesn't exist
    if not os.path.exists(ssl_dir):
        try:
            os.makedirs(ssl_dir, mode=0o755)
            logger.info(f"Created SSL directory: {ssl_dir}")
        except PermissionError:
            # If we can't create in /etc/ssl, fall back to local
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
    
    # File names
    key_file = os.path.join(ssl_dir, f'server_{timestamp}.key')
    cert_file = os.path.join(ssl_dir, f'server_{timestamp}.crt')
    
    # Build Subject Alternative Name (SAN) based on address type
    if address_type == 'ip':
        san = f'IP:{address}'
        cn = address
    else:
        san = f'DNS:{address}'
        cn = address
    
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
{f"IP.1 = {address}" if address_type == "ip" else f"DNS.1 = {address}"}
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
        
        logger.info(f"Generated SSL certificate: {cert_file}")
        return {
            'success': True,
            'cert_path': cert_file,
            'key_path': key_file,
            'message': f'SSL证书已生成（自签名，有效期10年）'
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
            subject_line = [l for l in output.split('\n') if 'Subject:' in l]
            if subject_line:
                details['subject'] = subject_line[0].strip()
        
        if 'Not After' in output:
            expiry_line = [l for l in output.split('\n') if 'Not After' in l]
            if expiry_line:
                details['expires'] = expiry_line[0].strip()
        
        # Verify key matches certificate
        cert_modulus = subprocess.run(
            ['openssl', 'x509', '-noout', '-modulus', '-in', cert_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        key_modulus = subprocess.run(
            ['openssl', 'rsa', '-noout', '-modulus', '-in', key_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if cert_modulus.returncode != 0 or key_modulus.returncode != 0:
            return {
                'valid': False,
                'message': '无法验证证书和私钥的匹配性',
                'details': details
            }
        
        if cert_modulus.stdout.strip() != key_modulus.stdout.strip():
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


def get_server_address():
    """Try to detect the server's public IP or hostname
    
    Returns:
        dict: {
            'address': detected address,
            'type': 'ip' or 'hostname',
            'message': result message
        }
    """
    # Try to get hostname
    try:
        hostname = socket.gethostname()
        # Try to resolve hostname to IP
        try:
            ip = socket.gethostbyname(hostname)
            return {
                'address': ip,
                'type': 'ip',
                'message': f'检测到服务器IP: {ip}'
            }
        except socket.gaierror:
            pass
    except Exception:
        pass
    
    # Try to get external IP by connecting to a public server
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(5)
        # This doesn't actually send data, just establishes routing
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
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
