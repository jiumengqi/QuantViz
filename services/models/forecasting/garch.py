import numpy as np
import pandas as pd
from arch import arch_model
import matplotlib.pyplot as plt
import io
import base64


def garch_forecast(returns, p=1, q=1, forecast_steps=5):
    """
    使用GARCH模型预测波动率
    
    参数:
    returns: 收益率时间序列数据
    p: GARCH模型的p参数，默认为1
    q: GARCH模型的q参数，默认为1
    forecast_steps: 预测步数，默认为5
    
    返回:
    包含预测结果的字典
    """
    try:
        # 转换为numpy数组
        returns = np.array(returns, dtype=float)
        
        # 检查数据长度
        if len(returns) < 20:
            return {
                'success': False,
                'error': '数据长度不足，至少需要20个数据点'
            }
        
        # 拟合GARCH模型
        model = arch_model(returns, vol='Garch', p=p, q=q)
        model_fit = model.fit(disp='off')
        
        # 进行预测
        forecast = model_fit.forecast(horizon=forecast_steps)
        
        # 获取波动率预测
        volatility_forecast = forecast.variance.values[-1, :] ** 0.5
        volatility_forecast = volatility_forecast.tolist()
        
        # 获取模型摘要
        summary = model_fit.summary().as_text()
        
        # 构建预测结果
        result = {
            'success': True,
            'params': (p, q),
            'volatility_forecast': volatility_forecast,
            'forecast_steps': forecast_steps,
            'aic': model_fit.aic,
            'bic': model_fit.bic,
            'summary': summary
        }
        
        return result
    except Exception as e:
        print(f"GARCH预测错误: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def find_optimal_garch_params(returns, max_p=2, max_q=2):
    """
    寻找GARCH模型的最优参数(p, q)
    
    参数:
    returns: 收益率时间序列数据
    max_p: 最大p值，默认为2
    max_q: 最大q值，默认为2
    
    返回:
    最优参数(p, q)
    """
    try:
        best_aic = float('inf')
        best_pq = (1, 1)
        
        for p in range(1, max_p + 1):
            for q in range(1, max_q + 1):
                try:
                    model = arch_model(returns, vol='Garch', p=p, q=q)
                    model_fit = model.fit(disp='off')
                    aic = model_fit.aic
                    if aic < best_aic:
                        best_aic = aic
                        best_pq = (p, q)
                except:
                    continue
        
        return best_pq
    except Exception as e:
        print(f"GARCH参数选择错误: {e}")
        return (1, 1)  # 默认参数


def generate_volatility_plot(data, volatility):
    """
    生成波动率图表
    
    参数:
    data: 原始数据
    volatility: 波动率数据
    
    返回:
    包含波动率图的base64编码字符串
    """
    try:
        # 创建图表
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # 绘制原始数据
        ax1.plot(data, label='原始数据', color='blue')
        ax1.set_ylabel('价格', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')
        
        # 创建第二个y轴用于波动率
        ax2 = ax1.twinx()
        ax2.plot(volatility, label='波动率', color='red', alpha=0.7)
        ax2.set_ylabel('波动率', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        
        # 添加标题和图例
        plt.title('价格与波动率')
        fig.tight_layout()
        
        # 保存为base64编码
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
    except Exception as e:
        print(f"生成波动率图错误: {e}")
        return None
