# -*- coding: utf-8 -*-
# 添加sys模块和路径配置
import os
import sys

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到Python路径中
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 加载 .env 文件（如果存在）
env_path = os.path.join(current_dir, '.env')
if os.path.exists(env_path):
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        # 设置 TUSHARE_TOKEN 环境变量，避免 Tushare SDK 写入 tk.csv
        if 'TUSHARE_API_KEY' in os.environ and 'TUSHARE_TOKEN' not in os.environ:
            os.environ['TUSHARE_TOKEN'] = os.environ.get('TUSHARE_API_KEY', '')
        print(f"已从 .env 文件加载环境变量")
    except ImportError:
        print("python-dotenv 未安装，将从系统环境变量读取配置")

from flask import Flask, render_template, jsonify, current_app, request
from flask_caching import Cache
from flask_migrate import Migrate
from flask_login import LoginManager, login_required
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler

# 导入配置
from config import Config

# 从db.py文件导入db对象，避免循环导入
try:
    from db import db
except ImportError:
    # 如果直接导入失败，尝试从当前目录导入
    sys.path.insert(0, current_dir)
    from db import db

# 初始化其他扩展（先于蓝图导入，避免循环引用）
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # 设置登录视图
login_manager.login_message_category = 'info'  # 设置登录消息类别

# CSRF保护已禁用（本地部署）
# from flask_wtf.csrf import CSRFProtect
# csrf = CSRFProtect()


def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app, config={'CACHE_TYPE': 'simple'})
    login_manager.init_app(app)
    # csrf.init_app(app)  # CSRF已禁用
    
    # 将缓存实例绑定到应用对象上
    app.cache = cache
    
    # 注册用户加载回调
    from services.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 配置日志
    configure_logging(app)

    # 根路由
    @app.route('/')
    def index():
        """平台首页"""
        return render_template('index.html')

    # 注册蓝图（延迟导入，避免循环引用）
    register_blueprints(app)

    # 创建数据目录
    create_directories(app)

    # 注册错误处理程序
    register_error_handlers(app)

    # 应用启动时的操作
    with app.app_context():
        # 导入所有模型，确保创建所有数据表
        from services.models.user import User
        from services.models.stock import Stock, StockPrice, Strategy, BacktestResult, SystemConfig
        from services.models.notification import Notification
        from services.models.feedback import Feedback
        from services.models.community import StrategyShare, Comment, Like
        from services.models.strategy_version import StrategyVersion
        from services.models.operation_log import OperationLog
        from services.models.site_content import SiteContent, init_default_content
        # 创建数据库表
        db.create_all()
        # 初始化默认站点内容
        init_default_content()
        # 初始化缓存
        init_cache()

    return app


def register_blueprints(app):
    """注册蓝图（单独提取方法，便于管理）"""
    try:
        # 导入并注册各个蓝图
        from services.routes.main import main_bp
        from services.routes.data import data_bp
        from services.routes.backtest import backtest_bp
        from services.routes.models import models_bp
        from services.routes.analysis import analysis_bp
        from services.routes.api import api_bp
        from services.routes.notifications import notifications_bp
        from services.routes.ml_prediction import ml_prediction_bp
        from services.auth import auth_bp
        
        # 注册蓝图
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(data_bp, url_prefix='/data')
        app.register_blueprint(backtest_bp, url_prefix='/backtest')
        app.register_blueprint(models_bp, url_prefix='/models')
        app.register_blueprint(analysis_bp, url_prefix='/analysis')
        app.register_blueprint(api_bp)  # API蓝图，前缀已在蓝图中定义
        app.register_blueprint(notifications_bp)  # 通知蓝图
        app.register_blueprint(ml_prediction_bp, url_prefix='/ml')  # 机器学习预测蓝图
        
        # 尝试注册课程模块（可选）
        try:
            from services.routes.courses import courses_bp
            app.register_blueprint(courses_bp, url_prefix='/courses')
            app.logger.info("课程模块导入成功")
        except ImportError as e:
            app.logger.warning(f"课程模块导入失败: {e} - 此模块暂不影响系统运行")
        
        # 尝试注册投资组合模块（可选）
        try:
            from services.routes.portfolio import portfolio_bp
            app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
            app.logger.info("投资组合模块导入成功")
        except ImportError as e:
            app.logger.warning(f"投资组合模块导入失败: {e} - 此模块暂不影响系统运行")

        # 尝试注册风险分析模块（可选）
        try:
            from services.routes.risk_analysis import risk_analysis_bp
            app.register_blueprint(risk_analysis_bp, url_prefix='/risk_analysis')
            app.logger.info("风险分析模块导入成功")
        except ImportError as e:
            app.logger.warning(f"风险分析模块导入失败: {e} - 此模块暂不影响系统运行")

        # 尝试注册反馈模块（可选）
        try:
            from services.routes.feedback import feedback_bp
            app.register_blueprint(feedback_bp, url_prefix='/feedback')
            app.logger.info("反馈模块导入成功")
        except ImportError as e:
            app.logger.warning(f"反馈模块导入失败: {e} - 此模块暂不影响系统运行")
        
        # 尝试注册知识库模块（可选）
        try:
            from services.routes.knowledge import knowledge_bp
            app.register_blueprint(knowledge_bp, url_prefix='/knowledge')
            app.logger.info("知识库模块导入成功")
        except ImportError as e:
            app.logger.warning(f"知识库模块导入失败: {e} - 此模块暂不影响系统运行")
            
        # 尝试注册多因子分析模块（可选）
        try:
            from services.routes.multi_factor import multi_factor_bp
            app.register_blueprint(multi_factor_bp, url_prefix='/multi_factor')
            app.logger.info("多因子分析模块导入成功")
        except ImportError as e:
            app.logger.warning(f"多因子分析模块导入失败: {e} - 此模块暂不影响系统运行")
        
        # 尝试注册导出模块（可选）
        try:
            from services.routes.export import export_bp
            app.register_blueprint(export_bp, url_prefix='/api/export')
            app.logger.info("导出模块导入成功")
        except ImportError as e:
            app.logger.warning(f"导出模块导入失败: {e} - 此模块暂不影响系统运行")

        # 尝试注册社区模块（可选）
        try:
            from services.routes.community import community_bp
            app.register_blueprint(community_bp)
            app.logger.info("社区模块导入成功")
        except ImportError as e:
            app.logger.warning(f"社区模块导入失败: {e} - 此模块暂不影响系统运行")

        # 尝试注册站点内容管理 API（可选）
        try:
            from services.routes.site_content_api import site_content_api_bp
            app.register_blueprint(site_content_api_bp)
            app.logger.info("站点内容管理 API 导入成功")
        except ImportError as e:
            app.logger.warning(f"站点内容管理 API 导入失败: {e} - 此模块暂不影响系统运行")
        
        app.logger.info("所有可用蓝图注册成功")
    except ImportError as e:
        app.logger.error(f"关键蓝图导入失败: {e}")
        raise


def configure_logging(app):
    """配置日志系统"""
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # 修改日志配置，避免文件权限问题
    file_handler = RotatingFileHandler(
        'logs/quant_platform.log', maxBytes=10*1024*1024, backupCount=5,
        mode='a', encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Quant Finance Platform startup')


def create_directories(app):
    """创建必要的数据目录"""
    # 确保配置中存在这些目录定义
    required_dirs = [
        'DATA_HISTORICAL_DIR',
        'DATA_FACTORS_DIR',
        'PLOTS_DIR',
        'BACKTEST_RESULTS_DIR'
    ]

    # 从配置中获取目录路径并创建
    for dir_key in required_dirs:
        if hasattr(app.config, dir_key):
            dir_path = app.config[dir_key]
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                app.logger.info(f"创建目录: {dir_path}")


def register_error_handlers(app):
    """注册错误处理程序"""

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403


def init_cache():
    """初始化缓存数据"""
    try:
        # 修复导入路径，使用之前定义的DataFetcher
        from services.data_fetcher import data_fetcher
        from flask import current_app
        
        # 确保使用current_app.cache而不是全局cache对象
        # 缓存市场概览数据
        market_overview = data_fetcher.get_market_overview()  # 获取市场概览字典
        # 直接使用绑定到app的缓存实例
        current_app.cache.set('market_overview', market_overview, timeout=3600)  # 缓存1小时
        current_app.logger.info("市场概览数据已缓存")

        # 缓存策略模板
        from services.strategy_templates import get_all_templates
        current_app.cache.set('strategy_templates', get_all_templates(), timeout=3600)

        # 缓存知识库数据
        from services import knowledge_base as kb
        current_app.cache.set('knowledge_base', {
            'tutorials': kb.TUTORIALS,
            'indicators': kb.INDICATORS,
            'strategies': kb.STRATEGIES,
            'risk_warnings': kb.RISK_WARNINGS,
            'faq': kb.FAQ_DATA
        }, timeout=3600)
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"初始化缓存失败: {str(e)}")


# 创建应用实例 - 通过环境变量控制配置
from config import config
config_name = os.environ.get('FLASK_CONFIG') or 'development'
app = create_app(config[config_name])

# 添加路由访问日志记录
@app.before_request
def log_request():
    if request.path.startswith('/static/'):
        return
    app.logger.info(f"Request: {request.method} {request.url}")


# 健康检查路由
@app.route('/health')
def health_check():
    """应用健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


if __name__ == '__main__':
    # 使用配置中的参数启动应用
    app.run(
        debug=app.config.get('DEBUG', False),
        port=app.config.get('PORT', 5000),
        host=app.config.get('HOST', '127.0.0.1'),
        use_reloader=app.config.get('DEBUG', False)
    )
