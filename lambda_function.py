import json
import pickle
import os
import boto3
from typing import Dict, List, Any
import numpy as np
import pandas as pd

# 初始化 S3 客户端（用于从 S3 加载模型，可选）
s3_client = boto3.client('s3')

# 全局变量存储模型（Lambda 容器复用）
similarity_matrix = None
products_df = None

def load_models():
    """加载推荐模型和产品数据"""
    global similarity_matrix, products_df
    
    if similarity_matrix is None or products_df is None:
        try:
            # 从本地文件加载（部署时模型文件会打包到 Lambda）
            model_bucket = os.environ.get('MODEL_BUCKET', '')
            
            if model_bucket:
                # 从 S3 加载模型
                try:
                    s3_client.download_file(model_bucket, 'models/similarity.pkl', '/tmp/similarity.pkl')
                    s3_client.download_file(model_bucket, 'models/products.pkl', '/tmp/products.pkl')
                    similarity_matrix = pickle.load(open('/tmp/similarity.pkl', 'rb'))
                    products_df = pickle.load(open('/tmp/products.pkl', 'rb'))
                except Exception as s3_error:
                    print(f"从 S3 加载模型失败: {s3_error}")
                    # 尝试从本地加载（如果模型已打包）
                    try:
                        similarity_matrix = pickle.load(open('models/similarity.pkl', 'rb'))
                        products_df = pickle.load(open('models/products.pkl', 'rb'))
                    except:
                        raise s3_error
            else:
                # 从本地文件加载（用于开发和测试）
                similarity_matrix = pickle.load(open('models/similarity.pkl', 'rb'))
                products_df = pickle.load(open('models/products.pkl', 'rb'))
                
        except FileNotFoundError as e:
            error_msg = f"模型文件未找到: {e}. 请确保模型文件已上传到 S3 或包含在部署包中"
            print(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"加载模型错误: {e}"
            print(error_msg)
            raise Exception(error_msg)

def recommend_products(product_id: str = None, product_name: str = None, limit: int = 6) -> List[Dict[str, Any]]:
    """
    推荐相似产品
    
    Args:
        product_id: 产品ID
        product_name: 产品名称
        limit: 返回推荐数量
    
    Returns:
        推荐产品列表
    """
    global similarity_matrix, products_df
    
    if similarity_matrix is None or products_df is None:
        load_models()
    
    # 根据 product_id 或 product_name 查找产品
    if product_id:
        if product_id not in products_df['product_id'].values:
            return []
        index = products_df[products_df['product_id'] == product_id].index[0]
    elif product_name:
        if product_name not in products_df['product_name'].values:
            return []
        index = products_df[products_df['product_name'] == product_name].index[0]
    else:
        return []
    
    try:
        # 计算相似度并排序
        distances = sorted(
            list(enumerate(similarity_matrix[index])), 
            reverse=True, 
            key=lambda x: x[1]
        )
        
        # 获取推荐产品
        recommended_products = []
        for i in distances[1:limit+1]:
            product = products_df.iloc[i[0]]
            recommended_products.append({
                'product_id': str(product['product_id']),
                'product_name': product['product_name'],
                'price': float(product['price']) if 'price' in product else None,
                'image_url': product.get('image_url', ''),
                'category': product.get('category', ''),
                'rating': float(product.get('rating', 0)) if 'rating' in product else None,
                'similarity_score': float(i[1])
            })
        
        return recommended_products
    except Exception as e:
        print(f"推荐过程错误: {e}")
        return []

def get_all_products() -> List[Dict[str, Any]]:
    """获取所有产品列表"""
    global products_df
    
    if products_df is None:
        load_models()
    
    return products_df[['product_id', 'product_name', 'price', 'image_url', 'category', 'rating']].to_dict('records')

def lambda_handler(event: Dict, context: Any) -> Dict:
    """
    AWS Lambda 处理函数
    
    API Gateway 事件格式:
    {
        "httpMethod": "GET" | "POST",
        "path": "/recommend",
        "queryStringParameters": {...},
        "body": "..."
    }
    """
    # 加载模型（首次调用时）
    try:
        load_models()
    except Exception as e:
        # 如果模型加载失败，返回错误响应
        return {
            'statusCode': 503,
            'headers': headers,
            'body': json.dumps({
                'error': '服务暂时不可用',
                'message': '模型文件未加载，请检查模型文件是否正确部署',
                'details': str(e)
            }, ensure_ascii=False)
        }
    
    # 解析请求
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    query_params = event.get('queryStringParameters') or {}
    body = event.get('body', '{}')
    
    # 解析请求体（如果是 POST）
    if http_method == 'POST' and body:
        try:
            if isinstance(body, str):
                body = json.loads(body)
        except:
            body = {}
    
    # 设置 CORS 头
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }
    
    # 处理 OPTIONS 请求（CORS 预检）
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'OK'})
        }
    
    try:
        # 路由处理
        if path == '/recommend' or path == '/api/recommend':
            # 获取推荐
            product_id = query_params.get('product_id') or body.get('product_id')
            product_name = query_params.get('product_name') or body.get('product_name')
            limit = int(query_params.get('limit', body.get('limit', 6)))
            
            if not product_id and not product_name:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'error': '请提供 product_id 或 product_name 参数'
                    })
                }
            
            recommendations = recommend_products(
                product_id=product_id,
                product_name=product_name,
                limit=limit
            )
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'data': recommendations,
                    'count': len(recommendations)
                }, ensure_ascii=False)
            }
        
        elif path == '/products' or path == '/api/products':
            # 获取所有产品
            products = get_all_products()
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'data': products,
                    'count': len(products)
                }, ensure_ascii=False)
            }
        
        elif path == '/health' or path == '/':
            # 健康检查
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'status': 'healthy',
                    'service': 'E-commerce Recommendation System',
                    'version': '1.0.0'
                })
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'error': '路径不存在',
                    'available_paths': ['/recommend', '/products', '/health']
                })
            }
    
    except Exception as e:
        print(f"处理请求错误: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': '服务器内部错误',
                'message': str(e)
            })
        }

