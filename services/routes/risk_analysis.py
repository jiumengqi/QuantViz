from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from typing import Dict, Any, List, Optional
from services.models.risk.risk_manager import (
    RiskManager, PositionConfig, StopLossConfig, TakeProfitConfig,
    RiskConstraints, IndustryConstraint, Position,
    PositionSizingMethod, StopLossType, TakeProfitType,
    calculate_kelly_formula, calculate_portfolio_volatility, calculate_portfolio_var
)
from services.models.risk.value_at_risk import (
    calculate_var, calculate_cvar, calculate_downside_risk,
    calculate_sortino_ratio, calculate_max_drawdown
)
from db import db
import logging
import numpy as np

# 创建日志记录器
logger = logging.getLogger(__name__)

# 创建风险分析蓝图
risk_analysis_bp = Blueprint('risk_analysis', __name__)


@risk_analysis_bp.route('/')
@login_required
def risk_management_page():
    """风险管理页面"""
    return render_template('portfolio/risk_management.html')


@risk_analysis_bp.route('/api/position-size', methods=['POST'])
@login_required
def calculate_position_size_api():
    """仓位计算接口"""
    try:
        data = request.json
        portfolio_value = float(data.get('portfolio_value', 1000000))
        symbol = data.get('symbol', '')
        price = float(data.get('price', 0))
        expected_return = float(data.get('expected_return', 0))
        volatility = float(data.get('volatility', 0))
        win_rate = float(data.get('win_rate', 0.5))
        avg_win = float(data.get('avg_win', 0))
        avg_loss = float(data.get('avg_loss', 0))

        # 获取仓位配置方法
        method_str = data.get('method', 'fixed')
        try:
            method = PositionSizingMethod(method_str)
        except ValueError:
            method = PositionSizingMethod.FIXED

        # 创建仓位配置
        position_config = PositionConfig(
            method=method,
            fixed_ratio=float(data.get('fixed_ratio', 0.1)),
            kelly_multiplier=float(data.get('kelly_multiplier', 0.5)),
            max_position_size=float(data.get('max_position_size', 0.2)),
            max_positions=int(data.get('max_positions', 10))
        )

        # 创建风险管理器
        risk_manager = RiskManager(
            portfolio_value=portfolio_value,
            position_config=position_config
        )

        # 计算仓位
        result = risk_manager.calculate_position_size(
            symbol=symbol,
            price=price,
            expected_return=expected_return,
            volatility=volatility,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss
        )

        # 计算凯利公式（如果适用）
        kelly_ratio = 0
        if method == PositionSizingMethod.KELLY and avg_loss > 0:
            kelly_ratio = calculate_kelly_formula(win_rate, avg_win, avg_loss)

        return jsonify({
            'success': True,
            'position_size': {
                'symbol': result['symbol'],
                'ratio': result['ratio'],
                'ratio_percent': result['ratio'] * 100,
                'allocated_amount': result['allocated_amount'],
                'quantity': result['quantity'],
                'method': result['method']
            },
            'kelly_ratio': kelly_ratio,
            'kelly_ratio_percent': kelly_ratio * 100
        })

    except Exception as e:
        logger.error(f"仓位计算失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@risk_analysis_bp.route('/api/stop-loss-check', methods=['POST'])
@login_required
def check_stop_loss_api():
    """止损触发检查接口"""
    try:
        data = request.json
        symbol = data.get('symbol', '')
        avg_cost = float(data.get('avg_cost', 0))
        current_price = float(data.get('current_price', 0))
        quantity = float(data.get('quantity', 0))

        # 止损配置
        stop_loss_enabled = data.get('stop_loss_enabled', True)
        stop_loss_type = data.get('stop_loss_type', 'fixed')
        fixed_stop_ratio = float(data.get('fixed_stop_loss_ratio', 0.05))
        trailing_stop_ratio = float(data.get('trailing_stop_ratio', 0.10))

        # 创建持仓
        position = Position(
            symbol=symbol,
            name=data.get('name', ''),
            quantity=quantity,
            avg_cost=avg_cost,
            current_price=current_price,
            industry=data.get('industry', 'unknown')
        )

        # 创建止损配置
        stop_loss_config = StopLossConfig(
            enabled=stop_loss_enabled,
            stop_loss_type=StopLossType(stop_loss_type) if stop_loss_type else StopLossType.FIXED,
            fixed_stop_loss_ratio=fixed_stop_ratio,
            trailing_stop_ratio=trailing_stop_ratio
        )

        # 创建风险管理器
        risk_manager = RiskManager(
            portfolio_value=quantity * current_price,
            stop_loss_config=stop_loss_config
        )
        risk_manager.add_position(position)

        # 检查止损
        triggered, stop_info = risk_manager.check_stop_loss(symbol)

        return jsonify({
            'success': True,
            'stop_loss_triggered': triggered,
            'stop_loss_info': stop_info,
            'current_loss_ratio': (current_price - avg_cost) / avg_cost if avg_cost > 0 else 0,
            'current_loss_amount': (current_price - avg_cost) * quantity
        })

    except Exception as e:
        logger.error(f"止损检查失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@risk_analysis_bp.route('/api/take-profit-check', methods=['POST'])
@login_required
def check_take_profit_api():
    """止盈触发检查接口"""
    try:
        data = request.json
        symbol = data.get('symbol', '')
        avg_cost = float(data.get('avg_cost', 0))
        current_price = float(data.get('current_price', 0))
        quantity = float(data.get('quantity', 0))

        # 止盈配置
        take_profit_enabled = data.get('take_profit_enabled', True)
        take_profit_type = data.get('take_profit_type', 'fixed')
        fixed_take_profit_ratio = float(data.get('fixed_take_profit_ratio', 0.15))
        target_price = data.get('target_price', None)
        trailing_callback = float(data.get('trailing_callback', 0.03))

        # 创建持仓
        position = Position(
            symbol=symbol,
            name=data.get('name', ''),
            quantity=quantity,
            avg_cost=avg_cost,
            current_price=current_price,
            industry=data.get('industry', 'unknown')
        )

        # 创建止盈配置
        take_profit_config = TakeProfitConfig(
            enabled=take_profit_enabled,
            take_profit_type=TakeProfitType(take_profit_type) if take_profit_type else TakeProfitType.FIXED,
            fixed_take_profit_ratio=fixed_take_profit_ratio,
            target_price=float(target_price) if target_price else None,
            trailing_callback=trailing_callback
        )

        # 创建风险管理器
        risk_manager = RiskManager(
            portfolio_value=quantity * current_price,
            take_profit_config=take_profit_config
        )
        risk_manager.add_position(position)

        # 检查止盈
        triggered, profit_info = risk_manager.check_take_profit(symbol)

        return jsonify({
            'success': True,
            'take_profit_triggered': triggered,
            'take_profit_info': profit_info,
            'current_profit_ratio': (current_price - avg_cost) / avg_cost if avg_cost > 0 else 0,
            'current_profit_amount': (current_price - avg_cost) * quantity
        })

    except Exception as e:
        logger.error(f"止盈检查失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@risk_analysis_bp.route('/api/risk-metrics', methods=['POST'])
@login_required
def calculate_risk_metrics_api():
    """风险指标计算接口"""
    try:
        data = request.json
        returns = data.get('returns', [])
        portfolio_value = float(data.get('portfolio_value', 1000000))

        # 如果没有提供收益率数据，生成模拟数据
        if not returns or len(returns) == 0:
            returns = np.random.normal(0.0005, 0.02, 30).tolist()

        returns_array = np.array(returns)

        # 计算风险指标
        risk_manager = RiskManager(portfolio_value=portfolio_value)
        metrics = risk_manager.calculate_risk_metrics(returns_array, portfolio_value)

        return jsonify({
            'success': True,
            'risk_metrics': {
                'var_95': metrics['var_95'],
                'var_99': metrics['var_99'],
                'cvar_95': metrics['cvar_95'],
                'cvar_99': metrics['cvar_99'],
                'downside_risk': metrics['downside_risk'],
                'sortino_ratio': metrics['sortino_ratio'],
                'max_drawdown': metrics['max_drawdown'],
                'kurtosis': metrics['kurtosis'],
                'skewness': metrics['skewness'],
                'volatility': metrics['volatility'],
                'average_return': metrics['average_return'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'var_95_amount': metrics['var_95_amount'],
                'var_99_amount': metrics['var_99_amount']
            },
            'interpretation': _get_risk_interpretation(metrics)
        })

    except Exception as e:
        logger.error(f"风险指标计算失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _get_risk_interpretation(metrics: Dict) -> Dict:
    """获取风险指标解释"""
    interpretation = {}

    # VaR解释
    var_95 = metrics['var_95']
    if var_95 < 0.02:
        interpretation['var_95'] = '低风险'
    elif var_95 < 0.05:
        interpretation['var_95'] = '中等风险'
    else:
        interpretation['var_95'] = '高风险'

    # 波动率解释
    vol = metrics['volatility']
    if vol < 0.10:
        interpretation['volatility'] = '低波动'
    elif vol < 0.20:
        interpretation['volatility'] = '中等波动'
    else:
        interpretation['volatility'] = '高波动'

    # 夏普比率解释
    sharpe = metrics['sharpe_ratio']
    if sharpe < 0.5:
        interpretation['sharpe_ratio'] = '较差'
    elif sharpe < 1.0:
        interpretation['sharpe_ratio'] = '一般'
    elif sharpe < 2.0:
        interpretation['sharpe_ratio'] = '良好'
    else:
        interpretation['sharpe_ratio'] = '优秀'

    # 最大回撤解释
    max_dd = abs(metrics['max_drawdown'])
    if max_dd < 0.05:
        interpretation['max_drawdown'] = '较小'
    elif max_dd < 0.10:
        interpretation['max_drawdown'] = '中等'
    elif max_dd < 0.20:
        interpretation['max_drawdown'] = '较大'
    else:
        interpretation['max_drawdown'] = '严重'

    return interpretation


@risk_analysis_bp.route('/api/position-risk', methods=['POST'])
@login_required
def analyze_position_risk_api():
    """持仓风险分析接口"""
    try:
        data = request.json
        portfolio_value = float(data.get('portfolio_value', 1000000))
        holdings = data.get('holdings', [])

        if not holdings:
            return jsonify({
                'success': True,
                'position_risks': [],
                'total_risk': 0,
                'risk_distribution': {}
            })

        # 计算各持仓风险
        position_risks = []
        total_market_value = 0
        industry_risks = {}

        for holding in holdings:
            market_value = holding.get('market_value', 0)
            quantity = holding.get('quantity', 0)
            current_price = holding.get('current_price', 0)
            avg_cost = holding.get('avg_cost', 0)
            volatility = holding.get('volatility', 0.02)  # 默认波动率
            industry = holding.get('industry', 'unknown')

            total_market_value += market_value

            # 计算持仓盈亏
            profit_loss = (current_price - avg_cost) * quantity if quantity > 0 else 0
            profit_loss_ratio = (current_price - avg_cost) / avg_cost if avg_cost > 0 else 0

            # 计算持仓对组合的风险贡献（简化计算）
            risk_contribution = market_value * volatility / portfolio_value if portfolio_value > 0 else 0

            position_risks.append({
                'symbol': holding.get('symbol', ''),
                'name': holding.get('name', ''),
                'market_value': market_value,
                'allocation': market_value / portfolio_value if portfolio_value > 0 else 0,
                'profit_loss': profit_loss,
                'profit_loss_ratio': profit_loss_ratio,
                'volatility': volatility,
                'risk_contribution': risk_contribution,
                'industry': industry
            })

            # 累计行业风险
            if industry not in industry_risks:
                industry_risks[industry] = {'allocation': 0, 'risk': 0}
            industry_risks[industry]['allocation'] += market_value / portfolio_value if portfolio_value > 0 else 0
            industry_risks[industry]['risk'] += risk_contribution

        # 计算总风险
        total_risk = sum(p['risk_contribution'] for p in position_risks)

        # 风险分布
        risk_distribution = {}
        for p in position_risks:
            risk_distribution[p['symbol']] = {
                'allocation': p['allocation'],
                'risk_contribution': p['risk_contribution'],
                'risk_contribution_percent': (p['risk_contribution'] / total_risk * 100) if total_risk > 0 else 0
            }

        return jsonify({
            'success': True,
            'position_risks': position_risks,
            'total_risk': total_risk,
            'total_market_value': total_market_value,
            'industry_risks': industry_risks,
            'risk_distribution': risk_distribution
        })

    except Exception as e:
        logger.error(f"持仓风险分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@risk_analysis_bp.route('/api/industry-concentration', methods=['POST'])
@login_required
def check_industry_concentration_api():
    """行业集中度检查接口"""
    try:
        data = request.json
        portfolio_value = float(data.get('portfolio_value', 1000000))
        holdings = data.get('holdings', [])
        new_trade = data.get('new_trade', None)  # 新交易信息

        # 计算当前行业配置
        industry_allocations = {}
        for holding in holdings:
            industry = holding.get('industry', 'unknown')
            market_value = holding.get('market_value', 0)
            allocation = market_value / portfolio_value if portfolio_value > 0 else 0
            industry_allocations[industry] = industry_allocations.get(industry, 0) + allocation

        # 创建风险约束
        max_sector_concentration = float(data.get('max_sector_concentration', 0.30))
        risk_constraints = RiskConstraints(
            max_sector_concentration=max_sector_concentration
        )

        # 添加自定义行业约束
        custom_constraints = data.get('industry_constraints', [])
        for constraint in custom_constraints:
            risk_constraints.industry_constraints.append(
                IndustryConstraint(
                    industry_name=constraint.get('industry_name', ''),
                    max_allocation=float(constraint.get('max_allocation', 0.30))
                )
            )

        # 创建风险管理器
        risk_manager = RiskManager(
            portfolio_value=portfolio_value,
            risk_constraints=risk_constraints
        )

        result = {
            'success': True,
            'current_concentration': {},
            'violations': [],
            'warnings': [],
            'can_trade': True
        }

        # 检查当前集中度
        for industry, allocation in industry_allocations.items():
            status = 'normal'
            if allocation > max_sector_concentration:
                status = 'exceeded'
            elif allocation > max_sector_concentration * 0.8:
                status = 'warning'

            result['current_concentration'][industry] = {
                'allocation': allocation,
                'allocation_percent': allocation * 100,
                'status': status
            }

            if status == 'exceeded':
                result['violations'].append(f"行业 '{industry}' 配置 {allocation * 100:.1f}% 超过限制")
                result['can_trade'] = False

        # 检查新交易
        if new_trade:
            industry = new_trade.get('industry', '')
            trade_value = new_trade.get('trade_value', 0)
            new_allocation = trade_value / portfolio_value if portfolio_value > 0 else 0

            check_result = risk_manager.check_industry_concentration(
                industry, new_allocation, industry_allocations
            )

            if not check_result.passed:
                result['violations'].extend(check_result.violations)
                result['can_trade'] = False

            result['warnings'].extend(check_result.warnings)
            result['suggested_action'] = check_result.suggested_action

        return jsonify(result)

    except Exception as e:
        logger.error(f"行业集中度检查失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@risk_analysis_bp.route('/api/validate-trade', methods=['POST'])
@login_required
def validate_trade_api():
    """交易验证接口"""
    try:
        data = request.json
        portfolio_value = float(data.get('portfolio_value', 1000000))
        holdings = data.get('holdings', [])
        trade = data.get('trade', {})

        # 计算当前行业配置
        industry_allocations = {}
        for holding in holdings:
            industry = holding.get('industry', 'unknown')
            market_value = holding.get('market_value', 0)
            allocation = market_value / portfolio_value if portfolio_value > 0 else 0
            industry_allocations[industry] = industry_allocations.get(industry, 0) + allocation

        # 创建风险约束
        risk_constraints = RiskConstraints(
            max_sector_concentration=float(data.get('max_sector_concentration', 0.30)),
            max_single_position_loss=float(data.get('max_single_position_loss', 0.10))
        )

        # 创建仓位配置
        position_config = PositionConfig(
            max_position_size=float(data.get('max_position_size', 0.20)),
            max_positions=int(data.get('max_positions', 10))
        )

        # 创建风险管理器
        risk_manager = RiskManager(
            portfolio_value=portfolio_value,
            position_config=position_config,
            risk_constraints=risk_constraints
        )

        # 验证交易
        result = risk_manager.validate_trade(
            symbol=trade.get('symbol', ''),
            price=float(trade.get('price', 0)),
            quantity=int(trade.get('quantity', 0)),
            trade_type=trade.get('trade_type', 'buy'),
            industry=trade.get('industry', 'unknown'),
            current_industry_allocations=industry_allocations
        )

        return jsonify({
            'success': True,
            'passed': result.passed,
            'violations': result.violations,
            'warnings': result.warnings,
            'suggested_action': result.suggested_action
        })

    except Exception as e:
        logger.error(f"交易验证失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@risk_analysis_bp.route('/api/risk-report', methods=['POST'])
@login_required
def get_risk_report_api():
    """获取风险报告接口"""
    try:
        data = request.json
        portfolio_value = float(data.get('portfolio_value', 1000000))
        holdings = data.get('holdings', [])

        # 创建持仓
        positions = {}
        for holding in holdings:
            symbol = holding.get('symbol', '')
            positions[symbol] = Position(
                symbol=symbol,
                name=holding.get('name', ''),
                quantity=float(holding.get('quantity', 0)),
                avg_cost=float(holding.get('avg_cost', 0)),
                current_price=float(holding.get('current_price', 0)),
                industry=holding.get('industry', 'unknown'),
                volatility=float(holding.get('volatility', 0.02))
            )

        # 创建风险管理器
        risk_manager = RiskManager(portfolio_value=portfolio_value)

        # 添加持仓
        for pos in positions.values():
            risk_manager.add_position(pos)

        # 获取风险报告
        report = risk_manager.get_portfolio_risk_report()

        return jsonify({
            'success': True,
            'report': report
        })

    except Exception as e:
        logger.error(f"获取风险报告失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
