---
name: super_copy
version: v1.0
description: "Super SP 广告全景分析系统 - 14 维度广告架构预测与可视化"
category: productivity
triggers:
  - "super copy"
  - "超级复制"
  - "SP 广告分析"
  - "广告全景分析"
  - "广告数据分析"
---

# Super SP 广告全景分析系统

## 简介
基于亚马逊 SP（商品推广）广告报告，进行 14 维度分类、趋势分析、策略生成和可视化展示的全景分析系统。

## 功能特性
- **14 维度分类**：无效关键词/ASIN、低效、无竞争力、高竞争、超级、高潜力、次级潜力等
- **趋势分析**：近 7 天 vs 前 23 天对比，识别上升趋势和下降趋势
- **状态核查**：自动检测暂停/归档状态
- **策略生成**：根据分类结果自动生成投放、竞价、位置建议
- **可视化大屏**：KPI 卡片 + 14 维分类侧边栏 + 搜索筛选 + 一键导出 CSV
- **多格式输出**：JSON（8 字段）、Excel（含汇总统计）、HTML 可视化面板

## 使用方式

### 命令行运行
```bash
cd "D:\我的文档\Agent\super_copy"
python generate.py [data_dir] [output_dir]
```

### Hermes 触发
直接说"运行 Super"或"分析广告数据"

## 文件结构
```
super_copy/
├── generate.py          # 主脚本
├── report_loader.py     # 报告加载器
├── trend_engine.py      # 趋势引擎
├── classifier.py        # 14 维度分类器
├── strategy_mapper.py   # 策略映射器
├── status_auditor.py    # 状态核查器
├── writer.py            # 结果写入器（JSON+HTML+Excel）
├── template.html        # 可视化面板模板（含 KPI 占位符）
├── data/                # 输入数据目录
│   ├── 商品推广_搜索词_报告_US_每日_*.xlsx
│   ├── 商品推广_推广的商品_报告_US_每日_*.xlsx
│   └── 商品推广_广告位_报告_US_每日_*.xlsx
└── output/              # 输出目录（自动创建）
    ├── analysis.json    # JSON 分析结果（8 字段格式）
    ├── report.xlsx      # Excel 报告（含汇总统计）
    └── dashboard.html   # 可视化大屏
```

## 可视化面板功能
- **KPI 卡片**：总花费、总销售额、总订单数、整体 ACoS、平均 CPC（动态计算）
- **14 维分类侧边栏**：按类型切换视图
- **筛选器**：搜索、广告组合、广告活动、匹配类型
- **一键导出**：导出当前过滤结果为 CSV

## JSON 输出字段
1. 类型
2. 广告组合
3. 广告活动名称
4. 广告组名称
5. 客户搜索词/ASIN
6. 建议定向策略
7. 匹配类型
8. 建议策略洞察

## 分类阈值配置
在 `classifier.py` 的 `THRESHOLDS` 字典中修改：
- `target_acos`: 目标 ACoS（默认 0.30）
- `super_orders_min`: 超级词最低订单数（默认 10）
- `invalid_clicks_min`: 无效词最低点击数（默认 10）
- 等...

## 模板占位符
template.html 中使用 `{{PLACEHOLDER}}` 格式：
- `{{TOTAL_COST}}` - 总花费
- `{{TOTAL_SALES}}` - 总销售额
- `{{TOTAL_ORDERS}}` - 总订单数
- `{{ACOS}}` - 整体 ACoS
- `{{AVG_CPC}}` - 平均 CPC
