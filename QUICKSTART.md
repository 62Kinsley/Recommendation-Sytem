# 快速开始指南

## 5 分钟快速部署

### 步骤 1: 准备环境

```bash
# 安装 Node.js 依赖
npm install

# 安装 Python 依赖
pip install -r requirements.txt
```

### 步骤 2: 创建数据和训练模型

```bash
# 创建示例产品数据
python create_sample_data.py

# 训练推荐模型
python train_model.py
```

### 步骤 3: 配置 AWS

```bash
# 配置 AWS 凭证
aws configure
```

需要提供：
- AWS Access Key ID
- AWS Secret Access Key
- 默认区域（如：ap-northeast-1）
- 输出格式（json）

### 步骤 4: 部署

```bash
# 方式1: 使用部署脚本（推荐）
./deploy.sh

# 方式2: 手动部署
npm run deploy
```

### 步骤 5: 上传模型

部署完成后，从输出中获取 S3 存储桶名称，然后上传模型：

```bash
# 替换 <bucket-name> 为实际的存储桶名称
aws s3 cp models/ s3://<bucket-name>/models/ --recursive
```

### 步骤 6: 测试 API

从部署输出中获取 API Gateway URL，然后测试：

```bash
# 健康检查
curl https://<your-api-url>/health

# 获取推荐
curl "https://<your-api-url>/api/recommend?product_id=PROD0001&limit=6"
```

## 本地测试

在部署前，可以先在本地测试：

```bash
python test_local.py
```

## 常见问题

### Q: 部署失败，提示权限不足
A: 检查 AWS IAM 权限，确保有以下权限：
- Lambda 相关权限
- S3 相关权限
- API Gateway 权限
- CloudFormation 权限

### Q: 模型文件太大，上传失败
A: 可以：
1. 减少产品数量
2. 使用 Lambda Layers 存储大型依赖
3. 优化模型参数（减少特征数量）

### Q: Lambda 函数超时
A: 在 `serverless.yml` 中增加 `timeout` 值，或优化模型加载逻辑。

## 下一步

- 查看 [API.md](API.md) 了解完整的 API 文档
- 查看 [README.md](README.md) 了解详细配置
- 根据实际需求修改推荐算法

