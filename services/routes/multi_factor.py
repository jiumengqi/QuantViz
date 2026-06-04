# -*- coding: utf-8 -*-
"""
多因子分析路由

提供多因子分析的API接口和页面路由
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from services.models.portfolio.multi_factor import (
    FactorAnalysis, ValuationFactor, GrowthFactor, QualityFactor, TechnicalFactor,
    create_default_factors, generate_sample_data, generate_sample_returns
)
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 创建多因子分析蓝图
multi_factor_bp = Blueprint('multi_factor', __name__)


@multi_factor_bp.route('/')
@login_required
def multi_factor_index():
    """多因子分析首页"""
    today = datetime.now().strftime("%Y-%m-%d")
    default_start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    return render_template(
        'analysis/multi_factor.html',
        today=today,
        default_start=default_start
    )


@multi_factor_bp.route('/factors/list')
@login_required
def get_factors_list():
    """获取可用因子列表"""
    try:
        factors = [
            {
                'id': 'pe',
                'name': 'PE估值因子',
                'category': 'valuation',
                'description': '市盈率因子，衡量股价与每股收益的比值，负值表示低估值',
                'default_weight': 0.2
            },
            {
                'id': 'pb',
                'name': 'PB估值因子',
                'category': 'valuation',
                'description': '市净率因子，衡量股价与每股净资产的比值，负值表示低估值',
                'default_weight': 0.1
            },
            {
                'id': 'ps',
                'name': 'PS估值因子',
                'category': 'valuation',
                'description': '市销率因子，衡量股价与每股销售额的比值，负值表示低估值',
                'default_weight': 0.1
            },
            {
                'id': 'revenue_growth',
                'name': '营收增长因子',
                'category': 'growth',
                'description': '营业收入同比增长率，衡量企业营收成长能力',
                'default_weight': 0.15
            },
            {
                'id': 'profit_growth',
                'name': '利润增长因子',
                'category': 'growth',
                'description': '净利润同比增长率，衡量企业盈利成长能力',
                'default_weight': 0.15
            },
            {
                'id': 'roe',
                'name': 'ROE质量因子',
                'category': 'quality',
                'description': '净资产收益率，衡量股东权益的收益水平',
                'default_weight': 0.15
            },
            {
                'id': 'gross_margin',
                'name': '毛利率因子',
                'category': 'quality',
                'description': '销售毛利率，衡量企业盈利能力和定价权',
                'default_weight': 0.05
            },
            {
                'id': 'momentum',
                'name': '动量因子',
                'category': 'technical',
                'description': '股票过去一段时间的涨跌趋势，正值表示强势',
                'default_weight': 0.05
            },
            {
                'id': 'volatility',
                'name': '波动率因子',
                'category': 'technical',
                'description': '价格波动剧烈程度，负值表示低波动（偏好）',
                'default_weight': 0.05
            }
        ]
        
        # 按类别分组
        categories = {
            'valuation': {'name': '估值因子', 'factors': []},
            'growth': {'name': '成长因子', 'factors': []},
            'quality': {'name': '质量因子', 'factors': []},
            'technical': {'name': '技术因子', 'factors': []}
        }
        
        for factor in factors:
            cat = factor['category']
            if cat in categories:
                categories[cat]['factors'].append(factor)
        
        return jsonify({
            'success': True,
            'factors': factors,
            'categories': categories
        })
        
    except Exception as e:
        logger.error(f"获取因子列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@multi_factor_bp.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """
    执行多因子分析
    
    请求参数:
        selected_factors: List[str] - 选中的因子ID列表
        weights: Dict[str, float] - 因子权重
        stock_pool: List[str] - 股票代码列表
        use_orthogonalization: bool - 是否进行正交化处理
    """
    try:
        data = request.json
        
        selected_factor_ids = data.get('selected_factors', [])
        weights = data.get('weights', {})
        stock_pool = data.get('stock_pool', [])
        use_orthogonalization = data.get('use_orthogonalization', False)
        n_top = data.get('n_top', 50)
        
        if not selected_factor_ids:
            return jsonify({'success': False, 'error': '请至少选择一个因子'}), 400
        
        if not stock_pool:
            # 使用默认股票池
            from config import HOT_STOCKS
            hot_codes = [s['code'] for s in HOT_STOCKS]
            stock_pool = hot_codes + [
                '600276.SH', '002594.SZ', '600030.SH', '300750.SZ', '688981.SH',
                '600009.SH', '600028.SH', '601166.SH', '601398.SH', '601288.SH',
                '600031.SH', '600585.SH', '600887.SH', '600690.SH', '601012.SH'
            ]
        
        # 创建因子分析器
        analyzer = FactorAnalysis()
        
        # 添加选中的因子
        factor_map = {
            'pe': ValuationFactor('PE'),
            'pb': ValuationFactor('PB'),
            'ps': ValuationFactor('PS'),
            'revenue_growth': GrowthFactor('revenue'),
            'profit_growth': GrowthFactor('profit'),
            'roe': QualityFactor('ROE'),
            'gross_margin': QualityFactor('MARGIN'),
            'momentum': TechnicalFactor('momentum'),
            'volatility': TechnicalFactor('volatility')
        }
        
        for factor_id in selected_factor_ids:
            if factor_id in factor_map:
                weight = weights.get(factor_id, 0.1)
                analyzer.add_factor(factor_map[factor_id], weight=weight)
        
        # 生成模拟数据
        stock_data = generate_sample_data(stock_pool)
        returns_data = generate_sample_returns(stock_pool)
        
        # 计算IC/IR
        ic_ir_results = []
        for factor in analyzer.factors:
            factor_values = []
            stock_returns = []
            
            for stock_code in stock_pool:
                if stock_code in stock_data and stock_code in returns_data:
                    value = factor.calculate(stock_data[stock_code])
                    factor_values.append(value)
                    stock_returns.append(returns_data[stock_code])
            
            if len(factor_values) > 2:
                ic = np.corrcoef(factor_values, stock_returns)[0, 1]
                ic = float(ic) if not np.isnan(ic) else 0
            else:
                ic = 0
            
            ic_ir_results.append({
                'factor_name': factor.name,
                'category': factor.category,
                'ic': ic,
                'ic_abs': abs(ic),
                'ir': ic * 2 if ic != 0 else 0  # 简化IR计算
            })
        
        # 对因子进行正交化（如果需要）
        if use_orthogonalization and len(analyzer.factors) > 1:
            factors_df = pd.DataFrame([
                {factor.name: factor.calculate(stock_data[sc]) for factor in analyzer.factors}
                for sc in stock_pool if sc in stock_data
            ], index=stock_pool[:len(stock_data)])
            
            for factor in analyzer.factors:
                if factor.category != 'valuation':  # 主要对非估值因子正交化
                    orthogonalized = analyzer.orthogonalize(factors_df, factor.name)
                    # 更新因子值
                    for i, sc in enumerate(stock_pool[:len(factors_df)]):
                        if sc in stock_data:
                            pass  # 实际应该更新stock_data
        
        # 获取排名
        ranking_df = analyzer.rank_stocks(stock_data, stock_pool, n=n_top)
        
        ranking_list = []
        if not ranking_df.empty:
            for _, row in ranking_df.iterrows():
                ranking_list.append({
                    'rank': int(row['rank']),
                    'stock_code': row['stock_code'],
                    'stock_name': row['stock_name'],
                    'composite_score': float(row['composite_score'])
                })
        
        # 计算平均IC
        avg_ic = np.mean([r['ic'] for r in ic_ir_results]) if ic_ir_results else 0
        avg_ic_abs = np.mean([r['ic_abs'] for r in ic_ir_results]) if ic_ir_results else 0
        
        return jsonify({
            'success': True,
            'analysis_result': {
                'factor_validity': {
                    'factors': ic_ir_results,
                    'avg_ic': float(avg_ic),
                    'avg_ic_abs': float(avg_ic_abs),
                    'validity_level': '高' if avg_ic_abs > 0.05 else ('中' if avg_ic_abs > 0.02 else '低')
                },
                'ranking': ranking_list,
                'total_stocks': len(stock_pool),
                'selected_count': len(ranking_list)
            }
        })
        
    except Exception as e:
        logger.error(f"多因子分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@multi_factor_bp.route('/validity', methods=['POST'])
@login_required
def get_factor_validity():
    """
    获取因子有效性指标
    
    请求参数:
        stock_data: Dict[str, Dict] - 股票因子数据
        returns_data: Dict[str, float] - 股票收益率
    """
    try:
        data = request.json
        stock_data = data.get('stock_data', {})
        returns_data = data.get('returns_data', {})
        
        if not stock_data or not returns_data:
            return jsonify({'success': False, 'error': '缺少股票数据或收益率数据'}), 400
        
        # 创建默认因子分析器
        analyzer = create_default_factors()
        
        # 生成有效性报告
        report = analyzer.get_factor_validity_report(stock_data, returns_data)
        
        return jsonify({
            'success': True,
            'validity_report': report
        })
        
    except Exception as e:
        logger.error(f"获取因子有效性失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@multi_factor_bp.route('/rank', methods=['POST'])
@login_required
def get_stock_ranking():
    """
    生成股票排名
    
    请求参数:
        selected_factors: List[str] - 选中的因子
        weights: Dict[str, float] - 因子权重
        stock_pool: List[str] - 股票池
        n_top: int - 返回前n名
    """
    try:
        data = request.json
        
        selected_factor_ids = data.get('selected_factors', [])
        weights = data.get('weights', {})
        stock_pool = data.get('stock_pool', [])
        n_top = data.get('n_top', 50)
        
        if not selected_factor_ids:
            return jsonify({'success': False, 'error': '请至少选择一个因子'}), 400
        
        # 创建因子分析器
        analyzer = FactorAnalysis()
        
        factor_map = {
            'pe': ValuationFactor('PE'),
            'pb': ValuationFactor('PB'),
            'ps': ValuationFactor('PS'),
            'revenue_growth': GrowthFactor('revenue'),
            'profit_growth': GrowthFactor('profit'),
            'roe': QualityFactor('ROE'),
            'gross_margin': QualityFactor('MARGIN'),
            'momentum': TechnicalFactor('momentum'),
            'volatility': TechnicalFactor('volatility')
        }
        
        for factor_id in selected_factor_ids:
            if factor_id in factor_map:
                weight = weights.get(factor_id, 0.1)
                analyzer.add_factor(factor_map[factor_id], weight=weight)
        
        # 生成模拟数据
        if not stock_pool:
            from config import HOT_STOCKS
            hot_codes = [s['code'] for s in HOT_STOCKS]
            stock_pool = hot_codes + [
                '600276.SH', '002594.SZ', '600030.SH', '300750.SZ', '688981.SH'
            ]
        
        stock_data = generate_sample_data(stock_pool)
        
        # 获取排名
        ranking_df = analyzer.rank_stocks(stock_data, stock_pool, n=n_top)
        
        ranking_list = []
        if not ranking_df.empty:
            for _, row in ranking_df.iterrows():
                ranking_list.append({
                    'rank': int(row['rank']),
                    'stock_code': row['stock_code'],
                    'stock_name': row['stock_name'],
                    'composite_score': float(row['composite_score'])
                })
        
        return jsonify({
            'success': True,
            'ranking': ranking_list
        })
        
    except Exception as e:
        logger.error(f"获取股票排名失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@multi_factor_bp.route('/export', methods=['POST'])
@login_required
def export_results():
    """
    导出分析结果
    
    请求参数:
        ranking: List[Dict] - 排名数据
        format: str - 导出格式 (csv, excel)
    """
    try:
        data = request.json
        ranking = data.get('ranking', [])
        format_type = data.get('format', 'csv')
        
        if not ranking:
            return jsonify({'success': False, 'error': '没有可导出的数据'}), 400
        
        if format_type == 'csv':
            # 生成CSV内容
            csv_lines = ['排名,股票代码,股票名称,综合得分']
            for item in ranking:
                csv_lines.append(
                    f"{item['rank']},{item['stock_code']},{item['stock_name']},{item['composite_score']:.4f}"
                )
            csv_content = '\n'.join(csv_lines)
            
            return jsonify({
                'success': True,
                'format': 'csv',
                'content': csv_content,
                'filename': f'multi_factor_ranking_{datetime.now().strftime("%Y%m%d")}.csv'
            })
        else:
            return jsonify({'success': False, 'error': '不支持的导出格式'}), 400
        
    except Exception as e:
        logger.error(f"导出结果失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@multi_factor_bp.route('/sample-data', methods=['GET'])
@login_required
def get_sample_data():
    """获取示例股票数据"""
    try:
        from config import HOT_STOCKS
        hot_codes = [s['code'] for s in HOT_STOCKS]
        stock_pool = hot_codes + [
            '600276.SH', '002594.SZ', '600030.SH', '300750.SZ', '688981.SH',
            '600009.SH', '600028.SH', '601166.SH', '601398.SH', '601288.SH',
            '600031.SH', '600585.SH', '600887.SH', '600690.SH', '601012.SH'
        ]
        
        stock_data = generate_sample_data(stock_pool)
        returns_data = generate_sample_returns(stock_pool)
        
        return jsonify({
            'success': True,
            'stock_data': stock_data,
            'returns_data': returns_data
        })
        
    except Exception as e:
        logger.error(f"获取示例数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
