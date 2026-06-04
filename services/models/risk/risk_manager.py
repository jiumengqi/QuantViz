"""
风险控制管理器
提供仓位管理、止损止盈、行业分散度控制等功能
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class PositionSizingMethod(Enum):
    """仓位分配方法"""
    FIXED = "fixed"                  # 固定仓位
    KELLY = "kelly"                  # 凯利公式
    EQUAL_WEIGHT = "equal_weight"    # 等权重
    VOLATILITY_WEIGHT = "volatility_weight"  # 波动率加权
    RISK_PARITY = "risk_parity"      # 风险平价


class StopLossType(Enum):
    """止损类型"""
    FIXED = "fixed"                  # 固定比例止损
    TRAILING = "trailing"            # 移动止损
    TIME_BASED = "time_based"        # 时间止损


class TakeProfitType(Enum):
    """止盈类型"""
    FIXED = "fixed"                  # 固定比例止盈
    TARGET = "target"                # 目标价格止盈
    TRAILING = "trailing"            # 移动止盈


@dataclass
class PositionConfig:
    """仓位配置"""
    method: PositionSizingMethod = PositionSizingMethod.FIXED
    fixed_ratio: float = 0.1         # 固定比例（10%）
    kelly_multiplier: float = 0.5    # 凯利公式系数（半凯利）
    max_position_size: float = 0.2   # 最大单持仓比例
    max_positions: int = 10          # 最大持仓数量
    use_volatility: bool = True      # 是否使用波动率调整


@dataclass
class StopLossConfig:
    """止损配置"""
    enabled: bool = True
    stop_loss_type: StopLossType = StopLossType.FIXED
    fixed_stop_loss_ratio: float = 0.05      # 固定止损比例（5%）
    trailing_stop_ratio: float = 0.10        # 移动止损比例（10%）
    trailing_callback: float = 0.02          # 移动止损回撤触发（2%）
    time_based_days: int = 30                # 时间止损天数


@dataclass
class TakeProfitConfig:
    """止盈配置"""
    enabled: bool = True
    take_profit_type: TakeProfitType = TakeProfitType.FIXED
    fixed_take_profit_ratio: float = 0.15    # 固定止盈比例（15%）
    target_price: Optional[float] = None     # 目标价格
    trailing_take_profit_ratio: float = 0.08 # 移动止盈比例（8%）
    trailing_callback: float = 0.03          # 移动止盈回撤触发（3%）


@dataclass
class IndustryConstraint:
    """行业约束"""
    industry_name: str
    max_allocation: float = 0.30    # 最大配置比例（30%）


@dataclass
class RiskConstraints:
    """风险约束"""
    max_portfolio_var: float = 0.05         # 最大投资组合VaR（5%）
    max_single_position_loss: float = 0.10  # 最大单持仓亏损（10%）
    max_sector_concentration: float = 0.30 # 最大行业集中度（30%）
    industry_constraints: List[IndustryConstraint] = field(default_factory=list)


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    name: str
    quantity: float
    avg_cost: float
    current_price: float
    industry: str = "unknown"
    volatility: float = 0.0


@dataclass
class RiskCheckResult:
    """风险检查结果"""
    passed: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggested_action: Optional[str] = None


class RiskManager:
    """风险控制管理器"""

    def __init__(
        self,
        portfolio_value: float,
        position_config: Optional[PositionConfig] = None,
        stop_loss_config: Optional[StopLossConfig] = None,
        take_profit_config: Optional[TakeProfitConfig] = None,
        risk_constraints: Optional[RiskConstraints] = None
    ):
        """
        初始化风险管理器

        参数:
            portfolio_value: 投资组合总价值
            position_config: 仓位配置
            stop_loss_config: 止损配置
            take_profit_config: 止盈配置
            risk_constraints: 风险约束
        """
        self.portfolio_value = portfolio_value
        self.position_config = position_config or PositionConfig()
        self.stop_loss_config = stop_loss_config or StopLossConfig()
        self.take_profit_config = take_profit_config or TakeProfitConfig()
        self.risk_constraints = risk_constraints or RiskConstraints()
        self.positions: Dict[str, Position] = {}
        self.peak_value = portfolio_value  # 用于跟踪移动止损的最高值

    def update_portfolio_value(self, new_value: float) -> None:
        """更新投资组合价值"""
        self.portfolio_value = new_value

    def update_peak_value(self) -> None:
        """更新峰值价值（用于移动止损）"""
        if self.portfolio_value > self.peak_value:
            self.peak_value = self.portfolio_value

    def add_position(self, position: Position) -> None:
        """添加持仓"""
        self.positions[position.symbol] = position

    def remove_position(self, symbol: str) -> None:
        """移除持仓"""
        if symbol in self.positions:
            del self.positions[symbol]

    def calculate_position_size(
        self,
        symbol: str,
        price: float,
        expected_return: float = 0.0,
        volatility: float = 0.0,
        win_rate: float = 0.5,
        avg_win: float = 0.0,
        avg_loss: float = 0.0
    ) -> Dict:
        """
        计算仓位大小

        参数:
            symbol: 股票代码
            price: 当前价格
            expected_return: 预期收益率
            volatility: 波动率
            win_rate: 胜率
            avg_win: 平均盈利
            avg_loss: 平均亏损

        返回:
            包含仓位信息的字典
        """
        method = self.position_config.method
        max_ratio = self.position_config.max_position_size

        if method == PositionSizingMethod.FIXED:
            # 固定仓位
            ratio = self.position_config.fixed_ratio
        elif method == PositionSizingMethod.KELLY:
            # 凯利公式: f = (p * b - q) / b
            # p = 胜率, b = 赔率(avg_win/avg_loss), q = 1-p
            if avg_loss > 0:
                win_loss_ratio = avg_win / avg_loss
                kelly_ratio = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
                ratio = max(0, kelly_ratio * self.position_config.kelly_multiplier)
            else:
                ratio = self.position_config.fixed_ratio
        elif method == PositionSizingMethod.EQUAL_WEIGHT:
            # 等权重：平均分配给所有标的
            current_count = len(self.positions)
            ratio = 1.0 / (current_count + 1) if current_count > 0 else 1.0 / 10
        elif method == PositionSizingMethod.VOLATILITY_WEIGHT:
            # 波动率加权：波动率越低，仓位越大
            if volatility > 0:
                target_vol = 0.15  # 目标波动率15%
                ratio = min(target_vol / volatility, max_ratio * 2)
            else:
                ratio = self.position_config.fixed_ratio
        elif method == PositionSizingMethod.RISK_PARITY:
            # 风险平价：每个持仓对总风险的贡献相等
            if volatility > 0:
                # 仓位与波动率成反比
                ratio = self.position_config.fixed_ratio / (volatility / 0.2)
            else:
                ratio = self.position_config.fixed_ratio
        else:
            ratio = self.position_config.fixed_ratio

        # 应用最大持仓限制
        ratio = min(ratio, max_ratio)

        # 计算实际金额和股数
        allocated_amount = self.portfolio_value * ratio
        quantity = int(allocated_amount / price)

        return {
            'symbol': symbol,
            'ratio': ratio,
            'allocated_amount': allocated_amount,
            'quantity': quantity,
            'method': method.value
        }

    def check_stop_loss(self, symbol: str) -> Tuple[bool, Optional[Dict]]:
        """
        检查是否触发止损

        参数:
            symbol: 股票代码

        返回:
            (是否触发止损, 止损信息)
        """
        if not self.stop_loss_config.enabled:
            return False, None

        if symbol not in self.positions:
            return False, None

        position = self.positions[symbol]
        current_price = position.current_price
        avg_cost = position.avg_cost

        # 计算当前亏损比例
        loss_ratio = (current_price - avg_cost) / avg_cost

        stop_type = self.stop_loss_config.stop_loss_type

        if stop_type == StopLossType.FIXED:
            # 固定比例止损
            stop_loss_ratio = -self.stop_loss_config.fixed_stop_loss_ratio
            if loss_ratio <= stop_loss_ratio:
                return True, {
                    'type': 'fixed',
                    'loss_ratio': loss_ratio,
                    'stop_ratio': stop_loss_ratio,
                    'action': 'sell',
                    'reason': f'亏损达到 {-stop_loss_ratio:.1%}，触发固定止损'
                }

        elif stop_type == StopLossType.TRAILING:
            # 移动止损：跟踪最高价
            self.update_peak_value()
            peak_ratio = (current_price - self.peak_value) / self.peak_value

            # 从买入后最高价回撤超过阈值
            if peak_ratio <= -self.stop_loss_config.trailing_stop_ratio:
                return True, {
                    'type': 'trailing',
                    'peak_value': self.peak_value,
                    'current_price': current_price,
                    'drawdown': peak_ratio,
                    'action': 'sell',
                    'reason': f'从峰值回撤 {-peak_ratio:.1%}，触发移动止损'
                }

        elif stop_type == StopLossType.TIME_BASED:
            # 时间止损需要外部追踪持仓时间，这里简化处理
            pass

        return False, None

    def check_take_profit(self, symbol: str) -> Tuple[bool, Optional[Dict]]:
        """
        检查是否触发止盈

        参数:
            symbol: 股票代码

        返回:
            (是否触发止盈, 止盈信息)
        """
        if not self.take_profit_config.enabled:
            return False, None

        if symbol not in self.positions:
            return False, None

        position = self.positions[symbol]
        current_price = position.current_price
        avg_cost = position.avg_cost

        # 计算当前盈利比例
        profit_ratio = (current_price - avg_cost) / avg_cost

        take_profit_type = self.take_profit_config.take_profit_type

        if take_profit_type == TakeProfitType.FIXED:
            # 固定比例止盈
            take_profit_ratio = self.take_profit_config.fixed_take_profit_ratio
            if profit_ratio >= take_profit_ratio:
                return True, {
                    'type': 'fixed',
                    'profit_ratio': profit_ratio,
                    'target_ratio': take_profit_ratio,
                    'action': 'sell',
                    'reason': f'盈利达到 {take_profit_ratio:.1%}，触发固定止盈'
                }

        elif take_profit_type == TakeProfitType.TARGET:
            # 目标价格止盈
            target_price = self.take_profit_config.target_price
            if target_price and current_price >= target_price:
                return True, {
                    'type': 'target',
                    'target_price': target_price,
                    'current_price': current_price,
                    'action': 'sell',
                    'reason': f'达到目标价格 {target_price}，触发目标止盈'
                }

        elif take_profit_type == TakeProfitType.TRAILING:
            # 移动止盈：跟踪最高价，锁定利润
            self.update_peak_value()
            peak_ratio = (current_price - self.peak_value) / self.peak_value

            # 从最高点回撤超过阈值，触发止盈
            if peak_ratio <= -self.take_profit_config.trailing_callback:
                return True, {
                    'type': 'trailing',
                    'peak_value': self.peak_value,
                    'current_price': current_price,
                    'drawdown': peak_ratio,
                    'profit_ratio': profit_ratio,
                    'action': 'sell',
                    'reason': f'从峰值 {self.peak_value} 回撤 {-peak_ratio:.1%}，触发移动止盈'
                }

        return False, None

    def check_industry_concentration(
        self,
        industry: str,
        new_allocation: float,
        current_industry_allocations: Dict[str, float]
    ) -> RiskCheckResult:
        """
        检查行业集中度

        参数:
            industry: 行业名称
            new_allocation: 新增配置比例
            current_industry_allocations: 当前各行业配置比例

        返回:
            风险检查结果
        """
        violations = []
        warnings = []

        # 计算新的行业总配置
        current_industry_total = current_industry_allocations.get(industry, 0)
        new_industry_total = current_industry_total + new_allocation

        # 检查行业最大配置限制
        max_sector = self.risk_constraints.max_sector_concentration

        if new_industry_total > max_sector:
            violations.append(
                f"行业 '{industry}' 配置比例 {new_industry_total:.1%} 超过限制 {max_sector:.1%}"
            )
            return RiskCheckResult(
                passed=False,
                violations=violations,
                warnings=warnings,
                suggested_action=f"建议降低 '{industry}' 行业持仓至 {max_sector:.1%} 以内"
            )

        # 检查特定行业约束
        for constraint in self.risk_constraints.industry_constraints:
            if constraint.industry_name == industry:
                if new_industry_total > constraint.max_allocation:
                    violations.append(
                        f"行业 '{industry}' 配置比例 {new_industry_total:.1%} 超过自定义限制 {constraint.max_allocation:.1%}"
                    )
                    return RiskCheckResult(
                        passed=False,
                        violations=violations,
                        warnings=warnings,
                        suggested_action=f"建议降低 '{industry}' 行业持仓至 {constraint.max_allocation:.1%} 以内"
                    )

        # 检查其他行业配置
        for ind_name, ind_alloc in current_industry_allocations.items():
            if ind_name != industry and ind_alloc > max_sector:
                warnings.append(
                    f"行业 '{ind_name}' 当前配置 {ind_alloc:.1%} 较高，建议关注"
                )

        return RiskCheckResult(passed=True, violations=violations, warnings=warnings)

    def check_position_limits(self) -> RiskCheckResult:
        """
        检查持仓数量限制

        返回:
            风险检查结果
        """
        violations = []
        warnings = []

        current_count = len(self.positions)
        max_positions = self.position_config.max_positions

        if current_count >= max_positions:
            violations.append(
                f"当前持仓数量 {current_count} 已达到最大限制 {max_positions}"
            )
            return RiskCheckResult(
                passed=False,
                violations=violations,
                warnings=warnings,
                suggested_action="建议卖出部分持仓后再买入新标的"
            )

        if current_count >= max_positions - 2:
            warnings.append(
                f"持仓数量 {current_count} 接近最大限制 {max_positions}，剩余可用仓位: {max_positions - current_count}"
            )

        return RiskCheckResult(passed=True, violations=violations, warnings=warnings)

    def check_single_position_loss(
        self,
        symbol: str,
        current_price: float,
        avg_cost: float
    ) -> RiskCheckResult:
        """
        检查单持仓最大亏损限制

        参数:
            symbol: 股票代码
            current_price: 当前价格
            avg_cost: 平均成本

        返回:
            风险检查结果
        """
        violations = []
        warnings = []

        loss_ratio = (current_price - avg_cost) / avg_cost
        max_loss = -self.risk_constraints.max_single_position_loss

        if loss_ratio <= max_loss:
            violations.append(
                f"标的 '{symbol}' 亏损 {loss_ratio:.1%} 超过最大限制 {max_loss:.1%}"
            )
            return RiskCheckResult(
                passed=False,
                violations=violations,
                warnings=warnings,
                suggested_action=f"建议考虑止损 '{symbol}'"
            )

        if loss_ratio <= max_loss * 0.8:
            warnings.append(
                f"标的 '{symbol}' 亏损 {loss_ratio:.1%} 接近最大限制 {max_loss:.1%}"
            )

        return RiskCheckResult(passed=True, violations=violations, warnings=warnings)

    def calculate_risk_metrics(
        self,
        returns: np.ndarray,
        portfolio_value: float
    ) -> Dict:
        """
        计算风险指标

        参数:
            returns: 收益率数组
            portfolio_value: 投资组合价值

        返回:
            风险指标字典
        """
        from services.models.risk.value_at_risk import (
            calculate_var, calculate_cvar, calculate_downside_risk,
            calculate_sortino_ratio, calculate_max_drawdown,
            calculate_kurtosis, calculate_skewness
        )

        metrics = {
            'var_95': calculate_var(returns, confidence_level=0.95, method='historical'),
            'var_99': calculate_var(returns, confidence_level=0.99, method='historical'),
            'cvar_95': calculate_cvar(returns, confidence_level=0.95, method='historical'),
            'cvar_99': calculate_cvar(returns, confidence_level=0.99, method='historical'),
            'downside_risk': calculate_downside_risk(returns),
            'sortino_ratio': calculate_sortino_ratio(returns),
            'max_drawdown': calculate_max_drawdown(returns),
            'kurtosis': calculate_kurtosis(returns),
            'skewness': calculate_skewness(returns),
            'volatility': np.std(returns) * np.sqrt(252),
            'average_return': np.mean(returns) * 252,
            'sharpe_ratio': (
                np.mean(returns) / np.std(returns) * np.sqrt(252)
                if np.std(returns) > 0 else 0
            )
        }

        # 计算VaR金额
        metrics['var_95_amount'] = metrics['var_95'] * portfolio_value
        metrics['var_99_amount'] = metrics['var_99'] * portfolio_value

        return metrics

    def get_portfolio_risk_report(self) -> Dict:
        """
        获取投资组合风险报告

        返回:
            风险报告字典
        """
        positions_list = []
        total_value = 0

        for symbol, pos in self.positions.items():
            market_value = pos.quantity * pos.current_price
            total_value += market_value
            positions_list.append({
                'symbol': symbol,
                'name': pos.name,
                'quantity': pos.quantity,
                'avg_cost': pos.avg_cost,
                'current_price': pos.current_price,
                'market_value': market_value,
                'industry': pos.industry,
                'profit_loss': market_value - (pos.quantity * pos.avg_cost),
                'profit_loss_ratio': (pos.current_price - pos.avg_cost) / pos.avg_cost
            })

        # 计算行业分布
        industry_allocations = {}
        for pos_data in positions_list:
            ind = pos_data['industry']
            alloc = pos_data['market_value'] / total_value if total_value > 0 else 0
            industry_allocations[ind] = industry_allocations.get(ind, 0) + alloc

        return {
            'portfolio_value': self.portfolio_value,
            'positions_count': len(self.positions),
            'positions': positions_list,
            'industry_allocations': industry_allocations,
            'peak_value': self.peak_value,
            'config': {
                'position_method': self.position_config.method.value,
                'stop_loss_enabled': self.stop_loss_config.enabled,
                'take_profit_enabled': self.take_profit_config.enabled
            }
        }

    def validate_trade(
        self,
        symbol: str,
        price: float,
        quantity: int,
        trade_type: str,  # 'buy' or 'sell'
        industry: str,
        current_industry_allocations: Dict[str, float]
    ) -> RiskCheckResult:
        """
        验证交易是否合规

        参数:
            symbol: 股票代码
            price: 价格
            quantity: 数量
            trade_type: 交易类型 ('buy' or 'sell')
            industry: 行业
            current_industry_allocations: 当前行业配置

        返回:
            风险检查结果
        """
        violations = []
        warnings = []

        if trade_type == 'buy':
            # 检查持仓数量限制
            position_limit_check = self.check_position_limits()
            if not position_limit_check.passed:
                violations.extend(position_limit_check.violations)

            # 计算新标的的配置比例
            trade_value = price * quantity
            new_allocation = trade_value / self.portfolio_value if self.portfolio_value > 0 else 0

            # 检查行业集中度
            industry_check = self.check_industry_concentration(
                industry, new_allocation, current_industry_allocations
            )
            if not industry_check.passed:
                violations.extend(industry_check.violations)
            warnings.extend(industry_check.warnings)

            # 检查单个标的仓位限制
            max_single = self.position_config.max_position_size
            if new_allocation > max_single:
                violations.append(
                    f"交易配置比例 {new_allocation:.1%} 超过单标的限制 {max_single:.1%}"
                )

        # 返回检查结果
        return RiskCheckResult(
            passed=len(violations) == 0,
            violations=violations,
            warnings=warnings
        )


def calculate_kelly_formula(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    计算凯利公式

    参数:
        win_rate: 胜率
        avg_win: 平均盈利金额
        avg_loss: 平均亏损金额

    返回:
        凯利比例
    """
    if avg_loss <= 0:
        return 0.0

    win_loss_ratio = avg_win / avg_loss
    kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
    return max(0, kelly)


def calculate_portfolio_volatility(
    weights: np.ndarray,
    covariance_matrix: np.ndarray
) -> float:
    """
    计算投资组合波动率

    参数:
        weights: 权重数组
        covariance_matrix: 协方差矩阵

    返回:
        投资组合波动率
    """
    return np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))


def calculate_portfolio_var(
    portfolio_value: float,
    returns: np.ndarray,
    confidence_level: float = 0.95
) -> float:
    """
    计算投资组合VaR

    参数:
        portfolio_value: 投资组合价值
        returns: 收益率数组
        confidence_level: 置信水平

    返回:
        VaR值（金额）
    """
    from services.models.risk.value_at_risk import calculate_var
    var_ratio = calculate_var(returns, confidence_level=confidence_level, method='historical')
    return var_ratio * portfolio_value
