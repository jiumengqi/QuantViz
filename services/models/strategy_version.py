# -*- coding: utf-8 -*-
"""
策略版本管理模型
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


class StrategyVersion(db.Model):
    """策略版本"""
    __tablename__ = 'strategy_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategies.id'), nullable=False)  # 关联策略ID
    version_number = db.Column(db.Integer, nullable=False)  # 版本号
    code = db.Column(db.Text, nullable=False)  # 策略代码
    parameters = db.Column(db.Text)  # 策略参数
    description = db.Column(db.Text)  # 版本描述/变更说明
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 创建人
    
    # 关系
    strategy = db.relationship('Strategy', backref=db.backref('versions', lazy='dynamic', order_by='desc(StrategyVersion.version_number)'))
    creator = db.relationship('User', backref=db.backref('created_strategy_versions', lazy='dynamic'))
    
    def __repr__(self):
        return f'<StrategyVersion {self.strategy_id} v{self.version_number}>'
    
    __table_args__ = (
        db.UniqueConstraint('strategy_id', 'version_number', name='_strategy_version_uc'),
        db.Index('ix_strategy_versions_strategy_id', 'strategy_id'),
        db.Index('ix_strategy_versions_created_at', 'created_at'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'strategy_id': self.strategy_id,
            'version_number': self.version_number,
            'code': self.code,
            'parameters': self.parameters,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
