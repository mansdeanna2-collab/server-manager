"""Tests for preferences API routes"""
import pytest
import uuid
from app import create_app
from models import db
from models.user import User
from models.user_preference import (
    IpCheckStatus, IpIdResult, SegmentNote, SegmentFavorite, ServerFavorite,
    FetchServerTask
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


class TestIpCheckStatus:
    """Tests for IP check status endpoints"""

    def test_get_ip_check_status_empty(self, client, auth_headers):
        """Test getting empty IP check status"""
        response = client.get('/api/preferences/ip-check-status', headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json() == {}

    def test_save_ip_check_status(self, client, auth_headers):
        """Test saving IP check status"""
        response = client.post('/api/preferences/ip-check-status', 
            headers=auth_headers,
            json={
                'ip_address': '192.168.1.1',
                'port_checked': True,
                'ping_checked': True,
                'ping_online': True,
                'port_22': True,
                'port_3389': False
            })
        assert response.status_code == 200
        data = response.get_json()
        assert data['ip_address'] == '192.168.1.1'
        assert data['port_checked'] is True
        assert data['ping_online'] is True

    def test_get_saved_ip_check_status(self, client, auth_headers):
        """Test getting saved IP check status"""
        # First save
        client.post('/api/preferences/ip-check-status', 
            headers=auth_headers,
            json={
                'ip_address': '192.168.1.1',
                'ping_online': True
            })
        
        # Then get
        response = client.get('/api/preferences/ip-check-status', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert '192.168.1.1' in data
        assert data['192.168.1.1']['ping_online'] is True


class TestSegmentNotes:
    """Tests for segment notes endpoints"""

    def test_get_segment_notes_empty(self, client, auth_headers):
        """Test getting empty segment notes"""
        response = client.get('/api/preferences/segment-notes', headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json() == {}

    def test_save_segment_note(self, client, auth_headers):
        """Test saving segment note"""
        response = client.post('/api/preferences/segment-notes',
            headers=auth_headers,
            json={'segment': '192.168.1', 'note': 'Test note'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['segment'] == '192.168.1'
        assert data['note'] == 'Test note'

    def test_delete_segment_note(self, client, auth_headers):
        """Test deleting segment note by saving empty"""
        # First save
        client.post('/api/preferences/segment-notes',
            headers=auth_headers,
            json={'segment': '192.168.1', 'note': 'Test note'})
        
        # Then delete by saving empty
        response = client.post('/api/preferences/segment-notes',
            headers=auth_headers,
            json={'segment': '192.168.1', 'note': ''})
        assert response.status_code == 200


class TestSegmentFavorites:
    """Tests for segment favorites endpoints"""

    def test_get_segment_favorites_empty(self, client, auth_headers):
        """Test getting empty segment favorites"""
        response = client.get('/api/preferences/segment-favorites', headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json() == []

    def test_toggle_segment_favorite_add(self, client, auth_headers):
        """Test adding segment favorite"""
        response = client.post('/api/preferences/segment-favorites',
            headers=auth_headers,
            json={'segment': '192.168.1'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['favorited'] is True
        assert data['segment'] == '192.168.1'

    def test_toggle_segment_favorite_remove(self, client, auth_headers):
        """Test removing segment favorite"""
        # First add
        client.post('/api/preferences/segment-favorites',
            headers=auth_headers,
            json={'segment': '192.168.1'})
        
        # Then remove
        response = client.post('/api/preferences/segment-favorites',
            headers=auth_headers,
            json={'segment': '192.168.1'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['favorited'] is False


class TestServerFavorites:
    """Tests for server favorites endpoints"""

    def test_get_server_favorites_empty(self, client, auth_headers):
        """Test getting empty server favorites"""
        response = client.get('/api/preferences/server-favorites', headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json() == []

    def test_toggle_server_favorite_add(self, client, auth_headers):
        """Test adding server favorite"""
        response = client.post('/api/preferences/server-favorites',
            headers=auth_headers,
            json={'server_id': 1})
        assert response.status_code == 200
        data = response.get_json()
        assert data['favorited'] is True
        assert data['server_id'] == 1

    def test_toggle_server_favorite_remove(self, client, auth_headers):
        """Test removing server favorite"""
        # First add
        client.post('/api/preferences/server-favorites',
            headers=auth_headers,
            json={'server_id': 1})
        
        # Then remove
        response = client.post('/api/preferences/server-favorites',
            headers=auth_headers,
            json={'server_id': 1})
        assert response.status_code == 200
        data = response.get_json()
        assert data['favorited'] is False


class TestFetchServerTasks:
    """Tests for fetch server task endpoints"""

    def test_get_fetch_server_tasks_empty(self, client, auth_headers):
        """Test getting empty fetch server tasks"""
        response = client.get('/api/preferences/fetch-server-tasks', headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json() == {}

    def test_save_fetch_server_task(self, client, auth_headers):
        """Test saving fetch server task"""
        response = client.post('/api/preferences/fetch-server-tasks',
            headers=auth_headers,
            json={
                'ip_address': '192.168.1.1',
                'status': 'running',
                'log_output': 'Starting script...'
            })
        assert response.status_code == 200
        data = response.get_json()
        assert data['ip_address'] == '192.168.1.1'
        assert data['status'] == 'running'
        assert data['log_output'] == 'Starting script...'

    def test_get_fetch_server_task_by_ip(self, client, auth_headers):
        """Test getting specific fetch server task by IP"""
        # First save a task
        client.post('/api/preferences/fetch-server-tasks',
            headers=auth_headers,
            json={
                'ip_address': '192.168.1.2',
                'status': 'completed',
                'log_output': 'Done'
            })
        
        # Get by IP
        response = client.get('/api/preferences/fetch-server-tasks/192.168.1.2',
            headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['ip_address'] == '192.168.1.2'
        assert data['status'] == 'completed'

    def test_get_fetch_server_task_not_found(self, client, auth_headers):
        """Test getting non-existent fetch server task"""
        response = client.get('/api/preferences/fetch-server-tasks/10.0.0.1',
            headers=auth_headers)
        assert response.status_code == 404
        data = response.get_json()
        assert data['status'] == 'not_found'

    def test_get_running_fetch_server_tasks(self, client, auth_headers):
        """Test getting only running fetch server tasks"""
        # Save multiple tasks with different statuses
        client.post('/api/preferences/fetch-server-tasks',
            headers=auth_headers,
            json={'ip_address': '192.168.1.1', 'status': 'running'})
        client.post('/api/preferences/fetch-server-tasks',
            headers=auth_headers,
            json={'ip_address': '192.168.1.2', 'status': 'completed'})
        client.post('/api/preferences/fetch-server-tasks',
            headers=auth_headers,
            json={'ip_address': '192.168.1.3', 'status': 'running'})
        
        # Get running tasks only
        response = client.get('/api/preferences/fetch-server-tasks/running',
            headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert '192.168.1.1' in data
        assert '192.168.1.3' in data
        assert '192.168.1.2' not in data

    def test_update_fetch_server_task(self, client, auth_headers):
        """Test updating existing fetch server task"""
        # Create initial task
        client.post('/api/preferences/fetch-server-tasks',
            headers=auth_headers,
            json={
                'ip_address': '192.168.1.1',
                'status': 'running',
                'log_output': 'Starting...'
            })
        
        # Update the task
        response = client.post('/api/preferences/fetch-server-tasks',
            headers=auth_headers,
            json={
                'ip_address': '192.168.1.1',
                'status': 'completed',
                'log_output': 'Completed successfully',
                'servers_added': [{'ip': '192.168.1.100'}]
            })
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'completed'
        assert data['log_output'] == 'Completed successfully'
        assert data['servers_added'] == [{'ip': '192.168.1.100'}]

    def test_delete_fetch_server_task(self, client, auth_headers):
        """Test deleting fetch server task"""
        # Create a task
        client.post('/api/preferences/fetch-server-tasks',
            headers=auth_headers,
            json={'ip_address': '192.168.1.1', 'status': 'completed'})
        
        # Delete the task
        response = client.delete('/api/preferences/fetch-server-tasks/192.168.1.1',
            headers=auth_headers)
        assert response.status_code == 200
        
        # Verify it's deleted
        response = client.get('/api/preferences/fetch-server-tasks/192.168.1.1',
            headers=auth_headers)
        assert response.status_code == 404

    def test_delete_fetch_server_task_not_found(self, client, auth_headers):
        """Test deleting non-existent fetch server task"""
        response = client.delete('/api/preferences/fetch-server-tasks/10.0.0.1',
            headers=auth_headers)
        assert response.status_code == 404
