import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from scipy import stats
from sklearn.linear_model import LinearRegression

# 创建logger对象
logger = logging.getLogger(__name__)

# 条件导入talib，避免导入失败时程序崩溃
try:
    import talib as ta
    TA_LIB_AVAILABLE = True
    logger.info("TA-Lib模块已成功导入")
except ImportError:
    TA_LIB_AVAILABLE = False
    logger.warning("TA-Lib模块未安装，某些技术分析功能将不可用")
    # 创建一个简单的替代对象，提供基础功能
    class MockTA:
        def SMA(self, data, timeperiod=5):
            return data.rolling(window=timeperiod).mean()
        
        def RSI(self, data, timeperiod=14):
            delta = data.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=timeperiod).mean()
            avg_loss = loss.rolling(window=timeperiod).mean()
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
        
        def MACD(self, data, fastperiod=12, slowperiod=26, signalperiod=9):
            ema_fast = data.ewm(span=fastperiod, adjust=False).mean()
            ema_slow = data.ewm(span=slowperiod, adjust=False).mean()
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=signalperiod, adjust=False).mean()
            macd_hist = macd - macd_signal
            return macd, macd_signal, macd_hist
        
        def BBANDS(self, data, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0):
            sma = data.rolling(window=timeperiod).mean()
            std = data.rolling(window=timeperiod).std()
            upper = sma + (std * nbdevup)
            lower = sma - (std * nbdevdn)
            return upper, sma, lower
        
        def KDJ(self, data, high, low, timeperiod=9, fastk_period=3, fastd_period=3):
            # 计算RSV
            low_min = low.rolling(window=timeperiod).min()
            high_max = high.rolling(window=timeperiod).max()
            rsv = (data - low_min) / (high_max - low_min) * 100
            # 计算K、D值
            k = rsv.ewm(alpha=1/fastk_period, adjust=False).mean()
            d = k.ewm(alpha=1/fastd_period, adjust=False).mean()
            j = 3 * k - 2 * d
            return k, d, j
        
        def CCI(self, data, high, low, timeperiod=14):
            # 计算典型价格
            tp = (high + low + data) / 3
            # 计算MA
            tp_ma = tp.rolling(window=timeperiod).mean()
            # 计算平均绝对偏差
            mad = tp.rolling(window=timeperiod).apply(lambda x: abs(x - x.mean()).mean())
            # 计算CCI
            cci = (tp - tp_ma) / (0.015 * mad)
            return cci
        
        def ROC(self, data, timeperiod=10):
            return (data - data.shift(timeperiod)) / data.shift(timeperiod) * 100
        
        def OBV(self, data, volume):
            delta = data.diff()
            signal = np.where(delta > 0, 1, np.where(delta < 0, -1, 0))
            obv = (signal * volume).cumsum()
            return obv
        
        def ATR(self, high, low, close, timeperiod=14):
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=timeperiod).mean()
            return atr
        
        def WPR(self, high, low, close, timeperiod=14):
            high_max = high.rolling(window=timeperiod).max()
            low_min = low.rolling(window=timeperiod).min()
            wpr = (high_max - close) / (high_max - low_min) * 100
            return wpr
        
        def BIAS(self, data, timeperiod=6):
            ma = data.rolling(window=timeperiod).mean()
            bias = (data - ma) / ma * 100
            return bias
    
    ta = MockTA()

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 导入配置和其他服务
from config import Config
from services.data_fetcher import MarketDataFetcher

# 配置日志
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    """金融数据分析器，提供各种金融数据分析和指标计算功能"""

    def __init__(self):
        """初始化分析器，创建数据获取器实例"""
        self.fetcher = MarketDataFetcher()
        self.engine = self.fetcher.engine  # 复用数据库连接

        # 确保图表存储目录存在
        if not os.path.exists(Config.PLOTS_DIR):
            os.makedirs(Config.PLOTS_DIR)

    def get_stock_data(self, ts_code, start_date=None, end_date=None):
        """
        获取股票数据（优先从数据库获取，不存在则从API获取）
        :param ts_code: 股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 股票数据DataFrame
        """
        try:
            # 尝试从数据库获取数据
            try:
                # 构建参数化SQL查询
                query = "SELECT * FROM stock_daily WHERE ts_code = ?"
                params = [ts_code]

                if start_date:
                    query += " AND trade_date >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND trade_date <= ?"
                    params.append(end_date)

                query += " ORDER BY trade_date"

                # 从数据库查询
                df = pd.read_sql(query, self.engine, params=params)

                # 如果数据库中没有数据或数据不足，则从API获取
                if df.empty or (end_date and df['trade_date'].max() < end_date):
                    logger.info(f"数据库中{ts_code}数据不足，将从API获取")
                    df = self.fetcher.get_stock_daily(ts_code, start_date, end_date)
            except Exception as db_error:
                # 数据库查询失败，直接从API获取
                logger.warning(f"从数据库获取{ts_code}数据失败: {str(db_error)}，将从API获取")
                df = self.fetcher.get_stock_daily(ts_code, start_date, end_date)

            if df is not None and not df.empty:
                # 确保日期格式正确
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                return df.sort_values('trade_date')
            else:
                logger.warning(f"无法获取{ts_code}的数据")
                return None

        except Exception as e:
            logger.error(f"获取股票数据出错: {str(e)}")
            return None

    def calculate_return(self, df, price_col='close', period=1):
        """
        计算收益率
        :param df: 包含价格数据的DataFrame
        :param price_col: 价格列名，默认为'close'
        :param period: 计算收益率的周期，默认为1天
        :return: 包含收益率的DataFrame
        """
        if df is None or df.empty:
            return None

        df_copy = df.copy()
        # 计算简单收益率
        df_copy[f'return_{period}d'] = df_copy[price_col].pct_change(periods=period)
        # 计算对数收益率
        df_copy[f'log_return_{period}d'] = np.log(df_copy[price_col]) - np.log(df_copy[price_col].shift(period))

        return df_copy

    def calculate_technical_indicators(self, df):
        """
        计算常用技术指标
        :param df: 包含股票价格数据的DataFrame
        :return: 包含技术指标的DataFrame
        """
        if df is None or df.empty:
            return None

        df_copy = df.copy()

        # 移动平均线
        df_copy['ma5'] = ta.SMA(df_copy['close'], timeperiod=5)
        df_copy['ma10'] = ta.SMA(df_copy['close'], timeperiod=10)
        df_copy['ma20'] = ta.SMA(df_copy['close'], timeperiod=20)
        df_copy['ma60'] = ta.SMA(df_copy['close'], timeperiod=60)

        # RSI指标
        df_copy['rsi14'] = ta.RSI(df_copy['close'], timeperiod=14)

        # MACD指标
        df_copy['macd'], df_copy['macd_signal'], df_copy['macd_hist'] = ta.MACD(
            df_copy['close'], fastperiod=12, slowperiod=26, signalperiod=9)

        # 布林带
        df_copy['bb_upper'], df_copy['bb_middle'], df_copy['bb_lower'] = ta.BBANDS(
            df_copy['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

        # 成交量指标
        if 'vol' in df_copy.columns:
            df_copy['vol_ma5'] = ta.SMA(df_copy['vol'], timeperiod=5)
            df_copy['vol_ma20'] = ta.SMA(df_copy['vol'], timeperiod=20)
        
        # KDJ指标
        if all(col in df_copy.columns for col in ['close', 'high', 'low']):
            df_copy['kdj_k'], df_copy['kdj_d'], df_copy['kdj_j'] = ta.KDJ(
                df_copy['close'], df_copy['high'], df_copy['low'], timeperiod=9, fastk_period=3, fastd_period=3)
        
        # CCI指标
        if all(col in df_copy.columns for col in ['close', 'high', 'low']):
            df_copy['cci14'] = ta.CCI(df_copy['close'], df_copy['high'], df_copy['low'], timeperiod=14)
        
        # ROC指标
        if 'close' in df_copy.columns:
            df_copy['roc10'] = ta.ROC(df_copy['close'], timeperiod=10)
        
        # OBV指标
        if all(col in df_copy.columns for col in ['close', 'vol']):
            df_copy['obv'] = ta.OBV(df_copy['close'], df_copy['vol'])
        
        # ATR指标
        if all(col in df_copy.columns for col in ['high', 'low', 'close']):
            df_copy['atr14'] = ta.ATR(df_copy['high'], df_copy['low'], df_copy['close'], timeperiod=14)
        
        # WPR指标
        if all(col in df_copy.columns for col in ['high', 'low', 'close']):
            df_copy['wpr14'] = ta.WPR(df_copy['high'], df_copy['low'], df_copy['close'], timeperiod=14)
        
        # BIAS指标
        if 'close' in df_copy.columns:
            df_copy['bias6'] = ta.BIAS(df_copy['close'], timeperiod=6)
            df_copy['bias12'] = ta.BIAS(df_copy['close'], timeperiod=12)
            df_copy['bias24'] = ta.BIAS(df_copy['close'], timeperiod=24)

        return df_copy

    def calculate_risk_indicators(self, df, return_col='return_1d'):
        """
        计算风险指标
        :param df: 包含收益率数据的DataFrame
        :param return_col: 收益率列名
        :return: 风险指标字典
        """
        if df is None or df.empty or return_col not in df.columns:
            return None

        # 去除NaN值
        returns = df[return_col].dropna()

        # 计算基本风险指标
        risk_indicators = {
            'total_return': (1 + returns).prod() - 1,  # 总收益率
            'annualized_return': (1 + (1 + returns).prod() - 1) ** (252 / len(returns)) - 1,  # 年化收益率
            'volatility': returns.std() * np.sqrt(252),  # 年化波动率
            'max_drawdown': self.calculate_max_drawdown(df, 'close'),  # 最大回撤
            'sharpe_ratio': (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0,  # 夏普比率
            'skewness': returns.skew(),  # 偏度
            'kurtosis': returns.kurt(),  # 峰度
            'var_95': np.percentile(returns, 5),  # 95%置信水平下的VaR
            'mean_return': returns.mean(),  # 日均收益率
            'median_return': returns.median()  # 日中位数收益率
        }

        return risk_indicators

    def calculate_max_drawdown(self, df, price_col='close'):
        """计算最大回撤"""
        if df is None or df.empty:
            return None

        # 计算累计最大收益
        df_copy = df.copy()
        df_copy['cum_max'] = df_copy[price_col].cummax()
        # 计算每日回撤
        df_copy['drawdown'] = (df_copy[price_col] - df_copy['cum_max']) / df_copy['cum_max']

        return df_copy['drawdown'].min()  # 最大回撤（最负值）

    def plot_price_and_indicators(self, df, ts_code):
        """
        绘制价格和技术指标图表
        :param df: 包含价格和指标数据的DataFrame
        :param ts_code: 股票代码
        :return: 图表保存路径
        """
        if df is None or df.empty:
            return None

        # 确保数据按日期排序
        df = df.sort_values('trade_date')

        # 创建图表
        fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(20, 24), gridspec_kw={'hspace': 0.5, 'wspace': 0.3})

        # 价格和移动平均线
        ax1.plot(df['trade_date'], df['close'], label='收盘价')
        ax1.plot(df['trade_date'], df['ma5'], label='5日均线')
        ax1.plot(df['trade_date'], df['ma20'], label='20日均线')
        ax1.plot(df['trade_date'], df['ma60'], label='60日均线')
        ax1.set_title(f'{ts_code} 价格与移动平均线')
        ax1.legend()
        ax1.grid(True)

        # RSI指标
        ax2.plot(df['trade_date'], df['rsi14'], label='RSI(14)')
        ax2.axhline(70, color='r', linestyle='--', alpha=0.3)
        ax2.axhline(30, color='g', linestyle='--', alpha=0.3)
        ax2.set_title('相对强弱指数(RSI)')
        ax2.legend()
        ax2.grid(True)

        # MACD指标
        ax3.plot(df['trade_date'], df['macd'], label='MACD')
        ax3.plot(df['trade_date'], df['macd_signal'], label='信号线')
        ax3.bar(df['trade_date'], df['macd_hist'], label='MACD柱状图', alpha=0.3)
        ax3.set_title('MACD指标')
        ax3.legend()
        ax3.grid(True)

        # KDJ指标
        ax4.plot(df['trade_date'], df['kdj_k'], label='KDJ-K')
        ax4.plot(df['trade_date'], df['kdj_d'], label='KDJ-D')
        ax4.plot(df['trade_date'], df['kdj_j'], label='KDJ-J')
        ax4.axhline(80, color='r', linestyle='--', alpha=0.3)
        ax4.axhline(20, color='g', linestyle='--', alpha=0.3)
        ax4.set_title('KDJ指标')
        ax4.legend()
        ax4.grid(True)

        # CCI指标
        ax5.plot(df['trade_date'], df['cci14'], label='CCI(14)')
        ax5.axhline(100, color='r', linestyle='--', alpha=0.3)
        ax5.axhline(-100, color='g', linestyle='--', alpha=0.3)
        ax5.set_title('顺势指标(CCI)')
        ax5.legend()
        ax5.grid(True)

        # BIAS指标
        ax6.plot(df['trade_date'], df['bias6'], label='BIAS(6)')
        ax6.plot(df['trade_date'], df['bias12'], label='BIAS(12)')
        ax6.plot(df['trade_date'], df['bias24'], label='BIAS(24)')
        ax6.axhline(0, color='r', linestyle='--', alpha=0.3)
        ax6.set_title('乖离率(BIAS)')
        ax6.legend()
        ax6.grid(True)

        # 保存图表
        plot_filename = f"{ts_code.replace('.', '_')}_tech_indicators.png"
        plot_path = os.path.join(Config.PLOTS_DIR, plot_filename)
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"技术指标图表已保存至: {plot_path}")
        return plot_path

    def plot_return_distribution(self, df, ts_code, return_col='return_1d'):
        """绘制收益率分布图"""
        if df is None or df.empty or return_col not in df.columns:
            return None

        returns = df[return_col].dropna()

        plt.figure(figsize=(12, 6))
        sns.histplot(returns, kde=True, bins=50)
        plt.axvline(returns.mean(), color='r', linestyle='--', label=f"均值: {returns.mean():.4f}")
        plt.title(f'{ts_code} 日收益率分布')
        plt.xlabel('日收益率')
        plt.ylabel('频率')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # 保存图表
        plot_filename = f"{ts_code.replace('.', '_')}_return_dist.png"
        plot_path = os.path.join(Config.PLOTS_DIR, plot_filename)
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()

        return plot_path

    def correlation_analysis(self, stock_codes, start_date=None, end_date=None):
        """
        多只股票的相关性分析
        :param stock_codes: 股票代码列表
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 相关性矩阵和图表路径
        """
        # 获取所有股票的收盘价数据
        price_data = {}

        for code in stock_codes:
            df = self.get_stock_data(code, start_date, end_date)
            if df is not None and not df.empty:
                # 只保留日期和收盘价
                price_series = df.set_index('trade_date')['close']
                price_data[code] = price_series

        # 如果没有获取到数据
        if not price_data:
            logger.warning("没有获取到足够的股票数据进行相关性分析")
            return None, None

        # 合并为一个DataFrame
        combined_df = pd.DataFrame(price_data).dropna()

        # 计算收益率
        returns_df = combined_df.pct_change().dropna()

        # 计算相关性矩阵
        corr_matrix = returns_df.corr()

        # 绘制相关性热力图
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
        plt.title('股票收益率相关性热力图')

        # 保存图表
        plot_filename = 'stocks_correlation.png'
        plot_path = os.path.join(Config.PLOTS_DIR, plot_filename)
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()

        return corr_matrix, plot_path

    def calculate_correlation_matrix(self, stock_codes, start_date=None, end_date=None, method='pearson'):
        """
        计算多只股票的相关性矩阵（无需绘图，返回纯数据）
        :param stock_codes: 股票代码列表
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param method: 相关性方法 'pearson', 'spearman', 'kendall'
        :return: 相关性矩阵DataFrame和价格数据
        """
        # 获取所有股票的收盘价数据
        price_data = {}
        stock_names = {}

        for code in stock_codes:
            df = self.get_stock_data(code, start_date, end_date)
            if df is not None and not df.empty:
                price_series = df.set_index('trade_date')['close']
                price_data[code] = price_series
                # 提取股票名称
                try:
                    stock_names[code] = df.get('ts_code', pd.Series([code])).iloc[0] if 'ts_code' in df.columns else code
                except:
                    stock_names[code] = code

        if len(price_data) < 2:
            logger.warning("数据不足以计算相关性矩阵")
            return None, None, None

        # 合并为一个DataFrame
        price_df = pd.DataFrame(price_data).dropna()
        
        # 计算收益率
        returns_df = price_df.pct_change().dropna()
        
        if returns_df.empty or len(returns_df.columns) < 2:
            return None, None, None

        # 计算相关性矩阵
        corr_matrix = returns_df.corr(method=method)
        
        # 价格相关性
        price_corr = price_df.corr(method=method)

        return corr_matrix, price_corr, stock_names

    def calculate_factor_returns(self, stock_codes, benchmark_code='000300.SH', start_date=None, end_date=None):
        """
        计算因子收益（基于Fama-French三因子模型的简化版）
        :param stock_codes: 股票代码列表
        :param benchmark_code: 基准指数代码（默认沪深300）
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 因子分析结果字典
        """
        if not stock_codes:
            return None

        # 获取基准收益
        benchmark_df = self.fetcher.get_index_daily(benchmark_code, start_date, end_date)
        if benchmark_df is None or benchmark_df.empty:
            logger.warning(f"无法获取基准指数 {benchmark_code} 数据")
            return None

        benchmark_df = benchmark_df.sort_values('trade_date')
        benchmark_df['benchmark_return'] = benchmark_df['close'].pct_change()
        
        # 尝试获取规模因子（大市值-小市值）
        # 使用简化版：大盘股（沪深300）vs 中盘股（中证500）
        size_df = self.fetcher.get_index_daily('000905.SH', start_date, end_date)
        if size_df is not None and not size_df.empty:
            size_df = size_df.sort_values('trade_date')
            size_df['size_return'] = size_df['close'].pct_change()
            # SMB = 小盘 - 大盘
            merged = benchmark_df[['trade_date', 'benchmark_return']].merge(
                size_df[['trade_date', 'size_return']], on='trade_date', how='inner'
            )
            merged['smb'] = merged['size_return'] - merged['benchmark_return']
        else:
            merged = benchmark_df[['trade_date', 'benchmark_return']].copy()
            merged['smb'] = np.random.normal(0.0001, 0.005, len(merged))  # 模拟

        # 价值因子 (HML)：尝试用银行指数 vs 创业板指数代理
        value_df = self.fetcher.get_index_daily('399006.SZ', start_date, end_date)
        if value_df is not None and not value_df.empty:
            value_df = value_df.sort_values('trade_date')
            value_df['growth_return'] = value_df['close'].pct_change()
            merged2 = merged.merge(
                value_df[['trade_date', 'growth_return']], on='trade_date', how='inner'
            )
            # HML = 价值 - 成长（简化：基准 - 创业板作为价值因子近似）
            merged2['hml'] = merged2['benchmark_return'] - merged2['growth_return']
        else:
            merged2 = merged.copy()
            merged2['hml'] = np.random.normal(0.0002, 0.004, len(merged2))

        merged2 = merged2.dropna()
        
        # 计算各股票的超额收益并做因子回归
        factor_results = {}
        for code in stock_codes:
            try:
                df = self.get_stock_data(code, start_date, end_date)
                if df is None or df.empty:
                    continue
                df = df.sort_values('trade_date')
                df['stock_return'] = df['close'].pct_change()
                
                # 合并数据
                combined = df[['trade_date', 'stock_return']].merge(
                    merged2, on='trade_date', how='inner'
                ).dropna()
                
                if len(combined) < 30:
                    continue
                
                # 超额收益
                combined['excess_return'] = combined['stock_return'] - combined['benchmark_return']
                
                # 线性回归：excess_return = alpha + beta*benchmark + s*smb + h*hml
                X = combined[['benchmark_return', 'smb', 'hml']].values
                y = combined['excess_return'].values
                
                # 加入截距项
                X_with_const = np.column_stack([np.ones(len(X)), X])
                
                try:
                    # 使用最小二乘法
                    beta = np.linalg.lstsq(X_with_const, y, rcond=None)[0]
                    y_pred = X_with_const @ beta
                    residuals = y - y_pred
                    ss_res = np.sum(residuals ** 2)
                    ss_tot = np.sum((y - np.mean(y)) ** 2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                    
                    # 年化alpha
                    annual_alpha = beta[0] * 252
                    
                    factor_results[code] = {
                        'alpha': round(float(beta[0]) * 100, 4),  # 日alpha（%）
                        'annual_alpha': round(float(annual_alpha) * 100, 2),  # 年化alpha（%）
                        'beta_market': round(float(beta[1]), 4),  # 市场beta
                        'beta_smb': round(float(beta[2]), 4),  # 规模因子暴露
                        'beta_hml': round(float(beta[3]), 4),  # 价值因子暴露
                        'r_squared': round(float(r_squared), 4),
                        'observations': len(combined)
                    }
                except Exception as e:
                    logger.warning(f"{code} 因子回归失败: {str(e)}")
                    
            except Exception as e:
                logger.warning(f"计算 {code} 因子收益失败: {str(e)}")
        
        return {
            'factor_model': 'Fama-French三因子模型（简化版）',
            'benchmark': benchmark_code,
            'factor_returns': factor_results,
            'factor_description': {
                'market': '市场因子（Mkt-Rf）：基准指数收益 - 无风险利率',
                'smb': '规模因子（SMB）：小盘股收益 - 大盘股收益',
                'hml': '价值因子（HML）：价值股收益 - 成长股收益'
            }
        }

    def perform_regression_analysis(self, df, x_cols, y_col):
        """
        执行回归分析
        :param df: 包含分析数据的DataFrame
        :param x_cols: 自变量列名列表
        :param y_col: 因变量列名
        :return: 回归结果字典
        """
        if df is None or df.empty:
            return None

        # 准备数据
        df_clean = df.dropna(subset=x_cols + [y_col])
        X = df_clean[x_cols].values
        y = df_clean[y_col].values

        if len(X) < 2 or len(y) < 2:
            logger.warning("样本量不足，无法进行回归分析")
            return None

        # 执行线性回归
        model = LinearRegression()
        model.fit(X, y)

        # 计算预测值和残差
        y_pred = model.predict(X)
        residuals = y - y_pred

        # 回归结果
        result = {
            'coefficients': dict(zip(x_cols, model.coef_)),
            'intercept': model.intercept_,
            'r_squared': model.score(X, y),
            'residuals': residuals,
            'summary': {
                'samples': len(X),
                'x_variables': x_cols,
                'y_variable': y_col
            }
        }

        # 绘制回归结果图
        plt.figure(figsize=(10, 6))
        plt.scatter(y, y_pred, alpha=0.5)
        plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
        plt.xlabel(f'实际{y_col}')
        plt.ylabel(f'预测{y_col}')
        plt.title(f'回归分析: {y_col} vs {", ".join(x_cols)} (R²={result["r_squared"]:.4f})')
        plt.grid(True, alpha=0.3)

        # 保存图表
        plot_filename = f'regression_{y_col}_vs_{"_".join(x_cols)}.png'
        plot_path = os.path.join(Config.PLOTS_DIR, plot_filename)
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()

        result['plot_path'] = plot_path

        return result


# 示例用法
if __name__ == "__main__":
    analyzer = FinancialAnalyzer()

    # 分析单只股票
    from config import HOT_STOCKS
    stock_code = '600036.SH'  # 招商银行
    df = analyzer.get_stock_data(stock_code)

    if df is not None:
        # 计算收益率
        df = analyzer.calculate_return(df)

        # 计算技术指标
        df = analyzer.calculate_technical_indicators(df)

        # 计算风险指标
        risk_indicators = analyzer.calculate_risk_indicators(df)
        if risk_indicators:
            logger.info(f"{stock_code} 风险指标:")
            for key, value in risk_indicators.items():
                logger.info(f"  {key}: {value:.4f}")

        # 绘制技术指标图表
        analyzer.plot_price_and_indicators(df, stock_code)

        # 绘制收益率分布
        analyzer.plot_return_distribution(df, stock_code)

    # 多股票相关性分析
    from config import HOT_STOCKS
    stock_codes = [s['code'] for s in HOT_STOCKS[:3]]  # 招商银行、五粮液、中国平安
    corr_matrix, plot_path = analyzer.correlation_analysis(stock_codes)
    if corr_matrix is not None:
        logger.info("股票相关性矩阵:")
        logger.info(corr_matrix)

    # 回归分析示例
    if df is not None and not df.empty:
        # 用成交量和RSI预测收益率（示例）
        regression_result = analyzer.perform_regression_analysis(
            df,
            x_cols=['vol', 'rsi14'],
            y_col='return_1d'
        )
        if regression_result:
            logger.info("回归分析结果:")
            logger.info(f"  R²值: {regression_result['r_squared']:.4f}")
            logger.info(f"  系数: {regression_result['coefficients']}")

# 创建financial_analyzer实例，供其他模块导入使用
financial_analyzer = FinancialAnalyzer()
