#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从PostgreSQL数据库导出K线数据为CSV格式
"""

import argparse
import pandas as pd
from sqlalchemy import create_engine
from config import DB_URL, TABLE_NAME, DEFAULT_INSTRUMENT

def export_data(instrument: str):
    """导出指定股票的K线数据"""
    print(f"📥 正在导出 {instrument} 的日线数据...")

    # 安全验证：表名只能是允许的特定值
    allowed_tables = {"gp_real_bar1d", "gp_real_bar1min"}
    if TABLE_NAME not in allowed_tables:
        raise ValueError(f"不允许使用表名: {TABLE_NAME}")

    # 创建数据库连接
    engine = create_engine(DB_URL)

    # 查询数据（使用psycopg2的%s格式参数绑定）
    query = f"""
        SELECT date, open, high, low, close, volume, amount, deal_number, change_ratio, turn
        FROM {TABLE_NAME}
        WHERE instrument = %s
        ORDER BY date
    """

    df = pd.read_sql(query, engine, params=(instrument,))

    if df.empty:
        print(f"❌ 未找到 {instrument} 的数据")
        return

    print(f"✅ 找到 {len(df)} 条数据，时间范围: {df['date'].min()} ~ {df['date'].max()}")

    # 重命名列并转换格式
    df.rename(columns={
        "date": "timestamps",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "amount": "amount"
    }, inplace=True)

    # 转换时间格式
    df["timestamps"] = pd.to_datetime(df["timestamps"])

    # 按时间排序
    df = df.sort_values("timestamps").reset_index(drop=True)

    # 选择需要的列
    df = df[["timestamps", "open", "high", "low", "close", "volume", "amount"]]

    # 保存为CSV
    output_file = f"data/{instrument}_1d.csv"
    df.to_csv(output_file, index=False)

    print(f"✅ 数据已保存到: {output_file}")
    print(f"   列名: timestamps, open, high, low, close, volume, amount")
    print(f"   数据量: {len(df)} 条")

    return df

def main():
    parser = argparse.ArgumentParser(description="从PostgreSQL导出K线数据为CSV")
    parser.add_argument("--instrument", type=str, default=DEFAULT_INSTRUMENT,
                       help=f"股票代码，默认: {DEFAULT_INSTRUMENT}")
    args = parser.parse_args()

    export_data(args.instrument)

if __name__ == "__main__":
    main()
