from flask import Blueprint, render_template, request, jsonify, current_app
from services.analyzer import financial_analyzer
import json
from datetime import datetime, timedelta

# 创建分析模块蓝图
analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/')
def analysis_index():
    """数据分析首页"""
    # 获取默认日期范围
    today = datetime.now().strftime("%Y-%m-%d")
    default_start = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    
    # 获取可选的股票列表
    from config import HOT_STOCKS
    available_stocks = HOT_STOCKS
    
    return render_template(
        'analysis.html',
        today=today,
        default_start=default_start,
        available_stocks=available_stocks
    )

@analysis_bp.route('/correlation')
def correlation_analysis():
    """相关性分析页面"""
    # 获取默认日期范围
    today = datetime.now().strftime("%Y-%m-%d")
    default_start = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    
    # 获取可选的股票列表
    from config import HOT_STOCKS
    available_stocks = HOT_STOCKS
    
    return render_template(
        'analysis/correlation.html',
        today=today,
        default_start=default_start,
        available_stocks=available_stocks
    )

@analysis_bp.route('/factors')
def factor_analysis():
    """因子分析页面"""
    # 获取默认日期范围
    today = datetime.now().strftime("%Y-%m-%d")
    default_start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    return render_template(
        'analysis/factors.html',
        today=today,
        default_start=default_start
    )

@analysis_bp.route('/heatmap')
def heatmap_analysis():
    """热力图分析页面"""
    # 获取默认日期范围
    today = datetime.now().strftime("%Y-%m-%d")
    default_start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    return render_template(
        'analysis/heatmap.html',
        today=today,
        default_start=default_start
    )

@analysis_bp.route('/api/analyze', methods=['POST'])
def analyze_stock():
    """股票分析API"""
    try:
        data = request.json
        stock_code = data.get('stockCode')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        
        # 调用分析器进行实际分析
        from services.analyzer import financial_analyzer
        
        # 获取股票数据
        df = financial_analyzer.get_stock_data(stock_code, start_date, end_date)
        
        if df is None or df.empty:
            return jsonify({'success': False, 'message': '无法获取股票数据'}), 404
        
        # 计算收益率
        df = financial_analyzer.calculate_return(df)
        
        # 计算技术指标
        df = financial_analyzer.calculate_technical_indicators(df)
        
        # 计算风险指标
        risk_indicators = financial_analyzer.calculate_risk_indicators(df)
        
        # 生成分析结果
        latest_data = {
            'close': 0,
            'open': 0,
            'high': 0,
            'low': 0,
            'vol': 0,
            'trade_date': ''
        }
        
        if not df.empty:
            # 安全获取最新数据
            latest_data['close'] = float(df.get('close', [0]).iloc[-1]) if not df.get('close', pd.Series()).empty else 0
            latest_data['open'] = float(df.get('open', [0]).iloc[-1]) if not df.get('open', pd.Series()).empty else 0
            latest_data['high'] = float(df.get('high', [0]).iloc[-1]) if not df.get('high', pd.Series()).empty else 0
            latest_data['low'] = float(df.get('low', [0]).iloc[-1]) if not df.get('low', pd.Series()).empty else 0
            latest_data['vol'] = float(df.get('vol', [0]).iloc[-1]) if not df.get('vol', pd.Series()).empty else 0
            
            if 'trade_date' in df.columns and not df['trade_date'].empty:
                try:
                    latest_data['trade_date'] = df['trade_date'].iloc[-1].strftime('%Y-%m-%d')
                except:
                    latest_data['trade_date'] = str(df['trade_date'].iloc[-1])
        
        technical_indicators = {
            'ma5': 0,
            'ma20': 0,
            'ma60': 0,
            'rsi14': 0,
            'macd': 0,
            'macd_signal': 0,
            'kdj_k': 0,
            'kdj_d': 0,
            'kdj_j': 0
        }
        
        if not df.empty:
            # 安全获取技术指标
            technical_indicators['ma5'] = float(df.get('ma5', [0]).iloc[-1]) if not df.get('ma5', pd.Series()).empty else 0
            technical_indicators['ma20'] = float(df.get('ma20', [0]).iloc[-1]) if not df.get('ma20', pd.Series()).empty else 0
            technical_indicators['ma60'] = float(df.get('ma60', [0]).iloc[-1]) if not df.get('ma60', pd.Series()).empty else 0
            technical_indicators['rsi14'] = float(df.get('rsi14', [0]).iloc[-1]) if not df.get('rsi14', pd.Series()).empty else 0
            technical_indicators['macd'] = float(df.get('macd', [0]).iloc[-1]) if not df.get('macd', pd.Series()).empty else 0
            technical_indicators['macd_signal'] = float(df.get('macd_signal', [0]).iloc[-1]) if not df.get('macd_signal', pd.Series()).empty else 0
            technical_indicators['kdj_k'] = float(df.get('kdj_k', [0]).iloc[-1]) if not df.get('kdj_k', pd.Series()).empty else 0
            technical_indicators['kdj_d'] = float(df.get('kdj_d', [0]).iloc[-1]) if not df.get('kdj_d', pd.Series()).empty else 0
            technical_indicators['kdj_j'] = float(df.get('kdj_j', [0]).iloc[-1]) if not df.get('kdj_j', pd.Series()).empty else 0
        
        result = {
            'success': True,
            'message': '分析成功',
            'stockCode': stock_code,
            'period': f'{start_date} 至 {end_date}',
            'status': 'completed',
            'risk_indicators': risk_indicators,
            'latest_data': latest_data,
            'technical_indicators': technical_indicators
        }
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"股票分析失败: {str(e)}")
        return jsonify({'success': False, 'message': f'分析失败: {str(e)}'}), 500