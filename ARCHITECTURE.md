# 系统架构文档

## 概述

这是一个基于 AWS 的 serverless、事件驱动的电商推荐系统，实现了订单处理、库存管理和个性化 AI 推荐功能。

## 架构图

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       │ HTTP/HTTPS
       │
┌──────▼─────────────────────────────────────────────┐
│              API Gateway                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ /orders  │  │/products │  │/recommend│        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼──────────────┼──────────────┘
        │             │              │
        │             │              │
┌───────▼──────┐  ┌───▼──────┐  ┌───▼──────────────┐
│ Order Handler│  │  Product │  │ Recommendation  │
│   Lambda     │  │  Lambda  │  │   API Lambda    │
└──────┬───────┘  └──────────┘  └─────────────────┘
       │
       │ 1. 写入订单
       │ 2. 更新库存
       │ 3. 发布事件
       │
┌──────▼─────────────────────────────────────────────┐
│              DynamoDB Tables                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Orders  │  │ Products │  │Inventory │        │
│  └────┬─────┘  └──────────┘  └──────────┘        │
└───────┼────────────────────────────────────────────┘
        │
        │ DynamoDB Streams
        │
┌───────▼────────────────────────────────────────────┐
│    Recommendation Generator Lambda                  │
│    (触发: 新订单创建)                                │
│    - 分析订单历史                                    │
│    - 生成个性化推荐                                  │
│    - 目标: < 500ms                                  │
└───────┬────────────────────────────────────────────┘
        │
        │ 写入推荐
        │
┌───────▼────────────────────────────────────────────┐
│         UserRecommendations Table                   │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│              EventBridge Event Bus                 │
│  - Order Placed Events                             │
│  - User Action Events                              │
└────────────────────────────────────────────────────┘
```

## 核心组件

### 1. API Gateway
- **功能**: RESTful API 入口
- **路由**:
  - `POST /api/orders` - 创建订单
  - `GET /api/products` - 获取产品列表
  - `GET /api/products/{product_id}` - 获取产品详情
  - `GET /api/recommendations` - 获取用户推荐
  - `POST /api/user-actions` - 记录用户行为
  - `GET /health` - 健康检查

### 2. Lambda 函数

#### Order Handler
- **功能**: 处理订单创建
- **流程**:
  1. 验证库存（原子操作）
  2. 创建订单记录（DynamoDB）
  3. 更新库存
  4. 发布事件到 EventBridge
- **性能目标**: < 3s
- **内存**: 1024 MB
- **超时**: 10s

#### Recommendation Generator
- **功能**: 生成个性化推荐
- **触发**: DynamoDB Streams (Orders 表)
- **流程**:
  1. 分析用户订单历史
  2. 计算产品相似度
  3. 生成推荐列表
  4. 存储到 UserRecommendations 表
- **性能目标**: < 500ms
- **内存**: 2048 MB
- **超时**: 15s

#### Recommendation API
- **功能**: 提供推荐查询接口
- **性能目标**: < 500ms
- **内存**: 512 MB
- **超时**: 5s

#### Product Browse Handler
- **功能**: 产品浏览和搜索
- **内存**: 512 MB
- **超时**: 5s

#### User Action Handler
- **功能**: 记录用户行为
- **流程**:
  1. 写入 DynamoDB
  2. 发布事件到 EventBridge

### 3. DynamoDB 表

#### Orders Table
- **主键**: `order_id` (String)
- **GSI**: `user_id-created_at-index`
- **Streams**: 启用 (NEW_AND_OLD_IMAGES)
- **用途**: 存储订单信息

#### Products Table
- **主键**: `product_id` (String)
- **用途**: 存储产品信息

#### Inventory Table
- **主键**: `product_id` (String)
- **用途**: 库存管理（原子更新）

#### UserRecommendations Table
- **主键**: `user_id` (String)
- **用途**: 存储用户个性化推荐

#### UserActions Table
- **主键**: `action_id` (String)
- **用途**: 记录用户行为（浏览、点击等）

### 4. EventBridge
- **事件总线**: `ecommerce-events-{stage}`
- **事件类型**:
  - `Order Placed` - 订单创建
  - `User Action` - 用户行为

### 5. DynamoDB Streams
- **表**: Orders
- **视图类型**: NEW_AND_OLD_IMAGES
- **用途**: 触发推荐生成 Lambda

## 数据流

### 订单处理流程

1. **客户端请求** → API Gateway → Order Handler Lambda
2. **验证库存**: 使用 DynamoDB 条件更新（原子操作）
3. **创建订单**: 写入 Orders 表
4. **更新库存**: 原子减少库存数量
5. **发布事件**: 发送到 EventBridge
6. **返回响应**: 订单ID和处理时间

### 推荐生成流程

1. **订单创建** → DynamoDB Streams 触发
2. **推荐生成 Lambda** 被触发
3. **查询订单历史**: 从 Orders 表获取用户最近订单
4. **分析购买模式**: 提取类别偏好
5. **生成推荐**: 基于类别相似度、评分、价格
6. **存储推荐**: 写入 UserRecommendations 表

### 推荐查询流程

1. **客户端请求** → API Gateway → Recommendation API Lambda
2. **查询推荐**: 从 UserRecommendations 表读取
3. **返回结果**: JSON 格式的推荐列表

## 性能指标

### 目标性能
- **订单处理**: < 3 秒
- **推荐生成**: < 500 毫秒
- **推荐查询**: < 500 毫秒

### 优化策略
1. **Lambda 容器复用**: 利用全局变量缓存连接
2. **DynamoDB 按需计费**: 自动扩展
3. **批量处理**: DynamoDB Streams 批量触发
4. **内存优化**: 根据函数需求分配内存
5. **连接池**: 复用 boto3 客户端

## 安全架构

### IAM 策略
- **最小权限原则**: 每个 Lambda 只访问必要的资源
- **细粒度控制**:
  - DynamoDB: 表级别权限
  - EventBridge: 事件总线级别权限
  - S3: 存储桶级别权限

### 数据安全
- **加密**: DynamoDB 表加密（默认启用）
- **访问控制**: IAM 角色和策略
- **网络**: API Gateway 提供 HTTPS

## 监控和日志

### CloudWatch
- **Lambda 日志**: 自动记录
- **指标**: 执行时间、错误率、调用次数
- **告警**: 可配置性能阈值告警

### 自定义指标
- 订单处理时间
- 推荐生成时间
- 推荐查询时间

## 扩展性

### 水平扩展
- **Lambda**: 自动扩展，无限制并发
- **DynamoDB**: 按需计费，自动扩展
- **API Gateway**: 自动处理高并发

### 垂直扩展
- **内存调整**: 根据性能需求调整 Lambda 内存
- **超时设置**: 根据处理时间调整

## 成本优化

1. **按需计费**: 只为实际使用付费
2. **Lambda 优化**: 减少执行时间和内存使用
3. **DynamoDB 按需**: 无需预置容量
4. **API Gateway**: 按请求计费

## 故障处理

### 错误处理
- **库存不足**: 返回 400 错误
- **产品不存在**: 返回 404 错误
- **系统错误**: 返回 500 错误，记录日志

### 重试机制
- **DynamoDB Streams**: 自动重试失败记录
- **EventBridge**: 可配置重试策略

## 部署

### 环境
- **开发环境**: `dev`
- **生产环境**: `prod`

### 部署步骤
1. 安装依赖: `npm install`
2. 部署服务: `serverless deploy`
3. 初始化数据: `python scripts/init_dynamodb.py`

