"""系统日志服务 - 提供统一的日志记录功能"""
from flask import request
from models import db
from models.system_log import (
    SystemLog,
    LOG_TYPE_LOGIN,
    LOG_TYPE_LOGOUT,
    LOG_TYPE_LOGIN_FAILED,
    LOG_TYPE_PASSWORD_CHANGE,
    LOG_TYPE_SERVER_CONNECT,
    LOG_TYPE_SERVER_CREATE,
    LOG_TYPE_SERVER_UPDATE,
    LOG_TYPE_SERVER_DELETE,
    LOG_TYPE_SERVER_CHECK,
    LOG_TYPE_BACKUP,
    LOG_TYPE_SETTINGS,
    LOG_TYPE_IMPORT
)
import logging
import json

logger = logging.getLogger(__name__)


def get_client_ip():
    """获取客户端IP地址"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def log_action(
    log_type,
    action,
    user=None,
    target=None,
    details=None,
    status='success'
):
    """记录系统操作日志
    
    Args:
        log_type: 日志类型（使用 LOG_TYPE_* 常量）
        action: 操作描述
        user: 用户对象（可选）
        target: 操作目标（如服务器IP）
        details: 详细信息（dict或str）
        status: 状态（success, failed, warning）
    """
    try:
        # 获取客户端IP
        try:
            client_ip = get_client_ip()
        except RuntimeError:
            # Flask请求上下文不可用时（如在后台任务中调用）
            client_ip = None
        
        # 序列化详细信息
        if isinstance(details, dict):
            details = json.dumps(details, ensure_ascii=False)
        
        # 创建日志记录
        log_entry = SystemLog(
            user_id=user.id if user else None,
            username=user.username if user else None,
            log_type=log_type,
            action=action,
            target=target,
            details=details,
            ip_address=client_ip,
            status=status
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        logger.info(f"System log: [{log_type}] {action} - {target or ''} - {status}")
        
    except Exception as e:
        logger.error(f"Failed to log action: {str(e)}")
        # 不抛出异常，避免影响主要业务逻辑
        try:
            db.session.rollback()
        except Exception as rollback_error:
            logger.warning(f"Failed to rollback after log error: {str(rollback_error)}")


# 便捷方法
def log_login_success(user):
    """记录登录成功"""
    log_action(
        LOG_TYPE_LOGIN,
        '用户登录成功',
        user=user,
        status='success'
    )


def log_login_failed(username):
    """记录登录失败"""
    log_action(
        LOG_TYPE_LOGIN_FAILED,
        f'用户登录失败',
        target=username,
        status='failed'
    )


def log_logout(user):
    """记录登出"""
    log_action(
        LOG_TYPE_LOGOUT,
        '用户登出',
        user=user,
        status='success'
    )


def log_password_change(user, success=True):
    """记录密码修改"""
    log_action(
        LOG_TYPE_PASSWORD_CHANGE,
        '修改密码成功' if success else '修改密码失败',
        user=user,
        status='success' if success else 'failed'
    )


def log_server_connect(user, server_ip, success=True, error_msg=None):
    """记录服务器连接"""
    details = None
    if error_msg:
        details = {'error': error_msg}
    log_action(
        LOG_TYPE_SERVER_CONNECT,
        '连接服务器' + ('成功' if success else '失败'),
        user=user,
        target=server_ip,
        details=details,
        status='success' if success else 'failed'
    )


def log_server_create(user, server_ip, port, username):
    """记录创建服务器"""
    log_action(
        LOG_TYPE_SERVER_CREATE,
        '创建服务器',
        user=user,
        target=server_ip,
        details={'port': port, 'username': username},
        status='success'
    )


def log_server_update(user, server_ip, changes=None):
    """记录更新服务器"""
    log_action(
        LOG_TYPE_SERVER_UPDATE,
        '更新服务器',
        user=user,
        target=server_ip,
        details=changes,
        status='success'
    )


def log_server_delete(user, server_ip):
    """记录删除服务器"""
    log_action(
        LOG_TYPE_SERVER_DELETE,
        '删除服务器',
        user=user,
        target=server_ip,
        status='success'
    )


def log_server_check(user, server_ip, status_result):
    """记录检测服务器"""
    log_action(
        LOG_TYPE_SERVER_CHECK,
        f'检测服务器状态: {status_result}',
        user=user,
        target=server_ip,
        status='success'
    )


def log_backup(user, backup_filename, success=True, error_msg=None):
    """记录创建备份"""
    details = None
    if error_msg:
        details = {'error': error_msg}
    log_action(
        LOG_TYPE_BACKUP,
        '创建系统备份' + ('成功' if success else '失败'),
        user=user,
        target=backup_filename,
        details=details,
        status='success' if success else 'failed'
    )


def log_settings_change(user, setting_type):
    """记录设置修改"""
    log_action(
        LOG_TYPE_SETTINGS,
        f'修改系统设置: {setting_type}',
        user=user,
        status='success'
    )


def log_import(user, imported_count, skipped_count, error_count):
    """记录服务器导入"""
    log_action(
        LOG_TYPE_IMPORT,
        f'导入服务器: 成功{imported_count}个, 跳过{skipped_count}个, 失败{error_count}个',
        user=user,
        details={
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': error_count
        },
        status='success' if error_count == 0 else 'warning'
    )
