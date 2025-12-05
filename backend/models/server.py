from datetime import datetime
from models import db

class Server(db.Model):
    __tablename__ = 'servers'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    port = db.Column(db.Integer, default=22)
    username = db.Column(db.String(100), nullable=False)
    encrypted_password = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='unknown')  # online, offline, unknown
    last_checked = db.Column(db.DateTime)
    os_info = db.Column(db.String(255))
    cpu_info = db.Column(db.String(255))
    memory_info = db.Column(db.String(255))
    disk_info = db.Column(db.String(255))
    uptime = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'port': self.port,
            'username': self.username,
            'notes': self.notes,
            'status': self.status,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'os_info': self.os_info,
            'cpu_info': self.cpu_info,
            'memory_info': self.memory_info,
            'disk_info': self.disk_info,
            'uptime': self.uptime,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
