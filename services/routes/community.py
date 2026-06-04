# -*- coding: utf-8 -*-
"""
社区路由模块
"""
import json
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from db import db
from services.models.community import StrategyShare, Comment, Like


# 创建社区蓝图
community_bp = Blueprint('community', __name__)


class CommunityService:
    """社区服务类"""

    @staticmethod
    def get_strategies(page=1, per_page=12, sort_by='latest'):
        """获取策略分享列表"""
        query = StrategyShare.query
        
        # 排序
        if sort_by == 'latest':
            query = query.order_by(StrategyShare.created_at.desc())
        elif sort_by == 'popular':
            query = query.order_by(StrategyShare.likes_count.desc())
        elif sort_by == 'most_shared':
            query = query.order_by(StrategyShare.shares_count.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items, pagination.total

    @staticmethod
    def get_strategy_by_id(strategy_id):
        """根据ID获取策略"""
        return StrategyShare.query.get(strategy_id)

    @staticmethod
    def create_strategy(user_id, strategy_name, strategy_code, description='', parameters='{}'):
        """创建策略分享"""
        strategy = StrategyShare(
            user_id=user_id,
            strategy_name=strategy_name,
            strategy_code=strategy_code,
            description=description,
            parameters=parameters
        )
        db.session.add(strategy)
        db.session.commit()
        return strategy

    @staticmethod
    def like_strategy(user_id, strategy_id):
        """点赞策略"""
        strategy = StrategyShare.query.get(strategy_id)
        if not strategy:
            return False, '策略不存在'
        
        # 检查是否已点赞
        existing_like = Like.query.filter_by(
            user_id=user_id, 
            strategy_share_id=strategy_id
        ).first()
        
        if existing_like:
            # 取消点赞
            db.session.delete(existing_like)
            strategy.likes_count = max(0, strategy.likes_count - 1)
            db.session.commit()
            return True, '已取消点赞'
        
        # 添加点赞
        like = Like(user_id=user_id, strategy_share_id=strategy_id)
        db.session.add(like)
        strategy.likes_count += 1
        db.session.commit()
        return True, '点赞成功'

    @staticmethod
    def has_liked(user_id, strategy_id):
        """检查用户是否已点赞"""
        return Like.query.filter_by(
            user_id=user_id, 
            strategy_share_id=strategy_id
        ).first() is not None

    @staticmethod
    def add_comment(user_id, strategy_id, content):
        """添加评论"""
        strategy = StrategyShare.query.get(strategy_id)
        if not strategy:
            return None, '策略不存在'
        
        comment = Comment(
            user_id=user_id,
            strategy_share_id=strategy_id,
            content=content
        )
        db.session.add(comment)
        db.session.commit()
        return comment, '评论成功'

    @staticmethod
    def get_comments(strategy_id, page=1, per_page=20):
        """获取策略的评论列表"""
        strategy = StrategyShare.query.get(strategy_id)
        if not strategy:
            return [], 0
        
        pagination = Comment.query.filter_by(
            strategy_share_id=strategy_id
        ).order_by(Comment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return pagination.items, pagination.total


# ========== 页面路由 ==========

@community_bp.route('/community')
def community_index():
    """社区首页"""
    return render_template('community/index.html')


@community_bp.route('/community/strategies/<int:strategy_id>')
def strategy_detail(strategy_id):
    """策略详情页"""
    return render_template('community/detail.html', strategy_id=strategy_id)


@community_bp.route('/community/create')
@login_required
def create_strategy():
    """发布策略页面"""
    return render_template('community/create.html')


# ========== API路由 ==========

@community_bp.route('/api/community/strategies', methods=['GET'])
def get_strategies():
    """获取策略分享列表API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    sort_by = request.args.get('sort_by', 'latest')
    
    # 验证排序参数
    if sort_by not in ['latest', 'popular', 'most_shared']:
        sort_by = 'latest'
    
    try:
        strategies, total = CommunityService.get_strategies(
            page=page, 
            per_page=per_page, 
            sort_by=sort_by
        )
        
        pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        # 如果用户已登录，标记已点赞的策略
        liked_strategy_ids = set()
        if current_user.is_authenticated:
            for s in strategies:
                if CommunityService.has_liked(current_user.id, s.id):
                    liked_strategy_ids.add(s.id)
        
        return jsonify({
            'success': True,
            'strategies': [s.to_dict() for s in strategies],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages,
            'liked_strategy_ids': list(liked_strategy_ids)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@community_bp.route('/api/community/strategies', methods=['POST'])
@login_required
def create_strategy_api():
    """发布策略分享API"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400
    
    strategy_name = data.get('strategy_name', '').strip()
    strategy_code = data.get('strategy_code', '').strip()
    description = data.get('description', '').strip()
    parameters = data.get('parameters', '{}')
    
    if not strategy_name:
        return jsonify({'success': False, 'message': '策略名称不能为空'}), 400
    
    if not strategy_code:
        return jsonify({'success': False, 'message': '策略代码不能为空'}), 400
    
    try:
        strategy = CommunityService.create_strategy(
            user_id=current_user.id,
            strategy_name=strategy_name,
            strategy_code=strategy_code,
            description=description,
            parameters=json.dumps(parameters) if isinstance(parameters, dict) else parameters
        )
        return jsonify({
            'success': True,
            'message': '发布成功',
            'strategy': strategy.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'发布失败: {str(e)}'}), 500


@community_bp.route('/api/community/strategies/<int:strategy_id>', methods=['GET'])
def get_strategy(strategy_id):
    """获取策略详情API"""
    try:
        strategy = CommunityService.get_strategy_by_id(strategy_id)
        if not strategy:
            return jsonify({'success': False, 'message': '策略不存在'}), 404
        
        # 检查是否已点赞
        has_liked = False
        if current_user.is_authenticated:
            has_liked = CommunityService.has_liked(current_user.id, strategy_id)
        
        result = strategy.to_dict()
        result['has_liked'] = has_liked
        
        return jsonify({
            'success': True,
            'strategy': result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@community_bp.route('/api/community/strategies/<int:strategy_id>/like', methods=['POST'])
@login_required
def like_strategy_api(strategy_id):
    """点赞API"""
    try:
        success, message = CommunityService.like_strategy(current_user.id, strategy_id)
        
        if success:
            strategy = StrategyShare.query.get(strategy_id)
            return jsonify({
                'success': True,
                'message': message,
                'likes_count': strategy.likes_count if strategy else 0
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500


@community_bp.route('/api/community/strategies/<int:strategy_id>/comment', methods=['POST'])
@login_required
def add_comment_api(strategy_id):
    """添加评论API"""
    data = request.get_json()
    
    if not data or not data.get('content', '').strip():
        return jsonify({'success': False, 'message': '评论内容不能为空'}), 400
    
    try:
        comment, message = CommunityService.add_comment(
            user_id=current_user.id,
            strategy_id=strategy_id,
            content=data['content'].strip()
        )
        
        if comment:
            return jsonify({
                'success': True,
                'message': message,
                'comment': comment.to_dict()
            })
        else:
            return jsonify({'success': False, 'message': message}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'评论失败: {str(e)}'}), 500


@community_bp.route('/api/community/strategies/<int:strategy_id>/comments', methods=['GET'])
def get_comments_api(strategy_id):
    """获取评论列表API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    try:
        comments, total = CommunityService.get_comments(
            strategy_id=strategy_id,
            page=page,
            per_page=per_page
        )
        
        pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return jsonify({
            'success': True,
            'comments': [c.to_dict() for c in comments],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500
