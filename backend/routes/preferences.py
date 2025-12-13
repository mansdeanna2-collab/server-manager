from flask import Blueprint, request, jsonify
from models import db
from models.user_preference import (
    IpCheckStatus, IpIdResult, SegmentNote, SegmentFavorite, ServerFavorite
)
from routes.auth import token_required
from utils import china_now
import logging

preferences_bp = Blueprint('preferences', __name__, url_prefix='/api/preferences')
logger = logging.getLogger(__name__)


# ============ IP Check Status APIs ============

@preferences_bp.route('/ip-check-status', methods=['GET'])
@token_required
def get_all_ip_check_status(current_user):
    """获取当前用户的所有IP检测状态"""
    statuses = IpCheckStatus.query.filter_by(user_id=current_user.id).all()
    result = {}
    for status in statuses:
        result[status.ip_address] = status.to_dict()
    return jsonify(result), 200


@preferences_bp.route('/ip-check-status', methods=['POST'])
@token_required
def save_ip_check_status(current_user):
    """保存IP检测状态"""
    data = request.get_json()

    if not data or not data.get('ip_address'):
        return jsonify({'message': '请提供IP地址'}), 400

    ip_address = data['ip_address']

    # 查找或创建记录
    status = IpCheckStatus.query.filter_by(
        user_id=current_user.id,
        ip_address=ip_address
    ).first()

    if not status:
        status = IpCheckStatus(
            user_id=current_user.id,
            ip_address=ip_address
        )
        db.session.add(status)

    # 更新状态
    status.port_checked = data.get('port_checked', False)
    status.ping_checked = data.get('ping_checked', False)
    status.ping_online = data.get('ping_online', False)
    status.port_22 = data.get('port_22', False)
    status.port_3389 = data.get('port_3389', False)
    status.last_checked = china_now()
    status.updated_at = china_now()

    db.session.commit()

    return jsonify(status.to_dict()), 200


@preferences_bp.route('/ip-check-status/batch', methods=['POST'])
@token_required
def save_ip_check_status_batch(current_user):
    """批量保存IP检测状态"""
    data = request.get_json()

    if not data or not isinstance(data, list):
        return jsonify({'message': '请提供IP检测状态列表'}), 400

    results = []
    for item in data:
        ip_address = item.get('ip_address')
        if not ip_address:
            continue

        status = IpCheckStatus.query.filter_by(
            user_id=current_user.id,
            ip_address=ip_address
        ).first()

        if not status:
            status = IpCheckStatus(
                user_id=current_user.id,
                ip_address=ip_address
            )
            db.session.add(status)

        status.port_checked = item.get('port_checked', False)
        status.ping_checked = item.get('ping_checked', False)
        status.ping_online = item.get('ping_online', False)
        status.port_22 = item.get('port_22', False)
        status.port_3389 = item.get('port_3389', False)
        status.last_checked = china_now()
        status.updated_at = china_now()

        results.append(status.to_dict())

    db.session.commit()

    return jsonify(results), 200


# ============ IP ID Result APIs ============

@preferences_bp.route('/ip-id-results', methods=['GET'])
@token_required
def get_all_ip_id_results(current_user):
    """获取当前用户的所有IP ID查询结果"""
    results = IpIdResult.query.filter_by(user_id=current_user.id).all()
    result_dict = {}
    for result in results:
        result_dict[result.ip_address] = result.to_dict()
    return jsonify(result_dict), 200


@preferences_bp.route('/ip-id-results', methods=['POST'])
@token_required
def save_ip_id_result(current_user):
    """保存IP ID查询结果"""
    data = request.get_json()

    if not data or not data.get('ip_address'):
        return jsonify({'message': '请提供IP地址'}), 400

    ip_address = data['ip_address']

    # 查找或创建记录
    result = IpIdResult.query.filter_by(
        user_id=current_user.id,
        ip_address=ip_address
    ).first()

    if not result:
        result = IpIdResult(
            user_id=current_user.id,
            ip_address=ip_address
        )
        db.session.add(result)

    # 更新结果
    result.id_result = data.get('id_result')
    result.log_output = data.get('log_output')
    result.last_queried = china_now()
    result.updated_at = china_now()

    db.session.commit()

    return jsonify(result.to_dict()), 200


# ============ Segment Notes APIs ============

@preferences_bp.route('/segment-notes', methods=['GET'])
@token_required
def get_all_segment_notes(current_user):
    """获取当前用户的所有IP段备注"""
    notes = SegmentNote.query.filter_by(user_id=current_user.id).all()
    result = {}
    for note in notes:
        result[note.segment] = note.note
    return jsonify(result), 200


@preferences_bp.route('/segment-notes', methods=['POST'])
@token_required
def save_segment_note(current_user):
    """保存IP段备注"""
    data = request.get_json()

    if not data or not data.get('segment'):
        return jsonify({'message': '请提供IP段'}), 400

    segment = data['segment']
    note_text = data.get('note', '').strip()

    # 查找现有记录
    note = SegmentNote.query.filter_by(
        user_id=current_user.id,
        segment=segment
    ).first()

    if not note_text:
        # 如果备注为空，删除记录
        if note:
            db.session.delete(note)
            db.session.commit()
        return jsonify({'message': '备注已删除'}), 200

    if not note:
        note = SegmentNote(
            user_id=current_user.id,
            segment=segment
        )
        db.session.add(note)

    note.note = note_text
    note.updated_at = china_now()

    db.session.commit()

    return jsonify(note.to_dict()), 200


# ============ Segment Favorites APIs ============

@preferences_bp.route('/segment-favorites', methods=['GET'])
@token_required
def get_segment_favorites(current_user):
    """获取当前用户收藏的所有IP段"""
    favorites = SegmentFavorite.query.filter_by(user_id=current_user.id).all()
    return jsonify([f.segment for f in favorites]), 200


@preferences_bp.route('/segment-favorites', methods=['POST'])
@token_required
def toggle_segment_favorite(current_user):
    """切换IP段收藏状态"""
    data = request.get_json()

    if not data or not data.get('segment'):
        return jsonify({'message': '请提供IP段'}), 400

    segment = data['segment']

    # 查找现有收藏
    favorite = SegmentFavorite.query.filter_by(
        user_id=current_user.id,
        segment=segment
    ).first()

    if favorite:
        # 取消收藏
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'favorited': False, 'segment': segment}), 200
    else:
        # 添加收藏
        favorite = SegmentFavorite(
            user_id=current_user.id,
            segment=segment
        )
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'favorited': True, 'segment': segment}), 200


# ============ Server Favorites APIs ============

@preferences_bp.route('/server-favorites', methods=['GET'])
@token_required
def get_server_favorites(current_user):
    """获取当前用户收藏的所有服务器ID"""
    favorites = ServerFavorite.query.filter_by(user_id=current_user.id).all()
    return jsonify([f.server_id for f in favorites]), 200


@preferences_bp.route('/server-favorites', methods=['POST'])
@token_required
def toggle_server_favorite(current_user):
    """切换服务器收藏状态"""
    data = request.get_json()

    if not data or not data.get('server_id'):
        return jsonify({'message': '请提供服务器ID'}), 400

    server_id = data['server_id']

    # 查找现有收藏
    favorite = ServerFavorite.query.filter_by(
        user_id=current_user.id,
        server_id=server_id
    ).first()

    if favorite:
        # 取消收藏
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'favorited': False, 'server_id': server_id}), 200
    else:
        # 添加收藏
        favorite = ServerFavorite(
            user_id=current_user.id,
            server_id=server_id
        )
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'favorited': True, 'server_id': server_id}), 200
