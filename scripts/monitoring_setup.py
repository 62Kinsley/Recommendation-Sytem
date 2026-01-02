"""
CloudWatch 监控和告警配置
"""
import boto3
import json

cloudwatch = boto3.client('cloudwatch')

def create_alarm(alarm_name, metric_name, namespace, threshold, comparison_operator='GreaterThanThreshold'):
    """创建 CloudWatch 告警"""
    try:
        cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            ComparisonOperator=comparison_operator,
            EvaluationPeriods=1,
            MetricName=metric_name,
            Namespace=namespace,
            Period=60,
            Statistic='Average',
            Threshold=threshold,
            ActionsEnabled=True,
            AlarmDescription=f'监控 {metric_name} 指标'
        )
        print(f"✓ 已创建告警: {alarm_name}")
    except Exception as e:
        print(f"✗ 创建告警失败 {alarm_name}: {e}")

def setup_monitoring():
    """设置监控告警"""
    print("=" * 50)
    print("设置 CloudWatch 监控和告警")
    print("=" * 50)
    print()
    
    # Lambda 函数命名空间
    namespace = 'AWS/Lambda'
    
    # 订单处理性能告警（> 3s）
    create_alarm(
        'ecommerce-order-processing-time',
        'Duration',
        namespace,
        3000,  # 3秒 = 3000毫秒
        comparison_operator='GreaterThanThreshold'
    )
    
    # 推荐生成性能告警（> 500ms）
    create_alarm(
        'ecommerce-recommendation-generation-time',
        'Duration',
        namespace,
        500,  # 500毫秒
        comparison_operator='GreaterThanThreshold'
    )
    
    # Lambda 错误率告警（> 5%）
    create_alarm(
        'ecommerce-lambda-errors',
        'Errors',
        namespace,
        5,  # 5个错误
        comparison_operator='GreaterThanThreshold'
    )
    
    print()
    print("=" * 50)
    print("监控设置完成！")
    print("=" * 50)

if __name__ == '__main__':
    setup_monitoring()

