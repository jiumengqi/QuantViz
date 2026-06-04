# -*- coding: utf-8 -*-
"""
站点内容模型 - 动态内容管理系统
"""
from datetime import datetime
from db import db


class SiteContent(db.Model):
    """网站动态内容表 - 存储所有可编辑的前端文本和配置"""
    __tablename__ = 'site_contents'

    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(50), nullable=False, index=True)
    key = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(20), default='text')
    is_active = db.Column(db.Boolean, default=True, index=True)
    sort_order = db.Column(db.Integer, default=0)
    updated_by = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('section', 'key', name='uq_section_key'),
    )

    def __repr__(self):
        return f'<SiteContent {self.section}/{self.key}: {self.content[:30]}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'section': self.section,
            'key': self.key,
            'content': self.content,
            'content_type': self.content_type,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    @staticmethod
    def get_content(section, key, default=''):
        """获取指定区域和键的内容"""
        item = SiteContent.query.filter_by(
            section=section, key=key, is_active=True
        ).first()
        return item.content if item else default

    @staticmethod
    def get_section(section):
        """获取指定区域的所有内容（按排序排列）"""
        return SiteContent.query.filter_by(
            section=section, is_active=True
        ).order_by(SiteContent.sort_order).all()

    @staticmethod
    def get_all_grouped():
        """获取所有内容，按 section 分组"""
        items = SiteContent.query.filter_by(is_active=True).order_by(
            SiteContent.section, SiteContent.sort_order
        ).all()
        grouped = {}
        for item in items:
            if item.section not in grouped:
                grouped[item.section] = []
            grouped[item.section].append(item.to_dict())
        return grouped


# 默认内容配置
DEFAULT_CONTENT = [
    # ========== hero 区域 ==========
    {'section': 'hero', 'key': 'title', 'content': '金融数学驱动的\n量化投资分析平台', 'content_type': 'text', 'sort_order': 1},
    {'section': 'hero', 'key': 'subtitle', 'content': '融合金融数学理论与计算机技术，为您提供专业的量化分析工具', 'content_type': 'text', 'sort_order': 2},
    {'section': 'hero', 'key': 'button_text', 'content': '开始使用', 'content_type': 'text', 'sort_order': 3},
    {'section': 'hero', 'key': 'button_url', 'content': '/auth/register', 'content_type': 'url', 'sort_order': 4},
    {'section': 'hero', 'key': 'secondary_text', 'content': '了解更多', 'content_type': 'text', 'sort_order': 5},
    {'section': 'hero', 'key': 'secondary_url', 'content': '/features', 'content_type': 'url', 'sort_order': 6},

    # ========== features 区域 ==========
    {'section': 'features', 'key': 'title', 'content': '核心功能', 'content_type': 'text', 'sort_order': 1},
    {'section': 'features', 'key': 'subtitle', 'content': '全面的量化投资分析工具', 'content_type': 'text', 'sort_order': 2},
    {'section': 'features', 'key': 'card1_title', 'content': '数据驱动分析', 'content_type': 'text', 'sort_order': 10},
    {'section': 'features', 'key': 'card1_desc', 'content': '多源金融数据整合，实时行情监控，技术指标分析', 'content_type': 'text', 'sort_order': 11},
    {'section': 'features', 'key': 'card1_icon', 'content': 'fa-line-chart', 'content_type': 'text', 'sort_order': 12},
    {'section': 'features', 'key': 'card2_title', 'content': '策略回测系统', 'content_type': 'text', 'sort_order': 20},
    {'section': 'features', 'key': 'card2_desc', 'content': '内置经典策略模板，支持自定义策略开发与回测评估', 'content_type': 'text', 'sort_order': 21},
    {'section': 'features', 'key': 'card2_icon', 'content': 'fa-cogs', 'content_type': 'text', 'sort_order': 22},
    {'section': 'features', 'key': 'card3_title', 'content': '投资组合管理', 'content_type': 'text', 'sort_order': 30},
    {'section': 'features', 'key': 'card3_desc', 'content': '智能资产配置，风险收益分析，Markowitz优化', 'content_type': 'text', 'sort_order': 31},
    {'section': 'features', 'key': 'card3_icon', 'content': 'fa-pie-chart', 'content_type': 'text', 'sort_order': 32},
    {'section': 'features', 'key': 'card4_title', 'content': 'AI智能助手', 'content_type': 'text', 'sort_order': 40},
    {'section': 'features', 'key': 'card4_desc', 'content': '基于大模型的量化投资助手，解答您的投资疑问', 'content_type': 'text', 'sort_order': 41},
    {'section': 'features', 'key': 'card4_icon', 'content': 'fa-android', 'content_type': 'text', 'sort_order': 42},

    # ========== announcement 区域 ==========
    {'section': 'announcement', 'key': 'title', 'content': '系统公告', 'content_type': 'text', 'sort_order': 1},
    {'section': 'announcement', 'key': 'content', 'content': '欢迎使用股票分析与量化投资平台！系统已升级至3.0版本', 'content_type': 'text', 'sort_order': 2},
    {'section': 'announcement', 'key': 'is_active', 'content': 'true', 'content_type': 'text', 'sort_order': 3},

    # ========== about 区域 ==========
    {'section': 'about', 'key': 'title', 'content': '关于我们', 'content_type': 'text', 'sort_order': 1},
    {'section': 'about', 'key': 'subtitle', 'content': '专业的量化投资分析平台', 'content_type': 'text', 'sort_order': 2},
    {'section': 'about', 'key': 'description', 'content': '我们致力于将先进的金融数学理论与计算机技术相结合，为投资者和研究人员提供全面、专业、高效的量化投资分析工具。平台集成了股票数据分析、策略回测、投资组合优化、风险管理等多种功能，帮助用户在复杂的金融市场中做出更明智的决策。', 'content_type': 'text', 'sort_order': 3},

    # ========== footer 区域 ==========
    {'section': 'footer', 'key': 'about_text', 'content': '股票分析与量化投资平台，融合金融数学理论与计算机技术，为投资者提供专业的量化分析工具。', 'content_type': 'text', 'sort_order': 1},
    {'section': 'footer', 'key': 'contact_email', 'content': 'support@quantviz.com', 'content_type': 'text', 'sort_order': 2},
    {'section': 'footer', 'key': 'copyright', 'content': '© 2025 量化投资分析平台. All rights reserved.', 'content_type': 'text', 'sort_order': 3},
]


def init_default_content():
    """初始化默认内容（仅在内容不存在时插入）"""
    from db import db
    for item in DEFAULT_CONTENT:
        existing = SiteContent.query.filter_by(
            section=item['section'], key=item['key']
        ).first()
        if not existing:
            content = SiteContent(
                section=item['section'],
                key=item['key'],
                content=item['content'],
                content_type=item.get('content_type', 'text'),
                sort_order=item.get('sort_order', 0),
            )
            db.session.add(content)
    db.session.commit()
