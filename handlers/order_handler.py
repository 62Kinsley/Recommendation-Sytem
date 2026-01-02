"""
订单处理 Lambda 函数
处理订单放置、更新库存、发布事件到 EventBridge
目标：< 3s 订单处理时间
"""
import json
import os
import boto3
import time
from datetime import datetime
from typing import Dict, Any
from decimal import Decimal

# 初始化 AWS 客户端
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')

# 从环境变量获取表名
ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'Orders')
PRODUCTS_TABLE = os.environ.get('PRODUCTS_TABLE', 'Products')
INVENTORY_TABLE = os.environ.get('INVENTORY_TABLE', 'Inventory')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'ecommerce-events')

table_orders = dynamodb.Table(ORDERS_TABLE)
table_inventory = dynamodb.Table(INVENTORY_TABLE)
table_products = dynamodb.Table(PRODUCTS_TABLE)

def decimal_default(obj):
    """处理 Decimal 类型序列化"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def process_order(event: Dict, context: Any) -> Dict:
    """
    处理订单请求
    
    API Gateway 事件格式:
    {
        "httpMethod": "POST",
        "body": {
            "user_id": "USER001",
            "items": [
                {"product_id": "PROD001", "quantity": 2}
            ],
            "shipping_address": {...}
        }
    }
    """
    start_time = time.time()
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    # 处理 OPTIONS 请求
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'OK'})
        }
    
    try:
        # 解析请求体
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        items = body.get('items', [])
        shipping_address = body.get('shipping_address', {})
        
        if not user_id or not items:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': '缺少必要参数: user_id 和 items'})
            }
        
        # 生成订单ID
        order_id = f"ORD{int(time.time() * 1000)}"
        order_timestamp = datetime.utcnow().isoformat()
        
        # 1. 验证库存并计算总价
        total_amount = 0
        order_items = []
        
        for item in items:
            product_id = item.get('product_id')
            quantity = int(item.get('quantity', 1))
            
            # 获取产品信息
            product_response = table_products.get_item(
                Key={'product_id': product_id}
            )
            
            if 'Item' not in product_response:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': f'产品不存在: {product_id}'})
                }
            
            product = product_response['Item']
            price = float(product.get('price', 0))
            
            # 检查并更新库存（原子操作）
            try:
                inventory_response = table_inventory.update_item(
                    Key={'product_id': product_id},
                    UpdateExpression='SET quantity = quantity - :qty, last_updated = :ts',
                    ConditionExpression='quantity >= :qty',
                    ExpressionAttributeValues={
                        ':qty': quantity,
                        ':ts': order_timestamp
                    },
                    ReturnValues='ALL_NEW'
                )
                
                current_stock = inventory_response['Attributes']['quantity']
                
            except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': f'库存不足: {product_id}'})
                }
            
            item_total = price * quantity
            total_amount += item_total
            
            order_items.append({
                'product_id': product_id,
                'product_name': product.get('product_name'),
                'quantity': quantity,
                'price': price,
                'subtotal': item_total
            })
        
        # 2. 创建订单记录（写入 DynamoDB）
        order_data = {
            'order_id': order_id,
            'user_id': user_id,
            'items': order_items,
            'total_amount': Decimal(str(total_amount)),
            'status': 'pending',
            'shipping_address': shipping_address,
            'created_at': order_timestamp,
            'updated_at': order_timestamp
        }
        
        table_orders.put_item(Item=order_data)
        
        # 3. 发布订单事件到 EventBridge
        event_detail = {
            'order_id': order_id,
            'user_id': user_id,
            'total_amount': total_amount,
            'item_count': len(order_items),
            'timestamp': order_timestamp
        }
        
        eventbridge.put_events(
            Entries=[
                {
                    'Source': 'ecommerce.orders',
                    'DetailType': 'Order Placed',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
        processing_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'order_id': order_id,
                'total_amount': total_amount,
                'processing_time_ms': round(processing_time, 2),
                'message': '订单创建成功'
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"订单处理错误: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': '订单处理失败',
                'message': str(e)
            })
        }

