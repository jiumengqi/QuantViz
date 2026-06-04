# -*- coding: utf-8 -*-
"""
通知路由模块
"""
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from services.notification import NotificationService

# 创建通知蓝图
notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/notifications')
@login_required
def notifications_page():
    """通知页面"""
    return render_template('notifications.html')


@notifications_bp.route('/api/notifications')
@login_required
def get_notifications():
    """获取用户通知列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    notifications, total = NotificationService.get_user_notifications(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        unread_only=unread_only
    )

    return jsonify({
        'success': True,
        'notifications': [n.to_dict() for n in notifications],
        'total': total,
        'page': page,
        'per_page': per_page
    })


@notifications_bp.route('/api/notifications/unread-count')
@login_required
def get_unread_count():
    """获取未读通知数量"""
    count = NotificationService.get_unread_count(current_user.id)
    return jsonify({
        'success': True,
        'unread_count': count
    })


@notifications_bp.route('/api/notifications/read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """标记通知已读"""
    success = NotificationService.mark_as_read(notification_id, current_user.id)

    if success:
        return jsonify({'success': True, 'message': '通知已标记为已读'})
    else:
        return jsonify({'success': False, 'message': '通知不存在'}), 404


@notifications_bp.route('/api/notifications/read/all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """标记所有通知已读"""
    count = NotificationService.mark_all_as_read(current_user.id)
    return jsonify({
        'success': True,
        'message': f'已标记{count}条通知为已读',
        'updated_count': count
    })


@notifications_bp.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """删除通知"""
    success = NotificationService.delete_notification(notification_id, current_user.id)

    if success:
        return jsonify({'success': True, 'message': '通知已删除'})
    else:
        return jsonify({'success': False, 'message': '通知不存在'}), 404


@notifications_bp.route('/api/notifications/read/delete-all', methods=['DELETE'])
@login_required
def delete_all_read_notifications():
    """删除所有已读通知"""
    count = NotificationService.delete_all_read(current_user.id)
    return jsonify({
        'success': True,
        'message': f'已删除{count}条已读通知',
        'deleted_count': count
    })
