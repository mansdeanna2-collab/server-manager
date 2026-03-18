"""Tests for RDP file generation endpoint"""
import pytest
import uuid
from app import create_app
from models import db
from models.server import Server
from models.user import User
from utils.crypto import PasswordEncryption
from config import Config


password_encryptor = PasswordEncryption(Config.ENCRYPTION_KEY)


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.drop_all()
        db.create_all()
        # Create test user
        user = User(username=f'testuser_{uuid.uuid4().hex[:8]}')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        app.test_username = user.username

    yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers(app, client):
    """Get authentication headers"""
    response = client.post('/api/auth/login', json={
        'username': app.test_username,
        'password': 'testpass'
    })
    token = response.get_json()['token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def rdp_server(app):
    """Create a test RDP server"""
    with app.app_context():
        server = Server(
            ip_address='192.168.1.100',
            port=3389,
            username='Administrator',
            encrypted_password=password_encryptor.encrypt('testpassword'),
        )
        db.session.add(server)
        db.session.commit()
        server_id = server.id
    return server_id


@pytest.fixture
def ssh_server(app):
    """Create a test SSH server"""
    with app.app_context():
        server = Server(
            ip_address='192.168.1.200',
            port=22,
            username='root',
            encrypted_password=password_encryptor.encrypt('testpassword'),
        )
        db.session.add(server)
        db.session.commit()
        server_id = server.id
    return server_id


class TestRdpFileGeneration:
    """Tests for the RDP file generation endpoint"""

    def test_generate_rdp_file_success(self, client, auth_headers, rdp_server):
        """Test successful RDP file generation"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file',
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.content_type.startswith('application/x-rdp')
        assert 'attachment' in response.headers.get('Content-Disposition', '')
        assert '192.168.1.100.rdp' in response.headers.get('Content-Disposition', '')

        content = response.data.decode('utf-8')
        assert 'full address:s:192.168.1.100:3389' in content
        assert 'username:s:Administrator' in content

    def test_rdp_file_contains_background_settings(self, client, auth_headers, rdp_server):
        """Test that RDP file contains settings for background connection"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file',
            headers=auth_headers
        )
        content = response.data.decode('utf-8')

        # Verify key background-connection settings
        assert 'autoreconnection enabled:i:1' in content
        assert 'prompt for credentials:i:0' in content
        assert 'redirectclipboard:i:1' in content
        assert 'enablecredsspsupport:i:1' in content

    def test_rdp_file_not_found_server(self, client, auth_headers):
        """Test RDP file generation for non-existent server"""
        response = client.get(
            '/api/servers/99999/rdp-file',
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_rdp_file_non_rdp_server(self, client, auth_headers, ssh_server):
        """Test RDP file generation for non-RDP (SSH) server"""
        response = client.get(
            f'/api/servers/{ssh_server}/rdp-file',
            headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert '仅支持RDP端口' in data['message']

    def test_rdp_file_unauthorized(self, client, rdp_server):
        """Test RDP file generation without authentication"""
        response = client.get(f'/api/servers/{rdp_server}/rdp-file')
        assert response.status_code == 401

    def test_rdp_file_uses_crlf_line_endings(self, client, auth_headers, rdp_server):
        """Test that RDP file uses Windows-style CRLF line endings"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file',
            headers=auth_headers
        )
        content = response.data.decode('utf-8')
        # RDP files should use CRLF line endings
        assert '\r\n' in content


class TestRdpCustomSettings:
    """Tests for customizable RDP file settings"""

    def test_custom_resolution(self, client, auth_headers, rdp_server):
        """Test RDP file with custom resolution"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file?width=1600&height=900',
            headers=auth_headers
        )
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        assert 'desktopwidth:i:1600' in content
        assert 'desktopheight:i:900' in content

    def test_fullscreen_mode(self, client, auth_headers, rdp_server):
        """Test RDP file with fullscreen mode enabled"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file?fullscreen=1',
            headers=auth_headers
        )
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        assert 'screen mode id:i:2' in content

    def test_windowed_mode_default(self, client, auth_headers, rdp_server):
        """Test RDP file defaults to windowed mode"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file',
            headers=auth_headers
        )
        content = response.data.decode('utf-8')
        assert 'screen mode id:i:1' in content

    def test_clipboard_disabled(self, client, auth_headers, rdp_server):
        """Test RDP file with clipboard sharing disabled"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file?clipboard=0',
            headers=auth_headers
        )
        content = response.data.decode('utf-8')
        assert 'redirectclipboard:i:0' in content

    def test_drives_enabled(self, client, auth_headers, rdp_server):
        """Test RDP file with drive redirection enabled"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file?drives=1',
            headers=auth_headers
        )
        content = response.data.decode('utf-8')
        assert 'redirectdrives:i:1' in content

    def test_admin_session(self, client, auth_headers, rdp_server):
        """Test RDP file with admin/console session enabled"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file?admin=1',
            headers=auth_headers
        )
        content = response.data.decode('utf-8')
        assert 'administrative session:i:1' in content

    def test_admin_session_not_present_by_default(self, client, auth_headers, rdp_server):
        """Test admin session is not included by default"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file',
            headers=auth_headers
        )
        content = response.data.decode('utf-8')
        assert 'administrative session' not in content

    def test_multimon_enabled(self, client, auth_headers, rdp_server):
        """Test RDP file with multi-monitor enabled"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file?multimon=1',
            headers=auth_headers
        )
        content = response.data.decode('utf-8')
        assert 'use multimon:i:1' in content

    def test_resolution_clamped_minimum(self, client, auth_headers, rdp_server):
        """Test resolution values are clamped to minimum"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file?width=100&height=100',
            headers=auth_headers
        )
        content = response.data.decode('utf-8')
        assert 'desktopwidth:i:800' in content
        assert 'desktopheight:i:600' in content

    def test_resolution_clamped_maximum(self, client, auth_headers, rdp_server):
        """Test resolution values are clamped to maximum"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file?width=9999&height=9999',
            headers=auth_headers
        )
        content = response.data.decode('utf-8')
        assert 'desktopwidth:i:3840' in content
        assert 'desktopheight:i:2160' in content

    def test_combined_settings(self, client, auth_headers, rdp_server):
        """Test RDP file with multiple custom settings"""
        response = client.get(
            f'/api/servers/{rdp_server}/rdp-file?width=2560&height=1440&fullscreen=1&clipboard=0&drives=1&admin=1&multimon=1',
            headers=auth_headers
        )
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        assert 'desktopwidth:i:2560' in content
        assert 'desktopheight:i:1440' in content
        assert 'screen mode id:i:2' in content
        assert 'redirectclipboard:i:0' in content
        assert 'redirectdrives:i:1' in content
        assert 'administrative session:i:1' in content
        assert 'use multimon:i:1' in content
