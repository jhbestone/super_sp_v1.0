"""趋势引擎：计算近 7 天与前 23 天的对比，识别趋势偏差"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_trends(df):
    """计算 30 天窗口内的趋势数据"""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().all():
        raise ValueError("未找到有效日期列！")
        
    max_date = df["date"].max()
    cutoff_recent = max_date - timedelta(days=7)
    cutoff_all = max_date - timedelta(days=30)
    
    is_recent = (df["date"] > cutoff_recent) & (df["date"] <= max_date)
    is_all = (df["date"] > cutoff_all) & (df["date"] <= max_date)
    
    print(f"   📅 分析窗口：{cutoff_all.date()} ~ {max_date.date()}")
    print(f"   📅 近 7 天：{cutoff_recent.date()} ~ {max_date.date()}")
    
    group_cols = ["search_term", "campaign_name", "ad_group_name"]
    exist_cols = [c for c in group_cols if c in df.columns]
    
    agg_map = {
        "clicks": "sum", "cost": "sum", "orders": "sum", "sales": "sum", 
        "impressions": "sum", "ctr": "mean", "conv_rate": "mean", "acos": "mean"
    }
    valid_agg = {k: v for k, v in agg_map.items() if k in df.columns}
    
    recent_agg = df[is_recent].groupby(exist_cols).agg(valid_agg).reset_index()
    all_agg = df[is_all].groupby(exist_cols).agg(valid_agg).reset_index()
    
    trends = pd.merge(recent_agg, all_agg, on=exist_cols, how="outer", suffixes=("_recent_7d", "_all"))
    
    for metric in ["clicks", "cost", "orders", "sales", "impressions"]:
        r_col = f"{metric}_recent_7d"
        a_col = f"{metric}_all"
        if r_col in trends.columns and a_col in trends.columns:
            trends[f"{metric}_all"] = trends[a_col].fillna(0)
            trends[f"{metric}_recent_7d"] = trends[r_col].fillna(0)
            
            # 计算趋势偏差：(近 7 天实际 - 近 7 天预期) / 近 7 天预期
            denom = trends[f"{metric}_all"] / 30.0 * 7.0
            trends[f"{metric}_trend_dev"] = np.where(
                denom > 0,
                (trends[f"{metric}_recent_7d"] - denom) / denom,
                np.where(trends[f"{metric}_recent_7d"] > 0, 1.0, 0.0)
            )
            
    if "conv_rate_trend_dev" not in trends.columns:
        trends["conv_rate_trend_dev"] = 0.0
    if "acos_trend_dev" not in trends.columns:
        trends["acos_trend_dev"] = 0.0
        
    trends.fillna(0, inplace=True)
    return trends

def merge_trends_to_df(df, trends):
    """将趋势数据合并回主 DataFrame"""
    merge_cols = [c for c in ["search_term", "campaign_name", "ad_group_name"] 
                  if c in df.columns and c in trends.columns]
    if len(merge_cols) >= 1:
        df = pd.merge(df, trends, on=merge_cols, how="left", suffixes=("", "_trend"))
    return df
