from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from flask_login import login_required, current_user
from services.backtest import BacktestEngine, MovingAverageCrossStrategy, RSIStrategy, MACDStrategy
from services.data_fetcher import data_fetcher
from services.models.stock import Strategy as StrategyModel, BacktestResult
from services.models.strategy_version import StrategyVersion
from services.diff_utils import generate_diff_html
from services.strategy_templates import (
    get_all_templates, get_template_by_id, get_template_list, get_template_detail,
    search_templates, get_templates_by_tag, export_template_to_json,
    export_all_templates_to_json, import_template_from_json, create_custom_template
)
from db import db
import json
from datetime import datetime

# 创建回测模块蓝图
backtest_bp = Blueprint('backtest', __name__)


@backtest_bp.route('/')
def backtest_index():
    """回测首页"""
    # 获取可用策略列表
    strategies = [
        {'id': 'ma_cross', 'name': '移动平均线交叉策略', 'params': ['短期窗口', '长期窗口']},
        {'id': 'rsi', 'name': 'RSI超买超卖策略', 'params': ['周期', '超买阈值', '超卖阈值']},
        {'id': 'macd', 'name': 'MACD策略', 'params': ['快速周期', '慢速周期', '信号周期']}
    ]

    # 获取热门股票列表
    from config import HOT_STOCKS
    popular_stocks = HOT_STOCKS

    return render_template(
        'backtest.html',
        strategies=strategies,
        popular_stocks=popular_stocks
    )


@backtest_bp.route('/run', methods=['POST'])
@login_required
def run_backtest():
    """运行策略回测"""
    try:
        data = request.json

        # 获取参数
        strategy_id = data.get('strategy')
        ts_code = data.get('stock_code')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        initial_capital = float(data.get('initial_capital', 1000000))
        save_result = data.get('save_result', False)  # 是否保存结果
        
        # 日期格式转换：YYYY-MM-DD 转换为 YYYYMMDD
        if start_date and len(start_date) == 10 and start_date[4] == '-' and start_date[7] == '-':
            start_date = start_date.replace('-', '')
        if end_date and len(end_date) == 10 and end_date[4] == '-' and end_date[7] == '-':
            end_date = end_date.replace('-', '')

        # 根据选择的策略创建策略实例
        if strategy_id == 'ma_cross':
            strategy = MovingAverageCrossStrategy(
                short_window=int(data.get('short_window', 10)),
                long_window=int(data.get('long_window', 30))
            )
        elif strategy_id == 'rsi':
            strategy = RSIStrategy(
                period=int(data.get('rsi_period', 14)),
                overbought=int(data.get('rsi_overbought', 70)),
                oversold=int(data.get('rsi_oversold', 30))
            )
        elif strategy_id == 'macd':
            strategy = MACDStrategy(
                fast_period=int(data.get('macd_fast', 12)),
                slow_period=int(data.get('macd_slow', 26)),
                signal_period=int(data.get('macd_signal', 9))
            )
        else:
            return jsonify({'error': '未知的策略类型'}), 400

        # 初始化回测引擎并运行
        backtest = BacktestEngine(strategy, initial_capital)
        # 从数据获取器获取数据
        from services.data_fetcher import data_fetcher
        df = data_fetcher.get_stock_data(ts_code, start_date, end_date)
        
        # 如果没有获取到数据，使用模拟数据
        if df is None or df.empty:
            current_app.logger.warning(f"没有获取到{ts_code}的实际数据，使用模拟数据进行回测")
        
        # 调用回测引擎运行回测
        result = backtest.run(ts_code, start_date, end_date)

        if not result:
            return jsonify({'error': '回测失败，没有生成结果'}), 500

        # 确保返回的数据格式与前端期望一致
        standardized_result = {
            'status': 'success',
            'message': '回测完成',
            'start_date': str(result.get('start_date', '')),
            'end_date': str(result.get('end_date', '')),
            'initial_capital': result.get('initial_capital', initial_capital),
            'final_assets': result.get('final_assets', result.get('final_capital', initial_capital)),
            'total_return': result.get('total_return', result.get('cumulative_return', 0)),
            'annual_return': result.get('annual_return', 0),
            'sharpe_ratio': result.get('sharpe_ratio', 0),
            'max_drawdown': result.get('max_drawdown', 0),
            'total_trades': result.get('total_trades', 0),
            'win_rate': result.get('win_rate', 0),
            'max_drawdown_date': str(result.get('max_drawdown_date', '')),
            'max_drawdown_days': result.get('max_drawdown_days', 0),
            'profit_month_ratio': result.get('profit_month_ratio', 0),
            'total_months': result.get('total_months', 0),
            'profit_months': result.get('profit_months', 0),
            'best_month_return': result.get('best_month_return', 0),
            'best_month_date': str(result.get('best_month_date', '')),
            'trades': [],
            'equity_data': []
        }
        
        # 处理交易记录
        if 'trades' in result and hasattr(result['trades'], 'to_dict'):
            standardized_result['trades'] = result['trades'].to_dict('records')
        elif 'trades' in result:
            standardized_result['trades'] = result['trades']
        elif 'transactions' in result:
            standardized_result['trades'] = result['transactions']
        
        # 处理净值曲线数据
        if 'equity_curve' in result and hasattr(result['equity_curve'], 'to_dict'):
            equity_data = []
            if hasattr(result['equity_curve'], 'columns') and 'date' in result['equity_curve'].columns:
                try:
                    equity_data = result['equity_curve'][['date', 'total_assets', 'cumulative_return']].to_dict('records')
                except (KeyError, AttributeError):
                    # 处理列不存在或其他错误
                    equity_data = []
            standardized_result['equity_data'] = equity_data
        elif 'equity_data' in result:
            standardized_result['equity_data'] = result['equity_data']
        elif 'history' in result:
            standardized_result['equity_data'] = result['history']
        
        # 保存回测结果到数据库
        if save_result:
            try:
                from services.models.stock import Stock
                # 获取或创建股票记录
                stock = Stock.query.filter_by(symbol=ts_code).first()
                if not stock:
                    stock = Stock(symbol=ts_code, name=ts_code, market='未知')
                    db.session.add(stock)
                    db.session.flush()
                
                # 创建回测结果记录
                backtest_result = BacktestResult(
                    user_id=current_user.id,
                    strategy_id=0,  # 临时策略ID
                    stock_id=stock.id,
                    start_date=datetime.strptime(start_date, '%Y%m%d').date() if isinstance(start_date, str) else start_date,
                    end_date=datetime.strptime(end_date, '%Y%m%d').date() if isinstance(end_date, str) else end_date,
                    total_return=standardized_result['total_return'],
                    annual_return=standardized_result['annual_return'],
                    max_drawdown=standardized_result['max_drawdown'],
                    sharpe_ratio=standardized_result['sharpe_ratio'],
                    win_rate=standardized_result['win_rate'],
                    total_trades=standardized_result['total_trades'],
                    parameters=json.dumps(data),
                    result_data=json.dumps(standardized_result)
                )
                db.session.add(backtest_result)
                db.session.commit()
                standardized_result['backtest_id'] = backtest_result.id
            except Exception as db_error:
                current_app.logger.error(f"保存回测结果失败: {str(db_error)}")
                db.session.rollback()
        
        # 确保返回标准化后的结果，而不是原始结果
        return jsonify(standardized_result)
    except Exception as e:
        current_app.logger.error(f"回测执行失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@backtest_bp.route('/strategies')
def strategy_templates():
    """策略模板页面"""
    return render_template('backtest/strategies.html')

@backtest_bp.route('/history')
def backtest_history():
    """回测历史记录页面"""
    return render_template('backtest/history.html')


@backtest_bp.route('/results/<string:backtest_id>')
def backtest_results(backtest_id):
    """回测结果详情页面"""
    # 重定向到主回测页面，因为结果详情页面模板未实现
    return redirect(url_for('backtest.backtest_index'))


# ========== 用户策略管理API ==========

@backtest_bp.route('/api/strategies', methods=['GET'])
@login_required
def get_strategies():
    """获取用户的所有策略"""
    try:
        strategies = StrategyModel.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            'success': True,
            'strategies': [{
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'type': s.type,
                'code': s.code,
                'parameters': s.parameters,
                'is_active': s.is_active,
                'created_at': s.created_at.isoformat() if s.created_at else None
            } for s in strategies]
        })
    except Exception as e:
        current_app.logger.error(f"获取策略失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/strategies', methods=['POST'])
@login_required
def create_strategy():
    """创建新策略"""
    try:
        data = request.json
        name = data.get('name')
        strategy_type = data.get('type')
        description = data.get('description', '')
        parameters = data.get('parameters', '{}')
        
        if not name or not strategy_type:
            return jsonify({'success': False, 'error': '策略名称和类型不能为空'}), 400
        
        # 检查策略名称是否已存在
        existing = StrategyModel.query.filter_by(name=name, user_id=current_user.id).first()
        if existing:
            return jsonify({'success': False, 'error': '策略名称已存在'}), 400
        
        strategy = StrategyModel(
            user_id=current_user.id,
            name=name,
            type=strategy_type,
            description=description,
            parameters=json.dumps(parameters) if isinstance(parameters, dict) else parameters
        )
        db.session.add(strategy)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'strategy_id': strategy.id,
            'message': '策略创建成功'
        })
    except Exception as e:
        current_app.logger.error(f"创建策略失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/strategies/<int:strategy_id>', methods=['GET'])
@login_required
def get_strategy(strategy_id):
    """获取指定策略"""
    try:
        strategy = StrategyModel.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strategy:
            return jsonify({'success': False, 'error': '策略不存在'}), 404
        
        return jsonify({
            'success': True,
            'strategy': {
                'id': strategy.id,
                'name': strategy.name,
                'description': strategy.description,
                'type': strategy.type,
                'code': strategy.code,
                'parameters': strategy.parameters,
                'is_active': strategy.is_active,
                'created_at': strategy.created_at.isoformat() if strategy.created_at else None
            }
        })
    except Exception as e:
        current_app.logger.error(f"获取策略失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/strategies/<int:strategy_id>', methods=['PUT'])
@login_required
def update_strategy(strategy_id):
    """更新策略"""
    try:
        strategy = StrategyModel.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strategy:
            return jsonify({'success': False, 'error': '策略不存在'}), 404
        
        data = request.json
        
        if 'name' in data:
            # 检查新名称是否与其他策略冲突
            existing = StrategyModel.query.filter_by(name=data['name'], user_id=current_user.id).first()
            if existing and existing.id != strategy_id:
                return jsonify({'success': False, 'error': '策略名称已存在'}), 400
            strategy.name = data['name']
        
        if 'description' in data:
            strategy.description = data['description']
        if 'type' in data:
            strategy.type = data['type']
        if 'code' in data:
            strategy.code = data['code']
        if 'parameters' in data:
            strategy.parameters = json.dumps(data['parameters']) if isinstance(data['parameters'], dict) else data['parameters']
        if 'is_active' in data:
            strategy.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '策略更新成功'
        })
    except Exception as e:
        current_app.logger.error(f"更新策略失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/strategies/<int:strategy_id>', methods=['DELETE'])
@login_required
def delete_strategy(strategy_id):
    """删除策略"""
    try:
        strategy = StrategyModel.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strategy:
            return jsonify({'success': False, 'error': '策略不存在'}), 404
        
        db.session.delete(strategy)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '策略删除成功'
        })
    except Exception as e:
        current_app.logger.error(f"删除策略失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 回测历史记录API ==========

@backtest_bp.route('/api/history', methods=['GET'])
@login_required
def get_backtest_history():
    """获取用户的回测历史"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 只查询当前用户的回测结果
        query = BacktestResult.query.filter_by(user_id=current_user.id)
        
        # 按时间倒序排列
        query = query.order_by(BacktestResult.created_at.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        results = []
        for r in pagination.items:
            result_data = json.loads(r.result_data) if r.result_data else {}
            results.append({
                'id': r.id,
                'strategy_name': r.strategy.name if r.strategy else '未知策略',
                'stock_symbol': r.stock.symbol if r.stock else '未知股票',
                'start_date': r.start_date.isoformat() if r.start_date else None,
                'end_date': r.end_date.isoformat() if r.end_date else None,
                'total_return': r.total_return,
                'annual_return': r.annual_return,
                'max_drawdown': r.max_drawdown,
                'sharpe_ratio': r.sharpe_ratio,
                'win_rate': r.win_rate,
                'total_trades': r.total_trades,
                'created_at': r.created_at.isoformat() if r.created_at else None
            })
        
        return jsonify({
            'success': True,
            'history': results,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
    except Exception as e:
        current_app.logger.error(f"获取回测历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/history/<int:backtest_id>', methods=['GET'])
@login_required
def get_backtest_detail(backtest_id):
    """获取回测结果详情"""
    try:
        result = BacktestResult.query.filter_by(id=backtest_id, user_id=current_user.id).first()
        if not result:
            return jsonify({'success': False, 'error': '回测结果不存在'}), 404
        
        result_data = json.loads(result.result_data) if result.result_data else {}
        
        return jsonify({
            'success': True,
            'backtest': {
                'id': result.id,
                'strategy_name': result.strategy.name if result.strategy else '未知策略',
                'stock_symbol': result.stock.symbol if result.stock else '未知股票',
                'stock_name': result.stock.name if result.stock else '未知股票',
                'start_date': result.start_date.isoformat() if result.start_date else None,
                'end_date': result.end_date.isoformat() if result.end_date else None,
                'total_return': result.total_return,
                'annual_return': result.annual_return,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'win_rate': result.win_rate,
                'total_trades': result.total_trades,
                'parameters': result.parameters,
                'result_data': result_data,
                'created_at': result.created_at.isoformat() if result.created_at else None
            }
        })
    except Exception as e:
        current_app.logger.error(f"获取回测详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/history/<int:backtest_id>', methods=['DELETE'])
@login_required
def delete_backtest_result(backtest_id):
    """删除回测结果"""
    try:
        result = BacktestResult.query.filter_by(id=backtest_id, user_id=current_user.id).first()
        if not result:
            return jsonify({'success': False, 'error': '回测结果不存在'}), 404
        
        db.session.delete(result)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '回测结果删除成功'
        })
    except Exception as e:
        current_app.logger.error(f"删除回测结果失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 策略模板API ==========

@backtest_bp.route('/api/templates', methods=['GET'])
def get_strategy_templates():
    """获取所有策略模板列表"""
    try:
        templates = get_template_list()
        return jsonify({
            'success': True,
            'templates': templates,
            'total': len(templates)
        })
    except Exception as e:
        current_app.logger.error(f"获取策略模板失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/templates/<string:template_id>', methods=['GET'])
def get_strategy_template(template_id):
    """获取指定策略模板详情"""
    try:
        template = get_template_detail(template_id)
        if not template:
            return jsonify({'success': False, 'error': '模板不存在'}), 404
        
        return jsonify({
            'success': True,
            'template': template
        })
    except Exception as e:
        current_app.logger.error(f"获取策略模板详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/templates/search', methods=['GET'])
def search_strategy_templates():
    """搜索策略模板"""
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({'success': False, 'error': '关键词不能为空'}), 400
        
        templates = search_templates(keyword)
        return jsonify({
            'success': True,
            'templates': [t.to_dict() for t in templates],
            'total': len(templates)
        })
    except Exception as e:
        current_app.logger.error(f"搜索策略模板失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/templates/tag/<string:tag>', methods=['GET'])
def get_templates_by_tag_route(tag):
    """根据标签获取策略模板"""
    try:
        templates = get_templates_by_tag(tag)
        return jsonify({
            'success': True,
            'templates': [t.to_dict() for t in templates],
            'total': len(templates)
        })
    except Exception as e:
        current_app.logger.error(f"获取标签模板失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/templates/<string:template_id>/export', methods=['GET'])
def export_template(template_id):
    """导出指定模板为JSON"""
    try:
        json_str = export_template_to_json(template_id)
        if not json_str:
            return jsonify({'success': False, 'error': '模板不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': json.loads(json_str)
        })
    except Exception as e:
        current_app.logger.error(f"导出模板失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/templates/export/all', methods=['GET'])
def export_all_templates():
    """导出所有模板为JSON"""
    try:
        json_str = export_all_templates_to_json()
        return jsonify({
            'success': True,
            'data': json.loads(json_str)
        })
    except Exception as e:
        current_app.logger.error(f"导出所有模板失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/templates/import', methods=['POST'])
def import_template():
    """从JSON导入策略模板"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请提供有效的JSON数据'}), 400
        
        json_str = json.dumps(data, ensure_ascii=False)
        template = import_template_from_json(json_str)
        
        return jsonify({
            'success': True,
            'message': '模板导入成功',
            'template': template.to_dict()
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"导入模板失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/templates/custom', methods=['POST'])
@login_required
def create_custom_strategy():
    """创建自定义策略模板"""
    try:
        data = request.json
        
        name = data.get('name')
        description = data.get('description', '')
        scenario = data.get('scenario', '')
        parameters = data.get('parameters', [])
        default_params = data.get('default_params', {})
        tags = data.get('tags', ['自定义'])
        
        if not name:
            return jsonify({'success': False, 'error': '策略名称不能为空'}), 400
        
        template = create_custom_template(
            name=name,
            description=description,
            scenario=scenario,
            parameters=parameters,
            default_params=default_params,
            tags=tags
        )
        
        return jsonify({
            'success': True,
            'message': '自定义策略创建成功',
            'template': template.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"创建自定义策略失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 策略模板页面路由 ==========

@backtest_bp.route('/strategies')
def strategies_page():
    """策略模板中心页面"""
    return render_template('strategies/templates.html')


# ========== 策略版本管理API ==========

@backtest_bp.route('/api/strategies/<int:strategy_id>/versions', methods=['GET'])
@login_required
def get_strategy_versions(strategy_id):
    """获取策略的所有版本"""
    try:
        strategy = StrategyModel.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strategy:
            return jsonify({'success': False, 'error': '策略不存在'}), 404
        
        versions = StrategyVersion.query.filter_by(strategy_id=strategy_id).order_by(StrategyVersion.version_number.desc()).all()
        
        return jsonify({
            'success': True,
            'versions': [v.to_dict() for v in versions],
            'total': len(versions)
        })
    except Exception as e:
        current_app.logger.error(f"获取策略版本失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/strategies/<int:strategy_id>/versions', methods=['POST'])
@login_required
def create_strategy_version(strategy_id):
    """创建策略新版本"""
    try:
        strategy = StrategyModel.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strategy:
            return jsonify({'success': False, 'error': '策略不存在'}), 404
        
        data = request.json
        code = data.get('code')
        parameters = data.get('parameters', '{}')
        description = data.get('description', '')
        
        if not code:
            return jsonify({'success': False, 'error': '策略代码不能为空'}), 400
        
        # 获取当前最大版本号
        latest_version = StrategyVersion.query.filter_by(strategy_id=strategy_id).order_by(StrategyVersion.version_number.desc()).first()
        new_version_number = (latest_version.version_number + 1) if latest_version else 1
        
        version = StrategyVersion(
            strategy_id=strategy_id,
            version_number=new_version_number,
            code=code,
            parameters=json.dumps(parameters) if isinstance(parameters, dict) else parameters,
            description=description,
            created_by=current_user.id
        )
        db.session.add(version)
        
        # 同时更新策略表中的最新代码和参数
        strategy.parameters = json.dumps(parameters) if isinstance(parameters, dict) else parameters
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'version': version.to_dict(),
            'message': f'版本 v{new_version_number} 创建成功'
        })
    except Exception as e:
        current_app.logger.error(f"创建策略版本失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/strategies/<int:strategy_id>/versions/<int:version_id>', methods=['GET'])
@login_required
def get_strategy_version(strategy_id, version_id):
    """获取指定策略版本"""
    try:
        strategy = StrategyModel.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strategy:
            return jsonify({'success': False, 'error': '策略不存在'}), 404
        
        version = StrategyVersion.query.filter_by(id=version_id, strategy_id=strategy_id).first()
        if not version:
            return jsonify({'success': False, 'error': '版本不存在'}), 404
        
        return jsonify({
            'success': True,
            'version': version.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"获取策略版本失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/strategies/<int:strategy_id>/versions/<int:version_id>/diff', methods=['GET'])
@login_required
def diff_strategy_versions(strategy_id, version_id):
    """比较两个策略版本的差异"""
    try:
        strategy = StrategyModel.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strategy:
            return jsonify({'success': False, 'error': '策略不存在'}), 404
        
        compare_version_id = request.args.get('compare_with')
        if not compare_version_id:
            return jsonify({'success': False, 'error': '请指定要比较的版本ID'}), 400
        
        compare_version_id = int(compare_version_id)
        
        version = StrategyVersion.query.filter_by(id=version_id, strategy_id=strategy_id).first()
        compare_version = StrategyVersion.query.filter_by(id=compare_version_id, strategy_id=strategy_id).first()
        
        if not version or not compare_version:
            return jsonify({'success': False, 'error': '版本不存在'}), 404
        
        # 确定旧版本和新版本
        if version.version_number < compare_version.version_number:
            old_version, new_version = version, compare_version
        else:
            old_version, new_version = compare_version, version
        
        diff_result = generate_diff_html(
            old_code=old_version.code,
            new_code=new_version.code,
            old_label=f'v{old_version.version_number}',
            new_label=f'v{new_version.version_number}'
        )
        
        return jsonify({
            'success': True,
            'diff': diff_result,
            'old_version': old_version.to_dict(),
            'new_version': new_version.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"版本对比失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/api/strategies/<int:strategy_id>/rollback/<int:version_id>', methods=['POST'])
@login_required
def rollback_strategy_version(strategy_id, version_id):
    """回滚策略到指定版本"""
    try:
        strategy = StrategyModel.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strategy:
            return jsonify({'success': False, 'error': '策略不存在'}), 404
        
        version = StrategyVersion.query.filter_by(id=version_id, strategy_id=strategy_id).first()
        if not version:
            return jsonify({'success': False, 'error': '版本不存在'}), 404
        
        # 创建新版本（当前版本的新备份）
        latest_version = StrategyVersion.query.filter_by(strategy_id=strategy_id).order_by(StrategyVersion.version_number.desc()).first()
        new_version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # 备份当前策略
        backup_version = StrategyVersion(
            strategy_id=strategy_id,
            version_number=new_version_number,
            code=strategy.parameters if hasattr(strategy, 'parameters') else '',
            parameters=strategy.parameters,
            description=f'回滚前备份 (回滚到 v{version.version_number} 前)',
            created_by=current_user.id
        )
        db.session.add(backup_version)
        
        # 更新策略为指定版本的内容
        # 创建新版本记录（实际上是回滚到的版本）
        rollback_version = StrategyVersion(
            strategy_id=strategy_id,
            version_number=new_version_number + 1,
            code=version.code,
            parameters=version.parameters,
            description=f'从 v{version.version_number} 回滚',
            created_by=current_user.id
        )
        db.session.add(rollback_version)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'已成功回滚到 v{version.version_number}',
            'new_version': rollback_version.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"回滚策略失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/version-history/<int:strategy_id>')
@login_required
def version_history_page(strategy_id):
    """策略版本历史页面"""
    return render_template('backtest/version_history.html')
