# Super SP v1.0 - 亚马逊广告全景分析系统
2026-06-23
> 基于 AI 智能分类的广告数据分析工具，支持可视化大屏、否定关键词挖掘、花费结构分析等功能

## ✨ v1.0 新功能

### 1. 广告组合 (Portfolio) 筛选联动
- 筛选广告组合时，广告活动列表自动同步
- `"-"` 字段显示为 `"No Portfolio"`

### 2. 实时统计看板
筛选时自动更新顶部 KPI：
- 总花费 `{{TOTAL_COST}}`
- 总销售额 `{{TOTAL_SALES}}`
- 总订单数 `{{TOTAL_ORDERS}}`
- 整体 ACoS `{{ACOS}}`
- 平均 CPC `{{AVG_CPC}}`

### 3. 选定广告活动指标
- 已选广告活动数量
- 30 天花费 / 点击次数 / 订单 / 广告销售额
- 30 天转化率（总订单数/总点击量×100%）
- 30 天 ACoS（广告花费/广告销售额×100%）

### 4. 花费结构分析
- ASIN~不出单/出单 总花费
- 关键词~不出单/出单 总花费
- 关键词总花费
- 高点击~不出单 花费占比（点击>17 次且订单=0）
- 低点击~不出单 花费占比（点击<5 次且订单=0）

### 5. 否定关键词挖掘

#### 手动挖掘模式
提取已选广告活动的全部【词组否定】和【精准否定】关键词

#### 自动挖掘模式
多维度计算指标，自动筛选需要否定的关键词：
- 高点击无转化（点击≥5，订单=0）
- 低 CTR（CTR<0.5%）
- 高 ACoS（ACoS>100%）

#### 筛选否定关键词
支持多维度筛选：
- 出单标识：ASIN-不出单/出单、关键词 - 不出单/出单
- 指标范围：花费、点击、订单、CTR、ACoS

## 🚀 快速开始

### 环境要求
- Python 3.10+
- pandas
- openpyxl

### 安装依赖
```bash
pip install pandas openpyxl
```

### 运行分析
```bash
# Windows
run.bat

# 或直接运行
python generate.py
```

### 输出文件
| 文件 | 说明 |
|------|------|
| `output/dashboard.html` | 可视化大屏 |
| `output/report.xlsx` | Excel 报告 |
| `output/analysis.json` | JSON 数据 |
| `output/negatives.json` | 否定关键词数据 |

## 📁 项目结构

```
super_sp_v1.0/
├── generate.py           # 主入口脚本
├── writer.py             # 数据写入器
├── negative_keywords.py  # 否定关键词挖掘模块
├── template.html         # 可视化模板
├── classifier.py         # 14 维度分类器
├── trend_engine.py       # 趋势计算引擎
├── report_loader.py      # 报告加载器
├── strategy_mapper.py    # 策略映射器
├── status_auditor.py     # 状态核查器
├── data/                 # 广告报告数据
├── output/               # 输出文件（运行时生成）
└── README.md
```

## 📊 14 维度分类

系统自动将广告数据分类为：
- 超级 ASIN / 超级关键词
- 高潜力 ASIN / 高潜力关键词
- 次级潜力 ASIN / 次级潜力关键词
- 无效 ASIN / 无效关键词
- 无竞争力 ASIN / 无竞争力关键词
- 低效 ASIN / 低效关键词
- 高成本 ASIN

## 🔧 配置说明

### 数据文件要求
将亚马逊广告报告放入 `data/` 目录：
- 搜索词报告（必需）
- 广告位报告（可选）
- 推广商品报告（可选）

### 自定义分类阈值
编辑 `classifier.py` 中的 `THRESHOLDS` 配置

## 📄 许可证

MIT License

## 👤 作者

GitHub: [@jhbestone](https://github.com/jhbestone)

## 📝 更新日志

### v1.0.0 (2026-06-23)
- ✨ 新增广告组合筛选联动功能
- ✨ 新增选定广告活动指标板块
- ✨ 新增花费结构分析
- ✨ 新增否定关键词挖掘（手动/自动模式）
- ✨ 新增多维度否定关键词筛选
- 🐛 修复数据加载和计算问题
- 📝 更新文档和说明
