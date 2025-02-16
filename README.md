# AI NASDAQ Analysis

## 项目简介

这是一个基于Python的纳斯达克上市公司财务分析工具，能够自动获取、分析和可视化上市公司的财务数据，帮助投资者更好地理解公司的财务状况和投资价值。

## 主要功能

- 自动获取纳斯达克上市公司列表
- 下载公司财务报表数据（损益表、资产负债表等）
- 计算关键财务指标（毛利率、营业利润率、ROE等）
- 生成详细的财务分析报告
- 创建可视化图表展示财务趋势
- 支持批量分析多家公司
- 提供数据合并功能，便于比较分析

## 技术栈

- Python 3.x
- pandas：数据处理和分析
- matplotlib & seaborn：数据可视化
- requests：API数据获取
- beautifulsoup4：网页解析

## 安装指南

1. 克隆项目到本地：
```bash
git clone https://github.com/yourusername/ai-nasdaq-analysis.git
cd ai-nasdaq-analysis
```

2. 创建并激活虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 使用说明

### API密钥配置

本项目使用 Financial Modeling Prep API 获取财务数据。在运行程序前，请确保：

1. 注册并获取 API 密钥：[Financial Modeling Prep](https://financialmodelingprep.com/developer/docs/)
2. 将API密钥替换到代码中的相应位置

### 运行程序

1. 分析指定公司：
```bash
python main.py -s AAPL MSFT GOOGL
```

2. 分析所有公司：
```bash
python main.py -a
```

3. 默认分析前5家公司：
```bash
python main.py
```

### 合并数据

如果需要合并多个公司的分析结果：
```bash
python merge_csv.py
```

## 分析结果

程序会在 `analysis` 目录下生成以下文件：

- `{symbol}_financials.csv`：原始财务数据
- `{symbol}_analysis.json`：财务分析结果
- `{symbol}_analysis.png`：财务指标可视化图表
- `all_companies_financials.csv`：合并后的所有公司财务数据

## 数据分析内容

### 财务指标

- 收入增长趋势
- 利润率分析（毛利率、营业利润率、净利率）
- 运营效率（营业收入、净收入对比）
- 估值指标（市盈率、市净率）
- 杜邦分析（ROE分解）
- 财务健康度（流动比率、资产负债率）

### 可视化图表

生成的分析图表包含6个子图，全面展示公司的：

1. 收入增长趋势
2. 各类利润率变化
3. 营业收入与净收入对比
4. 估值指标变化
5. ROE分析
6. 财务健康指标

## 注意事项

- API调用可能有频率限制，请合理控制请求频率
- 建议先使用少量数据测试程序功能
- 确保网络连接稳定，避免数据下载中断

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。在提交代码前，请确保：

1. 代码符合Python代码规范
2. 添加必要的注释和文档
3. 确保所有测试通过

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件