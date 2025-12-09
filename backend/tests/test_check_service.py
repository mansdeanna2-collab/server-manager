from services.check_service import CheckService


def test_overall_online_when_port_is_open(monkeypatch):
    monkeypatch.setattr(CheckService, 'ping_check', staticmethod(lambda host, timeout=None: False))
    monkeypatch.setattr(CheckService, 'port_check', staticmethod(lambda host, port, timeout=None: True))

    status = CheckService.check_server_status('example.com', 22)

    assert status['ping'] is False
    assert status['port'] is True
    assert status['overall'] == 'online'


def test_overall_offline_when_all_checks_fail(monkeypatch):
    monkeypatch.setattr(CheckService, 'ping_check', staticmethod(lambda host, timeout=None: False))
    monkeypatch.setattr(CheckService, 'port_check', staticmethod(lambda host, port, timeout=None: False))

    status = CheckService.check_server_status('example.com', 22)

    assert status['ping'] is False
    assert status['port'] is False
    assert status['overall'] == 'offline'


def test_get_ip_region_hong_kong():
    region = CheckService.get_ip_region('103.10.20.30')
    assert region['code'] == 'HK'
    assert region['name'] == '香港'
    assert region['flag'] == '🇭🇰'


def test_get_ip_region_singapore():
    region = CheckService.get_ip_region('13.212.10.20')
    assert region['code'] == 'SG'
    assert region['name'] == '新加坡'
    assert region['flag'] == '🇸🇬'


def test_get_ip_region_united_states():
    region = CheckService.get_ip_region('52.20.30.40')
    assert region['code'] == 'US'
    assert region['name'] == '美国'
    assert region['flag'] == '🇺🇸'


def test_get_ip_region_unknown():
    region = CheckService.get_ip_region('192.168.1.1')
    assert region['code'] == 'UNKNOWN'
    assert region['name'] == '未知'
    assert region['flag'] == '🌐'


def test_get_port_type_ssh():
    port_info = CheckService.get_port_type(22)
    assert port_info['type'] == 'SSH'
    assert port_info['os_hint'] == 'Linux/Unix'
    assert port_info['icon'] == '🐧'


def test_get_port_type_rdp():
    port_info = CheckService.get_port_type(3389)
    assert port_info['type'] == 'RDP'
    assert port_info['os_hint'] == 'Windows'
    assert port_info['icon'] == '🪟'


def test_get_port_type_custom():
    port_info = CheckService.get_port_type(9999)
    assert port_info['type'] == 'Custom'
    assert port_info['os_hint'] == 'Unknown'
    assert port_info['icon'] == '🔌'


def test_check_server_status_includes_region_and_port_type(monkeypatch):
    monkeypatch.setattr(CheckService, 'ping_check', staticmethod(lambda host, timeout=None: True))
    monkeypatch.setattr(CheckService, 'port_check', staticmethod(lambda host, port, timeout=None: True))

    status = CheckService.check_server_status('103.10.20.30', 22)

    assert status['region']['code'] == 'HK'
    assert status['region']['name'] == '香港'
    assert status['port_type']['type'] == 'SSH'
    assert status['port_type']['icon'] == '🐧'
    assert 'detail' in status


def test_rdp_port_does_not_attempt_ssh_auth(monkeypatch):
    """RDP (port 3389) should not attempt SSH authentication"""
    monkeypatch.setattr(CheckService, 'ping_check', staticmethod(lambda host, timeout=None: True))
    monkeypatch.setattr(CheckService, 'port_check', staticmethod(lambda host, port, timeout=None: True))

    # Pass credentials that would fail SSH auth - but RDP should skip SSH check
    status = CheckService.check_server_status('192.168.1.100', 3389, 'user', 'password')

    # For RDP port, auth should be None (not attempted) and no SSH error should occur
    assert status['port'] is True
    assert status['overall'] == 'online'
    assert status['port_type']['type'] == 'RDP'
    assert status['auth'] is None  # SSH auth should not be attempted for RDP
    assert status['error_type'] is None  # No error because SSH auth was skipped
