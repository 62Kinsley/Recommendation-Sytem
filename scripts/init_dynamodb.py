"""
初始化 DynamoDB 表数据
创建示例产品和库存数据
"""
import boto3
import json
from decimal import Decimal
from create_sample_data import products_data

# 初始化 DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')

def init_products_table():
    """初始化产品表"""
    table_name = 'ecommerce-recommendation-system-products-dev'
    table = dynamodb.Table(table_name)
    
    print(f"正在初始化产品表: {table_name}")
    
    # 从 products_data 创建产品
    for i, product_name in enumerate(products_data['product_name'], 1):
        product_id = products_data['product_id'][i-1]
        
        item = {
            'product_id': product_id,
            'product_name': product_name,
            'category': products_data['category'][i-1],
            'price': Decimal(str(products_data['price'][i-1])),
            'rating': Decimal(str(products_data['rating'][i-1])),
            'description': products_data['description'][i-1],
            'tags': products_data['tags'][i-1],
            'image_url': products_data['image_url'][i-1]
        }
        
        table.put_item(Item=item)
        print(f"已添加产品: {product_id} - {product_name}")
    
    print(f"产品表初始化完成，共 {len(products_data['product_id'])} 个产品")

def init_inventory_table():
    """初始化库存表"""
    table_name = 'ecommerce-recommendation-system-inventory-dev'
    table = dynamodb.Table(table_name)
    
    print(f"正在初始化库存表: {table_name}")
    
    # 为每个产品创建库存记录
    for product_id in products_data['product_id']:
        # 随机库存数量（10-1000）
        import random
        quantity = random.randint(10, 1000)
        
        item = {
            'product_id': product_id,
            'quantity': quantity,
            'last_updated': '2024-01-01T00:00:00'
        }
        
        table.put_item(Item=item)
        print(f"已添加库存: {product_id} - 数量: {quantity}")
    
    print(f"库存表初始化完成，共 {len(products_data['product_id'])} 条记录")

if __name__ == '__main__':
    print("=" * 50)
    print("初始化 DynamoDB 表数据")
    print("=" * 50)
    print()
    
    try:
        init_products_table()
        print()
        init_inventory_table()
        print()
        print("=" * 50)
        print("初始化完成！")
        print("=" * 50)
    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()

