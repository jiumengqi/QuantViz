# -*- coding: utf-8 -*-
"""
社区模型模块
"""
import os
import sys

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到Python路径中
project_dir = os.path.abspath(os.path.join(current_dir, '../../'))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from datetime import datetime
from db import db


class StrategyShare(db.Model):
    """策略分享模型"""
    __tablename__ = 'strategy_shares'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    strategy_name = db.Column(db.String(200), nullable=False)
    strategy_code = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, default='')
    parameters = db.Column(db.Text, default='{}')  # JSON格式存储策略参数
    likes_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关系
    user = db.relationship('User', backref=db.backref('strategy_shares', lazy='dynamic'))
    comments = db.relationship('Comment', backref='strategy_share', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='strategy_share', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<StrategyShare {self.strategy_name}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '未知用户',
            'strategy_name': self.strategy_name,
            'strategy_code': self.strategy_code,
            'description': self.description,
            'parameters': self.parameters,
            'likes_count': self.likes_count,
            'shares_count': self.shares_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'comments_count': self.comments.count()
        }


class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    strategy_share_id = db.Column(db.Integer, db.ForeignKey('strategy_shares.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关系
    user = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))

    def __repr__(self):
        return f'<Comment {self.id}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '未知用户',
            'strategy_share_id': self.strategy_share_id,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Like(db.Model):
    """点赞模型"""
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    strategy_share_id = db.Column(db.Integer, db.ForeignKey('strategy_shares.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 唯一约束：同一用户对同一策略只能点赞一次
    __table_args__ = (
        db.UniqueConstraint('user_id', 'strategy_share_id', name='unique_user_strategy_like'),
    )

    # 关系
    user = db.relationship('User', backref=db.backref('likes', lazy='dynamic'))

    def __repr__(self):
        return f'<Like {self.user_id} -> {self.strategy_share_id}>'
