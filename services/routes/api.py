# -*- coding: utf-8 -*-
"""
API接口模块
"""
import os
import sys

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到Python路径中
project_dir = os.path.abspath(os.path.join(current_dir, '../../'))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import jwt
import json
import logging
from datetime import datetime, timedelta
from services.models.user import User
from services.analyzer import financial_analyzer
from services.ai_service import get_ai_service
from services.backtest import MovingAverageCrossStrategy, RSIStrategy, MACDStrategy, BollingerBandsStrategy, KDJStrategy, CCIStrategy, BacktestEngine
from db import db

# 创建API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# JWT配置
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    JWT_SECRET_KEY = 'dev-jwt-key-for-education'  # 仅开发环境使用的回退密钥
JWT_EXPIRATION_DELTA = timedelta(days=7)


def generate_token(user_id):
    """
    生成JWT令牌
    :param user_id: 用户ID
    :return: JWT令牌
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
    return token


def verify_token(token):
    """
    验证JWT令牌
    :param token: JWT令牌
    :return: 令牌有效返回用户ID，无效返回None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """
    API登录接口
    :return: JWT令牌和用户信息
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少请求数据'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    # 查找用户
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 检查用户是否被锁定
    if user.is_locked:
        return jsonify({'error': '账户已被锁定，请15分钟后再试'}), 403
    
    # 生成JWT令牌
    token = generate_token(user.id)
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    user.reset_login_attempts()
    db.session.commit()
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
    }), 200


@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    """
    API注册接口
    :return: 注册结果
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少请求数据'}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': '用户名、邮箱和密码不能为空'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已存在'}), 400
    
    # 创建新用户
    user = User(username=username, email=email)
    user.set_password(password)
    
    # 保存用户到数据库
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': '注册成功，请登录'}), 201


@api_bp.route('/auth/me', methods=['GET'])
def api_get_me():
    """
    获取当前用户信息
    :return: 用户信息
    """
    # 从请求头获取令牌
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': '缺少Authorization头'}), 401
    
    # 提取令牌
    token_parts = auth_header.split()
    if len(token_parts) != 2 or token_parts[0].lower() != 'bearer':
        return jsonify({'error': 'Authorization头格式错误'}), 401
    
    token = token_parts[1]
    user_id = verify_token(token)
    
    if not user_id:
        return jsonify({'error': '无效或过期的令牌'}), 401
    
    # 查找用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat()
        }
    }), 200


@api_bp.route('/data/stock/<ts_code>', methods=['GET'])
def api_get_stock_data(ts_code):
    """
    获取股票数据
    :param ts_code: 股票代码
    :return: 股票数据
    """
    # 从请求参数获取日期范围
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 获取股票数据
    try:
        df = financial_analyzer.get_stock_data(ts_code, start_date, end_date)
        if df is None or df.empty:
            return jsonify({'error': '无法获取股票数据'}), 404
        
        # 转换为字典列表
        data = df.to_dict('records')
        
        return jsonify({
            'stock_code': ts_code,
            'data': data,
            'count': len(data)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/data/stock/<ts_code>/indicators', methods=['GET'])
def api_get_stock_indicators(ts_code):
    """
    获取股票技术指标
    :param ts_code: 股票代码
    :return: 股票技术指标
    """
    # 从请求参数获取日期范围
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        # 获取股票数据
        df = financial_analyzer.get_stock_data(ts_code, start_date, end_date)
        if df is None or df.empty:
            return jsonify({'error': '无法获取股票数据'}), 404
        
        # 计算技术指标
        df_with_indicators = financial_analyzer.calculate_technical_indicators(df)
        if df_with_indicators is None:
            return jsonify({'error': '无法计算技术指标'}), 500
        
        # 转换为字典列表
        data = df_with_indicators.to_dict('records')
        
        return jsonify({
            'stock_code': ts_code,
            'data': data,
            'count': len(data)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/backtest/run', methods=['POST'])
def api_run_backtest():
    """
    运行策略回测
    :return: 回测结果
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少请求数据'}), 400
    
    ts_code = data.get('stock_code')
    strategy_name = data.get('strategy')
    parameters = data.get('parameters', {})
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    initial_capital = data.get('initial_capital', 1000000)
    
    if not ts_code or not strategy_name:
        return jsonify({'error': '股票代码和策略名称不能为空'}), 400
    
    try:
        # 创建策略实例
        if strategy_name == 'ma_cross':
            short_window = parameters.get('short_window', 10)
            long_window = parameters.get('long_window', 30)
            strategy = MovingAverageCrossStrategy(short_window=short_window, long_window=long_window)
        elif strategy_name == 'rsi':
            period = parameters.get('period', 14)
            overbought = parameters.get('overbought', 70)
            oversold = parameters.get('oversold', 30)
            strategy = RSIStrategy(period=period, overbought=overbought, oversold=oversold)
        elif strategy_name == 'macd':
            fast_period = parameters.get('fast_period', 12)
            slow_period = parameters.get('slow_period', 26)
            signal_period = parameters.get('signal_period', 9)
            strategy = MACDStrategy(fast_period=fast_period, slow_period=slow_period, signal_period=signal_period)
        elif strategy_name == 'bollinger':
            period = parameters.get('period', 20)
            num_std = parameters.get('num_std', 2)
            strategy = BollingerBandsStrategy(period=period, num_std=num_std)
        elif strategy_name == 'kdj':
            period = parameters.get('period', 9)
            k_period = parameters.get('k_period', 3)
            d_period = parameters.get('d_period', 3)
            strategy = KDJStrategy(period=period, k_period=k_period, d_period=d_period)
        elif strategy_name == 'cci':
            period = parameters.get('period', 14)
            strategy = CCIStrategy(period=period)
        else:
            return jsonify({'error': '不支持的策略类型'}), 400
        
        # 创建回测引擎并运行回测
        backtest = BacktestEngine(strategy, initial_capital=initial_capital)
        result = backtest.run(ts_code, start_date, end_date)
        
        if result is None:
            return jsonify({'error': '回测失败'}), 500
        
        # 转换回测结果
        trades = result['trades'].to_dict('records') if not result['trades'].empty else []
        equity_curve = result['equity_curve'].to_dict('records')
        
        return jsonify({
            'strategy': strategy.get_name(),
            'stock_code': ts_code,
            'start_date': result['start_date'].isoformat() if hasattr(result['start_date'], 'isoformat') else str(result['start_date']),
            'end_date': result['end_date'].isoformat() if hasattr(result['end_date'], 'isoformat') else str(result['end_date']),
            'total_return': result['total_return'],
            'annual_return': result['annual_return'],
            'sharpe_ratio': result['sharpe_ratio'],
            'max_drawdown': result['max_drawdown'],
            'max_drawdown_date': result['max_drawdown_date'].isoformat() if hasattr(result['max_drawdown_date'], 'isoformat') else str(result['max_drawdown_date']),
            'win_rate': result['win_rate'],
            'total_trades': result['total_trades'],
            'final_assets': result['final_assets'],
            'initial_capital': result['initial_capital'],
            'trades': trades,
            'equity_curve': equity_curve
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/strategies', methods=['GET'])
def api_get_strategies():
    """
    获取支持的策略列表
    :return: 策略列表
    """
    strategies = [
        {
            'name': 'ma_cross',
            'display_name': '移动平均线交叉策略',
            'description': '短期均线上穿长期均线时买入，下穿时卖出',
            'parameters': [
                {'name': 'short_window', 'type': 'integer', 'default': 10, 'description': '短期均线窗口'}, 
                {'name': 'long_window', 'type': 'integer', 'default': 30, 'description': '长期均线窗口'}
            ]
        },
        {
            'name': 'rsi',
            'display_name': 'RSI超买超卖策略',
            'description': 'RSI低于超卖阈值时买入，高于超买阈值时卖出',
            'parameters': [
                {'name': 'period', 'type': 'integer', 'default': 14, 'description': 'RSI计算周期'}, 
                {'name': 'overbought', 'type': 'integer', 'default': 70, 'description': '超买阈值'}, 
                {'name': 'oversold', 'type': 'integer', 'default': 30, 'description': '超卖阈值'}
            ]
        },
        {
            'name': 'macd',
            'display_name': 'MACD指标策略',
            'description': 'MACD线上穿信号线时买入，下穿时卖出',
            'parameters': [
                {'name': 'fast_period', 'type': 'integer', 'default': 12, 'description': '快速EMA周期'}, 
                {'name': 'slow_period', 'type': 'integer', 'default': 26, 'description': '慢速EMA周期'}, 
                {'name': 'signal_period', 'type': 'integer', 'default': 9, 'description': '信号EMA周期'}
            ]
        },
        {
            'name': 'bollinger',
            'display_name': '布林带策略',
            'description': '价格跌破下轨时买入，突破上轨时卖出',
            'parameters': [
                {'name': 'period', 'type': 'integer', 'default': 20, 'description': '计算周期'}, 
                {'name': 'num_std', 'type': 'number', 'default': 2, 'description': '标准差倍数'}
            ]
        },
        {
            'name': 'kdj',
            'display_name': 'KDJ指标策略',
            'description': 'K线下穿D线且J线低于20时买入，K线上穿D线且J线高于80时卖出',
            'parameters': [
                {'name': 'period', 'type': 'integer', 'default': 9, 'description': 'RSV计算周期'}, 
                {'name': 'k_period', 'type': 'integer', 'default': 3, 'description': 'K值计算周期'}, 
                {'name': 'd_period', 'type': 'integer', 'default': 3, 'description': 'D值计算周期'}
            ]
        },
        {
            'name': 'cci',
            'display_name': 'CCI指标策略',
            'description': 'CCI低于-100时买入，高于100时卖出',
            'parameters': [
                {'name': 'period', 'type': 'integer', 'default': 14, 'description': '计算周期'}
            ]
        }
    ]
    
    return jsonify({'strategies': strategies}), 200


@api_bp.route('/ai/chat', methods=['POST'])
def api_ai_chat():
    """
    AI 助手对话接口
    :return: AI 助手回复
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少请求数据'}), 400

    message = data.get('message')
    if not message:
        return jsonify({'error': '消息内容不能为空'}), 400

    # 获取用户ID（如果有登录）
    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.id

    try:
        ai_service = get_ai_service()
        if not ai_service.is_available():
            return jsonify({'error': 'AI 服务未配置'}), 503

        response = ai_service.chat(message, user_id=user_id)
        return jsonify({
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"AI 对话异常: {str(e)}")
        return jsonify({'error': f'AI 服务异常: {str(e)}'}), 500


@api_bp.route('/ai/clear', methods=['POST'])
def api_ai_clear():
    """
    清除 AI 对话历史
    :return: 操作结果
    """
    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.id

    try:
        ai_service = get_ai_service()
        ai_service.clear_history(user_id=user_id)
        return jsonify({'message': '对话历史已清除'}), 200
    except Exception as e:
        logger.error(f"清除对话历史异常: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ai/status', methods=['GET'])
def api_ai_status():
    """
    获取 AI 服务状态
    :return: AI 服务状态
    """
    try:
        ai_service = get_ai_service()
        return jsonify({
            'available': ai_service.is_available(),
            'model': ai_service.model if ai_service.is_available() else None
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ai/templates', methods=['GET'])
def api_ai_templates():
    """
    获取 AI 快捷问题模板
    :return: 快捷问题模板列表
    """
    try:
        ai_service = get_ai_service()
        category = request.args.get('category', None)
        templates = ai_service.get_quick_templates(category)
        return jsonify({
            'templates': templates
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ai/export', methods=['GET'])
def api_ai_export():
    """
    导出 AI 对话历史
    :return: 导出的对话内容
    """
    try:
        ai_service = get_ai_service()
        
        user_id = None
        if current_user.is_authenticated:
            user_id = current_user.id
            
        export_format = request.args.get('format', 'json')
        
        export_data = ai_service.export_conversation(user_id=user_id, format=export_format)
        
        if export_data is None:
            return jsonify({'error': '没有可导出的对话历史'}), 404
        
        if export_format == 'markdown':
            return export_data, 200, {'Content-Type': 'text/markdown; charset=utf-8'}
        else:
            return jsonify({
                'success': True,
                'format': 'json',
                'data': json.loads(export_data) if isinstance(export_data, str) else export_data
            }), 200
    except Exception as e:
        logger.error(f"导出对话历史异常: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ai/history/summary', methods=['GET'])
def api_ai_history_summary():
    """
    获取对话历史摘要
    :return: 对话统计信息
    """
    try:
        ai_service = get_ai_service()
        
        user_id = None
        if current_user.is_authenticated:
            user_id = current_user.id
            
        summary = ai_service.get_history_summary(user_id=user_id)
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ai/config', methods=['GET'])
def api_ai_config_get():
    """
    获取 AI 配置信息
    :return: AI 配置
    """
    try:
        ai_service = get_ai_service()
        return jsonify({
            'available': ai_service.is_available(),
            'model': ai_service.model,
            'temperature': 0.7,
            'max_tokens': 2048,
            'system_prompt': ai_service.system_prompt,
            'current_key': ai_service.api_key[:10] + '...' if ai_service.api_key else ''
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ai/config', methods=['POST'])
def api_ai_config_save():
    """
    保存 AI 配置（写入 .env 文件）
    :return: 操作结果
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '缺少请求数据'}), 400

        # 获取配置参数
        api_key = data.get('api_key', '')
        model = data.get('model', 'deepseek-chat')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 2048)
        system_prompt = data.get('system_prompt', '')

        # 更新 .env 文件中的 API 密钥
        if api_key and api_key.startswith('sk-'):
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith('DEEPSEEK_API_KEY='):
                        lines[i] = f'DEEPSEEK_API_KEY={api_key}\n'
                        updated = True
                        break
                
                if not updated:
                    lines.append(f'DEEPSEEK_API_KEY={api_key}\n')
                
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                # 更新环境变量
                os.environ['DEEPSEEK_API_KEY'] = api_key
                
                # 更新 AI 服务实例
                ai_service = get_ai_service()
                ai_service.api_key = api_key
                ai_service.model = model
                if system_prompt:
                    ai_service.system_prompt = system_prompt
                
                return jsonify({
                    'success': True,
                    'message': '配置已保存，请重启应用生效'
                }), 200
            else:
                return jsonify({'error': '.env 文件不存在'}), 500
        else:
            return jsonify({'error': 'API 密钥格式无效'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/health', methods=['GET'])
def api_health_check():
    """
    API健康检查
    :return: 健康状态
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'quant-finance-platform-api'
    }), 200
