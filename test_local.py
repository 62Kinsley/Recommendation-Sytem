"""
本地测试 Lambda 函数
"""
import json
from lambda_function import lambda_handler

def test_health_check():
    """测试健康检查端点"""
    print("测试健康检查...")
    event = {
        'httpMethod': 'GET',
        'path': '/health',
        'queryStringParameters': None,
        'body': None
    }
    result = lambda_handler(event, None)
    print(f"状态码: {result['statusCode']}")
    print(f"响应: {json.dumps(json.loads(result['body']), indent=2, ensure_ascii=False)}")
    print()

def test_get_products():
    """测试获取所有产品"""
    print("测试获取所有产品...")
    event = {
        'httpMethod': 'GET',
        'path': '/api/products',
        'queryStringParameters': None,
        'body': None
    }
    result = lambda_handler(event, None)
    print(f"状态码: {result['statusCode']}")
    response = json.loads(result['body'])
    print(f"产品数量: {response.get('count', 0)}")
    if response.get('data'):
        print(f"前3个产品:")
        for product in response['data'][:3]:
            print(f"  - {product.get('product_name')} (ID: {product.get('product_id')})")
    print()

def test_recommend_by_id():
    """测试通过产品ID获取推荐"""
    print("测试通过产品ID获取推荐...")
    event = {
        'httpMethod': 'GET',
        'path': '/api/recommend',
        'queryStringParameters': {
            'product_id': 'PROD0001',
            'limit': '6'
        },
        'body': None
    }
    result = lambda_handler(event, None)
    print(f"状态码: {result['statusCode']}")
    response = json.loads(result['body'])
    if response.get('success'):
        print(f"推荐数量: {response.get('count', 0)}")
        print("推荐产品:")
        for product in response.get('data', [])[:3]:
            print(f"  - {product.get('product_name')} (相似度: {product.get('similarity_score', 0):.2f})")
    else:
        print(f"错误: {response.get('error')}")
    print()

def test_recommend_by_name():
    """测试通过产品名称获取推荐"""
    print("测试通过产品名称获取推荐...")
    event = {
        'httpMethod': 'POST',
        'path': '/api/recommend',
        'queryStringParameters': None,
        'body': json.dumps({
            'product_name': '无线蓝牙耳机',
            'limit': 6
        })
    }
    result = lambda_handler(event, None)
    print(f"状态码: {result['statusCode']}")
    response = json.loads(result['body'])
    if response.get('success'):
        print(f"推荐数量: {response.get('count', 0)}")
        print("推荐产品:")
        for product in response.get('data', [])[:3]:
            print(f"  - {product.get('product_name')} (相似度: {product.get('similarity_score', 0):.2f})")
    else:
        print(f"错误: {response.get('error')}")
    print()

def test_error_handling():
    """测试错误处理"""
    print("测试错误处理（缺少参数）...")
    event = {
        'httpMethod': 'GET',
        'path': '/api/recommend',
        'queryStringParameters': None,
        'body': None
    }
    result = lambda_handler(event, None)
    print(f"状态码: {result['statusCode']}")
    response = json.loads(result['body'])
    print(f"错误信息: {response.get('error')}")
    print()

if __name__ == '__main__':
    print("=" * 50)
    print("Lambda 函数本地测试")
    print("=" * 50)
    print()
    
    try:
        test_health_check()
        test_get_products()
        test_recommend_by_id()
        test_recommend_by_name()
        test_error_handling()
        
        print("=" * 50)
        print("所有测试完成！")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

