"""状态核查器"""
import pandas as pd

def audit_status(df):
    """核查广告对象的状态（暂停/归档等）"""
    df = df.copy()
    df["status_flag"] = ""
    df["status_reason"] = ""
    
    if "status" in df.columns:
        df["status_clean"] = df["status"].astype(str).str.lower().str.strip()
        
        paused = df["status_clean"].isin(["paused", "已暂停", "pause"])
        df.loc[paused, "status_flag"] = "⚠️ [已暂停]"
        df.loc[paused, "status_reason"] = "检测到该对象当前处于暂停状态。"
        
        archived = df["status_clean"].isin(["archived", "已归档", "archive"])
        df.loc[archived, "status_flag"] = "⚠️ [已归档]"
        df.loc[archived, "status_reason"] = "检测到该对象当前处于已归档状态。"
    
    return df
