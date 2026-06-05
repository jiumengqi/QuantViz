# -*- coding: utf-8 -*-
"""
增强机器学习预测模块
提供 XGBoost、LightGBM、LSTM、Ensemble 预测器
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(current_dir, '../../'))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve, auc
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

# ============================================================
# 可选依赖导入
# ============================================================
try:
    import xgboost as xgb
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
    logger.info("XGBoost 模块已成功导入")
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost 未安装，XGBoost 预测器不可用")

try:
    import lightgbm as lgb
    from lightgbm import LGBMClassifier
    LIGHTGBM_AVAILABLE = True
    logger.info("LightGBM 模块已成功导入")
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM 未安装，LightGBM 预测器不可用")

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
    logger.info("TensorFlow/Keras 模块已成功导入")
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow 未安装，LSTM 将使用 sklearn MLP 作为后备")


# ============================================================
# 特征工程工具
# ============================================================
class FeatureEngineer:
    """特征工程类，为增强模型提供统一的特征构建"""

    @staticmethod
    def build_price_features(df):
        """构建价格相关特征"""
        features = {}
        if 'close' in df.columns:
            close = df['close']
            features['close'] = close.values
            features['price_change'] = close.diff().values
            features['price_change_pct'] = close.pct_change().values
            features['high_low_ratio'] = (df['high'] / df['low']).values if 'high' in df.columns and 'low' in df.columns else np.zeros(len(df))
            features['close_position'] = np.zeros(len(df))
            if 'high' in df.columns and 'low' in df.columns:
                h_l_range = df['high'] - df['low']
                mask = h_l_range > 0
                features['close_position'][mask] = ((close.values[mask] - df['low'].values[mask]) / h_l_range.values[mask])
            for window in [5, 10, 20, 60]:
                features[f'ma_{window}'] = close.rolling(window=window).mean().values
                features[f'price_std_{window}'] = close.rolling(window=window).std().values
        return features

    @staticmethod
    def build_volume_features(df):
        """构建成交量相关特征"""
        features = {}
        if 'vol' in df.columns:
            vol = df['vol']
            features['volume'] = vol.values
            features['volume_change'] = vol.diff().values
            features['volume_change_pct'] = vol.pct_change().values
            for window in [5, 10, 20]:
                features[f'vol_ma_{window}'] = vol.rolling(window=window).mean().values
            features['volume_ratio_5'] = (vol / vol.rolling(window=5).mean()).values
            features['volume_ratio_20'] = (vol / vol.rolling(window=20).mean()).values
        return features

    @staticmethod
    def build_technical_features(df):
        """构建技术指标特征"""
        features = {}
        close = df['close'] if 'close' in df.columns else None
        high = df['high'] if 'high' in df.columns else close
        low = df['low'] if 'low' in df.columns else close
        vol = df['vol'] if 'vol' in df.columns else None

        if close is not None:
            # RSI
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = (-delta).where(delta < 0, 0.0)
            avg_gain_14 = gain.rolling(window=14).mean()
            avg_loss_14 = loss.rolling(window=14).mean()
            rs = avg_gain_14 / avg_loss_14
            features['rsi_14'] = (100.0 - (100.0 / (1.0 + rs))).values

            # MACD
            ema_12 = close.ewm(span=12, adjust=False).mean()
            ema_26 = close.ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            macd_signal = macd_line.ewm(span=9, adjust=False).mean()
            features['macd'] = macd_line.values
            features['macd_signal'] = macd_signal.values
            features['macd_hist'] = (macd_line - macd_signal).values

            # 布林带
            ma_20 = close.rolling(window=20).mean()
            std_20 = close.rolling(window=20).std()
            features['bb_upper'] = (ma_20 + 2 * std_20).values
            features['bb_middle'] = ma_20.values
            features['bb_lower'] = (ma_20 - 2 * std_20).values
            features['bb_width'] = ((features['bb_upper'] - features['bb_lower']) / features['bb_middle']).flatten()

            # KDJ
            low_min = low.rolling(window=9).min()
            high_max = high.rolling(window=9).max()
            rsv = (close - low_min) / (high_max - low_min) * 100.0
            k = rsv.ewm(alpha=1.0/3, adjust=False).mean()
            d = k.ewm(alpha=1.0/3, adjust=False).mean()
            features['kdj_k'] = k.values
            features['kdj_d'] = d.values
            features['kdj_j'] = (3 * k - 2 * d).values

            # 动量指标
            features['roc_10'] = ((close - close.shift(10)) / close.shift(10) * 100.0).values
            features['momentum_20'] = (close - close.shift(20)).values

            # 价格相对位置
            ll_20 = low.rolling(window=20).min()
            hh_20 = high.rolling(window=20).max()
            range_20 = hh_20 - ll_20
            features['williams_r'] = np.zeros(len(df))
            mask = range_20 > 0
            features['williams_r'][mask.values] = ((hh_20.values[mask.values] - close.values[mask.values]) / range_20.values[mask.values] * -100.0)

            # ATR
            tr1 = high - low
            tr2 = (high - close.shift()).abs()
            tr3 = (low - close.shift()).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            features['atr_14'] = tr.rolling(window=14).mean().values

        if vol is not None:
            # OBV 简化版
            features['obv'] = (vol * np.sign(close.diff().fillna(0))).cumsum().values

        return features

    @staticmethod
    def build_all_features(df):
        """构建所有特征，返回填充了 NaN 的 DataFrame"""
        all_features = {}
        all_features.update(FeatureEngineer.build_price_features(df))
        all_features.update(FeatureEngineer.build_volume_features(df))
        all_features.update(FeatureEngineer.build_technical_features(df))

        result_df = pd.DataFrame(all_features, index=df.index)
        # 用前向填充处理 NaN
        result_df = result_df.ffill().fillna(0)
        return result_df

    @staticmethod
    def prepare_supervised_data(df, target_col='target', lookback=1):
        """将时间序列转换为监督学习格式"""
        if target_col not in df.columns:
            close = df['close'] if 'close' in df.columns else None
            if close is not None:
                df[target_col] = (close.shift(-lookback) > close).astype(int)

        data = df.dropna()
        if len(data) < 50:
            return None, None

        feature_df = FeatureEngineer.build_all_features(data)
        y = data[target_col].values

        # 对齐索引
        common_idx = feature_df.index.intersection(data.index)
        X = feature_df.loc[common_idx].values
        y = y[:len(X)]

        return X, y


# ============================================================
# 1. XGBoost 预测器
# ============================================================
class XGBoostPredictor:
    """XGBoost 预测器 —— 梯度提升树"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.feature_importance = None
        self.best_params = None
        self.trained = False

    @property
    def available(self):
        return XGBOOST_AVAILABLE

    def _default_params(self):
        return {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'use_label_encoder': False,
            'eval_metric': 'logloss',
            'verbosity': 0
        }

    def train(self, X, y, test_size=0.2, hyper_tune=True):
        """训练 XGBoost 模型（支持简单超参数搜索）"""
        if not XGBOOST_AVAILABLE:
            return {'success': False, 'error': 'XGBoost 未安装，请运行 pip install xgboost'}

        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, shuffle=False
            )

            X_train_s = self.scaler.fit_transform(X_train)
            X_test_s = self.scaler.transform(X_test)

            params = self._default_params()

            if hyper_tune:
                best_score = 0
                for n_est in [100, 200]:
                    for lr in [0.01, 0.05, 0.1]:
                        for depth in [3, 6, 9]:
                            candidate = {**params, 'n_estimators': n_est, 'learning_rate': lr, 'max_depth': depth}
                            m = XGBClassifier(**candidate)
                            m.fit(X_train_s, y_train, verbose=False)
                            acc = accuracy_score(y_test, m.predict(X_test_s))
                            if acc > best_score:
                                best_score = acc
                                self.best_params = candidate
                                self.model = m

                params = self.best_params or params
            else:
                self.model = XGBClassifier(**params)
                self.model.fit(X_train_s, y_train, verbose=False)
                self.best_params = params

            y_pred = self.model.predict(X_test_s)
            y_proba = self.model.predict_proba(X_test_s)[:, 1]

            self.feature_importance = dict(
                sorted(zip(range(X.shape[1]), self.model.feature_importances_),
                       key=lambda x: x[1], reverse=True)
            )
            self.trained = True

            return self._build_result(y_test, y_pred, y_proba, X_train, X_test, 'xgboost')

        except Exception as e:
            logger.error(f"XGBoost 训练失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def predict(self, X_latest):
        """单步预测"""
        if not self.trained or self.model is None:
            return {'success': False, 'error': '模型未训练'}
        try:
            X_s = self.scaler.transform(X_latest.reshape(1, -1) if X_latest.ndim == 1 else X_latest)
            pred = int(self.model.predict(X_s)[0])
            proba = self.model.predict_proba(X_s)[0]
            return {
                'success': True,
                'prediction': pred,
                'signal': '买入' if pred == 1 else '卖出',
                'confidence': float(proba[pred]),
                'probability': {'下跌': float(proba[0]), '上涨': float(proba[1])}
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _build_result(self, y_test, y_pred, y_proba, X_train, X_test, model_name):
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred)
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        roc_auc = auc(fpr, tpr)

        return {
            'success': True,
            'model_type': model_name,
            'accuracy': float(acc),
            'precision': float(prec),
            'recall': float(rec),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc),
            'confusion_matrix': cm.tolist(),
            'fpr': fpr.tolist(),
            'tpr': tpr.tolist(),
            'feature_importance': self.feature_importance,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'best_params': self.best_params
        }


# ============================================================
# 2. LightGBM 预测器
# ============================================================
class LightGBMPredictor:
    """LightGBM 预测器 —— 高效的梯度提升框架"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.feature_importance = None
        self.trained = False

    @property
    def available(self):
        return LIGHTGBM_AVAILABLE

    def train(self, X, y, test_size=0.2, categorical_features=None):
        """训练 LightGBM 模型"""
        if not LIGHTGBM_AVAILABLE:
            return {'success': False, 'error': 'LightGBM 未安装，请运行 pip install lightgbm'}

        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, shuffle=False
            )

            X_train_s = self.scaler.fit_transform(X_train)
            X_test_s = self.scaler.transform(X_test)

            params = {
                'n_estimators': 200,
                'max_depth': -1,
                'num_leaves': 31,
                'learning_rate': 0.05,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42,
                'verbosity': -1,
                'force_row_wise': True
            }

            self.model = LGBMClassifier(**params)
            self.model.fit(X_train_s, y_train)

            y_pred = self.model.predict(X_test_s)
            y_proba = self.model.predict_proba(X_test_s)[:, 1]

            self.feature_importance = dict(
                sorted(zip(range(X.shape[1]), self.model.feature_importances_),
                       key=lambda x: x[1], reverse=True)
            )
            self.trained = True

            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            cm = confusion_matrix(y_test, y_pred)
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            roc_auc = auc(fpr, tpr)

            return {
                'success': True,
                'model_type': 'lightgbm',
                'accuracy': float(acc),
                'precision': float(prec),
                'recall': float(rec),
                'f1_score': float(f1),
                'roc_auc': float(roc_auc),
                'confusion_matrix': cm.tolist(),
                'fpr': fpr.tolist(),
                'tpr': tpr.tolist(),
                'feature_importance': self.feature_importance,
                'train_size': len(X_train),
                'test_size': len(X_test),
                'best_params': params
            }

        except Exception as e:
            logger.error(f"LightGBM 训练失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def predict(self, X_latest):
        """单步预测"""
        if not self.trained or self.model is None:
            return {'success': False, 'error': '模型未训练'}
        try:
            X_s = self.scaler.transform(X_latest.reshape(1, -1) if X_latest.ndim == 1 else X_latest)
            pred = int(self.model.predict(X_s)[0])
            proba = self.model.predict_proba(X_s)[0]
            return {
                'success': True,
                'prediction': pred,
                'signal': '买入' if pred == 1 else '卖出',
                'confidence': float(proba[pred]),
                'probability': {'下跌': float(proba[0]), '上涨': float(proba[1])}
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ============================================================
# 3. LSTM 预测器
# ============================================================
class LSTMPredictor:
    """LSTM 预测器 —— 深度时序序列模型"""

    def __init__(self):
        self.model = None
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.feature_names = []
        self.sequence_length = 20
        self.trained = False
        self._model_type = 'lstm'

    @property
    def available(self):
        return TENSORFLOW_AVAILABLE

    def _create_sequences(self, X, y, seq_len):
        """从时间序列创建监督学习序列"""
        X_seq, y_seq = [], []
        for i in range(seq_len, len(X)):
            X_seq.append(X[i - seq_len:i])
            y_seq.append(y[i])
        return np.array(X_seq), np.array(y_seq)

    def _create_lstm_model(self, input_shape):
        """创建 LSTM 模型"""
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=input_shape),
            Dropout(0.3),
            LSTM(32, return_sequences=False),
            Dropout(0.3),
            Dense(16, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def _create_mlp_fallback(self, input_dim):
        """使用 sklearn MLP 作为 Keras 不可用时的后备"""
        from sklearn.neural_network import MLPClassifier
        return MLPClassifier(
            hidden_layer_sizes=(64, 32, 16),
            activation='relu',
            solver='adam',
            max_iter=300,
            random_state=42
        )

    def train(self, X, y, test_size=0.2, sequence_length=20, epochs=30, batch_size=32):
        """训练 LSTM 模型"""
        if not TENSORFLOW_AVAILABLE:
            # 使用 sklearn MLP 作为后备
            return self._train_fallback(X, y, test_size)

        try:
            self.sequence_length = sequence_length

            # 创建序列
            X_seq, y_seq = self._create_sequences(X, y, sequence_length)

            if len(X_seq) < 30:
                return {'success': False, 'error': f'序列样本不足 ({len(X_seq)}), 需要至少 30 条'}

            # 分割
            split = int(len(X_seq) * (1 - test_size))
            X_train, X_test = X_seq[:split], X_seq[split:]
            y_train, y_test = y_seq[:split], y_seq[split:]

            # 标准化（保留时间序列结构）
            nsamples, nsteps, nfeatures = X_train.shape
            X_train_flat = X_train.reshape(-1, nfeatures)
            X_train_s = self.scaler_X.fit_transform(X_train_flat).reshape(nsamples, nsteps, nfeatures)

            X_test_s = self.scaler_X.transform(
                X_test.reshape(-1, nfeatures)
            ).reshape(X_test.shape[0], nsteps, nfeatures)

            # 构建模型
            self.model = self._create_lstm_model((nsteps, nfeatures))

            # 训练
            early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True, verbose=0)
            history = self.model.fit(
                X_train_s, y_train,
                validation_split=0.2,
                epochs=epochs,
                batch_size=batch_size,
                callbacks=[early_stop],
                verbose=0
            )

            # 评估
            y_proba = self.model.predict(X_test_s, verbose=0).flatten()
            y_pred = (y_proba >= 0.5).astype(int)

            self.trained = True
            self._model_type = 'lstm'

            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            cm = confusion_matrix(y_test, y_pred)
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            roc_auc = auc(fpr, tpr)

            return {
                'success': True,
                'model_type': 'lstm',
                'accuracy': float(acc),
                'precision': float(prec),
                'recall': float(rec),
                'f1_score': float(f1),
                'roc_auc': float(roc_auc),
                'confusion_matrix': cm.tolist(),
                'fpr': fpr.tolist(),
                'tpr': tpr.tolist(),
                'feature_importance': None,
                'train_size': len(X_train),
                'test_size': len(X_test),
                'model_params': {
                    'sequence_length': sequence_length,
                    'epochs': epochs,
                    'batch_size': batch_size
                }
            }

        except Exception as e:
            logger.error(f"LSTM 训练失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _train_fallback(self, X, y, test_size=0.2):
        """使用 sklearn MLP 作为后备训练"""
        logger.info("使用 sklearn MLPClassifier 作为 LSTM 后备")

        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, shuffle=False
            )

            X_train_s = self.scaler_X.fit_transform(X_train)
            X_test_s = self.scaler_X.transform(X_test)

            self.model = self._create_mlp_fallback(X_train_s.shape[1])
            self.model.fit(X_train_s, y_train)

            y_pred = self.model.predict(X_test_s)
            y_proba = self.model.predict_proba(X_test_s)[:, 1]

            self.trained = True
            self._model_type = 'lstm_mlp_fallback'

            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            cm = confusion_matrix(y_test, y_pred)
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            roc_auc = auc(fpr, tpr)

            return {
                'success': True,
                'model_type': 'lstm_mlp_fallback',
                'note': 'TensorFlow 未安装，使用 sklearn MLPClassifier 替代',
                'accuracy': float(acc),
                'precision': float(prec),
                'recall': float(rec),
                'f1_score': float(f1),
                'roc_auc': float(roc_auc),
                'confusion_matrix': cm.tolist(),
                'fpr': fpr.tolist(),
                'tpr': tpr.tolist(),
                'feature_importance': None,
                'train_size': len(X_train),
                'test_size': len(X_test),
                'model_params': {
                    'fallback': 'sklearn MLPClassifier'
                }
            }

        except Exception as e:
            logger.error(f"LSTM 后备训练失败: {str(e)}")
            return {'success': False, 'error': f'MLP后备训练失败: {str(e)}'}

    def predict(self, X_latest, sequence_length=None):
        """预测 —— 如果模型是 LSTM 则需要提供足够长度的序列"""
        if not self.trained or self.model is None:
            return {'success': False, 'error': '模型未训练'}

        try:
            seq_len = sequence_length or self.sequence_length

            if self._model_type == 'lstm':
                # LSTM 需要序列输入
                if X_latest.ndim == 1:
                    X_latest = X_latest.reshape(1, -1)
                if X_latest.shape[0] < seq_len:
                    return {'success': False,
                            'error': f'序列长度不足，需要 {seq_len} 天，当前 {X_latest.shape[0]} 天'}

                X_seq = X_latest[-seq_len:].reshape(1, seq_len, -1)
                X_s = self.scaler_X.transform(
                    X_seq.reshape(-1, X_seq.shape[-1])
                ).reshape(1, seq_len, X_seq.shape[-1])

                proba = self.model.predict(X_s, verbose=0)[0][0]
                pred = int(proba >= 0.5)
            else:
                # sklearn MLP fallback
                X_s = self.scaler_X.transform(
                    X_latest.reshape(1, -1) if X_latest.ndim == 1 else X_latest[-1:]
                )
                proba = self.model.predict_proba(X_s)[0, 1]
                pred = self.model.predict(X_s)[0]

            return {
                'success': True,
                'prediction': pred,
                'signal': '买入' if pred == 1 else '卖出',
                'confidence': float(proba if proba >= 0.5 else 1 - proba),
                'probability': {'下跌': float(1 - proba), '上涨': float(proba)}
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}


# ============================================================
# 4. 集成预测器
# ============================================================
class EnsemblePredictor:
    """集成预测器 —— 加权组合多个模型的预测"""

    SUPPORTED_MODELS = ['logistic', 'random_forest', 'xgboost', 'lightgbm', 'lstm']

    def __init__(self):
        self.models = {}
        self.weights = {}
        self.performance_history = {}
        self.scaler = StandardScaler()
        self.trained = False

    def add_model(self, name, predictor, weight=None):
        """添加模型到集成"""
        self.models[name] = predictor
        if weight is not None:
            self.weights[name] = weight

    def train_all(self, X, y, models_to_train=None, test_size=0.2):
        """训练所有子模型并计算权重"""
        if models_to_train is None:
            models_to_train = list(self.models.keys())

        results = {}
        performances = {}

        for name in models_to_train:
            if name not in self.models:
                continue

            predictor = self.models[name]
            try:
                if name == 'logistic':
                    m = LogisticRegression(max_iter=1000, random_state=42)
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)
                    X_train_s = self.scaler.fit_transform(X_train)
                    X_test_s = self.scaler.transform(X_test)
                    m.fit(X_train_s, y_train)
                    predictor.model = m
                    predictor.scaler = self.scaler
                    predictor.trained = True
                    y_pred = m.predict(X_test_s)
                    y_proba = m.predict_proba(X_test_s)[:, 1]
                    acc = accuracy_score(y_test, y_pred)
                    results[name] = {'accuracy': float(acc), 'trained': True}
                    performances[name] = acc

                elif name == 'random_forest':
                    m = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)
                    X_train_s = self.scaler.fit_transform(X_train)
                    X_test_s = self.scaler.transform(X_test)
                    m.fit(X_train_s, y_train)
                    predictor.model = m
                    predictor.scaler = self.scaler
                    predictor.trained = True
                    y_pred = m.predict(X_test_s)
                    y_proba = m.predict_proba(X_test_s)[:, 1]
                    acc = accuracy_score(y_test, y_pred)
                    results[name] = {'accuracy': float(acc), 'trained': True}
                    performances[name] = acc

                elif name in ('xgboost', 'lightgbm', 'lstm'):
                    if not getattr(predictor, 'available', False):
                        results[name] = {'trained': False, 'error': f'{name} 未安装'}
                        continue
                    r = predictor.train(X, y, test_size=test_size)
                    if r['success']:
                        performances[name] = r['accuracy']
                        results[name] = {'accuracy': r['accuracy'], 'trained': True}
                    else:
                        results[name] = {'trained': False, 'error': r.get('error', 'Unknown')}

            except Exception as e:
                logger.error(f"集成训练 {name} 失败: {str(e)}")
                results[name] = {'trained': False, 'error': str(e)}

        # 基于性能计算权重（softmax）
        if performances:
            perf_array = np.array(list(performances.values()))
            exp_perf = np.exp(perf_array - np.max(perf_array))
            weight_vals = exp_perf / exp_perf.sum()

            for i, name in enumerate(performances.keys()):
                self.weights[name] = float(weight_vals[i])
                self.performance_history[name] = float(performances[name])

        self.trained = any(
            r.get('trained', False) for r in results.values()
        )

        return {
            'success': self.trained,
            'model_results': results,
            'weights': self.weights,
            'performance_history': self.performance_history
        }

    def predict(self, X_latest):
        """加权集成预测"""
        if not self.trained:
            return {'success': False, 'error': '集成模型未训练'}

        predictions = []
        total_weight = 0.0

        for name, predictor in self.models.items():
            if not getattr(predictor, 'trained', False):
                continue
            if name not in self.weights:
                continue

            try:
                if name == 'lstm' and predictor._model_type == 'lstm':
                    r = predictor.predict(X_latest)
                else:
                    r = predictor.predict(X_latest[-1:] if X_latest.ndim > 1 else X_latest)

                if r.get('success'):
                    prob_up = r['probability']['上涨']
                    weight = self.weights[name]
                    predictions.append((prob_up, weight))
                    total_weight += weight
            except Exception as e:
                logger.warning(f"集成预测子模型 {name} 失败: {str(e)}")

        if not predictions or total_weight == 0:
            return {'success': False, 'error': '没有可用的子模型预测'}

        # 加权平均
        weighted_prob = sum(p * w for p, w in predictions) / total_weight
        pred = 1 if weighted_prob >= 0.5 else 0

        return {
            'success': True,
            'prediction': pred,
            'signal': '买入' if pred == 1 else '卖出',
            'confidence': float(weighted_prob if weighted_prob >= 0.5 else 1 - weighted_prob),
            'probability': {'下跌': float(1 - weighted_prob), '上涨': float(weighted_prob)},
            'ensemble_weights': self.weights,
            'sub_predictions': len(predictions)
        }


# ============================================================
# 5. 模型管理器 —— 统一管理所有增强模型
# ============================================================
class EnhancedModelManager:
    """统一管理增强 ML 模型的训练、预测和状态"""

    MODEL_REGISTRY = {
        'logistic': {'name': '逻辑回归', 'module': 'sklearn'},
        'random_forest': {'name': '随机森林', 'module': 'sklearn'},
        'xgboost': {'name': 'XGBoost', 'module': 'xgboost'},
        'lightgbm': {'name': 'LightGBM', 'module': 'lightgbm'},
        'lstm': {'name': 'LSTM', 'module': 'tensorflow'},
        'ensemble': {'name': '集成模型', 'module': 'ensemble'}
    }

    def __init__(self):
        self._predictors = {}
        self._status = {}
        self.ensemble = None
        self.scaler = StandardScaler()
        self.feature_engineer = FeatureEngineer()

    def _get_or_create_predictor(self, model_type):
        """延迟创建预测器"""
        if model_type == 'xgboost':
            if 'xgboost' not in self._predictors:
                self._predictors['xgboost'] = XGBoostPredictor()
            return self._predictors['xgboost']

        elif model_type == 'lightgbm':
            if 'lightgbm' not in self._predictors:
                self._predictors['lightgbm'] = LightGBMPredictor()
            return self._predictors['lightgbm']

        elif model_type == 'lstm':
            if 'lstm' not in self._predictors:
                self._predictors['lstm'] = LSTMPredictor()
            return self._predictors['lstm']

        elif model_type == 'ensemble':
            if self.ensemble is None:
                self.ensemble = EnsemblePredictor()
                # 注册子模型 —— 使用简单的 sklean 包装器
                class _SklearnWrapper:
                    def __init__(self, scaler_ref):
                        self.model = None
                        self.scaler = scaler_ref
                        self.trained = False
                    def predict(self, X):
                        X_s = self.scaler.transform(X.reshape(1, -1) if X.ndim == 1 else X)
                        proba = self.model.predict_proba(X_s)[0, 1]
                        pred = self.model.predict(X_s)[0]
                        return {
                            'success': True,
                            'prediction': int(pred),
                            'signal': '买入' if pred == 1 else '卖出',
                            'confidence': float(max(proba, 1 - proba)),
                            'probability': {'下跌': float(1 - proba), '上涨': float(proba)}
                        }

                self.ensemble.add_model('logistic', _SklearnWrapper(self.scaler))
                self.ensemble.add_model('random_forest', _SklearnWrapper(self.scaler))
                if XGBOOST_AVAILABLE:
                    self.ensemble.add_model('xgboost', XGBoostPredictor())
                if LIGHTGBM_AVAILABLE:
                    self.ensemble.add_model('lightgbm', LightGBMPredictor())
                # LSTM with MLP fallback always available
                self.ensemble.add_model('lstm', LSTMPredictor())
            return self.ensemble

        return None

    def get_available_models(self):
        """获取可用模型列表及其状态"""
        models = []
        for key, info in self.MODEL_REGISTRY.items():
            entry = {
                'type': key,
                'name': info['name'],
                'module': info['module'],
                'available': True,
                'trained': False,
                'message': ''
            }

            if key == 'xgboost' and not XGBOOST_AVAILABLE:
                entry['available'] = False
                entry['message'] = '需要安装: pip install xgboost'
            elif key == 'lightgbm' and not LIGHTGBM_AVAILABLE:
                entry['available'] = False
                entry['message'] = '需要安装: pip install lightgbm'
            elif key == 'lstm':
                if not TENSORFLOW_AVAILABLE:
                    entry['available'] = True
                    entry['message'] = '使用 sklearn MLP 后备（安装 TensorFlow 以获得更好的效果）'
                else:
                    entry['message'] = 'TensorFlow/Keras 已就绪'
            elif key == 'ensemble':
                if not (XGBOOST_AVAILABLE or LIGHTGBM_AVAILABLE):
                    entry['available'] = True
                    entry['message'] = '仅逻辑回归+随机森林可用（安装 XGBoost/LightGBM 增强效果）'

            # 检查是否已训练
            pred = self._predictors.get(key)
            if pred and getattr(pred, 'trained', False):
                entry['trained'] = True
            elif key == 'ensemble' and self.ensemble and self.ensemble.trained:
                entry['trained'] = True

            models.append(entry)
        return models

    def train(self, X, y, model_type, **kwargs):
        """训练指定类型的模型"""
        predictor = self._get_or_create_predictor(model_type)
        if predictor is None:
            return {'success': False, 'error': f'不支持的模型类型: {model_type}'}

        if model_type == 'ensemble':
            result = predictor.train_all(X, y)
            self._status[model_type] = result
            return result

        test_size = kwargs.get('test_size', 0.2)
        result = predictor.train(X, y, test_size=test_size)

        if result.get('success'):
            self._status[model_type] = result

        return result

    def predict(self, X, model_type, **kwargs):
        """使用训练好的模型预测"""
        predictor = self._get_or_create_predictor(model_type)
        if predictor is None:
            return {'success': False, 'error': f'不支持的模型类型: {model_type}'}

        if model_type == 'ensemble':
            return predictor.predict(X)

        if not getattr(predictor, 'trained', False):
            result = self.train(X, None, model_type)
            if not result.get('success'):
                return {'success': False, 'error': '模型自动训练失败'}

        return predictor.predict(X)

    def get_status(self, model_type=None):
        """获取模型状态"""
        if model_type:
            return self._status.get(model_type, {'trained': False})
        return self._status


# 全局管理器实例
enhanced_model_manager = EnhancedModelManager()
