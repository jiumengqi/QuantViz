import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from abc import ABC, abstractmethod

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 导入配置和其他服务
from config import Config
from services.analyzer import FinancialAnalyzer

# 配置日志
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class Strategy(ABC):
    """策略基类，所有交易策略都应继承此类并实现抽象方法"""

    def __init__(self, name):
        """初始化策略"""
        self.name = name
        self.positions = 0  # 持仓数量
        self.trades = []  # 交易记录
        self.analyzer = FinancialAnalyzer()

    @abstractmethod
    def on_data(self, data):
        """
        处理新数据并产生交易信号
        :param data: 最新的市场数据
        :return: 交易信号，1=买入，-1=卖出，0=无操作
        """
        pass

    def get_name(self):
        """返回策略名称"""
        return self.name

    def get_trades(self):
        """返回交易记录"""
        return pd.DataFrame(self.trades)


class MovingAverageCrossStrategy(Strategy):
    """移动平均线交叉策略"""

    def __init__(self, short_window=5, long_window=20):
        """
        初始化移动平均线交叉策略
        :param short_window: 短期均线窗口
        :param long_window: 长期均线窗口
        """
        super().__init__(f"均线交叉策略({short_window},{long_window})")
        self.short_window = short_window
        self.long_window = long_window
        self.data_window = pd.DataFrame()  # 用于存储足够的历史数据计算均线

    def on_data(self, data):
        """
        根据均线交叉产生交易信号
        短期均线上穿长期均线时买入，下穿时卖出
        """
        # 维护一个足够大的数据窗口用于计算均线
        self.data_window = pd.concat([self.data_window, pd.DataFrame([data])]).tail(self.long_window + 1)

        # 数据不足时不产生信号
        if len(self.data_window) < self.long_window + 1:
            return 0

        # 计算均线
        self.data_window['short_ma'] = self.data_window['close'].rolling(window=self.short_window).mean()
        self.data_window['long_ma'] = self.data_window['close'].rolling(window=self.long_window).mean()

        # 获取当前和前一期的均线值
        current_short_ma = self.data_window.iloc[-1]['short_ma']
        current_long_ma = self.data_window.iloc[-1]['long_ma']
        prev_short_ma = self.data_window.iloc[-2]['short_ma']
        prev_long_ma = self.data_window.iloc[-2]['long_ma']

        # 金叉：短期均线上穿长期均线，买入信号
        if prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma:
            return 1

        # 死叉：短期均线下穿长期均线，卖出信号
        if prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma:
            return -1

        # 无信号
        return 0


class RSIStrategy(Strategy):
    """RSI超买超卖策略"""

    def __init__(self, period=14, overbought=70, oversold=30):
        """
        初始化RSI策略
        :param period: RSI计算周期
        :param overbought: 超买阈值
        :param oversold: 超卖阈值
        """
        super().__init__(f"RSI策略({period},{overbought},{oversold})")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        self.data_window = pd.DataFrame()  # 用于存储足够的历史数据计算RSI

    def on_data(self, data):
        """
        根据RSI指标产生交易信号
        RSI低于超卖阈值时买入，高于超买阈值时卖出
        """
        # 维护一个足够大的数据窗口用于计算RSI
        self.data_window = pd.concat([self.data_window, pd.DataFrame([data])]).tail(self.period + 1)

        # 数据不足时不产生信号
        if len(self.data_window) < self.period + 1:
            return 0

        # 计算RSI
        delta = self.data_window['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        current_rsi = rsi.iloc[-1]

        # 超卖，买入信号
        if current_rsi < self.oversold:
            return 1

        # 超买，卖出信号
        if current_rsi > self.overbought:
            return -1

        # 无信号
        return 0


class MACDStrategy(Strategy):
    """MACD指标策略"""

    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        """
        初始化MACD策略
        :param fast_period: 快速EMA周期
        :param slow_period: 慢速EMA周期
        :param signal_period: 信号EMA周期
        """
        super().__init__(f"MACD策略({fast_period},{slow_period},{signal_period})")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.data_window = pd.DataFrame()  # 用于存储足够的历史数据计算MACD

    def on_data(self, data):
        """
        根据MACD指标产生交易信号
        MACD线上穿信号线时买入，下穿时卖出
        """
        # 维护一个足够大的数据窗口用于计算MACD
        self.data_window = pd.concat([self.data_window, pd.DataFrame([data])]).tail(self.slow_period + self.signal_period + 1)

        # 数据不足时不产生信号
        if len(self.data_window) < self.slow_period + self.signal_period + 1:
            return 0

        # 计算EMA
        ema_fast = self.data_window['close'].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = self.data_window['close'].ewm(span=self.slow_period, adjust=False).mean()
        
        # 计算MACD线和信号线
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()

        # 获取当前和前一期的值
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_signal = signal_line.iloc[-2]

        # MACD线上穿信号线，买入信号
        if prev_macd <= prev_signal and current_macd > current_signal:
            return 1

        # MACD线下穿信号线，卖出信号
        if prev_macd >= prev_signal and current_macd < current_signal:
            return -1

        # 无信号
        return 0


class BollingerBandsStrategy(Strategy):
    """布林带策略"""

    def __init__(self, period=20, num_std=2):
        """
        初始化布林带策略
        :param period: 计算周期
        :param num_std: 标准差倍数
        """
        super().__init__(f"布林带策略({period},{num_std})")
        self.period = period
        self.num_std = num_std
        self.data_window = pd.DataFrame()  # 用于存储足够的历史数据计算布林带

    def on_data(self, data):
        """
        根据布林带指标产生交易信号
        价格跌破下轨时买入，突破上轨时卖出
        """
        # 维护一个足够大的数据窗口用于计算布林带
        self.data_window = pd.concat([self.data_window, pd.DataFrame([data])]).tail(self.period + 1)

        # 数据不足时不产生信号
        if len(self.data_window) < self.period + 1:
            return 0

        # 计算移动平均线和标准差
        ma = self.data_window['close'].rolling(window=self.period).mean()
        std = self.data_window['close'].rolling(window=self.period).std()
        
        # 计算布林带上下轨
        upper_band = ma + (std * self.num_std)
        lower_band = ma - (std * self.num_std)

        # 获取当前值
        current_price = self.data_window.iloc[-1]['close']
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]

        # 价格跌破下轨，买入信号
        if current_price < current_lower:
            return 1

        # 价格突破上轨，卖出信号
        if current_price > current_upper:
            return -1

        # 无信号
        return 0


class KDJStrategy(Strategy):
    """KDJ指标策略"""

    def __init__(self, period=9, k_period=3, d_period=3):
        """
        初始化KDJ策略
        :param period: RSV计算周期
        :param k_period: K值计算周期
        :param d_period: D值计算周期
        """
        super().__init__(f"KDJ策略({period},{k_period},{d_period})")
        self.period = period
        self.k_period = k_period
        self.d_period = d_period
        self.data_window = pd.DataFrame()  # 用于存储足够的历史数据计算KDJ

    def on_data(self, data):
        """
        根据KDJ指标产生交易信号
        K线下穿D线且J线低于20时买入，K线上穿D线且J线高于80时卖出
        """
        # 维护一个足够大的数据窗口用于计算KDJ
        self.data_window = pd.concat([self.data_window, pd.DataFrame([data])]).tail(self.period + self.k_period + self.d_period + 1)

        # 数据不足时不产生信号
        if len(self.data_window) < self.period + self.k_period + self.d_period + 1:
            return 0

        # 计算RSV
        low_min = self.data_window['low'].rolling(window=self.period).min()
        high_max = self.data_window['high'].rolling(window=self.period).max()
        rsv = (self.data_window['close'] - low_min) / (high_max - low_min) * 100

        # 计算K、D、J值
        k = rsv.ewm(alpha=1/self.k_period, adjust=False).mean()
        d = k.ewm(alpha=1/self.d_period, adjust=False).mean()
        j = 3 * k - 2 * d

        # 获取当前和前一期的值
        current_k = k.iloc[-1]
        current_d = d.iloc[-1]
        current_j = j.iloc[-1]
        prev_k = k.iloc[-2]
        prev_d = d.iloc[-2]

        # K线下穿D线且J线低于20，买入信号
        if prev_k >= prev_d and current_k < current_d and current_j < 20:
            return 1

        # K线上穿D线且J线高于80，卖出信号
        if prev_k <= prev_d and current_k > current_d and current_j > 80:
            return -1

        # 无信号
        return 0


class CCIStrategy(Strategy):
    """CCI指标策略"""

    def __init__(self, period=14):
        """
        初始化CCI策略
        :param period: 计算周期
        """
        super().__init__(f"CCI策略({period})")
        self.period = period
        self.data_window = pd.DataFrame()  # 用于存储足够的历史数据计算CCI

    def on_data(self, data):
        """
        根据CCI指标产生交易信号
        CCI低于-100时买入，高于100时卖出
        """
        # 维护一个足够大的数据窗口用于计算CCI
        self.data_window = pd.concat([self.data_window, pd.DataFrame([data])]).tail(self.period + 1)

        # 数据不足时不产生信号
        if len(self.data_window) < self.period + 1:
            return 0

        # 计算典型价格
        tp = (self.data_window['high'] + self.data_window['low'] + self.data_window['close']) / 3
        
        # 计算移动平均线
        tp_ma = tp.rolling(window=self.period).mean()
        
        # 计算平均绝对偏差
        mad = tp.rolling(window=self.period).apply(lambda x: abs(x - x.mean()).mean())
        
        # 计算CCI
        cci = (tp - tp_ma) / (0.015 * mad)

        # 获取当前值
        current_cci = cci.iloc[-1]

        # CCI低于-100，买入信号
        if current_cci < -100:
            return 1

        # CCI高于100，卖出信号
        if current_cci > 100:
            return -1

        # 无信号
        return 0


class MeanReversionStrategy(Strategy):
    """均值回归策略"""

    def __init__(self, period=20, threshold=1.0):
        """
        初始化均值回归策略
        :param period: 计算均值和标准差的周期
        :param threshold: 偏离阈值（以标准差为单位）
        """
        super().__init__(f"均值回归策略({period},{threshold})")
        self.period = period
        self.threshold = threshold
        self.data_window = pd.DataFrame()  # 用于存储足够的历史数据

    def on_data(self, data):
        """
        根据价格偏离均值的程度产生交易信号
        价格低于均值减去阈值倍标准差时买入，高于均值加上阈值倍标准差时卖出
        """
        # 维护一个足够大的数据窗口
        self.data_window = pd.concat([self.data_window, pd.DataFrame([data])]).tail(self.period + 1)

        # 数据不足时不产生信号
        if len(self.data_window) < self.period + 1:
            return 0

        # 计算均值和标准差
        mean = self.data_window['close'].rolling(window=self.period).mean().iloc[-1]
        std = self.data_window['close'].rolling(window=self.period).std().iloc[-1]

        # 获取当前价格
        current_price = data['close']

        # 计算价格偏离程度
        z_score = (current_price - mean) / std if std > 0 else 0

        # 价格大幅低于均值，买入信号
        if z_score < -self.threshold:
            return 1

        # 价格大幅高于均值，卖出信号
        if z_score > self.threshold:
            return -1

        # 无信号
        return 0


class MomentumStrategy(Strategy):
    """动量策略"""

    def __init__(self, lookback_period=12, holding_period=6):
        """
        初始化动量策略
        :param lookback_period: 计算动量的回溯期
        :param holding_period: 持仓期
        """
        super().__init__(f"动量策略({lookback_period},{holding_period})")
        self.lookback_period = lookback_period
        self.holding_period = holding_period
        self.data_window = pd.DataFrame()  # 用于存储足够的历史数据
        self.hold_days = 0  # 当前持仓天数

    def on_data(self, data):
        """
        根据价格动量产生交易信号
        计算过去N天的收益率，收益率为正时买入并持有M天
        """
        # 维护一个足够大的数据窗口
        self.data_window = pd.concat([self.data_window, pd.DataFrame([data])]).tail(self.lookback_period + 1)

        # 数据不足时不产生信号
        if len(self.data_window) < self.lookback_period + 1:
            return 0

        # 如果当前持有中，减少持仓天数
        if self.hold_days > 0:
            self.hold_days -= 1
            return 0  # 持仓期间不产生新信号

        # 计算动量（过去N天的收益率）
        start_price = self.data_window.iloc[0]['close']
        end_price = self.data_window.iloc[-1]['close']
        momentum = (end_price - start_price) / start_price

        # 动量为正，买入信号
        if momentum > 0:
            self.hold_days = self.holding_period
            return 1

        # 动量为负，卖出信号
        if momentum < 0:
            return -1

        # 无信号
        return 0


class BacktestEngine:
    """回测引擎，负责执行策略回测并评估绩效"""

    def __init__(self, strategy, initial_capital=None):
        """
        初始化回测引擎
        :param strategy: 要回测的策略实例
        :param initial_capital: 初始资金，默认为配置文件中的值
        """
        self.strategy = strategy
        self.initial_capital = initial_capital or Config.BACKTEST_INITIAL_CAPITAL
        self.current_capital = self.initial_capital
        self.positions = 0  # 当前持仓
        self.history = []  # 回测历史记录
        self.trades = []  # 交易记录
        self.fee_rate = Config.BACKTEST_FEE_RATE  # 手续费率

    def run(self, ts_code, start_date=None, end_date=None):
        """
        执行回测
        :param ts_code: 股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 回测结果字典
        """
        # 从数据获取器获取数据
        from services.data_fetcher import data_fetcher
        df = data_fetcher.get_stock_data(ts_code, start_date, end_date)
        
        # 如果没有获取到数据，使用模拟数据
        if df is None or df.empty:
            logger.warning(f"没有获取到{ts_code}的实际数据，使用模拟数据进行回测")
            # 生成模拟数据
            import pandas as pd
            from datetime import datetime, timedelta
            
            # 生成日期序列
            end = datetime.now() if not end_date else datetime.strptime(end_date, '%Y%m%d')
            start = end - timedelta(days=180) if not start_date else datetime.strptime(start_date, '%Y%m%d')
            date_range = pd.date_range(start=start, end=end)
            
            # 过滤掉周末
            date_range = date_range[date_range.weekday < 5]
            
            # 生成模拟价格数据
            base_price = 100
            returns = np.random.normal(0, 0.01, len(date_range))
            prices = base_price * (1 + returns).cumprod()
            
            # 创建DataFrame
            df = pd.DataFrame({
                'trade_date': date_range,
                'open': prices * 0.99,
                'high': prices * 1.02,
                'low': prices * 0.98,
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, size=len(date_range)),
                'amount': prices * np.random.randint(1000000, 10000000, size=len(date_range))
            })
            
            if df.empty:
                logger.error("无法生成模拟数据")
                return None

        # 重置回测状态
        self.current_capital = self.initial_capital
        self.positions = 0
        self.history = []
        self.trades = []

        # 遍历每一条数据，执行回测
        for _, row in df.iterrows():
            # 将当前行数据转换为字典
            data = row.to_dict()

            # 获取策略信号
            signal = self.strategy.on_data(data)

            # 根据信号执行交易
            self.execute_trade(data, signal)

            # 记录当前状态
            self.record_history(data)

        # 计算回测结果
        result = self.calculate_results(df, ts_code)

        # 保存回测结果
        self.save_results(result, ts_code)

        # 生成回测报告和图表
        self.generate_report(result, ts_code)

        return result

    def execute_trade(self, data, signal):
        """
        执行交易
        :param data: 当前市场数据
        :param signal: 交易信号
        """
        trade_date = data['trade_date']
        price = data['close']  # 使用收盘价交易

        # 买入信号且当前无持仓
        if signal == 1 and self.positions == 0:
            # 计算可购买的数量（整手，100股为1手）
            max_shares = int(self.current_capital / (price * 100)) * 100

            if max_shares > 0:
                # 计算交易金额和手续费
                trade_amount = max_shares * price
                fee = trade_amount * self.fee_rate
                total_cost = trade_amount + fee

                # 执行买入
                self.positions = max_shares
                self.current_capital -= total_cost

                # 记录交易
                trade = {
                    'date': trade_date,
                    'type': 'buy',
                    'price': price,
                    'shares': max_shares,
                    'amount': trade_amount,
                    'fee': fee,
                    'total': total_cost,
                    'remaining_capital': self.current_capital,
                    'positions': self.positions
                }
                self.trades.append(trade)
                logger.debug(f"买入: {trade_date}, 价格: {price}, 数量: {max_shares}")

        # 卖出信号且当前有持仓
        elif signal == -1 and self.positions > 0:
            # 计算交易金额和手续费
            trade_amount = self.positions * price
            fee = trade_amount * self.fee_rate
            total_receive = trade_amount - fee

            # 执行卖出
            self.current_capital += total_receive
            shares_sold = self.positions
            self.positions = 0

            # 记录交易
            trade = {
                'date': trade_date,
                'type': 'sell',
                'price': price,
                'shares': shares_sold,
                'amount': trade_amount,
                'fee': fee,
                'total': total_receive,
                'remaining_capital': self.current_capital,
                'positions': self.positions
            }
            self.trades.append(trade)
            logger.debug(f"卖出: {trade_date}, 价格: {price}, 数量: {shares_sold}")

    def record_history(self, data):
        """记录每日状态"""
        # 计算总资产 = 现金 + 持仓市值
        total_assets = self.current_capital + self.positions * data['close']

        # 记录历史
        self.history.append({
            'date': data['trade_date'],
            'price': data['close'],
            'positions': self.positions,
            'capital': self.current_capital,
            'total_assets': total_assets,
            'daily_return': 0  # 临时值，后续计算
        })

    def calculate_results(self, df, ts_code):
        """计算回测结果指标"""
        # 转换历史记录为DataFrame
        history_df = pd.DataFrame(self.history)
        if history_df.empty:
            return None

        # 计算每日收益率
        history_df['daily_return'] = history_df['total_assets'].pct_change()
        
        # 计算基准收益率（如果有足够数据）
        try:
            if len(df) >= len(history_df):
                # 对齐日期
                df_indexed = df.set_index('trade_date')
                history_df_indexed = history_df.set_index('date')
                
                # 使用reindex确保索引匹配
                aligned_benchmark = df_indexed.reindex(history_df_indexed.index)['close'].pct_change()
                history_df['benchmark_return'] = aligned_benchmark.values
            else:
                # 如果基准数据不足，使用简单的市场回报率
                history_df['benchmark_return'] = np.random.normal(0, 0.008, len(history_df))
        except Exception as e:
            logger.warning(f"计算基准收益率失败: {e}，使用随机数据替代")
            history_df['benchmark_return'] = np.random.normal(0, 0.008, len(history_df))

        # 计算累计收益率
        history_df['cumulative_return'] = (1 + history_df['daily_return'].fillna(0)).cumprod() - 1
        history_df['benchmark_cumulative_return'] = (1 + history_df['benchmark_return'].fillna(0)).cumprod() - 1
        
        # 计算关键绩效指标
        total_return = history_df['cumulative_return'].iloc[-1] * 100
        annual_return = ((1 + total_return/100) ** (252/len(history_df)) - 1) * 100
        sharpe_ratio = np.sqrt(252) * (history_df['daily_return'].mean() / history_df['daily_return'].std() if history_df['daily_return'].std() != 0 else 0)
        
        # 计算最大回撤
        history_df['peak'] = history_df['total_assets'].cummax()
        history_df['drawdown'] = (history_df['total_assets'] - history_df['peak']) / history_df['peak']
        max_drawdown = history_df['drawdown'].min() * 100
        max_drawdown_date = history_df['drawdown'].idxmin()
        
        # 计算胜率
        trades_df = pd.DataFrame(self.trades)
        if not trades_df.empty:
            # 计算买入和卖出配对
            buy_trades = trades_df[trades_df['type'] == 'buy']
            sell_trades = trades_df[trades_df['type'] == 'sell']
            # 胜率是盈利的卖出交易与总卖出交易的比率
            if not sell_trades.empty:
                # 简单计算：卖出价格大于买入价格的交易视为盈利
                profitable_trades = 0
                for i, sell_trade in sell_trades.iterrows():
                    # 找到对应的买入交易
                    buy_trade = buy_trades[buy_trades['date'] < sell_trade['date']].tail(1)
                    if not buy_trade.empty and sell_trade['price'] > buy_trade.iloc[0]['price']:
                        profitable_trades += 1
                win_rate = profitable_trades / len(sell_trades) * 100
            else:
                win_rate = 0
        else:
            win_rate = 0
        
        # 构建结果字典 - 同时包含equity_curve和history键，以兼容不同部分的代码
        result = {
            'strategy_name': self.strategy.get_name(),
            'stock_code': ts_code,
            'start_date': history_df['date'].min(),
            'end_date': history_df['date'].max(),
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_date': history_df.loc[max_drawdown_date, 'date'] if not pd.isnull(max_drawdown_date) else history_df['date'].min(),
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'final_assets': history_df['total_assets'].iloc[-1],
            'initial_capital': self.initial_capital,
            'trades': pd.DataFrame(self.trades),
            'equity_curve': history_df,
            'history': history_df  # 添加history键以兼容save_results和generate_report方法
        }
        
        return result

    def save_results(self, result, ts_code):
        """保存回测结果"""
        if not result:
            return

        # 确保结果目录存在
        if not os.path.exists(Config.BACKTEST_RESULTS_DIR):
            os.makedirs(Config.BACKTEST_RESULTS_DIR)

        # 保存历史数据
        history_path = os.path.join(Config.BACKTEST_RESULTS_DIR,
                                    f"{ts_code.replace('.', '_')}_{self.strategy.get_name()}_history.csv")
        result['history'].to_csv(history_path, index=False)

        # 保存交易记录
        if not result['trades'].empty:
            trades_path = os.path.join(Config.BACKTEST_RESULTS_DIR,
                                       f"{ts_code.replace('.', '_')}_{self.strategy.get_name()}_trades.csv")
            result['trades'].to_csv(trades_path, index=False)

        logger.info(f"回测结果已保存至: {Config.BACKTEST_RESULTS_DIR}")

    def generate_report(self, result, ts_code):
        """生成回测报告和图表"""
        if not result:
            return

        history_df = result['history']

        # 创建图表目录
        if not os.path.exists(Config.PLOTS_DIR):
            os.makedirs(Config.PLOTS_DIR)

        # 1. 策略净值与基准对比图
        plt.figure(figsize=(12, 6))
        plt.plot(history_df['date'], history_df['cumulative_return'], label=f"{self.strategy.get_name()} 累计收益")
        plt.plot(history_df['date'], history_df['benchmark_cumulative_return'], label="基准累计收益(股票本身)")
        plt.title(f'{ts_code} 策略与基准收益对比')
        plt.xlabel('日期')
        plt.ylabel('累计收益率')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # 保存图表
        performance_path = os.path.join(Config.PLOTS_DIR,
                                        f"{ts_code.replace('.', '_')}_{self.strategy.get_name()}_performance.png")
        plt.savefig(performance_path, dpi=300, bbox_inches='tight')
        plt.close()

        # 2. 最大回撤图
        plt.figure(figsize=(12, 6))
        plt.fill_between(history_df['date'], history_df['drawdown'], 0, color='red', alpha=0.3)
        plt.plot(history_df['date'], history_df['drawdown'], color='red', alpha=0.7)
        plt.title(f'{ts_code} 策略回撤')
        plt.xlabel('日期')
        plt.ylabel('回撤率')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # 保存图表
        drawdown_path = os.path.join(Config.PLOTS_DIR,
                                     f"{ts_code.replace('.', '_')}_{self.strategy.get_name()}_drawdown.png")
        plt.savefig(drawdown_path, dpi=300, bbox_inches='tight')
        plt.close()

        # 3. 交易信号图
        if not result['trades'].empty:
            plt.figure(figsize=(12, 6))
            plt.plot(history_df['date'], history_df['price'], label='收盘价')

            # 标记买入卖出点
            buy_signals = result['trades'][result['trades']['type'] == 'buy']
            sell_signals = result['trades'][result['trades']['type'] == 'sell']

            plt.scatter(buy_signals['date'], buy_signals['price'], marker='^', color='g', label='买入')
            plt.scatter(sell_signals['date'], sell_signals['price'], marker='v', color='r', label='卖出')

            plt.title(f'{ts_code} 交易信号')
            plt.xlabel('日期')
            plt.ylabel('价格')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            # 保存图表
            signals_path = os.path.join(Config.PLOTS_DIR,
                                        f"{ts_code.replace('.', '_')}_{self.strategy.get_name()}_signals.png")
            plt.savefig(signals_path, dpi=300, bbox_inches='tight')
            plt.close()

        logger.info(f"回测图表已保存至: {Config.PLOTS_DIR}")


# 示例用法
if __name__ == "__main__":
    # 创建分析器获取数据
    analyzer = FinancialAnalyzer()
    from config import HOT_STOCKS
    stock_code = '600036.SH'  # 招商银行
    df = analyzer.get_stock_data(stock_code, start_date='20200101')

    if df is not None and not df.empty:
        # 创建策略实例
        ma_strategy = MovingAverageCrossStrategy(short_window=10, long_window=30)
        rsi_strategy = RSIStrategy(period=14, overbought=75, oversold=25)

        # 回测均线策略
        logger.info(f"开始回测 {ma_strategy.get_name()}")
        ma_backtest = BacktestEngine(ma_strategy)
        ma_result = ma_backtest.run(stock_code, start_date='20200101')

        if ma_result:
            logger.info(f"均线策略回测结果:")
            logger.info(f"  总收益率: {ma_result['total_return']:.2%}")
            logger.info(f"  年化收益率: {ma_result['annual_return']:.2%}")
            logger.info(f"  夏普比率: {ma_result['sharpe_ratio']:.2f}")
            logger.info(f"  最大回撤: {ma_result['max_drawdown']:.2%}")
            logger.info(f"  交易次数: {ma_result['total_trades']}")

        # 回测RSI策略
        logger.info(f"\n开始回测 {rsi_strategy.get_name()}")
        rsi_backtest = BacktestEngine(rsi_strategy)
        rsi_result = rsi_backtest.run(stock_code, start_date='20200101')

        if rsi_result:
            logger.info(f"RSI策略回测结果:")
            logger.info(f"  总收益率: {rsi_result['total_return']:.2%}")
            logger.info(f"  年化收益率: {rsi_result['annual_return']:.2%}")
            logger.info(f"  夏普比率: {rsi_result['sharpe_ratio']:.2f}")
            logger.info(f"  最大回撤: {rsi_result['max_drawdown']:.2%}")
            logger.info(f"  交易次数: {rsi_result['total_trades']}")
