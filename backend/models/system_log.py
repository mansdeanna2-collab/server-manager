from models import db
from utils import china_now


class SystemLog(db.Model):
    """系统日志模型 - 存储系统操作日志"""
    __tablename__ = 'system_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(80), nullable=True)  # 存储用户名快照
    log_type = db.Column(db.String(50), nullable=False)  # login, logout, server_connect, server_modify, password_change, backup, etc.
    action = db.Column(db.String(100), nullable=False)  # 具体操作描述
    target = db.Column(db.String(255), nullable=True)  # 操作目标（如服务器IP）
    details = db.Column(db.Text, nullable=True)  # 详细信息（JSON格式）
    ip_address = db.Column(db.String(45), nullable=True)  # 客户端IP
    status = db.Column(db.String(20), default='success')  # success, failed, warning
    created_at = db.Column(db.DateTime, default=china_now, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'log_type': self.log_type,
            'action': self.action,
            'target': self.target,
            'details': self.details,
            'ip_address': self.ip_address,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# 日志类型常量
LOG_TYPE_LOGIN = 'login'
LOG_TYPE_LOGOUT = 'logout'
LOG_TYPE_LOGIN_FAILED = 'login_failed'
LOG_TYPE_PASSWORD_CHANGE = 'password_change'
LOG_TYPE_SERVER_CONNECT = 'server_connect'
LOG_TYPE_SERVER_CREATE = 'server_create'
LOG_TYPE_SERVER_UPDATE = 'server_update'
LOG_TYPE_SERVER_DELETE = 'server_delete'
LOG_TYPE_SERVER_CHECK = 'server_check'
LOG_TYPE_BACKUP = 'backup'
LOG_TYPE_SETTINGS = 'settings'
LOG_TYPE_IMPORT = 'import'
