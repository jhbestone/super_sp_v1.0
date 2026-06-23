"""策略映射器：根据分类结果生成投放策略"""
import pandas as pd

def map_strategy(df):
    """根据分类映射建议策略"""
    df = df.copy()
    
    strategies = []
    targeting_strategies = []
    bid_strategies = []
    placement_strategies = []
    match_strategies = []
    
    for idx, row in df.iterrows():
        typ = row.get("类型", "")
        status_flag = row.get("status_flag", "")
        acos30 = row.get("acos_all", 0) or 0
        o30 = row.get("orders_all", 0) or 0
        o7 = row.get("orders_recent_7d", 0) or 0
        o_dev = row.get("orders_trend_dev", 0) or 0
        
        # 默认值
        strategy = ""
        targeting = ""
        bid = ""
        placement = ""
        match_type = ""
        
        # 检查状态
        if "已暂停" in status_flag or "已归档" in status_flag:
            strategy = "无需操作（已暂停/归档）"
            targeting = "已暂停"
            bid = "已暂停"
            placement = "已暂停"
            match_type = "已暂停"
            strategies.append(strategy)
            targeting_strategies.append(targeting)
            bid_strategies.append(bid)
            placement_strategies.append(placement)
            match_strategies.append(match_type)
            continue
        
        # 根据类型生成策略
        if "超级关键词" in typ or "超级ASIN" in typ:
            strategy = "🚀 进攻型：加大投放，提高竞价，抢占流量"
            targeting = "积极投放"
            bid = "提高竞价 20-30%"
            placement = "顶部展示位置加价"
            match_type = "广泛匹配 + 词组匹配"
        
        elif "高潜力关键词" in typ or "高潜力ASIN" in typ:
            strategy = "🚀 进攻型：逐步提高竞价，观察趋势"
            targeting = "积极投放"
            bid = "提高竞价 10-20%"
            placement = "适度加价"
            match_type = "词组匹配"
        
        elif "次级潜力关键词" in typ or "次级潜力ASIN" in typ:
            strategy = "📊 观察型：维持现状，持续监控"
            targeting = "维持投放"
            bid = "维持当前竞价"
            placement = "标准投放"
            match_type = "当前匹配类型"
        
        elif "高竞争关键词" in typ or "高成本ASIN" in typ:
            strategy = "🚫 防守型：降低竞价或暂停，避免浪费"
            targeting = "谨慎投放"
            bid = "降低竞价 20-30%"
            placement = "降低商品页面加价"
            match_type = "精准匹配"
        
        elif "低效关键词" in typ or "低效ASIN" in typ:
            strategy = "🚫 防守型：降低出价，优化广告素材"
            targeting = "优化后投放"
            bid = "降低竞价 30-50%"
            placement = "减少展示"
            match_type = "精准匹配"
        
        elif "无效关键词" in typ or "无效ASIN" in typ:
            strategy = "❌ 立即否定：添加为否定关键词/ASIN"
            targeting = "立即停止"
            bid = "停止竞价"
            placement = "停止投放"
            match_type = "否定关键词"
        
        elif "无竞争力关键词" in typ or "无竞争力ASIN" in typ:
            strategy = "❌ 低效流量：建议否定或降低竞价"
            targeting = "观察后决定"
            bid = "降低竞价 50% 或停止"
            placement = "停止投放"
            match_type = "精准匹配或否定"
        
        else:
            strategy = "📊 待观察：数据不足，持续监控"
            targeting = "维持现状"
            bid = "维持竞价"
            placement = "标准投放"
            match_type = "当前匹配"
        
        strategies.append(strategy)
        targeting_strategies.append(targeting)
        bid_strategies.append(bid)
        placement_strategies.append(placement)
        match_strategies.append(match_type)
    
    df["建议定向策略"] = targeting_strategies
    df["建议竞价策略"] = bid_strategies
    df["建议投放位置"] = placement_strategies
    df["建议匹配类型"] = match_strategies
    df["建议策略"] = strategies
    
    return df
