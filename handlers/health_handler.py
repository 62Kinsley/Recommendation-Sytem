"""
健康检查 Lambda 函数
"""
import json
from typing import Dict, Any

def health_check(event: Dict, context: Any) -> Dict:
    """健康检查端点"""
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
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'status': 'healthy',
            'service': 'E-commerce Recommendation System',
            'version': '2.0.0',
            'architecture': 'serverless event-driven'
        })
    }

