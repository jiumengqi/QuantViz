import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt
import io
import base64


def difference(data, interval=1):
    """
    对时间序列数据进行差分，以使其平稳
    
    参数:
    data: 时间序列数据
    interval: 差分间隔，默认为1
    
    返回:
    差分后的数据
    """
    diff = []
    for i in range(interval, len(data)):
        value = data[i] - data[i - interval]
        diff.append(value)
    return np.array(diff)


def inverse_difference(history, yhat, interval=1):
    """
    将差分后的数据转换回原始尺度
    
    参数:
    history: 历史数据
    yhat: 预测的差分数据
    interval: 差分间隔，默认为1
    
    返回:
    转换后的预测值
    """
    return yhat + history[-interval]


def check_stationarity(series):
    """
    检查时间序列的平稳性
    
    参数:
    series: 时间序列数据
    
    返回:
    包含ADF检验结果的字典
    """
    try:
        result = adfuller(series)
        return {
            'adf_statistic': result[0],
            'p_value': result[1],
            'critical_values': result[4],
            'is_stationary': result[1] < 0.05
        }
    except Exception as e:
        print(f"平稳性检验错误: {e}")
        return {
            'adf_statistic': 0,
            'p_value': 1.0,
            'critical_values': {},
            'is_stationary': False
        }


def find_optimal_pdq(data, max_p=3, max_d=2, max_q=3):
    """
    寻找ARIMA模型的最优参数(p, d, q)
    
    参数:
    data: 时间序列数据
    max_p: 最大p值，默认为3
    max_d: 最大d值，默认为2
    max_q: 最大q值，默认为3
    
    返回:
    最优参数(p, d, q)
    """
    try:
        import warnings
        warnings.filterwarnings('ignore')
        
        best_aic = float('inf')
        best_pdq = (0, 0, 0)
        
        for p in range(max_p + 1):
            for d in range(max_d + 1):
                for q in range(max_q + 1):
                    try:
                        model = ARIMA(data, order=(p, d, q))
                        model_fit = model.fit()
                        aic = model_fit.aic
                        if aic < best_aic:
                            best_aic = aic
                            best_pdq = (p, d, q)
                    except:
                        continue
        
        return best_pdq
    except Exception as e:
        print(f"参数选择错误: {e}")
        return (1, 1, 1)  # 默认参数


def arima_forecast(data, order=None, forecast_steps=5):
    """
    使用ARIMA模型进行时间序列预测
    
    参数:
    data: 时间序列数据
    order: ARIMA模型参数(p, d, q)，如果为None则自动选择
    forecast_steps: 预测步数，默认为5
    
    返回:
    包含预测结果的字典
    """
    try:
        # 转换为numpy数组
        data = np.array(data, dtype=float)
        
        # 检查数据长度
        if len(data) < 10:
            return {
                'success': False,
                'error': '数据长度不足，至少需要10个数据点'
            }
        
        # 检查平稳性
        stationarity = check_stationarity(data)
        
        # 如果order为None，自动选择最优参数
        if order is None:
            order = find_optimal_pdq(data)
        
        # 拟合ARIMA模型
        model = ARIMA(data, order=order)
        model_fit = model.fit()
        
        # 进行预测
        forecast = model_fit.forecast(steps=forecast_steps)
        forecast = forecast.tolist()
        
        # 获取模型摘要
        summary = model_fit.summary().as_text()
        
        # 计算预测区间（近似）
        residuals = model_fit.resid
        residual_std = np.std(residuals)
        confidence_interval = 1.96 * residual_std
        
        # 构建预测结果
        result = {
            'success': True,
            'order': order,
            'forecast': forecast,
            'forecast_steps': forecast_steps,
            'confidence_interval': confidence_interval,
            'aic': model_fit.aic,
            'bic': model_fit.bic,
            'stationarity': stationarity,
            'summary': summary,
            'residuals': residuals.tolist()
        }
        
        return result
    except Exception as e:
        print(f"ARIMA预测错误: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def generate_acf_pacf_plots(data):
    """
    生成ACF和PACF图
    
    参数:
    data: 时间序列数据
    
    返回:
    包含ACF和PACF图的base64编码字符串
    """
    try:
        # 创建ACF图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        plot_acf(data, lags=20, ax=ax1)
        plot_pacf(data, lags=20, ax=ax2)
        
        # 保存为base64编码
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
    except Exception as e:
        print(f"生成ACF/PACF图错误: {e}")
        return None