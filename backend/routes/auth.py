from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime, timezone
from functools import wraps
from models.user import User
from models import db
from config import Config
from services.log_service import (
    log_login_success, log_login_failed, log_logout, log_password_change
)
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
logger = logging.getLogger(__name__)


def token_required(f):
    """JWT令牌验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'message': 'Token format invalid'}), 401

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return jsonify({'message': 'Token validation failed'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.get_json()

        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Username and password are required'}), 400

        user = User.query.filter_by(username=data['username']).first()

        if not user or not user.check_password(data['password']):
            logger.warning(f"Failed login attempt for username: {data.get('username')}")
            log_login_failed(data.get('username'))
            return jsonify({'message': 'Invalid credentials'}), 401

        # Check if TOTP is enabled for this user
        if user.totp_enabled:
            totp_code = data.get('totp_code')
            if not totp_code:
                # Return a special response indicating TOTP is required
                return jsonify({
                    'message': 'TOTP verification required',
                    'totp_required': True
                }), 200

            # Verify TOTP code
            if not user.verify_totp(totp_code):
                logger.warning(f"Failed TOTP verification for username: {data.get('username')}")
                log_login_failed(data.get('username'))
                return jsonify({'message': 'Invalid verification code'}), 401

        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.now(timezone.utc) + Config.JWT_ACCESS_TOKEN_EXPIRES
        }, Config.JWT_SECRET_KEY, algorithm='HS256')

        logger.info(f"User {user.username} logged in successfully")
        log_login_success(user)

        return jsonify({
            'token': token,
            'user': user.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """用户登出接口"""
    logger.info(f"User {current_user.username} logged out")
    log_logout(current_user)
    # In a stateless JWT system, logout is handled client-side
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """获取当前用户信息"""
    return jsonify(current_user.to_dict()), 200


@auth_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_token(current_user):
    """刷新JWT令牌"""
    try:
        token = jwt.encode({
            'user_id': current_user.id,
            'exp': datetime.now(timezone.utc) + Config.JWT_ACCESS_TOKEN_EXPIRES
        }, Config.JWT_SECRET_KEY, algorithm='HS256')

        return jsonify({'token': token}), 200
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'message': 'Token refresh failed'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """修改用户密码"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'message': '请提供请求数据'}), 400

        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not old_password or not new_password:
            return jsonify({'message': '请提供旧密码和新密码'}), 400

        # Verify old password
        if not current_user.check_password(old_password):
            logger.warning(f"Failed password change attempt for user: {current_user.username}")
            log_password_change(current_user, success=False)
            return jsonify({'message': '旧密码错误'}), 401

        # Validate new password length
        if len(new_password) < 6:
            return jsonify({'message': '新密码长度不能少于6个字符'}), 400

        # Set new password
        current_user.set_password(new_password)
        db.session.commit()

        logger.info(f"User {current_user.username} changed password successfully")
        log_password_change(current_user, success=True)
        return jsonify({'message': '密码修改成功'}), 200
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return jsonify({'message': '密码修改失败', 'error': str(e)}), 500


# ============ TOTP (Google Authenticator) APIs ============

@auth_bp.route('/totp/setup', methods=['POST'])
@token_required
def setup_totp(current_user):
    """生成TOTP密钥，返回用于二维码的URI"""
    try:
        # Generate new secret
        secret = current_user.generate_totp_secret()
        db.session.commit()

        # Get the URI for QR code
        uri = current_user.get_totp_uri()

        return jsonify({
            'success': True,
            'secret': secret,
            'uri': uri,
            'message': '请使用Google Authenticator扫描二维码'
        }), 200
    except Exception as e:
        logger.error(f"TOTP setup error: {str(e)}")
        return jsonify({'message': f'设置失败: {str(e)}'}), 500


@auth_bp.route('/totp/enable', methods=['POST'])
@token_required
def enable_totp(current_user):
    """启用TOTP验证（需要先验证一次验证码）"""
    try:
        data = request.get_json()

        if not data or not data.get('code'):
            return jsonify({'message': '请提供验证码'}), 400

        # Verify the code before enabling
        if not current_user.totp_secret:
            return jsonify({'message': '请先设置TOTP密钥'}), 400

        if not current_user.verify_totp(data['code']):
            return jsonify({'message': '验证码错误，请重试'}), 400

        current_user.totp_enabled = True
        db.session.commit()

        logger.info(f"User {current_user.username} enabled TOTP")
        return jsonify({
            'success': True,
            'message': '谷歌验证已启用'
        }), 200
    except Exception as e:
        logger.error(f"TOTP enable error: {str(e)}")
        return jsonify({'message': f'启用失败: {str(e)}'}), 500


@auth_bp.route('/totp/disable', methods=['POST'])
@token_required
def disable_totp(current_user):
    """禁用TOTP验证"""
    try:
        data = request.get_json()

        # If TOTP is enabled, require verification before disabling
        if current_user.totp_enabled:
            if not data or not data.get('code'):
                return jsonify({'message': '请提供验证码以禁用谷歌验证'}), 400

            if not current_user.verify_totp(data['code']):
                return jsonify({'message': '验证码错误'}), 400

        current_user.totp_enabled = False
        current_user.totp_secret = None
        db.session.commit()

        logger.info(f"User {current_user.username} disabled TOTP")
        return jsonify({
            'success': True,
            'message': '谷歌验证已禁用'
        }), 200
    except Exception as e:
        logger.error(f"TOTP disable error: {str(e)}")
        return jsonify({'message': f'禁用失败: {str(e)}'}), 500


@auth_bp.route('/totp/status', methods=['GET'])
@token_required
def get_totp_status(current_user):
    """获取当前用户的TOTP状态"""
    return jsonify({
        'totp_enabled': current_user.totp_enabled,
        'totp_configured': current_user.totp_secret is not None
    }), 200
