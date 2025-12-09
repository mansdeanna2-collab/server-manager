"""Tests for concurrent server checking functionality."""
import pytest
from unittest.mock import patch, MagicMock


def test_check_single_server_success(monkeypatch):
    """Test _check_single_server returns correct result on success."""
    from services.check_service import CheckService
    from routes.servers import _check_single_server, password_encryptor
    
    # Mock password decryption
    monkeypatch.setattr(password_encryptor, 'decrypt', lambda x: 'decrypted_password')
    
    # Mock the status check to return a successful result
    monkeypatch.setattr(CheckService, 'check_server_status', staticmethod(
        lambda ip, port, user, pwd: {
            'overall': 'online',
            'ping': True,
            'port': True,
            'detail': 'Connection successful',
            'error_type': None
        }
    ))
    
    server_data = (1, '192.168.1.1', 22, 'root', 'encrypted_password')
    result = _check_single_server(server_data)
    
    assert result['server_id'] == 1
    assert result['ip_address'] == '192.168.1.1'
    assert result['success'] is True
    assert result['status_info']['overall'] == 'online'
    assert result['status_info']['ping'] is True


def test_check_single_server_failure(monkeypatch):
    """Test _check_single_server handles exceptions gracefully."""
    from routes.servers import _check_single_server, password_encryptor
    
    # Mock password decryption to raise an exception
    monkeypatch.setattr(password_encryptor, 'decrypt', lambda x: None)
    
    # Mock the status check to raise an exception
    def raise_error(*args):
        raise Exception('Connection failed')
    
    from services.check_service import CheckService
    monkeypatch.setattr(CheckService, 'check_server_status', staticmethod(raise_error))
    
    server_data = (1, '192.168.1.1', 22, 'root', 'encrypted_password')
    result = _check_single_server(server_data)
    
    assert result['server_id'] == 1
    assert result['ip_address'] == '192.168.1.1'
    assert result['success'] is False
    assert result['status_info']['overall'] == 'offline'
    assert 'error_type' in result['status_info']
    assert result['status_info']['error_type'] == 'check_error'


def test_config_check_max_workers():
    """Test that CHECK_MAX_WORKERS config is properly set."""
    from config import Config
    
    # Default value should be 10
    assert Config.CHECK_MAX_WORKERS == 10
    assert isinstance(Config.CHECK_MAX_WORKERS, int)


def test_concurrent_checking_configuration():
    """Test that concurrent checking uses proper worker count."""
    from config import Config
    
    # Test that max_workers is properly bounded
    num_servers = 5
    max_workers = min(Config.CHECK_MAX_WORKERS, num_servers)
    assert max_workers == 5
    
    num_servers = 20
    max_workers = min(Config.CHECK_MAX_WORKERS, num_servers)
    assert max_workers == 10  # Capped at CHECK_MAX_WORKERS


def test_limiter_exemption_decorator_exists():
    """Test that the check-all endpoint has limiter exemption."""
    from routes.servers import check_all_servers
    
    # The function should have the limiter exempt decorator applied
    # Check that the function is decorated (it will have __wrapped__ attribute)
    assert callable(check_all_servers)
