"""
推荐生成 Lambda 函数
由 DynamoDB Streams 触发，分析订单历史并生成个性化推荐
目标：< 500ms 推荐生成延迟
"""
import json
import boto3
import time
from typing import Dict, Any, List
from decimal import Decimal
from boto3.dynamodb.types import TypeDeserializer

# 初始化 AWS 客户端
dynamodb = boto3.resource('dynamodb')

# 从环境变量获取表名
import os
ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'Orders')
PRODUCTS_TABLE = os.environ.get('PRODUCTS_TABLE', 'Products')
RECOMMENDATIONS_TABLE = os.environ.get('RECOMMENDATIONS_TABLE', 'UserRecommendations')

table_orders = dynamodb.Table(ORDERS_TABLE)
table_products = dynamodb.Table(PRODUCTS_TABLE)
table_recommendations = dynamodb.Table(RECOMMENDATIONS_TABLE)

# DynamoDB 类型反序列化器
deserializer = TypeDeserializer()

def decimal_default(obj):
    """处理 Decimal 类型序列化"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def generate_recommendations(user_id: str) -> List[Dict[str, Any]]:
    """
    基于用户订单历史生成推荐
    
    策略：
    1. 获取用户最近的订单
    2. 分析购买的产品类别
    3. 基于类别相似度推荐产品
    4. 考虑产品评分和价格
    """
    start_time = time.time()
    
    # 1. 获取用户订单历史（最近30天）
    try:
        response = table_orders.query(
            IndexName='user_id-created_at-index',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={
                ':uid': user_id
            },
            Limit=50,
            ScanIndexForward=False  # 按时间倒序
        )
        
        orders = response.get('Items', [])
        
        if not orders:
            # 如果没有订单历史，返回热门产品
            return get_popular_products(limit=6)
        
    except Exception as e:
        print(f"查询订单历史错误: {e}")
        return get_popular_products(limit=6)
    
    # 2. 分析用户购买模式
    purchased_categories = {}
    purchased_products = set()
    
    for order in orders:
        items = order.get('items', [])
        for item in items:
            product_id = item.get('product_id')
            purchased_products.add(product_id)
            
            # 获取产品类别
            try:
                product_response = table_products.get_item(
                    Key={'product_id': product_id}
                )
                if 'Item' in product_response:
                    category = product_response['Item'].get('category', '')
                    if category:
                        purchased_categories[category] = purchased_categories.get(category, 0) + 1
            except:
                pass
    
    # 3. 基于类别相似度推荐产品
    recommendations = []
    
    # 获取所有产品
    try:
        products_response = table_products.scan()
        all_products = products_response.get('Items', [])
        
        # 过滤已购买的产品，按类别匹配和评分排序
        candidate_products = []
        for product in all_products:
            product_id = product.get('product_id')
            if product_id not in purchased_products:
                category = product.get('category', '')
                rating = float(product.get('rating', 0))
                price = float(product.get('price', 0))
                
                # 计算推荐分数
                category_score = purchased_categories.get(category, 0) * 0.5
                rating_score = rating * 0.3
                price_score = (1 / (1 + price / 1000)) * 0.2  # 价格越低分数越高
                
                total_score = category_score + rating_score + price_score
                
                candidate_products.append({
                    'product_id': product_id,
                    'product_name': product.get('product_name'),
                    'category': category,
                    'price': price,
                    'rating': rating,
                    'image_url': product.get('image_url', ''),
                    'score': total_score
                })
        
        # 按分数排序并取前6个
        candidate_products.sort(key=lambda x: x['score'], reverse=True)
        recommendations = candidate_products[:6]
        
    except Exception as e:
        print(f"生成推荐错误: {e}")
        return get_popular_products(limit=6)
    
    generation_time = (time.time() - start_time) * 1000
    
    print(f"推荐生成时间: {generation_time:.2f}ms")
    
    return recommendations

def get_popular_products(limit: int = 6) -> List[Dict[str, Any]]:
    """获取热门产品（作为默认推荐）"""
    try:
        response = table_products.scan()
        products = response.get('Items', [])
        
        # 按评分排序
        sorted_products = sorted(
            products,
            key=lambda x: float(x.get('rating', 0)),
            reverse=True
        )
        
        recommendations = []
        for product in sorted_products[:limit]:
            recommendations.append({
                'product_id': product.get('product_id'),
                'product_name': product.get('product_name'),
                'category': product.get('category', ''),
                'price': float(product.get('price', 0)),
                'rating': float(product.get('rating', 0)),
                'image_url': product.get('image_url', ''),
                'score': float(product.get('rating', 0))
            })
        
        return recommendations
    except Exception as e:
        print(f"获取热门产品错误: {e}")
        return []

def lambda_handler(event: Dict, context: Any) -> Dict:
    """
    处理 DynamoDB Streams 事件
    
    DynamoDB Streams 事件格式:
    {
        "Records": [
            {
                "eventName": "INSERT",
                "dynamodb": {
                    "NewImage": {
                        "user_id": {"S": "USER001"},
                        "order_id": {"S": "ORD123"}
                    }
                }
            }
        ]
    }
    """
    try:
        records = event.get('Records', [])
        
        for record in records:
            # 只处理新订单（INSERT 事件）
            if record.get('eventName') != 'INSERT':
                continue
            
            # 提取订单信息
            new_image = record.get('dynamodb', {}).get('NewImage', {})
            
            # 转换 DynamoDB Streams 格式为 Python 字典
            deserialized_image = {}
            for key, value in new_image.items():
                deserialized_image[key] = deserializer.deserialize(value)
            
            user_id = deserialized_image.get('user_id')
            order_id = deserialized_image.get('order_id')
            
            if not user_id:
                continue
            
            print(f"为新订单生成推荐: order_id={order_id}, user_id={user_id}")
            
            # 生成推荐
            recommendations = generate_recommendations(user_id)
            
            # 存储推荐到 DynamoDB
            recommendation_data = {
                'user_id': user_id,
                'recommendations': recommendations,
                'generated_at': int(time.time()),
                'order_id': order_id  # 关联的订单ID
            }
            
            table_recommendations.put_item(Item=recommendation_data)
            
            print(f"推荐已保存: user_id={user_id}, 推荐数量={len(recommendations)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'success': True, 'processed': len(records)})
        }
        
    except Exception as e:
        print(f"处理推荐生成错误: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

