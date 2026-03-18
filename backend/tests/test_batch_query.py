"""Tests for batch query API routes"""
import pytest
import uuid
from app import create_app
from models import db
from models.user import User
from models.server import Server
from models.user_preference import BatchQueryTask


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
        app.test_username = user.username
        app.test_user_id = user.id

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


class TestBatchQueryStart:
    """Tests for batch query start endpoint"""

    def test_start_batch_query_success(self, client, auth_headers):
        """Test starting a batch query"""
        response = client.post('/api/batch-query/start',
            headers=auth_headers,
            json={'segment': '192.168.1'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['segment'] == '192.168.1'
        assert data['status'] == 'running'
        assert data['total_processed'] == 0
        assert data['total_online'] == 0
        assert data['total_error'] == 0

    def test_start_batch_query_missing_segment(self, client, auth_headers):
        """Test starting batch query without segment"""
        response = client.post('/api/batch-query/start',
            headers=auth_headers,
            json={})
        assert response.status_code == 400

    def test_start_batch_query_invalid_segment(self, client, auth_headers):
        """Test starting batch query with invalid segment"""
        response = client.post('/api/batch-query/start',
            headers=auth_headers,
            json={'segment': '999.999.999'})
        assert response.status_code == 400

    def test_start_batch_query_invalid_format(self, client, auth_headers):
        """Test starting batch query with wrong format"""
        response = client.post('/api/batch-query/start',
            headers=auth_headers,
            json={'segment': '192.168'})
        assert response.status_code == 400

    def test_start_batch_query_unauthorized(self, client):
        """Test starting batch query without auth"""
        response = client.post('/api/batch-query/start',
            json={'segment': '192.168.1'})
        assert response.status_code == 401


class TestBatchQueryStop:
    """Tests for batch query stop endpoint"""

    def test_stop_nonexistent_task(self, client, auth_headers):
        """Test stopping a task that doesn't exist"""
        response = client.post('/api/batch-query/stop',
            headers=auth_headers,
            json={'segment': '10.0.0'})
        assert response.status_code == 404

    def test_stop_non_running_task(self, app, client, auth_headers):
        """Test stopping a completed task"""
        with app.app_context():
            task = BatchQueryTask(
                user_id=app.test_user_id,
                segment='10.0.0',
                status='completed'
            )
            db.session.add(task)
            db.session.commit()

        response = client.post('/api/batch-query/stop',
            headers=auth_headers,
            json={'segment': '10.0.0'})
        assert response.status_code == 400

    def test_stop_missing_segment(self, client, auth_headers):
        """Test stopping without segment"""
        response = client.post('/api/batch-query/stop',
            headers=auth_headers,
            json={})
        assert response.status_code == 400


class TestBatchQueryStatus:
    """Tests for batch query status endpoint"""

    def test_get_status_not_found(self, client, auth_headers):
        """Test getting status for nonexistent task"""
        response = client.get('/api/batch-query/status/10.0.0',
            headers=auth_headers)
        assert response.status_code == 404

    def test_get_status_existing(self, app, client, auth_headers):
        """Test getting status for existing task"""
        with app.app_context():
            task = BatchQueryTask(
                user_id=app.test_user_id,
                segment='172.16.0',
                status='running',
                current_ip_index=50,
                total_processed=20,
                total_online=5,
                total_error=3,
                total_skipped=12
            )
            db.session.add(task)
            db.session.commit()

        response = client.get('/api/batch-query/status/172.16.0',
            headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['segment'] == '172.16.0'
        assert data['status'] == 'running'
        assert data['current_ip_index'] == 50
        assert data['total_processed'] == 20
        assert data['total_online'] == 5
        assert data['total_error'] == 3
        assert data['total_skipped'] == 12


class TestBatchQueryTasks:
    """Tests for batch query tasks list endpoint"""

    def test_get_all_tasks_empty(self, client, auth_headers):
        """Test getting all tasks when empty"""
        response = client.get('/api/batch-query/tasks',
            headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json() == {}

    def test_get_all_tasks(self, app, client, auth_headers):
        """Test getting all tasks"""
        with app.app_context():
            task1 = BatchQueryTask(
                user_id=app.test_user_id,
                segment='10.0.0',
                status='completed'
            )
            task2 = BatchQueryTask(
                user_id=app.test_user_id,
                segment='172.16.0',
                status='running'
            )
            db.session.add_all([task1, task2])
            db.session.commit()

        response = client.get('/api/batch-query/tasks',
            headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert '10.0.0' in data
        assert '172.16.0' in data
        assert data['10.0.0']['status'] == 'completed'
        assert data['172.16.0']['status'] == 'running'


class TestServerSourceField:
    """Tests for the source field on the Server model"""

    def test_server_source_field_in_dict(self, app):
        """Test that server to_dict includes source field"""
        with app.app_context():
            from utils.crypto import PasswordEncryption
            from config import Config
            encryptor = PasswordEncryption(Config.ENCRYPTION_KEY)

            server = Server(
                ip_address='192.168.1.100',
                port=22,
                username='root',
                encrypted_password=encryptor.encrypt('testpass'),
                status='online',
                source='batch_online'
            )
            db.session.add(server)
            db.session.commit()

            result = server.to_dict()
            assert result['source'] == 'batch_online'
            assert result['ip_address'] == '192.168.1.100'

    def test_server_source_field_null(self, app):
        """Test that server source field defaults to None"""
        with app.app_context():
            from utils.crypto import PasswordEncryption
            from config import Config
            encryptor = PasswordEncryption(Config.ENCRYPTION_KEY)

            server = Server(
                ip_address='192.168.1.101',
                port=22,
                username='root',
                encrypted_password=encryptor.encrypt('testpass')
            )
            db.session.add(server)
            db.session.commit()

            result = server.to_dict()
            assert result['source'] is None

    def test_server_source_batch_error(self, app):
        """Test batch_error source value"""
        with app.app_context():
            from utils.crypto import PasswordEncryption
            from config import Config
            encryptor = PasswordEncryption(Config.ENCRYPTION_KEY)

            server = Server(
                ip_address='192.168.1.102',
                port=22,
                username='root',
                encrypted_password=encryptor.encrypt('testpass'),
                status='online',
                error_type='auth_failed',
                source='batch_error'
            )
            db.session.add(server)
            db.session.commit()

            result = server.to_dict()
            assert result['source'] == 'batch_error'
            assert result['error_type'] == 'auth_failed'


class TestBatchQueryTaskModel:
    """Tests for the BatchQueryTask model"""

    def test_batch_query_task_to_dict(self, app):
        """Test BatchQueryTask to_dict conversion"""
        with app.app_context():
            task = BatchQueryTask(
                user_id=app.test_user_id,
                segment='10.0.1',
                status='running',
                current_ip_index=100,
                total_processed=50,
                total_online=10,
                total_error=5,
                total_skipped=35,
                log_output='test log output'
            )
            db.session.add(task)
            db.session.commit()

            result = task.to_dict()
            assert result['segment'] == '10.0.1'
            assert result['status'] == 'running'
            assert result['current_ip_index'] == 100
            assert result['total_processed'] == 50
            assert result['total_online'] == 10
            assert result['total_error'] == 5
            assert result['total_skipped'] == 35
            assert result['log_output'] == 'test log output'
            assert result['started_at'] is not None

    def test_batch_query_task_unique_constraint(self, app):
        """Test that user+segment combination is unique"""
        with app.app_context():
            task1 = BatchQueryTask(
                user_id=app.test_user_id,
                segment='10.0.1',
                status='completed'
            )
            db.session.add(task1)
            db.session.commit()

            task2 = BatchQueryTask(
                user_id=app.test_user_id,
                segment='10.0.1',
                status='running'
            )
            db.session.add(task2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
