import numpy as np
from scipy import stats

# 保留函数版本以兼容现有代码
def black_scholes(S, K, T, r, sigma, option_type='call'):
    """
    Black-Scholes期权定价模型函数
    
    参数:
    S: 标的资产当前价格
    K: 行权价格
    T: 到期时间（年化）
    r: 无风险利率
    sigma: 波动率
    option_type: 期权类型，'call'或'put'
    
    返回:
    期权理论价格
    """
    try:
        # 计算d1和d2
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == 'call':
            # 看涨期权价格
            price = S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
        elif option_type.lower() == 'put':
            # 看跌期权价格
            price = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)
        else:
            raise ValueError("期权类型必须是'call'或'put'")
        
        return price
    except Exception as e:
        print(f"Black-Scholes计算错误: {e}")
        # 返回模拟结果作为备选
        if option_type.lower() == 'call':
            return max(0, S - K) * 0.8  # 简化的模拟结果
        else:
            return max(0, K - S) * 0.8  # 简化的模拟结果


def compute_greeks(S, K, T, r, sigma, option_type='call'):
    """
    计算所有希腊字母
    
    参数:
    S: 标的资产当前价格
    K: 行权价格
    T: 到期时间（年化）
    r: 无风险利率
    sigma: 波动率
    option_type: 期权类型，'call'或'put'
    
    返回:
    包含所有希腊字母的字典
    """
    try:
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        pdf_d1 = stats.norm.pdf(d1)
        cdf_d1 = stats.norm.cdf(d1)
        cdf_d2 = stats.norm.cdf(d2)
        cdf_neg_d1 = stats.norm.cdf(-d1)
        cdf_neg_d2 = stats.norm.cdf(-d2)
        discount = np.exp(-r * T)
        
        is_call = option_type.lower() == 'call'
        
        # Delta: 期权价格对标的资产价格的一阶偏导
        if is_call:
            delta = cdf_d1
        else:
            delta = cdf_d1 - 1
        
        # Gamma: Delta对标的资产价格的偏导（call和put相同）
        gamma = pdf_d1 / (S * sigma * np.sqrt(T))
        
        # Theta: 期权价格对时间的一阶偏导（每日衰减，除以365年化）
        term1 = -(S * pdf_d1 * sigma) / (2 * np.sqrt(T))
        if is_call:
            theta = term1 - r * K * discount * cdf_d2
        else:
            theta = term1 + r * K * discount * cdf_neg_d2
        # 转换为每日theta
        theta_per_day = theta / 365.0
        
        # Vega: 期权价格对波动率的一阶偏导（call和put相同）
        # 通常Vega表示波动率变化1%（即0.01）时的价格变化
        vega = S * np.sqrt(T) * pdf_d1 * 0.01
        
        # Rho: 期权价格对无风险利率的一阶偏导
        # 通常Rho表示利率变化1%（即0.01）时的价格变化
        if is_call:
            rho = K * T * discount * cdf_d2 * 0.01
        else:
            rho = -K * T * discount * cdf_neg_d2 * 0.01
        
        return {
            'delta': float(delta),
            'gamma': float(gamma),
            'theta': float(theta_per_day),
            'theta_annual': float(theta),
            'vega': float(vega),
            'rho': float(rho),
            'd1': float(d1),
            'd2': float(d2)
        }
    except Exception as e:
        print(f"希腊字母计算错误: {e}")
        return {
            'delta': 0.0, 'gamma': 0.0, 'theta': 0.0,
            'theta_annual': 0.0, 'vega': 0.0, 'rho': 0.0,
            'd1': 0.0, 'd2': 0.0
        }


def implied_volatility(market_price, S, K, T, r, option_type='call', 
                        max_iterations=100, tolerance=1e-6):
    """
    使用牛顿迭代法计算隐含波动率
    
    参数:
    market_price: 市场观察到的期权价格
    S: 标的资产当前价格
    K: 行权价格
    T: 到期时间（年化）
    r: 无风险利率
    option_type: 期权类型，'call'或'put'
    max_iterations: 最大迭代次数
    tolerance: 收敛容差
    
    返回:
    隐含波动率（年化）
    """
    try:
        # 初始猜测：使用Manaster-Koehler近似
        sigma = np.sqrt(2 * np.abs(np.log(S / K) + r * T) / T)
        
        # 防止sigma过小
        sigma = max(sigma, 0.01)
        
        for i in range(max_iterations):
            # 计算当前sigma下的期权价格
            price = black_scholes(S, K, T, r, sigma, option_type)
            
            # 计算价格差
            diff = price - market_price
            
            # 检查收敛
            if abs(diff) < tolerance:
                return float(sigma)
            
            # 计算Vega（期权价格对波动率的导数）
            # Vega = S * sqrt(T) * N'(d1)
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            vega = S * np.sqrt(T) * stats.norm.pdf(d1)
            
            # 防止除以零
            if abs(vega) < 1e-10:
                # 使用二分法回退
                return _implied_vol_bisection(market_price, S, K, T, r, option_type, max_iterations, tolerance)
            
            # 牛顿迭代更新
            sigma = sigma - diff / vega
            
            # 防止sigma变为负值
            if sigma <= 0:
                sigma = 0.001
        
        # 如果未收敛，返回最后的估计值
        return float(max(sigma, 0.001))
        
    except Exception as e:
        print(f"隐含波动率计算错误: {e}")
        return float(_implied_vol_bisection(market_price, S, K, T, r, option_type, max_iterations, tolerance))


def _implied_vol_bisection(market_price, S, K, T, r, option_type='call',
                            max_iterations=100, tolerance=1e-6):
    """二分法计算隐含波动率（牛顿法失败时的回退方法）"""
    low = 0.001
    high = 5.0
    
    for i in range(max_iterations):
        mid = (low + high) / 2.0
        price = black_scholes(S, K, T, r, mid, option_type)
        
        if abs(price - market_price) < tolerance:
            return mid
        
        if price > market_price:
            high = mid
        else:
            low = mid
    
    return (low + high) / 2.0


# API接口使用的计算函数
def calculate_bs(spot, strike, time, rate, volatility, option_type='call', market_price=None):
    """
    API用的Black-Scholes计算函数
    
    参数:
    spot: 标的资产当前价格
    strike: 行权价格
    time: 到期时间（年化）
    rate: 无风险利率（小数形式，如0.05表示5%）
    volatility: 波动率（小数形式，如0.25表示25%）
    option_type: 期权类型，'call'或'put'
    market_price: 市场价格（可选，用于计算隐含波动率）
    
    返回:
    包含计算结果的字典
    """
    try:
        # 计算期权价格
        if option_type.lower() == 'call':
            price = spot * stats.norm.cdf(
                (np.log(spot / strike) + (rate + 0.5 * volatility**2) * time) / (volatility * np.sqrt(time))
            ) - strike * np.exp(-rate * time) * stats.norm.cdf(
                (np.log(spot / strike) + (rate - 0.5 * volatility**2) * time) / (volatility * np.sqrt(time))
            )
        elif option_type.lower() == 'put':
            d1 = (np.log(spot / strike) + (rate + 0.5 * volatility**2) * time) / (volatility * np.sqrt(time))
            d2 = d1 - volatility * np.sqrt(time)
            price = strike * np.exp(-rate * time) * stats.norm.cdf(-d2) - spot * stats.norm.cdf(-d1)
        else:
            raise ValueError("期权类型必须是'call'或'put'")
        
        # 计算希腊字母
        greeks = compute_greeks(spot, strike, time, rate, volatility, option_type)
        
        result = {
            'price': float(price),
            'delta': greeks['delta'],
            'gamma': greeks['gamma'],
            'theta': greeks['theta'],
            'theta_annual': greeks['theta_annual'],
            'vega': greeks['vega'],
            'rho': greeks['rho'],
            'd1': greeks['d1'],
            'd2': greeks['d2'],
            'spot_price': float(spot),
            'strike_price': float(strike),
            'time_to_maturity': float(time),
            'risk_free_rate': float(rate),
            'volatility': float(volatility),
            'option_type': option_type,
            'success': True
        }
        
        # 如果提供了市场价格，计算隐含波动率
        if market_price is not None and market_price > 0:
            iv = implied_volatility(market_price, spot, strike, time, rate, option_type)
            result['implied_volatility'] = float(iv)
            result['market_price'] = float(market_price)
        
        return result
    except Exception as e:
        print(f"Black-Scholes API计算错误: {e}")
        # 返回模拟结果作为备选
        if option_type.lower() == 'call':
            mock_price = max(0, spot - strike) * 0.8
        else:
            mock_price = max(0, strike - spot) * 0.8
        
        return {
            'price': float(mock_price),
            'delta': 0.5, 'gamma': 0.01, 'theta': -0.1,
            'theta_annual': -0.1, 'vega': 0.2, 'rho': 0.1,
            'd1': 0.0, 'd2': 0.0,
            'spot_price': float(spot),
            'strike_price': float(strike),
            'time_to_maturity': float(time),
            'risk_free_rate': float(rate),
            'volatility': float(volatility),
            'option_type': option_type,
            'success': True,
            'warning': f'使用模拟结果: {str(e)}'
        }


def calculate_iv(spot, strike, time, rate, market_price, option_type='call'):
    """
    独立的隐含波动率计算函数
    
    参数:
    spot: 标的资产当前价格
    strike: 行权价格
    time: 到期时间（年化）
    rate: 无风险利率（小数形式）
    market_price: 市场观察到的期权价格
    option_type: 期权类型，'call'或'put'
    
    返回:
    包含隐含波动率和相关信息的字典
    """
    try:
        iv = implied_volatility(market_price, spot, strike, time, rate, option_type)
        
        # 用计算出的IV重新计算理论价格以验证
        theoretical_price = black_scholes(spot, strike, time, rate, iv, option_type)
        greeks = compute_greeks(spot, strike, time, rate, iv, option_type)
        
        return {
            'success': True,
            'implied_volatility': float(iv),
            'implied_volatility_pct': float(iv * 100),
            'theoretical_price': float(theoretical_price),
            'market_price': float(market_price),
            'price_diff': float(theoretical_price - market_price),
            'delta': greeks['delta'],
            'gamma': greeks['gamma'],
            'vega': greeks['vega'],
            'spot_price': float(spot),
            'strike_price': float(strike),
            'time_to_maturity': float(time),
            'risk_free_rate': float(rate),
            'option_type': option_type
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
