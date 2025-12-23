"""Tests for version service and API routes"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from app import create_app
from models import db
from models.user import User
from services.version_service import (
    parse_version, compare_versions, get_current_version,
    check_for_updates, get_version_info, CURRENT_VERSION
)


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Create test user with unique name
        user = User(username=f'testuser_{uuid.uuid4().hex[:8]}')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        # Store user info for later
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


class TestVersionParsing:
    """Tests for version parsing functions"""

    def test_parse_version_simple(self):
        """Test parsing simple version string"""
        assert parse_version('2.1.0') == (2, 1, 0)

    def test_parse_version_with_v_prefix(self):
        """Test parsing version with v prefix"""
        assert parse_version('v2.1.0') == (2, 1, 0)
        assert parse_version('V2.1.0') == (2, 1, 0)

    def test_parse_version_invalid(self):
        """Test parsing invalid version string"""
        assert parse_version('invalid') == (0, 0, 0)
        assert parse_version('') == (0, 0, 0)

    def test_compare_versions_equal(self):
        """Test comparing equal versions"""
        assert compare_versions('2.1.0', '2.1.0') == 0
        assert compare_versions('v2.1.0', '2.1.0') == 0

    def test_compare_versions_less(self):
        """Test comparing when first version is less"""
        assert compare_versions('2.0.0', '2.1.0') == -1
        assert compare_versions('1.9.9', '2.0.0') == -1

    def test_compare_versions_greater(self):
        """Test comparing when first version is greater"""
        assert compare_versions('2.1.0', '2.0.0') == 1
        assert compare_versions('3.0.0', '2.9.9') == 1


class TestVersionInfo:
    """Tests for version info functions"""

    def test_get_current_version(self):
        """Test getting current version"""
        version = get_current_version()
        assert version == CURRENT_VERSION
        assert isinstance(version, str)

    def test_get_version_info(self):
        """Test getting version info dict"""
        info = get_version_info()
        assert 'current_version' in info
        assert 'github_owner' in info
        assert 'github_repo' in info
        assert 'github_url' in info
        assert info['current_version'] == CURRENT_VERSION


class TestCheckForUpdates:
    """Tests for update checking functionality"""

    @patch('services.version_service.urllib.request.urlopen')
    def test_check_for_updates_no_update(self, mock_urlopen):
        """Test when current version is latest"""
        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"tag_name": "v2.1.0", "html_url": "https://github.com/test/test/releases/tag/v2.1.0", "body": "Release notes", "published_at": "2024-01-01T00:00:00Z"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        result = check_for_updates()
        
        assert result['success'] is True
        assert result['has_update'] is False
        assert result['current_version'] == CURRENT_VERSION

    @patch('services.version_service.urllib.request.urlopen')
    def test_check_for_updates_with_update(self, mock_urlopen):
        """Test when a newer version is available"""
        # Mock the GitHub API response with a newer version
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"tag_name": "v99.0.0", "html_url": "https://github.com/test/test/releases/tag/v99.0.0", "body": "New features", "published_at": "2024-12-01T00:00:00Z"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        result = check_for_updates()
        
        assert result['success'] is True
        assert result['has_update'] is True
        assert result['latest_version'] == '99.0.0'

    @patch('services.version_service.urllib.request.urlopen')
    def test_check_for_updates_network_error(self, mock_urlopen):
        """Test handling of network errors"""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError('Network error')
        
        result = check_for_updates()
        
        assert result['success'] is False
        assert result['has_update'] is False
        assert '网络错误' in result['message']


class TestVersionAPI:
    """Tests for version API endpoints"""

    def test_get_version_info_api(self, client, auth_headers):
        """Test getting version info via API"""
        response = client.get('/api/preferences/version', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'version' in data
        assert 'current_version' in data['version']

    def test_get_version_info_unauthorized(self, client):
        """Test getting version info without auth"""
        response = client.get('/api/preferences/version')
        assert response.status_code == 401

    @patch('services.version_service.urllib.request.urlopen')
    def test_check_for_updates_api(self, mock_urlopen, client, auth_headers):
        """Test checking for updates via API"""
        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"tag_name": "v2.1.0", "html_url": "https://github.com/test/test/releases/tag/v2.1.0", "body": "Release notes", "published_at": "2024-01-01T00:00:00Z"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        response = client.get('/api/preferences/version/check', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'current_version' in data
        assert 'has_update' in data

    def test_check_for_updates_unauthorized(self, client):
        """Test checking for updates without auth"""
        response = client.get('/api/preferences/version/check')
        assert response.status_code == 401
