import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tushare as ts
import random
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import time
# 导入配置
from config import Config

# 配置日志
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """金融市场数据获取器，支持多种数据源和数据类型"""

    def __init__(self):
        """初始化数据源连接和数据库引擎"""
        try:
            # 优先使用环境变量中的 TUSHARE_TOKEN
            self.ts_token = os.environ.get('TUSHARE_TOKEN') or Config.API_KEYS.get('tushare')
            if self.ts_token:
                try:
                    # 如果 TUSHARE_TOKEN 环境变量已设置，tushare 会自动使用它
                    # 否则调用 set_token（可能需要写入 tk.csv）
                    if 'TUSHARE_TOKEN' not in os.environ:
                        ts.set_token(self.ts_token)
                    self.ts_pro = ts.pro_api()
                    logger.info("Tushare API连接成功初始化")
                except Exception as e:
                    self.ts_pro = None
                    logger.warning(f"Tushare API初始化失败: {str(e)}")
            else:
                self.ts_pro = None
                logger.warning("未配置Tushare API密钥，Tushare数据源不可用")

            # 初始化数据库连接
            try:
                self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
                logger.info("数据库引擎初始化成功")
            except Exception as e:
                self.engine = None
                logger.error(f"数据库引擎初始化失败: {str(e)}")

            # 创建数据存储目录（如果不存在）
            self._create_data_directories()
        except Exception as e:
            logger.error(f"初始化MarketDataFetcher失败: {str(e)}")
            # 确保必要的属性已初始化
            self.ts_pro = None
            self.engine = None
            
    def _create_data_directories(self):
        """创建必要的数据存储目录"""
        try:
            dirs = [
                Config.DATA_HISTORICAL_DIR,
                Config.DATA_FACTORS_DIR
            ]
            for dir_path in dirs:
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    logger.info(f"创建数据目录: {dir_path}")
        except Exception as e:
            logger.error(f"创建数据目录失败: {str(e)}")

    def _retry_on_error(self, func, max_retries=3, delay=2, **kwargs):
        """带重试机制的函数执行装饰器"""
        for attempt in range(max_retries):
            try:
                return func(**kwargs)
            except Exception as e:
                logger.warning(f"获取数据失败(尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))  # 指数退避
        logger.error(f"达到最大重试次数，获取数据失败")
        return None

    def get_stock_basic(self, exchange='', list_status='L'):
        """
        获取股票基本信息
        :param exchange: 交易所 SSE上交所 SZSE深交所 BSE北交所
        :param list_status: 上市状态 L上市 D退市 P暂停上市
        :return: 股票基本信息DataFrame
        """
        try:
            if not self.ts_pro:
                # 返回模拟数据
                logger.warning("返回股票基本信息的模拟数据")
                from config import HOT_STOCKS
                extra_info = {
                    '600036.SH': {'industry': '银行', 'market': '主板'},
                    '601318.SH': {'industry': '保险', 'market': '主板'},
                    '600519.SH': {'industry': '白酒', 'market': '主板'},
                    '000858.SZ': {'industry': '白酒', 'market': '主板'},
                    '000001.SZ': {'industry': '银行', 'market': '主板'},
                }
                df = pd.DataFrame([
                    {'ts_code': s['code'], 'symbol': s['code'].split('.')[0], 'name': s['name'],
                     'industry': extra_info.get(s['code'], {}).get('industry', ''),
                     'market': extra_info.get(s['code'], {}).get('market', '')}
                    for s in HOT_STOCKS
                ])
                df.attrs['is_simulated'] = True
                return df

            def fetch_data():
                df = self.ts_pro.stock_basic(
                    exchange=exchange,
                    list_status=list_status,
                    fields='ts_code,symbol,name,area,industry,market,list_date,delist_date'
                )
                # 数据清洗
                if not df.empty:
                    df['list_date'] = pd.to_datetime(df['list_date'])
                    if 'delist_date' in df.columns:
                        df['delist_date'] = pd.to_datetime(df['delist_date'])
                    # 保存到数据库
                    if self.engine:
                        try:
                            df.to_sql('stock_basic', self.engine, if_exists='replace', index=False)
                        except Exception as e:
                            logger.warning(f"保存股票基本信息到数据库失败: {str(e)}")
                    logger.info(f"获取并保存股票基本信息 {len(df)} 条")
                return df

            result = self._retry_on_error(fetch_data)
            if result is None or result.empty:
                logger.warning("获取股票基本信息失败，返回模拟数据")
                return self._generate_mock_stock_basic()
            return result
        except Exception as e:
            logger.error(f"获取股票基本信息异常: {str(e)}")
            return self._generate_mock_stock_basic()
    
    def _generate_mock_stock_basic(self):
        """生成模拟的股票基本信息"""
        from config import HOT_STOCKS
        extra_info = {
            '600036.SH': {'area': '上海', 'industry': '银行', 'market': '主板', 'list_date': '20020409'},
            '601318.SH': {'area': '深圳', 'industry': '保险', 'market': '主板', 'list_date': '20070301'},
            '600519.SH': {'area': '贵州', 'industry': '白酒', 'market': '主板', 'list_date': '20010827'},
            '000858.SZ': {'area': '四川', 'industry': '白酒', 'market': '主板', 'list_date': '19980427'},
            '000001.SZ': {'area': '深圳', 'industry': '银行', 'market': '主板', 'list_date': '19910403'}
        }
        df = pd.DataFrame([
            {'ts_code': s['code'], 'symbol': s['code'].split('.')[0], 'name': s['name'],
             'area': extra_info.get(s['code'], {}).get('area', ''),
             'industry': extra_info.get(s['code'], {}).get('industry', ''),
             'market': extra_info.get(s['code'], {}).get('market', ''),
             'list_date': extra_info.get(s['code'], {}).get('list_date', '')}
            for s in HOT_STOCKS
        ])
        df.attrs['is_simulated'] = True
        return df

    def get_stock_daily(self, ts_code, start_date=None, end_date=None, adjust='qfq'):
        """
        获取股票日线数据
        :param ts_code: 股票代码 如 600000.SH
        :param start_date: 开始日期 格式 YYYYMMDD
        :param end_date: 结束日期 格式 YYYYMMDD
        :param adjust: 复权类型 qfq前复权 hfq后复权 None不复权
        :return: 日线数据DataFrame
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            # 尝试从数据库获取
            if self.engine:
                try:
                    table_name = 'stock_daily'
                    query = "SELECT * FROM {} WHERE ts_code = ? AND trade_date >= ? AND trade_date <= ?".format(table_name)
                    df = pd.read_sql(query, self.engine, params=(ts_code, start_date, end_date))
                    if not df.empty:
                        df['trade_date'] = pd.to_datetime(df['trade_date'])
                        logger.info(f"从数据库获取股票 {ts_code} 数据 {len(df)} 条")
                        return df.sort_values('trade_date')
                except Exception as e:
                    logger.warning(f"从数据库获取股票数据失败: {str(e)}")
            
            if not self.ts_pro:
                logger.warning(f"Tushare API不可用，返回股票 {ts_code} 的模拟数据")
                return self._generate_mock_stock_data(ts_code, start_date, end_date)

            def fetch_data():
                # 获取日线数据
                df = self.ts_pro.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not df.empty:
                    # 如果需要复权，获取复权因子
                    if adjust:
                        try:
                            adj_factor = self.ts_pro.adj_factor(
                                ts_code=ts_code,
                                start_date=start_date,
                                end_date=end_date
                            )
                            if not adj_factor.empty:
                                # 合并数据
                                df = pd.merge(df, adj_factor, on='trade_date', how='left')
                                # 应用复权
                                if adjust == 'qfq':
                                    for col in ['open', 'high', 'low', 'close']:
                                        df[col] = df[col] * df['adj_factor']
                        except Exception as e:
                            logger.warning(f"获取复权因子失败: {str(e)}")
                    
                    # 数据处理
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    # 保存到数据库
                    if self.engine:
                        try:
                            df.to_sql('stock_daily', self.engine, if_exists='append', index=False)
                        except Exception as e:
                            logger.warning(f"保存股票数据到数据库失败: {str(e)}")
                    logger.info(f"获取并保存股票 {ts_code} 日线数据 {len(df)} 条")
                return df

            result = self._retry_on_error(fetch_data)
            if result is None or result.empty:
                logger.warning(f"获取股票 {ts_code} 数据失败，返回模拟数据")
                return self._generate_mock_stock_data(ts_code, start_date, end_date)
            return result
        except Exception as e:
            logger.error(f"获取股票日线数据异常: {str(e)}")
            return self._generate_mock_stock_data(ts_code, start_date, end_date)
    
    def _generate_mock_stock_data(self, ts_code, start_date, end_date):
        """生成模拟股票数据"""
        try:
            # 解析日期
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            
            # 生成日期范围
            dates = pd.date_range(start=start, end=end, freq='B')  # B表示工作日
            
            if len(dates) == 0:
                return pd.DataFrame()
            
            # 基于股票代码生成一些变化，使不同股票有不同走势
            base_price = 100 + (int(ts_code[:6]) % 100)
            volatility = 0.02
            trend = 0.0005 if int(ts_code[:2]) % 2 == 0 else -0.0003
            
            # 生成价格数据
            prices = [base_price]
            for _ in range(1, len(dates)):
                change = prices[-1] * (random.uniform(-volatility, volatility) + trend)
                new_price = max(1, prices[-1] + change)  # 确保价格不会小于1
                prices.append(new_price)
            
            # 创建DataFrame
            df = pd.DataFrame({
                'ts_code': ts_code,
                'trade_date': dates.strftime('%Y%m%d'),
                'open': [p * random.uniform(0.98, 1.02) for p in prices],
                'high': [p * random.uniform(1.0, 1.03) for p in prices],
                'low': [p * random.uniform(0.97, 1.0) for p in prices],
                'close': prices,
                'pre_close': [base_price] + prices[:-1],
                'change': [0] + [prices[i] - prices[i-1] for i in range(1, len(prices))],
                'pct_chg': [0] + [(prices[i] - prices[i-1])/prices[i-1] * 100 for i in range(1, len(prices))],
                'vol': [random.randint(500000, 2000000) for _ in prices],
                'amount': [p * random.randint(500000, 2000000) for p in prices]
            })
            
            # 确保high不小于close和open，low不大于close和open
            df['high'] = df[['high', 'open', 'close']].max(axis=1)
            df['low'] = df[['low', 'open', 'close']].min(axis=1)
            
            df.attrs['is_simulated'] = True
            return df
        except Exception as e:
            logger.error(f"生成模拟股票数据失败: {str(e)}")
            return pd.DataFrame()

    def get_market_overview(self):
        """
        获取市场概览数据
        :return: 包含市场统计信息的字典
        """
        try:
            if not self.ts_pro:
                # 返回模拟数据
                logger.warning("返回市场概览的模拟数据")
                return {
                    'is_simulated': True,
                    'sh': {'code': '000001.SH', 'name': '上证指数', 'close': 3215.68, 'change': 25.32, 'pct_chg': 0.79},
                    'sz': {'code': '399001.SZ', 'name': '深证成指', 'close': 11032.45, 'change': 189.76, 'pct_chg': 1.75},
                    'cy': {'code': '399006.SZ', 'name': '创业板指', 'close': 2256.89, 'change': 45.67, 'pct_chg': 2.07}
                }

            # 尝试获取主要指数数据
            index_data = {}
            indexes = {
                'sh': {'code': '000001.SH', 'name': '上证指数'},
                'sz': {'code': '399001.SZ', 'name': '深证成指'},
                'cy': {'code': '399006.SZ', 'name': '创业板指'}
            }
            
            for key, index_info in indexes.items():
                index_df = self.get_index_daily(index_info['code'])
                if index_df is not None and not index_df.empty:
                    latest_data = index_df.sort_values('trade_date', ascending=False).iloc[0]
                    index_data[key] = {
                        'code': index_info['code'],
                        'name': index_info['name'],
                        'close': float(latest_data['close']),
                        'change': float(latest_data.get('change', 0)),
                        'pct_chg': float(latest_data.get('pct_chg', 0))
                    }
                else:
                    # 提供默认数据
                    index_data[key] = {
                        'code': index_info['code'],
                        'name': index_info['name'],
                        'close': 1000,
                        'change': 0,
                        'pct_chg': 0
                    }
            
            return index_data
        except Exception as e:
            logger.error(f"获取市场概览异常: {str(e)}")
            # 返回默认模拟数据
            return {
                'is_simulated': True,
                'sh': {'code': '000001.SH', 'name': '上证指数', 'close': 3200.50, 'change': 15.20, 'pct_chg': 0.48},
                'sz': {'code': '399001.SZ', 'name': '深证成指', 'close': 11000.30, 'change': 120.40, 'pct_chg': 1.10},
                'cy': {'code': '399006.SZ', 'name': '创业板指', 'close': 2250.70, 'change': 35.80, 'pct_chg': 1.62}
            }

    def get_index_daily(self, ts_code, start_date=None, end_date=None):
        """
        获取指数日线数据
        :param ts_code: 指数代码 如 000001.SH
        :param start_date: 开始日期 格式 YYYYMMDD
        :param end_date: 结束日期 格式 YYYYMMDD
        :return: 指数日线数据DataFrame
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            # 尝试从数据库获取
            if self.engine:
                try:
                    table_name = 'index_daily'
                    query = "SELECT * FROM {} WHERE ts_code = ? AND trade_date >= ? AND trade_date <= ?".format(table_name)
                    df = pd.read_sql(query, self.engine, params=(ts_code, start_date, end_date))
                    if not df.empty:
                        df['trade_date'] = pd.to_datetime(df['trade_date'])
                        logger.info(f"从数据库获取指数 {ts_code} 数据 {len(df)} 条")
                        return df.sort_values('trade_date')
                except Exception as e:
                    logger.warning(f"从数据库获取指数数据失败: {str(e)}")
            
            if not self.ts_pro:
                logger.warning(f"Tushare API不可用，返回指数 {ts_code} 的模拟数据")
                return self._generate_mock_index_data(ts_code, start_date, end_date)

            def fetch_data():
                # 对于指数，tushare使用index_daily接口
                df = self.ts_pro.index_daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not df.empty:
                    # 数据处理和保存
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    # 计算涨跌幅
                    if 'close' in df.columns:
                        df = df.sort_values('trade_date')
                        df['change'] = df['close'] - df['close'].shift(1)
                        df['pct_chg'] = (df['change'] / df['close'].shift(1) * 100).fillna(0)
                    # 保存到数据库
                    if self.engine:
                        try:
                            df.to_sql('index_daily', self.engine, if_exists='append', index=False)
                        except Exception as e:
                            logger.warning(f"保存指数数据到数据库失败: {str(e)}")
                    logger.info(f"获取并保存指数 {ts_code} 日线数据 {len(df)} 条")
                return df

            result = self._retry_on_error(fetch_data)
            if result is None or result.empty:
                logger.warning(f"获取指数 {ts_code} 数据失败，返回模拟数据")
                return self._generate_mock_index_data(ts_code, start_date, end_date)
            return result
        except Exception as e:
            logger.error(f"获取指数日线数据异常: {str(e)}")
            return self._generate_mock_index_data(ts_code, start_date, end_date)
    
    def _generate_mock_index_data(self, ts_code, start_date, end_date):
        """生成模拟指数数据"""
        try:
            # 解析日期
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            
            # 生成日期范围
            dates = pd.date_range(start=start, end=end, freq='B')
            
            if len(dates) == 0:
                return pd.DataFrame()
            
            # 为不同指数设置不同的基准值
            index_baselines = {
                '000001.SH': 3200,  # 上证指数
                '399001.SZ': 11000,  # 深证成指
                '399006.SZ': 2200    # 创业板指
            }
            
            base_price = index_baselines.get(ts_code, 1000)
            volatility = 0.015
            trend = 0.0002
            
            # 生成价格数据
            prices = [base_price]
            for _ in range(1, len(dates)):
                change = prices[-1] * (random.uniform(-volatility, volatility) + trend)
                new_price = max(1, prices[-1] + change)
                prices.append(new_price)
            
            # 创建DataFrame
            df = pd.DataFrame({
                'ts_code': ts_code,
                'trade_date': dates.strftime('%Y%m%d'),
                'open': [p * random.uniform(0.995, 1.005) for p in prices],
                'high': [p * random.uniform(1.0, 1.01) for p in prices],
                'low': [p * random.uniform(0.99, 1.0) for p in prices],
                'close': prices,
                'pre_close': [base_price] + prices[:-1],
                'change': [0] + [prices[i] - prices[i-1] for i in range(1, len(prices))],
                'pct_chg': [0] + [(prices[i] - prices[i-1])/prices[i-1] * 100 for i in range(1, len(prices))],
                'vol': [random.randint(1000000, 5000000) for _ in prices],
                'amount': [p * random.randint(1000000, 5000000) for p in prices]
            })
            
            # 确保high不小于close和open，low不大于close和open（指数数据）
            df['high'] = df[['high', 'open', 'close']].max(axis=1)
            df['low'] = df[['low', 'open', 'close']].min(axis=1)
            
            df.attrs['is_simulated'] = True
            return df
        except Exception as e:
            logger.error(f"生成模拟指数数据失败: {str(e)}")
            return pd.DataFrame()

    def get_index_data(self, ts_code, start_date=None, end_date=None):
        """
        获取指数日线数据（兼容方法）
        :param ts_code: 指数代码 如 000300.SH
        :param start_date: 开始日期 格式 YYYYMMDD
        :param end_date: 结束日期 格式 YYYYMMDD
        :return: 指数日线数据DataFrame
        """
        # 直接调用get_index_daily，保持兼容性
        return self.get_index_daily(ts_code, start_date, end_date)

    def get_stock_data(self, ts_code, start_date=None, end_date=None):
        """
        获取股票数据（兼容旧接口）
        :param ts_code: 股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 股票数据DataFrame
        """
        return self.get_stock_daily(ts_code, start_date, end_date)

# 创建全局data_fetcher实例，供其他模块导入使用
data_fetcher = MarketDataFetcher()

# 测试代码移到__main__块中，避免模块导入时自动执行
if __name__ == "__main__":
    # 初始化测试实例
    fetcher = MarketDataFetcher()
    
    # 获取主要指数数据
    fetcher.get_index_daily('000001.SH')  # 上证指数
    fetcher.get_index_daily('399001.SZ')  # 深证成指

    # 获取市场概览
    overview = fetcher.get_market_overview()
    if overview:
        logger.info(f"市场概览: {overview}")
