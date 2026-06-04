import numpy as np
import pandas as pd


def calculate_performance_attribution(holdings, benchmark_returns, portfolio_returns):
    """
    计算投资组合绩效归因
    
    Args:
        holdings (list): 持仓列表，每个元素包含 symbol, name, allocation
        benchmark_returns (np.array): 基准收益率序列
        portfolio_returns (np.array): 投资组合收益率序列
    
    Returns:
        dict: 绩效归因结果
    """
    # 计算超额收益
    excess_returns = portfolio_returns - benchmark_returns
    total_excess_return = np.sum(excess_returns)
    
    # 计算资产配置归因（Brinson模型）
    allocation_effect = 0
    selection_effect = 0
    interaction_effect = 0
    
    # 模拟每个资产类别的收益率
    asset_returns = {}
    benchmark_asset_returns = {}
    
    # 为每个持仓生成模拟收益率
    for holding in holdings:
        # 生成与投资组合相关性较高的收益率
        correlation = 0.7 + 0.3 * np.random.random()
        noise = np.random.normal(0, 0.01, len(portfolio_returns))
        asset_return = correlation * portfolio_returns + noise
        asset_returns[holding['symbol']] = asset_return
        
        # 生成与基准相关性较高的收益率
        benchmark_noise = np.random.normal(0, 0.01, len(benchmark_returns))
        benchmark_asset_return = correlation * benchmark_returns + benchmark_noise
        benchmark_asset_returns[holding['symbol']] = benchmark_asset_return
    
    # 计算归因效果
    for holding in holdings:
        weight_p = holding['allocation'] / 100
        # 假设基准权重为市场平均
        weight_b = 1.0 / len(holdings)
        
        return_p = np.mean(asset_returns[holding['symbol']])
        return_b = np.mean(benchmark_asset_returns[holding['symbol']])
        
        # 资产配置效果
        allocation_effect += (weight_p - weight_b) * return_b
        
        # 证券选择效果
        selection_effect += weight_b * (return_p - return_b)
        
        # 交互效果
        interaction_effect += (weight_p - weight_b) * (return_p - return_b)
    
    # 计算时间序列归因
    attribution_timeseries = []
    for i in range(len(portfolio_returns)):
        date = pd.Timestamp('2026-01-01') + pd.Timedelta(days=i)
        attribution_timeseries.append({
            'date': date.strftime('%Y-%m-%d'),
            'portfolio_return': portfolio_returns[i] * 100,
            'benchmark_return': benchmark_returns[i] * 100,
            'excess_return': excess_returns[i] * 100
        })
    
    # 计算行业归因
    sector_attribution = []
    sectors = ['科技', '金融', '消费', '医药', '能源', '材料']
    for sector in sectors:
        # 模拟行业归因数据
        sector_attribution.append({
            'sector': sector,
            'allocation_effect': (np.random.random() - 0.5) * 0.02,
            'selection_effect': (np.random.random() - 0.5) * 0.02,
            'total_effect': (np.random.random() - 0.5) * 0.04
        })
    
    return {
        'total_excess_return': total_excess_return * 100,
        'allocation_effect': allocation_effect * 100,
        'selection_effect': selection_effect * 100,
        'interaction_effect': interaction_effect * 100,
        'attribution_timeseries': attribution_timeseries,
        'sector_attribution': sector_attribution,
        'holdings_attribution': [
            {
                'symbol': holding['symbol'],
                'name': holding['name'],
                'allocation': holding['allocation'],
                'contribution': (np.random.random() - 0.3) * 0.05 * 100
            }
            for holding in holdings
        ]
    }


def calculate_factor_attribution(portfolio_returns, factors):
    """
    计算因子归因
    
    Args:
        portfolio_returns (np.array): 投资组合收益率序列
        factors (dict): 因子收益率序列
    
    Returns:
        dict: 因子归因结果
    """
    # 模拟因子暴露
    factor_exposures = {
        '市场': 0.8 + 0.4 * np.random.random(),
        '规模': -0.2 + 0.4 * np.random.random(),
        '价值': 0.3 + 0.4 * np.random.random(),
        '动量': 0.1 + 0.4 * np.random.random(),
        '质量': 0.4 + 0.4 * np.random.random()
    }
    
    # 计算因子贡献
    factor_contributions = {}
    total_factor_contribution = 0
    
    for factor_name, exposure in factor_exposures.items():
        if factor_name in factors:
            factor_return = np.mean(factors[factor_name])
            contribution = exposure * factor_return
            factor_contributions[factor_name] = contribution * 100
            total_factor_contribution += contribution
    
    # 计算残差
    total_return = np.mean(portfolio_returns)
    residual = total_return - total_factor_contribution
    
    return {
        'factor_contributions': factor_contributions,
        'residual': residual * 100,
        'total_return': total_return * 100
    }
