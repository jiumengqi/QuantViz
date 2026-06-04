import os
import logging  # 添加缺失的logging导入


class Config:
    """基础配置类，所有环境共享的配置"""
    # 项目根目录
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # 密钥配置（生产环境应使用环境变量设置）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-education-only-not-safe'

    # SQLite数据库配置 - 避免数据库连接问题
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quant_platform.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MySQL 8.0特定配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,  # 连接超时回收，避免MySQL 8小时超时问题
        'pool_pre_ping': True,  # 连接前测试连通性
    }

    # 数据目录配置
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    DATA_HISTORICAL_DIR = os.path.join(DATA_DIR, 'historical')  # 历史数据
    DATA_FACTORS_DIR = os.path.join(DATA_DIR, 'factors')  # 因子数据
    PLOTS_DIR = os.path.join(BASE_DIR, 'static', 'plots')  # 图表存储
    BACKTEST_RESULTS_DIR = os.path.join(DATA_DIR, 'backtest_results')  # 回测结果

    # 缓存配置
    CACHE_DEFAULT_TIMEOUT = 3600  # 默认缓存1小时

    # 应用运行配置
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '127.0.0.1')
    
    # HTTPS配置
    SSL_CONTEXT = os.environ.get('SSL_CONTEXT') or None  # 生产环境应设置为('cert.pem', 'key.pem')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'  # 生产环境应设置为True
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'  # 生产环境应设置为True

    # 数据源API配置（从环境变量读取）
    TUSHARE_API_KEY = os.environ.get('TUSHARE_API_KEY')
    if not TUSHARE_API_KEY:
        raise ValueError("TUSHARE_API_KEY 未配置，请在 .env 文件中设置")
    API_KEYS = {
        'tushare': TUSHARE_API_KEY,
        'akshare': os.environ.get('AKSHARE_API_KEY') or '',
    }

    # 日志配置
    LOG_LEVEL = logging.INFO

    # 回测相关配置
    BACKTEST_INITIAL_CAPITAL = 1000000  # 回测初始资金（100万）
    BACKTEST_FEE_RATE = 0.0003  # 交易手续费率（0.03%）
    
    # CSRF保护配置 - 本地部署禁用
    WTF_CSRF_ENABLED = False


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
    # 开发环境缓存时间缩短
    CACHE_DEFAULT_TIMEOUT = 600  # 10分钟

    # 开发环境SQLite配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quant_platform_new.db')


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境应使用更安全的密钥
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # 生产环境SQLite配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quant_platform_prod.db')


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quant_platform_test.db')
    WTF_CSRF_ENABLED = False  # 测试环境关闭CSRF保护


# 配置字典，方便根据环境选择配置
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# 常用热门股票列表
HOT_STOCKS = [
    {'code': '600036.SH', 'name': '招商银行'},
    {'code': '000858.SZ', 'name': '五粮液'},
    {'code': '601318.SH', 'name': '中国平安'},
    {'code': '600519.SH', 'name': '贵州茅台'},
    {'code': '000001.SZ', 'name': '平安银行'},
]
