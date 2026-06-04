# -*- coding: utf-8 -*-
"""
股票相关数据模型
"""
import os
import sys

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到Python路径中
project_dir = os.path.abspath(os.path.join(current_dir, '../../'))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from datetime import datetime
from db import db


class Stock(db.Model):
    """股票基本信息"""
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), index=True, unique=True, nullable=False)  # 股票代码
    name = db.Column(db.String(100), nullable=False)  # 股票名称
    market = db.Column(db.String(20), nullable=False)  # 市场（沪市、深市）
    industry = db.Column(db.String(100))  # 所属行业
    sector = db.Column(db.String(100))  # 所属板块
    listing_date = db.Column(db.Date)  # 上市日期
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Stock {self.symbol}: {self.name}>'


class StockPrice(db.Model):
    """股票价格数据"""
    __tablename__ = 'stock_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open = db.Column(db.Float, nullable=False)  # 开盘价
    high = db.Column(db.Float, nullable=False)  # 最高价
    low = db.Column(db.Float, nullable=False)  # 最低价
    close = db.Column(db.Float, nullable=False)  # 收盘价
    volume = db.Column(db.BigInteger, nullable=False)  # 成交量
    amount = db.Column(db.BigInteger, nullable=False)  # 成交额
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    stock = db.relationship('Stock', backref=db.backref('prices', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('stock_id', 'date', name='_stock_date_uc'),
        db.Index('ix_stock_prices_stock_id_date', 'stock_id', 'date'),
    )
    
    def __repr__(self):
        return f'<StockPrice {self.stock.symbol} {self.date}>'


class Strategy(db.Model):
    """交易策略"""
    __tablename__ = 'strategies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 用户ID
    name = db.Column(db.String(100), unique=True, nullable=False)  # 策略名称
    description = db.Column(db.Text)  # 策略描述
    type = db.Column(db.String(50), nullable=False)  # 策略类型（均线、RSI等）
    code = db.Column(db.Text)  # 策略代码
    parameters = db.Column(db.Text)  # 策略参数
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('strategies', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Strategy {self.name}>'
    
    __table_args__ = (
        db.Index('ix_strategies_name', 'name'),
        db.Index('ix_strategies_type', 'type'),
        db.Index('ix_strategies_user_id', 'user_id'),
    )


class BacktestResult(db.Model):
    """回测结果"""
    __tablename__ = 'backtest_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 用户ID
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategies.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_return = db.Column(db.Float, nullable=False)  # 总收益率
    annual_return = db.Column(db.Float, nullable=False)  # 年化收益率
    max_drawdown = db.Column(db.Float, nullable=False)  # 最大回撤
    sharpe_ratio = db.Column(db.Float, nullable=False)  # 夏普比率
    win_rate = db.Column(db.Float, nullable=False)  # 胜率
    total_trades = db.Column(db.Integer, nullable=False)  # 总交易次数
    parameters = db.Column(db.Text)  # 回测参数
    result_data = db.Column(db.Text)  # 详细结果数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('backtest_results', lazy='dynamic'))
    strategy = db.relationship('Strategy', backref=db.backref('backtest_results', lazy='dynamic'))
    stock = db.relationship('Stock', backref=db.backref('backtest_results', lazy='dynamic'))
    
    def __repr__(self):
        return f'<BacktestResult {self.strategy.name} on {self.stock.symbol}>'
    
    __table_args__ = (
        db.Index('ix_backtest_results_strategy_id', 'strategy_id'),
        db.Index('ix_backtest_results_stock_id', 'stock_id'),
        db.Index('ix_backtest_results_date_range', 'start_date', 'end_date'),
        db.Index('ix_backtest_results_user_id', 'user_id'),
    )


class SystemConfig(db.Model):
    """系统配置"""
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)  # 配置键
    value = db.Column(db.Text, nullable=False)  # 配置值
    description = db.Column(db.String(255))  # 配置描述
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemConfig {self.key}>'


class Portfolio(db.Model):
    """投资组合"""
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 用户ID
    name = db.Column(db.String(100), nullable=False)  # 投资组合名称
    description = db.Column(db.Text)  # 投资组合描述
    risk_level = db.Column(db.String(20))  # 风险等级（低、中、高）
    initial_balance = db.Column(db.Float, default=0)  # 初始资金
    total_value = db.Column(db.Float, default=0)  # 总价值
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('portfolios', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Portfolio {self.name}>'
    
    __table_args__ = (
        db.Index('ix_portfolios_user_id', 'user_id'),
    )


class PortfolioHolding(db.Model):
    """投资组合持仓"""
    __tablename__ = 'portfolio_holdings'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)  # 股票代码
    name = db.Column(db.String(100))  # 股票名称
    quantity = db.Column(db.Float, default=0)  # 持仓数量
    avg_cost = db.Column(db.Float, default=0)  # 平均成本
    current_price = db.Column(db.Float, default=0)  # 当前价格
    market_value = db.Column(db.Float, default=0)  # 市值
    allocation = db.Column(db.Float, default=0)  # 占比
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    portfolio = db.relationship('Portfolio', backref=db.backref('holdings', lazy='dynamic'))
    
    def __repr__(self):
        return f'<PortfolioHolding {self.symbol}>'
    
    __table_args__ = (
        db.UniqueConstraint('portfolio_id', 'symbol', name='_portfolio_symbol_uc'),
        db.Index('ix_portfolio_holdings_portfolio_id', 'portfolio_id'),
    )


class Watchlist(db.Model):
    """股票观察列表"""
    __tablename__ = 'watchlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 用户ID
    symbol = db.Column(db.String(20), nullable=False)  # 股票代码
    name = db.Column(db.String(100))  # 股票名称
    exchange = db.Column(db.String(20))  # 交易所
    group_name = db.Column(db.String(50), default='默认分组')  # 分组名称
    notes = db.Column(db.Text)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('watchlists', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Watchlist {self.symbol}>'
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'symbol', name='_user_symbol_uc'),
        db.Index('ix_watchlists_user_id', 'user_id'),
        db.Index('ix_watchlists_group_name', 'user_id', 'group_name'),
    )


class UserSettings(db.Model):
    """用户偏好设置"""
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)  # 用户ID
    theme = db.Column(db.String(20), default='light')  # 主题（light/dark）
    language = db.Column(db.String(10), default='zh-CN')  # 语言
    refresh_interval = db.Column(db.Integer, default=5)  # 行情刷新频率（秒）
    default_start_date = db.Column(db.String(10), default='2020-01-01')  # 回测默认开始日期
    default_end_date = db.Column(db.String(10), default='2024-12-31')  # 回测默认结束日期
    default_initial_capital = db.Column(db.Float, default=1000000.0)  # 回测默认初始资金
    default_commission = db.Column(db.Float, default=0.0003)  # 回测默认手续费率
    notification_email = db.Column(db.Boolean, default=True)  # 邮件通知
    notification_browser = db.Column(db.Boolean, default=False)  # 浏览器通知
    favorite_indices = db.Column(db.Text)  # 收藏的指数（JSON格式）
    favorite_sectors = db.Column(db.Text)  # 关注的板块（JSON格式）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('settings', uselist=False))
    
    def __repr__(self):
        return f'<UserSettings for user {self.user_id}>'
    
    __table_args__ = (
        db.Index('ix_user_settings_user_id', 'user_id'),
    )