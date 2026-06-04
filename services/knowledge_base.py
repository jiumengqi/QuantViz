# -*- coding: utf-8 -*-
"""
量化投资知识库
包含量化投资入门教程、技术指标解释、策略原理、风险提示和常见问题
"""

# 量化投资入门教程
TUTORIALS = {
    'getting_started': {
        'id': 'getting_started',
        'title': '量化投资入门',
        'category': '入门',
        'description': '了解量化投资的基本概念和发展历程',
        'level': 'beginner',
        'content': '''
# 什么是量化投资

量化投资是指利用数学、统计学和计算机技术，通过对历史数据的分析和建模，制定投资决策并实现自动化交易的投资方式。

## 量化投资的特点

1. **数据驱动**：基于历史数据分析和统计规律
2. **纪律性强**：严格遵循预设的交易规则
3. **系统化**：完整的投资流程和风控体系
4. **高效性**：计算机自动执行，处理速度快
5. **可回测**：可以在历史数据上验证策略有效性

## 量化投资的发展历程

- 1980年代：量化投资在华尔街兴起
- 1990年代：量化基金开始崭露头角
- 2000年代：高频交易快速发展
- 2010年代：机器学习广泛应用于量化领域
- 2020年代：AI驱动的智能量化成为趋势

## 量化投资的基本流程

1. **数据收集**：获取股票、期货等金融数据
2. **策略研发**：发现市场规律，设计交易策略
3. **回测验证**：在历史数据上测试策略表现
4. **参数优化**：调整策略参数提升表现
5. **实盘交易**：将策略应用到真实市场
6. **风险管理**：实时监控和控制风险
'''
    },
    'first_strategy': {
        'id': 'first_strategy',
        'title': '如何编写第一个量化策略',
        'category': '入门',
        'description': '从零开始学习编写简单的量化交易策略',
        'level': 'beginner',
        'content': '''
# 如何编写第一个量化策略

本教程将指导您从头开始编写一个简单的量化交易策略。

## 准备工作

1. **安装Python环境**：建议使用Anaconda
2. **安装必要的库**：pandas, numpy, tushare, matplotlib
3. **获取数据**：使用Tushare等免费数据接口

## 策略开发步骤

### 第一步：数据获取

```python
import pandas as pd
import tushare as ts

# 获取股票数据
df = ts.get_k_data('600036', start='2020-01-01', end='2024-12-31')
df.set_index('date', inplace=True)
```

### 第二步：计算技术指标

```python
# 计算简单移动平均线
df['MA5'] = df['close'].rolling(window=5).mean()
df['MA20'] = df['close'].rolling(window=20).mean()
```

### 第三步：生成交易信号

```python
# 金叉买入，死叉卖出
df['signal'] = 0
df.loc[df['MA5'] > df['MA20'], 'signal'] = 1  # 买入信号
df.loc[df['MA5'] <= df['MA20'], 'signal'] = -1  # 卖出信号
```

### 第四步：回测策略

```python
# 计算收益率
df['returns'] = df['close'].pct_change()
df['strategy_returns'] = df['signal'].shift(1) * df['returns']

# 计算累计收益
cumulative_returns = (1 + df['strategy_returns']).cumprod()
```

### 第五步：评估策略

- **年化收益率**：策略的平均年化收益
- **最大回撤**：策略历史最大亏损
- **夏普比率**：风险调整后的收益指标
- **胜率**：盈利交易次数占比

## 注意事项

1. **过拟合问题**：避免策略在历史数据上过度优化
2. **交易成本**：考虑手续费、滑点等成本
3. **风险管理**：设置止损、仓位控制
4. **实盘差异**：历史表现不代表未来收益
'''
    },
    'python_basics': {
        'id': 'python_basics',
        'title': 'Python金融数据处理基础',
        'category': '编程',
        'description': '学习使用Python处理金融数据的基础知识',
        'level': 'beginner',
        'content': '''
# Python金融数据处理基础

Python已成为量化投资领域最流行的编程语言，本教程介绍金融数据处理的基础知识。

## 核心库介绍

### Pandas - 数据处理

```python
import pandas as pd

# 创建DataFrame
data = {'price': [100, 101, 102], 'volume': [1000, 1100, 1200]}
df = pd.DataFrame(data, index=['day1', 'day2', 'day3'])

# 数据选择
df['price']  # 选择单列
df.iloc[0]   # 选择单行
df.loc['day1']  # 标签索引
```

### NumPy - 数值计算

```python
import numpy as np

# 创建数组
arr = np.array([1, 2, 3, 4, 5])

# 统计函数
np.mean(arr)  # 均值
np.std(arr)   # 标准差
np.max(arr)   # 最大值
np.min(arr)   # 最小值
```

### Matplotlib - 数据可视化

```python
import matplotlib.pyplot as plt

# 绑图
plt.plot(df['price'])
plt.title('价格走势')
plt.xlabel('日期')
plt.ylabel('价格')
plt.show()
```

## 金融数据处理技巧

### 缺失值处理

```python
df.dropna()  # 删除缺失值
df.fillna(0)  # 用0填充
df.fillna(method='ffill')  # 前向填充
```

### 数据对齐

```python
# 按日期合并多个股票数据
merged = pd.merge(stock1, stock2, on='date', how='outer')
```

### 滚动窗口计算

```python
# 计算20日滚动均值
df['MA20'] = df['close'].rolling(window=20).mean()

# 计算滚动标准差（波动率）
df['rolling_std'] = df['close'].rolling(window=20).std()
```
'''
    },
    'data_analysis': {
        'id': 'data_analysis',
        'title': '金融数据分析入门',
        'category': '分析',
        'description': '学习金融数据分析的基本方法',
        'level': 'intermediate',
        'content': '''
# 金融数据分析入门

金融数据分析是量化投资的核心，本教程介绍基本的数据分析方法。

## 数据类型

### 价格数据
- **OHLC**：开盘价、最高价、最低价、收盘价
- **调整后收盘价**：考虑分红拆股的调整价格
- **成交量**：当日交易股数

### 基本面数据
- **财务指标**：市盈率、市净率、每股收益
- **财务报表**：资产负债表、利润表、现金流量表
- **宏观数据**：GDP、CPI、利率

## 常用分析方法

### 收益率分析

```python
# 日收益率
daily_returns = df['close'].pct_change()

# 年化收益率
annual_return = daily_returns.mean() * 252

# 收益率标准差（波动率）
volatility = daily_returns.std() * np.sqrt(252)
```

### 趋势分析

```python
# 移动平均线
df['MA20'] = df['close'].rolling(20).mean()
df['MA60'] = df['close'].rolling(60).mean()

# 趋势判断
if df['MA20'].iloc[-1] > df['MA60'].iloc[-1]:
    print("当前处于上升趋势")
```

### 相关性分析

```python
# 计算两只股票的相关性
correlation = df1['returns'].corr(df2['returns'])

# 计算滚动相关性
rolling_corr = df1['returns'].rolling(60).corr(df2['returns'])
```

## 数据可视化

### K线图

```python
import mplfinance as mpf

mpf.plot(df, type='candle', style='charles')
```

### 收益率分布

```python
import seaborn as sns

sns.histplot(daily_returns, kde=True)
```
'''
    }
}

# 技术指标解释
INDICATORS = {
    'MA': {
        'id': 'MA',
        'name': '移动平均线 (MA)',
        'category': '趋势指标',
        'description': '通过计算一定周期内的平均价格来判断趋势方向',
        'formula': 'MA = (C1 + C2 + ... + Cn) / n',
        'parameters': [
            {'name': '周期', 'default': '5, 10, 20, 60', 'description': '计算平均值的周期数'}
        ],
        'interpretation': '''
**使用建议：**
- MA5：短期趋势，短期交易参考
- MA20：中期趋势，中线交易参考
- MA60：长期趋势，长线交易参考

**常见用法：**
- 多头排列：短期MA在长期MA上方，看涨
- 空头排列：短期MA在长期MA下方，看跌
- 金叉：短期MA上穿长期MA，买入信号
- 死叉：短期MA下穿长期MA，卖出信号

**注意事项：**
- 属于滞后指标，有延迟
- 在震荡市中容易产生假信号
- 需要结合其他指标使用
''',
        'example': '''
# Python计算MA
import pandas as pd

df['MA5'] = df['close'].rolling(window=5).mean()
df['MA20'] = df['close'].rolling(window=20).mean()
df['MA60'] = df['close'].rolling(window=60).mean()

# 金叉信号
df['golden_cross'] = (df['MA5'] > df['MA20']) & (df['MA5'].shift(1) <= df['MA20'].shift(1))

# 死叉信号
df['death_cross'] = (df['MA5'] < df['MA20']) & (df['MA5'].shift(1) >= df['MA20'].shift(1))
'''
    },
    'MACD': {
        'id': 'MACD',
        'name': '指数平滑异同移动平均线 (MACD)',
        'category': '趋势指标',
        'description': '利用短期与长期指数平滑移动平均线之间的聚合与分离状况，对买卖时机作出判断',
        'formula': '''
DIF = EMA12 - EMA26
DEA = EMA(DIF, 9)
MACD = 2 * (DIF - DEA)
''',
        'parameters': [
            {'name': '短期EMA', 'default': '12', 'description': '短期指数平滑移动平均线周期'},
            {'name': '长期EMA', 'default': '26', 'description': '长期指数平滑移动平均线周期'},
            {'name': '信号线', 'default': '9', 'description': 'DEA线的平滑周期'}
        ],
        'interpretation': '''
**组成：**
- DIF线：快线，反映短期与长期EMA的差值
- DEA线：慢线，DIF的移动平均线
- MACD柱：DIF与DEA差值的两倍

**交易信号：**
- 金叉：DIF上穿DEA，建议买入
- 死叉：DIF下穿DEA，建议卖出
- 顶背离：价格创新高但MACD未创新高，看跌
- 底背离：价格创新低但MACD未创新低，看涨

**注意事项：**
- 在趋势行情中效果较好
- 在震荡行情中容易失效
- MACD柱变长表示动能增强
''',
        'example': '''
# Python计算MACD
import pandas as pd

# 计算EMA
df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()

# 计算DIF和DEA
df['DIF'] = df['EMA12'] - df['EMA26']
df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()

# 计算MACD柱
df['MACD'] = 2 * (df['DIF'] - df['DEA'])

# 金叉和死叉
df['macd_golden'] = (df['DIF'] > df['DEA']) & (df['DIF'].shift(1) <= df['DEA'].shift(1))
df['macd_death'] = (df['DIF'] < df['DEA']) & (df['DIF'].shift(1) >= df['DEA'].shift(1))
'''
    },
    'RSI': {
        'id': 'RSI',
        'name': '相对强弱指数 (RSI)',
        'category': '动量指标',
        'description': '通过比较一定周期内的上涨和下跌幅度，来判断价格的强弱程度',
        'formula': '''
RS = 平均涨幅 / 平均跌幅
RSI = 100 - (100 / (1 + RS))
''',
        'parameters': [
            {'name': '周期', 'default': '14', 'description': '计算RSI的周期数'},
            {'name': '超买阈值', 'default': '70', 'description': 'RSI超过此值视为超买'},
            {'name': '超卖阈值', 'default': '30', 'description': 'RSI低于此值视为超卖'}
        ],
        'interpretation': '''
**取值范围：** 0-100

**超买超卖：**
- RSI > 70：超买区域，可能面临回调
- RSI < 30：超卖区域，可能出现反弹

**趋势判断：**
- RSI > 50：多头力量占优
- RSI < 50：空头力量占优

**背离信号：**
- 顶背离：价格创新高但RSI未创新高
- 底背离：价格创新低但RSI未创新低

**注意事项：**
- 在极端行情中可能长时间维持超买/超卖
- 需要结合趋势指标使用
- 不同股票的RSI敏感性不同
''',
        'example': '''
# Python计算RSI
import pandas as pd
import numpy as np

# 计算涨跌幅
df['price_change'] = df['close'].diff()

# 分离涨跌
df['gain'] = df['price_change'].apply(lambda x: x if x > 0 else 0)
df['loss'] = df['price_change'].apply(lambda x: -x if x < 0 else 0)

# 计算平均涨跌
window = 14
df['avg_gain'] = df['gain'].rolling(window=window).mean()
df['avg_loss'] = df['loss'].rolling(window=window).mean()

# 计算RS和RSI
df['rs'] = df['avg_gain'] / df['avg_loss']
df['rsi'] = 100 - (100 / (1 + df['rs']))

# 或者使用talib库
# import talib
# df['rsi'] = talib.RSI(df['close'], timeperiod=14)
'''
    },
    'KDJ': {
        'id': 'KDJ',
        'name': '随机指标 (KDJ)',
        'category': '动量指标',
        'description': '通过计算最高价、最低价与收盘价的关系，来判断价格走势的强弱和转折点',
        'formula': '''
RSV = (Ct - Ln) / (Hn - Ln) * 100
K = 2/3 * Kprev + 1/3 * RSV
D = 2/3 * Dprev + 1/3 * K
J = 3 * K - 2 * D
''',
        'parameters': [
            {'name': 'N', 'default': '9', 'description': 'RSV计算周期'},
            {'name': 'M1', 'default': '3', 'description': 'K值平滑因子'},
            {'name': 'M2', 'default': '3', 'description': 'D值平滑因子'}
        ],
        'interpretation': '''
**取值范围：** 0-100

**超买超卖：**
- KDJ > 80：超买区域
- KDJ < 20：超卖区域

**金叉死叉：**
- 金叉：K线上穿D线，买入信号
- 死叉：K线下穿D线，卖出信号

**背离信号：**
- 顶背离：价格创新高但KDJ未创新高
- 底背离：价格创新低但KDJ未创新低

**注意事项：**
- KDJ比RSI更敏感，波动更大
- 在震荡行情中容易产生无效信号
- 建议结合其他指标使用
''',
        'example': '''
# Python计算KDJ
import pandas as pd

n = 9
m1 = 3
m2 = 3

# 计算RSV
df['Hn'] = df['high'].rolling(window=n).max()
df['Ln'] = df['low'].rolling(window=n).min()
df['RSV'] = (df['close'] - df['Ln']) / (df['Hn'] - df['Ln']) * 100

# 计算K、D、J值
df['K'] = df['RSV'].ewm(alpha=1/m1, adjust=False).mean()
df['D'] = df['K'].ewm(alpha=1/m2, adjust=False).mean()
df['J'] = 3 * df['K'] - 2 * df['D']
'''
    },
    'BOLL': {
        'id': 'BOLL',
        'name': '布林带 (BOLL)',
        'category': '趋势指标',
        'description': '利用统计学中的标准差原理，绘制出价格波动的区间范围',
        'formula': '''
中轨 = MA20
上轨 = 中轨 + 2 * STD20
下轨 = 中轨 - 2 * STD20
''',
        'parameters': [
            {'name': '周期', 'default': '20', 'description': '中轨计算的周期'},
            {'name': '标准差倍数', 'default': '2', 'description': '上下轨与中轨的距离倍数'}
        ],
        'interpretation': '''
**带状通道：**
- 上轨：价格的压力位
- 中轨：价格的趋势方向
- 下轨：价格的支撑位

**收口扩张：**
- 收口：波动率降低，可能酝酿突破
- 开口：波动率增大，趋势可能加速

**价格位置：**
- 价格触及上轨：可能超买，有回调风险
- 价格触及下轨：可能超卖，有反弹机会
- 价格在中轨上方：多头趋势
- 价格在中轨下方：空头趋势

**注意事项：**
- 不应单独作为买卖依据
- 在趋势行情中效果较好
- 配合其他指标使用效果更佳
''',
        'example': '''
# Python计算布林带
import pandas as pd

period = 20
df['MA'] = df['close'].rolling(window=period).mean()
df['STD'] = df['close'].rolling(window=period).std()

df['upper'] = df['MA'] + 2 * df['STD']
df['middle'] = df['MA']
df['lower'] = df['MA'] - 2 * df['STD']

# 交易信号
df['buy_signal'] = df['close'] < df['lower']
df['sell_signal'] = df['close'] > df['upper']
'''
    },
    'CCI': {
        'id': 'CCI',
        'name': '顺势指标 (CCI)',
        'category': '超买超卖指标',
        'description': '测量价格相对于其统计平均值的偏离程度，用于判断价格的过度偏离',
        'formula': '''
TP = (最高价 + 最低价 + 收盘价) / 3
CCI = (TP - MA) / (0.015 * 平均绝对偏差)
''',
        'parameters': [
            {'name': '周期', 'default': '14', 'description': '计算CCI的周期'}
        ],
        'interpretation': '''
**取值范围：** 无固定范围，通常在-100到+100之间波动

**超买超卖：**
- CCI > +100：超买区域
- CCI < -100：超卖区域

**趋势判断：**
- CCI > 0：价格高于平均价，多头市场
- CCI < 0：价格低于平均价，空头市场

**背离信号：**
- 顶背离：价格创新高但CCI未创新高
- 底背离：价格创新低但CCI未创新低

**注意事项：**
- 属于无界指标，需设置参考线
- 在趋势行情中可能长时间维持超买/超卖
- 配合其他指标使用效果更好
''',
        'example': '''
# Python计算CCI
import pandas as pd

period = 14

# 计算典型价格
df['TP'] = (df['high'] + df['low'] + df['close']) / 3

# 计算平均价
df['MA'] = df['close'].rolling(window=period).mean()

# 计算平均绝对偏差
df['MAD'] = df['close'].rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())

# 计算CCI
df['CCI'] = (df['TP'] - df['MA']) / (0.015 * df['MAD'])

# 或者使用简化公式
# df['SMA'] = df['close'].rolling(window=period).mean()
# df['CCI'] = (df['close'] - df['SMA']) / (0.015 * df['close'].rolling(window=period).std())
'''
    }
}

# 策略原理
STRATEGIES = {
    'double_ma': {
        'id': 'double_ma',
        'name': '双均线策略',
        'category': '趋势跟踪',
        'difficulty': '入门',
        'description': '使用两条不同周期的移动平均线的交叉来判断买卖时机',
        'principle': '''
双均线策略是最基础的趋势跟踪策略之一。其核心思想是：
- 短期均线代表短期价格趋势
- 长期均线代表长期价格趋势
- 当短期均线上穿长期均线时，说明短期动力转强，是买入信号
- 当短期均线下穿长期均线时，说明短期动力减弱，是卖出信号

这种策略适用于趋势明显的市场，在震荡市中可能产生较多假信号。
''',
        'parameters': [
            {'name': '短期均线周期', 'default': '5', 'description': '短期移动平均线的周期'},
            {'name': '长期均线周期', 'default': '20', 'description': '长期移动平均线的周期'}
        ],
        'pros_cons': '''
**优点：**
- 原理简单，容易理解和实现
- 能够有效捕捉中长期趋势
- 历史悠久，验证充分

**缺点：**
- 滞后性强，反应较慢
- 在震荡市中容易产生假信号
- 需不断调整参数适应市场
''',
        'code_example': '''
import pandas as pd

def double_ma_strategy(df, short_period=5, long_period=20):
    """
    双均线策略
    
    参数:
        df: 包含收盘价的DataFrame
        short_period: 短期均线周期
        long_period: 长期均线周期
    
    返回:
        包含交易信号的DataFrame
    """
    # 计算均线
    df['MA_short'] = df['close'].rolling(window=short_period).mean()
    df['MA_long'] = df['close'].rolling(window=long_period).mean()
    
    # 生成交易信号
    df['signal'] = 0
    df.loc[df['MA_short'] > df['MA_long'], 'signal'] = 1
    df.loc[df['MA_short'] <= df['MA_long'], 'signal'] = -1
    
    # 计算信号变化（用于实际交易时点）
    df['trade_signal'] = df['signal'].diff()
    
    return df
'''
    },
    'rsi_strategy': {
        'id': 'rsi_strategy',
        'name': 'RSI均值回归策略',
        'category': '均值回归',
        'difficulty': '入门',
        'description': '利用RSI指标的超买超卖信号进行交易',
        'principle': '''
RSI均值回归策略基于一个核心假设：价格在短期内会围绕其均值波动，当偏离过大时，会向均值回归。

- 当RSI低于超卖阈值（通常30）时，价格可能过度下跌，形成买入机会
- 当RSI高于超买阈值（通常70）时，价格可能过度上涨，形成卖出机会

这种策略适用于震荡市场，在趋势明显的市场可能失效。
''',
        'parameters': [
            {'name': 'RSI周期', 'default': '14', 'description': 'RSI计算的周期'},
            {'name': '超卖阈值', 'default': '30', 'description': '低于此值视为超卖'},
            {'name': '超买阈值', 'default': '70', 'description': '高于此值视为超买'}
        ],
        'pros_cons': '''
**优点：**
- 交易信号明确，易于执行
- 能够在波动中获取收益
- 参数简单，易于优化

**缺点：**
- 在强趋势市场中可能持续亏损
- 需要准确判断市场状态
- 阈值设置需要根据市场调整
''',
        'code_example': '''
import pandas as pd
import numpy as np

def calculate_rsi(prices, period=14):
    """计算RSI"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def rsi_strategy(df, rsi_period=14, oversold=30, overbought=70):
    """
    RSI均值回归策略
    
    参数:
        df: 包含最高、最低、收盘价的DataFrame
        rsi_period: RSI周期
        oversold: 超卖阈值
        overbought: 超买阈值
    """
    # 计算RSI
    df['RSI'] = calculate_rsi(df['close'], rsi_period)
    
    # 生成交易信号
    df['signal'] = 0
    df.loc[df['RSI'] < oversold, 'signal'] = 1   # 买入信号
    df.loc[df['RSI'] > overbought, 'signal'] = -1  # 卖出信号
    
    return df
'''
    },
    'macd_strategy': {
        'id': 'macd_strategy',
        'name': 'MACD趋势策略',
        'category': '趋势跟踪',
        'difficulty': '入门',
        'description': '利用MACD指标的交叉和背离信号进行交易',
        'principle': '''
MACD策略主要利用以下信号进行交易：

1. **金叉死叉**：
   - 金叉（DIF上穿DEA）：短期趋势转强，买入信号
   - 死叉（DIF下穿DEA）：短期趋势转弱，卖出信号

2. **MACD柱变长变短**：
   - MACD柱变长：动能增强，趋势可能延续
   - MACD柱变短：动能减弱，趋势可能反转

3. **背离**：
   - 顶背离：价格创新高但MACD未创新高，看跌
   - 底背离：价格创新低但MACD未创新低，看涨

MACD策略适用于趋势明显的市场，能较好地捕捉中短期趋势。
''',
        'parameters': [
            {'name': '短期EMA周期', 'default': '12', 'description': '短期EMA周期'},
            {'name': '长期EMA周期', 'default': '26', 'description': '长期EMA周期'},
            {'name': '信号线周期', 'default': '9', 'description': 'DEA线平滑周期'}
        ],
        'pros_cons': '''
**优点：**
- 信号可靠性较高
- 能够捕捉中短期趋势
- 背离信号能预警趋势反转

**缺点：**
- 在震荡市中表现不佳
- 信号存在一定滞后
- 需要结合其他工具判断
''',
        'code_example': '''
import pandas as pd

def macd_strategy(df, fast=12, slow=26, signal=9):
    """
    MACD策略
    
    参数:
        df: 包含收盘价的DataFrame
        fast: 短期EMA周期
        slow: 长期EMA周期
        signal: 信号线周期
    """
    # 计算EMA
    df['EMA_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['EMA_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    
    # 计算DIF和DEA
    df['DIF'] = df['EMA_fast'] - df['EMA_slow']
    df['DEA'] = df['DIF'].ewm(span=signal, adjust=False).mean()
    
    # 计算MACD柱
    df['MACD_hist'] = 2 * (df['DIF'] - df['DEA'])
    
    # 生成交易信号
    df['signal'] = 0
    df.loc[df['DIF'] > df['DEA'], 'signal'] = 1
    df.loc[df['DIF'] <= df['DEA'], 'signal'] = -1
    
    # 金叉和死叉信号
    df['trade_signal'] = 0
    df.loc[(df['DIF'] > df['DEA']) & (df['DIF'].shift(1) <= df['DEA'].shift(1)), 'trade_signal'] = 1  # 买入
    df.loc[(df['DIF'] < df['DEA']) & (df['DIF'].shift(1) >= df['DEA'].shift(1)), 'trade_signal'] = -1  # 卖出
    
    return df
'''
    },
    'turtle_strategy': {
        'id': 'turtle_strategy',
        'name': '海龟交易策略',
        'category': '趋势跟踪',
        'difficulty': '进阶',
        'description': '著名的趋势跟随策略，基于短期和长期突破信号',
        'principle': '''
海龟交易策略源于著名的"海龟实验"，其核心思想是：

1. **趋势跟随**：当价格突破最近N天的最高/最低点时，说明趋势可能形成，顺势开仓

2. **双重仓位**：使用短期突破（N1）入场，使用长期突破（N2）加仓

3. **波动率仓位管理**：根据市场波动率调整仓位大小

4. **止损原则**：每笔交易设置硬止损，控制单笔亏损

5. **系统性交易**：严格遵循规则，不主观判断

入场规则：
- 多头入场：当价格突破最近20日最高价
- 空头入场：当价格跌破最近20日最低价

出场规则：
- 多头出场：当价格跌破最近10日最低价
- 空头出场：当价格突破最近10日最高价
''',
        'parameters': [
            {'name': '入场周期', 'default': '20', 'description': '入场信号计算周期'},
            {'name': '出场周期', 'default': '10', 'description': '出场信号计算周期'},
            {'name': '止损比例', 'default': '0.02', 'description': '止损比例（基于入场价）'}
        ],
        'pros_cons': '''
**优点：**
- 系统性强，纪律严格
- 能够捕捉大趋势
- 经过历史验证

**缺点：**
- 需要承受较大的短期回撤
- 趋势跟踪策略的通病——胜率较低
- 需要严格执行交易系统
''',
        'code_example': '''
import pandas as pd
import numpy as np

def turtle_strategy(df, entry_period=20, exit_period=10, risk_level=0.02):
    """
    海龟交易策略
    
    参数:
        df: 包含高、低、收盘价的DataFrame
        entry_period: 入场信号周期
        exit_period: 出场信号周期
        risk_level: 单笔风险敞口比例
    """
    # 计算唐奇安通道
    df['entry_high'] = df['high'].rolling(window=entry_period).max()  # 入场最高价
    df['entry_low'] = df['low'].rolling(window=entry_period).min()    # 入场最低价
    df['exit_high'] = df['high'].rolling(window=exit_period).max()    # 出场最高价
    df['exit_low'] = df['low'].rolling(window=exit_period).min()      # 出场最低价
    
    # 计算ATR（用于仓位管理）
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    # 生成交易信号
    df['signal'] = 0  # 0: 空仓, 1: 多头, -1: 空头
    
    # 初始状态为空仓
    position = 0
    
    for i in range(entry_period, len(df)):
        if position == 0:  # 空仓状态
            # 检查入场信号
            if df['close'].iloc[i] > df['entry_high'].iloc[i-1]:
                position = 1  # 多头入场
                entry_price = df['close'].iloc[i]
                stop_loss = entry_price * (1 - risk_level)
            elif df['close'].iloc[i] < df['entry_low'].iloc[i-1]:
                position = -1  # 空头入场
                entry_price = df['close'].iloc[i]
                stop_loss = entry_price * (1 + risk_level)
        elif position == 1:  # 多头持仓
            # 检查出场或止损信号
            if df['close'].iloc[i] < df['exit_low'].iloc[i-1]:
                position = 0  # 多头出场
            elif df['close'].iloc[i] < stop_loss:
                position = 0  # 止损出局
        elif position == -1:  # 空头持仓
            # 检查出场或止损信号
            if df['close'].iloc[i] > df['exit_high'].iloc[i-1]:
                position = 0  # 空头出场
            elif df['close'].iloc[i] > stop_loss:
                position = 0  # 止损出局
        
        df.loc[df.index[i], 'signal'] = position
    
    return df
'''
    }
}

# 风险提示
RISK_WARNINGS = [
    {
        'id': 'market_risk',
        'title': '市场风险',
        'icon': 'fa-line-chart',
        'content': '''
**市场风险**是指由于市场行情波动导致投资损失的风险。

**主要表现：**
- 股票价格整体下跌造成的亏损
- 行业周期性波动带来的风险
- 市场流动性不足导致的变现困难

**应对措施：**
- 分散投资，降低单一资产风险
- 设置止损点，控制最大亏损
- 保持适当现金储备
- 定期平衡资产配置
'''
    },
    {
        'id': 'model_risk',
        'title': '模型风险',
        'icon': 'fa-cogs',
        'content': '''
**模型风险**是指由于量化模型本身的缺陷导致的损失风险。

**主要表现：**
- 模型假设与实际情况不符
- 历史数据不代表未来表现
- 参数过拟合导致实盘失效
- 市场结构变化使模型失效

**应对措施：**
- 不断验证和优化模型
- 使用多个不相关策略分散风险
- 留有足够的安全边际
- 实时监控模型表现
'''
    },
    {
        'id': 'liquidity_risk',
        'title': '流动性风险',
        'icon': 'fa-tint',
        'content': '''
**流动性风险**是指无法在合理价格买入或卖出资产的风险。

**主要表现：**
- 大额订单难以成交
- 买卖价差扩大
- 价格波动剧烈

**应对措施：**
- 投资高流动性的大盘股
- 控制单笔交易规模
- 合理安排交易时机
- 避免投资冷门标的
'''
    },
    {
        'id': 'leverage_risk',
        'title': '杠杆风险',
        'icon': 'fa-balance-scale',
        'content': '''
**杠杆风险**是指使用融资融券等杠杆工具放大了亏损的风险。

**主要表现：**
- 亏损被杠杆比例放大
- 可能面临强制平仓
- 利息费用侵蚀收益

**应对措施：**
- 谨慎使用杠杆，控制杠杆比例
- 预留足够保证金
- 设置严格的止损线
- 充分了解杠杆产品特性
'''
    },
    {
        'id': 'operation_risk',
        'title': '操作风险',
        'icon': 'fa-keyboard-o',
        'content': '''
**操作风险**是指由于人为错误或系统故障导致的损失风险。

**主要表现：**
- 交易指令输入错误
- 系统故障导致无法交易
- 风控措施未能执行

**应对措施：**
- 完善交易流程审核
- 定期检查交易系统
- 设置交易限额和熔断机制
- 建立应急预案
'''
    },
    {
        'id': 'black_swan',
        'title': '黑天鹅事件',
        'icon': 'fa-exclamation-triangle',
        'content': '''
**黑天鹅事件**是指极其罕见的、无法预测的重大事件。

**主要表现：**
- 突发性政治事件
- 全球性金融危机
- 自然灾害
- 疫情爆发

**应对措施：**
- 始终保持风险意识
- 不要重仓单一资产
- 设置合理的止损点
- 保持资产多样性
'''
    }
]

# 常见问题FAQ
FAQ_DATA = [
    {
        'id': 'q1',
        'question': '量化投资适合普通投资者吗？',
        'answer': '''
量化投资并不仅仅是专业机构的专利。随着编程工具的普及和学习资源的丰富，个人投资者也可以学习和使用量化投资方法。但需要注意：

1. **学习曲线**：需要具备一定的金融知识和编程能力
2. **资金规模**：量化策略通常需要一定的资金规模来分摊固定成本
3. **风险管理**：无论使用何种方法，风险管理都是最重要的

对于初学者，建议从简单的技术分析策略开始，逐步学习和积累经验。
''',
        'category': '入门'
    },
    {
        'id': 'q2',
        'question': '量化策略回测表现好，实盘一定赚钱吗？',
        'answer': '''
这是一个非常重要的问题。**答案是否定的**，回测表现好不代表实盘一定能赚钱，原因包括：

1. **过拟合**：策略可能过度适应历史数据中的噪声
2. **未来函数**：回测中可能不小心使用了未来数据
3. **交易成本**：实盘中的手续费、滑点可能比预估的高
4. **市场变化**：历史规律在未来可能失效
5. **流动性问题**：大资金无法按照回测价格成交
6. **心理因素**：实盘中的情绪影响可能比想象中大

因此，实盘前应进行充分的验证和控制风险。
''',
        'category': '策略'
    },
    {
        'id': 'q3',
        'question': '如何选择合适的量化回测平台？',
        'answer': '''
选择回测平台时需要考虑以下因素：

1. **数据质量**：数据的准确性、完整性和及时性
2. **回测精度**：是否支持分钟级、tick级回测
3. **功能丰富度**：是否支持多种策略类型和风控功能
4. **仿真交易**：是否支持纸盘交易模拟实盘
5. **费用**：平台使用成本
6. **技术门槛**：是否支持Python等高级语言

常见的平台包括：聚宽、米筐、优矿、掘金量化等开源和商业平台。
''',
        'category': '工具'
    },
    {
        'id': 'q4',
        'question': '散户如何获取股票数据？',
        'answer': '''
散户获取股票数据有以下几种途径：

1. **免费数据接口**：
   - Tushare：国内最流行的免费金融数据接口
   - AKShare：开源财经数据接口库
   - baostock：免费证券数据接口

2. **券商数据**：部分券商提供API接口

3. **手动获取**：通过东方财富、新浪财经等网站手动下载

4. **购买数据**：专业数据服务商提供更完整的数据

建议初学者从Tushare或AKShare开始，数据质量较好且免费。
''',
        'category': '数据'
    },
    {
        'id': 'q5',
        'question': '量化投资需要学习编程吗？',
        'answer': '''
量化投资本质上是将投资思路程序化，因此编程是必要的技能。但具体程度取决于你的目标：

1. **使用现成平台**：如果只想使用已有的量化平台，不需要深入编程，只需学习如何设置策略参数

2. **半自动化交易**：需要学习基本的Python或量化平台脚本语言

3. **完全自主开发**：需要系统学习Python、数据分析、机器学习等

**建议学习路径**：
- Python基础语法
- Pandas数据处理
- 数据库操作
- 量化交易框架使用

编程技能会大大扩展你的量化投资能力边界。
''',
        'category': '入门'
    },
    {
        'id': 'q6',
        'question': '量化策略的年化收益多少才合理？',
        'answer': '''
量化策略的收益期望取决于多个因素：

1. **策略类型**：
   - 高频策略：收益稳定但容量有限
   - 中频策略：收益适中
   - 低频策略：收益波动较大

2. **市场环境**：不同市场环境下收益差异很大

3. **风险水平**：高收益通常伴随高风险

**一般参考**：
- 稳健型策略：年化10-20%
- 进取型策略：年化20-50%
- 高风险策略：可能更高但回撤也更大

**重要提示**：不要被过高的收益承诺所迷惑，警惕庞氏骗局。合理的收益预期是长期稳定复利增长。
''',
        'category': '策略'
    },
    {
        'id': 'q7',
        'question': '如何避免量化策略的过拟合？',
        'answer': '''
过拟合是量化策略开发中最常见的问题之一。以下是避免过拟合的方法：

1. **留出验证集**：将数据分为训练集和测试集，在训练集上开发策略，在测试集上验证

2. **简化模型**：参数越少越不容易过拟合

3. **增加样本量**：更多数据能减少过拟合风险

4. **使用交叉验证**：多次随机划分数据进行验证

5. **正则化**：在损失函数中加入惩罚项

6. **观察曲线**：如果回测曲线过于完美，很可能是过拟合

7. **样本外跟踪**：实盘后持续跟踪策略表现

记住：简单的策略往往比复杂的策略更稳健。
''',
        'category': '策略'
    },
    {
        'id': 'q8',
        'question': '散户做量化有哪些局限性？',
        'answer': '''
散户做量化确实存在一些局限性：

1. **数据限制**：
   - 无法获得高质量的tick数据
   - 缺乏基本面和另类数据
   - 数据处理能力有限

2. **计算资源**：
   - 无法运行复杂模型
   - 回测速度慢

3. **交易成本**：
   - 难以获得低佣金
   - 滑点可能较高

4. **策略容量**：
   - 小资金策略可能无法扩展

**但散户也有优势**：
- 资金量小，船小好调头
- 决策灵活，无需审批流程
- 可以尝试高频交易

关键在于选择适合自己资源和能力的策略类型。
''',
        'category': '入门'
    }
]

# 获取所有教程列表
def get_tutorials_list():
    """获取教程列表"""
    return [
        {
            'id': t['id'],
            'title': t['title'],
            'category': t['category'],
            'description': t['description'],
            'level': t['level']
        }
        for t in TUTORIALS.values()
    ]

# 获取单个教程内容
def get_tutorial(tutorial_id):
    """获取教程详情"""
    return TUTORIALS.get(tutorial_id)

# 获取所有指标列表
def get_indicators_list():
    """获取指标列表"""
    return [
        {
            'id': i['id'],
            'name': i['name'],
            'category': i['category'],
            'description': i['description']
        }
        for i in INDICATORS.values()
    ]

# 获取单个指标详情
def get_indicator(indicator_id):
    """获取指标详情"""
    return INDICATORS.get(indicator_id)

# 获取所有策略列表
def get_strategies_list():
    """获取策略列表"""
    return [
        {
            'id': s['id'],
            'name': s['name'],
            'category': s['category'],
            'difficulty': s['difficulty'],
            'description': s['description']
        }
        for s in STRATEGIES.values()
    ]

# 获取单个策略详情
def get_strategy(strategy_id):
    """获取策略详情"""
    return STRATEGIES.get(strategy_id)

# 获取风险提示
def get_risk_warnings():
    """获取所有风险提示"""
    return RISK_WARNINGS

# 获取FAQ
def get_faq():
    """获取所有FAQ"""
    return FAQ_DATA
