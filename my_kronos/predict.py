#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Kronos-mini进行K线预测（CPU版本）
"""

import argparse
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from config import (
    TOKENIZER_PRETRAINED, MODEL_PRETRAINED, MAX_CONTEXT,
    LOOKBACK, PRED_LEN, T, top_p, sample_count, DEVICE,
    PRICE_LIMIT, DEFAULT_INSTRUMENT
)

# 添加原项目路径以便导入model模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model import Kronos, KronosTokenizer, KronosPredictor

def apply_price_limits(pred_df, last_close, limit_rate=0.1):
    """应用涨跌停限制"""
    print(f"🔒 应用 ±{limit_rate*100:.0f}% 涨跌停限制...")

    pred_df = pred_df.reset_index(drop=True)
    cols = ["open", "high", "low", "close"]
    pred_df[cols] = pred_df[cols].astype("float64")

    for i in range(len(pred_df)):
        limit_up = last_close * (1 + limit_rate)
        limit_down = last_close * (1 - limit_rate)

        for col in cols:
            value = pred_df.at[i, col]
            if pd.notna(value):
                clipped = max(min(value, limit_up), limit_down)
                pred_df.at[i, col] = float(clipped)

        last_close = float(pred_df.at[i, "close"])

    return pred_df

def plot_result(df_hist, df_pred, instrument, save_dir):
    """绘制历史和预测价格对比图（全量）"""
    plt.figure(figsize=(12, 6))
    plt.plot(df_hist["timestamps"], df_hist["close"], label="历史收盘价", color="blue")
    plt.plot(df_pred["timestamps"], df_pred["close"], label="预测收盘价", color="red", linestyle="--")
    plt.title(f"Kronos-mini 预测结果 - {instrument}")
    plt.xlabel("日期")
    plt.ylabel("收盘价")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plot_path = os.path.join(save_dir, f"pred_{instrument.replace('.', '_')}_chart.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"📊 全量图表已保存: {plot_path}")


def plot_result_zoom(df_hist, df_pred, instrument, save_dir, zoom_days=60):
    """绘制最近N天历史 + 预测的局部放大图"""
    df_hist_zoom = df_hist.tail(zoom_days).copy()

    plt.figure(figsize=(12, 6))
    plt.plot(df_hist_zoom["timestamps"], df_hist_zoom["close"], label="历史收盘价", color="blue", marker="o", markersize=3)
    plt.plot(df_pred["timestamps"], df_pred["close"], label="预测收盘价", color="red", linestyle="--", marker="s", markersize=3)

    last_hist_date = df_hist["timestamps"].iloc[-1]
    last_hist_close = df_hist["close"].iloc[-1]
    first_pred_date = df_pred["timestamps"].iloc[0]
    first_pred_close = df_pred["close"].iloc[0]
    plt.plot([last_hist_date, first_pred_date], [last_hist_close, first_pred_close],
             color="red", linestyle="--", linewidth=1, alpha=0.6)

    plt.title(f"Kronos-mini 预测结果（最近{zoom_days}天放大）- {instrument}")
    plt.xlabel("日期")
    plt.ylabel("收盘价")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plot_path = os.path.join(save_dir, f"pred_{instrument.replace('.', '_')}_chart_zoom.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"📊 局部放大图表已保存: {plot_path}")

def predict(instrument: str):
    """执行预测流程"""
    save_dir = "outputs"
    os.makedirs(save_dir, exist_ok=True)

    # 加载模型
    print(f"🚀 加载模型: Tokenizer={TOKENIZER_PRETRAINED}, Model={MODEL_PRETRAINED}")
    print(f"   设备: {DEVICE}, 最大上下文: {MAX_CONTEXT}")

    tokenizer = KronosTokenizer.from_pretrained(TOKENIZER_PRETRAINED)
    model = Kronos.from_pretrained(MODEL_PRETRAINED)
    predictor = KronosPredictor(model, tokenizer, device=DEVICE, max_context=MAX_CONTEXT)

    # 加载数据
    data_file = f"data/{instrument}_1d.csv"
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        print("请先运行 db_to_csv.py 导出数据")
        return

    print(f"📂 加载数据: {data_file}")
    df = pd.read_csv(data_file)
    df["timestamps"] = pd.to_datetime(df["timestamps"])
    df = df.sort_values("timestamps").reset_index(drop=True)

    if len(df) < LOOKBACK:
        print(f"❌ 数据不足: 需要至少 {LOOKBACK} 条，实际 {len(df)} 条")
        return

    # 准备输入数据
    print(f"📊 准备输入数据: 最近 {LOOKBACK} 条历史数据")
    x_df = df.iloc[-LOOKBACK:][["open", "high", "low", "close", "volume", "amount"]]
    x_timestamp = df.iloc[-LOOKBACK:]["timestamps"]

    # 生成未来时间戳（转为Series，与模型要求一致）
    last_date = df["timestamps"].iloc[-1]
    y_timestamp = pd.Series(pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=PRED_LEN))
    print(f"⏰ 预测时间范围: {y_timestamp.iloc[0]} ~ {y_timestamp.iloc[-1]}")

    # 执行预测
    print(f"🔮 开始预测，预测长度: {PRED_LEN}...")
    pred_df = predictor.predict(
        df=x_df,
        x_timestamp=x_timestamp,
        y_timestamp=y_timestamp,
        pred_len=PRED_LEN,
        T=T,
        top_p=top_p,
        sample_count=sample_count,
        verbose=True
    )

    pred_df["timestamps"] = y_timestamp.values

    # 应用涨跌停限制
    if PRICE_LIMIT > 0:
        last_close = df["close"].iloc[-1]
        pred_df = apply_price_limits(pred_df, last_close, PRICE_LIMIT)

    # 合并历史和预测数据
    df_out = pd.concat([
        df[["timestamps", "open", "high", "low", "close", "volume", "amount"]],
        pred_df[["timestamps", "open", "high", "low", "close", "volume", "amount"]]
    ]).reset_index(drop=True)

    # 保存预测结果
    out_file = os.path.join(save_dir, f"pred_{instrument.replace('.', '_')}_data.csv")
    df_out.to_csv(out_file, index=False)
    print(f"✅ 预测结果已保存: {out_file}")
    print(f"   总数据量: {len(df_out)} 条（历史 {len(df)} + 预测 {len(pred_df)}）")

    # 绘制全量对比图
    plot_result(df, pred_df, instrument, save_dir)

    # 绘制最近60天局部放大图
    plot_result_zoom(df, pred_df, instrument, save_dir, zoom_days=60)

    print("\n🎉 预测完成！")
    print(f"   历史数据: {len(df)} 条")
    print(f"   预测数据: {len(pred_df)} 条")
    print(f"   输出目录: {save_dir}")

def main():
    parser = argparse.ArgumentParser(description="Kronos-mini 股票预测（CPU版本）")
    parser.add_argument("--instrument", type=str, default=DEFAULT_INSTRUMENT,
                       help=f"股票代码，默认: {DEFAULT_INSTRUMENT}")
    args = parser.parse_args()

    predict(args.instrument)

if __name__ == "__main__":
    main()
