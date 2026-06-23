"""否定关键词挖掘模块：手动/自动模式"""
import pandas as pd
import numpy as np
import json
import re


def is_asin(search_term):
    """判断搜索词是否为 ASIN"""
    if not search_term or pd.isna(search_term):
        return False
    search_term = str(search_term).strip().upper()
    if len(search_term) == 10 and re.match(r'^[A-Z0-9]{10}$', search_term):
        return True
    return False


def classify_search_term(search_term):
    """分类搜索词：ASIN 或 关键词"""
    return "ASIN" if is_asin(search_term) else "关键词"


def extract_negatives_from_data(df):
    """
    从广告数据中提取否定关键词
    返回：{
        'phrase': [{'keyword': str, 'campaign': str, 'match_type': str, 'cost': float, 'clicks': int, 'orders': int, 'sales': float, 'is_asin': bool, 'has_order': bool}],
        'exact': [...]
    }
    """
    result = {
        'phrase': [],
        'exact': []
    }
    
    # 检查是否有否定关键词相关的列
    neg_keywords_col = None
    neg_type_col = None
    
    for col in df.columns:
        col_lower = col.lower().replace(' ', '_')
        if 'negative' in col_lower or 'neg' in col_lower:
            if 'type' in col_lower or 'match' in col_lower or '关键词' in col:
                neg_type_col = col
            elif neg_keywords_col is None:
                neg_keywords_col = col
    
    if neg_keywords_col and neg_type_col:
        for _, row in df.iterrows():
            neg_str = row.get(neg_keywords_col, '')
            if not neg_str or pd.isna(neg_str):
                continue
            
            neg_type = row.get(neg_type_col, '')
            cost = float(row.get('cost', 0) or row.get('cost_all', 0) or 0)
            clicks = int(row.get('clicks', 0) or 0)
            orders = int(row.get('orders', 0) or row.get('orders_all', 0) or 0)
            sales = float(row.get('sales', 0) or row.get('sales_all', 0) or 0)
            search_term = str(row.get('search_term', row.get('客户搜索词/ASIN', '')))
            campaign = str(row.get('campaign_name', row.get('广告活动名称', '')))
            
            keyword_entry = {
                'keyword': neg_str.strip() if isinstance(neg_str, str) else str(neg_str),
                'campaign': campaign,
                'match_type': neg_type if isinstance(neg_type, str) else str(neg_type),
                'cost': cost,
                'clicks': clicks,
                'orders': orders,
                'sales': sales,
                'is_asin': is_asin(search_term),
                'has_order': orders > 0,
                'conv_rate': (orders / clicks * 100) if clicks > 0 else 0,
                'acos': (cost / sales * 100) if sales > 0 else 0,
                'ctr': 0
            }
            
            if '精准' in str(neg_type) or 'EXACT' in str(neg_type).upper():
                result['exact'].append(keyword_entry)
            elif '词组' in str(neg_type) or 'PHRASE' in str(neg_type).upper():
                result['phrase'].append(keyword_entry)
    else:
        # 如果没有否定关键词列，尝试从匹配类型列推断
        match_col = None
        for col in df.columns:
            if 'match' in col.lower() or '匹配' in col:
                match_col = col
                break
        
        if match_col:
            for _, row in df.iterrows():
                match_type = str(row.get(match_col, ''))
                if 'NEGATIVE' in match_type.upper():
                    cost = float(row.get('cost', 0) or row.get('cost_all', 0) or 0)
                    clicks = int(row.get('clicks', 0) or 0)
                    orders = int(row.get('orders', 0) or row.get('orders_all', 0) or 0)
                    sales = float(row.get('sales', 0) or row.get('sales_all', 0) or 0)
                    search_term = str(row.get('search_term', row.get('客户搜索词/ASIN', '')))
                    campaign = str(row.get('campaign_name', row.get('广告活动名称', '')))
                    
                    keyword_entry = {
                        'keyword': search_term,
                        'campaign': campaign,
                        'match_type': match_type,
                        'cost': cost,
                        'clicks': clicks,
                        'orders': orders,
                        'sales': sales,
                        'is_asin': is_asin(search_term),
                        'has_order': orders > 0,
                        'conv_rate': (orders / clicks * 100) if clicks > 0 else 0,
                        'acos': (cost / sales * 100) if sales > 0 else 0
                    }
                    
                    if 'EXACT' in match_type.upper():
                        result['exact'].append(keyword_entry)
                    elif 'PHRASE' in match_type.upper():
                        result['phrase'].append(keyword_entry)
    
    return result


def auto_mine_negative_keywords(negatives_data, df):
    """
    自动挖掘模式：多维度计算已选广告活动的指标，自动筛选出精准否定关键词
    """
    candidates = []
    
    all_negatives = negatives_data.get('exact', []) + negatives_data.get('phrase', [])
    
    if not all_negatives:
        df_copy = df.copy()
        
        # 筛选条件：有花费但无订单
        no_order_df = df_copy[
            (df_copy['cost'] > 0) & 
            (df_copy['orders'] == 0)
        ]
        
        # 高点击无转化（点击数 >= 5，订单 = 0）
        high_click_no_conv = no_order_df[no_order_df['clicks'] >= 5]
        
        for _, row in high_click_no_conv.iterrows():
            search_term = row.get('客户搜索词/ASIN', '')
            candidates.append({
                'keyword': search_term,
                'type': '精准否定',
                'reason': '高点击无转化',
                'cost': float(row.get('cost', 0)),
                'clicks': int(row.get('clicks', 0)),
                'orders': 0,
                'is_asin': is_asin(search_term),
                'acos': float('inf')
            })
        
        # 低 CTR 关键词（CTR < 0.5%，点击数 >= 10）
        low_ctr_df = df_copy[
            (df_copy['clicks'] >= 10) & 
            (df_copy['impressions'] > 100)
        ]
        if 'ctr' in low_ctr_df.columns or 'ctr_all' in low_ctr_df.columns:
            ctr_col = 'ctr' if 'ctr' in low_ctr_df.columns else 'ctr_all'
            low_ctr_candidates = low_ctr_df[low_ctr_df[ctr_col] < 0.005]
            
            for _, row in low_ctr_candidates.iterrows():
                search_term = row.get('客户搜索词/ASIN', '')
                candidates.append({
                    'keyword': search_term,
                    'type': '精准否定',
                    'reason': '低 CTR',
                    'cost': float(row.get('cost', 0)),
                    'clicks': int(row.get('clicks', 0)),
                    'orders': int(row.get('orders', 0)),
                    'is_asin': is_asin(search_term),
                    'ctr': float(row.get(ctr_col, 0))
                })
    else:
        for neg in all_negatives:
            if neg.get('orders', 0) == 0 and neg.get('cost', 0) > 0:
                candidates.append({
                    'keyword': neg.get('keyword', ''),
                    'type': '精准否定',
                    'reason': '无订单浪费花费',
                    'cost': neg.get('cost', 0),
                    'clicks': neg.get('clicks', 0),
                    'orders': 0,
                    'is_asin': neg.get('is_asin', False),
                    'acos': neg.get('acos', float('inf'))
                })
            elif neg.get('clicks', 0) >= 10 and neg.get('orders', 0) == 0:
                candidates.append({
                    'keyword': neg.get('keyword', ''),
                    'type': '精准否定',
                    'reason': '高点击无转化',
                    'cost': neg.get('cost', 0),
                    'clicks': neg.get('clicks', 0),
                    'orders': 0,
                    'is_asin': neg.get('is_asin', False),
                    'acos': neg.get('acos', float('inf'))
                })
    
    # 去重
    if candidates:
        df_candidates = pd.DataFrame(candidates)
        df_candidates = df_candidates.sort_values('cost', ascending=False)
        df_candidates = df_candidates.drop_duplicates(subset=['keyword'], keep='first')
        candidates = df_candidates.to_dict(orient='records')
    
    return candidates


def filter_negative_keywords(negatives_data, filters):
    """根据筛选条件过滤否定关键词"""
    results = []
    
    neg_type = filters.get('type', 'exact')
    keywords = negatives_data.get(neg_type, [])
    
    for kw in keywords:
        if filters.get('asin_filter') == 'asin_only' and not kw.get('is_asin', False):
            continue
        if filters.get('asin_filter') == 'keyword_only' and kw.get('is_asin', False):
            continue
        
        if filters.get('order_filter') == 'has_order' and not kw.get('has_order', False):
            continue
        if filters.get('order_filter') == 'no_order' and kw.get('has_order', False):
            continue
        
        cost = kw.get('cost', 0)
        if filters.get('min_cost') is not None and cost < filters['min_cost']:
            continue
        if filters.get('max_cost') is not None and cost > filters['max_cost']:
            continue
        
        clicks = kw.get('clicks', 0)
        if filters.get('min_clicks') is not None and clicks < filters['min_clicks']:
            continue
        if filters.get('max_clicks') is not None and clicks > filters['max_clicks']:
            continue
        
        orders = kw.get('orders', 0)
        if filters.get('min_orders') is not None and orders < filters['min_orders']:
            continue
        if filters.get('max_orders') is not None and orders > filters['max_orders']:
            continue
        
        acos = kw.get('acos', 0)
        if filters.get('min_acos') is not None and acos < filters['min_acos']:
            continue
        if filters.get('max_acos') is not None and acos > filters['max_acos']:
            continue
        
        ctr = kw.get('ctr', 0)
        if filters.get('min_ctr') is not None and ctr < filters['min_ctr']:
            continue
        if filters.get('max_ctr') is not None and ctr > filters['max_ctr']:
            continue
        
        search_kw = filters.get('keyword', '')
        if search_kw and search_kw.lower() not in kw.get('keyword', '').lower():
            continue
        
        results.append(kw)
    
    return results


def get_negative_keywords_summary(negatives_data, df):
    """生成否定关键词汇总统计"""
    summary = {
        'total_phrase': len(negatives_data.get('phrase', [])),
        'total_exact': len(negatives_data.get('exact', [])),
        'phrase_no_order': len([kw for kw in negatives_data.get('phrase', []) if not kw.get('has_order', False)]),
        'exact_no_order': len([kw for kw in negatives_data.get('exact', []) if not kw.get('has_order', False)]),
        'total_cost': sum(kw.get('cost', 0) for kw in negatives_data.get('phrase', []) + negatives_data.get('exact', [])),
        'total_clicks': sum(kw.get('clicks', 0) for kw in negatives_data.get('phrase', []) + negatives_data.get('exact', [])),
        'total_orders': sum(kw.get('orders', 0) for kw in negatives_data.get('phrase', []) + negatives_data.get('exact', [])),
        'avg_cost': 0,
        'avg_clicks': 0
    }
    
    total = summary['total_phrase'] + summary['total_exact']
    if total > 0:
        summary['avg_cost'] = summary['total_cost'] / total
        summary['avg_clicks'] = summary['total_clicks'] / total
    
    return summary
