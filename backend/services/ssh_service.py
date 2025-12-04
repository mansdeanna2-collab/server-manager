import paramiko
import socket
from io import StringIO

class SSHService:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
    
    def connect(self):
        """Establish SSH connection"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            return True
        except Exception as e:
            print(f"SSH connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
    
    def execute_command(self, command):
        """Execute a command on the remote server"""
        if not self.client:
            return None
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if error:
                print(f"Command error: {error}")
            
            return output
        except Exception as e:
            print(f"Command execution failed: {str(e)}")
            return None
    
    def get_system_info(self):
        """Get comprehensive system information"""
        if not self.connect():
            return None
        
        try:
            info = {}
            
            # OS Information
            os_info = self.execute_command('cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d \'"\'')
            if not os_info:
                os_info = self.execute_command('uname -s')
            info['os'] = os_info or 'Unknown'
            
            # CPU Information
            cpu_count = self.execute_command('nproc')
            cpu_usage = self.execute_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
            info['cpu'] = f"{cpu_usage}% ({cpu_count} cores)" if cpu_usage and cpu_count else 'Unknown'
            
            # Memory Information
            mem_info = self.execute_command("free -h | awk 'NR==2{print $2,$3,$4}'")
            if mem_info:
                parts = mem_info.split()
                if len(parts) >= 3:
                    info['memory'] = f"Total: {parts[0]}, Used: {parts[1]}, Free: {parts[2]}"
                else:
                    info['memory'] = mem_info
            else:
                info['memory'] = 'Unknown'
            
            # Disk Information
            disk_info = self.execute_command("df -h / | awk 'NR==2{print $2,$3,$4,$5}'")
            if disk_info:
                parts = disk_info.split()
                if len(parts) >= 4:
                    info['disk'] = f"Total: {parts[0]}, Used: {parts[1]} ({parts[3]}), Free: {parts[2]}"
                else:
                    info['disk'] = disk_info
            else:
                info['disk'] = 'Unknown'
            
            # Uptime
            uptime = self.execute_command("uptime -p")
            if not uptime:
                uptime = self.execute_command("uptime | awk '{print $3,$4}'")
            info['uptime'] = uptime or 'Unknown'
            
            return info
        except Exception as e:
            print(f"Failed to get system info: {str(e)}")
            return None
        finally:
            self.disconnect()
    
    def verify_credentials(self):
        """Verify if credentials are correct"""
        result = self.connect()
        if result:
            self.disconnect()
        return result
