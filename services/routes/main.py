from flask import Blueprint, render_template, request, current_app, make_response
from datetime import datetime, timedelta
from flask_login import login_required, current_user
import json

# 创建主蓝图
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """平台首页"""
    # 获取默认日期范围
    today = datetime.now().strftime("%Y-%m-%d")
    default_start = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

    # 从缓存获取市场概览（如果有）
    from flask import current_app
    market_overview = current_app.cache.get('market_overview')

    return render_template(
        'index.html',
        today=today,
        default_start=default_start,
        market_overview=market_overview
    )


@main_bp.route('/about')
def about():
    """关于平台页面"""
    return render_template('about.html')


@main_bp.route('/features')
def features():
    """功能介绍页面"""
    return render_template('features.html')


@main_bp.route('/contact')
def contact():
    """联系我们页面"""
    return render_template('contact.html')


@main_bp.route('/api/market-status')
def market_status():
    """获取市场状态API"""
    try:
        # 模拟市场状态数据
        status = {
            'is_open': datetime.now().weekday() < 5 and 9 <= datetime.now().hour < 15,
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'next_open': "周一 09:30" if datetime.now().weekday() >= 5 else
            "今日 09:30" if datetime.now().hour < 9 else
            "明日 09:30"
        }
        return json.dumps(status)
    except Exception as e:
        current_app.logger.error(f"获取市场状态失败: {str(e)}")
        return json.dumps({'error': str(e)}), 500


@main_bp.route('/ai-assistant')
def ai_assistant():
    """AI 助手页面"""
    return render_template('ai_assistant.html')


@main_bp.route('/ai-config')
@login_required
def ai_config():
    """AI 配置页面"""
    from services.ai_service import get_ai_service
    ai_service = get_ai_service()
    return render_template('ai_config.html',
        api_available=ai_service.is_available(),
        model=ai_service.model,
        current_key=ai_service.api_key[:10] + '...' if ai_service.api_key else '',
        system_prompt=ai_service.system_prompt)


@main_bp.route('/changelog')
def changelog():
    """产品更新日志页面"""
    return render_template('changelog.html')


@main_bp.route('/debug/csrf-test', methods=['POST'])
def csrf_test():
    """CSRF测试路由"""
    test_field = request.form.get('test_field', '无内容')
    return f'<div class="p-3 bg-green-100 text-green-700 rounded">✓ CSRF测试成功！收到数据: {test_field}</div>'


@main_bp.route('/api/contact', methods=['POST'])
def submit_contact():
    """联系我们表单提交API（支持匿名提交）"""
    try:
        data = request.get_json()
        if not data:
            return json.dumps({'success': False, 'message': '无效的请求数据'}), 400, {'Content-Type': 'application/json'}

        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()

        if not name:
            return json.dumps({'success': False, 'message': '请输入您的姓名'}), 400, {'Content-Type': 'application/json'}
        if not email:
            return json.dumps({'success': False, 'message': '请输入您的邮箱'}), 400, {'Content-Type': 'application/json'}
        if not message:
            return json.dumps({'success': False, 'message': '请输入消息内容'}), 400, {'Content-Type': 'application/json'}

        # 邮箱格式验证
        import re
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return json.dumps({'success': False, 'message': '请输入有效的邮箱地址'}), 400, {'Content-Type': 'application/json'}

        from db import db
        from services.models.feedback import ContactMessage

        contact = ContactMessage(
            name=name,
            email=email,
            subject=subject or '未指定主题',
            message=message,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(contact)
        db.session.commit()

        return json.dumps({
            'success': True,
            'message': '消息发送成功！我们将尽快与您联系。'
        }), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        current_app.logger.error(f"联系表单提交失败: {str(e)}")
        return json.dumps({'success': False, 'message': f'提交失败，请稍后重试'}), 500, {'Content-Type': 'application/json'}


@main_bp.route('/api/hot-stocks')
def api_hot_stocks():
    """获取热门股票实时数据API"""
    try:
        from services.data_fetcher import data_fetcher
        from config import HOT_STOCKS
        import numpy as np
        from datetime import datetime, timedelta

        hot_codes = [s['code'] for s in HOT_STOCKS]
        hot_names = {s['code']: s['name'] for s in HOT_STOCKS}
        result = []
        is_simulated = False

        for code in hot_codes:
            try:
                df = data_fetcher.get_stock_daily(code,
                    start_date=(datetime.now() - timedelta(days=5)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d'))
                if df is not None and not df.empty:
                    df = df.sort_values('trade_date')
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    price = float(latest['close'])
                    prev_price = float(prev['close'])
                    change_pct = round((price - prev_price) / prev_price * 100, 2) if prev_price != 0 else 0
                    volume = int(float(latest.get('vol', 0)))
                    result.append({
                        'code': code,
                        'name': hot_names.get(code, code),
                        'latest_price': round(price, 2),
                        'change_pct': change_pct,
                        'volume': volume
                    })
                else:
                    result.append(_mock_hot_stock(code, hot_names.get(code, code)))
                    is_simulated = True
            except Exception:
                result.append(_mock_hot_stock(code, hot_names.get(code, code)))
                is_simulated = True

        # 检测是否是模拟数据
        if not result:
            for code in hot_codes:
                result.append(_mock_hot_stock(code, hot_names.get(code, code)))
            is_simulated = True

        response_data = {
            'stocks': result,
            'is_simulated': is_simulated
        }
        return json.dumps(response_data), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        current_app.logger.error(f"获取热门股票数据失败: {str(e)}")
        # 完全回退到模拟数据
        try:
            from config import HOT_STOCKS
            mock_data = {
                'stocks': [_mock_hot_stock(s['code'], s['name']) for s in HOT_STOCKS],
                'is_simulated': True
            }
            return json.dumps(mock_data), 200, {'Content-Type': 'application/json'}
        except Exception:
            return json.dumps({'stocks': [], 'is_simulated': True, 'error': '获取数据失败'}), 200, {'Content-Type': 'application/json'}


def _mock_hot_stock(code, name):
    """生成模拟热门股票数据"""
    import hashlib
    # 基于代码生成稳定的模拟数据
    seed = int(hashlib.md5(code.encode()).hexdigest()[:8], 16)
    mock_prices = {
        '600036.SH': 32.65, '000858.SZ': 168.50, '601318.SH': 45.80,
        '600519.SH': 1680.00, '000001.SZ': 12.34
    }
    mock_changes = {
        '600036.SH': 2.58, '000858.SZ': 1.94, '601318.SH': -0.65,
        '600519.SH': 1.54, '000001.SZ': 3.79
    }
    mock_volumes = {
        '600036.SH': 85000000, '000858.SZ': 32000000, '601318.SH': 56000000,
        '600519.SH': 12000000, '000001.SZ': 78000000
    }
    return {
        'code': code,
        'name': name,
        'latest_price': mock_prices.get(code, round(10 + seed % 50, 2)),
        'change_pct': mock_changes.get(code, round(((seed % 100) - 50) / 10, 2)),
        'volume': mock_volumes.get(code, 50000000 + seed % 50000000)
    }


@main_bp.route('/api/search')
def api_search():
    """全局搜索API"""
    query = request.args.get('q', '').strip()
    if not query:
        return json.dumps({'success': True, 'results': []}), 200, {'Content-Type': 'application/json'}

    results = []
    q_lower = query.lower()

    # 搜索策略模板
    try:
        from services.strategy_templates import STRATEGY_TEMPLATES
        for t in STRATEGY_TEMPLATES:
            if q_lower in t.name.lower() or q_lower in t.description.lower() or any(q_lower in tag.lower() for tag in (t.tags or [])):
                results.append({
                    'title': t.name,
                    'url': '/backtest/strategies',
                    'category': '策略模板',
                    'categoryIcon': 'cube',
                    'categoryColor': 'blue',
                    'subtitle': t.scenario or t.description[:50]
                })
    except ImportError:
        pass

    # 搜索知识库
    try:
        from services.knowledge_base import TUTORIALS, INDICATORS
        from services.knowledge_base import STRATEGIES as KB_STRATEGIES
        all_kb = {}
        all_kb.update(TUTORIALS)
        all_kb.update(INDICATORS)
        all_kb.update(KB_STRATEGIES)
        for key, article in all_kb.items():
            if not isinstance(article, dict):
                continue
            title = article.get('title', '')
            content = article.get('content', '')
            category = article.get('category', '')
            desc = article.get('description', '')
            if q_lower in title.lower() or q_lower in content.lower() or q_lower in category.lower() or q_lower in desc.lower():
                results.append({
                    'title': title,
                    'url': f"/knowledge/{article.get('id', key)}",
                    'category': '知识库',
                    'categoryIcon': 'book',
                    'categoryColor': 'purple',
                    'subtitle': category or desc
                })
    except ImportError:
        pass

    # 搜索内置功能页面
    fallback_pages = [
        {'title': '回测系统', 'url': '/backtest', 'category': '策略回测', 'categoryIcon': 'refresh', 'categoryColor': 'green'},
        {'title': '数据中心', 'url': '/data', 'category': '数据中心', 'categoryIcon': 'database', 'categoryColor': 'cyan'},
        {'title': '技术指标分析', 'url': '/analysis', 'category': '数据分析', 'categoryIcon': 'bar-chart', 'categoryColor': 'indigo'},
        {'title': 'Black-Scholes期权定价模型', 'url': '/models/black-scholes', 'category': '金融模型', 'categoryIcon': 'calculator', 'categoryColor': 'pink'},
        {'title': '风险价值(VaR)', 'url': '/models/var', 'category': '金融模型', 'categoryIcon': 'shield', 'categoryColor': 'red'},
        {'title': '马克维茨投资组合优化', 'url': '/models/markowitz', 'category': '金融模型', 'categoryIcon': 'pie-chart', 'categoryColor': 'orange'},
        {'title': '投资组合', 'url': '/portfolio', 'category': '投资组合', 'categoryIcon': 'briefcase', 'categoryColor': 'orange'},
        {'title': '股票数据', 'url': '/data/stock', 'category': '数据中心', 'categoryIcon': 'line-chart', 'categoryColor': 'cyan'},
        {'title': '指数数据', 'url': '/data/indexes', 'category': '数据中心', 'categoryIcon': 'area-chart', 'categoryColor': 'cyan'},
        {'title': '课程中心', 'url': '/courses', 'category': '课程实践', 'categoryIcon': 'graduation-cap', 'categoryColor': 'yellow'},
        {'title': '策略社区', 'url': '/community', 'category': '策略社区', 'categoryIcon': 'users', 'categoryColor': 'green'},
        {'title': 'AI助手', 'url': '/ai-assistant', 'category': 'AI服务', 'categoryIcon': 'android', 'categoryColor': 'blue'},
        {'title': '个人资料', 'url': '/auth/profile', 'category': '账户', 'categoryIcon': 'user', 'categoryColor': 'gray'},
        {'title': '通知中心', 'url': '/notifications', 'category': '账户', 'categoryIcon': 'bell', 'categoryColor': 'yellow'},
        {'title': '功能介绍', 'url': '/features', 'category': '关于平台', 'categoryIcon': 'star', 'categoryColor': 'orange'},
        {'title': '联系我们', 'url': '/contact', 'category': '关于平台', 'categoryIcon': 'envelope', 'categoryColor': 'blue'},
        {'title': '关于我们', 'url': '/about', 'category': '关于平台', 'categoryIcon': 'info-circle', 'categoryColor': 'indigo'},
        {'title': '创建投资组合', 'url': '/portfolio/create', 'category': '投资组合', 'categoryIcon': 'plus-circle', 'categoryColor': 'orange'},
        {'title': '市场监控', 'url': '/portfolio/market_monitor', 'category': '投资组合', 'categoryIcon': 'eye', 'categoryColor': 'orange'},
        {'title': '股票观察列表', 'url': '/portfolio/watchlist', 'category': '投资组合', 'categoryIcon': 'list', 'categoryColor': 'orange'},
        {'title': '回测历史', 'url': '/backtest/history', 'category': '策略回测', 'categoryIcon': 'history', 'categoryColor': 'green'},
        {'title': '策略模板', 'url': '/backtest/strategies', 'category': '策略回测', 'categoryIcon': 'clone', 'categoryColor': 'green'},
        {'title': '债券定价模型', 'url': '/models/bond-pricing', 'category': '金融模型', 'categoryIcon': 'money', 'categoryColor': 'pink'},
        {'title': '时间序列预测', 'url': '/models/forecasting', 'category': '金融模型', 'categoryIcon': 'line-chart', 'categoryColor': 'green'},
        {'title': '机器学习预测', 'url': '/ml', 'category': '金融模型', 'categoryIcon': 'brain', 'categoryColor': 'purple'},
        {'title': '登录', 'url': '/auth/login', 'category': '账户', 'categoryIcon': 'sign-in', 'categoryColor': 'gray'},
        {'title': '注册', 'url': '/auth/register', 'category': '账户', 'categoryIcon': 'user-plus', 'categoryColor': 'gray'},
        {'title': '更改密码', 'url': '/auth/change_password', 'category': '账户', 'categoryIcon': 'key', 'categoryColor': 'gray'},
    ]
    for page in fallback_pages:
        if q_lower in page['title'].lower() or q_lower in page['category'].lower():
            results.append(page)

    return json.dumps({
        'success': True,
        'results': results[:10],
        'query': query
    }), 200, {'Content-Type': 'application/json'}
