# -*- coding: utf-8 -*-
"""
通知服务模块
"""
from datetime import datetime
from db import db
from services.models.notification import Notification


class NotificationService:
    """通知服务类"""

    @staticmethod
    def create_notification(user_id, title, content, notification_type='system'):
        """
        创建通知

        Args:
            user_id: 用户ID
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型 (system/system/交易/策略)

        Returns:
            Notification: 创建的通知对象
        """
        notification = Notification(
            user_id=user_id,
            title=title,
            content=content,
            type=notification_type,
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def get_user_notifications(user_id, page=1, per_page=20, unread_only=False):
        """
        获取用户通知列表

        Args:
            user_id: 用户ID
            page: 页码
            per_page: 每页数量
            unread_only: 仅返回未读通知

        Returns:
            tuple: (通知列表, 总数)
        """
        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        query = query.order_by(Notification.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return pagination.items, pagination.total

    @staticmethod
    def get_unread_count(user_id):
        """
        获取用户未读通知数量

        Args:
            user_id: 用户ID

        Returns:
            int: 未读通知数量
        """
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """
        标记通知为已读

        Args:
            notification_id: 通知ID
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if not notification:
            return False

        notification.is_read = True
        db.session.commit()
        return True

    @staticmethod
    def mark_all_as_read(user_id):
        """
        标记所有通知为已读

        Args:
            user_id: 用户ID

        Returns:
            int: 更新的通知数量
        """
        updated = Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        return updated

    @staticmethod
    def delete_notification(notification_id, user_id):
        """
        删除通知

        Args:
            notification_id: 通知ID
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if not notification:
            return False

        db.session.delete(notification)
        db.session.commit()
        return True

    @staticmethod
    def delete_all_read(user_id):
        """
        删除所有已读通知

        Args:
            user_id: 用户ID

        Returns:
            int: 删除的通知数量
        """
        deleted = Notification.query.filter_by(user_id=user_id, is_read=True).delete()
        db.session.commit()
        return deleted

    @staticmethod
    def send_system_notification(user_id, title, content):
        """发送系统通知"""
        return NotificationService.create_notification(user_id, title, content, 'system')

    @staticmethod
    def send_trade_notification(user_id, title, content):
        """发送交易通知"""
        return NotificationService.create_notification(user_id, title, content, 'trade')

    @staticmethod
    def send_strategy_notification(user_id, title, content):
        """发送策略通知"""
        return NotificationService.create_notification(user_id, title, content, 'strategy')
