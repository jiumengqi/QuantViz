# -*- coding: utf-8 -*-
"""
操作日志模型
"""
from datetime import datetime
from db import db


class OperationLog(db.Model):
    """系统操作日志模型"""
    __tablename__ = 'operation_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    username = db.Column(db.String(64), nullable=False)
    action = db.Column(db.String(100), nullable=False, index=True)
    ip_address = db.Column(db.String(45), default='')
    details = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref=db.backref('operation_logs', lazy='dynamic'))

    def __repr__(self):
        return f'<OperationLog {self.id}: {self.action} by {self.username}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'ip_address': self.ip_address,
            'details': self.details,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    @staticmethod
    def log(user_id, username, action, ip_address='', details=''):
        """记录操作日志的便捷方法"""
        log_entry = OperationLog(
            user_id=user_id,
            username=username,
            action=action,
            ip_address=ip_address,
            details=details
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
