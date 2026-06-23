"""报告加载器：读取、清洗、合并三份亚马逊广告报告"""
import pandas as pd
import os
from pathlib import Path
from datetime import datetime, timedelta

COLUMN_MAP = {
    "广告活动名称": "campaign_name",
    "广告组合名称": "portfolio_name",
    "广告组名称": "ad_group_name",
    "客户搜索词": "search_term",
    "Customer Search Term": "search_term",
    "匹配类型": "match_type",
    "投放": "targeting",
    "Targeting": "targeting",
    "展示量": "impressions",
    "点击量": "clicks",
    "点击率 (CTR)": "ctr",
    "点击率": "ctr",
    "单次点击成本 (CPC)": "cpc",
    "花费": "cost",
    "7天总销售额": "sales",
    "销售额": "sales",
    "广告投入产出比 (ACOS) 总计": "acos",
    "ACoS": "acos",
    "7天总订单数(#)": "orders",
    "订单数": "orders",
    "7天的转化率": "conv_rate",
    "转化率": "conv_rate",
    "日期": "date",
    "Status": "status",
    "状态": "status",
    "广告 ASIN": "asin",
    "ASIN": "asin",
    "放置": "placement",
    "Placement": "placement",
}

def load_report(path):
    """加载单个报告文件"""
    ext = os.path.splitext(path)[1].lower()
    if ext in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    elif ext == ".csv":
        df = pd.read_csv(path)
    else:
        return None
    
    df.columns = df.columns.str.strip()
    col_map = {c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP}
    df.rename(columns=col_map, inplace=True)
    
    # 确保列名唯一
    df = df.loc[:, ~df.columns.duplicated()]
    
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    num_cols = ["clicks", "cost", "orders", "sales", "impressions", "ctr", "acos", "cpc", "conv_rate"]
    for c in num_cols:
        if c not in df.columns:
            df[c] = 0.0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    
    # 计算派生指标
    if "acos" in df.columns and "sales" in df.columns:
        mask = (df["sales"] > 0) & (df["cost"] > 0)
        df.loc[mask, "acos"] = (df["cost"] / df["sales"]).fillna(0)
    
    if "ctr" in df.columns and "impressions" in df.columns and "clicks" in df.columns:
        mask = df["impressions"] > 0
        df.loc[mask, "ctr"] = (df["clicks"] / df["impressions"]).fillna(0)
    
    if "conv_rate" in df.columns and "clicks" in df.columns and "orders" in df.columns:
        mask = df["clicks"] > 0
        df.loc[mask, "conv_rate"] = (df["orders"] / df["clicks"]).fillna(0)
        
    return df

def load_and_merge(report_dir):
    """加载并合并所有报告"""
    path = Path(report_dir)
    if not path.exists():
        raise FileNotFoundError(f"报告目录不存在：{path}")
    
    search_df = None
    prod_df = None
    place_df = None
    search_file_name = None
    
    for f in path.glob("*"):
        if f.is_file():
            try:
                df = load_report(str(f))
                if df is None:
                    continue
                
                if "search_term" in df.columns:
                    print(f"   📂 [搜索词报告] {f.name}")
                    search_file_name = f.name
                    search_df = df if search_df is None else pd.concat([search_df, df])
                elif "asin" in df.columns or "status" in df.columns:
                    print(f"   📂 [推广商品报告] {f.name}")
                    prod_df = df if prod_df is None else pd.concat([prod_df, df])
                elif "placement" in df.columns:
                    print(f"   📂 [广告位报告] {f.name}")
                    place_df = df if place_df is None else pd.concat([place_df, df])
            except Exception as e:
                print(f"   ⚠️  跳过文件 {f.name}：{e}")
    
    return search_df, prod_df, place_df, search_file_name
