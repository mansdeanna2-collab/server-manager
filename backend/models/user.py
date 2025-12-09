from models import db
from utils import china_now
import bcrypt


class User(db.Model):
    """用户数据模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=china_now)

    def set_password(self, password):
        """哈希并设置用户密码"""
        self.password_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

    def check_password(self, password):
        """检查提供的密码是否与哈希匹配"""
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
