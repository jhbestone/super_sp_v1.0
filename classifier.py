"""Super 14维度分类引擎：基于数据和趋势对每个投放对象进行分类"""
import pandas as pd
import numpy as np

THRESHOLDS = {
    "target_acos": 0.30,
    "super_orders_min": 10,
    "high_orders_min": 5,
    "low_orders_min": 1,
    "invalid_clicks_min": 10,
    "low_eff_clicks_min": 15,
    "high_comp_clicks_min": 20,
    "low_ctr_min": 0.005,
    "no_comp_ctr_min": 0.002,
    "trend_boost_threshold": 0.20
}

def classify(df):
    """
    14维度分类：
    1. 无效关键词 (P1-立即否定)
    2. 低效关键词 (CTR过低)
    3. 无竞争力关键词 (CTR极低)
    4. 高竞争关键词 (高花费高ACoS)
    5. 超级关键词 (高订单低ACoS趋势升)
    6. 高潜力关键词 (订单不错ACoS可接受趋势升)
    7. 次级潜力关键词 (有些订单ACoS可接受)
    8. 无效ASIN
    9. 低效ASIN
    10. 无竞争力ASIN
    11. 高成本ASIN
    12. 次级潜力ASIN
    13. 高潜力ASIN
    14. 超级ASIN
    """
    types = []
    for idx, row in df.iterrows():
        o30 = row.get("orders_all", 0) or 0
        o7 = row.get("orders_recent_7d", 0) or 0
        c30 = row.get("clicks_all", 0) or 0
        c7 = row.get("clicks_recent_7d", 0) or 0
        cost30 = row.get("cost_all", 0) or 0
        sales30 = row.get("sales_all", 0) or 0
        conv30 = row.get("conv_rate_all", 0) or 0
        acos30 = row.get("acos_all", 0) or 0
        ctr30 = row.get("ctr_all", 0) or 0
        imp30 = row.get("impressions_all", 0) or 0
        o_dev = row.get("orders_trend_dev", 0) or 0
        conv_dev = row.get("conv_rate_trend_dev", 0) or 0
        
        t = THRESHOLDS
        up = (o_dev > t["trend_boost_threshold"]) or (conv_dev > t["trend_boost_threshold"])
        typ = "无竞争力关键词"
        
        # 1. Invalid: High clicks, 0 orders
        if c30 >= t["invalid_clicks_min"] and o30 == 0:
            typ = "无效关键词"
        # 2. Low efficiency: Low CTR
        elif ctr30 < t["low_ctr_min"] and imp30 > 100:
            typ = "低效关键词"
        # 3. Uncompetitive: Very low CTR
        elif ctr30 < t["no_comp_ctr_min"] and imp30 > 50:
            typ = "无竞争力关键词"
        # 4. High competition: High clicks, very high ACoS
        elif c30 >= t["high_comp_clicks_min"] and acos30 > (t["target_acos"]*1.5):
            typ = "高竞争关键词"
        # 5. Super: High orders, low ACoS, trending up
        elif o30 >= t["super_orders_min"] and acos30 < (t["target_acos"]*0.8) and up:
            typ = "超级关键词"
        # 6. High potential: Good orders, good ACoS, trending up
        elif o30 >= t["high_orders_min"] and (t["target_acos"]*0.8) <= acos30 <= t["target_acos"] and up:
            typ = "高潜力关键词"
        # 7. Secondary potential: Some orders, acceptable ACoS
        elif o30 >= t["low_orders_min"] and acos30 < (t["target_acos"]*1.3):
            typ = "次级潜力关键词"
        # 8. Invalid fallback
        elif c30 > 0 and o30 == 0:
            typ = "无效关键词"
        else:
            typ = "无竞争力关键词"
        
        # 判断是否为ASIN类型
        tgt = str(row.get("targeting", "")).upper()
        if "ASIN" in tgt or "PRODUCT" in tgt:
            if "高竞争" in typ:
                typ = "高成本ASIN"
            elif "无竞争力" in typ:
                typ = "无竞争力ASIN"
            elif "低效" in typ:
                typ = "低效ASIN"
            elif "无效" in typ:
                typ = "无效ASIN"
            elif "次级" in typ:
                typ = "次级潜力ASIN"
            elif "高潜力" in typ:
                typ = "高潜力ASIN"
            elif "超级" in typ:
                typ = "超级ASIN"
        
        types.append(typ)
    
    return pd.Series(types, index=df.index)
