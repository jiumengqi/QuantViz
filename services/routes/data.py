from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from services.data_fetcher import data_fetcher
from services.analyzer import financial_analyzer
import pandas as pd
import json
from datetime import datetime

# 创建数据模块蓝图
data_bp = Blueprint('data', __name__)


@data_bp.route('/')
def data_index():
    """数据中心首页"""
    try:
        # 获取热门股票列表
        from config import HOT_STOCKS
        popular_stocks = HOT_STOCKS

        # 尝试获取市场概览数据（如果可用）
        market_overview = None
        try:
            # 从缓存获取市场概览数据
            if hasattr(current_app, 'cache'):
                market_overview = current_app.cache.get('market_overview')
                if market_overview is None:
                    market_overview = data_fetcher.get_market_overview()
                    if market_overview:
                        current_app.cache.set('market_overview', market_overview, timeout=3600)
        except Exception as e:
            current_app.logger.warning(f"获取市场概览数据失败: {str(e)}")
            # 继续运行，使用静态数据

        return render_template('data/index.html', popular_stocks=popular_stocks, market_overview=market_overview)
    except Exception as e:
        current_app.logger.error(f"数据中心首页加载失败: {str(e)}")
        # 即使出错也要返回页面，使用静态数据
        from config import HOT_STOCKS
        popular_stocks = HOT_STOCKS
        return render_template('data/index.html', popular_stocks=popular_stocks, market_overview=None)


@data_bp.route('/stock')
def stock_data_default():
    """股票数据默认页面（重定向到数据中心首页）"""
    return redirect(url_for('data.data_index'))


@data_bp.route('/stock/<string:ts_code>')
def stock_data(ts_code):
    """股票数据详情页"""
    try:
        # 获取前端传递的日期范围
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 尝试获取股票数据，但不依赖它来渲染页面
        df = None
        try:
            df = data_fetcher.get_stock_data(ts_code, start_date, end_date)
        except Exception as e:
            current_app.logger.warning(f"获取股票数据失败: {str(e)}")
            # 继续渲染页面，使用默认日期范围

        # 如果没有指定日期范围，使用默认值
        if not start_date:
            start_date = (datetime.now() - pd.Timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        # 从代码中解析股票名称（简单实现）
        from config import HOT_STOCKS
        stock_name_map = {s['code']: s['name'] for s in HOT_STOCKS}
        stock_name = stock_name_map.get(ts_code, ts_code.split('.')[0])

        return render_template(
            'data/stock.html',
            ts_code=ts_code,
            stock_name=stock_name,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        current_app.logger.error(f"股票详情页加载失败: {str(e)}")
        return render_template('errors/500.html'), 500


@data_bp.route('/api/stock/<string:ts_code>/prices')
def get_stock_prices(ts_code):
    """获取股票价格数据API"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 获取数据
        df = data_fetcher.get_stock_data(ts_code, start_date, end_date)

        if df is None or df.empty:
            # 如果没有数据，返回模拟数据
            current_app.logger.warning(f"没有找到股票 {ts_code} 的数据，返回模拟数据")
            # 生成模拟数据
            dates = pd.date_range(end=datetime.now(), periods=30)
            base_price = 100
            prices = [base_price + (i % 10 - 5) * 0.5 for i in range(30)]
            
            df = pd.DataFrame({
                'trade_date': dates,
                'open': prices,
                'high': [p * 1.02 for p in prices],
                'low': [p * 0.98 for p in prices],
                'close': prices,
                'volume': [1000000 + i * 10000 for i in range(30)]
            })

        # 转换为前端需要的格式
        try:
            # 检查trade_date是否为日期类型
            if pd.api.types.is_datetime64_any_dtype(df['trade_date']):
                df['trade_date'] = df['trade_date'].dt.strftime('%Y-%m-%d')
            else:
                # 如果是字符串类型，尝试转换格式
                df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')
        except Exception as e:
            current_app.logger.warning(f"转换trade_date格式失败: {str(e)}")
            # 如果转换失败，保持原有格式
        data = df.to_dict('records')

        return jsonify({
            'code': ts_code,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        current_app.logger.error(f"获取股票价格数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/indexes')
def indexes_data():
    """指数数据页面"""
    try:
        return render_template('data/indexes.html')
    except Exception as e:
        current_app.logger.error(f"指数数据页面加载失败: {str(e)}")
        return render_template('errors/500.html'), 500
