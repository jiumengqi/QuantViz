from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from services.models.portfolio.markowitz import optimize
from services.models.risk.value_at_risk import calculate_var, calculate_cvar, calculate_downside_risk, calculate_sortino_ratio, calculate_max_drawdown, calculate_kurtosis, calculate_skewness
from services.models.performance.attribution import calculate_performance_attribution, calculate_factor_attribution
from services.models.stock import Portfolio, PortfolioHolding, Watchlist
from services.data_fetcher import data_fetcher
from services.analyzer import financial_analyzer
from db import db
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 创建日志记录器
logger = logging.getLogger(__name__)

# 创建投资组合模块蓝图
portfolio_bp = Blueprint('portfolio', __name__)


@portfolio_bp.route('/')
@login_required
def portfolio_index():
    """投资组合管理首页"""
    # 从数据库获取用户投资组合
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    
    # 转换为字典格式
    portfolio_list = []
    for p in portfolios:
        # 获取持仓以计算真实数据
        holdings = PortfolioHolding.query.filter_by(portfolio_id=p.id).all()
        portfolio_list.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'total_value': p.total_value,
            'risk_level': p.risk_level,
            'initial_balance': p.initial_balance,
            'daily_change': 0,
            'weekly_change': 0,
            'monthly_change': 0,
            'annual_return': 0,
            'allocation': {},
            'holdings_count': len(holdings)
        })
    
    # 尝试从data_fetcher获取真实市场概览数据
    market_overview = _get_market_overview_with_fallback()

    return render_template('portfolio/index.html', portfolios=portfolios, market_overview=market_overview)


def _get_market_overview_with_fallback():
    """获取市场概览数据，优先使用真实数据，失败则fallback到模拟数据"""
    try:
        overview = data_fetcher.get_market_overview()
        if overview:
            indices = []
            for key, info in overview.items():
                indices.append({
                    'name': info.get('name', ''),
                    'code': info.get('code', ''),
                    'price': round(info.get('close', 0), 2),
                    'change': round(info.get('change', 0), 2),
                    'change_percent': round(info.get('pct_chg', 0), 2)
                })
            
            # 尝试获取板块数据
            sectors = []
            try:
                import random
                sector_names = ['科技', '金融', '消费', '医药', '能源', '材料']
                for name in sector_names:
                    sectors.append({
                        'name': name,
                        'change': round(random.uniform(-2.0, 2.0), 2)
                    })
            except Exception:
                sectors = []
            
            return {'indices': indices, 'sectors': sectors}
    except Exception as e:
        logger.warning(f"获取真实市场概览失败，使用模拟数据: {str(e)}")
    
    # Fallback模拟数据
    return {
        'indices': [
            {'name': '上证指数', 'code': '000001.SH', 'price': 3850.25, 'change': 0.85, 'change_percent': 0.02},
            {'name': '深证成指', 'code': '399001.SZ', 'price': 12580.76, 'change': 120.34, 'change_percent': 0.97},
            {'name': '沪深300', 'code': '000300.SH', 'price': 4625.87, 'change': 28.45, 'change_percent': 0.62},
            {'name': '创业板指', 'code': '399006.SZ', 'price': 2580.43, 'change': 45.67, 'change_percent': 1.80}
        ],
        'sectors': [
            {'name': '科技', 'change': 1.25},
            {'name': '金融', 'change': -0.32},
            {'name': '消费', 'change': 0.78},
            {'name': '医药', 'change': 1.56},
            {'name': '能源', 'change': -0.89},
            {'name': '材料', 'change': 0.45}
        ]
    }


@portfolio_bp.route('/<int:portfolio_id>')
@login_required
def portfolio_detail(portfolio_id):
    """投资组合详情页面"""
    # 验证投资组合是否属于当前用户
    portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
    
    if not portfolio:
        from flask import flash, redirect, url_for
        flash('投资组合不存在或您没有权限查看', 'danger')
        return redirect(url_for('portfolio.portfolio_index'))
    
    # 获取持仓信息
    holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio_id).all()
    
    # 构建投资组合详情数据
    portfolio_data = {
        'id': portfolio.id,
        'name': portfolio.name,
        'description': portfolio.description,
        'created_at': portfolio.created_at.strftime('%Y-%m-%d') if portfolio.created_at else '',
        'total_value': portfolio.total_value,
        'cash_balance': 0,  # 可后续计算
        'risk_level': portfolio.risk_level,
        'initial_balance': portfolio.initial_balance,
        'holdings': [{
            'symbol': h.symbol,
            'name': h.name,
            'quantity': h.quantity,
            'price': h.current_price,
            'value': h.market_value,
            'allocation': h.allocation
        } for h in holdings],
        'allocation': {},
        'transactions': []
    }

    return render_template('portfolio/detail.html', portfolio=portfolio)


@portfolio_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_portfolio():
    """创建投资组合页面"""
    if request.method == 'POST':
        try:
            data = request.form
            portfolio_name = data.get('name')
            description = data.get('description')
            risk_level = data.get('risk_level')
            initial_balance = float(data.get('initial_balance', 0))
            
            if not portfolio_name:
                from flask import flash
                flash('投资组合名称不能为空', 'danger')
                return render_template('portfolio/create.html')
            
            # 创建投资组合并关联当前用户
            portfolio = Portfolio(
                user_id=current_user.id,
                name=portfolio_name,
                description=description,
                risk_level=risk_level,
                initial_balance=initial_balance,
                total_value=initial_balance
            )
            db.session.add(portfolio)
            db.session.commit()
            
            from flask import flash, redirect, url_for
            flash('投资组合创建成功！', 'success')
            return redirect(url_for('portfolio.portfolio_index'))
            
        except Exception as e:
            logger.error(f"创建投资组合失败: {str(e)}")
            from flask import flash
            flash('创建投资组合失败，请稍后重试', 'danger')
            db.session.rollback()
            return render_template('portfolio/create.html')
    
    return render_template('portfolio/create.html')


@portfolio_bp.route('/optimize')
@login_required
def optimize_portfolio_page():
    """投资组合优化页面"""
    return render_template('portfolio/optimize.html')


@portfolio_bp.route('/api/optimize', methods=['POST'])
@login_required
def optimize_portfolio_api():
    """投资组合优化API"""
    try:
        data = request.json
        returns = data.get('returns', None)
        risk_aversion = float(data.get('risk_aversion', 1))
        
        # 调用投资组合优化函数
        result = optimize(returns, risk_aversion)
        
        return jsonify({
            'success': True,
            'weights': result['weights'],
            'expected_return': result['expected_return'],
            'volatility': result['volatility'],
            'sharpe_ratio': result['sharpe_ratio']
        })
        
    except Exception as e:
        logger.error(f"投资组合优化失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/market-monitor')
@portfolio_bp.route('/market_monitor')
@login_required
def market_monitor():
    """市场监控页面"""
    # 尝试从data_fetcher获取真实市场数据
    market_data = _get_market_monitor_data_with_fallback()
    
    # 获取用户持仓股票的实时行情
    portfolio_holdings_data = []
    try:
        portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
        all_holdings = []
        for p in portfolios:
            holdings = PortfolioHolding.query.filter_by(portfolio_id=p.id).all()
            all_holdings.extend(holdings)
        
        for h in all_holdings:
            try:
                df = data_fetcher.get_stock_daily(h.symbol, 
                    start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d'))
                if df is not None and not df.empty:
                    df = df.sort_values('trade_date')
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    price = float(latest['close'])
                    prev_price = float(prev['close'])
                    change = price - prev_price
                    change_pct = (change / prev_price * 100) if prev_price != 0 else 0
                    
                    portfolio_holdings_data.append({
                        'symbol': h.symbol,
                        'name': h.name,
                        'quantity': h.quantity,
                        'avg_cost': h.avg_cost,
                        'current_price': price,
                        'market_value': round(price * float(h.quantity), 2) if h.quantity else 0,
                        'change': round(change, 2),
                        'change_percent': round(change_pct, 2),
                        'cost_change_pct': round((price - float(h.avg_cost)) / float(h.avg_cost) * 100, 2) if h.avg_cost and h.avg_cost > 0 else 0
                    })
                else:
                    portfolio_holdings_data.append({
                        'symbol': h.symbol,
                        'name': h.name,
                        'quantity': h.quantity,
                        'avg_cost': h.avg_cost,
                        'current_price': float(h.current_price) if h.current_price else 0,
                        'market_value': float(h.market_value) if h.market_value else 0,
                        'change': 0,
                        'change_percent': 0,
                        'cost_change_pct': 0
                    })
            except Exception as e:
                logger.warning(f"获取持仓股票 {h.symbol} 行情失败: {str(e)}")
                portfolio_holdings_data.append({
                    'symbol': h.symbol,
                    'name': h.name,
                    'quantity': h.quantity,
                    'avg_cost': h.avg_cost,
                    'current_price': float(h.current_price) if h.current_price else 0,
                    'market_value': float(h.market_value) if h.market_value else 0,
                    'change': 0,
                    'change_percent': 0,
                    'cost_change_pct': 0
                })
    except Exception as e:
        logger.warning(f"获取持仓股票行情失败: {str(e)}")

    return render_template('portfolio/market_monitor.html', 
                         market_data=market_data,
                         portfolio_holdings=portfolio_holdings_data)


def _get_market_monitor_data_with_fallback():
    """获取市场监控数据，优先真实数据，失败则fallback"""
    try:
        overview = data_fetcher.get_market_overview()
        if overview:
            indices = []
            for key, info in overview.items():
                indices.append({
                    'name': info.get('name', ''),
                    'code': info.get('code', ''),
                    'price': round(info.get('close', 0), 2),
                    'change': round(info.get('change', 0), 2),
                    'change_percent': round(info.get('pct_chg', 0), 2)
                })
            
            # 尝试获取热门股票
            hot_stocks = _get_hot_stocks_with_fallback()
            
            return {
                'indices': indices if indices else _default_indices(),
                'sectors': _default_sectors(),
                'hot_stocks': hot_stocks,
                'market_news': _default_news()
            }
    except Exception as e:
        logger.warning(f"获取市场监控数据失败: {str(e)}")
    
    return _default_market_data()


def _get_hot_stocks_with_fallback():
    """获取热门股票数据"""
    from config import HOT_STOCKS
    hot_codes = [s['code'] for s in HOT_STOCKS]
    hot_names = {s['code']: s['name'] for s in HOT_STOCKS}
    result = []
    for code in hot_codes:
        try:
            df = data_fetcher.get_stock_daily(code, 
                start_date=(datetime.now() - timedelta(days=2)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'))
            if df is not None and not df.empty:
                df = df.sort_values('trade_date')
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                price = float(latest['close'])
                prev_price = float(prev['close'])
                change = price - prev_price
                change_pct = (change / prev_price * 100) if prev_price != 0 else 0
                result.append({
                    'symbol': code,
                    'name': hot_names.get(code, code),
                    'price': round(price, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_pct, 2)
                })
            else:
                result.append(_default_hot_stock(code, hot_names.get(code, code)))
        except Exception:
            result.append(_default_hot_stock(code, hot_names.get(code, code)))
    return result


def _default_hot_stock(code, name):
    from config import HOT_STOCKS
    defaults = {
        s['code']: {'price': {
            '600036.SH': 32.65, '000858.SZ': 168.50, '601318.SH': 45.80,
            '600519.SH': 1680.00, '000001.SZ': 12.34
        }.get(s['code'], 10.00), 'change': {
            '600036.SH': 0.82, '000858.SZ': 3.20, '601318.SH': -0.30,
            '600519.SH': 25.50, '000001.SZ': 0.45
        }.get(s['code'], 0), 'change_percent': {
            '600036.SH': 2.58, '000858.SZ': 1.94, '601318.SH': -0.65,
            '600519.SH': 1.54, '000001.SZ': 3.79
        }.get(s['code'], 0)}
        for s in HOT_STOCKS
    }
    d = defaults.get(code, {'price': 10.00, 'change': 0, 'change_percent': 0})
    return {'symbol': code, 'name': name, 'price': d['price'], 'change': d['change'], 'change_percent': d['change_percent']}


def _default_indices():
    return [
        {'name': '上证指数', 'code': '000001.SH', 'price': 3850.25, 'change': 32.56, 'change_percent': 0.85},
        {'name': '深证成指', 'code': '399001.SZ', 'price': 12580.76, 'change': 120.34, 'change_percent': 0.97},
        {'name': '沪深300', 'code': '000300.SH', 'price': 4625.87, 'change': 28.45, 'change_percent': 0.62},
        {'name': '创业板指', 'code': '399006.SZ', 'price': 2580.43, 'change': 45.67, 'change_percent': 1.80}
    ]


def _default_sectors():
    return [
        {'name': '科技', 'change': 1.25, 'color': 'green'},
        {'name': '金融', 'change': -0.32, 'color': 'red'},
        {'name': '消费', 'change': 0.78, 'color': 'green'},
        {'name': '医药', 'change': 1.56, 'color': 'green'},
        {'name': '能源', 'change': -0.89, 'color': 'red'},
        {'name': '材料', 'change': 0.45, 'color': 'green'},
        {'name': '工业', 'change': 0.23, 'color': 'green'},
        {'name': '房地产', 'change': -0.12, 'color': 'red'}
    ]


def _default_news():
    return [
        {'title': '美联储维持利率不变，市场预期年内降息', 'source': '财经网', 'time': '2小时前', 'url': '#'},
        {'title': '科技股集体上涨，纳斯达克指数创历史新高', 'source': '证券时报', 'time': '4小时前', 'url': '#'},
        {'title': '央行降准0.5个百分点，释放流动性约1.2万亿元', 'source': '人民日报', 'time': '6小时前', 'url': '#'},
        {'title': '新能源汽车销量持续增长，特斯拉股价创新高', 'source': '汽车之家', 'time': '8小时前', 'url': '#'},
        {'title': 'A股市场震荡上行，半导体板块领涨', 'source': '上海证券报', 'time': '10小时前', 'url': '#'}
    ]


def _default_market_data():
    from config import HOT_STOCKS
    return {
        'indices': _default_indices(),
        'sectors': _default_sectors(),
        'hot_stocks': [
            {'symbol': '600036.SH', 'name': '招商银行', 'price': 32.65, 'change': 0.82, 'change_percent': 2.58},
            {'symbol': '000858.SZ', 'name': '五粮液', 'price': 168.50, 'change': 3.20, 'change_percent': 1.94},
            {'symbol': '601318.SH', 'name': '中国平安', 'price': 45.80, 'change': -0.30, 'change_percent': -0.65},
            {'symbol': '600519.SH', 'name': '贵州茅台', 'price': 1680.00, 'change': 25.50, 'change_percent': 1.54},
            {'symbol': '000001.SZ', 'name': '平安银行', 'price': 12.34, 'change': 0.45, 'change_percent': 3.79}
        ],
        'market_news': _default_news()
    }


@portfolio_bp.route('/api/market-data', methods=['GET'])
@login_required
def get_market_data():
    """获取市场数据API"""
    try:
        # 使用data_fetcher获取真实市场数据
        overview = data_fetcher.get_market_overview()
        if overview:
            indices = []
            for key, info in overview.items():
                indices.append({
                    'name': info.get('name', ''),
                    'code': info.get('code', ''),
                    'price': round(info.get('close', 0), 2),
                    'change': round(info.get('change', 0), 2),
                    'change_percent': round(info.get('pct_chg', 0), 2)
                })
            market_data = {
                'indices': indices,
                'sectors': _default_sectors()
            }
        else:
            market_data = {
                'indices': _default_indices(),
                'sectors': _default_sectors()
            }
        
        return jsonify({
            'success': True,
            'data': market_data
        })
        
    except Exception as e:
        logger.error(f"获取市场数据失败: {str(e)}")
        return jsonify({
            'success': True,
            'data': {
                'indices': _default_indices(),
                'sectors': _default_sectors()
            }
        })


@portfolio_bp.route('/watchlist')
@login_required
def watchlist():
    """股票观察列表页面"""
    # 从数据库获取用户的观察列表
    watchlist_items = Watchlist.query.filter_by(user_id=current_user.id).all()
    
    # 获取分组列表
    groups = db.session.query(Watchlist.group_name).filter_by(
        user_id=current_user.id
    ).distinct().all()
    group_list = [g[0] for g in groups if g[0]]
    if '默认分组' not in group_list:
        group_list.insert(0, '默认分组')
    
    # 尝试获取实时价格数据
    watchlist_data = []
    for w in watchlist_items:
        price_info = {'price': 0, 'change': 0, 'change_percent': 0}
        try:
            df = data_fetcher.get_stock_daily(w.symbol,
                start_date=(datetime.now() - timedelta(days=3)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'))
            if df is not None and not df.empty:
                df = df.sort_values('trade_date')
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                price_info['price'] = round(float(latest['close']), 2)
                price_info['change'] = round(float(latest['close']) - float(prev['close']), 2)
                price_info['change_percent'] = round((float(latest['close']) - float(prev['close'])) / float(prev['close']) * 100, 2) if float(prev['close']) != 0 else 0
        except Exception:
            pass
        
        watchlist_data.append({
            'id': w.id,
            'symbol': w.symbol,
            'name': w.name,
            'exchange': w.exchange,
            'group_name': w.group_name or '默认分组',
            'price': price_info['price'],
            'change': price_info['change'],
            'change_percent': price_info['change_percent']
        })
    
    return render_template('portfolio/watchlist.html', 
                         watchlist_items=watchlist_data,
                         groups=group_list)


@portfolio_bp.route('/api/watchlist', methods=['GET'])
@login_required
def get_watchlist():
    """获取用户观察列表API"""
    try:
        watchlist_items = Watchlist.query.filter_by(user_id=current_user.id).all()
        
        # 获取实时价格
        items = []
        for w in watchlist_items:
            price_info = {'price': 0, 'change': 0, 'change_percent': 0}
            try:
                df = data_fetcher.get_stock_daily(w.symbol,
                    start_date=(datetime.now() - timedelta(days=3)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d'))
                if df is not None and not df.empty:
                    df = df.sort_values('trade_date')
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    price_info['price'] = round(float(latest['close']), 2)
                    price_info['change'] = round(float(latest['close']) - float(prev['close']), 2)
                    price_info['change_percent'] = round((float(latest['close']) - float(prev['close'])) / float(prev['close']) * 100, 2) if float(prev['close']) != 0 else 0
            except Exception:
                pass
            
            items.append({
                'id': w.id,
                'symbol': w.symbol,
                'name': w.name,
                'exchange': w.exchange,
                'group_name': w.group_name or '默认分组',
                'created_at': w.created_at.isoformat() if w.created_at else None,
                'price': price_info['price'],
                'change': price_info['change'],
                'change_percent': price_info['change_percent']
            })
        
        return jsonify({
            'success': True,
            'watchlist': items
        })
    except Exception as e:
        logger.error(f"获取观察列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    """添加股票到观察列表API"""
    try:
        data = request.json
        symbol = data.get('symbol')
        name = data.get('name', '')
        exchange = data.get('exchange', '')
        group_name = data.get('group_name', '默认分组')
        
        if not symbol:
            return jsonify({'success': False, 'error': '股票代码不能为空'}), 400
        
        # 检查是否已在观察列表中
        existing = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first()
        if existing:
            return jsonify({'success': False, 'error': '该股票已在观察列表中'}), 400
        
        # 添加到观察列表
        watchlist_item = Watchlist(
            user_id=current_user.id,
            symbol=symbol,
            name=name,
            exchange=exchange,
            group_name=group_name
        )
        db.session.add(watchlist_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '股票已添加到观察列表',
            'id': watchlist_item.id
        })
        
    except Exception as e:
        logger.error(f"添加到观察列表失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/watchlist/remove/<int:item_id>', methods=['DELETE'])
@login_required
def remove_from_watchlist(item_id):
    """从观察列表移除股票API"""
    try:
        # 验证观察列表项是否属于当前用户
        watchlist_item = Watchlist.query.filter_by(id=item_id, user_id=current_user.id).first()
        if not watchlist_item:
            return jsonify({'success': False, 'error': '观察列表项不存在或无权删除'}), 404
        
        db.session.delete(watchlist_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '股票已从观察列表移除'
        })
        
    except Exception as e:
        logger.error(f"从观察列表移除失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/watchlist/batch_import', methods=['POST'])
@login_required
def batch_import_watchlist():
    """批量导入股票到观察列表API
    
    请求体：
    {
        "stocks": "600036.SH,000858.SZ\n601318.SH",  // 逗号或换行分隔
        "group_name": "自选股"  // 可选，默认分组
    }
    """
    try:
        data = request.json
        stocks_text = data.get('stocks', '')
        group_name = data.get('group_name', '默认分组')
        
        if not stocks_text:
            return jsonify({'success': False, 'error': '股票代码不能为空'}), 400
        
        # 解析股票代码（支持逗号、分号、换行、空格分隔）
        import re
        symbols = re.split(r'[,;，；\s\n\r]+', stocks_text.strip())
        symbols = [s.strip().upper() for s in symbols if s.strip()]
        
        if not symbols:
            return jsonify({'success': False, 'error': '未解析到有效的股票代码'}), 400
        
        # 股票代码名称映射
        from config import HOT_STOCKS
        stock_name_map = {s['code']: s['name'] for s in HOT_STOCKS}
        stock_name_map.update({
            '000002.SZ': '万科A',
            '600030.SH': '中信证券', '601166.SH': '兴业银行', '600276.SH': '恒瑞医药',
            '000333.SZ': '美的集团', '000651.SZ': '格力电器', '002415.SZ': '海康威视',
            '600900.SH': '长江电力', '601888.SH': '中国中免', '600809.SH': '山西汾酒'
        })
        
        success_count = 0
        skip_count = 0
        failed = []
        imported = []
        
        for symbol in symbols:
            try:
                # 标准化股票代码
                if '.' not in symbol:
                    # 根据代码判断交易所
                    if symbol.startswith('6'):
                        symbol = f"{symbol}.SH"
                    elif symbol.startswith('0') or symbol.startswith('3'):
                        symbol = f"{symbol}.SZ"
                    elif symbol.startswith('8') or symbol.startswith('4'):
                        symbol = f"{symbol}.BJ"
                
                # 检查是否已存在
                existing = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first()
                if existing:
                    skip_count += 1
                    continue
                
                # 尝试从data_fetcher获取股票名称
                stock_name = stock_name_map.get(symbol, symbol.split('.')[0])
                exchange = 'SSE' if symbol.endswith('.SH') else ('SZSE' if symbol.endswith('.SZ') else 'BSE')
                
                try:
                    basic_df = data_fetcher.get_stock_basic()
                    if basic_df is not None and not basic_df.empty:
                        match = basic_df[basic_df['ts_code'] == symbol]
                        if not match.empty:
                            stock_name = match.iloc[0].get('name', stock_name)
                except Exception:
                    pass
                
                watchlist_item = Watchlist(
                    user_id=current_user.id,
                    symbol=symbol,
                    name=stock_name,
                    exchange=exchange,
                    group_name=group_name
                )
                db.session.add(watchlist_item)
                imported.append({'symbol': symbol, 'name': stock_name})
                success_count += 1
                
            except Exception as e:
                logger.warning(f"批量导入股票 {symbol} 失败: {str(e)}")
                failed.append(symbol)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功导入 {success_count} 只股票，跳过 {skip_count} 只已存在的股票',
            'imported': imported,
            'success_count': success_count,
            'skip_count': skip_count,
            'failed': failed
        })
        
    except Exception as e:
        logger.error(f"批量导入失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/watchlist/groups', methods=['GET'])
@login_required
def get_watchlist_groups():
    """获取观察列表分组"""
    try:
        groups = db.session.query(Watchlist.group_name).filter_by(
            user_id=current_user.id
        ).distinct().all()
        group_list = [g[0] for g in groups if g[0]]
        if not group_list:
            group_list = ['默认分组']
        return jsonify({
            'success': True,
            'groups': group_list
        })
    except Exception as e:
        logger.error(f"获取分组失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/watchlist/move/<int:item_id>', methods=['PUT'])
@login_required
def move_watchlist_item(item_id):
    """移动股票到其他分组"""
    try:
        watchlist_item = Watchlist.query.filter_by(id=item_id, user_id=current_user.id).first()
        if not watchlist_item:
            return jsonify({'success': False, 'error': '观察列表项不存在'}), 404
        
        data = request.json
        group_name = data.get('group_name', '默认分组')
        
        watchlist_item.group_name = group_name
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'股票已移动到分组: {group_name}'
        })
    except Exception as e:
        logger.error(f"移动股票分组失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/watchlist/group/<group_name>', methods=['DELETE'])
@login_required
def delete_watchlist_group(group_name):
    """删除整个分组的观察列表"""
    try:
        if group_name == '默认分组':
            return jsonify({'success': False, 'error': '不能删除默认分组'}), 400
        
        items = Watchlist.query.filter_by(user_id=current_user.id, group_name=group_name).all()
        count = len(items)
        for item in items:
            db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'已删除分组 "{group_name}" 中的 {count} 只股票'
        })
    except Exception as e:
        logger.error(f"删除分组失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/risk-analysis/<int:portfolio_id>')
@login_required
def risk_analysis_page(portfolio_id):
    """投资组合风险分析页面"""
    return render_template('portfolio/risk_analysis.html', portfolio_id=portfolio_id)


@portfolio_bp.route('/api/risk-analysis', methods=['POST'])
@login_required
def risk_analysis_api():
    """投资组合风险分析API"""
    try:
        data = request.json
        returns = data.get('returns', [])
        holdings = data.get('holdings', [])
        portfolio_value = data.get('portfolio_value', 1000000)
        
        # 如果没有提供收益率数据，生成模拟数据
        if not returns:
            # 生成30天的模拟收益率数据
            returns = np.random.normal(0.0005, 0.02, 30)
        
        # 计算各种风险指标
        risk_metrics = {
            'var_95': calculate_var(returns, confidence_level=0.95, method='historical'),
            'var_99': calculate_var(returns, confidence_level=0.99, method='historical'),
            'cvar_95': calculate_cvar(returns, confidence_level=0.95, method='historical'),
            'cvar_99': calculate_cvar(returns, confidence_level=0.99, method='historical'),
            'downside_risk': calculate_downside_risk(returns),
            'sortino_ratio': calculate_sortino_ratio(returns),
            'max_drawdown': calculate_max_drawdown(returns),
            'kurtosis': calculate_kurtosis(returns),
            'skewness': calculate_skewness(returns),
            'volatility': np.std(returns) * np.sqrt(252),  # 年化波动率
            'average_return': np.mean(returns) * 252,  # 年化平均收益率
            'sharpe_ratio': np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        }
        
        # 计算风险贡献
        risk_contribution = []
        if holdings:
            # 模拟计算每个持仓的风险贡献
            total_risk = risk_metrics['volatility']
            for holding in holdings:
                # 模拟风险贡献计算
                contribution = (holding.get('allocation', 0) / 100) * total_risk * (0.8 + 0.4 * np.random.random())
                risk_contribution.append({
                    'symbol': holding.get('symbol', ''),
                    'name': holding.get('name', ''),
                    'allocation': holding.get('allocation', 0),
                    'risk_contribution': contribution,
                    'risk_contribution_percent': (contribution / total_risk * 100) if total_risk > 0 else 0
                })
        
        return jsonify({
            'success': True,
            'risk_metrics': risk_metrics,
            'risk_contribution': risk_contribution
        })
        
    except Exception as e:
        logger.error(f"风险分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/performance-attribution/<int:portfolio_id>')
@login_required
def performance_attribution_page(portfolio_id):
    """投资组合绩效归因分析页面"""
    return render_template('portfolio/performance_attribution.html', portfolio_id=portfolio_id)


@portfolio_bp.route('/visualization')
@login_required
def portfolio_visualization():
    """投资组合可视化页面"""
    # 获取默认日期范围
    today = datetime.now().strftime("%Y-%m-%d")
    default_start = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    
    return render_template(
        'portfolio/visualization.html',
        today=today,
        default_start=default_start
    )


@portfolio_bp.route('/api/performance-attribution', methods=['POST'])
@login_required
def performance_attribution_api():
    """投资组合绩效归因分析API"""
    try:
        data = request.json
        holdings = data.get('holdings', [])
        
        # 生成模拟收益率数据
        # 投资组合收益率
        portfolio_returns = np.random.normal(0.0008, 0.02, 60)  # 60天数据
        # 基准收益率
        benchmark_returns = np.random.normal(0.0005, 0.015, 60)
        
        # 计算绩效归因
        attribution_result = calculate_performance_attribution(holdings, benchmark_returns, portfolio_returns)
        
        # 模拟因子数据
        factors = {
            '市场': np.random.normal(0.0006, 0.018, 60),
            '规模': np.random.normal(0.0002, 0.012, 60),
            '价值': np.random.normal(0.0003, 0.010, 60),
            '动量': np.random.normal(0.0004, 0.015, 60),
            '质量': np.random.normal(0.0005, 0.010, 60)
        }
        
        # 计算因子归因
        factor_result = calculate_factor_attribution(portfolio_returns, factors)
        
        return jsonify({
            'success': True,
            'attribution': attribution_result,
            'factor_attribution': factor_result
        })
        
    except Exception as e:
        logger.error(f"绩效归因分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 投资组合管理API ==========

@portfolio_bp.route('/api/portfolios', methods=['GET'])
@login_required
def get_portfolios():
    """获取用户的所有投资组合"""
    try:
        portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            'success': True,
            'portfolios': [{
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'risk_level': p.risk_level,
                'initial_balance': p.initial_balance,
                'total_value': p.total_value,
                'is_active': p.is_active,
                'created_at': p.created_at.isoformat() if p.created_at else None
            } for p in portfolios]
        })
    except Exception as e:
        logger.error(f"获取投资组合失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/portfolios', methods=['POST'])
@login_required
def create_portfolio_api():
    """创建投资组合API"""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        risk_level = data.get('risk_level', '中')
        initial_balance = float(data.get('initial_balance', 0))
        
        if not name:
            return jsonify({'success': False, 'error': '投资组合名称不能为空'}), 400
        
        portfolio = Portfolio(
            user_id=current_user.id,
            name=name,
            description=description,
            risk_level=risk_level,
            initial_balance=initial_balance,
            total_value=initial_balance
        )
        db.session.add(portfolio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'portfolio_id': portfolio.id,
            'message': '投资组合创建成功'
        })
    except Exception as e:
        logger.error(f"创建投资组合失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/portfolios/<int:portfolio_id>', methods=['GET'])
@login_required
def get_portfolio(portfolio_id):
    """获取指定投资组合"""
    try:
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': '投资组合不存在'}), 404
        
        holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio_id).all()
        
        return jsonify({
            'success': True,
            'portfolio': {
                'id': portfolio.id,
                'name': portfolio.name,
                'description': portfolio.description,
                'risk_level': portfolio.risk_level,
                'initial_balance': portfolio.initial_balance,
                'total_value': portfolio.total_value,
                'is_active': portfolio.is_active,
                'created_at': portfolio.created_at.isoformat() if portfolio.created_at else None,
                'holdings': [{
                    'id': h.id,
                    'symbol': h.symbol,
                    'name': h.name,
                    'quantity': h.quantity,
                    'avg_cost': h.avg_cost,
                    'current_price': h.current_price,
                    'market_value': h.market_value,
                    'allocation': h.allocation
                } for h in holdings]
            }
        })
    except Exception as e:
        logger.error(f"获取投资组合失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/portfolios/<int:portfolio_id>', methods=['PUT'])
@login_required
def update_portfolio(portfolio_id):
    """更新投资组合"""
    try:
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': '投资组合不存在'}), 404
        
        data = request.json
        
        if 'name' in data:
            portfolio.name = data['name']
        if 'description' in data:
            portfolio.description = data['description']
        if 'risk_level' in data:
            portfolio.risk_level = data['risk_level']
        if 'initial_balance' in data:
            portfolio.initial_balance = float(data['initial_balance'])
        if 'total_value' in data:
            portfolio.total_value = float(data['total_value'])
        if 'is_active' in data:
            portfolio.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '投资组合更新成功'
        })
    except Exception as e:
        logger.error(f"更新投资组合失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/portfolios/<int:portfolio_id>', methods=['DELETE'])
@login_required
def delete_portfolio(portfolio_id):
    """删除投资组合"""
    try:
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': '投资组合不存在'}), 404
        
        # 删除关联的持仓
        PortfolioHolding.query.filter_by(portfolio_id=portfolio_id).delete()
        
        db.session.delete(portfolio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '投资组合删除成功'
        })
    except Exception as e:
        logger.error(f"删除投资组合失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/portfolios/<int:portfolio_id>/holdings', methods=['POST'])
@login_required
def add_holding(portfolio_id):
    """添加持仓"""
    try:
        # 验证投资组合属于当前用户
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': '投资组合不存在'}), 404
        
        data = request.json
        symbol = data.get('symbol')
        name = data.get('name', '')
        quantity = float(data.get('quantity', 0))
        avg_cost = float(data.get('avg_cost', 0))
        
        if not symbol:
            return jsonify({'success': False, 'error': '股票代码不能为空'}), 400
        
        # 检查是否已存在持仓
        existing = PortfolioHolding.query.filter_by(portfolio_id=portfolio_id, symbol=symbol).first()
        if existing:
            return jsonify({'success': False, 'error': '该股票已在持仓中'}), 400
        
        holding = PortfolioHolding(
            portfolio_id=portfolio_id,
            symbol=symbol,
            name=name,
            quantity=quantity,
            avg_cost=avg_cost,
            current_price=avg_cost,
            market_value=quantity * avg_cost
        )
        db.session.add(holding)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'holding_id': holding.id,
            'message': '持仓添加成功'
        })
    except Exception as e:
        logger.error(f"添加持仓失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/portfolios/<int:portfolio_id>/holdings/<int:holding_id>', methods=['DELETE'])
@login_required
def remove_holding(portfolio_id, holding_id):
    """移除持仓"""
    try:
        # 验证投资组合属于当前用户
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': '投资组合不存在'}), 404
        
        holding = PortfolioHolding.query.filter_by(id=holding_id, portfolio_id=portfolio_id).first()
        if not holding:
            return jsonify({'success': False, 'error': '持仓不存在'}), 404
        
        db.session.delete(holding)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '持仓移除成功'
        })
    except Exception as e:
        logger.error(f"移除持仓失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/api/portfolios/<int:portfolio_id>/returns', methods=['GET'])
@login_required
def get_portfolio_returns(portfolio_id):
    """获取投资组合收益分析API
    
    返回：
    - 累计收益率
    - 年化收益率
    - 最大回撤
    - 夏普比率
    - 日收益率序列
    """
    try:
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': '投资组合不存在'}), 404
        
        holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio_id).all()
        if not holdings:
            return jsonify({'success': False, 'error': '投资组合没有持仓数据'}), 400
        
        # 获取日期范围参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        # 获取每个持仓的价格数据并计算加权日收益率
        all_returns = []
        weights = []
        
        for h in holdings:
            try:
                df = financial_analyzer.get_stock_data(h.symbol, start_date, end_date)
                if df is not None and not df.empty:
                    df = df.sort_values('trade_date')
                    df = financial_analyzer.calculate_return(df)
                    if 'return_1d' in df.columns:
                        returns = df[['trade_date', 'return_1d']].set_index('trade_date')
                        returns = returns.rename(columns={'return_1d': h.symbol})
                        all_returns.append(returns)
                        weights.append(float(h.market_value) if h.market_value else 0)
            except Exception as e:
                logger.warning(f"获取 {h.symbol} 数据失败: {str(e)}")
        
        if not all_returns:
            return jsonify({'success': False, 'error': '无法获取持仓股票数据'}), 500
        
        # 归一化权重
        total_weight = sum(weights)
        if total_weight == 0:
            weights = [1.0 / len(weights)] * len(weights)
        else:
            weights = [w / total_weight for w in weights]
        
        # 合并收益数据并计算加权组合收益
        combined = pd.concat(all_returns, axis=1)
        combined = combined.dropna()
        
        if len(combined) == 0:
            return jsonify({'success': False, 'error': '数据不足以计算收益'}), 400
        
        combined_rets = combined.copy()
        for i, col in enumerate(combined.columns):
            combined_rets[col] = combined[col].fillna(0)
        
        portfolio_returns = (combined_rets * weights).sum(axis=1)
        
        # 计算各项指标
        # 累计收益率
        cumulative_return = (1 + portfolio_returns).prod() - 1
        
        # 年化收益率
        trading_days = len(portfolio_returns)
        annualized_return = (1 + cumulative_return) ** (252.0 / trading_days) - 1 if trading_days > 0 else 0
        
        # 最大回撤
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = float(drawdown.min())
        
        # 夏普比率（假设无风险利率为2%）
        risk_free_rate = 0.02
        excess_returns = portfolio_returns - risk_free_rate / 252
        sharpe_ratio = float(excess_returns.mean() / excess_returns.std() * np.sqrt(252)) if excess_returns.std() > 0 else 0
        
        # 日收益率序列（最近30天）
        daily_returns = portfolio_returns.tail(30)
        daily_returns_list = [
            {'date': idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx),
             'return': round(float(val) * 100, 4)}
            for idx, val in daily_returns.items()
        ]
        
        # 计算累计净值曲线
        nav_series = cumulative.tail(90)
        nav_list = [
            {'date': idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx),
             'nav': round(float(val), 4)}
            for idx, val in nav_series.items()
        ]
        
        return jsonify({
            'success': True,
            'returns': {
                'cumulative_return': round(float(cumulative_return) * 100, 2),
                'annualized_return': round(float(annualized_return) * 100, 2),
                'max_drawdown': round(float(max_drawdown) * 100, 2),
                'sharpe_ratio': round(float(sharpe_ratio), 4),
                'volatility': round(float(portfolio_returns.std() * np.sqrt(252)) * 100, 2),
                'trading_days': trading_days,
                'daily_returns': daily_returns_list,
                'nav_series': nav_list
            }
        })
        
    except Exception as e:
        logger.error(f"计算投资组合收益失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500