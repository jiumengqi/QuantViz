from flask import Blueprint, render_template, request, jsonify, current_app
from services.models.pricing.black_scholes import black_scholes, calculate_bs
from services.models.pricing.bond_pricing import BondPricing
from services.models.risk.value_at_risk import calculate_var, calculate_cvar, calculate_downside_risk, calculate_sortino_ratio, calculate_max_drawdown, calculate_kurtosis, calculate_skewness
from services.models.portfolio.markowitz import optimize
import numpy as np
import json
import logging

# 创建日志记录器
logger = logging.getLogger(__name__)

# 创建模型模块蓝图
models_bp = Blueprint('models', __name__)


@models_bp.route('/')
def models_index():
    """金融模型首页"""
    # 模型分类列表
    model_categories = [
        {'id': 'pricing', 'name': '定价模型', 'count': 5},
        {'id': 'risk', 'name': '风险模型', 'count': 4},
        {'id': 'forecasting', 'name': '预测模型', 'count': 6},
        {'id': 'portfolio', 'name': '组合优化', 'count': 3}
    ]

    return render_template('models/index.html', categories=model_categories)


@models_bp.route('/black-scholes')
def black_scholes_model():
    """Black-Scholes期权定价模型页面"""
    # 默认参数
    params = {
        'spot': 100,
        'strike': 100,
        'time': 1,
        'rate': 5,
        'volatility': 30,
        'option_type': 'call'
    }

    # 如果有GET参数，使用GET参数
    if request.args:
        params.update({
            'spot': float(request.args.get('spot', 100)),
            'strike': float(request.args.get('strike', 100)),
            'time': float(request.args.get('time', 1)),
            'rate': float(request.args.get('rate', 5)),
            'volatility': float(request.args.get('volatility', 30)),
            'option_type': request.args.get('option_type', 'call')
        })

    # 计算默认价格
    price = black_scholes(
        params['spot'],
        params['strike'],
        params['time'],
        params['rate'] / 100,
        params['volatility'] / 100,
        params['option_type']
    )
    # 构建结果字典
    result = {
        'price': float(price),
        'spot_price': float(params['spot']),
        'strike_price': float(params['strike']),
        'time_to_maturity': float(params['time']),
        'risk_free_rate': float(params['rate'] / 100),
        'volatility': float(params['volatility'] / 100),
        'option_type': params['option_type'],
        'success': True
    }

    return render_template('models/black-scholes.html', params=params, result=result)


@models_bp.route('/api/black-scholes/calculate', methods=['POST'])
def calculate_black_scholes():
    """API端点：计算Black-Scholes期权价格"""
    try:
        data = request.get_json()
        
        # 验证输入参数
        required_fields = ['spot', 'strike', 'time', 'rate', 'volatility', 'option_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必要参数: {field}'}), 400
        
        # 转换参数（将百分比转换为小数）
        spot = float(data['spot'])
        strike = float(data['strike'])
        time = float(data['time'])
        rate = float(data['rate']) / 100  # 转换为小数
        volatility = float(data['volatility']) / 100  # 转换为小数
        option_type = data['option_type'].lower()
        
        # 调用模型计算
        result = calculate_bs(spot, strike, time, rate, volatility, option_type)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Black-Scholes计算错误: {str(e)}")
        return jsonify({'error': str(e)}), 500


@models_bp.route('/var')
def var_model():
    """风险价值(VaR)模型页面"""
    return render_template('models/var.html')


@models_bp.route('/api/risk/calculate', methods=['POST'])
def calculate_risk_metrics():
    """API端点：计算各种风险指标"""
    try:
        data = request.get_json()
        
        # 验证输入参数
        required_fields = ['returns']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必要参数: {field}'}), 400
        
        # 转换参数
        returns = np.array(data['returns'], dtype=float)
        confidence_level = float(data.get('confidence_level', 0.95))
        time_horizon = int(data.get('time_horizon', 1))
        method = data.get('method', 'historical')
        risk_free_rate = float(data.get('risk_free_rate', 0))
        target_return = float(data.get('target_return', 0))
        
        # 计算各种风险指标
        var = calculate_var(returns, confidence_level, time_horizon, method)
        cvar = calculate_cvar(returns, confidence_level, time_horizon, method)
        downside_risk = calculate_downside_risk(returns, target_return)
        sortino_ratio = calculate_sortino_ratio(returns, risk_free_rate, target_return)
        max_drawdown = calculate_max_drawdown(returns)
        kurtosis = calculate_kurtosis(returns)
        skewness = calculate_skewness(returns)
        
        # 计算夏普比率作为参考
        if len(returns) > 0:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (avg_return - risk_free_rate) / std_return if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # 构建响应
        result = {
            'var': float(var),
            'cvar': float(cvar),
            'downside_risk': float(downside_risk),
            'sortino_ratio': float(sortino_ratio),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'kurtosis': float(kurtosis),
            'skewness': float(skewness),
            'confidence_level': float(confidence_level),
            'time_horizon': int(time_horizon),
            'method': method,
            'success': True
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"风险指标计算错误: {str(e)}")
        return jsonify({'error': str(e)}), 500


@models_bp.route('/markowitz')
def markowitz_model():
    """Markowitz均值-方差模型页面"""
    return render_template('models/markowitz.html')


@models_bp.route('/portfolio-optimization', methods=['POST'])
def optimize_portfolio():
    """投资组合优化"""
    try:
        data = request.get_json()
        
        # 支持传入收益率数据或使用模拟数据
        returns = data.get('returns', None)
        risk_free_rate = float(data.get('risk_free_rate', 0.03))
        objective = data.get('objective', 'max_sharpe')
        target_return = data.get('target_return', None)
        constraints = data.get('constraints', None)
        
        if returns is not None:
            returns = np.array(returns)
        
        # 使用新的MarkowitzOptimizer
        from services.models.portfolio.markowitz import MarkowitzOptimizer
        optimizer = MarkowitzOptimizer(
            returns if returns is not None else np.random.normal(0.0005, 0.01, (252, 5)),
            risk_free_rate=risk_free_rate
        )
        result = optimizer.optimize(
            objective=objective,
            target_return=target_return,
            constraints_dict=constraints
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"投资组合优化失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@models_bp.route('/api/black-scholes/implied-volatility', methods=['POST'])
def calculate_implied_volatility():
    """API端点：计算隐含波动率"""
    try:
        from services.models.pricing.black_scholes import calculate_iv
        data = request.get_json()
        
        required_fields = ['spot', 'strike', 'time', 'rate', 'market_price', 'option_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必要参数: {field}'}), 400
        
        spot = float(data['spot'])
        strike = float(data['strike'])
        time = float(data['time'])
        rate = float(data['rate']) / 100
        market_price = float(data['market_price'])
        option_type = data['option_type'].lower()
        
        result = calculate_iv(spot, strike, time, rate, market_price, option_type)
        return jsonify(result)
    except Exception as e:
        logger.error(f"隐含波动率计算错误: {str(e)}")
        return jsonify({'error': str(e)}), 500


@models_bp.route('/bond-pricing')
def bond_pricing_model():
    """债券定价模型页面"""
    # 默认参数
    params = {
        'face_value': 1000,
        'coupon_rate': 5,
        'years_to_maturity': 5,
        'yield_to_maturity': 4,
        'compounding_frequency': 2,
        'bond_type': 'coupon'
    }

    # 如果有GET参数，使用GET参数
    if request.args:
        params.update({
            'face_value': float(request.args.get('face_value', 1000)),
            'coupon_rate': float(request.args.get('coupon_rate', 5)),
            'years_to_maturity': float(request.args.get('years_to_maturity', 5)),
            'yield_to_maturity': float(request.args.get('yield_to_maturity', 4)),
            'compounding_frequency': int(request.args.get('compounding_frequency', 2)),
            'bond_type': request.args.get('bond_type', 'coupon')
        })

    # 计算默认价格
    if params['bond_type'] == 'coupon':
        price = BondPricing.price_coupon_bond(
            params['face_value'],
            params['coupon_rate'] / 100,
            params['years_to_maturity'],
            params['yield_to_maturity'] / 100,
            params['compounding_frequency']
        )
    else:
        price = BondPricing.price_zero_coupon_bond(
            params['face_value'],
            params['years_to_maturity'],
            params['yield_to_maturity'] / 100,
            params['compounding_frequency']
        )

    # 计算久期和凸性
    if params['bond_type'] == 'coupon':
        macaulay_duration = BondPricing.calculate_macaulay_duration(
            params['face_value'],
            params['coupon_rate'] / 100,
            params['years_to_maturity'],
            params['yield_to_maturity'] / 100,
            params['compounding_frequency']
        )
        modified_duration = BondPricing.calculate_modified_duration(
            params['face_value'],
            params['coupon_rate'] / 100,
            params['years_to_maturity'],
            params['yield_to_maturity'] / 100,
            params['compounding_frequency']
        )
        convexity = BondPricing.calculate_convexity(
            params['face_value'],
            params['coupon_rate'] / 100,
            params['years_to_maturity'],
            params['yield_to_maturity'] / 100,
            params['compounding_frequency']
        )
    else:
        # 零息债券的久期等于到期时间
        macaulay_duration = params['years_to_maturity']
        modified_duration = macaulay_duration / (1 + params['yield_to_maturity'] / 100 / params['compounding_frequency'])
        # 计算零息债券的凸性
        convexity = BondPricing.calculate_convexity(
            params['face_value'],
            0,
            params['years_to_maturity'],
            params['yield_to_maturity'] / 100,
            params['compounding_frequency']
        )

    # 构建结果字典
    result = {
        'price': float(price),
        'macaulay_duration': float(macaulay_duration),
        'modified_duration': float(modified_duration),
        'convexity': float(convexity),
        'face_value': float(params['face_value']),
        'coupon_rate': float(params['coupon_rate']),
        'years_to_maturity': float(params['years_to_maturity']),
        'yield_to_maturity': float(params['yield_to_maturity']),
        'compounding_frequency': int(params['compounding_frequency']),
        'bond_type': params['bond_type'],
        'success': True
    }

    return render_template('models/bond-pricing.html', params=params, result=result)


@models_bp.route('/api/bond-pricing/calculate', methods=['POST'])
def calculate_bond_price():
    """API端点：计算债券价格、久期和凸性"""
    try:
        data = request.get_json()
        
        # 验证输入参数
        required_fields = ['face_value', 'coupon_rate', 'years_to_maturity', 'yield_to_maturity', 'compounding_frequency', 'bond_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必要参数: {field}'}), 400
        
        # 转换参数
        face_value = float(data['face_value'])
        coupon_rate = float(data['coupon_rate']) / 100  # 转换为小数
        years_to_maturity = float(data['years_to_maturity'])
        yield_to_maturity = float(data['yield_to_maturity']) / 100  # 转换为小数
        compounding_frequency = int(data['compounding_frequency'])
        bond_type = data['bond_type']
        
        # 计算债券价格
        if bond_type == 'coupon':
            price = BondPricing.price_coupon_bond(
                face_value,
                coupon_rate,
                years_to_maturity,
                yield_to_maturity,
                compounding_frequency
            )
        else:
            price = BondPricing.price_zero_coupon_bond(
                face_value,
                years_to_maturity,
                yield_to_maturity,
                compounding_frequency
            )
        
        # 计算久期和凸性
        if bond_type == 'coupon':
            macaulay_duration = BondPricing.calculate_macaulay_duration(
                face_value,
                coupon_rate,
                years_to_maturity,
                yield_to_maturity,
                compounding_frequency
            )
            modified_duration = BondPricing.calculate_modified_duration(
                face_value,
                coupon_rate,
                years_to_maturity,
                yield_to_maturity,
                compounding_frequency
            )
            convexity = BondPricing.calculate_convexity(
                face_value,
                coupon_rate,
                years_to_maturity,
                yield_to_maturity,
                compounding_frequency
            )
        else:
            # 零息债券的久期等于到期时间
            macaulay_duration = years_to_maturity
            modified_duration = macaulay_duration / (1 + yield_to_maturity / compounding_frequency)
            # 计算零息债券的凸性
            convexity = BondPricing.calculate_convexity(
                face_value,
                0,
                years_to_maturity,
                yield_to_maturity,
                compounding_frequency
            )
        
        # 构建响应
        result = {
            'price': float(price),
            'macaulay_duration': float(macaulay_duration),
            'modified_duration': float(modified_duration),
            'convexity': float(convexity),
            'face_value': float(face_value),
            'coupon_rate': float(data['coupon_rate']),
            'years_to_maturity': float(years_to_maturity),
            'yield_to_maturity': float(data['yield_to_maturity']),
            'compounding_frequency': int(compounding_frequency),
            'bond_type': bond_type,
            'success': True
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"债券定价计算错误: {str(e)}")
        return jsonify({'error': str(e)}), 500


@models_bp.route('/forecasting')
def forecasting_model():
    """预测模型页面"""
    return render_template('models/forecasting.html')


@models_bp.route('/api/forecasting/arima', methods=['POST'])
def forecast_arima():
    """API端点：使用ARIMA模型进行时间序列预测"""
    try:
        from services.models.forecasting import arima_forecast, check_stationarity, find_optimal_pdq, generate_acf_pacf_plots
        
        data = request.get_json()
        
        # 验证输入参数
        required_fields = ['data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必要参数: {field}'}), 400
        
        # 转换参数
        time_series_data = data['data']
        forecast_steps = int(data.get('forecast_steps', 5))
        order = data.get('order', None)
        
        if order:
            order = tuple(order)
        
        # 进行ARIMA预测
        result = arima_forecast(time_series_data, order, forecast_steps)
        
        if result['success']:
            # 生成ACF和PACF图
            acf_pacf_plot = generate_acf_pacf_plots(time_series_data)
            result['acf_pacf_plot'] = acf_pacf_plot
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"ARIMA预测错误: {str(e)}")
        return jsonify({'error': str(e)}), 500


@models_bp.route('/api/forecasting/garch', methods=['POST'])
def forecast_garch():
    """API端点：使用GARCH模型进行波动率预测"""
    try:
        from services.models.forecasting import garch_forecast, find_optimal_garch_params, generate_volatility_plot
        
        data = request.get_json()
        
        # 验证输入参数
        required_fields = ['returns']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必要参数: {field}'}), 400
        
        # 转换参数
        returns = data['returns']
        forecast_steps = int(data.get('forecast_steps', 5))
        params = data.get('params', None)
        
        if params:
            p, q = params
        else:
            # 自动选择最优参数
            p, q = find_optimal_garch_params(returns)
        
        # 进行GARCH预测
        result = garch_forecast(returns, p, q, forecast_steps)
        
        if result['success']:
            # 生成波动率图
            if 'data' in data:
                volatility_plot = generate_volatility_plot(data['data'], returns)
                result['volatility_plot'] = volatility_plot
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"GARCH预测错误: {str(e)}")
        return jsonify({'error': str(e)}), 500
