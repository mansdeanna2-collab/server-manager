from models import db
from utils import china_now


class IpCheckStatus(db.Model):
    """IP检测状态模型 - 存储IP的ping和端口检测结果"""
    __tablename__ = 'ip_check_status'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    port_checked = db.Column(db.Boolean, default=False)
    ping_checked = db.Column(db.Boolean, default=False)
    ping_online = db.Column(db.Boolean, default=False)
    port_22 = db.Column(db.Boolean, default=False)
    port_3389 = db.Column(db.Boolean, default=False)
    last_checked = db.Column(db.DateTime, default=china_now)
    created_at = db.Column(db.DateTime, default=china_now)
    updated_at = db.Column(db.DateTime, default=china_now, onupdate=china_now)

    # 添加复合唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'ip_address', name='uq_user_ip_check'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'port_checked': self.port_checked,
            'ping_checked': self.ping_checked,
            'ping_online': self.ping_online,
            'port_22': self.port_22,
            'port_3389': self.port_3389,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None
        }


class IpIdResult(db.Model):
    """IP ID查询结果模型 - 存储IP的ID查询结果和日志"""
    __tablename__ = 'ip_id_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    id_result = db.Column(db.String(255))
    log_output = db.Column(db.Text)
    last_queried = db.Column(db.DateTime, default=china_now)
    created_at = db.Column(db.DateTime, default=china_now)
    updated_at = db.Column(db.DateTime, default=china_now, onupdate=china_now)

    # 添加复合唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'ip_address', name='uq_user_ip_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'id_result': self.id_result,
            'log_output': self.log_output,
            'last_queried': self.last_queried.isoformat() if self.last_queried else None
        }


class SegmentNote(db.Model):
    """IP段备注模型 - 存储IP段的备注信息"""
    __tablename__ = 'segment_notes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    segment = db.Column(db.String(45), nullable=False)  # e.g., "192.168.1"
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=china_now)
    updated_at = db.Column(db.DateTime, default=china_now, onupdate=china_now)

    # 添加复合唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'segment', name='uq_user_segment_note'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'segment': self.segment,
            'note': self.note,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SegmentFavorite(db.Model):
    """IP段收藏模型 - 存储用户收藏的IP段"""
    __tablename__ = 'segment_favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    segment = db.Column(db.String(45), nullable=False)  # e.g., "192.168.1"
    created_at = db.Column(db.DateTime, default=china_now)

    # 添加复合唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'segment', name='uq_user_segment_favorite'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'segment': self.segment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ServerFavorite(db.Model):
    """服务器收藏模型 - 存储用户收藏的服务器"""
    __tablename__ = 'server_favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=china_now)

    # 添加复合唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'server_id', name='uq_user_server_favorite'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
