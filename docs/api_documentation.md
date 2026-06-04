# 股票分析与量化投资平台API文档

## 1. 概述

本API文档描述了股票分析与量化投资平台的RESTful API接口，旨在为开发者提供程序化访问平台功能的能力。API使用JWT（JSON Web Tokens）进行身份认证，支持股票数据获取、技术指标计算、策略回测等功能。

### 1.1 基础URL

```
http://localhost:5000/api
```

### 1.2 认证方式

所有API请求（除了登录和注册）都需要在请求头中包含JWT令牌：

```
Authorization: Bearer <your-jwt-token>
```

### 1.3 响应格式

所有API响应均为JSON格式，包含以下字段：

- `status`：请求状态，`success` 或 `error`
- `message`：响应消息
- `data`：响应数据（成功时返回）
- `error`：错误信息（失败时返回）

示例成功响应：

```json
{
  "status": "success",
  "message": "数据获取成功",
  "data": {
    "stock_code": "600036",
    "stock_name": "招商银行",
    "price": 35.25,
    "change": 0.5
  }
}
```

示例错误响应：

```json
{
  "status": "error",
  "message": "认证失败",
  "error": "无效的令牌"
}
```

## 2. 认证接口

### 2.1 用户登录

**接口**：`POST /api/auth/login`

**功能**：用户登录并获取JWT令牌

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**响应**：

```json
{
  "status": "success",
  "message": "登录成功",
  "data": {
    "access_token": "<jwt-token>",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true
    }
  }
}
```

### 2.2 用户注册

**接口**：`POST /api/auth/register`

**功能**：注册新用户

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| username | string | 是 | 用户名（3-20个字符） |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码（至少8位，包含大小写字母和数字） |

**响应**：

```json
{
  "status": "success",
  "message": "注册成功",
  "data": {
    "id": 2,
    "username": "user1",
    "email": "user1@example.com"
  }
}
```

### 2.3 刷新令牌

**接口**：`POST /api/auth/refresh`

**功能**：刷新JWT令牌

**参数**：无

**响应**：

```json
{
  "status": "success",
  "message": "令牌刷新成功",
  "data": {
    "access_token": "<new-jwt-token>",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

## 3. 股票数据接口

### 3.1 市场概览

**接口**：`GET /api/data/market`

**功能**：获取市场概览数据

**参数**：无

**响应**：

```json
{
  "status": "success",
  "message": "市场概览获取成功",
  "data": {
    "indexes": [
      {
        "code": "000001.SH",
        "name": "上证指数",
        "price": 3500.25,
        "change": 0.85,
        "change_pct": 0.0246
      },
      {
        "code": "399001.SZ",
        "name": "深证成指",
        "price": 14500.75,
        "change": -0.25,
        "change_pct": -0.0017
      }
    ],
    "market_stats": {
      "up_count": 1850,
      "down_count": 1200,
      "flat_count": 350,
      "total_count": 3400
    }
  }
}
```

### 3.2 股票列表

**接口**：`GET /api/data/stocks`

**功能**：获取股票列表

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| per_page | integer | 否 | 每页数量（默认20） |
| industry | string | 否 | 行业代码 |
| market | string | 否 | 市场类型（sh/sz） |

**响应**：

```json
{
  "status": "success",
  "message": "股票列表获取成功",
  "data": {
    "stocks": [
      {
        "code": "600036",
        "name": "招商银行",
        "industry": "银行",
        "market": "sh",
        "price": 35.25,
        "change": 0.5,
        "change_pct": 0.0144
      },
      {
        "code": "000001",
        "name": "平安银行",
        "industry": "银行",
        "market": "sz",
        "price": 18.75,
        "change": -0.25,
        "change_pct": -0.0132
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 3400,
      "pages": 170
    }
  }
}
```

### 3.3 股票详情

**接口**：`GET /api/data/stock/{code}`

**功能**：获取股票详细信息

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| code | string | 是 | 股票代码 |

**响应**：

```json
{
  "status": "success",
  "message": "股票详情获取成功",
  "data": {
    "code": "600036",
    "name": "招商银行",
    "industry": "银行",
    "market": "sh",
    "price": 35.25,
    "open": 34.80,
    "high": 35.30,
    "low": 34.70,
    "prev_close": 34.75,
    "volume": 12500000,
    "amount": 440625000,
    "change": 0.5,
    "change_pct": 0.0144,
    "pe": 6.5,
    "pb": 0.8,
    "market_cap": 950000000000
  }
}
```

### 3.4 历史数据

**接口**：`GET /api/data/history/{code}`

**功能**：获取股票历史数据

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| code | string | 是 | 股票代码 |
| start_date | string | 否 | 开始日期（YYYY-MM-DD） |
| end_date | string | 否 | 结束日期（YYYY-MM-DD） |
| frequency | string | 否 | 频率（daily/weekly/monthly） |

**响应**：

```json
{
  "status": "success",
  "message": "历史数据获取成功",
  "data": {
    "code": "600036",
    "name": "招商银行",
    "history": [
      {
        "date": "2026-02-05",
        "open": 34.80,
        "high": 35.30,
        "low": 34.70,
        "close": 35.25,
        "volume": 12500000,
        "amount": 440625000
      },
      {
        "date": "2026-02-04",
        "open": 34.50,
        "high": 34.90,
        "low": 34.40,
        "close": 34.75,
        "volume": 10200000,
        "amount": 354450000
      }
    ]
  }
}
```

## 4. 技术分析接口

### 4.1 技术指标计算

**接口**：`POST /api/analysis/indicators`

**功能**：计算股票技术指标

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| stock_code | string | 是 | 股票代码 |
| indicators | array | 是 | 要计算的指标列表 |
| params | object | 否 | 指标参数 |
| start_date | string | 否 | 开始日期（YYYY-MM-DD） |
| end_date | string | 否 | 结束日期（YYYY-MM-DD） |

**示例请求**：

```json
{
  "stock_code": "600036",
  "indicators": ["MA", "MACD", "RSI"],
  "params": {
    "MA": {"periods": [10, 30]},
    "RSI": {"period": 14}
  },
  "start_date": "2026-01-01",
  "end_date": "2026-02-05"
}
```

**响应**：

```json
{
  "status": "success",
  "message": "技术指标计算成功",
  "data": {
    "stock_code": "600036",
    "indicators": {
      "MA": {
        "MA10": [34.5, 34.7, 34.9, 35.1, 35.2],
        "MA30": [34.2, 34.3, 34.4, 34.5, 34.6]
      },
      "MACD": {
        "MACD": [0.1, 0.15, 0.2, 0.25, 0.3],
        "Signal": [0.08, 0.12, 0.16, 0.2, 0.24],
        "Histogram": [0.02, 0.03, 0.04, 0.05, 0.06]
      },
      "RSI": [55, 58, 62, 65, 68]
    }
  }
}
```

### 4.2 相关性分析

**接口**：`POST /api/analysis/correlation`

**功能**：分析多只股票之间的相关性

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| stock_codes | array | 是 | 股票代码列表 |
| start_date | string | 否 | 开始日期（YYYY-MM-DD） |
| end_date | string | 否 | 结束日期（YYYY-MM-DD） |

**示例请求**：

```json
{
  "stock_codes": ["600036", "000001", "601318"],
  "start_date": "2026-01-01",
  "end_date": "2026-02-05"
}
```

**响应**：

```json
{
  "status": "success",
  "message": "相关性分析成功",
  "data": {
    "correlation_matrix": [
      [1.0, 0.85, 0.72],
      [0.85, 1.0, 0.68],
      [0.72, 0.68, 1.0]
    ],
    "stock_codes": ["600036", "000001", "601318"]
  }
}
```

## 5. 回测接口

### 5.1 策略回测

**接口**：`POST /api/backtest/run`

**功能**：运行策略回测

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| strategy | string | 是 | 策略名称（ma_cross/macd/rsi/bollinger/kdj/cci/mean_reversion/momentum） |
| stock_code | string | 是 | 股票代码 |
| params | object | 否 | 策略参数 |
| initial_capital | number | 否 | 初始资金（默认1000000） |
| start_date | string | 否 | 开始日期（YYYY-MM-DD） |
| end_date | string | 否 | 结束日期（YYYY-MM-DD） |
| fee_rate | number | 否 | 手续费率（默认0.0003） |

**示例请求**：

```json
{
  "strategy": "ma_cross",
  "stock_code": "600036",
  "params": {
    "short_period": 10,
    "long_period": 30
  },
  "initial_capital": 1000000,
  "start_date": "2025-01-01",
  "end_date": "2026-02-05",
  "fee_rate": 0.0003
}
```

**响应**：

```json
{
  "status": "success",
  "message": "回测完成",
  "data": {
    "strategy": "ma_cross",
    "stock_code": "600036",
    "params": {
      "short_period": 10,
      "long_period": 30
    },
    "performance": {
      "total_return": 0.156,
      "annual_return": 0.098,
      "max_drawdown": 0.085,
      "sharpe_ratio": 1.2,
      "winning_rate": 0.65,
      "total_trades": 25,
      "avg_win": 0.032,
      "avg_loss": 0.018
    },
    "trades": [
      {
        "date": "2025-02-01",
        "type": "buy",
        "price": 32.5,
        "quantity": 30769,
        "amount": 1000000
      },
      {
        "date": "2025-03-15",
        "type": "sell",
        "price": 34.2,
        "quantity": 30769,
        "amount": 1052300
      }
    ]
  }
}
```

### 5.2 回测历史

**接口**：`GET /api/backtest/history`

**功能**：获取回测历史记录

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| per_page | integer | 否 | 每页数量（默认10） |

**响应**：

```json
{
  "status": "success",
  "message": "回测历史获取成功",
  "data": {
    "backtests": [
      {
        "id": 1,
        "strategy": "ma_cross",
        "stock_code": "600036",
        "total_return": 0.156,
        "max_drawdown": 0.085,
        "sharpe_ratio": 1.2,
        "created_at": "2026-02-05T10:30:00"
      },
      {
        "id": 2,
        "strategy": "rsi",
        "stock_code": "000001",
        "total_return": 0.123,
        "max_drawdown": 0.102,
        "sharpe_ratio": 1.0,
        "created_at": "2026-02-05T09:15:00"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 50,
      "pages": 5
    }
  }
}
```

## 6. 金融模型接口

### 6.1 Markowitz投资组合优化

**接口**：`POST /api/models/markowitz`

**功能**：Markowitz投资组合优化

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| stock_codes | array | 是 | 股票代码列表 |
| start_date | string | 否 | 开始日期（YYYY-MM-DD） |
| end_date | string | 否 | 结束日期（YYYY-MM-DD） |
| risk_free_rate | number | 否 | 无风险利率（默认0.03） |

**示例请求**：

```json
{
  "stock_codes": ["600036", "000001", "601318", "600519"],
  "start_date": "2025-01-01",
  "end_date": "2026-02-05",
  "risk_free_rate": 0.03
}
```

**响应**：

```json
{
  "status": "success",
  "message": "投资组合优化成功",
  "data": {
    "stock_codes": ["600036", "000001", "601318", "600519"],
    "optimal_weights": [0.25, 0.2, 0.3, 0.25],
    "portfolio_stats": {
      "expected_return": 0.12,
      "volatility": 0.15,
      "sharpe_ratio": 0.6,
      "max_drawdown": 0.1
    },
    "efficient_frontier": [
      {"return": 0.08, "volatility": 0.12},
      {"return": 0.10, "volatility": 0.13},
      {"return": 0.12, "volatility": 0.15},
      {"return": 0.14, "volatility": 0.18},
      {"return": 0.16, "volatility": 0.22}
    ]
  }
}
```

### 6.2 Black-Scholes期权定价

**接口**：`POST /api/models/black-scholes`

**功能**：Black-Scholes期权定价模型

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| s | number | 是 | 标的资产价格 |
| k | number | 是 | 执行价格 |
| t | number | 是 | 到期时间（年） |
| r | number | 是 | 无风险利率 |
| sigma | number | 是 | 波动率 |
| option_type | string | 否 | 期权类型（call/put，默认call） |

**示例请求**：

```json
{
  "s": 100,
  "k": 100,
  "t": 1,
  "r": 0.05,
  "sigma": 0.2,
  "option_type": "call"
}
```

**响应**：

```json
{
  "status": "success",
  "message": "期权定价计算成功",
  "data": {
    "option_price": 10.45,
    "greeks": {
      "delta": 0.6368,
      "gamma": 0.0189,
      "theta": -0.0285,
      "vega": 0.3853,
      "rho": 0.4308
    },
    "params": {
      "s": 100,
      "k": 100,
      "t": 1,
      "r": 0.05,
      "sigma": 0.2,
      "option_type": "call"
    }
  }
}
```

### 6.3 债券定价模型

**接口**：`POST /api/models/bond-pricing`

**功能**：债券定价、久期和凸性计算

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| face_value | number | 是 | 面值 |
| coupon_rate | number | 是 | 票面利率 |
| years_to_maturity | number | 是 | 到期年限 |
| yield_to_maturity | number | 是 | 到期收益率 |
| compounding_frequency | number | 否 | 复利频率（默认2） |
| bond_type | string | 否 | 债券类型（coupon/zero，默认coupon） |

**示例请求**：

```json
{
  "face_value": 1000,
  "coupon_rate": 0.05,
  "years_to_maturity": 5,
  "yield_to_maturity": 0.04,
  "compounding_frequency": 2,
  "bond_type": "coupon"
}
```

**响应**：

```json
{
  "status": "success",
  "message": "债券定价计算成功",
  "data": {
    "price": 1044.91,
    "macaulay_duration": 4.54,
    "modified_duration": 4.45,
    "convexity": 22.65,
    "params": {
      "face_value": 1000,
      "coupon_rate": 0.05,
      "years_to_maturity": 5,
      "yield_to_maturity": 0.04,
      "compounding_frequency": 2,
      "bond_type": "coupon"
    }
  }
}
```

### 6.4 风险价值(VaR)计算

**接口**：`POST /api/models/risk`

**功能**：计算投资组合风险价值及其他风险指标

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| returns | array | 是 | 收益率数据列表 |
| confidence_level | number | 否 | 置信水平（默认0.95） |
| time_horizon | number | 否 | 时间 horizon（默认1） |
| method | string | 否 | 计算方法（historical/parametric/monte_carlo，默认historical） |
| risk_free_rate | number | 否 | 无风险利率（默认0.03） |
| target_return | number | 否 | 目标收益率（默认0） |

**示例请求**：

```json
{
  "returns": [0.01, -0.005, 0.008, -0.012, 0.006, 0.015, -0.009, 0.007, -0.011, 0.013],
  "confidence_level": 0.95,
  "time_horizon": 1,
  "method": "historical",
  "risk_free_rate": 0.03,
  "target_return": 0.005
}
```

**响应**：

```json
{
  "status": "success",
  "message": "风险指标计算成功",
  "data": {
    "var": 0.011,
    "cvar": 0.012,
    "downside_risk": 0.009,
    "sortino_ratio": 0.333,
    "sharpe_ratio": 0.286,
    "max_drawdown": 0.012,
    "kurtosis": 2.8,
    "skewness": -0.15,
    "confidence_level": 0.95,
    "time_horizon": 1,
    "method": "historical"
  }
}
```

### 6.5 时间序列预测模型

#### 6.5.1 ARIMA模型

**接口**：`POST /api/models/forecasting/arima`

**功能**：使用ARIMA模型进行时间序列预测

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| data | array | 是 | 时间序列数据 |
| forecast_steps | number | 否 | 预测步数（默认5） |
| order | array | 否 | ARIMA模型阶数(p, d, q)，默认自动选择 |

**示例请求**：

```json
{
  "data": [100, 102, 105, 103, 106, 108, 110, 109, 112, 114, 113, 115],
  "forecast_steps": 5,
  "order": [1, 1, 1]
}
```

**响应**：

```json
{
  "status": "success",
  "message": "ARIMA预测成功",
  "data": {
    "order": [1, 1, 1],
    "forecast": [116.5, 117.2, 118.0, 118.7, 119.5],
    "forecast_steps": 5,
    "confidence_interval": 1.2,
    "aic": 50.2,
    "bic": 52.8,
    "stationarity": {
      "adf_statistic": -3.5,
      "p_value": 0.01,
      "is_stationary": true
    },
    "acf_pacf_plot": "data:image/png;base64,..."
  }
}
```

#### 6.5.2 GARCH模型

**接口**：`POST /api/models/forecasting/garch`

**功能**：使用GARCH模型进行波动率预测

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| returns | array | 是 | 收益率数据 |
| forecast_steps | number | 否 | 预测步数（默认5） |
| params | array | 否 | GARCH模型阶数(p, q)，默认自动选择 |
| data | array | 否 | 原始价格数据（用于绘图） |

**示例请求**：

```json
{
  "returns": [0.01, -0.005, 0.008, -0.012, 0.006, 0.015, -0.009, 0.007, -0.011, 0.013],
  "forecast_steps": 5,
  "params": [1, 1]
}
```

**响应**：

```json
{
  "status": "success",
  "message": "GARCH波动率预测成功",
  "data": {
    "params": [1, 1],
    "volatility_forecast": [0.011, 0.010, 0.009, 0.009, 0.008],
    "forecast_steps": 5,
    "aic": 45.6,
    "bic": 48.2,
    "volatility_plot": "data:image/png;base64,..."
  }
}
```

## 7. 用户接口

### 7.1 用户信息

**接口**：`GET /api/user/profile`

**功能**：获取当前用户信息

**参数**：无

**响应**：

```json
{
  "status": "success",
  "message": "用户信息获取成功",
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true,
    "created_at": "2026-01-01T00:00:00",
    "last_login": "2026-02-05T10:00:00"
  }
}
```

### 7.2 更新用户信息

**接口**：`PUT /api/user/profile`

**功能**：更新用户信息

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| email | string | 否 | 邮箱地址 |
| password | string | 否 | 新密码（至少8位，包含大小写字母和数字） |
| confirm_password | string | 否 | 确认新密码 |

**示例请求**：

```json
{
  "email": "newemail@example.com"
}
```

**响应**：

```json
{
  "status": "success",
  "message": "用户信息更新成功",
  "data": {
    "id": 1,
    "username": "admin",
    "email": "newemail@example.com",
    "role": "admin",
    "is_active": true
  }
}
```

### 7.3 管理员用户列表

**接口**：`GET /api/admin/users`

**功能**：获取所有用户列表（仅管理员可用）

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| per_page | integer | 否 | 每页数量（默认20） |

**响应**：

```json
{
  "status": "success",
  "message": "用户列表获取成功",
  "data": {
    "users": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "is_active": true,
        "created_at": "2026-01-01T00:00:00",
        "last_login": "2026-02-05T10:00:00"
      },
      {
        "id": 2,
        "username": "user1",
        "email": "user1@example.com",
        "role": "user",
        "is_active": true,
        "created_at": "2026-01-02T00:00:00",
        "last_login": "2026-02-04T15:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 50,
      "pages": 3
    }
  }
}
```

### 7.4 管理员编辑用户

**接口**：`PUT /api/admin/users/{id}`

**功能**：编辑用户信息（仅管理员可用）

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| email | string | 否 | 邮箱地址 |
| role | string | 否 | 角色（user/admin） |
| is_active | boolean | 否 | 账户状态 |

**示例请求**：

```json
{
  "email": "newemail@example.com",
  "role": "admin",
  "is_active": true
}
```

**响应**：

```json
{
  "status": "success",
  "message": "用户信息更新成功",
  "data": {
    "id": 2,
    "username": "user1",
    "email": "newemail@example.com",
    "role": "admin",
    "is_active": true
  }
}
```

### 7.5 管理员删除用户

**接口**：`DELETE /api/admin/users/{id}`

**功能**：删除用户账户（仅管理员可用）

**参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| id | integer | 是 | 用户ID |

**响应**：

```json
{
  "status": "success",
  "message": "用户删除成功",
  "data": {
    "user_id": 2,
    "username": "user1"
  }
}
```

## 8. 错误码

| 错误码 | 描述 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 认证失败，无效的令牌 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 9. 速率限制

为保护API服务，平台对API请求实施速率限制：

- 普通用户：每分钟60次请求
- 管理员用户：每分钟120次请求

超出限制的请求会返回429状态码。

## 10. 最佳实践

1. **令牌管理**：使用安全的方式存储JWT令牌，避免在客户端代码中硬编码。

2. **错误处理**：正确处理API返回的错误信息，为用户提供友好的错误提示。

3. **请求优化**：合理批量获取数据，避免频繁调用API。

4. **安全性**：不要在API请求中包含敏感信息，如密码等。

5. **版本控制**：API可能会在未来进行版本更新，请关注平台公告。

## 11. 联系支持

如果您在使用API过程中遇到任何问题，请通过以下方式联系我们：

- **邮箱**：api-support@quant-platform.com
- **文档**：https://quant-platform.com/docs/api
- **社区**：https://quant-platform.com/community

---

© 2026 股票分析与量化投资平台. 保留所有权利.