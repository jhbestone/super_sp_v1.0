"""结果写入器：输出 JSON、HTML、Excel 报告"""
import pandas as pd
import json
import os
import re
from datetime import datetime

def is_asin(search_term):
    """判断搜索词是否为 ASIN（10 位字母数字组合）"""
    if not search_term or pd.isna(search_term):
        return False
    search_term = str(search_term).strip().upper()
    # ASIN 格式：10 位字母数字，通常以 B 开头
    if len(search_term) == 10 and re.match(r'^[A-Z0-9]{10}$', search_term):
        return True
    return False

def calculate_spend_structure(df):
    """计算花费结构"""
    df = df.copy()
    
    # 判断是否为 ASIN - 使用正确的列名
    if '客户搜索词/ASIN' in df.columns:
        search_col = '客户搜索词/ASIN'
    elif 'search_term' in df.columns:
        search_col = 'search_term'
    else:
        # 没有搜索词列，返回默认值
        return {
            'asin_no_order': 0, 'asin_has_order': 0,
            'keyword_total': 0, 'keyword_no_order': 0, 'keyword_has_order': 0,
            'high_click_no_order': 0, 'low_click_no_order': 0,
            'keyword_no_order_pct': 0, 'high_click_pct': 0, 'low_click_pct': 0
        }
    
    df['is_asin'] = df[search_col].apply(is_asin)
    
    cost_col = 'cost_all' if 'cost_all' in df.columns else 'cost'
    orders_col = 'orders_all' if 'orders_all' in df.columns else 'orders'
    clicks_col = 'clicks_all' if 'clicks_all' in df.columns else 'clicks'
    
    # 计算各项花费
    asin_no_order = df[(df['is_asin'] == True) & (df[orders_col] == 0)][cost_col].sum()
    asin_has_order = df[(df['is_asin'] == True) & (df[orders_col] > 0)][cost_col].sum()
    
    keyword_total = df[df['is_asin'] == False][cost_col].sum()
    keyword_no_order = df[(df['is_asin'] == False) & (df[orders_col] == 0)][cost_col].sum()
    keyword_has_order = df[(df['is_asin'] == False) & (df[orders_col] > 0)][cost_col].sum()
    
    # 高点击~不出单（点击数>17 次且订单=0）
    high_click_no_order = df[(df['is_asin'] == False) & (df[orders_col] == 0) & (df[clicks_col] > 17)][cost_col].sum()
    
    # 低点击~不出单（点击数<5 次且订单=0）
    low_click_no_order = df[(df['is_asin'] == False) & (df[orders_col] == 0) & (df[clicks_col] < 5)][cost_col].sum()
    
    # 计算占比
    keyword_no_order_pct = (high_click_no_order / keyword_total * 100) if keyword_total > 0 else 0
    high_click_pct = (high_click_no_order / keyword_total * 100) if keyword_total > 0 else 0
    low_click_pct = (low_click_no_order / keyword_total * 100) if keyword_total > 0 else 0
    
    return {
        'asin_no_order': asin_no_order,
        'asin_has_order': asin_has_order,
        'asin_total': asin_no_order + asin_has_order,
        'keyword_total': keyword_total,
        'keyword_no_order': keyword_no_order,
        'keyword_has_order': keyword_has_order,
        'high_click_no_order': high_click_no_order,
        'low_click_no_order': low_click_no_order,
        'keyword_no_order_pct': keyword_no_order_pct,
        'high_click_pct': high_click_pct,
        'low_click_pct': low_click_pct
    }

def generate_strict_json(df, output_path):
    """生成标准 JSON 输出 - 新可视化面板格式"""
    df = df.copy()
    
    # 广告组合名称 - 无组合时显示 "No Portfolio"
    if "portfolio_name" not in df.columns:
        df["portfolio_name"] = "-"
    df["广告组合"] = df["portfolio_name"].fillna("-").replace("-", "No Portfolio")
    
    # 广告活动名称
    df["广告活动名称"] = df["campaign_name"].astype(str)
    
    # 广告组名称
    df["广告组名称"] = df["ad_group_name"].astype(str)
    
    # 客户搜索词/ASIN - 优先用 search_term，没有则用 asin
    if "search_term" in df.columns:
        df["客户搜索词/ASIN"] = df["search_term"].fillna("")
    elif "asin" in df.columns:
        df["客户搜索词/ASIN"] = df["asin"].astype(str)
    else:
        df["客户搜索词/ASIN"] = ""
    
    # 匹配类型
    if "match_type" in df.columns:
        df["匹配类型"] = df["match_type"].fillna("-")
    elif "建议匹配类型" in df.columns:
        df["匹配类型"] = df["建议匹配类型"]
    else:
        df["匹配类型"] = "-"
    
    # 建议定向策略
    if "建议定向策略" not in df.columns:
        df["建议定向策略"] = "待分析"
    
    # 建议策略洞察 - 组合策略信息
    def build_insight(row):
        parts = []
        bid = row.get("建议竞价策略", "")
        placement = row.get("建议投放位置", "")
        main_strategy = row.get("建议策略", "持续监控")
        
        if bid and bid not in ["已暂停", "维持竞价"]:
            parts.append(bid)
        if placement and placement not in ["已暂停", "标准投放"]:
            parts.append(placement)
        if not parts:
            parts.append(main_strategy)
        return "，".join(parts)
    
    df["建议策略洞察"] = df.apply(build_insight, axis=1)
    
    # 类型
    if "类型" not in df.columns:
        df["类型"] = "待分类"
    
    # KPI 计算字段 - 用于前端动态统计
    df["cost"] = df.get("cost_all", df.get("cost", 0)).fillna(0)
    df["sales"] = df.get("sales_all", df.get("sales", 0)).fillna(0)
    df["orders"] = df.get("orders_all", df.get("orders", 0)).fillna(0)
    df["clicks"] = df.get("clicks_all", df.get("clicks", 0)).fillna(0)
    
    # 新增字段：是否为 ASIN
    df["is_asin"] = df["客户搜索词/ASIN"].apply(is_asin)
    
    # 新面板需要的字段
    cols = [
        "类型",
        "广告组合",
        "广告活动名称",
        "广告组名称",
        "客户搜索词/ASIN",
        "建议定向策略",
        "匹配类型",
        "建议策略洞察",
        "cost",
        "sales",
        "orders",
        "clicks",
        "is_asin"
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    
    records = df[cols].to_dict(orient="records")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return records

def calculate_kpis(df):
    """计算 KPI 指标"""
    total_cost = df["cost_all"].sum() if "cost_all" in df.columns else 0
    total_sales = df["sales_all"].sum() if "sales_all" in df.columns else 0
    total_orders = int(df["orders_all"].sum()) if "orders_all" in df.columns else 0
    total_clicks = df["clicks_all"].sum() if "clicks_all" in df.columns else 0
    
    acos = "0.0%"
    if total_sales > 0:
        acos = "{:.1f}%".format((total_cost / total_sales) * 100)
    
    avg_cpc = "$0.00"
    if total_clicks > 0:
        avg_cpc = "${:.2f}".format(total_cost / total_clicks)
    
    conv_rate = "0.0%"
    if total_clicks > 0:
        conv_rate = "{:.2f}%".format((total_orders / total_clicks) * 100)
    
    return {
        "TOTAL_COST": "${:,.2f}".format(total_cost),
        "TOTAL_SALES": "${:,.2f}".format(total_sales),
        "TOTAL_ORDERS": "{:,}".format(total_orders),
        "ACOS": acos,
        "AVG_CPC": avg_cpc,
        "CONV_RATE": conv_rate,
        "TOTAL_CLICKS": "{:,}".format(total_clicks)
    }

def write_excel(df, output_path):
    """生成 Excel 报告，包含汇总统计页"""
    df = df.copy()
    
    # 格式化日期列为 2026年6月15日 格式
    if "date" in df.columns:
        df["date"] = df["date"].apply(
            lambda x: f"{x.year}年{x.month}月{x.day}日" if pd.notna(x) else ""
        )
    # 列名中文映射
    COL_CN = {
        "date": "日期",
        "campaign_name": "广告活动名称",
        "ad_group_name": "广告组名称",
        "portfolio_name": "广告组合名称",
        "search_term": "客户搜索词/ASIN",
        "match_type": "匹配类型",
        "status": "状态",
        "status_flag": "状态标记",
        "status_reason": "状态原因",
        "asin": "ASIN",
        "placement": "广告位",
        "targeting": "投放",
        "impressions": "展示量",
        "clicks": "点击次数",
        "cost": "花费",
        "sales": "广告销售额",
        "orders": "订单数",
        "ctr": "点击率",
        "cpc": "单次点击成本",
        "acos": "ACoS",
        "conv_rate": "转化率",
        "currency": "货币",
        "retailer": "零售商",
        "country": "国家/地区",
        "总广告投资回报率 (ROAS)": "总广告投资回报率 (ROAS)",
        "7天总销售量(#)": "7天总销售量",
        "7天内广告SKU销售量(#)": "7天内广告SKU销售量",
        "7天内其他SKU销售量(#)": "7天内其他SKU销售量",
        "7天内广告SKU销售额": "7天内广告SKU销售额",
        "7天内其他SKU销售额": "7天内其他SKU销售额",
        "impressions_recent_7d": "7天展示量",
        "ctr_recent_7d": "7天CTR",
        "conv_rate_recent_7d": "7天转化率",
        "acos_recent_7d": "7天ACoS",
        "clicks_trend_dev": "点击量趋势偏差",
        "cost_trend_dev": "花费趋势偏差",
        "orders_trend_dev": "订单趋势偏差",
        "sales_trend_dev": "销售额趋势偏差",
        "impressions_trend_dev": "展示量趋势偏差",
        "conv_rate_trend_dev": "转化率趋势偏差",
        "acos_trend_dev": "ACoS趋势偏差",
        "类型": "类型",
        "建议定向策略": "建议定向策略",
        "建议竞价策略": "建议竞价策略",
        "建议投放位置": "建议投放位置",
        "建议匹配类型": "建议匹配类型",
        "建议策略": "建议策略",
        "建议策略洞察": "建议策略洞察",
        "cost_all": "30 天花费",
        "sales_all": "30 天销售额",
        "orders_all": "30 天订单数",
        "clicks_all": "30 天点击次数",
        "impressions_all": "30 天展示量",
        "acos_all": "30 天ACoS",
        "conv_rate_all": "30 天转化率",
        "cpc_all": "30 天CPC",
        "ctr_all": "30 天CTR",
        "cost_recent_7d": "7 天花费",
        "sales_recent_7d": "7 天销售额",
        "orders_recent_7d": "7 天订单数",
        "clicks_recent_7d": "7 天点击次数",
        "is_asin": "是否为 ASIN",
    }
    
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # 详细分析页 - 使用中文列名
        df_cn = df.copy()
        df_cn.columns = [COL_CN.get(c, c) for c in df_cn.columns]
        df_cn.to_excel(writer, index=False, sheet_name="详细分析")
        
        summary_data = []
        type_counts = df["类型"].value_counts()
        for typ, count in type_counts.items():
            subset = df[df["类型"] == typ]
            summary_data.append({
                "分类": typ,
                "数量": count,
                "总花费": subset["cost_all"].sum() if "cost_all" in subset.columns else 0,
                "总销售额": subset["sales_all"].sum() if "sales_all" in subset.columns else 0,
                "平均 ACoS": subset["acos_all"].mean() if "acos_all" in subset.columns else 0,
                "总订单数": subset["orders_all"].sum() if "orders_all" in subset.columns else 0,
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, index=False, sheet_name="汇总统计")
        
        attack_df = df[df["类型"].str.contains("超级 | 高潜力", na=False)]
        attack_df_cn = attack_df.copy()
        attack_df_cn.columns = [COL_CN.get(c, c) for c in attack_df_cn.columns]
        attack_df_cn.to_excel(writer, index=False, sheet_name="进攻型策略")
        
        defend_df = df[df["类型"].str.contains("无效 | 低效 | 无竞争力 | 高竞争", na=False)]
        defend_df_cn = defend_df.copy()
        defend_df_cn.columns = [COL_CN.get(c, c) for c in defend_df_cn.columns]
        defend_df_cn.to_excel(writer, index=False, sheet_name="防守型策略")

def generate_dashboard_html(json_data, template_path, output_path, df=None, search_file_name=None):
    """将 JSON 数据注入 HTML 模板 - 新面板格式"""
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 注入 JSON 数据 - 替换 mockData 数组
    json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
    html = re.sub(
        r'const mockData = \[.*?\];',
        'const mockData = ' + json_str + ';',
        html,
        count=1,
        flags=re.DOTALL
    )
    
    # 注入 KPI 值
    if df is not None:
        kpis = calculate_kpis(df)
        for key, value in kpis.items():
            placeholder = '{{' + key + '}}'
            html = html.replace(placeholder, value)
        
        # 注入花费结构数据
        spend_struct = calculate_spend_structure(df)
        html = html.replace('{{ASIN_NO_ORDER}}', "${:,.2f}".format(spend_struct['asin_no_order']))
        html = html.replace('{{ASIN_HAS_ORDER}}', "${:,.2f}".format(spend_struct['asin_has_order']))
        html = html.replace('{{ASIN_TOTAL}}', "${:,.2f}".format(spend_struct['asin_total']))
        html = html.replace('{{KEYWORD_NO_ORDER}}', "${:,.2f}".format(spend_struct['keyword_no_order']))
        html = html.replace('{{KEYWORD_HAS_ORDER}}', "${:,.2f}".format(spend_struct['keyword_has_order']))
        html = html.replace('{{KEYWORD_TOTAL}}', "${:,.2f}".format(spend_struct['keyword_total']))
        html = html.replace('{{KEYWORD_NO_ORDER_PCT}}', "{:.2f}%".format(spend_struct['keyword_no_order_pct']))
        html = html.replace('{{HIGH_CLICK_PCT}}', "{:.2f}%".format(spend_struct['high_click_pct']))
        html = html.replace('{{LOW_CLICK_PCT}}', "{:.2f}%".format(spend_struct['low_click_pct']))
    
    # 注入数据来源（搜索词报告文件名）
    data_source = search_file_name if search_file_name else "系统解析"
    html = html.replace('数据来源：系统解析', f'数据来源：{data_source}')
    
    # 注入生成时间
    generated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = html.replace('{{GENERATED_TIME}}', generated_time)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 可视化大屏已生成：{output_path}")
