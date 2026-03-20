"""Background batch query for IP segments.

Processes IPs in a segment that satisfy both conditions:
- Not already existing as an online server with port 22 open
- Port 22 is detected as open (from saved IpCheckStatus data)

For each qualifying IP, processes sequentially (one at a time):
1. Query ID via id.py script
2. Fetch server via mm.py script
3. Check connectivity
4. Categorize as batch_online or batch_error

Runs as a background thread that survives browser/computer close.
Auto-refreshes cookies every 2 hours.
"""

import threading
import subprocess
import os
import re
import sys
import time
import logging
from flask import Blueprint, request, jsonify, current_app
from config import Config
from routes.auth import token_required
from utils import china_now

logger = logging.getLogger(__name__)

batch_query_bp = Blueprint('batch_query', __name__, url_prefix='/api/batch-query')

# Store active batch query tasks in memory:
# {segment: {'thread': Thread, 'stop_event': Event, 'process': Popen|None}}
_active_tasks = {}
_active_tasks_lock = threading.Lock()

# Lock for serializing script executions (id.py / mm.py write to shared files ip.txt / mm.py)
_script_execution_lock = threading.Lock()

# Cookie refresh interval: 2 hours in seconds (per requirement specification)
COOKIE_REFRESH_INTERVAL = 2 * 60 * 60

# Script execution timeouts
ID_QUERY_TIMEOUT = 300       # 5 minutes for id.py
FETCH_SERVER_TIMEOUT = 1200  # 20 minutes for mm.py (script runs ~15 min)

# SSH port constant
SSH_PORT = 22

# Maximum length for error_type field (must match Server model VARCHAR(50))
ERROR_TYPE_MAX_LENGTH = 50

# Stop check interval during subprocess execution (seconds)
STOP_CHECK_INTERVAL = 1.0

# Maximum retries for database operations during stop
DB_RETRY_COUNT = 3
DB_RETRY_DELAY = 0.5


def _get_stop_event(segment):
    """Get the stop event for a segment task."""
    with _active_tasks_lock:
        task_info = _active_tasks.get(segment)
        if task_info:
            return task_info.get('stop_event')
    return None


def _set_current_process(segment, process):
    """Store reference to the current subprocess for force-killing."""
    with _active_tasks_lock:
        task_info = _active_tasks.get(segment)
        if task_info:
            task_info['process'] = process


def _kill_current_process(segment):
    """Kill the current subprocess for a segment task."""
    with _active_tasks_lock:
        task_info = _active_tasks.get(segment)
        if task_info and task_info.get('process'):
            try:
                task_info['process'].kill()
            except (OSError, ProcessLookupError):
                pass


def _read_subprocess_output(process, stop_event=None, timeout=300):
    """Read subprocess output using a reader thread with stop event checking.

    Instead of blocking on readline() forever, uses a separate reader thread
    so the main thread can periodically check the stop event and timeout.

    Returns (output_string, was_stopped) tuple.
    """
    output_lines = []
    reader_done = threading.Event()

    def _reader():
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    output_lines.append(line)
        except Exception:
            pass
        finally:
            reader_done.set()

    reader_thread = threading.Thread(target=_reader, daemon=True)
    reader_thread.start()

    start_time = time.time()
    while not reader_done.is_set():
        # Check stop event
        if stop_event and stop_event.is_set():
            try:
                process.kill()
            except (OSError, ProcessLookupError):
                pass
            reader_thread.join(timeout=5)
            return ''.join(output_lines), True

        # Check timeout
        if time.time() - start_time > timeout:
            try:
                process.kill()
            except (OSError, ProcessLookupError):
                pass
            reader_thread.join(timeout=5)
            return ''.join(output_lines) + '\n[执行超时]', False

        # Wait briefly before next check
        reader_done.wait(timeout=STOP_CHECK_INTERVAL)

    # Process exited normally, collect remaining output
    reader_thread.join(timeout=5)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except (OSError, ProcessLookupError):
            pass
        process.wait()

    return ''.join(output_lines), False


def _append_log(app, user_id, segment, message):
    """Append a log line to the batch query task in the database."""
    try:
        with app.app_context():
            from models import db
            from models.user_preference import BatchQueryTask

            task = BatchQueryTask.query.filter_by(
                user_id=user_id, segment=segment
            ).first()
            if task:
                current_log = task.log_output or ''
                task.log_output = current_log + message + '\n'
                task.updated_at = china_now()
                db.session.commit()
    except Exception as e:
        logger.error(f"Error appending log: {str(e)}")


def _update_task_progress(app, user_id, segment, **kwargs):
    """Update batch query task progress in the database."""
    try:
        with app.app_context():
            from models import db
            from models.user_preference import BatchQueryTask

            task = BatchQueryTask.query.filter_by(
                user_id=user_id, segment=segment
            ).first()
            if task:
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                task.updated_at = china_now()
                db.session.commit()
    except Exception as e:
        logger.error(f"Error updating task progress: {str(e)}")


def _refresh_cookie(app, python_dir):
    """Run update_cookie.sh to refresh authentication cookies.

    Returns True if successful, False otherwise.
    """
    script_path = os.path.join(python_dir, 'update_cookie.sh')
    if not os.path.exists(script_path):
        logger.warning("update_cookie.sh not found, skipping cookie refresh")
        return False

    try:
        result = subprocess.run(
            ['bash', script_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=python_dir
        )
        if result.returncode == 0:
            logger.info("Cookie refreshed successfully")
            return True
        else:
            logger.warning(f"Cookie refresh failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error refreshing cookie: {str(e)}")
        return False


def _query_id_for_ip(ip_address, python_dir, stop_event=None, segment=None):
    """Run id.py script to query the ID for an IP address.

    Returns (id_result, log_output) tuple.
    Uses non-blocking output reading with stop event support.
    """
    ip_file = os.path.join(python_dir, 'ip.txt')
    id_py_file = os.path.join(python_dir, 'id.py')

    if not os.path.exists(id_py_file):
        return None, 'id.py script not found'

    try:
        # Write IP to ip.txt
        with open(ip_file, 'w', encoding='utf-8') as f:
            f.write(ip_address)
        os.chmod(ip_file, 0o600)

        # Run id.py
        process = subprocess.Popen(
            [sys.executable, '-u', id_py_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=python_dir,
            bufsize=1
        )

        # Store process reference for force-killing on stop
        if segment:
            _set_current_process(segment, process)

        # Read output with stop event and timeout support
        full_output, was_stopped = _read_subprocess_output(
            process, stop_event, timeout=ID_QUERY_TIMEOUT
        )

        if was_stopped:
            return None, full_output + '\n[任务已停止]'

        # Extract ID from output
        id_result = None
        id_match = re.search(r'前\d+个最小的id[:\s]*\[(\d+)\]', full_output)
        if id_match:
            id_result = id_match.group(1)
        else:
            id_match = re.search(r'\[(\d+)\]', full_output)
            if id_match:
                id_result = id_match.group(1)

        return id_result, full_output

    except Exception as e:
        return None, f'Error running id.py: {str(e)}'


def _fetch_server_for_ip(ip_address, ipid, python_dir, app, stop_event=None, segment=None):
    """Run mm.py script to fetch server for an IP with given ID.

    Returns (added_servers, log_output) tuple.
    added_servers is a list of dicts with server info.
    Uses non-blocking output reading with stop event support.
    """
    mm_py_file = os.path.join(python_dir, 'mm.py')

    if not os.path.exists(mm_py_file):
        return [], 'mm.py script not found'

    try:
        # Update target_ids in mm.py
        ipid_int = int(ipid)
        with open(mm_py_file, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = re.sub(
            r'target_ids\s*=\s*\[[^\]]*\]',
            f'target_ids = [{ipid_int}]',
            content
        )

        with open(mm_py_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # Run mm.py
        process = subprocess.Popen(
            [sys.executable, '-u', mm_py_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=python_dir,
            bufsize=1
        )

        # Store process reference for force-killing on stop
        if segment:
            _set_current_process(segment, process)

        # Read output with stop event and timeout support
        full_output, was_stopped = _read_subprocess_output(
            process, stop_event, timeout=FETCH_SERVER_TIMEOUT
        )

        if was_stopped:
            return [], full_output + '\n[任务已停止]'

        # Parse server info from output (reuse logic from fetch_server.py)
        from routes.fetch_server import _parse_server_info, _determine_port_and_username

        servers = _parse_server_info(full_output)
        added_servers = []

        if servers:
            from models import db
            from models.server import Server
            from utils.crypto import PasswordEncryption
            from services.check_service import CheckService

            password_encryptor = PasswordEncryption(Config.ENCRYPTION_KEY)

            with app.app_context():
                for server_data in servers:
                    ips = server_data.get('ips', [])
                    password = server_data.get('password', '')

                    if not ips or not password:
                        continue

                    if not isinstance(ips, list):
                        ips = [str(ips)]

                    port, username = _determine_port_and_username(server_data)
                    notes = '/'.join(ips) if len(ips) > 1 else (
                        server_data.get('name') or server_data.get('instance_id') or ''
                    )
                    encrypted_password = password_encryptor.encrypt(password)

                    for ip_addr in ips:
                        existing = Server.query.filter_by(ip_address=ip_addr).first()
                        if existing:
                            logger.info(f"Batch query: Server {ip_addr} already exists, skipping")
                            continue

                        # Check server status
                        source = 'batch_error'
                        try:
                            status_info = CheckService.check_server_status(
                                ip_addr, port, username, password
                            )
                            overall_status = status_info['overall']
                            check_detail = status_info.get('detail')
                            error_type = status_info.get('error_type')

                            if overall_status == 'online' and not error_type:
                                source = 'batch_online'
                            else:
                                source = 'batch_error'
                        except Exception as e:
                            overall_status = 'unknown'
                            check_detail = f'检测出错: {str(e)}'
                            error_type = None
                            source = 'batch_error'

                        server = Server(
                            ip_address=ip_addr,
                            port=port,
                            username=username,
                            encrypted_password=encrypted_password,
                            notes=notes,
                            status=overall_status,
                            last_checked=china_now(),
                            check_detail=check_detail,
                            error_type=str(error_type)[:ERROR_TYPE_MAX_LENGTH] if error_type else None,
                            source=source
                        )
                        db.session.add(server)
                        added_servers.append({
                            'ip': ip_addr,
                            'port': port,
                            'username': username,
                            'status': overall_status,
                            'source': source
                        })
                        logger.info(f"Batch query: Added server {ip_addr} as {source}")

                if added_servers:
                    db.session.commit()

        return added_servers, full_output

    except Exception as e:
        return [], f'Error running mm.py: {str(e)}'


def _should_skip_ip(app, ip_address):
    """Check if an IP should be skipped (already exists and is online with port 22).

    Returns True if the IP should be skipped.
    """
    try:
        with app.app_context():
            from models.server import Server

            server = Server.query.filter_by(ip_address=ip_address).first()
            if server and server.status == 'online' and server.port == SSH_PORT and not server.error_type:
                return True
    except Exception as e:
        logger.error(f"Error checking if IP should be skipped: {str(e)}")
    return False


def _is_port_22_open(app, user_id, ip_address):
    """Check if port 22 is open on the given IP address.

    Checks saved IpCheckStatus from previous port scanning.
    If no port check data exists, returns False (user should run port
    checks on the InformationQuery page before starting a batch query).

    Returns True if port 22 is confirmed open.
    """
    try:
        with app.app_context():
            from models.user_preference import IpCheckStatus

            check_status = IpCheckStatus.query.filter_by(
                user_id=user_id, ip_address=ip_address
            ).first()
            if check_status and check_status.port_checked:
                return check_status.port_22
    except Exception as e:
        logger.error(f"Error checking IpCheckStatus for {ip_address}: {str(e)}")

    return False


def _is_task_stopped(app, user_id, segment):
    """Check if the task has been stopped by the user.

    First checks the in-memory stop event (fast, no DB needed),
    then falls back to checking the database status.
    """
    # Fast check via stop event (no DB access needed)
    stop_event = _get_stop_event(segment)
    if stop_event and stop_event.is_set():
        return True

    # Fallback: check database status
    try:
        with app.app_context():
            from models.user_preference import BatchQueryTask

            task = BatchQueryTask.query.filter_by(
                user_id=user_id, segment=segment
            ).first()
            if task and task.status == 'stopped':
                return True
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}")
    return False


def _run_batch_query(app, user_id, segment, stop_event=None):
    """Main batch query background task.

    Iterates through all IPs in the segment (1-255). For each IP:
    1. Skip if already exists as online server with port 22 (no errors)
    2. Skip if port 22 is not open (from saved IpCheckStatus data)
    3. Query ID via id.py (one IP at a time)
    4. Fetch server via mm.py
    5. Check connectivity and categorize

    Wrapped in a top-level try/except to ensure the task is always marked
    as failed if an unexpected error occurs (prevents stuck 'running' tasks).
    """
    try:
        _run_batch_query_inner(app, user_id, segment, stop_event)
    except Exception as e:
        logger.error(f"Batch query for {segment} failed with unexpected error: {str(e)}")
        try:
            _append_log(app, user_id, segment,
                        f'\n[任务异常终止: {str(e)}]')
            _update_task_progress(
                app, user_id, segment,
                status='failed',
                completed_at=china_now()
            )
        except Exception as inner_e:
            logger.error(f"Failed to update task status after error: {str(inner_e)}")
    finally:
        # Always clean up from active tasks
        with _active_tasks_lock:
            _active_tasks.pop(segment, None)


def _run_batch_query_inner(app, user_id, segment, stop_event=None):
    """Inner implementation of the batch query task."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python_dir = os.path.join(backend_dir, 'Python')
    python_dir = os.path.realpath(python_dir)

    total_online = 0
    total_error = 0
    total_skipped = 0
    total_processed = 0
    cookie_last_updated = time.time()

    # Initial cookie refresh
    _append_log(app, user_id, segment, f'[{segment}] 开始一键查询...')
    _append_log(app, user_id, segment, '正在刷新Cookie...')
    if _refresh_cookie(app, python_dir):
        _append_log(app, user_id, segment, 'Cookie刷新成功')
        cookie_last_updated = time.time()
        _update_task_progress(app, user_id, segment, cookie_last_updated=china_now())
    else:
        _append_log(app, user_id, segment, 'Cookie刷新失败，继续执行（可能使用旧Cookie）')

    for i in range(1, 256):
        # Check if task was stopped (checks stop_event first, then DB)
        if _is_task_stopped(app, user_id, segment):
            _append_log(app, user_id, segment, f'\n[任务已被用户停止]')
            _update_task_progress(
                app, user_id, segment,
                status='stopped',
                completed_at=china_now()
            )
            break

        ip_address = f'{segment}.{i}'

        # Check if cookie needs refreshing (every 2 hours)
        if time.time() - cookie_last_updated > COOKIE_REFRESH_INTERVAL:
            _append_log(app, user_id, segment, f'\n--- Cookie已超过2小时，正在刷新... ---')
            if _refresh_cookie(app, python_dir):
                _append_log(app, user_id, segment, 'Cookie刷新成功')
                cookie_last_updated = time.time()
                _update_task_progress(app, user_id, segment, cookie_last_updated=china_now())
            else:
                _append_log(app, user_id, segment, 'Cookie刷新失败，继续执行')

        # Check if IP should be skipped (already exists as online server with port 22)
        if _should_skip_ip(app, ip_address):
            total_skipped += 1
            _update_task_progress(
                app, user_id, segment,
                current_ip_index=i,
                total_skipped=total_skipped
            )
            continue

        # Check if port 22 is open (from saved IpCheckStatus data)
        # Only process IPs where port 22 is confirmed open
        if not _is_port_22_open(app, user_id, ip_address):
            total_skipped += 1
            _update_task_progress(
                app, user_id, segment,
                current_ip_index=i,
                total_skipped=total_skipped
            )
            continue

        _append_log(app, user_id, segment, f'\n=== 处理 {ip_address} ({i}/255) ===')
        _update_task_progress(app, user_id, segment, current_ip_index=i)

        # Acquire script execution lock to prevent concurrent writes to ip.txt/mm.py
        with _script_execution_lock:
            # Check stop again before long-running script operations
            if _is_task_stopped(app, user_id, segment):
                _append_log(app, user_id, segment, f'\n[任务已被用户停止]')
                _update_task_progress(
                    app, user_id, segment,
                    status='stopped',
                    completed_at=china_now()
                )
                break

            # Step 1: Query ID
            _append_log(app, user_id, segment, f'[{ip_address}] 正在查询ID...')
            id_result, id_log = _query_id_for_ip(
                ip_address, python_dir, stop_event, segment
            )

            # Check if stopped during ID query
            if stop_event and stop_event.is_set():
                _append_log(app, user_id, segment, f'\n[任务已被用户停止]')
                _update_task_progress(
                    app, user_id, segment,
                    status='stopped',
                    completed_at=china_now()
                )
                break

            if not id_result:
                _append_log(app, user_id, segment, f'[{ip_address}] 未获取到ID，跳过')
                total_processed += 1
                _update_task_progress(app, user_id, segment, total_processed=total_processed)
                continue

            _append_log(app, user_id, segment, f'[{ip_address}] 获取到ID: {id_result}')

            # Save ID result to database
            try:
                with app.app_context():
                    from models import db
                    from models.user_preference import IpIdResult

                    existing = IpIdResult.query.filter_by(
                        user_id=user_id, ip_address=ip_address
                    ).first()
                    if existing:
                        existing.id_result = id_result
                        existing.log_output = id_log
                        existing.last_queried = china_now()
                    else:
                        new_result = IpIdResult(
                            user_id=user_id,
                            ip_address=ip_address,
                            id_result=id_result,
                            log_output=id_log
                        )
                        db.session.add(new_result)
                    db.session.commit()
            except Exception as e:
                logger.error(f"Error saving ID result: {str(e)}")

            # Step 2: Fetch server
            _append_log(app, user_id, segment, f'[{ip_address}] 正在获取服务器 (ID={id_result})...')
            added_servers, fetch_log = _fetch_server_for_ip(
                ip_address, id_result, python_dir, app, stop_event, segment
            )

            # Check if stopped during server fetch
            if stop_event and stop_event.is_set():
                _append_log(app, user_id, segment, f'\n[任务已被用户停止]')
                _update_task_progress(
                    app, user_id, segment,
                    status='stopped',
                    completed_at=china_now()
                )
                break

        total_processed += 1

        if added_servers:
            for srv in added_servers:
                if srv['source'] == 'batch_online':
                    total_online += 1
                    _append_log(app, user_id, segment,
                                f'[{srv["ip"]}] ✓ 在线 (端口:{srv["port"]}, 用户:{srv["username"]})')
                else:
                    total_error += 1
                    _append_log(app, user_id, segment,
                                f'[{srv["ip"]}] ✗ 错误 (状态:{srv["status"]})')
        else:
            _append_log(app, user_id, segment, f'[{ip_address}] 未发现新服务器')

        _update_task_progress(
            app, user_id, segment,
            total_processed=total_processed,
            total_online=total_online,
            total_error=total_error
        )
    else:
        # Loop completed without break (not stopped)
        _append_log(app, user_id, segment,
                    f'\n=== 查询完成 ===\n'
                    f'处理: {total_processed}, 在线: {total_online}, '
                    f'错误: {total_error}, 跳过: {total_skipped}')
        _update_task_progress(
            app, user_id, segment,
            status='completed',
            current_ip_index=255,
            completed_at=china_now()
        )


@batch_query_bp.route('/start', methods=['POST'])
@token_required
def start_batch_query(current_user):
    """Start a batch query for an IP segment.

    Request body: { "segment": "192.168.1" }
    """
    data = request.get_json()
    if not data or not data.get('segment'):
        return jsonify({'message': '请提供IP段'}), 400

    segment = data['segment'].strip()

    # Validate segment format (e.g., "192.168.1")
    parts = segment.split('.')
    if len(parts) != 3:
        return jsonify({'message': '无效的IP段格式'}), 400
    for part in parts:
        try:
            num = int(part)
            if num < 0 or num > 255:
                return jsonify({'message': '无效的IP段格式'}), 400
        except ValueError:
            return jsonify({'message': '无效的IP段格式'}), 400

    # Check if task is already running
    with _active_tasks_lock:
        task_info = _active_tasks.get(segment)
        if task_info and task_info['thread'].is_alive():
            return jsonify({'message': '该IP段正在查询中'}), 409

    # Create or update task in database
    from models import db
    from models.user_preference import BatchQueryTask

    task = BatchQueryTask.query.filter_by(
        user_id=current_user.id, segment=segment
    ).first()

    if task:
        # Reset task
        task.status = 'running'
        task.current_ip_index = 0
        task.total_processed = 0
        task.total_online = 0
        task.total_error = 0
        task.total_skipped = 0
        task.log_output = ''
        task.cookie_last_updated = None
        task.started_at = china_now()
        task.completed_at = None
        task.updated_at = china_now()
    else:
        task = BatchQueryTask(
            user_id=current_user.id,
            segment=segment,
            status='running'
        )
        db.session.add(task)

    db.session.commit()

    # Start background thread with stop event
    app = current_app._get_current_object()
    stop_event = threading.Event()
    thread = threading.Thread(
        target=_run_batch_query,
        args=(app, current_user.id, segment, stop_event),
        daemon=True,
        name=f'batch-query-{segment}'
    )
    thread.start()

    with _active_tasks_lock:
        _active_tasks[segment] = {
            'thread': thread,
            'stop_event': stop_event,
            'process': None
        }

    return jsonify(task.to_dict()), 200


@batch_query_bp.route('/stop', methods=['POST'])
@token_required
def stop_batch_query(current_user):
    """Stop a running batch query.

    Request body: { "segment": "192.168.1" }

    Uses a multi-layer stop mechanism:
    1. Set stop event (immediate, in-memory signal to background thread)
    2. Kill running subprocess (force-stop any hanging script)
    3. Update database status with retry (handles SQLite lock contention)
    """
    data = request.get_json()
    if not data or not data.get('segment'):
        return jsonify({'message': '请提供IP段'}), 400

    segment = data['segment'].strip()

    from models import db
    from models.user_preference import BatchQueryTask

    task = BatchQueryTask.query.filter_by(
        user_id=current_user.id, segment=segment
    ).first()

    if not task:
        return jsonify({'message': '任务不存在'}), 404

    if task.status != 'running':
        return jsonify({'message': '任务未在运行中'}), 400

    # Step 1: Signal stop via event (immediate, no DB needed)
    stop_event = _get_stop_event(segment)
    if stop_event:
        stop_event.set()

    # Step 2: Kill running subprocess to unblock the background thread
    _kill_current_process(segment)

    # Step 3: Update database with retry for SQLite lock contention
    for attempt in range(DB_RETRY_COUNT):
        try:
            # Re-fetch task to avoid stale session data after potential rollback
            task = BatchQueryTask.query.filter_by(
                user_id=current_user.id, segment=segment
            ).first()
            if task and task.status == 'running':
                task.status = 'stopped'
                task.completed_at = china_now()
                task.updated_at = china_now()
                db.session.commit()
            break
        except Exception as e:
            db.session.rollback()
            if attempt < DB_RETRY_COUNT - 1:
                time.sleep(DB_RETRY_DELAY)
            else:
                logger.error(f"Failed to update task status after {DB_RETRY_COUNT} retries: {str(e)}")
                # Even if DB update fails, the stop event is set and process killed,
                # so the background thread will still stop
                return jsonify({
                    'message': '停止信号已发送，数据库更新稍后完成',
                    'segment': segment,
                    'status': 'stopped'
                }), 200

    # Re-fetch final state for response
    task = BatchQueryTask.query.filter_by(
        user_id=current_user.id, segment=segment
    ).first()

    return jsonify(task.to_dict()), 200


def _cleanup_stale_task(task):
    """Check if a running task has no active thread and mark as failed.

    This handles the case where the server was restarted while a task was running,
    leaving the task stuck in 'running' status with no actual background thread.
    """
    if task.status != 'running':
        return

    with _active_tasks_lock:
        task_info = _active_tasks.get(task.segment)
        if task_info and task_info['thread'].is_alive():
            return  # Thread is still running, task is not stale

    # No active thread for this running task - mark as failed
    try:
        from models import db
        task.status = 'failed'
        task.completed_at = china_now()
        task.log_output = (task.log_output or '') + '\n[任务异常终止：后台线程已停止]\n'
        db.session.commit()
        logger.info(f"Cleaned up stale task for segment {task.segment}")
    except Exception as e:
        logger.error(f"Error cleaning up stale task: {str(e)}")


@batch_query_bp.route('/status/<segment>', methods=['GET'])
@token_required
def get_batch_query_status(current_user, segment):
    """Get the status of a batch query for a segment."""
    from models.user_preference import BatchQueryTask

    task = BatchQueryTask.query.filter_by(
        user_id=current_user.id, segment=segment
    ).first()

    if not task:
        return jsonify({'status': 'not_found'}), 404

    # Clean up stale tasks (e.g., after server restart)
    _cleanup_stale_task(task)

    return jsonify(task.to_dict()), 200


@batch_query_bp.route('/tasks', methods=['GET'])
@token_required
def get_all_batch_query_tasks(current_user):
    """Get all batch query tasks for the current user."""
    from models.user_preference import BatchQueryTask

    tasks = BatchQueryTask.query.filter_by(user_id=current_user.id).all()
    result = {}
    for task in tasks:
        # Clean up stale tasks (e.g., after server restart)
        _cleanup_stale_task(task)
        result[task.segment] = task.to_dict()
    return jsonify(result), 200
