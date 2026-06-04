# -*- coding: utf-8 -*-
"""
股票机器学习预测模块
使用scikit-learn实现股票涨跌预测
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(current_dir, '../../'))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from config import Config
from services.analyzer import FinancialAnalyzer

# 创建logger
logger = logging.getLogger(__name__)

# 导入机器学习库
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve, auc
)
from sklearn.preprocessing import StandardScaler

# 尝试导入XGBoost
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
    logger.info("XGBoost模块已成功导入")
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost模块未安装，将不使用XGBoost模型")


class MLPredictor:
    """机器学习预测器，用于股票涨跌预测"""

    # 支持的模型
    SUPPORTED_MODELS = {
        'logistic': LogisticRegression,
        'random_forest': RandomForestClassifier,
        'xgboost': XGBClassifier if XGBOOST_AVAILABLE else None
    }

    # 支持的特征类型
    FEATURE_CATEGORIES = {
        'technical': [
            'ma5', 'ma10', 'ma20', 'ma60',
            'rsi14', 'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_middle', 'bb_lower',
            'kdj_k', 'kdj_d', 'kdj_j',
            'cci14', 'roc10', 'atr14', 'wpr14',
            'bias6', 'bias12', 'bias24',
            'vol_ma5', 'vol_ma20'
        ],
        'fundamental': [
            'return_1d', 'return_5d', 'return_10d', 'return_20d',
            'volatility', 'volume_ratio'
        ]
    }

    # 所有可用特征
    ALL_FEATURES = sum(FEATURE_CATEGORIES.values(), [])

    def __init__(self):
        """初始化预测器"""
        self.analyzer = FinancialAnalyzer()
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_type = None
        self.model_params = {}

    def get_stock_data(self, ts_code, start_date=None, end_date=None):
        """
        获取股票数据并计算特征
        :param ts_code: 股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 包含特征的DataFrame
        """
        try:
            # 获取原始数据
            df = self.analyzer.get_stock_data(ts_code, start_date, end_date)

            if df is None or df.empty:
                return None

            # 计算收益率
            df = self.analyzer.calculate_return(df)

            # 计算技术指标
            df = self.analyzer.calculate_technical_indicators(df)

            # 计算波动率
            if 'return_1d' in df.columns:
                df['volatility'] = df['return_1d'].rolling(window=20).std()

            # 计算成交量比率
            if 'vol' in df.columns and 'vol_ma20' in df.columns:
                df['volume_ratio'] = df['vol'] / df['vol_ma20']

            return df

        except Exception as e:
            logger.error(f"获取股票数据失败: {str(e)}")
            return None

    def prepare_features(self, df, feature_list=None, target_type='next_day_direction'):
        """
        准备特征和目标变量
        :param df: 包含股票数据的DataFrame
        :param feature_list: 要使用的特征列表
        :param target_type: 目标类型 ('next_day_direction', 'future_n_return')
        :return: 特征矩阵X, 目标变量y
        """
        if df is None or df.empty:
            return None, None

        df_copy = df.copy()

        # 确定要使用的特征
        if feature_list is None:
            feature_list = self.ALL_FEATURES

        # 过滤存在的特征
        available_features = [f for f in feature_list if f in df_copy.columns]
        self.feature_names = available_features

        if len(available_features) == 0:
            logger.warning("没有可用的特征")
            return None, None

        # 创建目标变量：次日涨跌方向
        if target_type == 'next_day_direction':
            df_copy['target'] = (df_copy['close'].shift(-1) > df_copy['close']).astype(int)
        else:
            # 未来N日收益率
            df_copy['target'] = (df_copy['close'].shift(-5) > df_copy['close']).astype(int)

        # 删除包含NaN的行
        df_clean = df_copy.dropna(subset=available_features + ['target'])

        if len(df_clean) < 50:
            logger.warning(f"有效样本数不足: {len(df_clean)}")
            return None, None

        # 准备特征矩阵
        X = df_clean[available_features].values
        y = df_clean['target'].values

        return X, y

    def train_model(self, X, y, model_type='logistic', test_size=0.2, **kwargs):
        """
        训练机器学习模型
        :param X: 特征矩阵
        :param y: 目标变量
        :param model_type: 模型类型 ('logistic', 'random_forest', 'xgboost')
        :param test_size: 测试集比例
        :param kwargs: 模型参数
        :return: 训练结果字典
        """
        if X is None or y is None:
            return {'success': False, 'error': '数据无效'}

        try:
            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, shuffle=False
            )

            # 标准化特征
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # 选择模型
            if model_type == 'logistic':
                params = {
                    'max_iter': kwargs.get('max_iter', 1000),
                    'random_state': 42
                }
                self.model = LogisticRegression(**params)

            elif model_type == 'random_forest':
                params = {
                    'n_estimators': kwargs.get('n_estimators', 100),
                    'max_depth': kwargs.get('max_depth', 10),
                    'min_samples_split': kwargs.get('min_samples_split', 5),
                    'random_state': 42
                }
                self.model = RandomForestClassifier(**params)

            elif model_type == 'xgboost':
                if not XGBOOST_AVAILABLE:
                    return {'success': False, 'error': 'XGBoost未安装'}
                params = {
                    'n_estimators': kwargs.get('n_estimators', 100),
                    'max_depth': kwargs.get('max_depth', 6),
                    'learning_rate': kwargs.get('learning_rate', 0.1),
                    'random_state': 42,
                    'use_label_encoder': False,
                    'eval_metric': 'logloss'
                }
                self.model = XGBClassifier(**params)

            else:
                return {'success': False, 'error': f'不支持的模型类型: {model_type}'}

            self.model_type = model_type
            self.model_params = params

            # 训练模型
            self.model.fit(X_train_scaled, y_train)

            # 预测
            y_pred = self.model.predict(X_test_scaled)
            y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

            # 计算评估指标
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            cm = confusion_matrix(y_test, y_pred)

            # 计算ROC曲线和AUC
            fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
            roc_auc = auc(fpr, tpr)

            # 交叉验证
            X_scaled = self.scaler.fit_transform(X)
            cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)

            # 特征重要性
            feature_importance = None
            if model_type == 'random_forest':
                feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
            elif model_type == 'xgboost':
                feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
            elif model_type == 'logistic':
                feature_importance = dict(zip(self.feature_names, abs(self.model.coef_[0])))

            result = {
                'success': True,
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1),
                'roc_auc': float(roc_auc),
                'confusion_matrix': cm.tolist(),
                'cv_mean': float(cv_scores.mean()),
                'cv_std': float(cv_scores.std()),
                'feature_importance': feature_importance,
                'train_size': len(X_train),
                'test_size': len(X_test),
                'model_type': model_type,
                'model_params': params,
                'fpr': fpr.tolist(),
                'tpr': tpr.tolist()
            }

            return result

        except Exception as e:
            logger.error(f"模型训练失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def predict(self, df, feature_list=None):
        """
        使用训练好的模型进行预测
        :param df: 包含最新数据的DataFrame
        :param feature_list: 特征列表
        :return: 预测结果
        """
        if self.model is None:
            return {'success': False, 'error': '模型未训练'}

        try:
            if feature_list is None:
                feature_list = self.feature_names

            # 获取最新一行数据
            latest = df[feature_list].iloc[-1:].values

            if np.isnan(latest).any():
                return {'success': False, 'error': '特征数据包含NaN'}

            # 标准化
            latest_scaled = self.scaler.transform(latest)

            # 预测
            prediction = self.model.predict(latest_scaled)[0]
            probability = self.model.predict_proba(latest_scaled)[0]

            # 生成交易信号
            signal = '买入' if prediction == 1 else '卖出'
            confidence = probability[prediction] if prediction == 1 else probability[0]

            return {
                'success': True,
                'prediction': int(prediction),
                'signal': signal,
                'confidence': float(confidence),
                'probability': {
                    '下跌': float(probability[0]),
                    '上涨': float(probability[1])
                }
            }

        except Exception as e:
            logger.error(f"预测失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def generate_trading_signals(self, df):
        """
        生成交易信号序列
        :param df: 包含数据的DataFrame
        :return: 包含信号的DataFrame
        """
        if self.model is None:
            return None

        try:
            df_copy = df.copy()

            # 获取特征数据
            available_features = [f for f in self.feature_names if f in df_copy.columns]
            X = df_copy[available_features].values

            # 处理NaN
            X = np.nan_to_num(X, nan=0)

            # 标准化
            X_scaled = self.scaler.transform(X)

            # 批量预测
            predictions = self.model.predict(X_scaled)
            probabilities = self.model.predict_proba(X_scaled)

            # 添加到DataFrame
            df_copy['ml_signal'] = predictions
            df_copy['ml_confidence'] = np.max(probabilities, axis=1)
            df_copy['ml_action'] = df_copy['ml_signal'].map({1: '买入', 0: '卖出'})

            return df_copy

        except Exception as e:
            logger.error(f"生成交易信号失败: {str(e)}")
            return None

    def plot_confusion_matrix(self, cm, save_path=None):
        """
        绘制混淆矩阵
        :param cm: 混淆矩阵
        :param save_path: 保存路径
        :return: base64编码的图像
        """
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                       xticklabels=['预测下跌', '预测上涨'],
                       yticklabels=['实际下跌', '实际上涨'])
            ax.set_xlabel('预测值')
            ax.set_ylabel('实际值')
            ax.set_title('混淆矩阵')

            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')

            # 转换为base64
            image_base64 = self._fig_to_base64(fig)
            plt.close()

            return image_base64

        except Exception as e:
            logger.error(f"绘制混淆矩阵失败: {str(e)}")
            return None

    def plot_feature_importance(self, feature_importance, save_path=None):
        """
        绘制特征重要性图
        :param feature_importance: 特征重要性字典
        :param save_path: 保存路径
        :return: base64编码的图像
        """
        try:
            if feature_importance is None:
                return None

            # 排序
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            features = [f[0] for f in sorted_features[:15]]
            importances = [f[1] for f in sorted_features[:15]]

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(features, importances)
            ax.set_xlabel('重要性')
            ax.set_title('特征重要性 (Top 15)')
            ax.invert_yaxis()

            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')

            image_base64 = self._fig_to_base64(fig)
            plt.close()

            return image_base64

        except Exception as e:
            logger.error(f"绘制特征重要性图失败: {str(e)}")
            return None

    def plot_roc_curve(self, fpr, tpr, roc_auc, save_path=None):
        """
        绘制ROC曲线
        :param fpr: 假阳性率
        :param tpr: 真阳性率
        :param roc_auc: AUC值
        :param save_path: 保存路径
        :return: base64编码的图像
        """
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot(fpr, tpr, color='darkorange', lw=2,
                   label=f'ROC曲线 (AUC = {roc_auc:.4f})')
            ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
            ax.set_xlim([0.0, 1.0])
            ax.set_ylim([0.0, 1.05])
            ax.set_xlabel('假阳性率 (FPR)')
            ax.set_ylabel('真阳性率 (TPR)')
            ax.set_title('ROC曲线')
            ax.legend(loc='lower right')

            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')

            image_base64 = self._fig_to_base64(fig)
            plt.close()

            return image_base64

        except Exception as e:
            logger.error(f"绘制ROC曲线失败: {str(e)}")
            return None

    def _fig_to_base64(self, fig):
        """将matplotlib figure转换为base64"""
        import io
        import base64
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return image_base64

    def get_available_features(self):
        """
        获取所有可用特征
        :return: 特征分类字典
        """
        return self.FEATURE_CATEGORIES

    def get_feature_description(self):
        """
        获取特征描述
        :return: 特征描述字典
        """
        descriptions = {
            'ma5': '5日移动平均线',
            'ma10': '10日移动平均线',
            'ma20': '20日移动平均线',
            'ma60': '60日移动平均线',
            'rsi14': '相对强弱指数(14日)',
            'macd': 'MACD指标',
            'macd_signal': 'MACD信号线',
            'macd_hist': 'MACD柱状图',
            'bb_upper': '布林带上轨',
            'bb_middle': '布林带中轨',
            'bb_lower': '布林带下轨',
            'kdj_k': 'KDJ指标K值',
            'kdj_d': 'KDJ指标D值',
            'kdj_j': 'KDJ指标J值',
            'cci14': '顺势指标(14日)',
            'roc10': '变动率指标(10日)',
            'atr14': '平均真实波幅(14日)',
            'wpr14': '威廉指标(14日)',
            'bias6': '乖离率(6日)',
            'bias12': '乖离率(12日)',
            'bias24': '乖离率(24日)',
            'vol_ma5': '成交量5日均线',
            'vol_ma20': '成交量20日均线',
            'return_1d': '1日收益率',
            'return_5d': '5日收益率',
            'return_10d': '10日收益率',
            'return_20d': '20日收益率',
            'volatility': '波动率(20日标准差)',
            'volume_ratio': '成交量比率'
        }
        return descriptions


# 创建全局实例
ml_predictor = MLPredictor()
