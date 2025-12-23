"""Anti-scanner middleware to detect and block scanning tools.

This module helps prevent discovery by automated scanning tools like:
- Google Search crawlers
- FOFA, Shodan, Censys, ZoomEye scanners
- Common vulnerability scanners
"""

import re
import logging
from functools import wraps
from flask import request, jsonify, abort

logger = logging.getLogger(__name__)

# Configuration constants
MIN_USER_AGENT_LENGTH = 10  # Minimum length for a valid User-Agent

# Known scanner/bot User-Agent patterns
SCANNER_USER_AGENTS = [
    # Search engine crawlers
    r'Googlebot',
    r'bingbot',
    r'Baiduspider',
    r'YandexBot',
    r'DuckDuckBot',
    # Security scanners and crawlers
    r'FOFA',
    r'Shodan',
    r'Censys',
    r'ZoomEye',
    r'masscan',
    r'nmap',
    r'Nmap',
    r'zgrab',
    r'httpx',
    r'nuclei',
    r'nikto',
    r'dirbuster',
    r'gobuster',
    r'wfuzz',
    r'sqlmap',
    r'acunetix',
    r'nessus',
    r'burp',
    r'owasp',
    r'zap',
    r'arachni',
    r'w3af',
    r'whatweb',
    r'skipfish',
    r'wpscan',
    r'joomscan',
    # Generic crawler patterns
    r'bot',
    r'crawler',
    r'spider',
    r'scan',
    r'curl',
    r'wget',
    r'python-requests',
    r'python-urllib',
    r'libwww',
    r'httplib',
    r'Go-http-client',
    r'Java/',
    r'Apache-HttpClient',
    r'okhttp',
]

# Compile patterns for performance
SCANNER_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SCANNER_USER_AGENTS]

# Suspicious request patterns (common scanner probes)
# These patterns target common vulnerable/sensitive paths that scanners look for
# Note: These patterns use ^ to match from path start or $ to match standalone paths
SUSPICIOUS_PATHS = [
    r'^/\.env$',
    r'^/\.env\.',
    r'^/\.git',
    r'^/\.svn',
    r'^/wp-admin',
    r'^/wp-content',
    r'^/wp-includes',
    r'^/phpmyadmin',
    r'^/admin\.php$',
    r'^/config\.php$',
    r'^/backup$',  # Exact match only
    r'^/backups$',  # Exact match only
    r'^/database$',  # Exact match only
    r'^/\.htaccess$',
    r'^/\.htpasswd$',
    r'^/robots\.txt$',
    r'^/sitemap\.xml$',
    r'^/actuator',
    r'^/swagger',
    r'^/api-docs$',
    r'^/console$',
    r'^/manager$',
    r'^/status$',
    r'^/info$',
    r'^/metrics$',
    r'^/debug$',
    r'^/trace$',
    r'^/heapdump$',
    r'^/threaddump$',
    r'^/env$',
    r'^/configprops$',
    r'^/beans$',
    r'^/mappings$',
    r'^/conditions$',
    r'^/loggers$',
]

SUSPICIOUS_PATH_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_PATHS]


def is_scanner_request():
    """Check if the current request is from a known scanner."""
    user_agent = request.headers.get('User-Agent', '')
    
    # Check User-Agent against known scanner patterns
    for pattern in SCANNER_PATTERNS:
        if pattern.search(user_agent):
            logger.warning(f"Scanner detected: User-Agent '{user_agent}' from {request.remote_addr}")
            return True
    
    # Check for empty or missing User-Agent (common in scanners)
    if not user_agent or len(user_agent) < MIN_USER_AGENT_LENGTH:
        logger.warning(f"Suspicious request: Empty/short User-Agent from {request.remote_addr}")
        return True
    
    return False


def is_suspicious_path():
    """Check if the requested path is commonly probed by scanners."""
    path = request.path
    
    for pattern in SUSPICIOUS_PATH_PATTERNS:
        if pattern.search(path):
            logger.warning(f"Suspicious path access: '{path}' from {request.remote_addr}")
            return True
    
    return False


def anti_scanner_check():
    """Middleware to check for scanner requests.
    
    Returns:
        tuple: (should_block, response) - If should_block is True, return the response
    """
    # Check for scanner User-Agents
    if is_scanner_request():
        return True, (jsonify({'error': 'Forbidden'}), 403)
    
    # Check for suspicious paths
    if is_suspicious_path():
        # Return a generic 404 to not reveal this is a protected application
        return True, (jsonify({'error': 'Not found'}), 404)
    
    return False, None


def block_scanners(f):
    """Decorator to block scanner requests for specific routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        should_block, response = anti_scanner_check()
        if should_block:
            return response
        return f(*args, **kwargs)
    return decorated_function


def register_anti_scanner_handlers(app):
    """Register anti-scanner handlers for the Flask app.
    
    This adds a before_request handler that checks all incoming requests
    for scanner signatures and blocks them.
    """
    @app.before_request
    def check_for_scanners():
        # Skip health check endpoint for monitoring purposes
        if request.path in ['/health', '/']:
            return None
        
        # Check if it's a scanner request
        should_block, response = anti_scanner_check()
        if should_block:
            response_data, status_code = response
            return response_data, status_code
        
        return None
    
    # Add custom headers to hide server information
    @app.after_request
    def add_security_headers(response):
        # Remove server header that could reveal technology stack
        response.headers['Server'] = 'nginx'
        # Remove X-Powered-By if present
        response.headers.pop('X-Powered-By', None)
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
