# -*- coding: utf-8 -*-
"""
反馈路由模块
"""
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from db import db
from services.models.feedback import Feedback


# 创建反馈蓝图
feedback_bp = Blueprint('feedback', __name__)


class FeedbackService:
    """反馈服务类"""

    @staticmethod
    def create_feedback(user_id, feedback_type, title, content):
        """创建反馈"""
        feedback = Feedback(
            user_id=user_id,
            type=feedback_type,
            title=title,
            content=content,
            status='pending'
        )
        db.session.add(feedback)
        db.session.commit()
        return feedback

    @staticmethod
    def get_user_feedbacks(user_id, page=1, per_page=10):
        """获取用户的反馈列表"""
        pagination = Feedback.query.filter_by(user_id=user_id).order_by(
            Feedback.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items, pagination.total

    @staticmethod
    def get_all_feedbacks(page=1, per_page=10, status=None, feedback_type=None):
        """获取所有反馈（管理员）"""
        query = Feedback.query
        if status:
            query = query.filter_by(status=status)
        if feedback_type:
            query = query.filter_by(type=feedback_type)
        pagination = query.order_by(Feedback.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return pagination.items, pagination.total

    @staticmethod
    def get_feedback_by_id(feedback_id):
        """根据ID获取反馈"""
        return Feedback.query.get(feedback_id)

    @staticmethod
    def reply_feedback(feedback_id, admin_reply):
        """回复反馈"""
        feedback = Feedback.query.get(feedback_id)
        if feedback:
            feedback.admin_reply = admin_reply
            if feedback.status == 'pending':
                feedback.status = 'processing'
            feedback.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def update_status(feedback_id, status):
        """更新反馈状态"""
        feedback = Feedback.query.get(feedback_id)
        if feedback and status in ['pending', 'processing', 'resolved', 'rejected']:
            feedback.status = status
            feedback.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def delete_feedback(feedback_id):
        """删除反馈"""
        feedback = Feedback.query.get(feedback_id)
        if feedback:
            db.session.delete(feedback)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_feedback_stats():
        """获取反馈统计数据"""
        total = Feedback.query.count()
        pending = Feedback.query.filter_by(status='pending').count()
        processing = Feedback.query.filter_by(status='processing').count()
        resolved = Feedback.query.filter_by(status='resolved').count()
        rejected = Feedback.query.filter_by(status='rejected').count()
        return {
            'total': total,
            'pending': pending,
            'processing': processing,
            'resolved': resolved,
            'rejected': rejected
        }


# ========== 路由定义 ==========

@feedback_bp.route('/feedback/submit')
@login_required
def submit_feedback():
    """提交反馈页面"""
    return render_template('feedback/submit.html')


@feedback_bp.route('/feedback/my')
@login_required
def my_feedback():
    """我的反馈页面"""
    return render_template('feedback/my_feedback.html')


@feedback_bp.route('/feedback/manage')
@login_required
def manage_feedback():
    """管理员反馈管理页面"""
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    return render_template('feedback/manage.html')


@feedback_bp.route('/api/feedbacks', methods=['POST'])
@login_required
def create_feedback():
    """创建反馈API"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400
    
    feedback_type = data.get('type', 'bug')
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not title or not content:
        return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400
    
    if feedback_type not in ['bug', 'suggestion', 'feature']:
        feedback_type = 'bug'
    
    try:
        feedback = FeedbackService.create_feedback(
            user_id=current_user.id,
            feedback_type=feedback_type,
            title=title,
            content=content
        )
        return jsonify({
            'success': True,
            'message': '反馈提交成功',
            'feedback': feedback.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'提交失败: {str(e)}'}), 500


@feedback_bp.route('/api/feedbacks')
@login_required
def get_user_feedbacks():
    """获取用户自己的反馈列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        feedbacks, total = FeedbackService.get_user_feedbacks(
            user_id=current_user.id,
            page=page,
            per_page=per_page
        )
        
        # 计算总页数
        pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return jsonify({
            'success': True,
            'feedbacks': [f.to_dict() for f in feedbacks],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@feedback_bp.route('/api/feedbacks/all')
@login_required
def get_all_feedbacks():
    """获取所有反馈（管理员）"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', None)
    feedback_type = request.args.get('type', None)
    
    try:
        feedbacks, total = FeedbackService.get_all_feedbacks(
            page=page,
            per_page=per_page,
            status=status,
            feedback_type=feedback_type
        )
        
        pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return jsonify({
            'success': True,
            'feedbacks': [f.to_dict() for f in feedbacks],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@feedback_bp.route('/api/feedbacks/stats')
@login_required
def get_feedback_stats():
    """获取反馈统计数据（管理员）"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    try:
        stats = FeedbackService.get_feedback_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@feedback_bp.route('/api/feedbacks/<int:feedback_id>/reply', methods=['POST'])
@login_required
def reply_feedback(feedback_id):
    """回复反馈（管理员）"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    data = request.get_json()
    if not data or not data.get('admin_reply', '').strip():
        return jsonify({'success': False, 'message': '回复内容不能为空'}), 400
    
    try:
        success = FeedbackService.reply_feedback(feedback_id, data['admin_reply'].strip())
        if success:
            return jsonify({'success': True, 'message': '回复成功'})
        else:
            return jsonify({'success': False, 'message': '反馈不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'回复失败: {str(e)}'}), 500


@feedback_bp.route('/api/feedbacks/<int:feedback_id>/status', methods=['PUT'])
@login_required
def update_feedback_status(feedback_id):
    """更新反馈状态（管理员）"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    data = request.get_json()
    if not data or not data.get('status'):
        return jsonify({'success': False, 'message': '状态不能为空'}), 400
    
    status = data.get('status')
    if status not in ['pending', 'processing', 'resolved', 'rejected']:
        return jsonify({'success': False, 'message': '无效的状态值'}), 400
    
    try:
        success = FeedbackService.update_status(feedback_id, status)
        if success:
            return jsonify({'success': True, 'message': '状态更新成功'})
        else:
            return jsonify({'success': False, 'message': '反馈不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500
