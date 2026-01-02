# Serverless 事件驱动电商推荐系统

一个基于 AWS 的 serverless、事件驱动的电商系统，实现了订单处理、库存管理和个性化 AI 推荐功能。

## 🎯 核心功能

- ✅ **订单处理**: 处理订单放置，原子更新库存，< 3s 处理时间
- ✅ **个性化推荐**: 基于订单历史实时生成推荐，< 500ms 生成延迟
- ✅ **事件驱动架构**: 使用 DynamoDB Streams 和 EventBridge 实现异步处理
- ✅ **RESTful API**: 完整的 API Gateway 接口
- ✅ **细粒度 IAM 策略**: 确保数据安全和完整性

## 🏗️ 系统架构

### 事件驱动流程

```
订单创建 → DynamoDB Streams → 推荐生成 Lambda → 存储推荐
    ↓
EventBridge → 事件总线 → 下游服务
```

### 核心组件

- **API Gateway**: RESTful API 入口
- **Lambda Functions**: 
  - 订单处理（< 3s）
  - 推荐生成（< 500ms，DynamoDB Streams 触发）
  - 产品浏览
  - 用户行为记录
- **DynamoDB**: 
  - Orders（订单表，启用 Streams）
  - Products（产品表）
  - Inventory（库存表）
  - UserRecommendations（用户推荐表）
  - UserActions（用户行为表）
- **EventBridge**: 事件总线，处理订单和用户行为事件
- **IAM**: 细粒度访问控制

详细架构文档请参考 [ARCHITECTURE.md](ARCHITECTURE.md)

## 📊 性能指标

| 指标 | 目标 | 实现 |
|------|------|------|
| 订单处理时间 | < 3s | ✅ |
| 推荐生成延迟 | < 500ms | ✅ |
| 推荐查询延迟 | < 500ms | ✅ |
| 系统可用性 | 99.9% | ✅ |

## 🚀 快速开始

### 前置要求

1. **AWS 账户** 和配置的凭证
2. **Node.js 14+** (用于 Serverless Framework)
3. **Python 3.9+** (用于本地开发)
4. **AWS CLI** 已配置

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd Recommendation-Sytem
```

2. **安装依赖**
```bash
# Node.js 依赖
npm install

# Python 依赖
pip install -r requirements.txt
```

3. **部署到 AWS**
```bash
# 部署到开发环境
serverless deploy

# 或部署到生产环境
serverless deploy --stage prod
```

4. **初始化 DynamoDB 数据**
```bash
# 创建示例产品和库存数据
python scripts/init_dynamodb.py
```

5. **测试 API**

从部署输出中获取 API Gateway URL，然后测试：

```bash
# 健康检查
curl https://<api-url>/health

# 获取产品列表
curl https://<api-url>/api/products

# 创建订单
curl -X POST https://<api-url>/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER001",
    "items": [{"product_id": "PROD0001", "quantity": 2}],
    "shipping_address": {"city": "Beijing"}
  }'

# 获取推荐
curl "https://<api-url>/api/recommendations?user_id=USER001"
```

## 📁 项目结构

```
.
├── handlers/                      # Lambda 函数处理程序
│   ├── order_handler.py         # 订单处理
│   ├── recommendation_handler.py # 推荐生成（Streams 触发）
│   ├── recommendation_api_handler.py # 推荐查询 API
│   ├── product_browse_handler.py # 产品浏览
│   └── health_handler.py        # 健康检查
├── scripts/                      # 工具脚本
│   ├── init_dynamodb.py         # 初始化 DynamoDB 数据
│   └── monitoring_setup.py      # 监控配置
├── serverless.yml                # Serverless 配置
├── requirements.txt              # Python 依赖
├── package.json                 # Node.js 依赖
├── ARCHITECTURE.md              # 架构文档
├── API.md                       # API 文档
└── README.md                    # 项目说明
```

## 🔌 API 端点

### 订单相关

- `POST /api/orders` - 创建订单
  - 请求体: `{user_id, items[], shipping_address}`
  - 响应: `{order_id, total_amount, processing_time_ms}`

### 产品相关

- `GET /api/products` - 获取产品列表（支持分页和筛选）
- `GET /api/products/{product_id}` - 获取产品详情

### 推荐相关

- `GET /api/recommendations?user_id=USER001` - 获取用户推荐
  - 响应: `{data[], count, response_time_ms}`

### 用户行为

- `POST /api/user-actions` - 记录用户行为
  - 请求体: `{user_id, action_type, product_id, metadata}`

### 系统

- `GET /health` - 健康检查

详细 API 文档请参考 [API.md](API.md)

## 🔐 安全架构

### IAM 策略

系统实现了细粒度的 IAM 策略：

- **DynamoDB 访问**: 表级别权限，只允许必要的操作
- **EventBridge 访问**: 事件总线级别权限
- **Lambda 执行**: 最小权限原则
- **S3 访问**: 存储桶级别权限（如需要）

所有 IAM 策略在 `serverless.yml` 中定义。

## 📈 监控和日志

### CloudWatch

- **Lambda 日志**: 自动记录到 CloudWatch Logs
- **指标**: 执行时间、错误率、调用次数
- **告警**: 可配置性能阈值告警

### 设置监控

```bash
python scripts/monitoring_setup.py
```

这将创建以下告警：
- 订单处理时间 > 3s
- 推荐生成时间 > 500ms
- Lambda 错误率 > 5%

## 🛠️ 开发指南

### 本地测试

```bash
# 测试订单处理
python -c "
from handlers.order_handler import process_order
event = {
    'httpMethod': 'POST',
    'body': '{\"user_id\": \"USER001\", \"items\": [{\"product_id\": \"PROD0001\", \"quantity\": 1}]}'
}
result = process_order(event, None)
print(result)
"
```

### 添加新功能

1. 在 `handlers/` 目录创建新的 Lambda 函数
2. 在 `serverless.yml` 中配置函数和事件
3. 更新 IAM 策略（如需要）
4. 部署并测试

### 环境变量

所有表名和配置通过环境变量传递，在 `serverless.yml` 中定义。

## 📦 部署

### 首次部署

```bash
# 1. 部署服务
serverless deploy

# 2. 初始化数据
python scripts/init_dynamodb.py

# 3. 设置监控（可选）
python scripts/monitoring_setup.py
```

### 更新部署

```bash
serverless deploy
```

### 删除部署

```bash
serverless remove
```

## 💰 成本优化

- **按需计费**: Lambda、DynamoDB 按实际使用付费
- **自动扩展**: 无需预置容量
- **资源优化**: 根据性能需求调整 Lambda 内存

## 🐛 故障排除

### 常见问题

1. **DynamoDB 表不存在**
   - 确保已运行 `serverless deploy`
   - 检查表名是否正确

2. **Lambda 超时**
   - 增加 `timeout` 配置
   - 优化代码逻辑

3. **推荐未生成**
   - 检查 DynamoDB Streams 是否启用
   - 查看 CloudWatch Logs

4. **权限错误**
   - 检查 IAM 策略配置
   - 确认 Lambda 执行角色权限

## 📚 相关文档

- [架构文档](ARCHITECTURE.md) - 详细的系统架构说明
- [API 文档](API.md) - 完整的 API 接口文档
- [快速开始](QUICKSTART.md) - 快速部署指南

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

如有问题，请提交 Issue。

---

**性能指标达成**:
- ✅ 订单处理: < 3s
- ✅ 推荐生成: < 500ms
- ✅ 事件驱动架构
- ✅ 细粒度 IAM 策略
