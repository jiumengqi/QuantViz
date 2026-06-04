# -*- coding: utf-8 -*-
"""
知识库路由
提供知识库相关的页面和API接口
"""

from flask import Blueprint, render_template, request, jsonify, current_app
import services.knowledge_base as kb

# 创建知识库蓝图
knowledge_bp = Blueprint('knowledge', __name__)


@knowledge_bp.route('/')
def knowledge_index():
    """知识库首页"""
    tutorials = kb.get_tutorials_list()
    indicators = kb.get_indicators_list()
    strategies = kb.get_strategies_list()
    
    return render_template(
        'knowledge/index.html',
        tutorials=tutorials,
        indicators=indicators,
        strategies=strategies
    )


@knowledge_bp.route('/tutorials')
def tutorials():
    """教程列表页面"""
    tutorials = kb.get_tutorials_list()
    return render_template('knowledge/tutorials.html', tutorials=tutorials)


@knowledge_bp.route('/tutorials/<string:tutorial_id>')
def tutorial_detail(tutorial_id):
    """教程详情页面"""
    tutorial = kb.get_tutorial(tutorial_id)
    if not tutorial:
        return render_template('errors/404.html'), 404
    
    tutorials = kb.get_tutorials_list()
    return render_template(
        'knowledge/tutorials.html',
        tutorial=tutorial,
        tutorials=tutorials
    )


@knowledge_bp.route('/indicators')
def indicators():
    """指标解释页面"""
    indicators = kb.get_indicators_list()
    return render_template('knowledge/indicators.html', indicators=indicators)


@knowledge_bp.route('/indicators/<string:indicator_id>')
def indicator_detail(indicator_id):
    """指标详情页面"""
    indicator = kb.get_indicator(indicator_id)
    if not indicator:
        return render_template('errors/404.html'), 404
    
    indicators = kb.get_indicators_list()
    return render_template(
        'knowledge/indicators.html',
        indicator=indicator,
        indicators=indicators
    )


@knowledge_bp.route('/strategies')
def strategies():
    """策略原理页面"""
    strategies = kb.get_strategies_list()
    return render_template('knowledge/strategies.html', strategies=strategies)


@knowledge_bp.route('/strategies/<string:strategy_id>')
def strategy_detail(strategy_id):
    """策略详情页面"""
    strategy = kb.get_strategy(strategy_id)
    if not strategy:
        return render_template('errors/404.html'), 404
    
    strategies = kb.get_strategies_list()
    return render_template(
        'knowledge/strategies.html',
        strategy=strategy,
        strategies=strategies
    )


@knowledge_bp.route('/risk-warning')
def risk_warning():
    """风险提示页面"""
    warnings = kb.get_risk_warnings()
    return render_template('knowledge/risk_warning.html', warnings=warnings)


@knowledge_bp.route('/faq')
def faq():
    """常见问题页面"""
    faq_data = kb.get_faq()
    return render_template('knowledge/faq.html', faq_data=faq_data)


# API接口

@knowledge_bp.route('/api/tutorials')
def api_tutorials():
    """获取教程列表API"""
    try:
        tutorials = kb.get_tutorials_list()
        return jsonify({
            'success': True,
            'data': tutorials
        })
    except Exception as e:
        current_app.logger.error(f"获取教程列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@knowledge_bp.route('/api/tutorials/<string:tutorial_id>')
def api_tutorial_detail(tutorial_id):
    """获取教程详情API"""
    try:
        tutorial = kb.get_tutorial(tutorial_id)
        if not tutorial:
            return jsonify({'success': False, 'error': '教程不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': tutorial
        })
    except Exception as e:
        current_app.logger.error(f"获取教程详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@knowledge_bp.route('/api/indicators')
def api_indicators():
    """获取指标列表API"""
    try:
        indicators = kb.get_indicators_list()
        return jsonify({
            'success': True,
            'data': indicators
        })
    except Exception as e:
        current_app.logger.error(f"获取指标列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@knowledge_bp.route('/api/indicators/<string:indicator_id>')
def api_indicator_detail(indicator_id):
    """获取指标详情API"""
    try:
        indicator = kb.get_indicator(indicator_id)
        if not indicator:
            return jsonify({'success': False, 'error': '指标不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': indicator
        })
    except Exception as e:
        current_app.logger.error(f"获取指标详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@knowledge_bp.route('/api/strategies')
def api_strategies():
    """获取策略列表API"""
    try:
        strategies = kb.get_strategies_list()
        return jsonify({
            'success': True,
            'data': strategies
        })
    except Exception as e:
        current_app.logger.error(f"获取策略列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@knowledge_bp.route('/api/strategies/<string:strategy_id>')
def api_strategy_detail(strategy_id):
    """获取策略详情API"""
    try:
        strategy = kb.get_strategy(strategy_id)
        if not strategy:
            return jsonify({'success': False, 'error': '策略不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': strategy
        })
    except Exception as e:
        current_app.logger.error(f"获取策略详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@knowledge_bp.route('/api/faq')
def api_faq():
    """获取FAQ API"""
    try:
        faq_data = kb.get_faq()
        return jsonify({
            'success': True,
            'data': faq_data
        })
    except Exception as e:
        current_app.logger.error(f"获取FAQ失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@knowledge_bp.route('/api/risk-warnings')
def api_risk_warnings():
    """获取风险提示API"""
    try:
        warnings = kb.get_risk_warnings()
        return jsonify({
            'success': True,
            'data': warnings
        })
    except Exception as e:
        current_app.logger.error(f"获取风险提示失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
