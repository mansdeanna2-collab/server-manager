"""Tests for fetch_server.py parsing functionality."""
import pytest
from routes.fetch_server import _parse_server_info, _determine_port_and_username, _extract_server_data_regex


class TestParseServerInfo:
    """Test cases for _parse_server_info function."""

    def test_parse_single_server_from_issue(self):
        """Test parsing the exact output format from the issue."""
        output = '''步骤 1/5: 处理中...
步骤 2/5: 处理中...
步骤 3/5: 处理中...
步骤 4/5: 处理中...
步骤 5/5: 处理中...

===== 完整获取结果（控制台输出） =====
{"region":"hkv3","line":"hkv3","cpu":4,"memory":4096,"bandwidth":5,"disk":[],"ddos":0,"os_id":"ubuntu-22.04-server_x86-64","os_name":"Ubuntu 22.04-server  64bit","instance_id":"CLOUD-SADODS-HLZZ","password":"Aa62690946","config_id":6,"ips":["38.181.24.170","38.47.220.35"],"ip":2,"remark":"","name":"CLOUD-SADODS-HLZZ","oid":"73609","uuid":"217f0146-98fb-4e65-9fae-4c5958f2ca11"}

脚本执行完成
'''
        servers = _parse_server_info(output)
        
        assert len(servers) == 1
        assert servers[0]['password'] == 'Aa62690946'
        assert servers[0]['ips'] == ['38.181.24.170', '38.47.220.35']
        assert servers[0]['os_name'] == 'Ubuntu 22.04-server  64bit'
        assert servers[0]['name'] == 'CLOUD-SADODS-HLZZ'

    def test_parse_multiple_servers(self):
        """Test parsing multiple server entries."""
        output = '''===== 完整获取结果（控制台输出） =====
{"region":"hkv3","cpu":2,"memory":4096,"os_id":"ubuntu-22.04","os_name":"Ubuntu 22.04","password":"Pass123","ips":["192.168.1.1"]}
{"region":"sgv2","cpu":4,"memory":8192,"os_id":"centos-8","os_name":"CentOS 8","password":"Pass456","ips":["192.168.1.2"]}
'''
        servers = _parse_server_info(output)
        
        assert len(servers) == 2
        assert servers[0]['ips'] == ['192.168.1.1']
        assert servers[0]['password'] == 'Pass123'
        assert servers[1]['ips'] == ['192.168.1.2']
        assert servers[1]['password'] == 'Pass456'

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        servers = _parse_server_info('')
        assert servers == []

    def test_parse_output_without_marker(self):
        """Test parsing output without the marker line."""
        output = '''Some random output
{"ips":["192.168.1.1"],"password":"test"}
'''
        servers = _parse_server_info(output)
        assert servers == []

    def test_skip_invalid_json(self):
        """Test that invalid JSON is skipped."""
        output = '''===== 完整获取结果（控制台输出） =====
{invalid json}
{"ips":["192.168.1.1"],"password":"test"}
'''
        servers = _parse_server_info(output)
        assert len(servers) == 1
        assert servers[0]['ips'] == ['192.168.1.1']

    def test_skip_missing_required_fields(self):
        """Test that entries without required fields are skipped."""
        output = '''===== 完整获取结果（控制台输出） =====
{"ips":["192.168.1.1"]}
{"password":"test"}
{"ips":["192.168.1.2"],"password":"valid"}
'''
        servers = _parse_server_info(output)
        assert len(servers) == 1
        assert servers[0]['ips'] == ['192.168.1.2']

    def test_parse_with_unknown_characters_marker(self):
        """Test parsing when output contains '未知字符数量' marker.
        
        This tests the fix for the issue where servers weren't added when
        there were unknown characters (incomplete verification).
        """
        output = '''===== 完整获取结果（控制台输出） =====
{"region":"sgbv3","line":"sgbv3","cpu":4,"memory":4096,"bandwidth":5,"disk":[],"ddos":0,"os_id":"windows-server-2022-datacenter_x86-64_cn","os_name":"Windows server 2022 datacenter 64bit (cn)","instance_id":"CLOUD-SYJSGK-6AHH","password":"Ge5,Eb5_Nv6<","config_id":12,"ips":["45.194.18.18"],"ip":1,"remark":"","name":"CLOUD-SYJSGK-6AHH","oid":50515,"uuid":"85716dda-e837-4547-aa6e-69c452af0a80"}
===== 完整获取结果结束 =====

结果已保存到 option_json_30088.txt
未知字符数量(未做二次验证): 2
'''
        servers = _parse_server_info(output)
        
        # Should still parse the server even with unknown characters marker
        assert len(servers) == 1
        assert servers[0]['ips'] == ['45.194.18.18']
        assert servers[0]['password'] == 'Ge5,Eb5_Nv6<'
        assert 'windows' in servers[0]['os_id'].lower()


class TestExtractServerDataRegex:
    """Test cases for _extract_server_data_regex fallback function."""

    def test_extract_from_valid_json_string(self):
        """Test regex extraction from valid JSON string."""
        line = '{"ips":["192.168.1.1","192.168.1.2"],"password":"TestPass123","os_id":"ubuntu-22.04","os_name":"Ubuntu 22.04"}'
        result = _extract_server_data_regex(line)
        
        assert result is not None
        assert result['ips'] == ['192.168.1.1', '192.168.1.2']
        assert result['password'] == 'TestPass123'
        assert result['os_id'] == 'ubuntu-22.04'

    def test_extract_with_corrupted_characters(self):
        """Test regex extraction when some characters are corrupted."""
        # Simulating corrupted JSON where some chars are replaced with ?
        line = '{"region":"sgbv3","?l?ne":"sgbv3","ips":["45.194.18.18"],"password":"Ge5,Eb5_Nv6<"}'
        result = _extract_server_data_regex(line)
        
        # Should still extract the essential fields
        assert result is not None
        assert result['ips'] == ['45.194.18.18']
        assert result['password'] == 'Ge5,Eb5_Nv6<'

    def test_extract_without_ips_returns_none(self):
        """Test that extraction returns None without ips field."""
        line = '{"password":"TestPass123"}'
        result = _extract_server_data_regex(line)
        assert result is None

    def test_extract_without_password_returns_none(self):
        """Test that extraction returns None without password field."""
        line = '{"ips":["192.168.1.1"]}'
        result = _extract_server_data_regex(line)
        assert result is None


class TestDeterminePortAndUsername:
    """Test cases for _determine_port_and_username function."""

    def test_linux_ubuntu_system(self):
        """Test Linux/Ubuntu system detection."""
        server_data = {
            'os_name': 'Ubuntu 22.04-server  64bit',
            'os_id': 'ubuntu-22.04-server_x86-64'
        }
        port, username = _determine_port_and_username(server_data)
        assert port == 22
        assert username == 'root'

    def test_windows_system_by_os_name(self):
        """Test Windows system detection by os_name."""
        server_data = {
            'os_name': 'Windows Server 2019',
            'os_id': 'win2019'
        }
        port, username = _determine_port_and_username(server_data)
        assert port == 3389
        assert username == 'Administrator'

    def test_windows_system_by_os_id(self):
        """Test Windows system detection by os_id."""
        server_data = {
            'os_name': 'Server 2019',
            'os_id': 'windows-server-2019'
        }
        port, username = _determine_port_and_username(server_data)
        assert port == 3389
        assert username == 'Administrator'

    def test_default_to_linux(self):
        """Test that unknown OS defaults to Linux/SSH."""
        server_data = {
            'os_name': '',
            'os_id': ''
        }
        port, username = _determine_port_and_username(server_data)
        assert port == 22
        assert username == 'root'

    def test_centos_system(self):
        """Test CentOS system detection."""
        server_data = {
            'os_name': 'CentOS 8.5 64bit',
            'os_id': 'centos-8.5-x86-64'
        }
        port, username = _determine_port_and_username(server_data)
        assert port == 22
        assert username == 'root'
