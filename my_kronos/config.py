# -*- coding: utf-8 -*-
"""
配置文件 - Kronos 本地运行配置
"""

# 数据库配置
DB_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/quantization"
TABLE_NAME = "gp_real_bar1d"

# 模型配置
TOKENIZER_PRETRAINED = "NeoQuasar/Kronos-Tokenizer-2k"
MODEL_PRETRAINED = "NeoQuasar/Kronos-mini"
MAX_CONTEXT = 2048  # Kronos-mini 的最大上下文长度
LOOKBACK = 2000    # 使用最近2000条历史数据（不超过2048）
PRED_LEN = 60      # 预测未来60个交易日（约3个月）

# 采样参数
T = 1.0             # 温度系数
top_p = 0.9        # 核采样概率
sample_count = 1   # 预测路径数量

# 设备配置
DEVICE = "cpu"      # 强制使用CPU

# 涨跌停限制（A股）
PRICE_LIMIT = 0.1   # ±10%

# 默认测试标的
DEFAULT_INSTRUMENT = "600519.SH"  # 贵州茅台
