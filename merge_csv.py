import os
import pandas as pd

# 定义分析目录
analysis_dir = 'analysis/'

# 获取所有CSV文件路径（包括隐藏文件）
csv_files = [f for f in os.listdir(analysis_dir) if f.endswith('.csv')]

# 初始化一个空的DataFrame来存储合并后的数据
merged_df = pd.DataFrame()

# 读取每个CSV文件并将其内容加载到DataFrame中
for csv_file in csv_files:
    file_path = os.path.join(analysis_dir, csv_file)
    df = pd.read_csv(file_path, encoding='latin1')
    merged_df = pd.concat([merged_df, df], ignore_index=True)

# 将合并后的DataFrame保存为一个新的CSV文件
output_file = 'all_companies_financials.csv'
merged_df.to_csv(output_file, index=False, sep=',', encoding='utf-8', lineterminator='\n')
