# -*- coding: utf-8 -*-
"""
机器学习预测路由
提供股票涨跌预测的API接口
"""
from flask import Blueprint, render_template, request, jsonify
import logging
import json

# 创建日志记录器
logger = logging.getLogger(__name__)

# 创建机器学习预测蓝图
ml_prediction_bp = Blueprint('ml_prediction', __name__)


@ml_prediction_bp.route('/')
def ml_prediction_index():
    """机器学习预测首页"""
    return render_template('models/ml_prediction.html')


@ml_prediction_bp.route('/api/features', methods=['GET'])
def get_available_features():
    """
    获取所有可用特征列表
    :return: 特征分类列表
    """
    try:
        from services.models.ml_predictor import ml_predictor, MLPredictor

        features = ml_predictor.get_available_features()
        descriptions = ml_predictor.get_feature_description()

        result = {
            'success': True,
            'features': features,
            'descriptions': descriptions
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"获取特征列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ml_prediction_bp.route('/api/train', methods=['POST'])
def train_model():
    """
    训练机器学习模型（支持旧 MLPredictor 和新 EnhancedModelManager）
    请求参数:
    {
        "stock_code": "600036.SH",
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "model_type": "logistic|random_forest|xgboost|lightgbm|lstm|ensemble",
        "feature_categories": ["technical", "fundamental"],
        "test_size": 0.2
    }
    """
    try:
        from services.models.ml_predictor import ml_predictor, MLPredictor

        data = request.get_json()

        # 验证必要参数
        if not data or 'stock_code' not in data:
            return jsonify({'success': False, 'error': '缺少必要参数: stock_code'}), 400

        stock_code = data['stock_code']
        start_date = data.get('start_date', '2020-01-01')
        end_date = data.get('end_date', '2024-12-31')
        model_type = data.get('model_type', 'logistic')
        feature_categories = data.get('feature_categories', ['technical'])
        test_size = float(data.get('test_size', 0.2))

        # 获取特征列表
        feature_list = []
        for category in feature_categories:
            if category in MLPredictor.FEATURE_CATEGORIES:
                feature_list.extend(MLPredictor.FEATURE_CATEGORIES[category])

        # 获取股票数据
        df = ml_predictor.get_stock_data(stock_code, start_date, end_date)

        if df is None or df.empty:
            return jsonify({'success': False, 'error': '无法获取股票数据'}), 400

        # ---- 增强模型分支（xgboost 增强版 / lightgbm / lstm / ensemble） ----
        ENHANCED_MODELS = ['xgboost', 'lightgbm', 'lstm', 'ensemble']
        if model_type in ENHANCED_MODELS:
            return _train_enhanced_model(stock_code, start_date, end_date, model_type, df, test_size)

        # ---- 传统模型分支（logistic / random_forest） ----
        # 验证模型类型
        if model_type not in ['logistic', 'random_forest']:
            return jsonify({'success': False, 'error': f'不支持的模型类型: {model_type}'}), 400

        # 准备特征
        X, y = ml_predictor.prepare_features(df, feature_list)

        if X is None or y is None:
            return jsonify({'success': False, 'error': '特征准备失败，数据不足'}), 400

        # 训练模型
        result = ml_predictor.train_model(X, y, model_type, test_size)

        if not result['success']:
            return jsonify(result), 400

        # 生成图表
        cm_base64 = None
        fi_base64 = None
        roc_base64 = None

        try:
            cm_base64 = ml_predictor.plot_confusion_matrix(result['confusion_matrix'])
            if result['feature_importance']:
                fi_base64 = ml_predictor.plot_feature_importance(result['feature_importance'])
            roc_base64 = ml_predictor.plot_roc_curve(result['fpr'], result['tpr'], result['roc_auc'])
        except Exception as e:
            logger.warning(f"生成图表失败: {str(e)}")

        # 添加图表到结果
        result['confusion_matrix_plot'] = cm_base64
        result['feature_importance_plot'] = fi_base64
        result['roc_curve_plot'] = roc_base64
        result['stock_code'] = stock_code
        result['start_date'] = start_date
        result['end_date'] = end_date

        return jsonify(result)

    except Exception as e:
        logger.error(f"模型训练失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _train_enhanced_model(stock_code, start_date, end_date, model_type, df, test_size):
    """使用 EnhancedModelManager 训练增强模型"""
    from services.ml_enhanced import enhanced_model_manager, FeatureEngineer

    # 用 FeatureEngineer 准备数据
    df_copy = df.copy()
    df_copy['target'] = (df_copy['close'].shift(-1) > df_copy['close']).astype(int)
    X, y = FeatureEngineer.prepare_supervised_data(df_copy)

    if X is None or y is None:
        return jsonify({'success': False, 'error': '特征准备失败，数据不足'}), 400

    # 训练
    result = enhanced_model_manager.train(X, y, model_type, test_size=test_size)

    if not result.get('success'):
        return jsonify(result), 400

    # 生成图表
    from services.models.ml_predictor import ml_predictor
    cm_base64 = None
    fi_base64 = None
    roc_base64 = None

    try:
        if 'confusion_matrix' in result:
            cm_base64 = ml_predictor.plot_confusion_matrix(result['confusion_matrix'])
        if 'fpr' in result and 'tpr' in result:
            roc_base64 = ml_predictor.plot_roc_curve(result['fpr'], result['tpr'], result.get('roc_auc', 0))
    except Exception as e:
        logger.warning(f"生成增强模型图表失败: {str(e)}")

    # 特征重要性
    fi_data = result.get('feature_importance')
    if fi_data:
        try:
            fi_base64 = ml_predictor.plot_feature_importance(fi_data)
        except Exception:
            pass

    result['confusion_matrix_plot'] = cm_base64
    result['feature_importance_plot'] = fi_base64
    result['roc_curve_plot'] = roc_base64
    result['stock_code'] = stock_code
    result['start_date'] = start_date
    result['end_date'] = end_date

    return jsonify(result)


@ml_prediction_bp.route('/api/predict', methods=['POST'])
def predict():
    """
    使用训练好的模型进行预测（支持增强模型）
    请求参数:
    {
        "stock_code": "600036.SH",
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "feature_categories": ["technical", "fundamental"],
        "model_type": "logistic|random_forest|xgboost|lightgbm|lstm|ensemble"
    }
    """
    try:
        from services.models.ml_predictor import ml_predictor, MLPredictor

        data = request.get_json()

        # 验证必要参数
        if not data or 'stock_code' not in data:
            return jsonify({'success': False, 'error': '缺少必要参数: stock_code'}), 400

        stock_code = data['stock_code']
        start_date = data.get('start_date', '2020-01-01')
        end_date = data.get('end_date', '2024-12-31')
        feature_categories = data.get('feature_categories', ['technical'])
        model_type = data.get('model_type', 'logistic')

        # 获取特征列表
        feature_list = []
        for category in feature_categories:
            if category in MLPredictor.FEATURE_CATEGORIES:
                feature_list.extend(MLPredictor.FEATURE_CATEGORIES[category])

        # 获取股票数据
        df = ml_predictor.get_stock_data(stock_code, start_date, end_date)

        if df is None or df.empty:
            return jsonify({'success': False, 'error': '无法获取股票数据'}), 400

        # ---- 增强模型分支 ----
        ENHANCED_MODELS = ['xgboost', 'lightgbm', 'lstm', 'ensemble']
        if model_type in ENHANCED_MODELS:
            return _predict_enhanced_model(stock_code, model_type, df)

        # ---- 传统模型分支 ----
        # 检查模型是否已训练
        if ml_predictor.model is None or ml_predictor.model_type != model_type:
            # 需要先训练模型
            X, y = ml_predictor.prepare_features(df, feature_list)

            if X is None or y is None:
                return jsonify({'success': False, 'error': '特征准备失败'}), 400

            train_result = ml_predictor.train_model(X, y, model_type, test_size=0.2)

            if not train_result['success']:
                return jsonify(train_result), 400

        # 进行预测
        prediction_result = ml_predictor.predict(df, feature_list)

        if not prediction_result['success']:
            return jsonify(prediction_result), 400

        # 获取最新数据信息
        latest_data = {
            'date': df['trade_date'].iloc[-1].strftime('%Y-%m-%d') if 'trade_date' in df.columns else None,
            'close': float(df['close'].iloc[-1]) if 'close' in df.columns else None
        }

        prediction_result['latest_data'] = latest_data
        prediction_result['stock_code'] = stock_code

        return jsonify(prediction_result)

    except Exception as e:
        logger.error(f"预测失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _predict_enhanced_model(stock_code, model_type, df):
    """使用 EnhancedModelManager 进行预测"""
    from services.ml_enhanced import enhanced_model_manager, FeatureEngineer

    df_copy = df.copy()
    df_copy['target'] = (df_copy['close'].shift(-1) > df_copy['close']).astype(int)
    X, y = FeatureEngineer.prepare_supervised_data(df_copy)

    if X is None:
        return jsonify({'success': False, 'error': '特征准备失败'}), 400

    # 确保模型已训练
    status = enhanced_model_manager.get_status(model_type)
    if not status.get('trained', False):
        # 自动训练
        train_result = enhanced_model_manager.train(X, y, model_type, test_size=0.2)
        if not train_result.get('success'):
            return jsonify(train_result), 400

    # 预测
    prediction_result = enhanced_model_manager.predict(X, model_type)

    if not prediction_result.get('success'):
        return jsonify(prediction_result), 400

    latest_data = {
        'date': df['trade_date'].iloc[-1].strftime('%Y-%m-%d') if 'trade_date' in df.columns else None,
        'close': float(df['close'].iloc[-1]) if 'close' in df.columns else None
    }

    prediction_result['latest_data'] = latest_data
    prediction_result['stock_code'] = stock_code

    return jsonify(prediction_result)


@ml_prediction_bp.route('/api/signals', methods=['POST'])
def generate_signals():
    """
    生成交易信号序列
    请求参数:
    {
        "stock_code": "600036.SH",
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "model_type": "logistic|random_forest|xgboost"
    }
    """
    try:
        from services.models.ml_predictor import ml_predictor, MLPredictor

        data = request.get_json()

        # 验证必要参数
        if not data or 'stock_code' not in data:
            return jsonify({'success': False, 'error': '缺少必要参数: stock_code'}), 400

        stock_code = data['stock_code']
        start_date = data.get('start_date', '2020-01-01')
        end_date = data.get('end_date', '2024-12-31')
        model_type = data.get('model_type', 'logistic')

        # 获取特征列表
        feature_list = MLPredictor.ALL_FEATURES

        # 获取股票数据
        df = ml_predictor.get_stock_data(stock_code, start_date, end_date)

        if df is None or df.empty:
            return jsonify({'success': False, 'error': '无法获取股票数据'}), 400

        # 检查模型是否已训练
        if ml_predictor.model is None or ml_predictor.model_type != model_type:
            # 需要先训练模型
            X, y = ml_predictor.prepare_features(df, feature_list)

            if X is None or y is None:
                return jsonify({'success': False, 'error': '特征准备失败'}), 400

            train_result = ml_predictor.train_model(X, y, model_type, test_size=0.2)

            if not train_result['success']:
                return jsonify(train_result), 400

        # 生成交易信号
        df_with_signals = ml_predictor.generate_trading_signals(df)

        if df_with_signals is None:
            return jsonify({'success': False, 'error': '生成交易信号失败'}), 400

        # 转换日期格式
        if 'trade_date' in df_with_signals.columns:
            df_with_signals['trade_date'] = df_with_signals['trade_date'].dt.strftime('%Y-%m-%d')

        # 获取信号统计
        signal_counts = df_with_signals['ml_action'].value_counts().to_dict()

        # 只返回部分数据（避免数据量过大）
        result_df = df_with_signals[['trade_date', 'close', 'ml_signal', 'ml_confidence', 'ml_action']].tail(100)

        result = {
            'success': True,
            'stock_code': stock_code,
            'signals': result_df.to_dict(orient='records'),
            'signal_counts': signal_counts,
            'total_records': len(df_with_signals)
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"生成交易信号失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ml_prediction_bp.route('/api/models', methods=['GET'])
def get_available_models():
    """
    列出所有可用的 ML 模型及其状态
    返回增强模型（来自 ml_enhanced）+ 传统模型状态
    """
    try:
        from services.models.ml_predictor import ml_predictor

        # 传统模型状态
        traditional = {
            'logistic': {
                'type': 'logistic',
                'name': '逻辑回归',
                'module': 'sklearn',
                'available': True,
                'trained': ml_predictor.model is not None and ml_predictor.model_type == 'logistic'
            },
            'random_forest': {
                'type': 'random_forest',
                'name': '随机森林',
                'module': 'sklearn',
                'available': True,
                'trained': ml_predictor.model is not None and ml_predictor.model_type == 'random_forest'
            }
        }

        # 增强模型状态
        try:
            from services.ml_enhanced import enhanced_model_manager
            enhanced_models = enhanced_model_manager.get_available_models()
        except ImportError as e:
            logger.warning(f"增强模型模块不可用: {e}")
            enhanced_models = []

        return jsonify({
            'success': True,
            'models': enhanced_models,
            'traditional': list(traditional.values())
        })

    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ml_prediction_bp.route('/api/metrics', methods=['GET'])
def get_model_metrics():
    """
    获取当前模型的评估指标
    """
    try:
        from services.models.ml_predictor import ml_predictor

        if ml_predictor.model is None:
            return jsonify({'success': False, 'error': '模型未训练'}), 400

        result = {
            'success': True,
            'model_type': ml_predictor.model_type,
            'model_params': ml_predictor.model_params,
            'feature_names': ml_predictor.feature_names
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"获取模型指标失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
