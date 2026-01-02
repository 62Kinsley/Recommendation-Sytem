"""
推荐 API Lambda 函数
从 UserRecommendations 表获取用户的个性化推荐
"""
import json
import boto3
import time
from typing import Dict, Any
from decimal import Decimal

# 初始化 AWS 客户端
dynamodb = boto3.resource('dynamodb')

# 从环境变量获取表名
import os
RECOMMENDATIONS_TABLE = os.environ.get('RECOMMENDATIONS_TABLE', 'UserRecommendations')

table_recommendations = dynamodb.Table(RECOMMENDATIONS_TABLE)

def decimal_default(obj):
    """处理 Decimal 类型序列化"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_user_recommendations(event: Dict, context: Any) -> Dict:
    """
    获取用户的个性化推荐
    
    GET /api/recommendations?user_id=USER001
    """
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'OK'})
        }
    
    start_time = time.time()
    
    try:
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': '缺少 user_id 参数'})
            }
        
        # 从 DynamoDB 获取推荐
        response = table_recommendations.get_item(
            Key={'user_id': user_id}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'error': '未找到该用户的推荐',
                    'message': '推荐可能正在生成中，请稍后重试'
                })
            }
        
        item = response['Item']
        recommendations = item.get('recommendations', [])
        generated_at = item.get('generated_at', 0)
        
        # 计算响应时间
        response_time = (time.time() - start_time) * 1000
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'data': recommendations,
                'count': len(recommendations),
                'generated_at': generated_at,
                'response_time_ms': round(response_time, 2)
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"获取推荐错误: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

