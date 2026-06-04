# -*- coding: utf-8 -*-
"""
多因子分析模块

提供多因子模型的构建、分析和股票筛选功能
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class FactorBase:
    """因子基类"""
    
    def __init__(self, name: str, category: str, description: str = ""):
        self.name = name
        self.category = category
        self.description = description
    
    def calculate(self, stock_data: Dict[str, Any]) -> float:
        """计算因子值"""
        raise NotImplementedError("子类必须实现calculate方法")
    
    def normalize(self, values: np.ndarray) -> np.ndarray:
        """标准化因子值"""
        if len(values) == 0:
            return values
        mean = np.nanmean(values)
        std = np.nanstd(values)
        if std == 0:
            return np.zeros_like(values)
        return (values - mean) / std


class ValuationFactor(FactorBase):
    """估值因子"""
    
    def __init__(self, factor_type: str = 'PE'):
        """
        初始化估值因子
        
        Args:
            factor_type: 估值类型，'PE', 'PB', 'PS' 之一
        """
        self.factor_type = factor_type.upper()
        descriptions = {
            'PE': '市盈率因子，衡量股价与每股收益的比值',
            'PB': '市净率因子，衡量股价与每股净资产的比值',
            'PS': '市销率因子，衡量股价与每股销售额的比值'
        }
        super().__init__(
            name=f'{factor_type.upper()}估值因子',
            category='valuation',
            description=descriptions.get(factor_type.upper(), '')
        )
    
    def calculate(self, stock_data: Dict[str, Any]) -> float:
        """
        计算估值因子值
        
        Args:
            stock_data: 包含财务数据的字典
            
        Returns:
            因子值（负数表示低估值，便于与其他因子方向一致）
        """
        try:
            if self.factor_type == 'PE':
                pe = stock_data.get('pe_ratio', None)
                if pe is not None and pe > 0:
                    return -1 / pe  # 负数表示低PE（高价值）
                return 0
            elif self.factor_type == 'PB':
                pb = stock_data.get('pb_ratio', None)
                if pb is not None and pb > 0:
                    return -1 / pb  # 负数表示低PB（高价值）
                return 0
            elif self.factor_type == 'PS':
                ps = stock_data.get('ps_ratio', None)
                if ps is not None and ps > 0:
                    return -1 / ps  # 负数表示低PS（高价值）
                return 0
            return 0
        except Exception as e:
            logger.warning(f"计算{self.factor_type}因子失败: {e}")
            return 0


class GrowthFactor(FactorBase):
    """成长因子"""
    
    def __init__(self, factor_type: str = 'revenue'):
        """
        初始化成长因子
        
        Args:
            factor_type: 成长类型，'revenue'（营收增长）或 'profit'（利润增长）
        """
        self.factor_type = factor_type.lower()
        descriptions = {
            'revenue': '营收增长率因子，衡量营业收入同比增长率',
            'profit': '净利润增长率因子，衡量净利润同比增长率'
        }
        super().__init__(
            name=f"{'营收' if factor_type.lower() == 'revenue' else '净利润'}增长因子",
            category='growth',
            description=descriptions.get(factor_type.lower(), '')
        )
    
    def calculate(self, stock_data: Dict[str, Any]) -> float:
        """
        计算成长因子值
        
        Args:
            stock_data: 包含财务数据的字典
            
        Returns:
            增长率因子值
        """
        try:
            if self.factor_type == 'revenue':
                growth = stock_data.get('revenue_growth', 0)
                return growth if growth is not None else 0
            elif self.factor_type == 'profit':
                growth = stock_data.get('profit_growth', 0)
                return growth if growth is not None else 0
            return 0
        except Exception as e:
            logger.warning(f"计算{self.factor_type}增长因子失败: {e}")
            return 0


class QualityFactor(FactorBase):
    """质量因子"""
    
    def __init__(self, factor_type: str = 'ROE'):
        """
        初始化质量因子
        
        Args:
            factor_type: 质量类型，'ROE'（净资产收益率）或 'margin'（毛利率）
        """
        self.factor_type = factor_type.upper()
        descriptions = {
            'ROE': '净资产收益率因子，衡量股东权益的收益水平',
            'MARGIN': '毛利率因子，衡量销售收入的盈利水平'
        }
        super().__init__(
            name=f"{'ROE' if factor_type.upper() == 'ROE' else '毛利率'}质量因子",
            category='quality',
            description=descriptions.get(factor_type.upper(), '')
        )
    
    def calculate(self, stock_data: Dict[str, Any]) -> float:
        """
        计算质量因子值
        
        Args:
            stock_data: 包含财务数据的字典
            
        Returns:
            质量因子值
        """
        try:
            if self.factor_type == 'ROE':
                roe = stock_data.get('roe', 0)
                return roe if roe is not None else 0
            elif self.factor_type == 'MARGIN':
                margin = stock_data.get('gross_margin', 0)
                return margin if margin is not None else 0
            return 0
        except Exception as e:
            logger.warning(f"计算{self.factor_type}质量因子失败: {e}")
            return 0


class TechnicalFactor(FactorBase):
    """技术因子"""
    
    def __init__(self, factor_type: str = 'momentum'):
        """
        初始化技术因子
        
        Args:
            factor_type: 技术类型，'momentum'（动量）或 'volatility'（波动率）
        """
        self.factor_type = factor_type.lower()
        descriptions = {
            'momentum': '动量因子，衡量股票过去一段时间的涨跌趋势',
            'volatility': '波动率因子，衡量股票价格波动的剧烈程度'
        }
        super().__init__(
            name=f"{'动量' if factor_type.lower() == 'momentum' else '波动率'}技术因子",
            category='technical',
            description=descriptions.get(factor_type.lower(), '')
        )
    
    def calculate(self, stock_data: Dict[str, Any]) -> float:
        """
        计算技术因子值
        
        Args:
            stock_data: 包含市场数据的字典
            
        Returns:
            技术因子值
        """
        try:
            if self.factor_type == 'momentum':
                momentum = stock_data.get('momentum', 0)
                return momentum if momentum is not None else 0
            elif self.factor_type == 'volatility':
                volatility = stock_data.get('volatility', 0)
                return -volatility if volatility is not None else 0  # 负数表示低波动（偏好）
            return 0
        except Exception as e:
            logger.warning(f"计算{self.factor_type}技术因子失败: {e}")
            return 0


class FactorAnalysis:
    """多因子分析引擎"""
    
    def __init__(self):
        self.factors: List[FactorBase] = []
        self.factor_weights: Dict[str, float] = {}
        self.stock_data: pd.DataFrame = None
    
    def add_factor(self, factor: FactorBase, weight: float = 1.0):
        """添加因子及其权重"""
        self.factors.append(factor)
        self.factor_weights[factor.name] = weight
        logger.info(f"添加因子: {factor.name}, 权重: {weight}")
    
    def remove_factor(self, factor_name: str):
        """移除因子"""
        self.factors = [f for f in self.factors if f.name != factor_name]
        if factor_name in self.factor_weights:
            del self.factor_weights[factor_name]
    
    def set_weights(self, weights: Dict[str, float]):
        """设置因子权重"""
        for name, weight in weights.items():
            if name in self.factor_weights:
                self.factor_weights[name] = weight
    
    def calculate_composite_score(self, stock_data: Dict[str, Dict[str, Any]], 
                                   stock_list: List[str]) -> pd.DataFrame:
        """
        计算股票的综合因子得分
        
        Args:
            stock_data: 股票数据字典，格式 {stock_code: {factor_name: value, ...}}
            stock_list: 股票代码列表
            
        Returns:
            包含股票代码和综合得分的DataFrame
        """
        results = []
        
        for stock_code in stock_list:
            if stock_code not in stock_data:
                continue
                
            data = stock_data[stock_code]
            weighted_score = 0
            total_weight = 0
            
            for factor in self.factors:
                factor_value = factor.calculate(data)
                weight = self.factor_weights.get(factor.name, 1.0)
                weighted_score += factor_value * weight
                total_weight += weight
            
            if total_weight > 0:
                composite_score = weighted_score / total_weight
            else:
                composite_score = 0
            
            results.append({
                'stock_code': stock_code,
                'stock_name': data.get('name', stock_code),
                'composite_score': composite_score
            })
        
        return pd.DataFrame(results)
    
    def calculate_ic_ir(self, factor_returns: pd.DataFrame, 
                         forward_returns: pd.Series,
                         factor_name: str) -> Dict[str, float]:
        """
        计算因子的IC值和IR值
        
        Args:
            factor_returns: 因子值序列
            forward_returns: 未来收益序列
            factor_name: 因子名称
            
        Returns:
            包含IC值、IR值等指标的字典
        """
        try:
            # 计算横截面相关性（IC）
            ic = factor_returns.corr(forward_returns)
            
            # 计算IC序列
            ic_series = []
            for date in factor_returns.index:
                if date in forward_returns.index:
                    f_ret = factor_returns.loc[date]
                    f_ret_val = forward_returns.loc[date]
                    if not (np.isnan(f_ret) or np.isnan(f_ret_val)):
                        ic_series.append(f_ret * f_ret_val)
            
            ic_mean = np.nanmean(ic_series) if ic_series else 0
            ic_std = np.nanstd(ic_series) if len(ic_series) > 1 else 0
            
            # IR = IC均值 / IC标准差
            ir = ic_mean / ic_std if ic_std > 0 else 0
            
            return {
                'factor_name': factor_name,
                'ic': float(ic) if not np.isnan(ic) else 0,
                'ic_mean': float(ic_mean),
                'ic_std': float(ic_std),
                'ir': float(ir),
                'cum_ic': float(np.nancumsum(ic_series)[-1]) if ic_series else 0
            }
        except Exception as e:
            logger.error(f"计算IC/IR失败: {e}")
            return {
                'factor_name': factor_name,
                'ic': 0,
                'ic_mean': 0,
                'ic_std': 0,
                'ir': 0,
                'cum_ic': 0
            }
    
    def orthogonalize(self, factors_df: pd.DataFrame, target_factor: str) -> pd.Series:
        """
        对因子进行正交化处理，去除与其他因子的相关性
        
        Args:
            factors_df: 因子值DataFrame
            target_factor: 目标因子名称
            
        Returns:
            正交化后的因子值序列
        """
        try:
            if target_factor not in factors_df.columns:
                return factors_df[target_factor]
            
            # 使用剩余法正交化
            y = factors_df[target_factor].values
            other_factors = [col for col in factors_df.columns if col != target_factor]
            
            if not other_factors:
                return factors_df[target_factor]
            
            X = factors_df[other_factors].values
            
            # 去除NaN值
            valid_mask = ~(np.isnan(y) | np.any(np.isnan(X), axis=1))
            if not valid_mask.any():
                return factors_df[target_factor]
            
            y_valid = y[valid_mask]
            X_valid = X[valid_mask]
            
            # 简单线性回归
            try:
                coeffs = np.linalg.lstsq(X_valid, y_valid, rcond=None)[0]
                predicted = X_valid @ coeffs
                residuals = y_valid - predicted
                
                # 将结果放回原位置
                result = np.full_like(y, np.nan)
                result[valid_mask] = residuals
                return pd.Series(result, index=factors_df.index)
            except:
                return factors_df[target_factor]
                
        except Exception as e:
            logger.error(f"因子正交化失败: {e}")
            return factors_df[target_factor]
    
    def calculate_factor_returns(self, factor_quantiles: pd.DataFrame, 
                                 returns: pd.Series,
                                 n_quantiles: int = 5) -> pd.DataFrame:
        """
        计算因子收益率（多空组合收益）
        
        Args:
            factor_quantiles: 因子分位数分组
            returns: 收益率序列
            n_quantiles: 分位数数量
            
        Returns:
            因子收益率统计
        """
        results = []
        
        for date in factor_quantiles.index:
            if date not in returns.index:
                continue
                
            daily_return = returns.loc[date]
            
            for quantile in range(1, n_quantiles + 1):
                key = f'Q{quantile}'
                if key not in factor_quantiles.columns:
                    continue
                    
                stocks_in_quantile = factor_quantiles.loc[date, key]
                if isinstance(stocks_in_quantile, str):
                    stocks_in_quantile = [stocks_in_quantile]
                
                # 这里简化处理，实际应该用加权平均
                if len(stocks_in_quantile) > 0:
                    results.append({
                        'date': date,
                        'quantile': quantile,
                        'return': daily_return / len(stocks_in_quantile)
                    })
        
        if not results:
            return pd.DataFrame()
        
        result_df = pd.DataFrame(results)
        
        # 计算各分组的累积收益
        summary = []
        for quantile in range(1, n_quantiles + 1):
            q_returns = result_df[result_df['quantile'] == quantile]['return']
            if len(q_returns) > 0:
                cum_return = (1 + q_returns).prod() - 1
                summary.append({
                    'quantile': f'Q{quantile}',
                    'mean_return': q_returns.mean(),
                    'std_return': q_returns.std(),
                    'cum_return': cum_return,
                    'win_rate': (q_returns > 0).mean()
                })
        
        return pd.DataFrame(summary)
    
    def rank_stocks(self, stock_data: Dict[str, Dict[str, Any]], 
                    stock_list: List[str],
                    n: int = 50,
                    ascending: bool = False) -> pd.DataFrame:
        """
        根据因子综合得分对股票排名
        
        Args:
            stock_data: 股票数据字典
            stock_list: 股票代码列表
            n: 返回前n名股票
            ascending: 是否升序排列（False表示降序，分数高的排名靠前）
            
        Returns:
            排名后的股票列表
        """
        scores_df = self.calculate_composite_score(stock_data, stock_list)
        
        if scores_df.empty:
            return pd.DataFrame()
        
        # 按综合得分排序
        scores_df = scores_df.sort_values('composite_score', ascending=ascending)
        
        # 添加排名
        scores_df['rank'] = range(1, len(scores_df) + 1)
        
        # 返回前n名
        return scores_df.head(n)
    
    def get_factor_validity_report(self, stock_data: Dict[str, Dict[str, Any]],
                                    returns_data: Dict[str, float]) -> Dict[str, Any]:
        """
        生成因子有效性分析报告
        
        Args:
            stock_data: 股票因子数据
            returns_data: 股票收益率数据
            
        Returns:
            因子有效性报告
        """
        report = {
            'factors': [],
            'summary': {}
        }
        
        stock_list = list(stock_data.keys())
        
        for factor in self.factors:
            factor_values = []
            stock_returns = []
            
            for stock_code in stock_list:
                if stock_code in returns_data:
                    value = factor.calculate(stock_data[stock_code])
                    factor_values.append(value)
                    stock_returns.append(returns_data[stock_code])
            
            if len(factor_values) < 3:
                continue
            
            # 计算IC
            ic = np.corrcoef(factor_values, stock_returns)[0, 1]
            
            factor_info = {
                'name': factor.name,
                'category': factor.category,
                'description': factor.description,
                'weight': self.factor_weights.get(factor.name, 1.0),
                'ic': float(ic) if not np.isnan(ic) else 0,
                'ic_abs': float(abs(ic)) if not np.isnan(ic) else 0
            }
            report['factors'].append(factor_info)
        
        # 计算综合评分
        if report['factors']:
            avg_ic = np.mean([f['ic'] for f in report['factors']])
            avg_ic_abs = np.mean([f['ic_abs'] for f in report['factors']])
            report['summary'] = {
                'avg_ic': avg_ic,
                'avg_ic_abs': avg_ic_abs,
                'factor_count': len(report['factors']),
                'validity': '高' if avg_ic_abs > 0.05 else ('中' if avg_ic_abs > 0.02 else '低')
            }
        
        return report


def create_default_factors() -> FactorAnalysis:
    """
    创建默认的多因子分析实例，包含常用因子
    
    Returns:
        配置好的FactorAnalysis实例
    """
    analyzer = FactorAnalysis()
    
    # 估值因子
    analyzer.add_factor(ValuationFactor('PE'), weight=0.2)
    analyzer.add_factor(ValuationFactor('PB'), weight=0.1)
    analyzer.add_factor(ValuationFactor('PS'), weight=0.1)
    
    # 成长因子
    analyzer.add_factor(GrowthFactor('revenue'), weight=0.15)
    analyzer.add_factor(GrowthFactor('profit'), weight=0.15)
    
    # 质量因子
    analyzer.add_factor(QualityFactor('ROE'), weight=0.15)
    analyzer.add_factor(QualityFactor('MARGIN'), weight=0.05)
    
    # 技术因子
    analyzer.add_factor(TechnicalFactor('momentum'), weight=0.05)
    analyzer.add_factor(TechnicalFactor('volatility'), weight=0.05)
    
    return analyzer


def generate_sample_data(stock_list: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    生成模拟股票数据用于测试
    
    Args:
        stock_list: 股票代码列表
        
    Returns:
        股票因子数据字典
    """
    np.random.seed(42)
    
    from config import HOT_STOCKS
    data = {}
    stock_names = {s['code']: s['name'] for s in HOT_STOCKS}
    stock_names.update({
        '600276.SH': '恒瑞医药',
        '002594.SZ': '比亚迪',
        '600030.SH': '中信证券',
        '300750.SZ': '宁德时代',
        '688981.SH': '中芯国际'
    })
    
    # 随机种子保证可复现
    np.random.seed(42)
    for stock_code in stock_list:
        data[stock_code] = {
            'name': stock_names.get(stock_code, stock_code),
            'pe_ratio': np.random.uniform(5, 50),
            'pb_ratio': np.random.uniform(0.5, 5),
            'ps_ratio': np.random.uniform(0.5, 10),
            'revenue_growth': np.random.uniform(-0.2, 0.5),
            'profit_growth': np.random.uniform(-0.3, 0.6),
            'roe': np.random.uniform(0.05, 0.25),
            'gross_margin': np.random.uniform(0.2, 0.8),
            'momentum': np.random.uniform(-0.3, 0.3),
            'volatility': np.random.uniform(0.1, 0.5)
        }
    
    return data


def generate_sample_returns(stock_list: List[str]) -> Dict[str, float]:
    """
    生成模拟收益率数据用于测试
    
    Args:
        stock_list: 股票代码列表
        
    Returns:
        股票收益率字典
    """
    np.random.seed(42)
    
    returns = {}
    for stock_code in stock_list:
        returns[stock_code] = np.random.uniform(-0.3, 0.5)
    
    return returns
