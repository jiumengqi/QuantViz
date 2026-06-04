# -*- coding: utf-8 -*-
"""
导出API路由
提供回测结果和投资组合的导出功能
"""

from flask import Blueprint, jsonify, current_app, send_file
from flask_login import login_required, current_user
from services.models.stock import BacktestResult, Portfolio, PortfolioHolding
from services.export_utils import (
    export_to_csv_response,
    export_to_excel_response,
    export_to_pdf_response,
    generate_backtest_report_html,
    generate_portfolio_report_html
)
import json
import logging

logger = logging.getLogger(__name__)

# 创建导出模块蓝图
export_bp = Blueprint('export', __name__)


@export_bp.route('/backtest/<int:backtest_id>/csv')
@login_required
def export_backtest_csv(backtest_id):
    """导出回测结果为CSV格式"""
    try:
        # 获取回测结果
        result = BacktestResult.query.filter_by(id=backtest_id, user_id=current_user.id).first()
        if not result:
            return jsonify({'success': False, 'error': '回测结果不存在'}), 404

        result_data = json.loads(result.result_data) if result.result_data else {}
        trades = result_data.get('trades', [])

        if not trades:
            return jsonify({'success': False, 'error': '没有交易记录可以导出'}), 400

        # 转换交易记录格式
        export_data = []
        for trade in trades:
            export_data.append({
                '日期': trade.get('date', ''),
                '类型': '买入' if trade.get('type') == 'buy' else '卖出',
                '价格': trade.get('price', 0),
                '数量': trade.get('shares', 0),
                '金额': trade.get('amount', 0),
                '手续费': trade.get('fee', 0),
                '剩余资金': trade.get('remaining_capital', 0),
                '持仓': trade.get('positions', 0)
            })

        filename = f"backtest_{backtest_id}_trades.csv"
        response, _ = export_to_csv_response(export_data, filename)

        logger.info(f"用户 {current_user.id} 导出了回测 {backtest_id} 的CSV")
        return response

    except Exception as e:
        logger.error(f"导出CSV失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@export_bp.route('/backtest/<int:backtest_id>/excel')
@login_required
def export_backtest_excel(backtest_id):
    """导出回测结果为Excel格式"""
    try:
        # 获取回测结果
        result = BacktestResult.query.filter_by(id=backtest_id, user_id=current_user.id).first()
        if not result:
            return jsonify({'success': False, 'error': '回测结果不存在'}), 404

        result_data = json.loads(result.result_data) if result.result_data else {}
        trades = result_data.get('trades', [])

        if not trades:
            return jsonify({'success': False, 'error': '没有交易记录可以导出'}), 400

        # 转换交易记录格式
        export_data = []
        for trade in trades:
            export_data.append({
                '日期': trade.get('date', ''),
                '类型': '买入' if trade.get('type') == 'buy' else '卖出',
                '价格': trade.get('price', 0),
                '数量': trade.get('shares', 0),
                '金额': trade.get('amount', 0),
                '手续费': trade.get('fee', 0),
                '剩余资金': trade.get('remaining_capital', 0),
                '持仓': trade.get('positions', 0)
            })

        filename = f"backtest_{backtest_id}_report.xlsx"
        response, _ = export_to_excel_response(export_data, filename, sheet_name='交易记录')

        logger.info(f"用户 {current_user.id} 导出了回测 {backtest_id} 的Excel")
        return response

    except ImportError as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        logger.error(f"导出Excel失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@export_bp.route('/backtest/<int:backtest_id>/pdf')
@login_required
def export_backtest_pdf(backtest_id):
    """导出回测报告为PDF格式"""
    try:
        # 获取回测结果
        result = BacktestResult.query.filter_by(id=backtest_id, user_id=current_user.id).first()
        if not result:
            return jsonify({'success': False, 'error': '回测结果不存在'}), 404

        result_data = json.loads(result.result_data) if result.result_data else {}

        # 构建回测结果字典
        backtest_result = {
            'strategy_name': result.strategy.name if result.strategy else '未知策略',
            'stock_code': result.stock.symbol if result.stock else '未知股票',
            'start_date': result.start_date.isoformat() if result.start_date else '',
            'end_date': result.end_date.isoformat() if result.end_date else '',
            'total_return': result.total_return,
            'annual_return': result.annual_return,
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown,
            'win_rate': result.win_rate,
            'total_trades': result.total_trades,
            'initial_capital': json.loads(result.parameters).get('initial_capital', 1000000) if result.parameters else 1000000,
            'final_assets': result_data.get('final_assets', 0)
        }

        # 获取交易记录
        trades = result_data.get('trades', [])

        # 生成HTML报告
        html_content = generate_backtest_report_html(backtest_result, trades_data=trades)

        filename = f"backtest_{backtest_id}_report.pdf"
        response, _ = export_to_pdf_response(html_content, filename)

        logger.info(f"用户 {current_user.id} 导出了回测 {backtest_id} 的PDF")
        return response

    except ImportError as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        logger.error(f"导出PDF失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@export_bp.route('/portfolio/<int:portfolio_id>/csv')
@login_required
def export_portfolio_csv(portfolio_id):
    """导出投资组合持仓数据为CSV格式"""
    try:
        # 获取投资组合
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': '投资组合不存在'}), 404

        # 获取持仓信息
        holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio_id).all()

        if not holdings:
            return jsonify({'success': False, 'error': '没有持仓数据可以导出'}), 400

        # 转换持仓数据格式
        export_data = []
        for holding in holdings:
            export_data.append({
                '代码': holding.symbol,
                '名称': holding.name,
                '数量': holding.quantity,
                '成本价': holding.avg_cost,
                '当前价': holding.current_price,
                '市值': holding.market_value,
                '盈亏': holding.market_value - (holding.quantity * holding.avg_cost),
                '盈亏比例': ((holding.current_price - holding.avg_cost) / holding.avg_cost * 100) if holding.avg_cost > 0 else 0,
                '占比': holding.allocation
            })

        filename = f"portfolio_{portfolio_id}_holdings.csv"
        response, _ = export_to_csv_response(export_data, filename)

        logger.info(f"用户 {current_user.id} 导出了投资组合 {portfolio_id} 的CSV")
        return response

    except Exception as e:
        logger.error(f"导出CSV失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@export_bp.route('/portfolio/<int:portfolio_id>/excel')
@login_required
def export_portfolio_excel(portfolio_id):
    """导出投资组合持仓数据为Excel格式"""
    try:
        # 获取投资组合
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': '投资组合不存在'}), 404

        # 获取持仓信息
        holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio_id).all()

        if not holdings:
            return jsonify({'success': False, 'error': '没有持仓数据可以导出'}), 400

        # 转换持仓数据格式
        export_data = []
        for holding in holdings:
            export_data.append({
                '代码': holding.symbol,
                '名称': holding.name,
                '数量': holding.quantity,
                '成本价': holding.avg_cost,
                '当前价': holding.current_price,
                '市值': holding.market_value,
                '盈亏': holding.market_value - (holding.quantity * holding.avg_cost),
                '盈亏比例': ((holding.current_price - holding.avg_cost) / holding.avg_cost * 100) if holding.avg_cost > 0 else 0,
                '占比': holding.allocation
            })

        filename = f"portfolio_{portfolio_id}_report.xlsx"
        response, _ = export_to_excel_response(export_data, filename, sheet_name='持仓明细')

        logger.info(f"用户 {current_user.id} 导出了投资组合 {portfolio_id} 的Excel")
        return response

    except ImportError as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        logger.error(f"导出Excel失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@export_bp.route('/portfolio/<int:portfolio_id>/pdf')
@login_required
def export_portfolio_pdf(portfolio_id):
    """导出投资组合报告为PDF格式"""
    try:
        # 获取投资组合
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': '投资组合不存在'}), 404

        # 获取持仓信息
        holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio_id).all()

        # 构建投资组合数据
        portfolio_data = {
            'name': portfolio.name,
            'description': portfolio.description,
            'total_value': portfolio.total_value,
            'cash_balance': 0,  # 可以根据实际情况计算
            'risk_level': portfolio.risk_level,
            'initial_balance': portfolio.initial_balance,
            'daily_change': 0,
            'annual_return': 0
        }

        # 转换持仓数据
        holdings_data = []
        for holding in holdings:
            holdings_data.append({
                'symbol': holding.symbol,
                'name': holding.name,
                'quantity': holding.quantity,
                'avg_cost': holding.avg_cost,
                'current_price': holding.current_price,
                'market_value': holding.market_value,
                'allocation': holding.allocation
            })

        # 生成HTML报告
        html_content = generate_portfolio_report_html(portfolio_data, holdings_data=holdings_data)

        filename = f"portfolio_{portfolio_id}_report.pdf"
        response, _ = export_to_pdf_response(html_content, filename)

        logger.info(f"用户 {current_user.id} 导出了投资组合 {portfolio_id} 的PDF")
        return response

    except ImportError as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        logger.error(f"导出PDF失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@export_bp.route('/equity/<int:backtest_id>/csv')
@login_required
def export_equity_csv(backtest_id):
    """导出回测净值曲线数据为CSV格式"""
    try:
        # 获取回测结果
        result = BacktestResult.query.filter_by(id=backtest_id, user_id=current_user.id).first()
        if not result:
            return jsonify({'success': False, 'error': '回测结果不存在'}), 404

        result_data = json.loads(result.result_data) if result.result_data else {}
        equity_data = result_data.get('equity_data', [])

        if not equity_data:
            return jsonify({'success': False, 'error': '没有净值数据可以导出'}), 400

        # 转换净值数据格式
        export_data = []
        for item in equity_data:
            export_data.append({
                '日期': item.get('date', ''),
                '总资产': item.get('total_assets', 0),
                '累计收益率': item.get('cumulative_return', 0)
            })

        filename = f"backtest_{backtest_id}_equity.csv"
        response, _ = export_to_csv_response(export_data, filename)

        logger.info(f"用户 {current_user.id} 导出了回测 {backtest_id} 的净值CSV")
        return response

    except Exception as e:
        logger.error(f"导出净值CSV失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
