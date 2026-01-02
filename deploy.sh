#!/bin/bash

# Serverless 电商推荐系统部署脚本

set -e

echo "=========================================="
echo "Serverless 电商推荐系统部署"
echo "=========================================="
echo ""

# 检查是否安装了 Node.js
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node.js，请先安装 Node.js"
    exit 1
fi

# 检查是否安装了 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python3"
    exit 1
fi

# 检查是否安装了 AWS CLI
if ! command -v aws &> /dev/null; then
    echo "错误: 未找到 AWS CLI，请先安装 AWS CLI"
    exit 1
fi

# 检查是否配置了 AWS 凭证
if ! aws sts get-caller-identity &> /dev/null; then
    echo "错误: 未配置 AWS 凭证，请运行 'aws configure'"
    exit 1
fi

echo "1. 安装 Node.js 依赖..."
npm install

echo ""
echo "2. 安装 Python 依赖..."
pip3 install -r requirements.txt

echo ""
echo "3. 检查产品数据..."
if [ ! -f "products.csv" ]; then
    echo "   未找到 products.csv，正在创建示例数据..."
    python3 create_sample_data.py
else
    echo "   找到 products.csv"
fi

echo ""
echo "4. 检查模型文件..."
if [ ! -f "models/similarity.pkl" ] || [ ! -f "models/products.pkl" ]; then
    echo "   未找到模型文件，正在训练模型..."
    python3 train_model.py
else
    echo "   找到模型文件"
fi

echo ""
echo "5. 部署到 AWS Lambda..."
npm run deploy

echo ""
echo "6. 获取部署信息..."
DEPLOY_OUTPUT=$(npm run deploy 2>&1)
BUCKET_NAME=$(echo "$DEPLOY_OUTPUT" | grep -oP 'models-\K[^\s]+' | head -1 || echo "")

if [ -z "$BUCKET_NAME" ]; then
    # 从 serverless.yml 获取存储桶名称
    STAGE=${1:-dev}
    BUCKET_NAME="ecommerce-recommendation-system-models-${STAGE}"
fi

echo ""
echo "7. 上传模型文件到 S3..."
echo "   存储桶名称: $BUCKET_NAME"
aws s3 cp models/ s3://$BUCKET_NAME/models/ --recursive

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 从部署输出中获取 API Gateway URL"
echo "2. 使用 API.md 中的文档测试 API"
echo "3. 查看日志: npm run logs"
echo ""

