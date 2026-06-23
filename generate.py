"""Super SP v1.0 主脚本：读取 Excel → 分类 → 输出 JSON+HTML+Excel
新增功能：
- 广告组合 (Portfolio) 筛选联动
- 选定广告活动指标实时更新
- 花费结构分析
"""
import os
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_loader import load_and_merge
from trend_engine import calculate_trends, merge_trends_to_df
from classifier import classify
from strategy_mapper import map_strategy
from status_auditor import audit_status
from writer import generate_strict_json, write_excel, generate_dashboard_html


def run_analysis(data_dir, output_dir):
    """执行完整分析流程"""
    print("=" * 60)
    print("🚀 Super SP 广告全景分析系统 v1.0")
    print("=" * 60)
    
    # 1. 加载数据
    print("\n📂 步骤 1: 加载广告报告...")
    search_df, prod_df, place_df, search_file_name = load_and_merge(data_dir)
    
    if search_df is None:
        print("❌ 未找到搜索词报告，无法继续分析")
        return
    
    print(f"   ✅ 搜索词报告：{len(search_df)} 行")
    if prod_df is not None:
        print(f"   ✅ 推广商品报告：{len(prod_df)} 行")
    if place_df is not None:
        print(f"   ✅ 广告位报告：{len(place_df)} 行")
    
    # 2. 合并数据（以搜索词报告为主）
    df = search_df.copy()
    
    # 3. 计算趋势
    print("\n📈 步骤 2: 计算 30 天趋势...")
    trends = calculate_trends(df)
    df = merge_trends_to_df(df, trends)
    
    # 4. 状态核查
    print("\n🔍 步骤 3: 状态核查...")
    df = audit_status(df)
    paused_count = (df["status_flag"] != "").sum()
    print(f"   ⚠️  检测到 {paused_count} 个已暂停/归档对象")
    
    # 5. 分类
    print("\n🏷️  步骤 4: 14 维度分类...")
    df["类型"] = classify(df)
    type_counts = df["类型"].value_counts()
    for typ, count in type_counts.items():
        print(f"   - {typ}: {count}")
    
    # 6. 策略映射
    print("\n💡 步骤 5: 生成投放策略...")
    df = map_strategy(df)
    
    # 7. 去重（同一广告活动下的同一关键词/ASIN 只保留一条）
    print("\n🧹 步骤 6: 去重处理...")
    print(f"   去重前：{len(df)} 条")
    if 'cost_recent_7d' in df.columns:
        df = df.sort_values('cost_recent_7d', ascending=False, na_position='last')
    df = df.drop_duplicates(subset=['campaign_name', 'search_term'], keep='first')
    df = df.reset_index(drop=True)
    print(f"   去重后：{len(df)} 条")
    print(f"   已删除：{len(df)} 条重复记录")
    
    # 8. 输出结果
    print("\n📤 步骤 7: 输出结果...")
    os.makedirs(output_dir, exist_ok=True)
    
    # JSON
    json_path = os.path.join(output_dir, "analysis.json")
    records = generate_strict_json(df, json_path)
    print(f"   ✅ JSON: {json_path} ({len(records)} 条记录)")
    
    # Excel
    excel_path = os.path.join(output_dir, "report.xlsx")
    write_excel(df, excel_path)
    print(f"   ✅ Excel: {excel_path}")
    
    # HTML 可视化
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")
    html_path = os.path.join(output_dir, "dashboard.html")
    generate_dashboard_html(records, template_path, html_path, df, search_file_name)
    
    print("\n" + "=" * 60)
    print("✅ 分析完成！")
    print(f"📂 输出目录：{output_dir}")
    print("📄 dashboard.html - 可视化大屏")
    print("📄 report.xlsx - Excel 报告")
    print("📄 analysis.json - JSON 数据")
    print("=" * 60)
    
    return df


def main():
    """命令行入口"""
    # 默认路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    output_dir = os.path.join(base_dir, "output")
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    print(f"数据目录：{data_dir}")
    print(f"输出目录：{output_dir}")
    
    run_analysis(data_dir, output_dir)


if __name__ == "__main__":
    main()
