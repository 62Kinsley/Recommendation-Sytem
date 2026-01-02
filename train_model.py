"""
电商推荐系统模型训练脚本
用于生成产品相似度矩阵
"""
import pandas as pd
import numpy as np
import pickle
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem.porter import PorterStemmer
import nltk

# 下载必要的 NLTK 数据
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

ps = PorterStemmer()

def stem(text):
    """词干提取"""
    if pd.isna(text):
        return ""
    y = []
    for i in str(text).split():
        y.append(ps.stem(i))
    return " ".join(y)

def prepare_data(df):
    """准备数据用于训练"""
    # 创建标签组合（产品名称 + 类别 + 描述 + 标签）
    df['tags'] = (
        df['product_name'].fillna('') + ' ' +
        df['category'].fillna('') + ' ' +
        df['description'].fillna('') + ' ' +
        df['tags'].fillna('')
    )
    
    # 转换为小写
    df['tags'] = df['tags'].str.lower()
    
    # 词干提取
    df['tags'] = df['tags'].apply(stem)
    
    return df

def train_model(products_file='products.csv', output_dir='models'):
    """训练推荐模型"""
    print("正在加载产品数据...")
    df = pd.read_csv(products_file)
    
    print(f"数据形状: {df.shape}")
    print(f"列名: {df.columns.tolist()}")
    
    # 准备数据
    print("正在准备数据...")
    df = prepare_data(df)
    
    # 特征提取
    print("正在提取特征...")
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vectors = cv.fit_transform(df['tags']).toarray()
    
    # 计算相似度矩阵
    print("正在计算相似度矩阵...")
    similarity = cosine_similarity(vectors)
    
    # 保存模型
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"正在保存模型到 {output_dir}...")
    pickle.dump(similarity, open(f'{output_dir}/similarity.pkl', 'wb'))
    pickle.dump(df[['product_id', 'product_name', 'price', 'image_url', 'category', 'rating', 'description']], 
                open(f'{output_dir}/products.pkl', 'wb'))
    
    print("模型训练完成！")
    print(f"相似度矩阵形状: {similarity.shape}")
    print(f"产品数量: {len(df)}")
    
    return similarity, df

if __name__ == '__main__':
    # 检查产品数据文件是否存在
    if not os.path.exists('products.csv'):
        print("错误: 找不到 products.csv 文件")
        print("请先创建产品数据文件")
    else:
        train_model()

