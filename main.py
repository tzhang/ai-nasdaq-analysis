import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import matplotlib.pyplot as plt
import json

# 配置
ANALYSIS_DIR = './analysis'
NASDAQ_URL = 'https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=25&offset=0'

def get_nasdaq_companies():
    """获取纳斯达克上市公司列表"""
    try:
        response = requests.get(NASDAQ_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        data = response.json()
        
        # 调试：打印API响应结构
        print("API响应结构：")
        print(json.dumps(data, indent=2))
        
        # 尝试从不同路径提取数据
        if 'data' in data and 'table' in data['data'] and 'rows' in data['data']['table']:
            companies = pd.DataFrame(data['data']['table']['rows'])
        elif 'data' in data and 'rows' in data['data']:
            companies = pd.DataFrame(data['data']['rows'])
        else:
            print("无法解析API响应格式")
            return None
            
        # 确保包含必要字段
        if 'symbol' not in companies.columns:
            print("API响应中缺少symbol字段")
            return None
            
        print(f"成功获取{len(companies)}家公司数据")
        print("示例公司数据：")
        print(companies.head())
            
        return companies
    except Exception as e:
        print(f"获取公司列表失败: {str(e)}")
        return None

def download_financials(symbol):
    """下载指定公司的财报数据"""
    try:
        print(f"\n开始下载{symbol}财报数据...")
        
        # 获取公司基本信息（包含marketCap）
        company_url = f'https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey=b148Lq1vPP0FDEtmnj2ffVnZq2Gg8iSL'
        company_response = requests.get(company_url)
        company_response.raise_for_status()
        company_data = company_response.json()
        market_cap = float(company_data[0]['mktCap']) if company_data else None
        
        # 下载损益表
        income_url = f'https://financialmodelingprep.com/api/v3/income-statement/{symbol}?apikey=b148Lq1vPP0FDEtmnj2ffVnZq2Gg8iSL'
        print(f"损益表URL: {income_url}")
        income_response = requests.get(income_url)
        income_response.raise_for_status()
        income_data = income_response.json()
        print(f"成功获取{symbol}损益表数据")
        
        # 下载资产负债表
        balance_url = f'https://financialmodelingprep.com/api/v3/balance-sheet-statement/{symbol}?apikey=b148Lq1vPP0FDEtmnj2ffVnZq2Gg8iSL'
        print(f"资产负债表URL: {balance_url}")
        balance_response = requests.get(balance_url)
        balance_response.raise_for_status()
        balance_data = balance_response.json()
        print(f"成功获取{symbol}资产负债表数据")
        
        # 合并数据
        financials = []
        for income, balance in zip(income_data, balance_data):
            if income['date'] == balance['date']:  # 确保同一报告期
                merged = {**income, **balance}
                merged['marketCap'] = market_cap  # 添加市值信息
                financials.append(merged)
                
        return financials
    except Exception as e:
        print(f"下载{symbol}财报失败: {str(e)}")
        return None

def analyze_valuation(company_data):
    """分析公司估值"""
    try:
        df = pd.DataFrame(company_data)
        symbol = df.iloc[0]['symbol']
        
        # 计算关键财务指标
        df['gross_profit_margin'] = df['grossProfit'] / df['revenue']
        df['operating_margin'] = df['operatingIncome'] / df['revenue']
        df['net_margin'] = df['netIncome'] / df['revenue']
        df['asset_turnover'] = df['revenue'] / df['totalAssets']
        df['roe'] = df['netIncome'] / df['totalStockholdersEquity']
        df['current_ratio'] = df['totalCurrentAssets'] / df['totalCurrentLiabilities']
        
        # 计算增长率
        revenue_growth = df['revenue'].pct_change().mean() * 100
        net_income_growth = df['netIncome'].pct_change().mean() * 100
        
        # DCF估值参数
        wacc = 0.08  # 加权平均资本成本
        terminal_growth = 0.03  # 永续增长率
        forecast_years = 3  # 预测年数
        
        # 计算自由现金流
        df['free_cash_flow'] = df['operatingCashFlow'] - df['capitalExpenditure']
        
        # 预测未来自由现金流
        latest = df.iloc[0]
        fcf_growth = df['free_cash_flow'].pct_change().mean()
        forecast_fcf = [
            latest['free_cash_flow'] * (1 + fcf_growth) ** (i + 1)
            for i in range(forecast_years)
        ]
        
        # 计算终值
        terminal_value = forecast_fcf[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
        
        # 折现现金流
        discounted_cash_flows = [
            fcf / (1 + wacc) ** (i + 1)
            for i, fcf in enumerate(forecast_fcf)
        ]
        discounted_terminal_value = terminal_value / (1 + wacc) ** forecast_years
        
        # 计算企业价值
        enterprise_value = sum(discounted_cash_flows) + discounted_terminal_value
        
        # 计算股权价值
        equity_value = enterprise_value - latest['totalDebt'] + latest['cashAndCashEquivalents']
        
        # 计算每股内在价值
        shares_outstanding = latest['marketCap'] / latest['price']
        intrinsic_value = equity_value / shares_outstanding
        
        # 最新财报数据
        valuation = {
            'symbol': latest['symbol'],
            'revenue_growth': round(revenue_growth, 2),
            'net_income_growth': round(net_income_growth, 2),
            'dcf_valuation': {
                'intrinsic_value': round(intrinsic_value, 2),
                'enterprise_value': round(enterprise_value, 2),
                'equity_value': round(equity_value, 2),
                'wacc': wacc,
                'terminal_growth': terminal_growth,
                'forecast_years': forecast_years,
                'forecast_fcf': [round(fcf, 2) for fcf in forecast_fcf],
                'discounted_cash_flows': [round(dcf, 2) for dcf in discounted_cash_flows],
                'discounted_terminal_value': round(discounted_terminal_value, 2)
            },
            'profitability': {
                'gross_margin': round(latest['gross_profit_margin'] * 100, 2),
                'operating_margin': round(latest['operating_margin'] * 100, 2),
                'net_margin': round(latest['net_margin'] * 100, 2),
                'roe': round(latest['roe'] * 100, 2) if pd.notnull(latest['roe']) else None
            },
            'efficiency': {
                'asset_turnover': round(latest['asset_turnover'], 2),
                'current_ratio': round(latest['current_ratio'], 2)
            },
            'financial_health': {
                'debt_to_equity': (latest['totalLiabilities'] / latest['totalStockholdersEquity']) 
                    if latest['totalStockholdersEquity'] > 0 else None
            }
        }
        
        # 保存分析结果
        analysis_path = os.path.join(ANALYSIS_DIR, f"{latest['symbol']}_analysis.json")
        with open(analysis_path, 'w') as f:
            json.dump(valuation, f, indent=2)
            
        # 生成可视化图表
        plot_financials(df, latest['symbol'])
        
        return valuation
    except Exception as e:
        print(f"分析{symbol}估值失败: {str(e)}")
        return None

def plot_financials(df, symbol):
    """生成财务数据可视化图表"""
    try:
        # 确保analysis目录存在
        os.makedirs(ANALYSIS_DIR, exist_ok=True)
        
        # 按日期排序，确保最新数据在右侧
        df = df.sort_values('date', ascending=True)
        
        import seaborn as sns
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(18, 12))
        
        # 1. 收入增长趋势
        plt.subplot(3, 2, 1)
        plt.plot(df['date'], df['revenue'], 'b-o', linewidth=2, markersize=8)
        plt.xticks(rotation=45, ha='right')  # 旋转x轴标签
        plt.title(f'{symbol} Revenue Growth Trend', fontsize=12, pad=20)
        plt.xlabel('Date', fontsize=10)
        plt.ylabel('Revenue (Millions USD)', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 添加数据标签，使用财务格式
        def format_currency(value):
            """将数值格式化为财务格式"""
            if value >= 1e9:
                return f'${value/1e9:.1f}B'
            elif value >= 1e6:
                return f'${value/1e6:.1f}M'
            else:
                return f'${value/1e3:.1f}K'
                
        for x, y in zip(df['date'], df['revenue']):
            plt.text(x, y, format_currency(y), 
                    fontsize=8, ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        # 2. 利润率趋势
        plt.subplot(3, 2, 2)
        plt.plot(df['date'], df['gross_profit_margin']*100, 'g-s', label='Gross Margin')
        plt.plot(df['date'], df['operating_margin']*100, 'b-o', label='Operating Margin')
        plt.plot(df['date'], df['net_margin']*100, 'r-^', label='Net Margin')
        plt.title('Profitability Trends', fontsize=12, pad=20)
        plt.xlabel('Date', fontsize=10)
        plt.ylabel('Percentage (%)', fontsize=10)
        plt.legend(loc='best', fontsize=8)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 添加利润率数据标签
        for x, y in zip(df['date'], df['gross_profit_margin']*100):
            plt.text(x, y, f'{y:.1f}%', fontsize=8, ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        for x, y in zip(df['date'], df['operating_margin']*100):
            plt.text(x, y, f'{y:.1f}%', fontsize=8, ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        for x, y in zip(df['date'], df['net_margin']*100):
            plt.text(x, y, f'{y:.1f}%', fontsize=8, ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        # 3. 运营效率
        plt.subplot(3, 2, 3)
        plt.bar(df['date'], df['operatingIncome'], width=0.4, label='Operating Income')
        plt.bar(df['date'], df['netIncome'], width=0.4, label='Net Income', alpha=0.7)
        plt.title('Operating vs Net Income', fontsize=12, pad=20)
        plt.xlabel('Date', fontsize=10)
        plt.ylabel('Income (Millions USD)', fontsize=10)
        plt.legend(loc='best', fontsize=8)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 添加运营效率数据标签
        for x, y in zip(df['date'], df['operatingIncome']):
            plt.text(x, y, format_currency(y), 
                    fontsize=8, ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        for x, y in zip(df['date'], df['netIncome']):
            plt.text(x, y, format_currency(y), 
                    fontsize=8, ha='center', va='top',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        # 4. 估值指标
        plt.subplot(3, 2, 4)
        df['pe_ratio'] = df['marketCap'] / df['netIncome']
        df['pb_ratio'] = df['marketCap'] / df['totalStockholdersEquity']
        plt.plot(df['date'], df['pe_ratio'], 'm-*', label='P/E Ratio')
        plt.plot(df['date'], df['pb_ratio'], 'c-D', label='P/B Ratio')
        plt.title('Valuation Ratios', fontsize=12, pad=20)
        plt.xlabel('Date', fontsize=10)
        plt.ylabel('Ratio', fontsize=10)
        plt.legend(loc='best', fontsize=8)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 添加估值指标数据标签
        for x, y in zip(df['date'], df['pe_ratio']):
            plt.text(x, y, f'{y:.1f}x', 
                    fontsize=8, ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        for x, y in zip(df['date'], df['pb_ratio']):
            plt.text(x, y, f'{y:.1f}x', 
                    fontsize=8, ha='center', va='top',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        # 5. 杜邦分析
        plt.subplot(3, 2, 5)
        df['dupont_roe'] = df['net_margin'] * df['asset_turnover'] * (1 + df['totalLiabilities']/df['totalStockholdersEquity'])
        plt.plot(df['date'], df['dupont_roe']*100, 'k-p', label='ROE')
        plt.title('DuPont ROE Analysis', fontsize=12, pad=20)
        plt.xlabel('Date', fontsize=10)
        plt.ylabel('ROE (%)', fontsize=10)
        plt.legend(loc='best', fontsize=8)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 添加杜邦分析数据标签
        for x, y in zip(df['date'], df['dupont_roe']*100):
            plt.text(x, y, f'{y:.1f}%', 
                    fontsize=8, ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        # 6. DCF估值分析
        plt.subplot(3, 2, 6)
        
        # 获取DCF估值数据
        valuation = analyze_valuation(df.to_dict('records'))
        dcf = valuation['dcf_valuation']
        
        # 绘制DCF估值图表
        years = list(range(1, dcf['forecast_years'] + 1))
        plt.bar(years, dcf['forecast_fcf'], color='b', alpha=0.6, label='Forecast FCF')
        plt.plot(years, dcf['discounted_cash_flows'], 'ro-', label='Discounted FCF')
        plt.axhline(dcf['discounted_terminal_value'], color='g', linestyle='--', 
                   label=f'Terminal Value\n({dcf['terminal_growth']*100}% growth)')
        
        plt.title('DCF Valuation', fontsize=12, pad=20)
        plt.xlabel('Year', fontsize=10)
        plt.ylabel('Value (Millions USD)', fontsize=10)
        plt.legend(loc='best', fontsize=8)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 添加DCF数据标签
        for x, y in zip(years, dcf['forecast_fcf']):
            plt.text(x, y, f'${y/1e6:.1f}M', 
                    fontsize=8, ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        for x, y in zip(years, dcf['discounted_cash_flows']):
            plt.text(x, y, f'${y/1e6:.1f}M', 
                    fontsize=8, ha='center', va='top',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        plt.text(dcf['forecast_years'] + 0.5, dcf['discounted_terminal_value'], 
                f'${dcf['discounted_terminal_value']/1e6:.1f}M',
                fontsize=8, ha='left', va='center',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        # 整体布局调整
        plt.suptitle(f'{symbol} Financial Analysis Report\nDCF Intrinsic Value: ${dcf['intrinsic_value']:.2f}', 
                    fontsize=16, y=1.02)
        plt.tight_layout()
        
        # 保存图表
        plot_path = os.path.join(ANALYSIS_DIR, f'{symbol}_analysis.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"成功生成{symbol}分析图表")
    except Exception as e:
        print(f"生成{symbol}图表失败: {str(e)}")

def main():
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='纳斯达克上市公司财报分析')
    parser.add_argument('-s', '--symbols', nargs='+', 
                       help='要分析的公司代码列表，如 AAPL MSFT')
    parser.add_argument('-a', '--all', action='store_true',
                       help='分析所有公司')
    args = parser.parse_args()

    # 创建分析目录
    os.makedirs(ANALYSIS_DIR, exist_ok=True)

    # 获取公司列表
    companies = get_nasdaq_companies()
    if companies is None:
        return

    # 确定要分析的公司
    if args.symbols:
        symbols = [s.upper() for s in args.symbols]
    elif args.all:
        symbols = companies['symbol'].tolist()
    else:
        symbols = companies['symbol'].head(5).tolist()  # 默认前5家

    # 下载并分析财报数据
    for symbol in symbols:
        financials = download_financials(symbol)
        if financials:
            # 保存财报数据
            pd.DataFrame(financials).to_csv(
                os.path.join(ANALYSIS_DIR, f'{symbol}_financials.csv'),
                index=False,
                sep=',',
                encoding='utf-8',
                lineterminator='\n'
            )
            # 分析估值
            analyze_valuation(financials)

if __name__ == '__main__':
    main()
