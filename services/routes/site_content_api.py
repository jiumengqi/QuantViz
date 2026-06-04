# -*- coding: utf-8 -*-
"""
站点内容管理 API 路由
"""
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from db import db
from services.models.site_content import SiteContent, DEFAULT_CONTENT, init_default_content

# 创建蓝图
site_content_api_bp = Blueprint('site_content_api', __name__, url_prefix='/api/admin/content')


# ========== API 路由 ==========

@site_content_api_bp.route('', methods=['GET'])
@login_required
def get_all_content():
    """获取所有内容（按 section 分组）"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    try:
        grouped = SiteContent.get_all_grouped()
        return jsonify({'success': True, 'data': grouped})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取内容失败: {str(e)}'}), 500


@site_content_api_bp.route('/<section>', methods=['GET'])
@login_required
def get_section_content(section):
    """获取指定区域的所有内容"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    try:
        items = SiteContent.query.filter_by(section=section).order_by(SiteContent.sort_order).all()
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in items]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取内容失败: {str(e)}'}), 500


@site_content_api_bp.route('/<section>/<key>', methods=['PUT'])
@login_required
def update_single_content(section, key):
    """更新单条内容"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403

    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    try:
        item = SiteContent.query.filter_by(section=section, key=key).first()
        if not item:
            # 如果不存在则创建
            item = SiteContent(
                section=section,
                key=key,
                content=data['content'],
                content_type=data.get('content_type', 'text'),
                sort_order=data.get('sort_order', 0),
            )
            db.session.add(item)
        else:
            item.content = data['content']
            if 'content_type' in data:
                item.content_type = data['content_type']
            if 'is_active' in data:
                item.is_active = data['is_active']
            if 'sort_order' in data:
                item.sort_order = data['sort_order']

        item.updated_by = current_user.id
        item.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '内容已更新',
            'data': item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@site_content_api_bp.route('', methods=['POST'])
@login_required
def batch_update_content():
    """批量更新内容"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403

    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({'success': False, 'message': '无效的请求数据，期望数组格式'}), 400

    updated_count = 0
    errors = []

    try:
        for item_data in data:
            section = item_data.get('section')
            key = item_data.get('key')
            content = item_data.get('content')

            if not section or not key:
                errors.append(f'缺少 section 或 key: {item_data}')
                continue

            item = SiteContent.query.filter_by(section=section, key=key).first()
            if not item:
                item = SiteContent(
                    section=section,
                    key=key,
                    content=content or '',
                    content_type=item_data.get('content_type', 'text'),
                    sort_order=item_data.get('sort_order', 0),
                )
                db.session.add(item)
            else:
                if content is not None:
                    item.content = content
                if 'content_type' in item_data:
                    item.content_type = item_data['content_type']
                if 'is_active' in item_data:
                    item.is_active = item_data['is_active']
                if 'sort_order' in item_data:
                    item.sort_order = item_data['sort_order']

            item.updated_by = current_user.id
            item.updated_at = datetime.utcnow()
            updated_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'成功更新 {updated_count} 条内容',
            'updated_count': updated_count,
            'errors': errors
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'批量更新失败: {str(e)}'}), 500


@site_content_api_bp.route('/reset', methods=['POST'])
@login_required
def reset_to_default():
    """重置所有内容为默认值"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403

    try:
        # 删除所有现有内容
        SiteContent.query.delete()
        # 重新初始化默认内容
        for item in DEFAULT_CONTENT:
            content = SiteContent(
                section=item['section'],
                key=item['key'],
                content=item['content'],
                content_type=item.get('content_type', 'text'),
                sort_order=item.get('sort_order', 0),
            )
            db.session.add(content)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'已恢复 {len(DEFAULT_CONTENT)} 条默认内容'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'重置失败: {str(e)}'}), 500
