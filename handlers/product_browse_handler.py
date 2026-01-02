"""
产品浏览和用户行为处理 Lambda 函数
处理产品浏览、搜索、用户行为记录
"""
import json
import boto3
import time
from typing import Dict, Any
from datetime import datetime
from decimal import Decimal

# 初始化 AWS 客户端
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')

# 从环境变量获取表名
import os
PRODUCTS_TABLE = os.environ.get('PRODUCTS_TABLE', 'Products')
USER_ACTIONS_TABLE = os.environ.get('USER_ACTIONS_TABLE', 'UserActions')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'ecommerce-events')

table_products = dynamodb.Table(PRODUCTS_TABLE)
table_user_actions = dynamodb.Table(USER_ACTIONS_TABLE)

def decimal_default(obj):
    """处理 Decimal 类型序列化"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_products(event: Dict, context: Any) -> Dict:
    """获取产品列表（支持分页和筛选）"""
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
    
    try:
        query_params = event.get('queryStringParameters') or {}
        category = query_params.get('category')
        page = int(query_params.get('page', 1))
        limit = int(query_params.get('limit', 20))
        
        # 扫描产品表
        if category:
            # 按类别筛选
            response = table_products.scan(
                FilterExpression='category = :cat',
                ExpressionAttributeValues={
                    ':cat': category
                }
            )
        else:
            response = table_products.scan()
        
        products = response.get('Items', [])
        
        # 分页
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_products = products[start_idx:end_idx]
        
        # 格式化产品数据
        formatted_products = []
        for product in paginated_products:
            formatted_products.append({
                'product_id': product.get('product_id'),
                'product_name': product.get('product_name'),
                'category': product.get('category', ''),
                'price': float(product.get('price', 0)),
                'rating': float(product.get('rating', 0)),
                'image_url': product.get('image_url', ''),
                'description': product.get('description', '')
            })
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'data': formatted_products,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': len(products),
                    'total_pages': (len(products) + limit - 1) // limit
                }
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"获取产品列表错误: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def get_product_detail(event: Dict, context: Any) -> Dict:
    """获取产品详情"""
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
    
    try:
        path_params = event.get('pathParameters') or {}
        product_id = path_params.get('product_id')
        
        if not product_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': '缺少 product_id 参数'})
            }
        
        response = table_products.get_item(
            Key={'product_id': product_id}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': '产品不存在'})
            }
        
        product = response['Item']
        formatted_product = {
            'product_id': product.get('product_id'),
            'product_name': product.get('product_name'),
            'category': product.get('category', ''),
            'price': float(product.get('price', 0)),
            'rating': float(product.get('rating', 0)),
            'image_url': product.get('image_url', ''),
            'description': product.get('description', ''),
            'tags': product.get('tags', '')
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'data': formatted_product
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"获取产品详情错误: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def record_user_action(event: Dict, context: Any) -> Dict:
    """
    记录用户行为（浏览、点击、搜索等）
    写入 DynamoDB 并发布事件到 EventBridge
    """
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'OK'})
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        action_type = body.get('action_type')  # view, click, search, add_to_cart
        product_id = body.get('product_id')
        metadata = body.get('metadata', {})
        
        if not user_id or not action_type:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': '缺少必要参数: user_id 和 action_type'})
            }
        
        # 记录到 DynamoDB
        action_id = f"{user_id}_{int(time.time() * 1000)}"
        action_data = {
            'action_id': action_id,
            'user_id': user_id,
            'action_type': action_type,
            'product_id': product_id,
            'metadata': metadata,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        table_user_actions.put_item(Item=action_data)
        
        # 发布事件到 EventBridge
        eventbridge.put_events(
            Entries=[
                {
                    'Source': 'ecommerce.user-actions',
                    'DetailType': 'User Action',
                    'Detail': json.dumps({
                        'user_id': user_id,
                        'action_type': action_type,
                        'product_id': product_id,
                        'timestamp': action_data['timestamp']
                    }),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'action_id': action_id,
                'message': '用户行为已记录'
            })
        }
        
    except Exception as e:
        print(f"记录用户行为错误: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

