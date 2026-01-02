# API 文档 - 事件驱动电商推荐系统

## 基础信息

- **服务名称**: E-commerce Recommendation System
- **版本**: 2.0.0
- **架构**: Serverless Event-Driven
- **部署方式**: AWS Lambda + API Gateway

## 性能指标

- **订单处理**: < 3 秒
- **推荐生成**: < 500 毫秒
- **推荐查询**: < 500 毫秒

## API 端点

### 1. 健康检查

检查服务是否正常运行。

**请求**
```
GET /health
```

**响应**
```json
{
  "status": "healthy",
  "service": "E-commerce Recommendation System",
  "version": "2.0.0",
  "architecture": "serverless event-driven"
}
```

---

### 2. 创建订单

创建新订单，自动更新库存并发布事件。

**请求**
```
POST /api/orders
Content-Type: application/json

{
  "user_id": "USER001",
  "items": [
    {
      "product_id": "PROD0001",
      "quantity": 2
    }
  ],
  "shipping_address": {
    "street": "123 Main St",
    "city": "Beijing",
    "postal_code": "100000"
  }
}
```

**响应**
```json
{
  "success": true,
  "order_id": "ORD1234567890",
  "total_amount": 599.98,
  "processing_time_ms": 2450.5,
  "message": "订单创建成功"
}
```

**错误响应**
```json
{
  "error": "库存不足: PROD0001"
}
```

**状态码**
- `200`: 成功
- `400`: 请求参数错误或库存不足
- `404`: 产品不存在
- `500`: 服务器错误

---

### 3. 获取产品列表

获取产品列表，支持分页和类别筛选。

**请求**
```
GET /api/products?category=电子产品&page=1&limit=20
```

**查询参数**
- `category` (可选): 产品类别
- `page` (可选): 页码，默认 1
- `limit` (可选): 每页数量，默认 20

**响应**
```json
{
  "success": true,
  "data": [
    {
      "product_id": "PROD0001",
      "product_name": "无线蓝牙耳机",
      "category": "电子产品",
      "price": 299.99,
      "rating": 4.5,
      "image_url": "https://example.com/image.jpg",
      "description": "高品质无线蓝牙耳机"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

### 4. 获取产品详情

获取单个产品的详细信息。

**请求**
```
GET /api/products/{product_id}
```

**响应**
```json
{
  "success": true,
  "data": {
    "product_id": "PROD0001",
    "product_name": "无线蓝牙耳机",
    "category": "电子产品",
    "price": 299.99,
    "rating": 4.5,
    "image_url": "https://example.com/image.jpg",
    "description": "高品质无线蓝牙耳机",
    "tags": "蓝牙 无线 降噪 音乐"
  }
}
```

---

### 5. 获取用户推荐

获取用户的个性化推荐（从 UserRecommendations 表读取）。

**请求**
```
GET /api/recommendations?user_id=USER001
```

**查询参数**
- `user_id` (必需): 用户ID

**响应**
```json
{
  "success": true,
  "data": [
    {
      "product_id": "PROD0002",
      "product_name": "智能手机",
      "category": "电子产品",
      "price": 2999.99,
      "rating": 4.7,
      "image_url": "https://example.com/image2.jpg",
      "score": 0.85
    }
  ],
  "count": 6,
  "generated_at": 1704067200,
  "response_time_ms": 125.5
}
```

**错误响应**
```json
{
  "error": "未找到该用户的推荐",
  "message": "推荐可能正在生成中，请稍后重试"
}
```

**注意**: 推荐由 DynamoDB Streams 异步生成，首次查询可能需要等待。

---

### 6. 记录用户行为

记录用户行为（浏览、点击、搜索等），写入 DynamoDB 并发布事件。

**请求**
```
POST /api/user-actions
Content-Type: application/json

{
  "user_id": "USER001",
  "action_type": "view",
  "product_id": "PROD0001",
  "metadata": {
    "page": "product_detail",
    "duration": 30
  }
}
```

**请求体参数**
- `user_id` (必需): 用户ID
- `action_type` (必需): 行为类型 (`view`, `click`, `search`, `add_to_cart`)
- `product_id` (可选): 产品ID
- `metadata` (可选): 额外元数据

**响应**
```json
{
  "success": true,
  "action_id": "USER001_1704067200000",
  "message": "用户行为已记录"
}
```

---

## 使用示例

### cURL

```bash
# 健康检查
curl https://your-api-url/health

# 创建订单
curl -X POST https://your-api-url/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER001",
    "items": [{"product_id": "PROD0001", "quantity": 1}],
    "shipping_address": {"city": "Beijing"}
  }'

# 获取产品列表
curl "https://your-api-url/api/products?category=电子产品&page=1"

# 获取推荐
curl "https://your-api-url/api/recommendations?user_id=USER001"

# 记录用户行为
curl -X POST https://your-api-url/api/user-actions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER001",
    "action_type": "view",
    "product_id": "PROD0001"
  }'
```

### Python

```python
import requests

BASE_URL = "https://your-api-url"

# 创建订单
order_data = {
    "user_id": "USER001",
    "items": [{"product_id": "PROD0001", "quantity": 2}],
    "shipping_address": {"city": "Beijing"}
}
response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
order = response.json()
print(f"订单ID: {order['order_id']}")
print(f"处理时间: {order['processing_time_ms']}ms")

# 获取推荐
response = requests.get(f"{BASE_URL}/api/recommendations", 
                       params={"user_id": "USER001"})
recommendations = response.json()['data']
print(f"推荐数量: {len(recommendations)}")
```

### JavaScript

```javascript
const BASE_URL = 'https://your-api-url';

// 创建订单
fetch(`${BASE_URL}/api/orders`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'USER001',
    items: [{ product_id: 'PROD0001', quantity: 2 }],
    shipping_address: { city: 'Beijing' }
  })
})
  .then(res => res.json())
  .then(data => {
    console.log(`订单ID: ${data.order_id}`);
    console.log(`处理时间: ${data.processing_time_ms}ms`);
  });

// 获取推荐
fetch(`${BASE_URL}/api/recommendations?user_id=USER001`)
  .then(res => res.json())
  .then(data => {
    console.log(`推荐数量: ${data.count}`);
    console.log(`响应时间: ${data.response_time_ms}ms`);
  });
```

## 事件流

### 订单创建事件流

1. **客户端** → `POST /api/orders`
2. **Order Handler Lambda**:
   - 验证库存（原子操作）
   - 创建订单（DynamoDB）
   - 更新库存
   - 发布事件到 EventBridge
3. **DynamoDB Streams** 触发
4. **Recommendation Generator Lambda**:
   - 分析订单历史
   - 生成推荐
   - 存储到 UserRecommendations 表

### 用户行为事件流

1. **客户端** → `POST /api/user-actions`
2. **User Action Handler Lambda**:
   - 写入 UserActions 表
   - 发布事件到 EventBridge

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |

## CORS

所有端点都支持 CORS，可以从任何域名访问。

## 性能监控

### 关键指标

- **订单处理时间**: 目标 < 3s
- **推荐生成时间**: 目标 < 500ms
- **推荐查询时间**: 目标 < 500ms

### 监控方式

- CloudWatch Logs: 查看 Lambda 执行日志
- CloudWatch Metrics: 查看性能指标
- 自定义指标: 在响应中包含处理时间

## 注意事项

1. **推荐生成**: 推荐由 DynamoDB Streams 异步生成，首次查询可能需要等待
2. **库存更新**: 使用原子操作确保数据一致性
3. **事件顺序**: EventBridge 事件可能不保证顺序
4. **冷启动**: Lambda 冷启动可能影响首次请求性能

## 版本历史

- **v2.0.0**: 事件驱动架构，DynamoDB Streams 集成
- **v1.0.0**: 初始版本，基础推荐功能
