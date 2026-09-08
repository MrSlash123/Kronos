# Kronos 本地运行指南

## 概述

这个目录用于独立运行 Kronos 金融时序预测模型，从 PostgreSQL 数据库导出数据并进行预测，不与原项目混淆。

## 环境要求

- Python 3.10+
- PostgreSQL 数据库（已配置数据）
- 足够的磁盘空间（模型文件约几十 MB）
- 网络连接（首次运行需下载模型）

## 安装步骤

### 1. 安装依赖

```bash
cd C:\Users\slash\PycharmProjects\Kronos\my_kronos
pip install -r requirements.txt
```

### 2. 配置数据库

确保 PostgreSQL 服务正常运行，并且你的数据库包含 `gp_real_bar1d` 表。

## 使用方法

### 步骤 1: 导出数据

从 PostgreSQL 导出指定股票的 K 线数据为 CSV 格式：

```bash
python db_to_csv.py --instrument 600519.SH
```

- `--instrument`: 股票代码，格式如 `600519.SH`（默认：`600519.SH`）
- 数据将保存到 `data/600519.SH_1d.csv`

### 步骤 2: 运行预测

使用 Kronos-mini 模型进行预测：

```bash
python predict.py --instrument 600519.SH
```

- `--instrument`: 股票代码，格式如 `600519.SH`（默认：`600519.SH`）
- 预测结果将保存到 `outputs/` 目录

## 输出文件

### 数据文件
- `data/{instrument}_1d.csv`: 从数据库导出的原始 K 线数据

### 预测结果
- `outputs/pred_{instrument}_data.csv`: 合并的历史+预测数据
- `outputs/pred_{instrument}_chart.png`: 收盘价对比图表

## 配置说明

所有配置参数在 `config.py` 中：

```python
# 数据库配置
DB_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/quantization"

# 模型配置
TOKENIZER_PRETRAINED = "NeoQuasar/Kronos-Tokenizer-2k"
MODEL_PRETRAINED = "NeoQuasar/Kronos-mini"
MAX_CONTEXT = 2048
LOOKBACK = 2000
PRED_LEN = 60

# 设备配置
DEVICE = "cpu"
```

## 注意事项

1. **首次运行**：会自动从 Hugging Face 下载模型文件，首次运行时间较长
2. **CPU 运行**：模型运行在 CPU 上，预测 60 天数据约需要几分钟
3. **数据要求**：股票数据至少需要 2000 条日线数据（约 8 年）
4. **内存占用**：Kronos-mini 模型内存占用约 1GB 左右

## 故障排除

- **数据库连接失败**：检查 DB_URL 是否正确，PostgreSQL 服务是否运行
- **数据不足**：确保数据库中有足够的历史数据
- **模型下载失败**：检查网络连接，或手动从 Hugging Face 下载模型
- **内存不足**：减少 LOOKBACK 值（如改为 1024）
