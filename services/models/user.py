# -*- coding: utf-8 -*-
"""
用户模型模块
"""
import os
import sys

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到Python路径中
project_dir = os.path.abspath(os.path.join(current_dir, '../../'))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from db import db


class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # user, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    # 新增字段
    avatar = db.Column(db.String(255), default='')  # 头像文件名
    phone = db.Column(db.String(20), default='')  # 电话号码
    bio = db.Column(db.Text, default='')  # 个人简介
    theme_preference = db.Column(db.String(10), default='light')  # 主题偏好
    refresh_frequency = db.Column(db.Integer, default=5)  # 行情刷新频率（秒）
    notification_email = db.Column(db.Boolean, default=True)  # 邮件通知偏好
    notification_browser = db.Column(db.Boolean, default=False)  # 浏览器通知偏好
    backtest_default_capital = db.Column(db.Float, default=100000.0)  # 回测默认资金
    backtest_default_fee = db.Column(db.Float, default=0.0003)  # 回测默认手续费
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """设置密码（哈希加密）"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        """是否为管理员"""
        return self.role == 'admin'
    
    @property
    def is_locked(self):
        """是否被锁定"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    def increment_login_attempts(self):
        """增加登录尝试次数"""
        self.login_attempts += 1
        if self.login_attempts >= 5:  # 5次尝试后锁定
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)  # 锁定15分钟
        db.session.commit()
    
    def reset_login_attempts(self):
        """重置登录尝试次数"""
        self.login_attempts = 0
        self.locked_until = None
        db.session.commit()
    
    def generate_reset_token(self, expires_in=3600):
        """生成密码重置令牌"""
        from itsdangerous import TimedSerializer
        from config import Config
        s = TimedSerializer(Config.SECRET_KEY)
        return s.dumps({'user_id': self.id})
    
    @staticmethod
    def verify_reset_token(token, expires_in=3600):
        """验证密码重置令牌"""
        from itsdangerous import TimedSerializer, BadSignature, SignatureExpired
        from config import Config
        s = TimedSerializer(Config.SECRET_KEY)
        try:
            data = s.loads(token, max_age=expires_in)
        except (BadSignature, SignatureExpired):
            return None
        return User.query.get(data['user_id'])
