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
    # Google Authenticator (TOTP) fields
    totp_secret = db.Column(db.String(32), nullable=True)  # Base32 encoded secret
    totp_enabled = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """哈希并设置用户密码"""
        self.password_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

    def check_password(self, password):
        """检查提供的密码是否与哈希匹配"""
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def generate_totp_secret(self):
        """生成新的TOTP密钥"""
        import pyotp
        self.totp_secret = pyotp.random_base32()
        return self.totp_secret

    def get_totp_uri(self):
        """获取用于生成二维码的TOTP URI"""
        import pyotp
        if not self.totp_secret:
            return None
        totp = pyotp.TOTP(self.totp_secret)
        return totp.provisioning_uri(name=self.username, issuer_name="ServerManager")

    def verify_totp(self, code):
        """验证TOTP验证码"""
        import pyotp
        if not self.totp_secret:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(code)

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'totp_enabled': self.totp_enabled
        }
