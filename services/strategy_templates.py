"""
策略模板库 - 包含多种预定义的交易策略模板
每个策略包含：名称、描述、参数说明、适用场景、默认参数
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any
import json


@dataclass
class StrategyParameter:
    """策略参数定义"""
    name: str  # 参数名称
    display_name: str  # 显示名称
    type: str  # 参数类型：int, float, str, bool
    default: Any  # 默认值
    min_value: Any = None  # 最小值
    max_value: Any = None  # 最大值
    step: Any = None  # 步长
    description: str = ""  # 参数说明


@dataclass
class StrategyTemplate:
    """策略模板定义"""
    id: str  # 模板唯一标识
    name: str  # 策略名称
    description: str  # 策略描述
    scenario: str  # 适用场景
    parameters: List[StrategyParameter]  # 参数列表
    default_params: Dict[str, Any]  # 默认参数字典
    author: str = "系统"  # 作者
    version: str = "1.0"  # 版本
    tags: List[str] = None  # 标签
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'scenario': self.scenario,
            'parameters': [
                {
                    'name': p.name,
                    'display_name': p.display_name,
                    'type': p.type,
                    'default': p.default,
                    'min_value': p.min_value,
                    'max_value': p.max_value,
                    'step': p.step,
                    'description': p.description
                } for p in self.parameters
            ],
            'default_params': self.default_params,
            'author': self.author,
            'version': self.version,
            'tags': self.tags
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyTemplate':
        """从字典创建模板"""
        parameters = [
            StrategyParameter(**p) for p in data.get('parameters', [])
        ]
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            scenario=data['scenario'],
            parameters=parameters,
            default_params=data.get('default_params', {}),
            author=data.get('author', '未知'),
            version=data.get('version', '1.0'),
            tags=data.get('tags', [])
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'StrategyTemplate':
        """从JSON字符串创建模板"""
        return cls.from_dict(json.loads(json_str))


# 预定义策略模板
STRATEGY_TEMPLATES: List[StrategyTemplate] = [
    # 1. 双均线策略
    StrategyTemplate(
        id="dual_moving_average",
        name="双均线策略",
        description="基于短期和长期移动平均线的交叉来判断趋势，当短期均线上穿长期均线时买入，下穿时卖出。经典的趋势跟踪策略，简单有效。",
        scenario="适用于有明显趋势的股票，在震荡行情中可能产生频繁虚假信号。建议用于中短期操作，配合其他指标过滤噪音。",
        parameters=[
            StrategyParameter("short_window", "短期窗口", "int", 10, 2, 50, 1, "短期均线的计算周期"),
            StrategyParameter("long_window", "长期窗口", "int", 30, 5, 200, 1, "长期均线的计算周期")
        ],
        default_params={"short_window": 10, "long_window": 30},
        author="系统",
        version="1.0",
        tags=["趋势跟踪", "均线", "经典"]
    ),
    
    # 2. RSI超买超卖策略
    StrategyTemplate(
        id="rsi_strategy",
        name="RSI超买超卖策略",
        description="利用RSI相对强弱指标判断市场的超买超卖状态。RSI低于超卖阈值时买入，高于超买阈值时卖出。适合反转交易。",
        scenario="适用于震荡市，在明显趋势行情中可能失效。参数可根据不同品种调整，周期一般为14，超买70-80，超卖20-30。",
        parameters=[
            StrategyParameter("period", "RSI周期", "int", 14, 2, 50, 1, "计算RSI的周期天数"),
            StrategyParameter("overbought", "超买阈值", "int", 70, 50, 90, 5, "RSI超过此值视为超买"),
            StrategyParameter("oversold", "超卖阈值", "int", 30, 10, 50, 5, "RSI低于此值视为超卖")
        ],
        default_params={"period": 14, "overbought": 70, "oversold": 30},
        author="系统",
        version="1.0",
        tags=["反转交易", "RSI", "超买超卖"]
    ),
    
    # 3. MACD金叉死叉策略
    StrategyTemplate(
        id="macd_strategy",
        name="MACD金叉死叉策略",
        description="利用MACD指标的DIF线与信号线的交叉来判断买卖时机。DIF线上穿信号线（金叉）买入，下穿（死叉）卖出。",
        scenario="适用于中短期趋势交易，可有效捕捉中期趋势的启动和结束。参数默认12/26/9为经典参数，也可根据品种特性调整。",
        parameters=[
            StrategyParameter("fast_period", "快速EMA周期", "int", 12, 5, 30, 1, "快速EMA的计算周期"),
            StrategyParameter("slow_period", "慢速EMA周期", "int", 26, 10, 50, 1, "慢速EMA的计算周期"),
            StrategyParameter("signal_period", "信号线周期", "int", 9, 5, 20, 1, "信号线的EMA周期")
        ],
        default_params={"fast_period": 12, "slow_period": 26, "signal_period": 9},
        author="系统",
        version="1.0",
        tags=["趋势跟踪", "MACD", "中短期"]
    ),
    
    # 4. 多因子选股策略
    StrategyTemplate(
        id="multi_factor_strategy",
        name="多因子选股策略",
        description="综合考虑多个财务和技术因子进行选股，采用价值、成长、动量、质量等维度的综合评分。",
        scenario="适用于中长期投资，需要股票的基本面数据支持。回测周期建议1年以上，以充分体现因子有效性。",
        parameters=[
            StrategyParameter("value_weight", "价值因子权重", "float", 0.25, 0, 1, 0.05, "价值因子的综合权重"),
            StrategyParameter("growth_weight", "成长因子权重", "float", 0.25, 0, 1, 0.05, "成长因子的综合权重"),
            StrategyParameter("momentum_weight", "动量因子权重", "float", 0.25, 0, 1, 0.05, "动量因子的综合权重"),
            StrategyParameter("quality_weight", "质量因子权重", "float", 0.25, 0, 1, 0.05, "质量因子的综合权重"),
            StrategyParameter("rebalance_period", "调仓周期", "int", 20, 5, 60, 5, "组合再平衡的周期（交易日）")
        ],
        default_params={
            "value_weight": 0.25,
            "growth_weight": 0.25,
            "momentum_weight": 0.25,
            "quality_weight": 0.25,
            "rebalance_period": 20
        },
        author="系统",
        version="1.0",
        tags=["选股", "多因子", "量化"]
    ),
    
    # 5. 海龟交易法则策略
    StrategyTemplate(
        id="turtle_trading_strategy",
        name="海龟交易法则策略",
        description="源自著名的海龟交易员培训系统，采用趋势跟随策略。核心是用唐奇安通道突破确定入场，用平均真实波幅确定仓位。",
        scenario="适用于趋势明显的市场，在震荡市中会产生较多止损。建议用于商品期货和ETF等高流动性品种。",
        parameters=[
            StrategyParameter("entry_period", "入场通道周期", "int", 20, 10, 50, 1, "唐奇安通道的突破周期"),
            StrategyParameter("exit_period", "出场通道周期", "int", 10, 5, 30, 1, "唐奇安通道的退出周期"),
            StrategyParameter("atr_period", "ATR周期", "int", 20, 10, 50, 1, "计算平均真实波幅的周期"),
            StrategyParameter("max_position_pct", "最大仓位比例", "float", 0.02, 0.01, 0.1, 0.01, "单次交易最大资金比例"),
            StrategyParameter("stop_loss_atr", "止损ATR倍数", "float", 2.0, 0.5, 5.0, 0.5, "止损距离（ATR倍数）")
        ],
        default_params={
            "entry_period": 20,
            "exit_period": 10,
            "atr_period": 20,
            "max_position_pct": 0.02,
            "stop_loss_atr": 2.0
        },
        author="系统",
        version="1.0",
        tags=["趋势跟踪", "海龟", "仓位管理"]
    ),
    
    # 6. 布林带策略
    StrategyTemplate(
        id="bollinger_bands_strategy",
        name="布林带策略",
        description="利用布林带上下轨与价格的关系进行交易。价格触及下轨时买入（超卖），触及上轨时卖出（超买）。",
        scenario="适用于震荡行情，在趋势行情中可能持续持有不利仓位。可结合其他指标确认信号，提高胜率。",
        parameters=[
            StrategyParameter("period", "布林带周期", "int", 20, 10, 50, 1, "中轨的计算周期"),
            StrategyParameter("num_std", "标准差倍数", "float", 2.0, 1.0, 4.0, 0.5, "上下轨与中轨的距离（标准差倍数）")
        ],
        default_params={"period": 20, "num_std": 2.0},
        author="系统",
        version="1.0",
        tags=["震荡交易", "布林带", "反转"]
    ),
    
    # 7. KDJ随机指标策略
    StrategyTemplate(
        id="kdj_strategy",
        name="KDJ随机指标策略",
        description="利用KDJ指标的K线和D线交叉以及J值的超买超卖状态进行交易判断。",
        scenario="适用于短线交易，需要结合市场整体环境。J值对价格变化敏感，可提前发出信号但也可能产生虚假信号。",
        parameters=[
            StrategyParameter("period", "RSV周期", "int", 9, 5, 30, 1, "计算RSV的周期"),
            StrategyParameter("k_period", "K值周期", "int", 3, 1, 10, 1, "K值的平滑周期"),
            StrategyParameter("d_period", "D值周期", "int", 3, 1, 10, 1, "D值的平滑周期"),
            StrategyParameter("oversold_threshold", "超卖阈值", "int", 20, 10, 40, 5, "J值低于此值视为超卖"),
            StrategyParameter("overbought_threshold", "超买阈值", "int", 80, 60, 90, 5, "J值高于此值视为超买")
        ],
        default_params={
            "period": 9,
            "k_period": 3,
            "d_period": 3,
            "oversold_threshold": 20,
            "overbought_threshold": 80
        },
        author="系统",
        version="1.0",
        tags=["短线", "KDJ", "超买超卖"]
    ),
    
    # 8. 动量策略
    StrategyTemplate(
        id="momentum_strategy",
        name="动量策略",
        description="基于价格动量理论，认为过去一段时间表现好的资产在未来一段时间仍会表现较好。买入近期上涨的股票，卖出近期下跌的。",
        scenario="适用于趋势市场，在市场反转时可能遭受重大损失。建议定期再平衡仓位，并设置止损。",
        parameters=[
            StrategyParameter("lookback_period", "动量计算期", "int", 12, 5, 60, 1, "计算动量收益的回溯期（交易日）"),
            StrategyParameter("holding_period", "持仓周期", "int", 6, 1, 30, 1, "每次持仓的天数"),
            StrategyParameter("momentum_threshold", "动量阈值", "float", 0.0, -0.1, 0.1, 0.01, "只有动量超过此阈值才进行交易")
        ],
        default_params={
            "lookback_period": 12,
            "holding_period": 6,
            "momentum_threshold": 0.0
        },
        author="系统",
        version="1.0",
        tags=["动量", "趋势跟踪", "中短期"]
    ),
    
    # 9. 均值回归策略
    StrategyTemplate(
        id="mean_reversion_strategy",
        name="均值回归策略",
        description="基于价格会围绕均值波动的假设，当价格偏离均值过大时进行反向交易。价格低于均值减去阈值倍标准差时买入，高于时卖出。",
        scenario="适用于震荡市场，在趋势行情中可能逆势交易导致损失。需设置合理的止损防止趋势行情中的持续亏损。",
        parameters=[
            StrategyParameter("period", "均值周期", "int", 20, 10, 60, 1, "计算均值的回溯期"),
            StrategyParameter("threshold", "偏离阈值", "float", 1.5, 0.5, 3.0, 0.1, "触发交易的偏离标准差倍数"),
            StrategyParameter("exit_threshold", "退出阈值", "float", 0.5, 0, 1.0, 0.1, "回归均值多少时平仓")
        ],
        default_params={"period": 20, "threshold": 1.5, "exit_threshold": 0.5},
        author="系统",
        version="1.0",
        tags=["均值回归", "震荡交易", "反转"]
    ),
    
    # 10. CCI商品通道指数策略
    StrategyTemplate(
        id="cci_strategy",
        name="CCI商品通道指数策略",
        description="利用CCI指标测量价格与其平均价格的偏离程度，当CCI低于-100时视为超卖买入，高于+100时视为超买卖出。",
        scenario="适用于短线交易和波段操作，在盘整行情中效果较好。CCI对价格变化敏感，适合捕捉短期转折点。",
        parameters=[
            StrategyParameter("period", "CCI周期", "int", 14, 5, 30, 1, "计算CCI的周期"),
            StrategyParameter("oversold", "超卖阈值", "int", -100, -200, -20, 10, "CCI低于此值视为超卖"),
            StrategyParameter("overbought", "超买阈值", "int", 100, 20, 200, 10, "CCI高于此值视为超买")
        ],
        default_params={"period": 14, "oversold": -100, "overbought": 100},
        author="系统",
        version="1.0",
        tags=["短线", "CCI", "超买超卖"]
    )
]


def get_all_templates() -> List[StrategyTemplate]:
    """获取所有策略模板"""
    return STRATEGY_TEMPLATES


def get_template_by_id(template_id: str) -> StrategyTemplate:
    """根据ID获取策略模板"""
    for template in STRATEGY_TEMPLATES:
        if template.id == template_id:
            return template
    return None


def search_templates(keyword: str) -> List[StrategyTemplate]:
    """根据关键词搜索策略模板"""
    keyword = keyword.lower()
    results = []
    for template in STRATEGY_TEMPLATES:
        if (keyword in template.name.lower() or 
            keyword in template.description.lower() or
            keyword in template.scenario.lower() or
            any(keyword in tag.lower() for tag in template.tags)):
            results.append(template)
    return results


def get_templates_by_tag(tag: str) -> List[StrategyTemplate]:
    """根据标签获取策略模板"""
    tag = tag.lower()
    return [t for t in STRATEGY_TEMPLATES if tag in [t.lower() for t in t.tags]]


def export_template_to_json(template_id: str) -> str:
    """导出指定模板为JSON字符串"""
    template = get_template_by_id(template_id)
    if template:
        return template.to_json()
    return None


def export_all_templates_to_json() -> str:
    """导出所有模板为JSON字符串"""
    templates_data = [t.to_dict() for t in STRATEGY_TEMPLATES]
    return json.dumps({
        'version': '1.0',
        'export_time': str(__import__('datetime').datetime.now()),
        'templates': templates_data
    }, ensure_ascii=False, indent=2)


def import_template_from_json(json_str: str) -> StrategyTemplate:
    """从JSON字符串导入模板"""
    try:
        data = json.loads(json_str)
        # 如果是包含多个模板的格式
        if 'templates' in data:
            raise ValueError("请使用 import_templates_from_json 导入多个模板")
        return StrategyTemplate.from_dict(data)
    except Exception as e:
        raise ValueError(f"JSON格式无效: {str(e)}")


def import_templates_from_json(json_str: str) -> List[StrategyTemplate]:
    """从JSON字符串导入多个模板"""
    try:
        data = json.loads(json_str)
        if 'templates' not in data:
            # 单个模板格式
            return [StrategyTemplate.from_dict(data)]
        return [StrategyTemplate.from_dict(t) for t in data['templates']]
    except Exception as e:
        raise ValueError(f"JSON格式无效: {str(e)}")


def create_custom_template(
    name: str,
    description: str,
    scenario: str,
    parameters: List[Dict],
    default_params: Dict,
    tags: List[str] = None
) -> StrategyTemplate:
    """创建自定义策略模板"""
    import uuid
    return StrategyTemplate(
        id=f"custom_{uuid.uuid4().hex[:8]}",
        name=name,
        description=description,
        scenario=scenario,
        parameters=[StrategyParameter(**p) for p in parameters],
        default_params=default_params,
        author="用户",
        version="1.0",
        tags=tags or ["自定义"]
    )


# 获取模板列表（用于前端展示）
def get_template_list() -> List[Dict]:
    """获取模板列表（简化信息）"""
    return [
        {
            'id': t.id,
            'name': t.name,
            'description': t.description[:100] + '...' if len(t.description) > 100 else t.description,
            'scenario': t.scenario[:80] + '...' if len(t.scenario) > 80 else t.scenario,
            'tags': t.tags,
            'author': t.author,
            'version': t.version,
            'param_count': len(t.parameters)
        }
        for t in STRATEGY_TEMPLATES
    ]


# 获取模板详情（包含完整参数信息）
def get_template_detail(template_id: str) -> Dict:
    """获取模板详情"""
    template = get_template_by_id(template_id)
    if template:
        return template.to_dict()
    return None
