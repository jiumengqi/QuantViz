import numpy as np
from scipy import stats

def calculate_var(returns, confidence_level=0.95, time_horizon=1, method='historical', simulations=10000):
    """
    计算风险价值(Value at Risk)
    
    参数:
    returns: 收益率数据数组
    confidence_level: 置信水平，默认为95%
    time_horizon: 时间范围（天），默认为1天
    method: 计算方法，可选值为'historical'（历史模拟法）、'parametric'（参数法）、'monte_carlo'（蒙特卡洛模拟法），默认为'historical'
    simulations: 蒙特卡洛模拟的次数，默认为10000
    
    返回:
    VaR值
    """
    try:
        if method.lower() == 'historical':
            # 历史模拟法：使用历史收益率的分位数
            var = -np.percentile(returns, (1 - confidence_level) * 100)
        elif method.lower() == 'parametric':
            # 方差-协方差法（参数法，假设收益率服从正态分布）
            mean_return = np.mean(returns)
            std_return = np.std(returns, ddof=0)
            # 使用正态分布的理论分位数（如95%置信度对应1.645）
            z_score = stats.norm.ppf(1 - confidence_level)  # 负值
            var = -(mean_return + z_score * std_return)
        elif method.lower() == 'monte_carlo':
            # 蒙特卡洛模拟法
            mean_return = np.mean(returns)
            std_return = np.std(returns, ddof=0)
            # 生成模拟收益率（基于正态分布假设）
            simulated_returns = np.random.normal(mean_return, std_return, simulations)
            var = -np.percentile(simulated_returns, (1 - confidence_level) * 100)
        else:
            raise ValueError("计算方法必须是'historical'、'parametric'或'monte_carlo'")
        
        # 根据时间范围调整VaR（平方根法则）
        var *= np.sqrt(time_horizon)
        
        return float(var)
    except Exception as e:
        print(f"VaR计算错误: {e}")
        # 返回模拟结果作为备选
        if len(returns) > 0:
            return float(np.std(returns) * 1.65 * np.sqrt(time_horizon))
        return 0.02  # 2%的默认风险值

def calculate_cvar(returns, confidence_level=0.95, time_horizon=1, method='historical', simulations=10000):
    """
    计算条件风险价值(Conditional Value at Risk, CVaR)，也称为预期尾部损失(Expected Tail Loss)
    
    参数:
    returns: 收益率数据数组
    confidence_level: 置信水平，默认为95%
    time_horizon: 时间范围（天），默认为1天
    method: 计算方法，可选值为'historical'（历史模拟法）、'parametric'（参数法）、'monte_carlo'（蒙特卡洛模拟法），默认为'historical'
    simulations: 蒙特卡洛模拟的次数，默认为10000
    
    返回:
    CVaR值
    """
    try:
        if method.lower() == 'historical':
            # 历史模拟法：取尾部数据的平均值
            var_threshold = np.percentile(returns, (1 - confidence_level) * 100)
            tail_returns = returns[returns <= var_threshold]
            if len(tail_returns) == 0:
                tail_returns = returns
            cvar = -np.mean(tail_returns)
        elif method.lower() == 'parametric':
            # 参数法（假设收益率服从正态分布）
            mean_return = np.mean(returns)
            std_return = np.std(returns, ddof=0)
            z_score = stats.norm.ppf(1 - confidence_level)  # 负值
            # 理论CVaR：对于正态分布，CVaR = -mean - sigma * phi(z) / (1-alpha) / sqrt(T)
            # 其中 phi 是标准正态PDF
            pdf_z = stats.norm.pdf(z_score)
            alpha = 1 - confidence_level
            # 单日CVaR
            cvar = -(mean_return - std_return * pdf_z / alpha)
        elif method.lower() == 'monte_carlo':
            # 蒙特卡洛模拟法
            mean_return = np.mean(returns)
            std_return = np.std(returns, ddof=0)
            simulated_returns = np.random.normal(mean_return, std_return, simulations)
            var_threshold = np.percentile(simulated_returns, (1 - confidence_level) * 100)
            tail_returns = simulated_returns[simulated_returns <= var_threshold]
            if len(tail_returns) == 0:
                tail_returns = simulated_returns
            cvar = -np.mean(tail_returns)
        else:
            raise ValueError("计算方法必须是'historical'、'parametric'或'monte_carlo'")
        
        # 根据时间范围调整CVaR
        cvar *= np.sqrt(time_horizon)
        
        return float(cvar)
    except Exception as e:
        print(f"CVaR计算错误: {e}")
        # 返回模拟结果作为备选
        if len(returns) > 0:
            return float(np.std(returns) * 2.0 * np.sqrt(time_horizon))
        return 0.03  # 3%的默认风险值

def calculate_downside_risk(returns, target_return=0):
    """
    计算下行风险(Downside Risk)，即收益率低于目标收益率的风险
    
    参数:
    returns: 收益率数据数组
    target_return: 目标收益率，默认为0
    
    返回:
    下行风险值
    """
    try:
        # 计算低于目标收益率的部分
        downside_returns = np.minimum(returns - target_return, 0)
        # 计算下行风险（半方差的平方根）
        downside_risk = np.sqrt(np.mean(downside_returns ** 2))
        return downside_risk
    except Exception as e:
        print(f"下行风险计算错误: {e}")
        # 返回标准差作为备选
        if len(returns) > 0:
            return np.std(returns)
        return 0.02  # 2%的默认风险值

def calculate_sortino_ratio(returns, risk_free_rate=0, target_return=0):
    """
    计算索提诺比率(Sortino Ratio)，使用下行风险的夏普比率变体
    
    参数:
    returns: 收益率数据数组
    risk_free_rate: 无风险利率，默认为0
    target_return: 目标收益率，默认为0
    
    返回:
    索提诺比率
    """
    try:
        # 计算超额收益率
        excess_returns = returns - risk_free_rate
        # 计算平均超额收益率
        avg_excess_return = np.mean(excess_returns)
        # 计算下行风险
        downside_risk = calculate_downside_risk(returns, target_return)
        
        if downside_risk > 0:
            return avg_excess_return / downside_risk
        return 0
    except Exception as e:
        print(f"索提诺比率计算错误: {e}")
        return 0

def calculate_max_drawdown(returns):
    """
    计算最大回撤(Maximum Drawdown)
    
    参数:
    returns: 收益率数据数组
    
    返回:
    最大回撤值
    """
    try:
        # 计算累积收益率
        cumulative_returns = np.cumprod(1 + returns)
        # 计算累积最大值
        cumulative_max = np.maximum.accumulate(cumulative_returns)
        # 计算回撤
        drawdowns = (cumulative_returns - cumulative_max) / cumulative_max
        # 计算最大回撤
        max_drawdown = np.min(drawdowns)
        return max_drawdown
    except Exception as e:
        print(f"最大回撤计算错误: {e}")
        return 0

def calculate_kurtosis(returns):
    """
    计算收益率的峰度(Kurtosis)，衡量收益率分布的尾部厚度
    
    参数:
    returns: 收益率数据数组
    
    返回:
    峰度值
    """
    try:
        # 计算峰度
        kurtosis = np.mean(((returns - np.mean(returns)) / np.std(returns)) ** 4) - 3
        return kurtosis
    except Exception as e:
        print(f"峰度计算错误: {e}")
        return 0

def calculate_skewness(returns):
    """
    计算收益率的偏度(Skewness)，衡量收益率分布的不对称性
    
    参数:
    returns: 收益率数据数组
    
    返回:
    偏度值
    """
    try:
        # 计算偏度
        skewness = np.mean(((returns - np.mean(returns)) / np.std(returns)) ** 3)
        return skewness
    except Exception as e:
        print(f"偏度计算错误: {e}")
        return 0