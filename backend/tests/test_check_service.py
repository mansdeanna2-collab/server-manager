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
